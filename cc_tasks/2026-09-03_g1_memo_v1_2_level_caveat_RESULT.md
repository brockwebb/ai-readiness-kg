# RESULT: G1 memo v1.2 — level-based verdicts qualified by the calibration; the binary is the score; skeleton v0.2.8; DD-038

**Task:** `cc_tasks/2026-09-03_g1_memo_v1_2_level_caveat.md` (no addenda: globbed `…_ADDENDUM*.md`, none found). **Sequencing honoured:** the calibration RESULT existed before this task started. **Spend: zero model calls** — no `claude -p`, no ledger reservation, `ANTHROPIC_API_KEY` never set. **Instrument frozen:** `git status` on `assessment/harness` and `assessment/config` is empty. Biblio-cron files not committed. **Date:** 2026-09-03 UTC.

**Nothing was re-scored and nothing withdrawn.** E5 and E6 keep their coded verdicts; what changed is that each now says whose reading it is.

## 0. The missing Results, registered first

The memo had to say "the rater matched the scorer's exact level on 0 of 5 L2 records" and "on all 18 preserved-exact records", and may not write a literal. The step-2 registration of the calibration had registered each stratum's agreement *rate* with the scorer and its rated `n`, but not the numerators, not the reviewer-side counts, and not the two aggregates that carry the grain finding. Per the task's discrepancy clause these were registered with a minimal script rather than written as literals: `scripts/register_g1_calibration_stratum_results.py`, **42 Results**, read from `assessment/results/g1_calibration_stratum_agreement_2026-09-03.json` (itself produced by the unmodified agreement script) and not recomputed:

`g1_cal_fable_stratum_scorer_agreed_<level>_<verdict>` · `…_stratum_reviewer_n_<…>` · `…_stratum_reviewer_agreed_<…>` · `…_stratum_reviewer_agreement_<…>` · `g1_cal_fable_preserved_exact_n` / `_agreed` (18 / 18) · `g1_cal_fable_parser_miss_reviewer_n` / `_agreed` (14 / 14).

No existing Result was touched.

## 1. Memo v1.2 (`docs/research/2026-09-03_g1_eval_findings.md`)

Four edits, and only these; **214 `{{result:}}` tokens, 214 resolved.**

