<!-- authored by cc_tasks/2026-09-23_brief_narrative.md at commit 80ac5f6a4beef31e28e9c3e135f2a587fab87e4b (§Narrative, verbatim; numeral corrections, if any, listed in cc_tasks/2026-09-23_brief_narrative_RESULT.md); framework record at commit 9ffcffddbf8f (framework/ai_readiness_framework.json, generated_from docs/crosswalk/usafacts_operationalization_skeleton.md); cycle of record scan_2026-09-10_rj4. Projected by scripts/build_brief_deck.py into chapter 0 of docs/deck/brief_deck.pptx: the title section is one slide, every ## section one slide, bullets on the slide, paragraphs in the speaker notes. -->
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

- 49 indicators under 7 criteria [G]; USAFacts' A to D kept, E to G added [B].
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
