# ADDENDUM 08 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-10-10. **Status:** AMENDS decision 2 (c7) and ADDENDUM_03 §1's table. Does not
supersede either.
Written by the implementing task (`cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md`),
from the daily full suite going red on `main` on 2026-10-08 and 2026-10-09 (Issues `24deefb3`,
`b2828020`).

Decisions 1 and 3 to 10 stand as ADDENDUM_01 to ADDENDUM_07 left them.

---

## 1. c7 is two facts, and a failed read is a third: each gets its own reason

Decision 2's c7 is "on the configured branch **and** the tree is clean". Until this addendum,
every c7 failure was reported as `dirty_tree`. The daily suite's worktree is a **detached HEAD**
(`scripts/jobs/airkg_daily_suite.sh` checks out `--detach`), so in it c7 failed on the branch
half with a clean tree. The worktree's `logs/airkg_dispatch.log` printed `d3de4348 dirty_tree: c7`
followed by `dirty: (branch)`, and the stuck alarm wrote `dispatch_stuck{criterion: dirty_tree,
dirty_paths: [], dirty_count: 0}`. A refusal that names no dirt sends whoever reads it looking
for dirt.

`seldon/core/dispatch.py::c7_reason` now gives:

| c7 failed because | reason | evidence the line carries |
|---|---|---|
| a git read failed (`rev-parse` or `status` exited non-zero) | `tree_unreadable` | git's exit code and stderr |
| the tree has at least one dirty path (on any branch) | `dirty_tree` | the paths, always at least one |
| the tree is clean and HEAD is not the configured branch | `wrong_branch` | the branch and the configured one |

`tree_state` used to ignore git's exit codes, so a failed `status` read as "no paths" and a failed
`rev-parse` as a wrong branch. It now returns `read_error` instead. **A pass whose tree read failed
counts nothing toward a stuck streak**: it has not observed the queue, so it neither advances a
streak nor clears one. `status` is now run with `--no-optional-locks`. git(1) documents that flag
for a background `git status` in a checkout someone else is working in, which is what the
dispatcher's poll is.

ADDENDUM_03 §1's table, extended by the same rule (*an event only for a beginning recorded nowhere
else*):

| reason | what it is | the record of its beginning | event |
|---|---|---|---|
| `wrong_branch` | standing, until someone checks the branch out | **git** (the reflog) | none |
| `tree_unreadable` | an occurrence: one git call that failed | nothing, but it is not an assertion about the queue | none; the pass prints it |

The stuck alarm (ADDENDUM_01 decision 6b) still fires on `wrong_branch`. A checkout left on
another branch stops the queue as surely as a dirty one does.

## 2. The stuck streak file can be pointed elsewhere, and a test that runs a real pass does that

The streak file is `.seldon/dispatch_stuck.json`, one per checkout. The two tests in
`tests/test_dispatch_config.py` that run a real pass made three passes within four seconds, all
against that one file. The third pass crossed `stuck_after_passes: 3` and wrote the event that
reddened `main`. The same passes, run from an operator shell, advanced the launchd dispatcher's own
streaks. In the worktree, the file outlived each rebuild because `.seldon/` is ignored and
`git clean -fd` keeps ignored files: 6f6d03c5 stood at 6 passes after two days.

`$SELDON_DISPATCH_STUCK_STATE` (`seldon/core/dispatch.py::STUCK_STATE_ENV`) moves the file. It is
unset in production. Each real-pass test copies the live file into its `tmp_path` and points the
pass and its `status` survey at the copy, so no test counts another test's passes or the
scheduler's. `status --json` gained `stuck_due`, the candidates the next pass would alarm on. The
quiet-state test names that as a reason it is not in the quiet state, because a `dispatch_stuck`
is an assertion the pass would make.
