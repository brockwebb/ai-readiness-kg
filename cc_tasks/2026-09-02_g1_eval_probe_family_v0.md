# CC Task: G1 EVAL probe family v0 — uncertainty preservation under AI restatement (declared leg + observed leg), gated F7 prior-art check, pilot run, DD-033

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_g1_eval_probe_family_v0_ADDENDUM*.md` files.**
**SEQUENCING:** runs AFTER `cc_tasks/2026-09-02_post_burn_reconciliation.md` (that task writes DD-032 and registers burn Results; this task writes DD-033 and registers G1 Results — shared numbering and shared Result namespace, not independent).
**Spend:** steps 0–5 are zero model spend. Step 6 is the only model-calling step; ceiling **200,000 tokens**, declared per DD-022 (`--ceiling-tokens 200000`), under Max OAuth via `claude -p` only. Confirm before step 6 that this ceiling is below the standing daily band in `controls.yaml`; if it is not, stop before step 6 and report — do not run it.

## Context

Indicator G1 (skeleton §5d) is DOC + EVAL: error measures published as structured fields beside estimates, and an EVAL of whether AI restatements carry the uncertainty. No implementation exists. Prior art was searched 2026-09-02 (`docs/research/2026-09-02_g1_eval_prior_art.md`, 162 logged queries, 17 sources admitted, corpus 211). Read that memo §1, §3, §4 before touching code. §4 fixes eight design constraints from found prior art; this task adopts them and cites them in code docstrings. What §4 leaves open — the numeric level scale, CV/reliability/suppression, DP noise and vintage, per-answer vs per-proposition — is designed here as **v0, pre-registered, and frozen before the pilot run (step 6) produces any data**.

The measurement template is the A11 triad (skeleton §5d note): declared uncertainty (structured fields) → surfaced uncertainty (what retrieval delivers) → observed preservation (what restatements carry). This task builds the **declared** leg as an AUTO probe and the **observed** leg as an EVAL probe with retrieval removed by construction (source text supplied in context), so every failure the observed leg records is a restatement failure, never a retrieval failure (memo §4.8). The **surfaced** leg (live answer engines, retrieval included) is out of scope; it is a separate proposal with its own gate.

## Step 0 — F7 prior-art gap check (gated; zero model spend)

Family F6 in the memo (12 queries) is the only evidence that DP noise parameters and vintage are uncharted. Twelve queries is thin for a claim the design builds on. Before any design step, extend `scripts/g1_prior_art_search.py` with family **F7** and run it, appending the log to `docs/research/2026-09-02_g1_eval_prior_art_query_log_f7.json` (new file; never edit the run-1/2/3 logs).

**Pre-registered falsifier (same as memo §3):** a work that annotates uncertainty carriers on statistical estimates and scores machine restatements against them. Hits that do not meet that description are neighbours, not falsifiers, and are recorded as such.

F7 phrasings (each on OpenAlex title/abstract, arXiv abs, Semantic Scholar):
1. `disclosure avoidance noise user guidance large language model`
2. `differential privacy communicating noisy statistics data users`
3. `temporal validity statistics answer large language model release date`
4. `outdated statistic stale answer official data vintage`
5. `data release version temporal misalignment retrieval augmented`
6. `number rounding precision preservation summarization`

Named lookups (resolve, read abstract, classify with clause): FreshQA (Vu et al. 2023, arXiv:2310.03214); TimeQA (Chen et al. 2021); RealTime QA (Kasai et al. 2022); Cummings et al. 2021 "I need a better description" (user expectations for differential privacy); the Census Bureau's Disclosure Avoidance System documentation for the 2020 Census (whatever the current handbook is titled — this is also the fixture source for the DP class, see step 3).

**Gate:** if any hit meets the falsifier for any qualifier class, STOP the design steps for that class only, record the work in a `docs/research/2026-09-02_g1_eval_prior_art_F7_addendum.md` (new file), stage it through the standing acquisition path, and continue with the remaining classes. If the falsifier is met for numeric uncertainty preservation generally, stop the whole task and report. If nothing meets it, record that with the query counts in the same addendum and proceed. Do not admit FreshQA/TimeQA/RealTimeQA to the corpus unless they meet the falsifier or supply a vintage-preservation *metric*; "temporal knowledge" benchmarks measure whether the answer is current, not whether a restatement carries the as-of date, and that distinction is the finding to record.

## Design (fixed here; do not re-derive in code)

### D1. Unit of analysis
A **proposition**: one published estimate plus its qualifier set (memo §4.1; FActScore; Du 2026). Schema, as YAML fixture (`assessment/tests/fixtures/g1/propositions.yaml`):

```yaml
- id: g1-acs-001
  source_doc_id: census-acs-general-handbook-2020     # admitted doc_id, required
  grounding_span: "<verbatim span from the source>"   # kg/extraction/grounding.py rules
  estimate: {value: 12.3, unit: percent, label: "…"}
  qualifiers:
    - {class: MOE, value: 1.8, unit: percent_points, level: 0.90}
  vintage: {as_of: "2018", period: "5-year"}           # optional; present when the source states it
  producer_rule: "ACS MOE published at the 90 percent confidence level"   # one line, cited to source_doc_id
