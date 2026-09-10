# CC Task — guards earn their keep: incident-replay tests, no self-licensing, suite tiers

**Date:** 2026-09-09
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-09_manners_closeout_RESULT.md` (gate PASS, `f1cd26c9` completed). Draws on that RESULT's §4 items 3 to 7 and §5 items 2 and 3.
**Fulfils:** its own ResearchTask (`seldon cc register`). Part of `520ec74b` (cycle-4 maintenance). Cycle 4 itself is not this task and waits on the operator's flagship declarations.
**Spend:** zero model calls. **Network: none.** No federal host.

**Decisions taken here (operator overrides later):**
1. **A guard ships with its incident.** Every guard in `assessment/harness/` (the blind-probe lint, the fetcher gate, the evidence-store guard, the AST gate detector) gets a test that replays the recorded incident it was built for, asserted red against a copy of the pre-guard code path or a stub of it, and green against the shipped guard. Prior art: regression testing as practised, and the "write the failing test first" discipline of TDD (Beck 2002). A guard without a replayed incident is listed in the RESULT as such.
2. **A driver cannot license itself.** `AIRKG_SCAN_CYCLE` set anywhere in source other than `run.py::main` is a lint failure over `assessment/`, `scripts/`, `tests/` (source-level assertion, the same pattern already used for the suffix-list retirement). The RESULT's §4 item 5 incident is decision 1's replay case for this guard.
3. **The redirect log is read.** A hygiene check fails when `unlicensed/redirects.jsonl` is non-empty at the start of a gate, printing the offending writers, and is cleared only by an explicit sweep that records what was swept.
4. **Suite tiers by marker, not by deletion.** `@pytest.mark.slow` on the full re-derivation of payloads older than the two most recent cycles and on Lighthouse runs; everything else is the fast tier. The per-task gate is: fast tier, plus re-derivation of every payload a task could have touched (all of them, if a rule or the engine changed), plus the fixture gate. The full suite remains the pre-push check under the long-running protocol. Report both tiers' wall-clock so the split is measured, not asserted. No test is removed or weakened.
5. `params.manners.same_host_only`: leave it. Retiring it is a params change with a re-derivation consequence and is queued, not done.

**Zero edits to:** shipped rule modules, registered Result values, prior RESULTs, cycle evidence, the report, targets v4.

**Immutable once written. Glob `2026-09-09_guards_earn_their_keep_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 to 3
For each guard, name the incident (task, RESULT section) in the test's docstring.

## 2. Decision 4
Markers, a `make gate-fast` / `make gate-full` (or equivalent) pair, CLAUDE.md updated to say which tier a task's gate is and that the full suite is pre-push.

## 3. Gate (the one gate of this task)
Fast tier green with its wall-clock reported; full suite green under the long-running protocol with its wall-clock reported; every guard listed with its replay test and its red/green evidence; the self-licensing lint fails against a planted `os.environ["AIRKG_SCAN_CYCLE"]=...` in a throwaway script and passes after removal; the redirect-log hygiene check fails against a planted line and passes after the sweep; `seldon verify`; protected paths.
**Failure: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-09_guards_earn_their_keep_RESULT.md`, written after the logs show EXIT=0. Fast versus full wall-clock as a registered Result each (`suite_fast_seconds_2026-09-09`, `suite_full_seconds_2026-09-09`). Every premise this task got wrong. `seldon cc complete`, commit, push. Final message states whether the RESULT exists and the push succeeded.

**SEQUENCING:** §1 → §2 → glob addenda → §3 (hard stop; detached, logged, polled) → §4 → push.
