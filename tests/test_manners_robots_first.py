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
from scan.manners import (Fetcher, netloc_of, same_site,            # noqa: E402
                          site_key)
from scan.collectors import robots as robots_col                    # noqa: E402
from scan.collectors import sitemap as sitemap_col                  # noqa: E402


def _netloc(url: str) -> str:
    return url.split("//", 1)[1]


def _declared(fetcher, base, params):
    """The `Sitemap:` URLs a host declares, read the way the runner reads them."""
    obs = robots_col.fetch(fetcher, "A4", "control:x", base + "/", params)
    return [u for o in obs for u in ((o.parsed or {}).get("sitemaps") or [])]


# ------------------------------------------------------------------ decision 2: the site

def test_a_site_key_is_the_roster_host_with_one_www_stripped():
    """DD-063 decision 1. ONE leading `www.`, and nothing else: stripping every leading label
    is what turned `nces.ed.gov` into `ed.gov` under the superseded definition."""
    assert site_key("https://www.samhsa.gov/x") == "samhsa.gov"
    assert site_key("https://samhsa.gov/sitemap.xml") == "samhsa.gov"
    assert site_key("nces.ed.gov") == "nces.ed.gov"
    assert site_key("bjs.ojp.gov") == "bjs.ojp.gov"
    assert site_key("https://www.ers.usda.gov/") == "ers.usda.gov"
    assert netloc_of("https://user@www.bls.gov:443/x") == "www.bls.gov"


@pytest.mark.parametrize("netloc,roster_host,want", [
    # Every consequence decision 1 lists, by name.
    ("samhsa.gov", "www.samhsa.gov", True),
    ("catalog.data.gov", "www.data.gov", True),
    ("nass.usda.gov", "www.ers.usda.gov", False),
    ("www.usda.gov", "www.ers.usda.gov", False),
    # And the three the superseded PSL definition got wrong in the other direction.
    ("data.nist.gov", "www.nist.gov", True),
    ("open.gsa.gov", "www.gsa.gov", True),
    ("ies.ed.gov", "nces.ed.gov", False),
    ("www.ojp.gov", "bjs.ojp.gov", False),
    # Suffix matching is on a LABEL boundary, not a substring: RFC 6265 §5.1.3.
    ("evilsamhsa.gov", "www.samhsa.gov", False),
    ("samhsa.gov.attacker.test", "www.samhsa.gov", False),
])
def test_same_site_is_rfc_6265_domain_matching(netloc, roster_host, want):
    """Prior art adopted, not invented: a string domain-matches a domain string if they are
    identical, or the string is a suffix of it and the character before the match is a dot.
    The two negative cases at the end are why the dot is in the test."""
    assert same_site(netloc, roster_host) is want


def test_the_frame_has_one_site_key_per_body():
    """The count decision 1 predicts, over the real target list: 19 keys for 19 bodies, and
    every netloc in the frame belongs to exactly one of them. A Tier C machine entry point
    takes its BODY's key, so `catalog.data.gov` does not become a twentieth site."""
    import json as _json
    doc = _json.loads((REPO / "state" / "scan_targets_fss_2026-09.json")
                      .read_text(encoding="utf-8"))
    assert doc["targets_version"] >= 4
    keys = {h["site_key"] for h in doc["hosts"]}
    bodies = {h.get("netloc_of") or h["host"] for h in doc["hosts"]}
    assert len(keys) == len(bodies) == 19, (sorted(keys), sorted(bodies))
    assert doc["site_count"] == 19
    for h in doc["hosts"]:
        assert same_site(h["host"], h["site_key"]), h
    # The merge the superseded definition made, asserted as undone.
    by = {h["host"]: h["site_key"] for h in doc["hosts"]}
    assert by["www.ers.usda.gov"] != by["www.nass.usda.gov"] != by["www.aphis.usda.gov"]


