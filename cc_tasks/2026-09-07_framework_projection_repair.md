# CC Task — framework-projection-repair: make the graph say what the framework of record says

**Date:** 2026-09-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-07_scan_run_RESULT.md`, premises verified against the live graph 2026-09-07)
**Fulfils:** graph hygiene prerequisite for ResearchTask `eda-and-charts` (`c1ede3d9`). Registered as its own ResearchTask by `seldon cc register`.
**Spend:** zero model calls. No network.

**Premise (verified by labelled Cypher against `seldon-ai-readiness-kg` on 2026-09-07, after scan-run completed):**
- `framework/ai_readiness_framework.json` (framework of record, DD-050) holds **49** `AssessmentIndicator` nodes: 16 `measured`, 1 `harness_built` (E5), 32 `specified` (31 plus the candidate A12); each measured indicator carries `measured_by: {cycle: scan_2026-09-07, legs: [...], params_hash: ...}`.
- The Neo4j projection holds **48** `AssessmentIndicator` nodes: 46 `specified`, 2 `measured` (G1-D, G1-O). A12 is absent. Neither the rule-review write-back (`framework_indicators_harness_built_after_review` = 15, 02:16Z) nor the scan-run write-back (11:03Z) reached the graph. Observations (3,717), Findings (1,353) and Rules (29) did reach it, so `build_projection.py` ran but the framework layer is projected by some other path or not re-projected at all. **Root cause is unknown to Desktop; finding it is §1.**
- Every `Rule` node carries `version: 'v1'`, including `RULE-A2-v3`, `RULE-A3-v3`, `RULE-D1-v3`, `RULE-F4-v3`, `RULE-A12-v1` and every `-v2`. `keys(Rule)` = `['version','rule_id']` only.
- There is **no edge from `Rule` or `Finding` to `AssessmentIndicator`**. The only edges touching the assessment layer are `Observation-SUPPORTS->Finding`, `Observation-OBSERVED_ON->Document`, `Finding-RULED_BY->Rule`, `AssessmentConstruct-DECOMPOSES_INTO->AssessmentIndicator`, `AssessmentIndicator-MEASURED_BY->MeasurementSpec`, `AssessmentIndicator-EVIDENCED_BY_INTERNAL->AssessmentInternalRef`. Evidence therefore cannot be traversed to the framework; the operator's standing instrument requirement (evidence assigned to the framework directly, progress visible at every level) is unmet in the graph.
- 22 open ResearchTasks `Conversion gap [...] on scan-*` were emitted by the admission convertibility gate at 02:06Z when the 26 scan surfaces were admitted under epoch `scan-2026-09`. Those Documents are observation targets (HTML landing pages by design, DD-055) and never extraction corpus; thin extent is expected and no conversion is owed. 23 earlier conversion-gap tasks on other documents were superseded on 2026-09-06 with the same shape of reasoning.

**Consequence of the premise:** `seldon go` and `seldon_query` currently verify framework state against a projection two write-backs old. The Desktop protocol ("verify against the graph before trusting a handoff") is hollow for this layer until this task lands.

**Zero edits to:** `framework/ai_readiness_framework.json` content (project it; do not change it), any rule module, `params.yaml`, the target list, the G1 harness, `assessment/cq/*.yaml`, any event line, any prior cc_task or RESULT.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-07_framework_projection_repair_ADDENDUM*.md` before starting.**

---

## 1. Root-cause, then record it
Find where `AssessmentIndicator` / `AssessmentConstruct` / `AssessmentCriterion` / `MeasurementSpec` nodes are projected into Neo4j (candidates: `scripts/build_projection.py`, `scripts/build_framework_graph.py`, a loader under `framework/` or `assessment/`) and why the two write-backs of 2026-09-07 did not reach the graph. State the mechanism in the RESULT in one paragraph with file and line. If the framework layer is projected by a script that `build_projection.py` does not call, that is the defect; if `build_projection.py` projects it from a source other than the JSON of record, that is the defect. Do not speculate in the RESULT; read the code.

## 2. Project the framework of record, exactly
The graph's framework layer must be a projection of `framework/ai_readiness_framework.json` and nothing else. After this task:
- `AssessmentIndicator` count = 49 (A12 included, distinguished by its `status: candidate` property; it is still not counted in any fraction, DD-054).
- Every property on every framework node in the JSON is on the graph node with the same value (`measurement_status`, `status`, `code`, `criterion_code`, `type`, `tier`, `measured_by` flattened to `measured_cycle`, `measured_legs`, `measured_params_hash`, plus the A12 `candidate_*` fields).
- Every JSON edge is projected (`DECOMPOSES_INTO`, `MEASURED_BY`, `EVIDENCED_BY`, `EVIDENCED_BY_INTERNAL`); counts in the RESULT.
- **New edge `Rule-[:MEASURES]->AssessmentIndicator`**, one per Rule, derived from `rule_id` (`RULE-A11-declared-v2` → A11; `RULE-G1-D-v1` → G1-D; `RULE-A12-v1` → A12; `RULE-E5-v2` → E5). 29 Rules → 29 edges. Put the derivation in one function with a test; no per-rule table.
- `Rule.version` = the version parsed from `rule_id`; `Rule.indicator_code` set; `Rule.current` boolean from `CURRENT`.
- Whatever path you fix, `build_projection.py` (the documented reset-and-replay entry point in CLAUDE.md) must leave the framework layer fresh on every run. One command projects everything, or the RESULT says why not and the framework projection gets its own documented command in CLAUDE.md §Commands.

## 3. Gate (the one gate of this task)
Add `tests/test_framework_projection_roundtrip.py`, runnable under `python -m pytest tests/`, skipped cleanly (not failed) when Neo4j is unreachable:
- for every node in the JSON, a graph node with the same labels and identical property values exists (cell-for-cell, the same discipline as the DD-050 skeleton round-trip);
- node and edge counts per label and type match the JSON exactly;
- `MATCH (r:Rule)-[:MEASURES]->(i:AssessmentIndicator)` count = `count(r:Rule)`, every rule exactly one indicator;
- `measurement_status` distribution on the graph = 16 / 1 / 32 (measured / harness_built / specified).
The gate runs after §2. **If it fails, write no RESULT numbers as achieved: report the diff and stop.** Do not patch the JSON to match the graph.

## 4. Withdraw the 22 scan-surface conversion-gap tasks
Reason string, verbatim, on every one: `scan-surface Document under epoch scan-2026-09: observation target (HTML landing page by design, DD-055), never extraction corpus; thin extent expected, no conversion owed. Withdrawn by cc_tasks/2026-09-07_framework_projection_repair.md.`
IDs (prefixes): `88b32870 3c7b2265 2e6e5064 98e82641 dc73d636 0fb5fc8e 9e7ecfab 3509d2e4 4188a13d 736c1439 0e6537fb 7837aad2 315889bd f5298494 82385914 b077dffe 0aa07400 63b71371 af88b525 bc17cd11 3c9d08b4 6fcec4fd`.
Use `seldon task withdraw` (or `seldon task update --state withdrawn --reason`, whichever the CLI exposes; run `seldon task --help` first). Withdrawn, not completed and not superseded: the premise is false, no work was done. If the CLI has no withdraw path, do not close them any other way; list the 22 in the RESULT and stop this section. Confirm afterwards by labelled Cypher: `MATCH (t:ResearchTask) WHERE t.description STARTS WITH 'Conversion gap' AND t.description CONTAINS ' on scan-' RETURN t.state, count(*)` shows only `withdrawn: 22`.
Then the admission gate: add a one-line note to the RESULT naming the file and function in `kg/ingest/gate.py` (or wherever the convertibility gate lives) that would need a `purpose: scan_surface` skip so the second scan cycle does not emit 26 more. **Name it; do not change it** (that is the next scan-cycle task's `v3` list).

## 5. Record two conventions as design decisions
Append to `docs/design_decisions.md` using the next free DD number (read the file; do not guess):
- **Cycle-level Result names carry the cycle.** `scan_<metric>_<cycle>` for every per-cycle Result; the 2026-09-07 bare names (`scan_surfaces`, `scan_findings`, `scan_observations`, `scan_<leg>_*`) stand as immutable first-cycle exceptions and are never reused; the second scan cycle registers cycle-suffixed names only. Cite the AD-028 refusal that `scan_control_findings` (31 vs 33) already produced as the motivating incident (scan-run RESULT §7.4).
- **The framework projection is part of `build_projection.py`'s contract**, gated by the round-trip test of §3. Verification of framework state by Cypher is valid only while that test is green.

## 6. Report
RESULT: `cc_tasks/2026-09-07_framework_projection_repair_RESULT.md`. Lead with the §1 root cause, then the §3 gate output (counts before / after), then the §4 withdraw confirmation query output, then every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on protected paths. `seldon cc complete`; commit, push.

**SEQUENCING:** §1 → §2 → §3 (hard stop on failure) → §4 → §5 → §6. This task runs **before** `cc_tasks/2026-09-07_eda_and_charts.md`; that task reads the graph this one repairs.
