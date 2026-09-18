# RESULT: `scan_2026-09-10_rj4` is published. The seven new legs, plus D4 under v3, are judged over cycle 4's retained evidence, with no host contacted; the snapshot stays `_rj2`, and a re-snapshot looks owed

**Task:** `cc_tasks/2026-09-18_rejudge_seven_legs.md`. I globbed `2026-09-18_rejudge_seven_legs_ADDENDUM*.md` before starting and again before §3, at 14:28:55Z. Both globs found nothing (`logs/rj7_addendum_glob_start.log`, `logs/rj7_addendum_glob_pre_s3.log`).
**Session:** launched headless by the standing dispatcher from HEAD `a1eb586`. It ran after `2026-09-18_scoring_levels.md` (`4d52fe8`), as the SEQUENCING line requires.
**Framework layer served:** DN-005 §2.2, Tier M. On the 16 bodies, 23 legs are now judged where 16 were, and 21 of the 23 adopted harness legs are scored where 14 were (§4).
**Spend:** zero model calls. **Network:** none beyond `git push`. Every Observation judged here was made on 2026-09-10. No byte was fetched and no Observation was created.

**Gate: green.** The tier is `make gate-full`, and `make gate-task` was also run, before it (§6).
- **`make gate-full`:** 2616 passed, 3 skipped, 12 xfailed, 0 deselected, in 1458.32 s. `EXIT=0`.
- **`make gate-task`:** fast tier 2590 passed, 3 skipped, 12 xfailed, 26 deselected, in 557.18 s. Re-derivation 23 passed, 0 skipped, 25 deselected, in 11.36 s. `EXIT=0`.
- **`seldon verify`:** all checks passed. `EXIT=0`.
- **Protected paths:** `PROTECTED PATHS OK`. `EXIT=0`.
- **The snapshot-successor guard:** `EXIT=0`. It compares against `_rj3` only (§3).

**In one paragraph.** One re-judgement covers the whole current registry: `scan_2026-09-10_rj4`, generation 4 of cycle 4.
- **What was judged.** 1,009 Findings on 23 legs, against the Observations of `scan_2026-09-10`.
- **What was written.** 1,009 `finding_derived` events and 717 `finding_supersedes` events went to `events/cycle-scan_2026-09-10_rj4.jsonl`. No Observation event was written. 292 Findings are unpaired, because they are on the seven legs `_rj3` never judged.
- **Projection.** Done, with 0 unresolved supersessions.
- **Artifacts.** Three matrices were written. 168 L0 Results were registered as `proposed`.
- **What did not move.** The report, its PDF, `publication.yaml`, the site's published Results and `framework/` are byte-identical.

**Two things the task did not foresee made this possible, and each is recorded (DD-067):**
- **Retained bodies were re-read.** D4's `membership` and `dcat_fields` blocks and A4's `content_signal` block were re-read from sha256-checked retained bodies, using the collector's own functions. Without this, every one of the seven legs and D4-v3 would have returned `error`.
- **The per-surface legs come from the frame.** Without this, D2 would have landed on the Tier C reference hosts.

---

## 0. The control gate (§1, a hard stop): PASS

- **Where the gate ran.** It ran through `rederive.control_gate_record`, which is `run.run_controls` with a throwaway evidence root. That is the path generations 9 and 10 used. The result is recorded on the payload as `control_gate`. §5 premise 3 explains why I did not use `run.py --controls-only` itself.
- **Result:**
  > CONTROL GATE: PASS — both control fixtures fired and every rule returned its expected verdict; ordering not asserted (no surface was scanned in this cycle)
  > fixtures: ['body_two_products', 'body_two_products_split', 'fails_all', 'invalid_route_unobserved', 'passes_all', 'refuses_identified_client', 'resets_connection', 'resets_links_only', 'robots_404_html', 'robots_forbids_product', 'sitemap_on_sibling'] — unexpected: []
