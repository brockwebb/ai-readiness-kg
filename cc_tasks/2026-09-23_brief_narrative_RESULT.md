# RESULT: the case, as a short paper, projected into the brief's opening slides

**Task:** `cc_tasks/2026-09-23_brief_narrative.md` (no addenda). **Status:** complete. Every gate in §5 ran to its EXIT line. Work commit `f0dd9dc`; launch base `996d8f0`.

## 1. Chapter 0
The narrative is `docs/deck/brief_narrative.md`, with the comment line on top. Chapter 0 has **10 slides**: the title slide plus 9 `## ` sections. They sit after the cover and before chapter A. `docs/deck/brief_deck.pptx` went from 67 to **77 slides**. `brief_appendix.pptx` is still 219 and byte-identical, and its closing `@stamp` is unchanged. Each slide's notes are its section's paragraphs, joined by a blank line, with the tags kept. On the slides the tags are replaced by a footer: `see chapter X · docs/deck/brief_narrative.md`. "The ask" projects only `operator ruling pending`, and its draft is in the notes. Nothing in chapter 0 split, and nothing overflowed.

## 2. Numeral corrections
**None.** Every numeral in the narrative is held by the page its sentence's tag names, with one exception (§3).

**How the gate assigns pages** (decision 2, which does not cover untagged sentences):
- A sentence with no tag takes the tags of its bullet or paragraph, since each tag trails the sentences it covers.
- If the bullet or paragraph has no tag either, it takes its section's tags.
- The title section, the paper's abstract, has no tag. It is checked against every chapter page: 49 is on B's ledger, 264 is in C's table, and 13 is on G's ledger.

**"1,009":** the pack's scan reads this as `1` and `009`. Both are held by page G, whose quotation contains `1,009`.

## 3. The one change to the narrative (a citation, not a numeral)
In the section "What we measured against…", the bullet had its `7` refused under `[B]`. Page B lists the seven criteria as table rows, but the numeral 7 appears nowhere on it. The value is on page G's ledger (`score.py coverage.criteria.total = 7`).

Decision 2's two remedies do not fit this case:
- Correcting to the pack's value would change nothing, because the value is already right.
- Striking applies only when a number "is not in the pack at all", and this one is in the pack.

So I kept the sentence and fixed the citation: `- 49 indicators under 7 criteria; … added [B].` became `- 49 indicators under 7 criteria [G]; … added [B].` The protected-deck check prints this diff against the task's §Narrative on every run. If Desktop would rather strike the bullet, that is a one-line override.

**Struck sentences:** none.

## 4. Claims to check (not edited)
1. "census.gov fails 34 of the 39 legs judged" [G]. Page G says "34 failing of 39 judged" (line 6), and its table is "one row per judged cell" (line 30). The whole cycle judged 23 legs (line 14), so the 39 are judged rows (leg × surface), not legs.
2. "run against 13 federal statistical bodies" (title) and "13 bodies scanned on one cycle" [G]. Page G line 6 says "16 bodies are on this cycle", and Census "ranks 5 of 13". 13 is the number of ranked bodies, not the number scanned.
3. "Every body's rank rests on one leg" [H]. This is supported: page H line 69, and page G's quotation on line 14.

## 5. Premises wrong
1. Decision 2 assumes every numeral is in a sentence with its own `[X]` tag. Untagged sentences, and the untagged title section, needed the page-assignment rule in §2.
2. `test_the_appendix_is_one_slide_per_sheet…` counted every slide not marked `authored` as generated, so the new kind `case` broke it. It now counts the three generated kinds (`indicator`, `rule`, `corpus`) by name.
3. `check_protected_brief_pack.sh` checks the pack task's own write set against HEAD. So it fails on any uncommitted deck work, as it would have for the packaging task. I ran it after the work commit, as that task did.

## 6. Gate (logs under `logs/`, not shipped)
- `make gate-fast`: **2795 passed, 3 skipped, 27 deselected, 12 xfailed**, 663.88 s, EXIT=0 (`logs/narr_gate_fast.log`). This is the fast tier, not the full suite. It is 7 more passes than the packaging task's 2788, which matches the 7 tests added to `tests/test_brief_deck.py` (21 passed there, 0 skipped).
- `seldon verify`: all checks passed, EXIT=0 (`logs/narr_seldon_verify.log`).
- `check_protected_brief_pack.sh`: 61 files checked, 0 drifted, PROTECTED PATHS OK, EXIT=0, after `f0dd9dc` (`logs/narr_protected_pack.log`).
- `check_protected_brief_deck.sh` (base `996d8f0`): both outputs identical, PROTECTED PATHS OK, EXIT=0, both before and after the commit (`logs/narr_protected_deck.log`, `logs/narr_protected_deck_postcommit.log`). The byte-identical set is enforced: `docs/brief/`, `brief_appendix.pptx`, `docs/deck/diagrams/`, `brief_deck_content.md`, `build_brief_pack.py`.

## 7. Spend
Measured session total up to this RESULT: **3,087,214 tokens** over 29 model turns on `claude-opus-5-5`. Of these, 2,948,427 were cache reads and 24,613 were output. The estimate was 2 to 4M. There were no model calls and no projection.
