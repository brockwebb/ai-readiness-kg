# RESULT: the figure gate reads the cycle of record from where the report reads it; a guard that cannot run says so on the record

**Task:** `cc_tasks/2026-09-17_figure_gate_reads_cycle_of_record.md` (ResearchTask `c2f30449`). I globbed for addenda twice, at the start and again before §3, and neither glob found one.
**Executed:** 2026-09-17, UTC 10:46Z to 11:33Z, when the `cc complete` transition was written. This was a headless session launched by the standing dispatcher (`dispatch_launched` `3c38d5d7`), from base commit `e24dc2e`.
**Gate:** green, and every command below reached its `EXIT=` line before this file was written.
* `make gate-full` (whole suite, `-rs`): 2299 passed, 3 skipped, 12 xfailed, 0 deselected, 1435.77 s, `EXIT=0`. The skip count is the expected 3.
* `seldon verify`: `EXIT=0`.
* Protected paths: `EXIT=0`.

**Outcome.**
* The 15 tests that used to skip now run against the `_rj2` matrices.
* Their first run found **two failures**, and both were in how the tests identified a cycle; neither was in a figure or a matrix. §2 covers them.
* Two new tests pin down the one skip that remains and the failure that replaced the other skips.
* The dispatcher-quiet guard now carries a declared `interactive_only` condition.

---

## §0 Session identity, observed live (task §1)

This is the first launch by a dispatcher pass that runs the session-identity fix, and every link in the chain can be read from the store.

