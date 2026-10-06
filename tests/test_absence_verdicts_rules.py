"""Absence verdicts over a partial search become `error`, naming the remainder. Generation 14.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 8, DN-012 d1 to d3, audit C-01, C-04,
C-14. **No network.** Observations are built directly, and the collector is driven through a
stub fetcher that answers every HEAD and GET with nothing beyond what each test needs.

The three properties each new rule version owes:

1. a truncated, guessed or undeclared search yields `error`, and the reason names the remainder;
2. a complete search that finds nothing yields `fail`;
3. the predecessor, judging the same Observations, still returns what it always returned, and
   its module is untouched (`tests/test_scan_harness_v3.py` holds the bytes; here, the
   verdict).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import declarations, load_params, manners                  # noqa: E402
from scan.collectors import links as links_collector                  # noqa: E402
from scan.model import Observation                                     # noqa: E402
from scan.rules import CURRENT, GENERATIONS, REGISTRY, claim_of       # noqa: E402
from scan.rules import judge as judge_rule                             # noqa: E402
from scan.rules import _scope                                          # noqa: E402

HOST = "https://stats.example.gov"
PAGE = f"{HOST}/products/estimates.html"
DOC = "flagship:stats.example.gov/products/estimates.html"
NEW = ("RULE-A1-v5", "RULE-A2-v4", "RULE-A3-v7", "RULE-A9-v2", "RULE-B1-v3", "RULE-B3-v4",
       "RULE-B4-v2", "RULE-D1-v4", "RULE-D3-v2", "RULE-D4-v4", "RULE-F4-v4", "RULE-G4-v2")


@pytest.fixture(scope="module")
def params():
    return load_params()


def _obs(params, leg, url, *, status=200, ctype="text/html", parsed=None, error_class=None,
         collector="http", body=b"x"):
    return Observation.make(leg, leg, DOC, url, collector, "0.1.0", params,
                            {"method": "GET", "url": url},
                            {"status": status, "headers": {"content-type": ctype},
                             "body_sha256": None if status is None else "0" * 64,
                             "body_path": None, "bytes": len(body) if status else 0,
                             "elapsed_ms": 1},
                            parsed=parsed, error_class=error_class)


def _decl(**kw) -> dict:
    """A `declared` block as `declarations.record` writes it."""
    return {"scheme": declarations.SCHEME, "body": "X", "unresolved": [], **kw}


# --------------------------------------------------------------------------- generation 14

def test_generation_fourteen_is_the_twelve_new_modules_and_they_are_current():
    assert [m.RULE_ID for m in GENERATIONS[-1]] == list(NEW)
    for rid in NEW:
        assert CURRENT[REGISTRY[rid].LEG] == rid
        assert claim_of(rid) == "absence", rid
    # Every predecessor stays registered: a Finding recorded under it must re-derive.
    for rid in ("RULE-A1-v4", "RULE-A2-v3", "RULE-A3-v6", "RULE-A9-v1", "RULE-B1-v2",
                "RULE-B3-v3", "RULE-B4-v1", "RULE-D1-v3", "RULE-D3-v1", "RULE-D4-v3",
                "RULE-F4-v3", "RULE-G4-v1"):
        assert rid in REGISTRY


def test_the_rules_restate_the_schemes_the_collector_writes(params):
    """A rule may not import `scan.declarations`, so `_scope` restates the two scheme numbers;
    this holds them equal to the writers'."""
    assert _scope.DECLARED_SCHEME == declarations.SCHEME
    assert _scope.CANDIDATES_SCHEME == params["link_probe"]["rank"]["candidates_scheme"]


# --------------------------------------------------------------------------- A1 and A3

def _page(params, n_on_host, probed, *, block=True):
    """A link-probe page carrying `n_on_host` on-host links, and its `link_candidates` block as
    the collector would write it when `probed` of them were HEADed."""
    links = [{"href": f"{HOST}/nav/{i}.html", "text": f"nav {i}"} for i in range(n_on_host)]
    parsed = {"content_type": "text/html", "links": links}
    if block:
        parsed["link_candidates"] = {
            "scheme": 1, "on_host": n_on_host, "probed": probed, "unprobed": n_on_host - probed,
            "cap": params["link_probe"]["max_links_probed"], "off_host": 0,
            "unprobed_first": [f"{HOST}/nav/{probed}.html"] if n_on_host > probed else []}
    return _obs(params, "link_probe", PAGE, parsed=parsed)


