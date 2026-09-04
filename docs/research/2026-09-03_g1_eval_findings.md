# G1 EVAL — findings at the v2 freeze

**Date:** 2026-09-03. **Status:** internal; not for distribution until the operator says so.
**Revision:** v1.1, 2026-09-03 — §4 replaced: the reviewer's genuine-loss count is now reported as a range bounded by the scorer's count and an independent model rater's, with the two agreement coefficients and the escalation list (task `cc_tasks/2026-09-03_g1_calibration_rating_agreement.md`, DD-037). No other section changed. Prior: v1.0, 2026-09-03.
**Instrument:** parser `g1-parse-v2`, scorer `g1-score-v2`, prompt epoch `g1-v2-2026-09-03`,
pinned consumer `claude-opus-5` — frozen for the January pilot (DD-036).
**Numbers:** every number in this memo is a `{{result:<NAME>:value}}` token resolving to a
registered Seldon Result; render with
`/opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --render <this file> --out <out>`
and check with `--check`. No literal here is a measurement.

## 1. Question and construct

G1 asks whether a data product's uncertainty is legible to an AI consumer, which the prior-art
memo (`docs/research/2026-09-02_g1_eval_prior_art.md`, with its F7 addendum and ERRATUM-01)
established has no named metric: the literature measures numeric faithfulness, generalization
bias and quantity hallucination, but nothing measures whether the qualifier attached to an
estimate survives restatement. DD-033 fixed the construct as an ordinal preservation scale over
one estimate and its published qualifiers, with retrieval removed by construction and an honest
`unparseable` outcome; DD-034 made the parser a versioned instrument whose readiness is measured
only on sealed held-out model output; DD-035 made the scored unit the qualifier family, made
binding explicit, and moved the fixtures onto product surfaces captured as served with a
compression budget as a pre-registered factor. This memo reports what the instrument measured
across v0, v1 and v2, and what it does not measure.

## 2. The instrument at freeze

