"""robots.txt is read by its STATUS before its body. RFC 9309 §2.3.1.

`cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 1. `Fetcher._robots_for` parsed
the response body as robots text whatever the status, so a 5xx with an empty body meant "allow
everything" — the opposite of what the RFC the fetcher claims to follow says:

* §2.3.1.3 "Unavailable": "in the context of HTTP, such status codes are in the 400-499 range.
  If a server status code indicates that the robots.txt file is unavailable to the crawler,
  then the crawler MAY access any resources on the server."
* §2.3.1.4 "Unreachable": "If the robots.txt file is unreachable due to server or network
  errors, this means the robots.txt file is undefined and the crawler MUST assume complete
  disallow. For example, in the context of HTTP, server errors are identified by status codes
  in the 500-599 range."

(corpus/kernel/rfc-9309-robots-exclusion-protocol.md, doc_id
`rfc-9309-robots-exclusion-protocol`.)

Driven through a real `httpx.Client` over `httpx.MockTransport` and a virtual clock, so the
status, the redirect handling and the backoff are httpx's and the fetcher's own, not a stub's.
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.clock import VirtualClock                                 # noqa: E402
from scan.collectors import http as http_col                        # noqa: E402
from scan.errors import RobotsDisallowed                            # noqa: E402
from scan.manners import Fetcher                                    # noqa: E402

HOST = "stats.example.gov"
BASE = f"https://{HOST}"
PAGE = f"{BASE}/products/estimates.html"


@pytest.fixture(scope="module")
def params():
    return load_params()


def _fetcher(params, robots, page_status=200):
    """A fetcher whose host answers `/robots.txt` with `robots` — a `(status, body)` pair, an
    exception to raise, or a callable taking the request — and every other path with a page."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.url.path == "/robots.txt":
            r = robots(request) if callable(robots) and not isinstance(robots, type) else robots
            if isinstance(r, BaseException):
                raise r
            if isinstance(r, httpx.Response):
                return r
            status, body = r
            return httpx.Response(status, content=body, headers={"content-type": "text/plain"})
        return httpx.Response(page_status, content=b"<html>page</html>",
                              headers={"content-type": "text/html"})

    m = params["manners"]
    client = httpx.Client(transport=httpx.MockTransport(handler),
                          follow_redirects=m["follow_redirects"],
                          max_redirects=m["max_redirects"])
    return Fetcher(params, client=client, clock=VirtualClock()), seen


def _decision(f: Fetcher, netloc: str = HOST) -> dict:
    [row] = [r for r in f.robots_log if r["netloc"] == netloc]
    return row


# ------------------------------------------------------------------ 2xx: parse

def test_a_served_robots_txt_is_parsed_and_obeyed(params):
    f, _ = _fetcher(params, (200, b"User-agent: *\nDisallow: /products/\n"))
    assert f.allowed(PAGE) is False
    row = _decision(f)
    assert (row["status"], row["robots_status"], row["decision"]) == (200, "successful", "rules")
    assert row["rfc9309"] == "2.3.1.1"


def test_a_served_empty_robots_txt_allows_everything(params):
    f, _ = _fetcher(params, (200, b""))
    assert f.allowed(PAGE) is True
    assert _decision(f)["robots_status"] == "successful"


# ------------------------------------------------------------------ 4xx: unavailable, allow

@pytest.mark.parametrize("status", [404, 403, 410, 401])
def test_a_4xx_is_unavailable_and_allows_everything(params, status):
    """§2.3.1.3. A 404 whose BODY happens to read like robots rules is still a 404: the file is
    unavailable and its body is an error page, not the host's policy."""
    f, _ = _fetcher(params, (status, b"User-agent: *\nDisallow: /\n"))
    assert f.allowed(PAGE) is True
    row = _decision(f)
    assert (row["status"], row["robots_status"], row["decision"]) == (
        status, "unavailable", "allow_all")
    assert row["rfc9309"] == "2.3.1.3"


# ------------------------------------------------------------------ 5xx / network: disallow

@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_a_5xx_is_unreachable_and_disallows_everything(params, status):
    """§2.3.1.4 — the defect. An empty 5xx body used to parse to nothing and allow all."""
    f, _ = _fetcher(params, (status, b""))
    assert f.allowed(PAGE) is False
    row = _decision(f)
    assert (row["status"], row["robots_status"], row["decision"]) == (
        status, "unreachable", "disallow_all")
    assert row["rfc9309"] == "2.3.1.4"


@pytest.mark.parametrize("exc", [httpx.ConnectError("reset by peer"),
                                 httpx.ReadTimeout("timed out"),
                                 httpx.RemoteProtocolError("server disconnected")])
def test_a_network_error_is_unreachable_and_disallows_everything(params, exc):
    """"unreachable due to server OR NETWORK errors". Before this change an exception on the
    robots read was swallowed into "no robots.txt", which is allow-all."""
    f, _ = _fetcher(params, exc)
    assert f.allowed(PAGE) is False
    row = _decision(f)
    assert (row["status"], row["robots_status"], row["decision"]) == (
        None, "unreachable", "disallow_all")
    assert row["error_class"] in ("connection_reset", "timeout", "unknown")


