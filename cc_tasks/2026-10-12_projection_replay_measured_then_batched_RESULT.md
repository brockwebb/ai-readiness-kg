# RESULT: projection replay measured; stopped at decision 1, nothing batched

**Stopped after decision 1, as decisions 1 and 4 require.** The measured cause is not mainly per-event transactions. 67.6% of query time is server work: scans, because no property index exists and the KG edge and overlay queries match nodes with no label. Per-row commits are the other 32.4%. Batching removes only the commits, which leaves about 64 min of server work, so it cannot reach decision 4's 10 minutes. `scripts/build_projection.py` is byte-identical. The canonical export (decision 3) was built anyway, to serve as the next task's baseline.

## 1. Profile and measured cause (`scripts/profile_projection.py`; `Session.run` wrapped, server time = Bolt `t_first + t_last`)
- **Transactions:** 308,768 queries, each its own auto-commit transaction (no explicit transaction anywhere). Events per transaction ≤ 1.
- **Time split:** total query wall 5,654 s = server 3,823 s + commit/round trip 1,831 s. The network floor is 0.34 ms per `RETURN 1` (≈105 s in total); the rest of the 1,831 s is commit.
- **kg_replay:** 81,991 tx; 2,488 s wall; server 1,898 s (77%). The edge write `MERGE (a {key:$from_id}) MERGE (b {key:$to_id})` has no label, so its plan is AllNodesScan (85,306 db hits per lookup). It costs 47–51 ms per edge, ≈85% of it server time; 44,234 edges cost ≈2,000 s.
- **overlays / restorations:** 551 s and 174 s. The same scan comes from `MATCH (n {key:$key}) WHERE any(l IN labels(n) …)`, at ≈43–45 ms per row.
- **resolutions / thin_spans:** 218 s and 16 s. These do have a label (`MATCH (n:Concept {key})`) but no index, so each is a NodeByLabelScan over 13,830 Concepts (13–15 ms).
- **scan_layer:** 2,303 s, 188,566 tx, server 1,277 s and commit 1,010 s. It writes 83,973 `MATCH (o:Observation {obs_id}) MATCH (f:Finding {finding_id}) MERGE …SUPPORTS` at 17.6 ms each, two label scans per row (20,194 and 14,510 nodes), with no index. It is owned by `assessment/harness/scan/publish.py`, outside this write set.
- **The fast burst** (events 22,076–40,000, about 5 s): 17,924 events, of which 15,115 are `attribute_restored` / `attribute_nulled` / `grounding_relocated`. `kg_replay` issues no query for them; the overlays phase pays for the same events later, at 45 ms each, which is why its own 20,000–35,000 window is the slow one.
- **Neo4j state:** 5.26.8. `SHOW INDEXES` returns only the two built-in LOOKUP indexes, with no range index or constraint on `key`, `term_id`, `obs_id`, `finding_id`, `rule_id` or `id`.

## 2. Batch and index sweep (`--sweep`: 10,000 scratch `MERGE … SET` rows per arm; each arm writes new values; scratch label and index removed afterwards)
| | batch 1 (today) | 500 | 2,000 | 10,000 |
|---|---|---|---|---|
| no index, ms/row | 8.95 | 1.98 | 1.98 | 2.21 |
| indexed, ms/row | 7.10 | 0.037 | 0.014 | 0.010 |

Each commit costs about 7 ms; a label scan costs about 2 ms per 10,000 nodes. Each fix alone stays slow:
- Batching alone leaves the scans: the profile's ≥3,823 s of server work.
- Indexing alone leaves 308,768 commits at about 7 ms each, ≈36 min.

Both together measure 0.01–0.04 ms per row. The first run's sweep wrote identical values, so its commits wrote nothing and it under-measured commit cost (`logs/2026-10-14_projection_sweep.log`). It is superseded by `_sweep_2`.