| component | at freeze |
|---|---|
| fixtures, dev | {{result:g1_v2_instrument_fixture_dev_propositions:value}} propositions on {{result:g1_v2_instrument_fixture_dev_passages:value}} passages: table_coded {{result:g1_v2_instrument_fixture_dev_table_coded_propositions:value}}, table_labeled {{result:g1_v2_instrument_fixture_dev_table_labeled_propositions:value}}, footnoted {{result:g1_v2_instrument_fixture_dev_footnoted_propositions:value}}, flagged_cell {{result:g1_v2_instrument_fixture_dev_flagged_cell_propositions:value}} (`assessment/tests/fixtures/g1/v2/propositions.yaml`), plus the v1 `prose_labeled` passages re-split into dev |
| fixtures, holdout | {{result:g1_v2_instrument_fixture_holdout_propositions:value}} propositions on {{result:g1_v2_instrument_fixture_holdout_passages:value}} passages: table_coded {{result:g1_v2_instrument_fixture_holdout_table_coded_propositions:value}}, table_labeled {{result:g1_v2_instrument_fixture_holdout_table_labeled_propositions:value}}, footnoted {{result:g1_v2_instrument_fixture_holdout_footnoted_propositions:value}}, flagged_cell {{result:g1_v2_instrument_fixture_holdout_flagged_cell_propositions:value}} (`propositions_holdout.yaml`); dev and holdout are different surface files, zero passage overlap |
| surfaces | the 17 product surfaces admitted under epoch `g1sfc-2026-09-03`, captured as served (JSON, CSV, PDF, browser-rendered text), each with `surface_type`, `surface_format` and its exact request URL |
| prompts | `assessment/config/g1_prompts.toml`, epoch `g1-v2-2026-09-03`: one direct template, and one indirect template per compression budget (`none` — byte-identical to the v0 indirect template, `short`, `tight`) |
| consumer | `claude-opus-5` pinned; `claude-haiku-4-5-20251001` as a single control arm on the holdout grid only, reported beside and never pooled (D13) |
| scoring | qualifier families (D9) as the record unit, binding by anchor / estimate-in-clause / label competition / anaphora (D10), covariates never scored (D11) |
| schedule | pre-registered in `assessment/config/g1_v2_schedule.toml` before any call: dev {{result:g1_v2_instrument_schedule_dev_steps:value}} steps ({{result:g1_v2_instrument_schedule_dev_new_calls:value}} new calls), holdout {{result:g1_v2_instrument_schedule_holdout_steps:value}} ({{result:g1_v2_instrument_schedule_holdout_new_calls:value}}), control {{result:g1_v2_instrument_schedule_control_steps:value}} ({{result:g1_v2_instrument_schedule_control_new_calls:value}}) — {{result:g1_v2_instrument_schedule_new_calls_total:value}} new calls, {{result:g1_v2_instrument_schedule_tokens_at_floor:value}} tokens at the DD-022 floor, against {{result:g1_v2_instrument_schedule_calls_without_reuse:value}} calls and {{result:g1_v2_instrument_schedule_tokens_at_floor_without_reuse:value}} tokens without byte-identical reuse |
| readiness gate, v1 (fresh responses only) | {{result:g1_v1_holdout_fresh_all_unparseable:value}} of {{result:g1_v1_holdout_fresh_all_n:value}} records unparseable — share {{result:g1_v1_holdout_fresh_gate_unparseable_share:value}}, threshold 0.10, **passed**; {{result:g1_v1_holdout_fresh_all_L3plus:value}} of {{result:g1_v1_holdout_fresh_all_scored:value}} scored at L3+ ({{result:g1_v1_holdout_fresh_all_preservation_rate:value}}, Wilson [{{result:g1_v1_holdout_fresh_all_wilson95_lower:value}}, {{result:g1_v1_holdout_fresh_all_wilson95_upper:value}}]) |
| readiness gate, v2 (sealed holdout, pinned consumer) | {{result:g1_v2_holdout_all_unparseable:value}} of {{result:g1_v2_holdout_all_families:value}} family records unparseable — share {{result:g1_v2_holdout_gate_unparseable_share:value}}, threshold 0.10, **passed**; {{result:g1_v2_holdout_all_L3plus:value}} of {{result:g1_v2_holdout_all_scored:value}} scored families at L3+ ({{result:g1_v2_holdout_all_preservation_rate:value}}, Wilson [{{result:g1_v2_holdout_all_wilson95_lower:value}}, {{result:g1_v2_holdout_all_wilson95_upper:value}}]) |
| spend | {{result:g1_v2_instrument_spend_g1_eval_v2_dev_2026-09-03_settled:value}} + {{result:g1_v2_instrument_spend_g1_eval_v2_dev_2026-09-03_b_settled:value}} (dev) + {{result:g1_v2_instrument_spend_g1_eval_v2_holdout_2026-09-03_settled:value}} (holdout) + {{result:g1_v2_instrument_spend_g1_eval_v2_control_2026-09-03_settled:value}} (control) = {{result:g1_v2_instrument_spend_task_total:value}} tokens, each run under its declared 2,000,000 ceiling |

The v0/v1 evidence re-scored under the frozen pair: {{result:g1_v2_rescore_v1_pooled_all_L3plus:value}} of
{{result:g1_v2_rescore_v1_pooled_all_scored:value}} families at L3+
({{result:g1_v2_rescore_v1_pooled_all_preservation_rate:value}}), {{result:g1_v2_rescore_v1_pooled_all_unparseable:value}}
unparseable, {{result:g1_v2_rescore_v1_pooled_genuine_losses:value}} genuine losses against the
{{result:g1_v1_pooled_genuine_losses:value}} the v1 scorer produced on the same responses.

## 3. Findings

Each row is a statement registered before the responses it is tested on were read. Verdicts are
the coded verdicts in `expectations_v2` of the named results file.

**E3 (v1, not supported).** Form shift (L2) was pre-registered as the most frequent non-omission
failure. In the v1 grid it never occurred: {{result:g1_v1_pooled_all_level_degraded_verbal:value}} L2 records in
{{result:g1_v1_pooled_all_n:value}}; the non-omission failures were quantity hallucination
{{result:g1_v1_pooled_all_failure_quantity_hallucination:value}} and binding error
{{result:g1_v1_pooled_all_failure_binding_error:value}}. The v1 consumer either carried the number or dropped it.

