# CC Task: the USAFacts note: how their framework was operationalized, in plain narrative

**Date:** 2026-10-14
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** `docs/design/2026-10-12_DN-014_executive_summary_brief.md` (DN-014) as amended by DN-014 ADDENDUM 01 §5 (verified and committed by the v3 task this one runs after).
**Framework layer served (DN-005 §5 rule 1):** §2.1, a view of the framework's provenance.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** ba40cb29
**Why after:** it needs the plain names written by the v3 task's Part A.
**Model:** author
**Spend:** est. 800k tokens. The session writes; Fable reads, at most two rounds.
**Parts:** A 0.40, B 0.40, C 0.20.
**Part map:** A is the derivation; B is the writing and reading; C is the checks and the build.
**Network:** none.

**HEADLESS NOTICE.** No next turn.

## Step 0

If this task is `in_progress` from an earlier dispatch, stop. Confirm the served model equals `seldon models resolve author`.

## Part A: derive, do not recall

From the record and the graph, with locators: which of the seven criteria rest on USAFacts' four qualities (accessible, understandable, accurate, open) by their evidence edges; which three were added, and the sources each one cites; which USAFacts standards from the detailed user guide became checks the harness runs, and which did not and why (gap nodes); the measurement result, that every public-tier check maps to a criterion. Write the derivation to `reports/summary/usafacts_note_source.yaml` with a locator on every fact. Nothing in the note may come from memory of what USAFacts says; it comes from the corpus document and the record.

## Part B: write

`reports/summary/USAFACTS_NOTE.md`, two or three paragraphs. Narrative: what USAFacts set out; what this work took from it unchanged; what it added and on whose evidence; what became measurable and what did not; the result. Plain language: no nodes, edges, counts of nodes or edges, codes, tier letters, or process words. "SI" throughout except inside a published title. No em dashes. Each sentence that states a fact carries, in the source file, the locator that supports it. Fable reads with two questions: does a reader who knows USAFacts' guide learn what was done with it, and is any term on the page one a CIO new to SI would not know.

## Part C: check and build

The text check from the summary runs on the note; the unsupported-sentence check runs with the source file as its evidence; the PDF is rendered by the same script that writes the Markdown.

- check: text check zero findings; quote.
- check: every fact sentence has a locator; the unsupported check passes.
- judgment: Fable's last round, quoted.
- check: `seldon verify`.

## RESULT

Under 25 lines: the criteria mapping in one line each; which standards became checks; Fable's rounds; checks; premises found wrong. `seldon cc complete`, commit, push.
