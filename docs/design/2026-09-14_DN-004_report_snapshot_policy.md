# DN-004 — Design note: when the published report re-snapshots, and what it says when it does not

**Date:** 2026-09-14. Desktop design note; not a task. Under DD-001, DN-002, DN-003. Raised by `2026-09-14_rejudgements_on_the_log_RESULT.md` §2 and §7 item 1: the report's snapshot `scan_2026-09-10_rj2` has a successor on the graph, `scan_2026-09-10_rj3`, differing in reason strings only, zero verdict moves.

## Decision

1. **The report re-snapshots when a number it publishes would change**: any tagged Result's value, any published matrix cell, any figure numeral, or any verdict a quoted rate is computed from. A successor generation that moves none of those does not force a republication; requiring one would make every sentence-level rule correction a publication event and would train the project to leave corrections unpublished.
2. **When it does not re-snapshot, the report says so, from the graph.** The generated version block carries one line: the snapshot cycle, the current successor cycle, the count of verdict moves and reason-only changes between them (from `SUPERSEDES` and the re-judgement diff), and the generation. Nothing typed; a test asserts the line agrees with a query at build time, and the site's `results_tagged.json` carries the same fields.
3. **The check is a standing guard**, not a task: on every build, if the snapshot's successor moves any published number, the build refuses and names the numbers. A refusal is the signal to re-snapshot, which is then a report-revision task under DN-002.
4. **Provenance is unchanged.** The 33 Results computed from the rj2 matrix stay `COMPUTED_FROM` it; the graph already says rj2 is superseded and by what. Re-pointing provenance at a matrix with identical values would rewrite what was computed from.
