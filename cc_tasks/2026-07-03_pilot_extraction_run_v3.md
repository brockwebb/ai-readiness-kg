# CC Task — Pilot Extraction Run v3 (provenance-ownership fix + full run)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md. Conflicts = STOP and report.
**Supersedes:** cc_tasks/2026-07-03_pilot_extraction_run_v2.md (ec39ac62 — clean STOP at doc 1 on an envelope contract defect: harness rejected output over document_id, a field the harness itself owns. Invocation path (claude -p / Fable / Agent SDK credit) is proven and carries forward unchanged.)

## Fix first — provenance ownership contract (root cause, not the one-line patch)

Principle: **harness-owned fields are injected by the harness and never requested from, or trusted from, the model.** Harness-owned: document_id, extraction_event_id, model_id (from the response envelope, not the model's text), schema_version, timestamps. Model-owned: nodes, edges, grounding spans, extract plan.

1. pipeline.extract_document: inject `document_id` (and any other harness-owned fields) into the output before parse — CC's proposed injection, adopted.
2. **Strip harness-owned fields from the prompt template and output_schema.json** if either asks the model to emit them — the model can't echo an id it was never given, and shouldn't be asked to.
3. If the model nonetheless emits a harness-owned field, discard it and log a warning (don't fail, don't trust).
4. Tests updated to cover: injection, strip-and-warn, and that a model-emitted conflicting document_id never reaches an event.

## Run

Re-run the full v2 protocol unchanged — preflight smoke call, sequential order (Lawrence → FCSM 25-03 → MLMU-25 → AIDRIN → Cisco 2025), doc-1 integrity checkpoint, one call per doc, verbatim-retry on transport errors only.

Gates carry forward verbatim and in force: quarantine > 10% per doc → STOP; concept density < 2.0/1k flagged; gates not adjustable mid-run; credit exhaustion = STOP, no usage credits.

The discarded doc-1 output from v2 is not salvaged or replayed — no event chain, no provenance, it does not exist. Fresh call.

## Deliverables

Per v2: extraction/validation events, per-doc metrics (events + committed file), pilot audit summary at docs/research/pilot_extraction_summary.md (facts only: metrics table, quarantine specimens, full proposed_relationships inventory with spans, protocol friction, per-call usage accounting incl. cumulative pilot spend across v2+v3). `seldon cc complete cc_tasks/2026-07-03_pilot_extraction_run_v3.md`; `seldon verify` clean.

## Out of scope

Schema patching. Ingested transitions. Docs beyond the 5. Bulk extraction forbidden regardless of pilot cleanliness.
