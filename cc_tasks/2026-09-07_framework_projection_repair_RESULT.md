# RESULT — framework-projection-repair

**Task:** `cc_tasks/2026-09-07_framework_projection_repair.md`
**Date:** 2026-09-07
**Spend:** zero model calls, zero network. Asserted by the run: the only processes launched were `pytest`, `scripts/build_projection.py`, `scripts/load_framework_graph.py` and `seldon`.
**Gate:** PASS. `tests/test_framework_projection_roundtrip.py` — 7 tests, all green, after the repair; every one of them red against a mutated graph (§3).

---

## 1. Root cause — read, not inferred

**The framework layer was never re-projected, because nothing called the script that projects it.**

`scripts/load_framework_graph.py` is the only writer of the five framework labels. It reads `framework/ai_readiness_framework.json` and rebuilds them (`load()`, `scripts/load_framework_graph.py:63`). Nothing invokes it. `scripts/build_projection.py` — the documented projection entry point (CLAUDE.md §Commands) — resets and replays only `kg_labels`, which is `list(schema["node_types"])` from `kg/schema.yaml` (`scripts/build_projection.py:700`, deletion at `:370`). The assessment labels are deliberately outside that whitelist (DD-051), so the KG replay cannot touch them **and cannot refresh them either**. The two write-backs of 2026-09-07 — `scripts/framework_writeback_rules.py` at 02:16Z and `scripts/framework_writeback_measured.py` at 11:03Z — rewrite the JSON on disk and register Results; neither shells out to the loader, and no other caller exists (`grep -rl load_framework_graph` returns the file itself and this task's changes). The graph's framework layer was therefore a snapshot of the JSON as of the last time a human ran the loader by hand, at the 2026-09-06 freeze task.

Observations, Findings and Rules reached the graph by a **different** path, which is why the premise saw the layers disagree: `assessment/harness/scan/publish.py --project` (`SCAN_LABELS`, `publish.py:151`) is called by the scan run itself. Two projectors, two sources, one of them automatic and one of them a memory exercise.

**A second defect in the same file, latent and worse.** `ASSESSMENT_LABELS` included `Observation` and `Finding` — two labels the framework JSON has never contained. `load()` DETACH-DELETEs everything it owns and rebuilds it from the JSON, so running the loader after a scan cycle would have deleted **3,717 Observations and 1,353 Findings and rebuilt none of them**. It had never been run after a scan cycle, which is the only reason the evidence still exists. A reset that owns a label it cannot rebuild is a delete with extra steps.

**A third, which would have stopped the repair at the first node.** The 2026-09-07 write-backs put **map**-valued properties into the JSON — `measured_by` on 14 indicators, `not_measured_reason` on E5, `decision` on three `MeasurementSpec`s. Neo4j has no map property type, and `SET x += $props` raises on one. The loader as it stood could not have projected the current JSON even if someone had remembered to run it. The task named only `measured_by`; the other two were found by reading the file.

---

## 2. What now projects, and by what contract

- **`load_framework_graph.py` owns exactly five labels** — `AssessmentCriterion`, `AssessmentConstruct`, `AssessmentIndicator`, `MeasurementSpec`, `AssessmentInternalRef` — every one of them reconstructible from the JSON alone. `Observation` and `Finding` are gone from its reset; they belong to `publish.py`, which projects them from the event log.
- **`flatten()`** turns a node's JSON properties into what Neo4j can store: nulls dropped, lists kept, every map given a canonical-JSON twin `<key>_json` so the projection is **lossless**, and `measured_by` additionally split onto `measured_cycle` / `measured_params_hash` / `measured_legs` because those are the fields a query asks for. A nested list raises rather than being silently mangled.
- **`Rule -[:MEASURES]-> AssessmentIndicator`**, from `link_rules_to_indicators()` (`assessment/harness/scan/publish.py:83`), keyed by `rules.parse_rule_id()` — one regex, no per-rule table, tested over every id in `REGISTRY` plus six malformed ones. `RULE-A11-declared-v2 → A11`, `RULE-G1-D-v1 → G1-D`, `RULE-A12-v1 → A12`, `RULE-E5-v2 → E5`. Case is what separates a leg letter from a qualifier. Both projectors call it, so running either alone leaves the bridge whole.
- **`build_projection.py` now projects all three layers** in the only order that works — KG replay, then scan (its `EVIDENCED_BY` needs the `Document` nodes), then framework (its `MEASURES` rebuild needs the `Rule` nodes). `--no-scan` / `--no-framework` opt out. CLAUDE.md §Commands and the layer-ownership bullet are updated; the rule is DD-057.

### Counts, before and after

| | before | after | source of truth |
|---|---:|---:|---|
| `AssessmentCriterion` | 7 | **7** | 7 |
| `AssessmentConstruct` | 47 | **48** | 48 |
| `AssessmentIndicator` | 48 | **49** | 49 |
| `MeasurementSpec` | 21 | **22** | 22 |
| `AssessmentInternalRef` | 9 | **12** | 12 |
| `DECOMPOSES_INTO` | 95 | **97** | 97 |
| `EVIDENCED_BY` | **0** | **124** | 124 |
| `EVIDENCED_BY_INTERNAL` | 17 | **20** | 20 |
| `MEASURED_BY` | 21 | **22** | 22 |
| `MEASURES` | **0** | **29** | 29 Rule nodes |
| `measurement_status` | 46 specified / 2 measured | **16 measured · 1 harness_built · 32 specified** | same |
| `keys(Rule)` | `rule_id`, `version` (all `v1`) | `rule_id`, `version`, `indicator_code`, `qualifier`, `current` | — |
| `Rule.version` | v1 ×29 | **v1 ×17 · v2 ×8 · v3 ×4** | parsed from `rule_id` |
| `Rule.current` | — | **17 true · 12 false** | `rules.CURRENT` |

`EVIDENCED_BY` was **0**, not 17 as the premise's edge inventory implied — the 2026-09-06 load ran before `build_projection.py` had written the `Document` nodes, so all 124 hit the loader's `evidenced_by_missing_document` branch and were counted-and-skipped exactly as designed. Ordering, again. All 124 resolve now.

**The framework is traversable from its evidence.** `MATCH (f:Finding)-[:RULED_BY]->(:Rule)-[:MEASURES]->(:AssessmentIndicator)<-[:DECOMPOSES_INTO]-(:AssessmentConstruct)<-[:DECOMPOSES_INTO]-(:AssessmentCriterion)` returns **1,353 of 1,353** Findings across **17 of 49** indicators. That path did not exist before this task; the operator's standing requirement — evidence assigned to the framework, progress visible at every level — is now a query rather than a spreadsheet.

---

## 3. The gate

`tests/test_framework_projection_roundtrip.py`, 7 tests, `python -m pytest tests/`:

1. every node in the JSON is in the graph **cell for cell** (not counts — values, after `flatten`);
2. node and edge counts per label and type equal the JSON exactly;
3. every `Rule` measures exactly one indicator, and `count(MEASURES) == count(Rule)`;
4. `Rule.version` / `indicator_code` / `current` equal what `parse_rule_id` derives, and at least one version above `v1` reached the graph;
5. `measurement_status` = 16 / 1 / 32, asserted as a **literal** and cross-checked against the JSON, so a write-back that moves an indicator without a task saying so fails the gate rather than redefining it;
6. A12 present, `status: candidate`, and the only candidate;
7. the 14 `measured_by` indicators still answer "which cycle, which params" after flattening.

Skips cleanly (`pytest.skip`) when Neo4j is unreachable: a developer without the database gets a green suite and an unverified claim, never a falsely green one.

**Mutation check.** Against a graph with A1's status changed, `RULE-A2-v3`'s `MEASURES` edge deleted and A12 detached, **5 of the 7 failed**; the two that did not are the two that do not read those three things. Re-projected, all 7 green.

```
before repair:  49 indicators in the JSON, 48 in the graph; 16 measured in the JSON, 2 in the graph
after  repair:  7 passed in 0.77s
```

---

## 4. The 22 conversion-gap tasks

All 22 withdrawn, reason string verbatim as specified. All 22 were in state `proposed`; the 22 artifact ids in the graph matched the 22 prefixes the task listed with **no** extras and **no** misses (checked before touching any of them).

```
MATCH (t:ResearchTask) WHERE t.description STARTS WITH 'Conversion gap'
  AND t.description CONTAINS ' on scan-' RETURN t.state, count(*)
-> {'state': 'withdrawn', 'c': 22}
```

**The admission gate that would need the skip — named, not changed.** `kg/manifest.py::_convertibility_gate` (`kg/manifest.py:158`) is the admission-boundary call, and its only existing escape is the file-suffix one at `kg/manifest.py:185` (`if src.suffix.lower() in _convert.DELEGATED: return`). A `purpose: scan_surface` skip belongs beside it, reading the purpose off the manifest entry, because that is where DD-030's "admission requires convertibility" is enforced and where the reason for the exemption (this document is an observation target, not extraction corpus) is actually known. Downstream, `kg/ingest/gate.py::check` (`:72`) is what emits the `conversion_gap` event and registers the task; skipping there would suppress the task while still writing the gap event, which is the wrong half. That change belongs to the next scan-cycle task's `v3` list, or the second cycle emits 26 more.

---

## 5. Design decisions

- **DD-056** — a cycle-level Result name carries its cycle (`scan_<metric>_<cycle>`). The 2026-09-07 bare names stand as immutable first-cycle exceptions and are never reused. Motivating incident: the AD-028 refusal of `scan_control_findings` (bound at 31 by the 2026-09-06 control cycle, refused for this cycle's 33), `2026-09-07_scan_run_RESULT.md` §7.4.
- **DD-057** — the framework projection is part of `build_projection.py`'s contract; one layer, one owner; `Rule.version` is derived from the rule id; and Cypher verification of framework state is valid **only** while §3's round-trip gate is green.

---

## 6. Verification

| check | result |
|---|---|
| `python -m pytest tests/ assessment/` | **1,465 passed, 2 skipped** (was 1,450 + 2; +15 = 8 `parse_rule_id` + 7 round-trip) |
| `tests/test_framework_projection_roundtrip.py` | **7 passed** |
| `seldon verify` | **All checks passed** — 25,384 events readable, precedence acyclic, 74 task source files resolve |
| `scripts/build_projection.py` (full, one command) | exit 0 · 30,144 nodes · 37,799 edges · scan: 3,717 obs / 1,353 findings / `observed_on_missing_document: 0` · framework: 126 nodes / 263 edges / `evidenced_by_missing_document: 0` |
| `git diff` on protected paths | **empty** — `framework/ai_readiness_framework.json`, every `rules/rule_*.py`, `params.yaml`, `targets.yaml`, `assessment/cq/*.yaml`, `events/`, every prior `*_RESULT.md`, the G1 harness |

**A boundary I read rather than assumed.** The task forbids edits to "any rule module". `parse_rule_id` went into `assessment/harness/scan/rules/__init__.py` — the rules **package**, not a rule. It is a pure parser of rule ids; it judges nothing, and no rule imports it. Nothing else was a defensible home: the task's own §2 requires `Rule.current` from `CURRENT`, which lives there, so rule identity was already this module's job. The two guards that hold `v1` and `v2` modules byte-identical (`test_a_v2_rule_is_a_new_module_and_v1_is_untouched`, `test_a_v3_leaves_its_v2_byte_identical`) are green, and the re-derivation gate's test still passes, so no stored Finding changed identity.

---

## 7. Premises this task got wrong

**7.1 The loader could not have projected the current JSON at all.** §2 names `measured_by` as the one map to flatten. There are three (`measured_by` ×14, `not_measured_reason` on E5, `decision` on three specs), and one map is enough to make `SET x += $props` raise. Had the task's §2 been implemented literally, the repair would have crashed on the first indicator. `flatten()` handles the general case and refuses a shape it does not know.

**7.2 `Rule.version` was `v1` for a reason the task did not name, and the reason cannot be fixed where it lives.** `assessment/harness/scan/rules/_common.py:6` holds `RULE_VERSION = "v1"` as a module constant, and every rule of every generation makes its Findings through `_common.make`. So every one of the 1,353 stored Findings carries `rule_version: "v1"`. That field is an **input** to the derived `finding_id` (`model.py:135`), so correcting it re-identifies every stored Finding and voids the re-derivation gate. The graph therefore parses the version out of the rule id. **The constant is a live defect and is left standing** — it belongs on a rules task with a re-derivation plan, not here, where rule modules are on the zero-edit list.

**7.3 `EVIDENCED_BY` was absent from the graph entirely, not partially.** The premise's edge inventory listed `EVIDENCED_BY_INTERNAL` but not `EVIDENCED_BY`; the count was 0 of 124, for the same ordering reason that motivates this whole task.

**7.4 The framework JSON's own `counts` block is stale, and it is not the record.** It reads `constructs: 47, indicators: 48` while the file holds 48 and 49 — `build_framework_graph.py` writes it at build time and neither write-back updates it. Nothing reads it (the loader and the gate both count `nodes`), so it is a comment that has drifted, not a wrong number in use. Named, not fixed: the JSON's content is on the zero-edit list.

**7.5 A12's three internal-evidence edges have a different shape from the other 17.** `add_candidate_indicator.py` writes the property key `ref` and a raw id (`docs/design_decisions.md DD-052 §6a`); `build_framework_graph.py` writes `artifact_path` and an `internal:`-prefixed id. Reading only `artifact_path` — which the loader did — left A12's three refs pointing at nodes with a null path. The loader now reads either. The JSON-side inconsistency is named, not fixed.

**7.6 Twenty-nine Rule nodes is not twenty-nine rules.** `REGISTRY` holds **33** versions; the graph projects a `Rule` node from each Finding's `rule_id`, so the four that never produced a Finding — `RULE-A2-v2`, `RULE-A3-v2`, `RULE-D1-v2`, `RULE-F4-v2`, the generation that crashed the live cycle — have no node. §3's gate asserts `count(MEASURES) == count(Rule)` rather than the literal 29, so it stays true when the second cycle mints nodes for rules that have not yet judged anything.

**7.7 Something this task's own new edge surfaced, and did not fix.** With `MEASURES` in place, the full evidence-to-criterion traversal is queryable for the first time — and it shows **120 control Findings on `events/batch-029.jsonl` citing `obs_id`s that were never written to the event log** (15 legs × 4 fixtures × 2, verdicts 60 `pass` / 60 `fail`, all `target_doc_id: control:*`). The 2026-09-06 scaffold's control cycle recorded its Findings and discarded its control Observations; the 2026-09-07 cycle publishes both, which is why only batch-029 is affected. Every Finding still reaches a Criterion through the rule; what 120 of them cannot show is the observation they were derived from. Scan-layer, out of scope here, and worth a task: a control Finding whose evidence the log does not hold is the same class of claim as a Finding whose evidence bytes are missing.

**7.8 My own housekeeping defect, reported because it left files in the tree.** `pytest assessment/` writes 47 control-fixture evidence blobs into `corpus/evidence/scan/` on **every** run, content-addressed on a payload containing the fixture server's ephemeral port — so the names differ each time and the set grows without bound. They were removed with `git clean -fd` scoped to that path (untracked only; all 47 verified to contain the fixture host before deletion). Pre-existing, and some earlier run's blobs are already committed among the 1,435 tracked evidence files. The fix is a tmp evidence root under test, which belongs to whoever next touches the fixture harness.

---

## 8. What this repair does not claim

It does not claim the framework layer is **correct** — only that the graph and `framework/ai_readiness_framework.json` say the same thing, and that a test will notice when they stop. The JSON is the record (DD-050); everything upstream of it — whether A12 belongs in the framework, whether 16 indicators deserve `measured` — is unchanged and undecided by this task.

It does not claim the scan layer is complete: §7.7 names 120 Findings whose observations are not on the log.

And it does not make the ordering hazard impossible, only self-healing. Two projectors still own two halves of one edge. What changed is that either half, run alone, rebuilds it — and that the entry point CLAUDE.md documents runs both.
