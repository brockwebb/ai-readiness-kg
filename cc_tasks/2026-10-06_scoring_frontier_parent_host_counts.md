# CC Task: frontier indicators out of the score, parent-host cells out of unit ranks, one measured count (audit C-06, C-13, C-07)

**Date:** 2026-10-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/audit/2026-10-04_full_audit.md` findings C-06, C-13 and C-07 (`docs/audit/2026-10-04_full_audit_findings.csv` rows 4, 6, 5). Three defects in what the shown scores and counts rest on. C-06 and C-07 are defects against standing decisions; C-13 is the ruling DN-012 d5 makes.
**Implements:** DN-012 d4, d5, d7.
**Framework layer served (DN-005 §5 rule 1):** §2.1, the framework object and its scoring model.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** 2026-10-06_absence_verdicts_rules
**Cycle:** the scores regenerate once, on rj5. If the recollection has also completed, rerun on the composite it declares; otherwise on rj5 and say so.
**Spend:** est. 2M tokens (Opus). Code, tests, regeneration, the suite. No model call.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Frontier exclusion (d4).** `score.structure` selects legs by `measurement_basis` today and lets `frontier: true` through. Exclude `frontier: true` indicators from every criterion's leg set, as candidates are excluded. A9 is reported on the matrix with its verdicts and is marked `frontier`. Regenerate `docs/design/scoring_model.md` and every quoted score. The audit's recomputation (CENSUS 0.080 to 0.089, EIA 0.133 to 0.160, SAMHSACBHS flat rank 7 to 5) is the check: reproduce those three or explain the difference.

2. **Parent-host cells (d5).** For every roster row with `host_shared_with`, or whose `host` is a department's rather than the unit's (SOI on irs.gov, ORES on ssa.gov, DRSMSU on federalreserve.gov; derive from the roster, do not hard-code the list), mark every cell read from that host (`robots.txt`, `/data.json`, `/.well-known/`, A4, A5, A11-declared, D2, and the D4 family) as `parent_host` on the matrices. Those cells do not enter the unit's score or rank. The unit's product-surface legs still do. A unit with no scorable legs left is shown unranked with the reason, not ranked last.
   - `docs/brief/H_limits.md` and the L0 report's methods section state which bodies lost which cells and why, generated from the roster.
   - The flat rank regenerates. Report NCHS's rank before and after.

3. **One measured count (d7).** Run the measured write-back against the cycle of record through `framework_writeback.save`: B1, B2, B4, B5, D2, D3, G4 to `measured`, G1-D to its DD-066 state, `measured_by` on every measured node pointing at the cycle of record (rj5 or the composite). Project. Rebuild the progress page. Then `docs/progress/index.html`, fig1 and `docs/brief/G_census_dogfood.md` print one count, computed at the generator, or two counts under two names ("indicators with a rule" and "indicators measured on the cycle of record"). Never one name with two values. Record which.

4. **Tests.** A `frontier: true` fixture indicator never enters `score.structure`. A roster row with `host_shared_with` yields `parent_host` cells that `score_body` ignores. A body with zero scorable legs is reported unranked. The counts block in `ai_readiness_framework.json` equals the generator's count on both surfaces.

**Write set:** `scripts/score.py`, the matrix and brief-pack generators, `framework/ai_readiness_framework.json` through the write-back only, `docs/design/scoring_model.md` regenerated, `docs/brief/H_limits.md` and `G_census_dogfood.md` regenerated, the L0 report's methods section, `docs/progress/`, `tests/`, the RESULT. Byte-identical: every rule and collector, `targets.yaml`.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-06_scoring_frontier_parent_host_counts_RESULT.md`, under 60 lines: scores before and after with the three audit checks; cells marked `parent_host` per body; ranks before and after; the count as now printed, with its name(s); premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** frontier exclusion → parent-host marking → write-back → regenerate scores, matrices, pack, report methods, progress page → tests → gate → RESULT → push.
