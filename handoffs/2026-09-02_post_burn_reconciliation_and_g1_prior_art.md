# Handoff — 2026-09-02 (evening): post-burn reconciliation, G1 prior art landed, design session next

Desktop thread. Zero model spend. Burn closed 2026-09-02 17:38 UTC (41/41 → 43/43 demand units; 14 accept, 1 sampling_inconclusive, 0 reject).

## Landed today (all committed, pushed; graph reconciled)

- Seldon AD-027 (snapshot artifacts), red test fixed (root cause `cf6cf0c` copy-edit gate flagging its own xref substitution; suite 697/0).
- ai-readiness-kg: housekeeping (verify clean); D0-r2 probes closed (238 tests); rubric v1.1 (`catalog_zero_coverage` v1 → PARTIAL; no-lastmod unscored; fractional threshold deferred to January pilot); spend guard (outcome classes, `empty_failure` release-and-back-off, burn state merges by batch id, 628 tests); deck v4 + brief with measured counts; G1 prior-art memo `docs/research/2026-09-02_g1_eval_prior_art.md`, 17 sources admitted (batch-025, epoch `g1eval-2026-09-02`, corpus 211).
- Graph: `2026-09-01_harness_reconciliation` → superseded.

## Findings from reviewing the RESULTs against each other

- §21.6 of the v038 RESULT says 37/1,474, 13 accept; its own table and the state file say **37/1,480, 14 accept** (b010 was never judged). The spend-guard RESULT copied the wrong figure; the deck RESULT recomputed correctly and flagged it. Errata + Result registration are in the queued task below.
- Slide 15 was stale within the hour (194 → 211 admitted) because the deck and G1 tasks ran concurrently. Lesson: tasks that write shared numbers are not independent; sequence them or have them resolve `{{result:…}}`.
- Nothing rebuilt the projection at burn close; the deck task had to. Fix queued.
- Seldon's own `cc_tasks/` is gitignored — its execution records are unversioned. Fix queued.

## Queued

- `cc_tasks/2026-09-02_post_burn_reconciliation.md` (ai-readiness-kg): errata ×2, Result artifacts for burn headline numbers, slide 15 → 211, brief demand paragraph, projection rebuild at burn close + staleness check, DD-032.
- `seldon/cc_tasks/2026-09-02_track_cc_tasks.md` (Seldon): un-ignore and version `cc_tasks/`.

## Next design session (fresh thread; this one is long)

G1 EVAL probe family. Read `docs/research/2026-09-02_g1_eval_prior_art.md` §1, §3, §4 first. Established: no named metric for numeric-uncertainty preservation under LLM restatement (162 logged queries, 6 families, memo §3 states the falsifier). Fixed by prior art: proposition-level unit (Du, Lu & Qu 2026), ordinal preservation levels, failure taxonomy (certainty assertion / omission), direct vs indirect assessment, producer-side definitions (ACS handbook, ONS, StatCan). Open: the numeric instrument itself — G1's contribution. Qualifier classes with **no** prior art at all: CV/RSE, DP noise parameters, vintage (memo F6). Design under `assessment/harness/`, fetch/evaluate separation, fixtures, thresholds in config. Also on the table for that session: `ansari-2026-slop-paradox-radiology-rewriting` cut as `ambiguous_contribution` — a `manifest_add` reverses it if the memo's use of it warrants.

## Waiting on the world

SEO spec finalization → item-level crosswalk + admission. Harness tagged release → admission. UNECE HLG-MOS GenAI chapter: 403 to every scripted fetch; operator drop admits it (`needs_source`).

## Superseded, keep on disk

`cc_tasks/2026-09-01_harness_reconciliation.md` (ADDENDUM-01). Never dispatch.
