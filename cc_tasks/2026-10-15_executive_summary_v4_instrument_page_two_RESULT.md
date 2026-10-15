# RESULT: executive summary v4 — STOPPED at Part A (reader), Fable usage limit exhausted

**Where it stopped and why.** Stopped at **Part A, step A3** — the Fable re-reading of A6 (DN-015 §7).
The `judge` role resolves to `claude-fable-5-1`, and every call returns HTTP 429
`model_requires_usage_credits`: *"You've reached your Fable limit."* (raw envelope in
`reports/instrument/run/raw/` and reproduced below). DN-015 §7 and `instrument_read.py` are explicit:
a refused reader call **stops and reports; the read is never routed through another role**, and the
model gate forbids substitution (`model_substituted`). Fable is required by Part A (A6's reader
verdict, which sets A6's state and thus the grid's column count) and by Part D (three prose rounds),
so no deliverable (rebuilt `SUMMARY.pdf`, Issue bcd28ee0 closure) is reachable this session. Parts
B, C, D, E not started. **This is an external usage-limit block, not a code or data fault.**

**Served model.** This session (role `author`) = `claude-opus-4-8` == `seldon models resolve author`;
no mismatch. Reader `judge` → `claude-fable-5-1` (unreachable, 429).

**Step 0 — all premises verified.**
- Not `in_progress` from an earlier dispatch: the only `dispatch_launched` is this session's
  (2026-10-15T21:12:57Z); the three earlier attempts are `dispatch_stuck`.
- ADDENDUM 02 prior art: already carried receipts + search log (`logs/dn014_add02_prior_art_search.log`),
  tracked/committed. `seldon prior-art verify` = **PASS** (sha256 1c39b5a4b1a1; verdict event
  `9f304ebf6e4e4f0196f30e27f2f116e2`; `logs/v4_add02_priorart_verify.log`).
- `db464d5f` `completed`; `ba40cb29` `completed`; Issue `bcd28ee0` `open`
  (Cypher via `run_cypher`, projection_gate green on each).
- `get_overview`: `projection_gate.status: green`, 232 nodes compared, 0 mismatches.

**Part A — A6 re-specification performed and verified, then REVERTED (reader unreachable).**
Both faulted requirements were resolved against the source body on disk
(`corpus/kernel/google-dataset-structured-data.md`): (1) the JSON-LD "(preferred)" attribution →
verbatim `"Here's an example for datasets using JSON-LD and schema.org syntax (preferred) in the Rich
Results Test."` (line 55); (2) `name` as a required property → a contiguous passage from the
"Required properties" heading through the `name` row, so description AND name are shown as the two
required properties, not asserted. `scripts/instrument.py check`: **16 entries, 0 problems, 0
unverifiable**; a planted false quote in A6 is still caught
(`RULE-A6-v2 quote[0]: not found verbatim ...`). The writer's pre-read assessment was `specified`,
but **DN-015 §7 forbids the writer self-certifying** `specified`; since Fable cannot read, A6's state
cannot be reader-decided, so the entry edit was reverted to keep the record (`invalid`) and the entry
consistent and the tree green. The exact quotes/edits are recorded here for a trivial resume.

**Raw block evidence (Fable).**
`{"api_error_status":429,"api_error":"model_requires_usage_credits","is_error":true,`
`"result":"You've reached your Fable limit. Switch to another model, or manage usage credits ..."}`
Checkpoint rows: `instrument.5aebbb09b367b944.r1.a1` and `.a2`, both `error` (`claude -p exited 1`),
classified `error_with_output`, settled at estimate in `state/spend_ledger.jsonl` (run
`instrument_spec_2026-10-15`); 2 failed attempts, ~0 content tokens.

**Tree left green.** After revert, working tree carries only the append-only
`state/spend_ledger.jsonl` events (the two failed-attempt settles — kept per DD-022). `instrument.py
check` 0 problems; `seldon verify` **All checks passed, EXIT=0** (`logs/v4_seldon_verify.log`);
`make gate-fast` **3406 passed, 5 skipped, 41 xfailed, 0 deselected, 212.95s, EXIT=0**
(`logs/v4_gate_fast.log`). Protected paths (framework/, rules/, params.yaml, events/, harness, prior
*_RESULT.md): empty diff — nothing under them changed.

**Premises found wrong.** None in the task file. One standing environment condition: the Claude Max
`judge` model (Fable) usage window is exhausted; the task's ~2.5M-token Fable+critic plan cannot run
until it resets. Incident Issue filed: `882cb6e8-0a90-46f3-8517-d55b0051e410` (merge_blocked, open).

**Resume (when Fable resets).** Re-apply the A6 `expected_behavior` + quotes above (verified: check =
0 problems), set `state: specified` as the writer's pre-read assessment, run
`instrument_read.py --round 1 --only RULE-A6-v2` (→ round 2 only on a q1 "no"); the reader's last-round
verdict sets A6 `specified`/`invalid`; then `apply_instrument_state.py`, project, roundtrip test, and
proceed to Parts B–E. **Not** `seldon cc complete` — task incomplete.
