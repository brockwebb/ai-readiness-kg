# RESULT: `run.py --target <body>` runs a spot cycle; a spot is named, published, projected and viewed beside the snapshot, and never stands in for it

**Task:** `cc_tasks/2026-09-19_spot_scan.md`. At session start `ls cc_tasks/2026-09-19_spot_scan*` listed only the base task. Before §3, at 2026-09-19T13:52:49Z, the addendum glob `cc_tasks/2026-09-19_spot_scan_ADDENDUM*.md` matched 0 files (`logs/spot_addendum_glob_pre_s3.log`).
**Session:** launched headless by the standing dispatcher from HEAD `a20c2d9`.
**Framework layer served:** DN-005 §2.2 Tier M, per body. A publisher's fixes can now be measured without running the frame. The views show the result beside the cycle of record.
**Spend:** zero model calls. **Network:** loopback only (127.0.0.1, the control fixtures and the scratch frame's two fixture bodies), plus `git push`. No federal host was contacted and `scripts/fetch_allowlisted.py` was not used. No real spot cycle was run. Decision 5 says the first one is the operator's request.

**Gate: green, with one warning in `seldon verify` that was already there.** Tier `gate-full`, which contains every test `gate-task` runs.
- **Full suite (`gate-full`, `pytest tests/ assessment/ -q -rs`):** 2692 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed, in 1503.79 s. `EXIT=0` (`logs/spot_gate_full.log`). The three skips are the expected three: `tests/test_dispatch_config.py:333` (dispatched session), `tests/test_scan_harness.py:283` (E5), `assessment/tests/test_g1_preservation.py:337`.
- **`make gate-task`:**
  - fast tier: 2666 passed, 3 skipped (the same three), 26 deselected, 12 xfailed, 602.24 s;
  - re-derivation tier (`-k re_derives`): 23 passed, 0 skipped, 25 deselected, 11.41 s;
  - `EXIT=0` (`logs/spot_gate_task.log`).

  This run used the code that ships, with one exception. After it, one test in `tests/test_spot_scan.py` was changed so it no longer leaks the cycle licence (§3 premise 9). `gate-full` above ran after that change and contains every test `gate-task` runs.

  An earlier `gate-task` launch was killed mid-run, together with the tool call that started it (`logs/spot_gate_task_killed.log`). An earlier `gate-full` was stopped on purpose at 5% to pick up that same fix (`logs/spot_gate_full_aborted.log`).
- **`seldon verify`:** `EXIT=1`, which it defines as "warnings only". There were 0 issues and 1 warning: `Stale artifacts — 36 stale`, all `…_2026-09-10_rj2` (`logs/spot_seldon_verify.log`). `seldon verify --strict`: `EXIT=0`, "1 advisory finding reported but not blocking" (`logs/spot_seldon_verify_strict.log`). This task did not cause the warning (§3 premise 10).
- **Protected paths:** `scripts/check_protected_spot.sh` gives `PROTECTED PATHS OK`, `EXIT=0` (`logs/spot_protected.log`).
- **Loopback end to end (decision 5):** 6 passed, 0 skipped, 12 deselected, 31.41 s. `EXIT=0` (`logs/spot_loopback.log`).

---

## 0. "Rescan BEA now" on this machine

With `dispatch.enabled: true`, DN-006 decision 10 says the operator does not hand-dispatch. The request is therefore a rendered task that the dispatcher picks up:

```bash
f=$(/opt/anaconda3/bin/python3 scripts/render_spot_scan.py --target BEA --write) && git add -- "$f" && seldon cc register "$f" && git commit -m "register: $f — spot cycle rendered on request" -- "$f" seldon_events.jsonl && git push
```

That writes `cc_tasks/<today>_spot_scan_bea.md`. The render step was run in this session without `--write`. It rendered with `**Network:** allowlist: www.bea.gov, 127.0.0.1`, and `seldon.core.dispatch.parse_network` parses that line as an allowlist (`tests/test_spot_scan.py::test_the_spot_template_renders_a_dispatchable_task_for_one_body`). The register, commit and push steps were not run, because they would create a real spot task.

The direct command is the one that rendered task's session runs. On this machine, `<day>` is the UTC date:

```bash
/opt/anaconda3/bin/python3 assessment/harness/scan/run.py --target BEA --task cc_tasks/<day>_spot_scan_bea.md   # detached, logged
/opt/anaconda3/bin/python3 assessment/harness/scan/rederive.py --from state/spot_bea_<day>.json                     # must print PASS
/opt/anaconda3/bin/python3 assessment/harness/scan/publish.py --from state/spot_bea_<day>.json
/opt/anaconda3/bin/python3 assessment/harness/scan/publish.py --project
/opt/anaconda3/bin/python3 scripts/build_l0_matrices.py --cycle spot_bea_<day>
/opt/anaconda3/bin/python3 scripts/score.py --body BEA
```

**What it writes:**
- `state/spot_bea_<day>.json`. The payload carries `scope: spot`, `spot_targets: [BEA]` and `params_cycle`.
- Bodies staged in `state/evidence_staging/spot_bea_<day>/`. The publish step deletes that directory and promotes only the cited digests into `corpus/evidence/scan/`.
- `events/cycle-spot_bea_<day>.jsonl`, generation 0 of a new cycle. Every event carries `scope`/`spot_targets`. There is no `finding_supersedes`.
- The projection.
- `docs/reports/scan_matrix_{tierA,tierC,product}_spot_bea_<day>.{json,csv}`, with BEA's rows only. The tierC pair has zero rows.
- The spot's L0 Results, registered `proposed` as `scan_l0_…_spot_bea_<day>`.

**What it does not write:**
- `publication.yaml`.
- `docs/reports/generated/`, because `build_l0_matrices` writes fragments only for the snapshot.
- The report, the PDF or the site.

A second spot of BEA on the same day is refused. It takes `--rerun b` (§2 refusal 5).

## 1. The loopback run (decision 5)

Source: `tests/test_spot_scan.py`, fixture `loopback`. Log: `logs/spot_loopback.log`.

**The scratch frame.** A targets file in a throwaway `state/` held two bodies:
- `BEA`: the `body_two_products` fixture on one port. It has a `host:` row, a `home:` row and two `flagship:` rows.
- `NCHS`: the `passes_all` fixture. The spot must not touch it.

Both use real agency names so the views could set the spot beside the real snapshot. Every URL was 127.0.0.1 and every doc id synthetic. The whole tree, the event log and the scratch labels were deleted afterwards. Nothing of the run is in the repository: `check_protected_spot.sh` clause 4 finds no `spot_*` payload, shard, matrix or staging directory.

**Run.** `run.canonical_bodies(params, ["bea"])` → `["BEA"]`, so the cycle is `spot_bea_2026-09-19`. `run.targets(params, ["BEA"])` returned BEA's four rows, and the NCHS rows were excluded. Controls ran first with a `VirtualClock`, then `run.run_cycle`.

Payload summary:

| field | value |
|---|---|
| `control_verdict` | `pass` ("both control fixtures fired, every rule returned its expected verdict, and every control observation precedes the first real host") |
| `control_findings` | 289 |
| `surfaces` | 4 |
| `findings` | 64 (64 pass, 0 fail, 0 error) |
| `observations` | 130 |
| `error_class_unknown` | 0 |
| `requests_per_host` | `{127.0.0.1:53420: 134}` |
| B5 | one Finding, on `host:127.0.0.1:…` |

The NCHS fixture's port appears in no request and no Observation. Every leg the frame gives each surface was judged; the test asserts each `(doc_id, leg)` pair.

**Publish** into a throwaway log and evidence root:

| field | value |
|---|---|
| shard | `events/cycle-spot_bea_2026-09-19.jsonl` |
| generation | 0 |
| `supersedes` | null |
| `observation_events_written` | 696 (130 surface + 566 control) |
| `finding_events_written` | 353 |
| `supersession_events_written` | 0 |
| evidence promoted | 49 of 49 cited digests |

**Re-derivation.** 353 recorded, 353 re-derived, `identical: true`.

**Projection** under the scratch prefix `ScratchSpot5e68b61f_`:

| field | value |
|---|---|
| Observation / Finding / Rule nodes | 696 / 353 / 24 |
| `supports` | 948 |
| `supersedes` | 0 |
| `findings_current` | 353 |
| `observed_on_missing_document` | 0 |

The indicator bridge was not built, because it would touch the real `AssessmentIndicator` nodes. The scratch nodes left afterwards: 0.

**Matrices:**
- tier A: 1 row (BEA).
- tier C: 0 rows.
- product: 2 rows (BEA's two declared surfaces).
- The header carries `scope: spot`, `spot_targets: [BEA]` and `measured_on: 2026-09-19`.
- 138 Result names, all ending `_spot_bea_2026-09-19`. There is no `scan_l0_tierc_*` name, because the population is empty. The notes read "Tier A body of spot cycle spot_bea_2026-09-19 (BEA)", never "the 16 Tier A bodies".
- `cycle_results.check_names` passed. Nothing was registered, since nothing of the run is kept.

**Views**, pointed at a throwaway reports tree that held the real `_rj4` matrices and the spot's:
- `get_body("BEA").latest_measurement`: `latest: spot_bea_2026-09-19`, `latest_measured_on: 2026-09-19`, `latest_is_spot: true`. Its sentence reads:
  > BEA measured again by spot cycle spot_bea_2026-09-19 on 2026-09-19 (snapshot scan_2026-09-10_rj4, measured 2026-09-10). passed since the snapshot: A1, A2, A5, A6, A8, A9, B1, B2, B4, B5, D1, D2, D3, D4, F4, G4; still failing: none.

  These 16 legs are exactly the legs BEA fails on the snapshot. `prescriptions.py --body BEA` reports "16 failing leg(s)" on `_rj4`, and the fixture passes every leg.
- `get_body("NCHS")`: `latest_is_spot: false`.
- `get_prescriptions(body="BEA")`: `failing_legs: []`, `failing_legs_from: spot_bea_2026-09-19`, `bodies_failing_now_from: scan_2026-09-10_rj4`. Every action's `value` equals the snapshot record's.
- `get_overview().cycles`: `full: [scan_2026-09-10_rj4]`, `spot: [{cycle: spot_bea_2026-09-19, bodies: [BEA], …}]`. `cycle_of_record` is still `scan_2026-09-10_rj4`.
- `score.py --body BEA` ends with:
  > latest measurement: spot_bea_2026-09-19 (2026-09-19)
  > score on spot_bea_2026-09-19: 1.000 hierarchical, 1.000 flat; unranked (a spot cycle measures the bodies it names, and ranks nobody)

On the real tree, with no spot published, `get_overview().cycles` is `full: [scan_2026-09-09, scan_2026-09-10_rj2, scan_2026-09-10_rj4]`, `spot: []`. Every body's `latest_measurement` is the snapshot. `docs/design/mcp_over_the_graph.md` was regenerated to show the two new fields.

## 2. The refusals, quoted

From `logs/spot_refusals.log`. Each refusal is also pinned by a test in `tests/test_spot_scan.py`.

1. A spot payload named `scan_…`. `publish.write_events` and `write_supersession` refuse it, and so do `run.write_payload` and `build_l0_matrices.compute`:
   > REFUSING: scan_2026-09-20 carries `scope: spot` (targets ['BEA']) and is not named `spot_…`. A spot cycle is named `spot_<body>_<YYYY-MM-DD>` so it can never be read as a cycle over the frame (cc_tasks/2026-09-19_spot_scan.md decision 1).
2. A spot name on a frame payload:
   > REFUSING: spot_bea_2026-09-20 is named as a spot cycle and its payload does not carry `scope: spot`. A name and a payload that disagree about what was measured are refused rather than reconciled.
3. A spot named as `snapshot_cycle`. Refused by `build_l0_report.load_publication`, `build_l0_site.publication`, `build_l0_matrices.snapshot_cycle`, `prescriptions.snapshot_cycle` (and so `score.py`) and `Tools.cycle` (MCP):
   > REFUSING: docs/reports/publication.yaml names the spot cycle 'spot_bea_2026-09-20' as `snapshot_cycle`. A spot measures the bodies it names and nothing else; the report is a view of the frame, so its snapshot is a full cycle (cc_tasks/2026-09-19_spot_scan.md decision 2).
4. A spot and a frame cycle in one supersession pair, in either direction:
   > REFUSING: scan_2026-09-20_rj1 (frame) would supersede scan_2026-09-20 (spot). A spot cycle and a frame cycle never supersede one another.

   A measured spot writes no `finding_supersedes` by construction: `supersedes_of` gives a measurement no predecessor. The loopback run confirmed it with 0 events.
5. A second spot of one scope on one day. `refuse_clobber` alone would allow it, because the two share a `params_hash`:
   > REFUSING: spot_bea_2026-09-20.json exists. A spot cycle already measured this scope today; a second measurement is a second cycle and takes DD-041's rerun letter (`--rerun b` names it spot_bea_2026-09-20b).
6. An unknown body. This is refused before the control cycle runs:
   > REFUSING: --target ['NOPE'] names no body in the frame. Bodies: BEA, BJS, BLS, BTS, CENSUS, DRSMSU, EIA, ERS, GSA, NAHMSAPHIS, NASS, NCES, NCHS, NCSES, NIST, ORES, SAMHSACBHS, SOI, data.gov
7. A scratch projection prefix that could name a real label:
   > REFUSING: scratch label prefix 'Observation' is not `Scratch<word>_`; a prefix that could name a real label is not one

## 3. Premises this task file got wrong, and departures from the write set

1. **`docs/reports/build_report.py` does not exist.** The builders that read `snapshot_cycle` are `scripts/build_l0_report.py` and `scripts/build_l0_site.py`, and both now refuse a spot. `build_l0_matrices.py` lives in `scripts/`, not beside `run.py`.
2. **`seldon cadence render` does not exist,** and `seldon.core.cadence.render` substitutes only its five fixed fields. So `seldon cadence render spot_scan --target bea` cannot be written today. The one-line equivalent is `scripts/render_spot_scan.py` (new, outside the write set). It renders the five fields through Seldon's own `render`, then fills `{target}` and `{network_hosts}` from the target list.
3. **`assessment/harness/scan/spot.py` (new, outside the write set).** It is the one definition of a spot: name, identity check, snapshot refusal, measured-on date. The harness, the builders and the views all import it rather than each testing `spot_` for itself.
4. **`docs/design/mcp_over_the_graph.md`** is generated by `mcp/airkg_doc.py`. Its `--check` test is red until the page shows the new fields, so it was regenerated.
5. **The scratch-label projection did not exist.** `publish.project()` reset the real `Observation`/`Finding`/`Rule` labels unconditionally, so running decision 5's projection over a throwaway log would have wiped the real scan layer. `project(label_prefix=…)` was added. It accepts only `Scratch<word>_` and skips the indicator bridge under a prefix.
6. **"Views know about spots" needed a seam the views did not have.** `prescriptions.matrices` hard-coded `docs/reports/`. `REPORTS` is now a call-time global, and `score.py` reads through it. `score.prior_cycle` sorted every `scan_matrix_tierA_*` suffix, so a `spot_…` suffix would have sorted after every date and been taken for the newest full cycle. It now reads full cycles only.
7. **"`get_prescriptions(body=…)` ranks by the latest measurement's failures".** Ranking still sorts by `bodies_failing_now`, which is the snapshot's, as the same decision requires. What the latest measurement decides is which legs are listed as failing, and so which actions appear. That is how both halves of the decision hold at once.
8. **"L0 Results registered `proposed` with the spot cycle's suffix".** `cycle_results.cycle_suffix` strips only `scan_`, so a spot's suffix is its whole name: `scan_l0_a4_pass_spot_bea_<day>`. That follows DD-056 and names the spot on every Result. The Result notes also no longer claim the frame's population for a spot (§1).
9. **A test defect of this session, found and fixed before the final gate.** The CLI refusal test called `run.main`, which sets `model.CYCLE_TOKEN_ENV` before parsing arguments. Left set, that would license every later test in the pytest process to write into the committed evidence store. The test now `setenv`s the variable first, so the monkeypatch undo removes it. No write happened: `git status` showed `corpus/` clean after `gate-task`.
10. **`seldon verify` was already at warnings-only (`EXIT=1`) at HEAD.** `59d1fd1` (resnapshot_rj4) moved the 36 replaced `_rj2` Results to `stale` with `superseded_by`. Seldon's stale check exempts `withdrawn_reason`, not `superseded_by`, so it warns. That RESULT's "`seldon verify` … `EXIT=0`" was measured before its own supersede step. This task touches no Seldon artifact, so it left that as found. Next task: have Seldon's `check_stale_artifacts` treat `superseded_by` as a recorded decision, as it treats `withdrawn_reason`.
11. **A Tier C spot has a view gap.** `--target GSA` (or `NIST`, `data.gov`) runs and publishes, because the frame holds those rows. But `get_body` and `score.py --body` answer only for bodies on the snapshot's tier-A and product matrices, and Tier C bodies are not among them (DD-059). The spot's tier-C matrix is written; it is not viewed. Nothing in the task asked for it.

## 4. Gate table

| gate | tier | result | log |
|---|---|---|---|
| full suite | `gate-full` | 2692 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed, 1503.79 s, `EXIT=0` | `logs/spot_gate_full.log` |
| per-task gate | `gate-task` (fast + re-derivation) | fast 2666 passed, 3 skipped, 26 deselected, 12 xfailed, 602.24 s; re-derivation 23 passed, 0 skipped, 25 deselected, 11.41 s; `EXIT=0` | `logs/spot_gate_task.log` |
| loopback spot, end to end | `tests/test_spot_scan.py -k loopback` | 6 passed, 0 skipped, 12 deselected, 31.41 s, `EXIT=0` | `logs/spot_loopback.log` |
| `seldon verify` | default | `EXIT=1`, warnings only: 36 stale `_rj2` Results from `59d1fd1`; 0 issues | `logs/spot_seldon_verify.log` |
| `seldon verify --strict` | strict | `EXIT=0` | `logs/spot_seldon_verify_strict.log` |
| protected paths | `scripts/check_protected_spot.sh` | `PROTECTED PATHS OK`, `EXIT=0` | `logs/spot_protected.log` |
| addendum glob before §3 | — | 0 matches at 2026-09-19T13:52:49Z | `logs/spot_addendum_glob_pre_s3.log` |

**Byte-identical, per the protected check:**
- `state/`, `corpus/`, `events/`
- `docs/reports/`, `docs/data/`
- `framework/`
- the rule modules, `params.yaml`, `runner.py`, `manners.py`, `model.py`, collectors, fixtures, figures

The frame cycles' matrix Results are unchanged. `build_l0_matrices.compute("scan_2026-09-10_rj4")` returns the same 168 rows, sha256 prefix `c86eed525687`, before and after the change.

**Ships in this commit:**
- code: `assessment/harness/scan/{run,publish,rederive,spot}.py`, `scripts/{build_l0_matrices,build_l0_report,build_l0_site,prescriptions,score,render_spot_scan}.py`, `mcp/airkg_tools.py`
- `docs/design/mcp_over_the_graph.md`
- `cc_tasks/templates/spot_scan.md`
- `tests/test_spot_scan.py` (18 tests)
- `scripts/check_protected_spot.sh`
- `seldon_events.jsonl`, which includes one `dispatch_refused` line the dispatcher wrote during this session
- this RESULT
