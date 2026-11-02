# RESULT: the projection was never erased; the "stale" verdict came from a Claude Desktop MCP server running code older than the labels it was checking

**Task:** `cc_tasks/2026-11-02_projection_restored_and_its_eraser_found.md` (task `4e27e7bf`). I globbed for `_ADDENDUM*` siblings before starting and found none.
**Executed:** 2026-11-02, 17:47Z to 19:4xZ. This was a headless dispatched session in worktree `bubbly-puzzling-zebra` (branch `worktree-bubbly-puzzling-zebra`, based on `036c935b`).
**Ran to the end.** All three Parts are done and `seldon dispatch part-complete` was recorded for A, B and C. Per the launch prompt, this session does not merge, push or run `seldon cc complete`; the dispatcher does those.
**Recall used:** none. The eight RECALL-001 hits are about dispatcher dirty trees, the spend guard, DCAT rules, scan hygiene, derived counts and the 9af5f624 resume. None of them is about the MCP projection gate or the framework loader, and none changed the approach.

## §1 Part A finding

**Nothing erased the framework nodes, and the shared database was never behind main.** The `stale` result (243 compared, 11 `record: present, graph: MISSING`) came from a Claude Desktop `airkg_server.py` process. That process was started on Fri 2026-10-30 at 06:56 local (pids 17681 and 18628), before either commit that added the three new labels.

`mcp/airkg_tools.py` `projection_gate` reads the graph only for the labels in the module constant `FRAMEWORK_LABELS` (`mcp/airkg_tools.py:79`). That constant is imported once, when the process starts. At `a75400e5` it held seven labels:
- `FcsmConcern` joined at `0aad48fd` (2026-11-02 14:20Z).
- `AiReadyCriterion` and `ExtensionGroup` joined at `37b3b82a` (15:41Z).

The record, by contrast, is read from disk on first use (`Tools.record`). So the old process compared a 243-node record against a 7-label read of the graph. It reported as MISSING exactly the 11 nodes that make up those three labels.

The evidence:
1. Before any projection in this task, at 17:48Z, `tests/test_framework_projection_roundtrip.py` passed in full against `seldon-ai-readiness-kg`: 10 passed, 0 failed, 0 skipped.
2. A freshly started MCP server reported `green`, 243 compared, no mismatches, at the same time.
3. Cypher found all 11 ids present, before and after the projection run.
4. The current `projection_gate`, with `FRAMEWORK_LABELS` set to the `a75400e5` tuple and run against the live graph and the current record, reproduces the report exactly: `stale`, 243 compared, the same 11 mismatches.

The V3 RESULT's 16:00Z `green` came from an MCP process that the V3 session started itself, after `37b3b82a`.

**Corpus layer (step 5):** database `ai-readiness` is written by squiddy from the kit ledger `graphs/ai-readiness/ledger` (`python -m squiddy.project`; `squiddy/neo4j_store.py:159`). It is not built from `corpus/manifest.json` or `events/`. A `kg.manifest` admission does not reach it, and no projection run can put the two V3 documents there, because neither is in that ledger. I recorded this in Issue `abe74ad2`.

## §2 Premises the task file got wrong