def test_no_suffix_list_dependency_remains():
    """Decision 1: "The PSL dependency is removed unless something else uses it." Nothing
    does. Asserted over source, because an unused import is exactly how a dependency survives
    the decision that retired it."""
    import subprocess
    # The needles are assembled rather than written, so this file does not match its own
    # search and report itself as the surviving dependency.
    needles = ["tld" + "extract", "psl_" + "identity"]
    r = subprocess.run(["git", "grep", "-l", "-e", needles[0], "-e", needles[1],
                        "--", "assessment", "scripts", "tests"],
                       capture_output=True, text=True, cwd=str(REPO))
    left = [f for f in r.stdout.split() if f != "tests/test_manners_robots_first.py"]
    assert not left, f"the Public Suffix List is still reached from: {left}"
    assert load_params()["manners"]["site_bound"]["resolver"] is None


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
        # The site key of a host with no leading `www.` is the host itself. Under DD-062's
        # registrable-domain definition this read `example.org`; under DD-063 an unrelated
        # host is named in full, which is the more useful thing to record about a declaration
        # we declined to follow.
        assert (o.parsed or {})["sitemap_site"] == "someone-elses-site.example.org"
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
    import json as _json
    import urllib.parse
    from scan import errors

    payload = REPO / "state" / "scan_2026-09-09.json"
    if not payload.is_file():
        pytest.skip("cycle 3's payload is not on disk")
    doc = _json.loads(payload.read_text(encoding="utf-8"))

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
    # The four counts §3 of `cc_tasks/2026-09-09_manners_closeout.md` names.
    assert len(first_request) == 24, sorted(first_request)
    unread = sorted(set(first_request) - robots_read)
    would_add = sorted(first_request[n] for n in unread)
    assert would_add == ["https://data.gov/sitemap.xml",
                         "https://samhsa.gov/sitemap.xml"], would_add

    # OFF-SITE FETCHES, under the unified bound: a netloc matching no roster site key. These
    # are what the bound forbids outright, as against the two above, which it merely makes
    # polite. Cycle 3 has none, and the two apex GETs are on-site by DD-063.
    keys = {h["site_key"] for h in _json.loads(
        (REPO / "state" / "scan_targets_fss_2026-09.json")
        .read_text(encoding="utf-8"))["hosts"]}
    assert len(keys) == 19
    off_site = sorted(n for n in first_request if not any(same_site(n, k) for k in keys))
    assert off_site == [], off_site

    # And each is same-site with the host whose robots.txt declared it, so decision 3 permits
    # the fetch and only decision 1 changes anything.
    assert same_site("https://www.samhsa.gov/", "https://samhsa.gov/sitemap.xml")
    assert same_site("https://www.data.gov/", "https://data.gov/sitemap.xml")
    would_refuse = [u for u in would_add
                    if not same_site(f"https://www.{urllib.parse.urlsplit(u).netloc}/", u)]
    assert would_refuse == [], (
        "the new policy would refuse a request on this log; §3 expected it to refuse none and "
        "to add two robots reads")


# ------------------------------------------- decision 2: one contact policy, not two

def test_links_and_declarations_are_bounded_by_the_same_test():
    """Decision 2. `on_roster_host` governed links by NETLOC EQUALITY while `sitemap.fetch`
    compared declared URLs by site: two contact policies wearing one name, under which a
    sibling netloc was off-limits to a link and reachable through a `Sitemap:` line. Both go
    through `same_site` now, so the two agree by construction rather than by coincidence."""
    from scan import manners
    params = load_params()
    surface = "https://www.data.gov/"
    for url, want in (("https://catalog.data.gov/dataset", True),
                      ("https://www.data.gov/x", True),
                      ("https://data.gov/sitemap.xml", True),
                      ("https://www.usda.gov/x", False)):
        assert manners.on_roster_host(url, surface, params) is want, url
        assert same_site(url, surface) is want, url
    # The link gate and the declaration gate are the same function, read from source: a second
    # comparison anywhere is the defect returning.
    src = Path(manners.__file__).read_text(encoding="utf-8")
    assert "return same_site(url, surface_url)" in src, (
        "on_roster_host no longer delegates to the shared site test")


