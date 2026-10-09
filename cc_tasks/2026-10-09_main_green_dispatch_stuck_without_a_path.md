# CC Task: main goes green: the dispatcher never records a dirty tree it cannot name, and the suite's own dispatcher passes stop counting toward each other's stuck threshold

**Date:** 2026-10-09
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from Issues `24deefb3` and `b2828020` (daily full suite red on main, two runs running).
**Framework layer served (DN-005 §5 rule 1):** none directly: the dispatcher and the daily gate every framework task passes through. No verdict, record, score or framework cell may change.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1.5M tokens (Opus). Read it as 2 to 4x low, like every estimate in this queue (handoff 2026-10-09). Diagnosis, a narrow fix, regression tests, `make gate-full` once, detached. No harness model call.
**Network:** none beyond git push

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Measured premises (verify before acting; report any that is wrong)

- `logs/daily_suite/job.log`: main green 2026-10-07T20:56Z (`c0f643dc`, 3178 passed, 4 skipped) and 22:35Z (`6a73b431`, 3180 passed, 3 skipped); red 2026-10-08T08:49Z (`33d95583`) and 2026-10-09T08:49Z (`ad9e78c7`), each `1 failed, 3180 passed, 2 skipped, 41 xfailed`. The skip count fell by one when the failure appeared.
- 10-09 failure (`logs/daily_suite/2026-10-09T083003Z.log`): `tests/test_dispatch_config.py::test_a_single_pass_writes_no_event_when_there_is_nothing_to_assert`, line 381, "a pass with nothing to assert wrote to the event log". Desktop did not read the 10-08 log; confirm it is the same test.
- The event that pass wrote is the last line of `/Users/brock/.cache/airkg/daily_suite_worktree/seldon_events.jsonl`. The worktree is rebuilt on every daily run: copy the line into the RESULT before anything resets it. As read by Desktop: `dispatch_stuck`, actor `dispatcher`, 2026-10-09T08:31:03Z, task `d3de4348`, `criterion: dirty_tree`, `failed: ["c7"]`, `passes: 3`, `threshold: 3`, `first_seen: 2026-10-09T08:30:59Z`, `dirty_paths: []`, `dirty_count: 0`, `poll_interval_s: 300`.
- Three things in that line do not cohere:
  (a) c7 asserted a dirty tree and named zero dirty paths;
  (b) three passes counted in four seconds against a 300 s poll interval, so the passes were the suite's own dispatcher invocations under xdist sharing one stuck counter, not the scheduler's (the job seeds 55 ignored paths into the worktree, `job.log`; `.seldon/dispatch_stuck.json` is the first candidate to check);
  (c) the test's survey read the state as quiet (nothing eligible, tree clean, no STOP, lease free) while the pass found a candidate failing c7: the survey and c7 read cleanliness differently, and "nothing eligible" is not "nothing to assert".
- The test is `@interactive_only`; by its own docstring it skips inside a dispatched session. **This session cannot run the failing test as the daily job runs it.** The proof that main is green is the next daily run, not this task's gate (decision 5).
- `.seldon/DISPATCH_STOP` in the working checkout holds three lines: an operator budget stop written by Desktop 2026-10-07T20:36Z, then one red-main line per daily run, appended by the job.

## Decisions

1. **No launch is possible while diagnosing.** Before running any test or wrapper that executes a real dispatcher pass, establish from the code whether that path can launch a session. Every reproduction runs in a throwaway `git worktree` (never the working checkout) with `claude` absent from `PATH`, so a launch fails loudly instead of spending. Say in the RESULT what you found the launch path to be.
2. **Diagnose before editing.** Find what c7 ran and what it saw when it reported dirty with no paths. Hypothesis to test, not to adopt: under xdist several workers run git in one tree; `git status` takes `index.lock` opportunistically to refresh the index, and git documents `--no-optional-locks` (`GIT_OPTIONAL_LOCKS=0`) for exactly the background-status case (git(1), "--no-optional-locks"). A status call that failed or raced may have been read as dirty. Whatever the cause, the RESULT shows the evidence for it.
3. **c7 never asserts a dirty tree it cannot name.** A c7 failure carries at least one path. A git call that fails is recorded as a failed read under its own reason, not as `dirty_tree`, and a failed read does not advance the stuck counter. Fix it where c7 lives: this repo's wrapper or the seldon checkout beside it. Commit in the repo that owns the code and say which; if that is seldon, run its relevant tier and quote it.
4. **Isolate the tests, do not weaken them.** Tests that run a real dispatcher pass must not share stuck state with each other or with seeded live state: each gets its own copy of what the pass reads and writes. `xdist_group` serializes, it does not isolate, so it is not the fix by itself. The assertion at :381 is kept as written. The test's precondition may be narrowed only by a survey field naming a real assertion a pass would make (a candidate failing a criterion for `threshold` passes), and only if that state is still reachable after decision 3; say which.
5. **Regression tests that run anywhere.** Because the quiet-state test skips in a dispatched session, add tests that pin each mechanism without depending on queue state or session kind: c7 on a failed git read records no `dirty_tree` and no counter advance; two passes in two isolated state copies do not see each other's counts. Show each failing on the pre-fix code and passing after (run them against the parent commit in the throwaway worktree).
6. **Daily job Issue hygiene** (`scripts/jobs/airkg_daily_suite.sh`): the Issues it opens carry a `name` (today `seldon go` prints `None` for them); a red run, while an open `merge_blocked` Issue for the same failing test exists, updates that Issue instead of opening another; the first green run closes the job's open `merge_blocked` Issues with the log path. `24deefb3` and `b2828020` are left open for that green run to close.
7. **The STOP file is not touched by this task.** Read how the job decides a STOP file is its own when it goes green, and report what it would do with the present file, whose first line it did not write. If it would delete the operator's line, change it to remove only its own lines; if it would leave the file because of that line, say so, since that leaves dispatch stopped after main is green until the operator clears it.

## Gate

`make gate-full`, detached and logged per CLAUDE.md, from a fresh `git worktree` of the committed fix, seeded as `scripts/jobs/airkg_daily_suite.sh` seeds it, `claude` absent from `PATH`. Quote passed, skipped, xfailed, deselected, and name which tests skipped because the session is dispatched (the quiet-state test should be among them). Run the decision-5 tests 20 times in that worktree under `-n auto` (bash loop; `pytest-repeat` is not installed) and quote the pass count. `seldon verify` and the protected-paths diff as usual.

A failed gate writes nothing beyond the RESULT and reports. No assertion or threshold moves.

## RESULT

§1 premises, each confirmed or wrong. §2 launch path (decision 1). §3 root cause with its evidence. §4 the change, per repo, with commits. §5 regression tests, red before and green after. §6 gate output and log paths. §7 the STOP-file finding (decision 7). Then `seldon cc complete`, commit, push.
