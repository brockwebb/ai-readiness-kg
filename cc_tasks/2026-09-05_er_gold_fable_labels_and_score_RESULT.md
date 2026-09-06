# RESULT: the gold sample is labelled and scored — stratum E found the false merges the homograph pass left behind

**Task:** `cc_tasks/2026-09-05_er_gold_fable_labels_and_score.md` §1–§5. **No addenda** — globbed before starting, none exist. **Dated 2026-09-05; executed 2026-09-06 UTC** (the band had rolled over, which is why 4.1M fits). **Spend: 4,063,448 tokens settled** against 4,732,014 declared, stop threshold 8,000,000 — not approached. Claude Max OAuth. **Task file committed before execution** (`3b1eb30`).

**Lead, in the order §5 asks for.**

## §1. Stratum E — the measurement the homograph split was waiting on

| | |
|---|---:|
| pipeline says **match** on all 20 | |
| rater: `same` | 16 |
| rater: **`different`** | **2** |
| rater: `uncertain` | 2 |
| **precision in stratum E** | **0.8889** |
| Wilson 95 % CI | **[0.672, 0.969]** |

**Both false merges are the same term, and it is a construct-arm homograph.** `air:concept/accessibility`:

> **P089** — `mitre-ai-maturity-model::d-accessibility` (arm `org_maturity`) merged with `statistical-policy-working-paper-46-data-quality-assessment::c_accessibility` (arm `publication_actionability`).
> *"Node A's bare 'Accessibility' in an AI maturity model context is an organizational-capability dimension, while Node B defines accessibility specifically as 'the ease with which the data file extract can be obtained from the administrative agency', a data-quality dimension for administrative data."*

> **P090** — the same MITRE node merged with `wilkinson-2016-fair-guiding-principles::c_accessibility`.
> *"Node A's 'Accessibility' sits inside an organizational maturity model, while Node B's 'Accessibility' is a FAIR data principle for 'scientific data management and stewardship' — a homonymous label applied to two distinct concepts (organizational capability vs. a data-stewardship property)."*

**This independently confirms DD-046's diagnosis, on a term the homograph pass was never asked about.** `air:concept/accessibility` was classified **`auto_keep`** with arms `{org_maturity: 1, publication_actionability: 29, training_data_readiness: 1}` — cross 0.6143, within 0.5251, **`s` = +0.0891**. Exactly the failure mode the positive control caught on `ai-ready`: **an arm holding one member contributes to `cross` and nothing to `within`**, `s` goes positive, the auto-keep limb fires, and a genuine homograph survives. The gold rater, seeing only two spans and no scores, caught it.

Both of stratum E's `uncertain` pairs point the same way — `air:concept/interoperability` (`{org 1, pub 18, train 3}`, `s` = +0.028) and `air:concept/accuracy` (`{org 4, pub 21, train 1}`, `s` = +0.003), both `auto_keep`, both with a one- or few-member arm.

## §2. DD-045 §3 verdict: **PASS on both thresholds — with an interval caveat that matters more than the verdict**

| metric | measured | floor | Wilson 95 % CI | n_eff |
|---|---:|---:|---|---:|
| pairwise **precision** | **0.9945** | 0.95 | **[0.8368, 0.9998]** | 21.1 |
| pairwise **recall** | **0.9920** | 0.80 | [0.8334, 0.9997] | 21.2 |
| cluster F1 | 0.8996 | — (reported, never a gate) | cluster P 0.8819 / R 0.9180 | |
| **verdict** | **PASS** | | | |

97 of 100 pairs scored; 3 `uncertain`, excluded by the sheet's own rule.

**The caveat, stated because the verdict alone would mislead.** DD-045 §3 puts the threshold on the point estimate and asks for the interval alongside; that is what the scorer implements. But **the precision interval's lower bound, 0.8368, sits below the 0.95 floor.** The reason is structural, not a defect: 20 pairs drawn from a stratum of 16,624 carry a weight of 831.2, and the design-effect correction reduces 97 scored pairs to an **effective n of 21**. **No 100-pair stratified sample of this shape can certify a 0.95 precision floor with a lower bound above it.** The estimate passes; the sample cannot rule out failure at 95 % confidence. If a future pass lands near the floor rather than comfortably above it, that is the moment to spend more sample — or a human rater — and DD-045 addendum-01 says so.

**Second caveat: the population estimate is stratum A.** Weighted, A contributes 15,793 of the 16,570 weighted true positives — 95 %. The 0.9945 headline means *"the pairs the pipeline is asked about in the population are overwhelmingly easy exact-name matches, and it gets those right"*, not *"the pipeline is right 99 % of the time on hard cases"*. The per-stratum table is where the hard cases live:

| stratum | what it is | tp | fp | fn | tn | precision | recall | pipeline |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A | exact-name auto-links | 19 | 0 | 0 | 0 | **1.000** | 1.000 | match |
| B | clerical band, accepted | 20 | 0 | 0 | 0 | **1.000** | 1.000 | match |
| C | clerical band, rejected | 0 | 0 | 1 | 19 | — | **0.000** | no match |
| D | near-miss, cosine ∈ [0.70, 0.80) | 0 | 0 | 6 | 14 | — | **0.000** | no match |
| E | cross-arm in KEPT terms | 16 | **2** | 0 | 0 | **0.889** | 1.000 | match |

**Stratum B is the vindication of the prior task's clerical band: 20 of 20 accepted merges are correct.** Stratum C is the same band's rejections: 19 of 20 correct, one miss.

