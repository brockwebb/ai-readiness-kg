"""squiddy SQ-022b Part A (DN-050 R-219, R-220, R-221): the ai-readiness graph's emitter fills every slot its
transcription declares from the item it is given, types a scalar slot by the schema, builds the one derived annotation
the graph declares (`grounding_thin`), and takes a Document's unmeasured catalog properties from this repository's
`manifest_add` (and `document_annotation`) events, its measured `content_hash` from the kit's own sha256.

Pure: the emitter is called with the graph's generated classes and a stand-in for the kit's graph object; nothing is
written. The end-to-end path (adopter, ingest, ledger updates) is squiddy's `tests/test_sq022b_reemit.py`.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GRAPH = REPO / "graphs" / "ai-readiness"
DOC = "d-fixture"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def emit():
    return _load("airkg_graph_emit_sq022b", GRAPH / "emit.py")


@pytest.fixture(scope="module")
def classes():
    mod = _load("airkg_graph_classes_sq022b", GRAPH / "schema" / "generated" / "ai_readiness_pydantic.py")
    cfg = yaml.safe_load((GRAPH / "graph.yaml").read_text(encoding="utf-8"))
    return {c["name"]: getattr(mod, c["name"]) for c in cfg["classes"]}


@pytest.fixture(scope="module")
def graph():
    cfg = yaml.safe_load((GRAPH / "config.yaml").read_text(encoding="utf-8"))
    return SimpleNamespace(domain=cfg["domain"], engine=cfg["engine"], root=GRAPH)


def _row(kind: str, claim_kind: str, props: dict, **claim) -> dict:
    return {"status": "grounded", "span": {"start": 0, "end": 4, "sha256": "a" * 64, "parsed_sha256": "b" * 64},
            "airkg": {"batch": "batch-001", "chunk_id": "c1", "timestamp": "2026-07-01T00:00:00+00:00",
                      "model_id": "m", "prompt_version": "v", "extraction_event_id": "e1"},
            "claim": {"kind": kind, "claim_kind": claim_kind, "props": props, **claim}}


def _node(claim_kind: str, item: str, **props) -> dict:
    return _row("node", claim_kind, {"id": item, "doc_id": DOC, "prov_wasDerivedFrom": DOC, **props},
                key=f"{DOC}::{item}")


def _edge(claim_kind: str, frm: str, to: str, **props) -> dict:
    return _row("edge", claim_kind, props, subject=f"{DOC}::{frm}", object=f"{DOC}::{to}")


def _one(emit, graph, classes, row):
    out = emit.emit_extraction({"id": DOC}, [row], graph, classes)
    assert len(out) == 1
    return out[0]


# ------------------------------------------------------------------------------------------ R-219: every slot filled


INSTRUMENT = dict(name="Data Readiness Index", owner="Lab", year=2024, method="survey",
                  grounding_span="the Data Readiness Index (Lab, 2024) is a survey of readiness in agencies",
                  aliases=["DRI", "the index"], attribute_anchors='{"owner": "Lab"}', nulled_at_parse=["method"])


def test_every_declared_slot_the_item_carries_is_written(emit, graph, classes):
    rows = [
        _node("Instrument", "i1", **INSTRUMENT),
        _node("Definition", "d1", term="AI-Ready Data", verbatim_text="AI-Ready Data is data that is discoverable",
              grounding_span="AI-Ready Data is data that is discoverable", name="AI-Ready Data",
              term_as_ocrd="Al-Ready Data", component_discoverable="discoverable",
              component_machine_readable_understandable="machine-readable", component_sufficient_quality="quality",
              component_documentation="documentation", component_access_methods="access methods"),
        _node("Claim", "cl1", claim_text="x", grounding_span="x", evidence_grade="inference", name="NAO 216-128 4.05"),
        _node("Framework", "f1", name="F", year="2017", aliases=["F1"], grounding_span="F (2017) frames it"),
        _node("Standard", "s1", name="S", aliases=["S-1"], grounding_span="S is the standard of record for it"),
    ]
    renamed = {**emit.RENAMED, **graph.domain["airkg_schema"]["renamed_extra"]}
    for row in rows:
        inst = _one(emit, graph, classes, row)
        fields = type(inst).model_fields
        for k, v in row["claim"]["props"].items():
            slot = renamed.get(k, k)
            if k in emit.OWNED or slot not in fields:
                continue
            assert getattr(inst, slot) is not None, f"{type(inst).__name__}.{slot} left empty"
        # nothing the item carries is outside a slot: the transcription declares every property it holds
        undeclared = {k for k in row["claim"]["props"] if renamed.get(k, k) not in fields and k not in emit.OWNED}
        assert undeclared <= {"id"}, f"{type(inst).__name__}: {undeclared} ride only in source_item"


def test_prov_method_is_an_edge_slot_and_is_written(emit, graph, classes):
    row = _edge("conflicts_with", "cl1", "cl2", grounding_span="they disagree", prov_method="cross_document_pass",
                prov_doc=DOC, kind="contradiction", source="judge", adjudicated=True, grounding_span_to="no")
    e = _one(emit, graph, classes, row)
    assert type(e).__name__ == "ConflictsWith"
    assert "prov_method" in type(e).model_fields
    assert (e.prov_method, e.prov_doc) == ("cross_document_pass", DOC)
    assert (e.qualified_kind, e.qualified_source, e.adjudicated, e.grounding_span_to) == ("contradiction", "judge",
                                                                                         True, "no")
    assert json.loads(e.source_item)["kind"] == "contradiction"      # the item as asserted, unchanged


# ------------------------------------------------------------------------------------------ R-221: year is an integer


@pytest.mark.parametrize("asserted,written", [(2024, 2024), ("2017", 2017), (" 2020 ", 2020), (0, 0)])
def test_year_is_written_as_an_integer(emit, graph, classes, asserted, written):
    i = _one(emit, graph, classes, _node("Instrument", "i1", **{**INSTRUMENT, "year": asserted}))
    assert i.year == written and type(i.year) is int
    assert json.loads(i.source_item)["year"] == asserted              # source_item keeps the value as asserted


@pytest.mark.parametrize("asserted", ["", "n.d.", "2011–2014", "began in the early 1960s"])
def test_a_year_with_no_integer_form_leaves_the_slot_absent_and_keeps_the_value(emit, graph, classes, asserted):
    """The four forms the adopted records hold (SQ-022b, docs/evidence/sq022b/year_not_integer.jsonl in squiddy)."""
    i = _one(emit, graph, classes, _node("Framework", "f1", name="F", year=asserted,
                                         grounding_span="F frames the field"))
    assert i.year is None
    assert json.loads(i.source_item)["year"] == asserted


# ------------------------------------------------------------------------------------------ _coerce, per scalar type


def test_coerce_writes_each_scalar_type_the_schema_declares(emit, classes):
    Ins, Doc, Con = classes["Instrument"], classes["Document"], classes["Concept"]
    # integer
    assert emit._coerce(Ins, "year", "2017") == 2017 and emit._coerce(Ins, "year", 2017) == 2017
    assert emit._coerce(Ins, "year", 2017.0) == 2017
    assert emit._coerce(Ins, "year", "") is None and emit._coerce(Ins, "year", "about 2017") is None
    with pytest.raises(SystemExit, match="year"):                       # a boolean is a type confusion, not text
        emit._coerce(Ins, "year", True)
    with pytest.raises(SystemExit, match="year"):
        emit._coerce(Ins, "year", ["2017"])
    with pytest.raises(SystemExit, match="year"):
        emit._coerce(Ins, "year", True)
    # boolean
    assert emit._coerce(Doc, "is_platform_operator", False) is False
    assert emit._coerce(Doc, "is_platform_operator", True) is True
    # string: a number the extractor wrote is its decimal string; a structure is its JSON
    assert emit._coerce(Ins, "owner", 7) == "7" and emit._coerce(Ins, "owner", "Lab") == "Lab"
    assert emit._coerce(Ins, "attribute_anchors", {"owner": "Lab"}) == '{"owner": "Lab"}'
    # multivalued
    assert emit._coerce(Con, "aliases", ["a", 2]) == ["a", "2"] and emit._coerce(Con, "aliases", "a") == ["a"]


# ------------------------------------------------------------------------------------------ R-220: grounding_thin


def test_grounding_thin_is_built_by_the_projections_own_rule(emit, graph, classes):
    thin = _one(emit, graph, classes, _node("Concept", "c1", name="RDF", grounding_span="RDF 1.1"))
    full = _one(emit, graph, classes, _node("Concept", "c2", name="RDF",
                                            grounding_span="RDF is the W3C framework for describing resources"))
    unnamed = _one(emit, graph, classes, _node("Claim", "cl9", claim_text="x", grounding_span="x",
                                               evidence_grade="inference"))
    assert thin.grounding_thin is True
    assert full.grounding_thin is None and unnamed.grounding_thin is None     # absent, as the old store left it
    bp = emit._projection(graph)
    assert bp.is_thin_span("RDF 1.1", "RDF") and not bp.is_thin_span(
        "RDF is the W3C framework for describing resources", "RDF")


# ------------------------------------------------------------------------------------------ R-219: the Document


def test_the_acquisition_fold_is_the_projections(emit, graph):
    """manifest_add SETs source_type and pub_date (a null removes) and coalesces construct_arm and grounding_surface;
    a document_annotation SETs is_platform_operator or construct_arm; in log order (build_projection `build`)."""
    bp = emit._projection(graph)
    events = [
        {"event_type": "manifest_add", "payload": {"doc_id": "a", "source_type": "federal", "pub_date": "2020",
                                                   "construct_arm": "org_maturity", "content_hash": "h0"}},
        {"event_type": "document_annotation", "doc_id": "a", "property": "is_platform_operator", "value": False},
        {"event_type": "document_annotation", "doc_id": "a", "property": "construct_arm",
         "value": "publication_actionability"},
        {"event_type": "document_annotation", "doc_id": "a", "property": "not_whitelisted", "value": 1},
        {"event_type": "manifest_add", "payload": {"doc_id": "a", "source_type": "academic", "pub_date": None,
                                                   "construct_arm": None, "grounding_surface": "slides"}},
    ]
    fold = emit.acquisition_fold(events, bp, skip_reason=lambda ev: None)
    assert fold["a"] == {"source_type": "academic", "construct_arm": "publication_actionability",
                         "is_platform_operator": False, "grounding_surface": "slides", "content_hash": None,
                         "pub_date": None}


def test_a_document_takes_manifest_add_values_and_the_kits_content_hash(emit, graph, classes, monkeypatch):
    rec = {"identity": {"pub_year": "2022", "doc_type": "standard", "sha256": "dixie-sha", "authors_or_org": ["W3C"]}}
    entry = {"id": "doc-a", "kind": "document", "title": "A", "sha256": "kit-sha", "local_path": "/x",
             "dixie_record": json.dumps(rec)}
    monkeypatch.setattr(emit, "_ACQ", {"doc-a": {"source_type": "academic", "pub_date": "n.d.",
                                                 "construct_arm": "org_maturity", "is_platform_operator": False,
                                                 "content_hash": "old-sha"}})
    (d,) = emit.emit(entry, None, graph, classes)
    assert (d.source_type, d.pub_date, d.construct_arm, d.is_platform_operator) == ("academic", "n.d.",
                                                                                   "org_maturity", False)
    assert d.content_hash == "kit-sha"                    # the kit's measurement, never either catalog's
    assert "pub_date" not in emit.manifest_projection(entry, graph)    # not a manifest field any more


def test_without_a_manifest_add_value_the_dixie_catalog_answers(emit, graph, classes, monkeypatch):
    rec = {"identity": {"pub_year": "2022", "doc_type": "standard", "sha256": "s"}}
    entry = {"id": "doc-b", "kind": "document", "title": "B", "sha256": "s", "dixie_record": json.dumps(rec)}
    monkeypatch.setattr(emit, "_ACQ", {"doc-b": {"source_type": None, "pub_date": None}})
    (d,) = emit.emit(entry, None, graph, classes)
    assert (d.pub_date, d.source_type, d.construct_arm, d.is_platform_operator) == ("2022", "standard", None, None)
    rec2 = {"identity": {"pub_year": None, "doc_type": "platform"}}          # outside source_type's closed list
    entry2 = {**entry, "id": "doc-c", "dixie_record": json.dumps(rec2)}
    monkeypatch.setattr(emit, "_ACQ", {})
    (d2,) = emit.emit(entry2, None, graph, classes)
    assert d2.source_type is None and d2.doc_type == "platform"
