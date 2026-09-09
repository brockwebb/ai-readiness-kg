"""Robots-first, the site bound, and off-site declarations.

`cc_tasks/2026-09-09_closeout_and_manners.md` §2, decisions 1 to 3. DD-062.

The defect these are about is on the cycle-3 request log and was found by
`cc_tasks/2026-09-09_report_draft_RESULT.md` §3: two GETs went to apex netlocs whose
`robots.txt` this scanner had never fetched, because the sitemap follower dereferenced a
declared URL through `raw_get` and nothing gated it. Three collectors were in that state, not
one.

Each test below drives real HTTP against loopback fixtures rather than asserting over source,
because the property is about what goes on the wire.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.errors import RobotsDisallowed                            # noqa: E402
from scan.fixtures.server import FixtureServer                      # noqa: E402
from scan.manners import Fetcher, psl_identity, same_site, site_of  # noqa: E402
from scan.collectors import robots as robots_col                    # noqa: E402
from scan.collectors import sitemap as sitemap_col                  # noqa: E402


def _netloc(url: str) -> str:
    return url.split("//", 1)[1]


def _declared(fetcher, base, params):
    """The `Sitemap:` URLs a host declares, read the way the runner reads them."""
    obs = robots_col.fetch(fetcher, "A4", "control:x", base + "/", params)
    return [u for o in obs for u in ((o.parsed or {}).get("sitemaps") or [])]


# ------------------------------------------------------------------ decision 2: the site

def test_a_site_is_the_registrable_domain_and_the_port_is_not_part_of_it():
    """The WHATWG "same site" test: scheme plus registrable domain, port excluded. This is
    what makes `www.samhsa.gov` and `samhsa.gov` one site, which is the relation the cycle-3
    defect ran along."""
    assert site_of("https://www.samhsa.gov/x") == "samhsa.gov"
    assert site_of("https://samhsa.gov/sitemap.xml") == "samhsa.gov"
    assert same_site("https://www.samhsa.gov/x", "https://samhsa.gov/sitemap.xml")
    # Two ports of one IP literal are one site: an IP has no registrable domain, so the host
    # itself is the key. The loopback fixture depends on this being true.
    assert same_site("http://127.0.0.1:1/", "http://127.0.0.1:2/sitemap.xml")
    assert not same_site("https://www.bls.gov/", "https://example.org/sitemap.xml")
    # A body's own subdomain is the same site as its department domain, which WIDENS the
    # contact bound. Asserted so the widening is visible rather than discovered later.
    assert site_of("https://www.ers.usda.gov/") == site_of("https://www.nass.usda.gov/")


def test_the_suffix_list_is_resolved_offline_and_identified_in_params():
    """A resolver that fetched the Public Suffix List over the network would falsify this
    harness's account of which hosts a cycle contacted, in the one module whose subject is
    exactly that. The identity is registered so a silent package upgrade is visible."""
    declared = load_params()["manners"]["site_bound"]
    live = psl_identity()
    assert declared["resolver"] == live["resolver"] == "tldextract"
    assert declared["version"] == live["version"], (
        "the installed tldextract is not the version params declares; the site bound moved "
        "without anyone registering it")
    assert declared["snapshot_sha256"] == live["snapshot_sha256"], (
        "the Public Suffix List snapshot changed under the same version")
    assert declared["snapshot_date"] is None, (
        "the bundled list carries no date; a date here would be an mtime wearing the look of "
        "provenance")


# ------------------------------------------------- decision 1: robots before anything else

def test_a_same_site_sibling_is_followed_but_only_after_its_own_robots_is_read():
    """**The defect, and the fix, on one fixture.**

    `sitemap_on_sibling` declares its sitemap on a second netloc of the same site. Before the
    fix the sibling's first and only request was `GET /sitemap.xml`. The verdict does not
    change: a same-site sibling is inside the contact bound and IS followed. What changes is
    that its `robots.txt` arrives first.
    """
    params = load_params()
    srv = FixtureServer("sitemap_on_sibling")
    base = srv.__enter__()
    try:
        sibling = _netloc(srv.sibling_url)
        f = Fetcher(params)
        sitemap_col.fetch(f, "A5", "control:sitemap_on_sibling", base + "/", params,
                          declared_sitemaps=_declared(f, base, params))
        got = [r for r in srv.requests if r["netloc"] == sibling]
        assert got, "the same-site sibling was never contacted; the declaration was not followed"
        assert got[0]["path"] == "/robots.txt", (
            f"the sibling's first request was {got[0]['path']}, not /robots.txt: this scanner "
            f"touched a netloc before reading its robots.txt")
        assert any(r["path"] == "/sitemap.xml" for r in got), (
            "the declared sitemap was never fetched")
    finally:
        srv.__exit__()


def test_no_netloc_is_ever_fetched_before_its_robots_txt():
    """The general property, over every request a fixture receives: for each netloc, the first
    thing this scanner asks for is `/robots.txt`. Stated over the log rather than over one
    collector, because the guarantee is the fetcher's and applies to all of them."""
    params = load_params()
    for fixture in ("passes_all", "sitemap_on_sibling"):
        srv = FixtureServer(fixture)
        base = srv.__enter__()
        try:
            f = Fetcher(params)
            sitemap_col.fetch(f, "A5", f"control:{fixture}", base + "/", params,
                              declared_sitemaps=_declared(f, base, params))
            first: dict = {}
            for r in srv.requests:
                first.setdefault(r["netloc"], r["path"])
            assert first, f"{fixture} received no requests"
            for netloc, path in first.items():
                assert path == "/robots.txt", (
                    f"{fixture}: {netloc} was first asked for {path}")
        finally:
            srv.__exit__()


