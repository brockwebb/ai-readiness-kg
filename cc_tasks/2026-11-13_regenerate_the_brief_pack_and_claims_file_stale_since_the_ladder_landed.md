# CC Task: regenerate the brief pack and the claims file, stale since the USAFacts ladder landed in the record, so the daily suite goes green

**Date:** 2026-11-13
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on the daily suite).
**Implements:** the byte-for-byte regeneration guards of `tests/test_brief_pack.py` and `tests/test_evidence_map.py` (a generated view is rebuilt by its generator, never edited).
**Amended by:** none.
**Builds on:** `cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents_RESULT.md` (commit b5c940ce changed `framework/ai_readiness_framework.json`).
**Framework layer served (DN-005 §5 rule 1):** none; generated views brought back in step with the record.
**Fulfils:** its own ResearchTask.
**Model:** primary
**Spend:** est. 0.2M tokens, Claude Code session included. No model calls through model_stub. The task ends by printing its own session usage.
**Parts:** A 0.70, B 0.30.
**Part map:** A regenerates and proves green; B records why the gate missed it.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

The daily suite (`scripts/jobs/airkg_daily_suite.sh`) has been red on main every day from 2026-11-05T09:30Z to 2026-11-13T09:30Z, EXIT=2, the same four failures each day (`logs/daily_suite/2026-11-13T093005Z.log`):

- `tests/test_brief_pack.py::test_graph_free_pages_regenerate_byte_for_byte`
- `tests/test_brief_pack.py::test_every_page_names_its_generator_record_commit_and_cycle`
- `tests/test_brief_pack.py::test_full_pack_regenerates_byte_for_byte_and_nothing_else_is_there`
- `tests/test_evidence_map.py::test_claims_file_regenerates_byte_for_byte`

The assertion text names the cause: the brief pack pages and `docs/evidence/claims.yaml` stamp the commit of the framework record; they carry `37b3b82ae3de` and the record is now at `b5c940ce3aff` (task ec1112d3 added the USAFacts tracks, levels and prerequisites). The red suite wrote `.seldon/DISPATCH_STOP` and the dispatcher evaluated nothing for eight days. Desktop set that file aside on 2026-11-13 so this task can run; the daily job writes it again if main is still red.

## Part A: regenerate, prove green

1. Run the four tests first and quote the failures (expected: the four above, the stamp mismatch). Anything else is a premise the author got wrong; report it and continue.
2. Run `python scripts/build_brief_pack.py` and `python scripts/build_evidence_map.py` the way their own tests and docstrings say to (quote the command lines), detached and logged if either runs past a minute. Quote `git diff --stat`.
3. Read the diff. Expected: the record-commit stamp on every generated page, and whatever content the record change moves by design (the new lineage nodes and edges where a page or the claims file lists them). Quote three representative hunks. Any change that is neither is reported in the RESULT §1 and left in place (the generator is the authority); do not hand-edit a generated file.
4. Re-run the four tests; quote passed. If a test still fails, stop Part A and report the assertion; do not edit the test.
5. `make gate-fast`, detached and logged; quote passed, skipped, xfailed and deselected.

- check: `sh -c "git log -1 --format=%h -- framework/ai_readiness_framework.json"` prints a commit beginning `b5c940ce`.

## Part B: record why the gate missed it

ec1112d3 ran `make gate-task` to EXIT=0 and still left main red for the daily suite. Say, by file and line, which marker or selection keeps these four tests out of `gate-task` (the `-m "not slow"` selection in the Makefile, or another), and open one Issue (`seldon issue create`), importance high, urgency medium: "a task that changes the framework record passes gate-task while the brief pack and claims file go stale, and the daily suite then holds the dispatcher". Body: the eight red days, the four tests, the cause, and the evidence. Propose nothing; the design note that picks a fix is Desktop's.

Do not create or remove any file under `.seldon/`.

## Gate and RESULT

Write set: the regenerated files under `docs/brief/` (or wherever the pack generator writes; quote it) and `docs/evidence/claims.yaml`, logs, Issue events, `seldon_events.jsonl`. No record, no schema, no generator code. `seldon verify`, quote EXIT. Protected-paths diff on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json`: expected empty.

RESULT at `cc_tasks/2026-11-13_regenerate_the_brief_pack_and_claims_file_stale_since_the_ladder_landed_RESULT.md`: §1 the four tests before and after, first; then every quote above. Then `seldon cc complete`, commit, push.
