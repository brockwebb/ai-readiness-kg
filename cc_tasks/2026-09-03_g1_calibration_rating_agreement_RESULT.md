# RESULT: G1 calibration — independent-model rating of the blind sheet, agreement on real labels, escalation list, findings memo §4, DD-037

**Task:** `cc_tasks/2026-09-03_g1_calibration_rating_agreement.md` (no addenda: globbed `…_ADDENDUM*.md`, none found). **Sequencing honoured:** the freeze RESULT existed before this task started. **Instrument frozen:** no file under `assessment/harness/` or `assessment/config/` changed (`git status` on both is empty). Biblio-cron files not committed. **Date:** 2026-09-03 UTC (the rating run's own stamps are 2026-09-04 UTC).

**Headline.** The independent rater answered all 60 records. Rater against the frozen scorer: **κ_w = 0.392 [0.205, 0.614]** (quadratic weights, L0–L4, n = 52), raw agreement 0.442. Rater against the LLM reviewer on the review queue: **κ = 0.421 [0.206, 0.665]** (n = 35), raw agreement 0.686. The pooled-grid genuine-loss count is now a range: **173 (rater-implied) — 178 (reviewer) — 232 (scorer)** of 232 queued records.

## 1. Rating run (the only model spend)

`scripts/g1_calibration_rate.py`, run `g1_calibration_fable_2026-09-03`, ceiling 2,500,000 declared on the shared ledger, model `claude-fable-5-1` selected with `--model`. **`--model claude-fable-5-1` is selectable under Max OAuth**: every one of the 60 envelopes reported `canonicalModel: claude-fable-5-1` and the invariant-5 identity gate passed on all of them; the run never stopped.

| | |
|---|---|
| records rated | **60 of 60**, 0 retried, 0 unparseable after retry |
| rater level distribution | L4 32 · L3 8 · L2 7 · L1 12 · L0 1 · U 0 |
| scorer level distribution in the same 60 | L4 18 · L3 7 · L2 8 · L1 11 · L0 8 · unparseable 8 |
| spend | **1,954,688 tokens settled**, 0 refusals, 0 released, 545,312 left under the ceiling; day total 1,954,688 of the 55,000,000 band |
| evidence | `assessment/evidence/g1/calibration/<sample_id>.claude-fable-5-1.json` — 60 files, each the full prompt, the response verbatim, every attempt, the usage and the reservation id, written **before** the filled sheet |
| output | `assessment/results/g1_calibration_sheet_2026-09-03_filled_fable.md` (DataFile `072f9416`, content-hashed) |

**Independence, enforced rather than asserted** (each is a test in `tests/test_g1_calibration_rate.py`): a different model family, with the reviewer's own model `claude-opus-5` refused by name in code; the call routed through `kg/extraction/model_stub.invoke`, whose hermetic empty cwd keeps CLAUDE.md, the design decisions and every results file out of the rater's context; **one record per call** (asserted: each of the 60 prompts contains exactly one `## C###` heading), so the rater cannot see a distribution and rate to it; and a prompt built from the blind sheet's own instruction paragraph with the D2 scale and D9 families verbatim, carrying the passage, the response, the estimate, the family and its published forms, the mode and the compression level — and, asserted across all 60 prompts, none of `claude-opus-5`, `claude-haiku`, `genuine_loss`, `parser_miss`, `review_note`, `surface_type`, `not_in_queue`, the seed or the stratum table. The three standing gates applied unchanged: DD-007 (OAuth only; `ANTHROPIC_API_KEY` never set), DD-022 (reserve-before-dispatch, run declared with its ceiling), invariant 5.

## 2. Agreement on real labels

`scripts/g1_calibration_agreement.py` **unmodified**, driven by `scripts/register_g1_calibration_results.py`. Report: `assessment/results/g1_calibration_agreement_2026-09-03.json` (DataFile `bcb6147c`); confusion tables `…_confusion_2026-09-03.json` (`b21ce25f`); stratum table `…_stratum_agreement_2026-09-03.json` (`e9f83fd6`). **61 Results** under prefix `g1_cal_fable_`, each `computed_from` the filled-sheet DataFile and `generated_by` the agreement Script.

| comparison | n | κ | 95 % bootstrap | raw agreement |
|---|---:|---:|---|---:|
| rater vs scorer, L0–L4, **quadratic weights** | 52 | **0.392** | [0.205, 0.614] | 0.442 |
| rater vs scorer, six categories incl. `unparseable`/U, unweighted | 60 | 0.199 | [0.092, 0.313] | 0.383 |
| rater vs reviewer, review queue, binary verdict | 35 | **0.421** | [0.206, 0.665] | 0.686 |

Positive specific agreement on the minority call (`parser_miss`) 0.718; 0 queue records excluded for a rater U (the rater never used U).

**The range** (pooled Opus grid, 232 queued records): **rater-implied 173 — reviewer 178 — scorer 232**, implied U 0.0. The extrapolation, registered weight by weight and rate by rate (`g1_cal_fable_range_weight_*`, `g1_cal_fable_range_rate_*`): the sum over the eight queue strata of (the pooled grid's stratum population) × (the share of that stratum's rated sample the rater put below L3, U excluded). **It assumes stratum-homogeneity** — that the rater's genuine share inside a stratum is the same in the grid as in the 60-record sample, which mixes pooled-Opus and control-arm records. The weights come from the pooled file itself (650 records, 232 in queue), not from the sheet's stratum table, because the sheet's population includes the control arm.

**Stratum-level agreement** (`n` rated, agreement with the scorer's exact level / with the reviewer's verdict): L4·not_in_queue 18 → 1.000 / — · L3·not_in_queue 7 → 0.143 / — · L2·genuine 5 → 0.000 / 1.000 · L2·parser_miss 3 → 0.000 / 1.000 · L1·genuine 7 → 0.571 / 0.714 · L1·parser_miss 4 → 0.000 / 1.000 · L0·genuine 4 → 0.000 / 0.000 · L0·parser_miss 4 → 0.000 / 1.000 · unparseable·genuine 5 → 0.000 / 0.000 · unparseable·parser_miss 3 → 0.000 / 1.000.

The two instruments agree completely on preserved-exact records (18/18) and on every flagged record the reviewer called a parser miss (14/14 across four strata); they disagree about *which* sub-L3 level a loss is. That moves the level distribution, not the loss count — which is why the range's lower bound (173) lands within five records of the reviewer's count (178) while κ_w on the levels is middling.

## 3. Escalation list

`assessment/results/g1_calibration_disagreements_2026-09-03.md` (DataFile `4e580e07`): **9 of the 60 rated records** — 4 separated by two or more levels, 5 where one side had no level to give. Per record: sample id, record id, family, mode, compression, evidence path, scorer level, reviewer verdict and its note, rater level and its note, and the passage and response as printed on the blind sheet. No commentary, no proposed resolution. Counts registered as three further Results (`g1_cal_fable_disagreements_listed` / `_level_gap` / `_with_U`), so the memo can cite them as tokens.

**ResearchTask handling — `85851bcd` is left `proposed`.** Two reasons, both reported rather than worked around: `seldon task close` does not exist (the CLI has `create`, `list`, `show`, `update`), and, more to the point, `85851bcd`'s description says *"Operator labels the G1 reviewer-calibration sheet"* — the operator did not label it, so closing it would record something that did not happen. The replacement ResearchTask **`529133e4`** carries the correct description (rater identity, the two κ values, the range, the escalation-list path, "operator review OPTIONAL", and that it supersedes `85851bcd`) and is in state `completed`; the ontology has no direct `proposed → completed` transition, so it was walked `proposed → accepted → in_progress → completed`.

## 4. Findings memo §4 and DD-037

**Memo** `docs/research/2026-09-03_g1_eval_findings.md`, §4 replaced: the rater's identity and the four enforced independence conditions; both κ values with their intervals, n and raw agreement; the genuine-loss range as three tokens; where the agreement sits by stratum; a plain statement that the coefficient measures agreement between two instruments and establishes neither one's correctness; and the escalation list's count and path. **200 `{{result:}}` tokens, 200 resolved** (`scripts/g1_resolve_results.py --check`). No literal measurement was introduced.

**Registration convention.** This repo's convention for a document *edited in place* is a dated version line in its header plus a new artifact for the new version (the skeleton's `**Status:** v0.2.7 … Prior: v0.2.6 …`; `docs/design_decisions.md` gets one DesignNote per entry at the same path). Its convention for a *correction to a research memo* is a separate file (`…_ERRATUM-01.md`, `…_F7_addendum.md`). The task directed replacing §4's paragraph, not writing an erratum, so the in-place convention applies: a `**Revision:** v1.1` line was added to the memo header naming what changed and what did not, and DesignNote **`c9a81161`** registers v1.1 with `supersedes` = `6760baaf` (v1.0, not deleted). Reported below as the one edit outside §4.

