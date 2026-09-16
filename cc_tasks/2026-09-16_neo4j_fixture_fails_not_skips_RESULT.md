# RESULT: the Seldon suite's Neo4j tier fails when it cannot run; it does not skip and call itself green

**Task:** `cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips.md` (ResearchTask `01d22208`). I checked for addenda twice, once before starting and once before §3, and found none.
**Session:** dispatched headless by the standing dispatcher at 2026-09-16T16:35:57Z (`CLAUDE_CODE_SESSION_ID=09c35113-f577-41b6-af23-293681d40590`).
**Gate:** green. Every command below ran to its `EXIT=` line before this file was written. Run (a) of the Seldon suite: 1919 passed, 0 skipped. Run (b): 1919 passed, 0 skipped. Run (c), the negative control, failed as designed: 1189 passed, 730 errors, 0 skipped, `EXIT=1`. `make gate-fast` here: 2257 passed, 18 skipped, 25 deselected, 12 xfailed, `EXIT=0`. `seldon verify` and the protected-paths check both reached `EXIT=0`.

## 0. Live observation for the predecessor's prompt clause

I captured this first, at 2026-09-16T16:36:19Z, into `logs/neo4j_fixture_s0_capture.txt`.

**This session's dispatch log**, `logs/dispatch/2026-09-16_neo4j_fixture_fails_not_skips.log`, verbatim at capture:

```
=== 2026-09-16T16:36:01.223965Z | dispatch | claude -p 'Read CLAUDE.md, then execute cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips.md. Glob and read all sibling 2026-09-16_neo4j_fixture_fails_not_skips_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task. This session is headless: there is no next turn and ending it ends the process. Poll every detached command to its EXIT line inside this turn; never use background-task mode or wait to be notified.' --permission-mode bypassPermissions
```

**The `dispatch_finished` event does not exist yet, and cannot exist during this session.** The dispatcher writes it only after this process exits, so the task asked for evidence that cannot exist while the session runs (§6 premise 1). The launch event that does exist, `3db00e1a-dbff-4e22-96b6-90da27b29277` at line 34777 of `seldon_events.jsonl`, is quoted in full in the capture file. Its key fields:

```
"event_type": "dispatch_launched", "timestamp": "2026-09-16T16:35:57.317745Z",
"payload": {"task_id": "01d22208-9c68-46a1-9697-eb703139125b", ...,
 "c2": {"predecessors": 1, "unsatisfied": [], "ok": true}, "c3": {"addenda": [], "superseding": null, "ok": true},
 "c4": {..., "declared_tokens": 0, ...}, "c7": {"branch": "main", "dirty": false, ...},
 "log_path": "logs/dispatch/2026-09-16_neo4j_fixture_fails_not_skips.log", "permission_mode": "bypassPermissions"}
```

**The predecessor's two fixes are observed working in this session:**
- The launch prompt carries the headless clause verbatim, as the log above shows.
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is set in this session's environment.
- As a result, the Bash tool offered this session has no background-mode parameter at all.
- Every long command was started with `nohup bash -c '…; echo EXIT=$?' > log &` and then polled to its `EXIT=` line by a blocking loop (`for i in …; do grep -q '^EXIT=' … && break; sleep 15; done`) inside this turn.

The dispatcher's `dispatch_finished` for `01d22208` will be the first record of whether that held through to exit. The next OODA should read it.

## 1. Commits

**Seldon** (`/Users/brock/GitHub/seldon`, pushed to `origin/main`):
- Branch `fix/neo4j-fixture-fails-not-skips` has one commit, `65a0874`.
- It was merged `--no-ff` as `2da137b`. `git diff 65a0874 2da137b` is empty, so the suite runs in §2 ran on the merged tree.

