# RESULT: G1 instrument freeze at v2 — blind reviewer-calibration sample, two-leg G1, findings memo, deck slide draft, DD-036

**Task:** `cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md` (no addenda: globbed `…_ADDENDUM*.md`, none found). **Sequencing honoured:** the v2 RESULT existed before this task started. **Spend: zero model calls** — no `claude -p`, no reservation on `state/spend_ledger.jsonl`, `ANTHROPIC_API_KEY` never set. Biblio-cron files not committed. **Date:** 2026-09-03 UTC.

Every number in the findings memo and on the new deck slide is a `{{result:<NAME>:value}}` token that resolves to a registered Seldon Result; the memo carries no literal measurement. **162 Results registered by this task** to make that true (§3).

## 1. Reviewer calibration sample (blind)

`scripts/g1_calibration_sample.py` → `assessment/results/g1_calibration_sheet_2026-09-03.md` and `.csv`, plus the gitignored key `assessment/results/.g1_calibration_key_2026-09-03.json`.

**Draw (as printed in the first block of the sheet).** Seed `20260903`; population 778 family records — 650 from `g1_v2_pooled_opus_reviewed.json` and 128 from `g1_v2_control_reviewed.json`; strata = scorer level × reviewer verdict; proportional allocation with a floor of 3 per non-empty stratum (largest remainder on the residual, capped at stratum size); n = 60.

| stratum | population | allocated | | stratum | population | allocated |
|---|---:|---:|---|---|---:|---:|
| L0 × genuine | 18 | 4 | | L2 × parser_miss | 7 | 3 |
| L0 × parser_miss | 29 | 4 | | L3 × not_in_queue | 106 | 7 |
| L1 × genuine | 112 | 7 | | L4 × not_in_queue | 372 | 18 |
| L1 × parser_miss | 25 | 4 | | unparseable × genuine | 44 | 5 |
| L2 × genuine | 59 | 5 | | unparseable × parser_miss | 6 | 3 |

**Eight of the eighteen cells are structurally empty** and are named on the sheet: the review queue is by construction the records at L0/L1/L2 or unparseable, so no L3/L4 record carries a reviewer verdict (`L3 × genuine`, `L3 × parser_miss`, `L4 × genuine`, `L4 × parser_miss`) and no queued record is `not_in_queue` (`L0`, `L1`, `L2`, `unparseable` × `not_in_queue`). No floor was waived; the allocation above is what ran.

**Blinding.** Each record shows the sample id, the prompt exactly as the consumer saw it, the response verbatim, the estimate's label and value, the qualifier family and the forms the source published, the mode and the compression level — and nothing else. Checked on the generated sheet: zero occurrences of `claude-opus-5`, `claude-haiku`, `genuine_loss`, `failure_class`, `surface_type` or any surface-type name; the strings `parser_miss`, `preserved_exact` and `degraded_verbal` appear only in the stratum table and the verbatim D2 definitions at the top. Sample ids are assigned after a final shuffle, so their order carries no stratum information. The key file is ignored twice over (`assessment/.gitignore`'s `results/*` and an explicit new rule in `.gitignore`).

**Labelling instructions** are one paragraph, followed by the D2 level scale quoted verbatim from DD-033 and the D9 families quoted verbatim from DD-035, and one question per record ("which level (L0–L4) did the response achieve for this family, or U if the qualifier is stated in a form you cannot classify?") with a free-text note line.

**`scripts/g1_calibration_agreement.py`** computes, on a filled sheet: operator-vs-scorer Cohen's kappa with quadratic weights over L0–L4, a secondary unweighted six-category kappa that includes `unparseable`/`U`, and operator-vs-reviewer agreement on the review queue through a pre-registered implied-verdict rule (operator level above the scorer's ⇒ `parser_miss`; equal or below ⇒ `genuine`; `U` excluded and counted) — each with a percentile bootstrap 95 % interval, raw agreement, a full confusion table, and positive specific agreement on the minority call. It was **not run on real labels**; there are none. Tested on synthetic sheets: `tests/test_g1_calibration_agreement.py` (22 tests, including a hand-computed 2×2 where κ = 0.4, that quadratic weights rank a near miss above a distant one where unweighted κ cannot, that an undefined κ returns undefined rather than 0.0, and that a blank answer line is "not labelled" while a garbage one raises). `tests/test_g1_calibration_sample.py` (11 tests) pins the allocation rule.

