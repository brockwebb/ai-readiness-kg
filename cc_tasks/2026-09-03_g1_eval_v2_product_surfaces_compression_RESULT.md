# RESULT: G1 EVAL v2 — product surfaces × compression, families, binding, one control arm, seal recompute, DD-035

**Readiness gate (pre-registered, step 6): PASSED — 7 of 128 sealed-holdout family records unparseable under the pinned consumer, share 0.055 ≤ 0.10** (`g1_v2_holdout_unparseable`, `g1_v2_holdout_all_families`; computed on `assessment/evidence/g1/v2/holdout/` plus the eight byte-identical v1 holdout slots the schedule reuses, nothing from dev).

**Task:** `cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression.md` (no addenda: globbed `…_ADDENDUM*.md`, none). **Sequencing honoured:** dev grid (step 4, runs `g1_eval_v2_dev_2026-09-03` and `_b`) before parser/scorer v2; holdout (`g1_eval_v2_holdout_2026-09-03`) and control arm (`g1_eval_v2_control_2026-09-03`) only after the freeze commit `281421c` (`g1-v2-frozen`) — with one amendment commit `6976464` before any holdout response was read (§9.1). Biblio-cron files not committed. **Dates:** 2026-09-03 UTC. **Spend:** four declared runs, each at the task's 2,000,000 ceiling, `claude -p` under Max OAuth only; total settled **6,587,826 tokens** ≤ the task's 8,000,000 (§8).

## 1. Seal recompute for v1 (zero spend)

`scripts/rescore_g1.py --fresh-only` (new flag; the results file carries `fresh_only: true`) over `assessment/evidence/g1/holdout/` only — the 35 responses elicited after the v1 freeze, no parent-directory slot. DataFile `g1_v1_holdout_fresh_reviewed` (`83eea46e`), 125 Results `g1_v1_holdout_fresh_*`, the v1 reviewer judgments carried per record.

| | v1 gate as reported (64 records incl. 12 shared-passage dev responses) | corrected: fresh responses only |
|---|---|---|
| records | 64 | 37 |
| unparseable | 2 (0.031) | 1 (**0.027 — gate still passes**) |
| scored / L3+ | 62 / 57 = 0.919 [0.825, 0.965] | 36 / 33 = **0.917 [0.782, 0.971]** |
| genuine losses (reviewer) | 5 | 2 |

The v1 RESULT and its Results are unchanged.

## 2. Product surfaces (zero model spend)

`scripts/g1sfc_list_2026-09-03.yaml` → `harvest_triage.py` → `manifest_triage.py`, batch-028, epoch `g1sfc-2026-09-03`, `docs/research/2026-09-03_g1sfc_manifest_summary.json`. Corpus 216 → **233**; `kg.manifest verify` clean. Every surface captured as served (raw JSON / CSV / PDF / browser-rendered HTML-to-text) with `surface_type`, `surface_format` and the exact `request_url` in the manifest entry's `acquisition.surface` block.

