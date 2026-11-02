# DN-019: every check renders as a measurement specification, and the diagnostic is explained through a fixed ladder of views

**Date:** 2026-11-02
**Status:** Ruling. Governs how the readiness diagnostic is rendered for every audience, and which fields of a check every rendered measurement carries.
**Depends on:** DN-014 (three tiers of check), DN-015 (the four states), DN-016 (vocabulary), DN-018 (FCSM concern per check), the operator's measurement standard of 2026-10-15 (every check is a hypothesis documented like an instrument specification before a finding rests on it).
**Question it answers:** the operator's reading of the rendered artifacts on 2026-11-02: nothing shows what instrument takes each measurement, what it measures, and how the reading is interpreted; and the levels of detail are not decomposed into views a reader can move between.

## 1. Ruling

1. The unit of explanation below the check name is a **measurement specification** with a fixed set of fields (section 3). Every field is a property the MeasurementSpec node already carries; the view renders, it does not author. A check whose node lacks a field renders the field as "not specified", and that is a defect in the record, never filled by the builder.
2. The diagnostic is rendered through a **ladder of four views** (section 4), each generated from the graph, each one level of decomposition deeper than the last, and each citing the one above it. No rendered material sits between rungs.
3. The field set follows the measurement information model of ISO/IEC/IEEE 15939 (section 2), so the questions "what sensor, what does it read, what range counts" have a named answer per check instead of a project vocabulary.

## 2. Prior art: the measurement information model

ISO/IEC/IEEE 15939 (Systems and software engineering: measurement process) defines a measurement information model that runs from an information need through a measurable concept, the entity and its attribute, a measurement method that yields a base measure, a measurement function that yields a derived measure, an analysis model that yields an indicator, and decision criteria that turn the indicator into an interpretation. It is the standard answer to the operator's three questions: the method and its instrument are the sensor; the base measure is what the sensor reads; the decision criteria are the range that counts. Goal Question Metric (Basili, Caldiera and Rombach 1994) is the older and simpler form of the same chain and is the one most readers have met. Both are cited here from the operator's and the author's knowledge, not fetched; verification before any paper is the operator's existing machinery (ways-of-working, citation risk rule). Neither is in the project library (prior-art receipts below); the library's hits for the query are model-benchmark tables, not measurement theory.

The operator's 2026-10-15 standard is the same chain in four parts: a valid question (information need), expected behaviour from literature or a standard (decision criteria's source), the test and why it is the recognised way (method and instrument), the result and what it does and does not claim (indicator and its limits).

## 3. The measurement specification fields

One row per check. Field, its 15939 name, and the MeasurementSpec property that supplies it.

| Field, as rendered | 15939 element | Record property |
|---|---|---|
| Question | information need | `rf_hypothesis` (first sentence) |
| What is examined | entity and attribute | `rf_where_we_look` |
| Instrument | measurement method, tool | `collector`, `collector_pin`, `mode` (auto, doc, eval) |
| What the instrument reads | base measure | `signal` |
| Evidence kept | measurement record | `evidence_kind` |
| Passes when | decision criteria | `rf_pass` |
| Partial when | decision criteria | `rf_partial` |
| Fails when, and what a fail does not claim | decision criteria, limits of the indicator | `rf_fail` |
| Not measured when | validity condition | `rf_not_measured` |
| Expected behaviour comes from | source of the criteria | `rf_standards_urls`, `rf_requirements` (source and verbatim quote) |
| Who else measures this | corroboration | `rf_who_else` |
| Client | measurement context | standard user or API user, from `rf_rung_two_changes` |

The four states are the decision criteria; a check whose pass line rests on a published source is Scored, exactly as the one-pager marks it. Qualitative checks (`mode` doc or eval) use the same fields; their instrument is a documented attribute a person confirms or an evaluation harness, and the row says so rather than pretending to a sensor.

## 4. The view ladder

Each view is a build product generated from the graph, carries its own rung number, and names the rung above it in one line. The ladder is the project's answer to the DoDAF habit of fixed views at fixed levels of detail, without adopting DoDAF's product set.

| Rung | View | Reader | Contents | Source of record | Status |
|---|---|---|---|---|---|
| V0 | The picture | anyone | one diagram: the public client, an agency's data pages, the four concerns, the readiness picture back to the agency | DN-014, DN-016 | to draw; the operator intends to use an image model for the friendly form, from a diagram this project generates |
| V1 | The criteria | ICSP member, agency head | the AI-ready criteria the checks descend from, what each asks for, the concern it serves, how many agencies pass the bucket | task 32e394f1 (roll-up) | task registered |
| V2 | The checks | working-group member, site owner | the sixteen checks: what is examined, passes when, why it matters, concern | task 9af5f624 (one-pager) | task resuming |
| V3 | The measurements | implementer, reviewer, the operator's own reasoning | the section 3 fields per check; one page per check or one long table | this note | task to register |
| Lineage figure | between V1 and V2 | ICSP member | the framework's own structure (its criteria and, if the record holds them, its levels) flowing to FAIR principles and on to the sixteen checks: a Sankey or chord diagram generated from `DESCENDS_FROM` and `SERVES_FCSM_CONCERN` edges | 32e394f1 Part A nodes | after the framework's levels are in the record; not before (section 5) |

Rule: a rendered material cites its rung ("V2 of the readiness diagnostic") so a reader knows which level they hold and that the others exist.

## 5. What this note does not settle

- The USAFacts framework's internal levels. The operator recalls the guide as having three levels with items to tick at each. The corpus copy (`state/docling_md/usafacts-ai-ready-data-guide.md`) is the source of record; whether it carries levels, and what they descend from, is read from it by the task that adds them to the record, not asserted here. The lineage figure waits on that.
- The use-case layer (user, data product, task) from the 2026-11-03 meeting; a later note.
- TEVV as a word on any page above V3. It stays an extension group name in the record and appears, spelled out, only at V3.

