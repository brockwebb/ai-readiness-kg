"""The manners layer honours a host's `Crawl-delay`. `cc_tasks/2026-10-11_manners_honours_crawl_delay.md`.

Part 2's cycle (`cc_tasks/2026-10-07_seed_known_locations_verify_RESULT.md` §5 item 12) asked
catalog.data.gov for 47 resources at the standing 1 request per second while that host's
robots.txt says `Crawl-Delay: 10`. RFC 9309 does not define the record; its §2.2.4 lets a
parser read records it does not define, and this scanner's posture is to be the most polite
client on the host, so the interval is `max(standing, Crawl-delay)` for the group that applies
to this client (decision 1). Above `manners.crawl_delay_max_s` the host is not fetched in that
cycle and every leg that needed it is `error`, with the delay and the ceiling named (decision 2).
The interval used and its source are on the cycle's `robots_log` (decision 3).

Driven like `test_manners_robots_status.py`: a real `httpx.Client` over `httpx.MockTransport`
and a `VirtualClock`, so the gaps asserted are the ones the limiter asked for.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import errors, load_params                                # noqa: E402
from scan.clock import VirtualClock                                 # noqa: E402
from scan.collectors import http as http_col                        # noqa: E402
from scan.errors import RobotsDisallowed, classify_exception        # noqa: E402
from scan.manners import Fetcher                                    # noqa: E402

HOST = "catalog.example.gov"
BASE = f"https://{HOST}"
PAGES = [f"{BASE}/dataset/{i}" for i in range(4)]


@pytest.fixture(scope="module")
def params():
    return load_params()


def _fetcher(params, robots_txt: bytes):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, content=robots_txt,
                                  headers={"content-type": "text/plain"})
        return httpx.Response(200, content=b"<html>page</html>",
                              headers={"content-type": "text/html"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Fetcher(params, client=client, clock=VirtualClock()), seen


def _gaps(f: Fetcher) -> list:
    """Gaps between consecutive requests to HOST, the robots read included."""
    t = f.request_times[HOST]
    return [round(b - a, 6) for a, b in zip(t, t[1:])]


def _line(f: Fetcher) -> dict:
    [row] = [r for r in f.robots_log if r["netloc"] == HOST]
    return row


def _standing(params) -> float:
    return 1.0 / float(params["manners"]["requests_per_second_per_host"])


def test_a_crawl_delay_of_ten_spaces_requests_ten_seconds_apart(params):
    f, seen = _fetcher(params, b"User-agent: *\nCrawl-delay: 10\nDisallow: /private/\n")
    for url in PAGES:
        f.raw_get(url)
    # The robots read, then four pages: every gap after the read is the host's ten seconds.
    assert len(f.request_times[HOST]) == 5
    assert all(g >= 10.0 for g in _gaps(f)), _gaps(f)
    row = _line(f)
    assert (row["crawl_delay_s"], row["interval_s"], row["interval_source"]) == (
        10.0, 10.0, "crawl_delay")


def test_no_crawl_delay_runs_at_the_standing_interval_and_says_so(params):
    f, _ = _fetcher(params, b"User-agent: *\nDisallow: /private/\n")
    for url in PAGES:
        f.raw_get(url)
    assert _gaps(f) == [_standing(params)] * 4
    row = _line(f)
    assert (row["crawl_delay_s"], row["interval_s"], row["interval_source"]) == (
        None, _standing(params), "standing")


def test_a_crawl_delay_shorter_than_the_standing_interval_does_not_speed_us_up(params):
    """`max(standing, Crawl-delay)`: a host that permits a faster pace is not taken up on it."""
    f, _ = _fetcher(params, b"User-agent: *\nCrawl-delay: 0.25\n")
    for url in PAGES:
        f.raw_get(url)
    assert _gaps(f) == [_standing(params)] * 4
    row = _line(f)
    assert (row["crawl_delay_s"], row["interval_s"], row["interval_source"]) == (
        0.25, _standing(params), "standing")


@pytest.mark.parametrize("robots_txt, expected_gap", [
    # Another client's group asks for 30 s; ours is the wildcard group, which asks nothing.
    (b"User-agent: Googlebot\nCrawl-delay: 30\n\nUser-agent: *\nDisallow: /private/\n", 1.0),
    # Our own group asks for 5 s; the wildcard's 30 s does not apply to us.
    (b"User-agent: ai-readiness-kg-scanner\nCrawl-delay: 5\n\n"
     b"User-agent: *\nCrawl-delay: 30\n", 5.0),
])
def test_a_group_specific_delay_applies_only_to_its_group(params, robots_txt, expected_gap):
    """The same group-matching rule the Fetcher already uses for Allow and Disallow."""
    f, _ = _fetcher(params, robots_txt)
    for url in PAGES:
        f.raw_get(url)
    assert _gaps(f) == [expected_gap] * 4


@pytest.mark.parametrize("raw", [b"soon", b"-5", b"nan", b"inf", b"10s"])
def test_an_unparseable_crawl_delay_is_ignored_and_logged(params, raw, caplog):
    f, _ = _fetcher(params, b"User-agent: *\nCrawl-delay: " + raw + b"\n")
    with caplog.at_level(logging.WARNING, logger="scan.manners"):
        for url in PAGES:
            f.raw_get(url)
    assert _gaps(f) == [_standing(params)] * 4
    row = _line(f)
    assert (row["crawl_delay_s"], row["interval_source"]) == (None, "standing")
    assert row["crawl_delay_ignored"] == [{"line": 2, "value": raw.decode()}]
    assert any(raw.decode() in r.getMessage() and HOST in r.getMessage()
               for r in caplog.records), [r.getMessage() for r in caplog.records]


def test_a_crawl_delay_over_the_ceiling_refuses_the_host_for_the_cycle(params):
    """Decision 2: not fetched, and never quietly run at the ceiling instead. The carve-out
    paths are refused too: the ceiling is about the HOST, not about a rule in its file."""
    ceiling = float(params["manners"]["crawl_delay_max_s"])
    f, seen = _fetcher(params, b"User-agent: *\nCrawl-delay: 120\n")
    for url in [PAGES[0], f"{BASE}/sitemap.xml", f"{BASE}/data.json"]:
        with pytest.raises(RobotsDisallowed) as e:
            f.raw_get(url)
        msg = str(e.value)
        assert "Crawl-delay" in msg and "120" in msg and f"{ceiling:g}" in msg, msg
        assert classify_exception(e.value) == "robots_disallowed"
    with pytest.raises(RobotsDisallowed):
        f.raw_head(PAGES[1])
    # Only the bootstrap went on the wire, and it stays fetchable (A4's own measurement).
    assert [p for _m, p in seen] == ["/robots.txt"]
    assert f.raw_get(f"{BASE}/robots.txt")["status"] == 200
    row = _line(f)
    assert (row["crawl_delay_s"], row["interval_s"], row["interval_source"]) == (
        120.0, None, "crawl_delay_over_ceiling")
    assert row["crawl_delay_max_s"] == ceiling


def test_over_the_ceiling_a_leg_records_error_naming_the_delay_and_the_ceiling(params):
    """The collector path: a BLIND class, so every rule over it returns `error`, and the
    Observation carries the reason."""
    f, _ = _fetcher(params, b"User-agent: *\nCrawl-delay: 120\n")
    [o] = http_col.fetch(f, "B3", "scan-x", PAGES[0], params)
    assert o.error_class == "robots_disallowed"
    assert errors.is_blind(o.error_class, errors.harness_of(params))
    assert "Crawl-delay" in o.response["error"] and "crawl_delay_max_s" in o.response["error"]


def test_the_ceiling_is_sixty_seconds_in_params(params):
    assert params["manners"]["crawl_delay_max_s"] == 60
