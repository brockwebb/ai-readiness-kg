# CC Task: narrative v2, USAFacts credited, two counts corrected

**Date:** 2026-09-23
**Project:** ai-readiness-kg
**Authored by:** Desktop session, for ResearchTask `5f1bf9f0`, after the OODA over `2026-09-23_brief_narrative_RESULT.md` (`97b58374`). Operator ruling 2026-09-23 on framing: USAFacts built a framework to help agencies make decisions and it is credited as such; this project's contribution is operationalizing it, adding the criteria it needed to act on, tying each result to an action through the graph, and giving it a conversational interface so a non-specialist can use it. The tone is a project standing on prior work, not one correcting it. Two counts in v1 were wrong and are corrected here (RESULT §4 items 1 and 2).
**Implements:** DN-005 and DN-008 ruling 2, as before.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1.5 to 3M tokens (Opus). Prior narrative task: est. 2 to 4M, measured 3.09M.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Section replacement, nothing else.** In `docs/deck/brief_narrative.md`, replace whole the title section (the `# ` heading and its abstract paragraph), and the four `## ` sections named below, with the text under §Replacements. Every other section stays byte-identical to `f0dd9dc`, including the `[G]` citation fix from the last RESULT §3. The renderer and its tests are unchanged unless the new sections make a slide split or overflow, in which case the RESULT says which.

2. **Same gate as v1**, decision 2 of `2026-09-23_brief_narrative.md`, with the page-assignment rule that RESULT §2 added for untagged sentences. Corrections and struck sentences listed the same way. "Claims to check" the same way; do not edit them.

3. **What the guide says about itself.** Search the USAFacts guide text (`usafacts-ai-ready-data-guide`, read the way `build_brief_pack.py` decision 7 read it) for any sentence in which the guide describes its own scope or limits, for instance that it is a starting point, not exhaustive, expected to evolve, or a framework for decisions rather than a measurement. Quote up to two such sentences in the RESULT with their location. Do not put them in the narrative: a `> ` line must ground in a pack page, and the guide is not one. If Desktop wants a quote in §1, it goes through the pack generator in a later task. If nothing is found, say so.

**Write set:** `docs/deck/brief_narrative.md` (the five sections), `docs/deck/brief_deck.pptx`, `tests/test_brief_deck.py` only if a split or overflow needs a count changed, `scripts/check_protected_brief_deck.sh` (base moves to this launch commit; its narrative diff now compares to §Replacements for the five sections and to `f0dd9dc` for the rest), the RESULT. Byte-identical: everything else the last two deck tasks listed, `brief_appendix.pptx` included.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, both protected checks after the work commit. RESULT `cc_tasks/2026-09-23_brief_narrative_v2_RESULT.md`, under 40 lines: chapter 0 slide count; corrections; claims to check; decision 3's quotes or their absence; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** replace sections → gate the file alone → render → tests → gate → RESULT → push.

---

## Replacements

### Title section (replaces the `# ` heading and the abstract paragraph)

# What a machine sees when it reads federal statistics

USAFacts published a framework to help government agencies decide how to make their data ready for AI. This brief describes what it took to run that framework as a measurement: a test for each of 49 indicators, three criteria the framework needed and did not have, a corpus of 264 admitted documents behind the indicators, and a graph that ties every result to an action an agency can take. The measurement was run against the federal statistical bodies on one scan cycle, 16 on the cycle and 13 ranked, and census.gov is the first body to read its own result. This paper makes the case in the order of the argument; the chapters that follow hold the record in the order of the framework.

### Section "The problem is measurable, and nobody was measuring it" (replaced whole, new title)

## USAFacts built the framework; running it needed tests

- USAFacts' guide gives agencies 7 criteria [G] for AI-ready data, written for the people who decide what to publish [B].
- A criterion says what good looks like. Acting on it needs a test that names which product falls short, why, and what to change first.
- This project keeps the criteria and adds the tests, the criteria the guide did not cover, and the graph from each result to an action [B].