1. **"The shared database held these nodes after 32e394f1's merge and lost them afterwards."** False. The nodes were present at 17:48Z, before this task wrote anything (§3 A1, §4 B3). The 17:2xZ `stale` was produced by the reader, not the graph (§1).
2. **"Expected: red on the 11 nodes above"** (A1). The gate was green: 10 passed.
3. **"Part B restores the projection."** There was nothing to restore in the framework layer. The `build_projection.py` run still did real work: the KG layer's `Document` count went from 288 to 290, adding `iso-iec-ieee-15939-2017` and `basili-caldiera-rombach-1994-gqm` from their `manifest_add` events. Before the run, the project database lacked both.
4. **"The MCP corpus layer (database ai-readiness) … neither of the two"** implied that a projection run would fix it. It cannot. Squiddy feeds that layer from its own ledger, and the two documents are not in that ledger or in `graphs/ai-readiness/corpus/manifest.yaml` (0 matches each). Following the "different command" clause, I considered `python -m squiddy.project --graph graphs/ai-readiness` and **did not run it**. Its Neo4j reset is `CREATE OR REPLACE DATABASE` (`squiddy/neo4j_store.py:127`), so it would rebuild the MCP-served corpus database from a ledger that does not contain the two documents. That would change nothing for them while putting a squiddy release's parity at risk. Getting them in needs an admission into the kit, which is in the Issue.
5. **"Run in the primary checkout"** (A1). The harness confines this session to its worktree. I ran the test there at `036c935b`: the same record as main, against the same shared database.
6. **"The V3 session's logs in worktree hidden-herding-pie."** That worktree was removed at merge. I read the session's stream-json dispatch log instead (`logs/dispatch/2026-11-02_v3_measurement_sheet.log` in the primary).
7. Incidental: the two V3 `substrate_converted` events (`events/`) carry an absolute `substrate_path` inside the removed worktree `hidden-herding-pie`. It is noted here only.

## §3 Part A quotes

**A1.** Command: `/opt/anaconda3/bin/python3 -m pytest tests/test_framework_projection_roundtrip.py -v -p no:xdist -p no:cacheprovider`, run at 17:48Z. Result: `10 passed, 1 warning in 13.39s`, `EXIT=0`. Failed 0, skipped 0, mismatch list empty.

`get_overview` from this session's own MCP server, at about 17:50Z:
```
"status":"green","nodes_compared":243,"mismatches":[]
```

**A2.** Code paths that write framework labels into `seldon-ai-readiness-kg`:

- **`scripts/load_framework_graph.py:124`**, inside `load()`: `session.run(f"MATCH (n) WHERE {pred} DETACH DELETE n")` over `ASSESSMENT_LABELS` (`:58-60`, all 11 labels including `FcsmConcern`, `AiReadyCriterion` and `ExtensionGroup`). It then MERGEs every record node (`:125-131`). This is the only code that deletes framework labels.
- **`scripts/build_projection.py:1056-1061`** calls `mod.load(session, …framework/ai_readiness_framework.json)` as its last layer.
- **`scripts/build_projection.py:613`, `:620`, `:631`** reset KG labels (`kg_labels`), `Term`, and unlabelled nodes. None of these touch framework labels.
- **`assessment/harness/scan/publish.py:604-605`** resets `Observation`/`Finding`/`Rule` only (`SCAN_LABELS`, `:504`).
- **Tests:** every `bp.build(...)` call in `tests/` passes a fake session (`test_build_projection_progress.py:64`, `test_build_projection_filters.py:128`, `test_replay_selection.py:101`, …). `tests/test_requirements.py:330` and `tests/test_framework_projection_roundtrip.py:56-61` load the loader module only for `ASSESSMENT_LABELS` and `flatten`. `tests/conftest.py:183-205` (`no_live_projection`) refuses any subprocess that names `build_projection.py`. No test loads a framework record into the shared database.
- **The `xdist_group` assignment** (`tests/conftest.py`, the `neo4j` group regex) only serializes the tests that read it.
- **The dispatcher's merge path:** `grep -rln -E 'build_projection|load_framework_graph' /Users/brock/GitHub/seldon/seldon` returned nothing, and `seldon.yaml` has no projection hook. `scripts/jobs/*` invoke neither.

**A3.** What ran in the window, from the logs:

- `logs/dispatch/2026-11-02_v3_measurement_sheet.log` (V3, 829a5010), tool calls between 16:18Z and 17:14Z:
  - `make gate-task` three times (16:27Z, 16:37Z, 17:00Z).
  - The regeneration script `/tmp/airkg_inspect/regen.sh` (16:57Z): `build_l0_report build_brief_pack build_evidence_map build_figures build_scan_catalog build_l0_site build_report_pdf`, none of which calls the loader.
  - `seldon prior-art verify`.
  - No `build_projection` and no `load_framework_graph`.
