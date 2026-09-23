# CC Task: the case, as a short paper, projected into the brief's opening slides

**Date:** 2026-09-23
**Project:** ai-readiness-kg
**Authored by:** Desktop session, for ResearchTask `5f1bf9f0`, from the OODA over `2026-09-23_brief_deck_packaging_RESULT.md` (`bffd0ed2`, closed clean: 67-slide brief, 219-slide appendix). Operator direction 2026-09-23: the deck needs a recommended order and a narrative that builds the case and walks each chapter in logical order; start with a short paper, then summarize it into the opening slides, bullets on the slide and the paper's prose in the notes. The paper is in §Narrative below. It is authored text, the one place in the brief where argument is made rather than record transcribed, and it is written so every number in it is a pack number and every chapter reference names the page the reader can check. This session writes it to disk verbatim, gates it, and projects it.
**Implements:** DN-005 (the brief is a view of the framework) and DN-008 ruling 2 (chapter order A to H stands for the body; the case is a chapter 0 that references the body in the order of the argument, which is not the order of the record).
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 2 to 4M tokens (Opus). Last two deck tasks: est. 3 to 6M measured 9.99M; est. 2 to 4M measured 4.48M. The RESULT ends with the measured total and the model.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line. Targeted reads only.

## Decisions

1. **The paper is the source; the slides are a projection.** Write §Narrative below, verbatim, to `docs/deck/brief_narrative.md` with the pack's generated-from comment line on top (record commit, cycle of record, and the commit of this task file). `build_brief_deck.py` gains a chapter 0, "The case", rendered from that file: the title section is one slide; every `## ` section is one slide whose bullets are the section's `- ` lines and whose speaker notes are the section's paragraphs, in full. The `[X]` chapter tags stay in the notes and become a small "see chapter X" footer on the slide. Notes go on the pptx notes slide (python-pptx `slide.notes_slide.notes_text_frame`), so the prose travels with the deck and can be pulled back out as the paper. Chapter 0 goes after the cover and before A. The closing slide's `@stamp` is unchanged.

2. **The gate applies to authored argument exactly as it applies to transcription.** Every numeral in the narrative, after `tests/test_brief_pack.py::prose_numerals` strips codes, ids, versions and dates, must be a `value` on `docs/brief/numbers.json` under the page the sentence's `[X]` tag names, or a cell in a table on that page, or inside a `> ` quotation on that page. Every `> ` line in the narrative must ground in the named page under `grounding.normalize`. A numeral that fails is a Desktop transcription error: correct it to the pack's value, keep the sentence, and list every correction in the RESULT by section and old-to-new value. A sentence that cannot be corrected (the number is not in the pack at all) is struck and listed. Nothing else in the narrative changes: no rewording, no additions, no reordering. If a sentence reads to you as a claim the pack does not support, list it in the RESULT under "claims to check" with the pack page you looked at; do not edit it.

3. **Chapter order for a first audience, decided.** The body stays in ruling order A to H. The case (chapter 0) walks the argument in this order: the problem, the Census result as the hook, then the measurement, its grounding, the instrument, the architecture, the results across the system, the limits, the ask. A Census audience sees its own product first and the method second; a federal statistical system audience sees the same slides, and the ask changes. The ask section is marked for the operator's ruling and is not projected until he rules; render it as a slide titled "The ask" whose only bullet is "operator ruling pending" and whose notes hold the draft.

4. **Tests.** `tests/test_brief_deck.py` adds: chapter 0 slide count equals the number of `## ` sections plus one; every chapter 0 slide has notes and the notes equal the section's paragraphs; the narrative passes the numeral and quotation gates; both outputs remain `--check` stable.

