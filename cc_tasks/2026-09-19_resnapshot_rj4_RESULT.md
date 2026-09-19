# RESULT: the report is re-snapshotted onto `scan_2026-09-10_rj4`; the guard walks the chain; every rank prints the leg it rests on; the 22 orphaned G1-D Findings are withdrawn on the log; the two tool READMEs have Document nodes

**Task:** `cc_tasks/2026-09-19_resnapshot_rj4.md`. At session start `ls cc_tasks/2026-09-19_resnapshot_rj4*` listed the base task alone (that listing was not written to a log). Before §3, at 2026-09-19T12:16:04Z, `ls cc_tasks/2026-09-19_resnapshot_rj4_ADDENDUM*.md` matched nothing (`logs/resnap_addendum_glob_pre_s3.log`).
**Session:** launched headless by the standing dispatcher from HEAD `354108a`.
**Framework layer served:** DN-005 §2.2 Tier M. The published state of the 16 bodies now matches the instrument: 17 product checks where 10 were.
**Spend:** zero model calls. **Network:** none beyond `git push`. Nothing was fetched and no host was contacted.

**Gate: green.** Tier `make gate-full` (its command, run directly so the log carries this task's name), detached and polled to `EXIT=`.
- **`make gate-full`:** 2674 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed, in 1475.05 s, `EXIT=0` (`logs/resnap_suite_3.log`). The three skips are the expected three: `test_dispatch_config.py:333` (dispatched session), `test_scan_harness.py:283` (E5), `assessment/tests/test_g1_preservation.py:337`. Two earlier full runs each failed one test, and both failures are in §4 premise 12 (`logs/resnap_suite.log`, `logs/resnap_suite_2.log`).
- **`seldon verify`:** all checks passed, replay skipped as expensive (its default). `EXIT=0` (`logs/resnap_seldon_verify.log`).
- **Protected paths:** `scripts/check_protected_resnapshot.sh` gives `PROTECTED PATHS OK`, `EXIT=0` (`logs/resnap_protected.log`).
- **Projection round-trip (DD-057):** 9 passed, 0 skipped, `EXIT=0` (`logs/resnap_roundtrip.log`).
- **Successor guard on the new snapshot:** `EXIT=0`. `_rj4` is the head of its chain, so there is no successor and no comparison, and the build does not refuse (`logs/resnap_snapshot_guard.log`).

---

## 0. The published numbers, before and after

Every value is from `docs/data/results_tagged.json` before this task (copied to `logs/resnap_before/`) and after it. The full line-by-line list is in `logs/resnap_published_diff.log`.

**Three tagged Results moved, as the task said they would.** No other value moved.

| metric | `_rj2` | `_rj4` |
|---|---|---|
| `scan_findings` | 739 | 1009 |
| `scan_l0_product_legs` | 10 | 17 |
| `scan_l0_product_legs_at_zero` | 5 | 11 |

**Unchanged.** The other 35 cycle-suffixed tags were renamed from `_rj2` to `_rj4` at identical values. The 18 tags that carry no snapshot suffix (frame, collection and crosswalk facts, plus the two `_rj1` A3 numbers in the movement section) are the same names at the same values.

**Two tags are new:** `scan_l0_product_g4_pass_2026-09-10_rj4` = 1 and `scan_l0_product_g4_applicable_n_2026-09-10_rj4` = 19. The product section now says that the SCF row holds the only pass on any check generation 12 added. In all, the report tags 58 Results, up from 56.

**Report fragments.**
- `matrix_tierA.md`, `matrix_tierC.md`, `requests_per_netloc.md` and `withdrawn_legs.md` are byte-identical.
- `matrix_product.md` gained the seven columns (161 cells). `rules_by_leg.md` gained the seven rules and D4's v3.
- `sources_per_check.md` gained two G4 rows (premise 8).
- All six published matrices (`docs/reports/scan_matrix_*_2026-09-10_rj4.*`) are byte-identical to what the previous task wrote. This task changed no matrix content, created no Observation and created no Finding.

**Prose.** I rewrote four sentences because the new cycle made them false; everything else is a tag rename.
- **`40_product.md`:** the zero-pass list now names all eleven checks. The G4 sentence is added.
- **`60_movement.md`:** "no row on the figure below is marked as a rule change" is false against the new comparison, because D4 v2 → v3 is now marked. "the previous judgement" became "the first re-judgement", since `_rj3` now sits between them.
- **`10_frame.md`:** names this task.
- **`80_appendix.md`:** "rules current on 2026-09-11" became 2026-09-18.

**Build.** `build_l0_report.py`: gate PASS, 0 fatal references, 0 unresolved tokens, 0 bare numerals. The version block's standing line is "No later judgement of this cycle's evidence is on the event log: the snapshot is the current judgement of record" (`logs/resnap_report_build_2.log`). The PDF has 15 pages (`logs/resnap_pdf_2.log`), and the site was rebuilt (`logs/resnap_site_2.log`).

## 1. The promotions

**The rule I applied.** It is DN-002 decision 3, as `scripts/publish_result_states.py` implements it, not DD-056 (premise 1). A Result moves to `verified` only on a fresh re-derivation that reproduces its value, and to `published` only after the commit that publishes the tree.

1. **Re-derivation.** `scripts/rederive_tagged_results.py` gave 58 tagged, 58 reproduced, 0 not re-derived, 0 disagreeing, `gate: PASS` (`state/rederive_tagged_2026-09-19.json`, `logs/resnap_rederive.log`).
2. **`verify`.** 40 Results went `proposed → verified`: the 36 `_rj4` successors of `_rj2` tags, the two `over_four_legs` counts, and the two G4 counts. The other 18 were already `published` and are counted as `already_beyond_target` (`logs/resnap_verify_states.log`).
3. **`publish`.** This ran after commit `f763563`, which publishes the tree: no document can name the commit that contains it, which is the reason `publish_l0` gave. The step moved 40 Results `verified → published`, each stamped `published_commit f763563c96da6b7e271ac9f787e2eb40f13ac394`. The other 18 were already at the target, and 0 were refused (`logs/resnap_publish_states.log`). `build_l0_site.py --only results_tagged` then rewrote those 40 `state` fields and nothing else (`logs/resnap_site_3.log`). `test_publication`, `test_snapshot_successor`, `test_resnapshot_rj4`, `test_mcp_server`, `test_report_figures_agree` and `test_report_pdf` were re-run after it: 179 passed, 0 skipped, `EXIT=0` (`logs/resnap_post_publish_tests.log`).
4. **The `_rj2` Results the report stopped quoting.** 36 `published` `_rj2` Results went to `stale`, each carrying `superseded_by` (its `_rj4` name), `superseded_reason` and `superseded_by_task`. 33 of them have the same value as their successor; 3 do not, the three in §0. 0 were left unmoved (`logs/resnap_supersede_rj2.log`). On `_2026-09-10_rj2` the graph now holds 41 `stale` (these 36, plus DD-066's 5) and 311 `proposed`; on `_2026-09-10_rj4` it holds 40 `published`, all at `f763563`, and 390 `proposed`.

**What was not promoted.** 390 `_rj4` Results stay `proposed`, as 532 of `_rj2`'s did. They are 131 of the 168 L0 Results (37 are tagged), 173 of the 174 cycle-family Results (`scan_findings` is tagged) and the 86 figure inputs. The report quotes none of them.

**Registered by this task** (each needed by a generator the re-snapshot runs):
- `scan_report --cycle scan_2026-09-10_rj4`: 174 cycle-family Results, `scan_findings` among them (`logs/resnap_scan_report.log`).
- `register_l0_report_results --cycle`: 2 Results (`logs/resnap_report_results.log`).
- `register_figure_results --cycle`: 86 new and 9 already at their value (`logs/resnap_figure_results.log`).
- `register_scan_figures --cycle`: 6 Figures and 342 links (`logs/resnap_register_figures.log`).
- The payload's DataFile, `scan_2026-09-10_rj4` (`logs/resnap_payload_datafile.log`).

## 2. The guard's walked chain (decision 3)

`snapshot_successor.successor_info` now walks `SUPERSEDES` to the head of the chain. `supersession_chain` is fatal on a cycle. The function reports `chain` and per-hop `hops`, and its three counts run snapshot → head over `SUPERSEDES*`.

**From the old snapshot** (`scripts/snapshot_successor.py --snapshot scan_2026-09-10_rj2`, `logs/resnap_guard_from_rj2.log`, exit 1 by design):

| hop | generation | pairs | verdict moves | reason-only |
|---|---|---|---|---|
| `_rj2` → `_rj3` | 3 | 739 | 0 | 3 |
| `_rj3` → `_rj4` | 4 | 717 | 2 | 8 |
| **`_rj2` → `_rj4`, transitive** | — | **717 of 739** | **2** | **11** |

- **The 22 without a successor** at the head are the G1-D Findings that DD-066 withdrew from `home` and Tier C surfaces.
- **The refusal.** It names 162 moves: 161 product cells, each `None` → a verdict, plus the rendered product fragment. It compared 0 tagged Results, because the report now tags `_rj4` names.
- **The line** reads "superseded … by `scan_2026-09-10_rj4`, generation 4 of this cycle (reached through `scan_2026-09-10_rj3`)".

**The pin** is `tests/test_snapshot_successor.py::test_the_old_one_hop_answer_would_have_missed_rj4`. One hop from `_rj2` lands on `_rj3` with `moved == 0`. The walked head moves 161 product cells, and the three Results differ exactly as §0 says. Before the change, the four chain tests failed against the one-hop code: 4 failed (`logs/resnap_d3_red.log`).

**Against the new snapshot**, the chain is `[scan_2026-09-10_rj4]` and has no hop. There is nothing to compare, so the guard reports no move and the build proceeds (premise 3).

## 3. The concentration sentence for each of the 13 scored bodies (decision 4)

`score.concentration` reverses one body's `pass` and `fail` rows on one leg at a time, holds every other body fixed, and re-ranks. Reversal keeps the denominator fixed, which deletion would not. The leg that moves the rank furthest is reported, with ties going to the framework's order.

**Where it is printed.**
- `score.py`: the grid, the body page and the sensitivity table.
- `--json`, as `concentration`.
- The MCP's `get_body`, as `score.concentration` and in `summary` (`logs/resnap_mcp_get_body.log`).
- The design page's step 10 says why.

On `scan_2026-09-10_rj4` (`logs/resnap_score.log`):

- DRSMSU ranks 1 of 13 (hierarchical), and it rests on one pass: 1 pass of 1 judged row on G4; were that leg's verdicts reversed it would rank 4.
- EIA ranks 2 of 13 (hierarchical), and it rests on one pass: 1 pass of 1 judged row on A10; were that leg's verdicts reversed it would rank 4.
- BEA ranks 3 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 2 judged rows on F4; were that leg's verdicts reversed it would rank 1.
- NCSES ranks 3 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 1 judged row on F4; were that leg's verdicts reversed it would rank 1.
- CENSUS ranks 5 of 13 (hierarchical), and it rests on one pass: 1 pass of 1 judged row on A10; were that leg's verdicts reversed it would rank 9.
- NCES ranks 5 of 13 (hierarchical), and it rests on one pass: 1 pass of 1 judged row on A10; were that leg's verdicts reversed it would rank 9.
- SAMHSACBHS ranks 7 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 1 judged row on F4; were that leg's verdicts reversed it would rank 1.
- NASS ranks 8 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 2 judged rows on F4; were that leg's verdicts reversed it would rank 2.
- SOI ranks 8 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 2 judged rows on F4; were that leg's verdicts reversed it would rank 2.
- BJS ranks 10 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 2 judged rows on F4; were that leg's verdicts reversed it would rank 2.
- ERS ranks 10 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 2 judged rows on F4; were that leg's verdicts reversed it would rank 2.
- NAHMSAPHIS ranks 10 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 1 judged row on F4; were that leg's verdicts reversed it would rank 2.
- NCHS ranks 13 of 13 (hierarchical), and the leg that would move it most is F4: 0 pass of 2 judged rows on F4; were that leg's verdicts reversed it would rank 2.

BLS, BTS and ORES are unscored and carry no sentence.

**What the list shows.** Every rank rests on a one-leg criterion, because under equal weights a one-leg criterion carries a whole criterion's weight. For four bodies it is a single pass: G4 for DRSMSU, A10 for EIA, CENSUS and NCES. For the other nine it is F4's fails; F4 is criterion F's only harness leg, and reversing it lifts any body to first or second.

## 4. Every premise this task file got wrong

1. **"Promoted per DD-056's rule."** DD-056 is the naming rule: a cycle-level name carries its cycle. Promotion is DN-002 decision 3: re-derive, then `verify`, then `publish`, and only for the Results the report quotes. I promoted the 40 tagged `_rj4` Results, 37 of them L0, not the 168. The other 131 L0 Results stay `proposed`, as `_rj2`'s untagged 532 do.
2. **"The `_rj2` ones they succeed are marked superseded."** The Result state machine (`seldon/domain/research.yaml`) has no `superseded` state; `published` goes only to `stale`. I followed `scripts/withdraw_g1d_results.py`: state `stale`, with `superseded_by`, `superseded_reason` and `superseded_by_task` on each artifact (`scripts/supersede_rj2_published_results.py`).
3. **"Against the new snapshot it must report `moved: 0`."** `_rj4` has no successor, so the guard makes no comparison and reports `comparison: null`. `moved: 0` exists only when there is something to compare. The meaningful check is from `_rj2`, where the walked chain reports 162 moves (§2).
4. **"The three tagged Results move (739 → 1009 …)."** Two of the three had a `_rj4` Result to move to (`scan_l0_product_legs*` were among the 168). The third, `scan_findings`, had never been registered for `_rj4`. Nor had two unchanged tags, `scan_a5_fail_offroster_sitemap` and `scan_refusal_consecutive_measurements`, nor the payload's own DataFile. I registered each with its own registrar (§1).
5. **The write set leaves out the report's figure.** `60_movement.md` embeds F5 for the snapshot cycle, and `tests/test_report_figures_agree.py` requires the figure and the prose to name one cycle. Drawing F5 for `_rj4` took five things:
   - a `figures.yaml` comparison entry, against `scan_2026-09-09_rj2`. Cycle 3's generation-10 judgement `_rj3` registered no Results, so it cannot be drawn. The entry marks D4 v2 → v3; A12 also changed, but it is a candidate with no F5 row, and marking it would put a mark in the caption that the figure does not draw;
   - the cycle-family and figure-input Results;
   - the SVGs;
   - Figure registration;
   - two code changes (premise 6).
6. **B5 is the first body leg, and three consumers assumed every matrix column has a per-surface rate.**
   - `figures.py` F1 crashed on `scan_b5_pass_rate`.
   - `register_figure_results.py` raised `KeyError`.
   - Three tests had the same assumption: two in `test_scan_figures.py` and one in `test_f5_membership.py`.
   - **The fix.** `figures.rated_legs(mx)` returns the columns that have a `per_leg` entry. F1 and F5 draw those, and `register_figure_results` and the tests read them. B5 is counted once per body on the product matrix and in the L0 family.
   - **The row test.** `test_every_l0_matrix_row_re_derives_from_the_graph` now expects a body leg's cell to cite the body's `host:` Finding, the one A12 cites.
   - **No earlier figure moved:** protected check §6.
7. **Latent defects found on the way, each fixed at its source:**
   - **`build_l0_matrices.snapshot_cycle` read `publication.yaml` from `OUT_DIR`.** The re-derivation gate redirects `OUT_DIR` to a temporary tree, so the gate crashed the first time it ran after the previous task wrote that function. The previous task never ran it. The function now reads the file from its fixed path.
   - **`publish_result_states.py verify` counted the 18 already-published, cycle-independent tags as `wrong_state` and exited 1.** Any re-snapshot hits this. A Result already further along the one legal path is now counted as `already_beyond_target`.
   - **`register_l0_report_results --cycle` would have minted `fss_scan_netlocs_contacted_2026-09-10_rj4`.** That is the socket count filed under a re-judgement's name, the defect `register_measured_collection_facts.py` already recorded for `_rj2`. It is now dropped for a re-judgement; the report quotes the measured cycle's name.
   - **`rederive_tagged_results.py` typed the snapshot as `scan_2026-09-10_rj2`.** It now reads `publication.yaml`.
8. **The report now quotes G4, so the appendix cites G4's two sources, and neither was citable.** `fcsm-19-01-…` and `statistical-policy-working-paper-46-…` both carried `(unspecified)` / `n.d.`. `scripts/backfill_g4_source_metadata.py` wrote two `metadata_corrected` events, with each value quoted from page 1 or 2 of the PDF on disk. `tests/test_report_traceability.py`'s pin gained G4, which is the alarm working as designed.
   - **Open.** Both G4 rows have an empty Locator cell: the indicator's evidence cell names no locator for either document.
9. **Decision 6 had a side effect the task did not mention.** `kg.manifest.add` runs DD-030's admission gate, which converted both READMEs to substrates and appended two `substrate_converted` events to `events/batch-024.jsonl`. Neither document enters an extraction queue, because the queue is epoch membership.
10. **Decision 5's shard.** The 22 overlays went onto the Findings' own shard, `events/cycle-scan_2026-09-10_rj3.jsonl`, by `publish.shard_for`, the rule every overlay of a cycle follows.
    - The 22 surfaces are 19 `home` surfaces (16 agencies and 3 Tier C) and 3 Tier C `machine` surfaces. DD-067 §3 counts these as "16 home and 6 Tier C".
    - **Projection.** 22 withdrawn, 0 unresolved. `current` went from 3,832 to 3,810. `findings_superseded` now counts the Findings that have a successor, not the Findings that are not current (`logs/resnap_projection_1.log`).
11. **Decision 4's "flip".** I read it as reversal: pass ↔ fail on one leg, for one body. Reversal asks the question in both directions, and it is the only reading that leaves the denominator alone.
12. **Pages the write set did not name, and the two failed full runs:**
    - **`docs/progress/`.** It is a view of the cycle of record (`tests/test_scan_run_2.py`), and full run 1 failed on its stale `_rj2` denominator. `scripts/framework_progress.py --cycle scan_2026-09-10_rj4` regenerated it. The regeneration also moved counts that had drifted from the framework record since 2026-09-11; no test compares the page to the record. Full run 2 then failed in `test_f5_membership.py`, which had no `_rj4` entitlement. I added it: B1, B2, B4, D2, D3 and G4 are blank on cycle 3's side only.
    - **Generated views.** `docs/design/mcp_over_the_graph.md` was regenerated by `mcp/airkg_doc.py`, and `docs/design/scoring_model.md` by `score.py --explain`.
13. **Test pins that named the old snapshot or the fixed ten columns:**
    - `test_mcp_server.py`: cycle of record. Its supersession test now expects no successor.
    - `test_report_figures_agree.py`: `REPORT_CYCLE`.
    - `test_rejudge_seven_legs.py`: two tests now read the current snapshot.
    - `test_publication.py`: the fixture reads the cycle's own product columns.
    - `test_snapshot_successor.py`: the standing tests accept "no successor" as the state it is.
    - `test_report_traceability.py`, `test_scan_figures.py` and `test_f5_membership.py`: premises 6 and 8.
14. **The full projection took 52 minutes** (07:07 → about 07:59 local), almost all of it the KG replay. Recent tasks projected only the scan or framework layer. That is informational, not a defect.

## 5. Gate

**Tier:** `make gate-full`'s command (`python -m pytest tests/ assessment/ -q -rs`), detached and polled.

| check | result | log |
|---|---|---|
| tests first, decision 3 | 4 failed against the one-hop code, then passed | `logs/resnap_d3_red.log` |
| tests first, decisions 4–6 | 5 failed, 5 passed, 1 skipped before the writers ran; green after | `logs/resnap_d456_red.log`, `logs/resnap_d4_tests.log` |
| withdrawal overlay | 22 selected, 22 written, `EXIT=0` | `logs/resnap_withdraw.log` |
| manifest events | 2 emitted, `EXIT=0` | `logs/resnap_manifest_adds.log` |
| projection (all three layers) | `EXIT=0`: documents 265, findings 11,346, current 3,810, withdrawn 22, unresolved 0; framework 228 nodes, 389 edges | `logs/resnap_projection_1.log` |
| prescription re-tag | writer event `4188d6f7…` on `events/batch-033_framework.jsonl`; 63 Actions changed, 0 added, 0 removed | `logs/resnap_tag_prescriptions.log` |
| framework projection | `EXIT=0` | `logs/resnap_framework_projection.log` |
| re-derivation of tagged Results | 58 of 58 reproduce, PASS | `logs/resnap_rederive.log` |
| report / PDF / site | each `EXIT=0` | `logs/resnap_report_build_2.log`, `logs/resnap_pdf_2.log`, `logs/resnap_site_2.log` |
| full run 1 | 1 failed (`test_scan_run_2.py`, premise 12), 2671 passed, 3 skipped, 12 xfailed, 0 deselected | `logs/resnap_suite.log` |
| full run 2 | 1 failed (`test_f5_membership.py`, premise 12), 2671 passed, 3 skipped, 12 xfailed, 0 deselected | `logs/resnap_suite_2.log` |
| **full run 3** | **2674 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed, in 1475.05 s, `EXIT=0`** | `logs/resnap_suite_3.log` |
| `seldon verify` | all checks passed, `EXIT=0` | `logs/resnap_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`; 4 shards appended with exactly the expected types, 0 rewritten, 0 new; ledger append-only by 2 | `logs/resnap_protected.log` |
| round-trip (DD-057) | 9 passed, 0 skipped | `logs/resnap_roundtrip.log` |
| after the publish commit | 40 published, 36 `_rj2` stale; `results_tagged.json` changed only in 40 `state` fields; 179 passed, 0 skipped | `logs/resnap_publish_states.log`, `logs/resnap_supersede_rj2.log`, `logs/resnap_post_publish_tests.log` |
| guard on `_rj4` | no successor, `EXIT=0` | `logs/resnap_snapshot_guard.log` |
| graph cross-check | 1,009 `_rj4` Findings current; 22 withdrawn, all `_rj3` G1-D; both READMEs are Documents at the ledger's sha256; Actions D2 13, B2/B4/B5/D3 12, B1/G4 11 | `logs/resnap_graph_check.log` |

**Open, for the next OODA:**
1. **Every rank rests on a one-leg criterion (§3).** Nine bodies' ranks turn on F4, and four turn on one pass. Weighting is the operator's (scoring task decision 8), and this is the evidence for that decision.
2. **G4's two appendix rows have no locator (premise 8).** The indicator's evidence cell should name one for each document.
3. **Cycle 3's generation-10 judgement has no registered Results**, so F5 compares against generation 9 and marks D4 as changed (premise 5).
4. **`docs/progress/` can drift from the framework record without any test noticing (premise 12).**

**Commits.** `f763563` carries the whole tree, the code, the shards and the tests, gated by full run 3. The commit that carries this RESULT follows it and adds three things: the 40 `state` fields in `docs/data/results_tagged.json`, the Seldon state events for the promotions and the stale moves, and this file.
