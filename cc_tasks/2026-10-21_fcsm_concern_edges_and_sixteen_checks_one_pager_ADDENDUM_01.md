# ADDENDUM 01 to `cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md`: the dispatcher comes back on in Step 0

**Date:** 2026-10-21
**Status:** AMENDS the base task. Not a supersession.
**Authored by:** Desktop session, on the operator's instruction (2026-10-21 20:37 America/New_York: "I want the dispatcher enabled").

## What changes

The base task's **Fulfils** line says this task does not change `dispatch.enabled`, and its **Out of scope** section lists the flip and the STOP file as operator housekeeping. Both are withdrawn. The operator has ordered the dispatcher on, and a Desktop session cannot do it cleanly (`seldon.yaml` is outside the governed commit roots, so a Desktop edit leaves the dirty tree the dispatcher refuses on, c7). This task is the hand-dispatched session that does it.

## Step 0, new item 0 (before every other Step 0 item)

1. In `seldon.yaml`, set `dispatch.enabled: true`. Change nothing else in the file.
2. Remove `.seldon/DISPATCH_STOP` only if its contents name task b694c14a or carry no daily-suite log path. If the file names a `logs/daily/` or `airkg-daily-suite` log, leave it, quote its contents in the RESULT, and continue: a red daily run owns that STOP and the next green run clears it (suite tiers rule 3). Quote the file's contents either way.
3. Commit that one path (plus the removed STOP file, if removed) as its own commit, message `dispatch: enabled per operator 2026-10-21`, and quote the sha.
4. `make gate-fast` is not run here; `tests/test_dispatch_config.py::test_the_dispatch_block_is_complete_and_the_dispatcher_is_enabled` and `tests/test_cadence_template.py::test_the_cadence_list_is_empty_and_loads` were red while `enabled` was false (open Issues). Run those two tests alone now and quote passed, skipped, xfailed, deselected. If either is still red with `enabled: true`, stop and report; do not proceed to Part A on a red dispatch config.

The rest of Step 0 and Parts A to C are unchanged.

## Sequencing consequence

Once committed, the standing dispatcher (launchd, `seldon dispatch once` every 5 minutes) sees this task as a registered candidate with a dirty-tree check that this session's own commits keep clean. The dispatcher must not launch a second copy of a task a hand session is running (DN-006 decision 10). Therefore item 5: immediately after item 3, `seldon task update 9af5f624 --state in_progress` (or the equivalent `seldon cc` claim), so the task is no longer `proposed` and the dispatcher skips it. Quote the state transition. The base task's Step 0 item 1 (register if not landed) is moot: the task is registered as 9af5f624 (commit 04e63c4a).

## RESULT

Add a section "Dispatcher" quoting items 1 to 5. The open Issues for the two red tests are closed by the session with `seldon issue update` once item 4 is green, naming this task.
