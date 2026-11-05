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

## Prior art

Searched 2026-11-04 through `seldon_prior_art_search`, two queries, both arms. Internal: no hits in any of the seven repositories for either query; the three-track framework entered the corpus on 2026-11-03 and no note has used it before. Library: 41 and 32 rows, nearly all LLM agent benchmark papers matching "levels" or "tracks" by accident. Two rows are prior art for a readiness ladder and are taken: the FAIR toolkit's findability maturity indicators (Pistoia Alliance; a per-principle maturity scale over FAIR, the closest published analogue to placing checks on levels) and NASA's technology readiness levels (Banke 2010; the original cumulative-level readiness scale that SLSA and every maturity model since echo). Both strengthen section 2's lineage and section 3's T3; neither changes a decision here. The EU DSA data-access level row (arXiv 2601.18127) is a different sense of "level" and is set aside.

### Internal

- internal receipt: query "maturity levels tailoring framework SLSA" | repo seldon@40d03aa81fe252967bf64e2b1947e4b1d46c2666 | hits none
- internal receipt: query "maturity levels tailoring framework SLSA" | repo squiddy@50789897c7df09fbd41ac9fd5c24875fd8e15f2b | hits none
- internal receipt: query "maturity levels tailoring framework SLSA" | repo ai-readiness-kg@ab30f13425855873da68c7fd409907d1ec60ffd3 | hits none
- internal receipt: query "maturity levels tailoring framework SLSA" | repo arnold@6114fe89226c455af64e3142bd6bee841769aeeb | hits none
- internal receipt: query "maturity levels tailoring framework SLSA" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits none
- internal receipt: query "maturity levels tailoring framework SLSA" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits none
- internal receipt: query "maturity levels tailoring framework SLSA" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo seldon@40d03aa81fe252967bf64e2b1947e4b1d46c2666 | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo squiddy@50789897c7df09fbd41ac9fd5c24875fd8e15f2b | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo ai-readiness-kg@a21465eca71858837ca75c4747df852a9fc55944 | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo arnold@6114fe89226c455af64e3142bd6bee841769aeeb | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits none
- internal receipt: query "USAFacts tracks levels prerequisites" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none

### External

