# CC Task — Pilot Extraction Run v5 (model pin: Fable, operator decision)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md. Conflicts = STOP and report.
**Supersedes:** cc_tasks/2026-07-03_pilot_extraction_run_v4.md (0a7bc052 — never executed. Operator decision reverses the model swap: run Fable now while subscription-included; post-July-7 budget is operator-managed via token allocation. Everything in v4 except the model pin carries forward.)

## Model pin

- Extraction model: **claude-fable-5**. model_config.yaml set accordingly.
- **Model-identity hard gate (unchanged from v4, now load-bearing):** preflight smoke call verifies claude-fable-5 is served; any per-call envelope reporting a different model_id (including a classifier reroute to Opus 4.8) → that document's output discarded unparsed, substitution recorded in an event, run STOPs. This gate is what makes the Fable pin safe.
- Auth guards unchanged: no ANTHROPIC_API_KEY, no ANTHROPIC_AUTH_TOKEN, no --bare.

## Carries forward verbatim and in force

- v3 provenance-ownership fix (required precondition if not already applied).
- v4 rider: schema §5 amended model-agnostic — protocol in schema, model in model_config.yaml, stamped per item (§4).
- claude -p invocation under subscription; gates (quarantine > 10%/doc → STOP; density < 2.0/1k flagged; gates immutable mid-run; usage exhaustion = STOP, never spillover).
- Protocol: preflight → Lawrence → integrity checkpoint → FCSM 25-03 → MLMU-25 → AIDRIN → Cisco 2025. One call per doc; verbatim retry on transport errors only; bad extraction is data.
- States end at validated. Deliverables per v3/v4 incl. cumulative pilot spend accounting. `seldon cc complete cc_tasks/2026-07-03_pilot_extraction_run_v5.md`; `seldon verify` clean.

## Out of scope

Schema patching beyond the §5 rider. Ingested transitions. Docs beyond the 5. Bulk extraction forbidden regardless of pilot cleanliness.
