# RESULT: main goes green: the dispatcher never records a dirty tree it cannot name, and the suite's own dispatcher passes stop counting toward each other's stuck threshold

**Task:** `cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md` (no addenda). **Run:** 2026-10-10, dispatched session (task `422251c1`).
**Commits:** seldon `4bc8e22`; ai-readiness-kg `ef2edb0f`, then this RESULT and the protected-paths check.
**Outcome:** done. The full gate is green in a fresh seeded worktree with `claude` off `PATH`, the decision-5 tests passed 20 of 20 runs, `seldon verify` passed, and the protected-paths check is OK. One limit, stated in §1 P5: the failing test no longer runs in the daily job at all, so the next daily run cannot be the proof the task expected.

## 1. Premises

| # | Premise | Verdict |
|---|---|---|
| P1 | `job.log`: green 10-07 20:56Z (`c0f643dc`, 3178 passed, 4 skipped) and 22:35Z (`6a73b431`, 3180 passed, 3 skipped); red 10-08 08:49Z (`33d95583`) and 10-09 08:49Z (`ad9e78c7`), each `1 failed, 3180 passed, 2 skipped, 41 xfailed` | **Confirmed**, and there is a third red run since: 10-10T08:50:41Z, `015a4f1c`, `1 failed, 3202 passed, 4 skipped, 41 xfailed`, Issue `a82451c1`. That run failed a **different** test: `tests/test_brief_pack.py::test_full_pack_regenerates_byte_for_byte_and_nothing_else_is_there` (`E_architecture.md drifted`, a Seldon line cite `dispatch.py:834` → `:788`). Commit `34fc0e91`, which pins the pack's Seldon citations, is on main, and this task's gate passes that test. |
| P2 | 10-09 failure is `test_a_single_pass_writes_no_event_when_there_is_nothing_to_assert`, :381; the 10-08 log shows the same test | **Confirmed.** Both logs carry the same test and the same assertion at `tests/test_dispatch_config.py:381`; only the hashes differ. |
| P3 | The `dispatch_stuck` line is the last line of the worktree's `seldon_events.jsonl`; copy it before a reset | **Wrong.** The 10-10 run had already reset the worktree (`checkout --force` at 08:30Z), and its `seldon_events.jsonl` now ends at an `artifact_created` from 2026-10-08. The line could not be copied. Two of its sources survive, because the worktree's ignored files persist across runs. The first is `.seldon/dispatch_stuck.json`: `d3de4348 {criterion: dirty_tree, first_seen: 2026-10-09T08:30:59.425114Z, notified_at: 2026-10-09T08:31:03.466535Z, passes: 3}`, with 6f6d03c5 and 99beb5b6 at `passes: 6` and `first_seen: 2026-10-08T08:30:51Z`. The second is the worktree's `logs/airkg_dispatch.log` (§3). Both agree with Desktop's reading. |
| P4a | c7 asserted a dirty tree and named zero paths | **Confirmed, and explained** (§3): the failure was c7's *branch* half. |
| P4b | Three passes in four seconds were the suite's own, sharing one counter, "under xdist" | **Confirmed except the mechanism.** The passes were the suite's own (08:30:58, :59 and 08:31:02Z). xdist did not cause the sharing. Two tests ran three passes in sequence (the idempotence test runs two, the quiet-state test one), all against the worktree's one `.seldon/dispatch_stuck.json`. `.seldon/` is not seeded (`SEED_EXCLUDE`), but `git clean -fd` keeps ignored files, so the file also **persisted across daily runs**. |
| P4c | The survey read the state as quiet while the pass found a candidate failing c7 | **Confirmed.** `status --json` has `tree_dirty`, which is c7's dirt half only; c7 is `branch == configured and not dirty`. In the detached worktree, `tree_dirty` was false and every candidate failed c7 on the branch. |
| P5 | The test is `@interactive_only` and skips in a dispatched session; the next daily run is the proof | **Half wrong.** It is `interactive_only` **and** `@pytest.mark.live_model` (seldon AD-036-R9, PA-001 Part E), which `tests/conftest.py` skips unless `LIVE_MODEL_CALLS=1`. The daily job does not set that variable: the 10-10 log reports both real-pass tests skipped, at `:275` and `:341`. **The next daily run will not run this test either**, so its green says nothing about it. The mechanisms are pinned instead by the decision-5 tests (§5), which run everywhere, the daily job included. |
| P6 | `.seldon/DISPATCH_STOP` holds three lines: an operator budget stop, then one red-main line per daily run | **Wrong now.** There is no `.seldon/DISPATCH_STOP`. It was renamed to `.seldon/DISPATCH_STOP.off3_2026-10-10_operator_fresh_week` and holds four lines: the operator's 2026-10-07T20:36Z line, then the job's lines for 10-08, 10-09 and 10-10. Nothing reads the `.off3` file. §7 has the analysis. |