def test_the_fetcher_refuses_a_disallowed_url_rather_than_the_collector_remembering():
    """A collector that never checked robots cannot mistake a refusal for a response: the
    fetcher raises, and the exception maps to `robots_disallowed` so the existing
    `except Exception` path in those collectors records the right class."""
    from scan.errors import classify_exception
    assert classify_exception(RobotsDisallowed("http://x/y")) == "robots_disallowed"
    params = load_params()
    srv = FixtureServer("passes_all")
    base = srv.__enter__()
    try:
        f = Fetcher(params)
        # `passes_all` allows everything, so this asserts the gate is WIRED rather than that
        # it refuses: a disallowing fixture would test the parser, and Protego is not ours.
        f.raw_get(base + "/index.html")
        assert f"{base}" in " ".join(f._robots) or f._robots, (
            "the fetcher issued a GET without populating its robots cache for that netloc")
    finally:
        srv.__exit__()


# ------------------------------------- decision 3: an off-site declaration is observed only

def test_an_off_site_declaration_is_recorded_and_never_requested():
    """Decision 3. The declaration is evidence and carries its URL; no request is made. The
    URL used here resolves to a different registrable domain and is never contacted, which is
    also why this test needs no second server."""
    params = load_params()
    srv = FixtureServer("passes_all")
    base = srv.__enter__()
    try:
        f = Fetcher(params)
        off = "https://someone-elses-site.example.org/sitemap.xml"
        obs = sitemap_col.fetch(f, "A5", "control:passes_all", base + "/", params,
                                declared_sitemaps=[off])
        recorded = [o for o in obs if o.error_class == "sitemap_off_site"]
        assert len(recorded) == 1, [o.error_class for o in obs]
        o = recorded[0]
        assert o.target_url == off
        assert o.request.get("not_requested") is True
        assert o.response["status"] is None
        assert (o.parsed or {})["sitemap_site"] == "example.org"
        assert not any(r["netloc"].startswith("someone") for r in srv.requests)
        assert f.requests.get("someone-elses-site.example.org", 0) == 0, (
            "the fetcher counted a request to an off-site netloc")
    finally:
        srv.__exit__()


def test_an_off_site_declaration_is_not_a_discovery_failure():
    """`RULE-A5-v2`. v1 called this `fail`, which reports OUR contact bound as THEIR omission.
    Both rules are asserted, because a rule that returned `not_applicable` for everything
    would satisfy the second assertion alone."""
    from scan.model import Observation
    from scan.rules import judge as judge_rule
    params = load_params()
    off = Observation.make(
        "A5", "A5", "d", "https://other.example.org/sitemap.xml", "sitemap", "0.1.0", params,
        {"method": None, "url": "https://other.example.org/sitemap.xml", "not_requested": True},
        {"status": None, "headers": {}, "body_sha256": None, "body_path": None, "bytes": 0,
         "elapsed_ms": 0},
        parsed={"present": None, "kind": "sitemap", "covers_product": None,
                "sitemap_site": "example.org"},
        error_class="sitemap_off_site")
    assert judge_rule("RULE-A5-v1", [off], params).verdict == "fail", (
        "the recorded defect no longer reproduces under v1")
    v2 = judge_rule("RULE-A5-v2", [off], params)
    assert v2.verdict == "not_applicable", v2.reason
    assert "another site" in v2.reason and "the bound is ours" in v2.reason


