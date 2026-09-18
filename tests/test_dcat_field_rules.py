"""Generation 11: the four DCAT-US structured-field rules, B1 (its DCAT half), B4, D3 and G4.

`cc_tasks/2026-09-18_dcat_field_rules.md` decision 3: each rule is exercised three ways before it
is registered — a fixture catalog that passes, one fixture per failing outcome, and the retained
catalogs of the cycle of record — and two runs over the same bytes give the same Finding ids.

**No network.** The fixtures are dicts turned into D4 observations by the same collector
function the runner calls (`v2clauses.dcat_record_fields`), and the retained catalogs are the
bodies the cycle of record stored under `corpus/evidence/scan/`.
"""
from __future__ import annotations

import copy
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
from scan.rules import (CURRENT, GENERATIONS, REGISTRY, V11, claim_of,  # noqa: E402
                        consumes, measures, judge as judge_rule)

LEGS = ("B1", "B4", "D3", "G4")
RULES = {"B1": "RULE-B1-v1", "B4": "RULE-B4-v1", "D3": "RULE-D3-v1", "G4": "RULE-G4-v1"}
PRODUCT = "https://stats.example.gov/products/estimates.html"
CATALOG = "https://stats.example.gov/data.json"


@pytest.fixture(scope="module")
def params():
    return load_params()


def _record(**extra) -> dict:
    """A dataset entry that is the product's (its URL is in the entry) and carries every field
    the four rules read, well-formed. Each failing fixture removes or breaks exactly one thing."""
    rec = {"title": "Estimates", "description": "d", "keyword": ["k"], "modified": "2026-09-01",
           "identifier": PRODUCT, "accessLevel": "public", "publisher": {"name": "Agency"},
           "contactPoint": {"fn": "Desk", "hasEmail": "mailto:d@example.invalid"},
           "bureauCode": ["015:11"], "programCode": ["015:001"],
           "hasQualityMeasurement": [{"isMeasurementOf": "accuracy", "value": "0.9"}],
           "versionNotes": "Revised benchmark.",
           "wasGeneratedBy": [{"title": "Annual survey collection and estimation"}],
           "distribution": [{"downloadURL": "https://stats.example.gov/e.csv",
                             "mediaType": "text/csv",
                             "describedBy": "https://stats.example.gov/dictionary.json",
                             "describedByType": "application/schema+json"}]}
    rec.update(extra)
    return rec


def _without(*keys, **extra) -> dict:
    rec = _record(**extra)
    for k in keys:
        rec.pop(k, None)
    return rec


def _catalog(*records) -> dict:
    return {"conformsTo": "https://project-open-data.cio.gov/v1.1/schema",
            "dataset": list(records)}


def _obs(params, catalog=None, status=200, error_class=None, raw=None, product=PRODUCT,
         enrich=True) -> Observation:
    """One D4 catalog observation, shaped the way `dcat.fetch_catalog` + `runner` shape it."""
    present = status < 400 and error_class is None
    parsed = {"present": present, "served_content_type": "application/json",
              "wrong_content_type": False}
    if present and enrich:
        if raw is not None:
            parsed["dcat_fields"] = {"scheme": v2clauses.DCAT_FIELDS_SCHEME, "parsed": False,
                                     "reason": raw}
        else:
            parsed["dcat_fields"] = v2clauses.dcat_record_fields(catalog, product, params)
    body = json.dumps(catalog).encode() if catalog is not None else b""
    import hashlib
    return Observation.make("D4", "D4", "scan-fixture", CATALOG, "dcat", "0.1.0", params,
                            {"method": "GET", "url": CATALOG},
                            {"status": status, "headers": {},
                             "body_sha256": hashlib.sha256(body).hexdigest() if body else None,
                             "body_path": None, "bytes": len(body), "elapsed_ms": 0},
                            parsed=parsed, error_class=error_class,
                            captured_at="2026-09-18T00:00:00Z")