**DD-037** appended to `docs/design_decisions.md` (DesignNote `fa36a92d`): the independent-model rater design and its enforced conditions; the no-threshold consequence rule (a range, not a verdict — a low κ widens the range and triggers nothing, and no Landis & Koch band is named); the disagreement list as the operator's only, optional touchpoint, with the G1 touchpoint list closed to the January threshold, over-cap spend, and distribution decisions; what the coefficient does and does not establish; and the extrapolation with its assumption. Prior art searched and cited first, including the failed part of the search: no named method exists for calibrating an LLM reviewer against a second model when no human labels exist — Han et al. (arXiv:2510.09738) is the nearest and its criterion is human agreement, which this design does not have.

## 5. Provenance backfill — **skipped**

There is no `seldon result backfill-provenance`: `seldon result` offers only `check-stale`, `list`, `register`, `trace`, `verify`, and the only match for "backfill" in the Seldon source is an unrelated comment in `mcp_server.py` (checked at seldon `dd66519`). Seldon task `0bc41cfc` is not in this project's graph either (`seldon artifact show 0bc41cfc` → "no artifact found"). Nothing was hand-written: the 515 `g1_v2_pooled_opus_*` Results still carry no `computed_from` edge to DataFile `0bc7bcdb`, exactly as the freeze RESULT recorded.