| file | change |
|---|---|
| `seldon/config.py` | Adds `NEO4J_CREDENTIAL_ENV_PAIRS` and `resolve_neo4j_credentials()`, which returns `(username, password)` with `None` for any value that is unset. `get_neo4j_driver` now calls it and keeps its existing `neo4j`/`password` defaults unchanged (they are tested by `tests/test_env_var_fallback.py`). |
| `tests/conftest.py` | `_neo4j_creds` now goes through the resolver. A new `_neo4j_unavailable_reason()` explains why the tier cannot run. `neo4j_available` now **fails**, naming both credential pairs and the excuse variable. It skips only when `SELDON_TESTS_ALLOW_NEO4J_SKIP=1`. |
| `seldon/commands/go.py` | Decision 4. The Dispatcher block now replays `artifact_state_changed` from the event log and prints `state=<current>`, adding `(at finish: <observed>)` when the two differ. A failed finish stays on the blocked list only while the current state is `blocked` or unknown. |
| `tests/test_go.py` | +2 tests: the `c609b1e1` walk (`ok:false` → `blocked` → `in_progress` → `completed` by another actor), and "no state history stays listed". |
| `tests/test_neo4j_fixture_gate.py`, `tests/neo4j_gate_probe.py` | +8 tests. The probe is run in a subprocess with the credential variables scrubbed. Cases: no credentials and no excuse fails and names all five variables; the excuse set to `1` skips on the record; an excuse of `true` does not excuse; either spelling reaches the connection attempt, and an unreachable URI fails; the resolver reads either spelling; the resolver supplies no default. |

**Test-first:**
- The two `go` tests failed before `go.py` changed.
- 5 of the 8 gate tests failed against the old `conftest.py`, which was stashed to check this. The 3 resolver-only tests passed against it because `config.py` was not stashed.

**Decision 1, `seldon/.env`: kept, and not loaded by the suite.**
- Production code already loads it. `load_project_config` calls `python-dotenv` (`seldon/config.py:41`), and that parses the file cleanly: 2 keys, values of length 5 and 10. So "nothing loads it" was wrong (§6 premise 3).
- The suite does not load it: tests run in `tmp_path`, and a suite whose result depends on an untracked developer file cannot be reproduced. The fixture's failure message says so.

**ai-readiness-kg** (this commit):
- `CLAUDE.md` gets decision 3's sentence, placed after the placeholder paragraph.
- `seldon_events.jsonl` gets this task's transitions, plus the Issue events described in §4.
- This RESULT file.

## 2. The three Seldon suite runs

Each run was `pytest tests/ -q -rs -p no:cacheprovider`, detached and polled. All three started at 2026-09-16T16:38:55Z and ran concurrently; per-process test databases (`tests/testdb.py`) make that safe.

| run | environment | outcome | wall clock | log |
|---|---|---|---|---|
| (a) | `NEO4J_USER`/`NEO4J_PASS` only (`NEO4J_USERNAME`/`NEO4J_PASSWORD` unset) | **1919 passed**, 0 skipped, 0 xfailed, 0 deselected, `EXIT=0` | 229.59 s | `/Users/brock/GitHub/seldon/logs/neo4j_gate_run_a_user_pass.log` |
| (b) | `NEO4J_USERNAME`/`NEO4J_PASSWORD` only (`NEO4J_USER`/`NEO4J_PASS` unset) | **1919 passed**, 0 skipped, 0 xfailed, 0 deselected, `EXIT=0` | 229.59 s | `/Users/brock/GitHub/seldon/logs/neo4j_gate_run_b_username_password.log` |
| (c) | all four unset, `SELDON_TESTS_ALLOW_NEO4J_SKIP` unset | **1189 passed, 730 errors**, 0 skipped, `EXIT=1` | 37.58 s | `/Users/brock/GitHub/seldon/logs/neo4j_gate_run_c_nothing.log` |

Notes on the counts:
- 1919 is the predecessor's 1909 plus the 10 new tests.
- The 730 errors in (c) are exactly the 730 tests that an ordinary shell used to skip.
- pytest reports a `pytest.fail` inside a fixture as a setup **error** (`ERROR at setup of …`), not a failure. The exit code is 1 either way.

The message run (c) printed, verbatim:

```
Neo4j credentials unresolved (username and password): export NEO4J_USERNAME/NEO4J_PASSWORD or NEO4J_USER/NEO4J_PASS. No file is read for them (seldon/.env is loaded only by load_project_config, never by the test suite). Set SELDON_TESTS_ALLOW_NEO4J_SKIP=1 only to excuse the Neo4j tier on purpose.
```

## 3. `seldon go` Dispatcher block on the `c609b1e1` case

Both blocks were rendered by `_get_dispatch_section('.')` against this repo's live event log.

