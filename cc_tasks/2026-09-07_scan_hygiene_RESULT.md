# RESULT — scan-hygiene

**Task:** `cc_tasks/2026-09-07_scan_hygiene.md` (no `_ADDENDUM*` siblings exist; globbed before starting)
**Date:** 2026-09-07
**Spend:** zero model calls, zero network. The only processes launched were `pytest`, `git`, `seldon`, `scripts/build_projection.py` and this task's own scripts. No federal host was touched; the only HTTP in the run was against the local control fixture server on `127.0.0.1`.

---

## 0. Gate — PASS

`cc_tasks/2026-09-07_scan_hygiene.md` §4, all four clauses, in the order the task lists them. The standing reader is `tests/test_scan_hygiene.py` (13 tests); the Neo4j clauses were also run standalone against the live graph after `scripts/build_projection.py` completed (exit 0).

**1. `pytest tests/ assessment/` leaves `corpus/` untouched.**

```
1495 passed, 2 skipped, 24 warnings in 698.75s (0:11:38)

$ git status --porcelain corpus/   # before the suite -> 261 lines (260 pending renames + the
                                   # new quarantine dir); after the suite -> byte-identical
IDENTICAL — the suite added nothing
```

Before this task the same command wrote 24 new blobs per run of `tests/test_scan_harness.py` alone.

**2. No Finding is both unsupported and unannotated; the annotated count is 120.**

```cypher
MATCH (f:Finding) WHERE NOT (:Observation)-[:SUPPORTS]->(f)
  AND coalesce(f.evidence_unretained, false) = false RETURN count(f) AS n   -> 0
MATCH (f:Finding) WHERE f.evidence_unretained = true  RETURN count(f) AS n  -> 120
MATCH (f:Finding)                                     RETURN count(f) AS n  -> 1353
```

and from `scripts/build_projection.py`'s own summary: `"findings_evidence_unretained": 120`.

**3. `counts` equals a recount of `nodes`/`edges`; every `EVIDENCED_BY_INTERNAL` entry has one key shape.**

```
$ python scripts/framework_writeback_normalize.py --check
{"counts_drift": {},
 "internal_ref_key_shapes": [["artifact_path"]],
 "internal_refs_all_prefixed": true,
 "rules_built_expected": 17, "rules_built_recorded": 17}
```

`rules_built` is the one key `recount` cannot derive from the JSON and it has its own reader; see §3.

**4. Zero UNCITED fixture-host blobs under `corpus/evidence/scan/`.**

```
$ python scripts/quarantine_fixture_evidence.py --dry-run
{"quarantined": 0, "untracked_litter_removed": 0, "cited_fixture_blobs_left_in_place": 8,
 "non_fixture_blobs": 1167, "distinct_body_hashes_cited_by_the_log": 757, "applied": false}
```

**This clause is implemented in a narrowed form and the narrowing is a decision, not a threshold move — see §7.3.** The task's literal clause ("zero blobs contain the fixture host") would have required quarantining the eight blobs the control cycle's own Observations cite, stranding live evidence. The gate checks *uncited* fixture-host blobs, and the test carries that reasoning on its face.

**Also green:** `seldon verify` — all 12 checks passed.

**Registered:** `scan_control_findings_evidence_unretained_2026-09-06` = 120, `scan_evidence_fixture_blobs_quarantined` = 260, both confirmed in the graph.

---

## 1. §2 — the tests stop writing into the evidence store

**The guard.** `tests/conftest.py` gains `no_writes_to_the_real_evidence_store`, autouse, alongside the four guards already there for the event log, the substrate store, the `seldon` CLI and the live projection. It does two things:

- repoints `scan.model.EVIDENCE_ROOT` at a per-test tmp directory. That alone is the fix, and it works because `store_evidence` reads the global at CALL time (`root or EVIDENCE_ROOT` inside the body) — the module-path-global convention CLAUDE.md §Conventions records exists for exactly this;
- wraps `store_evidence` in every module that holds its own binding of it (the model plus each collector, which did `from ..model import store_evidence` and so would not see a patch on the model alone), refusing any call whose resolved root is the real one. The module list is built once at import, not per test, because the fixture runs on all ~1,500 of them.

**Verified, not assumed:** the five fixture-driving tests of `tests/test_scan_harness.py` were re-run under the guard and the real evidence store did not change. `tests/test_scan_hygiene.py::test_a_fixture_collection_writes_nothing_into_the_committed_evidence_store` drives a real fixture collection and counts the store before and after, so the property has a standing reader rather than a one-off measurement.

