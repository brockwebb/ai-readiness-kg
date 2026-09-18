"""Generation 12: the schema.org and robots structured-field rules — `RULE-B1-v2` (B1 whole),
`RULE-B2-v1`, `RULE-B5-v1` and `RULE-D2-v1`.

`cc_tasks/2026-09-18_schema_field_rules.md`, taking decisions 1 to 4 of
`cc_tasks/2026-09-18_dcat_field_rules.md` unchanged: each rule is exercised on a fixture that
passes, one fixture per failing outcome, and the retained evidence of the cycle of record, and
two runs over the same bytes give the same Finding ids.

**No network.** A6 observations are built from `extruct`-shaped markup dicts, A4 observations
from robots.txt bytes through the same parser the runner calls (`v2clauses.content_signals`),
and D4 observations as `tests/test_dcat_field_rules.py` builds them.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from scan import load_params                                          # noqa: E402
from scan.collectors import v2clauses                                 # noqa: E402
from scan.model import Observation                                    # noqa: E402
from scan.rules import (BODY_LEGS, CURRENT, GENERATIONS, REGISTRY,    # noqa: E402
                        V12, body_groups, claim_of, consumes, measures, scope,
                        judge as judge_rule)

RULES = {"B1": "RULE-B1-v2", "B2": "RULE-B2-v1", "B5": "RULE-B5-v1", "D2": "RULE-D2-v1"}
HOST = "stats.example.gov"
PRODUCT = f"https://{HOST}/products/estimates.html"


@pytest.fixture(scope="module")
def params():
    return load_params()


# ------------------------------------------------------------------ builders

def _term(name="Occupied housing unit", code="HU-OCC",
          tset="https://stats.example.gov/glossary", description="A unit that is lived in."):
    t = {"@type": "DefinedTerm", "name": name}
    if code is not None:
        t["termCode"] = code
    if tset is not None:
        t["inDefinedTermSet"] = tset
    if description is not None:
        t["description"] = description
    return t


def _dataset(*terms, variables=True) -> dict:
    d = {"@context": "https://schema.org", "@type": "Dataset", "name": "Estimates",
         "description": "d"}
    if variables:
        d["variableMeasured"] = [{"@type": "PropertyValue", "name": "Estimate",
                                  **({"measurementTechnique": list(terms)} if terms else {})}]
    elif terms:
        d["measurementTechnique"] = list(terms)
    return d


def _raw(*jsonld, rdfa=None) -> dict:
    return {"json-ld": list(jsonld), "microdata": [], "rdfa": list(rdfa or [])}


def _a6(params, raw=None, url=PRODUCT, doc="scan-fixture", status=200, error_class=None,
        content_type="text/html") -> Observation:
    parsed = {"syntaxes": {}, "types": [], "keys": [], "content_type": content_type}
    if raw is not None:
        parsed["raw"] = raw
    body = json.dumps(raw).encode() if raw is not None else b""
    return Observation.make("A6", "A6", doc, url, "structured_data", "0.1.0", params,
                            {"method": "GET", "url": url},
                            {"status": status, "headers": {},
                             "body_sha256": hashlib.sha256(body).hexdigest(), "body_path": None,
                             "bytes": len(body), "elapsed_ms": 0},
                            parsed=parsed, error_class=error_class,
                            captured_at="2026-09-18T00:00:00Z")


def _a4(params, robots: str | None, status=200, error_class=None, url=PRODUCT,
        enrich=True) -> Observation:
    present = robots is not None and status < 400 and error_class is None
    parsed = {"present": present, "per_ua": {}, "robots_status": status, "probe_url": url}
    if present and enrich:
        parsed["content_signal"] = v2clauses.content_signals(robots.encode(), url, params)
    body = (robots or "").encode()
    return Observation.make("A4", "A4", "scan-fixture", f"https://{HOST}/robots.txt", "robots",
                            "0.1.0", params, {"method": "GET", "url": f"https://{HOST}/robots.txt"},
                            {"status": status, "headers": {},
                             "body_sha256": hashlib.sha256(body).hexdigest(), "body_path": None,
                             "bytes": len(body), "elapsed_ms": 0},
                            parsed=parsed, error_class=error_class,
                            captured_at="2026-09-18T00:00:00Z")


def _d4(params, carries_dictionary: bool) -> Observation:
    """A served catalog whose one product record does or does not link a data dictionary."""
    rec = {"title": "Estimates", "identifier": PRODUCT, "distribution": [
        {"downloadURL": f"https://{HOST}/e.csv", "mediaType": "text/csv",
         **({"describedBy": f"https://{HOST}/dict.json"} if carries_dictionary else {})}]}
    cat = {"dataset": [rec]}
    parsed = {"present": True,
              "dcat_fields": v2clauses.dcat_record_fields(cat, PRODUCT, params)}
    body = json.dumps(cat).encode()
    return Observation.make("D4", "D4", "scan-fixture", f"https://{HOST}/data.json", "dcat",
                            "0.1.0", params, {"method": "GET", "url": f"https://{HOST}/data.json"},
                            {"status": 200, "headers": {},
                             "body_sha256": hashlib.sha256(body).hexdigest(), "body_path": None,
                             "bytes": len(body), "elapsed_ms": 0},
                            parsed=parsed, captured_at="2026-09-18T00:00:00Z")


def _d4_absent(params) -> Observation:
    return Observation.make("D4", "D4", "scan-fixture", f"https://{HOST}/data.json", "dcat",
                            "0.1.0", params, {"method": "GET", "url": f"https://{HOST}/data.json"},
                            {"status": 404, "headers": {}, "body_sha256": None,
                             "body_path": None, "bytes": 0, "elapsed_ms": 0},
                            parsed={"present": False}, error_class="http_4xx",
                            captured_at="2026-09-18T00:00:00Z")


def _products(params, *raws) -> list:
    """One A6 observation per product surface of one body, each on its own path."""
    return [_a6(params, raw, url=f"https://{HOST}/p{i}/index.html", doc=f"scan-p{i}")
            for i, raw in enumerate(raws)]


def _j(leg, obs, params):
    return judge_rule(RULES[leg], obs if isinstance(obs, list) else [obs], params)


# ------------------------------------------------------------------ registration

def test_generation_twelve_is_registered_and_current():
    # Generation 13 (`RULE-D4-v3`, `cc_tasks/2026-09-18_manners_status_and_b5_control.md`
    # decision 4) followed; twelve is the one before it.
    assert GENERATIONS[11] is V12
    assert {m.RULE_ID for m in V12} == set(RULES.values())
    for leg, rid in RULES.items():
        assert CURRENT[leg] == rid and REGISTRY[rid].LEG == leg
    # B1-v1 is shipped and stays: every Finding recorded under it must keep re-deriving.
    assert "RULE-B1-v1" in REGISTRY


def test_each_rule_declares_what_it_reads_claims_and_is_about():
    assert consumes("RULE-B1-v2") == ("D4", "A6")
    assert consumes("RULE-B2-v1") == ("A6",)
    assert consumes("RULE-B5-v1") == ("A6",)
    assert consumes("RULE-D2-v1") == ("A4",)
    for rid in RULES.values():
        assert claim_of(rid) == "absence"
    assert measures("RULE-B5-v1") == "host", "decision 5: the body, at host level"
    for rid in ("RULE-B1-v2", "RULE-B2-v1", "RULE-D2-v1"):
        assert measures(rid) == "product"


def test_b5_alone_is_judged_per_body(params):
    assert BODY_LEGS == ("B5",)
    assert scope("RULE-B5-v1") == "body"
    assert all(scope(r) == "surface" for r in REGISTRY if r != "RULE-B5-v1")
    from scan.run import CONTROL_LEGS
    assert "B5" not in CONTROL_LEGS
    assert {"B1", "B2", "D2"} <= set(CONTROL_LEGS)


def test_the_field_legs_collect_nothing_of_their_own(params):
    from scan.runner import collect_leg
    for leg in ("B1", "B2", "B5", "D2"):
        assert collect_leg({"leg": leg}, {"doc_id": "x", "url": PRODUCT}, params,
                           fetcher=object()) == []


def test_b5_is_the_one_rule_with_an_unmeasured_until():
    assert REGISTRY["RULE-B5-v1"].UNMEASURED_UNTIL == "second cycle with term codes"


# ------------------------------------------------------------------ B2

def test_b2_passes_a_complete_term_linked_from_a_variable(params):
    f = _j("B2", _a6(params, _raw(_dataset(_term()))), params)
    assert f.verdict == "pass", f.reason
    assert "not measured:" in f.reason and "versioned" in f.reason


def test_b2_reads_rdfa_expanded_markup_linked_by_id(params):
    """RDFa arrives EXPANDED from `extruct`: full IRIs, `@value`s and `@id` links."""
    S = "http://schema.org/"
    rdfa = [{"@id": "_:ds", "@type": [f"{S}Dataset"], f"{S}name": [{"@value": "E"}],
             f"{S}measurementTechnique": [{"@id": "_:t"}]},
            {"@id": "_:t", "@type": [f"{S}DefinedTerm"], f"{S}name": [{"@value": "Unit"}],
             f"{S}termCode": [{"@value": "U1"}],
             f"{S}inDefinedTermSet": [{"@id": "https://stats.example.gov/glossary"}],
             f"{S}description": [{"@value": "A unit."}]}]
    assert _j("B2", _a6(params, _raw(rdfa=rdfa)), params).verdict == "pass"


def test_a_foreign_vocabulary_is_not_read_as_schema_org():
    from scan.rules import _schema_terms as s
    assert s.local("http://xmlns.com/foaf/0.1/Image") is None
    assert s.local("schema:termCode") == "termCode"
    assert s.local("https://schema.org/DefinedTerm") == "DefinedTerm"


def _b2_failing(params) -> dict:
    glossary = {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "Glossary",
                "hasDefinedTerm": [_term()]}
    return {
        ("B2", "no_defined_terms"): _a6(params, _raw(_dataset())),
        ("B2", "terms_not_linked"): _a6(params, _raw(_dataset(), glossary)),
        ("B2", "terms_incomplete"): _a6(params, _raw(_dataset(_term(code=None)))),
    }


# ------------------------------------------------------------------ B1 v2

def test_b1_passes_on_either_half(params):
    page_with = _a6(params, _raw(_dataset(_term())))
    page_without = _a6(params, _raw(_dataset(variables=False)))
    assert _j("B1", [_d4(params, True), page_without], params).verdict == "pass"
    f = _j("B1", [_d4_absent(params), page_with], params)
    assert f.verdict == "pass" and "`variableMeasured`" in f.reason


def test_b1_passes_on_a_catalog_even_when_the_page_is_blind(params):
    """Existence is established by what was read; a blind half cannot unfind it."""
    blind = _a6(params, None, status=None, error_class="connection_reset")
    assert _j("B1", [_d4(params, True), blind], params).verdict == "pass"


def test_b1_is_error_when_an_unpassed_half_is_blind(params):
    blind = _a6(params, None, status=None, error_class="connection_reset")
    assert _j("B1", [_d4_absent(params), blind], params).verdict == "error"


def test_b1_on_a_non_html_surface_is_the_catalog_half(params):
    csv = _a6(params, None, content_type="text/csv")
    assert _j("B1", [_d4(params, True), csv], params).verdict == "pass"
    assert _j("B1", [_d4(params, False), csv], params).verdict == "fail"


def _b1_failing(params) -> dict:
    no_vars = _a6(params, _raw(_dataset(variables=False)))
    return {
        ("B1", "no_product_record"): [_d4_absent(params), no_vars],
        ("B1", "no_data_dictionary"): [_d4(params, False), no_vars],
        ("B1", "no_variable_measured"): [_d4(params, False), _a6(params, _raw())],
    }


def test_a_b1_fail_names_both_halves(params):
    import tag_prescriptions as tp
    f = _j("B1", [_d4(params, False), _a6(params, _raw(_dataset(variables=False)))], params)
    assert f.verdict == "fail"
    assert tp.OUTCOMES["B1"]["no_data_dictionary"] in f.reason
    assert tp.OUTCOMES["B1"]["no_variable_measured"] in f.reason


# ------------------------------------------------------------------ D2

SIGNAL = "User-agent: *\nContent-Signal: ai-train=no, search=yes, ai-input=yes\nAllow: /\n"


def test_d2_passes_when_both_uses_are_declared_yes_or_no(params):
    f = _j("D2", _a4(params, SIGNAL), params)
    assert f.verdict == "pass", f.reason
    assert "ai-train=no" in f.reason and "ai-input=yes" in f.reason


def test_d2_reads_a_path_scoped_directive_only_where_it_applies(params):
    scoped = ("User-agent: *\nContent-Signal: /products/ ai-train=no, ai-input=no\n"
              "Content-Signal: /blog/ ai-train=yes, ai-input=yes\n")
    assert _j("D2", _a4(params, scoped), params).verdict == "pass"
    elsewhere = "User-agent: *\nContent-Signal: /blog/ ai-train=no, ai-input=no\n"
    f = _j("D2", _a4(params, elsewhere), params)
    assert f.verdict == "fail" and "scoped to other paths" in f.reason


def test_the_content_signal_parser_matches_the_policys_own_examples(params):
    """The three shapes `cloudflare-content-signals-policy` shows: plain, path-scoped, and in a
    per-agent group. Comments are stripped; the directive name is case-insensitive."""
    body = (b"User-Agent: googlebot\ncontent-signal: ai-train=no, search=yes, ai-input=no  # c\n"
            b"User-Agent: *\nContent-Signal: /about ai-train=yes, search=yes, ai-input=yes\n")
    b = v2clauses.content_signals(body, "https://h.gov/about/team", params)
    assert b["directives"] == [
        {"path": None, "signals": {"ai-input": "no", "ai-train": "no", "search": "yes"},
         "malformed": [], "applies": True},
        {"path": "/about", "signals": {"ai-input": "yes", "ai-train": "yes", "search": "yes"},
         "malformed": [], "applies": True}]


def test_d2_before_the_block_existed_is_error(params):
    f = _j("D2", _a4(params, SIGNAL, enrich=False), params)
    assert f.verdict == "error" and "before `content_signal` existed" in f.reason


def test_d2_blind_robots_is_error(params):
    assert _j("D2", _a4(params, None, status=None, error_class="connection_reset"),
              params).verdict == "error"


def _d2_failing(params) -> dict:
    return {
        ("D2", "no_content_signal"): _a4(params, "User-agent: *\nAllow: /\n"),
        ("D2", "unknown_category"): _a4(
            params, "User-agent: *\nContent-Signal: ai-train=no, ai-input=no, ai-sell=no\n"),
    }


def test_d2_one_use_undeclared_is_not_addressed(params):
    import tag_prescriptions as tp
    for robots in (None, "User-agent: *\nContent-Signal: search=yes\n",
                   "User-agent: *\nContent-Signal: ai-train=no, search=yes\n"):
        f = _j("D2", _a4(params, robots, status=404 if robots is None else 200), params)
        assert f.verdict == "fail", robots
        assert tp.OUTCOMES["D2"]["no_content_signal"] in f.reason


# ------------------------------------------------------------------ B5

def test_b5_passes_one_identifier_per_concept_across_products(params):
    obs = _products(params, _raw(_dataset(_term())), _raw(_dataset(_term(), _term("Vacant unit",
                                                                                "HU-VAC"))))
    f = _j("B5", obs, params)
    assert f.verdict == "pass", f.reason
    assert f.target_doc_id == f"host:{HOST}"
    assert sorted(f.evidence) == sorted(o.obs_id for o in obs)
    assert "cross-vintage" in f.reason


def test_b5_compares_names_case_and_space_insensitively(params):
    obs = _products(params, _raw(_dataset(_term("Occupied  Housing Unit"))),
                    _raw(_dataset(_term("occupied housing unit"))))
    assert _j("B5", obs, params).verdict == "pass"


def test_b5_nothing_to_compare_is_not_applicable(params):
    one = _products(params, _raw(_dataset(_term())))
    assert _j("B5", one, params).verdict == "not_applicable"
    disjoint = _products(params, _raw(_dataset(_term())),
                         _raw(_dataset(_term("Vacant unit", "HU-VAC"))))
    assert _j("B5", disjoint, params).verdict == "not_applicable"


def test_b5_no_codes_with_a_blind_product_is_error_not_fail(params):
    obs = _products(params, _raw(_dataset())) + [
        _a6(params, None, url=f"https://{HOST}/p9/", doc="scan-p9", status=None,
            error_class="connection_reset")]
    f = _j("B5", obs, params)
    assert f.verdict == "error" and f.blind_candidates == 1


def test_b5_all_blind_is_error(params):
    obs = [_a6(params, None, url=f"https://{HOST}/p{i}/", doc=f"scan-p{i}", status=None,
               error_class="connection_reset") for i in range(2)]
    assert _j("B5", obs, params).verdict == "error"


def _b5_failing(params) -> dict:
    return {
        ("B5", "no_term_codes"): _products(params, _raw(_dataset(_term(code=None))),
                                           _raw(_dataset())),
        ("B5", "codes_without_set"): _products(params, _raw(_dataset(_term(tset=None))),
                                               _raw(_dataset(_term()))),
        ("B5", "codes_not_shared_across_products"): _products(
            params, _raw(_dataset(_term())), _raw(_dataset(_term(code="OCC-1")))),
    }


def test_body_groups_takes_product_surfaces_of_one_host_and_nothing_else(params):
    prod = _products(params, _raw(), _raw())
    home = _a6(params, _raw(), url=f"https://{HOST}/", doc=f"home:{HOST}")
    control = _a6(params, _raw(), url="http://127.0.0.1:9/index.html", doc="control:passes_all")
    other = _a6(params, _raw(), url="https://other.example.gov/x", doc="scan-other")
    d4 = _d4(params, True)
    groups = body_groups("RULE-B5-v1", prod + [home, control, other, d4], params)
    assert list(groups) == ["other.example.gov", HOST]
    assert groups[HOST] == prod


def test_a_cycle_judges_b5_once_per_body_and_rederives_it(params):
    """`run.judge_bodies` and `rederive.rederive` group through `rules.body_groups`: a payload
    built from the first re-derives byte-identically, and a per-surface judgement of B5 appears
    in neither."""
    from scan.model import params_hash
    from scan.run import judge_bodies
    import scan.rederive as rd
    obs = _products(params, _raw(_dataset(_term())), _raw(_dataset(_term())))
    sp = {"B5": {"leg": "B5"}}
    found = judge_bodies(sp, params, obs)
    assert [f.leg for f in found] == ["B5"] and found[0].verdict == "pass"
    payload = {"params_hash": params_hash(params), "findings_detail": [found[0].to_dict()],
               "observations_detail": [o.to_dict() for o in obs]}
    out = rd.rederive(payload, params)
    assert out["identical"], out


# ------------------------------------------------------------------ every outcome, one fixture

def _all_failing(params) -> dict:
    return {**_b1_failing(params), **_b2_failing(params), **_b5_failing(params),
            **_d2_failing(params)}


def test_every_failing_fixture_fails_with_its_outcomes_fragment(params):
    import tag_prescriptions as tp
    fixtures = _all_failing(params)
    for (leg, outcome), o in fixtures.items():
        f = _j(leg, o, params)
        assert f.verdict == "fail", (leg, outcome, f.reason)
        assert tp.OUTCOMES[leg][outcome] in f.reason, (leg, outcome, f.reason)
    named = {(leg, o) for leg in ("B2", "B5", "D2") for o in tp.OUTCOMES[leg]}
    named |= {("B1", "no_variable_measured"), ("B1", "no_product_record"),
              ("B1", "no_data_dictionary")}
    assert named == set(fixtures), "an outcome with no fixture, or a fixture with no outcome"
    assert set(tp.OUTCOMES["B1"]) == {"no_product_record", "no_data_dictionary",
                                      "no_variable_measured"}


def test_two_runs_over_the_same_bytes_give_the_same_finding_ids(params):
    for (leg, _o), o in _all_failing(params).items():
        a = _j(leg, o, params).finding_id
        b = _j(leg, copy.deepcopy(o), params).finding_id
        assert a == b, leg


# ------------------------------------------------------------------ the control fixture page

def test_the_passing_control_page_passes_b1_b2_and_its_robots_passes_d2(params):
    """`passes_all`'s bytes, through `extruct` and the robots parser, pass the new legs — the
    derivation `params.e5_control` records for them, checked here without a server."""
    import extruct
    fx = REPO / "assessment/harness/scan/fixtures/passes_all"
    html = (fx / "index.html").read_text().replace("HOSTPORT", "127.0.0.1:9")
    raw = extruct.extract(html, base_url="http://127.0.0.1:9/index.html",
                          syntaxes=params["a6_markup"]["syntaxes"], uniform=True)
    page = _a6(params, raw, url="http://127.0.0.1:9/index.html")
    assert _j("B2", page, params).verdict == "pass"
    assert _j("B1", [_d4_absent(params), page], params).verdict == "pass"
    for name in ("passes_all", "robots_forbids_product", "sitemap_on_sibling",
                 "refuses_identified_client"):
        robots = (REPO / f"assessment/harness/scan/fixtures/{name}/robots.txt").read_text()
        assert _j("D2", _a4(params, robots, url="http://127.0.0.1:9/index.html"),
                  params).verdict == "pass", name


# ------------------------------------------------------------------ the retained evidence

def test_the_retained_evidence_of_the_cycle_of_record_judges_deterministically():
    """The third leg of decision 3. The distribution is in the RESULT §1 and is not published;
    this pins it so a change to a rule, a reader or the retained evidence is seen."""
    import exercise_schema_field_rules as ex
    out = ex.exercise()
    assert out["deterministic"] is True
    assert out["robots_bodies_missing"] == []
    assert out["distribution"] == ex.EXPECTED_DISTRIBUTION