**Before**, at `c0b232c` (`logs/neo4j_fixture_go_before.txt`):

```
- `c609b1e1` exit=0 result=NO graph=in_progress — `logs/dispatch/2026-09-16_dispatcher_commits_its_record.log`
...
**Blocked by the dispatcher — read the log before re-queueing:**
- `c609b1e1` exit=0 — `logs/dispatch/2026-09-16_dispatcher_commits_its_record.log`
```

**After** (`logs/neo4j_fixture_go_after.txt`):

```
- `c55e40b7` exit=0 result=yes state=completed — `logs/dispatch/2026-09-16_publication_guards.log`
- `c609b1e1` exit=0 result=NO state=completed (at finish: in_progress) — `logs/dispatch/2026-09-16_dispatcher_commits_its_record.log`
- `f560c82a` exit=0 result=yes state=completed — `logs/dispatch/2026-09-16_headless_session_polls_to_completion.log`
```

The block no longer has a "Blocked by the dispatcher" section.

**Why the state comes from the event log rather than Neo4j.** The task asked for "the artifact's current state". The section's docstring requires it to render when Neo4j is down. The graph is a projection of this same log, so replaying `artifact_state_changed` gives the graph's state without needing the graph. That satisfies both requirements.

## 4. The `session_id` smear (decision 5): diagnosed, not fixed

**The id is not the dispatcher's session id, and it is not "the last id in the store".** It comes from a session file that was never closed:
- `seldon/config.py:86` `start_session` writes `.seldon/current_session.json`, and returns the existing id if that file is already present.
- Its only caller is `seldon briefing` (`seldon/commands/session.py:133`).
- `end_session` runs only from `seldon closeout` (`session.py:312`).
- In this repo the file reads `{"session_id": "87ea77ee-a403-4972-9e1c-6efdf326b558", "started_at": "2026-08-22T14:00:52.690207Z"}`, and has done so since 2026-08-22.

**Every writer stamps that id.** Every `get_current_session` caller does: `cc.py:669` (the `seldon cc complete` path), `cc.py:989/1064/1188`, `dispatch.py:107`, and `result.py`, `issue.py`, `link.py`, `verify.py`, `governed.py`, `task.py`.

**The operator's environment played no part.** Nothing reads an environment variable for the id, and this session's real id (`CLAUDE_CODE_SESSION_ID=09c35113…`) is never consulted.

**Scale:** 34,137 of the 34,777 events in the log at capture carry `87ea77ee`:

| actor | events |
|---|---|
| `human` | 21,290 |
| `cc` | 12,822 |
| `dispatcher` | 25 |

These include `e504dc63`, `b9cb5f08` and `ee6d74aa` on `c609b1e1`, and the predecessor's own completion events `a95c7ab5` and `83317bf9`. As provenance, `session_id` currently tells you nothing about which session wrote an event.

**Issues filed:**
- **`5c6f694a-8b78-4dff-b412-258c60a56166`** (factual_error, high/medium; event `cf7bcbce`): the diagnosis above. I did not fix it; a provenance change needs its own task.
- **`cf6d440c-a9f1-4161-bf38-448dff5788f3`**: an accidental duplicate, now closed `wont_fix`. My first `seldon issue create` passed `--affects 01d22208`. The command printed `Error: 'ResearchTask' cannot target a 'affects' relationship` and exited non-zero, but it had already appended `artifact_created` (`043860b2`). I corrected this with a state transition, not by editing the log.
- **`7af77cb8-d942-40e4-a61f-67a22bb8c45f`** (internal_contradiction, medium/low; event `3fb2e85b`): `seldon issue create` is not atomic. It should check every link before it writes its first event.

These three Issues are also stamped `87ea77ee` with actor `human`, which is the defect showing up again.

## 5. The re-read: RESULTs dated 2026-09-01 or later that claim the Seldon suite green

Where the cited log still exists, I read its pytest summary line directly. `-q` prints `N skipped` whenever N > 0, so a summary line with no `skipped` means zero skips.

