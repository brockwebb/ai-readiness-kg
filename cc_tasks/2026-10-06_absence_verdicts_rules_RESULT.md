# RESULT: absence verdicts over a partial search are `error`, naming the remainder; `scan_2026-09-10_rj5` is the cycle of record

**Task:** `cc_tasks/2026-10-06_absence_verdicts_rules.md` (DN-012 d1–d3; audit C-01, C-04, C-14). No addendum existed at start or before rj5 (`logs/avr_addendum_glob_pre_rj5.log`). Launched headless by the dispatcher from `0b86e070`. **Layer:** DN-005 §2.2, measurement. **Network:** none beyond `git push`; nothing was fetched. **Spend:** no harness model call; this session used about 0.74M tokens under `claude-opus-5-5`.

**Gate: green.** The tier is `make gate-full`'s command, run detached on the final tree `31f8fd66`.
- **Full suite:** 3052 passed, 4 skipped, 41 xfailed, 0 deselected, 0 failed, 2557.52 s, `EXIT=0` (`logs/avr_gate_full_2.log`).
  - Three skips are the standing ones.
  - The fourth is new: `test_kg_questions.py:115`, "corpus epoch moved under the stored answers". The epoch hashes the framework record, which this task rewrote. The stored answers stay the stored epoch's, and the script itself says a re-run is a new task.
  - The first full run had 6 failed, all view drift from the commit sequence (`logs/avr_gate_full_1.log`).
- **`seldon verify`:** all checks passed, `EXIT=0` (`logs/avr_seldon_verify_3.log`). Run 2 warned on three Results I had marked stale without the withdrawal fields (§4).
- **Protected paths:** `scripts/check_protected_absence_verdicts.sh` against `0b86e070` gives `PROTECTED PATHS: PASS`, `EXIT=0` (`logs/avr_protected_3.log`). It covers: every shipped rule module byte-identical; every pre-existing `params.yaml` value unchanged; `score.py` untouched; no prior payload, matrix or task file moved; shards and the Seldon store append-only.

## 1. Inventory and rules
`docs/research/2026-10-06_absence_rules_inventory.md` lists 12 legs whose `fail` asserts absence over a partial search.
- **The three the audit named:** A1, A3 (C-01), A2 (C-14), and D4 with its consumers B1, B4, D3, G4 (C-04).
- **Four more the inventory found:** A9 (documented API base), B3 (only the first methodology link was followed), D1 (3 of 7 terms paths, and "the API's terms endpoint" never located) and F4 (guessed changelog paths).
- **Generation 14:** `RULE-A1-v5`, `A2-v4`, `A3-v7`, `A9-v2`, `B1-v3`, `B3-v4`, `B4-v2`, `D1-v4`, `D3-v2`, `D4-v4`, `F4-v4`, `G4-v2`. Shared logic is in `rules/_scope.py`; every predecessor is still in `REGISTRY`.
- **The collector (`links.py` 0.2.0)** ranks on-host candidates before the cap, using archive or data extension first, then a `download`/`data` token, then document order. Every candidate past the cap is recorded as `unprobed_over_cap`, a new class that is BLIND and not requested. Each page carries `link_candidates` (on-host, probed, unprobed, cap).
- **Controls:** E5 still PASSes on all 11 fixtures with no table edit, because each fixture declares the locations it serves (`params.declarations.control_fixture`).

## 2. `scan_2026-09-10_rj5`, judged with no fetch
- **Moves:** 1,009 Findings and 402 moves, every one `fail` → `error`. The 457 Findings on unchanged legs are identical but for their ids, and the payload re-derives byte for byte (`logs/avr_rj5.log`, `state/rejudgement_diff_2026-10-06.json`).
- **Graph:** 1,009 current, 1,009 `SUPERSEDES` into rj4, and 0 rj4 Findings current (`logs/avr_graph_check.log`).
- **Per leg:** A1 37, A2 40, A3 20, A9 40, B1 36, B3 1, B4 37, D1 40, D3 37, D4 37, F4 40, G4 37.
- **Per body:** BEA 40, BJS 33, CENSUS 44, DRSMSU 17, EIA 27, ERS 44, NAHMSAPHIS 22, NASS 40, NCES 20, NCHS 39, NCSES 33, SAMHSACBHS 13, SOI 30. BLS, BTS and ORES had 0, because they were already `error`.
- **What remains `fail` on those legs:** A1 and A3 on `home:www.cdc.gov` (the served page carries no on-host link); B1, B4 and D3 on the SCF record found in the Fed catalog; 33 B3.
- **ACS flagship:** A1/A3 "25 of 115 on-host links probed, 90 unprobed, cap 25"; A2 "documented API base declared and not probed: https://api.census.gov/data"; D4 "declared inventory not observed: https://www.commerce.gov/data.json".
- **Views regenerated from rj5:** snapshot, matrices, report, PDF, site, brief pack, evidence map, figures, catalog, progress page, the scoring page, and the record's rule ids and prescription values. Results: 61 of 61 tagged reproduce, 41 published at `ca30546d`; 37 rj4 Results are stale with `superseded_by`, and A1's three are withdrawn.

