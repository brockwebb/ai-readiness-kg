# RESULT: the recollection ran; the cycle of record is the composite `scan_2026-10-06_composite_b`, with A2 and D1 withheld for two rule defects the new declarations exposed

**Task:** `cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` with `_ADDENDUM_01.md` (an amendment, read before any step). Operator-launched, headless. **Layer:** DN-005 §2.2, measurement. **Spend:** no harness model call; about 0.7M tokens in this session plus four read-only explore subagents, all `claude-opus-5-5`. **Network:** the manners layer only (identified UA, robots-first, 1 req/s): 82 requests for the declarations and 2,074 for the cycle (§4). The STOP file is covered in the last line.

**Gate: green.** `make gate-full`'s command, run detached in its own session on `4094c9c0`: 3099 passed, 4 skipped, 41 xfailed, 0 deselected, 0 failed, 3140.64 s, `EXIT=0` (`logs/arc_gate_full_2.log`). **Skips:** three are the standing ones (`test_kg_questions.py:115`, `test_scan_harness.py:290`, `test_g1_preservation.py:337`). The fourth, `test_dispatch_config.py:373`, is the dispatcher's quiet state: STOP was present and the dispatcher's observation line was uncommitted. **The first run (`arc_gate_full_1.log`) died at 35% with no `EXIT` line,** last written 02:17:51Z, while a Desktop session committed `4094c9c0` (DN-013) in this checkout. `test_invariants.py`, where it stopped, passes alone. The cause is not established. **Fast tier before the first commit:** 3070 passed, 4 skipped, 41 xfailed, 29 deselected, 0 failed (`arc_fast_3.log`). **`seldon verify`:** all checks passed, `EXIT=0` (`arc_seldon_verify_2.log`). **Protected paths:** `scripts/check_protected_absence_recollection.sh` against `b2b2c9b6` gives `PROTECTED PATHS: PASS`, `EXIT=0` (`arc_protected_2.log`). It covers: `rules/` and `collectors/` byte-identical; `score.py` untouched; `params.yaml` moved only in `cycle.name` and added only `b3_methodology.max_followed`; `targets.yaml` moved only in `declared_locations`; no prior payload, matrix or task file changed; shards and the Seldon store only grow.

