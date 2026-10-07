# The table's rows, in detail

Prepared 7 October 2026. For each statistical need: the answers the check confirmed, each with its sources, and the outcome the rule assigns.

## 1. series: outcome E

- **Asked for?** The public record of what FCSM and the FAIRness Project asked for does not ask for whether a dataset is one release in a series.
- **Where it landed** The link marking a dataset as one release in a series was Optional in earlier drafts but no longer appears on the federal dataset page. [1][2]
- **What the standards say** Data Catalog Vocabulary version 3 makes series their own record type and links a dataset to its series with inSeries, which the current federal dataset page no longer lists. [1][3]

## 2. dimensions: outcome D

- **Asked for?** The Federal Committee on Statistical Methodology's transparent reporting paper tells reporters to describe the data's categorical variables, called dimensions, such as place, item and time. [4]
- **What the standards say** StatDCAT-AP, a statistical catalog profile, and the Data Cube vocabulary name each breakdown as its own field in the record, not in a written description of variables. [4][5][6]

## 3. units of measure: not placed: B or C or D or E

Why it is not placed: parts left unconfirmed by the check in both rounds: asked, literature.

- **Where it landed** Unit of measure is Optional, and it sits on the quality measurement class, giving the unit of a quality score rather than of the data itself. [7]

## 4. uncertainty: not placed: A or B

Why it is not placed: parts left unconfirmed by the check in both rounds: landed.

- **Asked for?** The Federal Committee on Statistical Methodology's report on transparent reporting for integrated data quality says sampling and nonsampling errors need to be measured and documented. [4]
- **What the standards say** The World Wide Web Consortium's Data Quality Vocabulary expresses precision and accuracy as quality measurements, the same Optional property DCAT-US 3.0 adopts for quality reporting. [1][2][8]

## 5. methodology and provenance: outcome D

- **Asked for?** The Federal Committee on Statistical Methodology's framework for data quality and its transparent reporting report ask documentation to give source data and the methods used to combine it. [4][9]
- **Where it landed** Statements of a dataset's history, the activity that generated it, its source, and documentation links are each Optional on the dataset page. [1][10]
- **What the standards say** The World Wide Web Consortium asks for origin and history a computer can process automatically, while the statistical side asked for written detail on the processing methods used. [9][11]

## 6. revisions and versions: outcome E

- **Asked for?** The public record of what FCSM and the FAIRness Project asked for does not ask for a record of whether numbers were revised after first release, or of which version a user has.
- **Where it landed** The Data Catalog Vocabulary profile for the United States, DCAT-US 3.0, marks version, versionNotes, hasVersion, hasCurrentVersion, previousVersion and replaces Optional on its Dataset page. [1][10]
- **What the standards say** The World Wide Web Consortium's Data Catalog Vocabulary builds version chains linking previous, current and later versions, and the United States profile uses those same chain properties. [1][2][3]

## 7. quality dimensions: outcome D

- **Asked for?** The Federal Committee on Statistical Methodology's 2025 paper says each data element should be assessed for quality on named aspects, called dimensions, such as timeliness and accuracy. [12]
- **Where it landed** In DCAT-US 3.0 the Dataset element hasQualityMeasurement is Optional, and it lists quality measurements for the dataset such as completeness, accuracy, or timeliness. [1][10]
- **What the standards say** The Data Quality Vocabulary, a web standard, offers a quality dimension class but no fixed dimension list, leaving the choice to publishers, unlike the statistical framework's named set. [3][8][9]

## 8. restricted-access terms: outcome E

- **Asked for?** The public record of what FCSM and the FAIRness Project asked for does not ask for restricted-access terms, meaning whether a dataset can be used only under conditions and how to apply for access.
- **Where it landed** Separate structured fields for access limits, use limits and controlled unclassified information limits are Recommended, and the rights field is also Recommended. [1][13]

## Sources

1. Requirement level of each Dataset element, read from four versions of the DCAT-US Dataset page and schema (v1.1; 2025 working draft; pages of 21 August, 15 September and 5 October 2026), as tabled in the attachment to the questions-and-answers paper of 5 October 2026.
2. DCAT-US - Version 3: Data Catalog Application Profile for the United States of America (Candidate Recommendation Snapshot; Internet Archive capture 2025-05-04). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Sections: Dataset; Version Chains and Hierarchies. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>
3. Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation). W3C. 2024-08-22. Sections: 12.1 How to specify dataset series; passage 1283; 1. Introduction; 14. Quality information. <https://www.w3.org/TR/vocab-dcat-3/>
4. FCSM 19-01: Transparent Reporting for Integrated Data Quality. Prell M; Chapman C; Adeshiyan S; Fixler D; Garin T; Mirel L; Phipps P. n.d. Sections: page 113; page 24; 8. Conclusions. <https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf>
5. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. Sections: page 31; page 43. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>
6. The RDF Data Cube Vocabulary (W3C Recommendation, 16 January 2014). W3C Government Linked Data Working Group. 2014-01-16. 6.1 Dimensions, attributes and measures. <https://www.w3.org/TR/vocab-data-cube/>
7. DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov). U.S. General Services Administration / Data.gov. 2026. Sections: Class QualityMeasurement; QualityMeasurement &gt; unitMeasure. <https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/>
8. Data on the Web Best Practices: Data Quality Vocabulary (W3C Working Group Note). W3C Data on the Web Best Practices Working Group. 2016-12-15. Sections: Table of Contents; 6.13 Express dataset precision and accuracy; 4.18 Instance: Precision; 3. Vocabulary Overview. <https://www.w3.org/TR/vocab-dqv/>
9. FCSM 20-04: A Framework for Data Quality. FCSM. 2020-09. Sections: page 54; page 8. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf>
10. DCAT-US 3.0 Schema: Dataset (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. DCAT-US 3.0: Dataset. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
11. Data on the Web Best Practices (W3C Recommendation, 31 January 2017). W3C Data on the Web Best Practices Working Group. 2017-01-31. Sections: Intended Outcome; How to Test. <https://www.w3.org/TR/dwbp/>
12. FCSM 25-03: AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality. FCSM. 2025-05. page 4. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>
13. DCAT-US 3.0 Overview (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. What's new in v3.0. <https://resources.data.gov/resources/dcat-us3/>