| surface_type | admitted (dev / holdout) | verdict notes |
|---|---|---|
| table_coded | `census-api-acs5-2023-b19013-counties-colorado` / `…-idaho` (Census Data API JSON, `B19013_001E,B19013_001M`, all counties) | The API now requires a key: `api.census.gov` redirects unkeyed requests to "Missing Key". The harvester gained `secret_env` — `CENSUS_API_KEY` (held in `~/.wintermute/.env`) is substituted at request time and every recorded string (register, event, capture header) carries `{CENSUS_API_KEY}`; checked: the key value appears in no event, file or register. `ANTHROPIC_API_KEY` is refused by name. The code→meaning map comes from the API's own `/variables/B19013_001E.json` and `…M.json` endpoints into fixture metadata; the direct prompt names the estimate by its code. |
| table_labeled | `statcan-14-10-0287-01-lfs-2026-07-provinces-estimate-se-csv` / `…-2025-12-…` (LFS, Canada + provinces, Estimate and Standard error of estimate rows, seasonally adjusted) + cube-metadata companion | data.census.gov's CSV export: HTTP 403 "Request Rejected" (WAF) → **needs_source** with the exact URL, not hand-built. The StatCan "download selected data" endpoint's date window is off by one period (startDate=endDate=2026-01-01 serves December 2025); the recorded request is the form that serves the month. |
| footnoted | `nchs-data-brief-500-dental-visits-adults-65-2022` / `nchs-data-brief-515-high-total-cholesterol-2021-2023` (body text ↔ appendix "Data table for Figure N"); `bls-employment-situation-2026-08-news-release` (July 2026 data) / `…-2026-05-…-archive` (headline ↔ Technical Note "plus or minus 122,000") | The task's named targets were **cut with reason**: the Census newsroom 2025 ACS release (`census-newsroom-2025-acs-1-year-estimates-release`) carries no MOE or technical note — only "not statistically significant"; eight ONS bulletins probed all point to a separate "sampling variability" dataset (A11) with no CI value on the bulletin. BLS refuses scripted requests (HTTP 403) but served the browser fetcher. |
| flagged_cell | `statcan-13-10-0096-01-cchs-2022-provinces-percent-ci-csv` (STATUS `E` on 9 cells) / `statcan-13-10-0113-01-cchs-2021-2022-quebec-health-regions-percent-ci-csv` (30 `E`, 6 `F`) + cube-metadata companions; `nchs-data-brief-530-perinatal-mortality-2022-2023` (state table, `†` replaces the change column, legend printed beneath) | StatCan's table pages are JS-rendered (no cells, no legend in the static HTML); the CSV download package serves the legend in the cube-metadata file, so each flagged passage joins the data rows with the legend block as its own verbatim part and records `legend_on_surface: true` with `legend_file`. Suppressed cells (`F`, `x`) have no value to anchor and are not propositions (§9.7). |
| no_declared | `census-quickfacts-denver-county-colorado` (browser-rendered) and `…-csv`; `census-api-dec2020-dhc-p1-counties-colorado` (2020 counts with no uncertainty field) | QuickFacts is Cloudflare-blocked for scripted requests but served the browser fetcher; BLS `laucntycur14.txt` → HTTP 404, **needs_source**. Declared leg only. |

**Fixtures** (`assessment/tests/fixtures/g1/v2/propositions.yaml`, `propositions_holdout.yaml`, `fixture_version: v2-2026-09-03`, generated by `scripts/gen_g1_v2_fixtures.py` by verbatim anchor slicing; every passage is the newline-join of `parts`, each a contiguous block of one captured file; `tests/test_g1_fixtures.py` re-checks every part against its corpus file and asserts zero passage overlap between splits and against the v1 files): dev **26 propositions on 7 passages** (table_coded 6, table_labeled 6, flagged_cell 8, footnoted 6); holdout **14 on 6** (3 / 3 / 4 / 4). All floors met (≥ 6 dev / ≥ 3 holdout). Table passages are the header row plus ≥ 3 data rows; footnoted passages carry `footnote_distance_chars` (11,623–13,350 characters in the captured text).

**Declared leg** (`scripts/g1_declared_surfaces.py`, zero spend) on all 17 surface files → `assessment/tests/fixtures/g1/v2/declared_leg.json`, joined into every observed record as `declared_leg_score` (§6.5).

## 3. Scorer v2 design and schedule (zero spend)

D9 families, D10 binding, D11 covariates, D12 compression, D13 control arm and D14 are implemented in `harness/records.py` (`FAMILIES`, `EvalResult.scorer_version` / `family` / `surface_type` / `compression_level`), `harness/probes/g1_preservation.py` (`SCORER_VERSION = "g1-score-v2"`, `score_family`, `bind_candidates`, `covariates`, compression-aware prompts and evidence reuse), `harness/g1_expectations.py`, `harness.toml [g1.families]` / `[g1.binding]`, `g1_prompts.toml` (epoch `g1-v2-2026-09-03`; `none` is the v0/v1 indirect prompt verbatim), `g1_consumer.toml [control]`. Design detail and rationale: DD-035.

**Schedule** (`scripts/gen_g1_schedule.py --version v2` → `assessment/config/g1_v2_schedule.toml`, pre-registered before any call; split by passage, the twelve v1 shared passages assigned to dev): dev 212 steps (111 new calls, 101 reusable v1 slots), holdout 59 (51 new, 8 reusable), control 59 (all new) — **221 new calls = 7,514,000 tokens at the 34,000 floor**, under the 8.0M cap; without the byte-identical-prompt reuse the grid would be 330 calls = 11,220,000 and the task would have stopped here.