**The sweep.** `scripts/quarantine_fixture_evidence.py`, re-runnable, `--dry-run`:

```
{"quarantined": 260, "untracked_litter_removed": 48, "cited_fixture_blobs_left_in_place": 8,
 "non_fixture_blobs": 1167, "distinct_body_hashes_cited_by_the_log": 757, "applied": true}
```

- **260** tracked blobs moved to `corpus/quarantine/evidence_scan_fixture/` under their own digest, with one `reason.txt` naming every one of them and stating the discriminator, the date and the counts. Moved, never deleted (invariant 2); git shows them as renames.
- **48** blobs of the same kind, written by this task's own diagnostic runs of `tests/test_scan_harness.py` and never committed, were **removed** rather than moved. The distinction is invariant 2's own: it protects bad *acquisitions*, and an uncommitted test output was never an acquisition. Quarantining them would have added 48 files of scratch to the tracked tree, which is what this sweep exists to take out of it. Both counts are on the `reason.txt` header and in the script's output.
- **8** fixture-host blobs were left in place: Observations on the log cite their `body_sha256`. See §7.3.

**§2's confirmation clause, checked in the graph:**

```
MATCH (o:Observation) WHERE o.evidence_hash IN $quarantined_digests RETURN count(o)   -> 0
MATCH (o:Observation)-[:SUPPORTS]->(f:Finding)
  WHERE o.evidence_hash IN $quarantined_digests RETURN count(DISTINCT f)              -> 0
```

Zero, as it must be by construction — an uncited digest cannot be cited by a node projected from the citations. The independent check is recorded because the task asked for it, not because it could have come out otherwise.

`assessment/harness/scan/fixtures/server.py` gains `BIND_HOST = "127.0.0.1"`, used by the bind, the served base URL and the sweep's marker. Two literals would be two definitions of "what a fixture body looks like", and the one that drifted would be the one that mattered (`tests/test_scan_hygiene.py::test_the_fixture_host_is_named_once`).

---

## 2. §1 — the 120 orphan control Findings, annotated

**The annotation.** `scripts/annotate_orphan_findings.py` appends one `finding_evidence_unretained` event per orphan Finding to `events/batch-032.jsonl` — a new shard, checked to be free and refused if it ever holds events of another kind. Idempotent: a second run writes nothing.

Each event carries `finding_id`, `rule_id`, `leg`, `target_doc_id`, `cycle`, `params_hash`, `missing_obs_ids`, the task's `reason` string verbatim, `annotated_by`, and two facts the task did not ask for but that a reader of the log needs:

- `cycle` — resolved by joining the Finding's `params_hash` to the `params_hash` of a surviving cycle payload in `state/`. 60 resolve to `scan_smoke_2026-09-06`; 60 have no surviving payload and carry `null` rather than a name invented for them.
- `params_recoverable` / `params_committed_at` — whether any committed revision of `assessment/harness/scan/params.yaml` hashes to the Finding's `params_hash`, recomputed from the bytes in git. 60 of 120 are `false`. Those cannot be re-derived even if their Observations were recovered, which is a stronger and more useful statement than "the evidence is missing".

**The projection.** `publish.py::project` reads the annotations in a pass BEFORE the replay — an append-only correction may land on a later shard than the record it corrects, and a single forward pass would project the Finding before seeing the event that qualifies it (the same shape as `edge_endpoint_alias` in batch-005). It then sets `Finding.evidence_unretained` on **every** Finding, true or false: an absent property and a false one read alike to `coalesce`, and an integrity check deserves an answer that is stored rather than inferred from a missing key.

**The standing rule.** `publish.py::write_events` now refuses to publish a Finding whose cited `obs_id`s are neither already on the log nor in the same payload, unless a `finding_evidence_unretained` annotation exists for it. It fails loud and writes nothing — the check runs before any append, so a refused payload leaves the log exactly as it found it. Both branches are tested on a synthetic orphan against a tmp event log (`test_publish_refuses_a_finding_whose_evidence_is_not_on_the_log`, `test_publish_admits_the_same_finding_once_it_is_annotated`).

**The re-derivation gate is untouched, read rather than assumed.** `assessment/harness/scan/rederive.py:56-57` builds its `recorded` set as

```python
recorded = {f["finding_id"]: f for f in
            payload["findings_detail"] + payload.get("control_findings_detail", [])}
```

