# DCAT-US 3.0: questions and answers

Prepared 5 October 2026 for a briefing to the Office of Management and Budget.

How these answers were made. Each answer was drafted by one AI model reading only the passages quoted in the attachment, and each sentence was then checked against the passages it cites by a different AI model. A sentence the check could not confirm was removed, not reworded. The attachment quotes every passage the answers rely on.

“Not found” lists what the documents collected for this briefing do not say. Each item was checked twice: against the passages gathered for its question, and against a second search of the same documents using the item's own words. An item means the search did not find it; it does not mean that no document anywhere says it.

## 1. What is DCAT-US 3.0, and how does it relate to W3C DCAT 3?

DCAT-US v3.0 is the federal data catalog metadata standard, updated to improve the Findability, Accessibility, Interoperability, and Reusability (FAIRness) of federal data. [1][2] It is a U.S. application profile of W3C DCAT version 3, not a new or separate standard, so most DCAT-US v3.0 metadata is valid W3C DCAT 3 metadata. [1][2] OMB memorandum M-25-05 states the OMB-approved standard metadata schema will conform to the United States profile of the W3C Data Catalog Vocabulary Version 3, known as DCAT-US 3.0. [3]

Sources:

1. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What is DCAT-US v3.0. <https://resources.data.gov/resources/dcat-us3/>
2. DCAT-US Schema v3.0 (overview and reference). GSA. 2026-05. passage 7. <https://resources.data.gov/resources/dcat-us3/>
3. M-25-05: Phase 2 Implementation of the Evidence Act — Open Government Data Access and Management Guidance. OMB. 2025-01-15. passage 104. <https://bidenwhitehouse.archives.gov/wp-content/uploads/2025/01/M-25-05-Phase-2-Implementation-of-the-Foundations-for-Evidence-Based-Policymaking-Act-of-2018-Open-Government-Data-Access-and-Management-Guidance.pdf>

## 2. Who developed it, and what was FCSM's role (the FAIRness Project)?

GSA's DCAT-US v3.0 overview pages state it was developed collaboratively by the Federal Chief Data Officers Council, the Federal Committee on Statistical Methodology, and the Data.gov team at GSA. [1][2] The FAIRness Project wiki says the Federal Chief Data Officer Council, in partnership with FCSM, is leading the project, whose outcome will be an updated federal metadata standard for agency data inventories. [3] A 2024 FCSM conference presentation names the project co-chairs as Thomas Dabolt of Interior and Michael Ratcliffe of the Census Bureau, for the CDO Council and FCSM. [4]

Not found:

- The sources do not state what specific tasks FCSM performed within the project beyond partnering with the CDO Council to lead it and co-chairing it.
- The sources do not state whether FCSM formally approved or adopted the final DCAT-US v3.0 schema.

Sources:

1. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What is DCAT-US v3.0. <https://resources.data.gov/resources/dcat-us3/>
2. DCAT-US Schema v3.0 (overview and reference). GSA. 2026-05. passage 8. <https://resources.data.gov/resources/dcat-us3/>
3. Welcome to the CDOC/FCSM FAIRness Project (DCAT-US 3 project wiki, Home). CDOC/FCSM FAIRness Project (GitHub DOI-DO/dcat-us wiki). 2023-10-26. Welcome to the CDOC/FCSM FAIRness Project. <https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Home.md>
4. The FAIRness Project: Building Trust and FAIRness into Finding and Using Government Data (FCSM 2024 Research and Policy Conference, session B3.3). Thomas Dabolt (DOI); Michael Ratcliffe (U.S. Census Bureau). 2024-10-30. <https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/B3.3_Dabolt.pdf>

## 3. What does policy require of agencies, and by when (M-25-05, the Evidence Act's inventory requirements)?

The Implementation Guide says Title II of the Evidence Act and M-25-05 direct each agency to develop and maintain a comprehensive data inventory and submit metadata to Data.gov's Federal Data Catalog by September 30, 2026. [1] M-25-05's action table sets September 30, 2026 for inventory data asset listings updated to DCAT-US 3.0, and requires the inventory hosted publicly at www.[agency].gov/data.json. [2] M-25-05 also says agencies must update the inventory no later than 90 days after creating or identifying a data asset, and within one year if the schema changes. [2]

Not found:

- The sources do not state what consequences apply to an agency that misses the September 30, 2026 date.
- The sources do not state when Data.gov stops harvesting DCAT-US v1.1 data.json files at the end of the transition period.
- The sources do not state whether any extension or waiver of these deadlines is available to agencies.

