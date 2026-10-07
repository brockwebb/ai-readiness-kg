# The federal data catalog standard (DCAT-US 3.0) and statistics: a short brief

Names used. DCAT-US is the United States version of the Data Catalog Vocabulary (DCAT) of the World Wide Web Consortium (W3C) [1][2]. FAIR stands for findable, accessible, interoperable and reusable. The FAIRness Project is the federal Chief Data Officers Council's project with the Federal Committee on Statistical Methodology (FCSM) [3].

Prepared 7 October 2026 for the Office of Management and Budget. One artificial intelligence model wrote each sentence from the documents listed at the end. Two others checked it. A sentence they did not both confirm was cut. The questions-and-answers paper of 5 October 2026 and the companion rows file quote every passage.

## 1. What DCAT-US 3.0 is

DCAT-US 3.0 is the federal standard for the catalog card, or metadata, that describes each government data asset listed publicly on Data.gov. [4][5][6] The Office of Management and Budget (OMB) memorandum M-25-05 directs each agency to update its comprehensive data inventory listings to the DCAT-US 3.0 schema by September 30, 2026. [6][7]

## 2. Who made it

The General Services Administration says DCAT-US version 3.0 was built together by the Federal Chief Data Officers Council, the Federal Committee on Statistical Methodology (FCSM), and the Data.gov team. [4][5]

## 3. Does it deliver for statistics?

**Finding statistical data (rows 1 to 3): not decided.** The rule would say “no” only if dimensions (row 2, now D) and units of measure (row 3, not placed) were each in B, C or E. No row can be in A.

**Judging whether data are fit for a use (rows 4 and 7): not decided.** The rule would say “no” only if quality dimensions (row 7, now D) were in B, C or E. No row can be in A.

A rule fixed in advance, not a model, reads the table in section 4. It says “no” if every need is in outcome B, C or E, and “partly” if at least one is in A. Otherwise it does not decide.

## 4. The statistical needs, by outcome

CDO is Chief Data Officers; StatDCAT-AP is the European Union's statistical version of DCAT.

| Need | Asked for in public? | Where it landed in 3.0 (page of 5 October 2026) | What the standards say | Outcome |
|:----|:------|:--------|:----------|:----|
| series | Yes: FCSM 20-04 [8] | Dropped (inSeries) [9][10][11] | W3C DCAT 3 carries it; 3.0 does not [2][9][10] | B |
| dimensions | Yes: FCSM 19-01 [12] | Not confirmed | StatDCAT-AP and W3C Data Cube carry it differently from the ask [12][13][14] | D |
| units of measure | Not confirmed | Optional (unitMeasure) [15] | Not confirmed | Not placed: B or C or D or E |
| uncertainty | Yes: FCSM 19-01 [12] | Optional (hasQualityMeasurement) [9][10] | W3C Data Quality Vocabulary carries it, and 3.0 does too [9][10][16] | B |
| methodology and provenance | Yes: FCSM 19-01 and FCSM 20-04 [8][12] | Optional (provenance and 3 more) [9][10] | W3C Data on the Web Best Practices carries it differently from the ask [8][17] | D |
| revisions and versions | Yes: FCSM 19-01 and FCSM 25-03 [12][18] | Optional (version and 5 more) [9][10] | Not confirmed | Not placed: B or D |
| quality dimensions | Yes: FCSM 25-03 [18] | Optional (hasQualityMeasurement) [9][10] | W3C DCAT 3 and W3C Data Quality Vocabulary carry it differently from the ask [2][8][16] | D |
| restricted-access terms | Yes: CDO Council data sharing report, 2022, FCSM 19-01, FCSM 20-04 and FCSM 23-02 [8][12][19][20] | Recommended (accessRestriction and 4 more) [1][9][10] | Not confirmed | Not placed: A or D |

The five outcomes:

- **A.** Asked for, and Mandatory or Recommended.
- **B.** Asked for, and left Optional, put off, dropped or left out.
- **C.** Not asked for, though the standards say a catalog needs it (the void).
- **D.** Asked for, but the standards carry it a better way (the mismatch).
- **E.** Not knowable from the public record, because the plan is unpublished.

“Not confirmed”: the check could not confirm it in two tries. “Not placed”: the outcomes still possible are shown.

## 5. The void and the mismatch

Dimensions, methodology and provenance and quality dimensions are in outcome D, the mismatch. Whether the statistical side left out a need the standards call for (outcome C, the void) cannot be shown while the plan is unpublished. That is open for units of measure (row 3).

The Federal Committee on Statistical Methodology (FCSM) report A Framework for Data Quality says documentation should include methods used in processing, imputations, weighting, editing, integration methods, and data dictionaries. [8][18] Data on the Web Best Practices (2017) intends that people learn a dataset's origin and history and that computer programs process this provenance automatically, and tests for that. [17] The Data Catalog Vocabulary (DCAT) Version 3 says quality dimensions are characteristics that matter to users, sets no required list, and leaves implementers to choose their own. [2][16]

## 6. What could happen next

