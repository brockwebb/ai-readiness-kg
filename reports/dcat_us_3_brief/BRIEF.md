# The federal data catalog standard (DCAT-US 3.0) and statistics: a short brief

Names used. DCAT-US is the Data Catalog Application Profile for the United States of America [1], a version of the Data Catalog Vocabulary (DCAT) of the World Wide Web Consortium (W3C) [2]. AI is artificial intelligence. FCSM is the Federal Committee on Statistical Methodology. FAIR stands for findable, accessible, interoperable and reusable; the FAIRness Project is the federal Chief Data Officers Council's project with FCSM [3].

Prepared 7 October 2026 for a briefing to the Office of Management and Budget. Every sentence below comes from the documents listed at the end. One AI model wrote each sentence from those documents. Two other AI models checked it against them. A sentence they could not both confirm was cut, not reworded. The table and the yes-or-no answers come from a fixed rule, not from a model.

## 1. What DCAT-US 3.0 is

DCAT-US 3.0 is the federal standard for the catalog card, or metadata, that describes each government data asset listed publicly on Data.gov. [4][5][6] The Office of Management and Budget (OMB) memorandum M-25-05 directs each agency to update its comprehensive data inventory listings to the DCAT-US 3.0 schema by September 30, 2026. [6][7]

## 2. Who made it, and the statistical side's part

The General Services Administration says DCAT-US version 3.0 was built together by the Federal Chief Data Officers Council, the Federal Committee on Statistical Methodology (FCSM), and the Data.gov team. [4][5]

## 3. Does it deliver for statistics?

**Finding statistical data: no.** The needs that help people find statistical data are series, dimensions and units of measure (table rows 1, 2, 3). Series is in outcome E. Dimensions is in outcome D. Units of measure could not be placed; it could still be B, C, D or E.

**Judging whether data are fit for a use: no or partly.** The needs that let a user judge whether data are fit for a use are uncertainty and quality dimensions (table rows 4, 7). Uncertainty could not be placed; it could still be A or B. Quality dimensions is in outcome D.

A fixed rule gives these answers from the table in section 4. The answer is “no” if none of the needs is in outcome A, “partly” if at least one is, and “yes” if all are. When a need could not be placed, the rule is run for each outcome it could still be in, and both answers are shown when they differ.

## 4. What the statistical side asked for, by outcome

Names used in the table: StatDCAT-AP is the European Union's statistical version of DCAT.

Levels are read from the Dataset page as served on 5 October 2026.

| Need | Asked for in public? | Where it landed in 3.0 | What the standards say | Outcome |
|:----|:------|:--------|:----------|:----|
| series | Not in the public record | Dropped (inSeries) [1][8] | W3C DCAT 3 carries it; 3.0 does not [2][8] | E |
| dimensions | Yes: FCSM 19-01 [9] | Not confirmed | StatDCAT-AP and W3C Data Cube carry it differently from the ask [9][10][11] | D |
| units of measure | Not confirmed | Optional (unitMeasure) [12] | Not confirmed | Not placed: B or C or D or E |
| uncertainty | Yes: FCSM 19-01 [9] | Not confirmed | W3C Data Quality Vocabulary carries it, and 3.0 does too [1][8][13] | Not placed: A or B |
| methodology and provenance | Yes: FCSM 19-01 and FCSM 20-04 [9][14] | Optional (provenance, wasGeneratedBy, source and 1 more) [8][15] | W3C Data on the Web Best Practices carries it differently from the ask [14][16] | D |
| revisions and versions | Not in the public record | Optional (version, versionNotes, hasVersion and 3 more) [8][15] | W3C DCAT 3 carries it, and 3.0 does too [1][2][8] | E |
| quality dimensions | Yes: FCSM 25-03 [17] | Optional (hasQualityMeasurement) [8][15] | W3C DCAT 3 and W3C Data Quality Vocabulary carry it differently from the ask [2][13][14] | D |
| restricted-access terms | Not in the public record | Recommended (accessRestriction, useRestriction, cuiRestriction and 2 more) [8][18] | Not confirmed | E |

The five outcomes:

- **A.** Asked for, and included as Mandatory or Recommended.
- **B.** Asked for, and left Optional, put off to a later version, dropped, or left out.
- **C.** Not asked for, though the standards say a catalog needs it. This is the void.
- **D.** Asked for, but the standards say there is a better way to carry it than what was asked. This is the mismatch.
- **E.** Cannot be told from the public record, because the plan that held the project's recommendations is not public.

“Not confirmed” means the check could not confirm that part of the answer, in two tries; “not placed” means the rule needs that part, and the outcomes still possible are shown.

## 5. The void and the mismatch

Under the rule, dimensions, methodology and provenance and quality dimensions are in outcome D, the mismatch: the statistical side asked for them, and the standards carry them another way. No need is in outcome C, the void.

The Federal Committee on Statistical Methodology (FCSM) report A Framework for Data Quality says documentation should include methods used in processing, imputations, weighting, editing, integration methods, and data dictionaries. [14][17] Data on the Web Best Practices (2017) intends that people learn a dataset's origin and history and that computer programs process this provenance automatically, and tests for that. [16] The Data Catalog Vocabulary (DCAT) Version 3 says quality dimensions are characteristics that matter to users, sets no required list, and leaves implementers to choose their own. [2][13]