**Prior art, searched before writing either script** (doctrine §1 order): this repo's own record first — `scripts/tevv_stability.py` already computes Cohen's kappa (item-presence, over a set union) and its Results `kappa` under tasks `de7ae80b` and `68426971` already record a kappa paradox (κ = −0.5904 at PA = 0.4092), with Cicchetti & Feinstein 1990 as the named remedy. That statistic is not reusable for an ordinal confusion table, but its lesson is adopted: kappa never travels alone here, and the sample is stratified precisely because 372 of the 778 records are L4. From the literature: Cohen 1960; Cohen 1968 and Fleiss & Cohen 1973 for quadratic weights on an ordinal scale; Efron & Tibshirani 1993 for the bootstrap; Landis & Koch 1977 cited and deliberately not applied (no κ threshold is pre-registered); and, for judging an LLM judge by human agreement, Han et al., arXiv:2510.09738, held in Wintermute as `harvest-arxiv-e2a16615` (metadata and triage abstract only — the body was not captured).

**Registered:** DataFile `g1_calibration_sheet_2026-09-03` (`09517e34`, with content hash), DataFile `g1_calibration_key_2026-09-03` (`6280ae39`, path only, not committed), Scripts `g1_calibration_sample` (`682ef91f`), `g1_calibration_agreement` (`8eca971e`), `g1_resolve_results` (`06eaeaca`); ResearchTask `85851bcd` — "Operator labels the G1 calibration sheet; then run g1_calibration_agreement" — state `proposed`, `DEPENDS_ON` the sheet.

## 2. Two-leg G1 in the skeleton and the protocol

`docs/crosswalk/usafacts_operationalization_skeleton.md` → **v0.2.7**. The G1 row now reads as two legs: **G1-D (declared)**, the unchanged `g1_declared` probe (AUTO, `public`), and **G1-O (observed)**, the family preservation rate at indirect `none` with the `unparseable` share and the `short`/`tight` rates beside it, per surface, every record stamped with consumer, prompt epoch, `parser_version` and `scorer_version` (EVAL, `paid`) — reported as a vector, never composited, with no product-level PASS/PARTIAL/FAIL in v0.2.x and compression a reported condition rather than a scored one. Type cell `G1-D: AUTO · G1-O: EVAL`; Tier cell `G1-D public · G1-O paid`; Status `v2 harness, frozen for the pilot (DD-036)`.

The G1 note gains the dissociation statement in one sentence, naming the two Results that show it (`g1_v2_pooled_opus_table_coded_{none,short,tight}_preservation_rate` against `g1_v2_pooled_opus_prose_labeled_{none,short,tight}_preservation_rate`, H3 in `expectations_v2`) and the §6.5 join file (`assessment/tests/fixtures/g1/v2/declared_leg.json`), plus the freeze, the v3 backlog (`73f0aa5d`) and the uncalibrated-reviewer status (`85851bcd`). The §5d Evidence cell gains DD-036, the admission groups by epoch (17 memo sources `g1eval-2026-09-02`, 4 producer rules `g1srp-2026-09-03`, 17 product surfaces `g1sfc-2026-09-03`) and the three pilot RESULT files.

`docs/crosswalk/assessment_protocol.md` §9: the eval-family paragraph is replaced with G1-D / G1-O as two vectors, never composited, and one sentence stating that G1-O's denominator is qualifier families (D9) — not forms, not documents. 21 lines against the 17 it replaces; the DD-033/DD-034 content of that paragraph (elicit/evaluate split, the rollup firewall, parser-version discipline, sealed-holdout readiness) is kept.