Sources:

1. DCAT-US v3.0 Schema Implementation Guide, version 1.1. Federal CDO Council. 2026-08-21 (version 1.1, 2026-09-09). passage 70. <https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf>
2. M-25-05: Phase 2 Implementation of the Evidence Act — Open Government Data Access and Management Guidance. OMB. 2025-01-15. Sections: Section 4(a)(ii); Section 6; passage 92; passage 103. <https://bidenwhitehouse.archives.gov/wp-content/uploads/2025/01/M-25-05-Phase-2-Implementation-of-the-Foundations-for-Evidence-Based-Policymaking-Act-of-2018-Open-Government-Data-Access-and-Management-Guidance.pdf>

## 4. Which elements are Mandatory, Recommended and Optional, and what did v1.1 require that 3.0 does not?

The DCAT-US 3.0 Dataset page captured on 15 September 2026 lists title, description, identifier and contactPoint as Mandatory. [1] On that same capture, publisher, keyword, modified, distribution and rights are Recommended, while accrualPeriodicity, issued, language, accessRights and conformsTo are Optional. [1] The v1.1 schema required accessLevel always, bureauCode and programCode for federal agencies, and publisher, keyword and modified always; the 15 September 2026 page drops the first three and makes the rest Recommended. [1]

Not found:

- The sources do not state why publisher is Mandatory on the 21 August 2026 Dataset page but Recommended on the 15 September 2026 capture.
- The sources do not state the full list of elements at each requirement level in a single summary.

Sources:

1. Requirement level of each Dataset element in four versions of the schema, read from each version's text (table in the attachment). Read from: DCAT-US 3.0 Schema: Dataset (resources.data.gov; Internet Archive capture 2026-09-15, after the September 2026 rewrite), 2026-09-15 <https://web.archive.org/web/20260915131436id_/https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US 3.0 Schema: Dataset (resources.data.gov), 2026-08-21 <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04), 2025-05-04 <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>; DCAT-US Schema v1.1 (Project Open Data Metadata Schema) - resources.data.gov, 2026-08-21 <https://resources.data.gov/resources/dcat-us/>.

## 5. What did FCSM and the FAIRness Project recommend for findability and for assessing fitness for use?

The FAIRness Project describes a strategic two-year sequencing plan to improve and integrate government-wide metadata cataloging so users can easily find, access, assess for fitness-for-use, and use federal data. [1][2] FCSM 19-01 states that transparent reporting is achieved when an agency provides clear and detailed documentation so users can assess data quality, that is fitness for use, for themselves. [3] FCSM 25-03 says enriching data access points with high-quality metadata and standardized, AI-friendly APIs can significantly improve how large language models discover, interpret, and relay publicly available federal statistics. [4]

Not found:

- The sources do not state the key findings and recommendations contained in the FAIRness Project's sequencing plan, which was provided to the Office of Management and Budget with no public copy located.
- The sources do not state which DCAT-US v3.0 fields FCSM or the FAIRness Project recommended for carrying fitness-for-use information, or at what requirement level.

Sources:

1. FAIRness Project: Project Overview (DCAT-US GitHub wiki). Federal CDO Council and FCSM. 2023-09-12. Introduction. <https://github.com/DOI-DO/dcat-us/wiki/Project-Overview>
2. The FAIRness Project: Building Trust and FAIRness into Finding and Using Government Data (FCSM 2024 Research and Policy Conference, session B3.3). Thomas Dabolt (DOI); Michael Ratcliffe (U.S. Census Bureau). 2024-10-30. <https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/B3.3_Dabolt.pdf>
3. FCSM 19-01: Transparent Reporting for Integrated Data Quality. Prell M; Chapman C; Adeshiyan S; Fixler D; Garin T; Mirel L; Phipps P. n.d. <https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf>
4. FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality. FCSM. 2025-05. Sections: Challenge & Opportunity; passage 31. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>

## 6. Which of those recommendations reached the Mandatory or Recommended tiers, and which did not?

contactPoint reached Mandatory: the 2025 working draft gave it Recommended, and both DCAT-US 3.0 Dataset pages, August and September 2026, list it as Mandatory. [1] Quality measurement did not rise: hasQualityMeasurement is Optional in the 2025 working draft and Optional on both the August and September 2026 Dataset pages. [1] geographicBoundingBox was Recommended in the 2025 working draft but is not listed on either DCAT-US 3.0 Dataset page. [1]

