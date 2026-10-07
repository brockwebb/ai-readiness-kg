# The table's rows, in detail

Prepared 7 October 2026. For each statistical need: the answers the check confirmed, each with its sources, and the outcome the rule assigns.

## 1. series: outcome B

- **Asked for?** FCSM's Framework for Data Quality asks that documentation state the expected periodicity of a data product's production and the time frames it covers. [1]
- **Asked for?** FCSM's Framework for Data Quality asks agencies to tell data users the expected periodicity of production and the time frames available. [1]
- **Asked for?** FCSM's Framework for Data Quality calls for telling data users the expected periodicity of a data product's production. [1]
- **Asked for?** FCSM's Framework for Data Quality recommends documentation state the expected periodicity of a data product's production. [1]
- **Asked for?** FCSM notes OMB directives require agencies to publish annual release dates identifying reports as regular and recurring. [1]
- **Asked for?** FCSM notes OMB directives require agencies to publish annual release dates identifying reports as regular and recurring. [1]
- **Where it landed** The link marking a dataset as one release in a series was Optional in earlier drafts but no longer appears on the federal dataset page. [2][3][4]
- **What the standards say** Data Catalog Vocabulary version 3 makes series their own record type and links a dataset to its series with inSeries, which the current federal dataset page no longer lists. [2][3][5]

## 2. dimensions: outcome D

- **Asked for?** The Federal Committee on Statistical Methodology's transparent reporting paper tells reporters to describe the data's categorical variables, called dimensions, such as place, item and time. [6]
- **What the standards say** StatDCAT-AP, a statistical catalog profile, and the Data Cube vocabulary name each breakdown as its own field in the record, not in a written description of variables. [6][7][8]

## 3. units of measure: not placed: B or C or D or E

Why it is not placed: parts left unconfirmed by the check in both rounds: asked, literature.

- **Where it landed** Unit of measure is Optional, and it sits on the quality measurement class, giving the unit of a quality score rather than of the data itself. [9]

## 4. uncertainty: outcome B

- **Asked for?** The Federal Committee on Statistical Methodology's report on transparent reporting for integrated data quality says sampling and nonsampling errors need to be measured and documented. [6]
- **Where it landed** DCAT-US 3.0 lists hasQualityMeasurement, a measurement of a dataset against one quality measure such as accuracy, as Optional. [2][3]
- **What the standards say** The World Wide Web Consortium's Data Quality Vocabulary expresses precision and accuracy as quality measurements, the same Optional property DCAT-US 3.0 adopts for quality reporting. [2][3][10]

## 5. methodology and provenance: outcome D

- **Asked for?** The Federal Committee on Statistical Methodology's framework for data quality and its transparent reporting report ask documentation to give source data and the methods used to combine it. [1][6]
- **Where it landed** Statements of a dataset's history, the activity that generated it, its source, and documentation links are each Optional on the dataset page. [2][3]
- **What the standards say** The World Wide Web Consortium asks for origin and history a computer can process automatically, while the statistical side asked for written detail on the processing methods used. [1][11]

## 6. revisions and versions: not placed: B or D

Why it is not placed: parts left unconfirmed by the check in both rounds: literature.

- **Asked for?** FCSM 19-01's transparent reporting report calls for errors to be measured and documented and for revisions to be regularly analyzed. [6]
- **Asked for?** FCSM 25-03 on AI-ready federal statistical data asks agencies to return comprehensive metadata, including update timestamps, through their data product APIs. [12]
- **Asked for?** FCSM 25-03 on AI-ready federal statistical data recommends that high-value data products expose metadata recording when the data were updated. [12]
- **Asked for?** FCSM's AI-Ready Federal Statistical Data report calls for data product metadata that includes update timestamps reflecting when data was revised. [12]
- **Where it landed** The Data Catalog Vocabulary profile for the United States, DCAT-US 3.0, marks version, versionNotes, hasVersion, hasCurrentVersion, previousVersion and replaces Optional on its Dataset page. [2][3]

## 7. quality dimensions: outcome D

- **Asked for?** The Federal Committee on Statistical Methodology's 2025 paper says each data element should be assessed for quality on named aspects, called dimensions, such as timeliness and accuracy. [12]
- **Where it landed** In DCAT-US 3.0 the Dataset element hasQualityMeasurement is Optional, and it lists quality measurements for the dataset such as completeness, accuracy, or timeliness. [2][3]
- **What the standards say** The Data Quality Vocabulary, a web standard, offers a quality dimension class but no fixed dimension list, leaving the choice to publishers, unlike the statistical framework's named set. [1][5][10]

## 8. restricted-access terms: not placed: A or D

Why it is not placed: parts left unconfirmed by the check in both rounds: literature.

