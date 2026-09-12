# RESULT — the framework record has one writer, and that writer refuses to drop what it did not author

**Task:** `cc_tasks/2026-09-11_framework_single_writer.md` (no addendum existed at start or before §3; globbed both times).
**Date:** 2026-09-11. **Spend:** zero model calls. **Network:** none.
**Gate (§3): PASS.** Every command in §6 ran to `EXIT=0` before this file was written.

## 1. Outcome in one paragraph

`scripts/framework_writeback.py::save` is now the only code that writes `framework/ai_readiness_framework.json`, and a static test over every module in `scripts/`, `kg/`, `assessment/` and `tests/` says so. It refuses a write that drops any node, edge or `counts` key the file on disk holds unless called with `force=True` and a reason (CLI: `--force --reason "<text>"`), names what it would drop and how many, and puts the full delta on the `framework_writeback` event. `scripts/build_framework_graph.py` no longer writes the file: it generates what the skeleton authors, merges that over the record on disk, and hands the result to `save`. Regenerating from the current skeleton over `HEAD` is a byte-for-byte no-op, asserted by a test, and the record itself is byte-identical to `HEAD` at the end of the task. The skeleton was not touched.

## 2. Decision 3 — what the skeleton does not author, by kind and count

Measured by `tests/test_framework_single_writer.py::test_what_the_skeleton_does_not_author_is_exactly_what_merge_preserves`, which asserts the list rather than typing it:

