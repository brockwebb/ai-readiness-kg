# DCAT-US 3.0 and federal statistics: was FCSM's input included?

Brock Webb, U.S. Census Bureau. 8 October 2026.

**Bottom line: partly.** The Federal Committee on Statistical Methodology (FCSM) publicly asked for seven of the eight statistical needs in the table below. In DCAT-US 3.0 none of the seven is Mandatory. One, restricted-access terms, is Recommended. Four are Optional fields that agencies may leave out, the link that marks a dataset as part of a series was dropped, and the published page does not settle where dimensions landed. [1][2][3][4][5][6][7][8][9]

## 1. What DCAT-US 3.0 is

DCAT-US 3.0 is the federal standard for the catalog card, or metadata, that describes each government data asset listed publicly on Data.gov. [10][11][12] It is the United States version of the World Wide Web Consortium's Data Catalog Vocabulary (DCAT). [9][14] The Office of Management and Budget (OMB) memorandum M-25-05 directs each agency to update its comprehensive data inventory listings to the DCAT-US 3.0 schema by September 30, 2026. [12][13]

## 2. Who made it

The General Services Administration says DCAT-US version 3.0 was built together by the Federal Chief Data Officers Council, the Federal Committee on Statistical Methodology (FCSM), and the Data.gov team. [10][11] Their joint effort is the FAIRness Project (FAIR: findable, accessible, interoperable and reusable). [15]

## 3. What FCSM asked for, and where it landed

| Statistical need | Asked for by FCSM? | Level in DCAT-US 3.0 (page of 5 October 2026) | Result |
|:----|:------|:--------|:----------|
| series | Yes [1] | Dropped (the series link) [2][3][4] | **Dropped** |
| dimensions (breakdowns such as place, item, time) | Yes [5] | Not confirmed | **Different form**; level not confirmed |
| units of measure | Not confirmed | No field for the data's unit; unitMeasure gives the unit of a quality score [16] | **No field**; FCSM ask not confirmed |
| uncertainty (margins of error) | Yes [5] | Optional [2][3] | **Optional only** |
| methodology and provenance | Yes [1][5] | Optional [2][3] | **Optional**, and **different form** |
| revisions and versions | Yes [5][6] | Optional [2][3] | **Optional**; form not checked |
| quality dimensions | Yes [6] | Optional [2][3] | **Optional**, and **different form** |
| restricted-access terms | Yes [1][5][7][8] | Recommended [2][3][9] | **Recommended**; form not checked |

What the results mean:

- **Optional only:** it has a field in 3.0, but agencies may leave it out.
- **Recommended:** agencies are expected to fill it; it is not required.
- **Dropped:** it was in the 2025 working draft and is not in the published 3.0.
- **No field:** 3.0 has no field for it.
- **Different form:** the international standards (StatDCAT-AP, the European statistical version of DCAT, and W3C vocabularies) carry it differently from how FCSM asked for it. Section 4 gives each case.
- **Not confirmed / not checked:** the source check could not confirm that part.

## 4. Where the standards carry it differently

The Federal Committee on Statistical Methodology (FCSM) report A Framework for Data Quality says documentation should include methods used in processing, imputations, weighting, editing, integration methods, and data dictionaries. [1][6] Data on the Web Best Practices (2017) intends that people learn a dataset's origin and history and that computer programs process this provenance automatically, and tests for that. [17] The Data Catalog Vocabulary (DCAT) Version 3 says quality dimensions are characteristics that matter to users, sets no required list, and leaves implementers to choose their own. [14][18] StatDCAT-AP, a statistical catalog profile, and the Data Cube vocabulary name each breakdown as its own field in the record, not in a written description of variables. [5][19][20]

Whether FCSM left out something the standards call for cannot be shown from the public record while the project's sequencing plan is unpublished.

## 5. A path forward

Europe built StatDCAT-AP, an add-on to its data catalog standard for describing statistical datasets, which the European Commission says improves the quality of published dataset records. [19]

