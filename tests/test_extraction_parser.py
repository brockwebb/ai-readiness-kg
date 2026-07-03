"""Parser: valid output accepted; unknown edge type routed to proposed_relationships;
missing grounding_span quarantined; endpoint type mismatch quarantined; grounding miss
quarantined. Uses the real kg/schema.yaml (authoritative type catalogue)."""
import pytest

from kg.extraction import parser
from kg.extraction.schema_loader import load_schema

SCHEMA = load_schema()

SOURCE = (
    "AI readiness is a construct describing organizational preparedness. "
    "The FCSM defines data quality as fitness for use. "
    "Discoverability of records matters for AI-mediated access."
)


def _base_output():
    return {
        "document_id": "doc-1",
        "extract_plan": {"section_map": [], "concept_inventory": ["AI readiness"]},
        "concepts": [
            {"id": "c1", "name": "AI readiness",
             "grounding_span": "AI readiness is a construct", "location": "p1"},
            {"id": "c2", "name": "discoverability",
             "grounding_span": "Discoverability of records matters", "location": "p1"},
        ],
        "definitions": [
            {"id": "d1", "term": "data quality", "verbatim_text": "fitness for use",
             "grounding_span": "The FCSM defines data quality as fitness for use", "location": "p1"},
        ],
        "edges": [
            {"type": "mentions", "from_id": "doc-1", "to_id": "c1",
             "grounding_span": "AI readiness is a construct", "location": "p1"},
            {"type": "defines", "from_id": "doc-1", "to_id": "d1",
             "grounding_span": "The FCSM defines data quality", "location": "p1"},
        ],
        "cites": [],
        "proposed_relationships": [],
    }


def test_valid_output_accepted():
    r = parser.parse_extraction(_base_output(), SOURCE, SCHEMA)
    ids = {n["id"] for n in r.nodes}
    assert ids == {"c1", "c2", "d1"}
    edge_types = sorted(e["type"] for e in r.edges)
    assert edge_types == ["defines", "mentions"]
    assert r.quarantined == []
    assert r.proposed_relationships == []


def test_unknown_edge_type_routed_to_proposed():
    out = _base_output()
    out["edges"].append({"type": "correlates_with", "from_id": "c1", "to_id": "d1",
                         "grounding_span": "Discoverability of records matters"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert all(e["type"] != "correlates_with" for e in r.edges)  # never a valid edge
    proposed = [p for p in r.proposed_relationships if p["suggested_edge"] == "correlates_with"]
    assert len(proposed) == 1
    assert proposed[0]["source"] == "auto_routed_unknown_edge"


def test_missing_grounding_span_quarantined():
    out = _base_output()
    out["concepts"].append({"id": "c3", "name": "no-ground"})  # no grounding_span
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "c3" not in {n["id"] for n in r.nodes}
    q = [x for x in r.quarantined if x["item"].get("id") == "c3"]
    assert len(q) == 1 and "grounding_span" in q[0]["reason"]


def test_endpoint_type_mismatch_quarantined():
    out = _base_output()
    # defines requires Document->Definition; c1 (Concept) -> d1 is invalid
    out["edges"].append({"type": "defines", "from_id": "c1", "to_id": "d1",
                         "grounding_span": "The FCSM defines data quality"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    mism = [x for x in r.quarantined if "endpoint type mismatch" in x["reason"]]
    assert len(mism) == 1


def test_grounding_miss_quarantined():
    out = _base_output()
    out["concepts"].append({"id": "c9", "name": "hallucinated",
                            "grounding_span": "this sentence is not in the source at all"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    q = [x for x in r.quarantined if x["item"].get("id") == "c9"]
    assert len(q) == 1 and "not found in source" in q[0]["reason"]


def test_edge_to_quarantined_node_is_quarantined():
    out = _base_output()
    out["concepts"].append({"id": "cbad", "name": "x",
                            "grounding_span": "not present anywhere"})  # will quarantine
    out["edges"].append({"type": "mentions", "from_id": "doc-1", "to_id": "cbad",
                         "grounding_span": "AI readiness is a construct"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert not any(e["to_id"] == "cbad" for e in r.edges)
    assert any("unresolved endpoint" in x["reason"] for x in r.quarantined)


def test_missing_document_id_raises():
    with pytest.raises(ValueError, match="document_id"):
        parser.parse_extraction({"concepts": []}, SOURCE, SCHEMA)


def test_valid_cites_accepted():
    out = _base_output()
    out["cites"].append({"from_id": "doc-1", "to_id": "fcsm-20-04",
                         "grounding_span": "The FCSM defines data quality", "location": "p1"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    cites = [e for e in r.edges if e["type"] == "cites"]
    assert len(cites) == 1
    assert cites[0]["from_type"] == "Document" and cites[0]["to_type"] == "Document"
    assert cites[0]["to_id"] == "fcsm-20-04"


def test_cites_grounding_miss_quarantined():
    out = _base_output()
    out["cites"].append({"from_id": "doc-1", "to_id": "other",
                         "grounding_span": "citation text absent from the source"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert not any(e["type"] == "cites" for e in r.edges)
    assert any(x["kind"] == "cites" and "not found" in x["reason"] for x in r.quarantined)


def test_cites_from_wrong_document_quarantined():
    out = _base_output()
    out["cites"].append({"from_id": "not-this-doc", "to_id": "other",
                         "grounding_span": "AI readiness is a construct"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert any("not this document" in x["reason"] for x in r.quarantined)


def test_model_proposed_relationships_passthrough():
    out = _base_output()
    out["proposed_relationships"].append(
        {"suggested_edge": "presupposes", "from_id": "c1", "to_id": "d1",
         "grounding_span": "AI readiness is a construct", "note": "schema can't express"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    model_pr = [p for p in r.proposed_relationships if p["source"] == "model"]
    assert len(model_pr) == 1 and model_pr[0]["suggested_edge"] == "presupposes"
