# CC Task: the projection says where it is while it runs

**Date:** 2026-09-21
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-21_g4_narrowed_RESULT_02.md` ("Projection took ~65 min; the log is empty until the end").
**Implements:** `~/GitHub/CLAUDE.md` §15 point 3 (progress on a fixed interval) for `scripts/build_projection.py`. Points 1, 2 and 6 (per-unit persistence, resume, partial results) do NOT apply and are not built: the projection is reset-and-replay by design (`DETACH DELETE` then replay, `build_projection.py:376`), so a half-finished projection is a wrong graph, not a partial result; the only honest recovery is to run it again. Say so in the module docstring.
**Framework layer served (DN-005 §5 rule 1):** none. Tooling.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1.5M tokens (Sonnet-class task; the dispatcher launches on the default model). The RESULT ends with the measured session total.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Wait on detached commands with ONE blocking bash call (`until grep -q EXIT= <log>; do sleep 20; done`, 10 min timeout, repeated as needed). Targeted `grep`/`sed` reads only.

## Decisions

1. **Progress lines, to stdout and to `logs/projection_<UTC stamp>.log`,** at every phase boundary (reset, KG replay, vocabulary, overlays, scan layer, framework layer) and, inside any loop over documents or items, every `PROJECTION_PROGRESS_EVERY` items or 60 seconds, whichever first (`controls.yaml`, not a literal). Each line: phase, done/total when the total is known, elapsed, and the running node and edge counts. Flushed on write.
2. **A per-phase timing table at the end,** printed and written to the log, so the next reader knows whether the 65 minutes is the KG replay, the per-item `session.run` calls, or the scan replay. This task does not optimize anything; it measures. If the table shows one phase dominating and an obvious `UNWIND` batching fix, that is one sentence in the RESULT and a ResearchTask, not a change here.
3. **`--dry-run` prints the phase plan and exits** without touching Neo4j, so the gate can test the progress path without a 65 minute run.
4. **Tests:** progress lines appear at the configured interval against a fake session (monkeypatched `session.run`); the log file exists and ends with the timing table; `--dry-run` writes nothing to the graph. Existing projection tests unchanged.
5. **One measured run** of the real projection at the end, detached and polled, is the RESULT's evidence: quote the timing table. The graph after it must equal the graph before it (node and edge counts per label, from the fingerprint the script already computes at line 671).

**Write set:** `scripts/build_projection.py`, `controls.yaml` (one key with a comment), `tests/test_build_projection_progress.py` (new), this task's `scripts/check_protected_projection_progress.sh`, the RESULT. Everything else byte-identical; `framework/`, `state/`, `events/` untouched.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, protected paths; `make gate-full` is not required (no rule, payload or record changes). RESULT `cc_tasks/2026-09-21_projection_progress_RESULT.md`, under 30 lines: the timing table, the before/after fingerprint, the gate table, premises wrong, measured session tokens. `seldon cc complete`, commit, push.

**SEQUENCING:** 1, 3 → 4 → 2 → 5 → gate → RESULT → push.