## 3. Declarations (`targets.yaml` `declared_locations`, each entry with the page it was read from)
- **`api_base` declared:** CENSUS (`https://api.census.gov/data`, from `docs/data/sources_per_check.json:237`) and NASS (`https://quickstats.nass.usda.gov/api`, linked "API" from its home page in `state/scan_preflight_2026-09.json`).
- **Left to the recollection:** `api_base` for the other 14 bodies.
- **Department inventory declared for 14 bodies.** For 12 it was read off the body's own retained page linking the department home; for DRSMSU and ORES the department publishes on the roster host itself.
- **Left to the recollection:** the department for BLS and BTS (none written here; their pages 403'd on every cycle) and the catalog.data.gov organization for all 16 (no slug written anywhere). So no body's `inventory_urls` is complete.

## 4. Prescriptions
- **Withdrawn by verdict:** `bodies_failing_now` fell to 0 on A1, A2, A3, A9, D1, D4, F4 and G4, and to 1 on B1, B4 and D3 (B3 10 → 9). No body is now shown A2's or D4's actions. CENSUS page G lists neither "Expose the product through an API" nor "Publish a data.json inventory on the host".
- **Withdrawn by declaration:** `act:a2-expose-an-api-and-publish-its-description` carries `withdrawn_when_declared: api_base`, and `prescriptions.applicable` (CLI and MCP) drops it for a declaring body. D4's is withdrawn by construction, because v4 fails only after every declared inventory was observed.
- **Prescribes nothing:** no generation-14 remainder sentence carries an `OUTCOMES` fragment (tested). D4's `no_catalog` fragment now names the inventories searched.
- **One exception.** The 37 B1 `error` reasons still quote the markup half's sentence ("no `variableMeasured`"), as `RULE-B1-v2` did. No view prescribes from a reason fragment, since actions follow failing legs only, so nothing is shown from it.

## 5. Premises the task file got wrong (and my own)
1. **"Five" consuming legs** are four: B1, B4, D3, G4. The audit's 5 counts D4 itself.
2. **`targets.yaml` holds the 14-agency cycle-1 roster**, without DRSMSU, NAHMSAPHIS or SAMHSACBHS. The fields went under a new `declared_locations` key, keyed by frame body code. The row's `department` is a name, not a host.
3. **`tag_prescriptions.py` is in `scripts/`**, not in the harness directory.
4. **Writes outside the stated write set.** The recollection holds every collector byte-identical, so following declarations had to land here: `runner.py` (A2/A9/D4/D1/F4), `dcat.py`, `run.py`, `reread.py` (scheme 2), `rederive.py`, `errors.py` and `declarations.py`. The rj5 n = 0 legs also broke three view tools, fixed in `build_l0_matrices`, `register_figure_results` and `figures.py`. `rederive_tagged_results`, the supersede script and the Q4 claim in `build_evidence_map` were generalised. Many test pins followed the snapshot.
5. **`api.census.gov` is on-site for census.gov** (DD-063), so `manners` never refused it; admission matters for off-site declarations. The test uses a synthetic one.
6. **Two fields added that DN-012 d3 does not name: `api_base.terms_url` and `changelog_urls`.** spec:D1 and spec:F4 name those places. Neither is populated, so every D1/F4 absence is `error` until declared.
7. **The flips are wider than "where truncated or undeclared".** Every body has an unresolved inventory and 14 have no API base, so every A2, A9, D1, F4 and D4-family absence is `error`. Five product legs are now unmeasured on all 23 declared surfaces.
8. **`score.py` was protected here**, but its prescription join does not apply `withdrawn_when_declared`. That falls to the scoring task. Under rj5 no body fails A2, so nothing shows it today.
9. **Recollection premise:** the 3 Tier C hosts carry only `tier0.legs`, so "A1/A2/A3/D4 on the three reference hosts" is not in the frame.

## 6. Logs
`logs/avr_rj5.log`, `avr_publish.log`, `avr_projection.log` (`EXIT=0`, 12,355 Findings, 0 unresolved), `avr_matrices_2.log`, `avr_registrations_3.log`, `avr_writebacks.log`, `avr_views_7.log`, `avr_rederive_tagged.log`, `avr_publish_states.log`, `avr_supersede_rj4.log`, `avr_withdraw_a1_rj4_fix.log`, `avr_gate_full_2.log`, `avr_seldon_verify_3.log`, `avr_protected_3.log`.