## 6. Tasks this note governs

1. V3 build product: `scripts/measurement_sheet_build.py` rendering the section 3 table per check from the record, md, docx and pdf, with the same font, colour, vocabulary, dash and digit checks as the one-pager; "not specified" cells counted and reported. After 32e394f1.
2. The framework's levels into the record (read from the corpus copy), then the lineage figure. After item 1.
3. Every later rendered material carries its rung.

## Prior art

Searched 2026-11-02 through `seldon_prior_art_search`, query "measurement information model base measure indicator ISO 15939", both arms. Internal: no hits in any of the seven repositories. Library: 43 rows, all benchmark result tables and LLM evaluation papers; none on measurement theory. ISO/IEC/IEEE 15939 and Basili, Caldiera and Rombach (1994) are cited unverified under the citation-risk rule and are to be fetched into the corpus by the V3 task so the record carries them.

### Internal

- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo seldon@b4eba780566639e5135fdf93aab40cf59f3b1ba6 | hits none
- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo squiddy@d5a0e5cf06e1f793634c057f8d0885dad406c359 | hits none
- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo ai-readiness-kg@4c47be99b3fb89ee7da7938189b784aec24e8fe2 | hits none
- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo arnold@6114fe89226c455af64e3142bd6bee841769aeeb | hits none
- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits none
- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits none
- internal receipt: query "measurement information model base measure indicator ISO 15939" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none

### External

- library receipt: query "measurement information model base measure indicator ISO 15939" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-02-22_arXiv_2503_09572#p9:154:3423-3449, lesson:2026-02-22_arXiv_2412_01928#p15:366:1531-1559, lesson:2026-02-22_arXiv_2412_01928#p8:198:1569-1597, lesson:2026-02-22_arXiv_2412_01928#p8:197:1520-1567, lesson:2026-02-22_arXiv_2405_20309#p8:170:103-139, lesson:2026-02-22_arXiv_2405_20309#p18:309:108-165, lesson:2026-05-09_arXiv_2601_18278#p7:57:0-58, lesson:2026-05-09_arXiv_2601_18278#p3:16:3056-4202, lesson:2026-05-09_arXiv_2601_18278#p9:113:0-64, lesson:2026-02-22_arXiv_2410_14157#p23:507:412-441, lesson:2026-02-22_arXiv_2410_14157#p23:506:379-410, lesson:2026-02-22_arXiv_2410_14157#p23:505:347-377, lesson:2026-02-22_arXiv_2310_00533#p18:410:898-920, lesson:2026-02-22_arXiv_2507_02616#p6:136:1598-2163, lesson:2026-05-09_arXiv_2505_08245#p5:34:376-464, lesson:2026-05-09_arXiv_2505_08245#p5:29:0-291, lesson:2026-05-09_arXiv_2505_08245#p8:69:977-988, lesson:2026-02-22_arXiv_2409_12917#p11:295:315-355, lesson:2026-02-22_arXiv_2409_12917#p12:313:338-381, lesson:2026-02-22_arXiv_2409_12917#p9:240:341-351, lesson:2026-02-22_arXiv_2505_15872#p6:116:991-1752, lesson:2026-02-22_arXiv_2505_15872#p7:136:2030-2144, lesson:2026-04-12_arXiv_2403_05530#p126:1763:363-368, lesson:2026-04-12_arXiv_2403_05530#p21:294:736-1370, lesson:2026-02-11_arXiv_2504_14765#p79:736:0-1450, lesson:2026-02-11_arXiv_2504_14765#p18:162:1058-2498, lesson:2026-02-11_arXiv_2504_14765#p81:760:0-1352, lesson:2026-03-17_arXiv_2601_21557#p8:165:1763-1792, lesson:2026-03-17_arXiv_2601_21557#p8:169:2053-2082, lesson:2026-03-17_arXiv_2601_21557#p8:159:309-345, lesson:2026-02-22_arXiv_2503_22732#p8:196:14-452, lesson:2026-08-25_10_1038_s42003_026_10694_y#p5:63:4101-4117, lesson:2026-03-15_arXiv_2105_06956#p6:150:5606-5639, lesson:2026-03-15_arXiv_2105_06956#p4:63:747-788, lesson:2026-03-15_arXiv_2105_06956#p6:144:1181-1807, lesson:2026-02-21_arXiv_2406_18532#p15:229:3098-3255, lesson:2026-02-22_arXiv_2504_00993#p7:123:1304-1390, lesson:2026-02-21_arXiv_2509_25911#p18:321:2290-2357, lesson:2026-02-21_arXiv_2509_25911#p18:294:1162-1481, lesson:2026-02-21_arXiv_2509_25911#p18:299:1513-1571, lesson:2026-02-22_arXiv_2508_06471#p3:55:222-339, lesson:2026-02-22_arXiv_2508_06471#p14:282:1720-2045, lesson:2026-02-22_arXiv_2508_06471#p14:281:1218-1718

## References

Basili, V. R., Caldiera, G., and Rombach, H. D. (1994). The Goal Question Metric approach. In *Encyclopedia of Software Engineering*. Wiley. [unverified]
ISO/IEC/IEEE 15939:2017. *Systems and software engineering: Measurement process*. [unverified]
Federal Committee on Statistical Methodology (2020). *A Framework for Data Quality* (FCSM 20-04).
USAFacts (2026). *AI-ready data guide* (corpus document usafacts-ai-ready-data-guide).