— i.e. from a cycle PAYLOAD, never from the event log. Checked directly: **zero** of the 120 orphan `finding_id`s appear in any of the four surviving payloads.

| payload | recorded | overlap with the 120 |
|---|---|---|
| `state/scan_smoke_2026-09-06.json` | 286 | 0 |
| `state/scan_controls_2026-09-06.json` | 33 | 0 |
| `state/scan_2026-09-07.json` | 437 | 0 |
| `state/scan_2026-09-07_controls.json` | 33 | 0 |

The 286-of-286 gate's denominator is the first row, and none of these 120 was ever in it.

---

## 3. §3 — the framework of record, self-consistent

The premise this section was authored from is wrong in the way §7.4-7.6 record. What was actually built is the guard the premise was reaching for.

**`scripts/framework_writeback.py`** — the one place a write-back goes through:

- `recount(g)` regenerates every `counts` key derivable from `nodes`/`edges`, with each key's denominator stated. Two denominators, and the split is not stylistic: counts of what the **framework** holds exclude candidate indicators and their constructs (DD-054); counts of what the **instrument** holds include every spec, adopted or not (which `tests/test_framework_graph.py:131` already asserts). `rules_built` is deliberately absent — it is a fact about `assessment/harness/scan/rules`, and five spec `rule_id`s name rules that were never built (`RULE-C4-auto-v0`, `RULE-F2-v0`, `RULE-F3-v0`, `RULE-G1-O-v0`, `RULE-G3-v0`), so deriving it from the specs would overcount by five. It has its own reader instead.
- `apply_counts(g)` merges the recount and stamps `counts_basis` onto the record, so a reader of the JSON never has to find a script to learn what a number is a count of. It returns the keys that MOVED, so a caller reports drift rather than swallowing it.
- `save(...)` writes the JSON **and** appends the `framework_writeback` event, so the write and the record of the write cannot come apart. The event carries the sha256 of the bytes written — "which revision of the record does this projection correspond to" becomes answerable from the log rather than from a commit message.

**The shard is TAGGED** — `events/batch-033_framework.jsonl`. `kg/eventlog.replay()` skips tagged shards by design ("tagged shards hold events that are NOT part of the graph"), and it must here: the framework layer is projected from the JSON by `scripts/load_framework_graph.py`, never from the log. These events are a provenance trail, not a projection source; putting them on an untagged shard would feed the graph replay events no projector knows how to read.

**All four write-backs now go through it** — `framework_writeback_rules`, `_measured`, `_decisions`, `add_candidate_indicator` — replacing four ad-hoc recomputations of four different subsets. Each remains idempotent; all three re-run dry against the normalised file and report the same `framework_sha256` the file holds.

**`scripts/framework_writeback_normalize.py`** rewrote A12's three `EVIDENCED_BY_INTERNAL` edges onto the shape the other seventeen use — `properties.artifact_path`, `to: "internal:<ref>"` — and refuses any third key shape rather than silently dropping it. The reference TEXT is never rewritten; only the key it sits under and the node-id prefix. `scripts/add_candidate_indicator.py` was fixed to mint that shape, so the next candidate does not need a third repair.

`--check` on the file as it stood **before** this task touched it:

```
{"counts_drift": {},
 "internal_ref_key_shapes": [["artifact_path"], ["ref"]],
 "internal_refs_all_prefixed": false,
 "rules_built_expected": 17, "rules_built_recorded": 17}
```

and after:

```
{"counts_drift": {},
 "internal_ref_key_shapes": [["artifact_path"]],
 "internal_refs_all_prefixed": true,
 "rules_built_expected": 17, "rules_built_recorded": 17}
```

`counts_drift: {}` in the first block is the measurement that refutes §7.4: nothing had drifted, and the twelve stored values are reproduced key for key by `recount`.

---

## 7. Every premise this task got wrong

The task file's §Premise block has four bullets. **One is right, one is right-but-mis-drawn, and two are wrong.** Each is stated here with what was measured instead.

### 7.1 The 120 orphan control Findings — CORRECT, and the recorded mechanism is corroborated

120 `finding_derived` events cite at least one `obs_id` that no `observation_recorded` event carries; all 120 sit on `events/batch-029.jsonl`; all 120 are control Findings, 60 on `control:passes_all` and 60 on `control:fails_all`. The same 120 appear in the graph as `Finding` nodes with no incoming `SUPPORTS` edge.