## 3. Findings memo

`docs/research/2026-09-03_g1_eval_findings.md` (DesignNote `6760baaf`; internal, not for distribution until the operator says so). Six sections exactly as specified, no recommendations section: the question and construct; the instrument at freeze as a table (fixtures per split and surface type, surfaces, prompts, consumer, scoring, schedule, both readiness gates, spend per run); the pre-registered statements with verdicts and Result tokens (E3 not supported; E4, E5, E6, H3 supported; H4, H5, C1 underpowered, C1 with both readings of its coded-verdict/wording disagreement) and the declared→observed join reproduced per surface file; what the reviewer counts are and are not; seven limits; what changes in the instrument and what does not. **173 tokens, 173 resolved.**

**Results registered to make the memo literal-free (162):**

| script | Results | what |
|---|---:|---|
| `scripts/register_g1_instrument_results.py` | 29 | fixture counts per split and surface type; schedule steps / new calls / tokens at the DD-022 floor and the no-reuse counterfactual; tokens settled per declared run and the task total; the two readiness-gate unparseable shares |
| `scripts/register_g1_join_results.py` | 70 | the declared→observed join per surface file (families, scored, lost, loss rate, declared score) and the same join by surface type at compression `none` |
| `scripts/register_g1_expectation_results.py` | 63 | the D14 counts behind E5, H3, H4, H5 and C1, read from `expectations_v2` and the C1 comparison file |
| **new Results** | **162** | wrote nothing to any existing Result |

`scripts/g1_resolve_results.py` renders and checks the tokens (`--check`, `--render`, `--get`, `--prefix`); `tests/test_g1_resolve_results.py` (8 tests) covers replay, ambiguity, integer rendering, unresolved-token behaviour, and asserts the committed memo resolves end to end.

## 4. Deck slide draft

`docs/crosswalk/framework_deck_2026-09-03_draft.pptx` — 19 slides: the 2026-09-01 deck's v5 content unmodified, plus **one** new slide 14 after the G1 slide (slides 14–18 renumbered 15–19). Title: *"Structured fields are necessary for the declared leg and not sufficient for the observed one."* It carries the join by surface type at compression `none` (surface type, declared leg, observed loss, scored families) as a monospace block and the E4 three-rate line, and is marked a draft on its own last bullet. Built by `scripts/build_framework_deck.py` from the new content file `docs/crosswalk/deck_content_2026-09-03_draft.md` after `g1_resolve_results.py` resolved its 13 tokens; the slide fits at 15 pt with no split. **`framework_deck_2026-09-01.pptx` is not modified** (git shows it unchanged). Registered: DataFile `framework_deck_2026-09-03_draft` (`c3e98de7`, state `proposed`) and DataFile `deck_content_2026-09-03_draft` (`a09d0532`). Nothing was sent anywhere.

## 5. DD-036 and close

