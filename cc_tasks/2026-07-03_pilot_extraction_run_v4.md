# CC Task — Pilot Extraction Run v4 (extraction model → Opus 4.8)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md. Conflicts = STOP and report.
**Supersedes:** cc_tasks/2026-07-03_pilot_extraction_run_v3.md (f7249d86 — model pin invalidated by product change: Fable 5 moves to usage-credit billing after 2026-07-07 and its redeployed cyber classifier auto-reroutes blocked requests to Opus 4.8, an unacceptable silent-model-substitution hazard for a security-adjacent corpus. The v3 provenance-ownership fix is REQUIRED and carries forward — do it exactly as v3 specifies if not already done.)

## Model change (Desktop decision, 2026-07-03)

- Extraction model: **claude-opus-4-8** for pilot AND bulk. Rationale on record: pilot/bulk model continuity, no July 7 billing cliff, no classifier-reroute heterogeneity, subscription-covered.
- Update model_config.yaml. The stub's guards stay: no ANTHROPIC_API_KEY, no ANTHROPIC_AUTH_TOKEN, no --bare.
- Preflight smoke call verifies claude-opus-4-8 is served. **Per-call check:** if any response envelope reports a model_id other than claude-opus-4-8, that document's output is discarded unparsed, the event records the substitution, and the run STOPs. Model identity is a gate, not a log line.

## Rider — make schema §5 model-agnostic

Amend docs/schema_v0.1.md §5: the protocol (whole-document, single call, emission order) lives in the schema; the model is pinned in model_config.yaml and stamped per item via §4. Replace the hardcoded model name with that language; note the amendment in the doc header. Draft schema, still unlocked — this is the last pre-pilot amendment.

## Everything else carries forward from v3/v2 verbatim and in force

- v3 provenance-ownership fix (harness-owned fields injected, stripped from prompt/schema, strip-and-warn).
- claude -p invocation under the Agent SDK subscription credit; no --bare.
- Gates: quarantine > 10% per doc → STOP; density < 2.0/1k flagged; gates immutable mid-run; credit exhaustion = STOP, never usage-credit spillover.
- Protocol: preflight → Lawrence → integrity checkpoint → FCSM 25-03 → MLMU-25 → AIDRIN → Cisco 2025. One call per doc; verbatim retry on transport errors only; bad extraction is data.
- States end at validated; no ingested.
- Deliverables: events, per-doc metrics (events + file), pilot audit summary at docs/research/pilot_extraction_summary.md (facts only, incl. cumulative pilot spend v2+v3+v4). `seldon cc complete cc_tasks/2026-07-03_pilot_extraction_run_v4.md`; `seldon verify` clean.

## Out of scope

Schema patching beyond the §5 rider. Ingested transitions. Docs beyond the 5. Bulk extraction forbidden regardless of pilot cleanliness.