Found beside the premises: on 10-08 and 10-09, the suite's alarming pass **ran the real notifier**. The worktree's dispatch log shows `notify: sent (6f6d03c5 stuck)`, `notify: sent (99beb5b6 stuck)` and `notify: sent (d3de4348 stuck)`, so the operator was notified about stuck tasks by a test. The green 10-07 runs never counted because c6 failed then (a claim in flight), and `_stuck` returns early whenever a claim is in flight.

## 2. Launch path (decision 1)

`seldon dispatch once` → `_pass` → `_launch_inplace` → `_launch_cmd` runs `spec["cli_path"]` from the **model lock** (`seldon/commands/dispatch.py::_session_spec` → `models.launch_spec_for`). Under the wrapper's `env -i`, `SELDON_MODELS_HOME` is stripped, so the lock is the live one, `seldon/models/models.lock.yaml`. Its CLI is the absolute path `/Users/brock/.local/share/seldon/claude-cli/2.1.296/node_modules/.bin/claude`. **`claude` absent from `PATH` does not prevent a launch**: the launcher never looks `claude` up on `PATH`.

What does prevent one in this suite: only the two `live_model` tests run a real pass, and they skip without `LIVE_MODEL_CALLS=1`, which no run in this session set. The gate script also unset it. No reproduction here ran a pass. The regression tests call `_stuck` and `tree_state` directly, with `_emit` and `_run_notifier` replaced by recorders. The gate still ran with `claude` absent, as specified: `PATH` was rebuilt from a symlink copy of `/opt/homebrew/bin` and `/usr/local/bin` minus `claude`, and the log shows `claude on PATH: none`. The first attempt kept `/opt/homebrew/bin/claude` on `PATH` and was killed and restarted before it finished.

## 3. Root cause, with its evidence

The daily worktree is a **detached HEAD** (`airkg_daily_suite.sh`: `worktree add --detach` / `checkout --detach`; `git rev-parse --abbrev-ref HEAD` in it prints `HEAD`). c7 is `branch == "main" and not dirty`. It failed on the branch with a clean tree. Pre-fix `first_refusal_reason` mapped **every** c7 failure to `dirty_tree`, and the stuck alarm copied the empty path list into its payload.

The worktree's own `logs/airkg_dispatch.log` says so in its words, on every pass:

```
=== 2026-10-09T08:31:02Z | airkg-dispatch fire
STUCK: d3de4348 refused as dirty_tree for 3 consecutive passes since 2026-10-09T08:30:59.425114Z; dirty: (none)
notify: sent (d3de4348 stuck)
nothing eligible (42 open, 3 candidate(s))
  d3de4348 dirty_tree: c7  cc_tasks/2026-10-08_dcat_brief_pdfs_from_build.md
      dirty: (branch)
```

`(branch)` is `_echo_refusals`' fallback when `dirty_paths` is empty, which means c7 failed and named no path.

**Decision 2's hypothesis (an `index.lock` race read as dirty) is refuted.** Pre-fix, a failed `status` returned no paths. With `rev-parse` succeeding on `main`, c7 would then have *passed*, not failed. c7 can fail with zero paths only when the branch differs, and in the worktree it does, every time. The `(branch)` line is printed on every pass on 10-07, 10-08 and 10-09, not intermittently. The hypothesis did surface a real gap, though: the return codes were never checked. Decision 3 closes it anyway.

The red needs a second mechanism: the shared, persistent streak file (P4b). The idempotence test's two passes and the quiet-state test's one reached `stuck_after_passes: 3` on a candidate new that day (`d3de4348` on 10-09; 6f6d03c5 and 99beb5b6 on 10-08). The third pass belonged to the quiet-state test and wrote `dispatch_stuck`, which is the event its :381 assertion caught.

## 4. The change