Europe built StatDCAT-AP, an add-on to its data catalog standard for describing statistical datasets, which the European Commission says improves the quality of published dataset records. [13] Data.gov's overview page says agencies can automatically check their dataset descriptions against the version 3.0 schema, using an online validator or their own tools. [1]

## 7. What the public record cannot show

The FAIRness Project's two-year sequencing plan, a plan for transition, went to the Office of Management and Budget and was not published; a 2024 public request remains unanswered. [21][22]

## Sources

1. DCAT-US 3.0 Overview (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. Sections: What's new in v3.0; Validation. <https://resources.data.gov/resources/dcat-us3/>
2. Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation). W3C. 2024-08-22. Sections: 12.1 How to specify dataset series; 14. Quality information. <https://www.w3.org/TR/vocab-dcat-3/>
3. Welcome to the CDOC/FCSM FAIRness Project (DCAT-US 3 project wiki, Home). CDOC/FCSM FAIRness Project (GitHub DOI-DO/dcat-us wiki). 2023-10-26. <https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Home.md>
4. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What is DCAT-US v3.0. <https://resources.data.gov/resources/dcat-us3/>
5. DCAT-US Schema v3.0 (overview and reference). GSA. 2026-05. Sections: passage 7; passage 8. <https://resources.data.gov/resources/dcat-us3/>
6. DCAT-US v3.0 Schema Implementation Guide, version 1.1. Federal CDO Council. 2026-08-21 (version 1.1, 2026-09-09). passage 70. <https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf>
7. M-25-05: Phase 2 Implementation of the Foundations for Evidence-Based Policymaking Act of 2018: Open Government Data Access and Management Guidance. OMB. 2025-01-15. Sections: Section 4(a)(ii); Section 6. <https://bidenwhitehouse.archives.gov/wp-content/uploads/2025/01/M-25-05-Phase-2-Implementation-of-the-Foundations-for-Evidence-Based-Policymaking-Act-of-2018-Open-Government-Data-Access-and-Management-Guidance.pdf>
8. FCSM 20-04: A Framework for Data Quality. FCSM. 2020-09. Sections: page 54; page 55; passage 646; page 38; page 8; passage 475; passage 420; passage 505. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf>
9. Requirement level of each Dataset element, read from four versions of the DCAT-US Dataset page and schema (v1.1; 2025 working draft; pages of 21 August, 15 September and 5 October 2026), as tabled in the attachment to the questions-and-answers paper of 5 October 2026.
10. DCAT-US 3.0 Schema: Dataset (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. Sections: DCAT-US 3.0: Dataset; Dataset &gt; hasQualityMeasurement. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
11. The 2025 working draft of DCAT-US Version 3 (Candidate Recommendation Snapshot, not the published 3.0). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Dataset. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>
12. FCSM 19-01: Transparent Reporting for Integrated Data Quality. Prell M; Chapman C; Adeshiyan S; Fixler D; Garin T; Mirel L; Phipps P. n.d. Sections: page 113; page 24; 8. Conclusions. <https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf>
13. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. Sections: page 31; page 43. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>
14. The RDF Data Cube Vocabulary (W3C Recommendation, 16 January 2014). W3C Government Linked Data Working Group. 2014-01-16. 6.1 Dimensions, attributes and measures. <https://www.w3.org/TR/vocab-data-cube/>
15. DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov). U.S. General Services Administration / Data.gov. 2026. Sections: Class QualityMeasurement; QualityMeasurement &gt; unitMeasure. <https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/>
16. Data on the Web Best Practices: Data Quality Vocabulary (W3C Working Group Note). W3C Data on the Web Best Practices Working Group. 2016-12-15. Sections: Table of Contents; 6.13 Express dataset precision and accuracy; 4.18 Instance: Precision; 3. Vocabulary Overview. <https://www.w3.org/TR/vocab-dqv/>
17. Data on the Web Best Practices (W3C Recommendation, 31 January 2017). W3C Data on the Web Best Practices Working Group. 2017-01-31. Sections: Intended Outcome; How to Test. <https://www.w3.org/TR/dwbp/>
18. FCSM 25-03: AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality. FCSM. 2025-05. Sections: page 5; passage 39; page 4. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>
19. Data Sharing Working Group: Findings & Recommendations (Federal CDO Council). Federal Chief Data Officers Council, Data Sharing Working Group. 2022-03-30. page 6. <https://resources.data.gov/assets/documents/2021_DSWG_Recommendations_and_Findings_508.pdf>
20. FCSM 23-02: A Framework for Data Quality: Case Studies. Mirel LB; Singpurwalla D; Hoppe T; Liliedahl E; Schmitt R; Weber J. n.d. page 45. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.23.02_DQ_case_studies_FINAL.pdf>
21. Building Trust and FAIRness into the Process for Finding and Using Government Data Project (FAIRness Project): Implementing DCAT-US 3.0 Sequencing Plan (not published). Federal CDO Council and FCSM. 5 August 2024.
22. The FAIRness Project: Building Trust and FAIRness into Finding and Using Government Data (FCSM 2024 Research and Policy Conference, session B3.3). Thomas Dabolt (DOI); Michael Ratcliffe (U.S. Census Bureau). 2024-10-30. page 4. <https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/B3.3_Dabolt.pdf>
