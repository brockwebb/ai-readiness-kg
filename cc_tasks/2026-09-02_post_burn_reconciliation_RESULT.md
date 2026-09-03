# RESULT: Post-burn reconciliation — errata, Result registration, slide 15/brief, projection rebuild at burn close, DD-032

**Task:** `cc_tasks/2026-09-02_post_burn_reconciliation.md` (no addenda existed at execution time)
**Date:** 2026-09-02
**Model calls:** 0

## 1. Outcome

All six steps done. Two errata files issued (no RESULT edited). Twenty Result artifacts registered
with `computed_from` / `generated_by` provenance, every one linked to the deck RESULT (registered as a
snapshot DataFile). Slide 15 is content v5 with 211 admitted and every number resolvable to a Result;
the brief's admitted count and demand-ledger paragraph are current. The burn driver now replays the
projection as the final step of a completed burn (stale marker on unreachable Neo4j), and the gate
runner refuses to report while the projection lacks the newest declared corpus epoch. DD-032 is
appended. Suite 631 → 641 passed; `seldon verify` clean.

## 2. Errata (step 1)

| file | corrects | wrong → measured |
|---|---|---|
| `cc_tasks/2026-08-30_bulk_extraction_v038_ERRATUM-01.md` | §21.6 | 37/1,474 = 0.0251 [0.0183, 0.0344], "fourteen judged, 13 accept" → **37/1,480 = 0.0250 [0.0182, 0.0343]**, fifteen batches, fourteen judged, **14 accept**, 1 sampling_inconclusive |
| `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_ERRATUM-01.md` | §2.4 closing sentence | copied §21.6 instead of summing its own table; table sums to 37/1,480, 14 accept |

Wilson interval recomputed here (z = 1.959964): 37/1,480 → p = 0.025000, [0.018191, 0.034268].
Cross-check: 37/1,474 → [0.018266, 0.034407], i.e. §21.6's interval was correct for its wrong
denominator. Batch-by-batch derivation from `state/bulk_v038_burn.json` is in the erratum.

## 3. Result artifacts (step 2)

All `proposed`, linked `computed_from` the named DataFile(s) and `computed_from` DataFile
`deck_numbers_post_burn_RESULT` (`e2b67c87`, snapshot of `cc_tasks/2026-09-02_deck_numbers_post_burn_RESULT.md`).
Graph counts are additionally `generated_by` Script `build_projection` (`e6dc5182`, `scripts/build_projection.py`).
New DataFile artifacts: `bulk_v038_burn_state` (`4c0d79ad`, `state/bulk_v038_burn.json`, snapshot),
`t2_priority` (`9e58f0e6`, `state/t2_priority.json`, snapshot). Existing `corpus-manifest` (`ed75f634`) reused.

| units (result name) | value | id | computed_from |
|---|---:|---|---|
| v038_pooled_fabrication_F | 0.0250 | `410cdb4c-47f6-4e96-aec3-3a2defab893b` | burn state |
| v038_pooled_fabrication_F_wilson95_lower | 0.0182 | `12b4bb5e-fe2a-44d0-9a0d-81e8d132bebd` | burn state |
| v038_pooled_fabrication_F_wilson95_upper | 0.0343 | `4930ee88-58a3-421e-a5c4-7aab04aad293` | burn state |
| v038_judged_facts_n | 1480 | `8bc24cb0-31f0-4ebc-9a5a-929e0746fc7d` | burn state |
| v038_fabrications | 37 | `bd5e5ca1-0342-485a-8100-ee32b505a8f0` | burn state |
| v038_batches_total | 15 | `4335375b-f673-4273-b4fe-74ca0204f413` | burn state |
| v038_batches_judged | 14 | `e82fd68d-81b7-4b3c-a086-8bbe67367f0c` | burn state |
| v038_batches_accept | 14 | `741c9e05-59d0-4ee0-9719-70bf7c239107` | burn state |
| v038_batches_sampling_inconclusive | 1 | `d8818006-4823-4495-9663-1c78c27dea53` | burn state |
| v038_batches_reject | 0 | `b78a6a54-9453-4e2b-84ec-9def5c5bb1d0` | burn state |
| v038_batches_quarantine | 0 | `aa41eba9-829c-4c5d-bb4e-6b38465b3320` | burn state |
| documents_admitted | 211 | `e9dacc88-8fef-4e24-b5ee-e34d9a24f481` | corpus-manifest |
| documents_extracted_v038 | 35 | `e9feebb3-10e4-44ae-991f-9fd68b5762a3` | corpus-manifest |
| crosswalk_demand_units_total | 43 | `71d5200c-f9c8-4da9-8a4e-0c911823ce08` | t2_priority |
| crosswalk_demand_units_covered | 43 | `dfe40fb4-895c-4d47-919c-64bbd4b0e07c` | t2_priority |
| graph_v038_nodes | 10305 | `7e6ff35c-8739-464b-a80c-6ad15342bd53` | build_projection |
| graph_v038_edges | 11914 | `d673fb71-5556-4147-9238-13eff93e270c` | build_projection |
| graph_kg_nodes_non_document | 18844 | `30c6636f-404e-4411-8c1f-b323a625e1b3` | build_projection |
| graph_document_nodes | 211 | `6eb52a11-decc-413f-ad6b-e8b8aff91030` | build_projection |
| graph_kg_edges | 22141 | `78a29a82-2e2a-428a-aa5d-3089e5b73b84` | build_projection |

