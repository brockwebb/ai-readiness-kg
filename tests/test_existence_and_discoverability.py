"""Generation 16 (existence) and the discoverability candidate A13, on synthetic Observations, and
declarations scheme 2.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decisions 3 and 5,
DN-013-R1. Existence legs read only recorded or seeded locations and say `fail` only over a
complete seeded search; A13 says whether a machine starting from the product page reaches what
exists. Live evidence is the task's part 2; these fix the rules' behaviour on every branch first.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import declarations, load_params                            # noqa: E402
from scan.model import Observation                                     # noqa: E402
from scan.rules import (CANDIDATE_LEGS, CURRENT, GENERATIONS, REGISTRY,  # noqa: E402
                        claim_of)
from scan.rules import judge as judge_rule                             # noqa: E402
from scan.rules import _existence, _scope, rule_a13                    # noqa: E402

HOST = "https://stats.example.gov"
PAGE = f"{HOST}/products/estimates.html"
API = "https://api.stats.example.gov/v2"
TERMS = f"{HOST}/developers/terms.html"
CHANGELOG = f"{HOST}/developers/changelog.json"
INVENTORY = f"{HOST}/data.json"
DEPT = "https://www.department.example.gov/data.json"
DOC = "flagship:stats.example.gov/products/estimates.html"
ALL = list(declarations.SEED_SOURCES)
GEN16 = ("RULE-A2-v6", "RULE-B1-v4", "RULE-B4-v3", "RULE-D1-v6", "RULE-D3-v3", "RULE-D4-v5",
         "RULE-F4-v5", "RULE-G4-v3")


@pytest.fixture(scope="module")
def params():
    return load_params()


def _obs(params, leg, url, *, status=200, ctype="text/html", parsed=None, error_class=None,
         headers=None):
    h = {"content-type": ctype, **(headers or {})}
    return Observation.make(leg, leg, DOC, url, "http", "0.1.0", params,
                            {"method": "GET", "url": url},
                            {"status": status, "headers": h,
                             "body_sha256": None if status is None else "0" * 64,
                             "body_path": None, "bytes": 1 if status else 0, "elapsed_ms": 1},
                            parsed=parsed, error_class=error_class)


def _block(field, searched=None, scheme=2, **kw):
    """A `declared` block as `declarations.record` writes it for one field."""
    out = {"scheme": scheme, "body": "X", "field": field, "unresolved": [], **kw}
    if scheme >= 2:
        out["searched"] = searched if searched is not None else {}
    return out


def _complete(*objs):
    return {o: list(ALL) for o in objs}


# --------------------------------------------------------------------------- registry, schemes

def test_generation_sixteen_is_current_and_every_predecessor_stays(params):
    assert [m.RULE_ID for m in GENERATIONS[15]] == list(GEN16)
    for rid in GEN16:
        assert CURRENT[REGISTRY[rid].LEG] == rid
        assert claim_of(rid) == "absence", rid
    for rid in ("RULE-A2-v5", "RULE-D1-v5", "RULE-F4-v4", "RULE-D4-v4", "RULE-B1-v3",
                "RULE-B4-v2", "RULE-D3-v2", "RULE-G4-v2"):
        assert rid in REGISTRY
    assert CURRENT["A13"] == "RULE-A13-v1" and "A13" in CANDIDATE_LEGS
    assert "A13" in params["link_probe"]["legs_served"]


def test_the_rules_restate_the_writer_constants(params):
    assert tuple(params["existence"]["seed_sources"]) == declarations.SEED_SOURCES
    assert set(_existence.DECLARED_SCHEMES) == set(declarations.SCHEMES)
    assert set(_scope.DECLARED_SCHEMES) == set(declarations.SCHEMES)


def test_no_stored_observation_carries_a_scheme_2_block():
    """Why widening `_scope.declared` to scheme 2 moves no stored Finding: before this task no
    payload carries one."""
    for name in ("scan_2026-10-06_recollect", "scan_2026-09-10"):
        p = json.loads((REPO / "state" / f"{name}.json").read_text(encoding="utf-8"))
        schemes = {(o.get("parsed") or {}).get("declared", {}).get("scheme")
                   for o in p["observations_detail"]
                   if isinstance((o.get("parsed") or {}).get("declared"), dict)}
        assert 2 not in schemes, name


# --------------------------------------------------------------------------- existence: A2

def _api(params, url, version="3.0.3", status=200, searched=None, api=None, **kw):
    parsed = {"api": {"openapi_parsed": version is not None or api == "json",
                      "openapi_version": version, "auth_schemes_declared": [],
                      "auth_headers_seen": [], "rate_limit_headers_seen": [],
                      "rate_limit_declared_in_description": False},
              "declared": _block("api_base", searched, **kw)}
    return _obs(params, "A2", url, status=status, ctype="application/json", parsed=parsed)


def test_a2_a_description_at_a_guessed_path_is_not_existence_evidence(params):
    """The product host's `/openapi.json` serves a description, and nothing is recorded: v5
    passed on it; v6 does not judge from a guess, and with the seed sources unsearched the
    verdict is `error` naming them."""
    o = _api(params, f"{HOST}/openapi.json", api_base=None)
    assert judge_rule("RULE-A2-v5", [_api(params, f"{HOST}/openapi.json", scheme=1,
                                          api_base=None)], params).verdict == "pass"
    f = judge_rule("RULE-A2-v6", [o], params)
    assert f.verdict == "error", f.reason
    assert "seed sources not searched" in f.reason and "model_knowledge" in f.reason


def test_a2_passes_at_the_recorded_base(params):
    rec = {"url": API, "seeded_from": ["model_knowledge:claude-opus-5-5"],
           "status": "verified", "verified_at": "2026-10-10T00:00:00Z"}
    f = judge_rule("RULE-A2-v6", [_api(params, API, api_base=rec)], params)
    assert f.verdict == "pass", f.reason


def test_a2_fails_only_over_a_complete_search(params):
    rec = {"url": API, "read_from": {"page": f"{HOST}/developers"}}
    partial = _api(params, API, version=None, api="json", api_base=rec,
                   searched={"api_base": ["developer_page"]})
    f = judge_rule("RULE-A2-v6", [partial], params)
    assert f.verdict == "error" and "catalog.data.gov" in f.reason, f.reason
    whole = _api(params, API, version=None, api="json", api_base=rec,
                 searched=_complete("api_base"))
    f = judge_rule("RULE-A2-v6", [whole], params)
    assert f.verdict == "fail", f.reason
    assert "the API is present" in f.reason and "does not parse as an API " in f.reason


def test_a2_an_unverified_seed_is_error_naming_it(params):
    rec = {"url": API, "seeded_from": ["api.data.gov:agency listing"], "status": "http_403",
           "verified_at": "2026-10-10T00:00:00Z"}
    guess = _api(params, f"{HOST}/openapi.json", version=None, status=404, api_base=rec,
                 searched=_complete("api_base"))
    f = judge_rule("RULE-A2-v6", [guess], params)
    assert f.verdict == "error" and API in f.reason and "http_403" in f.reason, f.reason


def test_a2_a_seed_that_named_nothing_leaves_a_complete_search_to_fail(params):
    rec = {"url": API, "seeded_from": ["model_knowledge:claude-opus-5-5"],
           "status": "not_the_object", "verified_at": "2026-10-10T00:00:00Z"}
    guess = _api(params, f"{HOST}/openapi.json", version=None, status=404, api_base=rec,
                 searched=_complete("api_base"))
    f = judge_rule("RULE-A2-v6", [guess], params)
    assert f.verdict == "fail", f.reason
    assert "no OpenAPI/JSON API description served at any probed path" in f.reason


# --------------------------------------------------------------------------- existence: F4, D4, D1

def _changelog(params, url, *, ctype="application/json", entries=3, classified=1.0, status=200,
               searched=None, changelog_urls=None):
    parsed = {"content_type": ctype,
              "changelog": {"entries": entries, "classified_fraction": classified,
                            "entries_classified": int(entries * classified)},
              "declared": _block("changelog_urls", searched,
                                 changelog_urls=changelog_urls or [])}
    return _obs(params, "F4", url, status=status, ctype=ctype, parsed=parsed)


def test_f4_a_guessed_changelog_does_not_pass_and_a_recorded_one_does(params):
    guessed = _changelog(params, f"{HOST}/changelog.json")
    assert judge_rule("RULE-F4-v5", [guessed], params).verdict == "error"
    rec = [{"url": CHANGELOG, "seeded_from": ["repo:docs/x.md:1"]}]
    assert judge_rule("RULE-F4-v5", [_changelog(params, CHANGELOG, changelog_urls=rec)],
                      params).verdict == "pass"


def test_f4_nothing_recorded_over_a_complete_search_is_fail(params):
    o = _changelog(params, f"{HOST}/changelog.json", status=404, searched=_complete("changelog"))
    f = judge_rule("RULE-F4-v5", [o], params)
    assert f.verdict == "fail", f.reason
    assert "no changelog or release-notes endpoint served" in f.reason
    assert "no seed source records" in f.reason


def _catalog(params, url, *, records=1, present=True, status=200, searched=None, inv=None,
             scheme=2):
    parsed = {"present": present, "membership": {"records": records},
              "pod": {"validated": True, "conforms": True, "datasets_validated": 1,
                      "datasets_total": 1},
              "declared": _block("inventory_urls", searched, scheme=scheme,
                                 inventory_urls=inv or [], department_is_own_host=False)}
    return _obs(params, "D4", url, status=status, ctype="application/json", parsed=parsed)


def test_d4_the_host_root_catalog_is_not_existence_unless_recorded(params):
    unrecorded = _catalog(params, INVENTORY)
    # v4 judged every catalog the leg observed, so the host root's record passed it.
    assert judge_rule("RULE-D4-v4", [_catalog(params, INVENTORY, scheme=1, inv=[])],
                      params).verdict == "pass"
    f = judge_rule("RULE-D4-v5", [unrecorded], params)
    assert f.verdict == "error", f.reason
    inv = [{"url": INVENTORY, "kind": "data_json", "role": "own_host",
            "seeded_from": ["model_knowledge:claude-opus-5-5"]}]
    assert judge_rule("RULE-D4-v5", [_catalog(params, INVENTORY, inv=inv)], params).verdict \
        == "pass"


def test_d4_absent_from_every_recorded_inventory_over_a_complete_search_is_fail(params):
    inv = [{"url": DEPT, "kind": "data_json", "role": "department",
            "read_from": {"page": PAGE}}]
    o = _catalog(params, DEPT, records=0, inv=inv, searched={"inventory": ["developer_page"]})
    assert judge_rule("RULE-D4-v5", [o], params).verdict == "error"
    o = _catalog(params, DEPT, records=0, inv=inv, searched=_complete("inventory"))
    f = judge_rule("RULE-D4-v5", [o], params)
    assert f.verdict == "fail" and "but the product is not in it" in f.reason, f.reason


def test_d1_no_api_over_a_complete_search_settles_the_terms_source(params):
    page = _obs(params, "D1", PAGE, parsed={"keys": [], "raw": {},
                                            "declared": _block("api_terms",
                                                               _complete("api_base"),
                                                               api_base=None)})
    f = judge_rule("RULE-D1-v6", [page], params)
    assert f.verdict == "fail", f.reason
    page = _obs(params, "D1", PAGE, parsed={"keys": [], "raw": {},
                                            "declared": _block("api_terms", {},
                                                               api_base=None)})
    assert judge_rule("RULE-D1-v6", [page], params).verdict == "error"


# --------------------------------------------------------------------------- A13

def _page(params, links, headers=None, status=200):
    return _obs(params, "link_probe", PAGE, status=status, headers=headers,
                parsed={"links": [{"href": h, "text": ""} for h in links]})


def _world(params, *, links=(), api=True, terms=True, changelog=True, inventory=DEPT,
           catalog_at=None, headers=None):
    searched = _complete("api_base", "api_terms", "changelog", "inventory")
    rec_api = {"url": API, "terms_url": TERMS, "seeded_from": ["model_knowledge:x"]}
    obs = [_page(params, links, headers)]
    obs.append(_obs(params, "A2", API, ctype="application/json", status=200 if api else 404,
                    parsed={"api": {"openapi_parsed": api, "openapi_version": None},
                            "declared": _block("api_base", searched, api_base=rec_api)}))
    obs.append(_obs(params, "D1", TERMS, status=200 if terms else 404,
                    parsed={"probe": "terms", "terms_text": "Terms",
                            "declared": _block("api_terms", searched, api_base=rec_api)}))
    obs.append(_obs(params, "F4", CHANGELOG, status=200 if changelog else 404,
                    parsed={"declared": _block("changelog_urls", searched,
                                               changelog_urls=[{"url": CHANGELOG,
                                                                "seeded_from": ["repo:x:1"]}])}))
    obs.append(_obs(params, "D4", inventory, ctype="application/json",
                    parsed={"present": True,
                            "declared": _block("inventory_urls", searched,
                                               inventory_urls=[{"url": inventory,
                                                                "kind": "data_json",
                                                                "role": "department",
                                                                "seeded_from": ["repo:x:2"]}])}))
    if catalog_at:
        obs.append(_obs(params, "A13", catalog_at[0], ctype=catalog_at[1]))
    return obs


def test_a13_passes_when_everything_that_exists_is_linked(params):
    obs = _world(params, links=[API + "/datasets", TERMS, CHANGELOG, DEPT])
    each = rule_a13.per_object(obs, params)
    assert {k: v["verdict"] for k, v in each.items()} == dict.fromkeys(each, "pass"), each
    assert judge_rule("RULE-A13-v1", obs, params).verdict == "pass"


def test_a13_fails_on_one_unreachable_object_whatever_else_is_unsettled(params):
    # The API is not linked and its convention location was not fetched (`error`); the
    # changelog exists and is not linked (`fail`). The `fail` stands.
    obs = _world(params, links=[TERMS, DEPT])
    each = rule_a13.per_object(obs, params)
    assert each["api"]["verdict"] == "error" and "was not fetched" in each["api"]["reason"]
    assert each["changelog"]["verdict"] == "fail"
    f = judge_rule("RULE-A13-v1", obs, params)
    assert f.verdict == "fail" and "and is not reachable from the " in f.reason


def test_a13_convention_locations(params):
    # The inventory at the host root is reachable by convention; the API through an RFC 9727
    # catalog or a `Link: rel="api-catalog"` header.
    obs = _world(params, links=[TERMS, CHANGELOG], inventory=INVENTORY,
                 catalog_at=(f"{HOST}/.well-known/api-catalog", "application/linkset+json"))
    each = rule_a13.per_object(obs, params)
    assert each["inventory"]["verdict"] == "pass" and "convention" in each["inventory"]["reason"]
    assert each["api"]["verdict"] == "pass" and "RFC 9727" in each["api"]["reason"]
    obs = _world(params, links=[TERMS, CHANGELOG, DEPT],
                 headers={"link": f'<{HOST}/.well-known/api-catalog>; rel="api-catalog"'})
    assert rule_a13.per_object(obs, params)["api"]["verdict"] == "pass"
    # A catalog served as HTML is not a Linkset: the API is not reachable by convention.
    obs = _world(params, links=[TERMS, CHANGELOG, DEPT],
                 catalog_at=(f"{HOST}/.well-known/api-catalog", "text/html"))
    assert rule_a13.per_object(obs, params)["api"]["verdict"] == "fail"


def test_a13_what_does_not_exist_is_not_applicable(params):
    obs = _world(params, links=[], api=False, terms=False, changelog=False)
    obs = [o for o in obs if o.leg != "D4"] + [_obs(
        params, "D4", DEPT, status=404, ctype="text/html",
        parsed={"present": False, "declared": _block(
            "inventory_urls", _complete("inventory"),
            inventory_urls=[{"url": DEPT, "kind": "data_json", "role": "department",
                             "seeded_from": ["repo:x:2"]}])})]
    f = judge_rule("RULE-A13-v1", obs, params)
    assert f.verdict == "not_applicable", f.reason


def test_a13_a_page_not_read_is_error(params):
    obs = _world(params, links=[])
    obs[0] = _page(params, [], status=403)
    assert judge_rule("RULE-A13-v1", obs, params).verdict == "error"


def test_a13_reads_the_page_never_the_probed_links(params):
    """`CONSUMES_PAGE_ONLY`: a blind link probe moves nothing, and the derivation of control
    expectations honours it (`fixture_expectations.leg_probes`)."""
    obs = _world(params, links=[API, TERMS, CHANGELOG, DEPT])
    blind = _obs(params, "link_probe", TERMS, status=None, error_class="connection_reset",
                 parsed={"probe": "link"})
    a = judge_rule("RULE-A13-v1", obs, params)
    b = judge_rule("RULE-A13-v1", obs + [blind], params)
    assert (a.verdict, a.finding_id) == (b.verdict, b.finding_id)
    from scan import fixture_expectations as fx
    got = fx.leg_probes(["A13", "A1"])
    assert "HEAD" not in got["A13"]["dereference_methods"]
    assert "HEAD" in got["A1"]["dereference_methods"]


# --------------------------------------------------------------------------- declarations scheme 2

def _scheme(scheme, body):
    return {"scheme": scheme, "bodies": {"X": body}}


def test_scheme_1_still_loads_and_its_blocks_are_unchanged(params):
    block = declarations.load()
    assert block["scheme"] == 1
    body = declarations.for_body(block, "CENSUS")
    assert "scheme" not in body
    rec = declarations.record(body, "CENSUS", "A2", params)
    assert rec["scheme"] == 1 and "searched" not in rec


def test_scheme_2_accepts_seeded_locations_with_status():
    seeded = {"url": API, "seeded_from": ["model_knowledge:claude-opus-5-5"],
              "status": "seeded_unverified"}
    declarations.validate(_scheme(2, {"api_base": seeded,
                                      "searched": {"api_base": ["model_knowledge"]}}))
    with pytest.raises(declarations.DeclarationError, match="read_from"):
        declarations.validate(_scheme(1, {"api_base": seeded}))
    with pytest.raises(declarations.DeclarationError, match="verified_at"):
        declarations.validate(_scheme(2, {"api_base": dict(seeded, status="verified")}))
    declarations.validate(_scheme(2, {"api_base": dict(seeded, status="http_403",
                                                       verified_at="2026-10-10T00:00:00Z")}))
    with pytest.raises(declarations.DeclarationError, match="status"):
        declarations.validate(_scheme(2, {"api_base": dict(seeded, status="maybe")}))
    with pytest.raises(declarations.DeclarationError, match="seeded_from"):
        declarations.validate(_scheme(2, {"api_base": dict(seeded, seeded_from=["a guess"])}))
    with pytest.raises(declarations.DeclarationError, match="searched"):
        declarations.validate(_scheme(2, {"searched": {"api_base": ["a blog"]}}))
    with pytest.raises(declarations.DeclarationError, match="unknown field"):
        declarations.validate(_scheme(1, {"searched": {"api_base": ["repo"]}}))


def test_scheme_2_record_carries_its_scheme_and_search(params):
    block = _scheme(2, {"api_base": {"url": API, "terms_url": TERMS,
                                     "seeded_from": ["model_knowledge:x"]},
                        "searched": {"api_base": ALL, "api_terms": ["repo"]}})
    body = declarations.for_body(declarations.validate(block), "X")
    rec = declarations.record(body, "X", "D1", params)
    assert rec["scheme"] == 2
    assert rec["searched"] == {"api_terms": ["repo"], "api_base": ALL}


def test_a_generation_15_rule_reads_a_scheme_2_block_as_it_reads_scheme_1(params):
    rec = {"url": API, "read_from": {"page": f"{HOST}/developers"}}
    one = _api(params, API, version=None, api="json", scheme=1, api_base=rec)
    two = _api(params, API, version=None, api="json", api_base=rec, searched={})
    assert judge_rule("RULE-A2-v5", [one], params).verdict == \
        judge_rule("RULE-A2-v5", [two], params).verdict == "fail"


# --------------------------------------------------------------------------- the seed table

SEEDS = REPO / "assessment" / "harness" / "scan" / "seeds" / "known_locations_2026-10-07.yaml"


@pytest.fixture(scope="module")
def seeds():
    import yaml
    return yaml.safe_load(SEEDS.read_text(encoding="utf-8"))


def test_the_seed_table_is_valid_and_covers_every_declared_body(seeds):
    declarations.validate_seed_table(seeds)
    assert set(seeds["bodies"]) == set(declarations.load()["bodies"])
    for b, v in seeds["bodies"].items():
        assert set(v["objects"]) == set(declarations.SEED_OBJECTS), b
        assert "catalog.data.gov" in v["queries"] and "api.data.gov" in v["queries"], b
        for es in v["objects"].values():
            for e in es:
                assert e["status"] == "seeded_unverified", (b, e["url"])
                assert e["host"] in seeds["hosts"], (b, e["url"])


def test_every_seed_names_its_source_and_model_seeds_their_confidence(seeds):
    for v in seeds["bodies"].values():
        for es in v["objects"].values():
            for e in es:
                srcs = {s.split(":", 1)[0] for s in e["seeded_from"]}
                assert srcs <= set(declarations.SEED_SOURCES), e
                if "model_knowledge" in srcs:
                    assert e.get("confidence") in ("high", "medium", "low"), e


def test_the_known_endpoints_dn_013_names_are_seeded(seeds):
    """DN-013 §1 and the task's decision 4 name these; a table without them is the defect."""
    want = {"CENSUS": "https://api.census.gov/data", "BLS": "api.bls.gov/publicAPI/v2",
            "EIA": "https://api.eia.gov/v2", "BEA": "https://apps.bea.gov/api/data",
            "NASS": "https://quickstats.nass.usda.gov/api", "NCHS": "data.cdc.gov",
            "BTS": "data.bts.gov", "ERS": "api.ers.usda.gov"}
    for body, frag in want.items():
        urls = [e["url"] for e in seeds["bodies"][body]["objects"]["api_base"]]
        assert any(frag in u for u in urls), (body, urls)