- `logs/dispatch/2026-11-02_land_dn019_and_redrive_v3.log` (4b329769): `make gate-fast` at 17:24Z and 17:33Z, then the RESULT. No projection or loader call.
- The Neo4j `query.log` logs only queries over 1 s. Its seven 2026-11-02 rows for this database are all reads (`MATCH (a:Artifact) …` and one `AssessmentIndicator` traceability read at 17:24:52Z). It holds no `DETACH DELETE`.
- MCP processes (`ps -eo pid,lstart,command`):
  ```
  17681 Fri Oct 30 06:56:38 2026  /opt/anaconda3/bin/python3 /Users/brock/GitHub/ai-readiness-kg/mcp/airkg_server.py
  18628 Fri Oct 30 06:56:48 2026  /opt/anaconda3/bin/python3 /Users/brock/GitHub/ai-readiness-kg/mcp/airkg_server.py
  23197 Mon Nov  2 12:47:50 2026  /opt/anaconda3/bin/python3 /Users/brock/GitHub/ai-readiness-kg/mcp/airkg_server.py   (this session)
  ```
- `git show a75400e5:mcp/airkg_tools.py`, lines 79-80:
  ```
  FRAMEWORK_LABELS = ("AssessmentCriterion", "AssessmentConstruct", "AssessmentIndicator",
                      "MeasurementSpec", "Action", "AssessmentTool", "Precondition")
  ```
- Reproduction (`logs/2026-11-02_repro_stale_labels.log`):
  ```
  CURRENT labels: {"status": "green", "nodes_compared": 243} mismatches 0
  OLD (Oct-22) labels: {"status": "stale", "nodes_compared": 243} mismatches 11
     {"node": "fcsm_20_04_accessibility_c1", ... "record": "present", "graph": "MISSING"}  … c2, c3, c4,
     aiready:accessible, aiready:understandable, aiready:accurate, aiready:open, ext:E, ext:F, ext:G
  EXIT=0
  ```
- The record read by every candidate is `framework/ai_readiness_framework.json` at `036c935b` (243 nodes; the 11 are indices 232-242). No candidate read another copy. The `state/` seeding copies no framework record (the seed set is `corpus/<dirs>`, `state/{docling_md,substrate_md,biblio_cache}` and `state/corpus_index.db`).

**A4.** In one sentence: there was no writer, because a Claude Desktop `airkg_server.py` process started on 2026-10-30, holding the 7-label `FRAMEWORK_LABELS` from `a75400e5`, compared the current 243-node record against a graph read that skipped the three labels added on 2026-11-02, as reproduced in §3 A3.

**A5.** The corpus layer:
- `mcp/airkg_guard.py:127-139` `corpus_database()` reads `graphs/ai-readiness/config.yaml`, which sets `engine.projection.backends[neo4j].database: ai-readiness` (`:191-193`).
- The writer is squiddy's projection, `python -m squiddy.project --graph graphs/ai-readiness` (`squiddy/project.py:248-263`, `write_neo4j`). It writes nodes at `/Users/brock/GitHub/squiddy/squiddy/neo4j_store.py:159`:
  ```
  s.run(f"UNWIND $rows AS r MERGE (n:`{label}` {{id: r.id}}) SET n += r.props", ...)
  ```
- That projection replays the kit ledger (`graphs/ai-readiness/ledger/*.jsonl`).
- A `kg.manifest` admission is **not** expected to reach it, with or without a projection run. `grep -c` for both doc ids returns 0 in `graphs/ai-readiness/corpus/manifest.yaml` and in every ledger shard, and 12 in `corpus/manifest.json`.

## §4 Part B quotes