**E4 (v2, supported).** Family loss rises with the compression budget: loss
{{result:g1_v2_pooled_opus_E4_loss_rate_none:value}} at `none`, {{result:g1_v2_pooled_opus_E4_loss_rate_short:value}} at
`short`, {{result:g1_v2_pooled_opus_E4_loss_rate_tight:value}} at `tight`
({{result:g1_v2_pooled_opus_indirect_none_L3plus:value}}/{{result:g1_v2_pooled_opus_indirect_none_scored:value}},
{{result:g1_v2_pooled_opus_indirect_short_L3plus:value}}/{{result:g1_v2_pooled_opus_indirect_short_scored:value}},
{{result:g1_v2_pooled_opus_indirect_tight_L3plus:value}}/{{result:g1_v2_pooled_opus_indirect_tight_scored:value}} preserved).
The ordering holds and the `none` and `tight` intervals are disjoint.

**E5 (v2, supported).** Under `tight`, omission is the modal failure:
{{result:g1_v2_expect_E5_failures_at_tight:value}} failures, of which L1
{{result:g1_v2_expect_E5_L1:value}}, L2 {{result:g1_v2_expect_E5_L2:value}}, L0 {{result:g1_v2_expect_E5_L0:value}};
by class, omission {{result:g1_v2_expect_E5_class_omission:value}}, form shift
{{result:g1_v2_expect_E5_class_form_shift:value}}, suppression override
{{result:g1_v2_expect_E5_class_suppression_override:value}}, decontextualization
{{result:g1_v2_expect_E5_class_decontextualization:value}}, quantity hallucination
{{result:g1_v2_expect_E5_class_quantity_hallucination:value}}.

**E6 (v2, supported).** The verbal-band mechanism v1 never saw appears under compression: L2 rate
{{result:g1_v2_pooled_opus_E6_L2_rate_none:value}} at `none`
({{result:g1_v2_pooled_opus_indirect_none_level_degraded_verbal:value}} of
{{result:g1_v2_pooled_opus_indirect_none_scored:value}}) against
{{result:g1_v2_pooled_opus_E6_L2_rate_tight:value}} at `tight`
({{result:g1_v2_pooled_opus_indirect_tight_level_degraded_verbal:value}} of
{{result:g1_v2_pooled_opus_indirect_tight_scored:value}}).

**H3 (v2, supported).** Coded API tables and handbook prose differ, and the coded tables lose more:
table_coded {{result:g1_v2_expect_H3_table_coded_preserved:value}}/{{result:g1_v2_expect_H3_table_coded_n:value}}
preserved (loss {{result:g1_v2_expect_H3_table_coded_loss_rate:value}}) against prose_labeled
{{result:g1_v2_expect_H3_prose_labeled_preserved:value}}/{{result:g1_v2_expect_H3_prose_labeled_n:value}}
(loss {{result:g1_v2_expect_H3_prose_labeled_loss_rate:value}}).

**H4 (v2, underpowered).** Reliability markers on flagged cells against numeric interval qualifiers:
{{result:g1_v2_expect_H4_flagged_cell_reliability_preserved:value}}/{{result:g1_v2_expect_H4_flagged_cell_reliability_n:value}}
(loss {{result:g1_v2_expect_H4_flagged_cell_reliability_loss_rate:value}}) against
{{result:g1_v2_expect_H4_interval_all_surfaces_preserved:value}}/{{result:g1_v2_expect_H4_interval_all_surfaces_n:value}}
(loss {{result:g1_v2_expect_H4_interval_all_surfaces_loss_rate:value}}). The intervals overlap.

**H5 (v2, underpowered).** Footnoted against inline qualifiers:
{{result:g1_v2_expect_H5_footnoted_preserved:value}}/{{result:g1_v2_expect_H5_footnoted_n:value}} (loss
{{result:g1_v2_expect_H5_footnoted_loss_rate:value}}) against
{{result:g1_v2_expect_H5_inline_preserved:value}}/{{result:g1_v2_expect_H5_inline_n:value}} (loss
{{result:g1_v2_expect_H5_inline_loss_rate:value}}); by footnote-distance tercile, loss
{{result:g1_v2_expect_H5_tercile_low_loss_rate:value}} ({{result:g1_v2_expect_H5_tercile_low_n:value}}),
{{result:g1_v2_expect_H5_tercile_mid_loss_rate:value}} ({{result:g1_v2_expect_H5_tercile_mid_n:value}}),
{{result:g1_v2_expect_H5_tercile_high_loss_rate:value}} ({{result:g1_v2_expect_H5_tercile_high_n:value}}). The
tercile cuts fall at {{result:g1_v2_expect_H5_distance_cut_low_mid:value}} and
{{result:g1_v2_expect_H5_distance_cut_mid_high:value}} characters: the distance range these surfaces span is
narrow.

