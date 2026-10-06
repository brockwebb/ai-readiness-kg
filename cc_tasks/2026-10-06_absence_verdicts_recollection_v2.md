# CC Task: recollect the legs the absence fixes left blind, on all 16 bodies, as a new dated cycle (v2, operator-launched)

**Date:** 2026-10-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session, under DN-012 d3 and d6. v2 of `2026-10-06_absence_verdicts_recollection.md` (withdrawn, e61aca4b): identical in content, without the `Spend` and `Network` headers that make a task a dispatcher candidate (DN-006 decision 3), so the dispatcher cannot launch it. The rules task turned truncated absences into errors; this task collects what those errors say was not looked at. It is the rescan the operator's standing rule reserves to him: **launched by the operator, not the dispatcher.**
**Implements:** DN-012 d3, d6.
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement.
**Fulfils:** its own ResearchTask. Launched by the operator.
**After:** 2026-10-06_absence_verdicts_rules
**Read first:** the rules task's RESULT.
**Launch:** by the operator only, by pasting the dispatch line, after `2026-10-06_absence_verdicts_rules` has completed. Not a dispatcher candidate by construction. Estimated 4M tokens (Opus): one targeted collection cycle, one judgement, the views, the suite; no model call. Fetches under the manners layer only, on the roster hosts plus each body's declared `api_base` and `inventory_urls` hosts, on the legs below only; nothing else; `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Resolve the declarations the rules task left open.** For each body whose `inventory_urls` is incomplete, read its department's data.json URL from `catalog.data.gov` (the organization page lists the harvest source) and the agency's own developer or API page for `api_base`; write both to `targets.yaml` with the page they were read from. A body whose API page cannot be found on its own site gets no `api_base` and stays `error` on A2 under d1; that is the finding.

2. **Collect, targeted.** A new cycle `scan_2026-10-06_recollect` over exactly: A1, A2, A3 and the D4 family (D4, B1, B4, D3, G4, and the fifth consuming leg), all 16 bodies plus the three reference hosts, with the ranked links collector at the standing cap, the declared `api_base` probed for its description, and every `inventory_urls` entry fetched and membership-tested. The six L0 host checks and every other product leg are not collected; the cycle of record for them remains `scan_2026-09-10`. State this on the cycle's manifest.

3. **Judge** under the current rule versions, to the log per DN-003. Report per leg and per body: pass, fail, error, and for every remaining `error` the reason text. A `fail` now means a complete search found nothing.

4. **Composite record.** The views regenerate from a declared composite: host checks and untouched legs from `scan_2026-09-10` rj5, the recollected legs from this cycle. The composite is named on every matrix and in the report's methods line, with both cycle ids. No score is recomputed in this task (the scoring task owns `score.py`); the scoring task reruns on the composite after this one.

5. **Delta table.** For every body and each recollected leg: the rj4 verdict, the rj5 verdict, this cycle's verdict. Census ACS A2 and the 28 D4 "no catalog" rows are the named cases; say what each became.

**Write set:** `targets.yaml` (declaration fields), the new cycle's state and log events, the composite declaration, the regenerated views, the RESULT. Byte-identical: every rule, every collector, `score.py`.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md`, under 60 lines: declarations resolved and not resolved; verdict counts per leg before and after; the delta table's named cases; requests made per host (manners accounting); premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** read rules RESULT → resolve declarations → collect → judge → composite → views → delta → gate → RESULT → push.