## 4. Development grid (model spend)

| run | ceiling | calls | reused | tokens settled | stop |
|---|---|---:|---:|---:|---|
| `g1_eval_v2_dev_2026-09-03` | 2,000,000 | 65 | 101 | 1,987,031 | refused at call 66 (`over_ceiling`) |
| `g1_eval_v2_dev_2026-09-03_b` | 2,000,000 | 46 | 166 | 1,422,460 | schedule complete (111/111 new) |

Evidence: `assessment/evidence/g1/v2/dev/` (111 files). No holdout, no control arm in this step.

## 5. Parser v2 + scorer v2, freeze, and the v1 grid under v2

**Freeze:** commit `281421c` (`g1-v2-frozen`), amended by `6976464` (§9.1). Every v2 rule is motivated by a named response and reproduced verbatim in `tests/fixtures/g1/restatements.yaml`: `v2_cases` (the three v1 reviewer-labelled records, D10), `v2_cases_parser_misses` (two of the three v1 parser misses; the third — pm-source / bounds tolerance — is exercised by the ONS case), `v2_cases_dev` (18 cases from v2 development responses: lead-less ranges, quoted status letters, "treated with caution", "X percent of the estimate", "the true total is likely somewhere between", "19 out of every 20", sentence-scoped levels, sibling-named clauses, subject values, anaphora, DP parameters stated in a parenthesis, the estimate-absent precedence). Suites: `assessment/` **471 passed, 1 skipped**; root `tests/` **642 passed**.

**The v1 grid re-scored under (g1-parse-v2, g1-score-v2)** — the D9 effect as a registered pair (DataFiles `g1_v2_rescore_v1_{dev,holdout,pooled}_reviewed`; 152 + 152 + 155 Results `g1_v2_rescore_v1_*`):

| v1 evidence | families (forms) | unparseable | L3+ | rate | genuine losses (reviewer) | v1 reading (qualifiers) |
|---|---:|---:|---:|---:|---:|---|
| dev directory (84 responses) | 143 (169) | 0 | 142 | 0.993 [0.962, 0.999] | 1 | 132 records, 1 unparseable, 130 L3+ |
| fresh holdout (35) | 37 (47) | 0 | 35 | 0.946 [0.823, 0.985] | 2 | 37, 1 unparseable, 33 L3+ (§1) |
| pooled (119) | **180 (216)** | **0** | **177** | **0.983 [0.953, 0.994]** | **3** | 196 records, 3 unparseable, 187 L3+; 6 genuine losses |

Genuine losses 6 → **3** (the task expected ~3): the Loudoun row's CV and MOE (never restated) and the NCHS Asian-children SE (interval given only for another row). The other three v1 losses are not losses under families: the ONS interval quoted as its printed bounds (CI form L4; the SE form is a cross-form derivation within the bounds' rounding), the NHANES Black-children SE (the interval form carried), and the ONS "give or take roughly £1.0 billion" (D7 corruption of a form whose sibling bounds are exact). The three v1 failure-class mislabels are gone (no `binding_error` in the v1 grid).

## 6. Results (v2, family denominators; forms reported beside)

All numbers below are registered Results with prefix `g1_v2_<split>_…`, `computed_from` the split's reviewed DataFile (`g1_v2_dev_reviewed` `2e1d0864`, `g1_v2_holdout_reviewed` `5bee8802`, `g1_v2_pooled_opus_reviewed`, `g1_v2_control_reviewed`) and `generated_by` Script `rescore_g1_v2` (`f8898cfc`): dev 496, holdout 481, pooled 515, control 482.

### 6.1 Sealed holdout, pinned consumer `claude-opus-5` (128 families / 140 forms, 86 evidence files)

