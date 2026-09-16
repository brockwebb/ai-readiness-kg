# CC Task — a dispatcher pass is idempotent: no state change, no event; and a registered task file is committed by the dispatcher, not by a person

**Date:** 2026-09-16
**Project:** ai-readiness-kg (dispatcher code lands in `/Users/brock/GitHub/seldon`; the test and the config land here)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_publication_guards_RESULT.md` §0 and §8, and `cc_tasks/2026-09-16_cadence_and_enable_RESULT.md` §5 (b).
**Implements:** DN-006 decision 7 as it should have been stated (the log records assertions; a standing condition is asserted once, when it begins), and DN-006 decision 2's c1/c7 for Desktop-authored files.
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M. The cadence is not standing while every dispatched task reports a red gate for a reason that is the dispatcher's own.
**Fulfils:** its own ResearchTask (`seldon cc register`).
**Spend:** zero model calls. **Network:** none.

**Decisions taken here (operator overrides later):**
1. **`lease_held` gets the STOP file's treatment: one event per lease acquisition, none per pass.** The acquisition is the assertion (`dispatch_launched` already records it); a pass that finds the lease held by a live holder is observing a standing condition and writes nothing. `seldon dispatch status` still reports the holder and the task in flight on demand. The `dirty_tree`, `disabled` and `above_band` refusals are reviewed against the same rule: a refusal is written once when the condition begins and again only when the condition changes; the RESULT states for each reason which it is and why.
2. **The invariant the test asserts is idempotence, not emptiness.** `test_a_pass_in_a_launchd_shaped_environment_reaches_the_queue_and_writes_no_event` becomes: run the wrapper twice in succession with no change between; the second pass leaves the event log byte-identical. That holds with a task in flight, with a STOP file present, and with a dirty tree, so it runs in the only environment the dispatcher has and never skips. The single-pass "no event" claim is kept only for the state the cadence task observed (nothing eligible, nothing in flight, clean tree), as its own test, and the two together are the statement of decision 7 as amended. DN-006 gains ADDENDUM_03 restating decision 7 in those terms.
3. **The dispatcher commits registered task files.** In the pass, before candidacy: for every ResearchTask in `proposed` whose `source_file` exists and is untracked, stage and commit that file pathspec-limited (`register: <file>`), the same path the cadence uses for rendered instances; push nothing. An addendum file beside a registered task (`<stem>_ADDENDUM*.md`, untracked) is committed with the same rule. Anything else untracked or modified stays c7's business. A test authors a file, registers it, runs a pass, and sees it committed, tracked, and then eligible on c1 and c7.
4. **The dispatched session's own gate stops being red on this account.** The RESULT quotes `make gate-full` from inside this dispatched-or-not session: if this task is hand-dispatched (it must be, once, because its own file is untracked until decision 3 exists), the lease is free and the gate is green on its own terms; the RESULT then states that the next dispatched task is the real test of decision 2 and names which task that is.
5. **`seldon_events.jsonl` lines the dispatcher wrote during `publication_guards` stay.** They are true records of what the dispatcher did under the defect; nothing is rewritten.

**Zero edits to:** rule modules, `assessment/`, `state/`, `events/`, `corpus/`, `controls.yaml`, `framework/`, the report source, the PDF, the matrices, `publication.yaml`, `docs/`. `CLAUDE.md` changes only if decision 3 makes a sentence in the CC dispatch protocol false; then that sentence and nothing else.

**Immutable once written. Glob `2026-09-16_dispatch_idempotence_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Seldon repo: decisions 1 and 3; tests for both, including the two-pass idempotence under each standing condition and the untracked-registered-file commit. Seldon suite green, merged, pushed, reinstalled.
## 2. This repo: decision 2's tests in `tests/test_dispatch_config.py`; DN-006 ADDENDUM_03.
## 3. Decision 4: the gate from inside this session, stated for what it is.
## 4. Gate
Seldon suite green on the merged commit; `make gate-fast` and `make gate-full` here, detached, logged, polled, both wall-clocks reported; `seldon verify`; protected paths. Failure ships nothing: report and stop.
## 5. Report
RESULT `cc_tasks/2026-09-16_dispatch_idempotence_RESULT.md`: both repos' commits; per-reason table for decision 1; the two-pass byte comparison; the committed-by-dispatcher test's output; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (merged and reinstalled before §2) → §2 → §3 → glob addenda → §4 (detached, logged, polled) → §5 → push both repos. Hand-dispatched once, because the file that describes decision 3 cannot be committed by a mechanism that does not yet exist; the RESULT records this as the last such case.
