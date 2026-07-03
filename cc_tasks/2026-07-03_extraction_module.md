# CC Task — Extraction Module Build

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md is the spec. Where this task and the schema doc disagree, STOP and report — do not reconcile silently.

## Objective

Build the extraction module implementing schema §5 (whole-document protocol) and §7 (state machine). Module build + tests only. **No LLM extraction calls in this task** — the pilot run on the 5 docs is a separate, operator-gated task.

## Components

1. **Extraction prompt template** — implements §5 emission order: extract plan (section map + concept inventory) → Concepts (exhaustive) → Definitions → Claims → Instruments/Measures → edges → cites → proposed_relationships block. Output is strict JSON; template lives as a versioned file in the module, not inline code strings.
2. **Output schema + parser** — JSON schema validating the extraction output against node/edge types (schema §2–3). Edge whitelist enforced: any edge type not in schema.yaml is rejected at parse, routed to proposed_relationships, never written.
3. **Mechanical grounding validator** — string-match every grounding_span against source text, whitespace/OCR-tolerant (collapse whitespace; tolerate hyphenation breaks and common OCR ligature substitutions). Miss = item quarantined with reason, not ingested. No grounding span, no write (§4) — enforced in code, not convention.
4. **Event writer** — all graph writes through the sharded event log via existing infrastructure. Document state transitions per §7: manifest_added → extracted → validated → ingested. Attempting extraction on a doc without a manifest_added event = hard error.
5. **Per-document build metrics** — concepts per 1k tokens, definitions count, quarantine rate, proposed_relationships count. Written as an event and to a metrics file. These feed the pilot audit (§9) and the autonomy-ramp QC.
6. **proposed_relationships staging** — staged to a review file/area for operator batch review (§6). Never touches the graph.
7. **Model invocation stub** — Claude Max OAuth only (no ANTHROPIC_API_KEY anywhere; audit any .env the module reads). model_id, schema_version, extraction_event_id, timestamp stamped on every extracted item (§4). Model per schema: Fable.

## Riders (small, in-scope)

- **R1 — source_type enum:** amend the draft schema (docs/schema_v0.1.md §2 Document row + schema.yaml if enum lives there) to add `intergovernmental` to source_type, with a one-line note (policy bodies: OECD, UNESCO, UNDP, IADB, PARIS21, EU JRC, UN; SDOs like ITU/ISO stay `standard`). Correct the 8 affected candidate_register.jsonl entries. Schema is still draft/unlocked; record the amendment in the doc's changelog or header.
- **R2 — Seldon tracking:** register corpus/manifest.json (and the module's schema.yaml) as Seldon-tracked content so `seldon verify` has files to hash-check. Closes the "0 tracked files" gap from the pilot-adds run.

## Tests (fixtures only, no API calls)

- Grounding validator: exact match, whitespace variance, hyphenation break, OCR ligature, genuine miss → quarantine.
- Parser: valid output accepted; unknown edge type rejected to proposed_relationships; missing grounding_span rejected.
- State machine: extraction attempt without manifest_added event fails; correct transition sequence emits correct events.
- Metrics: computed correctly on a synthetic fixture.
- Event log: extraction events replay cleanly; projection rebuild reproduces state.

## Acceptance criteria

1. Module + tests pass; test count and coverage summary in report.
2. Zero LLM calls made; zero API keys introduced.
3. R1 and R2 done; register corrections logged.
4. `seldon cc complete cc_tasks/2026-07-03_extraction_module.md`; `seldon verify` clean (now with tracked files).

## Out of scope

- Running extraction on any pilot document (next task, operator-gated).
- Large-document chunked protocol (§5, case-by-case later).
- Construct promotion tooling (curated events, later).
- crosswalk DOI manifest-add (task cc082aaa).