def test_v2_agrees_with_v1_wherever_nothing_was_declared_off_site():
    """v2 changes the off-site case and nothing else."""
    from scan.model import Observation
    from scan.rules import judge as judge_rule
    params = load_params()

    def obs(**parsed):
        return Observation.make(
            "A5", "A5", "d", "https://x/sitemap.xml", "sitemap", "0.1.0", params,
            {"method": "GET", "url": "https://x/sitemap.xml"},
            {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 1, "elapsed_ms": 1},
            parsed={"kind": "sitemap", **parsed})

    for case in ({"present": True, "covers_product": True, "url_count": 3},
                 {"present": True, "covers_product": False, "url_count": 3},
                 {"present": False, "covers_product": None, "url_count": None}):
        o = [obs(**case)]
        assert (judge_rule("RULE-A5-v1", o, params).verdict
                == judge_rule("RULE-A5-v2", o, params).verdict), case


# ------------------------------------------------- §3: the cycle-3 log under the new policy

def test_replaying_cycle_3_names_exactly_the_two_apex_sitemap_gets():
    """**The defect, counted on the log that produced it.**

    `cc_tasks/2026-09-09_closeout_and_manners.md` §3 asks which requests the new policy would
    have refused, and expects the two apex sitemap GETs. The count is right and the verb is
    not, which is the premise this test corrects: both apex netlocs are the SAME SITE as the
    host that declared them (`samhsa.gov` from `www.samhsa.gov`), so decision 3 does not refuse
    them at all. Decision 1 is what applies: each would have been PRECEDED by a fetch of that
    netloc's own `robots.txt`. The new policy refuses nothing on this log and adds two reads.

    The filter is the load-bearing part and is why a first attempt at this replay reported 68
    netlocs. An Observation records a URL whether or not a request went out: an `off_host` link
    and a `robots_disallowed` path are recorded with their URL precisely so the log shows the
    policy was applied. Counting those as contacts turns 161 recorded exclusions into 44
    imaginary hosts. `errors.NOT_FETCHED` is the set that says which, and it is read from
    there rather than listed here.
    """
    import json
    import urllib.parse
    from scan import errors

    payload = REPO / "state" / "scan_2026-09-09.json"
    if not payload.is_file():
        pytest.skip("cycle 3's payload is not on disk")
    doc = json.loads(payload.read_text(encoding="utf-8"))

    first_request, robots_read, issued = {}, set(), 0
    for o in doc["observations_detail"]:
        url = (o.get("request") or {}).get("url") or ""
        if not url or url.startswith("fixture://"):
            continue
        if o.get("error_class") in set(errors.NOT_FETCHED):
            continue                       # recorded with its URL; no request was made
        netloc = urllib.parse.urlsplit(url).netloc.lower()
        if netloc.startswith("127.0.0.1"):
            continue                       # control fixtures
        issued += 1
        first_request.setdefault(netloc, url)
        if urllib.parse.urlsplit(url).path == "/robots.txt":
            robots_read.add(netloc)

    assert issued > 0 and first_request, "the replay found no requests to judge"
    unread = sorted(set(first_request) - robots_read)
    would_add = sorted(first_request[n] for n in unread)
    assert would_add == ["https://data.gov/sitemap.xml",
                         "https://samhsa.gov/sitemap.xml"], would_add

    # And each is same-site with the host whose robots.txt declared it, so decision 3 permits
    # the fetch and only decision 1 changes anything.
    assert same_site("https://www.samhsa.gov/", "https://samhsa.gov/sitemap.xml")
    assert same_site("https://www.data.gov/", "https://data.gov/sitemap.xml")
    would_refuse = [u for u in would_add
                    if not same_site(f"https://www.{urllib.parse.urlsplit(u).netloc}/", u)]
    assert would_refuse == [], (
        "the new policy would refuse a request on this log; §3 expected it to refuse none and "
        "to add two robots reads")
