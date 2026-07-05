#!/usr/bin/env python3
"""Extraction orchestrator (schema_v0.1.md §5 + §7). Ties the components together:

  require manifest_added -> parse+validate output -> emit assertion events (§4-stamped)
  -> record build metrics -> stage proposed_relationships -> advance state to validated.

No LLM call happens in the module-build task: ``extract_document`` takes an already-produced
extraction ``output`` (from a fixture, or later from the operator-gated model run). If
``output`` is None it asks the stub to invoke the model, which raises by design.
"""
from __future__ import annotations

import warnings

from kg import eventlog

from . import metrics as metrics_mod
from . import model_stub, parser, schema_loader, staging, state

# Harness-owned provenance fields (v3 provenance-ownership contract): the harness injects
# these and never trusts them from the model. document_id is the doc being extracted;
# extraction_event_id/model_id/schema_version/timestamp are stamped per item at event-write
# (§4). If the model emits any of them, they are stripped and warned — never trusted.
HARNESS_OWNED_FIELDS = (
    "document_id", "extraction_event_id", "model_id", "schema_version", "timestamp",
)


def _apply_provenance_ownership(output: dict, doc_id: str) -> dict:
    """Strip any harness-owned fields the model emitted (discard + warn), then inject the
    authoritative document_id. Model-owned content (nodes, edges, spans) is untouched."""
    emitted = [k for k in HARNESS_OWNED_FIELDS if k in output]
    if emitted:
        warnings.warn(
            f"model emitted harness-owned field(s) {emitted} for '{doc_id}'; discarding "
            f"(harness owns provenance)", stacklevel=2)
    cleaned = {k: v for k, v in output.items() if k not in HARNESS_OWNED_FIELDS}
    cleaned["document_id"] = doc_id  # authoritative; the model's value never reaches an event
    return cleaned


def extract_document(doc_id: str, source_text: str, output: dict | None = None,
                     model_meta: dict | None = None,
                     extra_provenance: dict | None = None) -> dict:
    """Run the extraction pipeline for one document. Returns a summary dict with the
    ExtractionResult, computed metrics, and the extraction_event_id.

    ``output`` is the parsed extraction envelope; ``model_meta`` (from model_stub.invoke)
    carries the reported model_id + usage. If ``output`` is None the model is invoked here.
    ``extra_provenance`` (harness-owned, e.g. corpus_epoch + source doc sha256 for the bulk
    run) is merged into every item's §4 stamp — it may not override stamp-owned keys.

    Preconditions (fail loud, §7): the document must have reached ``manifest_added`` — a
    document with no manifest_add event cannot be extracted."""
    state.require_state(doc_id, "manifest_added")

    schema = schema_loader.load_schema()
    extraction_event_id = state.new_extraction_event_id()

    if output is None:
        model_meta = model_stub.invoke(doc_id, source_text)
        output = model_meta["output"]

    output = _apply_provenance_ownership(output, doc_id)
    result = parser.parse_extraction(output, source_text, schema)
    reported_model = (model_meta or {}).get("model_id")
    provenance = model_stub.provenance_stamp(extraction_event_id, model_id=reported_model)
    if extra_provenance:
        collisions = set(extra_provenance) & set(provenance)
        if collisions:
            raise ValueError(f"extra_provenance may not override stamp keys: {sorted(collisions)}")
        provenance = {**provenance, **extra_provenance}

    # extracted: emit one §4-stamped assertion event per surviving node/edge.
    state.transition(doc_id, "extracted")
    for node in result.nodes:
        state.assert_item(doc_id, "node_asserted", extraction_event_id, provenance, node)
    for edge in result.edges:
        state.assert_item(doc_id, "edge_asserted", extraction_event_id, provenance, edge)

    # build metrics -> event + file (§5.6).
    metrics = metrics_mod.compute(doc_id, source_text, result)
    metrics_mod.write_metrics_file(metrics)
    eventlog.append(
        {"event_type": "build_metrics", "doc_id": doc_id,
         "extraction_event_id": extraction_event_id, "metrics": metrics},
        batch=state.EXTRACTION_BATCH,
    )

    # model call accounting -> event (§ usage accounting), when a real invocation happened.
    if model_meta:
        eventlog.append(
            {"event_type": "model_call", "doc_id": doc_id,
             "extraction_event_id": extraction_event_id,
             "model_id": model_meta.get("model_id"), "usage": model_meta.get("usage"),
             "cost_usd": model_meta.get("cost_usd"), "duration_ms": model_meta.get("duration_ms")},
            batch=state.EXTRACTION_BATCH,
        )

    # proposed_relationships -> review staging (never the graph, §6).
    staging.stage(doc_id, result.proposed_relationships)

    # Grounding was validated during parse; advance to validated.
    state.transition(doc_id, "validated")

    return {"extraction_event_id": extraction_event_id, "result": result,
            "metrics": metrics, "model_meta": model_meta}