def _link(params, i, ctype="text/html"):
    return _obs(params, "link_probe", f"{HOST}/nav/{i}.html", ctype=ctype, collector="links",
                parsed={"probe": "link", "content_type": ctype, "extension": ".html",
                        "is_bulk": False, "filtered_by_query": False, "content_length": 10,
                        "meets_size_floor": False})


@pytest.mark.parametrize("rid,prior", [("RULE-A1-v5", "RULE-A1-v4"),
                                       ("RULE-A3-v7", "RULE-A3-v6")])
def test_a_truncated_link_set_is_error_naming_the_remainder(params, rid, prior):
    obs = [_page(params, 115, 25)] + [_link(params, i) for i in range(25)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "error"
    assert "absence not established" in f.reason
    assert "25 of 115 on-host links probed, 90 unprobed, cap 25" in f.reason
    # The predecessor, over the same evidence, says what it always said.
    assert judge_rule(prior, obs, params).verdict == "fail"


@pytest.mark.parametrize("rid", ["RULE-A1-v5", "RULE-A3-v7"])
def test_a_complete_probed_link_set_with_nothing_found_is_fail(params, rid):
    obs = [_page(params, 8, 8)] + [_link(params, i) for i in range(8)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "fail", f.reason
    assert "all 8 on-host link(s) probed" in f.reason


@pytest.mark.parametrize("rid", ["RULE-A1-v5", "RULE-A3-v7"])
def test_a_page_whose_candidates_were_never_accounted_is_error(params, rid):
    obs = [_page(params, 8, 8, block=False)] + [_link(params, i) for i in range(8)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "error" and "were not accounted" in f.reason


def test_an_unprobed_record_is_blind_and_its_class_is_on_the_map():
    from scan import errors
    assert errors.is_blind("unprobed_over_cap", errors.HARNESS_CURRENT)
    assert "unprobed_over_cap" in errors.NOT_REQUESTED


def test_a_found_download_still_passes_over_a_truncated_set(params):
    """Existence stands: unprobed links cannot unfind a fetched whole-product archive."""
    zipped = _obs(params, "link_probe", f"{HOST}/bulk/all.zip", ctype="application/zip",
                  collector="links",
                  parsed={"probe": "link", "content_type": "application/zip", "extension": ".zip",
                          "is_archive": True, "is_bulk": True, "content_length": 10 ** 7})
    obs = [_page(params, 115, 25), zipped] + [_link(params, i) for i in range(24)]
    assert judge_rule("RULE-A3-v7", obs, params).verdict == "pass"


# --------------------------------------------------------------------------- A2 and A9

def _api_obs(params, leg, url, decl, *, status=404, parsed_api=False, ctype="text/plain"):
    parsed = {"content_type": ctype, "declared": decl}
    if leg == "A2":
        parsed["api"] = {"openapi_parsed": parsed_api}
    return _obs(params, leg, url, status=status, ctype=ctype, parsed=parsed,
                error_class="http_4xx" if status and status >= 400 else None)


@pytest.mark.parametrize("rid,prior", [("RULE-A2-v4", "RULE-A2-v3"),
                                       ("RULE-A9-v2", "RULE-A9-v1")])
def test_no_declared_api_base_is_error_not_fail(params, rid, prior):
    leg = REGISTRY[rid].LEG
    decl = _decl(field="api_base", api_base=None)
    obs = [_api_obs(params, leg, f"{HOST}/openapi.json", decl),
           _api_obs(params, leg, f"{HOST}/swagger.json", decl)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "error"
    assert ("no documented API base declared for this body; guessed paths do not establish "
            "absence") in f.reason
    assert judge_rule(prior, obs, params).verdict == "fail"


@pytest.mark.parametrize("rid", ["RULE-A2-v4", "RULE-A9-v2"])
def test_a_declared_api_base_not_probed_is_error(params, rid):
    leg = REGISTRY[rid].LEG
    decl = _decl(field="api_base", api_base={"url": "https://api.example.gov/data",
                                             "read_from": {"page": "https://x"}})
    obs = [_api_obs(params, leg, f"{HOST}/openapi.json", decl)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "error"
    assert "documented API base declared and not probed: https://api.example.gov/data" in f.reason


@pytest.mark.parametrize("rid", ["RULE-A2-v4", "RULE-A9-v2"])
def test_a_declared_api_base_probed_with_no_description_is_fail(params, rid):
    leg = REGISTRY[rid].LEG
    decl = _decl(field="api_base", api_base={"url": "https://api.example.gov/data",
                                             "read_from": {"page": "https://x"}})
    obs = [_api_obs(params, leg, f"{HOST}/openapi.json", decl),
           _api_obs(params, leg, "https://api.example.gov/data", decl)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "fail", f.reason
    assert "declared API base" in f.reason


def test_observations_with_no_declared_block_are_error_and_say_why(params):
    obs = [_obs(params, "A2", f"{HOST}/openapi.json", status=404, ctype="text/plain",
                parsed={"api": {"openapi_parsed": False}}, error_class="http_4xx")]
    f = judge_rule("RULE-A2-v4", obs, params)
    assert f.verdict == "error" and "collected before DN-012 d3" in f.reason


# --------------------------------------------------------------------------- D4 and its consumers

def _cat(params, url, decl, *, present):
    parsed = {"present": present, "declared": decl}
    if present:
        parsed.update({"membership": {"test": "x", "fields": [], "records": 0},
                       "dcat_fields": {"scheme": 1, "parsed": True, "product_records": 0,
                                       "catalog_records": 3}})
    return _obs(params, "D4", url, status=200 if present else 404,
                ctype="application/json" if present else "text/plain", parsed=parsed,
                error_class=None if present else "http_4xx")


def _inv(*urls, unresolved=()):
    return _decl(field="inventory_urls",
                 inventory_urls=[{"url": u, "kind": "data_json", "role": "department",
                                  "read_from": {"page": "https://x"}} for u in urls],
                 unresolved=list(unresolved))


D4_FAMILY = [("RULE-D4-v4", "RULE-D4-v3"), ("RULE-G4-v2", "RULE-G4-v1"),
             ("RULE-D3-v2", "RULE-D3-v1"), ("RULE-B4-v2", "RULE-B4-v1")]


@pytest.mark.parametrize("rid,prior", D4_FAMILY)
def test_a_declared_inventory_not_observed_is_error_naming_it(params, rid, prior):
    decl = _inv(f"{HOST}/data.json", "https://dept.example.gov/data.json")
    obs = [_cat(params, f"{HOST}/data.json", decl, present=False)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "error", f.reason
    assert "declared inventory not observed: https://dept.example.gov/data.json" in f.reason
    assert judge_rule(prior, obs, params).verdict == "fail"


@pytest.mark.parametrize("rid,prior", D4_FAMILY)
def test_an_unresolved_inventory_is_error_too(params, rid, prior):
    decl = _inv(f"{HOST}/data.json",
                unresolved=[{"role": "catalog_organization", "why": "slug unknown"}])
    obs = [_cat(params, f"{HOST}/data.json", decl, present=False)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "error" and "slug unknown" in f.reason


@pytest.mark.parametrize("rid,prior", D4_FAMILY)
def test_every_declared_inventory_observed_and_none_a_catalog_is_fail(params, rid, prior):
    decl = _inv(f"{HOST}/data.json", "https://dept.example.gov/data.json")
    obs = [_cat(params, f"{HOST}/data.json", decl, present=False),
           _cat(params, "https://dept.example.gov/data.json", decl, present=False)]
    f = judge_rule(rid, obs, params)
    assert f.verdict == "fail", f.reason
    assert "any" in f.reason and "declared inventor" in f.reason


def test_b1_v3_carries_the_inventory_remainder_in_its_catalog_half(params):
    decl = _inv(f"{HOST}/data.json", "https://dept.example.gov/data.json")
    page = _obs(params, "A6", PAGE, parsed={"content_type": "text/html", "raw": {},
                                            "keys": []})
    obs = [_cat(params, f"{HOST}/data.json", decl, present=False), page]
    f = judge_rule("RULE-B1-v3", obs, params)
    assert f.verdict == "error", f.reason
    assert "declared inventory not observed" in f.reason


# --------------------------------------------------------------------------- B3, D1, F4

def test_b3_judging_the_first_of_several_methodology_links_is_error(params):
    page = _obs(params, "B3", PAGE, parsed={
        "content_type": "text/html",
        "links": [{"href": f"{HOST}/methodology.pdf", "text": "Methodology"},
                  {"href": f"{HOST}/methodology.html", "text": "Methodology (HTML)"}]})
    pdf = _obs(params, "B3", f"{HOST}/methodology.pdf", ctype="application/pdf",
               parsed={"content_type": "application/pdf"})
    f = judge_rule("RULE-B3-v4", [page, pdf], params)
    assert f.verdict == "error"
    assert "1 of 2 methodology link(s) on the product page followed" in f.reason
    assert judge_rule("RULE-B3-v3", [page, pdf], params).verdict == "fail"


def test_b3_with_its_one_candidate_followed_still_fails(params):
    page = _obs(params, "B3", PAGE, parsed={
        "content_type": "text/html",
        "links": [{"href": f"{HOST}/methodology.pdf", "text": "Methodology"}]})
    pdf = _obs(params, "B3", f"{HOST}/methodology.pdf", ctype="application/pdf",
               parsed={"content_type": "application/pdf"})
    f = judge_rule("RULE-B3-v4", [page, pdf], params)
    assert f.verdict == "fail" and "PDF-only" in f.reason


def test_d1_without_a_declared_terms_endpoint_is_error(params):
    decl = _decl(field="api_terms", api_base=None,
                 unresolved=[{"role": "api_base", "why": "none cited"}])
    obs = [_obs(params, "D1", PAGE, parsed={"keys": [], "declared": decl}),
           _obs(params, "D1", f"{HOST}/terms", status=404, ctype="text/plain",
                parsed={"probe": "terms", "terms_text": "", "declared": decl},
                error_class="http_4xx")]
    f = judge_rule("RULE-D1-v4", obs, params)
    assert f.verdict == "error"
    assert "the API's terms endpoint spec:D1 names cannot be located" in f.reason
    assert judge_rule("RULE-D1-v3", obs, params).verdict == "fail"


def test_d1_with_its_declared_terms_endpoint_read_fails(params):
    decl = _decl(field="api_terms", api_base={"url": "https://api.example.gov",
                                              "terms_url": "https://api.example.gov/terms",
                                              "read_from": {"page": "https://x"}})
    obs = [_obs(params, "D1", PAGE, parsed={"keys": [], "declared": decl}),
           _obs(params, "D1", "https://api.example.gov/terms", status=404, ctype="text/plain",
                parsed={"probe": "terms", "terms_text": "", "declared": decl},
                error_class="http_4xx")]
    f = judge_rule("RULE-D1-v4", obs, params)
    assert f.verdict == "fail", f.reason


def test_f4_over_guessed_paths_only_is_error(params):
    decl = _decl(field="changelog_urls", changelog_urls=[])
    obs = [_obs(params, "F4", f"{HOST}{p}", status=404, ctype="text/plain",
                parsed={"declared": decl}, error_class="http_4xx")
           for p in params["f4_changelog"]["paths"]]
    f = judge_rule("RULE-F4-v4", obs, params)
    assert f.verdict == "error"
    assert "no changelog or release-notes location is declared" in f.reason
    assert judge_rule("RULE-F4-v3", obs, params).verdict == "fail"


def test_f4_with_its_declared_changelog_observed_fails(params):
    decl = _decl(field="changelog_urls",
                 changelog_urls=[{"url": f"{HOST}/releases.json", "read_from": {"page": "x"}}])
    obs = [_obs(params, "F4", f"{HOST}/releases.json", status=404, ctype="text/plain",
                parsed={"declared": decl}, error_class="http_4xx")]
    assert judge_rule("RULE-F4-v4", obs, params).verdict == "fail"


# --------------------------------------------------------------------------- the collector

class _HeadEverything:
    """Allows every URL and answers every HEAD with 200 text/html. Counts the HEADs."""

    def __init__(self):
        self.heads = []

    def allowed(self, url):
        return True

    def raw_head(self, url):
        self.heads.append(url)
        return {"status": 200, "headers": {"content-type": "text/html"}, "body": b"",
                "elapsed_ms": 1, "final_url": url, "method": "HEAD"}


def test_sixty_on_host_links_and_cap_25_write_25_probed_and_35_unprobed_in_rank_order(params):
    assert params["link_probe"]["max_links_probed"] == 25
    # 55 navigation links first in document order, then five data-like ones at the END: two
    # archives, one CSV, and two that carry a token only.
    nav = [{"href": f"{HOST}/nav/{i}.html", "text": f"Section {i}"} for i in range(55)]
    data = [{"href": f"{HOST}/files/all.zip", "text": "Everything"},
            {"href": f"{HOST}/files/est.csv", "text": "Estimates"},
            {"href": f"{HOST}/files/old.tar.gz", "text": "Archive"},
            {"href": f"{HOST}/download/page.html", "text": "Get it"},
            {"href": f"{HOST}/about.html", "text": "Data notes"}]
    found = nav + data + [{"href": "https://elsewhere.example.org/x", "text": "out"}]
    f = _HeadEverything()
    obs = links_collector.probe(f, "link_probe", DOC, found, params, page_url=PAGE)
    probed = [o for o in obs if (o.parsed or {}).get("probe") == "link"
              and o.error_class not in ("off_host", "unprobed_over_cap")]
    unprobed = [o for o in obs if o.error_class == "unprobed_over_cap"]
    off = [o for o in obs if o.error_class == "off_host"]
    assert (len(probed), len(unprobed), len(off)) == (25, 35, 1)
    assert len(f.heads) == 25, "the cap bounds requests"
    # Data-like first: the three extension matches (tier 0), then the two token matches (tier 1),
    # each tier in document order, then navigation.
    ranked = [o.target_url for o in sorted(probed + unprobed, key=lambda o: o.parsed["rank"])]
    assert ranked[:5] == [f"{HOST}/files/all.zip", f"{HOST}/files/est.csv",
                          f"{HOST}/files/old.tar.gz", f"{HOST}/download/page.html",
                          f"{HOST}/about.html"]
    assert [o.parsed["rank"] for o in unprobed] == list(range(26, 61))
    assert all(o.request.get("fetched") is False for o in unprobed)
    block = links_collector.account(obs, found, PAGE, params)
    assert {k: block[k] for k in ("on_host", "probed", "unprobed", "cap", "off_host")} == {
        "on_host": 60, "probed": 25, "unprobed": 35, "cap": 25, "off_host": 1}


# --------------------------------------------------------------------------- manners

def test_a_declared_api_base_host_is_admitted_for_that_body_and_leg_only(params):
    """A synthetic body whose API lives OFF its site, because the real CENSUS one does not:
    `api.census.gov` domain-matches `census.gov` (DD-063), so it was never refused."""
    mine = declarations.validate({"scheme": 1, "bodies": {"X": {
        "api_base": {"url": "https://api.example-data.org/v1",
                     "read_from": {"page": "https://stats.example.gov/developers"}}}}})
    decl = declarations.for_body(mine, "X")
    other = declarations.for_body(declarations.load(), "BEA")
    api = "https://api.example-data.org/v1/openapi.json"
    for leg in ("A2", "link_probe", "A1", "A3", "A9"):
        assert manners.on_roster_host(api, PAGE, params,
                                      declarations.admitted_hosts(decl, leg, params)), leg
    # Refused for every other leg of the same body ...
    for leg in ("D4", "B1", "B3", "D1", "F4", "A4", "A5", "A8"):
        assert not manners.on_roster_host(api, PAGE, params,
                                          declarations.admitted_hosts(decl, leg, params)), leg
    # ... and for the same leg of another body.
    assert not manners.on_roster_host(api, "https://www.bea.gov/data", params,
                                      declarations.admitted_hosts(other, "A2", params))


def test_a_third_host_is_still_refused(params):
    census = declarations.for_body(declarations.load(), "CENSUS")
    admitted = (declarations.admitted_hosts(census, "A2", params)
                | declarations.admitted_hosts(census, "D4", params))
    assert not manners.on_roster_host("https://www.example.org/x",
                                      "https://www.census.gov/acs", params, admitted)


def test_an_inventory_host_is_admitted_for_the_d4_family_only(params):
    census = declarations.for_body(declarations.load(), "CENSUS")
    url, surface = "https://www.commerce.gov/data.json", "https://www.census.gov/acs"
    for leg in ("D4", "B1", "B4", "D3", "G4"):
        assert manners.on_roster_host(url, surface, params,
                                      declarations.admitted_hosts(census, leg, params)), leg
    assert not manners.on_roster_host(url, surface, params,
                                      declarations.admitted_hosts(census, "A2", params))


# --------------------------------------------------------------------------- declarations

def test_the_declarations_load_and_every_entry_names_its_page():
    block = declarations.load()
    assert len(block["bodies"]) == 16
    assert block["bodies"]["CENSUS"]["api_base"]["url"] == "https://api.census.gov/data"
    for code, b in block["bodies"].items():
        for e in b.get("inventory_urls") or []:
            assert e["read_from"]["page"], (code, e)


def test_a_malformed_declaration_is_refused():
    with pytest.raises(declarations.DeclarationError):
        declarations.validate({"scheme": 1, "bodies": {"X": {"api_base": {"url": "nope"}}}})
    with pytest.raises(declarations.DeclarationError):
        declarations.validate({"scheme": 1, "bodies": {"X": {"inventory_urls": [
            {"url": "https://x.gov/data.json", "kind": "data_json", "role": "own_host"}]}}})


# --------------------------------------------------------------------------- prescriptions (7)

def _tp():
    sys.path.insert(0, str(REPO / "scripts"))
    import tag_prescriptions as tp
    return tp


def test_expose_an_api_is_withdrawn_for_a_body_that_declares_its_api_base():
    sys.path.insert(0, str(REPO / "scripts"))
    import prescriptions as P
    tp = _tp()
    expose = next(a for a in tp.ACTIONS if a["slug"] == "a2-expose-an-api-and-publish-its-"
                                                         "description")
    assert expose["withdrawn_when_declared"] == "api_base"
    acts = [{"id": "act:x", "leg": "A2", "withdrawn_when_declared": "api_base"},
            {"id": "act:y", "leg": "A2"}]
    assert [a["id"] for a in P.applicable(acts, "CENSUS")] == ["act:y"]
    assert [a["id"] for a in P.applicable(acts, "BEA")] == ["act:x", "act:y"]
    assert [a["id"] for a in P.applicable(acts, "NOT-A-BODY")] == ["act:x", "act:y"]


def test_every_outcome_fragment_is_in_its_current_rule_and_in_no_error_sentence():
    """Decision 7: an `error` prescribes nothing. No sentence an `error` branch of a
    generation-14 rule writes may carry a fragment that names a failing outcome."""
    tp = _tp()
    for leg, outs in tp.OUTCOMES.items():
        rid, src = tp.rule_module_source(leg)
        for name, frag in outs.items():
            assert frag in src, (leg, name, frag)
    errors = ["absence not established: ", "no documented API base declared for this body; "
              "guessed paths do not establish absence", "documented API base declared and not "
              "probed: ", "declared inventory not observed: ", "not declared (",
              "no changelog or release-notes location is declared for this body",
              "the API's terms endpoint spec:D1 names"]
    for leg, outs in tp.OUTCOMES.items():
        for frag in outs.values():
            assert not any(frag in e for e in errors), (leg, frag)
