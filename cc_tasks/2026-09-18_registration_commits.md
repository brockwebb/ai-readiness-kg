# CC Task: a Desktop registration commits its own task file, and a running session's tree stays its own

**Date:** 2026-09-18
**Project:** ai-readiness-kg (the registration change in `/Users/brock/GitHub/seldon`; the protected-paths convention here)
**Authored by:** Desktop session, from `cc_tasks/2026-09-18_scoring_model_RESULT.md` §4 premise 10 and its gate table: two task files registered from the Desktop at 03:01Z turned the running session's protected-paths check red, and the session had to prove its ship set in a clean worktree.
**Implements:** DN-006 decision 3 (the dispatcher commits Desktop-registered files) amended so the window between registration and commit is zero, and DN-006 c7 (a dispatched session's tree is its own for its whole life).
**Framework layer served (DN-005 §5 rule 1):** none. Dispatch path.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push` to both repos' own remotes.

---

## 0. The window

`seldon cc register` from the Desktop writes a ResearchTask whose `source_file` is untracked, and decision 3 of `2026-09-16_dispatch_idempotence` has the dispatcher commit that file on its next pass. A pass that finds the lease held exits. So a file registered during a dispatched session stays untracked until that session ends, and every protected-paths check the session runs sees a file it did not write. The scoring session handled it correctly and expensively. The fix is to close the window, not to teach every check to look away.

**Decisions taken here (operator overrides later):**

1. **Registration commits the file it registers, path-scoped.** When the registered `source_file` is untracked, `seldon cc register` runs `git add -- <file>` and `git commit -- <file>` with a message naming the task id, and records the commit sha on the registration event as `source_commit`. Only that path is staged; nothing else in the tree is touched, so a running session's uncommitted work is never swept up. If the commit fails (a hook, a lock), registration still succeeds and the event says `source_commit: null`, which is today's behaviour, and the dispatcher's pass commits it later as before.
2. **A path-scoped commit while a session runs is safe and is declared so.** The session commits its own write set by path at the end; a commit of one unrelated file underneath it moves HEAD but conflicts with nothing. The DN-006 addendum says this in one paragraph, with the git semantics that make it true (a commit is of the index, and the index holds only what was added).
3. **The convention here: `cc_tasks/*.md` and `seldon_events.jsonl` are never protected paths.** Every `scripts/check_protected_*.sh` in this repo that lists the tree's untracked or changed files excludes those two patterns, because both are written by actors other than the session by design (registration, the dispatcher, the Desktop's `seldon_events.jsonl` appends). One shared exclusion in one helper sourced by every check, not eight copies. The scoring session's live check re-run under the new convention must be green in the live checkout, not only in a worktree.
4. **The dispatcher's decision-3 sweep stays** as the fallback for `source_commit: null`.

**Write set:** `seldon/commands/cc.py` (register) and its tests, in the Seldon repo; `scripts/check_protected_lib.sh` (new, the shared exclusion) and the existing `scripts/check_protected_*.sh` (source the helper; no other line moves), `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_06.md` (glob for the next free number first), `seldon_events.jsonl`, the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-18_registration_commits_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Seldon repo: decision 1, tests first (an untracked file gets committed and `source_commit` set; a tracked file is left alone; a failing commit leaves registration intact). Suite green, 0 skipped. Merged, pushed.
## 2. This repo: decisions 2 to 4. Re-run `scripts/check_protected_score.sh` in the live checkout and quote it green.
## 3. Gate
`make gate-fast` (`-rs`), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_registration_commits_RESULT.md`: §0 the registration event shape with `source_commit`; §1 both repos' commits; §2 the helper and the list of checks that now source it; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (merged before §2) → §2 → glob addenda → §3 → §4 → push both repos.