**C1 (v2, underpowered; coded verdict "not supported").** The control arm's loss rate against the
pinned consumer's on the same holdout grid: `none` {{result:g1_v2_expect_C1_none_control_loss_rate:value}}
(n {{result:g1_v2_expect_C1_none_control_n:value}}) against {{result:g1_v2_expect_C1_none_consumer_loss_rate:value}}
(n {{result:g1_v2_expect_C1_none_consumer_n:value}}); `short`
{{result:g1_v2_expect_C1_short_control_loss_rate:value}} against
{{result:g1_v2_expect_C1_short_consumer_loss_rate:value}}; `tight`
{{result:g1_v2_expect_C1_tight_control_loss_rate:value}} against
{{result:g1_v2_expect_C1_tight_consumer_loss_rate:value}}; `direct`
{{result:g1_v2_expect_C1_direct_control_loss_rate:value}} against
{{result:g1_v2_expect_C1_direct_consumer_loss_rate:value}}. The direction reverses at `tight` and every
cell's intervals overlap; the coded verdict reads that reversal as "not supported" and the
pre-registered wording reads it as "underpowered". Both readings stand; no code was changed after
the freeze. The control arm is reported beside the pinned consumer and is never pooled with it.

### 3.1 Declared → observed join

The declared leg (`g1_declared`) and the observed leg run on the same captured surface file, so
the A11 triad's first and third legs meet per file. Loss is the share of scored families below L3
under the pinned consumer, pooled over compression.