| cell | families | scored | unparseable | L3+ | rate | Wilson 95 % | levels |
|---|---:|---:|---:|---:|---:|---|---|
| **all** | 128 | 121 | 7 | 71 | **0.587** | [0.498, 0.671] | L0 11 · L1 19 · L2 20 · L3 12 · L4 59 |
| direct | 32 | 32 | 0 | 29 | 0.906 | [0.758, 0.968] | L0 3 · L3 3 · L4 26 |
| indirect · none | 32 | 29 | 3 | 17 | 0.586 | [0.407, 0.745] | L0 5 · L1 7 · L3 4 · L4 13 |
| indirect · short | 32 | 29 | 3 | 15 | 0.517 | [0.344, 0.686] | L0 1 · L1 5 · L2 8 · L3 4 · L4 11 |
| indirect · tight | 32 | 31 | 1 | 10 | 0.323 | [0.186, 0.499] | L0 2 · L1 7 · L2 12 · L3 1 · L4 9 |

| surface × compression | families | scored | unp. | L3+ | rate | Wilson 95 % |
|---|---:|---:|---:|---:|---:|---|
| table_coded · none / short / tight / direct | 3 / 3 / 3 / 3 | 3 / 0 / 3 / 3 | 0 / 3 / 0 / 0 | 0 / 0 / 0 / 3 | 0.0 / — / 0.0 / 1.0 | [0, 0.561] / — / [0, 0.561] / [0.439, 1] |
| table_labeled · none / short / tight / direct | 6 each | 6 each | 0 | 3 / 3 / 3 / 6 | 0.5 / 0.5 / 0.5 / 1.0 | [0.188, 0.812] ×3 / [0.610, 1] |
| footnoted · none / short / tight / direct | 8 each | 5 / 8 / 8 / 8 | 3 / 0 / 0 / 0 | 4 / 4 / 4 / 8 | 0.8 / 0.5 / 0.5 / 1.0 | [0.376, 0.964] / [0.215, 0.785] ×2 / [0.676, 1] |
| flagged_cell · none / short / tight / direct | 10 each | 10 each | 0 | 7 / 6 / 3 / 7 | 0.7 / 0.6 / 0.3 / 0.7 | [0.397, 0.892] / [0.313, 0.832] / [0.108, 0.603] / [0.397, 0.892] |
| prose_labeled · none / short / tight / direct | 5 each | 5 / 5 / 4 / 5 | 0 / 0 / 1 / 0 | 3 / 2 / 0 / 5 | 0.6 / 0.4 / 0.0 / 1.0 | [0.231, 0.882] / [0.118, 0.769] / [0, 0.490] / [0.566, 1] |

By family (holdout): interval indirect 5/39 L3+ (0.128 [0.056, 0.267]; L2 19), interval direct 12/15; reliability indirect 6/8, direct 3/3; relative indirect 0/3; dp indirect 2/3; vintage indirect 29/36 (0.806), direct 12/12. Failure classes: omission 15, form_shift 20, quantity_hallucination 10, decontextualization 4, binding_error 1. Estimate status: exact 74, rounded 40, wrong 10, absent 4.

**The seven unparseable holdout responses, by form** (gate passed; listed anyway): `acs-id-block1 · short` ×3 — "carry wider margins of error" with no value for any county (genuine omission); `nchs515-fig2 · none` ×3 — the total's interval is stated as "could reasonably fall anywhere between about 12.1% and 15.7%" (a **parser miss**: the frozen CI cues do not include "could reasonably fall … between"), the men's and women's intervals are not stated (genuine); `lfs-ci-example · tight` ×1 — "the margin of error keeps that range above zero", no value (genuine).

**Genuine losses (reviewer CC, criterion recorded on each file, judgment and note per record):** holdout queue 57 → **45 genuine, 12 parser misses**. The parser misses, all v3 items (rules motivated by holdout responses belong to v3): dash-written ranges "15.8% – 40.9%", "7.1–10.8", "26.7% – 52.7%" and "(95% CI 26.7–52.7%)" (five records); "the plausible range runs from 16% all the way to 41%" and 'flags it "use with caution"' not binding to the youth row (three); "±0.3 percentage points at one standard error" anchored on a preceding 18,000 (one); "2021–22" as a two-year period (two); "flagging results … for expert review" (one); "could reasonably fall … between" (one, above).

### 6.2 Development grid (522 families / 604 forms, 230 evidence files incl. reused v1 slots)

