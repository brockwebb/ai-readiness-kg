# CC Task — Pilot Extraction Run v2 (claude -p invocation path)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md. Conflicts = STOP and report.
**Supersedes:** cc_tasks/2026-07-03_pilot_extraction_run.md (080956ad — blocked on auth precondition; its "bare Anthropic() client on OAuth profile" premise was unsanctioned. Strict index-pairing rider from v1 is DONE and carries forward; do not redo.)

## Corrected invocation path (Desktop-verified against Anthropic docs, 2026-07-03)

As of 2026-06-15, subscription plans carry a monthly Agent SDK credit covering `claude -p` and Agent SDK usage under the existing OAuth login — no API key. Reference: https://support.claude.com/en/articles/15036540

Implement `model_stub.invoke()` as a subprocess call to `claude -p`:

- `claude -p --model claude-fable-5 --output-format json` (exact flags per current `claude --help`; use structured/JSON output so the extraction envelope is machine-parsed).
- **Never pass `--bare`** — bare mode skips OAuth and demands ANTHROPIC_API_KEY (https://code.claude.com/docs/en/headless).
- Existing guard stays and extends: hard-fail if ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is set in the environment. Subscription OAuth only.
- Prompt template + full document text delivered via stdin/prompt argument; the extraction JSON is parsed from the response envelope. Restrict the subprocess call's tool permissions to none/minimum — this is a pure completion, not an agentic run.
- Record in each extraction event: model_id as reported in the response envelope (verify it is claude-fable-5, not a fallback), usage/token accounting from the envelope.
- **Preflight (before doc 1):** one trivial `claude -p --model claude-fable-5` smoke call ("reply with OK"). If the model id is rejected or unavailable on this plan → STOP and report; do not substitute another model.

## Pre-registered gates (unchanged from v1, restated verbatim in force)

- Per-document STOP: grounding quarantine rate > 10% on any document → STOP after that document.
- Concept density reported per doc; flag < 2.0 concepts/1k tokens as candidate thin layer. No hard gate.
- Gates not adjustable mid-run for any reason.
- Agent SDK credit exhaustion mid-run (requests stop) = STOP and report with docs completed so far. Do not enable usage credits, do not retry-wait loops.

## Run protocol (unchanged from v1)

1. Sequential, fixed order: Lawrence DRL → FCSM 25-03 → MLMU-25 → AIDRIN → Cisco 2025.
2. Integrity checkpoint after doc 1 (events, grounding validation, metrics, state = validated) before doc 2. Pipeline defect → STOP; fix is a new task.
3. All writes through the module. States: manifest_added → extracted → validated. No `ingested` — post-audit only.
4. One call per document. API/transport error: one verbatim retry. A bad extraction is data, not a defect to hide.
5. proposed_relationships staged; quarantined items retained with reasons.

## Deliverables (unchanged from v1)

1. Extraction + validation events in the sharded log.
2. Per-doc metrics (concepts/1k tokens, definitions, claims, quarantine rate, proposed_rel count) as events + committed file.
3. Pilot audit summary at docs/research/pilot_extraction_summary.md — §9 audit inputs, facts only: metrics table, quarantine specimens with reasons, full proposed_relationships inventory with grounding spans, protocol friction, per-call usage accounting.
4. `seldon cc complete cc_tasks/2026-07-03_pilot_extraction_run_v2.md`; `seldon verify` clean.

## Out of scope

- Schema patching. Ingested transitions. Any document beyond the 5. Bulk extraction forbidden regardless of pilot cleanliness.