**seldon `4bc8e22`** (owns c7 and the counter):
- `core/dispatch.py::tree_state` checks git's exit codes. A failed `rev-parse` or `status` returns `read_error`. `status` runs with `--no-optional-locks`, which git(1) documents for a background `git status` in a checkout someone else works in.
- `c7_reason`: c7 failures are `dirty_tree` (only with at least one path, on any branch), `wrong_branch`, or `tree_unreadable`. Both new reasons are in `REFUSAL_REASONS`. The c7 vector carries `read_error` only when one occurred, so a readable tree's vector has its old shape.
- `commands/dispatch.py::_stuck`: an unreadable tree leaves the streak file unread and unwritten and prints `stuck: not counted; …`. The STUCK payload gains `branch`/`configured_branch`, and the message names the branch for `wrong_branch`. The refusal lines print the branch or the git error. The cadence gate refuses on `tree_unreadable`.
- `$SELDON_DISPATCH_STUCK_STATE` (`STUCK_STATE_ENV`, through `stuck_state_path`) moves the streak file. It is unset in production. `status --json` gains `stuck_due` (the candidates the next pass would alarm on, computed with the pure `advance_stuck`, no write), `tree_read_error` and `stuck_state_file`.
- `issue create --name`, `issue list --json` and `issue update --description` (decision 6).
- Seldon tier, all of `tests/`, serial: **2315 passed, 0 skipped, 0 xfailed, 0 deselected, EXIT=0** (§6).

**ai-readiness-kg `ef2edb0f`:**
- `tests/test_dispatch_config.py` (decision 4): both real-pass tests copy the live streak file into `tmp_path` and point the pass, and the `status` survey, at the copy (`_isolated_stuck_state`, `_bare_env_run(..., stuck_state)`). The assertion at :381 (now :434) is unchanged. The quiet-state precondition is narrowed by one field, **`stuck_due`**, which names a `dispatch_stuck` the pass would write. That state is still reachable after decision 3: a `wrong_branch` or `dirty_tree` streak at `threshold - 1` in the copied file.
- `tests/test_dispatch_stuck_isolation.py`: the decision-5 tests (§5).
- `scripts/jobs/daily_suite_issues.py` and `airkg_daily_suite.sh` (decisions 6 and 7). A red run names its Issue `daily suite red: <failing node ids>`. When an open `merge_blocked` Issue of that name exists, it appends `Red again: …` to that Issue's description instead of opening another. Green resolves every open Issue the job opened, the pre-name ones (`Daily full suite on …`) included, with resolution notes naming the green log. If the Issue list cannot be read, the job says so in `job.log` and opens a new Issue rather than recording nothing.
- `Makefile`: `SUITE_CMD` reports `-rfEs`, so `FAILED <node id>` lines reach the log's summary. Nothing else in the tiers changed.
- `tests/test_daily_suite_job.py`: seven new tests on the scratch-repo fixture (a fake `seldon` answers `issue list --json`).
- `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_08.md` records the c7 split and the override as an amendment to decision 2 and ADDENDUM_03's table.

**Issues `24deefb3`, `b2828020` and `a82451c1` are left open.** The first green daily run closes all three: they carry the job's pre-name description prefix, which `test_the_first_green_run_closes_the_jobs_open_issues_and_only_those` asserts.

## 5. Regression tests, red before and green after (decision 5)

`tests/test_dispatch_stuck_isolation.py` uses no graph, no real pass, no queue state, and does not depend on the session kind:
1. `test_a_failed_git_read_records_no_dirty_tree_and_advances_no_streak`
2. `test_a_detached_clean_checkout_never_reports_dirty_tree`: the incident's own state.
3. `test_passes_in_two_isolated_streak_copies_do_not_see_each_others_counts`: four interleaved passes over two copies, past the threshold of three.

These ran in a throwaway `ai-readiness-kg` worktree, beside a seldon worktree at the parent commit `2c76c65`. A finding: `tests/conftest.py` imports seldon through `tests/model_lock.py` before this module is collected, so a `sys.path` insert in the test file is too late. The first "pre-fix" run passed 3 of 3 because it had imported the live checkout. The run of record put the pre-fix checkout first on `PYTHONPATH`, and a probe test printed `SELDON_FROM /tmp/airkg_redgreen_2026-10-10/seldon/seldon/core/dispatch.py False`.
- **Pre-fix `2c76c65`: 3 failed, EXIT=1.** Test 1: `assert 'dirty_tree' != 'dirty_tree'`. Test 2: `'dirty_tree' == 'wrong_branch'`. Test 3 recorded `('emit', 'dispatch_stuck', {'criterion': 'dirty_tree', 'dirty_count': 0, 'dirty_paths': [], …})`, which is the incident's payload, reproduced.
- **Post-fix `4bc8e22`: 3 passed, EXIT=0.**