- **Scope.** 11 fixtures, 0 unexpected, loopback only. The payload asserts `requests_total: 0` and `observations_detail: []`.
- **`refuse_clobber`.** I applied `run.refuse_clobber` to `state/scan_2026-09-10_rj4.json`, and the script also refuses if that file exists at all. It did not exist.
- **Logs.** `logs/rj7_rejudge.log` (`EXIT=0`). The dry run before it wrote nothing: `logs/rj7_dryrun.log`.

## 1. The seven legs as published (`scan_2026-09-10_rj4`)

**Coverage.** Surface legs are counted over the 46 Tier A non-well-known surfaces. B5 is counted over the 16 bodies. No leg is on a Tier C row.

| leg | rule | pass | fail | n/a | error |
|---|---|---|---|---|---|
| B1 | `RULE-B1-v2` | 0 | 37 | 0 | 9 |
| B2 | `RULE-B2-v1` | 0 | 38 | 0 | 8 |
| B4 | `RULE-B4-v1` | 0 | 38 | 0 | 8 |
| B5 | `RULE-B5-v1` | 0 | 12 | 0 | 4 |
| D2 | `RULE-D2-v1` | 0 | 40 | 0 | 6 |
| D3 | `RULE-D3-v1` | 0 | 38 | 0 | 8 |
| G4 | `RULE-G4-v1` | 1 | 37 | 0 | 8 |

**Agreement with the offline exercises.** These are exactly the distributions the exercises reported:
- `2026-09-18_schema_field_rules_RESULT.md` §1 for B1, B2, B5 and D2;
- `2026-09-18_dcat_field_rules_RESULT.md` §1 for B4 and D3;
- `2026-09-18_manners_status_and_b5_control_RESULT.md` §2 for G4 under DCAT-US field membership.

Here they were reached through the published path. `tests/test_rejudge_seven_legs.py::test_the_seven_legs_as_published` pins them.

**The one pass.** G4's only pass is `flagship:www.federalreserve.gov/econres/scfindex.htm`, the one product whose catalog record carries a well-formed `bureauCode`/`programCode`.

**Live graph cross-check** (`logs/rj7_graph_check.log`):
- `MATCH (f:Finding {cycle:'scan_2026-09-10_rj4'})-[:RULED_BY]->(r:Rule)` returns these 15 rows row for row, and 1,009 rj4 Findings, all `current`.
- 717 of them carry `SUPERSEDES` into `scan_2026-09-10_rj3`.

**In the product matrix** (23 declared surfaces; B5 counted once per body):

| leg | fail | error | applicable n |
|---|---|---|---|
| B1 | 18 | 5 | 18 |
| B2 | 19 | 4 | 19 |
| B4 | 19 | 4 | 19 |
| D2 | 20 | 3 | 20 |
| D3 | 19 | 4 | 19 |
| G4 | 18 (1 pass) | 4 | 19 |
| B5 (bodies) | 12 | 4 | 12 |

**What the re-read did.** It filled `membership` and `dcat_fields` on the 10 D4 Observations that served a catalog, and `content_signal` on the 44 A4 Observations that served a robots.txt. `logs/rj7_rejudge.log` records this, as does the payload's `observations_reread`.

**D4 under `RULE-D4-v3`.** Decision 1 asked which D4 verdicts moved and why.
- **Before and after.**
  - `_rj2` and `_rj3`: 3 pass, 35 fail, 8 error.
  - `_rj4`: 1 pass, 37 fail, 8 error.
- **The two moves.** Exactly two verdicts moved:
  - `home:www.bea.gov`: `RULE-D4-v2 pass` → `RULE-D4-v3 fail`;
  - `home:www.census.gov`: `RULE-D4-v2 pass` → `RULE-D4-v3 fail`.
- **Why they moved.** These are the two host home pages that "owned" 14 and 1,635 catalog records by substring. By DCAT-US's own URL fields they own none (`2026-09-18_manners_status_and_b5_control_RESULT.md` §2).
- **Where they show.** Neither move appears in any matrix. D4 is a product leg, so the product matrix reads flagships, and the flagship D4 cells are unchanged (1 pass, 18 fail, 4 error).

