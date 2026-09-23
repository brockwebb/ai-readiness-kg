# RESULT: the brief deck, assembled from the material pack

**Task:** `cc_tasks/2026-09-22_brief_deck_assembly.md` (no addenda). **Status:** complete; every gate below ran to its EXIT line. Commits: `f14a3da` (decision 7, gated alone by `check_protected_brief_pack.sh`), `2addd96` (deck), this RESULT.

## 1. What was built
`docs/deck/brief_deck.pptx`, 293 slides, from `docs/deck/brief_deck_content.md` (64 authored sections) plus the appendix, which `scripts/build_brief_deck.py` generates from the pack. The renderer imports `build_framework_deck`'s `parse`, `parse_body`, `layout` (factored out of `build`, the only change to that file), `fits` and `add_runs`. It adds directives (`@table`, `@csv`, `@capture`, `@diagram`, `@provenance`, `@stamp`) that copy pack content by script. Every `> ` line is a quotation, and the renderer refuses the build unless it finds the quotation in the slide's `source:` files under `grounding.normalize`. Any other numeral must be on `numbers.json` under a named page. `--check` is byte-stable because the archive's member timestamps are fixed.

| chapter | sections → slides | target | | chapter | sections → slides | target |
|---|---|---|---|---|---|---|
| cover | 1 → 1 | 1 | | E | 5 → 5 | 5–6 |
| A | 3 → 3 | 2 | | F | 3 → 3 | 1–2 |
| B | 22 → 22 | 12–16 | | G | 5 → 11 | 3–4 |
| C | 5 → 5 | 5–7 | | H | 6 → 9 | 2–3 |
| D | 13 → 16 | 8–12 | | Appendix | 75 → 218 | generated |

Every count includes the chapter's cover slide. B, D, G and H ran over target. They were split, not trimmed. B has the 11 §8 items one per slide and 7 criterion tables. G and H are the pack's tables split at the 14pt floor. The appendix has 49 indicator slides, 25 rule groups and one corpus slide. The groups are by leg, because 54 rules is more than 40 slides. `tests/test_brief_deck.py` asserts that 75 = 49 + 25 + 1.

## 2. Decision 7: the `kept_verbatim_or_restated` column, measured
The three USAFacts documents were read the way the extractor reads them (`run_bulk_extraction.doc_text`, imported). Each indicator's `construct`, then its `indicator`, was tested with `grounding.is_grounded`. Result: **0 verbatim, 27 restated, 22 n/a (added criterion)**, which matches the stated expectation, so there is no span to quote. The column and the one sentence in `B_usafacts_delta.md` changed, plus three counts on `numbers.json`. Pack `--check` passes: 61 files, 0 drifted.

## 3. Diagrams
`mmdc` 11.12.0 is installed, so each of the four Mermaid blocks was drawn once to PNG (`docs/deck/diagrams/E_{a,b,c,d}.png`, `--render-diagrams`). A sidecar holds each source's sha256, and a render refuses if a diagram is stale. The "how to read it" text is quoted under each diagram. Diagrams (c) and (d) are very wide (about 10:1 and 15:1), so they read small on a 16:9 slide.

## 4. Glue sentences (decision 5): what is not pack text
- Slide 1: `Brock Webb`. The date, pack commit and cycle come from `@stamp`.
- Slide 2: "DN-005 §1, transcribed; chapter A has no pack file."
- Slide 31: "Each indicator's cited documents, with their locators where the cell has one, are on its appendix slide."
- Slide 64: "One slide per indicator sheet, one per rule group, and one corpus summary follow, generated from the pack when the deck is built."
- Chapter covers 5, 27 and 32 carry `Pack files: …` labels. These are labels, not sentences.
- Everything else authored is a verified quotation or directive output. That includes chapter A: DN-005 §1 is quoted whole and checked against the DN-005 file.

## 5. Premises the task file got wrong
1. `scripts/numerals.py` is a count-to-word map (`word(5)` → `five`), not a numeral scanner. The scanner that strips codes, ids and dates is `tests/test_brief_pack.py::prose_numerals`. The deck imports it, so both gates use one definition.
2. The framework deck's output is not byte-identical from one run to the next: python-pptx stamps each zip member with the wall-clock time. What does hold is member-identical output. The rebuild after the refactor matches the committed `framework_deck_2026-09-02.pptx` member for member. The `_2026-09-01.pptx` output was built from an older content version and matches neither build. The test compares members.
3. `corpus/manifest.json` has no `source_type`. Its fields are `identity.doc_type` and `screening.decision`, the same ones page C prints. It holds 380 entries, of which 264 are admitted.
4. "82 of 264" and "34 of 39" are not on `numbers.json`: they sit in a pack table and in quoted tool output, which the pack's own gate treats as non-prose. They are on slides 29 and 54 through `@table` and a verified quote. This is not a pack defect, so no Issue was filed.
5. `check_protected_brief_pack.sh` diffs against HEAD, so it cannot pass while deck files are uncommitted. That is why decision 7 was committed and gated alone. The deck was committed before the final gate, and both checks then passed on a clean tree. This task's check diffs against the launch commit (`a3756e3`).
6. Spend was estimated at 3 to 6M tokens. The measured session total is in §7.

## 6. Gate (logs under `logs/`, not shipped)
- `make gate-fast`: **2785 passed, 3 skipped, 27 deselected, 12 xfailed**, 661.51 s, EXIT=0 (`logs/deck_gate_fast.log`). This was the fast tier, not the full suite.
- `seldon verify`: all checks passed, EXIT=0 (`logs/deck_seldon_verify.log`).
- `check_protected_brief_pack.sh`: PROTECTED PATHS OK, EXIT=0, both at decision 7 (`logs/deck_d7_protected_pack.log`) and at the final gate (`logs/deck_protected_pack.log`).
- `check_protected_brief_deck.sh`: pack 61/0 drifted, deck identical, PROTECTED PATHS OK, EXIT=0 (`logs/deck_protected_deck.log`).
- `tests/test_brief_deck.py` and `tests/test_brief_pack.py`: 37 passed, 0 skipped, inside the gate.

## 7. For the operator's read-through
1. **Chapter priority for a first audience.** The deck is built in DN-008 ruling-2 order. Whether a first audience should see G (Census) or B (the USAFacts delta) before C to F is carried to you and not answered here.
2. **Your read of the deck** is the last step before anything leaves the repository. The appendix is 218 of the 293 slides. Whether it ships in the deck or as a separate appendix file is a presentation choice that needs your read.
3. Measured session tokens up to this RESULT: 9,985,558, of which 97.1 percent were cache reads (67 model turns, from this session's transcript).