The stated reason — *"control observations discarded by the 2026-09-06 scaffold before publish"* — is corroborated by two independent readings rather than taken on trust:

- `assessment/harness/scan/run.py::run_controls` returns `control_obs + fixture_obs`, and its comment says so explicitly: *"Retained, not discarded. The re-derivation gate can only check a Finding whose evidence it still holds."* An earlier working-tree version returned only the two synthetic E5 observations and dropped the thirty per-leg fixture observations; Findings derived from those thirty were published, their Observations never were.
- The 120 carry **three** `params_hash` values — `045c17ebe39c…` (60), `018dea33553a…` (30), `86299688c25c…` (30). Only the first matches a committed revision of `assessment/harness/scan/params.yaml` (`6826050`). The other 60 were produced by a working tree that was never a commit, so they could not be re-derived even if their Observations were recovered. Both facts are on each annotation event (`params_committed_at`, `params_recoverable`).

### 7.2 "`pytest assessment/` writes 47 control-fixture evidence blobs per run" — WRONG on both counts

Measured, twice, on a clean tree:

| run | new files under `corpus/evidence/scan/` |
|---|---|
| `python -m pytest assessment/` (471 passed, 1 skipped, 9 s) | **0** |
| `python -m pytest tests/test_scan_harness.py` (73 passed, 1 skipped, 9 m 20 s) | **24** |

`assessment/tests/` imports no part of the scan package and writes nothing. The writer is `tests/test_scan_harness.py`, in the **root** suite, and it writes **24** blobs per run, not 47. The fix therefore went into `tests/conftest.py`, not `assessment/tests/conftest.py`.

### 7.3 "an unknown number from earlier runs are already committed" — the number was knowable, and it is not the number the task's rule would have selected

268 of the 1,435 tracked evidence blobs contain the fixture host. **Eight of them are the control cycle's own evidence** — bytes that `observation_recorded` events on the log cite by `body_sha256`. The task's §2 discriminator (*"whose payload names the fixture host"*) and §4's gate clause (*"zero evidence blobs … contain the fixture host"*) would have quarantined those eight and stranded live Observations — which is precisely the defect §1 of the same task exists to annotate.

**Decision, on the grounding, recorded rather than escalated:** the discriminator is BOTH conditions —

> the stored body names the fixture host **AND** no Observation on the event log cites its digest.

An unreferenced blob is litter by construction: the event log is the source of truth (invariant 1), so a body no event points at is a body no Finding can ever cite. This narrows the task's rule; it does not move a threshold, and the clause it replaces was derived from the premise 7.3 corrects. §4's gate is implemented in the corrected form and the test says so on its face (`tests/test_scan_hygiene.py::test_the_committed_evidence_store_holds_no_uncited_fixture_output`).

### 7.4 "`counts` reads `constructs: 47, indicators: 48` while the file holds 48 and 49" — TRUE AS NUMBERS, WRONG AS A DEFECT

The file holds 48 `AssessmentConstruct` and 49 `AssessmentIndicator` nodes **including the A12 candidate**. `counts.constructs` and `counts.indicators` are **candidate-excluded on purpose**, under DD-054 (*the framework does not adopt what the instrument found about itself without the operator*), and `scripts/add_candidate_indicator.py` applies and comments that rule in place. Recounting them as totals would have adopted A12 into the framework's headline numbers as a side effect of a hygiene pass.

`scripts/framework_writeback.py::recount` reproduces **every one of the twelve stored values exactly**; `--check` reports `counts_drift: {}` on the file as it stood before this task touched it. Nothing had drifted.

### 7.5 "nothing reads it; neither write-back updates it" — WRONG, both halves

Readers of `counts`: `scripts/register_framework_results.py:29` reads `criteria`, `constructs`, `evidenced_by` and `evidenced_by_internal` and registers each as a Result; `tests/test_framework_graph.py:131-133` asserts `measurement_specs == len(specs)` and recomputes `collectors_none_known`.

Writers of `counts`: `framework_writeback_rules.py` wrote `collectors_none_known` and `rules_built`; `framework_writeback_measured.py` wrote `indicators_measured`; `framework_writeback_decisions.py` wrote `specs_with_recorded_decision`; `add_candidate_indicator.py` wrote four more. What was actually true is the thing worth fixing and it is not what the premise says: **four writers, each recomputing the handful it happened to touch, and no single definition of any denominator.**

### 7.6 "as the two 2026-09-07 write-backs did" — WRONG; no such event has ever existed