Not found:

- The sources do not state what the FAIRness Project's sequencing plan recommended, as no public copy exists and it was provided only to OMB.
- The sources do not state who set these requirement levels, or why an element's tier differs between the working draft and the published Dataset pages.
- The sources do not state whether the elements the September 2026 page newly lists as Recommended, such as accessRestriction and license, came from any earlier recommendation.

Sources:

1. Requirement level of each Dataset element in four versions of the schema, read from each version's text (table in the attachment). Read from: DCAT-US 3.0 Schema: Dataset (resources.data.gov; Internet Archive capture 2026-09-15, after the September 2026 rewrite), 2026-09-15 <https://web.archive.org/web/20260915131436id_/https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US 3.0 Schema: Dataset (resources.data.gov), 2026-08-21 <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04), 2025-05-04 <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>; DCAT-US Schema v1.1 (Project Open Data Metadata Schema) - resources.data.gov, 2026-08-21 <https://resources.data.gov/resources/dcat-us/>.

## 7. What changed between the public working draft and the published schema?

The 2025 working draft listed contactPoint and publisher as Recommended, while the Dataset page as captured on 21 August 2026 lists both as Mandatory. [1] The published Dataset pages list elements the working draft did not, including created, rightsHolder, supportedSchema, wasAttributedTo and wasUsedBy, all Optional. [1] Three properties the working draft listed as Recommended or Optional — geographic bounding box, next and prev — are not listed on either published Dataset page. [1]

Not found:

- The sources do not state why any of these changes were made between the working draft and the published schema.
- The sources do not state what changed between the working draft and the published schema for classes other than Dataset.

Sources:

1. Requirement level of each Dataset element in four versions of the schema, read from each version's text (table in the attachment). Read from: DCAT-US 3.0 Schema: Dataset (resources.data.gov; Internet Archive capture 2026-09-15, after the September 2026 rewrite), 2026-09-15 <https://web.archive.org/web/20260915131436id_/https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US 3.0 Schema: Dataset (resources.data.gov), 2026-08-21 <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04), 2025-05-04 <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>; DCAT-US Schema v1.1 (Project Open Data Metadata Schema) - resources.data.gov, 2026-08-21 <https://resources.data.gov/resources/dcat-us/>.

## 8. How does 3.0 represent data quality, and how does that map to the FCSM Framework for Data Quality (FCSM 20-04)?

The DCAT-US 3.0 Dataset page lists hasQualityMeasurement as Optional, holding quality measurements such as completeness, accuracy, or timeliness beyond spatial or temporal resolution. [1] On the Temporal, Spatial, and Metrics page, a QualityMeasurement gives a value, a unitMeasure, and an isMeasurementOf metric whose inDimension names a dimension URI. [2] FCSM 20-04 groups dimensions into utility (relevance, accessibility, timeliness, punctuality, granularity), objectivity (accuracy and reliability, coherence), and integrity (scientific integrity, credibility, computer and physical security, confidentiality). [3]

Not found:

- The sources do not state any mapping or crosswalk between DCAT-US 3.0 quality measurements and the FCSM Framework's domains or dimensions.
- The sources do not state any required or recommended vocabulary of dimension values for inDimension, including whether FCSM dimension identifiers exist.
- The sources do not state whether DCAT-US 3.0 quality reporting satisfies any FCSM 20-04 data quality documentation or reporting expectation.

Sources:

1. DCAT-US 3.0 Schema: Dataset (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. Sections: DCAT-US 3.0: Dataset; Dataset > hasQualityMeasurement. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
2. DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov). U.S. General Services Administration / Data.gov. 2026. Class QualityMeasurement. <https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/>
3. FCSM 20-04: A Framework for Data Quality. FCSM. 2020-09. Sections: passage 386; passage 397. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf>

## 9. Can 3.0 carry what statistical users need: series, dimensions, units, uncertainty (margins of error, CVs), methodology and revisions?

DatasetSeries groups related datasets published over time, including annual releases, recurring surveys and versioned reference data, and individual Dataset records point back to the series using the inSeries field, listed as Optional. [1][2][3] For revisions, the Dataset page as captured on 15 September 2026 lists previousVersion, a reference to the previous dataset version, and versionNotes, describing how a version differs from earlier ones, both Optional. [4] On dimensions, the DOI-DO Candidate Recommendation snapshot captured 4 May 2025 says DCAT 3 and the RDF Data Cube specification introduce new vocabulary terms describing statistical datasets and their dimensions more effectively. [5]

