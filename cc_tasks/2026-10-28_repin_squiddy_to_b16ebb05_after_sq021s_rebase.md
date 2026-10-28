# CC Task: re-pin squiddy from `933153d2` to `b16ebb05`; the old pin is a tagged superseded generation

**Date:** 2026-10-28
**Project:** ai-readiness-kg
**Authored by:** Desktop session in squiddy (SQ11), filing the return of squiddy SQ-021M2's RESULT and DN-052 R-237 item 3.
**Implements:** squiddy `docs/design/2026-10-27_DN-052_operator_ruling_measure_only_gate_one_cost_rule_and_the_pass_ledger_is_mains.md` R-237 item 3 (a superseded generation stays reachable by tag; ai-readiness-kg re-pins); squiddy SQ-022b's follow-up.
**Amended by:** none.
**Builds on:** this repository's existing `squiddy.pin` and the way it was last re-pinned (read the most recent RESULT that changed it before touching it).
**Framework layer served (DN-005 §5 rule 1):** none (a dependency pin).
**Fulfils:** its own ResearchTask. **Hand-dispatched** by the operator (DN-006 decision 10; `dispatch.enabled` is false and `.seldon/DISPATCH_STOP` is present); not launched by the dispatcher. This task does not change `dispatch.enabled`.
**After:** none
**Model:** author
**Spend:** zero model calls. Tokens: under 0.15M (a pin change, a sync, the suite).
**Parts:** A 1.0.
**Network:** none beyond git push and the pin sync from github.

## Why

squiddy's SQ-021 branch was rebased and merged (SQ-021M2). The commit this repository pins, `933153d2`, is no longer on squiddy's main; it is reachable only through the tag `sq021-gen1-3d41fffa`, which squiddy keeps for exactly this reason. The merged tip that carries the same work with a pass recorded on main is `b16ebb05`.

## Steps

1. Confirm the current pin is `933153d2` and that `git -C /Users/brock/GitHub/squiddy tag -l 'sq021-gen1-*'` names a tag resolving to it. If the pin is already something else, stop and report.
2. Set `squiddy.pin` to `b16ebb05`, sync the way this repository syncs its kit, and record in the RESULT what the synced kit's `kit/ledger/passes.jsonl` last line names (it must be a main line, by R-237).
3. Run the suite and `seldon verify`. If anything the pin change touches fails, report it; do not patch the kit here.
4. Commit and push. `seldon cc complete`.

## Not in this task

Any other squiddy change; moving the pin past `b16ebb05`.
