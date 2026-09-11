# CC Task — absence claims under a scope limitation: a rule that could not look at the candidate does not get to say it is not there

**Date:** 2026-09-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-11_control_fixture_robots_forbids_product_RESULT.md` §1, §4 item 3, §7 items 1 to 3.
**Fulfils:** its own ResearchTask (`seldon cc register`). Supersedes ResearchTask `969f73c6` (RULE-A3-v5 was already CURRENT and fails the fixture; the gap is not "no guard" but "the guard does not ask what the verdict claims"). Runs before any cycle 5; `run_controls` is `ok=False` until it lands.
**Spend:** zero model calls. **Network: loopback only.** A test asserts no non-loopback host is observed.

**Prior art.** This is the auditor's scope limitation. ISA 705 / AU-C 705: when the auditor cannot obtain sufficient appropriate evidence on a material item, the response is a qualified opinion or a disclaimer, never an adverse opinion on the unexamined item. In knowledge-representation terms it is the open-world assumption: negation as failure is unsound when the evidence set is known to be incomplete. Existence verified from what was observed stands (A1-v4's policy, sound); absence asserted over a set with forbidden members is a disclaimer, which in this harness is `error`.

**Decisions taken here (operator overrides later):**
1. **One helper, in `_common`, is the only way an absence claim reaches `fail` when any candidate was blind.** `absence_verdict(candidates, blind, found)`: if the rule found the object among observed candidates, the verdict is that finding; if it found none and at least one candidate that the predicate ranges over was BLIND, the verdict is `error` with the blind candidates named on the Finding; if it found none and no candidate was blind, `fail`. The helper asks `errors.is_blind(cls, harness)` like `unobserved` does, so harness versioning still governs stored payloads.
2. **Every CURRENT rule module declares `CLAIM`** as `"existence"` or `"absence"`, on the module, inherited by leg the way `MEASURES` is. A test asserts every module in `CURRENT` declares it. A lint asserts that a module declaring `absence` and dereferencing any Observation beyond the surface page routes its `fail` through the helper; a module declaring `existence` may not call it. A1-v4 declares `existence` and does not change.
3. **`RULE-A3-v6` and `RULE-B3-v3`** are v5 and v2 with the helper in place of their current filter-then-judge. v5 and v2 stay in `REGISTRY` re-deriving the cycles that used them. The fixture expectation (`A3=error`, `B3=error`, derived before the fixture ran) is not edited; the rules move to meet it.
4. **The invariant gains a second reading, pinned before anything moves.** Alongside "no verdict on wholly blind evidence", `test_no_absence_verdict_rests_on_partially_blind_evidence` counts, per stored payload under CURRENT, the `fail` verdicts from absence-claim rules that excluded at least one blind candidate. The counts are the finding: written into the RESULT and pinned as strict xfails per payload exactly as the (6, 6, 6, 11) history was. This is the measurement that decides whether cycles 2 to 4 need a third re-judgement; that decision is the next task's, not this one's, and this task re-judges nothing.
5. **Decision 5 of the fixture task is wired now**: the fixture into `make guards` and the agreement gate; the eight-fixture control gate goes green on the derived expectation. The replay on the fixture reads RED under v5/v2 and GREEN under v6/v3, with the same Observations and the same class table, so this incident is reproducible at the control layer like A10's.

**Zero edits to:** stored payloads, prior Results, prior RESULTs, cycle evidence, targets, `docs/reports/`, the eight fixtures and their manifests, `params.e5_control.expected_verdicts`, `errors.CLASSES`, shipped rule modules (new versions are new files).

**Immutable once written. Glob `2026-09-11_absence_claims_under_scope_limitation_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 2, 4. Helper, declarations, lint, the second invariant reading with its counts. Stop if the lint finds an absence-claim rule that dereferences beyond the surface page other than A3, A8 and B3: that is a ninth instance and the RESULT names it before anything else is written.
## 2. Decisions 3, 5. The two new versions; the fixture replay; the Makefile line.
## 3. Gate (the one gate of this task)
Eight-fixture control gate under `CURRENT`, `unknown` = 0, expectation file unchanged; both-clocks agreement over eight fixtures, 0 differences; fixture replay RED under `RULE-A3-v5`/`RULE-B3-v2`, GREEN under v6/v3, and A1 still `pass` on it; `CLAIM` declared on every CURRENT module; lint green; second invariant reading pinned per payload with counts stated; byte-identical re-derivation of all stored payloads under their own harness and rule versions; the seven tests the fixture task left red are green with no test edited except where the fixture count is in its name; socket counter loopback only; `make guards`; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes nothing: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-11_absence_claims_under_scope_limitation_RESULT.md`: the per-payload counts from decision 4, which legs and which cycles; the replay verdicts; every CURRENT module's `CLAIM`; what the lint found; every premise wrong. Close ResearchTasks `969f73c6` and `a2981a12` as superseded via the CLI with a pointer to this task and to `7c6b2ba1` respectively (a Desktop MCP supersede timed out on 2026-09-11; verify state before writing). `seldon cc complete`, commit, push. Final message states the decision-4 counts and whether the push succeeded.

**SEQUENCING:** §1 (stop on a ninth instance) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
