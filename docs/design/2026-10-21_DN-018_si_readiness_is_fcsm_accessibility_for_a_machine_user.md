# DN-018: SI readiness is the Accessibility dimension of FCSM 20-04, measured for a machine user

**Date:** 2026-10-21
**Status:** Ruling. Governs how the readiness diagnostic is defined in every rendered material (executive summary, brief, dictionary, scan definitions) and what the framework record cites as the definition's source.
**Depends on:** DN-005 (the framework is the goal), DN-014 (decision support system, three tiers of check), DN-015 (the sixteen checks and the four states), DN-016 (the public client, the two kinds of user).
**Question it answers:** which published quality framework the readiness diagnostic is an instrument of, so that its definition of SI readiness is cited rather than invented (operator rule 2026-10-11: definitions are never made up in conversation).

## 1. Ruling

The readiness diagnostic measures the **Accessibility** dimension of the Federal Committee on Statistical Methodology's *A Framework for Data Quality* (FCSM 20-04, Utility domain), with the data user instantiated as a program acting for a member of the public. Nothing in the sixteen checks is a new quality construct. Each check is an operationalization of one of the activities FCSM 20-04 already names under Accessibility, read for a machine user instead of a person at a browser.

Consequences:

1. Rendered materials define SI readiness by citing FCSM 20-04 and its restatements (FCSM 23-02, FCSM 25-03), not by a project definition. The one-line form: *an agency's data product is SI ready to the extent that a program acting as an ordinary data user can obtain the product and its documentation in forms and formats it can use* (FCSM 20-04 Accessibility, machine user substituted).
2. The framework record carries one edge per MeasurementSpec to the FCSM 20-04 Accessibility concern it serves (section 4), so the mapping is graph data and the dictionary, brief and summary render it rather than restate it.
3. The NIST AI RMF is not the home of this work. The operator's own crosswalk (section 3) records that Accessibility has no equivalent subcategory in the RMF. A reader who reaches for AI governance vocabulary to place the diagnostic is reaching for a framework that does not cover it.

## 2. The definition, verbatim

FCSM 20-04, Utility domain, Accessibility (fss-policy-kg segment `fcsm_20_04#s389`):

> Accessibility relates to the ease with which data users can obtain an agency's products and documentation in forms and formats that are understandable to data users. Two main classes of activity support the accessibility of a data product: making the data product available to a broad range of users in easy-to-use formats and providing metadata and other documentation to facilitate the use and interpretation of the data (Statistical Community of Practice 2020). Documentation also provides users with information about the quality of the data.

FCSM 23-02 restates the first sentence unchanged (`fcsm_23_02#s617`). FCSM 25-03, the AI-ready extension, keeps the dimension and asks that each data element be assessed across the three domains and their dimensions, naming accessibility, timeliness and accuracy (fss-policy-kg obligation `895704a10c144df49f6df84cec1a284b`, force: recommendation).

The lineage matters for the working group: the dimension the diagnostic measures was published by the FCSM in 2020, restated in 2023, and carried into the FCSM's own AI-ready guidance in 2025. The diagnostic adds the measurement, not the construct.

### 2.1 A sense of "accessibility" this note excludes

OMB M-24-10 defines "accessibility" by reference to Executive Order 14035 section 2(e) (fss-policy-kg definition `m_24_10#s504`), the disability-access sense that Section 508 governs (M-23-22 obligations on 508 compliance and accessibility testing). That is a different construct with its own standards and conformance testing. Rendered materials say "accessibility in the FCSM data-quality sense" the first time the word appears, and never let the two senses share a sentence. The parallel is useful once, as an analogy: Section 508 testing checks whether a person using assistive technology can use the page; this diagnostic checks whether a program can use the data. Both test from the user's side with published criteria; neither needs the agency's cooperation to run.

## 3. The crosswalk: Accessibility has no NIST AI RMF equivalent

Webb (2026), *When AI Enters Federal Statistics: A Crosswalk Between Data Quality and AI Trustworthiness Frameworks*, v2, DOI 10.5281/zenodo.18772590, CC BY 4.0. Working copy: `/Users/brock/Documents/GitHub/central_library/crosswalks/fcsm_nist/FCSM_NIST_AI_RMF_Crosswalk.md`. The crosswalk is also admitted to fss-policy-kg as document `webb_nist_fcsm_crosswalk`.