all 347/495 = 0.701 [0.659, 0.740], 27 unparseable; direct 138/138; indirect none 112/124 = **0.903**, short 65/113 = **0.575**, tight 32/120 = **0.267**. By surface (indirect none / short / tight; direct): table_coded 1.0 / 0.0 / 0.0; 1.0 — table_labeled 0.667 / 0.583 / 0.5; 1.0 — footnoted 0.875 / 0.5 / 0.417; 1.0 — flagged_cell 0.667 / 0.625 / 0.444; 1.0 — prose_labeled 0.988 / 0.627 / 0.181; 1.0. Review queue 175 → **133 genuine, 42 parser misses** (the misses: stated-but-unbound suppression rules on threshold passages — "withholds any estimate below its minimum publishable size — 1,500", "drop a table from publication", "hid statistics based on too few cases — under 20"; CVs stated without the word — "about 5.0% for the unemployed count", "each accurate to within about 1%"; the † legend in other words — "Drop not meaningful", "were not statistically significant"; "within about four people"; "could be roughly 177,000 higher or lower").

### 6.3 Pooled, pinned consumer (dev + holdout; 650 families / 744 forms, 281 files)

all 418/616 = **0.679** [0.641, 0.714], 34 unparseable; direct 167/170 = 0.982; indirect none 129/153 = **0.843**, short 80/142 = **0.563**, tight 42/151 = **0.278**. Families (indirect): interval 51/166 = 0.307, relative 13/33 = 0.394, reliability 49/87 = 0.563, dp 12/13, vintage 126/147 = 0.857. Review queue 232 → **178 genuine, 54 parser misses**. Levels: L0 31 · L1 110 · L2 57 · L3 92 · L4 326.

### 6.4 Control arm `claude-haiku-4-5-20251001` (holdout grid; 128 families / 140 forms; reported beside, never pooled)

all 60/112 = **0.536** [0.444, 0.625], **16 unparseable** (0.125 — the control arm is not gated, but the share is reported); direct 26/31 = 0.839; indirect none 14/31 = 0.452, short 10/23 = 0.435, tight 10/27 = 0.370. Review queue 68 → **55 genuine, 13 parser misses**. Beside Opus on the same grid (`assessment/results/g1_v2_c1_control_vs_opus.json`): none 0.452 vs 0.586, short 0.435 vs 0.517, tight 0.370 vs 0.323, direct 0.839 vs 0.906.

### 6.5 Declared → observed join (A11's first two legs on one surface file; pooled Opus)

| surface file | surface_type | declared leg | families | lost (< L3) / scored | loss rate |
|---|---|---|---:|---:|---:|
| `census-api-acs5-2023-b19013-counties-colorado` | table_coded | **PASS** (paired `_E`/`_M`) | 24 | 12 / 24 | 0.500 |
| `census-api-acs5-2023-b19013-counties-idaho` | table_coded | **PASS** | 12 | 6 / 9 | 0.667 |
| `statcan-14-10-0287-01-lfs-2026-07-…` | table_labeled | PARTIAL (uncertainty in body text: "standard error" is a row value, not a column) | 48 | 15 / 48 | 0.312 |
| `statcan-14-10-0287-01-lfs-2025-12-…` | table_labeled | PARTIAL | 24 | 9 / 24 | 0.375 |
| `statcan-13-10-0096-01-cchs-2022-…` | flagged_cell | PARTIAL | 40 | 10 / 38 | 0.263 |
| `statcan-13-10-0113-01-cchs-2021-2022-…` | flagged_cell | PARTIAL | 40 | 17 / 40 | 0.425 |
| `nchs-data-brief-530-…` | flagged_cell | FAIL (PDF: no field header, no vocabulary hit) | 32 | 12 / 32 | 0.375 |
| `nchs-data-brief-500-…` | footnoted | PARTIAL (vocabulary in body text) | 40 | 10 / 36 | 0.278 |
| `nchs-data-brief-515-…` | footnoted | PARTIAL | 24 | 6 / 21 | 0.286 |
| `bls-employment-situation-2026-08-…` | footnoted | PARTIAL | 8 | 4 / 8 | 0.500 |
| `bls-employment-situation-2026-05-…` | footnoted | PARTIAL | 8 | 3 / 8 | 0.375 |
| QuickFacts (page, CSV); `census-api-dec2020-dhc-p1-…` | no_declared | PARTIAL, PARTIAL, **FAIL** | — | declared leg only | — |
| three `…-cube-metadata-csv` legend files | legend | PARTIAL (notes column) | — | companions | — |