* **This session's environment** has `SELDON_SESSION_ID=39f682e7-aeac-469a-8f0b-7a699c5d5113`. It also has `CLAUDE_CODE_SESSION_ID=373d283b-1e50-41e3-9b69-c7afd49d681c` (Claude Code's own id; case (b), shadowed) and `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.
* **`dispatch_launched`**, `seldon_events.jsonl` line 34814:
  * `event_id` `3c38d5d7-7161-4ca8-8f59-1ac110c9e1b6`, 2026-09-17T10:45:31.592115Z, actor `dispatcher`.
  * `session_id` `c2cedeb1-9208-4200-b9ea-1941cffb8c6b`: the dispatcher process's own bound id (`claimed_by` `dispatcher:HexagonMBP.local:32372`).
  * `payload.child_session_id` `39f682e7-aeac-469a-8f0b-7a699c5d5113`, **equal to this session's `SELDON_SESSION_ID`**.
  * The previous RESULT (§0 item 3) left one link unobserved on the live system: the dispatcher mints the id, passes it to the child through the environment, and records it on its own event. That link is now observed.
* **A dispatcher line written during this session** carries neither id. `dispatch_refused` `553d8b36-aedb-4940-b059-205b7f3b4d99` (2026-09-17T11:04:24.742235Z, reason `lease_held`) has `session_id` `3b4a3e0e-63fb-4aaa-8492-1aefd4a94201`. It came from the wrapper pass that `test_two_passes_in_a_launchd_shaped_environment_leave_the_event_log_byte_identical` runs; that test allows exactly one such line. So the pass bound its own process id and inherited nothing from the session, as designed. The line is committed with this task.
* **This session's own `cc`-actor events.** The only `seldon cc` verb that writes one is `complete` (`seldon cc --help`: complete, constrain, rederive-description, register). The protocol runs it after this file exists, so the events are quoted in §0.1, which was added after `seldon cc complete` returned and before the commit.

### §0.1 This session's `cc`-actor events

Added after `seldon cc complete` returned `EXIT=0`, quoted from the store, lines 34816–34817:

* `1212a9a5-30da-489f-ac80-7b161bca672d`, `artifact_updated`, 2026-09-17T11:32:33.697380Z, actor `cc`, `session_id` **`39f682e7-aeac-469a-8f0b-7a699c5d5113`**, artifact `c2f30449`.
* `12533f96-779c-424f-8c02-367371ab1bcc`, `artifact_state_changed` `in_progress -> completed`, 2026-09-17T11:32:33.737117Z, actor `cc`, `session_id` **`39f682e7-aeac-469a-8f0b-7a699c5d5113`**.

This completes the chain from the store:
* the dispatcher minted `child_session_id` `39f682e7` on `dispatch_launched`;
* this session's environment received it as `SELDON_SESSION_ID`;
* this session's `cc`-actor events carry it.

That is resolution case (a), and the dispatcher's own events carry a different id (`c2cedeb1`). `seldon cc complete` also printed "Task has no registered file_hash. Skipping immutability check." The Desktop registration of `c2f30449` recorded no file hash, so this task file's immutability was not machine-checked at completion.

## §1 The resolver, and how the tests call it (decisions 4 and 1)

**Prior art read first (decision 4).**
* `cc_tasks/2026-09-10_harness_v5_blind.md` decision 6 and its RESULT (lines 116–119) introduced skip-with-reason so that a task stopping before it reports could still be green on unrelated work. Its condition was "`params.cycle.name` has no matrix". At the time that meant the same thing as "nothing reported yet". It stopped meaning that once the re-judgements made a `_rjN` name the reported cycle.
* **The cycle-of-record declaration already exists.** It is `snapshot_cycle` in `docs/reports/publication.yaml` (currently `scan_2026-09-10_rj2`). The file's own header says it is "one declaration, read by three consumers".
* **The intended resolver also already exists, and the tests bypassed it.**
  * `scripts/build_l0_site.py::publication()` is how the site build reads the declaration.
  * `scripts/build_l0_report.py::load_publication()` is how the report reads it.
  * `scripts/snapshot_successor.py` and `tests/test_publication.py` read the YAML directly.
* No new resolver was written. The tests import `build_l0_site.publication()`, which already exposes everything they need, so no resolver module was edited.

**How the tests call it now.**
* `tests/test_scan_figures.py::reported_cycle()`:
  * returns `build_l0_site.publication()["snapshot_cycle"]`;
  * **skips only when `build_l0_site.PUBLICATION` does not exist**, with the reason "no cycle has been reported".
* `cfg(cycle)` now passes `cycle or reported_cycle()` explicitly to `figures.config()`. That function's own default is `params.cycle.name`, which stays what the harness runs.
* `matrix()` treats a missing matrix for a named cycle as an **assertion failure** instead of a skip.
* Four further readers now go through `cfg()` instead of `params.yaml`:
  * `_l0_csv`
  * the report-agreement test
  * `_tier_doc_ids`, which now takes the `targets` named on the cycle's own payload
  * the Finding query
* The two external callers that import this module by path pass `cycle=` explicitly, and the full suite shows them unaffected:
  * `tests/test_rejudgement_gen9.py:259`
  * `tests/test_scan_harness_v4.py:710`
* `tests/test_scan_run_2.py::test_the_denominator_is_per_leg_and_the_page_says_so` resolves the cycle through the same `build_l0_site.publication()` and applies the same skip-or-fail rule. Its second skip is a separate data condition and stays unchanged: "the progress page has not been generated". The page exists, so that skip does not fire.
* `params.yaml` is unchanged.

**New tests** (both pass):
* `test_the_only_skip_is_a_project_that_has_reported_nothing` points `PUBLICATION` at a missing file and asserts the skip and its reason.
* `test_a_declared_cycle_with_no_matrix_fails_rather_than_skips` asserts an `AssertionError` for a named cycle that has no matrix.

## §2 The 15 formerly skipped tests (decision 2)

**Before this task** (`logs/figgate_before.log`; the three files alone): 54 passed, 16 skipped, `EXIT=0`, 962.11 s.
* 14 skips were in `test_scan_figures.py`. Ten carried "cycle params.cycle.name has not been reported: state/scan_matrix_2026-09-10.json does not exist". Four carried "docs/reports/scan_matrix_*_2026-09-10.{csv,json} has not been built".
* One was `test_scan_run_2.py:534` ("this cycle has no matrix yet").
* One was `test_dispatch_config.py:333` (§3).

**First run after the resolver change** (`logs/figgate_after.log`): 2 failed, 20 passed, 1 skipped, `EXIT=1`. Once the gate pointed at the cycle of record, it failed.

1. **`test_each_legs_registered_counts_re_derive_from_the_graph`** failed on every leg. Examples: `A2 fail: graph 120, registry scan_a2_fail_2026-09-10_rj2 = 40.0`, `A3 pass: graph 17, registry … = 7.0`, `TIER C G1-D fail: graph 12, registry … = 6.0`.
   * **Cause:** the query selected Findings by `params_hash` alone. A re-judgement's Findings carry the hash of the rules they were judged under, and all four generation-9 re-judgements share hash `d3499218ef48`. The graph holds 352, 404, 634 and 739 Findings under that hash, for `scan_2026-09-07_rj2`, `scan_2026-09-07b_rj3`, `scan_2026-09-09_rj2` and `scan_2026-09-10_rj2`. The query therefore summed four cycles.
   * Measured cycles are different: their Findings have `cycle = null` and nine distinct hashes among them.
   * **Fix (test only):** a cycle is identified by `(params_hash, cycle)`. The query adds `AND ((f.cycle IS NULL AND $measured) OR f.cycle = $cycle)`, where `measured` is `not publish.is_rejudgement(payload)`, read from the cycle's own payload rather than its name.
   * **Not wrong:** the registry, the matrix and the figures. After the fix every leg's graph counts equal its registered counts.
2. **`test_the_l0_matrices_and_the_report_agree_on_the_cycle`** failed with "the built report does not carry the parameter hash its matrices were built under" (`'d3499218ef48' in <report>`).
   * **Cause:** the report identifies a re-judged snapshot as "Cycle `scan_2026-09-10`, parameter hash `4e0a92ba19ab…`, judged as `scan_2026-09-10_rj2`". That is the collection hash (the payload's `derived_from_params_hash`) plus the judgement name.
   * The matrices carry the judgement hash `d3499218ef48`. Four cycles share that hash, so it names a rule set, not a cycle, and the report's pair is the one that does identify the cycle.
   * **Fix (test only):** the test now asserts four things:
     * the three matrices share one hash;
     * the matrices name `cycle == snapshot_cycle`;
     * that hash equals the cycle payload's `params_hash`;
     * the report contains `` `scan_2026-09-10_rj2` `` and the **collection** hash (`derived_from_params_hash` for a re-judgement, `params_hash` for a measurement).
   * `docs/` is byte-identical, and the report's statement is true as written.

Both fixes are documented in the tests' docstrings, which cite this section.

**After the fixes** (`logs/figgate_after2.log`): 22 passed, 1 skipped (the declared guard), `EXIT=0`.

| # | test | outcome | resolved to |
|---|---|---|---|
| 1 | `test_scan_figures.py::test_the_registered_intervals_are_the_ones_the_matrix_holds` | passed | `state/scan_matrix_2026-09-10_rj2.json` |
| 2 | `…::test_every_numeral_in_every_figure_resolves_to_an_artifact` | passed | `state/scan_matrix_2026-09-10_rj2.json` (+ `state/scan_matrix_tierc_2026-09-10_rj2.json` via `figures.build`) |
| 3–7 | `…::test_the_gate_catches_a_number_from_nowhere[5 mutations]` | 5 passed | `state/scan_matrix_2026-09-10_rj2.json` |
| 8 | `…::test_the_figures_print_the_things_the_task_asked_them_to` | passed | `state/scan_matrix_2026-09-10_rj2.json` |
| 9 | `…::test_no_figure_reaches_the_network` | passed | `state/scan_matrix_2026-09-10_rj2.json` (figures fixture) |
| 10 | `…::test_each_legs_registered_counts_re_derive_from_the_graph` | **failed, fixed (above)**, then passed | `state/scan_matrix_2026-09-10_rj2.json`; payload `state/scan_2026-09-10_rj2.json`; targets `state/scan_targets_fss_2026-09_v5.json` |
| 11 | `…::test_every_l0_matrix_row_re_derives_from_the_graph[scan_matrix_tierA]` | passed: 80 cells re-derived, 0 unidentified | `docs/reports/scan_matrix_tierA_2026-09-10_rj2.csv` |
| 12 | `…[scan_matrix_tierC]` | passed: 15 cells, 0 unidentified | `docs/reports/scan_matrix_tierC_2026-09-10_rj2.csv` |
| 13 | `…[scan_matrix_product]` | passed: 230 cells, 0 unidentified | `docs/reports/scan_matrix_product_2026-09-10_rj2.csv` |
| 14 | `…::test_the_l0_matrices_and_the_report_agree_on_the_cycle` | **failed, fixed (above)**, then passed | `docs/reports/scan_matrix_{tierA,tierC,product}_2026-09-10_rj2.json` + `docs/reports/2026-09_fss_ai_readiness_L0.md` |
| 15 | `test_scan_run_2.py::test_the_denominator_is_per_leg_and_the_page_says_so` | passed (per-leg n = 28, 36, 38, 39, 40; page states `n = 28–40`) | `state/scan_matrix_2026-09-10_rj2.json` + `docs/progress/index.html` |

The cell counts are in `logs/figgate_l0_cells.log`.

## §3 The interactive-only guard (decision 3)

`tests/test_dispatch_config.py::test_a_single_pass_writes_no_event_when_there_is_nothing_to_assert` now carries `@interactive_only`.
* **Definition.** `interactive_only` is a module-level named `pytest.mark.skipif(bool(os.environ.get("SELDON_SESSION_ID")), reason="interactive_only: …")`.
* **Why that variable.** The dispatcher sets `SELDON_SESSION_ID` on every session it launches and on no other process (`seldon/commands/dispatch.py::_run`; `seldon/config.py::SESSION_ENV_VARS`).
* **The skip reason** names the marker and states why the checkout cannot be quiet inside a dispatched session: the session holds its own task's claim, and its own edits dirty the tree.
* **Why a named `skipif` and not a registered marker.** Registering a marker means editing `pyproject.toml`, which is outside this task's write set. A named `skipif` needs no registration and cannot turn into an unknown mark. The full suite log shows 0 `PytestUnknownMarkWarning`.
* **No configuration-invariant half to split out.** Every assertion in the test is about what one pass does in the quiet state. The part that holds in every state, dispatched sessions included, is the idempotence test above it, which never skips on queue state. The docstring now says this.
* **Two kinds of skip, told apart.** The data-condition reasons the test lists (eligible, claim in flight, dirty tree, lease, STOP, disabled) stay as they were. They apply in an operator shell, where the state could be quiet.
* **In this session** the test skips at `tests/test_dispatch_config.py:320` with the `interactive_only` reason (`logs/suite.log`).

## §4 Premises this task file got wrong

1. **"five tests, 14 cases".** The 14 skipped cases in `test_scan_figures.py` come from **eight** test functions: six figure/registry functions (10 cases) and two L0-matrix functions (4 cases).
2. **"The current cycle of record's figures are ungated today"** (the framework-layer header). This is only partly true. `tests/test_rejudgement_gen9.py::test_every_numeral_in_this_cycle_s_figures_resolves_to_an_artifact[scan_2026-09-10_rj2]` already ran the numeral audit on the `_rj2` figures. Seven checks had not been running, and one of them, the graph re-derivation, was wrong once it ran:
   * the structural checks
   * the network check
   * the registered-interval check
   * the graph re-derivation
   * the L0 matrix re-derivation
   * the report/matrix agreement check
   * the denominator check
3. **Decision 1's candidate locations.** `scripts/build_report.py` does not exist, and `scripts/build_projection.py` does not hold the cycle of record. The declaration is `docs/reports/publication.yaml:snapshot_cycle`. It has two function readers, `build_l0_site.publication()` and `build_l0_report.load_publication()`, and two raw-YAML readers, `snapshot_successor.py` and `tests/test_publication.py`. So "one resolver" is one declaration read four ways. These tests use the site's reader. Merging the four readers is not in this write set.
4. **Decision 2's assumption** that a failure would be "a finding about the figures of record … fix the figure or the matrix reference". Both failures were in how the tests identified a cycle: `params_hash` is not a cycle identity for re-judgements. The figures, matrices, registry and report all agree once a cycle is keyed as `(params_hash, cycle)`, or as (collection hash, name) in the report.
5. **Implicit in "the report and the site cite the re-judged matrix".** Until this task, `docs/progress/index.html` said its figures were "gated by `tests/test_scan_figures.py`: every numeral resolves to … a count in `state/scan_matrix_2026-09-10_rj2.json`". That gate was skipping on every run, so the page's claim was false. It is true now, and the page text did not change.
6. **"a skip by design".** The task asked for the test to be "marked `interactive_only`". A registered marker would require an edit to `pyproject.toml`, which is outside the write set. §3 records the named-`skipif` form used instead.
7. **The write set's event-store line.** Besides this task's own transitions, `seldon_events.jsonl` gained one dispatcher line, `dispatch_refused` `553d8b36` (`lease_held`). The suite's idempotence test wrote it (§0), and it is committed here.
8. **Observed, not a premise error, recorded for the next OODA.** The report's Standing paragraph says `scan_2026-09-10_rj2` is superseded on the event log by `scan_2026-09-10_rj3`, which moved no verdicts. So the cycle of record is deliberately not the newest judgement (DN-004). These tests follow the declaration, not the newest `_rjN`, and that is the intended behaviour.

## §5 Gate

**Tier: `make gate-full`** (the whole suite `tests/ assessment/`, `-q -rs`, detached by the Makefile target). Started 2026-09-17T11:06:46Z.

| check | passed | skipped | xfailed | deselected | wall clock | exit | log |
|---|---|---|---|---|---|---|---|
| `make gate-full` | 2299 | 3 | 12 | 0 | 1435.77 s (0:23:55) | `EXIT=0` | `logs/suite.log` (copied to `logs/figgate_suite_full.log`) |
| baseline, three files, before any edit | 54 | 16 | 0 | 0 | 962.11 s | `EXIT=0` | `logs/figgate_before.log` |
| changed tests, first run | 20 (2 failed) | 1 | 0 | 0 | 5.28 s | `EXIT=1` | `logs/figgate_after.log` |
| changed tests, after fixes | 22 | 1 | 0 | 0 | 5.24 s | `EXIT=0` | `logs/figgate_after2.log` |
| `seldon verify` | all checks passed (34815 events readable, 128 task source files resolve) | | | | | `EXIT=0` | `logs/figgate_verify.log` |
| protected paths | only the write set moved; `docs/`, `state/`, `assessment/` (incl. `params.yaml`), `events/`, `kg/`, `framework/`, `corpus/`, `scripts/` byte-identical | | | | | `EXIT=0` | `logs/figgate_protected.log` |

**The three skips in `gate-full`**, quoted from `logs/suite.log`. This is the expected count.
1. `tests/test_dispatch_config.py:320`: "interactive_only: SELDON_SESSION_ID is set, so this is a dispatched session, which holds its own task's claim and dirties the tree for its whole life; the quiet checkout this test asserts cannot exist inside one. Run it from an operator shell." This is the declared guard.
2. `tests/test_scan_harness.py:281`: "E5 judges the cycle's controls, not a surface". This is the parametrisation by design.
3. `assessment/tests/test_g1_preservation.py:337`: "no dev proposition publishes SE and CI together". This is the data condition.

**Write set as committed:**
* `tests/test_scan_figures.py`
* `tests/test_scan_run_2.py`
* `tests/test_dispatch_config.py`
* `seldon_events.jsonl`: the dispatcher line and this task's `cc complete` transitions
* this RESULT

No matrix, figure or report was rebuilt.
