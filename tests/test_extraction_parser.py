"""Parser: valid output accepted; unknown edge type routed to proposed_relationships;
missing grounding_span quarantined; endpoint type mismatch quarantined; grounding miss
quarantined. Uses the real kg/schema.yaml (authoritative type catalogue)."""
import pytest

from kg.extraction import parser
from kg.extraction.schema_loader import load_schema

SCHEMA = load_schema()


@pytest.fixture(autouse=True)
def _coverage_off_by_default(monkeypatch):
    """The span-coverage gate is ON in config since 2026-08-23 (repair Phase 5). The parser
    tests for OTHER gates use pointer spans as fixtures; isolate them from coverage so each
    test checks one rule. The enforcement tests at the bottom enable it explicitly."""
    monkeypatch.setattr(parser, "_span_coverage_default", lambda: False)

SOURCE = (
    "AI readiness is a construct describing organizational preparedness. "
    "The FCSM defines data quality as fitness for use. "
    "Discoverability of records matters for AI-mediated access. "
    "The DRL framework extends the FAIR framework for readiness assessment. "
    "Google consumes the DCAT specification when crawling catalogs."
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


def test_invalid_pair_routed_to_proposed_not_quarantined():
    out = _base_output()
    # defines legal pair is Document->Definition; c1(Concept)->d1(Definition) is illegal.
    # Grounded + resolvable => expressiveness signal, not quarantine, not graph.
    out["edges"].append({"type": "defines", "from_id": "c1", "to_id": "d1",
                         "grounding_span": "The FCSM defines data quality"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert not any(e["type"] == "defines" and e["from_id"] == "c1" for e in r.edges)
    assert not any(x["kind"] == "edge" and "mismatch" in x["reason"] for x in r.quarantined)
    routed = [p for p in r.proposed_relationships if p["source"] == "auto_routed_invalid_pair"]
    assert len(routed) == 1 and routed[0]["suggested_edge"] == "defines"


def test_cross_pair_on_multipair_edge_routed_to_proposed():
    # extends is index-paired: Definition->Definition and Framework->Framework only.
    # Definition->Framework is a cross pair -> proposed_relationships, not a valid edge.
    out = _base_output()
    out["frameworks"] = [{"id": "f1", "name": "FAIR",
                          "grounding_span": "Discoverability of records matters"}]
    out["edges"].append({"type": "extends", "from_id": "d1", "to_id": "f1",
                         "grounding_span": "AI readiness is a construct"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert not any(e["type"] == "extends" for e in r.edges)
    routed = [p for p in r.proposed_relationships
              if p["suggested_edge"] == "extends" and p["source"] == "auto_routed_invalid_pair"]
    assert len(routed) == 1


def test_valid_multipair_edge_accepted():
    # Framework->Framework IS a legal extends pair.
    out = _base_output()
    out["frameworks"] = [
        {"id": "f1", "name": "FAIR", "grounding_span": "AI readiness is a construct"},
        {"id": "f2", "name": "DRL", "grounding_span": "Discoverability of records matters"},
    ]
    # v0.3.4: a semantic edge's span must contain both endpoint names
    out["edges"].append({"type": "extends", "from_id": "f2", "to_id": "f1",
                         "grounding_span": "The DRL framework extends the FAIR framework"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert any(e["type"] == "extends" for e in r.edges)


def test_invalid_pair_but_ungrounded_still_quarantined():
    # grounding is checked before pairing: an illegal pair with a bad span quarantines.
    out = _base_output()
    out["edges"].append({"type": "defines", "from_id": "c1", "to_id": "d1",
                         "grounding_span": "text that is absent from the source"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert any(x["kind"] == "edge" and "not found in source" in x["reason"]
               for x in r.quarantined)


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


# --- v0.3: property enums + required evidence_grade (DD-010) ------------------------------

def _claim(**over):
    c = {"id": "k1", "claim_text": "discoverability matters", "claim_type": "empirical",
         "evidence_grade": "inference",
         "grounding_span": "Discoverability of records matters", "location": "p1"}
    c.update(over)
    return c


def test_claim_with_valid_evidence_grade_accepted():
    out = _base_output()
    out["claims"] = [_claim()]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "k1" in {n["id"] for n in r.nodes}
    assert r.quarantined == []


def test_claim_missing_evidence_grade_quarantined_with_reason():
    out = _base_output()
    c = _claim(); del c["evidence_grade"]
    out["claims"] = [c]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "k1" not in {n["id"] for n in r.nodes}
    q = [x for x in r.quarantined if x["item"].get("id") == "k1"]
    assert len(q) == 1 and q[0]["kind"] == "claims"
    assert "evidence_grade" in q[0]["reason"] and "required" in q[0]["reason"]


def test_claim_empty_evidence_grade_quarantined():
    out = _base_output()
    out["claims"] = [_claim(evidence_grade="  ")]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert any(x["item"].get("id") == "k1" and "evidence_grade" in x["reason"]
               for x in r.quarantined)


def test_claim_evidence_grade_outside_enum_quarantined():
    out = _base_output()
    out["claims"] = [_claim(evidence_grade="vibes")]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "k1" not in {n["id"] for n in r.nodes}
    q = [x for x in r.quarantined if x["item"].get("id") == "k1"]
    assert len(q) == 1 and "evidence_grade" in q[0]["reason"] and "'vibes'" in q[0]["reason"]


def test_claim_grounding_miss_reason_wins_over_missing_grade():
    # grounding gate runs first; an ungrounded claim keeps the grounding reason.
    out = _base_output()
    c = _claim(grounding_span="absent from source"); del c["evidence_grade"]
    out["claims"] = [c]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    q = [x for x in r.quarantined if x["item"].get("id") == "k1"]
    assert len(q) == 1 and "not found in source" in q[0]["reason"]


def test_edge_to_claim_quarantined_for_missing_grade_is_unresolved():
    out = _base_output()
    c = _claim(); del c["evidence_grade"]
    out["claims"] = [c]
    out["edges"].append({"type": "asserts", "from_id": "doc-1", "to_id": "k1",
                         "grounding_span": "AI readiness is a construct"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert not any(e["type"] == "asserts" for e in r.edges)
    assert any("unresolved endpoint" in x["reason"] for x in r.quarantined)


def test_measure_tier_optional_absent_ok():
    out = _base_output()
    out["measures"] = [{"id": "m1", "text": "x", "grounding_span": "AI readiness is a construct"}]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "m1" in {n["id"] for n in r.nodes}


def test_measure_tier_valid_accepted():
    out = _base_output()
    out["measures"] = [{"id": "m1", "text": "x", "tier": "agency_instrumented",
                        "grounding_span": "AI readiness is a construct"}]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "m1" in {n["id"] for n in r.nodes}


def test_measure_tier_outside_enum_quarantined():
    out = _base_output()
    out["measures"] = [{"id": "m1", "text": "x", "tier": "freemium",
                        "grounding_span": "AI readiness is a construct"}]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert "m1" not in {n["id"] for n in r.nodes}
    q = [x for x in r.quarantined if x["item"].get("id") == "m1"]
    assert len(q) == 1 and "Measure.tier" in q[0]["reason"]


def test_practice_scope_enforced():
    out = _base_output()
    out["practices"] = [
        {"id": "p1", "text": "publish DCAT", "scope": "dataset",
         "grounding_span": "AI readiness is a construct"},
        {"id": "p2", "text": "bad scope", "scope": "galaxy",
         "grounding_span": "Discoverability of records matters"},
    ]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    ids = {n["id"] for n in r.nodes}
    assert "p1" in ids and "p2" not in ids
    assert next(n for n in r.nodes if n["id"] == "p1")["type"] == "Practice"
    q = [x for x in r.quarantined if x["item"].get("id") == "p2"]
    assert len(q) == 1 and "Practice.scope" in q[0]["reason"]


def test_v03_layers_parsed_with_grounding_gate():
    # Tool/Platform carry grounding_span like every other node (§4 universal provenance).
    out = _base_output()
    out["tools"] = [
        {"id": "t1", "name": "Lighthouse", "grounding_span": "AI readiness is a construct"},
        {"id": "t2", "name": "ungrounded"},
    ]
    out["platforms"] = [
        {"id": "pl1", "name": "Google Search", "grounding_span": "The FCSM defines data quality"},
        {"id": "pl2", "name": "Bing", "grounding_span": "never in the source"},
    ]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    types = {n["id"]: n["type"] for n in r.nodes}
    assert types.get("t1") == "Tool" and types.get("pl1") == "Platform"
    assert "t2" not in types and "pl2" not in types
    assert any(x["kind"] == "tools" and "missing grounding_span" in x["reason"] for x in r.quarantined)
    assert any(x["kind"] == "platforms" and "not found in source" in x["reason"] for x in r.quarantined)


def test_v03_edges_legal_and_illegal_routing():
    out = _base_output()
    out["claims"] = [_claim()]
    out["practices"] = [{"id": "p1", "text": "t", "scope": "site",
                         "grounding_span": "AI readiness is a construct"}]
    out["tools"] = [{"id": "t1", "name": "Lighthouse", "grounding_span": "AI readiness is a construct"}]
    out["platforms"] = [{"id": "pl1", "name": "Google", "grounding_span": "AI readiness is a construct"}]
    out["measures"] = [{"id": "m1", "text": "x", "grounding_span": "AI readiness is a construct"}]
    out["standards"] = [{"id": "s1", "name": "DCAT", "grounding_span": "AI readiness is a construct"}]
    g = "Discoverability of records matters"
    out["edges"] += [
        {"type": "recommends", "from_id": "doc-1", "to_id": "p1", "grounding_span": g},
        {"type": "supported_by", "from_id": "p1", "to_id": "k1", "grounding_span": g},
        {"type": "implemented_by", "from_id": "m1", "to_id": "t1", "grounding_span": g},
        # consumes is semantic (v0.3.4): its span must contain both endpoint names
        {"type": "consumes", "from_id": "pl1", "to_id": "s1",
         "grounding_span": "Google consumes the DCAT specification"},
        {"type": "applies_to", "from_id": "p1", "to_id": "c1", "grounding_span": g},
        {"type": "applies_to", "from_id": "m1", "to_id": "c2", "grounding_span": g},
        {"type": "targets", "from_id": "p1", "to_id": "pl1", "grounding_span": g},
        # illegal pairs: grounded + resolvable => proposed_relationships, never graph
        {"type": "targets", "from_id": "m1", "to_id": "pl1", "grounding_span": g},
        {"type": "consumes", "from_id": "t1", "to_id": "s1", "grounding_span": g},
    ]
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert r.quarantined == []
    accepted = sorted((e["type"], e["from_id"], e["to_id"]) for e in r.edges
                      if e["type"] not in ("mentions", "defines"))
    assert accepted == sorted([
        ("recommends", "doc-1", "p1"), ("supported_by", "p1", "k1"),
        ("implemented_by", "m1", "t1"), ("consumes", "pl1", "s1"),
        ("applies_to", "p1", "c1"), ("applies_to", "m1", "c2"), ("targets", "p1", "pl1")])
    routed = sorted((p["suggested_edge"], p["from_type"], p["to_type"])
                    for p in r.proposed_relationships if p["source"] == "auto_routed_invalid_pair")
    assert routed == [("consumes", "Tool", "Standard"), ("targets", "Measure", "Platform")]


def test_v03_supersedes_document_to_document():
    # Both endpoints must resolve; this document + an in-output node can't be a Document, so
    # the only resolvable Document id is doc-1 itself (self-edge is type-legal).
    out = _base_output()
    out["edges"].append({"type": "supersedes", "from_id": "doc-1", "to_id": "doc-1",
                         "grounding_span": "AI readiness is a construct"})
    r = parser.parse_extraction(out, SOURCE, SCHEMA)
    assert any(e["type"] == "supersedes" for e in r.edges)
    out2 = _base_output()
    out2["edges"].append({"type": "supersedes", "from_id": "doc-1", "to_id": "c1",
                          "grounding_span": "AI readiness is a construct"})
    r2 = parser.parse_extraction(out2, SOURCE, SCHEMA)
    assert not any(e["type"] == "supersedes" for e in r2.edges)
    assert any(p["suggested_edge"] == "supersedes" and p["source"] == "auto_routed_invalid_pair"
               for p in r2.proposed_relationships)


# --- span-coverage invariant in the parser (task 2026-08-22_faithfulness_probe, Phase 7) ---

def test_span_partial_quarantined_only_when_enforced():
    from kg.extraction import parser as P
    src = "The methodology is internally consistent with other CPI methodologies. Fin."
    out = {"document_id": "d", "concepts": [], "definitions": [],
           "claims": [{"id": "c1", "claim_text": "The methodology is internally consistent with other CPI methodologies",
                       "claim_type": "empirical", "evidence_grade": "inference",
                       "grounding_span": "The methodology is internally"}],
           "instruments": [], "measures": [], "standards": [], "frameworks": [], "constructs": [],
           "practices": [], "tools": [], "platforms": [], "edges": [], "proposed_relationships": []}
    off = P.parse_extraction(out, src, enforce_span_coverage=False)
    assert len(off.nodes) == 1 and not off.quarantined
    on = P.parse_extraction(out, src, enforce_span_coverage=True)
    assert not on.nodes and on.quarantined[0]["reason"].startswith("span_partial")
    import yaml
    cfg = yaml.safe_load(open(P._DIXIE_CFG))
    assert cfg["extraction_gates"]["enforce_span_coverage"] is True   # flipped 2026-08-23 (repair Phase 5)


def test_enforcement_default_quarantines_partial_span_at_extraction_time():
    # Phase 5 regression: with the config default (now True) a partial span is quarantined
    from kg.extraction import parser as P
    src = "The methodology is internally consistent with other CPI methodologies."
    out = {"document_id": "d", "concepts": [], "definitions": [],
           "claims": [{"id": "c1", "claim_text": "The methodology is internally consistent with other CPI methodologies",
                       "claim_type": "empirical", "evidence_grade": "inference",
                       "grounding_span": "The methodology is internally"}],
           "instruments": [], "measures": [], "standards": [], "frameworks": [], "constructs": [],
           "practices": [], "tools": [], "platforms": [], "edges": [], "proposed_relationships": []}
    import yaml
    live_default = bool(yaml.safe_load(open(P._DIXIE_CFG))["extraction_gates"]["enforce_span_coverage"])
    res = P.parse_extraction(out, src, enforce_span_coverage=live_default)
    assert live_default is True
    assert not res.nodes and res.quarantined[0]["reason"].startswith("span_partial")