## 6. Verification and spend

| check | value |
|---|---|
| root `tests/` suite | **719 passed** (was 683; +36 across two new test files) |
| `assessment/` suite | **471 passed, 1 skipped** (unchanged — the instrument was not touched) |
| instrument frozen | `git status assessment/harness assessment/config` — empty |
| `kg.spend status` | run `g1_calibration_fable_2026-09-03`: ceiling 2,500,000, **settled 1,954,688**, outstanding 0, released 0, refusals 0; day total 1,954,688 of 55,000,000 |
| `seldon verify` | 1 issue: `docs/corpus/acquisition_candidates.md` modified — the biblio cron (Seldon task `989daaad`), not this task; expected and left |
| artifacts registered | 64 Results (`g1_cal_fable_*`), 5 DataFiles, 2 DesignNotes, 1 ResearchTask completed |

## 7. Discrepancies (premise vs live state) — reported, not reconciled

1. **The pre-registered implied-verdict rule cannot express agreement on an `unparseable` record.** `unparseable` has no position on the level scale, so *any* level the rater gives is "above" it and implies `parser_miss` — even when the rater's level (L1 "omitted", L2 "verbal band") says plainly that the qualifier is missing and the reviewer's `genuine` says the same. All five `unparseable | genuine` sample records are forced disagreements for that reason (stratum agreement 0.000), and they are five of the nine records on the escalation list. This depresses the rater-vs-reviewer κ. The rule was frozen before any rating existed and **is not patched here**; the range is unaffected because it reads the rater's level directly rather than through the rule. Recorded in DD-037 as a v3 item.
2. **The agreement script did not fail on any real-label edge case.** The task anticipated a traceback; there was none. It ran unmodified on all 60 records.
3. **The unparseable-answer clause never triggered.** The task provided for reporting raw responses and suppressing the extrapolation if more than 6 of 60 rater answers were unparseable after one retry; 0 were, and no retry was needed. Every response came back in the exact two-line shape requested.
4. **One edit outside §4:** a `**Revision:** v1.1` line in the memo header. The task's "not in this task" boundary names memo sections other than §4, and its step-4 instruction is to register the edit per the project's convention for updated memos — which, for a document edited in place, *is* a dated version line in the header (§4 above). Reported here rather than treated as licensed.
5. **One reviewer count outside §4 still stands alone.** §5 limit 6 cites the pooled parser-miss count (the token `g1_v2_pooled_opus_parser_misses`, 54) on its own. Editing it would touch a memo section other than §4, which the task excludes, so it is left; §4 now states the rule that governs every reviewer count in the memo, and limit 6's number is bounded by §4's range.
6. **Only the pooled grid has a rater-implied bound.** The sample was drawn to represent the pooled Opus grid, so the holdout, dev and control reviewer counts in §4 stand as the reviewer's alone; they are read against the agreement measured here. No range was invented for them.
7. **No `seldon task close`, and `85851bcd`'s wording does not permit closing** (§3): it is left `proposed`, with `529133e4` created and walked to `completed`.
8. **Step 5 skipped** (§5): the CLI has no `backfill-provenance` and Seldon task `0bc41cfc` is not in this graph.
9. **The rater's own model-family limit, stated because it bounds the finding:** both raters are language models, so a shared error a human would not make is possible. A different family with no shared context reduces that risk without removing it, and no human has labelled any of these records. The range is a statement about instrument disagreement, not about truth.

## Not in this task, by its own boundary

Any change to parser, scorer, prompts or fixtures (none made); any threshold on κ (none set, and no verbal band named); any edit to a registered Result, RESULT, DD, or a memo section other than §4 (none, beyond the header revision line disclosed in §7.4); operator labelling; rating by any model other than `claude-fable-5-1`.