- **Asked for?** The Chief Data Officers Council data sharing report calls for an expedited data use agreement process governing the conditions of access to shared data. [13]
- **Asked for?** The CDO Council's data sharing report calls for establishing data use agreements that define how a party requests access to a dataset. [13]
- **Asked for?** FCSM working paper 19-01 on transparent reporting adopts accessibility as reporting the conditions under which users obtain data, including where to go and how to order. [6]
- **Asked for?** The FCSM data quality case studies report lists procedures and practices surrounding access, plus time from application to receipt, among the things to document for users. [14]
- **Asked for?** FCSM's Framework for Data Quality describes special arrangements, such as Research Data Centers, by which users apply for access to restricted-use data. [1]
- **Asked for?** The FCSM Framework for Data Quality states that confidential information compiled for official statistics should be used only for statistical purposes, a condition limiting dataset use. [1]
- **Asked for?** The FCSM Framework for Data Quality notes agencies may establish special user access provisions for datasets under accessibility. [1]
- **Where it landed** Separate structured fields for access limits, use limits and controlled unclassified information limits are Recommended, and the rights field is also Recommended. [2][3][15]

## Sources

1. FCSM 20-04: A Framework for Data Quality. FCSM. 2020-09. Sections: page 54; page 55; passage 646; page 38; page 8; passage 475; passage 420; passage 505. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf>
2. Requirement level of each Dataset element, read from four versions of the DCAT-US Dataset page and schema (v1.1; 2025 working draft; pages of 21 August, 15 September and 5 October 2026), as tabled in the attachment to the questions-and-answers paper of 5 October 2026.
3. DCAT-US 3.0 Schema: Dataset (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. Sections: DCAT-US 3.0: Dataset; Dataset &gt; hasQualityMeasurement. <https://resources.data.gov/standards/catalog/dcat-us-3/dataset/>
4. The 2025 working draft of DCAT-US Version 3 (Candidate Recommendation Snapshot, not the published 3.0). DOI-DO DCAT-US working group (GitHub doi-do/dcat-us). 2025-05-04. Dataset. <https://web.archive.org/web/20250504194000id_/https://doi-do.github.io/dcat-us/>
5. Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation). W3C. 2024-08-22. Sections: 12.1 How to specify dataset series; 14. Quality information. <https://www.w3.org/TR/vocab-dcat-3/>
6. FCSM 19-01: Transparent Reporting for Integrated Data Quality. Prell M; Chapman C; Adeshiyan S; Fixler D; Garin T; Mirel L; Phipps P. n.d. Sections: page 113; page 24; 8. Conclusions. <https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf>
7. StatDCAT-AP - DCAT Application Profile for description of statistical datasets, Version 1.0.1. European Commission, ISA2 programme / SEMIC Support Centre. 2019-05-28. Sections: page 31; page 43. <https://interoperable-europe.ec.europa.eu/sites/default/files/distribution/access_url/2019-05/0812e528-c428-4832-b674-d5b9c68d1b42/StatDCAT-AP_1.0.1.pdf>
8. The RDF Data Cube Vocabulary (W3C Recommendation, 16 January 2014). W3C Government Linked Data Working Group. 2014-01-16. 6.1 Dimensions, attributes and measures. <https://www.w3.org/TR/vocab-data-cube/>
9. DCAT-US 3.0: Temporal, Spatial, and Metrics (resources.data.gov). U.S. General Services Administration / Data.gov. 2026. Sections: Class QualityMeasurement; QualityMeasurement &gt; unitMeasure. <https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/>
10. Data on the Web Best Practices: Data Quality Vocabulary (W3C Working Group Note). W3C Data on the Web Best Practices Working Group. 2016-12-15. Sections: Table of Contents; 6.13 Express dataset precision and accuracy; 4.18 Instance: Precision; 3. Vocabulary Overview. <https://www.w3.org/TR/vocab-dqv/>
11. Data on the Web Best Practices (W3C Recommendation, 31 January 2017). W3C Data on the Web Best Practices Working Group. 2017-01-31. Sections: Intended Outcome; How to Test. <https://www.w3.org/TR/dwbp/>
12. FCSM 25-03: AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality. FCSM. 2025-05. Sections: page 5; passage 39; page 4. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf>
13. Data Sharing Working Group: Findings & Recommendations (Federal CDO Council). Federal Chief Data Officers Council, Data Sharing Working Group. 2022-03-30. page 6. <https://resources.data.gov/assets/documents/2021_DSWG_Recommendations_and_Findings_508.pdf>
14. FCSM 23-02: A Framework for Data Quality: Case Studies. Mirel LB; Singpurwalla D; Hoppe T; Liliedahl E; Schmitt R; Weber J. n.d. page 45. <https://statspolicy.gov/assets/fcsm/files/docs/FCSM.23.02_DQ_case_studies_FINAL.pdf>
15. DCAT-US 3.0 Overview (resources.data.gov; as served 2026-10-05). U.S. General Services Administration / Data.gov. 2026-10-05. What's new in v3.0. <https://resources.data.gov/resources/dcat-us3/>