The two surfaces the declared leg scores highest (the coded API tables) are the two the observed leg loses most on (H3, §6.6).

### 6.6 Pre-registered statements (D14)

| | statement | pooled Opus counts | verdict (pooled) | holdout-only |
|---|---|---|---|---|
| E4 | family loss rises monotonically none → short → tight (Lee 2026) | loss 0.157 → 0.437 → 0.722 (129/153, 80/142, 42/151); ordering holds; none vs tight intervals disjoint | **supported** | underpowered (0.414 → 0.483 → 0.677; ordering holds; intervals overlap) |
| E5 | under `tight`, omission (L1) is the modal failure (Peters & Chin-Yee 2025; Ansari 2026) | 109 failures at tight: L0 11, **L1 60**, L2 38 | **supported** | not supported (21: L0 2, L1 7, L2 12 — form shift is modal on the product surfaces) |
| E6 | L2 rate at `tight` > at `none` (van der Bles 2019) | none 0/153, tight 38/151 = 0.252 | **supported** — the form-shift mechanism v1 never saw (0 L2 in 196) appears under compression | supported (0/29 vs 12/31) |
| H3 | table_coded and prose_labeled differ (two-sided) | table_coded 15/33 = 0.455 vs prose_labeled 234/328 = 0.713; **coded lost more** | **supported** | underpowered (3/9 vs 10/19, same direction) |
| H4 | flagged_cell reliability markers lost more than interval qualifiers | reliability 16/32 = 0.50 vs interval 121/239 = 0.506 | **underpowered** | underpowered (6/8 vs 17/54 — direction *against*) |
| H5 | footnoted lost more than inline; loss rises with footnote distance | footnoted 50/73 = 0.685 vs inline 368/543 = 0.678; terciles (cuts 13,118 / 13,232 chars) 0.714 / 0.727 / 0.633 | **underpowered** (no separation; the distance range on these surfaces is narrow) | underpowered |
| C1 | control loss ≥ Opus loss at every compression level | none 0.548 vs 0.414, short 0.565 vs 0.483, direct 0.161 vs 0.094 — direction holds; **tight 0.630 vs 0.677 — direction against**, every cell's intervals overlap | **as coded: not supported**; under the pre-registered wording ("not supported only where the direction fails with non-overlapping intervals") **underpowered** — both readings reported, no code changed after the freeze (§9.5) | — |