**Stratum D is where recall actually leaks.** Six of 20 near-misses just under the 0.80 floor are genuine matches, and they are all surface-form variants an exact-name rule cannot see: `Resource Description Framework (RDF)` ↔ `the W3C RDF (Resource Description Framework) standard`; `honors robots.txt exclusion protocol` ↔ `robots.txt lets automated tools know what access to a site is considered acceptable`; `SDMx 2.0 Technical Specifications` ↔ `SDMX Technical Standards`; `Agency Inventory of AI Use Cases` ↔ `AI use case inventory`; plus `data governance` and a truncated `subject protection`. Weighted to population that is ≈ **129 missed merges** — 0.8 % of the gold-same population, which is why the headline recall still reads 0.992. Within stratum D, recall is **zero**.

## §3. Test–retest: raw agreement **1.000**, Cohen's κ **1.000**

30 pairs re-rated in a fresh hermetic pass (seeded draw, 6 per stratum, seed 20260905): **30 of 30 identical**, zero verdicts changed. Marginals 20 `same` / 10 `different`.

Reported, not gated — and with two limits on its face. Perfect self-consistency measures **determinism, not accuracy**: a rater that is confidently wrong the same way twice scores 1.000 here. And **the seeded draw happened to contain none of the three `uncertain` pairs**, which are by construction the least stable, so the reliability bound is measured on the easy part of the sheet.

## §4. Escalations: **none**

`docs/research/2026-09-05_er_gold_escalations.md` is written and says so. The rule was applied mechanically, not estimated: for each of the 3 `uncertain` pairs, the sheet was **re-scored with that verdict flipped to `same` and to `different`**, and neither flip moved a DD-045 threshold verdict. It cannot — precision sits 0.045 above its floor and recall 0.19 above its, and one pair of 97 moves either by well under that. **There is nothing here that needs the operator's judgment**, which is the correct outcome for a narrow-band sensor.

The three `uncertain` pairs share one shape and it is an extraction finding, not a rating problem: **a node whose grounding span is the bare term itself gives a reader nothing to judge.** P088 — *"Node A's span is only the bare word 'interoperability' with no referent"*; P091 — *"Node A is only the bare word 'accuracy' with no definition"*; P018 — two `Google` nodes whose spans identify no specific product.

## §5. Premises this task got wrong

1. **The task is dated 2026-09-05; it executed on 2026-09-06 UTC.** This matters only because the spend band had rolled over — at the 2026-09-05 close there were ~3.0M tokens of headroom and this run needed 4.1M, so on the stated date it would have refused mid-pass.
2. **DD-045 §4's "gold is human-labelled" is withdrawn**, as the task instructs. Addendum-01 appended, with the limitation carried on every derived Result: a same-family rater bounds correctness relative to that rater, and a shared error between two models of one lab is invisible to any agreement statistic between them.
3. **"~30.8k tokens/pair, expect ~4.5M"** — measured 31,240.8 on the calibration and 31,263.5 on the main pass, total 4,063,448. The estimate was good to 10 %.
4. **The `er_gold_*` Results could not register until their DataFiles existed.** `score_er_gold.py` named `er_gold_scores_2026-09-05` and `er_gold_finalize.py` named `er_gold_analysis_2026-09-05`; the first was registered by the prior task, the second was not. Registered here. No number changed.
5. **Not a premise error but worth flagging:** the task says "register per-stratum precision/recall with Wilson intervals". Strata C and D have **no** pipeline-matched pairs, so precision is undefined there and no Result is registered for it — an undefined rate must not be published as a number. Recall is registered for all five.

## §6. Verification

| check | result |
|---|---|
| `python -m pytest tests/` | **845 passed** |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** |
| `git diff` on `state/er_gold_key.json`, `cq_set_v1.yaml`, `cq_set_v2.yaml`, `kg/schema.yaml` | **empty, all four** |
| sheet's pair set | unchanged — 100 pairs, same ids, only the blanks filled |
| `scripts/score_er_gold.py` logic | unchanged |

**Registered.** 2 Scripts (`er_gold_rate`, `er_gold_finalize`); 3 DataFiles, all `snapshot: true`; **15 Results** — the four DD-045 verdict Results (`er_gold_precision` 0.9945, `er_gold_recall` 0.9920, `er_gold_cluster_f1` 0.8996, `er_gold_verdict` 1), 7 per-stratum precision/recall with Wilson intervals, `er_gold_retest_agreement` 1.0, `er_gold_retest_kappa` 1.0, `er_gold_escalations` 0, plus `er_gold_tokens_declared` and `er_gold_tokens_settled`; **DD-045 addendum-01**.

## §7. What this leaves for the next task, and what it does not

The pipeline **passes** DD-045 §3 on the point estimates. The two things worth acting on are both narrow and both already diagnosed:

* **`air:concept/accessibility` is a measured false merge** and the auto-keep rule that let it through is the one DD-046 already identified. The same-arm null distribution DD-046 records as the fix would address it; nothing here changes that recommendation, it only supplies the first independent evidence that the fix is needed.
* **Stratum D's zero recall** says the 0.80 embedding floor discards real matches that are surface-form variants — expansion, article, truncation. That is an alias-generation problem, not a threshold problem.

Neither is acted on here. **Out of scope and untouched:** CQ-27's schema gap (Issue `2a2b6461`), epoch 2, the 41 `no consumer` deferrals, the memo and the deck, and any change to the homograph thresholds.
