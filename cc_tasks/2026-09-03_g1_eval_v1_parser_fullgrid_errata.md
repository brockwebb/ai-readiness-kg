# CC Task: G1 EVAL v1 — errata and Result annotation, suppression/reliability acquisition, sealed-holdout parser v1, full-grid elicitation, re-score, DD-034

**Date:** 2026-09-03
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-03_g1_eval_v1_parser_fullgrid_errata_ADDENDUM*.md` files.**
**SEQUENCING:** after `cc_tasks/2026-09-02_g1_eval_probe_family_v0_RESULT.md` (exists). Steps in this file are ordered by a hard dependency (the holdout is sealed until the parser is frozen); do not reorder.
**Spend:** steps 1–3 and 5 zero model spend. Steps 4 and 6 are the only model-calling steps, one declared run each under DD-022, **ceiling 2,000,000 tokens per run**, `claude -p` under Max OAuth only. 2.0M is below the standing daily band (55,000,000, `controls.yaml spend.daily_tokens`; verified in the v0 RESULT §6). If a run's schedule exceeds the ceiling at the `g1_eval` floor (34,000/call), split it into two declared runs; never raise the cap.

## Context

The v0 pilot (`2026-09-02_g1_eval_probe_family_v0_RESULT.md`) established three things this task acts on:

1. **The v0 readiness gate was circular** (Desktop spec defect). Parse coverage was measured on restatements written by the parser's author, scored 1.00, and then 8 of 18 real model responses were unparseable. Every scored failure in the run is a parser artifact (RESULT §6 items 1–5). This task fixes the gate, not just the parser: readiness is measured on model output the parser author has never seen, and the holdout responses do not exist until the parser is frozen.
2. **The 200k ceiling was set without reading the ledger** (Desktop defect). The per-call floor is 34,000 (`controls.yaml call_class_floors.g1_eval`); the grid is planned at that floor from the start.
3. **The memo's StatCan claim was snippet-sourced.** `docs/research/2026-09-02_g1_eval_prior_art.md` §2.3 asserts CV bands (16.6 % / 33.3 %) and suppression rules as content of the held 12-539-X 6e text; the held copy carries process guidance only (RESULT §9.2). SUPPRESSION is empty and RELIABILITY_FLAG is below floor as a result.

The design question the v0 prefix raised — whether the observed leg discriminates at all without compression pressure or product-surface fixtures — is **not** this task. Fixtures stay handbook-passage fixtures; this task makes the v0 design measurable on its full grid. The compression / product-surface design is a separate Desktop decision.

## Step 1 — Errata and Result annotation (zero spend; no edits to any RESULT, memo, or Result)

- **`docs/research/2026-09-02_g1_eval_prior_art_ERRATUM-01.md`** (new file, registered as a Seldon artifact, linked `corrects` → the memo's DesignNote). State: §2.3's StatCan row asserts CV bands and suppression rules as held content; they were read from a web-search snippet (§5 log row "Statistics Canada Quality Guidelines … coefficient of variation"), not from the held 49-page text; the corpus-wide scan (RESULT §9.2) found no such material in any admitted document. The bands are real but live in product-level user guides, not in 12-539-X — that is step 2's acquisition target, and until a copy is held the memo's transfer line for StatCan is process guidance only. Also record that memo §4.5's "StatCan CV bands and suppression" constraint is therefore unsupported by held text until step 2 lands.
- **Annotate the affected v0 Results.** The registered `g1_pilot_*` Results that encode the DP_NOISE direct L0 (`quantity_hallucination`, `10⁻¹⁰` read as 10) and the CV direct L1 (`certainty_assertion`, bare-number answer) are parser readings, not model behaviour. Use the mechanism the registry has for this without changing any Result value or state: create one Seldon Issue "v0 parser artifacts in pilot prefix" (importance high, urgency low) and link it to each affected Result with the relationship the ontology provides (`annotates`, `disputes`, or whatever `seldon link` accepts for Issue → Result; report which). List the affected Result ids in the Issue description with the evidence file and the parser rule that misread it. Do not register "corrected by eye" counts as Results.

## Step 2 — Acquire producer sources for SUPPRESSION and RELIABILITY_FLAG (zero model spend)

Standing acquisition path (`harvest_triage.py` → `manifest_triage.py`, a `scripts/g1srp_list_2026-09-03.yaml`, epoch `g1srp-2026-09-03`, rationale "G1 SUPPRESSION / RELIABILITY_FLAG fixture source"). Admit-with-reason or cut-with-reason for every candidate; never silence. Candidates, in order of expected yield:

1. **NCHS Data Presentation Standards for Proportions** — Parker, Talih, Malec et al. 2017, *Vital and Health Statistics* Series 2, No. 175. The federal suppression standard: RSE / CI-width / effective-sample-size rules with explicit "do not present" and "present with flag" outcomes. Primary source for SUPPRESSION.
2. **NCHS Data Presentation Standards for Rates and Counts** — the 2023 companion standard (Series 2; locate the exact number). Same class.
3. **Statistics Canada survey user guides carrying the A/B/C CV quality bands** — Canadian Community Health Survey user guide, Labour Force Survey guide (71-543-G), or any current StatCan product guide stating "acceptable / marginal / unacceptable" CV ranges with the 16.6 / 33.3 boundaries. Admit the first current one that states the bands with estimates; record the others as `R5_already_held`-class duplicates of the construct.
4. **U.S. Census Bureau CV-based reliability statement** for ACS — the current published rule behind data.census.gov's reliability presentation (historically CV < 12 % high, 12–40 % medium, > 40 % low). Locate the current Census page or handbook section that states it; the ACS general handbook already held may contain it — check before fetching.
5. Any ACS data-release filtering / suppression rule document (the ACS "data release rules" for 1-year estimates).

If a candidate is bot-blocked, route `needs_source` with the URL, as the UNECE chapter was. Then extend `assessment/tests/fixtures/g1/propositions.yaml` and `propositions_holdout.yaml` with SUPPRESSION (≥ 4 dev / ≥ 2 holdout) and RELIABILITY_FLAG (to ≥ 4 / ≥ 2) propositions from **admitted** text only, verbatim spans, `producer_rule` cited to `source_doc_id`, `tests/test_g1_fixtures.py` re-run. If the floor still cannot be met from held text, record the shortfall in the fixture header and the RESULT; do not invent. The synthetic suppression test case from v0 stays a unit test, never a proposition.

Bump the fixture files' header `fixture_version` to `v1-2026-09-03` and regenerate `assessment/config/g1_pilot.toml` from the fixtures so the schedule is complete and pre-registered before any call. Record the schedule size and its floor cost in the RESULT.

## Step 3 — Parser v1 development set: elicit the DEV grid only (model spend; run 1)

Run id `g1_eval_v1_dev_2026-09-03`, ceiling 2,000,000, both modes, pinned model `claude-opus-5`, prompt epoch unchanged (`g1-v0-2026-09-02` — the prompts are not the thing under revision). Elicit **only** propositions from `propositions.yaml` (dev). The runner must skip any proposition × mode (× class) whose evidence file already exists from the v0 prefix — the six v0 responses are reused, not re-elicited (evidence is not regenerable, and re-eliciting would make two responses for one schedule slot). Evidence to `assessment/evidence/g1/` as in v0.

**Do not elicit the holdout file in this step.** The holdout responses must not exist when parser v1 is developed.

## Step 4 — Parser v1 (zero model spend)

Every rule change is motivated by a named dev evidence file; a rule with no motivating response is not added. The v0 hand-written restatement fixtures stay; add fixture cases whose text is copied **verbatim** from dev responses (cite the evidence file in the case).

Required changes (from RESULT §6 items 1–5 and §9.4):

1. **Pre-normalisation layer** in `_g1_parse.py`, applied before the grounding-style NFKC pass, in this order: (a) superscript/subscript digits and superscript minus → explicit exponent notation (`10⁻¹⁰` → `1e-10`), plus `10^-10` and `1e-10` recognised as one form — this must run **before** NFKC, which maps `⁻¹⁰` to `-10` and destroys the exponent; (b) strip markdown emphasis (`**`, `*`, `_`, backticks) around and inside qualifier phrases; (c) pipe-table rows → one `label: value` line per cell pair; (d) bullet / colon label-then-value forms (`coefficient of variation: … 8.7%`) recognised as a label–value connector. Each transform is a named, tested function; the normalised text is stored in `observations` beside the raw so a reviewer can see what was parsed.
2. **Direct-mode leading-number rule.** In `direct` mode the qualifier class is named by the question; the first numeric token whose unit is compatible with the class (percent for CV/MOE-on-percent, points, count, rho/epsilon/delta forms for DP) is the qualifier even with no class keyword in the reply. Indirect mode is unchanged — a bare number there is still not a qualifier.
3. **Level-derived transformations for SE.** Add SE ↔ MOE and SE ↔ CI bounds as L3 transformations with the z factor derived from the proposition's `level` (0.90 → 1.644854, 0.95 → 1.959964; table in `harness.toml [g1.z_by_level]`, never hardcoded), so SE reaches L3 and the ACS 1.645 rule is the producer's rule, not the parser's. Tolerance remains D7 (published rounding).
4. **`parser_version`** stamped on every `EvalResult` (required field; validation fails without it), `g1-parse-v0` retro-assigned to the v0 results file by re-scoring it under v0 with the stamp (the DataFile is not edited; a new results file is written).
5. Readiness test rewritten: the dev-response coverage number is reported but is **not** the gate.

Commit, tag the message `g1-parser-v1-frozen`. Nothing in `_g1_parse.py` changes after this commit until the RESULT is written.

## Step 5 — Sealed holdout elicitation (model spend; run 2)

Run id `g1_eval_v1_holdout_2026-09-03`, ceiling 2,000,000, both modes, same model and prompt epoch, `propositions_holdout.yaml` only. Evidence to `assessment/evidence/g1/holdout/`.

## Step 6 — Readiness on holdout, full re-score, Results (zero model spend)

- **Readiness gate (pre-registered, replaces D5's):** `unparseable` share on the holdout responses ≤ 0.10. Report it before anything else. If it fails, the parser is not ready; still complete the re-score below, but the RESULT leads with the failure and every unparseable holdout response is read and its cause classified in a table (form, evidence file, whether the qualifier was in fact carried) — reported, not absorbed. Any rule change motivated by a holdout response belongs to a v2 parser in a future task.
- Re-score **all** evidence (v0 prefix + dev + holdout) under parser v1 → `assessment/results/g1_v1_<run>.json` per run plus one pooled file; each a Seldon DataFile. Score the v0 prefix under v0 as well (step 4.4) so the v0→v1 delta on the same six responses is a registered pair.
- Register Results with prefix `g1_v1_`: per class × mode × split (dev / holdout / pooled): n, scored, unparseable, L3+ count, rate, Wilson bounds; level distribution; failure-class counts; estimate-status counts; and the **genuine-loss count** — records at L0/L1/L2 after v1 where the reviewer's reading of the raw response agrees the qualifier was dropped, shifted, or corrupted (this is the number the v0 RESULT could only estimate by eye; the reading is recorded per record in the results file with the reviewer = CC and the criterion). Every number in the RESULT resolves to one of these Results.
- Test D8's E1–E3 and H1–H2 against the pooled v1 counts, each supported / not supported / underpowered with the counts, plus the v0-prefix-only verdicts under v1 for comparison.

## Step 7 — DD-034 and mechanical updates

Append DD-034 to `docs/design_decisions.md`: parser versioning as an instrument version stamped on every record; readiness measured on sealed holdout model output only, with the ordering rule that the holdout is elicited after the parser freeze; pre-normalisation before NFKC and why (superscript loss); z derived from the proposition's level; the memo erratum and what it withdraws from memo §4.5 until held sources land. Skeleton: G1 row Evidence cell adds DD-034 and the step-2 admissions; §9 gap for suppression/reliability updated with step 2's outcome; version bump. Protocol §9: one sentence on parser versioning in the eval family.

## Step 8 — Close

`seldon verify`, `seldon cc complete`, RESULT with the discrepancy section, both suites' counts, `kg.spend status` for both runs, commit, push.

## Discrepancies to report, not reconcile

- If any step-2 candidate is already held under another doc_id, report the id and do not re-admit.
- If the runner cannot skip existing evidence without a code change, make the change (it is the fetch/evaluate separation working as designed) and report it; never re-elicit a slot that has evidence.
- If the dev grid alone exceeds 2.0M at the floor, split into two declared runs and report both ids.
- If the holdout readiness gate fails, say so in the RESULT's first line.

## Not in this task

Compression conditions, product-surface fixtures, a second consumer model, the surfaced leg, model-judge scoring, product-level thresholds, any change to prompt templates, any edit to the memo, the v0 RESULT, or any registered Result.
