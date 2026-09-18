# ADDENDUM 06 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-18. **Status:** AMENDS ADDENDUM_03 §2 (the dispatcher commits a registered
task file) and states what c7 already implied. Does not supersede anything.
Written by the implementing task (`cc_tasks/2026-09-18_registration_commits.md`), from
`cc_tasks/2026-09-18_scoring_model_RESULT.md` §4 premise 10: two task files registered from the
Desktop at 03:01Z turned a running session's protected-paths check red, and the session had to
prove its ship set in a clean worktree.

Decisions 1 to 10 stand as ADDENDUM_01 to ADDENDUM_05 left them.

---

## 1. Registration commits the file it registers; the window is zero

ADDENDUM_03 §2 had the dispatcher commit a Desktop-registered task file on its next pass. A pass
that finds the lease held exits, so a file registered while a dispatched session ran stayed
untracked for that session's whole life, in the tree the session's checks read.

**As amended.** `seldon cc register` (the CLI, the `seldon_cc_register` MCP tool and the cadence
all run `register_task_file`) commits an **untracked** task file itself: `git add -- <file>`,
`git commit -- <file>`, with a message naming the task id, and records the full sha on
`artifact_created` as `properties.source_commit`. A tracked or staged file is its author's to
commit and is left alone; `source_commit` is null on those registrations, and null when git
refuses the commit (a hook, an `index.lock`), in which case the file is unstaged again and
registration succeeds exactly as before.

**The dispatcher's sweep stays, as the fallback** for `source_commit: null`. It gains one case:
the registration's own `artifact_created` line is appended to the tracked store *after* the
commit it names, so it cannot be in that commit, and the sweep — keyed on an untracked file —
no longer sees the task. Left alone, that one line would keep c7 false for the whole queue, the
wedge ADDENDUM_03 §2 removed. So a pass with no claim in flight, on the configured branch,
commits the store when it is append-only against HEAD and an appended line is a ResearchTask
`artifact_created` carrying a `source_commit` (`seldon/commands/dispatch.py::
_commit_registration_records`). While a claim is in flight the session's own end-of-task commit
of the store carries the line, as it carries every line written beside it.

## 2. A path-scoped commit beneath a running session is safe

A commit is of the index, not of the working tree. `git add -- <file>` puts one entry in the
index; `git commit -- <file>` is git's `--only` mode, which commits that path's working-tree
content and leaves every other index entry exactly as it was (git-commit(1), "--only").
So a session's staged, modified and untracked work is neither committed nor unstaged. HEAD moves
under the session by one commit that adds a file the session never wrote; nothing the session
holds can conflict with it, and the session's own end-of-task commit, also by path, lands on
top. The one contention is `index.lock` when both commit in the same instant; the loser is
registration, which falls back to §1's null.

This is what c7 (a dispatched session's tree is its own for its whole life) needs from a
concurrent writer: nothing in the session's diff against HEAD changes.

## 3. Two paths are never a session's protected paths

`cc_tasks/*.md` written untracked and `seldon_events.jsonl` are written into a session's
checkout by actors other than the session, by design: registration and addenda from the
Desktop, the store's appends from registration, the dispatcher and the Desktop. Every
`scripts/check_protected_*.sh` in ai-readiness-kg sources `scripts/check_protected_lib.sh` on
its line 2, which drops those two from the name listings the checks read (`git diff
--name-only`, `git ls-files --others`, `git status --porcelain`).

**Not excluded:** a modified *tracked* `cc_tasks/*.md` (task files are immutable once written;
no other actor edits one, so "a prior RESULT changed" stays a violation), and the store's
content diff, which every check's append-only test reads.
