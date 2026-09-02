# RESULT — Spend guard: empty-stderr exit 1 is release-and-back-off; burn state file merges, never overwrites

**Task:** `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge.md` (no addenda found:
`cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_ADDENDUM*.md` matched nothing).
**Executed:** 2026-09-02, Claude Code. Zero model calls; no live `claude -p`; the production
ledger, burn state file, event shards, raw responses and manifest were read only.

## 0. Discipline

| check | before | after |
|---|---|---|
| `python -m pytest tests/ -q` | **594 passed** (65.8 s) | **628 passed** (63.5 s), 0 failed |

The 34 new tests are `tests/test_cli_outcome_classes.py` (23) and
`tests/test_burn_state_merge.py` (11). Both were written first and run red (the classifier
file failed at collection on the missing symbols; 8 of 11 merge tests failed against the
wholesale writer) before any production code changed.

## 1. Defect 1 — `claude -p` exit 1 with empty stderr

### 1.1 Where the code actually lives

`_looks_rate_limited` is in `kg/extraction/model_stub.py` (not in `kg/spend.py`); the
settle/release decision is made inline in `model_stub.invoke`, the DD-022 choke point. No
driver retried on it: `scripts/chunked_pilot.py::phase_extract` counts any exception from a
chunk as a failure and stops the pass at `STOP_AFTER_FAILURES = 5` in a row;
`scripts/overnight_burn.py::invoke_backoff` and `scripts/restoration_v2.py` catch only
`ModelRateLimitError`. There were **no** rate-limit back-off keys in `controls.yaml` — the
overnight burn's `RATE_SLEEP_S, RATE_MAX = 600, 6` are module constants — so the two keys the
task names were added.

### 1.2 Evidence check before reclassifying (task: stop if empty failures consumed tokens)

Searched for any sign the seven 03:01Z failures produced billable work:

| source | query | result |
|---|---|---|
| `state/spend_ledger.jsonl` | `bulk_v038_b009` reserves/settles 03:01:26–03:01:40Z | 7 reserve→settle pairs, each `actual_tokens: 20000`, `settled_as_estimate: true`, `model_call_event_id: null`; reserve-to-settle gap **~3 s** per call (a real chunk call settles at ~36k after 8–10 s on the relaunch) |
| `events/raw/**` | files with mtime in 2026-09-01 22:55–23:10 ET (= 03:01Z window) | **none** (raws are written only on a parsed envelope) |
| `events/batch-*.jsonl` | events stamped `2026-09-02T03:0*` | 1 `document_chunk_census` for the b009 document; **0** `model_call` events |
| relaunch (§21.4/§21.6 of the v038 RESULT) | first chunks after relaunch | measured usage 35,854 / 36,768 tokens — normal; Haiku liveness call at 16:08Z succeeded with no change to the machine |

No evidence of server-side consumption. Step 2 was implemented.

### 1.3 Outcome classifier (`model_stub.classify_cli_outcome`, pure, beside `_looks_rate_limited`)

| class | rule | fixture (returncode, stdout, stderr) | reservation |
|---|---|---|---|
| `success` | exit 0 | `(0, envelope, "")`, `(0, envelope, "warning")` | settle at measured usage (`outcome_class: success`) |
| `rate_limited` | exit ≠ 0 and a `_RATE_LIMIT_MARKERS` marker in stderr+stdout[:2000] (markers win: a marker is output) | `(1, "", "Error: rate limit exceeded")`, `(1, "You've hit your limit", "")`, `(1, "", "529 overloaded")`, plus one test per marker | **release**, raise `ModelRateLimitError` (unchanged) |
| `empty_failure` | exit ≠ 0, stdout and stderr both None/empty/whitespace | `(1,"","")`, `(1,""," \n")`, `(1,"\n","")`, `(1,None,None)`, `(2,"","")` | **release**, back off, retry; after the cap settle at the estimate (`outcome_class: empty_failure`) and raise plain `ModelInvocationError` |
| `error_with_output` | exit ≠ 0, anything on either stream | `(1,"","Error: something broke")`, `(1,'{"partial": true}',"")`, `(1,"partial","trace")` | settle at the estimate (`outcome_class: error_with_output`), raise — **unchanged** |

The task defined `error_with_output` as "stderr non-empty"; a non-zero exit with output on
stdout only is classified the same way (output exists that could have been billed) and that
is a stated choice, fixture `(1, '{"partial": true}', "")`.

### 1.4 Retry loop and config

`invoke` now reserves → dispatches → classifies in a loop. On `empty_failure` with retries
left it releases the reservation, sleeps `empty_failure_backoff_seconds[min(attempt,
len-1)]` (last delay repeats if the cap exceeds the schedule), and reserves afresh — so a
retry is bounded by the same run ceiling and daily band. After `empty_failure_max_retries`
retries the conservative rule returns: settle at the estimate, raise `ModelInvocationError`
(not the rate-limit error), so `phase_extract`'s streak counts it toward the systemic rule.
Timeouts settle as `timeout`, unparseable envelopes as `unparseable_envelope`, envelopes
without usage fields as `usage_fields_missing`; CLI-not-found releases as `cli_unavailable`.

