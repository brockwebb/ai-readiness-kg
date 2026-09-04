# CC Task: G1 memo v1.2 — qualify level-based verdicts with the calibration finding; binary score is G1-O, levels are descriptive; skeleton note; DD-038 (one paragraph)

**Date:** 2026-09-03
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-03_g1_memo_v1_2_level_caveat_ADDENDUM*.md` files.**
**SEQUENCING:** after `cc_tasks/2026-09-03_g1_calibration_rating_agreement_RESULT.md` (exists). Instrument frozen; no file under `assessment/harness/` or `assessment/config/` changes. Do not commit biblio-cron files.
**Spend:** zero model calls. Every number a `{{result:}}` token; `g1_resolve_results.py --check` must resolve 100 % after the edit.

## Context

The calibration (`…_g1_calibration_rating_agreement_RESULT.md` §2) shows the instrument is robust at one grain and not at another. Rater and scorer agree on L3+ vs <L3 almost completely (18/18 preserved-exact; 14/14 reviewer parser-misses; genuine-loss range 173–178 of 232), and disagree on *which* sub-L3 level a loss is (rater vs scorer exact-level agreement 0.000 in every L2 and L0 stratum; κ_w 0.392 [0.205, 0.614]). The G1-O score is already the binary (family preservation rate, L3+ share). But the findings memo §3 reports E5 (omission modal under `tight`) and E6 (L2 appears under compression) as "supported" with no caveat, and those are level claims. **Desktop decision:** the binary is the score; the level distribution is descriptive and every level-based verdict carries the agreement caveat. Nothing is re-scored, nothing is withdrawn — the verdicts stand as the scorer's, labelled as such.

## Step 1 — Memo v1.2 (`docs/research/2026-09-03_g1_eval_findings.md`)

In-place edit under the repo convention (header `**Revision:** v1.2` line naming what changed; new DesignNote `supersedes` `c9a81161`). Edits, and only these:

1. **§3, E5 and E6 entries:** after each verdict, one sentence: this is a claim about the sub-L3 level; the independent rater agreed with the scorer's exact level on `{{result:g1_cal_fable_stratum_L2_genuine_scorer_agree}}` of L2 records and `{{…L0_genuine…}}` of L0 records (use the registered stratum-agreement Result names — look them up with `g1_resolve_results.py --prefix g1_cal_fable_stratum`; if the exact per-stratum agreement is not registered as a Result, register it from `…_stratum_agreement_2026-09-03.json` first), so the verdict is the scorer's and is not rater-robust. E4, H3, H4, H5, C1 are untouched: they are L3+/<L3 claims.
2. **§3, one new sentence before the statements:** G1-O's score is the L3+ share; the level distribution beneath it is descriptive, with the calibration's level agreement stated in §4.
3. **§5 limit 6:** replace the lone reviewer parser-miss count with the range sentence form used in §4 (scorer 232 — reviewer 178 — rater-implied 173 on the queue), tokens as registered.
4. **§4:** add one sentence stating the implied-verdict rule's `unparseable` defect and that `{{result:g1_cal_fable_disagreements_with_U}}` of the `{{result:g1_cal_fable_disagreements_listed}}` escalated records are artifacts of it (DD-037 v3 item), leaving `{{result:g1_cal_fable_disagreements_level_gap}}` substantive disagreements.

Nothing else in the memo changes. Report any sentence you judged should change but did not.

## Step 2 — Skeleton G1 note (`usafacts_operationalization_skeleton.md`, → v0.2.8)

One sentence appended to the G1 note: G1-O is scored on the binary (L3+ share of families); the level scale beneath it is recorded for diagnosis and is not rater-robust at the calibration measured (κ_w token). Also fix §7 item 8 to name the two legs (the sentence the freeze RESULT §6.6 reported and left): "G1 supplies that: structured error measures (G1-D) plus an eval of whether AI restatements keep them (G1-O)." Version line bumped.

## Step 3 — DD-038 (one paragraph)

Append to `docs/design_decisions.md`: binary is the score, levels are descriptive; why (the calibration's grain finding, with the two κ tokens and the 18/18, 14/14 counts as tokens); that level-based pre-registered statements keep their scorer verdicts labelled as scorer verdicts; that any future level-based claim needs a level-agreement estimate first. Cite DD-033 (scale), DD-037 (rater).

## Step 4 — Close

`seldon verify` (cron files expected dirty; say so), `seldon cc complete`, RESULT with discrepancies, suite counts, commit, push.

## Discrepancies to report, not reconcile
- If the per-stratum agreement values are not registered Results and cannot be registered without a new derivation script, register them with a minimal script and report it; do not write literals.
- If the memo convention has changed since v1.1, follow the current one and report.

## Not in this task
Any change to scorer, parser, prompts, fixtures, or any registered Result/RESULT/DD. Any re-scoring. Any edit to memo sections beyond §3, §4, §5 limit 6 and the header revision line. Fixing the implied-verdict rule (v3 backlog `73f0aa5d`).
