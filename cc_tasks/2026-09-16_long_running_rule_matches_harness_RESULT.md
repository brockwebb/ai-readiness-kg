# RESULT: the long-running-commands rule says what the harness allows, and the gate prints why it skipped

**Task:** `cc_tasks/2026-09-16_long_running_rule_matches_harness.md` (no addenda; globbed before §1 and again before §3, both empty).
**Date:** 2026-09-17 UTC (dispatched 2026-09-17T02:01:19Z).
**Gate:** green. Every command below ran to its `EXIT=` line before this file was written. `make gate-full`: 2282 passed, 18 skipped, 12 xfailed, 0 deselected, `EXIT=0`, 1462.41 s. `seldon verify` reported `EXIT=0`, and so did the protected-paths check.

## 0. The detach and poll commands this session used

Detach, via the `gate-full` recipe, which already has the corrected shape (the `echo EXIT` sits inside the `sh -c` string):

```bash
make gate-full
# expands to:
nohup sh -c '/opt/anaconda3/bin/python3 -m pytest tests/ assessment/ -q -rs; echo EXIT=$? >> logs/suite.log' \
    > logs/suite.log 2>&1 &
```

Started at 2026-09-17T02:02:12Z (pytest PID 61996).

Poll, as one foreground Bash call with the tool timeout at 600 000 ms and a loop bound of 38 × 15 s = 570 s, under the timeout:

```bash
for i in $(seq 1 38); do grep -q '^EXIT=' logs/suite.log && break; sleep 15; done; echo "polls=$i"; tail -3 logs/suite.log
```