| kind | count | what |
|---|---|---|
| `MeasurementSpec` nodes | 22 | every spec, minted by `build_measurement_specs.py` and written back to since (`rule_id`, `decision`, E5's collector) |
| `MEASURED_BY` edges | 22 | indicator → spec |
| `AssessmentIndicator` node | 1 | `ind:A12`, the DD-054 candidate |
| `AssessmentConstruct` node | 1 | `con:A12-access-policy-coherence`, A12's construct |
| `EVIDENCED_BY_INTERNAL` edges | 3 | A12's internal refs |
| `EVIDENCED_BY` edges | 2 | A12's two sources |
| `DECOMPOSES_INTO` edges | 2 | `crit:A → con:A12…`, `con:A12… → ind:A12` |
| `counts` keys | 6 | `measurement_specs`, `collectors_none_known`, `rules_built`, `specs_with_recorded_decision`, `candidate_indicators`, `indicators_measured` |
| top-level key | 1 | `counts_basis` |
| indicator properties | 15 `measurement_status` promotions, 14 `measured_by` blocks, 1 `not_measured_reason`, A12's `candidate_provenance` / `candidate_rationale` / `candidate_promotion` / `recorded_by` | write-backs from the rule review, the scan cycles and the candidate adoption |

**The A12 defect had a second cause the a3a10 RESULT did not name.** The skeleton carries A12 in a `### Candidate indicators (not part of the framework)` table under §10, after the last criterion heading. The generator's criterion-G slice ran from `## 5d` to end of file and parsed that row as a G indicator with its "Where it came from" cell in the Status column — which is why a regeneration moved A12 "into G" and set a wrong status. `render_framework.skeleton_rows` already truncated at that heading; `build_framework_graph.parse` now makes the same cut, importing the heading constant from the renderer so the two cannot drift.

**Preservation needed no skeleton change.** The generator learned the merge (`build_framework_graph.merge`): authored properties (`AUTHORED_PROPS`, the six cells' worth) come from the skeleton; every other property, every non-authored node and every non-authored edge comes from the record on disk; `measurement_status` is a generator default that the record's value overrides. Key order is the record's, so an unchanged record serialises to the same bytes.

## 3. Decisions 1, 2, 4 — what was built

* `framework_writeback.py`: `delta(before, after)` (nodes by `id`, edges by `(from, type, to)`, counts by key; added and removed carried whole, changed as `{key: [before, after]}`), `drops`, `summarize_delta`, `serialize`, `load`, `add_force_args`, `force_kwargs`, `RefusedWrite`; `save` gains `force`, `reason`, the refusal, the `delta` and `delta_summary` on the event, `forced: {reason, dropped}` when forced, and **writes and logs nothing when the bytes would be identical** (`unchanged: True`), because an event that records no change is noise on the provenance trail.
* `build_framework_graph.py`: `generate()`, `merge()`, `build(current)`, `main` through `save` with `--dry-run --force --reason`.
* `build_measurement_specs.py`: the second regenerator that wrote the file directly, now through `save`. **Its dry run against the current record is refused**: it would drop `spec:A12` and its `MEASURED_BY` edge (A12's spec was added by another path) and, forced, would change 16 spec nodes (revert `rule_id`s, `decision`s and E5's collector) — `logs/` not kept for a dry run, reproduced by `scripts/build_measurement_specs.py --dry-run`. Making that script merge like the generator was not in scope; the refusal and the delta are, and they make its hazard visible instead of silent.
* All eight writer CLIs take `--force --reason` the same way (`test_the_cli_flags_are_the_same_on_every_writer`).
* `scripts/check_protected_single_writer.sh`, this task's zero-edits list.
* `CLAUDE.md`: one line under "Where to read first" naming the single writer.
* Existing events untouched (`test_existing_events_are_not_rewritten`).

## 4. Tests added — `tests/test_framework_single_writer.py`, 20 cases

Single writer: scanner positive control on five synthetic shapes; the scanner run against the two real pre-task writers at `bb660f9` (both caught); zero offenders across the four roots; the writer writes only inside `save`. Refusal: an edge drop, a node drop, a `counts` key drop, and **`generate()` itself over the record** (the exact incident) are refused, the file and the ledger untouched; `--force` without a reason refused; a forced drop is written with the reason and the removed edge on the event. No-op: skeleton over `HEAD` is byte-identical; through `save` it writes and logs nothing; the candidate table is not parsed; a simulated skeleton edit reaches the record while every write-back on the same node survives, in the same key order. Delta: before/after values on a changed spec, an added node and edge, `counts_moved`, and the delta applied to the old record reproduces the new one; dry run computes the delta and the refusal and writes nothing; a first write to an empty path is all-added.

## 5. Every premise the task file got wrong

1. **"Undoing DD-054" was two defects, not one.** The task attributes the A12 damage to regeneration dropping write-backs. Dropping was half; the other half was the parser reading the candidate table as criterion G (§2). A merge alone would have preserved A12's node and still overwritten its authored properties with the mis-parsed row.
2. **`build_framework_graph.py` was not the only direct writer.** `build_measurement_specs.py` wrote the record with `Path(a.json).write_text` too, and its regeneration is not idempotent against the current record (§3). The task named one script; the single-writer test found two.
3. **"Regenerating from the current skeleton over `HEAD` is a no-op" required the merge to exist first.** The plain generator differs from the record in 24 nodes, 31 edges, 6 counts keys and ~35 property values; it is a no-op only through `merge`, which is what decision 3 anticipated and what was built.
4. **Not wrong, but unstated:** the writer's own smoke of `framework_writeback_measured.py --dry-run` shows one pending change (E5's `not_measured_reason.cycle` would move from `scan_2026-09-09` to `scan_2026-09-10`), i.e. the last scan cycle's measured write-back was never run over E5. Not written here; reported.

## 6. Verification

```
logs/single_writer_gate_task.log   make gate-task — 1,943 passed, 17 skipped, 19 deselected,
                                   12 xfailed, 364.2 s; then 16 of 16 payloads re-derive   EXIT=0
logs/single_writer_guards.log      make guards — 25 passed, 16.0 s                          EXIT=0
logs/suite.log                     make gate-full — 1,962 passed, 17 skipped, 12 xfailed,
                                   1,299.9 s, detached and polled to EXIT                   EXIT=0
logs/single_writer_verify.log      seldon verify — all checks passed                        EXIT=0
logs/single_writer_protected.log   scripts/check_protected_single_writer.sh — PASS          EXIT=0
git diff --quiet HEAD -- framework/ai_readiness_framework.json   byte-identical
tests/test_framework_projection_roundtrip.py   5 passed against live Neo4j (inside gate-task)
tests/test_framework_graph.py::test_the_round_trip_reproduces_every_row_cell_for_cell   passed
```

changed: `CLAUDE.md`, `scripts/framework_writeback.py`, `scripts/build_framework_graph.py`, `scripts/build_measurement_specs.py`, `scripts/framework_writeback_{rules,measured,decisions,evidence,normalize}.py`, `scripts/add_candidate_indicator.py`.
new: `tests/test_framework_single_writer.py`, `scripts/check_protected_single_writer.sh`, this RESULT.
untouched: the skeleton, the record, `scripts/load_framework_graph.py`, `assessment/harness/`, `state/`, `corpus/`, `docs/reports/`, `events/`, every prior RESULT.

## 7. What the next task needs

`2026-09-11_report_sources_appendix.md` decision 4 moves A10's status, if it moves, through `framework_writeback.py`; that path now refuses drops and logs the delta, and a status change is a `nodes_changed` entry, not a drop.