**Proposed next step (the author's).** The federal statistical system could do the same: adopt a statistical profile of DCAT-US 3.0 as a community standard, endorsed by the Interagency Council on Statistical Policy (ICSP). The profile names which of 3.0's Optional fields statistical agencies fill and adds the few statistical fields 3.0 lacks, on StatDCAT-AP's model. It stays optional for the government at large and is expected practice for statistical data.

**Checking it is automated.** DCAT-US 3.0 is published as a machine-readable JSON Schema, and agencies can check their metadata against it with Data.gov's online validator or the published validation script. [9] Both are programs that report records that do not conform, not checklists. A statistical profile can be published the same way, as a stricter schema, and checked by the same programs.

## 6. What the public record cannot show

The FAIRness Project's two-year sequencing plan, a plan for transition, went to the Office of Management and Budget and was not published; a 2024 public request remains unanswered. [21][22]

## AI use in this document

Generative AI made a meaningful contribution. It located passages in the source documents, drafted the summary sentences from them, checked each sentence against the passage it cites, and laid out this version from the author's direction. Sentences the check could not confirm were removed, not reworded. The models were Anthropic's Claude Opus 5, Claude Opus 4.8, Claude Sonnet 5 and Claude Fable 5.1, used through Claude Code under a commercial subscription, 5 to 8 October 2026. The author reviewed and approved the content and is responsible for it. The passage behind every statement is quoted in the companion detail file and the questions-and-answers attachment of 5 October 2026.

## Sources

1. FCSM 20-04: A Framework for Data Quality. FCSM. 2020-09. Sections: page 54; page 55; passage 646; page 38; passage 475; passage 420; passage 505; page 8. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf>
2. Requirement level of each Dataset element, read from four versions of the DCAT-US Dataset page and schema (v1.1; 2025 working draft; pages of 21 August, 15 September and 5 October 2026), as tabled in the attachment to the questions-and-answers paper of 5 October 2026.
3. DCAT-US 3.0 Schema: Dataset (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. Sections: DCAT-US 3.0: Dataset; Dataset &gt; hasQualityMeasurement. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
4. The 2025 working draft of DCAT-US Version 3 (Candidate Recommendation Snapshot, not the published 3.0). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Dataset. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>
5. FCSM 19-01: Transparent Reporting for Integrated Data Quality. Prell M; Chapman C; Adeshiyan S; Fixler D; Garin T; Mirel L; Phipps P. n.d. Sections: page 113; page 24; 8. Conclusions. <https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf>
6. FCSM 25-03: AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality. FCSM. 2025-05. Sections: page 5; passage 39; page 4. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>
7. Data Sharing Working Group: Findings & Recommendations (Federal CDO Council). Federal Chief Data Officers Council, Data Sharing Working Group. 2022-03-30. page 6. <https://resources.data.gov/assets/documents/2021_DSWG_Recommendations_and_Findings_508.pdf>
8. FCSM 23-02: A Framework for Data Quality: Case Studies. Mirel LB; Singpurwalla D; Hoppe T; Liliedahl E; Schmitt R; Weber J. n.d. page 45. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.23.02_DQ_case_studies_FINAL.pdf>
9. DCAT-US 3.0 Overview (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. What's new in v3.0. <https://resources.data.gov/resources/dcat-us3/>
10. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What is DCAT-US v3.0. <https://resources.data.gov/resources/dcat-us3/>
11. DCAT-US Schema v3.0 (overview and reference). GSA. 2026-05. Sections: passage 7; passage 8. <https://resources.data.gov/resources/dcat-us3/>
12. DCAT-US v3.0 Schema Implementation Guide, version 1.1. Federal CDO Council. 2026-08-21 (version 1.1, 2026-09-09). passage 70. <https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf>
13. M-25-05: Phase 2 Implementation of the Foundations for Evidence-Based Policymaking Act of 2018: Open Government Data Access and Management Guidance. OMB. 2025-01-15. Sections: Section 4(a)(ii); Section 6. <https://bidenwhitehouse.archives.gov/wp-content/uploads/2025/01/M-25-05-Phase-2-Implementation-of-the-Foundations-for-Evidence-Based-Policymaking-Act-of-2018-Open-Government-Data-Access-and-Management-Guidance.pdf>
14. Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation). W3C. 2024-08-22. 14. Quality information. <https://www.w3.org/TR/vocab-dcat-3/>
15. Welcome to the CDOC/FCSM FAIRness Project (DCAT-US 3 project wiki, Home). CDOC/FCSM FAIRness Project (GitHub DOI-DO/dcat-us wiki). 2023-10-26. <https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Home.md>
16. DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov). U.S. General Services Administration / Data.gov. 2026. Sections: Class QualityMeasurement; QualityMeasurement &gt; unitMeasure. <https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/>
17. Data on the Web Best Practices (W3C Recommendation, 31 January 2017). W3C Data on the Web Best Practices Working Group. 2017-01-31. Sections: Intended Outcome; How to Test. <https://www.w3.org/TR/dwbp/>
18. Data on the Web Best Practices: Data Quality Vocabulary (W3C Working Group Note). W3C Data on the Web Best Practices Working Group. 2016-12-15. 3. Vocabulary Overview. <https://www.w3.org/TR/vocab-dqv/>
19. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. Sections: page 31; page 43. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>
20. The RDF Data Cube Vocabulary (W3C Recommendation, 16 January 2014). W3C Government Linked Data Working Group. 2014-01-16. 6.1 Dimensions, attributes and measures. <https://www.w3.org/TR/vocab-data-cube/>
21. Building Trust and FAIRness into the Process for Finding and Using Government Data Project (FAIRness Project): Implementing DCAT-US 3.0 Sequencing Plan (not published). Federal CDO Council and FCSM. 5 August 2024.
22. The FAIRness Project: Building Trust and FAIRness into Finding and Using Government Data (FCSM 2024 Research and Policy Conference, session B3.3). Thomas Dabolt (DOI); Michael Ratcliffe (U.S. Census Bureau). 2024-10-30. page 4. <https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/B3.3_Dabolt.pdf>