| RESULT | claim quoted | passed | skipped |
|---|---|---|---|
| seldon `2026-09-02_paper_build_xref_passthrough_failure` | 697 passed, 0 failed | 697 | no skip count recorded (ran under `python -m dotenv -f .env run`, which exports `NEO4J_USERNAME`/`NEO4J_PASSWORD`) |
| seldon `2026-09-02_snapshot_artifacts_verify` | 694 passed, 1 failed (not a green claim) | 694 | no skip count recorded |
| seldon `2026-09-02_track_cc_tasks` | 697 passed, 0 failed | 697 | no skip count recorded (dotenv run) |
| seldon `2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology` | 934 passed, 0 failed, 0 deselected | 934 | no skip count recorded (dotenv run) |
| seldon `2026-09-03_…_laneC_SUBRESULT` | 928 passed, 0 failed, 6 deselected | 928 | no skip count recorded |
| seldon `2026-09-04_ad028_grammar_amendment_migrate_atomic` | 1180 passed, 0 failed | 1180 | no skip count recorded |
| seldon `2026-09-04_ontology_ingest_defects_SUBRESULT` | 1113 passed, 0 failed | 1113 | no skip count recorded |
| seldon `2026-09-04_reltype_case_and_source_provenance_SUBRESULT` | 1148 passed, 0 failed | 1148 | no skip count recorded |
| seldon `2026-09-04_resolver_options_and_placeholder_SUBRESULT` | 1368 passed | 1368 | no skip count recorded |
| seldon `2026-09-04_replica_sync_all_SUBRESULT` | 1444 passed, 0 failed | 1444 | no skip count recorded |
| seldon `2026-09-04_seldon_open_defect_closeout` | 1444 passed, 0 failed | 1444 | no skip count recorded |
| seldon `2026-09-04_si09_removal_condition_SUBRESULT` | 1391 passed, 0 failed | 1391 | no skip count recorded |
| seldon `2026-09-04_small_defects_SUBRESULT` | 1380 passed, 0 failed | 1380 | no skip count recorded |
| seldon `2026-09-06_task_precedes_relationship` | 1516 passed, 0 failed | 1516 | no skip count recorded |
| seldon `2026-09-07_precedence_artifact_labels` | 1542 passed in 112.05s | 1542 | no skip count recorded (summary line quoted with no `skipped`, so 0 if quoted verbatim) |
| seldon `2026-09-12_seldon_handoff_tool` | 1574 passed | 1574 | no skip count recorded |
| seldon `2026-09-12_ad030_governed_docs_ingest` | 1628 passed | 1628 | no skip count recorded |
| seldon `2026-09-12_ad030_findings_reconcile` | 1682 passed | 1682 | no skip count recorded |
| seldon `2026-09-12_ad030_names_supersession_reingest` | 1714 passed | 1714 | no skip count recorded |
| airkg `2026-09-15_standing_dispatcher` | 1,785 / 1,787 passed | 1787 | **0**, per logs `logs/sd_seldon_suite.log`, `logs/sd_seldon_suite2.log` (`1787 passed in 146.82s`) |
| airkg `2026-09-15_g1d_leaves_l0` | 1,791 passed | 1791 | **0**, per log `logs/g1d_seldon_suite.log` (`1791 passed in 132.59s`) |
| airkg `2026-09-16_cadence_and_enable` | 1,878 passed | 1878 | **0**, per log `seldon/logs/cadence_seldon_suite_final3.log` (`1878 passed in 137.16s`) |
| airkg `2026-09-16_dispatch_idempotence` | 1893 passed (×3) | 1893 | **0**, per logs `seldon/logs/seldon_suite{,_final,_merged}.log` |
| airkg `2026-09-16_dispatcher_commits_its_record` | 1907 passed; §5.5 also reports an ordinary-shell `1177 passed, 730 skipped` | 1907 | **0** on the gate runs, per logs `seldon/logs/own_record_suite_neo4j.log`, `own_record_merged.log`. That RESULT itself disclosed the 730-skip run. |
| airkg `2026-09-16_headless_session_polls_to_completion` | 1909 passed, 0 skipped | 1909 | **0**, recorded in the RESULT and in `seldon/logs/seldon_suite_headless.log` |

**What the table shows:**
- **No green claim with a surviving log was a skip-green.** Every one has zero skips.
- The Seldon-repo RESULTs from 09-02 to 09-12 have no skip count and no surviving log. Several say they ran under `python -m dotenv -f .env run`, which loads `seldon/.env` (`NEO4J_USERNAME`/`NEO4J_PASSWORD`), so their Neo4j tier plausibly ran. That is inference, not a record, so they stay "no skip count recorded".
- A skip-green would show a passed count far below the collected total, as `1177` against `1907` did. None of the counts above has that shape relative to its neighbours.

