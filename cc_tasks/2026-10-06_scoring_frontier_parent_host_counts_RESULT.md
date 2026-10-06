# RESULT: frontier legs out of the score, parent-host cells out of unit ranks, one name per count (audit C-06, C-13, C-07)

**Task:** `cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md`, launched by the dispatcher from `faffa362`; no addendum existed at start or before this RESULT. **Layer:** DN-005 §2.1. **Network:** none beyond `git push`. **Cycle:** the recollection has not run (no RESULT), so all of this is on `scan_2026-09-10_rj5`. **Decision recorded:** DD-069.

**Gate: green, on the final tree.**
- Full suite (`gate-full`'s command): **3066 passed, 4 skipped, 41 xfailed, 0 deselected, 0 failed, EXIT=0**, 43:28 (`logs/sfphc/gate_full_2.log`). Run 1 failed 1: the snapshot-successor guard rebuilds rj2's fragments and my new guard refused; it is now a conditional (`gate_full_1.log`).
- `make gate-fast`: **3038 passed, 4 skipped, 28 deselected, 41 xfailed, 0 failed, EXIT=0**, 14:24 (`gate_fast_2.log`). The four skips are the standing ones.
- `seldon verify`: all checks passed, EXIT=0 (`seldon_verify.log`).
- Protected paths: `scripts/check_protected_scoring_frontier_parent_host.sh` against `faffa362` PASS, EXIT=0 (`protected.log`). Byte-identical: rules, collectors, `runner.py`, `targets.yaml`, `params.yaml`, kept snapshots, payloads, every matrix but rj5's, prior task files. Shards and store append-only.

## 1. Frontier exclusion (d4)
`score.structure` excludes `frontier: true` legs as it excludes candidates. The product matrix marks A9 `frontier` on every row and lists it in `legs_frontier`.
- **The audit's three checks reproduce exactly on `scan_2026-09-10_rj4`**, the cycle it computed on (`test_the_audit_recomputation_reproduces`): CENSUS 0.080 → 0.089, EIA 0.133 → 0.160, SAMHSACBHS flat rank 7 → 5.
- **On rj5 the fix moves nothing.** Generation 14 had already made all 23 A9 cells `error` (`logs/sfphc/variants.log`).

## 2. Parent-host cells (d5)
`scripts/parent_host.py` derives the bodies from the roster, by three signals and no typed list: `host_shared_with` on the cycle-1 row, a frame home URL below the host root, and the .gov registry giving the bare domain to the parent department. It finds six.
- **Cells marked `parent_host` on rj5:** DRSMSU, NAHMSAPHIS, ORES and SAMHSACBHS have 10 each (A4, A5, A11-declared, A12 on the host matrix; D4, B1, B4, D2, D3, G4 on one flagship). NCHS and SOI have 16 each (the six product legs on two flagships).
- **Where they are shown:** each matrix header, with reasons; the report's method appendix (a generated fragment, plus a `C-13` correction line, prior text kept at `snapshots/…faffa362.{md,pdf}`); `docs/brief/H_limits.md`.
- **Scores and ranks on rj5, before → after** (hierarchical / flat):
  - DRSMSU: 0.458 r2 / 0.333 r6 → **0.500 r1** / 0.500 r2. Its parent-host *fails* (A4, A5, A11, B1, B4, D2, D3) leave together with its G4 pass.
  - EIA, NCSES, BEA, CENSUS, NCES: unchanged scores.
  - Flat: NAHMSAPHIS 0.300 r8 → 0.167 r11; SAMHSACBHS 0.333 r6 → 0.200 r10; SOI 0.300 r8 → 0.167 r11. The other rank moves are ties re-sorting.
- **NCHS:** 0.095 r13 / 0.182 r13 → 0.125 **r13** / 0.143 r13. On rj4 it goes from 13 to 11 (tied).
- **Unranked, with a reason:** BLS, BTS and ORES carry `unranked_reason`, never a last place. ORES's says 11 error and 9 parent_host, and those 9 are error underneath.

## 3. One count per name (d7)
`framework_writeback_measured.py` re-derives every scan-measured node against rj5 through `save` (event on `events/batch-033_framework.jsonl`, `writeback_measured.log`).
- **Promoted:** B2, B5, D2.
- **Re-pointed to rj5:** A3, A4, A5, A6, A8, A10, A11, B3, and G1-D on product surfaces only (DD-066).
- **Returned to `harness_built`:** A1, A2, A9, D1, D4, F4, with their old `measured_by` kept in `measured_previously`.
- **Projection:** `build_projection.py` exited 1 at the framework layer, because `flatten()` refused the new list-of-maps; I extended it as its message asks. `load_framework_graph.py` then exited 0 and the round-trip gate passed 9 (`projection.log`, `framework_layer.log`).

**Printed now: two counts under two names.**
- **"indicators measured" = 13**, the record's `counts.indicators_measured` (DD-055). The progress page says `13/48 measured`; fig1 says "13 of 48 indicators measured … 12 of them on the cycle of record"; `G_census_dogfood.md` says "The record marks 13 of the 48 framework indicators measured".
- **"indicators scored" = 11**, `score.py`'s coverage, shown in `scoring_model.md`, the brief and the `score.py` header.
- A test asserts that the counts block equals what all three surfaces print.

## 4. Premises wrong
1. **d3's seven did not all reach `measured`.** B1, B4, D3 and G4 qualify on rj5 only on DRSMSU's unadmitted flagship (DD-055 exclusion 2), so they stay `harness_built` with that reason. B5 qualifies only through the body-leg refinement (DD-069 §3).
2. **"measured_by on every measured node → cycle of record" forced six demotions** (§3). G1-O has no scan leg (DD-036, DD-055 §6) and keeps `measured` with no `measured_by`; it is the 13th.
3. **Six parent-host bodies, not four.** DN-012 d5 named four; NAHMSAPHIS and SAMHSACBHS are NCHS's case exactly, a unit that is a section of its parent agency's site.
4. **Wrong cycle in DN-012 d7.** It says to write back against rj4; the cycle of record is rj5, as the task says. The audit's numbers are also rj4's; on rj5, d4 alone moves nothing.
5. **Writes outside the stated write set:**
   - `framework_writeback_measured.py`, `load_framework_graph.py`;
   - `build_figures.py` (fig1 reads the record);
   - `build_evidence_map.py` (two reason classes, `open_tooling`);
   - `publication.yaml` (the correction) and the kept snapshots; DD-069;
   - test pins in `test_figures`, `test_publication`, `test_scan_figures`, `test_framework_projection_roundtrip` and `test_resnapshot_rj4`. The last now asserts that DRSMSU's G4 is `parent_host` and no longer ranks it first.
6. **The rj4 matrices still rebuild byte-identically.** Marks apply only to a cycle published with them, or not yet published (`published_unmarked`).
7. **Pre-existing, not fixed:** `build_brief_deck.py --check` fails identically at `faffa362` (slide 7 quote), checked in a clean worktree.
8. **`score.py`'s prescription join now applies `withdrawn_when_declared`**, as the prior RESULT §5.8 handed over.

**Model and tokens:** `claude-opus-5-5`, about 0.5M tokens of session context. No harness model call, no fetch.