Mapping A decomposes FCSM Accessibility into four concerns and finds no corresponding RMF subcategory for any of them (GOVERN 4.2 and MEASURE 2.9 considered and rejected: the RMF documents AI systems, it does not evaluate user access to data products):

| # | FCSM 20-04 Accessibility concern (crosswalk, Mapping A) | RMF equivalent |
|---|---|---|
| C1 | Users can locate and obtain the data product | none |
| C2 | Documentation is sufficient for users to understand the data product | none |
| C3 | Data products are available in formats suitable for diverse users | none |
| C4 | Metadata and supporting materials are provided | none |

Mapping B notes one partial correspondence in the other direction: MEASURE 3.3 (end-user feedback and appeal) relates to, but is not equivalent to, Accessibility.

What this settles: the readiness diagnostic sits in the gap the crosswalk already identified. It is data-quality measurement in the FCSM sense; the RMF's trustworthiness characteristics (valid and reliable, safe, secure, accountable, explainable, privacy-enhanced, fair) describe the AI system that consumes the data, not whether the data can be consumed. An agency that answers "we are covered by our AI governance" has answered a different question.

## 4. The sixteen checks mapped to the four concerns

Primary concern per check; a second concern is listed where the check serves two. Check names are the graph's `rf_name_brief` values (MeasurementSpec nodes, task b6c65bfe).

| Check | Name | Primary | Also |
|---|---|---|---|
| A1 | Data offered as a file a program can read | C3 | C1 |
| A2 | A published description of the agency's data service | C2 | C4 |
| A3 | The whole dataset in one download | C3 | C1 |
| A4 | Whether the site's visitor rules let AI tools in | C1 | |
| A5 | The data page is in the site's list of pages | C1 | |
| A6 | The page labels itself as a dataset | C4 | C1 |
| A8 | The release date, and a link to the latest release | C4 | |
| A9 | A front door built for programs | C1 | C3 |
| A10 | The interactive data tool answers honestly | C3 | |
| A11 | What the site states about automated access | C1 | |
| A12 | The site serves what its own rules permit | C1 | |
| A13 | From a data page to the data service, terms, change log and inventory | C1 | C4 |
| B3 | The methods are readable as plain text | C2 | |
| D1 | The terms of reuse, under a recognised name | C4 | |
| D4 | The product is listed in the agency's data inventory | C1 | C4 |
| F4 | A change history a program can follow | C4 | |

Reading the table honestly: eleven of sixteen checks serve C1 or C3 (obtain, in a usable format), which is FCSM 20-04's first activity class. C4 is served by metadata presence checks. C2, whether documentation is sufficient to understand the product, has two checks (A2, B3) and both test presence and readability, not sufficiency. The diagnostic therefore measures the first activity class well, the metadata half of the second, and the understanding half of the second barely. That is the same gap DN-017 names as the Understandable criterion having no automated check. The mapping makes the gap visible against a published framework instead of against the project's own criteria list.

## 5. The machine user is a data user

FCSM 20-04 says "data users" and "a broad range of users" without restricting them to people. The substitution of a program for the person is the FAIR principles' move (Wilkinson et al. 2016: findable, accessible, interoperable, reusable for machines as well as humans), and the operator's "machine as first-class user" phrasing is his manifestation of FAIR, not a new principle. USAFacts' AI-ready data framework built on FAIR; this project extends USAFacts (the USAFacts note, task e2c4e125). The chain of credit in rendered materials is therefore FCSM 20-04 for the dimension, FAIR for the machine-user reading, USAFacts for the operationalization skeleton, this project for the measurement.

The two kinds of user in DN-016 (standard user, no key; API user, free registered key) are both data users in the FCSM sense. The ladder does not change which dimension is measured; it changes which forms and formats the user can reach.

## 6. What this note does not claim

- It does not claim the diagnostic measures Relevance, Timeliness, Granularity, or any Objectivity or Integrity dimension. A8 (release date) touches Timeliness only as a metadata-presence check; it does not measure currency against user need.
- It does not claim C2 (documentation sufficient to understand) is measured. See section 4.
- It does not adopt the crosswalk's "critical gap" (AI confabulation in statistical consultation) as part of this diagnostic. That gap belongs to the AI system consuming the data, which is out of this instrument's scope by DN-014.

## 7. Coordination

The operator reported a colleague drafting a paper on the same FCSM-to-RMF mapping. That is a coordination item for the operator (whether the two papers cite each other), not a citation this note can carry: nothing of it is on disk or in any graph. Recorded so the next session does not treat the absence as a miss.