## 2. The unchanged-leg identity check

**Decision 1 cannot hold as written.** It asked that, where a leg's rule has not changed since `_rj2`, the Finding ids be byte-identical to `_rj2`'s. They cannot be:
- `finding_id` hashes `params_hash`, and `params_hash` hashes the whole `params.yaml` (`model.params_hash`).
- `params.yaml` has moved on every generation since:
  - `_rj2`: `d3499218…`
  - `_rj3`: `845aa6ab…`
  - now: `0ef2e016…`
- So every Finding is re-identified by construction, on every leg.

**What was checked instead.** `scripts/rejudge_seven_legs.py::identity` checks the property that can hold, and a failure stops the write. It is stated in DD-067 §4 and asserted in `tests/test_rejudge_seven_legs.py::test_every_unchanged_leg_is_the_predecessors_judgement`. Every Finding of an unchanged leg must equal its predecessor's in every field except `finding_id` and `params_hash`.

**Against `_rj3`, the predecessor:**
- **Unchanged legs.** 15 legs are unchanged: A1, A2, A3, A4, A5, A6, A8, A9, A10, A11-declared, A12, B3, D1, F4 and G1-D.
- **Identical.** 671 of 671 are identical apart from the two identity fields, and 0 differ.
- **New surfaces.** No unchanged leg judges a surface that `_rj3` did not judge.
- **Cells dropped (22).** 22 cells are in `_rj3` and not here. All 22 are G1-D: 16 `home` surfaces and 6 Tier C surfaces. The frame no longer gives G1-D to those surfaces (DD-066). The frame restriction (§5 premise 5) is what dropped them. They are not re-judged.
- **Changed legs.** The only changed leg is D4 (v2 → v3), with the 2 moves in §1.

**Against `_rj2`, the snapshot:**
- **Identical.** 650 of 652 are identical on 14 unchanged legs.
- **The 2 that differ.** Both are A10 `error` Findings on the two NASS flagships. Only the `reason` sentence differs, and that is generation 10's `reason_text: 2` correction, already in `_rj3`.
- **Changed legs.** Two legs changed: A12 (v2 → v3) and D4.

**Re-derivation (DD-041).**
- `rederive.rederive(_rj4)` gives 1,009 recorded, 1,009 re-derived, 0 missing, 0 unexpected, 0 mismatched.
- `_rj4` joins `PRIOR_CYCLES` at 1,009, and the rolling fast-tier window `RECENT_CYCLES` moves to `("scan_2026-09-10_rj4", "scan_2026-09-10")`.
- All 23 stored payloads re-derive byte-identically (`-k re_derives`: 23 passed).

## 3. The snapshot-successor guard, and whether a re-snapshot is owed

**The guard as it stands** (`scripts/snapshot_successor.py`, `logs/rj7_snapshot_guard.log`, `EXIT=0`):

> **Standing.** This snapshot has been superseded on the event log by `scan_2026-09-10_rj3`, generation 3 of this cycle, which re-judged the same evidence: 739 of this snapshot's 739 findings have a successor, 0 of them move a verdict and 3 change only the sentence that explains one. No number this report publishes differs under that successor, which is why the report is not re-snapshotted on it (`DN-004 decision 1`); the build refuses if that ever stops being true.

- Comparison figures: 38 tagged Results recomputed and compared, 0 uncovered, 42 matrix rows compared, `moved: 0`.

**What the guard cannot see.** It follows the one `SUPERSEDES` hop from the snapshot, which lands on `_rj3`. The newest judgement is `_rj4`, two generations ahead. So I ran the guard's own `moved()` against `_rj4` (`logs/rj7_moved_rj2_rj4.log`, `EXIT=0`). It reports `moved: 165`, 0 uncovered. The 165 break down as follows:
- **161 product-matrix cells that would appear.** These are 23 rows × the seven new columns, each `None` → a verdict.
- **The product fragment the report includes would change.**
- **Three tagged Results would move:**
  - `scan_findings_2026-09-10_rj2`: 739 → 1009;
  - `scan_l0_product_legs_2026-09-10_rj2`: 10 → 17;
  - `scan_l0_product_legs_at_zero_2026-09-10_rj2`: 5 → 11. The 11 are A1, A2, A9, D1, F4, B1, B2, B4, B5, D2 and D3.
