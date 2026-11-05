# DN-020: USAFacts' three-track framework is the base document, the diagnostic's sixteen checks are placed on its ladder, and every departure is a recorded tailoring

**Date:** 2026-11-04
**Status:** Decision note. Governs how the readiness diagnostic is parented, explained and illustrated for the ICSP and the working group. Supersedes the four-criteria parenting in DN-018 §2 and the "Criterion" column of the roll-up view (DN-019 §4 rung 1).
**Depends on:** DN-014 (three tiers of check), DN-015 (the four states), DN-016 (vocabulary), DN-019 (measurement specification and the view ladder).
**Question it answers:** the operator's finding of 2026-11-02 that every readiness artifact descends from USAFacts' early-2025 guide (four criteria) while USAFacts' current framework (August 2026) has three tracks with three levels each; and the operator's direction of 2026-11-03 that the framework is a starting point to be tailored, not a specification to be followed, and that nothing is re-measured.

## 0. Bottom line

1. The base document is now `usafacts-ai-ready-framework-deck-2026-08` (with `usafacts-ai-ready-framework-overview-2026`): three tracks, Agentic Access, Agentic Context, Agentic Evaluation, three levels in each, three prerequisites before any level applies, modeled on SLSA. The four-criteria guide (`usafacts-ai-ready-data-guide`) is its predecessor and stays in the lineage.
2. The sixteen measured checks are placed on that ladder (section 4). Nothing is re-run; the placement is a re-parenting of existing MeasurementSpec nodes, with the cycle of record unchanged.
3. Every departure from USAFacts' text is a tailoring entry (section 3), with the reason, in the sense of ISO/IEC/IEEE 15288 Annex A: the base is adopted, then adapted, and the adaptation is recorded so a reader can see what was kept and what was changed.
4. Two documents come out of this note (section 6), one per audience, built from the record. Their pictures are generated from the prompts in section 7, outside this repository.

## 1. The base document

USAFacts presented the framework at the Partnership for Public Service Federal Data Excellence roundtable on 2026-08-26 (`usafacts-ai-ready-framework-deck-2026-08`, slides 9, 15 to 20; `usafacts-ai-ready-framework-overview-2026`). Its parts, in its own words:

- Scope: data that SI agents can use when answering a member of the public, not training data for frontier models (slide 11).
- Prerequisites: open by default (the OPEN Government Data Act); discoverable, registered on data.gov or reachable on the open web; clearly licensed on the landing page (slide 15).
- Three tracks, each a ladder of three levels, "modeled on SLSA" (slide 16): the agency climbs at its own pace and Level I is meaningful on its own.
- Agentic Access I: machine-readable formats, crawlable. II: an API, usage documentation, lineage and change notes. III: read-only MCP servers, agent-to-agent protocols, pilots (slides 16, 18).
- Agentic Context I: published methodology, on the open web. II: field-level descriptions, provenance, update cadence, best practices. III: pragmatics and expert context, edge cases, context-specific MCP (slides 16, 19).
- Agentic Evaluation I: a public evaluation set, open license, reported pass rates. II: regular benchmarks against commercial models, scores and failures published, a feedback loop. III: coordinated evaluation across agencies, red-teaming, programs with SI labs (slides 16, 20).
- It becomes criterion 05, "AI-ready data", of the Federal Data Excellence standards (slide 9).
- Intended use: an agency places itself on each track and decides where to invest (slide 21's worked example).

Slide 16 gives Context I as "definitions and units documented for humans" and slide 19 as "published methodology on the open web". The operator reads these as one thing, documentation written for people, and this note follows that reading.

SLSA (`slsa-specification-v1-0`) is a maturity ladder for software supply chains: levels are cumulative, each level is a set of verifiable requirements, and an organisation claims a level rather than a score. USAFacts borrowed the shape, not the content.

## 2. Lineage

The lineage the two documents will show, each step cited to its text:

1. **FAIR, 2016** (`wilkinson-2016-fair-guiding-principles`): Findable, Accessible, Interoperable, Reusable, written so that machines as well as people can act on data. The principles are deliberately high level and have been read many ways (`jacobsen-2020-fair-principles-interpretations`).
2. **USAFacts guide, early 2025** (`usafacts-ai-ready-data-guide`): four criteria, Accessible, Understandable, Accurate, Open, written from USAFacts' experience as a heavy consumer of federal data. Accessible and Open are FAIR's F, A and R aimed at a program; Understandable is I plus documentation; Accurate is new, a call for public evaluation sets.
3. **USAFacts framework, August 2026** (the base document): Accessible becomes the Access track; Understandable becomes the Context track; Accurate becomes the Evaluation track; Open moves out of the ladder and becomes a prerequisite, together with discoverability and licensing. Levels are added, borrowed from SLSA.
4. **This project**: the ladder with a sensor on it. Each check is a measurement specification (DN-019), each prerequisite is tested rather than declared, and the tracks the sensor cannot reach yet are marked as such rather than scored.

The claim this project makes is operationalization and decision support, not a new framework. Prior art for decision support over a maturity ladder is SLSA itself (the level you hold tells you the next requirement to meet) and the FCSM data quality framework's use in agency self-assessment. The "machine as a first-class user" framing is the operator's own (AR-4, 2026-10-14) and is stated as such.

## 3. Tailoring record

Each entry: what USAFacts says, what this project does instead, why. The base is adopted; these are the adaptations.

- **T1, prerequisites are tested, not declared.** USAFacts lists three prerequisites and asks the agency to confirm them. The diagnostic measures them from outside: discoverability by three checks (in the site's page list; labels itself as a dataset; listed in the agency's data inventory, which is what data.gov harvests) and licensing by one (terms of reuse under a recognised name). Reason: a prerequisite that is only asserted cannot anchor a level. This also answers whether data.gov is a check or the entry point: USAFacts put it before the ladder, and so does the diagnostic.
- **T2, every check carries a measurement specification.** USAFacts' level captions are outcomes ("crawlable", "an API"). Each check here states its sensor, what it reads, the range that counts, and the source for the expected behaviour (DN-019, after ISO/IEC/IEEE 15939). Reason: a level claim needs a repeatable reading behind it, or two agencies can claim the same level for different reasons.
- **T3, a level is reported per check, and an agency's position on a track is the highest level at which every measured check passes.** USAFacts has the agency claim a level. Reason: SLSA's own rule (levels are cumulative) applied with the sensor's readings. A check not measured for an agency is left out of that agency's count and never read as a fail (DN-015; unchanged from the roll-up's footnote).
- **T4, Evaluation is empty and said to be empty.** No check measures the Evaluation track. USAFacts asks for public evaluation sets and benchmark loops; building one is a TEVV program (NIST AI RMF, MEASURE function), not a web check, and is deferred. Reason: an empty track shown honestly is the decision-support signal the operator raised with USAFacts in August 2026: the framework names the destination but carries no instrument for it. Nothing in this note designs that instrument.
- **T5, the four states of a reading (DN-015) stay.** USAFacts has pass or not. The diagnostic keeps pass, fail, blocked and not measured, because a public client is sometimes refused where a corporate crawler is not, and a refusal is a finding, not a failure.
- **T6, vocabulary.** Government material past 29 September 2026 says SI; USAFacts' own titles, vendor products and material before that date keep AI as written. DN-016 governs the rest.

Not tailored, kept as USAFacts wrote it: the three tracks, their names, the three levels, the three prerequisites, the SLSA shape, the intended use.

## 4. Placement of the sixteen checks

Read from the record (`framework/ai_readiness_framework.json`, `spec:*` nodes) and the deck's level captions. The re-parenting task writes these as the new `DESCENDS_FROM` targets; the old targets (`aiready:*`) stay as lineage edges.

| USAFacts rung | Check (record id) |
|---|---|
| Prerequisite, discoverable | The data page is in the site's list of pages (A3); the page labels itself as a dataset (A6); the product is listed in the agency's data inventory (D1) |
| Prerequisite, clearly licensed | The terms of reuse, under a recognised name (D2) |
| Access I, machine-readable and crawlable | Data offered as a file a program can read (A1); the whole dataset in one download (A2); whether the site's visitor rules let AI tools in (A4); the site serves what its own rules permit (A12); what the site states about automated access (A11, recorded, not scored); the interactive data tool answers honestly (A10) |
| Access II, API, usage docs, change notes | A published description of the agency's data service (A5); a front door built for programs (A9); from a data page to the data service, terms, change log and inventory (A13); a change history a program can follow (F3) |
| Context I, documentation for people | The methods are readable as plain text (B1) |
| Context II, provenance and update cadence | The release date, and a link to the latest release (A8) |
| Access III, Context III, Evaluation I to III | none measured |

Record ids are the ones the roll-up used; the re-parenting task confirms each against `rf_name_brief` before writing. The "Release engineering (added)" bucket of the roll-up dissolves: its one measured check (F3) is Access II in USAFacts' own words ("lineage/change notes").

## 5. Out of scope, by the operator's direction of 2026-11-03

No new checks, no re-scans, no re-runs, no construct-validity review, no evaluation harness. The remaining indicators in the record stay there as backlog and are not shown to either audience. The API layer (hitting the services the A5 and A9 checks found) is the one measured extension worth considering later and is parked as such.

## 6. The two documents

Both built by code from the record (DN-019's ladder), both PDF, both in `reports/`, never gitignored.

1. **ICSP page.** One page. What USAFacts built and why it is worth adopting (a heavy consumer's view of federal data, a ladder an agency can climb at its own pace). Where the sixteen agencies stand on it today, as a picture, not a table. What an agency gets from the diagnostic: its rung on each track and the one thing that lifts it to the next. The Evaluation track shown empty, with one sentence on why. No check names, no record ids, no numbers beyond counts of agencies.
2. **Working-group explainer.** Four to six pages for a mixed audience, lay reader first. What a check is (one worked example, end to end: the question, the sensor, the reading, the state). The lineage picture. The placement table of section 4 in plain labels. For each rung, what passing looks like and what the next rung asks for. The tailoring record as a short "what we kept, what we changed" box. The technical material (measurement sheet, DN-019) referenced as attachments, not repeated.

Both carry the FCSM 26-01 "SI use" statement at the end.

## 7. Image prompts

Generated outside the repository with an image model (the operator's choice, currently Google's Nano Banana 2). Style for all four: flat vector illustration, friendly and plain, white background, two colours plus grey, no gradients, no numbers or data in the picture, captions carry the facts. Nothing in the picture names an agency.

1. **The ladder.** "Three side-by-side ladders standing on one shared base platform. Each ladder has three rungs. The platform carries three small signposts. A small friendly robot with a notebook stands at the foot of the ladders looking up. Flat vector, white background, orange and slate blue, no text." Caption in the document: tracks, levels, prerequisites.
2. **The lineage.** "Three stepping stones in a row leading to a fourth larger stone, each stone a little bigger than the last, a simple arrow of footprints across them. On the fourth stone a small gauge or dial has been fixed. Flat vector, white background, orange and slate blue, no text." Caption: FAIR 2016, USAFacts 2025, USAFacts 2026, the sensor.
3. **Where the agencies stand.** "A single three-rung ladder in profile with a crowd of small identical paper-cutout figures: most clustered on the ground and first rung, a few on the second rung, none on the third. The top rung is drawn in dotted outline. Flat vector, white background, orange and slate blue, no text." Caption: the count per rung, from the roll-up. One picture per track, or one combined picture; the build task decides on the page.
4. **One check, end to end.** "A four-panel comic strip, no words: panel one, a small robot asks a question with a speech bubble containing only a question mark; panel two, the robot points a hand-held meter at a doorway; panel three, the meter's needle sits in a coloured band; panel four, the robot writes a single tick in its notebook. Flat vector, white background, orange and slate blue." Caption: question, sensor, reading, state.

## 8. What follows

One task, after this note is committed: re-parent the sixteen `spec:*` nodes per section 4, rebuild the roll-up and one-pager with the USAFacts rungs as the bucket column, and build the two documents of section 6 with placeholders where the four pictures go. The operator drops the generated pictures into `reports/figures/dn020/` and a rebuild places them.

## 9. Citations

- USAFacts (2026). AI-Ready Government Data: A Framework for Trust in the Age of AI. Roundtable deck, 2026-08-26. Corpus `usafacts-ai-ready-framework-deck-2026-08`.
- USAFacts (2026). Overview of USAFacts Project on AI-Ready Government Data. Corpus `usafacts-ai-ready-framework-overview-2026`.
- USAFacts (2025). The USAFacts Guide to AI-Ready Data for Government Agencies. Corpus `usafacts-ai-ready-data-guide`.
- Wilkinson, M. D. et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data 3, 160018. Corpus `wilkinson-2016-fair-guiding-principles`.
- Jacobsen, A. et al. (2020). FAIR Principles: Interpretations and Implementation Considerations. Data Intelligence 2(1-2). Corpus `jacobsen-2020-fair-principles-interpretations`.
- SLSA (2023). Supply-chain Levels for Software Artifacts, specification v1.0. Corpus `slsa-specification-v1-0`.
- ISO/IEC/IEEE 15288:2023. Systems and software engineering: system life cycle processes. Annex A, tailoring process. Not in corpus; cited for the term.
- ISO/IEC/IEEE 15939:2017. Measurement process. Corpus `iso-iec-ieee-15939-2017` (entry present; local copy pending re-fetch).
- Box, G. E. P. (1976). Science and statistics. Journal of the American Statistical Association 71(356), 791 to 799. Source of "all models are wrong, some are useful" (the 1979 wording). Not in corpus.
- NIST AI 100-1 (2023). AI Risk Management Framework, MEASURE function. Corpus `nist-ai-rmf-1-0` or the project's RMF entry, as the record names it.