## 1. Declarations (decision 1, amendment 1): resolved per field per body
`scripts/resolve_declared_locations.py` (manners layer, per-URL checkpoint log `state/declaration_fetches_2026-10-06.jsonl`, bodies kept in `corpus/evidence/frame/`) read 45 pages. Each declaration cites its page, digest and anchor. A location that was not found is ND (`not_declared`: the body's pages were searched and do not publish it) or UR (`unreadable`: the page that would carry it refused this client). Both name the pages searched, and the validator requires them. Both stay `error` (DN-012 d1).

| body | api_base | api terms | changelog | department inventory | catalog.data.gov org |
|---|---|---|---|---|---|
| BEA | UR (robots) | n/a | ND | declared | commerce |
| BJS | declared | ND | declared (1) | declared | doj |
| BLS | UR (403) | n/a | UR | declared (DOL) | dol-bls |
| BTS | UR (403) | n/a | UR | UR | dot |
| CENSUS | declared | declared | declared (1) | declared | census |
| DRSMSU | ND | n/a | ND | own host | fed-reserve |
| EIA | declared | declared | declared (2) | declared | energy |
| ERS | ND | n/a | ND | declared | usda |
| NAHMSAPHIS | ND | n/a | ND | declared | usda |
| NASS | declared | UR (robots) | declared (1) | declared | usda |
| NCES | ND | n/a | declared (1) | declared | ed |
| NCHS | ND | n/a | ND | declared | hhs |
| NCSES | ND | n/a | declared (2) | declared | nsf |
| ORES | UR (403) | n/a | UR | own host | ssa |
| SAMHSACBHS | ND | n/a | ND | declared | hhs |
| SOI | ND | n/a | declared (1) | declared | treasury |

## 2. Collection, judgement, composite, views (decisions 2–4)
- **`scan_2026-10-06_recollect`.** `run.py --legs` (new; `scope: legs`) over the twelve generation-14 legs, on the 16 bodies' 46 surfaces. The 3 Tier C hosts carry none of them and were not contacted. B3 now follows every distinct methodology link, up to `max_followed: 25` (amendment 2, `runner.py`). Controls PASS, 552 Findings, 0 `unknown`.
- **Re-derivation and publication.** The cycle re-derives 841 of 841. The first gate minted 16 B5 Findings the cycle never judged, so `rederive.py` now judges body legs only on `legs_collected`. Published with 493 bodies promoted and projected.
- **The judgement exposed two false passes on the new declarations.** The task freezes rules and collectors, so neither is fixed here. `RULE-D1-v4` matches licence tokens as substrings of the terms page's HTML. `CC0` matched a script hash on census.gov, and `MIT` matched "permit" and "Limit" on eia.gov; neither page states a licence. That gives 7 false passes. `v2clauses.api_declarations` counts any JSON object as an OpenAPI description, so `api.census.gov/data`, a `dcat:Catalog`, passed A2 on 4 surfaces.
- **The composite (`scan.composite`, `scripts/build_composite_cycle.py`).** `_composite_b` takes ten legs from the recollection, and A2, D1 and every other leg from `scan_2026-09-10_rj5`. The withholding and its reasons are on `composed_of`; both cycle ids are on every matrix and in the report's frame and provenance lines. Legs are withheld whole, never cell by cell. The first declaration took all twelve legs and was rejected before publication. Its 168 Results are `rejected`; its payload and matrices are in `state/composite_rejected_2026-10-06/`.
- **Views.** Matrices, report and PDF, site, figures, brief pack, evidence map, catalog, progress page, `scoring_model.md` and the MCP doc were regenerated, and every `--check` passes (`arc_views_9.log`). Measured write-back: A1, A9, B1, B4, D3, D4, F4 and G4 return to `measured` (21/3/25). Tagged Results: 66 of 66 reproduce (`state/rederive_tagged_2026-10-07_final.json`). 49 are published at `330de7b3`; 39 rj5 Results are `stale` with `superseded_by`; rj5's D4 pass and applicable_n are withdrawn.

## 3. Verdicts on the 46 surfaces, rj5 → recollection (pass/fail/error), and the named cases
A1 0/1/45 → 6/1/39 · A2 0/0/46 → 4*/3/39 · A3 7/1/38 → 14/1/31 · A9 0/0/46 → 4/3/39 · B1 0/1/45 → 0/13/33 · B3 5/33/8 → 5/34/7 · B4, D3 0/1/45 and D4, G4 1/0/45 → each 0/14/32 · D1 0/0/46 → 7*/0/39 · F4 0/0/46 → 0/15/31. An asterisk marks a withheld leg. Per body and per surface, with every reason: `docs/research/2026-10-06_recollection_delta.md`.
- **Census ACS A2** went rj4 `fail`, rj5 `error`, recollection `pass` (the A2 defect). The composite shows rj5's `error`.
- **The 28 rj4 D4 "no catalog" rows** are now 12 `fail` (every declared inventory read, none names the product) and 16 `error`. The errors are the department inventories at `www.commerce.gov`, `www.usda.gov`, `www.ed.gov` and `hhs.gov`, each answering 403 to robots.txt and to `/data.json`, plus the bodies that refuse this client.
- **The 40 rows per leg rj5 moved on no declaration:** A9 is now 33 `error`, 3 `fail`, 4 `pass`; D1 is 33 `error`, 7 `pass`*; F4 is 25 `error`, 15 `fail`, each `fail` a changelog page for people at a declared location.
- **DRSMSU's SCF D4** went `pass` → `fail` because the host changed: record `FRBCNA35` now carries `landingPage` as an object.
- **Product legs unmeasured on every declared surface:** the rules task left five (A1, A2, A9, D1, F4). Two remain, A2 and D1, and both are withheld. The recollection itself has none.

## 4. Requests (manners accounting)
**Declarations:** 82 requests over 21 hosts (`state/declaration_fetch_runs_2026-10-06.jsonl`). **Cycle:** 2,074 requests over 42 netlocs. The largest are `www.nass.usda.gov` 193, `www.census.gov` 189, `www.ers.usda.gov` 185 and `www.cdc.gov` 156. Off every roster site, 57 requests went only to hosts a body declared, on the leg that reads them: `api.ojp.gov` 7, `www.usda.gov` 11, `www.commerce.gov` 9, `hhs.gov` 5, `www.hhs.gov` 3, `www.dol.gov` 3, `www.ed.gov` 3, and `www.energy.gov`, `www.justice.gov`, `www.nsf.gov`, `www.treasury.gov` 4 each. `tests/test_recollection_cycle.py` asserts this from the payload, together with robots-first room on every netloc.

## 5. Premises wrong (the task's and mine)
1. **catalog.data.gov's organization page lists no harvest source** since its redesign, and `/harvest_source/<id>` is 404. Organizations were matched by name from its list. BLS's department was read from DOL's records and confirmed on `www.dol.gov`; BTS's could not be read.
2. **The scoring task already ran (`1be1d289`).** Holding the score views at rj5 would print two cycles of record (DN-012 d7), so they were regenerated through the unchanged `score.py`.
3. **"Every collector byte-identical" conflicts with amendment 2.** The B3 change is in `runner.py`; `collectors/` is untouched.
4. **Outside the write set, so a composite can be read:** `run.py`, `rederive.py`, `declarations.py`, the new `scan/composite.py`; eleven readers: `build_l0_matrices`, `scan_report`, `register_figure_results`, `build_l0_site`, `build_evidence_map`, `build_figures`, `snapshot_successor`, `rederive_tagged_results`, the two `exercise_*` scripts and `mcp/airkg_tools`; ten test pins; the `test_report_pdf` fixture now splits a footer number that pypdf glued to a table cell.
5. **Two rule defects bar A2 and D1** (§2). Separately, A3's "unfiltered file" branch passes HTML pages, `https://www.bea.gov/` among them. That is already published in rj5 and is not addressed here.
6. **Section 15:** the scan runner is not checkpointed (pre-existing; a killed cycle reruns under a new name). The resolver is checkpointed.
7. **Mine:** `https://www.transportation.gov/` was fetched without being read from any page; it answered 403, and the entry says so. The 68-tag gate report used to publish G4's pair was deleted; its outcome is in `arc_verify_states_2.log` and `arc_publish_states_2.log`. `state/rederive_tagged_2026-10-07.json` was overwritten, then restored from `330de7b3`.

**Next:** fix A2 (require OpenAPI/Swagger keys) and D1 (tokens matched on visible text at word boundaries), re-judge `scan_2026-10-06_recollect` as `_rj1`, and declare a composite that takes A2 and D1.
**Logs:** `logs/arc_collect.log`, `arc_rederive_2.log`, `arc_publish.log`, `arc_projection.log`, `arc_composite_b.log`, `arc_matrices_b.log`, `arc_registrations{,_2}.log`, `arc_writebacks.log`, `arc_reject_composite_results.log`, `arc_views_9.log`, `arc_rederive_tagged_final.log`, `arc_publish_states{,_2}.log`, `arc_supersede_rj5{,_2}.log`, `arc_withdraw_d4_rj5.log`, `arc_fast_3.log`, `arc_gate_full_{1,2}.log`, `arc_seldon_verify_2.log`, `arc_protected_2.log`, `arc_cc_complete.log`.
**STOP file:** `.seldon/DISPATCH_STOP` appeared 2026-10-06T16:57:17Z (the operator's, for this launch, amendment 4), was rewritten 2026-10-07T02:19:30Z by a Desktop session with its removal conditions (this RESULT exists, `2f302398` completed on the graph, a clean tree), and was removed by this session at 2026-10-07T03:33:41Z, after `seldon cc complete` and immediately before the commit that cleans the tree.