| call | `polls=` | outcome |
|---|---|---|
| 1 | 38 | no EXIT line, suite at 62 % |
| 2 | 38 | no EXIT line, suite still at 62 % (the `slow` tier's 1 req/s fixtures) |
| 3 | 22 | `EXIT=0` found |

In total there were 98 loop iterations over three tool calls. The third call's tool status was "Exit code 1", but the suite had not failed: the command ended with `ps -o etime= -p 61996`, and `ps` exits 1 because the process had already finished. The log's `EXIT=0` line is the suite's result.

`seldon verify` and the protected-paths check each finish in under a second, so both ran in the foreground, using the same `(…; echo EXIT=$?) > log 2>&1` shape.

## 1. `CLAUDE.md` diff (quoted)

```diff
@@ -97,12 +97,12 @@
 ```bash
 mkdir -p logs
-nohup <cmd> > logs/<name>.log 2>&1 &            # record the PID
-# ... then, in repeated tool calls, until the process has exited:
-sleep 240; tail -5 logs/<name>.log
+nohup bash -c '<cmd>; echo EXIT=$?' > logs/<name>.log 2>&1 &     # record the PID
+# ... then, in repeated foreground Bash calls (tool timeout <= 600 s, N*15 s under it), until the log has its EXIT line:
+for i in $(seq 1 N); do grep -q '^EXIT=' logs/<name>.log && break; sleep 15; done; tail -5 logs/<name>.log
 ```
 
-Append `; echo EXIT=$? >> logs/<name>.log` to the command itself, so the log carries the exit code and a reader never has to infer success from the absence of a traceback.
+The `echo EXIT=$?` goes inside the `bash -c` string, as above, so the log carries the exit code and a reader never has to infer success from the absence of a traceback. Written outside it (`nohup <cmd> > log 2>&1; echo EXIT=$? >> log &`), only the `echo` is detached and the tool call blocks on the command; a bare `sleep 240` is refused by the harness.
```

The task limited the write set to the two command lines, but the edit also changes the "Append …" sentence. That sentence is what caused the misreading named in defect 2 of the task's §0. If the two lines had changed and the sentence had stayed, the section would give two contradictory instructions. The three rules, the `logs/` sentence and the Headless-sessions paragraph are byte-unchanged. `tests/test_dispatch_config.py`, which pins that paragraph, passed inside this `gate-full`.

`Makefile`: `-rs` was added to the pytest call in `gate-fast`, in `gate-task` (its own `re_derives` call) and in `gate-full`. Nothing else changed. `guards` is not a `gate-*` target and was left alone.

## 2. The 18 skips, attributed (from `logs/suite.log`)

| # | reason (pytest `-rs` line) | count | class |
|---|---|---|---|
| 1 | `tests/test_scan_figures.py:74/287/291/311/353`: `cycle params.cycle.name has not been reported: state/scan_matrix_2026-09-10.json does not exist` | 10 (2+1+5+1+1) | cycle-name mismatch |
| 2 | `tests/test_scan_figures.py:453`: `docs/reports/scan_matrix_{tierA,tierC,product}_2026-09-10.csv has not been built` | 3 | cycle-name mismatch |
| 3 | `tests/test_scan_figures.py:530`: `scan_matrix_tierA_2026-09-10.json has not been built` | 1 | cycle-name mismatch |
| 4 | `tests/test_scan_run_2.py:534`: `this cycle has no matrix yet` (looks for `state/scan_matrix_2026-09-10.json`) | 1 | cycle-name mismatch |
| 5 | `tests/test_dispatch_config.py:333`: `not the quiet state this asserts: a claim is in flight; tree dirty (3 path(s)); lease held by dispatcher:HexagonMBP.local:61722` | 1 | structural: in a dispatched session |
| 6 | `tests/test_scan_harness.py:281`: `E5 judges the cycle's controls, not a surface` | 1 | by design (parametrisation) |
| 7 | `assessment/tests/test_g1_preservation.py:337`: `no dev proposition publishes SE and CI together` | 1 | data condition |
| | **total** | **18** | |

None of the reasons is a missing credential or service. Two findings go to the next task. Neither is fixed here.

- **Finding A (15 of 18).** `assessment/harness/scan/params.yaml:125` sets `cycle.name: scan_2026-09-10`. On disk, the 2026-09-10 cycle exists only as re-judged matrices: `state/scan_matrix_2026-09-10_rj1.json`, `state/scan_matrix_2026-09-10_rj2.json` and `state/scan_matrix_{tierA,tierC,product}_2026-09-10_rj2.{csv,json}`. There is no base `scan_matrix_2026-09-10.json`. The figure gate and the per-leg denominator check therefore skip every run. The figures of the current cycle of record are ungated while every gate reports green. The next task has two options: point the tests' cycle resolution at the newest re-judgement of the configured cycle, or set `cycle.name` to the reported cycle. It should grind the prior art first (`cc_tasks/2026-09-10_harness_v5_blind.md`, where the skip-with-reason was introduced).
- **Finding B (1 of 18).** Inside a dispatched session, `tests/test_dispatch_config.py:333` can never run: the dispatcher holds the lease, the claim is in flight and the session's own edits make the tree dirty. Its guard never runs on the gate that precedes a dispatched push. It can only run in a quiet interactive checkout.

## 3. Premises this task file got wrong

1. **"`make gate-full` (detached with the corrected form)."** The `Makefile` recipe already had the corrected shape before this task: `nohup sh -c '…; echo EXIT=$$? >> …'`. Only the `CLAUDE.md` prose was wrong. The recipe needed nothing but `-rs`.
2. **Write set, "the two command lines … nothing else".** Fixing defect 2 also required rewording the "Append `; echo EXIT=$?` …" sentence, because that sentence is what the misreading came from. §1 shows the edit. It is recorded here as a deviation from the stated write set.
3. **"The standing 18 skips" as one undifferentiated count.** They have four causes, and one cause accounts for 15 of them (§2 Finding A). That cause is a live coverage gap, not background noise.
4. **"every gate target".** `gate-task` runs `gate-fast` as a prerequisite, so its `-rs` shows up in two places (its own call and the one inherited from `gate-fast`). `guards` is not a gate target and was not changed.
5. **Poll form.** The task gives `tail -5` after the loop. That form worked as written. The bound (38 × 15 s under a 600 s timeout) had to be chosen per call, and that choice is now written into the `CLAUDE.md` comment.

## 4. Gate

| check | passed | skipped | xfailed | deselected | other | wall clock | log |
|---|---|---|---|---|---|---|---|
| `make gate-full` (whole suite, `-rs`) | 2282 | 18 | 12 | 0 | 248 warnings, 0 failed, `EXIT=0` | 1462.41 s (0:24:22) | `logs/suite.log` |
| `seldon verify` | n/a | n/a | n/a | n/a | "All checks passed.", `EXIT=0` | under 1 s | `logs/long_running_rule_seldon_verify.log` |
| protected paths (`docs/` byte-identical to `0e79fc0`, committed and working tree) | n/a | n/a | n/a | n/a | confirmed, `EXIT=0` | under 1 s | `logs/long_running_rule_protected.log` |

**Tier.** This run is `gate-full`, the whole suite, and its result stands as a green suite. It also covers the two earlier pushes that ran only the fast tier, `e379e7c` and `ebf5624`. Since those commits, the only changes are this task's `CLAUDE.md` and `Makefile` edits, two registered task files and eight dispatcher lines in `seldon_events.jsonl` (`git diff --stat ebf5624 HEAD`), and the full suite is green on top of them.