| surface file | surface_type | declared leg | families | scored | lost | loss rate |
|---|---|---|---:|---:|---:|---:|
| `census-api-acs5-2023-b19013-counties-colorado` | table_coded | PASS | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_colorado_families:value}} | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_colorado_scored:value}} | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_colorado_lost:value}} | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_colorado_loss_rate:value}} |
| `census-api-acs5-2023-b19013-counties-idaho` | table_coded | PASS | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_idaho_families:value}} | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_idaho_scored:value}} | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_idaho_lost:value}} | {{result:g1_v2_join_census_api_acs5_2023_b19013_counties_idaho_loss_rate:value}} |
| `statcan-14-10-0287-01-lfs-2026-07-…` | table_labeled | PARTIAL | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2026_07_provinces_estimate_se_csv_families:value}} | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2026_07_provinces_estimate_se_csv_scored:value}} | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2026_07_provinces_estimate_se_csv_lost:value}} | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2026_07_provinces_estimate_se_csv_loss_rate:value}} |
| `statcan-14-10-0287-01-lfs-2025-12-…` | table_labeled | PARTIAL | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2025_12_provinces_estimate_se_csv_families:value}} | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2025_12_provinces_estimate_se_csv_scored:value}} | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2025_12_provinces_estimate_se_csv_lost:value}} | {{result:g1_v2_join_statcan_14_10_0287_01_lfs_2025_12_provinces_estimate_se_csv_loss_rate:value}} |
| `statcan-13-10-0096-01-cchs-2022-…` | flagged_cell | PARTIAL | {{result:g1_v2_join_statcan_13_10_0096_01_cchs_2022_provinces_percent_ci_csv_families:value}} | {{result:g1_v2_join_statcan_13_10_0096_01_cchs_2022_provinces_percent_ci_csv_scored:value}} | {{result:g1_v2_join_statcan_13_10_0096_01_cchs_2022_provinces_percent_ci_csv_lost:value}} | {{result:g1_v2_join_statcan_13_10_0096_01_cchs_2022_provinces_percent_ci_csv_loss_rate:value}} |
| `statcan-13-10-0113-01-cchs-2021-2022-…` | flagged_cell | PARTIAL | {{result:g1_v2_join_statcan_13_10_0113_01_cchs_2021_2022_quebec_health_regions_percent_ci_csv_families:value}} | {{result:g1_v2_join_statcan_13_10_0113_01_cchs_2021_2022_quebec_health_regions_percent_ci_csv_scored:value}} | {{result:g1_v2_join_statcan_13_10_0113_01_cchs_2021_2022_quebec_health_regions_percent_ci_csv_lost:value}} | {{result:g1_v2_join_statcan_13_10_0113_01_cchs_2021_2022_quebec_health_regions_percent_ci_csv_loss_rate:value}} |
| `nchs-data-brief-530-…` | flagged_cell | FAIL | {{result:g1_v2_join_nchs_data_brief_530_perinatal_mortality_2022_2023_families:value}} | {{result:g1_v2_join_nchs_data_brief_530_perinatal_mortality_2022_2023_scored:value}} | {{result:g1_v2_join_nchs_data_brief_530_perinatal_mortality_2022_2023_lost:value}} | {{result:g1_v2_join_nchs_data_brief_530_perinatal_mortality_2022_2023_loss_rate:value}} |
| `nchs-data-brief-500-…` | footnoted | PARTIAL | {{result:g1_v2_join_nchs_data_brief_500_dental_visits_adults_65_2022_families:value}} | {{result:g1_v2_join_nchs_data_brief_500_dental_visits_adults_65_2022_scored:value}} | {{result:g1_v2_join_nchs_data_brief_500_dental_visits_adults_65_2022_lost:value}} | {{result:g1_v2_join_nchs_data_brief_500_dental_visits_adults_65_2022_loss_rate:value}} |
| `nchs-data-brief-515-…` | footnoted | PARTIAL | {{result:g1_v2_join_nchs_data_brief_515_high_total_cholesterol_2021_2023_families:value}} | {{result:g1_v2_join_nchs_data_brief_515_high_total_cholesterol_2021_2023_scored:value}} | {{result:g1_v2_join_nchs_data_brief_515_high_total_cholesterol_2021_2023_lost:value}} | {{result:g1_v2_join_nchs_data_brief_515_high_total_cholesterol_2021_2023_loss_rate:value}} |
| `bls-employment-situation-2026-08-…` | footnoted | PARTIAL | {{result:g1_v2_join_bls_employment_situation_2026_08_news_release_families:value}} | {{result:g1_v2_join_bls_employment_situation_2026_08_news_release_scored:value}} | {{result:g1_v2_join_bls_employment_situation_2026_08_news_release_lost:value}} | {{result:g1_v2_join_bls_employment_situation_2026_08_news_release_loss_rate:value}} |
| `bls-employment-situation-2026-05-…` | footnoted | PARTIAL | {{result:g1_v2_join_bls_employment_situation_2026_05_news_release_archive_families:value}} | {{result:g1_v2_join_bls_employment_situation_2026_05_news_release_archive_scored:value}} | {{result:g1_v2_join_bls_employment_situation_2026_05_news_release_archive_lost:value}} | {{result:g1_v2_join_bls_employment_situation_2026_05_news_release_archive_loss_rate:value}} |

The declared leg's score for each file is registered beside these counts as
`g1_v2_join_<doc_id>_declared_score` (0 FAIL, 1 PARTIAL, 2 PASS). The two files the declared leg
scores PASS are the two files the observed leg loses most on. The three `no_declared` surfaces
(QuickFacts as page and as CSV, the 2020 DHC counts) carry no qualifier and so have a declared
leg only.

## 4. What the reviewer counts are, and are not

