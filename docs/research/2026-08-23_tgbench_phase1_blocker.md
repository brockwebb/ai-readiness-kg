# TrustGraph benchmark — Phase 1 blocker (task `2026-08-23_trustgraph_benchmark`, Seldon b6900da4)

**Date:** 2026-08-23. **Phase 1 outcome:** STOPPED before deployment. **Deploy time spent:** 0 min (no `npx @trustgraph/config`, no docker invoked).

## The blocker

The task's Mode rule makes Gemini Flash via "the existing Google AI Studio credentials" the sole LLM for both extractors and says: *"If no Google credential is configured, STOP at Phase 1 and record the blocker; do not substitute another provider."* There is no live Google credential on this machine.

## Evidence (values redacted; fingerprints are sha256 prefixes)

`~/.wintermute/.env` lines 5–8, verbatim apart from the redaction:

```
5  # GEMINI_API_KEY REMOVED 2026-08-13 (S21 Part 1). Key sha256:3ee221ca4626 revoked in
6  # the Google console by the operator. Vendor retirement =<REDACTED>
7  # See docs/decisions/2026-08-13_google-spend-incident.md
8  # GOOGLE_API_KEY REMOVED 2026-08-13 (S21 Part 1) — see above.
```

`~/.wintermute/docs/decisions/2026-08-13_google-spend-incident.md` header: *"CLOSED. Kill verified GREEN 2026-08-14 — operator revoked the key in the console; the value is dead server-side and absent from all eleven locations and all nine code paths."* Standing rule registered there: *"Vendor retirement = credential revocation, not configuration."*

`~/.zshenv` line 8 carries only the removal comment; `launchctl getenv GEMINI_API_KEY` is empty.

## Discrepancy found while verifying (doctrine §3: state-words are checked live)

`GEMINI_API_KEY` and `GOOGLE_API_KEY` **are present** in this process's environment (39 chars each). Both hash to sha256 prefix `3ee221ca4626` — the exact fingerprint of the key recorded as revoked. They are not on disk anywhere; they are inherited from the parent `claude` process (PID 39743), whose launching shell predates the 2026-08-13 removal. So the precondition finding stands and is stronger than "no credential configured": the only credential reachable is a dead one. Had Phase 1 run naively, `npx @trustgraph/config` would have read the stale variable and failed at first model call, not at configuration — a friction finding against the "secrets from env" convention, not against TrustGraph. Remedy: restart the terminal/`claude` session; nothing to edit.

## Friction numbers (task Phase 1 asked for them)

| metric | value |
|---|---|
| containers count | not measured (not deployed) |
| RAM footprint | not measured |
| time-to-first-successful-query | not measured |
| deployment debugging time | 0 of 2 h time-box |

## Consequence for the task

Phases 3, 4, 5 (extract / normalize / judge) require the model and did not run. Phase 2 ran its deterministic half (ontology generation, `2026-08-23_tgbench_ontology.md`); its "load via their ontology workbench" step did not run. Phase 6 is unconditional and ran (`2026-08-23_tgbench_shacl_report.md`). The pre-registered decision rule is **not evaluable**; see DD-018 for the re-run trigger.