- **The Tier A and Tier C host matrices do not move.**

**A re-snapshot onto `scan_2026-09-10_rj4` looks owed.** Three numbers the report publishes would change and the product matrix gains seven columns. The guard as written reports "nothing moved" only because it compares against `_rj3`. The decision, and whether the guard should follow the chain to the newest judgement, belong to the Desktop.

## 4. The views under `_rj2` and under `_rj4`, side by side

**Scoring** (`scripts/score.py`, and `scripts/score.py --cycle scan_2026-09-10_rj4`; logs `rj7_score_rj2.log`, `rj7_score_rj4.log`, both `EXIT=0`):

**Coverage:**

| | `_rj2` | `_rj4` |
|---|---|---|
| adopted harness legs scored | 14/23 | 21/23 (not scored: A12, a candidate, and G1-D, withdrawn; E5 is not a publisher leg) |
| indicators measured | 14/48 | 21/48 |
| criteria measured | 4/7 (A, B, D, F) | 5/7 (G joins) |
| bodies scored | 13/16 (BLS, BTS and ORES are unobservable) | 13/16 (same three) |

**Scores by body** (hierarchical score, flat score, rank):

| body | `_rj2` score / flat / rank | `_rj4` score / flat / rank |
|---|---|---|
| BEA | 0.350 / 0.357 / 1 | 0.120 / 0.238 / 3 |
| NCSES | 0.350 / 0.357 / 1 | 0.120 / 0.238 / 3 |
| EIA | 0.222 / 0.444 / 3 | 0.133 / 0.308 / 2 |
| DRSMSU | 0.200 / 0.286 / 4 | **0.310 / 0.238 / 1** |
| CENSUS | 0.100 / 0.286 / 5 | 0.080 / 0.190 / 5 |
| NCES | 0.100 / 0.286 / 5 | 0.080 / 0.190 / 5 |
| NASS | 0.083 / 0.231 / 7 | 0.067 / 0.150 / 8 |
| SOI | 0.083 / 0.231 / 7 | 0.067 / 0.150 / 8 |
| BJS, ERS, NAHMSAPHIS | 0.075 / 0.214 / 9 | 0.060 / 0.143 / 10 |
| SAMHSACBHS | 0.075 / 0.231 / 9 | 0.075 / 0.188 / 7 |
| NCHS | 0.050 / 0.143 / 13 | 0.040 / 0.095 / 13 |
| BLS, BTS, ORES | — (unobservable at 1) | — (unobservable at 1) |

Every readiness level is 0 under both cycles.

**The move the Desktop should look at before re-snapshotting is DRSMSU going to first.** It gets there on one leg.
- **Why DRSMSU rises.** Criterion G is measured for the first time. Its only harness leg is G4, and G4's single pass is DRSMSU's SCF flagship. Under the hierarchical scheme, one pass on a one-leg criterion is worth a fifth of the score.
- **Why BEA and NCSES fall.** Criterion B went from one leg (B3, which they pass) to five legs, and they pass only B3. The flat scheme does not move DRSMSU above them in the same way: they tie at 0.238.
- **What kind of result this is.** It is the hierarchical scheme's documented behaviour ("two equal-weight schemes, no basis to prefer either"), not a defect. It is also exactly the kind of rank a reader will quote.