def _judge(leg, obs, params):
    return judge_rule(RULES[leg], obs if isinstance(obs, list) else [obs], params)


# ------------------------------------------------------------------ registration

def test_generation_eleven_is_four_first_versions_and_they_are_current():
    assert GENERATIONS[-1] is V11
    assert {m.RULE_ID for m in V11} == set(RULES.values())
    for leg, rid in RULES.items():
        assert CURRENT[leg] == rid
        assert REGISTRY[rid].LEG == leg


def test_each_rule_reads_d4s_catalog_and_declares_its_claim_and_subject():
    """Decision 1: the subject level is named on the module. The catalog is D4's observation,
    so the host is asked for `/data.json` once per surface."""
    for rid in RULES.values():
        assert consumes(rid) == ("D4",)
        assert claim_of(rid) == "absence"
        assert measures(rid) == "product"
        assert getattr(REGISTRY[rid], "MEASURES", None) == "product"


def test_the_field_legs_collect_nothing_of_their_own(params):
    from scan.runner import collect_leg
    for leg in LEGS:
        assert leg in params["dcat_fields"]["legs_served"]
        assert collect_leg({"leg": leg}, {"doc_id": "x", "url": PRODUCT}, params,
                           fetcher=object()) == []


# ------------------------------------------------------------------ the passing fixture

def test_a_record_carrying_every_field_passes_all_four(params):
    o = _obs(params, _catalog(_record()))
    for leg in LEGS:
        f = _judge(leg, o, params)
        assert f.verdict == "pass", (leg, f.reason)
        assert "not measured:" in f.reason, "the unmeasured clauses are printed on every verdict"


def test_a_dataset_level_data_dictionary_is_enough_for_b1(params):
    rec = _record(describedBy="https://stats.example.gov/dictionary.pdf")
    for d in rec["distribution"]:
        d.pop("describedBy")
    assert _judge("B1", _obs(params, _catalog(rec)), params).verdict == "pass"


def test_any_revision_field_satisfies_b4s_revision_clause(params):
    for field in ("versionNotes", "previousVersion", "hasCurrentVersion"):
        rec = _without("versionNotes")
        rec[field] = "https://stats.example.gov/v1"
        assert _judge("B4", _obs(params, _catalog(rec)), params).verdict == "pass", field


def test_a_prefixed_prov_property_satisfies_d3(params):
    for field in ("prov:wasGeneratedBy", "wasDerivedFrom", "prov:wasDerivedFrom"):
        rec = _without("wasGeneratedBy")
        rec[field] = [{"@id": "https://stats.example.gov/src"}]
        assert _judge("D3", _obs(params, _catalog(rec)), params).verdict == "pass", field


# ------------------------------------------------------------------ one fixture per outcome

#: (leg, outcome) -> the observation that must produce it. Every failing outcome
#: `scripts/tag_prescriptions.py` names for these legs is here; the test below checks that too.
def _failing_fixtures(params) -> dict:
    no_catalog = _obs(params, None, status=404, error_class="http_4xx")
    return {
        ("B1", "no_product_record"): no_catalog,
        ("B4", "no_product_record"): _obs(params, _catalog(
            _record(identifier="https://stats.example.gov/other", distribution=[])),
            product=PRODUCT),
        ("D3", "no_product_record"): _obs(params, _catalog(), raw="JSONDecodeError: x"),
        ("G4", "no_product_record"): no_catalog,
        ("B1", "no_data_dictionary"): _obs(params, _catalog(
            _record(distribution=[{"downloadURL": "https://stats.example.gov/e.csv",
                                   "mediaType": "text/csv"}]))),
        ("B4", "quality_measurement_absent"): _obs(params, _catalog(
            _without("hasQualityMeasurement"))),
        ("B4", "revision_metadata_absent"): _obs(params, _catalog(_without("versionNotes"))),
        ("D3", "no_lineage_field"): _obs(params, _catalog(_without("wasGeneratedBy"))),
        ("G4", "authority_codes_absent"): _obs(params, _catalog(
            _record(bureauCode=["Census Bureau"]))),
    }