**B1.** `python scripts/build_projection.py`, run detached:
- `START=2026-11-02T17:53:15Z`, `END=2026-11-02T19:24:31Z`, `EXIT=0`.
- KG layer: 36,855 nodes and 44,579 edges after replay. `document_skeletons total=290`.
- Framework layer:
  ```
  "framework": {"nodes": 243, "edges": 501, "evidenced_by_resolved": 209, "evidenced_by_missing_document": 0,
                "measures": 73, "rules_seen": 73, "rules_unparseable": [], "rules_without_indicator": []}
  ```

**B2.** `tests/test_framework_projection_roundtrip.py` after the run: `10 passed, 1 warning in 2.37s`, `EXIT=0`. Failed 0, skipped 0.

**B3.** Cypher on both layers after the run:
- `seldon-ai-readiness-kg`: all 11 present, with labels `FcsmConcern` ×4, `AiReadyCriterion` ×4 and `ExtensionGroup` ×3. `Document` count is 290, and `iso-iec-ieee-15939-2017` and `basili-caldiera-rombach-1994-gqm` each appear once. Before the run it was 288, with 0 and 0.
- `ai-readiness` (the MCP corpus layer): `Document` count 288. `iso-iec-ieee-15939-2017`: 0. `basili-caldiera-rombach-1994-gqm`: 0. These are unchanged, and expected to be unchanged (§3 A5).
- The record holds 0 `EVIDENCED_BY` edges citing either doc.

**B4.** `ls -la /Users/brock/GitHub/ai-readiness-kg/.seldon/`:
```
DISPATCH_STOP.held-2026-11-02
DISPATCH_STOP.off
DISPATCH_STOP.off2
DISPATCH_STOP.off3_2026-10-10_operator_fresh_week
attic_2026-09-21_g4_narrowed_ADDENDUM_01.md
dispatch.lock
dispatch_last_pass.json
dispatch_stuck.json
premise_review.json
stations.lock
```
`ls /Users/brock/GitHub/ai-readiness-kg/.seldon/DISPATCH_STOP 2>/dev/null; echo done` printed only `done`. The same check run in this worktree, which has no `.seldon/`, also printed `done`. I created and removed no STOP file.

## §5 Part C

