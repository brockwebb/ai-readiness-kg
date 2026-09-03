"""G1 declared leg: uncertainty fields beside estimate fields, scored on field names."""
from pathlib import Path

from harness.config import load_harness_config
from harness.probes.g1_declared import G1DeclaredProbe, header_fields
from harness.records import Score, Track

from tests.helpers import fetched

CFG = load_harness_config(Path(__file__).parents[1] / "config" / "harness.toml")


def _probe():
    return G1DeclaredProbe(CFG.g1_uncertainty_field_patterns, CFG.g1_footnote_field_patterns,
                           CFG.g1_id_field_patterns, CFG.g1_footnote_uncertainty_vocabulary)


CSV = {"mediaType": "text/csv", "downloadURL": "https://x.gov/t.csv"}
JSON = {"mediaType": "application/json", "downloadURL": "https://x.gov/t.json"}


def test_is_g1_core_catalog_only():
    p = _probe()
    assert p.dimension == "G1" and p.track is Track.CORE and p.sources == ("data.json",)


def test_acs_style_paired_estimate_and_moe_fields_pass():
    body = "GEO_ID,NAME,B01001_001E,B01001_001M,B01001_002E,B01001_002M\n0400000US08,Colorado,5,1,2,1\n"
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.csv", body=body, headers={"Content-Type": "text/csv"}), CSV)
    assert score is Score.PASS
    assert {(d["uncertainty"], d["estimate"]) for d in obs["paired"]} == {("B01001_001M", "B01001_001E"), ("B01001_002M", "B01001_002E")}
    assert obs["uncertainty_fields"][0]["pattern_id"] == "acs_moe_suffix"
    assert obs["read_from"] == "csv_header"


def test_some_estimates_without_a_companion_is_partial():
    body = "GEO_ID,B01001_001E,B01001_001M,B01001_002E\n1,5,1,2\n"
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.csv", body=body, headers={"Content-Type": "text/csv"}), CSV)
    assert score is Score.PARTIAL
    assert obs["unpaired_estimate_fields"] == ["B01001_002E"]


def test_generic_names_pass_when_each_estimate_has_an_error_field():
    body = "state,year,estimate,standard_error,cv\nCO,2015,564757,6156,1.1\n"
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.csv", body=body, headers={"Content-Type": "text/csv"}), CSV)
    assert score is Score.PASS
    assert {u["class"] for u in obs["uncertainty_fields"]} == {"SE", "CV"}
    assert obs["id_fields"] == ["state", "year"]


def test_footnote_only_is_partial_not_pass():
    body = "state,value,notes\nCO,564757,margin of error available on request\n"
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.csv", body=body, headers={"Content-Type": "text/csv"}), CSV)
    assert score is Score.PARTIAL
    assert obs["footnote_fields"] == ["notes"] and "margin of error" in obs["footnote_vocabulary_hits"]


def test_no_uncertainty_anywhere_fails():
    body = "state,value\nCO,564757\n"
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.csv", body=body, headers={"Content-Type": "text/csv"}), CSV)
    assert score is Score.FAIL and obs["uncertainty_fields"] == []


def test_json_records_and_census_header_row_shapes():
    body = '[{"NAME":"Colorado","B01001_001E":"5","B01001_001M":"1"}]'
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.json", body=body, headers={"Content-Type": "application/json"}), JSON)
    assert score is Score.PASS and obs["read_from"] == "json_first_record_keys"
    body = '[["NAME","B01001_001E","B01001_001M"],["Colorado","5","1"]]'
    fields, how = header_fields(fetched("https://x.gov/t.json", body=body, headers={"Content-Type": "application/json"}), JSON)
    assert fields == ["NAME", "B01001_001E", "B01001_001M"] and how == "json_header_row"


def test_unretrievable_distribution_fails_with_status():
    score, ev, obs = _probe().evaluate(fetched("https://x.gov/t.csv", status=404, body=""), CSV)
    assert score is Score.FAIL and "404" in ev


def test_heuristic_is_declared_in_observations():
    body = "state,value,moe\nCO,564757,10127\n"
    _, _, obs = _probe().evaluate(fetched("https://x.gov/t.csv", body=body, headers={"Content-Type": "text/csv"}), CSV)
    assert "values not inspected" in obs["heuristic"]