USAFacts did the hard first part: they looked at what AI systems need from public data and wrote it down as criteria an agency can read and agree with. Four of the criteria, A through D, describe the public surface a publisher controls: accessible, documented, licensed and cataloged. That framework is a decision aid, and it works as one. What it does not contain is a test per indicator, and the record says so plainly [B]. Without tests, an agency can endorse the framework and still not know which of its products fails, on which criterion, and for what reason. That is the gap this project set out to close, and it closed it by building on USAFacts' criteria rather than replacing them: a rule for every indicator that has one, the criteria for evaluation, release and governance that a running measurement turned out to need, and a graph in which each failing test points at a ranked action with an effort band. The graph is also served to an assistant over MCP, so the questions this brief asks of the record can be asked in plain language by someone who has never read a rule [D]. Little of the material is original. The corpus is 264 documents [C], the fields the rules read are standards other bodies wrote, and the scoring default is the OECD/JRC Handbook's [H]. The contribution is the join, and the fact that it runs.

### Section "Start with our own product" (replaced whole, same title)

## Start with our own product

- On the cycle of record, census.gov fails 34 of the 39 judged rows [G].
- Hierarchical score 0.080, rank 5 of 13; the rank rests on a single pass, A10 [G].
- One absence runs through most of the failures: the product is not in the catalog census.gov already serves [G].

The cycle of record is `scan_2026-09-10_rj4`. The judged rows are leg by surface, and Census fails 34 of 39 [G]. It ranks 5 of 13 on the hierarchical score and 5 on the flat score, and that rank rests on one leg: 1 pass of 1 judged row on A10, the deep-link test. Were that verdict reversed the body would rank 9 [G]. The ranking is therefore not the finding. The finding is in the reasons column. census.gov serves a public data catalog at data.json with 1805 records, and the catalog holds no record for the flagship products the harness probed. Because there is no record, there is no data dictionary link, no quality or revision metadata, no source lineage, no bureau and program code, and no inventory entry: B1, B4, D3, D4 and G4 all fail for the same absence [G]. This is what the framework is for as a diagnostic. The prescription table lists, for each failing leg, the action, its effort band, and an upper bound on what it would move; the cheapest actions are in the hours band at no cost, and two of them, on F4 and G4, each carry a delta of 0.2 [G]. A single catalog record with the fields the harness reads would move more legs than any other action the agency could take.

### Section "What we measured against, and how it differs from USAFacts" (replaced whole, new title)

## How the indicators relate to USAFacts' criteria

- 49 indicators under 7 criteria [G]; A to D are USAFacts' criteria, E to G are added [B].
- Every indicator operationalizes a criterion. None repeats the guide's text, because the guide wrote criteria, not tests: 27 restated, 22 under added criteria, 0 verbatim [B].
- 24 indicators have a current rule; 5 record a departure from USAFacts' intent, quoted; the items in §8 go back to USAFacts as feedback [B].

The delta page states the derivation rules and applies them to every indicator, so a reader can see what was kept, what was operationalized and what was added [B]. The verbatim test was run against the three USAFacts documents in the corpus with the same grounding normalizer every other span in the record uses, and no indicator's construct or text grounds in them. That is the expected result, not a finding against the guide: USAFacts named criteria, and each indicator is this project's operationalization of one [B]. Three criteria, E evaluation, F release and G governance, have no USAFacts counterpart and are marked added. Where an indicator departs from what USAFacts intended, the departure is quoted, not smoothed over [B]. The page ends with the items this project would hand back to USAFacts as feedback on their guide, in the spirit of a framework they published for others to build on [B].

### Section "What the whole cohort looks like" (replaced whole, same title)

## What the whole cohort looks like

- 16 bodies on the cycle, 13 ranked: 23 legs judged, 1,009 findings [G].
- Every body's rank rests on one leg; both equal-weight scores are printed and no weighting is asserted [H].
- The headline Results are named by id on the results page and traced from there [F].

The cohort result is deliberately not a league table. With equal weights and sparse passes, each body's rank rests on a single leg, F4 for nine bodies and a single pass on G4 or A10 for four, and the concentration sentence for every body is printed [H]. The equal-weight default follows the OECD/JRC Handbook for the case where no basis exists for other weights [H]. What the cohort view does show is the pattern: the same absences recur across bodies, which is what makes the prescriptions transferable.