## 6. Premises this task file got wrong

1. **"§0 this session's own … `dispatch_finished` event quoted verbatim."** The dispatcher appends `dispatch_finished` only after the session exits, so no session can quote its own finish event. §0 quotes the launch event and the dispatch log instead. The finish event for `01d22208` is for the next OODA to read.
2. **"the `~/.wintermute/.env` fallback that function already has."** `seldon/config.py:get_neo4j_driver` has no file fallback: it goes environment, then the literal defaults `neo4j`/`password`. The `~/.wintermute/.env` fallback lives in this repo (`scripts/jobs/airkg_dispatch.sh:37`, `scripts/build_projection.py:153`). I did not add it to Seldon: Seldon is a separate system, and reading Wintermute's credential file would couple the two (`~/GitHub/CLAUDE.md`, Cross-Project Architecture). The shared resolver covers both environment spellings, which is what this machine exports.
3. **"`seldon/.env` … nothing loads it."** `load_project_config` loads it with `python-dotenv` (`seldon/config.py:41`), and the apostrophe does not stop that parser. It is only the shell's `set -a; . .env` that fails.
4. **"`87ea77ee-...`, which is the dispatcher's session id from the launch at 14:34Z."** It is a `seldon briefing` session file from 2026-08-22 that was never closed out, and every actor stamps it (§4). It predates the dispatcher by more than three weeks.
5. **"If it reuses the last id in the store … file an Issue."** It does not reuse the store's last id; it reuses a stale session file. I filed the Issue anyway, because the defect is real and larger than the premise described.
6. **The `seldon go` block "is reading `graph_state_observed` off the last `dispatch_finished` event"** was correct. The block also kept a task on the blocked list until a *relaunch*, so a hand completion never cleared it. Both are fixed.
7. **Unstated in the task:** this repo's `CLAUDE.md` still tells a session to poll with `sleep 240; tail -5`. The predecessor's RESULT §4 reported that a plain `sleep` is refused in this harness and that the loop form is what works. This task's write set allowed exactly one `CLAUDE.md` sentence, so I did not change the polling example. It is still open.

## 7. Gate

| check | passed | skipped | xfailed | deselected | other | wall clock | log |
|---|---|---|---|---|---|---|---|
| Seldon suite (a), `NEO4J_USER`/`NEO4J_PASS`, merged tree | 1919 | 0 | 0 | 0 | `EXIT=0` | 229.59 s | `/Users/brock/GitHub/seldon/logs/neo4j_gate_run_a_user_pass.log` |
| Seldon suite (b), `NEO4J_USERNAME`/`NEO4J_PASSWORD` | 1919 | 0 | 0 | 0 | `EXIT=0` | 229.59 s | `/Users/brock/GitHub/seldon/logs/neo4j_gate_run_b_username_password.log` |
| Seldon suite (c), negative control | 1189 | 0 | 0 | 0 | 730 errors, `EXIT=1` (as designed) | 37.58 s | `/Users/brock/GitHub/seldon/logs/neo4j_gate_run_c_nothing.log` |
| `make gate-fast` (this repo) | 2257 | 18 | 12 | 25 | 248 warnings, `EXIT=0` | 494.44 s (8:14) | `logs/neo4j_fixture_gate_fast.log` |
| `seldon verify` | n/a | n/a | n/a | n/a | "All checks passed.", `EXIT=0` | under 1 s (started and finished 16:43:47Z–16:43:48Z) | `logs/neo4j_fixture_seldon_verify.log` |
| protected paths (`docs/` byte-identical to `c660539`) | n/a | n/a | n/a | n/a | confirmed, `EXIT=0` | under 1 s | `logs/neo4j_fixture_protected.log` |

**Tiers.** `gate-fast` is the fast tier. The task specified it because no stored payload was touched, and this is not a green full suite; `make gate-full` was not run.

**The 18 skips.** The `gate-fast` target does not pass `-rs`, so its log does not give their reasons. The predecessor reported the same 18.