Every scored record below L3, and every `unparseable` record, went into a review queue and was
judged by an LLM reviewer (this repo's CC session) against a criterion recorded on each results
file: genuine when the raw response does not state the qualifier's class and value for that
estimate in any form, a parser miss when it states it in a form the parser could not read. The
reviewer's own counts: pooled queue {{result:g1_v2_pooled_opus_review_queue:value}} →
{{result:g1_v2_pooled_opus_genuine_losses:value}} genuine and {{result:g1_v2_pooled_opus_parser_misses:value}}
parser misses; holdout {{result:g1_v2_holdout_review_queue:value}} →
{{result:g1_v2_holdout_genuine_losses:value}} and {{result:g1_v2_holdout_parser_misses:value}}; dev
{{result:g1_v2_dev_review_queue:value}} → {{result:g1_v2_dev_genuine_losses:value}} and
{{result:g1_v2_dev_parser_misses:value}}; control arm {{result:g1_v2_control_review_queue:value}} →
{{result:g1_v2_control_genuine_losses:value}} and {{result:g1_v2_control_parser_misses:value}}.

**Those counts are never to be read alone** (DD-037). A second, independent rater has now rated
the blind sample, and the genuine-loss count on the pooled grid is reported as a range:

> **{{result:g1_cal_fable_range_rater_implied_genuine_losses:value}} (rater-implied) —
> {{result:g1_v2_pooled_opus_genuine_losses:value}} (reviewer) —
> {{result:g1_cal_fable_range_scorer_genuine_losses:value}} (scorer)**, out of
> {{result:g1_cal_fable_range_queue_population:value}} queued records.

The upper bound is the scorer's own position, that every record it put below L3 or could not
parse is a loss. The lower bound extrapolates the rater's judgments from the 60 sampled records
to the grid by stratum weights, which assumes the rater's genuine share inside a stratum is the
same in the grid as in the sample; the weights and the per-stratum rates are registered
individually so the arithmetic is inspectable. Only the pooled grid has a rater-implied bound —
the sample was drawn to represent it — so the holdout, dev and control counts above stand as the
reviewer's alone, to be read against the agreement measured here.

**The rater.** `claude-fable-5-1`, a different model from the reviewer's (`claude-opus-5`), which
is refused by name in `scripts/g1_calibration_rate.py`. The independence conditions, each
enforced rather than asserted: one record per call, so the rater could not see a distribution and
rate to it; the call made through the repo's model choke point, which runs `claude -p` from a
hermetic empty directory, so no CLAUDE.md, design decision or results file was in its context;
the prompt built from the blind sheet's own instruction paragraph and the D2 and D9 definitions
verbatim, carrying the passage, the response, the estimate, the family and its published forms,
the mode and the compression level — and no scorer level, reviewer verdict, failure class,
surface type or model id. It answered {{result:g1_cal_fable_n_rated:value}} of 60 records, with
{{result:g1_cal_fable_n_U:value}} answers of U and none unparseable. The raw exchanges are under
`assessment/evidence/g1/calibration/`.

**Agreement.** Rater against the scorer, on the ordinal levels with quadratic weights:
κ_w = {{result:g1_cal_fable_scorer_kappa_w:value}}
[{{result:g1_cal_fable_scorer_kappa_w_ci_lower:value}},
{{result:g1_cal_fable_scorer_kappa_w_ci_upper:value}}] over
{{result:g1_cal_fable_scorer_n:value}} records, raw agreement
{{result:g1_cal_fable_scorer_raw_agreement:value}}; including the scorer's `unparseable` outcome as a
sixth, unweighted category, κ = {{result:g1_cal_fable_scorer_kappa_six_category:value}}
[{{result:g1_cal_fable_scorer_kappa_six_ci_lower:value}},
{{result:g1_cal_fable_scorer_kappa_six_ci_upper:value}}] over
{{result:g1_cal_fable_scorer_six_n:value}}. Rater against the reviewer, on the reviewer's own binary
verdict over the review queue: κ = {{result:g1_cal_fable_reviewer_kappa:value}}
[{{result:g1_cal_fable_reviewer_kappa_ci_lower:value}},
{{result:g1_cal_fable_reviewer_kappa_ci_upper:value}}] over
{{result:g1_cal_fable_reviewer_n:value}} records, raw agreement
{{result:g1_cal_fable_reviewer_raw_agreement:value}}, positive specific agreement on the minority
call (`parser_miss`) {{result:g1_cal_fable_reviewer_positive_agreement_parser_miss:value}}. No
threshold is applied to any of these and no verbal band is named: a low κ widens the range and
triggers nothing.

Where the agreement sits is as informative as its size, and the per-stratum table
(`assessment/results/g1_calibration_stratum_agreement_2026-09-03.json`) locates it. The two
instruments agree completely on preserved-exact records and on which flagged records are parser
misses; they disagree about *which* sub-L3 level a loss is, which moves the level distribution
and not the loss count — which is why the range's lower bound
({{result:g1_cal_fable_range_rater_implied_genuine_losses:value}}) lands near the reviewer's count
({{result:g1_v2_pooled_opus_genuine_losses:value}}) while κ_w on the levels is middling.

**What this does and does not establish.** It measures agreement between two instruments. It does
not establish that either is right: both are language models, and two models can share an error a
human would not make. The rater is a different model family with no shared context, which reduces
that risk without removing it, and no human has labelled any of these records.
{{result:g1_cal_fable_disagreements_listed:value}} of the {{result:g1_cal_fable_n_rated:value}} rated
records — {{result:g1_cal_fable_disagreements_level_gap:value}} separated by two or more levels and
{{result:g1_cal_fable_disagreements_with_U:value}} where one side had no level to give — are listed
in `assessment/results/g1_calibration_disagreements_2026-09-03.md` for the operator to look at if
he chooses. Nothing in this memo waits on that.

## 5. Limits

1. **One consumer at scale.** All pooled numbers are `claude-opus-5`. The control arm is a single
   weaker consumer on the holdout grid, and C1 is underpowered; nothing here separates consumer
   strength from the compression factor.
2. **The handbook stratum is thin in the holdout.** The by-passage re-split moved the twelve
   shared v1 passages into dev, leaving few `prose_labeled` propositions in the holdout, so H3
   leans on the pooled grid rather than on sealed data.
3. **Suppressed cells are unmeasured.** A StatCan `F` or `x` cell has no value to bind, and the
   proposition unit requires one; the flagged stratum measures the `E` letters and the NCHS `†`
   only.
4. **The footnote-distance range is narrow.** H5's terciles are cut at
   {{result:g1_v2_expect_H5_distance_cut_low_mid:value}} and
   {{result:g1_v2_expect_H5_distance_cut_mid_high:value}} characters — the surfaces admitted put nearly
   all footnoted qualifiers at a similar distance, so the covariate is barely varied.
5. **The freeze was amended once.** Commit `281421c` (`g1-v2-frozen`) was amended by `6976464`
   before any holdout response had been read: the required re-score of the v0/v1 evidence exposed
   binding defects in the frozen scorer. §9.1 of the v2 RESULT states what changed; no rule in the
   amendment is motivated by a holdout response.
6. **Parser misses bias the loss rate upward.** {{result:g1_v2_pooled_opus_parser_misses:value}} of the
   {{result:g1_v2_pooled_opus_review_queue:value}} queued records are qualifiers the response did state and the
   parser did not read. Correcting them would move the measured loss down, so the direction of
   every finding above survives them; their magnitudes would change. The v3 rule list is a
   registered backlog (ResearchTask `73f0aa5d`), not queued work.
7. **The gate is a parse-coverage gate, not an accuracy gate.** It bounds how often the
   instrument cannot read a response; it says nothing about whether the levels it assigns are the
   levels a human would assign. That is what §4's calibration sample is for.

## 6. What changes in the instrument, and what does not

**Changes.** G1 becomes two legs scored as a vector with no composite (skeleton v0.2.7, protocol
§9): **G1-D**, the declared leg, unchanged — uncertainty present as structured fields beside the
estimates; **G1-O**, the observed leg — the family preservation rate at indirect `none` with the
`unparseable` share and the `short` / `tight` rates reported beside it, per surface, every record
stamped with consumer, prompt epoch, parser and scorer version. The skeleton's G1 note carries the
dissociation statement and the surface-type vocabulary. Compression is a reported condition, not a
scored one.

**Does not change.** The construct, the level scale (DD-033 D2), the tolerance rule (D7: the
source's own printed rounding; a coarser rounding is L0), the retrieval-removed-by-construction
design, the `unparseable` outcome and its refusal to be coerced into a score, the eval firewall
that keeps `SOURCE_EVAL` and `G1` out of every composite, and the absence of any product-level
PASS/PARTIAL/FAIL threshold. The instrument itself is frozen at (`g1-parse-v2`, `g1-score-v2`,
`g1-v2-2026-09-03`, `claude-opus-5`) for the January pilot (DD-036); the January calibration run
is what sets a boundary, if one is set.
