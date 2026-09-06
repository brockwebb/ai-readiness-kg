# CC Task — Fable labels the ER gold sample; score it

**Date:** 2026-09-05
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-05_homograph_split_and_er_gold_sample_RESULT.md`)
**Follows:** `0b8ea847` (completed). Uses its sheet, key, and scorer unchanged.
**Correction to DD-045 §4:** "gold is human-labelled" is withdrawn. Gold is labelled by an independent model rater — `claude-fable-5-1` — that had no part in any pipeline decision on these pairs. Append this as DD-045 addendum-01 with the limitation stated plainly: a same-family rater bounds correctness relative to that rater, not to ground truth; the operator is the escalation path for decisive `uncertain` pairs only.
**Spend:** 100 pairs + 30 test-retest repeats on Fable, one pair per call, hermetic cwd. Ceiling from a 10-pair calibration at the `judge` floor (DD-042); the prior task measured ~30.8k tokens/pair for a comparable prompt, so expect ~4.5M; **stop above 8M**. Claude Max OAuth only; any `ANTHROPIC_API_KEY` in the environment is a STOP.
**Zero edits to:** the sheet's pair set, `state/er_gold_key.json`, `scripts/score_er_gold.py` logic (adding an input path is fine), both CQ yaml files, `kg/schema.yaml`.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-05_er_gold_fable_labels_and_score_ADDENDUM*.md` before starting.**

---

## 1. The rating protocol

- Rater: `claude-fable-5-1`. One pair per call; hermetic empty cwd; no repo access; no prior calls in context. The prompt is the sheet's own "What to do" section verbatim plus one pair's two spans, labels, doc titles, and arms — **nothing else**: no cosine, no term, no stratum, no pipeline decision (those are only in the key file, which the rater never sees).
- Output: `same | different | uncertain`, confidence in [0,1], one-sentence reason quoting the deciding phrase from each span.
- Calibration: first 10 pairs at the floor, measure tokens/pair, declare the ceiling for the remaining 90 + 30, then run.
- Resume from evidence on disk; every decision record stamps pair id, model, timestamp, prompt hash.

## 2. Test–retest
Re-rate 30 pairs (seeded draw, 6 per stratum, seed 20260905) in a fresh hermetic session after the main pass. Register `er_gold_retest_agreement` (raw) and `er_gold_retest_kappa` (Cohen). This is the reliability bound for the gold; it is reported, not gated.

## 3. Fill and score
Write the verdicts into the sheet's `verdict`/`note` columns (the sheet is the operator-facing record; Fable's reason goes in `note`). Run `scripts/score_er_gold.py`. It registers `er_gold_precision`, `er_gold_recall`, `er_gold_cluster_f1`, `er_gold_verdict` per DD-045 §3. Also register per-stratum precision/recall with Wilson intervals — **stratum E separately and first in the report**: it is the measurement the homograph split was waiting on.

## 4. Escalation rule — the only path to the operator
A pair goes in `docs/research/2026-09-05_er_gold_escalations.md` **only if** Fable says `uncertain` **and** flipping that single pair to `same` or `different` would move a DD-045 threshold verdict (precision across 0.95 or recall across 0.80, on the point estimate). Compute that by re-scoring with the flip. Anything else `uncertain` is excluded per the sheet rule. If the escalation file is empty, say so.

## 5. Reporting
RESULT: `cc_tasks/2026-09-05_er_gold_fable_labels_and_score_RESULT.md`. Lead with stratum E, then the DD-045 verdict, then retest κ, then escalations (or "none"). State every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on the three protected files. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 calibration → §1 main pass → §2 → §3 → §4 → §5.