# ---------------------------------- decision 3: a script cannot write into the committed store

def test_a_collector_call_from_a_script_lands_in_quarantine(tmp_path, monkeypatch):
    """Decision 3, and it is aimed at what actually happened: twice in two consecutive tasks a
    fixture driver run from a script filled `corpus/evidence/scan/` with loopback bodies that
    no Observation cited. The standing guard is `tests/conftest.py`, which redirects the store
    under pytest and cannot see a script.

    Driven through `store_evidence` with no explicit root, which is exactly how a collector
    calls it.
    """
    from scan import model
    monkeypatch.delenv(model.CYCLE_TOKEN_ENV, raising=False)
    # BOTH the root and the protected LANE move. The guard fires on where the bytes would
    # land, so a test that repoints only the root is testing a write to somewhere unprotected
    # and would pass against a guard that does nothing.
    monkeypatch.setattr(model, "COMMITTED_EVIDENCE", tmp_path / "committed")
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path / "committed" / "scan")
    monkeypatch.setattr(model, "SCRIPT_QUARANTINE", tmp_path / "quarantine")
    monkeypatch.setattr(model, "REDIRECT_LOG", tmp_path / "quarantine" / "redirects.jsonl")

    _digest, path = model.store_evidence(b"<html>a driver wrote this</html>")
    assert "quarantine" in path, path
    assert "committed" not in path
    assert not (tmp_path / "committed").exists(), (
        "an unlicensed write created the committed store")
    # The redirect is a RECORD, not a silence.
    logged = (tmp_path / "quarantine" / "redirects.jsonl").read_text(encoding="utf-8")
    assert model.CYCLE_TOKEN_ENV in logged and "redirected_to" in logged


def test_the_cycle_runner_licenses_the_write_and_nothing_else_does(tmp_path, monkeypatch):
    """With the token set, the same call reaches the committed store. The token is set in
    `run.py::main` and not at import, so importing the runner to reach `run_surface` from a
    driver licenses nothing."""
    from scan import model
    monkeypatch.setattr(model, "COMMITTED_EVIDENCE", tmp_path / "committed")
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path / "committed" / "scan")
    monkeypatch.setenv(model.CYCLE_TOKEN_ENV, "1")
    _digest, path = model.store_evidence(b"<html>a cycle wrote this</html>")
    assert "committed" in path, path

    run_src = (REPO / "assessment" / "harness" / "scan" / "run.py").read_text(encoding="utf-8")
    token_line = f'os.environ[CYCLE_TOKEN_ENV]'
    assert token_line in run_src
    before_main = run_src.split("def main(")[0]
    assert token_line not in before_main, (
        "the cycle token is set at import; importing run.py from a driver would license every "
        "write that driver makes, which is the case this guard exists for")


def test_a_root_outside_the_committed_store_is_always_honoured(tmp_path, monkeypatch):
    """The guard fires on WHERE THE BYTES LAND, not on whether the caller named a root.

    Both spellings are asserted, because the first implementation keyed on `root is None` and
    broke the second: `tests/conftest.py` redirects the store under pytest by repointing the
    module global, and `--evidence-root` passes a root explicitly. A guard that redirected a
    defaulted write no matter where the default pointed sent a deliberately staged body to
    quarantine, and it took the full suite to find it.
    """
    from scan import model
    monkeypatch.delenv(model.CYCLE_TOKEN_ENV, raising=False)
    # (a) named explicitly
    _d, path = model.store_evidence(b"staged", root=tmp_path / "staging")
    assert "staging" in path and "quarantine" not in path
    # (b) defaulted, with the module global repointed away from the committed lane
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path / "repointed")
    _d2, path2 = model.store_evidence(b"repointed")
    assert "repointed" in path2 and "quarantine" not in path2
