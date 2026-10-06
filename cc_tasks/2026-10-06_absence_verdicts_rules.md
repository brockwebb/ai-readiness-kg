# CC Task: absence verdicts over partial searches become errors, with the unsearched remainder named (audit C-01, C-04, C-14)

**Date:** 2026-10-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/audit/2026-10-04_full_audit.md` findings C-01, C-04 and C-14 (`docs/audit/2026-10-04_full_audit_findings.csv` rows 1, 3, 7) and the reader gate's first fix. This task changes rules and collectors and re-judges the cycle of record. It fetches nothing.
**Implements:** DN-012 d1, d2, d3.
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none.
**Spend:** est. 3M tokens (Opus). Code, tests, one re-judgement, the suite. No model call.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Inventory first.** List every rule in `assessment/harness/scan/rules/` `REGISTRY` whose `fail` branch asserts absence ("no ... served", "not linked", "not in it"), with the collector it reads and the bound or guess that limits its candidate set. Write the list to `docs/research/2026-10-06_absence_rules_inventory.md` before changing anything. C-01 (A1, A3), C-04 (D4 and the five `CONSUMES = ("D4",)` legs: B1, B4, D3, G4 and the fifth the inventory names) and C-14 (A2) are the known members; the inventory may add others, and each addition is treated under decision 5.

2. **Links collector (DN-012 d2).** In `collectors/links.py`:
   - Rank on-host candidates before the cap by data-likeness: archive and data extensions from `params.a3_bulk`, `download` or `data` in the path or anchor text, then document order. Record the ranking key on each Observation's `parsed`.
   - Every on-host candidate past `max_links_probed` is written as an Observation with `fetched: false`, `error_class: unprobed_over_cap`, and `parsed.rank`. The cap still bounds requests; it no longer hides candidates.
   - Report per surface: on-host candidates, probed, unprobed.

3. **A1 and A3 (DN-012 d1).** A `fail` is reached only when every on-host candidate was probed. If any Observation on the leg carries `unprobed_over_cap`, the verdict is `error` with reason "absence not established: N of M on-host links probed, M minus N unprobed, cap K". New rule versions (`rule_a1_v5`, `rule_a3_v7`); prior versions stay in `REGISTRY` untouched.

4. **A2 and D4 (DN-012 d3).** Add to `targets.yaml` two optional per-body fields, `api_base` and `inventory_urls`, each entry carrying the agency page it was read from. Populate them in this task only where the project's own files already cite the location: `docs/data/sources_per_check.json` cites api.census.gov for ACS (fill CENSUS `api_base`); `params.yaml:296-297` records that data.gov reads each department's data.json (fill `inventory_urls` for every body with its own host's `/data.json`, its department's `/data.json`, and its `catalog.data.gov` organization URL, the department host taken from the row's `department`). Where the department host is not already written somewhere in this repository, leave the entry out and record it in the RESULT; the recollection task resolves it with network.
   - `rule_a2_v4`: if the body declares `api_base` and no Observation on the leg targets it, the verdict is `error`, "documented API base declared and not probed". If no `api_base` is declared, the verdict is `error`, "no documented API base declared for this body; guessed paths do not establish absence". `fail` is reserved for a declared base that was probed and served no description.
   - `rule_d4_v4`: if `inventory_urls` holds entries not observed on the leg, the verdict is `error` naming them. `fail` on "no catalog" is reached only when every declared inventory URL was observed and none served a catalog. The five consuming legs inherit through `CONSUMES`.
   - `manners.on_roster_host` admits a body's `api_base` host and `inventory_urls` hosts for the A1/A2/A3 and D4-family legs of that body only. Add the test that proves a third host is still refused.

5. **Other rules the inventory finds.** Apply decision 1's rule: a `fail` on absence over a bounded, guessed, or undeclared search becomes `error` naming the remainder. New version per rule, prior version kept.

6. **Re-judge the cycle of record** (`scan_2026-09-10`, rj4) under the new versions, to the log per DN-003, as rj5. No fetch. Expected effect: A1, A3, A2 and the D4 family flip from `fail` to `error` on every surface where the candidate set was truncated or undeclared. Count the flips per leg and per body. Regenerate the matrices, the L0 site, the brief pack and the evidence map views from rj5; every A1/A3/A2/D4 `fail` shown anywhere now states the search it is reached over, or is `error`.

7. **Prescriptions.** `tag_prescriptions.OUTCOMES` for A2 and D4: an `error` outcome prescribes nothing. Withdraw the shown prescription "Expose the product through an API" for any body whose `api_base` is declared, and "Publish a data.json inventory on the host" for any body whose `inventory_urls` were not all observed. The brief page that carried them (`docs/brief/G_census_dogfood.md:125`) regenerates.

8. **Tests.** For each new rule version: a truncated candidate set yields `error` naming the remainder; a complete probed set with nothing found yields `fail`; the prior version's fixtures still pass under the prior version. For the collector: a page with 60 on-host links and cap 25 writes 25 probed plus 35 `unprobed_over_cap`, in rank order, data-like links first. For manners: a declared `api_base` host is admitted for A2 of that body and refused for every other leg and body.

**Write set:** `assessment/harness/scan/collectors/links.py`, `assessment/harness/scan/manners.py`, new rule files and `REGISTRY` entries, `assessment/harness/scan/targets.yaml` (new fields only), `assessment/harness/scan/tag_prescriptions.py`, `tests/`, `docs/research/2026-10-06_absence_rules_inventory.md`, the rj5 log events, the regenerated views, the RESULT. Byte-identical: every prior rule version, `params.yaml` values, `score.py`.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-06_absence_verdicts_rules_RESULT.md`, under 60 lines: the inventory count and which rules beyond the three were changed; flips per leg and per body under rj5; which bodies have `api_base` and complete `inventory_urls` and which are left for the recollection; prescriptions withdrawn; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** inventory → collector → rules → targets fields → manners → prescriptions → tests → rj5 → regenerate views → gate → RESULT → push.
