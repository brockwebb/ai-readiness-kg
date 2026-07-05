"""State machine, metrics, event-log replay, and projection rebuild.

- extraction without a manifest_add event fails (§7);
- a full run emits the correct events and advances state to validated;
- metrics computed correctly on a synthetic fixture;
- extraction events replay cleanly and the projected state is reproducible from replay.
"""
import pytest

from kg import eventlog
from kg.extraction import metrics as metrics_mod
from kg.extraction import parser, pipeline, state
from kg.extraction.schema_loader import load_schema

SCHEMA = load_schema()


def seed_manifest_add(doc_id: str, batch: int = 1) -> str:
    """Append a real manifest_add event so a doc is in state manifest_added."""
    return eventlog.append(
        {"event_type": "manifest_add", "payload": {"doc_id": doc_id, "content_hash": "x"}},
        batch=batch,
    )
SOURCE = (
    "AI readiness is a construct describing organizational preparedness. "
    "The FCSM defines data quality as fitness for use."
)


def _output(doc_id="doc-1"):
    # A real model output does NOT carry document_id — the harness injects it (v3 contract).
    return {
        "extract_plan": {"section_map": [], "concept_inventory": []},
        "concepts": [{"id": "c1", "name": "AI readiness",
                      "grounding_span": "AI readiness is a construct", "location": "p1"}],
        "definitions": [{"id": "d1", "term": "data quality",
                         "grounding_span": "The FCSM defines data quality as fitness for use",
                         "location": "p1"}],
        "edges": [{"type": "mentions", "from_id": doc_id, "to_id": "c1",
                   "grounding_span": "AI readiness is a construct", "location": "p1"}],
        "cites": [],
        "proposed_relationships": [
            {"suggested_edge": "presupposes", "from_id": "c1", "to_id": "d1",
             "grounding_span": "AI readiness is a construct", "note": "x"}],
    }


# --- state machine --------------------------------------------------------------------

def test_extraction_without_manifest_added_fails(ext_iso):
    assert state.current_state("doc-1") == "discovered"
    with pytest.raises(state.ExtractionError, match="manifest_added"):
        pipeline.extract_document("doc-1", SOURCE, output=_output())


def test_full_run_advances_state_and_emits_events(ext_iso):
    seed_manifest_add("doc-1")
    assert state.current_state("doc-1") == "manifest_added"

    summary = pipeline.extract_document("doc-1", SOURCE, output=_output())
    assert state.current_state("doc-1") == "validated"

    events = list(eventlog.replay())
    by_type = {}
    for e in events:
        by_type.setdefault(e["event_type"], []).append(e)
    # transitions extracted + validated, one build_metrics, node/edge assertions
    transitions = [(e["from_state"], e["to_state"]) for e in by_type.get("doc_state", [])]
    assert ("manifest_added", "extracted") in transitions
    assert ("extracted", "validated") in transitions
    assert len(by_type.get("node_asserted", [])) == 2   # c1, d1
    assert len(by_type.get("edge_asserted", [])) == 1   # mentions
    assert len(by_type.get("build_metrics", [])) == 1

    # every extracted item carries the §4 provenance stamp. model_id defaults to the config
    # pin when no envelope override is supplied (operator-tunable — Fable pilot, Opus bulk).
    from kg.extraction import model_stub
    pinned = model_stub.load_model_config()["model_id"]
    for e in by_type.get("node_asserted", []) + by_type.get("edge_asserted", []):
        prov = e["provenance"]
        assert prov["model_id"] == pinned
        assert prov["schema_version"] == "0.1"  # ext_iso patches a tmp schema at 0.1
        assert prov["prompt_version"] == "0.2.0"
        assert prov["extraction_event_id"] == summary["extraction_event_id"]
        assert prov["timestamp"]


def test_proposed_relationships_staged_not_emitted(ext_iso):
    seed_manifest_add("doc-1")
    pipeline.extract_document("doc-1", SOURCE, output=_output())
    # proposed_relationships never appear as graph assertion events
    assert not any(e["event_type"].endswith("_asserted") and "presupposes" in str(e)
                   for e in eventlog.replay())
    staged = ext_iso / "proposed" / "doc-1.jsonl"
    assert staged.is_file() and "presupposes" in staged.read_text()


def test_document_id_injected_when_model_omits_it(ext_iso):
    seed_manifest_add("doc-1")
    out = _output("doc-1")
    assert "document_id" not in out  # model didn't emit it
    summary = pipeline.extract_document("doc-1", SOURCE, output=out)  # succeeds via injection
    assert state.current_state("doc-1") == "validated"
    assert summary["result"].document_id == "doc-1"