Retained, not re-tested: vintage is carried in the reused v1 grid; on the product surfaces it is not (vintage indirect 126/147 pooled: the BLS releases' "July"/"May" lose their year, the DAS file date is replaced by the comparison year).

**Covariates (D11, never scored).** `compression_ratio` (passage tokens / response tokens), pooled Opus: none median 0.76 [q1 0.57, q3 1.01]; short 2.71 [1.80, 4.60]; tight 7.31 [4.82, 12.18] — the factor did what it was meant to. `relative_deviation` among L0 records (n = 13 with a numeric restatement): median +0.016, widened 10 / narrowed 3 — the corruptions are roundings, not fabrications (the one outlier, 151×, is the v1 Fairfax "±1,500 or so"-type summary band bound to a county). `summary_precision_consistent`: 172 of 305 records where both numbers are present — the D7 coarsening case is common and is a covariate for the calibration run, not a score.

## 7. DD-035 and mechanical updates

DD-035 appended (`docs/design_decisions.md`; DesignNote `043d77c8`): the product-test decision, families, binding by label competition / preceding value / anaphora, covariates-not-scores, split-by-passage, the single control arm, the corrected v1 gate, the byte-identical-prompt reuse rule, and the acquisition record. Skeleton v0.2.6 (G1 Evidence cell + the `surface_type` vocabulary in the G1 note); protocol §9 one paragraph. Script `rescore_g1_v2` (`f8898cfc`).

## 8. Verification and spend

| check | value |
|---|---|
| `assessment/` suite | 471 passed, 1 skipped (was 409 at task start) |
| root `tests/` suite | 642 passed |
| `kg.manifest verify` | clean, 233 included |
| `kg.spend status` | `g1_eval_v2_dev_2026-09-03` settled 1,987,031 (1 refusal, the planned stop); `…_b` 1,422,460; `g1_eval_v2_holdout_2026-09-03` 1,581,837; `g1_eval_v2_control_2026-09-03` 1,596,498; **task total 6,587,826** of 8,000,000; every run under its 2,000,000 ceiling; day total 10.4M of the 55M band |
| `seldon verify` | 1 issue: `docs/corpus/acquisition_candidates.md` modified — the biblio cron (Seldon task `989daaad`), not this task; left for that pipeline |

### 8.1 Close
`seldon verify` and `seldon cc complete` are recorded at the end of this file's commit; the four cron-owned files (`docs/corpus/acquisition_candidates.md`, `docs/corpus/operator_pickup.md`, `events/batch-024.jsonl`, `state/t2_priority.json`) are left uncommitted as instructed and `seldon verify` reports them.

## 9. Discrepancies (premise vs live state) — reported, not reconciled

1. **The freeze was amended once, before any holdout response was read.** Step 5a's own deliverable — re-scoring the v0/v1 evidence under v2 — exposed binding defects in the frozen scorer (a rounding-to-zero bug in `is_rounding_of` that made any small number a "rounding" of a large estimate; qualifier values, table references, range members and thresholds counted as the subject a qualifier follows; the label contest won by uncertainty vocabulary in a sibling's label). They were fixed and committed as `6976464` with the tag "amendment (before any holdout response was read)". The holdout elicitation had already started (its evidence is unaffected: evidence is never re-elicited) and its authoritative scoring happened after the amendment. No rule in the amendment is motivated by a holdout response; the twelve holdout parser misses in §6.1 are left for v3 as the task requires.
2. **Two of the task's named surfaces do not carry the uncertainty they were assumed to carry** (§2): no Census newsroom ACS release states an MOE, and no ONS bulletin states a CI on its own surface. The footnoted stratum is NCHS Data Briefs (body ↔ appendix table) and BLS Employment Situation releases (headline ↔ Technical Note), the latter reachable only through the browser fetcher.
3. **data.census.gov and BLS LAUS are routed `needs_source`** with their exact URLs (WAF 403; 404).
4. **The Census Data API requires a key**; the standing path gained request-time secret substitution with redaction (`harvest_kernel.secret_values`), and the key value is verified absent from every record.
5. **C1's coded verdict and its pre-registered wording disagree** on how to treat a reversal inside overlapping intervals (§6.6); both readings are reported and the code is untouched.
6. **The grid is affordable only because byte-identical v1 slots are reused** (DD-035 §4): 221 new calls against 330 without reuse. Records from reused slots carry the evidence file's own epoch (`g1-v0-2026-09-02`) and `prompt_text_identical: true`; the rollup lists both epochs.
7. **Suppressed cells have no proposition**: StatCan `F` / `x` cells carry no value to bind, and the proposition unit requires one; the flagged stratum measures `E` letters and the NCHS `†`. A v3 design item.
8. **The prose_labeled holdout stratum is three passages / five propositions** after the by-passage re-split (twelve shared v1 passages went to dev); the H3 comparison therefore leans on the pooled Opus grid.
9. **The Seldon registration of the pooled split's Results ran past one tool timeout** and was resumed with a `--skip` offset; no Result was registered twice (counts in §6).
10. **Working-tree state:** the four biblio-cron files are modified and left uncommitted (Seldon task `989daaad`); `state/spend_ledger.jsonl` is committed with the runs that wrote it.

## Not done, by the task's boundary

The surfaced (retrieval) leg; model-judge scoring; product-level thresholds; any rounding tolerance (D7 stays strict; the coarsening case is a covariate); a second consumer factor; edits to any RESULT, the memo, or a registered Result; parser rules motivated by holdout responses (the twelve in §6.1 and thirteen in the control arm are the v3 list).
