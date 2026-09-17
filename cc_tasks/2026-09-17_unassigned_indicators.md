# CC Task: the 20 unassigned indicators get a tier or a source-shaped reason they cannot have one

**Date:** 2026-09-17
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-17_measurement_tiers_RESULT.md` §2 (the 20 `tier_unassigned_reason` rows and the candidate each names) and §5 premises 5 and 6.
**Implements:** DN-005 §4 item 2, second half: a `measurement_tier` on every indicator node, sourced. DN-005 ADDENDUM_01 for the field readings.
**Framework layer served (DN-005 §5 rule 1):** §2.2.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. Where a candidate O tool's documentation is not on disk, the indicator stays unassigned with that stated; nothing is fetched in this task.

---

## 0. Where the 20 stand

Each carries a reason and a candidate. By candidate: D for E1, E2, E3, E7, F1, F5 (agency-side practices); M for B4, D2, D3, G4, G5 (structured-field legs not built); O for B2, C5, F2, F3, and A7 or B1; M judged reading for B6; undetermined for B5 and G3. None was defaulted, and this task does not default them either.

**Decisions taken here (operator overrides later):**

1. **D assignments come from the definition text.** For each of the six D candidates, quote the clause of the indicator's definition that places the act on the agency's side of publication (pre-registration, before going live, a tracked internal metric). If the clause is there, assign D, basis `declaration`, source the quote. If it is not, the indicator stays unassigned and the reason says what the definition actually says.
2. **M assignments require naming the structured field and the collector entry point that would read it.** For B4, D2, D3, G4, G5: name the field (a schema.org or DCAT-US property, an HTTP header, a terms endpoint) with its locator in the corpus document, and the existing collector entry point from the tool map §1 that could read it. Assign M, basis `harness_leg`, with `tier_note: no rule in rules.CURRENT yet` and the named field and collector on the node. If no corpus document names a field, stay unassigned.
3. **O assignments require the tool's documentation on disk.** For B2, C5, F2, F3, A7, B1: check `corpus/` for the named tool (`extruct` docs, AIDRIN, `oasdiff`, the Wayback CDX API). Where it is on disk, assign O with the locator. Where it is not, the node keeps its reason and gains `open_tool_candidate` with the tool name and the sentence "documentation not in corpus"; that field is the shopping list for a later ingest task, and it is not a tier.
4. **B6 is M judged reading on the G1 precedent only if the reading is the same kind of act** (a pinned consumer restating a surface and a preservation score). If "plain-language" and "current" need a different instrument, say so and leave it unassigned.
5. **B5 and G3 stay undetermined unless a definition clause or a corpus document settles them.** An undetermined row with its reason is a finding, not a failure.
6. **The distribution literal in `tests/test_measurement_tiers.py` moves to the new counts**, and the tool map regenerates. No matrix, figure or report is rebuilt; the site's framework copy and manifest move as in the predecessors.

**Write set:** `framework/ai_readiness_framework.json` through `framework_writeback.save`; `scripts/tag_measurement_tiers.py` (the rules for decisions 1 to 4); `tests/test_measurement_tiers.py`; `docs/design/scan_tool_map.md` (regenerated); the site payloads the predecessor named; `scripts/check_protected_unassigned_tiers.sh` (new); `seldon_events.jsonl`; the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-17_unassigned_indicators_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 to 5, indicator by indicator, with the quote or locator each rests on.
## 2. Decision 6.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths, projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-17_unassigned_indicators_RESULT.md`: §0 the 20-row table (code, tier or still unassigned, basis, source or reason, `open_tool_candidate` where set); §1 the new counts per tier and basis and the remaining unassigned count; §2 the tools whose documentation is not on disk, as one list; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
