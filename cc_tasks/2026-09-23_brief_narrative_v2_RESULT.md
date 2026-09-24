# RESULT: narrative v2, USAFacts credited, two counts corrected

**Task:** `cc_tasks/2026-09-23_brief_narrative_v2.md` (no addenda). **Status:** complete. Every gate in §6 ran to its EXIT line. Work commit `73a3c91`; launch base `3f0d0e7`.

## 1. Chapter 0
- The title section and the four named `## ` sections were replaced whole with §Replacements. Every other section, and the comment line, is byte-identical to `f0dd9dc`.
- Chapter 0 is still **10 slides** (deck slides 2 to 11). The deck is still **77 slides**.
- Nothing in chapter 0 split, and nothing overflowed. `brief_appendix.pptx` is byte-identical at 219 slides. `build_brief_deck.py` and `tests/test_brief_deck.py` are unchanged.

## 2. Corrections
**None; nothing struck.** `narrative_gate` returns `[]` on the file by itself, using the page-assignment rule from the last RESULT §2. The protected-deck diff against `f0dd9dc` + §Replacements prints no lines. A negative control (`1805` → `1806`) does print a diff.

## 3. Claims to check (not edited)
1. **"USAFacts' guide gives agencies 7 criteria [G]"** (section "USAFacts built the framework…", bullet 1). Page B line 12 says "USAFacts names four criteria". The guide text itself has four headed criteria: ACCESSIBLE, UNDERSTANDABLE, ACCURATE, OPEN. The 7 on G is `coverage.criteria.total`, the framework's count after E to G were added. The gate passes this number, but the attribution is wrong. The same section's paragraph says "Four of the criteria, A through D", which contradicts the bullet. v1 had the same error ("seven criteria").
2. **"A through D … accessible, documented, licensed and cataloged"** (same paragraph, carried over from v1). Page B lines 24 to 27 name A to D as ACCESSIBLE, UNDERSTANDABLE, ACCURATE and OPEN.
3. **"E evaluation, F release and G governance"** (section "How the indicators relate…", and "evaluation, release and governance" in the first section). Page B lines 28 to 30 name E as the TEVV loop, F as release engineering, and G as FSS-derived constructs. "Governance" does not name G.
4. Supported: "16 bodies on the cycle, 13 ranked" and "34 of the 39 judged rows" match page G line 6. These close claims 1 and 2 from the last RESULT §4.

## 4. Decision 3: what the guide says about itself
The guide was read through `run_bulk_extraction.doc_text` (`corpus/crosswalk/usafacts-ai-ready-data-guide.pdf`), which is how `build_brief_pack.py` reads it:
- PDF p. 2: "As government continues to evolve its role as a data provider to AI systems, these criteria should provide a roadmap for allowing AI to not only access, but also understand and validate the data they are retrieving and presenting to users."
- PDF p. 5: "USAFacts stands ready to collaborate with federal, state, and local agencies as well as industry leaders to establish best practices for AI-ready open data."

The guide never calls itself exhaustive, a starting point, or a measurement. It calls itself "guidelines" (p. 1) and a "roadmap". Neither quotation is in the narrative.

## 5. Premises wrong
1. The task says the two wrong counts in v1 are corrected, and they are. But the replacement text keeps v1's criterion miscount and its A to D labels (§3 items 1 and 2), and adds item 3. These are Desktop authoring errors that the numeral gate cannot catch, because 7 is a real value on G.
2. `$(…)` strips trailing newlines, so the first draft of the new narrative diff in `check_protected_brief_deck.sh` flagged the file's final newline as a false difference. The check now diffs against a temp file.
3. The write set left out `scripts/build_brief_deck.py`, so the check now protects it outright.

## 6. Gate (logs under `logs/`, not shipped). All ran after `73a3c91`.
- `make gate-fast` (fast tier, not the full suite): **2795 passed, 3 skipped, 27 deselected, 12 xfailed**, 642.75 s, EXIT=0 (`logs/narr2_gate_fast.log`).
- `seldon verify`: All checks passed, EXIT=0 (`logs/narr2_seldon_verify.log`).
- `check_protected_brief_pack.sh`: 61 files checked, 0 drifted, PROTECTED PATHS OK, EXIT=0 (`logs/narr2_protected_pack.log`).
- `check_protected_brief_deck.sh` (base `3f0d0e7`): 77 and 219 slides re-rendered identical, no narrative diff, PROTECTED PATHS OK, EXIT=0 (`logs/narr2_protected_deck.log`).

## 7. Spend
Measured session total up to this RESULT: **2,093,825 tokens** over 28 model turns on `claude-opus-5-5`. Of these, 2,000,020 were cache reads and 12,426 were output. The estimate was 1.5 to 3M. There were no model calls and no projection.