Not found:

- The sources do not state any DCAT-US 3.0 field for uncertainty measures such as margins of error or coefficients of variation.
- The sources do not state any DCAT-US 3.0 field for recording the methodology behind a dataset.
- The sources do not state a DCAT-US 3.0 field for the unit of measure of the data values themselves, as distinct from the Optional unitMeasure on QualityMeasurement.

Sources:

1. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What’s new in v3.0. <https://resources.data.gov/resources/dcat-us3/>
2. DCAT-US Schema v3.0 (overview and reference). GSA. 2026-05. passage 25. <https://resources.data.gov/resources/dcat-us3/>
3. DCAT-US 3.0 Schema: Dataset (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. DCAT-US 3.0: Dataset. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
4. DCAT-US 3.0 Schema: Dataset (resources.data.gov; Internet Archive capture 2026-09-15, after the September 2026 rewrite). U.S. General Services Administration / Data.gov. 2026-09-15. DCAT-US 3.0: Dataset. <https://web.archive.org/web/20260915131436id_/https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
5. DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Gaps with DCAT-US 1.1. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>

## 10. Where do the documents disagree with each other: the schema pages, the Implementation Guide, the M-25-05 crosswalk, M-25-05 itself, and secondary accounts? For example, is the language code ISO 639-1 or BCP 47?

On language the documents agree on ISO 639-1 two-letter codes, and the Overview's changelog says its own earlier BCP 47 description was an error corrected in May 2026. [1][2][3] The Overview disagrees with itself on accrualPeriodicity: its structural-changes table accepts three vocabularies and prefers plain-language codes, while its glossary says plain English descriptions cause validation failures. [1] The Dataset page as captured on 15 September 2026 lists publisher as Recommended, while the 21 August 2026 version lists it Mandatory and the 2025 working draft says Recommended. [4]

Not found:

- The sources do not state which language code standard M-25-05 itself requires.
- The sources do not state any element where the M-25-05 crosswalk differs from the schema pages or the Implementation Guide.
- The sources do not state what any secondary account says about the language code.

Sources:

1. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. Sections: Changelog; Structural changes; Glossary. <https://resources.data.gov/resources/dcat-us3/>
2. DCAT-US 3.0 Schema: Dataset (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. DCAT-US 3.0: Dataset. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
3. DCAT-US v3.0 Schema Implementation Guide, version 1.1. Federal CDO Council. 2026-08-21 (version 1.1, 2026-09-09). <https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf>
4. Requirement level of each Dataset element in four versions of the schema, read from each version's text (table in the attachment). Read from: DCAT-US 3.0 Schema: Dataset (resources.data.gov; Internet Archive capture 2026-09-15, after the September 2026 rewrite), 2026-09-15 <https://web.archive.org/web/20260915131436id_/https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US 3.0 Schema: Dataset (resources.data.gov), 2026-08-21 <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>; DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04), 2025-05-04 <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>; DCAT-US Schema v1.1 (Project Open Data Metadata Schema) - resources.data.gov, 2026-08-21 <https://resources.data.gov/resources/dcat-us/>.

## 11. How does DCAT-US 3.0 relate to AI readiness of statistical data (FCSM 25-03; the AI-readiness framework's indicators)?

FCSM 25-03 tells agencies to use common schemas or standards like the DCAT metadata standard used in data.gov catalogs, or SDMX, so AI developers have a consistent experience. [1] The DCAT-US v3.0 Schema Implementation Guide says adopting the schema aligns with the administration's AI priorities, because more descriptive metadata conveys context, structure, and lineage AI models need to interpret data correctly. [2] One framework indicator, G4, treats issuing authority as machine-readable catalog metadata: publisher, which DCAT-US 3.0 defines as Recommended, or DCAT-US 1.1's required bureauCode and programCode. [3]

Not found:

- The sources do not state that FCSM 25-03 names the DCAT-US v3.0 schema specifically, as opposed to the DCAT metadata standard generally.
- The sources do not state how the AI-readiness framework's other indicators map to DCAT-US 3.0 classes or fields.
- The sources do not state that DCAT-US 3.0 or its implementation guidance cites FCSM 25-03.

Sources:

1. FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality. FCSM. 2025-05. Sections: Approach (p.3); passage 39. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>
2. DCAT-US v3.0 Schema Implementation Guide, version 1.1. Federal CDO Council. 2026-08-21 (version 1.1, 2026-09-09). passage 85. <https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf>
3. AI-readiness framework for federal statistical publishers, indicator text. indicator G4.

## 12. What did the EU do for statistical data (StatDCAT-AP), and does the US have an equivalent?

StatDCAT-AP, dated 2019, extends Europe's DCAT Application Profile to describe statistical datasets, dataset series and services, aiming to integrate statistical data portals with open data portals and improve discoverability. [1] Because existing DCAT-AP properties did not meet the requirements, it created new properties in the StatDCAT-AP namespace to expose dimensions, such as time or region, and attributes, such as units of measure. [1] On the US side, the DCAT-US Version 3 Candidate Recommendation snapshot captured 4 May 2025 lists enhanced handling of statistical data, crediting new DCAT 3 and RDF Data Cube vocabulary terms. [2]

Not found:

- The sources do not state whether the United States has a separate statistical application profile equivalent to StatDCAT-AP.
- The sources do not state whether DCAT-US 3.0 adopts the StatDCAT-AP namespace properties for dimensions and attributes.
- The sources do not state any DCAT-US 3.0 requirement level, Mandatory, Recommended or Optional, for describing statistical dimensions of a dataset.

Sources:

1. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. 4.2. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>
2. DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Gaps with DCAT-US 1.1. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>

## 13. What options exist for next steps? Examples: a statistical application profile; raising requirement levels through guidance; conformance checking. State what each source supports. Do not recommend beyond the sources.

For conformance checking, the Data.gov overview says agencies can programmatically validate metadata against the JSON Schema (2020-12), and the 2025 Candidate Recommendation Snapshot defines the profile using SHACL. [1][2] The FAIRness project overview describes post-release governance as an open, transparent process to manage the application profile through any subsequent version releases. [3] On statistical extension, StatDCAT-AP 1.0.1 says the base DCAT Application Profile may in future be extended with additional agent roles that have proven useful across domains. [4]

Not found:

- The sources do not state that a statistical application profile of DCAT-US 3.0 is planned, proposed, or under development.

Sources:

1. DCAT-US 3.0 Overview (resources.data.gov). U.S. General Services Administration / Data.gov. 2026-08-21. What’s new in v3.0. <https://resources.data.gov/resources/dcat-us3/>
2. DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>
3. FAIRness Project: Project Overview (DCAT-US GitHub wiki). Federal CDO Council and FCSM. 2023-09-12. The Process. <https://github.com/DOI-DO/dcat-us/wiki/Project-Overview>
4. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>

## 14. What questions can the current sources not answer? List each, with the document that would answer it if one is known.

On the transition, the sources do not state the consequences of missing September 30, 2026, when Data.gov stops harvesting DCAT-US v1.1 data.json files, or whether extensions or waivers exist. [1]

Not found:

- The sources do not state any DCAT-US 3.0 field for uncertainty measures or methodology, any requirement level for statistical dimensions, or that a statistical application profile is planned.

Every unanswered part of the earlier answers, by question:

- Question 2:
    - The sources do not state what specific tasks FCSM performed within the project beyond partnering with the CDO Council to lead it and co-chairing it.
    - The sources do not state whether FCSM formally approved or adopted the final DCAT-US v3.0 schema.
- Question 3:
    - The sources do not state what consequences apply to an agency that misses the September 30, 2026 date.
    - The sources do not state when Data.gov stops harvesting DCAT-US v1.1 data.json files at the end of the transition period.
    - The sources do not state whether any extension or waiver of these deadlines is available to agencies.
- Question 4:
    - The sources do not state why publisher is Mandatory on the 21 August 2026 Dataset page but Recommended on the 15 September 2026 capture.
    - The sources do not state the full list of elements at each requirement level in a single summary.
- Question 5:
    - The sources do not state the key findings and recommendations contained in the FAIRness Project's sequencing plan, which was provided to the Office of Management and Budget with no public copy located.
    - The sources do not state which DCAT-US v3.0 fields FCSM or the FAIRness Project recommended for carrying fitness-for-use information, or at what requirement level.
- Question 6:
    - The sources do not state what the FAIRness Project's sequencing plan recommended, as no public copy exists and it was provided only to OMB.
    - The sources do not state who set these requirement levels, or why an element's tier differs between the working draft and the published Dataset pages.
    - The sources do not state whether the elements the September 2026 page newly lists as Recommended, such as accessRestriction and license, came from any earlier recommendation.
- Question 7:
    - The sources do not state why any of these changes were made between the working draft and the published schema.
    - The sources do not state what changed between the working draft and the published schema for classes other than Dataset.
- Question 8:
    - The sources do not state any mapping or crosswalk between DCAT-US 3.0 quality measurements and the FCSM Framework's domains or dimensions.
    - The sources do not state any required or recommended vocabulary of dimension values for inDimension, including whether FCSM dimension identifiers exist.
    - The sources do not state whether DCAT-US 3.0 quality reporting satisfies any FCSM 20-04 data quality documentation or reporting expectation.
- Question 9:
    - The sources do not state any DCAT-US 3.0 field for uncertainty measures such as margins of error or coefficients of variation.
    - The sources do not state any DCAT-US 3.0 field for recording the methodology behind a dataset.
    - The sources do not state a DCAT-US 3.0 field for the unit of measure of the data values themselves, as distinct from the Optional unitMeasure on QualityMeasurement.
- Question 10:
    - The sources do not state which language code standard M-25-05 itself requires.
    - The sources do not state any element where the M-25-05 crosswalk differs from the schema pages or the Implementation Guide.
    - The sources do not state what any secondary account says about the language code.
- Question 11:
    - The sources do not state that FCSM 25-03 names the DCAT-US v3.0 schema specifically, as opposed to the DCAT metadata standard generally.
    - The sources do not state how the AI-readiness framework's other indicators map to DCAT-US 3.0 classes or fields.
    - The sources do not state that DCAT-US 3.0 or its implementation guidance cites FCSM 25-03.
- Question 12:
    - The sources do not state whether the United States has a separate statistical application profile equivalent to StatDCAT-AP.
    - The sources do not state whether DCAT-US 3.0 adopts the StatDCAT-AP namespace properties for dimensions and attributes.
    - The sources do not state any DCAT-US 3.0 requirement level, Mandatory, Recommended or Optional, for describing statistical dimensions of a dataset.
- Question 13:
    - The sources do not state that a statistical application profile of DCAT-US 3.0 is planned, proposed, or under development.

Documents known to exist that were not available for this briefing, as their catalog records describe them:

- The FAIRness Project (briefing to the National Geospatial Advisory Committee, April 2024). no in-corpus reference points at it and it is not a member of any scoped layer. Recorded as assessed and declined, which is a different state from nobody having looked. Assessed mechanically by kg/assess.py against docs/runbook_document_admission.md §1 and corpus/layers.yaml. || PRIOR NOTE, PRESERVED: Found while resolving footnote 11, not named by the addendum, and cataloged so the decision is on the record (CLAUDE.md: every document the project has considered has one manifest entry). Nine slides from the same project, six months before B3.3, briefing the FGDC's advisory committee. Its content overlaps B3.3's and adds the geospatial side. Cataloged by kg/catalog.py; the admission decision is kg/assess.py's.
- Building Trust and FAIRness into the Process for Finding and Using Government Data Project (FAIRness Project): Implementing DCAT-US 3.0 Sequencing Plan. no public copy: Provided to OMB and not published. The FAIRness Project co-chairs' 2024 FCSM conference slides (session B3.3, slide 6) give its status as "Provided to Office of Management and Budget". Searched 2026-10-05 and absent from resources.data.gov, councils.gov, statspolicy.gov, the DOI-DO/dcat-us and GSA/dcat-us repositories and the DOI-DO/dcat-us wiki. A public request for it, DOI-DO/dcat-us issue #214 (2024-07-15), is open and unanswered. The corpus is 100% public (CLAUDE.md); 1 in-corpus segment(s) cite it, so basis (a) would hold if it were published. REVISIT IF: it is published at a source a program can fetch with no login. Assessed mechanically by kg/assess.py against docs/runbook_document_admission.md §1 and corpus/layers.yaml. || PRIOR NOTE, PRESERVED: The Implementation Guide's footnote 11, cited for the statement that OMB mandated DCAT-US v3.0 "to ensure datasets are more visible, accessible, and useful across the broader data ecosystem". The FAIRness Project's second deliverable: "a strategic two-year sequencing (i.e., transition) plan to improve and integrate government-wide metadata cataloging to facilitate data users being able to easily find, access, assess for fitness-for-use, and use federal data" (wiki Project Overview). Per the B3.3 slides it contains key findings and recommendations and what OMB, the councils, agencies and service providers need to consider. That is the FCSM side's record of what it asked for, and it is not public. Cataloged by kg/catalog.py; the admission decision is kg/assess.py's.

Sources:

1. Answer to question 3, above. question 3.