**Prescriptions: bodies failing each leg.** Before this task, `scripts/prescriptions.py` had no `--cycle`. It now has one. For a cycle other than the snapshot, it recomputes "bodies failing now" from that cycle's matrices by the record's own definition (per leg, bodies with a `fail` row, the same definition as `tag_prescriptions.matrix_fail_bodies`). `tests/test_rejudge_seven_legs.py` asserts that this reproduces every stored value on `_rj2`. Logs: `rj7_presc_rj2.log`, `rj7_presc_rj4.log`, `rj7_fail_bodies_by_leg.log`, all `EXIT=0`.

| leg | bodies failing, `_rj2` | bodies failing, `_rj4` |
|---|---|---|
| A2, A9, D1, F4 | 13 | 13 |
| **D2** | — | **13** |
| A1 | 12 | 12 |
| **B2, B4, B5, D3** | — | **12** |
| A6, A8, D4 | 11 | 11 |
| **B1, G4** | — | **11** |
| A5, B3 | 10 | 10 |
| A3 | 7 | 7 |
| A12 | 4 | 4 |
| A11-declared | 2 | 2 |
| A4, A10 | 1 | 1 |

**What changes in the top prescriptions.** Under `_rj4`, the top tier (13 of 16 bodies) gains D2's two actions. The first is "Declare the terms for AI training and AI input in robots.txt", in the `hours` / `none` band class. B2, B4, B5 and D3 enter at 12. Every existing leg's count is unchanged.

**MCP** (`logs/rj7_mcp_views.log`, `EXIT=0`). The server has no `--cycle`. I built the `Tools` object in-process with its `publication` dict pointed at each cycle and changed nothing else:
- **`get_overview` product matrix:** 10 legs × 23 rows → 17 legs × 23 rows.
- **`get_body("BEA")`:** "17 failing of 25 judged on scan_2026-09-10_rj2" → "31 failing of 39 judged on scan_2026-09-10_rj4".
- **`get_indicator("D2")`:** `cycle_of_record.verdicts` goes from `{}` to `{fail: 40, error: 6}`.
- **`get_prescriptions`:** it ranks by the record's stored value, which is the snapshot's, so it would not move until the record is re-tagged after a re-snapshot.

## 5. Every premise this task file got wrong

1. **"The Finding ids must be byte-identical to `_rj2`'s."**
   - This is impossible after any `params.yaml` edit (§2).
   - I replaced it with identity in every field but `finding_id`/`params_hash`. The stop condition is against `_rj3`, the actual predecessor, because `_rj2` differs by generation 10's two reason sentences. DD-067 §4 records this.
2. **"Attaching the `dcat_fields` and `content_signal` blocks offline exactly as the runner now does", and the published path.**
   - The exercises attached the blocks in a script. `rederive.rejudge` could not, and the re-derivation gate would have re-judged the published Findings to `error` from the bare stored Observations.
   - D4-v3 also needs a third block, `membership`, which the task does not mention.
   - **What I added.** `scan/reread.py` fills an absent block from the retained body after a sha256 check, calling `dcat.membership_block` (factored out of `fetch_catalog` so there is one copy) and the two `v2clauses` functions. It refuses a missing or mismatched body and never overwrites a recorded block.
   - **How it is recorded.** `rejudge(reread_retained=True)` records `observations_reread`, and `rederive.observations_for` applies the same re-read to such a payload.
   - `obs_id` never depends on `parsed`, so no Finding cites anything but the Observations on the log. DD-067 §2 records this.
3. **§1 "`run.py --controls-only`".**
   - That entry point writes `state/<params.cycle.name>_controls.json`, which would be `state/scan_2026-09-10_controls.json`. That is a controls payload named for cycle 4 that cycle 4 never ran, and it is outside the write set.
   - I used the same `run.run_controls` through `rederive.control_gate_record`, the re-judgement's established path (generations 9 and 10). It runs into a temporary evidence root and is recorded on the payload.