def test_model_emitted_document_id_stripped_and_never_reaches_event(ext_iso, recwarn):
    seed_manifest_add("doc-1")
    out = _output("doc-1")
    out["document_id"] = "WRONG-ID-FROM-MODEL"          # model tries to own a harness field
    out["model_id"] = "not-the-real-model"              # another harness-owned field
    pipeline.extract_document("doc-1", SOURCE, output=out)
    # warned about the harness-owned emission
    assert any("harness-owned" in str(w.message) for w in recwarn.list)
    # the model's forged id never reaches any event
    for e in eventlog.replay():
        assert "WRONG-ID-FROM-MODEL" not in str(e)
        if e.get("event_type", "").endswith("_asserted"):
            assert e["doc_id"] == "doc-1"


# --- metrics --------------------------------------------------------------------------

def test_metrics_computed_on_fixture():
    # calling the parser directly (not via pipeline) so supply the harness-owned document_id
    result = parser.parse_extraction({**_output(), "document_id": "doc-1"}, SOURCE, SCHEMA)
    m = metrics_mod.compute("doc-1", SOURCE, result)
    assert m["concepts"] == 1
    assert m["definitions_count"] == 1
    assert m["nodes"] == 2 and m["edges"] == 1
    assert m["quarantine_rate"] == 0.0
    assert m["proposed_relationships_count"] == 1
    # density: 1 concept over estimated tokens
    expected_tokens = metrics_mod.estimate_tokens(SOURCE)
    assert m["estimated_tokens"] == expected_tokens
    assert m["concepts_per_1k_tokens"] == round(1 / (expected_tokens / 1000), 4)


def test_metrics_quarantine_rate():
    out = {**_output(), "document_id": "doc-1"}
    out["concepts"] = out["concepts"] + [{"id": "cbad", "name": "x", "grounding_span": "absent from source"}]
    result = parser.parse_extraction(out, SOURCE, SCHEMA)
    m = metrics_mod.compute("doc-1", SOURCE, result)
    # 2 nodes + 1 edge + 1 quarantined = 4 items; 1 quarantined
    assert m["quarantine_rate"] == round(1 / 4, 4)


# --- event-log replay + projection rebuild --------------------------------------------

def test_events_replay_cleanly_and_state_reproducible(ext_iso):
    seed_manifest_add("doc-1")
    pipeline.extract_document("doc-1", SOURCE, output=_output())

    # replay is clean (no corrupt lines) and yields a stable count
    first = list(eventlog.replay())
    second = list(eventlog.replay())
    assert len(first) == len(second) and len(first) > 0

    # projection: reconstruct node count from node_asserted events
    projected_nodes = [e for e in first if e["event_type"] == "node_asserted"
                       and e["doc_id"] == "doc-1"]
    assert len(projected_nodes) == 2

    # state is reproducible purely from replay
    assert state.current_state("doc-1") == "validated"


def test_manifest_add_in_batch1_extraction_in_batch2(ext_iso):
    seed_manifest_add("doc-1")  # batch 1
    pipeline.extract_document("doc-1", SOURCE, output=_output())  # batch 2
    assert (ext_iso / "events" / "batch-001.jsonl").is_file()
    assert (ext_iso / "events" / "batch-002.jsonl").is_file()


# --- bulk v1 run-driver seams (task 2026-07-05_airkg_bulk_extraction_v1) ---------------

def test_extraction_batch_resolves_at_call_time(ext_iso):
    seed_manifest_add("doc-1")
    old = state.EXTRACTION_BATCH
    state.EXTRACTION_BATCH = 4
    try:
        pipeline.extract_document("doc-1", SOURCE, output=_output())
    finally:
        state.EXTRACTION_BATCH = old
    assert (ext_iso / "events" / "batch-004.jsonl").is_file()
    assert not (ext_iso / "events" / "batch-002.jsonl").exists()


def test_extra_provenance_stamped_and_protected(ext_iso):
    seed_manifest_add("doc-1")
    pipeline.extract_document(
        "doc-1", SOURCE, output=_output(),
        extra_provenance={"corpus_epoch": "v1", "source_sha256": "ab" * 32})
    stamped = [e for e in eventlog.replay() if e["event_type"] == "node_asserted"]
    assert stamped and all(
        e["provenance"]["corpus_epoch"] == "v1"
        and e["provenance"]["source_sha256"] == "ab" * 32 for e in stamped)

    import pytest as _pytest
    with _pytest.raises(ValueError, match="may not override"):
        pipeline.extract_document("doc-1", SOURCE, output=_output(),
                                  extra_provenance={"model_id": "spoof"})