## 8. Tasks this note governs

1. Framework record write-back: one `serves_fcsm_concern` edge per MeasurementSpec per the section 4 table, plus four `FcsmConcern` nodes citing the crosswalk, through `scripts/framework_writeback.py` and followed by a projection (DD-057). The dictionary, brief and summary builders read the edge.
2. Executive summary v4 (98ed1dd1, blocked) and every later rendered material: page-one definition of SI readiness is section 1 consequence 1, with FCSM 20-04 cited; the Section 508 disambiguation from section 2.1 appears once.
3. The 16-checks one-pager as a build product (its own task) gains a sixth column or footnote: the FCSM concern each check serves.

## Prior art

Searched 2026-10-21 through `seldon_prior_art_search` (receipts below) and `fss-policy-kg` lexical search. The operator's crosswalk was not found by the internal arm, which indexes seven repositories and not `central_library`; the operator supplied its path and DOI. The library arm's hits for all three queries are retrieval-agent, GUI-agent and LLM data-quality papers; the one on-topic external row is arXiv 2003.02320 (accessibility defined as the ease with which external agents can access a dataset once located), recorded here as corroboration of the machine-user reading and not relied on for the definition, which comes from FCSM 20-04 directly.

Sources for the definition: fss-policy-kg segments `fcsm_20_04#s389`, `fcsm_20_04#s334`, `fcsm_23_02#s617`; obligation `895704a10c144df49f6df84cec1a284b` (fcsm_25_03); definition `m_24_10#s504`; obligation `59a7f36ddc5e44169567e42d94fa293a` (wp_31, the four-concept decomposition accuracy, relevance, timeliness, accessibility); document `webb_nist_fcsm_crosswalk`.

### Internal

- internal receipt: query "FCSM data quality framework accessibility" | repo seldon@3fb05327f35914a6a8bc8c1c2f32d79c07594303 | hits none
- internal receipt: query "FCSM data quality framework accessibility" | repo squiddy@83e3751f5b313ca41b9fcfa76a0ff0c27d7885e6 | hits none
- internal receipt: query "FCSM data quality framework accessibility" | repo ai-readiness-kg@a83200db421374291ae6bb1daeee51ac0647925e | hits docs/design/2026-10-21_DN-017_commercial_tool_trial_protocol.md:58, docs/research/2026-10-04_node_key_fusion_audit.md:278, handoffs/2026-10-21_diagnostic_landed_tool_trial_protocol.md:77
- internal receipt: query "FCSM data quality framework accessibility" | repo arnold@f089fc8c79403a5371c823c6c3f2aec30fa90e57 | hits none
- internal receipt: query "FCSM data quality framework accessibility" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits docs/anchor_candidates_2026-06-08.md:58
- internal receipt: query "FCSM data quality framework accessibility" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits none
- internal receipt: query "FCSM data quality framework accessibility" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none
- internal receipt: query "RMF FCSM crosswalk" | repo seldon@3fb05327f35914a6a8bc8c1c2f32d79c07594303 | hits none
- internal receipt: query "RMF FCSM crosswalk" | repo squiddy@83e3751f5b313ca41b9fcfa76a0ff0c27d7885e6 | hits none
- internal receipt: query "RMF FCSM crosswalk" | repo ai-readiness-kg@c12e797e252d0ea7b94c686b495549a8e6637ab9 | hits handoffs/2026-10-21_diagnostic_landed_tool_trial_protocol.md:77, docs/research/2026-08-22_tevv_platform_operator_decisions.md:6, docs/research/2026-08-24_triage_backfill_report.md:7
- internal receipt: query "RMF FCSM crosswalk" | repo arnold@f089fc8c79403a5371c823c6c3f2aec30fa90e57 | hits none
- internal receipt: query "RMF FCSM crosswalk" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits docs/document_inventory.md:50, handoffs/2026-06-16_handoff_e3_design_pivot.md:13, handoffs/2026-06-16_handoff_e3_fix_source_pivot.md:22, docs/2026-06-08_corpus_breadth_override.md:19, docs/2026-06-08_corpus_acquisition_report.md:43, handoffs/2026-06-16_handoff.md:12, handoffs/2026-06-15_handoff.md:14, docs/project_plan.md:47, docs/2026-06-07_fcsm_trustworthy_ai_kg_design.md:372
- internal receipt: query "RMF FCSM crosswalk" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits docs/tevv/answers/B1.md:17, docs/tevv/context/B1.txt:3
- internal receipt: query "RMF FCSM crosswalk" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none