def test_every_failing_fixture_fails_with_its_outcomes_fragment(params):
    import tag_prescriptions as tp
    fixtures = _failing_fixtures(params)
    for (leg, outcome), o in fixtures.items():
        f = _judge(leg, o, params)
        assert f.verdict == "fail", (leg, outcome, f.reason)
        assert tp.OUTCOMES[leg][outcome] in f.reason, (leg, outcome, f.reason)
    named = {(leg, o) for leg in LEGS for o in tp.OUTCOMES[leg]}
    assert named == set(fixtures), "an outcome with no fixture, or a fixture with no outcome"


def test_the_product_absent_from_a_served_catalog_is_the_same_outcome_as_no_catalog(params):
    """Three states, one outcome: no catalog, a catalog that does not parse, and a catalog
    without the product. In each the product has no catalog record, and the prescription is
    the same — publish the record carrying the field."""
    import tag_prescriptions as tp
    other = _catalog(_record(identifier="https://stats.example.gov/other", distribution=[]))
    for o in (_obs(params, None, status=404, error_class="http_4xx"),
              _obs(params, other), _obs(params, _catalog(), raw="JSONDecodeError: x")):
        for leg in LEGS:
            f = _judge(leg, o, params)
            assert f.verdict == "fail"
            assert tp.OUTCOMES[leg]["no_product_record"] in f.reason


def test_b4_names_both_clauses_when_both_are_missing(params):
    import tag_prescriptions as tp
    f = _judge("B4", _obs(params, _catalog(_without("hasQualityMeasurement", "versionNotes"))),
               params)
    assert f.verdict == "fail"
    for outcome in ("quality_measurement_absent", "revision_metadata_absent"):
        assert tp.OUTCOMES["B4"][outcome] in f.reason


def test_g4_needs_both_codes_and_each_in_its_stated_format(params):
    """DCAT-US 1.1: bureauCode "in the format of `015:11`", programCode "Use the format of
    `015:001`". A missing code and a malformed one are the same failure."""
    for rec in (_without("programCode"), _without("bureauCode"),
                _record(programCode=["15:1"]), _record(bureauCode=[])):
        assert _judge("G4", _obs(params, _catalog(rec)), params).verdict == "fail"


def test_one_record_of_two_lacking_the_field_fails_and_says_how_many(params):
    second = _without("wasGeneratedBy", title="Estimates, second edition")
    f = _judge("D3", _obs(params, _catalog(_record(), second)), params)
    assert f.verdict == "fail"
    assert f.reason.startswith("1 of 2 catalog record(s)")


# ------------------------------------------------------------------ what is not a verdict

def test_a_blind_catalog_is_error_not_fail(params):
    o = _obs(params, None, status=403, error_class="refused")
    for leg in LEGS:
        assert _judge(leg, o, params).verdict == "error"


def test_a_catalog_collected_before_the_field_block_existed_is_error(params):
    """Every D4 observation stored before this task carries no `dcat_fields`. A re-judgement
    of an old cycle under CURRENT must say it could not read the field, never that the field
    is absent."""
    o = _obs(params, _catalog(_record()), enrich=False)
    for leg in LEGS:
        f = _judge(leg, o, params)
        assert f.verdict == "error"
        assert "collected before `dcat_fields` existed" in f.reason


def test_a_group_without_a_catalog_observation_is_error(params):
    for leg in LEGS:
        assert judge_rule(RULES[leg], [], params).verdict == "error"


# ------------------------------------------------------------------ determinism

def test_two_runs_over_the_same_bytes_give_the_same_finding_ids(params):
    cases = [_obs(params, _catalog(_record()))] + list(_failing_fixtures(params).values())
    for leg in LEGS:
        first = [_judge(leg, o, params).finding_id for o in cases]
        second = [_judge(leg, copy.deepcopy(o), params).finding_id for o in cases]
        assert first == second