```

Qualifier classes (closed enum, `records.py`): `MOE`, `CI`, `SE`, `CV`, `RELIABILITY_FLAG`, `SUPPRESSION`, `DP_NOISE`, `VINTAGE`. `CI` carries `lower`/`upper`/`level`; `CV` carries `value` and, when the producer defines bands, `band`; `SUPPRESSION` marks an estimate the producer would not publish (StatCan 12-539-X 6e); `VINTAGE` is the as-of / period statement.

### D2. Level scale for numeric qualifier preservation (v0 — G1's contribution)
Adopts the *structure* of Du 2026's ordinal scale and van der Bles 2019's form-of-expression axis (numeric range / verbal qualifier / none). Levels, per proposition, per qualifier:

| level | name | definition |
|---|---|---|
| L4 | `preserved_exact` | qualifier class, value (within the source's published rounding), confidence level and binding to the correct estimate all restated numerically |
| L3 | `preserved_transformed` | qualifier restated numerically under a legitimate transformation: MOE→interval bounds, interval→±, level-preserving rounding to the source's published precision, "±1.8 points" → "between 10.5 and 14.1 percent". Still numeric, still correct |
| L2 | `degraded_verbal` | numeric qualifier replaced by a verbal band ("about", "roughly", "approximately", "an estimated") with no number — the van der Bles form shift |
| L1 | `omitted` | estimate restated, qualifier absent — Du's *certainty assertion* / *omission* |
| L0 | `corrupted` | qualifier present and wrong: magnitude outside published rounding (record direction `widened`/`narrowed` in observations — both L0, asymmetry recorded not scored), wrong confidence level, bound to the wrong estimate, fabricated qualifier the source does not carry, or a `SUPPRESSION`/`RELIABILITY_FLAG` estimate restated as usable |

Mapping to the harness's three-point `Score` (protocol §3): `PASS` = L4 or L3; `PARTIAL` = L2; `FAIL` = L1 or L0. The level and failure class travel in `observations`, never collapsed into the score alone (skeleton §6b.5).

**Estimate fidelity is scored separately** from qualifier preservation: `estimate_status ∈ {exact, rounded, wrong, absent}` (Zhao 2020 quantity-hallucination class; Cao 2024 sub-taxonomy). A restatement with the estimate wrong and the qualifier right is a different finding from the converse, and G1's construct is the second one. Both are recorded; only qualifier preservation feeds the G1 score.

**Failure-class vocabulary** is the memo's (§4.3): `certainty_assertion`, `omission`, `decontextualization`, `overgeneralization`, `quantity_hallucination`, plus G1's own `form_shift` (L2), `level_change` (wrong confidence level), `binding_error`, `fabricated_qualifier`, `suppression_override`. Map to the named classes first; the G1-native names are used only where no memo class fits, and the docstring says so.

### D3. Elicitation modes (memo §4.4)
Two modes per proposition, both scored by the same `evaluate`:
- `indirect`: "Restate the following for a general-audience summary." (the source passage containing the proposition in context)
- `direct`: "What is the {qualifier class in plain words} on {estimate label}?" (same context)
Prompt templates live in `assessment/config/g1_prompts.toml`, versioned with a `prompt_epoch` string stamped on every record.

### D4. Retrieval separated by construction (memo §4.8)
The source passage is always supplied in context. No retrieval, no browsing, no tools. A consumer that cannot see the source cannot be measured by this probe; that is the surfaced leg's problem.

### D5. Scoring is deterministic, with an honest `unparseable` outcome
`evaluate` is pure and fixture-testable. Qualifier extraction from the restatement is a deterministic parser (`probes/_g1_parse.py`): ±, "plus or minus", "margin of error of", "between X and Y", "X to Y", "confidence interval", "standard error", "coefficient of variation", "CV of", "relative standard error", reliability/suppression language as enumerated from StatCan 6e and ONS, percent-vs-point disambiguation, level phrases ("90 percent confidence"). A restatement the parser cannot classify returns outcome `unparseable` — a fourth outcome beside the three scores, reported with its own count, never coerced into FAIL or PASS. **Pre-registered readiness floor:** parse coverage on the fixture set (step 4) must reach ≥ 0.90 or the probe is not ready and step 6 does not run; report the failing phrasings. No model-judge fallback in v0; a judge is a separate proposal with a calibration gate.

### D6. No product-level threshold before calibration
Per-proposition scores are deterministic from the level (D2). The product-level roll-up reports the preservation rate (share at L3+) per qualifier class and per mode with a Wilson 95 % interval and the denominator — **no PASS/PARTIAL/FAIL at product level in v0**. Protocol §3: no composite until an intended use is decided. A threshold set now would be invented; it is set from the January calibration run against a stated rationale and frozen before the second run.

### D7. Tolerance is the source's own rounding, not a free parameter
"Within published rounding" = the restated value, rounded to the source's number of significant decimals, equals the source value. No relative-tolerance knob in v0. If a class of legitimate transformations the parser cannot recognise emerges in step 6, it is reported, not absorbed.

### D8. Pre-registered expectations for the pilot (written before any data; step 6 tests them)
- E1 (expectation, Du 2026): `indirect` loses qualifiers at a higher rate than `direct`.
- E2 (expectation, Du 2026; Ansari 2026): omission (L1) exceeds corruption (L0).
- E3 (expectation, van der Bles 2019): among non-omission failures, `form_shift` (L2) is the most frequent.
- H1 (**hypothesis, no prior art**): `CV`, `RELIABILITY_FLAG`, `SUPPRESSION` are lost at a higher rate than `MOE`/`CI`.
- H2 (**hypothesis, no prior art**): `VINTAGE` is omitted more often than any numeric qualifier.
- Not tested in v0 (fixed by prior art, Peters & Chin-Yee 2025): accuracy prompting does not fix qualifier loss. Do not add an "accurate" prompt variant to test it.

## Steps

### 1. Harness data model
- `harness/records.py`: add `SOURCE_EVAL = "eval"` and partition it out of both composites in `rollup.py` exactly as `WEB_SURFACE_SOURCES` is (a third vector, its own denominator; never summed into D1–D4). Add the `QualifierClass` enum and the `Level` enum from D2. Add `EVAL_DIMENSIONS = ("G1",)` and make the rollup report G1 as its own block (rate + Wilson + n per class × mode, plus `unparseable` count), not as a fifth core dimension.
- `harness/probes/base.py`: add `EvalProbe` with the same pure-`evaluate` contract: `elicit(consumer, proposition, mode) -> Elicited` (network/model; the analogue of fetch) and `evaluate(elicited, proposition) -> (Score | UNPARSEABLE, evidence, observations)`. Docstring cites memo §4 items by number.
- `harness/consumers.py`: `Consumer` protocol with one implementation, `ClaudeCLIConsumer`, invoking `claude -p` the way `kg/extraction/model_stub.py` does (hermetic empty temp cwd — keep the 2026-07-09 finding), model identity pinned in `assessment/config/g1_consumer.toml`, every call reserved through the DD-022 spend guard at the same choke point. A response reporting a different model is discarded and the run stops (invariant 5). Raw request + response persisted under `assessment/evidence/g1/<proposition_id>.<mode>.<prompt_epoch>.<model_id>.json` before scoring — evidence is not asserted.

### 2. Declared leg — `probes/g1_declared.py`
A `DistributionProbe` over CSV/JSON distributions (sources: catalog only). Reads the header/fields; matches uncertainty-field patterns from config (`assessment/config/harness.toml`, new `[g1]` block: `uncertainty_field_patterns` — seed with ACS `*_M`/`*_MA`, `MOE`, `margin_of_error`, `CV`, `RSE`, `SE`, `standard_error`, `lower`/`upper` bound pairs, `flag`/`reliability`). PASS = uncertainty fields present for the estimate fields; PARTIAL = present for some, or present only as free-text notes/footnotes (skeleton G1: "not footnotes"); FAIL = none. Observations: fields matched, fields unmatched, pattern id. This is a heuristic on field names and the docstring says so; it is the declared leg, not a claim that the values are right.

### 3. Fixture set — `assessment/tests/fixtures/g1/propositions.yaml`
Build ≥ 4 propositions per class from **admitted** sources only, grounding span verbatim (invariant 3 discipline; run the span through `kg/extraction/grounding.py` normalisation in a test):
- `MOE`, `VINTAGE`: `census-acs-general-handbook-2020`
- `CI`, `SE`, `CV`: `ons-uncertainty-and-how-we-measure-it`
- `CV` bands, `RELIABILITY_FLAG`, `SUPPRESSION`: `statcan-quality-guidelines-6th-edition`
- `DP_NOISE`: **not from an invented example.** The skeleton records DP documentation as a gap. If step 0's Census DAS lookup yields a fetchable, admissible handbook, stage it through the standing path (`manifest_add`, rationale "G1 DP_NOISE fixture source"), and build the class. If not, create a Seldon ResearchTask "G1 DP_NOISE fixture source — acquire Census DAS user documentation" and leave the class empty with the reason in the fixture file header. An empty class is a recorded gap, not a silent omission.
Each proposition carries `producer_rule` cited to its `source_doc_id`. Write a **held-out** set of ≥ 2 per populated class in `propositions_holdout.yaml` for step 6; the parser is developed against the first file only.

### 4. Observed leg — `probes/g1_preservation.py` + `probes/_g1_parse.py`
Implement D2–D7. Tests (`assessment/tests/test_g1_parse.py`, `test_g1_preservation.py`, `test_g1_declared.py`, `test_rollup.py` extension) from fixtures, no network:
- every level L0–L4 reached by at least one hand-written restatement per class (a `restatements.yaml` fixture beside the propositions: restatement text → expected level, expected failure class, expected estimate_status);
- `unparseable` reached and counted, never coerced;
- widened vs narrowed both L0 with direction recorded;
- rollup: eval results never enter D1–D4 or the web-surface vector (positive control: inject a G1 result and assert the core composite is unchanged — a monitor without a mutation test is not trusted);
- parse coverage on the fixture restatements ≥ 0.90 (D5 floor) — this test is the readiness gate for step 6.
- prompt_epoch and model_id stamped on every record; a record missing either fails validation.

### 5. Freeze
Commit steps 1–4 with the fixture set and D8 expectations as written above; tag the commit message `g1-eval-v0-frozen`. Nothing in D2–D8 or the fixtures changes after this commit until the RESULT is written. Write DD-033 in `docs/design_decisions.md` (append-only): the level scale v0, retrieval-by-construction separation, deterministic parse with `unparseable`, no product-level threshold before calibration, tolerance = published rounding, and the F7 gate outcome from step 0. Cite the memo and the sources by doc_id.

### 6. Pilot run (the only model spend; ceiling 200,000 tokens)
Only if step 4's readiness test passes and the ceiling is under the standing band. Run `ClaudeCLIConsumer` over **both** fixture files × both modes × 1 pinned model. Persist evidence first, score second. Report per class × mode: n, level distribution, preservation rate (L3+) with Wilson 95 %, `unparseable` count, estimate_status distribution. Test E1–E3, H1–H2 against the pre-registered statements; report each as supported / not supported / underpowered with the counts. Register every headline rate with `seldon result register` (n and interval bounds as separate Results, derivation command in the description, evidence path linked). Numbers in the RESULT resolve from those Results; no literal in prose that is not also a registered Result.

### 7. Skeleton and protocol updates (mechanical; no new design)
- `usafacts_operationalization_skeleton.md`: G1 row Status `draft` → `v0 harness`, Evidence cell adds the 17 memo sources by doc_id and the DD-033 reference; §9 gap for DP documentation updated with step 3's outcome. Bump version line.
- `docs/crosswalk/assessment_protocol.md` §9: add the eval family to the reference-implementation paragraph and the `SOURCE_EVAL` third vector to the rollup description. One paragraph.
- Register `docs/research/2026-09-02_g1_eval_prior_art_F7_addendum.md` and the new fixture files as Seldon artifacts.

### 8. Close
`seldon verify`, `seldon cc complete`, RESULT with the discrepancy section (premise vs live state), commit, push. Rerun full suites (`assessment/` and root `tests/`); counts in the RESULT.

## Discrepancies to report, not reconcile
- If `rollup.py`'s dimension handling cannot represent G1 without touching the D1–D4 reporting, report the shape of the change; do not widen `CORE_DIMENSIONS`.
- If the memo's admitted doc_ids for ONS/StatCan/ACS do not resolve in the manifest exactly as spelled in memo §2.3, report the actual ids.
- If `claude -p` under the hermetic cwd refuses long in-context passages, report; do not switch to the API key (DD-007).

## Not in this task
Live answer-engine (surfaced) leg. Model-judge scoring. Product-level thresholds. Any `manifest_add` for `ansari-2026-slop-paradox` — it stays cut; nothing here depends on it. Human annotation of restatements.