4. **"If `RULE-D4-v2` exists…".** The rule that exists is `RULE-D4-v3`: `-v2` already existed when the membership test changed. D4's two moves are in §1, and neither reaches a matrix.
5. **The re-judgement engine judged a leg wherever its evidence existed.**
   - `RULE-D2-v1` reads A4, A4 is collected on Tier C, and so D2 landed on the six Tier C reference surfaces. DD-059 forbids that, and the template's gate §3.2 would have caught it.
   - **The fix.** `rejudge(frame=run.targets(params))` judges each surface on its own legs. The map goes on the payload as `surface_legs`, and `rederive` holds itself to it.
   - **A consequence.** `RULE-G1-D-v1` is no longer judged on the 22 `home`/Tier C surfaces DD-066 withdrew it from. Those 22 `_rj3` Findings have no successor, and the graph still calls them `current` (`logs/rj7_graph_check.log`). That agrees with DD-066 §3 ("not re-judged"), but it means `current` there says "not superseded", not "today's instrument". DD-067 §3 states this.
6. **A cycle-5 defect found on the way.** `rederive.rederive` had the same shared-leg problem. Cycle 5's own gate would have re-derived D2 on its Tier C rows and failed with `unexpected_after_rederive`. `run.py` now records `surface_legs` on every measured payload, and `rederive` honours it.
7. **The write set omits every view-side change the decisions require:**
   - `build_l0_matrices.PRODUCT_LEGS` was a fixed 10. The seven legs now join the product matrix only for a payload that judged them (`product_legs`), so `_rj2`'s matrix still rebuilds unchanged.
   - B5 is a body leg. It is read from the body's `host:` row and counted once per body; counting it per surface would count the seven two-flagship agencies twice.
   - `write_matrices` wrote the report's `docs/reports/generated/` fragments for any cycle. Building `_rj4`'s matrices would have rewritten the published report's tables, which is exactly the re-snapshot decision 3 withholds. The fragments are now written only for `publication.yaml:snapshot_cycle`.
   - `snapshot_successor._cell_moves` compared only `PRODUCT_LEGS`, so it would have called a seven-column successor unchanged.
   - `prescriptions.py` had no `--cycle`, and its ranking is the record's stored snapshot value. MCP has no `--cycle` either (§4).
8. **The guard compares against the immediate successor only** (§3). For the report it answers "does `_rj3` move anything". It no longer answers "is the snapshot current". I did not change it; that is the Desktop's to decide.
9. **"The site … byte-identical."** Publishing `_rj4` put `RULE-D4-v3` and seven new rules on the graph. Four artifacts generated from the graph drifted, their standing drift checks went red (run 1 of `gate-task`, 7 failed, `logs/rj7_gate_task_run1_7failed.log`), and each was regenerated by its own generator. Each is a one-line diff:
   - `docs/data/sources_per_check.json`: D4 `rules` 2 → 3, via `build_l0_site.py --only sources_per_check`. That is the appendix, not a published Result. `results_tagged.json`, the copies and the manifest are untouched, and the protected script asserts that only that line moved.
   - `docs/design/mcp_over_the_graph.md`: `current_rules` 16 → 24.
   - `docs/design/scan_tool_map.md`: `dcat`'s entry points now name `membership_block`.
10. **The standing tests assumed every re-judged Finding pairs with a predecessor.**
    - `publish.write_supersession` already writes no pair for a Finding on a leg the predecessor never judged.
    - `test_standing_guards.audit` and its graph twin, and `test_rejudgements_on_the_log`'s pairing and edge-count tests, now require a pair only on a leg the predecessor judged. They pin the exception at `{"scan_2026-09-10_rj4": 292}` (46 × 6 + 16).
    - A fork on a judged leg still fails.
    - The closed sets gained `_rj4` by name: `PUBLISHED_AFTER_THE_GUARD`, `REJUDGED`, and by_kind 15 re-judged.
11. **The three skips.** The task expected 3, and there are 3: `test_dispatch_config.py:333` (interactive only), `test_scan_harness.py:283` (E5 judges the cycle), and `assessment/tests/test_g1_preservation.py:337`.