## 6. What could happen next

Europe built StatDCAT-AP, an add-on to its data catalog standard for describing statistical datasets, which the European Commission says improves the quality of published dataset records. [10] Data.gov's overview page says agencies can automatically check their dataset descriptions against the version 3.0 schema, using an online validator or their own tools. [18]

## 7. What cannot be known from the public record

Whether the statistical side asked for series, revisions and versions and restricted-access terms cannot be told from the public record (outcome E in the table).

The FAIRness Project's two-year sequencing plan, a plan for transition, went to the Office of Management and Budget and was not published; a 2024 public request remains unanswered. [19][20]

## 8. Where the detail is

The questions-and-answers paper of 5 October 2026 and its attachment give the detail, and quote every passage the answers rest on; the row-by-row detail behind the table is in the companion rows file.

## Sources

1. DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Sections: Dataset; Version Chains and Hierarchies. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>
2. Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation). W3C. 2024-08-22. Sections: 12.1 How to specify dataset series; passage 1283; 1. Introduction; 14. Quality information. <https://www.w3.org/TR/vocab-dcat-3/>
3. Welcome to the CDOC/FCSM FAIRness Project (DCAT-US 3 project wiki, Home). CDOC/FCSM FAIRness Project (GitHub DOI-DO/dcat-us wiki). 2023-10-26. <https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Home.md>
4. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What is DCAT-US v3.0. <https://resources.data.gov/resources/dcat-us3/>
5. DCAT-US Schema v3.0 (overview and reference). GSA. 2026-05. Sections: passage 7; passage 8. <https://resources.data.gov/resources/dcat-us3/>
6. DCAT-US v3.0 Schema Implementation Guide, version 1.1. Federal CDO Council. 2026-08-21 (version 1.1, 2026-09-09). passage 70. <https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf>
7. M-25-05: Phase 2 Implementation of the Foundations for Evidence-Based Policymaking Act of 2018: Open Government Data Access and Management Guidance. OMB. 2025-01-15. Sections: Section 4(a)(ii); Section 6. <https://bidenwhitehouse.archives.gov/wp-content/uploads/2025/01/M-25-05-Phase-2-Implementation-of-the-Foundations-for-Evidence-Based-Policymaking-Act-of-2018-Open-Government-Data-Access-and-Management-Guidance.pdf>
8. Requirement level of each Dataset element, read from four versions of the DCAT-US Dataset page and schema (v1.1; 2025 working draft; pages of 21 August, 15 September and 5 October 2026), as tabled in the attachment to the questions-and-answers paper of 5 October 2026.
9. FCSM 19-01: Transparent Reporting for Integrated Data Quality. Prell M; Chapman C; Adeshiyan S; Fixler D; Garin T; Mirel L; Phipps P. n.d. Sections: page 113; page 24; 8. Conclusions. <https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf>
10. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. Sections: page 31; page 43. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>
11. The RDF Data Cube Vocabulary (W3C Recommendation, 16 January 2014). W3C Government Linked Data Working Group. 2014-01-16. 6.1 Dimensions, attributes and measures. <https://www.w3.org/TR/vocab-data-cube/>
12. DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov). U.S. General Services Administration / Data.gov. 2026. Sections: Class QualityMeasurement; QualityMeasurement &gt; unitMeasure. <https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/>
13. Data on the Web Best Practices: Data Quality Vocabulary (W3C Working Group Note). W3C Data on the Web Best Practices Working Group. 2016-12-15. Sections: Table of Contents; 6.13 Express dataset precision and accuracy; 4.18 Instance: Precision; 3. Vocabulary Overview. <https://www.w3.org/TR/vocab-dqv/>
14. FCSM 20-04: A Framework for Data Quality. FCSM. 2020-09. Sections: page 54; page 8. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf>
15. DCAT-US 3.0 Schema: Dataset (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. DCAT-US 3.0: Dataset. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
16. Data on the Web Best Practices (W3C Recommendation, 31 January 2017). W3C Data on the Web Best Practices Working Group. 2017-01-31. Sections: Intended Outcome; How to Test. <https://www.w3.org/TR/dwbp/>
17. FCSM 25-03: AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality. FCSM. 2025-05. page 4. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>
18. DCAT-US 3.0 Overview (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. Sections: What's new in v3.0; Validation. <https://resources.data.gov/resources/dcat-us3/>
19. Building Trust and FAIRness into the Process for Finding and Using Government Data Project (FAIRness Project): Implementing DCAT-US 3.0 Sequencing Plan (not published). Federal CDO Council and FCSM. 5 August 2024.
20. The FAIRness Project: Building Trust and FAIRness into Finding and Using Government Data (FCSM 2024 Research and Policy Conference, session B3.3). Thomas Dabolt (DOI); Michael Ratcliffe (U.S. Census Bureau). 2024-10-30. page 4. <https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/B3.3_Dabolt.pdf>
