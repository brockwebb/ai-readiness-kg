# CC Task: Spend guard — empty-stderr exit 1 is release-and-back-off; burn state file merges, never overwrites

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_spend_guard_exit1_and_state_merge_ADDENDUM*.md` files.**

## Context

Two defects recorded as open in `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md` §21.3 and §21.6. Both belong to the spend guard (DD-022) and the burn driver, not to any extraction task. Verify-first: reproduce each with a test before changing code.

## Defect 1 — `claude -p` exit 1 with empty stderr is settled as an estimate and does not back off

*What happened:* on 2026-09-01 five consecutive chunks failed with exit 1 and empty stderr (Max usage window closing). `_looks_rate_limited` did not match, so each reservation was **settled at the estimate** (140,000 tokens charged for no output) and the driver's systemic-failure rule stopped the pass. The relaunch succeeded with no code change.

*Required behavior:*

1. Classify a `claude -p` failure into a named outcome before settlement: `rate_limited` (existing matcher), `empty_failure` (exit ≠ 0, stderr empty or whitespace, stdout empty), `error_with_output` (exit ≠ 0, stderr non-empty), `success`. The classifier is a pure function with fixtures for each class; it lives beside `_looks_rate_limited` in `model_stub.py` (or wherever that function actually lives — read the code, do not assume the module).
2. `empty_failure` is treated like `rate_limited`: **release** the reservation (do not settle), back off, retry. Back-off schedule and retry cap are config values in `controls.yaml` `spend:` (read the existing rate-limit back-off keys and reuse them; if none exist, add `empty_failure_backoff_seconds` and `empty_failure_max_retries` with defaults `[60, 300, 900]` and `3`). After the cap, settle at the estimate as today and count the chunk failure toward the systemic-failure rule.
3. The conservative rule stays for `error_with_output`: settle at the estimate (a failed CLI may have consumed tokens). Do not weaken it.
4. Ledger entries carry the outcome class so `kg spend reconcile` can report how many tokens were booked under each class. Add that breakdown to `kg spend status` output.

*Justification for the reclassification, stated so it can be overridden:* an exit-1 with no stdout and no stderr has produced no output that could have been billed; the 2026-09-01 relaunch measured normal per-chunk usage immediately after, and the Haiku liveness call at 16:08 succeeded. The cost of being wrong (a genuine server-side charge under-booked) is bounded by the retry cap × estimate; the cost of the current rule is a driver stop plus 140k phantom tokens per five-chunk run. If you find evidence in the raw responses or ledger that empty-stderr failures **did** consume tokens server-side, stop, report it in the RESULT, and do not implement step 2.

## Defect 2 — the burn state file was rewritten by the tome runs and lost b010–b015's verdicts

*What happened:* after b009 the driver walked b010–b015 as "every chunk already extracted; judging without dispatch" because `state/bulk_v038_burn.json` no longer carried their verdicts. Harmless only because judge labels persisted and replayed at zero cost; a driver that could not replay would have re-spent ~9M tokens on judging.

*Required behavior:*

1. Find the write path that replaced the state file wholesale. Restate in the RESULT which run rewrote it and why (read the file's git history; do not guess).
2. State-file writes are read-modify-write **merges** keyed by batch id: a run may add or update its own batch entries and may never drop another batch's entry. Implement as a single function used by every writer.
3. A batch verdict, once written as `accept`/`reject`/`sampling_inconclusive`/`quarantine`, is immutable in the state file; a second write for the same batch with a different verdict is refused and logged (`verdict_conflict`). Re-verdicting is a new event with provenance, not an in-place edit — consistent with the repo's append-only rule.
4. Positive control: a test that writes batch A, then writes batch B through the same path, and asserts A survives; a mutation test that disables the merge and shows the test fail. Both in the RESULT.
5. Reconstruct the current state file from persisted judge outputs and confirm it matches what §21.6 reports (fifteen outcomes). If the reconstruction disagrees with the file on disk, report the diff; do not edit the file.

## Discipline

- `python -m pytest tests/ -v` passes; report the count before and after.
- No live `claude -p` call in tests. Fixtures for stdout/stderr/exit combinations.
- Zero model calls in this task.
- Do not touch event shards, raw responses, the manifest, or `state/spend_ledger.jsonl` except through the code paths under test using tmp copies.

## Completion

RESULT at `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md`: outcome classifier table with fixtures, config keys added, the state-file rewrite root cause, positive-control and mutation-test evidence, reconstruction check. `seldon cc complete`; commit and push.