# ------------------------------------------------------------------ the collector block

def test_the_product_records_are_d4s(params):
    """The field block's membership test is D4's (`product_url in json.dumps(d)`), so "in the
    catalog" and "the record carries X" are about the same records. Checked against D4's own
    collector on the control fixture's catalog."""
    import json as _j
    fixture = (REPO / "assessment/harness/scan/fixtures/passes_all/data.json").read_text()
    product = "http://127.0.0.1:9/index.html"
    cat = _j.loads(fixture.replace("HOSTPORT", "127.0.0.1:9"))
    block = v2clauses.dcat_record_fields(cat, product, params)
    d4_contains = any(product in _j.dumps(d) for d in cat["dataset"])
    assert (block["product_records"] > 0) == d4_contains is True
    for leg in LEGS:
        o = _obs(params, cat, product=product)
        assert _judge(leg, o, params).verdict == "pass", leg


def test_the_block_summarises_records_as_profiles(params):
    cat = _catalog(_record(), _record(title="b"), _without("bureauCode", title="c"))
    b = v2clauses.dcat_record_fields(cat, PRODUCT, params)
    assert b["product_records"] == 3 and b["catalog_records"] == 3
    assert sum(p["records"] for p in b["product_record_profiles"]) == 3
    assert len(b["product_record_profiles"]) == 2
    assert b["catalog_records_carrying"]["bureauCode"] == 2


# ------------------------------------------------------------------ the retained catalogs

def test_the_retained_catalogs_of_the_cycle_of_record_judge_without_error():
    """Decision 3's third leg. The distribution itself is in the RESULT §1 and is not
    published; this holds that every retained catalog body is re-read and judged, twice, to the
    same Finding ids, and that the counts are the ones the RESULT reports."""
    import exercise_dcat_field_rules as ex
    out = ex.exercise()
    assert out["deterministic"] is True
    assert out["catalog_bodies_missing"] == []
    assert out["distribution"] == ex.EXPECTED_DISTRIBUTION


# ------------------------------------------------------------------ one fetch, five readers

class _CountingFetcher:
    """Serves one catalog and counts what was asked for. No socket."""

    def __init__(self, catalog: dict):
        self.body = json.dumps(catalog).encode()
        self.gets: list = []

    def raw_get(self, url):
        self.gets.append(url)
        return {"status": 200, "headers": {"content-type": "application/json"},
                "body": self.body, "elapsed_ms": 1}


def test_a_cycle_fetches_the_catalog_once_and_judges_d4_and_the_field_legs_from_it(params):
    """`run.run_surface` collects a leg that is both judged and consumed ONCE. D4's own Finding
    is judged on exactly the observations it would have had alone, and the four field rules on
    the same observations — so the host is asked for `/data.json` once, not twice."""
    from scan.run import run_surface
    legs = ["D4", *LEGS]
    sp = {leg: {"leg": leg} for leg in legs}
    f = _CountingFetcher(_catalog(_record()))
    obs, findings = run_surface(sp, {"doc_id": "scan-fixture", "url": PRODUCT}, params, legs,
                                fetcher=f)
    assert f.gets == [CATALOG]
    assert len(obs) == 1 and obs[0].leg == "D4"
    by_leg = {x.leg: x for x in findings}
    assert set(by_leg) == set(legs)
    for leg in LEGS:
        assert by_leg[leg].verdict == "pass", (leg, by_leg[leg].reason)
        assert by_leg[leg].evidence == [obs[0].obs_id]
    # D4 alone, as it was judged before generation 11 existed: the same Finding.
    alone = run_surface({"D4": {"leg": "D4"}}, {"doc_id": "scan-fixture", "url": PRODUCT},
                        params, ["D4"], fetcher=_CountingFetcher(_catalog(_record())))[1][0]
    assert alone.finding_id == by_leg["D4"].finding_id