### External

- library receipt: query "FCSM data quality framework accessibility" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-03-07_10_3233_sji_230125#meta, lesson:2026-08-25_arXiv_2512_03541#p11:110:25-455, lesson:2026-08-25_arXiv_2512_03541#p35:447:563-730, hiniduma2025aidrin2#p1:19:1282-2767, hiniduma2025aidrin2#p1:22:3281-4284, hiniduma2025aidrin2#meta, lesson:2026-07-15_arXiv_2003_02320#p65:930:2333-2658, lesson:2026-07-15_arXiv_2003_02320#p87:1168:606-923, lesson:2026-07-15_arXiv_2003_02320#p84:1126:4028-4205, lesson:2026-06-16_arXiv_2505_00039#p20:171:2216-2800, lesson:2026-06-16_arXiv_2505_00039#p19:154:723-1715, lesson:2026-02-22_arXiv_2601_03515#p4:121:824-940, lesson:2026-02-22_arXiv_2601_03515#p4:125:969-1004, lesson:2026-02-22_arXiv_2601_03515#p4:92:15-162, lesson:2026-02-22_arXiv_2501_12599#p21:516:1602-1837, lesson:2026-02-22_arXiv_2501_12599#p21:515:1001-1600, lesson:2026-02-22_arXiv_2501_12599#p22:526:255-378, lesson:2026-05-23_arXiv_2405_16884#p12:224:1659-1832, lesson:2026-05-23_arXiv_2405_16884#p5:82:2535-4182, lesson:2026-05-23_arXiv_2405_16884#p6:89:2795-4097, lesson:2026-02-22_arXiv_2405_12819#p18:310:1181-1546, lesson:2026-02-22_arXiv_2406_12373#p27:423:435-794, lesson:2026-02-22_arXiv_2406_12373#p27:422:358-433, lesson:2026-02-22_arXiv_2406_12373#p29:467:574-649, lesson:2026-02-22_arXiv_2503_14434#p11:295:3380-5097, lesson:2026-02-22_arXiv_2503_14434#p22:531:3795-4398, lesson:2026-02-22_arXiv_2503_14434#p21:491:4012-4593, lesson:2026-06-23_arXiv_1705_02245#p3:28:690-806, lesson:2026-06-23_arXiv_1705_02245#p1:10:1363-1733, lesson:2026-06-23_arXiv_1705_02245#p2:16:823-1384, lesson:2026-02-04_arXiv_2503_16233#p22:517:3333-4183, lesson:2026-02-04_arXiv_2503_16233#p10:230:615-1254, lesson:2026-02-04_arXiv_2503_16233#p8:218:1836-4131, lesson:2026-02-22_arXiv_2503_13514#p1:10:3943-4128, lesson:2026-02-22_arXiv_2503_13514#p3:41:5594-5996, lesson:2026-02-22_arXiv_2503_13514#p11:172:209-668, lesson:2026-02-22_arXiv_2505_15155#p8:221:2035-3311, lesson:2026-02-22_arXiv_2504_21024#p17:398:1368-1450, lesson:2026-02-22_arXiv_2504_21024#p14:341:605-1208, lesson:2026-02-22_arXiv_2504_21024#p14:340:487-603, lesson:2026-03-27_arXiv_2407_10239#p10:117:2154-3377, lesson:2026-02-22_arXiv_2504_12679#p7:178:3181-3606, lesson:2026-02-22_arXiv_2504_12679#p19:441:348-739, lesson:2026-03-25_arXiv_2405_07560#p12:95:2620-2816, lesson:2026-04-12_arXiv_2312_10997#p15:183:14-171, lesson:2026-04-12_arXiv_2312_10997#p10:108:3707-4601, lesson:2026-04-12_arXiv_2312_10997#p14:172:1347-1500
- library receipt: query "accessibility machine user data quality dimension" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-02-22_arXiv_2404_07972#p23:400:2109-2491, lesson:2026-02-22_arXiv_2404_07972#p23:399:1546-2107, lesson:2026-02-22_arXiv_2404_07972#p4:50:150-168, lesson:2026-02-22_arXiv_2505_02484#p11:138:2341-2386, hiniduma2025aidrin2#p1:22:3281-4284, hiniduma2025aidrin2#p1:19:1282-2767, hiniduma2025aidrin2#p1:21:2788-3279, lesson:2026-03-17_arXiv_2602_12670#p17:368:1688-1794, lesson:2026-03-17_arXiv_2602_12670#p17:361:0-207, lesson:2026-02-22_arXiv_2410_10813#p17:300:518-841, lesson:2026-01-28_10_1007_s11135_017_0533_4#p16:147:3329-3597, lesson:2026-01-28_10_1007_s11135_017_0533_4#p5:35:0-261, lesson:2026-01-28_10_1007_s11135_017_0533_4#p19:180:0-307, lesson:2026-02-22_arXiv_2406_12373#p27:423:435-794, lesson:2026-02-22_arXiv_2406_12373#p17:308:910-1929, lesson:2026-02-22_arXiv_2406_12373#p27:422:358-433, lesson:2026-02-22_arXiv_2504_21024#p17:398:1368-1450, lesson:2026-02-22_arXiv_2504_21024#p15:361:1330-1663, lesson:2026-02-22_arXiv_2504_21024#p14:341:605-1208, lesson:2026-02-22_arXiv_2504_12679#p7:178:3181-3606, lesson:2026-02-22_arXiv_2504_12679#p7:172:2344-3036, lesson:2026-02-22_arXiv_2504_12679#p8:192:3276-3639, lesson:2026-02-22_arXiv_2410_02958#p29:729:687-1116, lesson:2026-02-22_arXiv_2410_02958#p26:661:730-1011, lesson:2026-02-22_arXiv_2410_02958#p29:719:71-454, lesson:2026-02-22_arXiv_2508_02621#p29:625:1524-1551, lesson:2026-02-22_arXiv_2508_02621#p37:797:908-1430, lesson:2026-02-22_arXiv_2508_02621#p43:906:103-384, lesson:2024-11-04_10_6028_nist_ai_600_1#p51:731:2791-2822, lesson:2026-07-15_arXiv_2003_02320#p65:930:2333-2658, lesson:2026-02-22_arXiv_2504_10458#p8:168:1027-1058, lesson:2026-06-23_arXiv_1705_02245#p1:10:1363-1733, lesson:2026-06-23_arXiv_1705_02245#p3:28:690-806, lesson:2026-06-23_arXiv_1705_02245#p1:11:1735-2293, lesson:2026-03-17_arXiv_2603_04448#p7:133:1093-2219, lesson:2026-03-17_arXiv_2603_04448#p6:128:3862-4144, lesson:2026-03-17_arXiv_2603_04448#p7:134:2221-2864, lesson:2026-02-22_10_18653_v1_2024_findings_acl_259#p32:689:16-403, lesson:2026-02-22_10_18653_v1_2024_findings_acl_259#p30:644:16-409, lesson:2026-02-22_10_18653_v1_2024_findings_acl_259#p5:180:4120-4465, lesson:2026-03-29_arXiv_2411_15594#p29:432:2182-2367, lesson:2026-03-29_arXiv_2411_15594#p8:101:346-586, lesson:2026-03-29_arXiv_2411_15594#p49:652:2759-3656, lesson:2026-03-25_arXiv_1802_03426#p1:11:964-1155, lesson:2026-03-25_arXiv_1802_03426#p1:10:312-962, lesson:2026-03-25_arXiv_1802_03426#p39:394:1137-1957, lesson:2026-02-22_arXiv_2409_20163#p7:244:2741-3229, lesson:2026-02-22_arXiv_2409_20163#p8:262:897-2047, lesson:2026-02-22_arXiv_2409_20163#p7:235:876-1706

## References

Federal Committee on Statistical Methodology (2020). *A Framework for Data Quality* (FCSM 20-04).
Federal Committee on Statistical Methodology (2023). FCSM 23-02 (restates the Accessibility definition).
Federal Committee on Statistical Methodology (2025). *AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality* (FCSM 25-03).
National Institute of Standards and Technology (2023). *AI Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1.
Office of Management and Budget (2024). M-24-10, definition of accessibility by reference to EO 14035 §2(e).
Webb, B. (2026). *When AI Enters Federal Statistics: A Crosswalk Between Data Quality and AI Trustworthiness Frameworks*, v2. Zenodo. https://doi.org/10.5281/zenodo.18772590
Wilkinson, M. D. et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data* 3, 160018.
