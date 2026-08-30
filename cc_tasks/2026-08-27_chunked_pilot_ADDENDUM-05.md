# ADDENDUM-05 to 2026-08-27_chunked_pilot.md — held-out confirmation on the PASS branch

**Date:** 2026-08-30. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-27_chunked_pilot_ADDENDUM*.md` (five including this one) and the parent. This addendum modifies ADDENDUM-04 §2.4's PASS branch only; the FAIL branch is unchanged.
**Result:** append to `cc_tasks/2026-08-27_chunked_pilot_RESULT.md`.

## 0. Rationale (recorded before A3's number is known)

The 44 shared chunks have been evaluated across three arms with single-variable design changes between rounds. They are functionally a dev set (adaptive data analysis: Dwork et al. 2015 reusable holdout; Recht et al. 2019 test-set replication). A PASS measured only on them is a claim about those chunks, not the corpus. The winning profile therefore confirms once on chunks never seen by any arm before bulk is unblocked.

## 1. Held-out confirmation (runs ONLY if A3 ≥ 0.60 floor)

1. **Set construction:** 30 chunks sampled deterministically (seeded, seed recorded) from the three pilot documents' chunks that were NOT in the 44-chunk comparator set, proportional to document chunk counts. Constructed by script, committed before the confirmation run dispatches. No member of the 44 may appear.
2. **One run, no iteration:** profile `v0_3_9` exactly as it passed — same sha, same parser, same judge protocol. Ceiling derived from A3 actuals, declared. If the confirmation fails, the response is NOT a template edit and rerun; it is §2.4's FAIL branch (ground-truth re-derivation) with the generalization gap recorded as the finding.
3. **Pre-registered confirmation criteria:** faithfulness gate at the standing thresholds (F_upper < 0.10, item-faithful ≥ 0.70) on the held-out chunks; yield reported against the 0.60 floor using the same v0.3.5 comparator where those chunks were covered by the v0.3.5 chunked arm, and reported without a floor verdict where they were not (no comparator exists there — say so rather than manufacture one).
4. **Interpretation, both directions, recorded now:** gates hold → §3 closes PASS, bulk unblocked, verdict states "confirmed on held-out chunks from pilot documents; corpus-level generalization remains an extrapolation across document types." Gates fail → dev-set overfitting is the finding, FAIL branch procedure applies.

## 2. Verdict language (either branch)

The §3 verdict must state: the yield floor's target (45.23 admitted/chunk, from an unvalidated arm) is a tripwire, not a validity criterion; floor met is not value validated. Ground-truth annotation remains the only path to a value-valid yield target and is mandatory on the FAIL branch, optional and unscheduled on the PASS branch.

## 3. Out of scope

Any template change; any arm beyond the confirmation run; Arm B; bulk extraction (separate decision after closure); ground-truth rubric content (operator value input).