**Also written, beyond the write set.** Each is asserted by `scripts/check_protected_rejudge.sh`:
- `scripts/rejudge_seven_legs.py`;
- `state/rejudgement_diff_2026-09-18.json` (the identity and diff record, as generation 10 wrote its own);
- DD-067 in `docs/design_decisions.md`;
- `tests/test_rejudge_seven_legs.py` (21 tests);
- the table edits in `test_scan_harness_v4.py`, `test_rejudgements_on_the_log.py` and `test_standing_guards.py`.

## 6. Gate

**Tier:** `make gate-full`, the full suite, detached and polled to `EXIT=`. `make gate-task` was run first, because the re-derivation engine changed.

| check | result | log |
|---|---|---|
| control gate (§1) | PASS: 11 fixtures, 0 unexpected, loopback | `logs/rj7_rejudge.log` |
| re-judgement stop conditions | 0 unchanged-leg differences, 0 new cells, 22 frame-explained drops, re-derives identical | `logs/rj7_rejudge.log`, `logs/rj7_dryrun.log` |
| targeted tests before publishing | **305 passed, 0 skipped, 12 xfailed, 23 deselected**, 84.76 s, `EXIT=0` | `logs/rj7_prepublish_tests.log` |
| publication | 1,009 `finding_derived`, 717 `finding_supersedes`, 0 Observations, 292 unpaired (new legs), `EXIT=0` | `logs/rj7_publish.log` |
| projection | 11,346 Findings, 7,514 `SUPERSEDES`, 0 unresolved, 3,832 current, `EXIT=0` | `logs/rj7_project.log` |
| matrices and Results | 6 files; 168 registered, 0 failed; no report fragment written | `logs/rj7_matrices.log` |
| Results before / after | 7,264 → 7,432 (+168 `proposed`); published 54 → 54, stale 5 → 5, superseded 1 → 1 | `logs/rj7_results_before.log`, `logs/rj7_results_after.log` |
| `make gate-task`, run 1 | **7 failed**, 2583 passed, 3 skipped, 26 deselected, 12 xfailed: the drift and pairing checks in §5 premises 9 and 10 | `logs/rj7_gate_task_run1_7failed.log` |
| `make gate-task`, run 2 | fast: **2590 passed, 3 skipped, 12 xfailed, 26 deselected**, 557.18 s; re-derivation: **23 passed, 0 skipped, 0 xfailed, 25 deselected**, 11.36 s; `EXIT=0` | `logs/rj7_gate_task.log` |
| `make gate-full` | **2616 passed, 3 skipped, 12 xfailed, 0 deselected**, 1458.32 s, `EXIT=0` | `logs/suite.log` |
| `seldon verify` | all checks passed (replay skipped as expensive, its default), `EXIT=0` | `logs/rj7_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`; 60 tracked shards, 0 appended to, 0 rewritten; 1 new shard; `EXIT=0` | `logs/rj7_protected.log` |
| snapshot-successor guard | `EXIT=0`, `moved: 0` against `_rj3`; against `_rj4`, `moved: 165` | `logs/rj7_snapshot_guard.log`, `logs/rj7_moved_rj2_rj4.log` |
| graph cross-check | 1,009 rj4 Findings current; 717 `SUPERSEDES` into `_rj3`; the seven rules' verdicts match §1; 22 `_rj3` G1-D still current | `logs/rj7_graph_check.log` |
| views | score, prescriptions and MCP under both cycles, all `EXIT=0` | `logs/rj7_score_*.log`, `logs/rj7_presc_*.log`, `logs/rj7_mcp_views.log` |

**Open, for the next OODA:**
1. **The re-snapshot decision (§3).** If it is taken, it goes with re-tagging the prescription values, which are the snapshot's.
2. **Whether the snapshot guard should follow `SUPERSEDES` to the newest judgement** rather than one hop.
3. **DRSMSU's first place rests on one G4 pass (§4).** This is worth a sentence in any view that prints a rank.
4. **The 22 G1-D Findings that are `current` without being today's instrument (§5 premise 5).** A `finding_withdrawn` overlay would say so on the log.
