"""D4's membership test is DCAT-US's own URL fields, not a substring. `RULE-D4-v3`.

`cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 4, from the question
`cc_tasks/2026-09-18_dcat_field_rules_RESULT.md` §1 left open. The DCAT-US v1.1 sentence the
decision rests on (corpus/kernel/dcat-us-1-1-schema.md, doc_id `dcat-us-1-1-schema`):
`landingPage` "is not intended for an agency's homepage (e.g. www.agency.gov), but rather if a
dataset has a human-friendly hub or landing page that users can be directed to for all
resources tied to the dataset." The substring test (`product_url in json.dumps(record)`) made
census.gov's home page the product of 1,635 of its 1,805 records.

**No network.** Records are dicts; the collector is driven through a stub fetcher that serves
one body, the shape `tests/test_dcat_field_rules.py` already uses.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

from scan import load_params                                        # noqa: E402
from scan.collectors import dcat                                    # noqa: E402
from scan.rules import CURRENT, GENERATIONS, REGISTRY, judge        # noqa: E402

HOST = "https://stats.example.gov"
PRODUCT = f"{HOST}/products/estimates.html"


@pytest.fixture(scope="module")
def params():
    return load_params()


def _rec(**fields) -> dict:
    base = {"title": "Estimates", "description": "d", "keyword": ["k"],
            "modified": "2026-09-01", "identifier": "urn:x:1", "accessLevel": "public",
            "publisher": {"name": "Agency"},
            "contactPoint": {"fn": "Desk", "hasEmail": "mailto:d@example.invalid"}}
    base.update(fields)
    return base


class _OneBody:
    """Serves one catalog body for any GET; counts nothing, fetches nothing."""

    def __init__(self, catalog):
        self.body = json.dumps(catalog).encode()

    def raw_get(self, url):
        return {"status": 200, "headers": {"content-type": "application/json"},
                "body": self.body, "elapsed_ms": 1, "final_url": url}


def _d4(params, *records, product=PRODUCT):
    return dcat.fetch_catalog(_OneBody({"dataset": list(records)}), "D4", "scan-x", product,
                              params)


# ------------------------------------------------------------------ the membership test

@pytest.mark.parametrize("field", ["identifier", "landingPage"])
def test_a_record_naming_the_product_in_a_dataset_url_field_is_the_products(params, field):
    assert len(dcat.product_records([_rec(**{field: PRODUCT})], PRODUCT, params)) == 1


@pytest.mark.parametrize("field", ["accessURL", "downloadURL"])
def test_a_distribution_url_naming_the_product_is_the_products(params, field):
    rec = _rec(distribution=[{field: PRODUCT, "mediaType": "text/html"}])
    assert len(dcat.product_records([rec], PRODUCT, params)) == 1


def test_the_home_page_owns_no_record_that_merely_contains_its_url(params):
    """The census.gov case: every record's URLs begin with the home URL, and none IS it."""
    home = f"{HOST}/"
    recs = [_rec(landingPage=f"{HOST}/products/{i}.html", identifier=f"{HOST}/id/{i}")
            for i in range(5)]
    assert all(home in json.dumps(r) for r in recs), "the substring test would claim all five"
    assert dcat.product_records(recs, home, params) == []


@pytest.mark.parametrize("field,value", [
    ("describedBy", PRODUCT), ("references", [PRODUCT]), ("description", f"see {PRODUCT}"),
    ("landingPage", PRODUCT + "/archive"), ("landingPage", PRODUCT + "l")])
def test_a_url_about_the_dataset_or_a_longer_url_is_not_membership(params, field, value):
    rec = _rec(**{field: value})
    assert PRODUCT in json.dumps(rec)
    assert dcat.product_records([rec], PRODUCT, params) == []


