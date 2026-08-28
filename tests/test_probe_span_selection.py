"""probe_judge 1.1.0: a fact about an attribute is judged against that attribute's own span."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import probe_judge as pj  # noqa: E402

ITEM = {"grounding_span": "AIDRIN is a data readiness inspector",
        "extra": {"name": "AIDRIN",
                  "grounding_spans": {"method": "computes completeness and outlier metrics",
                                      "owner": "   "}}}


def test_an_attribute_with_its_own_span_is_judged_against_that_span():
    assert pj.span_for(ITEM, "method") == ("computes completeness and outlier metrics",
                                           "attribute:method")


def test_a_blank_attribute_span_falls_back_to_the_node_span():
    assert pj.span_for(ITEM, "owner") == (ITEM["grounding_span"], "node")


def test_an_attribute_with_no_entry_falls_back_to_the_node_span():
    assert pj.span_for(ITEM, "year") == (ITEM["grounding_span"], "node")


def test_edges_and_unattributed_facts_use_the_node_span():
    assert pj.span_for(ITEM, None) == (ITEM["grounding_span"], "node")
    assert pj.span_for({"grounding_span": "S", "extra": {}}, "method") == ("S", "node")


def test_the_template_version_records_the_change():
    assert pj.judge_version() == "1.1.0"
