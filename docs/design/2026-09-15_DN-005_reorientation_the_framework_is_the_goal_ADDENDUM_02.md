# DN-005 ADDENDUM_02 — a sixth `measurement_basis`, for a named field that no rule reads yet

**Date:** 2026-09-17. **Written by:** `cc_tasks/2026-09-17_unassigned_indicators.md` (decision 2, executing DN-005 §4 item 2). **Amends:** DN-005 ADDENDUM_02's predecessor, [ADDENDUM_01](2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_01.md) §2. It adds one value to the `measurement_basis` enumeration and repeals nothing. The three tiers are untouched; this is a naming decision inside tier M, and the operator can overrule it.

---

## 1. The value

| basis | tier | what it is |
|---|---|---|
| `structured_field` | M | a corpus document names the structured field that carries the property, and a collector already in `docs/design/scan_tool_map.md` §1 already fetches the surface that carries it — and **no rule in `rules.CURRENT` reads it yet** |

Two properties travel with it on the node, so the claim can be checked without parsing a sentence:

* `tier_field` — the field, named as its own specification names it (`schema.org variableMeasured`, DCAT-US 3 `hasQualityMeasurement`, the robots.txt `Content-Signal` directive).
* `tier_collector` — the collector entry points, in the same `module.function` form the tool map's §1 prints.

`tests/test_measurement_tiers.py::test_a_tier_that_names_a_field_names_a_collector_that_exists` imports each named module and asserts each named entry point is callable, so a collector renamed or an entry point dropped fails the suite instead of reading plausibly forever.

## 2. Why it is not `harness_leg`

ADDENDUM_01 §2 defines `harness_leg` as "**a rule in `rules.CURRENT` serves the indicator**". Three things outside the tiering layer depend on that meaning and would silently become false if a rule-less indicator carried it:

1. `scripts/tag_prescriptions.py::validate` refuses to write unless the prescription layer's `OUTCOMES` covers exactly the record's `harness_leg` indicators — an action per failing rule outcome, which a rule-less indicator has none of.
2. `tests/test_prescriptions.py::test_every_harness_leg_indicator_has_at_least_one_action` and `::test_cypher_every_harness_leg_indicator_has_an_action` assert the same join, against the record and against the graph.
3. `scripts/load_framework_graph.py` publishes `harness_leg_indicators_without_an_action` as a projection count.

The task file this addendum executes asked for basis `harness_leg` with a note saying no rule exists. All three gates failed on the first write, which is the gates working: the note said in prose what the field said falsely in data. The value is added rather than the gates moved (`~/GitHub/CLAUDE.md` §5 and the repo's one-gate-per-task rule), and `test_the_basis_that_means_a_rule_is_only_ever_a_rule` now holds the boundary in both directions.

## 3. The verdict axis

`scripts/scan_tool_map.py::VERDICT_BY_BASIS` maps `structured_field` to **`scan-observable`**, the same verdict as `harness_leg`: the act that would read the field is a fetch of a served surface. What the row lacks is a rule, and that belongs in the row's `why` cell, which now reads `no rule in rules.CURRENT yet; <entry points> would read <field>`. A row that printed `no collector reaches this yet` beside a source naming a collector put two cells of one row in contradiction, and that is the only change to the generator.

## 4. Where the numbers are

Per-indicator assignments, the counts per tier and per basis, and the rows still unassigned with the reason for each are in `cc_tasks/2026-09-17_unassigned_indicators_RESULT.md` §0 to §2, on the record's nodes, and in `docs/design/scan_tool_map.md` §2 and §4. `tests/test_measurement_tiers.py` holds the distribution as a literal, for the record and for the graph.
