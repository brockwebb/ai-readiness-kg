# CC Task: narrative v3, criterion names from the page, the guide's own word for itself, a label gate

**Date:** 2026-09-24
**Project:** ai-readiness-kg
**Authored by:** Desktop session, for ResearchTask `5f1bf9f0`, after the OODA over `2026-09-23_brief_narrative_v2_RESULT.md` (`3afb7840`). That RESULT §3 found three authoring errors in the narrative, all Desktop's: USAFacts names four criteria, not seven; their four are ACCESSIBLE, UNDERSTANDABLE, ACCURATE and OPEN; E, F and G are the TEVV loop, release engineering and FSS-derived constructs. None is a numeral, so the numeral gate passed them. This task corrects the sentences, quotes the guide's description of itself through the pack, and adds a gate on criterion labels so the next hand edit cannot repeat this.
**Implements:** DN-005 and DN-008 ruling 2, as before.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1.5 to 3M tokens (Opus). v2: est. 1.5 to 3M, measured 2.09M.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **The guide's own words go on page B, through the generator.** `build_brief_pack.py` adds to `B_usafacts_delta.md`, directly after the sentence at line 12 ("USAFacts names four criteria"), a short subsection "What the guide says of itself" holding, as `> ` lines with locator (doc id, PDF page), the two sentences the v2 RESULT §4 found: p. 2 ("As government continues to evolve its role … presenting to users.") and p. 5 ("USAFacts stands ready to collaborate …"). Each must ground in `doc_text` of `usafacts-ai-ready-data-guide` under `grounding.normalize` or the build fails. Regenerate the pack; only `B_usafacts_delta.md` may change; `--check` and `check_protected_brief_pack.sh` pass; committed alone first.

2. **Sentence corrections in `docs/deck/brief_narrative.md`**, exact old to new, nothing else in the file changes:
   - Abstract: "a test for each of 49 indicators, three criteria the framework needed and did not have," → "49 indicators written as tests, 24 of them with a rule that runs today, three criteria the framework needed and did not have,"
   - §"USAFacts built the framework; running it needed tests", bullet 1: "USAFacts' guide gives agencies 7 criteria [G] for AI-ready data, written for the people who decide what to publish [B]." → "USAFacts' guide gives agencies four criteria for AI-ready data, accessible, understandable, accurate and open, written for the people who decide what to publish [B]."
   - Same section, paragraph: "Four of the criteria, A through D, describe the public surface a publisher controls: accessible, documented, licensed and cataloged." → "The guide calls itself a roadmap, and its four criteria, A through D, are accessible, understandable, accurate and open [B]." Then insert, as its own paragraph immediately after that sentence's paragraph, the p. 2 quotation as a `> ` line tagged [B], verbatim from the regenerated page.
   - Same paragraph: "the criteria for evaluation, release and governance that a running measurement turned out to need," → "the three criteria a running measurement turned out to need, E the TEVV loop, F release engineering and G the constructs the federal statistical system adds,"
   - §"How the indicators relate to USAFacts' criteria", bullet 1: "A to D are USAFacts' criteria, E to G are added [B]." → "A to D are USAFacts' four, E to G are added [B]."
   - Same section, paragraph: "Three criteria, E evaluation, F release and G governance, have no USAFacts counterpart and are marked added." → "Three criteria, E the TEVV loop, F release engineering and G the FSS-derived constructs, have no USAFacts counterpart and are marked added [B]."
   Where my wording of a criterion label differs from page B lines 24 to 30, use the page's label verbatim and list the change in the RESULT. "four" is written as a word because page B line 12 writes it as a word; if `prose_numerals` scans words and refuses it, the RESULT says so and the sentence stays.

3. **Label gate.** `tests/test_brief_deck.py` adds a test that parses the criteria table on page B (letter to label) and checks every place in the narrative where a criterion letter A to G is followed, within the same sentence, by a label phrase: the phrase must match the page's label for that letter, case-insensitive, after `grounding.normalize`. It also checks that any count of "USAFacts' criteria" in the narrative (the sentence containing "USAFacts" and "criteria" and a number or number word) is four. Negative controls, run once and reported: revert each of the three v2 errors in a temp copy; all three must fail the test. Design the matching against the actual sentences in the file, and say in the RESULT what pattern it uses and what it would miss.

4. **Same numeral and quotation gate as v1 and v2.** Corrections, struck sentences and "claims to check" listed the same way; not edited.

**Write set:** `scripts/build_brief_pack.py` (decision 1 only), `docs/brief/B_usafacts_delta.md` and `numbers.json` if a count changes (via the generator only), `docs/deck/brief_narrative.md` (decision 2 only), `docs/deck/brief_deck.pptx`, `tests/test_brief_deck.py`, `tests/test_brief_pack.py` (a test that the two quotations ground), `scripts/check_protected_brief_deck.sh` (base moves to this launch commit; narrative diff base is `73a3c91` plus decision 2), the RESULT. Byte-identical: every other file under `docs/brief/` and `docs/deck/`, `build_brief_deck.py`, and every directory the earlier deck tasks listed.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, both protected checks after the work commit. RESULT `cc_tasks/2026-09-24_brief_narrative_v3_RESULT.md`, under 40 lines: the label changes made against page B; the gate's pattern and its blind spots; negative-control results; corrections; claims to check; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** 1 (pack, committed alone) → 2 → 4 (gate the file) → 3 → render → tests → gate → RESULT → push.