- library receipt: query "maturity levels tailoring framework SLSA" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-02-22_arXiv_2505_20286#p8:151:1759-2147, lesson:2026-02-22_arXiv_2505_20286#p7:138:1259-1986, lesson:2026-04-13_arXiv_2410_12405#p2:12:0-1103, lesson:2026-04-13_arXiv_2410_12405#p1:8:386-1668, lesson:2026-04-13_arXiv_2410_12405#meta, lesson:2026-06-16_arXiv_2605_31468#p17:232:305-323, lesson:2026-06-16_arXiv_2605_31468#p18:271:2255-2706, lesson:2026-02-22_arXiv_2504_09037#p75:791:0-726, lesson:2026-02-22_arXiv_2504_09037#p12:154:1569-2120, lesson:2026-04-05_arXiv_2603_28589#p6:33:48-287, lesson:2026-04-05_arXiv_2603_28589#p6:35:292-532, lesson:2026-04-05_arXiv_2603_03823#p1:5:345-1515, lesson:2026-04-05_arXiv_2603_03823#p9:143:1031-1644, lesson:2026-04-05_arXiv_2603_03823#p11:169:1237-1660, lesson:2026-02-22_arXiv_2502_18449#p5:85:529-2386, lesson:2026-02-22_arXiv_2502_18449#p3:25:184-877, lesson:2026-02-22_arXiv_2502_18449#p6:94:1981-3132, lesson:2026-03-17_arXiv_2602_08004#p14:320:360-497, lesson:2026-02-22_arXiv_2405_09783#p3:37:1384-1776, lesson:2026-08-25_arXiv_2606_08317#p12:230:2324-2435, lesson:2026-08-25_arXiv_2606_08317#p13:271:2512-2521, lesson:2026-08-25_arXiv_2606_08317#p3:37:4506-4530, lesson:2026-02-22_arXiv_2410_02958#p7:201:1385-2007, lesson:2026-02-22_arXiv_2410_02958#p21:582:1356-1934, lesson:2026-02-22_arXiv_2410_02958#p4:76:1844-1867, lesson:2026-02-22_arXiv_2410_10762#p2:34:4220-4314, lesson:2026-02-22_arXiv_2504_13958#p11:363:1995-2156, lesson:2026-02-22_arXiv_2410_07553#p4:54:2295-2796, lesson:2026-02-22_arXiv_2308_03688#p34:602:821-1023, lesson:2026-02-22_arXiv_2308_03688#p20:346:46-57, lesson:2026-02-22_arXiv_2308_03688#p17:323:83-97, lesson:2026-02-22_arXiv_2507_21046#p69:950:2202-2782, lesson:2026-02-22_arXiv_2507_21046#p53:737:3937-4290, lesson:2026-02-22_arXiv_2507_21046#p21:284:1733-4195, lesson:2026-02-22_arXiv_2503_21760#p7:99:3315-3524, lesson:2026-02-22_arXiv_2311_13743#p21:328:304-481, lesson:2026-02-22_arXiv_2311_13743#p7:115:5188-5417, lesson:2026-02-22_arXiv_2507_06261#p27:412:3198-3556, lesson:2026-02-22_arXiv_2507_06261#p35:468:2894-3247, lesson:2026-02-22_arXiv_2507_06261#p28:424:1240-1655, lesson:2026-08-25_10_1038_s42003_026_10694_y#p7:125:3612-4171
- library receipt: query "USAFacts tracks levels prerequisites" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-02-22_arXiv_2306_06624#p9:163:224-294, lesson:2026-02-22_arXiv_2504_13805#p21:357:835-1105, lesson:2026-02-22_arXiv_2503_11664#p20:560:3393-3454, lesson:2026-08-25_arXiv_2606_28856#p4:140:1991-2188, lesson:2026-08-25_arXiv_2606_28856#p12:313:2623-2993, lesson:2026-08-25_arXiv_2606_28856#p4:111:21-137, lesson:2026-03-15_10_3389_frai_2020_00025#p16:311:244-365, lesson:2026-06-16_arXiv_2606_15474#p21:423:2484-2521, lesson:2026-02-22_arXiv_2408_07199#p10:175:2511-2570, lesson:2026-03-17_arXiv_2602_03587#p49:1024:2289-2505, lesson:2026-02-22_arXiv_2502_05453#p15:247:151-279, lesson:2026-02-22_arXiv_2502_05453#p103:1604:944-968, lesson:2026-02-22_arXiv_2502_05453#p103:1608:1453-1477, lesson:2026-02-22_arXiv_2509_01813#p13:271:2478-2841, lesson:2026-02-22_arXiv_2410_10934#p24:350:2543-2565, lesson:2026-02-22_arXiv_2410_10934#p24:356:2874-2894, lesson:2026-02-22_arXiv_2410_10934#p9:160:695-934, lesson:2026-06-23_arXiv_1705_02245#p9:102:807-875, lesson:2026-06-23_arXiv_1705_02245#p9:101:378-805, lesson:2026-02-22_arXiv_2505_09970#p10:261:3425-3886, lesson:2026-02-22_arXiv_2505_09970#p6:149:1584-2109, lesson:2026-02-22_arXiv_2505_09970#p6:161:2368-2569, lesson:2026-02-22_arXiv_2501_09136#p27:324:2346-2446, lesson:2026-02-22_arXiv_2601_03192#p30:715:870-1179, lesson:2026-02-22_arXiv_2506_15651#p17:262:1983-2104, lesson:2026-02-22_arXiv_2506_15651#p9:135:456-580, lesson:2026-02-22_arXiv_2407_03913#p9:153:577-1074, lesson:2026-02-22_arXiv_2410_16946#p22:385:1771-2366, lesson:2026-03-23_arXiv_2601_18127#p5:52:2470-3079, lesson:2026-03-23_arXiv_2601_18127#p5:53:3081-4066, lesson:2026-03-23_arXiv_2601_18127#p6:62:3549-3846, lesson:2026-02-22_arXiv_2504_16129#p15:430:1950-2167

## 9. Citations

- USAFacts (2026). AI-Ready Government Data: A Framework for Trust in the Age of AI. Roundtable deck, 2026-08-26. Corpus `usafacts-ai-ready-framework-deck-2026-08`.
- USAFacts (2026). Overview of USAFacts Project on AI-Ready Government Data. Corpus `usafacts-ai-ready-framework-overview-2026`.
- USAFacts (2025). The USAFacts Guide to AI-Ready Data for Government Agencies. Corpus `usafacts-ai-ready-data-guide`.
- Wilkinson, M. D. et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data 3, 160018. Corpus `wilkinson-2016-fair-guiding-principles`.
- Jacobsen, A. et al. (2020). FAIR Principles: Interpretations and Implementation Considerations. Data Intelligence 2(1-2). Corpus `jacobsen-2020-fair-principles-interpretations`.
- SLSA (2023). Supply-chain Levels for Software Artifacts, specification v1.0. Corpus `slsa-specification-v1-0`.
- ISO/IEC/IEEE 15288:2023. Systems and software engineering: system life cycle processes. Annex A, tailoring process. Not in corpus; cited for the term.
- ISO/IEC/IEEE 15939:2017. Measurement process. Corpus `iso-iec-ieee-15939-2017` (entry present; local copy pending re-fetch).
- Pistoia Alliance. FAIR toolkit, findability maturity indicators. Library row lesson:2026-08-25_10_1038_s42003_026_10694_y.
- Banke, J. (2010). Technology readiness levels demystified. NASA. Library row lesson:2026-06-23_arXiv_1705_02245.
- Box, G. E. P. (1976). Science and statistics. Journal of the American Statistical Association 71(356), 791 to 799. Source of "all models are wrong, some are useful" (the 1979 wording). Not in corpus.
- NIST AI 100-1 (2023). AI Risk Management Framework, MEASURE function. Corpus `nist-ai-rmf-1-0` or the project's RMF entry, as the record names it.