@pytest.mark.parametrize("a,b,same", [
    # RFC 3986 §6.2.2.1: scheme and host are case-insensitive.
    ("HTTPS://Stats.Example.GOV/x", "https://stats.example.gov/x", True),
    # §6.2.3: a default port is no port; an empty path is "/".
    ("https://stats.example.gov:443/x", "https://stats.example.gov/x", True),
    ("http://stats.example.gov:80", "http://stats.example.gov/", True),
    # And nothing further: the path is case-sensitive, a trailing slash counts, schemes differ.
    ("https://stats.example.gov/X", "https://stats.example.gov/x", False),
    ("https://stats.example.gov/x/", "https://stats.example.gov/x", False),
    ("http://stats.example.gov/x", "https://stats.example.gov/x", False),
    ("https://www.stats.example.gov/x", "https://stats.example.gov/x", False),
    ("https://stats.example.gov:8443/x", "https://stats.example.gov/x", False),
])
def test_url_equivalence_is_rfc_3986_section_6_and_no_further(params, a, b, same):
    assert (dcat.normalize_url(a, params) == dcat.normalize_url(b, params)) is same


def test_the_fields_are_the_ones_params_declares(params):
    assert params["d4_catalog"]["membership_fields"] == [
        "identifier", "landingPage", "distribution.accessURL", "distribution.downloadURL"]


# ------------------------------------------------------------------ the collector

def test_the_collector_records_both_tests_side_by_side(params):
    """`contains_product` stays (v1/v2 read it); `membership` is what v3 reads."""
    [o] = _d4(params, _rec(landingPage=f"{HOST}/products/estimates.html/old"))
    assert o.parsed["contains_product"] is True
    assert o.parsed["membership"] == {"test": dcat.MEMBERSHIP_TEST,
                                      "fields": params["d4_catalog"]["membership_fields"],
                                      "records": 0}


# ------------------------------------------------------------------ the rule

def test_generation_thirteen_is_d4_v3_and_it_is_current():
    assert CURRENT["D4"] == "RULE-D4-v3"
    assert [m.RULE_ID for m in GENERATIONS[-1]] == ["RULE-D4-v3"]
    assert {"RULE-D4-v1", "RULE-D4-v2", "RULE-D4-v3"} <= set(REGISTRY)


def test_v3_fails_where_v2_passed_on_a_substring_alone(params):
    obs = _d4(params, _rec(landingPage=f"{HOST}/products/estimates.html/old"))
    obs[0].parsed["pod"] = {"validated": True, "conforms": True, "datasets_validated": 1,
                            "datasets_total": 1}
    assert judge("RULE-D4-v2", obs, params).verdict == "pass"
    f = judge("RULE-D4-v3", obs, params)
    assert f.verdict == "fail"
    assert "but the product is not in it" in f.reason


def test_v3_passes_a_record_that_names_the_product(params):
    obs = _d4(params, _rec(identifier=PRODUCT))
    obs[0].parsed["pod"] = {"validated": True, "conforms": True, "datasets_validated": 1,
                            "datasets_total": 1}
    f = judge("RULE-D4-v3", obs, params)
    assert f.verdict == "pass", f.reason
    assert "1 record(s)" in f.reason


def test_v3_over_a_catalog_collected_before_the_block_is_error_not_fail(params):
    """Every stored catalog Observation predates `membership`. Reading the substring flag in
    its place would re-judge history under the test this version exists to replace."""
    obs = _d4(params, _rec(identifier=PRODUCT))
    del obs[0].parsed["membership"]
    f = judge("RULE-D4-v3", obs, params)
    assert f.verdict == "error"
    assert "before the DCAT-US membership test existed" in f.reason


def test_v3_keeps_every_prescription_fragment_of_v2():
    """`tag_prescriptions.OUTCOMES["D4"]` names D4's fail branches by a verbatim fragment of
    the CURRENT module's source; v3 must still produce every one."""
    import tag_prescriptions as tp
    src = Path(REGISTRY["RULE-D4-v3"].__file__).read_text(encoding="utf-8")
    for outcome, frag in tp.OUTCOMES["D4"].items():
        assert frag in src, outcome


def test_the_field_legs_follow_d4s_membership(params):
    """`v2clauses.dcat_record_fields` selects the product's records with the same function, so
    a home page reads no record through the four DCAT field legs either."""
    from scan.collectors import v2clauses
    recs = [_rec(landingPage=f"{HOST}/products/{i}.html") for i in range(3)]
    block = v2clauses.dcat_record_fields({"dataset": recs}, f"{HOST}/", params)
    assert block["product_records"] == 0 and block["catalog_records"] == 3
