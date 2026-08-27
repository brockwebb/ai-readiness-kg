"""v0.3.4 parser rules (task 2026-08-26_overnight_burn Lane 0; 2026-08-22_probe_decision.md):
Instrument owner/year/method null unless a covering per-attribute span exists; semantic
edges whose span lacks either endpoint name route to proposed_relationships."""
from kg.extraction import parser, schema_loader

SCHEMA = schema_loader.load_schema()

DOC = ("The AI Readiness Index is published by the Example Institute. "
       "The index scores organizations through a survey of 30 weighted questions. "
       "The Data Pillar is a component of the AI Readiness Framework overall.")


def _out(instruments=None, concepts=None, frameworks=None, edges=None):
    return {"document_id": "doc-x",
            "instruments": instruments or [], "concepts": concepts or [],
            "frameworks": frameworks or [], "edges": edges or []}


def test_instrument_method_without_span_is_nulled_not_quarantined():
    out = _out(instruments=[{
        "id": "i1", "name": "AI Readiness Index",
        "grounding_span": "The AI Readiness Index is published by the Example Institute.",
        "method": "a biennial household survey",          # fabricated: no covering span
        "owner": "Example Institute",
        "grounding_spans": {"owner": "published by the Example Institute"},
    }])
    res = parser.parse_extraction(out, DOC, SCHEMA, enforce_span_coverage=False)
    assert len(res.nodes) == 1 and not res.quarantined
    item = res.nodes[0]["item"]
    assert item["method"] is None
    assert item["owner"] == "Example Institute"           # covered -> kept
    assert item["nulled_at_parse"] == ["method"]


def test_instrument_method_with_covering_span_is_kept():
    out = _out(instruments=[{
        "id": "i1", "name": "AI Readiness Index",
        "grounding_span": "The AI Readiness Index is published by the Example Institute.",
        "method": "survey of 30 weighted questions",
        "grounding_spans": {"method": "scores organizations through a survey of 30 weighted questions"},
    }])
    res = parser.parse_extraction(out, DOC, SCHEMA, enforce_span_coverage=False)
    assert res.nodes[0]["item"]["method"] == "survey of 30 weighted questions"
    assert "nulled_at_parse" not in res.nodes[0]["item"]


def test_instrument_span_not_in_document_nulls_attribute():
    out = _out(instruments=[{
        "id": "i1", "name": "AI Readiness Index",
        "grounding_span": "The AI Readiness Index is published by the Example Institute.",
        "year": "2024",
        "grounding_spans": {"year": "first fielded in 2024"},   # not in DOC
    }])
    res = parser.parse_extraction(out, DOC, SCHEMA, enforce_span_coverage=False)
    assert res.nodes[0]["item"]["year"] is None


def test_semantic_edge_without_both_endpoint_names_routes_to_proposed():
    out = _out(
        concepts=[{"id": "c1", "name": "Data Pillar",
                   "grounding_span": "The Data Pillar is a component"}],
        frameworks=[{"id": "f1", "name": "AI Readiness Framework",
                     "grounding_span": "the AI Readiness Framework overall"}],
        edges=[{"type": "has_component", "from_id": "f1", "to_id": "c1",
                # span names only one endpoint -> structural inference, not a stated relation
                "grounding_span": "The Data Pillar is a component"}])
    res = parser.parse_extraction(out, DOC, SCHEMA, enforce_span_coverage=False)
    assert not any(e["type"] == "has_component" for e in res.edges)
    routed = [p for p in res.proposed_relationships if p["source"] == "auto_routed_semantic_span"]
    assert len(routed) == 1 and "AI Readiness Framework" in routed[0]["note"]


def test_semantic_edge_with_both_endpoints_and_predicate_is_written():
    out = _out(
        concepts=[{"id": "c1", "name": "Data Pillar",
                   "grounding_span": "The Data Pillar is a component"}],
        frameworks=[{"id": "f1", "name": "AI Readiness Framework",
                     "grounding_span": "the AI Readiness Framework overall"}],
        edges=[{"type": "has_component", "from_id": "f1", "to_id": "c1",
                "grounding_span": "The Data Pillar is a component of the AI Readiness Framework"}])
    res = parser.parse_extraction(out, DOC, SCHEMA, enforce_span_coverage=False)
    assert any(e["type"] == "has_component" for e in res.edges)


def test_non_semantic_edges_unaffected_by_span_rule():
    out = _out(
        concepts=[{"id": "c1", "name": "Data Pillar",
                   "grounding_span": "The Data Pillar is a component"}],
        edges=[{"type": "mentions", "from_id": "doc-x", "to_id": "c1",
                "grounding_span": "The Data Pillar is a component"}])
    res = parser.parse_extraction(out, DOC, SCHEMA, enforce_span_coverage=False)
    assert any(e["type"] == "mentions" for e in res.edges)
