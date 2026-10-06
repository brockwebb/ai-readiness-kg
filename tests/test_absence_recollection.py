"""The recollection's own changes: declarations resolved with network, `not_declared` and
`unreadable` entries that name the pages searched, B3 following every methodology candidate,
and a cycle restricted to the legs it recollects.

`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` and its ADDENDUM_01 (DN-012 d3, d6).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

from scan import declarations, load_params                            # noqa: E402

#: The twelve legs generation 14 re-scoped (rules RESULT §1), collected by this cycle.
RECOLLECTED = ["A1", "A2", "A3", "A9", "B1", "B3", "B4", "D1", "D3", "D4", "F4", "G4"]


@pytest.fixture(scope="module")
def params():
    return load_params()


def _block(unresolved: list) -> dict:
    return {"scheme": 1, "bodies": {"X": {"unresolved": unresolved}}}


# --------------------------------------------------------------------------- declarations

def test_a_not_declared_entry_must_name_the_pages_searched():
    with pytest.raises(declarations.DeclarationError, match="pages_searched"):
        declarations.validate(_block([{"role": "api_base", "status": "not_declared",
                                       "why": "none published"}]))
    declarations.validate(_block([{"role": "api_base", "status": "not_declared",
                                   "why": "none published",
                                   "pages_searched": ["https://www.example.gov/"]}]))


def test_an_unreadable_entry_must_name_the_pages_searched_too():
    with pytest.raises(declarations.DeclarationError, match="pages_searched"):
        declarations.validate(_block([{"role": "api_base", "status": "unreadable",
                                       "why": "403", "pages_searched": []}]))


def test_an_unknown_status_is_refused():
    with pytest.raises(declarations.DeclarationError, match="status"):
        declarations.validate(_block([{"role": "api_base", "status": "maybe", "why": "x"}]))


def test_a_searched_page_must_be_an_absolute_url():
    with pytest.raises(declarations.DeclarationError):
        declarations.validate(_block([{"role": "changelog", "status": "not_declared",
                                       "why": "x", "pages_searched": ["home page"]}]))


def test_every_body_has_every_field_resolved_or_says_why():
    """ADDENDUM_01 amendment 1: for each of the 16 bodies, api_base, the catalog organization,
    the department inventory and changelog_urls are each declared or carry an entry saying
    why not; api_base.terms_url likewise wherever an api_base is declared."""
    block = declarations.load()
    assert len(block["bodies"]) == 16
    for code, b in block["bodies"].items():
        roles = {u["role"] for u in b.get("unresolved") or []}
        inv = {e["role"] for e in b.get("inventory_urls") or []}
        assert b.get("api_base") or "api_base" in roles, code
        assert "catalog_organization" in inv or "catalog_organization" in roles, code
        assert ("department" in inv or "department" in roles
                or b.get("department_is_own_host")), code
        assert b.get("changelog_urls") or "changelog" in roles, code
        if b.get("api_base"):
            assert b["api_base"].get("terms_url") or "api_terms" in roles, code
        # No entry is left in the legacy "not attempted" state: the recollection read for each.
        for u in b.get("unresolved") or []:
            assert u.get("status") in ("not_declared", "unreadable"), (code, u)


def test_every_catalog_organization_is_on_catalog_data_gov(params):
    for code, b in declarations.load()["bodies"].items():
        for e in b.get("inventory_urls") or []:
            if e["kind"] == "catalog_organization":
                assert e["url"].startswith("https://catalog.data.gov/organization/"), code
                assert e["read_from"]["page"].startswith("https://catalog.data.gov/organization")


def test_a_not_declared_role_still_keeps_its_leg_at_error(params):
    """DN-012 d1 unchanged: a location the body does not publish is an `error`, never `fail`."""
    from scan.model import Observation
    from scan.rules import CURRENT, judge
    decl = {"unresolved": [{"role": "changelog", "status": "not_declared", "why": "none",
                            "pages_searched": ["https://www.example.gov/"]}]}
    block = declarations.record(decl, "X", "F4", params)
    o = Observation.make("F4", "F4", "doc", "https://www.example.gov/changelog", "http", "0.1.0",
                         params, {"method": "GET", "url": "https://www.example.gov/changelog"},
                         {"status": 404, "headers": {}, "body_sha256": None, "body_path": None,
                          "bytes": 0, "elapsed_ms": 1, "error": None},
                         parsed={"content_type": "text/html", "declared": block})
    f = judge(CURRENT["F4"], [o], params)
    assert f.verdict == "error" and "not declared (changelog)" in f.reason


# --------------------------------------------------------------------------- B3 collector

class _Fetcher:
    """Serves one product page whose links carry three methodology candidates, and records
    every URL asked for. No network."""

    def __init__(self, page: bytes):
        self.page, self.asked, self.requests = page, [], {}

    def allowed(self, url):
        return True

    def raw_get(self, url):
        self.asked.append(url)
        body = self.page if url.endswith("/product") else b"<html><body>m</body></html>"
        return {"status": 200, "headers": {"content-type": "text/html"}, "body": body,
                "elapsed_ms": 1, "final_url": url}


def _page(n: int) -> bytes:
    links = "".join(f'<a href="/methodology-{i}.html">Methodology {i}</a>' for i in range(n))
    return f"<html><body>{links}<a href='/methodology-0.html'>again</a></body></html>".encode()


def test_b3_follows_every_distinct_methodology_candidate(params, tmp_path, monkeypatch):
    from scan import model
    from scan.runner import collect_leg
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path)
    f = _Fetcher(_page(3))
    obs = collect_leg({"leg": "B3"}, {"doc_id": "d", "url": "https://h.example/product"},
                      params, f)
    followed = [o.target_url for o in obs[1:]]
    assert followed == [f"https://h.example/methodology-{i}.html" for i in range(3)]


def test_b3_stops_at_its_cap_and_the_rule_names_the_remainder(params, tmp_path, monkeypatch):
    from scan import model
    from scan.rules import CURRENT, judge
    from scan.runner import collect_leg
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path)
    cap = int(params["b3_methodology"]["max_followed"])
    f = _Fetcher(_page(cap + 2))
    obs = collect_leg({"leg": "B3"}, {"doc_id": "d", "url": "https://h.example/product"},
                      params, f)
    assert len(obs) == 1 + cap
    finding = judge(CURRENT["B3"], obs, params)
    assert finding.verdict == "error" and f"{cap} of {cap + 2}" in finding.reason


# --------------------------------------------------------------------------- leg restriction

def test_restrict_legs_keeps_only_the_named_legs_and_drops_empty_surfaces():
    from scan.run import restrict_legs
    tgts = [{"doc_id": "host:h", "legs": ["A12"]},
            {"doc_id": "home:h", "legs": ["A1", "A4", "D4", "G1-D"]},
            {"doc_id": "tierc", "legs": ["A4", "A5"]}]
    out, dropped = restrict_legs(tgts, ["A1", "D4"])
    assert [(t["doc_id"], t["legs"]) for t in out] == [("home:h", ["A1", "D4"])]
    assert dropped == ["host:h", "tierc"]


def test_restrict_legs_refuses_an_unknown_leg():
    from scan.run import restrict_legs
    with pytest.raises(SystemExit, match="ZZ"):
        restrict_legs([{"doc_id": "home:h", "legs": ["A1"]}], ["A1", "ZZ"])


def test_the_recollected_legs_are_the_generation_fourteen_twelve():
    from scan.rules import V14
    assert sorted(RECOLLECTED) == sorted(m.LEG for m in V14)
