# CC Task: the scoring model, as a documented query over the record and the cycle of record

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md` §2.5 and §4 item 5, with the prescription layer (`2026-09-17_prescription_layer_RESULT.md`) and the tier record (`2026-09-17_unassigned_indicators_RESULT.md` §1) as inputs.
**Implements:** DN-005 §2.5, read verbatim before anything is designed. Under DD-001 and DD-057.
**Framework layer served (DN-005 §5 rule 1):** §2.5, scoring.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

## 0. Prior art, and the one rule it all agrees on

Composite scoring of institutions is a settled field with a handbook: the OECD/JRC *Handbook on Constructing Composite Indicators* (2008) sets the ten steps (framework, data, imputation, normalisation, weighting, aggregation, uncertainty, decomposition, links, presentation) and says two things this task obeys: **equal weights are the default when no theoretical or empirical basis for others exists**, and **every step is documented so the score can be re-derived**. Instances in this domain: the Open Data Barometer and ODIN (Open Data Watch) score countries per element with equal weights and publish the per-element grid, not only the total; WCAG conformance is a gating model (A / AA / AAA, not additive), which is the alternative shape; OpenSSF Scorecard is additive 0 to 10 with per-check weights it publishes. None is on disk; cite by reference and say so, and check `corpus/` for any that is.

**Decisions taken here (operator overrides later):**

1. **The score is a query, `scripts/score.py`, over the record and the cycle of record.** No number is authored. Inputs: the Tier M `harness_leg` indicators (17 today, read from the record's basis field so new rules enter automatically), their verdicts per body on the cycle of record, and the `DECOMPOSES_INTO` edges to constructs and criteria.
2. **Denominator first, always.** Every score line carries `measured / total` at its level (indicators measured of indicators in the framework; legs judged of legs on the cycle; bodies on the cycle). A score without its coverage is not printed. The sentence on every output: "Scores cover only what the harness measures; Tier O and D indicators are not scored."
3. **Equal weights, hierarchical, additive.** Body score at an indicator = pass share over its judged rows (products, surfaces); construct = mean over its measured indicators; criterion = mean over its measured constructs; body = mean over criteria with at least one measured construct. `error` and `not_applicable` rows are excluded from the denominator and counted separately. This is the OECD default; the RESULT says so and says what would justify departing from it (a documented basis, which none exists).
4. **A second view, gating, beside the additive one.** Per body: the count of legs passed outright, and the first construct with zero passes. WCAG's shape, so a reader can see that an additive 0.4 can hide a construct with nothing in it.
5. **The prescription join is the third view.** For each body, the actions whose completion would raise its score, with the score delta each would produce (recomputed by flipping that leg's cells to pass) and its notional bands. Ranked by delta per effort band. This is where the prescription layer and the scoring model meet, and it is the January slide.
6. **Uncertainty is reported as sensitivity, not as an interval.** Re-derive every body score under (a) the prior cycle of record, (b) with each criterion dropped in turn; report the rank changes. OECD step 7 with no distributional claims.
7. **Every step documented once**: `docs/design/scoring_model.md`, generated from `score.py --explain`, listing the steps in OECD order with the choice made at each and the sentence that justifies it. Tests: the score of a synthetic body with known verdicts equals the hand computation; every body's score is re-derivable from its printed cells; the sum of `measured` never exceeds `total`.
8. **Nothing is published.** No report page, no site payload. The query exists and is documented; putting a score on the site is a publication and is the operator's.

**Write set:** `scripts/score.py` (new), `docs/design/scoring_model.md` (new, generated), `tests/test_score.py` (new), `scripts/check_protected_score.sh` (new), `seldon_events.jsonl`, the RESULT. The record is not written. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-18_scoring_model_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Prior art: DN-005 §2.5 verbatim, the corpus for any of the five references, the OECD steps as the outline.
## 2. Decisions 1 to 7. Tests first.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_scoring_model_RESULT.md`: §0 what DN-005 §2.5 says and what prior art is on disk; §1 the 16-body grid (additive score with coverage, gating view); §2 the ranked prescription join for one body and the top ten overall by delta per effort; §3 the sensitivity table; §4 every premise this task file got wrong; §5 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