Config added to `controls.yaml` `spend:` with the task's defaults, commented with the
2026-09-02 observation and the bound on being wrong (`max_retries × estimate`):

```yaml
  empty_failure_backoff_seconds: [60, 300, 900]
  empty_failure_max_retries: 3
```

`spend.empty_failure_policy()` reads them at call time; both keys are **required** (a missing
or malformed policy is a `SpendConfigError` at the first `invoke`, before any reservation —
test `test_a_missing_backoff_policy_refuses_before_the_cli_runs` asserts the fake CLI is
never called). The three test fixtures that write a tmp `controls.yaml`
(`test_extraction_model_stub`, `test_spend_guard`, `test_truncation_fallback`) gained the two
keys. The sleep is `model_stub._sleep` (module attribute) so tests record it.

Positive control for the 2026-09-01 shape: `Proc(1), Proc(1), Proc(0, envelope)` → 3 CLI
calls, sleeps `[60, 300]` (from the tmp config's values, which are deliberately not the
production ones), two `release` records with `outcome_class: empty_failure`, one `settle`
at measured 15 tokens, `committed == 15`. Cap case: 4 calls, 3 releases, 1 settle at the
111,000 extraction floor with `settled_as_estimate: true`.

Cost of the same event under the new rule: 5 chunk workers × (release, 60 s, release,
300 s, release, 900 s) = 21 minutes of wait per chunk before the first settle-at-estimate,
versus 140,000 phantom tokens and a driver stop.

### 1.5 Ledger and reporting

`settle` and `release` records carry `outcome_class`. `SpendLedger.status()` adds per run
`settled_by_class` (tokens) and `released_by_class` (counts); `reconcile()` reports
`settled_by_class`. Records written before this task report as `unclassified`
(`test_pre_classifier_records_are_reported_as_unclassified`). Read-only check on the live
ledger:

```
python -m kg.spend status --run-id bulk_v038_b009
  settled 6,122,134; settled_by_class {"unclassified": 6122134}; released_by_class {}
```

## 2. Defect 2 — the burn state file lost b010–b015

### 2.1 Root cause, from `git log --follow state/bulk_v038_burn.json` and the ledger

`write_burn_state` (`scripts/run_chunked_bulk.py`) rewrote the file wholesale from
`ledger_rows`, a list that starts empty each run and grows only as the loop **reaches** a
batch (an already-settled batch is appended when the loop gets to it; a batch the loop has
not reached yet is not in the list). The 2026-08-31 fix for the b004 crash carried settled
rows, but only at the moment the loop reached them.

| commit | `written_at` | rows on disk | writer |
|---|---|---|---|
| `82428ff` (close-out) | 2026-09-01T12:56:34Z | b001–b004, b006, b007, b010–b015 (12; b005/b008/b009 deferred) | scoped burn, pids 54119 / 9108 |
| `031d14f` "burn artifacts in flight" | **2026-09-02T00:14:57Z** | **b001–b005 only** | tome run, **pid 46272** (declared b005 20:58Z, its judge 23:21Z) |
| `34b51cc` (b008 accept, b009 stopped) | 2026-09-02T03:01:26Z | b001–b008 | same pid 46272, after carrying b006/b007 and judging b008 |
| `51ef64f` (b009 accept) | 2026-09-02T17:37:52Z | b001–b015 | relaunch pid 59666, re-walk of b010–b015 |

So: the tome run launched 2026-09-01 20:58Z (pid 46272, operator scope reversal) judged
b005 and, at its first write, replaced the twelve-row file with its own one-batch-reached
list plus the carried b001–b004. b006 and b007 came back when the loop reached them (their
aggregates were not re-run: mtimes 2026-08-31). b010–b015 were never reached because the run
died at b009 on the 03:01Z exit-1 failures (§1). The 17:13Z relaunch found no verdicts for
them and re-judged from persisted labels at zero cost (§21.6). It was not `--max-batches`;
it was the writer's shape.

### 2.2 Fix — one merge function, every writer goes through it

`merge_burn_state(path, rows, header)` in `scripts/run_chunked_bulk.py`, called by
`write_burn_state` (the only writer; `grep bulk_v038_burn` finds no other). Read-modify-write
keyed by `batch_id`:

1. a row without `batch_id` → `ValueError` (write refused);
2. a batch whose on-disk outcome is in `SETTLED_VERDICTS = (accept, reject,
   sampling_inconclusive, quarantine)` keeps it; an incoming row with a different outcome is
   refused, appended to the file's `verdict_conflicts` list (`batch_id, kept, refused, ts,
   pid`) and printed to stderr as `verdict_conflict:`; the rest of the write proceeds;
3. the same verdict may be updated in place (`phase_burn` re-writes a row to attach
   report-only yield flags);
4. a non-verdict row (`protocol_failed`) may be replaced by a verdict;
5. `outcomes` is derived from the merged rows in batch-id order (`len(batches) ==
   len(outcomes)` on its face); `stopped` still comes from this run's `BurnState`;
6. an unparseable existing file is a `ValueError`, never silently replaced; the write is
   temp-file + `os.replace`.

`phase_burn`'s `settled_rows` read is unchanged (it is also what skips re-judging).

### 2.3 Positive control and mutation test

`tests/test_burn_state_merge.py::test_writing_batch_b_keeps_batch_a` writes b001 through
`write_burn_state`, then b002 through the same path from a fresh `BurnState` that never saw
b001, and asserts both rows (with b001's evidence intact) and `outcomes == [accept,
sampling_inconclusive]`. `test_the_2026_09_01_shape_…` replays the exact incident: twelve
scoped rows on disk, one tome write of b005, all thirteen survive.

Mutation: the merge was disabled by making the on-disk rows unreadable
(`for row in [] and existing.get("batches") or []:  # MUTANT`) and the file re-run:

```
FAILED test_writing_batch_b_keeps_batch_a
FAILED test_the_2026_09_01_shape_a_run_whose_loop_never_reaches_later_batches
FAILED test_a_second_write_with_a_different_verdict_is_refused_and_logged[accept|reject|sampling_inconclusive|quarantine]
6 failed, 5 passed
```

The mutant was then removed; the file re-runs 11 passed, and the final full suite (§0) is on
the restored code. (The restore was done with `git checkout`, which also reverted the merge
edit itself; it was re-applied and the diff re-verified before the full suite ran.)

### 2.4 Reconstruction from persisted judge outputs

`corpus/staging/metrics/burn_bulk_v038_bNNN_aggregate.json` (pooled `n_facts`,
`fabrication`) → `sprt_decide` with the pre-registered boundaries (n_min = 55); b010 has no
aggregate because it never reached the judge — its admitted item count from the shard under
the production profile is 33 < 55 → `sampling_inconclusive`.

| batch | agg fab/facts | reconstructed | on disk | facts/fab on disk | match |
|---|---|---|---|---|---|
| b001 | 3/110 | accept | accept | 3/110 | ok |
| b002 | 3/110 | accept | accept | 3/110 | ok |
| b003 | 0/55 | accept | accept | 0/55 | ok |
| b004 | 0/55 | accept | accept | 0/55 | ok |
| b005 | 11/220 | accept | accept | 11/220 | ok |
| b006 | 5/165 | accept | accept | 5/165 | ok |
| b007 | 0/55 | accept | accept | 0/55 | ok |
| b008 | 2/105 | accept | accept | 2/105 | ok |
| b009 | 1/110 | accept | accept | 1/110 | ok |
| b010 | items 33 < 55 | sampling_inconclusive | sampling_inconclusive | — | ok |
| b011 | 3/110 | accept | accept | 3/110 | ok |
| b012 | 4/110 | accept | accept | 4/110 | ok |
| b013 | 0/55 | accept | accept | 0/55 | ok |
| b014 | 2/110 | accept | accept | 2/110 | ok |
| b015 | 3/110 | accept | accept | 3/110 | ok |

**15/15 match** the file on disk and §21.6 (13 accept, 1 sampling_inconclusive, 0 reject).
Sum of fabrications/facts over the 14 judged batches: 37/1,474, as §21.6 states. The state
file was not edited.

## 3. Files

Modified: `controls.yaml`, `kg/spend.py`, `kg/extraction/model_stub.py`,
`scripts/run_chunked_bulk.py`, `tests/test_bulk_v038.py` (rows in the
write-after-every-batch test now carry batch ids), `tests/test_extraction_model_stub.py`,
`tests/test_spend_guard.py`, `tests/test_truncation_fallback.py` (tmp controls carry the
policy keys).
Created: `tests/test_cli_outcome_classes.py`, `tests/test_burn_state_merge.py`, this file.

## 4. Discrepancies and notes

- The task located `_looks_rate_limited` "in `model_stub.py` (or wherever…)": it is there.
  Settlement is inline in `invoke`, not in `kg/spend.py`.
- No design-decision entry was added to `docs/design_decisions.md`; the task's completion
  clause names only this RESULT. DD-022's rule is amended in behaviour (empty_failure
  releases) and the amendment is recorded here and in the `controls.yaml` comment.
- `verdict_conflict` is logged in the state file and on stderr, not as a shard event: the
  merge function must not append to the event log on a refusal. Re-verdicting remains an
  event (`bulk_batch_quarantined` / requalification) per the append-only rule.
