# CC Task — Pilot Extraction Run (5 documents, Fable)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md. Conflicts with this task = STOP and report.
**Predecessor:** cc_tasks/2026-07-03_extraction_module.md (module built, 50 tests).

## Precondition rider — strict index-pairing (do FIRST, before any extraction)

Replace the set-membership endpoint gate with strict index-pairing: add pairing metadata to schema.yaml (each edge type lists its legal (from_type, to_type) pairs per schema §3), update parser/schema_loader, update tests. A cross-pair edge on a whitelisted type (e.g. extends: Definition→Framework) must route to proposed_relationships, not the graph — this preserves the §9 expressiveness measurement. All tests pass before proceeding.

## Pre-registered gates (set now, before seeing data)

- **Per-document STOP:** grounding quarantine rate > 10% on any document → STOP the run after that document, report, no further extraction.
- **Concept density:** report concepts/1k tokens per doc. No hard gate — pilot is the measurement — but flag any doc below 2.0/1k in the summary as a candidate thin layer.
- Gates are not adjustable mid-run for any reason.

## Run protocol

1. Model: claude-fable-5 via Claude Max OAuth (model stub → real client). Hard-fail if ANTHROPIC_API_KEY is present in the environment.
2. One document per call, full document in context, §5 emission order. Sequential, fixed order:
   1. Lawrence DRL (shortest, cleanest — protocol shakeout)
   2. FCSM 25-03
   3. MLMU-25
   4. AIDRIN
   5. Cisco AI Readiness Index 2025
3. After document 1: verify end-to-end integrity (events written, grounding validation ran, metrics emitted, state = validated) before proceeding to document 2. Any pipeline defect → STOP, fix is a new task.
4. All writes through the module: parser gate, grounding validator, event log, state transitions manifest_added → extracted → validated. Ingested state is NOT set in this task — ingestion is post-audit.
5. proposed_relationships staged per doc for operator review. Quarantined items retained with reasons.

## Deliverables

1. Extraction + validation events for up to 5 docs in the sharded log.
2. Per-doc metrics (concepts/1k tokens, definitions count, claims count, quarantine rate, proposed_relationships count) as events + committed metrics file.
3. **Pilot audit summary** at docs/research/pilot_extraction_summary.md (committed): the §9 audit inputs — per-doc metrics table, quarantine specimens (each quarantined span + reason), full proposed_relationships inventory with grounding spans, any protocol friction observed. Facts only; no schema-patch recommendations — that's the operator's audit.
4. Token/usage accounting per call as reported by the API, in the summary.
5. `seldon cc complete cc_tasks/2026-07-03_pilot_extraction_run.md`; `seldon verify` clean.

## Out of scope

- Schema patching (post-audit Desktop decision, then a new task).
- Ingested state transitions.
- Any document beyond the 5. Bulk extraction is forbidden regardless of how clean the pilot runs.
- Retry-with-prompt-tweaks on a bad extraction: one call per document. A failed call (API error) may be retried once verbatim; a *bad* extraction is data, not a defect to hide.
