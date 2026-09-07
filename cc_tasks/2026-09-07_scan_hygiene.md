# CC Task — scan-hygiene: nothing on the log without its evidence, nothing in the tree the tests left behind

**Date:** 2026-09-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-07_framework_projection_repair_RESULT.md` and `2026-09-07_eda_and_charts_RESULT.md`; premises re-checked by labelled Cypher 2026-09-07 afternoon)
**Fulfils:** its own ResearchTask (registered by `seldon cc register`); prerequisite for `cc_tasks/2026-09-07_scan_harness_v3.md`, which must not inherit a test suite that litters the evidence store.
**Spend:** zero model calls, zero network.

**Premise (verified):**
- 120 `Finding` nodes with `target_doc_id` prefix `control:` have **no** `Observation-[:SUPPORTS]->` edge (`events/batch-029.jsonl`, the 2026-09-06 scaffold control cycle, which recorded Findings and discarded its control Observations; repair RESULT §7.7). The 2026-09-07 cycle publishes both and is unaffected. A Finding whose evidence the log does not hold is the same class of claim as a Finding whose evidence bytes are missing; invariant 3 ("no grounding span, no write") is the standing rule for extraction and it applies here.
- `pytest assessment/` writes 47 control-fixture evidence blobs into `corpus/evidence/scan/` per run, content-addressed on a payload that includes the fixture server's ephemeral port, so the set grows without bound; an unknown number from earlier runs are already committed among the 1,435 tracked evidence files (both RESULTs §7.8).
- `framework/ai_readiness_framework.json::counts` reads `constructs: 47, indicators: 48` while the file holds 48 and 49; nothing reads it, and neither write-back updates it (repair §7.4). A12's three `EVIDENCED_BY_INTERNAL` entries use key `ref` with a raw id where the other 17 use `artifact_path` with an `internal:` prefix (repair §7.5); the loader tolerates both, the JSON is inconsistent with itself.
- Four superseded `Figure` artifacts exist beside the four live ones (eda §7.7); correct as recorded, no action.

**Zero edits to:** any rule module, `params.yaml`, the target list, any existing event line, the G1 harness, `assessment/cq/*.yaml`, any prior cc_task or RESULT. The framework JSON may change **only** through a write-back script that appends a `framework_writeback` event, as the two 2026-09-07 write-backs did.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-07_scan_hygiene_ADDENDUM*.md` before starting.**

---

## 1. The 120 orphan control Findings: annotate, never delete
Append-only correction, the pattern this repo already uses (`extraction_superseded`, `edge_endpoint_alias`): a new event type `finding_evidence_unretained` on a new shard, one event per Finding, carrying `finding_id`, `cycle`, `reason: "control observations discarded by the 2026-09-06 scaffold before publish; evidence not recoverable"`, `annotated_by: cc_tasks/2026-09-07_scan_hygiene.md`. `publish.py --project` projects it as `Finding.evidence_unretained = true`. The Findings keep their ids; the re-derivation gate for that cycle (286 of 286, byte-identical) is untouched because these 120 are control Findings and were never in its denominator; confirm that by reading the gate, and say so in the RESULT with the file and line. Register `scan_control_findings_evidence_unretained_2026-09-06` = 120.
Then the standing rule, in code: `publish.py` refuses to publish a Finding whose `obs_id`s are not on the log **unless** an `evidence_unretained` annotation exists for it; test with one synthetic orphan.

## 2. Tests stop writing into the evidence store
A tmp evidence root under test (fixture in `assessment/tests/conftest.py` or the harness's own conftest; the pattern `tests/conftest.py` already uses for `_EVENTS_DIR` monkeypatching, CLAUDE.md §Conventions). Then find every committed blob under `corpus/evidence/scan/` whose payload names the fixture host: **move** them to `corpus/quarantine/evidence_scan_fixture/` with a `.reason.txt` (invariant 2: bad acquisitions are never deleted), register `scan_evidence_fixture_blobs_quarantined` with the count, and confirm no live Finding's `evidence_hash` pointed at any of them (if one did, stop and report: that Finding's evidence would then be a fixture, which is a different defect).

## 3. Framework JSON self-consistency (write-back script, event, no hand edit)
`scripts/framework_writeback_normalize.py`: regenerate `counts` from `nodes`/`edges`, normalize A12's three internal refs to the `artifact_path` + `internal:` shape, fix `add_candidate_indicator.py` so the next candidate is written in that shape, append a `framework_writeback` event. The round-trip gate (`tests/test_framework_projection_roundtrip.py`) and the skeleton round-trip must both stay green; re-run `build_projection.py`. Every write-back from now on regenerates `counts` (put it in the shared write-back helper, not in three scripts).

## 4. Gate (the one gate of this task)
`tests/test_scan_hygiene.py`:
- after `python -m pytest tests/ assessment/`, `git status --porcelain corpus/` is empty;
- `MATCH (f:Finding) WHERE NOT (:Observation)-[:SUPPORTS]->(f) AND coalesce(f.evidence_unretained,false) = false RETURN count(f)` = 0, and the annotated count = 120;
- `counts` in the JSON equals a recount of `nodes`/`edges`; every `EVIDENCED_BY_INTERNAL` entry has the same key shape;
- zero evidence blobs under `corpus/evidence/scan/` contain the fixture host.
**Failure writes nothing and reports.**

## 5. Report
RESULT `cc_tasks/2026-09-07_scan_hygiene_RESULT.md`: gate output, the three counts registered, the quarantine list, every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on protected paths. `seldon cc complete`; commit, push.

**SEQUENCING:** §2 → §1 → §3 → §4 (hard stop) → §5. §2 first so §1's and §3's test runs do not write blobs. This task runs **before** `cc_tasks/2026-09-07_scan_harness_v3.md`.