1. **Issue `abe74ad2-4b00-457b-9c27-a96af57118d0`** was opened with importance high, urgency high, type `factual_error`, target `code`, detection `audit` (the closest of the CLI's five values to "Desktop OODA, projection gate stale"). Its name: "no eraser: the stale projection_gate came from a long-lived MCP server holding a pre-2026-11-02 FRAMEWORK_LABELS, not from the graph". Its description carries:
   - the evidence in §1 and §3;
   - the structural defect: the gate's label set is frozen at server start, so it can call a correct graph stale, and, after a label is removed, a stale graph green. The fix is to read `ASSESSMENT_LABELS` from the loader the gate already re-execs on every call;
   - the workaround: restart the Desktop MCP server after any merge that touches `mcp/` or the loader;
   - the corpus-layer finding (§3 A5).
2. B2 was green, so I appended the restore log path and the green line to both open Issues. Their state is unchanged (`open`), left for the next green daily run to close:
   - `004239b0` ("daily suite red: tests/test_framework_projection_roundtrip.py::test_node_and_edge_counts_match_the_json_exactly@neo4j");
   - `85353679` ("dispatcher held by a red suite that only a held task can fix (2026-11-02)"). This one also records that main now carries the FcsmConcern layer it described as graph-ahead.

   Both `seldon issue update` calls returned rc 0 (`logs/2026-11-02_issue_updates.log`). The three resulting events (`artifact_created` and `artifact_updated` ×2) are in `seldon_events.jsonl`.

## §6 Gate, verify and protected paths

**Gate tier: `make gate-fast`.** The write set touches no scan, scoring or record code. This is the fast tier only, not the full suite.

1. **Run 1: worktree not seeded.** This was an attempt to seed by shell script that the harness refused, so the run used a fresh worktree. Result: `16 failed, 3384 passed, 50 skipped, 41 xfailed, 1 error in 224.45s`, `EXIT=2`. Every failure was a gitignored input absent from a fresh worktree, for example `FileNotFoundError: …/corpus/kernel/w3c-dwbp-2017.md` and `…/corpus/crosswalk/usafacts-ai-ready-data-guide.pdf`. Log: `logs/2026-11-02_gate_fast_unseeded.log`.
2. **Run 2: seeding still not applied** (a second refused attempt). Result: `16 failed, 3384 passed, 50 skipped, 41 xfailed, 1 error in 239.89s`, `EXIT=2`. Log: `logs/2026-11-02_gate_fast_seeded.log`.
3. **Seeding.** `logs/seed_worktree.py` rsync-copied (no symlink, no `--delete`) the 15 corpus document dirs, `state/{docling_md,substrate_md,biblio_cache}` and `state/corpus_index.db` from the primary, as `scripts/jobs/airkg_daily_suite.sh` does. Result: `SEED_OK`, `EXIT=0`. Log: `logs/2026-11-02_seed.log`.
4. **Run 3: seeded.** Result: **`3443 passed, 8 skipped, 41 xfailed, 1858 warnings in 307.47s (0:05:07)`, `EXIT=0`. Deselected: the log prints no deselected count (0 lines match `deselected`; the run is under xdist).** Log: `logs/2026-11-02_gate_fast_seeded2.log`.

**`seldon verify`:** `EXIT=1`, with 0 `✗` and 2 `⚠`. Both warnings predate this task and neither comes from its write set:
- "Blocks and waits: 98ed1dd1 is blocked with no reason recorded".
- "Task source files: 5ae6744f [proposed] cc_tasks/2026-11-02_admit_usafacts_three_track_framework.md not on disk".

Log: `logs/2026-11-02_seldon_verify.log`.

**Protected paths:** `git diff --stat HEAD -- framework/ai_readiness_framework.json kg/schema.yaml docs/schema_v0.1.md docs/data/ai_readiness_framework.json` printed nothing (empty), with HEAD = `036c935b`, the branch base. The only tracked change in this task besides this RESULT is 3 appended lines in `seldon_events.jsonl`.

**Other logs** (all in this worktree's `logs/`, which is gitignored):
- `2026-11-02_roundtrip_before.log`
- `2026-11-02_check11_before.log`
- `2026-11-02_check11_after.log`
- `2026-11-02_docs_both_layers_before.log`
- `2026-11-02_docs_both_layers_after.log`
- `2026-11-02_projection_restore.log`, with its progress log `projection_20261102T175315Z.log`
- `2026-11-02_roundtrip_after.log`
- `2026-11-02_repro_stale_labels.log`
- `2026-11-02_issue_updates.log`

The read-only scratch scripts beside them are `scratch_check11.py`, `scratch_docs_kg.py`, `scratch_repro_stale_labels.py`, `scratch_scanlogs.py` and `scratch_update_issues.py`.

## §7 What the next OODA should do first

1. Restart the Claude Desktop ai-readiness-kg MCP server (quit and relaunch Claude Desktop), then call `get_overview`. Expected: `green`, 243 compared.
2. Author the fix for `abe74ad2`. The gate should take its labels from `load_framework_graph.ASSESSMENT_LABELS`, which it already re-execs on every call, and needs a test that a label added to the loader is compared without a restart. Write that test first.
3. Get the two V3 documents into the kit ledger (an admission into `graphs/ai-readiness`), or record that the corpus layer lags the manifest by design.

## §8 Session usage

`seldon dispatch part-complete` reported **168,014 tokens** at the end of Part C (input plus cache writes plus output, from the dispatch log), with a wall time of 6,767 s since launch. Most of the wall time was the 91-minute projection. The estimate was 0.3M tokens. There were no model calls through `model_stub`.