`framework_writeback` appears **zero** times across all 41 event types on the log (`grep` over `events/batch-*.jsonl`, and the full `event_type` census in §3 below). Neither 2026-09-07 write-back appended one; both rewrote `framework/ai_readiness_framework.json` directly and registered Results. The convention the task file describes as established is installed **by this task**.

### 7.7 A12's three internal references — CORRECT

Three `EVIDENCED_BY_INTERNAL` edges used `properties.ref` with an unprefixed `to`; the other seventeen used `properties.artifact_path` with `to: "internal:<ref>"`. `scripts/load_framework_graph.py:111-119` was taught to read both, which kept the projection right and left the record ambiguous.

### 7.8 Four superseded `Figure` artifacts beside the four live ones — CORRECT, no action

Confirmed by labelled Cypher: four names, each with one `superseded` and one `proposed` node. Left as recorded.

### 7.9 Not a premise, but found on the way

**418 blobs under `corpus/evidence/scan/` that are NOT fixture output are also cited by no Observation on the log.** They are host bodies from superseded observations — a real host re-fetched under new parameters mints a new digest and the old body stays. That is a different question from this task's (it is retention policy for real evidence, not test litter), it is out of this task's scope, and it is named here so the next OODA has the number.

---

---

## 4. What changed

**New**

| file | what |
|---|---|
| `scripts/framework_writeback.py` | the shared write-back helper: `recount`, `apply_counts`, `check`, `save` (+ the `framework_writeback` event) |
| `scripts/framework_writeback_normalize.py` | §3's write-back: one `EVIDENCED_BY_INTERNAL` shape, `--check` for self-consistency |
| `scripts/annotate_orphan_findings.py` | §1's annotator, idempotent, `--report` |
| `scripts/quarantine_fixture_evidence.py` | §2's sweep, idempotent, `--dry-run` |
| `scripts/register_hygiene_results.py` | the two Results, recounted from the artifacts rather than typed |
| `tests/test_scan_hygiene.py` | §4's gate, 13 tests |
| `events/batch-032.jsonl` | 120 `finding_evidence_unretained` events |
| `events/batch-033_framework.jsonl` | 1 `framework_writeback` event (TAGGED — not a projection source) |
| `corpus/quarantine/evidence_scan_fixture/` | 260 swept blobs + `reason.txt` |

**Modified**

| file | what |
|---|---|
| `tests/conftest.py` | `no_writes_to_the_real_evidence_store`, autouse |
| `assessment/harness/scan/publish.py` | the ungrounded-Finding refusal in `write_events`; `Finding.evidence_unretained` in `project` |
| `assessment/harness/scan/fixtures/server.py` | `BIND_HOST`, named once |
| `scripts/framework_writeback_{rules,measured,decisions}.py`, `scripts/add_candidate_indicator.py` | routed through the shared helper; `add_candidate_indicator` also mints the correct edge shape |
| `framework/ai_readiness_framework.json` | A12's 3 internal refs normalised; `counts_basis` stamped. 8 insertions, 7 deletions. |

**Untouched, per the task's "Zero edits to" line:** every rule module, `params.yaml`, the target list, every existing event line, the G1 harness, `assessment/cq/*.yaml`, every prior cc_task and RESULT. `git diff` against those paths is empty.

---

## 5. Two checks the task did not ask for

**The new refusal walls off nothing that already exists.** Every surviving cycle payload was replayed against `write_events`'s admissibility test offline (no writes): 0 of 286, 0 of 33, 0 of 437, 0 of 33 would be refused. A guard that retroactively made a stored cycle unpublishable would be a worse defect than the one it closes.

**418 non-fixture blobs are also uncited.** See §7.9 — out of scope here, named for the next OODA.

---

## 6. What the next OODA should verify first

1. That `corpus/evidence/scan/` stays flat. The guard is autouse in `tests/conftest.py`; `assessment/tests/` is outside its reach and writes nothing today (it imports no part of the scan package — checked). If a scan-touching test ever lands under `assessment/`, the guard moves to a conftest both trees see.
2. Retention for the 418 uncited non-fixture blobs — real host bodies from superseded observations. The question is a policy one (does the evidence store keep every body ever fetched, or only the bodies the current log cites?) and it wants a decision, not a sweep.
3. That every future write-back goes through `scripts/framework_writeback.py::save`. Four writers do now; nothing enforces it for a fifth. The cheap guard is a test that greps for a direct `FRAMEWORK.write_text` outside the helper.