1. **§3, before the statements** — one sentence: G1-O's score is the L3+ share of families and the level distribution beneath it is descriptive, because the calibration found the two instruments agree on L3+ against below-L3 and disagree on which sub-L3 level a loss is; a statement about levels carries the caveat printed with it, one about the L3+ share does not.
2. **§3, E5** — after the verdict: this is a claim about which sub-L3 level a failure sits at, and the level scale is the part of the instrument the calibration found least robust; the rater matched the scorer's exact level on **0 of 5** L2 records and **0 of 4** L0 records; the verdict stands as the scorer's and is not rater-robust.
3. **§3, E6** — the same caveat on the L2 claim, plus what the rater *does* confirm on those records: the loss call rather than the level (its verdict matched the reviewer's on 5 of 5 sampled L2 records called genuine losses and 3 of 3 called parser misses).
4. **§4** — one sentence: the 5 escalated records where one side had no level to give are artifacts of the pre-registered implied-verdict rule (`unparseable` has no position on the level scale, so any level the rater gives reads as "the parser missed it" even when both sides agree the qualifier is absent), the rule is frozen and not patched here (DD-037; v3 backlog `73f0aa5d`), leaving **4 substantive** disagreements.
5. **§5 limit 6** — the lone reviewer parser-miss count is replaced by §4's range form: of the 232 queued records, genuine losses 173 (rater-implied) — 178 (reviewer) — 232 (scorer), the rest of the queue being parser misses under whichever bound is read.

**E4, H3, H4, H5 and C1 are untouched** — every one is an L3+/below-L3 claim, which is the grain the calibration found robust.

**Registration convention, unchanged since v1.1** and followed here: a document edited in place gets a dated `**Revision:**` line in its header naming what changed and what did not, plus a new artifact for the new version. Header line added; DesignNote **`92795fa0`** registers v1.2 with `supersedes` = `c9a81161` (v1.1, not deleted).

## 2. Skeleton → v0.2.8

`docs/crosswalk/usafacts_operationalization_skeleton.md`. The G1 note gains one sentence: G1-O is scored on the binary (the L3+ share of qualifier families) and the five-level scale beneath it is recorded for diagnosis rather than scoring, because the rater and the scorer agree on L3+ against below-L3 and disagree on which sub-L3 level a loss is (κ_w as a token), so a level-based reading is the scorer's and is not rater-robust (DD-038). It also records that the sheet was rated by an independent model rather than the operator (DD-037). §7 item 8 now names the two legs: *"G1 supplies that: structured error measures (G1-D) plus an eval of whether AI restatements keep them (G1-O)"* — the sentence the freeze RESULT §6.6 reported and left. Version line bumped, prior version retained.

## 3. DD-038

One paragraph appended to `docs/design_decisions.md` (DesignNote `4ce326b1`): the binary is the score and the levels are descriptive; why, with the grain finding in tokens (18/18 preserved-exact, 14/14 reviewer parser-misses, the 173–178 of 232 range against exact-level agreement 0 of 5 and 0 of 4, and κ_w 0.392 [0.205, 0.614] against κ 0.421 [0.206, 0.665] on the binary verdict); that E5 and E6 keep their coded verdicts labelled as the scorer's while E4/H3/H4/H5/C1 are untouched; and that **any future level-based claim needs a level-agreement estimate at its own grain first**. No κ threshold is set, here or anywhere in G1 — low agreement qualifies a claim, it does not gate one. Cites DD-033 (the scale) and DD-037 (the rater).

## 4. Verification

| check | value |
|---|---|
| root `tests/` suite | **719 passed** (unchanged — the new script is a registration wrapper over an already-tested derivation) |
| `assessment/` suite | **471 passed, 1 skipped** (unchanged) |
| instrument frozen | `git status assessment/harness assessment/config` — empty |
| token resolution | memo 214/214, skeleton 3/3, `design_decisions.md` 17/17 |
| model calls | **0** — no ledger entry for this task |
| `seldon verify` | 1 issue: `docs/corpus/acquisition_candidates.md` modified — the biblio cron (Seldon task `989daaad`), not this task; expected and left |
| artifacts | 42 Results, 2 DesignNotes |

## 5. Discrepancies (premise vs live state) — reported, not reconciled

1. **The per-stratum agreement counts were not registered Results**, only the rates and the rated `n`. Registered with a minimal script (§0) rather than written as literals, exactly as the task's discrepancy clause directs. The reviewer-side per-stratum counts and the two aggregates (18/18, 14/14) were also missing and are registered in the same pass.
2. **E3 is a level claim and did not get the caveat.** §3's E3 entry reads *"Form shift (L2) was pre-registered as the most frequent non-omission failure. In the v1 grid it never occurred: 0 L2 records in 196."* That is a claim about a sub-L3 level, so by DD-038's rule it belongs with E5 and E6. The task enumerated E5 and E6 and listed E4/H3/H4/H5/C1 as untouched, so E3 was outside the authorised edits and is **left as it stands**. Two things make it a weaker case than E5/E6 and neither is a reason to skip it permanently: it is a *zero* count (no L2 record existed to disagree about), and it was scored under the v1 parser and scorer, while the calibration measured the v2 scorer — the level agreement registered here does not directly apply to it. Reported for a later task to settle.
3. **The skeleton now contains `{{result:}}` tokens for the first time.** Its previous convention was to cite Result *names* without values (the v0.2.7 G1 note names the Results behind the dissociation statement); the task asked for a "κ_w token". Tokens were used as instructed, and the skeleton is now a file that must be rendered or checked with `g1_resolve_results.py` before anyone reads a number off it. If the operator prefers the name-only convention there, reverting is a one-line change.
4. **§5 limit 6 is inside the memo's §5**, which the task's "not in this task" line excludes in general while its step 1 item 3 names limit 6 specifically. The specific instruction was followed and nothing else in §5 was touched.
5. **The one-sentence budget was exceeded in two places.** §3's E5 and E6 caveats each run to two sentences: one stating that this is a level claim with the agreement figures, one saying what the verdict therefore is (or, for E6, what the rater does confirm). The task asked for "one sentence"; the second sentence carries the consequence, which is the point of the caveat, and packing both into one sentence made it unreadable.

## Not in this task, by its own boundary

Any change to scorer, parser, prompts or fixtures (none); any re-scoring (none); any edit to a registered Result, RESULT or existing DD (none — DD-038 is appended, and the two prior memo DesignNotes are superseded rather than edited); any memo edit beyond §3, §4, §5 limit 6 and the header revision line; fixing the implied-verdict rule (v3 backlog `73f0aa5d`).