DD-036 appended to `docs/design_decisions.md` (DesignNote `9b502f69`): the freeze at v2 and why (the remaining parser misses bias the loss rate upward, i.e. against the finding); two-leg G1 with no composite and the dissociation that forces it; the reviewer-calibration protocol (blind sheet, stratification, quadratic-weighted kappa, no pre-registered threshold, kappa never alone); **a freeze is the last act of the task that declares it** (v2's amendment was correct but its sequencing was not — back-test before the tag, seal after it); and what does not change. v3 backlog reference `73f0aa5d`.

| check | value |
|---|---|
| root `tests/` suite | **683 passed** (was 642; +41 across three new test files) |
| `assessment/` suite | **471 passed, 1 skipped** (unchanged — no harness code was touched) |
| `seldon verify` | 1 issue: `docs/corpus/acquisition_candidates.md` modified — the biblio cron (Seldon task `989daaad`), not this task; expected and left |
| model calls | **0** — no ledger entry exists for this task |
| files changed under `assessment/harness/` or `assessment/config/` | none: the instrument is frozen |

## 6. Discrepancies (premise vs live state) — reported, not reconciled

1. **There is no deck resolver, and Seldon's own resolver cannot reach these Results.** The task's premise ("numbers from Results via the deck's resolver as slide 15 uses") does not hold: slide 15's numbers are literals in `deck_content_2026-09-01.md`, verified by hand against Results in a prior RESULT's derivation table. Seldon's resolver (`seldon/paper/build.py: load_named_artifacts`) matches an artifact's `name` property and runs inside a `paper/` project; this repo has no `paper/` directory, `seldon result register` has **no `--name`**, and the G1 Results carry their name in `properties.units`. **Lookup path used:** replay `seldon_events.jsonl` → `Result` artifacts → `properties.units == NAME` → `properties.<field>`, implemented in `scripts/g1_resolve_results.py`. A second consequence, unfixed: Seldon's `resolve_references` treats a Result in state `proposed` as a fatal reference (SI-03), and every G1 Result is `proposed`, so these numbers could not be resolved by that path even with a `name`.
2. **`units` is overloaded in the registry.** 14 registered Result names are ambiguous because older Results used `units` as an actual unit (`count`, `proportion`, `accuracy`, `kappa`, …). No `g1_*` name is ambiguous, and the resolver refuses to guess rather than picking one.
3. **The `g1_v2_pooled_opus_reviewed` DataFile did not exist.** The v2 task registered 515 `g1_v2_pooled_opus_*` Results with `--data-name g1_v2_pooled_opus_reviewed`; `seldon result register` accepted the name without creating the artifact, so those 515 Results carry **no `computed_from` edge**. The DataFile is created now (`0bc7bcdb`, with content hash and a description recording this), but the 515 existing Results are not edited — the task forbids editing a registered Result, and back-filling 515 edges is a separate job.
4. **Seldon's ontology refuses DataFile provenance edges.** `DataFile → GENERATED_BY Script` and `DataFile → COMPUTED_FROM DataFile` are both rejected ("valid from_types: Result, Figure, Table" / "Result"), so the calibration sheet's provenance lives in its description rather than in edges. The required edge — ResearchTask `85851bcd` `DEPENDS_ON` the sheet — was created.
5. **No pptx skill exists on this machine.** `/mnt/skills/public/pptx/SKILL.md` is absent (there is no `/mnt/skills`), so it could not be read as instructed. The repo's own deterministic builder `scripts/build_framework_deck.py` (python-pptx, no theme, the path that produced the 09-01 deck) was used instead, and the slide is rendered in that deck's existing idiom: bullets plus a monospace preformatted block, as slides 4, 8 and 15 already are. No table shape is used, because the builder emits none.
6. **One skeleton sentence outside the G1 row is now looser than the row.** §7 item 8: *"G1 supplies that: structured error measures plus an eval for whether AI restatements keep them."* It is not wrong under the two-leg definition, but it does not name the legs. Reported and **left**, per the task.
7. **The `no_declared` and `prose_labeled` strata do not appear in the fixture-count Results.** `g1_v2_instrument_fixture_*` counts only the four surface types present in the v2 fixture files; `no_declared` surfaces carry no qualifier and so no proposition (declared leg only), and the `prose_labeled` stratum lives in the v1 fixture files re-split into dev. The memo's §2 says so in words.
8. **The join covers 11 surface files, not 17.** Six of the 17 admitted surfaces have no observed records: the three `no_declared` surfaces and the three cube-metadata legend companions. They are declared-leg-only and are named as such in the memo.

## Not in this task, by its own boundary

Any model call; any parser or scorer change (frozen — no file under `assessment/harness/` was touched); running the agreement script on real labels; product-level thresholds; sending or publishing anything; editing any RESULT, DD, memo or registered Result.
