# CC Task: narrative v4, last three claims closed, page B subsection placed, 48 and 49 reconciled

**Date:** 2026-09-24
**Project:** ai-readiness-kg
**Authored by:** Desktop session, for ResearchTask `5f1bf9f0`, after the OODA over `2026-09-24_brief_narrative_v3_RESULT.md` (`087adf78`). That RESULT's §4 leaves three claims to check and §5 item 2 a placement defect. This closes them. After this task the narrative goes to the operator's read-through; no further narrative tasks are planned by Desktop.
**Implements:** DN-005 and DN-008 ruling 2, as before.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 2 to 4M tokens (Opus). Narrative tasks have measured 1.2 to 2x their estimates (3.09M on 2 to 4; 2.09M on 1.5 to 3; 3.62M on 1.5 to 3); this estimate is set with that ratio in. Read pages by section, not whole, where a section suffices.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Page B subsection moves to the end of its section.** In `build_brief_pack.py`, `### What the guide says of itself` is emitted after the last paragraph of "How the delta is derived" (the one beginning "Of 49"), so the two paragraphs it swallowed return to their section. Content of the subsection unchanged.

2. **48 and 49, reconciled on the pack, then cited.** The graph holds 49 `AssessmentIndicator` nodes; one has status `candidate` (DD-054) and one is a `paid`-tier candidate; page H's tables sum to 48 because the framework record holds 48. Confirm those counts from the record by script (not from this task). Then `build_brief_pack.py` adds one sentence to page H, at the top of its coverage section, stating the reconciliation in the record's terms, with the candidate named by code and decision, and the counts on `numbers.json` for H. If the confirmed counts differ from what this paragraph says, the RESULT says so and the sentence states the confirmed ones. Regenerate; only `H_limits.md` (and `B_usafacts_delta.md` for decision 1) and `numbers.json` may change; `--check` and the pack's protected check pass; committed alone first.

3. **Sentence corrections in `docs/deck/brief_narrative.md`**, exact old to new, nothing else changes:
   - Abstract: "24 of them with a rule that runs today," → "24 of them with a current rule in the registry,"
   - §"What it cannot yet see", bullet 1: "16 of 48 framework indicators are measured; 8 have a harness built; 24 are specified only [H]." → "Of the 48 indicators in the framework record, 16 are measured, 8 have a harness built and 24 are specified only; the record's 49th is a candidate [H]." Adjust the last clause to page H's new sentence so the label gate and the numeral gate both pass, and list the adjustment.
   - Same section, bullet 3: "The evaluation criteria, C and E, are largely unmeasured: they need benchmark sets this project has not built [G]." → "Criteria C accurate and E the TEVV loop are largely unmeasured: the requirements table says what would unlock them, and it is reference material this project has not built [G]." Check the requirements table on page G for what it actually says C and E need; if "reference material" is not a fair one-phrase reading of the C and E rows, replace it with the table's own wording for those rows and list the change.

4. **Same three gates** (numerals and quotations, labels, protected diff). Corrections, struck sentences and claims to check listed the same way; not edited.

**Write set:** `scripts/build_brief_pack.py` (decisions 1 and 2), `docs/brief/B_usafacts_delta.md`, `docs/brief/H_limits.md`, `docs/brief/numbers.json` (via the generator only), `docs/deck/brief_narrative.md` (decision 3 only), `docs/deck/brief_deck.pptx`, `docs/deck/brief_appendix.pptx` and line 1 of `brief_deck_content.md` (pack-commit stamp only, as v3 RESULT §5.1 established), `tests/test_brief_pack.py` (the reconciliation sentence's counts match the record), `scripts/check_protected_brief_deck.sh` (base moves to this launch commit; narrative diff base is `d2b2d5b` plus decision 3), the RESULT. Byte-identical: every other file under `docs/brief/` and `docs/deck/`, `build_brief_deck.py`, `tests/test_brief_deck.py` unless a count assertion must move, and every directory the earlier deck tasks listed.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, both protected checks after the work commit. RESULT `cc_tasks/2026-09-24_brief_narrative_v4_RESULT.md`, under 35 lines: the reconciliation sentence as emitted and the counts confirmed; the C and E wording as landed; corrections; claims to check; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** 1 and 2 (pack, committed alone) → 3 → 4 → render → tests → gate → RESULT → push.
