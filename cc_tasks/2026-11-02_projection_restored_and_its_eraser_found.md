# CC Task: restore the shared projection before the next daily suite, and find what erased the framework nodes after a green gate

**Date:** 2026-11-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on 829a5010).
**Implements:** DD-057 (a Cypher answer over the framework labels is the record only while the roundtrip gate is green).
**Amended by:** none.
**Builds on:** cc_tasks/2026-11-02_v3_measurement_sheet_RESULT.md §1 item 1 and §2.
**Framework layer served (DN-005 §5 rule 1):** none; projection integrity, so the daily suite does not hold the dispatcher again.
**Fulfils:** its own ResearchTask.
**After:** 2026-11-02_land_dn019_and_redrive_v3
**Model:** primary
**Spend:** est. 0.3M tokens, Claude Code session included. No model calls through model_stub. The task ends by printing its own session usage.
**Parts:** A 0.45, B 0.35, C 0.20.
**Part map:** A finds the writer; B restores the projection; C records both on the graph.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

At 2026-11-02T17:2xZ the ai-readiness-kg MCP `get_overview` reports `projection_gate.status: stale`, 243 nodes compared, 11 mismatches, every one `record: present, graph: MISSING`: `fcsm_20_04_accessibility_c1..c4`, `aiready:accessible`, `aiready:understandable`, `aiready:accurate`, `aiready:open`, `ext:E`, `ext:F`, `ext:G`. These are the nodes 9af5f624 and 32e394f1 added to `framework/ai_readiness_framework.json`, both merged to main today.

The V3 RESULT (§1 item 1) quotes the same tool at its Step 0, about 16:00Z, as `green`, 243 compared, no mismatches. So the shared database held these nodes after 32e394f1's merge and lost them afterwards. Open Issue "dispatcher held by a red suite that only a held task can fix" records the opposite mismatch (graph ahead of main); this one is graph behind main. The daily suite (`scripts/jobs/airkg_daily_suite.sh`, last run 2026-11-02T093004Z) runs `test_framework_projection_roundtrip.py` against this shared database; left as is, its next run fails, writes `.seldon/DISPATCH_STOP`, and repeats the two-week hold.

Also from the V3 RESULT §2: `corpus/manifest.json` admits `iso-iec-ieee-15939-2017` and `basili-caldiera-rombach-1994-gqm`, but the MCP corpus layer (database `ai-readiness`) holds 288 `Document` nodes and neither of the two.

## Part A: find the writer (read-only)

1. In the primary checkout, run `python -m pytest tests/test_framework_projection_roundtrip.py -v` (anaconda python, see `scripts/jobs/airkg_extraction_burn.sh` for the environment). Quote passed, failed, skipped and the mismatch list. Expected: red on the 11 nodes above. Anything else is a premise the author got wrong; report it and continue.
2. Identify every code path that writes framework labels (the five owned by `scripts/load_framework_graph.py`, plus `FcsmConcern`, the AI-ready criterion and extension-group labels) into the shared database `seldon-ai-readiness-kg`. Search `scripts/`, `assessment/`, `tests/` (including `tests/conftest.py` fixtures and the `xdist_group` assignment) and the dispatcher's merge path for: `load_framework_graph`, `build_projection`, `DETACH DELETE`, a reset of framework labels, and any test that loads a framework record into the shared database rather than a scratch one. Quote each by file:line.
3. Establish which one ran between 2026-11-02T16:00Z and the start of this task, from logs, not inference. Read at least: the V3 session's logs in worktree `hidden-herding-pie` (or wherever they survived the merge; `logs/2026-11-02_v3_gate_task_3.log`, `logs/regen_*.log`), `logs/dispatch/2026-11-02_v3_measurement_sheet.log`, `logs/dispatch/2026-11-02_land_dn019_and_redrive_v3.log`, and the projection logs if any. For each candidate: did it run in the window, which framework record did it read (path and git blob or sha256), and does that record carry the 11 nodes? A seeded worktree copies `state/` from the primary (V3 RESULT §5 item 5); check whether a copied file is the source of an older record.
4. If the writer is found, state it in one sentence with the evidence. If not, say so plainly, list what was checked, and leave the question open for Part C's Issue. Do not fix code in this task.
5. Corpus layer: name the code that projects `Document` nodes into database `ai-readiness` and say whether a manifest admission is expected to reach it without a projection run. Quote the line.

## Part B: restore

1. Run `python scripts/build_projection.py` detached and logged (`logs/2026-11-02_projection_restore.log`, `echo EXIT=$?` inside the `bash -c`), polled to its EXIT line. It projects all three layers (DD-057).
2. Re-run `tests/test_framework_projection_roundtrip.py`; quote passed, failed, skipped. Expected green. If red, stop Part B here and report the mismatches; do not edit the record or the test.
3. Cypher, both layers, quoted: the 11 node ids present in `seldon-ai-readiness-kg`; `Document` count in the corpus layer and whether the two admitted doc_ids are present. If Part A step 5 says the corpus layer is fed by a different command, run that command instead, logged and polled, and quote it.
4. Confirm `.seldon/DISPATCH_STOP` is absent; quote `ls .seldon/`. Do not create or remove a STOP file.

- check: `sh -c "ls .seldon/DISPATCH_STOP 2>/dev/null; echo done"` prints only `done`.

## Part C: record

1. Open one Issue (`seldon issue create`) titled from Part A's finding: the writer and its evidence, or "framework labels erased from the shared projection after a green gate, writer not found" with the checked list. Importance high, urgency high. Detection method: Desktop OODA, projection gate stale.
2. If Part B step 2 is green, update the two open Issues "daily suite red: tests/test_framework_projection_roundtrip.py::test_node_and_edge_counts_match_the_json_exactly@neo4j" and "dispatcher held by a red suite that only a held task can fix (2026-11-02)" with the restore log path and the green line. Leave their state for the next green daily run to close (the job removes only the STOP file it wrote; the Issues close on that evidence).

## Gate and RESULT

Write set: logs, Issue events, `seldon_events.jsonl`. No code, no record, no schema. Gate: `make gate-fast`, detached and logged; quote passed, skipped, xfailed and deselected. Then `seldon verify` (quote EXIT) and the protected-paths diff on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json` (expected empty).

RESULT at `cc_tasks/2026-11-02_projection_restored_and_its_eraser_found_RESULT.md`: §1 Part A finding first, in one paragraph; then every quote above; log paths in §6. Then `seldon cc complete`, commit, push.