## 6. Gate

| check | result | log |
|---|---|---|
| `make suite` (= `gate-full`'s command) in a fresh worktree of `ef2edb0f`, 55 ignored paths seeded with the job's `SEED_EXCLUDE`, `seldon` linked beside it, `claude on PATH: none`, `-n auto --dist loadgroup` | **3275 passed, 5 skipped, 41 xfailed, 0 deselected**, 1239.56 s, **EXIT=0** | `logs/gate_full_2026-10-10_main_green.log` |
| decision-5 tests ×20 in that worktree, `-n auto` | **PASSED_RUNS=20/20**, EXIT=0 | `logs/main_green_regression_x20.log` |
| decision-5 tests, pre-fix seldon / post-fix seldon | 3 failed EXIT=1 / 3 passed EXIT=0 | `logs/regression_red_prefix_2026-10-10.log`, `logs/regression_green_postfix_2026-10-10.log` |
| seldon `tests/`, serial, dotenv | 2315 passed, 0 skipped, 0 xfailed, 0 deselected, 681.69 s, EXIT=0 | `logs/seldon_full_suite_2026-10-10.log` |
| `seldon verify` | All checks passed, EXIT=0 | `logs/main_green_seldon_verify.log` |
| protected paths, `scripts/check_protected_main_green.sh 66a525d2` | PROTECTED PATHS OK, EXIT=0 (re-run with this RESULT in place before the commit) | `logs/main_green_protected.log` |

The five skips in the gate:
- `tests/test_dispatch_config.py:305` and `:373`: the two real-pass tests, skipped as `live_model` (`LIVE_MODEL_CALLS` unset). **`:373` is the quiet-state test.** This session is dispatched (`SELDON_SESSION_ID` set), so its `interactive_only` skip applies too. pytest reports the `live_model` reason because conftest puts that marker first.
- `tests/test_kg_questions.py:115`: "corpus epoch moved under the stored answers". The framework record's sha moved between `015a4f1c` and main, before this task; the protected-paths check shows `framework/` unchanged since `66a525d2`. It did not skip in the 10-10 daily run. It is a data condition for whoever owns the stored answers, outside this task's write set.
- `tests/test_scan_harness.py:290` and `assessment/tests/test_g1_preservation.py:337`: standing skips, present in every daily log.

Two log artefacts, stated so nobody misreads them. `logs/seldon_full_suite_2026-10-10.log` and `logs/gate_full_2026-10-10_main_green.log` each contain a stray `PluggyTeardownRaisedWarning … OSError: cannot send (already closed?)` block. Each was written by a first attempt that I killed: a parallel seldon run (seldon has no xdist grouping for its shared Neo4j database), and a gate run with `claude` still on `PATH`. Each was restarted into the same filename. The summary and `EXIT=` lines quoted above belong to the completed runs.

## 7. The STOP file (decision 7)

**How the job decided, before this task.** On green, it deleted the STOP file if its first line was `airkg-daily-suite: main is red`, and otherwise left it untouched. On the file Desktop described, whose first line was the operator's, the job would have **left all of it, red-run lines included**. Dispatch would have stayed stopped after main went green until the operator cleared it, and the stale red lines would have stayed with it. The reverse case was worse: a job-first file to which the operator later appended a line would have been **deleted with the operator's line in it**.

**Changed** (`airkg_daily_suite.sh`): on green, the job removes only its own lines, the mark and its `<STAMP> <branch>@<sha40> EXIT=… log=…` lines. It deletes the file only when nothing else remains. When a line someone else wrote remains, the job leaves that line and logs `dispatch stays stopped until they are removed`. Both cases are tested: `test_green_removes_only_the_jobs_lines_and_leaves_the_operators` and `test_green_never_deletes_an_operator_line_appended_to_the_jobs_own_file`.

**On the present state:** `.seldon/DISPATCH_STOP` does not exist (P6), so the next green run touches no STOP file. The `.off3` file holds the operator's budget line and the job's three lines. Nothing reads it, and this task did not touch it. If the operator ever renames it back, the next green run will strip the job's three lines and leave the operator's, so dispatch would stay stopped on that line alone.
