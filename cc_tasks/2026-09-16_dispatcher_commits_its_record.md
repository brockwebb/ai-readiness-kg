# CC Task — the dispatcher commits and pushes its own record; the cadence cannot be blocked by a line only the dispatcher wrote

**Date:** 2026-09-16
**Project:** ai-readiness-kg (dispatcher code lands in `/Users/brock/GitHub/seldon`; the test, one `CLAUDE.md` sentence and the addendum land here)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_dispatch_idempotence_RESULT.md` §6 and DN-006 ADDENDUM_03 §4.
**Implements:** DN-006 decision 8 (a cadence that can be blocked by the dispatcher's own bookkeeping is not standing) and the doctrine that commit and push are never the operator's job.
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M. Cycle 5 on 2026-10-05 is the first thing this protects.
**Fulfils:** its own ResearchTask (`seldon cc register`). Committed and launched by the dispatcher under decision 3 of the previous task; this file is the first live test of that path and of decision 2's lease-held gate.
**Spend:** zero model calls. **Network:** none beyond `git push`, which the decisions below require of the dispatcher.

**Decisions taken here (operator overrides later):**
1. **Every line the dispatcher writes to a tracked store is committed by the dispatcher in the same pass, pathspec-limited to that store.** `dispatch_finished` is the case in hand; `dispatch_launched`, `dispatch_refused`, `cadence_created` and the registration commit of decision 3 are reviewed under the same rule, and the RESULT's table states for each whether it already leaves the tree clean or is changed here. The commit message names the event type and the task id. The check is the tree, not the event: after a pass, `git status --porcelain` on `seldon_events.jsonl` is empty unless a session is in flight.
2. **The dispatcher pushes what it commits.** A local `main` ahead of origin by dispatcher-only commits is a dirty state of a different kind: the next dispatched session's push carries them, but between sessions the record on the machine and the record on GitHub disagree, and the cadence's clean-tree gate is satisfied while the pushed history is not. Push runs after commit in the same pass; a failed push (offline, auth) is logged on stdout where the wrapper's log carries it, is not a refusal, and is retried by the next pass whenever `git status -sb` shows `ahead`. No event is written for a push, succeeded or failed: git records the beginning.
3. **The cadence's clean-tree gate is re-read against decisions 1 and 2.** After them, the only ways the tree can be dirty at a cadence tick are a session in flight (correct to wait), a Desktop-authored file not yet committed (decision 3 commits it before the cadence runs), or an operator's own uncommitted work (correct to wait, and the reason is on stdout). The RESULT names the cadence's dirtiness reasons at the tick as the code reports them, so October's first pass can be read from its log.
4. **`CLAUDE.md`'s CC dispatch protocol says who launches.** The sentence that every registration turn ends with the full dispatch line becomes: a registration turn ends with the registration; the dispatcher commits and launches the file; a dispatch line is written only while `dispatch.enabled` is false or the operator is directed to claim a task first for a hand dispatch, per DN-006 decision 10 and the previous task's §5.5. One sentence replaced, nothing else in the file.
5. **DN-006 ADDENDUM_04** records decisions 1 to 3 and closes ADDENDUM_03 §4.

**Write set, derived from the decisions:** `seldon/commands/dispatch.py` and its tests in the Seldon repo; `tests/test_dispatch_config.py` and `CLAUDE.md` (one sentence) here; `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_04.md`; `seldon_events.jsonl` by the dispatcher's own lines and this task's state transitions; the RESULT. Nothing else, and the protected-paths check asserts `docs/` byte-identical apart from the addendum.

**Immutable once written. Glob `2026-09-16_dispatcher_commits_its_record_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Seldon repo: decisions 1 and 2, with tests: a finished dispatch leaves the tree clean; a pass after a finished dispatch creates a due cadence instance rather than reporting `dirty_tree`; a failed push is reported and retried on the next pass; nothing outside the pathspec is ever staged. Seldon suite green, merged, pushed.
## 2. This repo: decision 3's reasons-at-tick test; decision 4's sentence; the addendum.
## 3. Live: this session was launched by the dispatcher under a held lease. The RESULT quotes `seldon dispatch status --json` from inside the session (lease holder, task in flight) and `make gate-full` green with the lease held, which is decision 2 of the previous task tested in the only environment it exists for.
## 4. Gate
Seldon suite green on the merged commit; `make gate-fast` and `make gate-full` here, both wall-clocks; `seldon verify`; protected paths. Failure ships nothing: report and stop.
## 5. Report
RESULT `cc_tasks/2026-09-16_dispatcher_commits_its_record_RESULT.md`: both repos' commits; the per-event table; the tree state after a finished dispatch; the status output from inside the held lease; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (merged before §2) → §2 → §3 → glob addenda → §4 (detached, logged, polled) → §5 → push both repos. Not hand-dispatched.