**Write set:** `docs/deck/brief_narrative.md` (new, verbatim from §Narrative, plus the comment line), `scripts/build_brief_deck.py`, `docs/deck/brief_deck.pptx`, `tests/test_brief_deck.py`, `scripts/check_protected_brief_deck.sh` (base moves to this task's launch commit), the RESULT. Byte-identical: everything under `docs/brief/`, `docs/deck/brief_appendix.pptx`, `docs/deck/diagrams/`, and every directory the packaging task listed. No projection, no model call.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, both protected checks. RESULT `cc_tasks/2026-09-23_brief_narrative_RESULT.md`, under 50 lines: chapter 0 slide count; every numeral correction (section, old, new, page); every struck sentence; "claims to check"; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** write the narrative file → gate it alone (numerals, quotations) → renderer → tests → gate → RESULT → push.

---

## Narrative

# What a machine sees when it reads federal statistics

The framework in this brief is a set of 49 tests that ask one question of a statistical agency's website: when an AI system reads it, what does it get? The tests were built by operationalizing the USAFacts criteria for AI-ready government data, grounded in 264 admitted documents, and run against 13 federal statistical bodies on one scan cycle. census.gov is the first body to read its own result. This paper makes the case in the order of the argument; the chapters that follow hold the record in the order of the framework.

## The problem is measurable, and nobody was measuring it

- AI systems now answer questions about federal statistics from what agency websites serve to a crawler.
- USAFacts published criteria for AI-ready government data. They are criteria, not tests.
- An agency cannot improve what it cannot measure, and cannot compare itself with peers without a shared instrument.

USAFacts' guide gives government agencies seven criteria for AI-ready data. Four of them, A through D, describe what a publisher must put on the public surface: accessible, documented, licensed and cataloged, in the agency's own words. Those criteria are written for a human program manager reading a page. They are not written for a test that runs against a URL and returns a verdict, and USAFacts did not supply indicator-level tests beneath them [B]. So the criteria could be endorsed and could not be applied. That is the gap this project closes: a shared measurement, run the same way against every body, that a publisher can rerun on its own product before anyone else does.

## Start with our own product

- On the cycle of record, census.gov fails 34 of the 39 legs judged [G].
- Hierarchical score 0.080, rank 5 of 13; the rank rests on a single pass, A10 [G].
- One cause runs through most of the failures: the product is not in the catalog census.gov already serves.

The cycle of record is `scan_2026-09-10_rj4`. Census ranks 5 of 13 on the hierarchical score and 5 on the flat score, and that rank rests on one leg: 1 pass of 1 judged row on A10, the deep-link test. Were that verdict reversed the body would rank 9 [G]. The ranking is therefore not the finding. The finding is in the reasons column. census.gov serves a public data catalog at data.json with 1805 records, and the catalog holds no record for the flagship products the harness probed. Because there is no record, there is no data dictionary link, no quality or revision metadata, no source lineage, no bureau and program code, and no inventory entry: B1, B4, D3, D4 and G4 all fail for the same absence [G]. The cheapest actions in the prescription table are in the hours band at no cost, and two of them, on F4 and G4, each carry an upper-bound delta of 0.2 [G]. A single catalog record with the fields the harness reads would move more legs than any other action the agency could take.

## What we measured against, and how it differs from USAFacts

- 49 indicators under 7 criteria; USAFacts' A to D kept, E to G added [B].
- 0 of the 49 are USAFacts' words: 27 restated, 22 under added criteria [B].
- 24 indicators have a current rule; 5 record a departure from USAFacts' intent, quoted [B].

The delta page states the derivation rules and applies them to every indicator, so the reader can see what was kept, what was operationalized and what was added [B]. The verbatim test was run against the three USAFacts documents in the corpus with the same grounding normalizer every other span in the record uses, and no indicator's construct or text grounds in them: USAFacts named criteria, and every indicator is this project's operationalization of one. Three criteria, E evaluation, F release and G governance, have no USAFacts counterpart and are marked added. Where an indicator departs from what USAFacts intended, the departure is quoted, not smoothed over. The page ends with the items this project would hand back to USAFacts as feedback on their guide [B].

## Every indicator points at a document, and the pointing is uneven

- 264 documents admitted; 82 cited by at least one indicator [C].
- 9 of 49 evidence cells carry a pinpoint locator; 27 of 147 evidence edges are located; 16 indicators have no evidence edge [C].
- No admitted document matches Title 13, CIPSEA or the Statistical Policy Directives [C].

The provenance page states its coverage first, because the honest number is the useful one. Most indicators cite their sources as general support without a place inside the source, and 16 cite nothing by edge at all [C]. The corpus is weighted toward federal (94 admitted) and academic (60) documents, with standards (34) cited at the highest rate [C]. The three statutory instruments a federal statistician would look for first are absent from this corpus; that is a statement about the corpus, not about the instruments, and the statistical-policy corpus lives in a separate graph this page does not reach into [C]. The locator backfill is an open task on the graph and is not scheduled [H].

## Anyone can run it

- The runbook is a sequence of commands with their captured output, failures included [D].
- No fetch is needed to reproduce the brief: every page reads the published cycle back through the same tools [D].
- The framework is served over MCP, so an assistant can ask the record the same questions this brief does [D].

The demo chapter is not a screenshot. It is each command the operator would type, followed by the output the harness produced when the pack was generated, captured once and checked into the record [D]. A command that failed stays in with its failure. The point is that the brief is a reading of the record, not a rendering of it: the same commands against the same cycle give the same numbers, and a different cycle gives different ones.

## How it is built

- Record, rules, cycle, findings, score: five layers, each generated from the one before [E].
- Rules supersede; every finding names the rule version that produced it [E].
- The scan cycle is frozen as a cycle of record; nothing in this brief was refetched [E].

The four diagrams on the architecture page show the record and its supersession chain, the path from an indicator to a rule to a finding, and how a cycle becomes the cycle of record [E]. Under each diagram is the text that says how to read it. The design choice that matters for a reader is that no layer is edited by hand: the framework record is generated from the crosswalk skeleton, the rules are versioned, the cycle is judged once and frozen, and the brief is generated from all of it.

## What the whole cohort looks like

- 13 bodies scanned on one cycle: 23 legs judged, 1,009 findings [G].
- Every body's rank rests on one leg; both equal-weight scores are printed and no weighting is asserted [H].
- The headline Results are named by id on the results page and traced from there [F].

The cohort result is deliberately not a league table. With equal weights and sparse passes, each body's rank rests on a single leg, F4 for nine bodies and a single pass on G4 or A10 for four, and the concentration sentence for every body is printed [H]. The equal-weight default follows the OECD/JRC Handbook for the case where no basis exists for other weights [H]. What the cohort view does show is the pattern: the same absences recur across bodies, which is what makes the prescriptions transferable.

## What it cannot yet see

- 16 of 48 framework indicators are measured; 8 have a harness built; 24 are specified only [H].
- 3 indicators are unassigned to a measurement tier, each with the reason the record gives [H].
- The evaluation criteria, C and E, are largely unmeasured: they need benchmark sets this project has not built [G].

The limits page lists every indicator the record does not mark measured, with the record's own reason where it has one [H]. Several reasons say the same thing: what is missing is a standard to test against, not a tool or a grant. The requirements table on the Census page names what would unlock each unmeasured test and who would provide it, from an open-source parser to a publisher's edge logs [G]. Two roadmap items are already on the graph: session-spend estimation, and a bake-off against the National Secure Data Service's AI-readiness tools when their access is known [H].

## The ask

- OPERATOR RULING PENDING.

Draft, for the operator's ruling and not projected until ruled. For Census: publish the catalog record for the flagship products with the fields the harness reads, and let the harness run a second cycle to measure the change. For the federal statistical system: adopt the indicator set as a shared measurement, return the feedback items to USAFacts jointly, and nominate one product per body for the second cycle. For both: the record, the rules and the harness are public; run them before anyone else does.
