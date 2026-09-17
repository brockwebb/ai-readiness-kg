# CC Task: every indicator carries a measurement tier, sourced, and the tool map's verdicts are derived, not defaulted

**Date:** 2026-09-17
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md` §2.2 and §4 item 2, `docs/design/scan_tool_map.md` §1 to §3, and the handoff of 2026-09-16 (the product matrix's misplaced `legs_withdrawn` header).
**Implements:** DN-005 §4 item 2: "a `measurement_tier` on every indicator node, sourced". Under DN-001 (locators read from the documents) and DD-001 (every assertion citable by a stranger).
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement capability tiered three ways. This is the first framework-layer task since the standing cadence.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

## 0. What exists and what is wrong with it

The framework record (`framework/ai_readiness_framework.json`, one writer, event-logged, projected to Neo4j) carries 44 indicators; 12 have a spec, a rule and sources, and the harness measures the L0 six plus A1, A3, A8, B3, D4 and G1-D. `docs/design/scan_tool_map.md` §2 already sorts the 32 unmeasured indicators into three verdicts. Two of those verdicts are trustworthy and one is not:

- `not web-observable` (A12, B4, D2, D3, E4) reads as an organisational fact. Sound.
- `content-evaluation` (E7, G2, G3, G5, G6) reads as "needs the second instrument". Sound.
- `scan-observable`, with the identical why "`http` + `structured_data` would serve it", is stamped on 22 indicators. For A7, B1, B2, B5, B6, F2, F3, G4 it is plausible. For C1 to C5 it is false on its face: C1 is answer accuracy of a retrieval-augmented model against a benchmark set, C2 is entailment judgement, C4 is which sources generative engines cite. No fetch of a page serves those. E1, E2, E3, E6, E8, E9, F1, F5, F6 sit between. The generator (`scripts/scan_tool_map.py`) is defaulting to `scan-observable` when no keyword matches, and printing a reason it did not derive. A generated table that says "would serve it" without a derivation is prose with a script's name on it.

The tiers, from DN-005 §2.2, verbatim: **M** measured by our harness; **O** measurable with open tools; **D** declared, only the agency can say. The tool map's verdict axis (observable / organisational / needs judged reading) is not the tier axis; the tier answers *who could measure this*, the verdict answers *by what kind of act*. Both are needed and neither substitutes for the other.

**Decisions taken here (operator overrides later):**

1. **Two fields on every indicator, written through the framework's one writer, each with a source.** `measurement_tier` ∈ {M, O, D} and `measurement_basis`, the kind of act: `harness_leg` (a rule in `rules.CURRENT` serves it), `judged_reading` (the G1-style second instrument), `open_tool` (a named tool, cited), `evaluation` (a benchmark or entailment run the project would build), `declaration` (only the agency can say). Every assignment carries `tier_source`: a locator into the tool map, the Screaming Frog investigation, a tool's documentation on disk, or the indicator's own definition text with the sentence quoted. No assignment without a source; an assignment whose only source is this task's reasoning is written with `tier_source: "estimate, cc_tasks/2026-09-17_measurement_tiers.md decision 1"` and counted in the RESULT.
2. **The tier rule, applied mechanically before any judgment.**
   - A rule exists in `rules.CURRENT` for the indicator → **M**, basis `harness_leg` (or `judged_reading` for G1-D). The 12 measured indicators resolve this way and nothing else.
   - The tool map's `not web-observable` verdict, confirmed against the indicator's definition text → **D**, basis `declaration`.
   - The tool map §3 gap table or the Screaming Frog investigation names an open tool that reaches the indicator's spec → **O**, basis `open_tool`, source the row or the investigation section.
   - The verdict is `content-evaluation` → **M**, basis `judged_reading`, because the second instrument is this project's and already runs under harness discipline (G1-D is the precedent). `tier_source` cites the G1 instrument.
   - The indicator's definition names a benchmark, an eval set, entailment, or what a generative engine does (C1 to C5, E2, E3, E8, E9 on their face) → **M**, basis `evaluation`, with the definition sentence quoted, and a note that no such instrument exists yet.
   - Anything the rules above do not reach → the RESULT lists it with the reason, assigns nothing, and the count of unassigned indicators is a number in §2 of the RESULT. A tier is not defaulted.
   The addendum to DN-005 written by this task (`…_DN-005_…_ADDENDUM_01.md`) records the `measurement_basis` field and the reading "M includes instruments this project builds, O is tools this project runs but does not own, D is what only the agency can say", so the three-way split stays three-way and the basis carries the rest. The operator can overrule that reading; it is a naming decision, not a value one.
3. **`scripts/scan_tool_map.py` derives its verdict from the framework record, not from a keyword default.** §2's `verdict` and `why` columns are regenerated from `measurement_tier` and `measurement_basis`, and the `why` cites `tier_source`. A `scan-observable` row must name which collector's entry point reaches which clause of the indicator's spec, or it says `no collector reaches this yet`. `tests/test_scan_frame.py` continues to regenerate and diff, so the table stays generated.
4. **The graph carries both fields and one test asserts coverage.** After projection (`scripts/build_projection.py` or the projection path the framework already uses), a Cypher test asserts every `AssessmentIndicator` has `measurement_tier`, `measurement_basis` and `tier_source`, and that the count per tier matches the RESULT's table. The appendix query that lists indicators shows the tier column.
5. **The product matrix's `legs_withdrawn: [G1-D]` header is moved to where it is true.** G1-D was withdrawn from the L0 host instrument (2026-09-16), not from the product instrument, where it is measured (104 product-tier passes are on the log). Read the withdrawal RESULT before touching it; the header belongs on the L0 host matrix or in the framework record's G1-D entry as `withdrawn_from: L0-host`, and the product matrix's copy is removed. This is one header, and it is in this task because G1-D's tier entry is the place a stranger would look for that fact.
6. **Nothing is measured, re-judged or rebuilt.** No cycle runs. `state/`, `corpus/`, `docs/reports/` byte-identical except the regenerated tool map and any report page that prints the tier column, which the RESULT names.

**Write set:** `framework/ai_readiness_framework.json` through its writer (and the events the writer emits), `scripts/scan_tool_map.py`, `docs/design/scan_tool_map.md` (regenerated), the projection script only if the two fields need mapping, one new test file for decision 4, the DN-005 addendum, the matrix header of decision 5, `seldon_events.jsonl` by this task's transitions, the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-17_measurement_tiers_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Prior art. Read DN-005 §2.2 in full, the tool map, the Screaming Frog investigation (find it; cite its path), the G1 instrument's definition, and the framework writer's contract. If a tier or basis field already exists under another name, use it and say so.
## 2. Decisions 1 and 2, indicator by indicator. The RESULT carries the full 44-row table: code, tier, basis, source locator, and the sentence quoted where the source is the definition.
## 3. Decisions 3, 4, 5, then the DN-005 addendum.
## 4. Gate
`make gate-full` (`-rs`; the tool-map regeneration test and the projection tests are in the full tier), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Failure ships nothing: report and stop.
## 5. Report
RESULT `cc_tasks/2026-09-17_measurement_tiers_RESULT.md`: §0 what prior art already had; §1 the 44-row table; §2 counts per tier and per basis, the number of `estimate` sources, and the list of unassigned indicators with reasons; §3 the tool map's before/after for the C-class rows; §4 the header move; §5 every premise this task file got wrong; §6 the gate table, tier named. The next task under DN-005 §4 item 3 (prescription schema for the Tier M checks) is authored from §1. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → §3 → glob addenda → §4 → §5 → push. Runs after `2026-09-17_dispatcher_notifies.md` so that its finish is the first notified one.
