"""Generation 15: the three false passes the recollection exposed, reproduced from the stored
Observations and fixed (`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md`
decision 1).

Each fixture is the group of Observations a rule judged on one surface of
`scan_2026-10-06_recollect`, read from the stored payload (`state/scan_2026-10-06_recollect.json`)
and never rebuilt by hand, so the test reproduces the false pass from the evidence the cycle of
record holds. Each test asserts both halves: the predecessor still passes on it (the defect is
real and `REGISTRY` still re-derives it), and the new version does not.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

from scan import load_params                                        # noqa: E402
from scan.rederive import rehydrate                                 # noqa: E402
from scan.rules import CURRENT, REGISTRY, consumes, judge           # noqa: E402
from scan.rules import _text                                        # noqa: E402

PAYLOAD = REPO / "state" / "scan_2026-10-06_recollect.json"


@pytest.fixture(scope="module")
def params():
    return load_params()


@pytest.fixture(scope="module")
def stored():
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def group(stored: dict, doc_id: str, rule_id: str) -> list:
    """The Observations `rule_id` judges on `doc_id`: its own leg plus what it consumes, exactly
    as `run.run_surface` and `rederive.rejudge` build the group."""
    legs = {REGISTRY[rule_id].LEG, *consumes(rule_id)}
    rows = [r for r in stored["observations_detail"]
            if r["target_doc_id"] == doc_id and r["leg"] in legs]
    assert rows, f"no stored observation for {doc_id} on {sorted(legs)}"
    return rehydrate(rows)


def recorded(stored: dict, doc_id: str, leg: str) -> dict:
    return next(f for f in stored["findings_detail"]
                if f["target_doc_id"] == doc_id and f["leg"] == leg)


def test_generation_15_is_registered_and_a3_is_current():
    """A3-v8 is current; A2-v5 and D1-v5 judged `scan_2026-10-06_recollect_rj1` and were then
    versioned again by generation 16 (the existence legs), which keeps their object tests."""
    from scan.rules import GENERATIONS
    assert [m.RULE_ID for m in GENERATIONS[14]] == ["RULE-A2-v5", "RULE-A3-v8", "RULE-D1-v5"]
    assert CURRENT["A3"] == "RULE-A3-v8"
    assert (CURRENT["A2"], CURRENT["D1"]) == ("RULE-A2-v6", "RULE-D1-v6")
    for old in ("RULE-A2-v4", "RULE-D1-v4", "RULE-A3-v7", "RULE-A2-v5", "RULE-D1-v5"):
        assert old in REGISTRY


# ------------------------------------------------------------------ A2: a dcat:Catalog
CENSUS_A2 = ["home:www.census.gov", "scan-census-machine",
             "scan-census-flagship-1-surveys-programs",
             "scan-census-flagship-2-american-community-survey-acs"]


@pytest.mark.parametrize("doc_id", CENSUS_A2)
def test_a2_the_census_dcat_catalog_is_not_an_api_description(stored, params, doc_id):
    assert recorded(stored, doc_id, "A2")["verdict"] == "pass"
    old = judge("RULE-A2-v4", group(stored, doc_id, "RULE-A2-v4"), params)
    assert old.verdict == "pass" and "api.census.gov/data" in old.reason
    new = judge("RULE-A2-v5", group(stored, doc_id, "RULE-A2-v5"), params)
    assert new.verdict == "fail", new.reason
    assert "the API is present" in new.reason
    assert "does not parse as an API " in new.reason          # the prescription's fragment
    assert "`openapi`" in new.reason and "`swagger`" in new.reason


def test_a2_an_openapi_or_swagger_document_still_passes():
    from scan.rules import rule_a2_v5
    for v in ("3.0.3", "3.1.0", "3.1", "2.0"):
        assert rule_a2_v5.is_description({"openapi_parsed": True, "openapi_version": v}), v
    for v in (None, "", "1.1", "https://project-open-data.cio.gov/v1.1/schema", 3):
        assert not rule_a2_v5.is_description({"openapi_parsed": True, "openapi_version": v}), v


# ------------------------------------------------------------------ D1: tokens in markup
D1_CASES = [("home:www.census.gov", "CC0"), ("scan-census-machine", "CC0"),
            ("scan-census-flagship-1-surveys-programs", "CC0"),
            ("scan-census-flagship-2-american-community-survey-acs", "CC0"),
            ("home:www.eia.gov", "MIT"), ("scan-eia-machine", "MIT"),
            ("scan-eia-flagship-1-open-data", "MIT")]


@pytest.mark.parametrize("doc_id,token", D1_CASES)
def test_d1_a_token_inside_a_script_hash_or_a_word_is_not_a_licence(stored, params, doc_id,
                                                                    token):
    assert recorded(stored, doc_id, "D1")["verdict"] == "pass"
    old = judge("RULE-D1-v4", group(stored, doc_id, "RULE-D1-v4"), params)
    assert old.verdict == "pass" and old.reason.endswith(f"the recognised token {token}")
    new = judge("RULE-D1-v5", group(stored, doc_id, "RULE-D1-v5"), params)
    assert new.verdict != "pass", new.reason
    # Neither page states a licence in the visible text that was kept, and both were kept only
    # in part: the verdict is the partial search's `error`, naming how much was read.
    assert new.verdict == "error", new.reason
    assert "was read to" in new.reason


def test_d1_where_the_false_tokens_were(stored):
    """The defect, located: the token is in the markup and absent from the visible text."""
    terms = {"CC0": "https://www.census.gov/data/developers/about/terms-of-service.html",
             "MIT": "https://www.eia.gov/opendata/terms-of-service.php"}
    for tok, url in terms.items():
        row = next(r for r in stored["observations_detail"]
                   if r["target_url"] == url and (r.get("parsed") or {}).get("terms_text"))
        html = row["parsed"]["terms_text"]
        assert tok in html.upper()
        assert _text.find_token(_text.visible_text(html), tok) is None
    # v4 upper-cased the markup and searched it: every `MIT` it could have found on eia.gov is
    # the inside of a longer word ("permit", "Limit", "submit"), never the identifier.
    eia = next(r for r in stored["observations_detail"]
               if r["target_url"] == terms["MIT"])["parsed"]["terms_text"]
    hits = [m.start() for m in re.finditer("MIT", eia.upper())]
    assert hits
    assert all(eia[i - 1].isalpha() or eia[i + 3:i + 4].isalpha() for i in hits)


def test_d1_word_boundaries_and_the_license_link_type(params):
    p = params["d1_licence"]
    from scan.rules import rule_d1_v5
    assert rule_d1_v5._recognised("We permit use within Limits.", p) is None
    assert "MIT" in rule_d1_v5._recognised("Released under the MIT licence.", p)
    assert "CC0" in rule_d1_v5._recognised("Dedicated under CC0 1.0.", p)
    assert rule_d1_v5._recognised("in the public domain", p)
    html = ('<p>Terms</p><a rel="license noopener" '
            'href="https://creativecommons.org/publicdomain/zero/1.0/">here</a>')
    assert rule_d1_v5._recognised(_text.visible_text(html), p,
                                  _text.licence_links(html))


# ------------------------------------------------------------------ A3: HTML as a file
BEA_A3 = ["home:www.bea.gov", "scan-bea-machine", "scan-bea-flagship-1-interactive-data",
          "scan-bea-flagship-2-news-releases"]


@pytest.mark.parametrize("doc_id", BEA_A3)
def test_a3_the_bea_papers_page_is_not_an_unfiltered_file(stored, params, doc_id):
    assert recorded(stored, doc_id, "A3")["verdict"] == "pass"
    old = judge("RULE-A3-v7", group(stored, doc_id, "RULE-A3-v7"), params)
    assert old.verdict == "pass"
    assert "special-sworn-researcher-program/papers" in old.reason
    assert "unfiltered file" in old.reason
    new = judge("RULE-A3-v8", group(stored, doc_id, "RULE-A3-v8"), params)
    assert new.verdict != "pass", new.reason
    assert "special-sworn-researcher-program/papers" not in new.reason


def test_a3_an_archive_still_passes(stored, params):
    """The archive branch is unchanged: NASS's `.txt.gz` stays a whole-product download."""
    new = judge("RULE-A3-v8", group(stored, "scan-nass-machine", "RULE-A3-v8"), params)
    assert new.verdict == "pass" and "(archive)" in new.reason


def test_is_html():
    assert _text.is_html("text/html; charset=UTF-8")
    assert _text.is_html("application/xhtml+xml")
    assert not _text.is_html("application/zip")
    assert not _text.is_html("application/vnd.ms-excel")
    assert _text.is_html(None, "\n  <!DOCTYPE html><html>")
    assert not _text.is_html(None, "<base64>")
