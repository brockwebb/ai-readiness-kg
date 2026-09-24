# RESULT: narrative v3, criterion labels from page B, the guide's own word, a label gate

**Task:** `cc_tasks/2026-09-24_brief_narrative_v3.md` (no addenda). **Status:** complete; every gate in §6 ran to its EXIT line. Pack commit `12d578c` (decision 1, alone); work commit `d2b2d5b`; launch base `a4fa402`.

## 1. Label changes against page B (lines 24 to 30)
- The task wrote G as "the constructs the federal statistical system adds". Page B's label is "FSS-derived constructs", so both places now read **"G the FSS-derived constructs"**. Every other label in decision 2 already matched page B. A to D are written in lowercase, and the gate compares labels case-insensitively.
- "four" is a word. `prose_numerals` scans digits only, so it passes. `narrative_gate` returns `[]`.
- Page B has a new subsection, `### What the guide says of itself`, after line 12. It quotes the two sentences, with page locators measured from the PDF text layer (p. 2 and p. 5), not typed. The render fails if a sentence does not ground in `doc_text` or grounds on anything other than exactly one PDF page. `numbers.json` did not change.

## 2. The label gate (`tests/test_brief_deck.py::label_defects`): pattern and blind spots
- **Range:** "A through D" or "E to G", followed in the same sentence by a list with exactly one item per letter ("w, w, w and w", 1 to 4 words each, with a leading "are/is/the" removed). The items, in order, must be page B's labels.
- **Lone letter:** A to G, not the sentence's first word, not inside a range, a `[B]` tag or an indicator code (`A10`). Then an optional "the" and a phrase that runs to the next `, ; . : [ ] ( )` or "and". The phrase must equal the letter's label, unless its first word is on a closed stoplist of connectives and verbs.
- **Count:** in a sentence naming "USAFacts" or "the guide", look at the word before the first "criteria" after that name. If it is a number or a number word, it must be 4. If a 4-item list follows it, the list must be A to D's labels.
- **What it misses:** labels given without a letter (v2's "the criteria for evaluation, release and governance"); a letter at the start of a sentence; a label phrase whose first word is on the stoplist; a wrong label on a range with no following list; counts where "USAFacts" is replaced by a pronoun ("their seven criteria"); a USAFacts count that comes after the word "criteria"; and "The evaluation criteria, C and E" (§4).

## 3. Negative controls
The three v2 errors are now permanent parametrized tests (`test_the_label_gate_refuses_each_v2_error`), and each one fails the gate: `7 criteria [G]` ("counted 7, page B says four"); A to D "accessible, documented, licensed and cataloged" (list mismatch); "E evaluation, F release and G governance" (three label mismatches).

## 4. Corrections, and claims to check (not edited)
**No corrections and nothing struck.** The numeral and quotation gate returns `[]`. The protected-deck narrative diff against `73a3c91` plus decision 2 prints no lines. A negative control (`runs today` changed to `runs now`) does print a diff.

Claims to check: (1) "The evaluation criteria, C and E" (§"What it cannot yet see"): C is ACCURATE on page B, and although the skeleton calls C "EVAL-heavy", page B does not call it an evaluation criterion. (2) "24 of them with a rule that runs today": page B says 24 "have a current rule in the registry", so "runs today" is a gloss. (3) "16 of 48 framework indicators" [H] stands beside "49 indicators" elsewhere; carried over, the gap is presumably the DD-054 candidate, not checked here.

## 5. Premises wrong
1. **The byte-identical list cannot hold once page B is committed.** `brief_appendix.pptx` stamps the pack commit on its cover. Line 1 of `brief_deck_content.md` must name that commit, or `test_the_content_file_names_the_pack_it_was_built_from` fails. Both files moved only by that stamp (cover `slide1.xml`, and one SHA). `check_protected_brief_deck.sh` §3 asserts exactly that.
2. **The subsection's placement.** Decision 1 puts it after line 12, inside "How the delta is derived". As a result, that section's last two paragraphs ("An indicator whose…", "Of 49…") now sit under the `###` heading.
3. **G's label** in the task's wording (see §1).
4. **Spend over the estimate** (see §7).

## 6. Gate (logs under `logs/`, not shipped). All ran after `d2b2d5b`.
- `make gate-fast` (fast tier, not the full suite): **2800 passed, 3 skipped, 27 deselected, 12 xfailed**, 633.25 s, EXIT=0 (`logs/narr3_gate_fast.log`).
- `seldon verify`: All checks passed, EXIT=0 (`logs/narr3_seldon_verify.log`).
- `check_protected_brief_pack.sh`: 61 files checked, 0 drifted, PROTECTED PATHS OK, EXIT=0 (`logs/narr3_protected_pack.log`). It also ran green before `12d578c`, while the change was uncommitted.
- `check_protected_brief_deck.sh` (base `a4fa402`): 77 and 219 slides re-rendered identical, no narrative diff, PROTECTED PATHS OK, EXIT=0 (`logs/narr3_protected_deck.log`).

## 7. Spend
Measured session total up to this RESULT: **3,623,327 tokens** over 34 model turns on `claude-opus-5-5`. Of these, 3,460,927 were cache reads and 33,513 were output. That is **above the 1.5 to 3M estimate**; most of the excess is cache reads of the full-page file reads. There were no model calls and no projection.
