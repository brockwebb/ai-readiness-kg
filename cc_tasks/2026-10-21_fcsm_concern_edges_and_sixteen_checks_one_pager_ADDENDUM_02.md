# ADDENDUM 02 to `cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md`: resume from the orphaned worktree; Part A reaches main first

**Date:** 2026-11-02
**Status:** AMENDS the base task and ADDENDUM_01. Not a supersession.
**Authored by:** Desktop session, OODA on the 2026-10-23 dispatcher launch.

## What happened

The dispatcher launched this task on 2026-10-23 under `claude-opus-4-8` (log `logs/dispatch/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.log`, session ebd8af68) in worktree `.claude/worktrees/gleaming-munching-kahan`. Part A was carried out there: `scripts/apply_fcsm_concerns.py`, `tests/test_fcsm_concerns.py`, the record write-back and the projection. Part B's `scripts/sixteen_checks_build.py` was mid-edit (fit ladder gaining a `passes_mode` lever) when the API retried ten times and the session died at about 10:36Z; the task went `blocked` with nothing merged.

Consequence on main: the shared Neo4j projection now holds 4 `FcsmConcern` nodes and 23 `SERVES_FCSM_CONCERN` edges (Desktop query, 2026-11-02) while main's framework record has neither, so `tests/test_framework_projection_roundtrip.py::test_node_and_edge_counts_match_the_json_exactly@neo4j` fails and the daily suite has been red every day since (the only failure in `logs/daily_suite/2026-11-02T093004Z.log`: 1 failed, 3470 passed). That red run owns `.seldon/DISPATCH_STOP`, which holds the dispatcher, which cannot therefore launch the one task that repairs the cause. Desktop broke the loop on 2026-11-02 by moving the STOP file aside (Issue filed) and redriving this task.

## Step 0, amended

Base Step 0 item 3 required `projection_gate.status: green` before any write. It is red for the reason above and this task is the fix, so item 3 is replaced by:

3a. Confirm the orphaned worktree exists and carries Part A: `git -C .claude/worktrees/gleaming-munching-kahan log --oneline -20`, `ls scripts/apply_fcsm_concerns.py tests/test_fcsm_concerns.py scripts/sixteen_checks_build.py` there. Quote the branch name and its head.
3b. Bring Part A to main before anything else: merge (or cherry-pick, if the branch carries unrelated noise, and say which) the commits that add `apply_fcsm_concerns.py`, its test, and the framework record write-back. Then `python scripts/load_framework_graph.py` and `python -m pytest tests/test_framework_projection_roundtrip.py`. The roundtrip must be green on main before Part B starts; quote the counts. This is the base task's Part A, done once, from the worktree's work, not redone.
3c. Confirm the record's delta matches ADDENDUM-free DN-018 §4: 4 concern nodes, 16 `primary` edges, 7 `also` edges. A different count is a premise error to report, not to fix silently.

The rest of Step 0 stands (model check, read DN-018). ADDENDUM_01 items 1 to 5 are done (c1091b58, f74c3bb7, 2e6edb18) and are not repeated; item 5's claim is re-made by the dispatcher's own launch.

## Part B, amended

Continue `scripts/sixteen_checks_build.py` from the worktree's version, which is further along than main (main has no copy). The worktree's last edits added a `passes_mode` lever and a seven-step fit ladder; the build loop had not yet been updated to the new `rows()` and `render_pdf()` signatures. Finish that, run the build, and carry on with the base task's Part B checks unchanged. The ladder's extra step (cutting "It passes when" to its first clause) is permitted by the base task's "before any other change" rule only after the where-column cut; the build report records the setting used.

## Part C, amended

`make gate-task` as before. Additionally the RESULT's "Premises this task file got wrong" names the base task's Step 0 item 3 as unsatisfiable by a task that itself writes the record, and proposes the fix in one line (the gate is checked after Part A's projection, not before it) for the seldon backlog.

## Housekeeping this task owns

After the suite is green on main, `.seldon/DISPATCH_STOP.held-2026-11-02` (the file Desktop moved aside) is deleted; quote the deletion. If the daily run between now and then wrote a fresh STOP, leave it to the suite rule.