def test_unreachable_overrides_the_measurement_carve_out(params):
    """"Complete disallow" is complete: `/sitemap.xml`, `/data.json` and `/llms.txt` are fetched
    whatever robots SAYS (they are the object of measurement), but an unreachable robots.txt
    says nothing — the RFC's instruction is about the server, not about a rule in the file.
    `/robots.txt` itself stays fetchable, because it is the bootstrap and A4's measurement."""
    f, seen = _fetcher(params, (503, b""))
    for path in ("/sitemap.xml", "/data.json", "/llms.txt", "/.well-known/x"):
        assert f.allowed(BASE + path) is False, path
        with pytest.raises(RobotsDisallowed) as e:
            f.raw_get(BASE + path)
        assert "unreachable" in str(e.value) and "2.3.1.4" in str(e.value)
    assert f.allowed(BASE + "/robots.txt") is True
    assert f.raw_get(BASE + "/robots.txt")["status"] == 503
    # Only robots.txt ever went on the wire: the first read (with its 503 backoff retries) and
    # the explicit re-read above.
    assert {p for _m, p in seen} == {"/robots.txt"}


def test_an_unreachable_host_returns_error_never_fail(params):
    """DD-052 §6: the collector records the refusal as a BLIND class, so every rule returns
    `error` over it and none can score an absence claim about a page nobody read."""
    from scan import errors
    f, _ = _fetcher(params, (500, b""))
    [o] = http_col.fetch(f, "B3", "scan-x", PAGE, params)
    assert o.error_class == "robots_disallowed"
    assert errors.is_blind(o.error_class, errors.harness_of(params))
    assert o.response["status"] is None


def test_a_503_is_retried_under_the_backoff_before_it_is_called_unreachable(params):
    """The existing backoff still applies to the robots read (`backoff_on_status`), so a single
    transient 503 is not a cycle-long disallow."""
    answers = iter([(503, b""), (200, b"User-agent: *\nAllow: /\n")])
    f, seen = _fetcher(params, lambda _r: next(answers))
    assert f.allowed(PAGE) is True
    assert _decision(f)["robots_status"] == "successful"
    assert [p for _m, p in seen].count("/robots.txt") == 2


# ------------------------------------------------------------------ 3xx: follow, then the table

def test_a_redirect_is_followed_and_the_final_status_decides(params):
    """§2.3.1.2: follow, then "the robots.txt file MUST be fetched, parsed, and its rules
    followed in the context of the initial authority"."""
    def robots(request):
        if request.url.host == HOST:
            return httpx.Response(301, headers={"location": "https://cdn.example.gov/robots.txt"})
        return httpx.Response(200, content=b"User-agent: *\nDisallow: /products/\n")
    f, _ = _fetcher(params, robots)
    assert f.allowed(PAGE) is False
    row = _decision(f)
    assert (row["status"], row["robots_status"]) == (200, "successful")
    assert row["final_url"] == "https://cdn.example.gov/robots.txt"


def test_a_redirect_to_a_5xx_is_unreachable(params):
    def robots(request):
        if request.url.host == HOST:
            return httpx.Response(302, headers={"location": "https://cdn.example.gov/robots.txt"})
        return httpx.Response(500)
    f, _ = _fetcher(params, robots)
    assert f.allowed(PAGE) is False
    assert _decision(f)["robots_status"] == "unreachable"


def test_more_redirects_than_the_policy_follows_is_unavailable(params):
    """§2.3.1.2: "If there are more than five consecutive redirects, crawlers MAY assume that
    the robots.txt file is unavailable." A redirect loop is not a server error."""
    def robots(request):
        return httpx.Response(301, headers={"location": f"{BASE}/robots.txt"})
    f, _ = _fetcher(params, robots)
    assert f.allowed(PAGE) is True
    row = _decision(f)
    assert (row["robots_status"], row["decision"], row["rfc9309"]) == (
        "unavailable", "allow_all", "2.3.1.2")
    assert row["error_class"] == "redirect_loop"


# ------------------------------------------------------------------ the manners log line

def test_each_netloc_is_read_once_and_logged_once(params):
    f, seen = _fetcher(params, (404, b""))
    for _ in range(3):
        assert f.allowed(PAGE) is True
    assert [p for _m, p in seen].count("/robots.txt") == 1
    assert len(f.robots_log) == 1
    row = f.robots_log[0]
    assert set(row) >= {"netloc", "url", "status", "final_url", "robots_status", "decision",
                        "rfc9309", "error_class", "read_at"}
    assert row["url"] == f"{BASE}/robots.txt"


def test_the_status_table_is_the_rfc_and_nothing_else():
    """The table is read in one place (`manners.robots_access`), so a reader can check it
    against the RFC without running anything."""
    from scan.manners import robots_access
    assert robots_access(200) == ("successful", "rules", "2.3.1.1")
    assert robots_access(204) == ("successful", "rules", "2.3.1.1")
    assert robots_access(404) == ("unavailable", "allow_all", "2.3.1.3")
    assert robots_access(429) == ("unavailable", "allow_all", "2.3.1.3")
    assert robots_access(500) == ("unreachable", "disallow_all", "2.3.1.4")
    assert robots_access(599) == ("unreachable", "disallow_all", "2.3.1.4")
    assert robots_access(304) == ("unavailable", "allow_all", "2.3.1.2")
    assert robots_access(None, error_class="timeout") == ("unreachable", "disallow_all",
                                                           "2.3.1.4")
    assert robots_access(None, error_class="redirect_loop") == ("unavailable", "allow_all",
                                                                 "2.3.1.2")