## 3. Equivalence hashes (`scripts/projection_canonical_export.py`; scope from `controls.yaml` `projection.canonical_export`)
- After the profiled run: `ec4d207fbddbe599b3fb257c94540c274f3393a73f56279f31af70f3650d613f` (74,598 nodes, 166,789 relationships).
- After the sweep (proves cleanup): the same hash.
- After a second, unprofiled projection: the same hash, and `cmp` of the two canonical line files is identical.
- Volatile properties: none. No projection Cypher writes a write time, and two projections of one log hash equal. This hash is the next task's "before".

## 4. Wall clock per phase (s): the 10-11 log / profiled run / unprofiled run. There is no "after", because nothing changed
prepass 5.6/4.6/4.8 · reset 1.0/0.7/0.7 · document_skeletons 4.9/4.2/4.3 · vocabulary 40.5/30.5/30.2 · **kg_replay 2,686/2,488/2,391** · overlays 524/551/490 · restorations 184/174/168 · resolutions 234/218/207 · thin_spans 15/16/14 · fingerprint 0.3/0.2/0.2 · **scan_layer 2,493/2,303/2,218** · framework_layer 10.9/10.5/10.1 · **TOTAL 6,200/5,801/5,539**.

## 5. Premises wrong
1. "Time is transaction overhead, not work": refuted as the main cause. Server-side scanning is 67.6%; per-row commits are 32.4% and also have to be removed.
2. "The fast burst is a run of events that write nothing": confirmed for `kg_replay`, but the same events are the slow part of `overlays`.
3. "kg_replay dominated b3a2df60": it is 43%. `scan_layer` is 40% (2,493 s) and the task does not mention it.
4. "35 events/s": the measured rate is 38–48 events/s over the edge-bearing stretches.

The next task's fix is index first, batch second. Neo4j's Cypher manual says search-performance indexes are per label, and a pattern with no label cannot use one. Its MERGE guidance pairs MERGE with an index or constraint on the merge key. Its batching guidance is UNWIND with parameters. These are cited from the docs, not fetched this session (Network: none).
1. Create a range index or uniqueness constraint on every merge key. Indexes are schema, not graph content, so the canonical hash cannot move.
2. Give the label-less endpoint and overlay patterns a label. This needs a design: the 4,799 unlabelled endpoint nodes have no label to match on, and adding one changes the canonical form.
3. Then batch with `UNWIND`.

That is one task with its own equivalence gate against `ec4d207f…`, covering publish.py as well.

## 6. Gate and logs
- `make gate-task` (fast tier plus re-derivation): `3360 passed, 5 skipped, 41 xfailed`, then `25 passed`. Deselected is not printed under xdist in either run. Wall 3m57.8s; `EXIT=0` (`logs/2026-10-14_projection_measured_gate_task.log`).
- `seldon verify`: All checks passed, `EXIT=0` (`logs/2026-10-14_projection_measured_verify.log`). The protected-paths check `scripts/check_protected_projection_measured.sh` reports PASS, `EXIT=0` (`logs/2026-10-14_projection_measured_protected.log`).
- **Logs:**
  - Profiled run: `logs/2026-10-13_projection_profile_run.log`, `logs/projection_20261014T034027Z.log`, `logs/projection_profile_20261014T034026Z.json`.
  - Unprofiled run: `logs/2026-10-14_projection_run2.log`.
  - Sweep: `logs/2026-10-14_projection_sweep_2.log` and `logs/projection_sweep_20261014T052409Z.json`.
  - Exports: `logs/2026-10-14_canonical_{A,A2,B}.{log,jsonl}`.
  - Before: `logs/2026-10-11_standards_projection.log`.
- **Write set:**
  - New: `scripts/profile_projection.py`, `scripts/projection_canonical_export.py`, `tests/test_profile_projection.py` (2), `tests/test_projection_canonical_export.py` (6), `scripts/check_protected_projection_measured.sh`.
  - Modified: `controls.yaml`, `projection.canonical_export` block only.
  - The fixture test of batched against unbatched (§Gate) was not written, because no batching was built.
