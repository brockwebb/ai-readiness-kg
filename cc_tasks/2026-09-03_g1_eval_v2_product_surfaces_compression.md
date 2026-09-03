# CC Task: G1 EVAL v2 — product-surface fixtures × compression budget, one consumer control arm, seal recompute, qualifier equivalence classes, failure-class attribution, parser v2, D7/compression covariates, DD-035

**Date:** 2026-09-03
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-03_g1_eval_v2_product_surfaces_compression_ADDENDUM*.md` files.**
**SEQUENCING:** after `cc_tasks/2026-09-03_g1_eval_v1_parser_fullgrid_errata_RESULT.md` (exists). Steps are order-dependent (holdout and control arm are elicited only after the parser/scorer v2 freeze). Do not commit the biblio cron's files (Seldon task `989daaad`); leave them.
**Spend:** steps 1–3 and 6–8 zero model spend. Steps 4, 5b, 5c are model-calling, each a declared DD-022 run at **ceiling 2,000,000 tokens**, split into further declared runs when a schedule exceeds it at the `g1_eval` floor (34,000/call); **total across all runs in this task ≤ 8,000,000**. If the generated schedule exceeds 8.0M at the floor, stop after step 3 and report the schedule size — do not trim it silently. `claude -p` under Max OAuth only.

## Context

v1 (`…_v1_parser_fullgrid_errata_RESULT.md`) measured the v0 design on its full grid: handbook-passage fixtures, source in context, no compression. Holdout preservation 0.919 [0.825, 0.965]; pooled 0.969; six genuine losses in 193; **zero L2 in 196 records** (E3 not supported). The observed leg as built sits near ceiling for a frontier consumer, and every genuine loss is a compression-class event (an interval given in place of an SE; a summary rounding coarser than the source). Two structural defects in the v0/v1 design were also found: (i) qualifiers that are deterministic transforms of each other (SE, MOE, CI at one level) are scored as separate facts, so an interval carried correctly still records an SE "omission"; (ii) SUPPRESSION and RELIABILITY_FLAG fixtures are producer *rule prose*, not flagged or suppressed *cells*, so those classes measured a different, easier task.

**Decision (Desktop, 2026-09-03): G1's observed leg is a product test.** The skeleton defines G1 as "MOEs/CVs as structured fields, not footnotes" — a property of the data product's presentation. v2 fixtures therefore come from product surfaces (tables, API responses, footnoted releases, flagged cells) with a compression budget as a pre-registered factor; the v1 handbook stratum becomes the `prose_labeled` control stratum. One weaker consumer runs as a single control arm, not a factor. The declared leg (`g1_declared`) is run on every surface file so the declared → observed join exists for the first time.

This task does not loosen anything under a freeze. v1's numbers stand; v2 is a new instrument version (`parser_version` `g1-parse-v2`, new `scorer_version` `g1-score-v2`), and all v0/v1 evidence is re-scored under it as a registered pair.

## Step 1 — Seal recompute for v1 (zero spend)

The v1 holdout gate (2/64) includes records scored on 12 shared-passage responses that were dev evidence the parser author had read. Recompute every v1 holdout Result restricted to the **35 fresh holdout responses** (`assessment/evidence/g1/holdout/` only, no parent-directory fallback), register with prefix `g1_v1_holdout_fresh_`, and state in the RESULT whether the readiness gate still passes on fresh responses only. Add `fresh_only` as a boolean on the v1 holdout results file's re-score, not by editing the existing DataFile. Link the new Results to the same evidence. This is the corrected v1 gate; it does not change the v1 RESULT.

## Step 2 — Acquire product surfaces (zero model spend)

Standing acquisition path (`scripts/g1sfc_list_2026-09-03.yaml` → `harvest_triage.py` → `manifest_triage.py`, epoch `g1sfc-2026-09-03`, rationale "G1 v2 product-surface fixture"). Surfaces are captured **as served** — the raw CSV, JSON, HTML-to-text, or PDF-to-text — because the surface's form is the thing under test; record `surface_type` and the exact request/URL in the manifest entry. Admit-with-reason or cut-with-reason for each. **Dev and holdout must be different files** (different geography, year, or brief) — no passage may appear in both splits; `tests/test_g1_fixtures.py` asserts zero passage overlap by normalised text.

| surface_type | definition | dev target | holdout target |
|---|---|---|---|
| `table_coded` | estimate and uncertainty as coded fields with no label on the surface | Census API JSON, ACS 5-year 2023, `B19013_001E,B19013_001M` (median household income) for all counties in one state | same query, a different state |
| `table_labeled` | estimate and uncertainty as columns whose headers name them | data.census.gov CSV export of the same table (label row present) for one state; and/or a StatCan LFS monthly table CSV (14-10-0287-01) carrying its quality-indicator column | different state / different reference month |
| `footnoted` | the estimate appears in body text or a table; the MOE/CI appears in a footnote or technical note elsewhere on the surface | a Census ACS news release (newsroom) with its technical note on margins of error; an ONS statistical bulletin section whose CIs sit in a "sampling variability" annex | a different release / bulletin |
| `flagged_cell` | cells carrying a reliability or suppression marker (†, *, letters A–F, "F", "x", "..") with the legend on the surface | an NCHS Data Brief table with "does not meet NCHS standards of reliability" flags; a StatCan table with letter quality indicators and/or suppressed cells | a different Data Brief / table |
| `no_declared` | a surface publishing the estimate with no uncertainty at all | Census QuickFacts for one county | — (declared leg only; no observed-leg fixture can exist by construction) |
| `prose_labeled` | v1 handbook passages (control stratum) | existing v1 dev fixtures | existing v1 holdout fixtures |

Floors: ≥ 6 dev / ≥ 3 holdout propositions per surface type (`table_coded`, `table_labeled`, `footnoted`, `flagged_cell`). Passages: a table passage is a contiguous block of rows (≥ 3 estimates, so binding errors are possible); a footnoted passage includes both the body span and the footnote span with their separation recorded (`footnote_distance_chars`). Every passage and span verbatim from the captured surface under the grounding normalisation. Fixtures in `assessment/tests/fixtures/g1/v2/propositions.yaml` and `propositions_holdout.yaml`, `fixture_version: v2-2026-09-03`. Each proposition records `surface_type`, `source_doc_id`, `surface_file`, and for `table_coded` the code→meaning mapping **from the surface's own metadata endpoint** (`/variables.json`), stored as fixture metadata, never shown to the consumer.

If a surface type cannot reach floor from admissible captures, record the shortfall in the fixture header and the RESULT; do not substitute rule prose for cells again.

Also register each captured surface's file path with `g1_declared` in mind: step 3 runs the declared probe on every surface file.

## Step 3 — Scorer v2 design (fixed here; zero spend) and schedule

### D9. Qualifier families (replaces per-qualifier scoring for redundant forms)
An estimate's qualifiers are grouped into families; the family is the scored unit, the published forms are recorded:
- `interval` = {SE, MOE(level), CI(level)} — deterministic transforms of one another given the level; z from `[g1.z_by_level]` or the qualifier's own `z`.
- `relative` = {CV, RSE} — the SE/estimate ratio; scored separately from `interval` so H1-type questions remain testable.
- `reliability` = {RELIABILITY_FLAG, SUPPRESSION} — the producer's categorical outcome.
- `dp` = {DP_NOISE}; `vintage` = {VINTAGE}.
Family level = the best level achieved by any of its published forms, with a legitimate cross-form derivation (CI given where SE was published) scoring L3, an exact published form L4. Cross-family derivations (SE stated where only CV was published) score the *target* family only if the estimate is also correct and are recorded as `cross_family_derivation` in observations. Denominators in all v2 Results are families, not qualifiers; report both counts.

### D10. Failure-class attribution
A candidate counts as this estimate's qualifier only if it is **bound** to it: same row, same sentence, or an explicit reference (the estimate's label or value within the binding window, configurable in `harness.toml [g1.binding]`). No bound candidate → **L1 `omission`**. A bound candidate that is wrong → L0 with its specific class (`quantity_hallucination`, `level_change`, `fabricated_qualifier`, `suppression_override`). `binding_error` is reserved for a candidate bound to *another* estimate being presented as this one's. The three v1 records the reviewer labelled omission but the scorer labelled otherwise become verbatim test cases with the corrected expected class.

### D11. Covariates recorded on every record, never scored
`relative_deviation` (restated qualifier vs source, signed), `rounding_direction` (widened/narrowed/none), `summary_precision_consistent` (qualifier rounded to the same significant digits as the restated estimate — the D7 coarsening case), `compression_ratio` (source passage tokens / response tokens), `footnote_distance_chars` (from the fixture), `declared_leg_score` (from step 3's `g1_declared` run on the surface file), `surface_type`, `compression_level`, `consumer_model_id`. D7 stays strict in v2; the calibration run sets any rounding boundary from these covariates.

### D12. Compression budget factor (indirect mode only)
Three prompt variants in `g1_prompts.toml`, new epoch `g1-v2-2026-09-03` (the direct prompt is unchanged in text but carries the new epoch):
- `none`: the v0/v1 indirect prompt verbatim.
- `short`: "Restate the following for a general-audience summary in no more than two sentences."
- `tight`: "Restate the following in one sentence of at most 30 words for a general audience."
Direct mode has no compression variant. Every indirect passage is elicited at all three levels.

### D13. Control arm
One weaker consumer, `claude-haiku-4-5-20251001`, pinned in `g1_consumer.toml` as `control`, invoked through the same `model_stub` choke point with `--model`; identity gate (invariant 5) applies — a response reporting a different model stops the run. Runs **only** on the holdout grid (all surface types incl. `prose_labeled` holdout, all compression levels, direct mode). It is a control, not a factor: results are reported beside Opus's, never pooled with them.

### D14. Pre-registered statements (written before any v2 data)
- **E4** (Lee 2026 decontextualization under summarization): family loss rate rises monotonically none → short → tight.
- **E5** (Peters & Chin-Yee 2025; Ansari 2026 hedging collapse): under `tight`, omission (L1) is the modal failure.
- **E6** (van der Bles 2019; v1 found no L2 at `none`): L2 rate at `tight` > L2 rate at `none`. If L2 stays at zero under compression too, that is the finding — the form-shift mechanism does not appear in this consumer.
- **H3** (two-sided, no prior art; the G1 construct question): `table_coded` and `prose_labeled` differ in family loss rate. Either direction is a finding: structured coded fields helping machines *find* uncertainty may or may not help them *restate* it.
- **H4** (replaces v1's H1 on the correct construct): `flagged_cell` reliability markers are lost at a higher rate than numeric `interval` qualifiers.
- **H5** (Lee 2026; spatial separation): `footnoted` qualifiers are lost more than inline ones; loss rate increases with `footnote_distance_chars`.
- **C1** (control): the control consumer's loss rate ≥ Opus's at every compression level.
- Retained from v1, not re-tested as an expectation: `vintage` is carried (0/149 lost).

### Schedule
`scripts/gen_g1_schedule.py` v2: split **by passage** (a passage belongs to exactly one split); indirect = passages × 3 compression levels; direct = (proposition, family); control arm = holdout schedule again under the control model. Report schedule size and floor cost per run before any call. Run `g1_declared` on every surface file now (zero spend) and store its score in the fixture metadata for D11.

## Step 4 — Dev grid elicitation (model spend; Opus only)

Runs `g1_eval_v2_dev_2026-09-03[_b, _c…]`, ceiling 2.0M each. Dev split only, all three compression levels, direct mode. Evidence to `assessment/evidence/g1/v2/dev/`. **No holdout, no control arm in this step.**

## Step 5a — Parser v2 + scorer v2 (zero spend), then freeze

Parser v2 rules motivated by named dev responses (table forms, footnote forms, flag legends) and by the three v1 parser misses (exact ±-form outranking quoted bounds; hyphenated coverage phrase; exact MOE outranking rounded bounds), each cited in its docstring and reproduced verbatim in `restatements.yaml` `v2_cases`. Scorer v2 implements D9–D11. Both stamps required on every record. Re-score all v0 and v1 evidence under (`g1-parse-v2`, `g1-score-v2`) → new results files (`g1_v2_rescore_v1_*`), registered beside v1's so the D9 effect on the v1 grid is a registered pair (expected: genuine losses 6 → ~3 by the reviewer's reading; report the scorer's number).

Commit; tag the message `g1-v2-frozen`. `_g1_parse.py`, the scorer, prompts, fixtures, and D14 do not change after this commit until the RESULT is written.

## Step 5b — Sealed holdout elicitation (model spend; Opus)
Runs `g1_eval_v2_holdout_2026-09-03[…]`; holdout split; evidence to `assessment/evidence/g1/v2/holdout/`. Nothing reused from dev — the split is by passage, so nothing can be.

## Step 5c — Control arm (model spend; control model)
Runs `g1_eval_v2_control_2026-09-03[…]`; holdout schedule under the control consumer; evidence to `assessment/evidence/g1/v2/control/`.

## Step 6 — Readiness gate, Results

- **Gate (pre-registered):** `unparseable` share on the Opus holdout records (families) ≤ 0.10, computed **only** on holdout evidence. Report first. If it fails, complete the rest, lead with the failure, table every unparseable holdout response by form; rules motivated by holdout responses belong to v3.
- Register Results with prefix `g1_v2_<split>_` (`dev`, `holdout`, `control`, `pooled_opus`): per surface_type × compression_level × mode: families, scored, unparseable, L3+ count, rate, Wilson 95 %, level distribution, failure classes, estimate status; per family type; genuine-loss count by the reviewer criterion (recorded per record as in v1, with `review_note`); covariate summaries (compression_ratio distribution per level; relative_deviation distribution among L0s).
- Test E4–E6, H3–H5, C1 each as supported / not supported / underpowered with counts; for E4 report the three rates and whether the ordering holds; for H5 report loss by footnote-distance tercile.
- Declared → observed join: table of surface_file × `declared_leg_score` × observed family loss rate (the A11 triad's first two legs side by side).

## Step 7 — DD-035 and mechanical updates
Append DD-035: the product-test decision and its rationale; qualifier families; binding-based failure attribution; covariates-not-scores for rounding and compression; split-by-passage seal rule; single control arm not a factor; the corrected v1 gate. Skeleton: G1 row Evidence adds DD-035 and step 2 admissions; `surface_type` vocabulary added to the G1 note; version bump. Protocol §9: one paragraph on families, compression factor, and the declared/observed join.

## Step 8 — Close
`seldon verify` (expect the cron files still dirty; say so), `seldon cc complete`, RESULT with discrepancies, both suites' counts, `kg.spend status` per run and the task total, commit, push.

## Discrepancies to report, not reconcile
- If the Census API or data.census.gov export is bot-blocked, route `needs_source` with the exact URL; do not hand-construct a table.
- If `claude -p --model` cannot select the control model under Max OAuth, report and skip step 5c; do not use the API key (DD-007).
- If the schedule exceeds 8.0M at the floor, stop after step 3 and report (see header).
- If a v1 reviewer-labelled omission cannot be reproduced as a D10 test case because the binding window is ambiguous, report the record and the window tried.

## Not in this task
The surfaced (retrieval) leg. Model-judge scoring. Product-level thresholds. Any rounding tolerance. Any second factor on the consumer axis. Edits to any RESULT, the memo, or any registered Result. Committing cron-owned files.