Each description carries the derivation (command or Cypher). `seldon result list` shows all twenty.

**Recount after the rebuild (step 4, `build_projection.py` exit 0, 2026-09-02):** v038 nodes 10,305 and
edges 11,914 unchanged (no new extraction); non-Document KG nodes 18,844 unchanged (by epoch:
bulk-v038 10,305, v1 4,504, kernel-v03 3,755, null 280); **Document nodes 194 → 211**, all 17
batch-025 doc ids present by id; KG-label edges 22,141 unchanged (Document nodes gain edges only on
extraction). The 17 G1 documents are not extracted, per the task.

## 4. Slide 15 and brief (step 3)

`docs/crosswalk/deck_content_2026-09-01.md`: header v4 → v5 with a one-line note; `**Numbers:**`
line now points at the registered Results; slide 15 bullet 1 reads 211 admitted (17 G1-EVAL sources,
admitted 2026-09-02, not yet extracted), "35 of the 211" extracted, and states the whole-graph count
as 18,844 non-document nodes + 211 document nodes and 22,141 edges. Bullets 2–3 unchanged (their
numbers were already the measured ones). Deck rebuilt to `docs/crosswalk/framework_deck_2026-09-02.pptx`
(overwritten, same day): 18 slides, no splits, slide 15 text contains the three new phrases and no "194".

`docs/crosswalk/meeting_brief_2026-09-01.md`: admitted sentence → 211 with the G1 clause; demand-ledger
paragraph → 43 of 43 units over 35 documents, all covered; queue now 156 deferred (zero demand), 3
skipped_oversize, 17 not_requested (G1 sources). Nothing else changed.

## 5. Projection rebuild at burn close (step 4)

- `controls.yaml` schema 0.3 → 0.4, append-only `projection:` block: `replay_script`, `stale_marker`
  (`state/projection_stale.json`), `python` (null = driver's interpreter).
- `scripts/run_chunked_bulk.py`: `burn_complete(plan, settled, halted)` (pure) and `close_burn(probe, replay)`;
  `phase_burn` calls it only when the loop ran to the end, every dispatching batch is settled, and
  `--max-batches` is unset. Unreachable Neo4j or a non-zero replay writes the marker (reason, profile,
  task, written_at, replay argv), prints its path, and returns — the burn never fails on it.
- `scripts/build_projection.py`: `projection_config()`, `newest_corpus_epoch()` (newest
  `corpus_epoch_declared` by timestamp across `corpus/evidence/decisions.jsonl` and the shards),
  `missing_epoch_members()`, `projected_document_ids_live()`, `neo4j_reachable()`; `main()` retires the
  marker after a successful replay.
- `scripts/run_baseline_gates.py`: `refuse_if_projection_stale()` before any report is written; raises
  `ProjectionStaleError` naming the epoch and the missing doc ids.
- Tests: `tests/test_projection_at_burn_close.py` (10, red first). `tests/conftest.py` gains an autouse
  guard: the live probe and live document read raise, and `subprocess.run` refuses any argv naming
  `build_projection.py`. `tests/test_bulk_v038.py`'s `plan_isolation` fixture stubs `close_burn`.

**Incident during this task.** The first version of the step-4 tests drove `phase_burn` to completion
without stubbing the close and spawned the real `build_projection.py` against the live database
(21:40Z), concurrently with this task's own rebuild, which then failed with
`Neo.ClientError.Statement.EntityNotFound`. The guard above is the fix; after it, a full suite run
spawned no replay and left no marker, and the rebuild was rerun cleanly (detached; a foreground run
exceeds a 10-minute shell limit). The 09-02 deck task hit the same "who rebuilds the graph" gap from the
other side; both are closed by the close hook.

**Premise discrepancy.** The task says to read the newest `corpus_epoch` "in the event log".
`manifest_add` events carry no epoch field and batch-025 has none; epochs are declared on
`corpus/evidence/decisions.jsonl` (`corpus_epoch_declared`, g1eval with 17 members) and, for older
epochs, on shards. The check reads both. `kg.queue.corpus_epochs()` reports g1eval-2026-09-02 = 17.

## 6. DD-032 (step 5)

Appended to `docs/design_decisions.md`: outcome classes, `empty_failure` release-and-back-off under
`controls.yaml spend.empty_failure_*`, `error_with_output` keeps DD-022's settle-at-estimate, the
merge-by-batch-id state file with immutable verdicts and `verdict_conflict`; cites the 2026-09-01 03:01Z
incident and the spend-guard RESULT §1.2 evidence.

## 7. Verification (step 6)

| check | before | after |
|---|---|---|
| `python -m pytest tests/ -q` | 631 passed | **641 passed** |
| `seldon verify` | — | All checks passed |
| `seldon result list` | 0 burn-headline Results | 20 |

## 8. Files

Created: the two ERRATUM files, `tests/test_projection_at_burn_close.py`, this RESULT.
Modified: `controls.yaml`, `docs/crosswalk/deck_content_2026-09-01.md`, `docs/crosswalk/framework_deck_2026-09-02.pptx`,
`docs/crosswalk/meeting_brief_2026-09-01.md`, `docs/design_decisions.md`, `scripts/build_projection.py`,
`scripts/run_baseline_gates.py`, `scripts/run_chunked_bulk.py`, `tests/conftest.py`, `tests/test_bulk_v038.py`,
`seldon_events.jsonl` (artifact/link/result events).
Not touched: any `*_RESULT.md`, `state/bulk_v038_burn.json`, the ledger, manifest, event shards.
