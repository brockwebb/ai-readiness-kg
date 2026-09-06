# Entity-resolution gold sample — 100 pairs for the operator

**Task:** `cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md` §5. **Zero model spend.** **Seed:** 20260905. **Drawn:** 20 per stratum from five strata.

**§2 wrote NOTHING to the vocabulary log** — the §1.3 positive control failed, so no homograph split was applied. These pairs are drawn from the PRE-SPLIT vocabulary (epoch 1).

## What to do

For each pair below, read the two spans and decide whether the two nodes denote **the same thing**. Not whether they are related, not whether they are about the same topic — whether a reader asking "how many distinct X does this corpus describe" should count them once or twice.

- `same` — one thing, named twice.
- `different` — two things. Includes the case where one is a SPECIES of the other ("explainable AI techniques" is narrower than "explainable AI"): narrower is not the same.
- `uncertain` — the spans do not let you tell. This is a real answer and is excluded from the rates rather than pushed to one side.

**You are not checking the machine's work.** The sheet deliberately does not show you the pipeline's decision, the similarity score, the vocabulary term, or which stratum a pair came from — those are held in `state/er_gold_key.json` and are joined in only at scoring time. Please do not read the key first.

---

## P001

**Node A** — `Concept` · *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)* · arm `training_data_readiness`

> **data quality**
>
> In designing AIDRIN, we incorporate a comprehensive range of metrics cover- ing not only traditional data quality parameters but also offering assessments of AI readiness using metrics such as data bias, privacy, feature relevance, correlation, and FAIR compliance.

**Node B** — `Concept` · *Data Readiness for AI: A 360-Degree Survey* · arm `training_data_readiness`

> **data quality**
>
> Data quality

**P001 — verdict (same / different / uncertain):** ______

**P001 — note:** ______

---

## P002

**Node A** — `Concept` · *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)* · arm `training_data_readiness`

> **data quality**
>
> In designing AIDRIN, we incorporate a comprehensive range of metrics cover- ing not only traditional data quality parameters but also offering assessments of AI readiness using metrics such as data bias, privacy, feature relevance, correlation, and FAIR compliance.

**Node B** — `Concept` · *Statistics Canada Quality Guidelines, Sixth Edition* · arm `publication_actionability`

> **data quality**
>
> This phase also plays a key role in the evaluation of data quality because it is here that specific problems can be identified, which can lead to future improvements to the process.

**P002 — verdict (same / different / uncertain):** ______

**P002 — note:** ______

---

## P003

**Node A** — `Platform` · *Bing Webmaster Tools API documentation (Microsoft Learn)* · arm `publication_actionability`

> **Bing**
>
> programmatically access information about their website on Bing search and index

**Node B** — `Platform` · *Auditing Google's AI Overviews and Featured Snippets: A Case Study on Baby Care and Pregnancy* · arm `publication_actionability`

> **Bing**
>
> 10.4 million distinct Bing

**P003 — verdict (same / different / uncertain):** ______

**P003 — note:** ______

---

## P004

**Node A** — `Concept` · *Understanding and Using American Community Survey Data: What All Data Users Need to Know* · arm `publication_actionability`

> **Nonsampling error**
>
> ACS Quality Measures Nonsampling error is extremely difficult, if not impos- sible, to measure directly.

**Node B** — `Concept` · *Census Bureau Statistical Quality Standards — Standard F2: Providing Documentation to Support Transparency in Information Products* · arm `publication_actionability`

> **Nonsampling error**
>
> Discussion of potential nonsampling errors (e.g., nonresponse, coverage, processing, and measurement).

**P004 — verdict (same / different / uncertain):** ______

**P004 — note:** ______

---

## P005

**Node A** — `Concept` · *Census Bureau Statistical Quality Standards — Standard F1: Releasing Information Products* · arm `publication_actionability`

> **Metadata**
>
> Metadata

**Node B** — `Concept` · *FAIR Principles: Interpretations and Implementation Considerations* · arm `publication_actionability`

> **Metadata**
>
> Metadata is any description of a resource

**P005 — verdict (same / different / uncertain):** ______

**P005 — note:** ______

---

## P006

**Node A** — `Concept` · *Census Bureau Statistical Quality Standards — Standard F2: Providing Documentation to Support Transparency in Information Products* · arm `publication_actionability`

> **Nonsampling error**
>
> Discussion of potential nonsampling errors (e.g., nonresponse, coverage, processing, and measurement).

**Node B** — `Concept` · *Measuring and Communicating the Uncertainty in Official Economic Statistics* · arm `publication_actionability`

> **nonsampling errors**
>
> It accordingly reviews different categorisations of uncertainty, speciﬁcally the traditional typology that distinguishes sampling from nonsampling errors and the newer, but complementary, typology of Manski (2015) that distinguishes transitory, permanent and conceptual uncertainties.

**P006 — verdict (same / different / uncertain):** ______

**P006 — note:** ______

---

## P007

**Node A** — `Platform` · *Generative Engine Optimization: How to Dominate AI Search* · arm `publication_actionability`

> **ChatGPT**
>
> Instead of relying exclusively on ranked lists of hyperlinks, AI- powered systems such as ChatGPT, Perplexity, and other emerging platforms synthesize information directly into narrative answers.

**Node B** — `Platform` · *Improving LLM Access to Federal Open Data: A Pilot Study of Model Context Protocol* · arm `publication_actionability`

> **ChatGPT**
>
> Methodology We tested the free-tier versions of ChatGPT (GPT-4.1) and Gemini (Flash 2.5) to evaluate their ability

**P007 — verdict (same / different / uncertain):** ______

**P007 — note:** ______

---

## P008

**Node A** — `Concept` · *America's DataHub RFS Topic MLMU-25: Measuring LLM Understanding of Federal Statistical Data* · arm `publication_actionability`

> **Accuracy**
>
> accuracy and relevancy of LLM responses

**Node B** — `Concept` · *FCSM 23-02: A Framework for Data Quality: Case Studies* · arm `publication_actionability`

> **accuracy**
>
> This case study highlights how BLS mitigated threats to the accuracy and reliability of these crowdsourced data.

**P008 — verdict (same / different / uncertain):** ______

**P008 — note:** ______

---

## P009

**Node A** — `Concept` · *FCSM 19-01: Transparent Reporting for Integrated Data Quality* · arm `publication_actionability`

> **relevance**
>
> Two other limitations can have effects on relevance, due to limited granularity.

**Node B** — `Concept` · *Webb: NIST x FCSM Crosswalk (Data Quality <-> AI Trustworthiness)* · arm `publication_actionability`

> **Relevance**
>
> Relevance Fitness for user needs

**P009 — verdict (same / different / uncertain):** ______

**P009 — note:** ______

---

## P010

**Node A** — `Platform` · *Google Search Central: Introduction to robots.txt* · arm `publication_actionability`

> **Google Search**
>
> prevent image, video, and audio files from appearing in Google Search results

**Node B** — `Platform` · *Google Search Central: Get started with Search Console* · arm `publication_actionability`

> **Google Search**
>
> how they are performing on Google Search

**P010 — verdict (same / different / uncertain):** ______

**P010 — note:** ______

---

## P011

**Node A** — `Concept` · *M-25-05: Phase 2 Implementation of the Evidence Act — Open Government Data Access and Management* · arm `publication_actionability`

> **Metadata**
>
> Metadata means

**Node B** — `Concept` · *A framework for AI-ready data* · arm `training_data_readiness`

> **metadata**
>
> metadata,

**P011 — verdict (same / different / uncertain):** ______

**P011 — note:** ______

---

## P012

**Node A** — `Concept` · *Croissant Format Specification (MLCommons)* · arm `publication_actionability`

> **Dataset**
>
> **Dataset** : A collection of data points or items reflecting the results of such activities as measuring, reporting, collecting, analyzing, or observing.

**Node B** — `Concept` · *schema.org: Dataset* · arm `publication_actionability`

> **Dataset**
>
> Instances of [Dataset](https://schema.org/Dataset "Dataset") may appear as a value for the following properties Property | On Types | Description ---|---|--- A dataset contained in this catalog.

**P012 — verdict (same / different / uncertain):** ______

**P012 — note:** ______

---

## P013

**Node A** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **AI risk**
>
> Categories Subcategories 5.3 Measure The MEASURE function employs quantitative, qualitative, or mixed-method tools, tech- niques, and methodologies to analyze, assess, benchmark, and monitor AI risk and related impacts.

**Node B** — `Concept` · *NIST Generative AI Profile (AI 600-1)* · arm `org_maturity`

> **AI risks**
>
> 40 MANAGE 1.3: Responses to the AI risks deemed high priority, as identiﬁed by the MAP function, are developed, planned, and documented.

**P013 — verdict (same / different / uncertain):** ______

**P013 — note:** ______

---

## P014

**Node A** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **human-AI configurations**
>
> Measuring AI risks includes tracking metrics for trustworthy characteristics, social impact, and human-AI configurations.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **human-AI teaming configurations**
>
> • Development and regular tracking of human-AI teaming configurations.

**P014 — verdict (same / different / uncertain):** ______

**P014 — note:** ______

---

## P015

**Node A** — `Framework` · *NIST AI RMF Playbook* · arm `org_maturity`

> **AI Accountability Framework for Federal Agencies & Other Entities**
>
> AI Transparency Resources • GAO-21-519SP: AI Accountability Framework for Federal Agencies & Other Entities.

**Node B** — `Framework` · *NIST AI RMF Playbook* · arm `org_maturity`

> **AI Accountability Framework for Federal Agencies & Other Entities**
>
> • GAO-21-519SP: AI Accountability Framework for Federal Agencies & Other Entities.

**P015 — verdict (same / different / uncertain):** ______

**P015 — note:** ______

---

## P016

**Node A** — `Concept` · *NIST Generative AI Profile (AI 600-1)* · arm `org_maturity`

> **misinformation**
>
> Information Security; Harmful Bias and Homogenization MG-2.2-005 Engage in due diligence to analyze GAI output for harmful content, potential misinformation, and CBRN-related or NCII content.

**Node B** — `Concept` · *AI-Ready Data: Ensuring Public Data Meets the Needs of AI and the American Public — The USAFacts Guide to AI-Ready Data for Government Agencies* · arm `publication_actionability`

> **misinformation**
>
> • Documentation and data should be regularly reviewed and updated by internal teams to find and correct potential abuse and misinformation.

**P016 — verdict (same / different / uncertain):** ______

**P016 — note:** ______

---

## P017

**Node A** — `Standard` · *Perplexity crawlers (docs.perplexity.ai)* · arm `publication_actionability`

> **robots.txt**
>
> we recommend allowing `PerplexityBot` in your site’s `robots.txt` file

**Node B** — `Standard` · *Sitemaps XML format (sitemaps.org protocol)* · arm `publication_actionability`

> **robots.txt**
>
> You can specify more than one Sitemap file per robots.txt file.

**P017 — verdict (same / different / uncertain):** ______

**P017 — note:** ______

---

## P018

**Node A** — `Platform` · *schema.org: DataCatalog* · arm `publication_actionability`

> **Google**
>
> Google - July 2026

**Node B** — `Platform` · *schema.org: SoftwareApplication* · arm `publication_actionability`

> **Google**
>
> Based on monthly aggregations from Google's web index.

**P018 — verdict (same / different / uncertain):** ______

**P018 — note:** ______

---

## P019

**Node A** — `Concept` · *Technology Readiness Levels for Machine Learning Systems (MLTRL)* · arm `org_maturity`

> **data readiness**
>
> considers data readiness and availability

**Node B** — `Concept` · *AI-ready data action plan* · arm `publication_actionability`

> **data readiness**
>
> This document looks to explore the characteristics of whether available data is suitable for AI capabilities – i.e. **does it have right data?** Effective data readiness requires consideration of the specific AI capability in use; whether traditional machine learning methods, large language models, or emerging trends in AI [footnote 3].

**P019 — verdict (same / different / uncertain):** ______

**P019 — note:** ______

---

## P020

**Node A** — `Concept` · *AI-ready data action plan* · arm `publication_actionability`

> **FAIR principles**
>
> Genomics England’s approach aligns with FAIR principles: data is highly findable and accessible to approved researchers via a governed research portal (over 1,500 researchers securely analyse de identified data), interoperable through global standards (adopting GA4GH frameworks such as CRAM and the htsget API), and well documented and curated for reusability.

**Node B** — `Concept` · *The FAIR Guiding Principles for scientific data management and stewardship* · arm `publication_actionability`

> **FAIR principles**
>
> The FAIR principles can equally be applied to these non-data assets, which need to be identi ﬁed, described, discovered, and reused in much the same manner as data.

**P020 — verdict (same / different / uncertain):** ______

**P020 — note:** ______

---

## P021

**Node A** — `Concept` · *AI Data Readiness Checklist (Digital Government Hub)* · arm `publication_actionability`

> **AI data readiness**
>
> AI Data Readiness

**Node B** — `Concept` · *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)* · arm `training_data_readiness`

> **Data Readiness for AI**
>
> 3 DEFINING DATA READINESS FOR AI The concept of “Data Readiness for AI” lacks a standard definition and is still evolving.

**P021 — verdict (same / different / uncertain):** ______

**P021 — note:** ______

---

## P022

**Node A** — `Concept` · *AI-REAL Toolkit: AI Readiness Assessment Guide* · arm `org_maturity`

> **Bias and fairness in AI**
>
> free from bias

**Node B** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **Fairness in AI**
>
> 3.7 Fair – with Harmful Bias Managed Fairness in AI includes concerns for equality and equity by addressing issues such as harm- ful bias and discrimination.

**P022 — verdict (same / different / uncertain):** ______

**P022 — note:** ______

---

## P023

**Node A** — `Concept` · *Understanding and Using American Community Survey Data: What All Data Users Need to Know* · arm `publication_actionability`

> **Public Use Microdata Areas (PUMAs)**
>
> Geographic areas covered: Nation, states, and Public Use Microdata Areas (PUMAs).

**Node B** — `Concept` · *Understanding and Using American Community Survey Data: What All Data Users Need to Know* · arm `publication_actionability`

> **Public Use Microdata Areas**
>
> Alternatively, data users could present ACS estimates for Public Use Microdata Areas, since they meet the 65,000-population threshold required for single- year estimates and are often used as a substitute for county-level data.

**P023 — verdict (same / different / uncertain):** ______

**P023 — note:** ______

---

## P024

**Node A** — `Framework` · *Executive Order 14110: Safe, Secure, and Trustworthy Development and Use of AI* · arm `org_maturity`

> **AI Risk Management Framework (NIST AI 100–1)**
>
> companion resource to the AI Risk Management Framework, NIST AI 100–1

**Node B** — `Framework` · *Beyond Model Readiness: Institutional Readiness for AI Deployment in Public Systems (IAR)* · arm `org_maturity`

> **NIST AI Risk Management Framework**
>
> NIST AI Risk Management Framework

**P024 — verdict (same / different / uncertain):** ______

**P024 — note:** ______

---

## P025

**Node A** — `Instrument` · *FCSM 23-02: A Framework for Data Quality: Case Studies* · arm `publication_actionability`

> **State Safety Data Quality (SSDQ) methodology**
>
> The methodology for State Safety Data Quality (SSDQ) was developed by the FMCSA to

**Node B** — `Instrument` · *FCSM 23-02: A Framework for Data Quality: Case Studies* · arm `publication_actionability`

> **State Safety Data Quality**
>
> The methodology for State Safety Data Quality (SSDQ) was developed by the FMCSA to evaluate the completeness, timeliness, accuracy, and consistency of the state-reported commercial

**P025 — verdict (same / different / uncertain):** ______

**P025 — note:** ______

---

## P026

**Node A** — `Framework` · *FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality* · arm `publication_actionability`

> **Framework for Data Quality**
>
> FCSM Framework for Data Quality

**Node B** — `Framework` · *FCSM 23-02: A Framework for Data Quality: Case Studies* · arm `publication_actionability`

> **FCSM Framework for Data Quality**
>
> Introduction: This case study examines how the FCSM Framework for Data Quality serves as a tool to determine the utility of administrative data in determining program effectiveness and provides considerations for the data’s use that are paramount to upholding rigor and ethics as principles of program evaluation.

**P026 — verdict (same / different / uncertain):** ______

**P026 — note:** ______

---

## P027

**Node A** — `Framework` · *From Accuracy to Readiness: Metrics and Benchmarks for Human-AI Decision-Making* · arm `org_maturity`

> **four-part taxonomy of metrics for human–AI onboarding**
>
> Figure 1: We propose a four-part taxonomy of metrics for human–AI onboarding (top) and show how each metric family becomes observable and actionable across the human-AI onboarding lifecycle (Understand–Control–Improve) (bottom).

**Node B** — `Framework` · *From Accuracy to Readiness: Metrics and Benchmarks for Human-AI Decision-Making* · arm `org_maturity`

> **taxonomy of metrics**
>
> 2.3 A Taxonomy of Metrics for Human–AI Onboarding & Decision-Making Building on empirical findings across healthcare AI onboarding, decision-support evaluation, uncertainty-aware delegation, and accountable AI systems, we propose a taxonomy of metrics that capture complementary aspects of onboarding and collaboration [9, 17, 24, 25, 37, 38].

**P027 — verdict (same / different / uncertain):** ______

**P027 — note:** ______

---

## P028

**Node A** — `Standard` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **sitemap.xml**
>
> sitemap.xml is a list of all the indexable human-readable information available on a site.

**Node B** — `Standard` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **sitemap.xml**
>
> sitemap.xml is a list of all the indexable human-readable information available on a site.

**P028 — verdict (same / different / uncertain):** ______

**P028 — note:** ______

---

## P029

**Node A** — `Standard` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **sitemap.xml**
>
> sitemap.xml is a list of all the indexable human-readable information available on a site.

**Node B** — `Standard` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **sitemap.xml**
>
> sitemap.xml is a list of all the indexable human-readable information available on a site.

**P029 — verdict (same / different / uncertain):** ______

**P029 — note:** ______

---

## P030

**Node A** — `Framework` · *M-24-10: Advancing Governance, Innovation, and Risk Management for Agency Use of AI* · arm `org_maturity`

> **NIST AI Risk Management Framework (AI RMF 1.0)**
>
> Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST Publication AI 100-1

**Node B** — `Framework` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **AI RMF 1.0**
>
> NIST AI 100-1 Artificial Intelligence Risk Management Framework (AI RMF 1.0)

**P030 — verdict (same / different / uncertain):** ______

**P030 — note:** ______

---

## P031

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **k-anonymity metrics**
>
> k-anonymity metrics, l-diversity, t-closeness).

**Node B** — `Concept` · *AIDRIN 2.0: A Framework to Assess Data Readiness for AI* · arm `training_data_readiness`

> **k-anonymity**
>
> k-anonymity, l-diversity, t-closeness

**P031 — verdict (same / different / uncertain):** ______

**P031 — note:** ______

---

## P032

**Node A** — `Framework` · *NIST AI RMF Playbook* · arm `org_maturity`

> **Model AI Governance Framework Assessment**
>
> • WEF Model AI Governance Framework Assessment 2020.

**Node B** — `Framework` · *NIST AI RMF Playbook* · arm `org_maturity`

> **WEF Model AI Governance Framework Assessment 2020**
>
> • WEF Model AI Governance Framework Assessment 2020.

**P032 — verdict (same / different / uncertain):** ______

**P032 — note:** ______

---

## P033

**Node A** — `Framework` · *NIST Generative AI Profile (AI 600-1)* · arm `org_maturity`

> **AI Risk Management Framework (AI RMF 1.0)**
>
> AI Risk Management Framework (AI RMF 1.0)

**Node B** — `Framework` · *NIST AI 100-3: The Language of Trustworthy AI — An In-Depth Glossary of Terms* · arm `org_maturity`

> **NIST AI Risk Management Framework (AI RMF)**
>
> NIST AI Risk Management Framework (AI RMF)

**P033 — verdict (same / different / uncertain):** ______

**P033 — note:** ______

---

## P034

**Node A** — `Concept` · *Generalization bias in large language model summarization of scientific research* · arm `publication_actionability`

> **algorithmic overgeneralization tendency**
>
> The model was significant overall (F7, 4492 = 32.34, p < 0.001), showing that LLM summaries (all combined) were twice as likely to contain generalized conclusions compared to the original abstracts, indicating an algorithmic overgeneralization tendency (table 1, figure 2).

**Node B** — `Concept` · *Generalization bias in large language model summarization of scientific research* · arm `publication_actionability`

> **algorithmic overgeneralizations**
>
> Compared to a simple summarization request, asking for responses faithful to the original text produced a twofold increase in the likelihood of generalized conclusions, in some models, increasing overall algorithmic overgeneralizations by up to 15% (see e.g. ChatGPT-4o (UI), table 2).

**P034 — verdict (same / different / uncertain):** ______

**P034 — note:** ______

---

## P035

**Node A** — `Standard` · *schema.org: Dataset* · arm `publication_actionability`

> **W3C DCAT (Data Catalog Vocabulary)**
>
> This class is based upon W3C DCAT work

**Node B** — `Standard` · *Google Search Central: Dataset (Dataset, DataCatalog, DataDownload) structured data* · arm `publication_actionability`

> **Data Catalog Vocabulary (DCAT)**
>
> equivalent structures represented in [W3C](https://www.w3.org/)'s [Data Catalog Vocabulary (DCAT) format](https://www.w3.org/TR/vocab-dcat/)

**P035 — verdict (same / different / uncertain):** ______

**P035 — note:** ______

---

## P036

**Node A** — `Concept` · *SDMX 3.0 Technical Specifications, Section 1: Framework for SDMX Technical Standards* · arm `publication_actionability`

> **Statistical Data and Metadata Exchange (SDMX)**
>
> Statistical Data and Metadata Exchange (SDMX)

**Node B** — `Standard` · *Fostering AI-Readiness and Responsible Redistribution of Official Statistics* · arm `publication_actionability`

> **SDMX**
>
> • Adopt common data exchange standards : Supporting the implementation of SDMX can boost efficiency in transferring data and metadata across platforms with open APIs.

**P036 — verdict (same / different / uncertain):** ______

**P036 — note:** ______

---

## P037

**Node A** — `Concept` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMX (Statistical Data and Metadata eXchange)**
>
> The SDMx initiative sets standards to facilitate the exchange of statistical data and metadata

**Node B** — `Standard` · *Fostering AI-Readiness and Responsible Redistribution of Official Statistics* · arm `publication_actionability`

> **SDMX**
>
> Solutions involve adopting metadata standards and best practices of data curation, using data exchange standards such as SDMX, systematically employing APIs for data and metadata sharing, and utilizing technology for data and metadata quality control and optimization.

**P037 — verdict (same / different / uncertain):** ______

**P037 — note:** ______

---

## P038

**Node A** — `Standard` · *Statistical Policy Working Paper 46: Data Quality Assessment Tool for Administrative Data* · arm `publication_actionability`

> **OMB race and ethnicity categories**
>
> Do questions asked about race use the current race and ethnicity categories defined by the Office of Management and Budget (OMB)?

**Node B** — `Standard` · *Statistical Policy Working Paper 46: Data Quality Assessment Tool for Administrative Data* · arm `publication_actionability`

> **race and ethnicity categories**
>
> For example: Do questions asked about race use the current race and ethnicity categories defined by the Office of Management and Budget (OMB)?

**P038 — verdict (same / different / uncertain):** ______

**P038 — note:** ______

---

## P039

**Node A** — `Concept` · *Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation)* · arm `publication_actionability`

> **data access service**
>
> DCAT allows the description of a data access service to be included in a catalog.

**Node B** — `Concept` · *Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation)* · arm `publication_actionability`

> **Data Service**
>
> ### 6.9 Class: Data Service

**P039 — verdict (same / different / uncertain):** ______

**P039 — note:** ______

---

## P040

**Node A** — `Framework` · *Webb: NIST x FCSM Crosswalk (Data Quality <-> AI Trustworthiness)* · arm `publication_actionability`

> **NIST AI RMF 1.0 (Artificial Intelligence Risk Management Framework)**
>
> NIST AI RMF 1.0 ( Artificial Intelligence Risk Management Framework )

**Node B** — `Framework` · *M-24-10: Advancing Governance, Innovation, and Risk Management for Agency Use of AI* · arm `org_maturity`

> **NIST AI Risk Management Framework (AI RMF 1.0)**
>
> Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST Publication AI 100-1

**P040 — verdict (same / different / uncertain):** ______

**P040 — note:** ______

---

## P041

**Node A** — `Concept` · *GEO: Generative Engine Optimization* · arm `publication_actionability`

> **content visibility**
>
> While SEO methods such as Keyword Stuffing perform poorly, our proposed GEO methods generalize well to multiple generative engines sig- nificanlty improve content visibility.

**Node B** — `Concept` · *GEO: Generative Engine Optimization* · arm `publication_actionability`

> **SEO methods**
>
> However, we note that changes made by GEO methods are targeted changes in textual content, bearing some resemblance with SEO methods, while not affecting other metadata such as domain name, backlinks, etc, and thus, they are less likely to affect search engine rankings.

**P041 — verdict (same / different / uncertain):** ______

**P041 — note:** ______

---

## P042

**Node A** — `Concept` · *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)* · arm `training_data_readiness`

> **SGC**
>
> We evaluate the features of AIDRIN using two case studies, i,e., German Credit (SGC) dataset [28] and Cancer Genome Atlas Lung Adenocarcinoma (TCGA-LUAD) clinical data of patients accessed from the National Cancer Institute NCI Data Portal [24].

**Node B** — `Concept` · *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)* · arm `training_data_readiness`

> **TCGA-LUAD**
>
> 5.3.2 TCGA-LUAD Case Study dataset analysis using Jupyter Note- book.

**P042 — verdict (same / different / uncertain):** ______

**P042 — note:** ______

---

## P043

**Node A** — `Tool` · *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)* · arm `training_data_readiness`

> **Pandas**
>
> Pandas handles and processes the datasets efficiently, while Matplotlib enhances AIDRIN with visualization capabilities.

**Node B** — `Tool` · *Are LLMs ready to help non-expert users to make charts of official statistics data?* · arm `publication_actionability`

> **matplotlib**
>
> This led to disordered axes and uneven spacing since plotting libraries like matplotlib do not automatically interpret strings as temporal data.

**P043 — verdict (same / different / uncertain):** ______

**P043 — note:** ______

---

## P044

**Node A** — `Concept` · *Characterizing Multimodal Long-form Summarization: A Case Study on Financial Reports* · arm `publication_actionability`

> **NUM**
>
> To enhance GPT-4’s performance in ex- tracting numeric values, particularly from tables, we design three explicit prompts and one chain-of-thought (CoT) prompt (Appendix D): NUM to explicitly request the inclusion of nu- meric values.

**Node B** — `Concept` · *Characterizing Multimodal Long-form Summarization: A Case Study on Financial Reports* · arm `publication_actionability`

> **GPT-4**
>
> To enhance GPT-4’s performance in ex- tracting numeric values, particularly from tables, we design three explicit prompts and one chain-of-thought (CoT) prompt (Appendix D): NUM to explicitly request the inclusion of nu- meric values.

**P044 — verdict (same / different / uncertain):** ______

**P044 — note:** ______

---

## P045

**Node A** — `Concept` · *Characterizing Multimodal Long-form Summarization: A Case Study on Financial Reports* · arm `publication_actionability`

> **numeric values**
>
> To enhance GPT-4’s performance in ex- tracting numeric values, particularly from tables, we design three explicit prompts and one chain-of-thought (CoT) prompt (Appendix D): NUM to explicitly request the inclusion of nu- meric values.

**Node B** — `Concept` · *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation* · arm `publication_actionability`

> **GPT-4**
>
> GPT-4 (OpenAI, 2023) is a multi- modal LM released by OpenAI available through an API.

**P045 — verdict (same / different / uncertain):** ______

**P045 — note:** ______

---

## P046

**Node A** — `Concept` · *Understanding and Using American Community Survey Data: What All Data Users Need to Know* · arm `publication_actionability`

> **Product of Two Estimates**
>
> To calculate standard errors for overlapping ACS multiyear estimates see the section on “Understanding Error and Determining Statistical Significance.” Calculating Measures of Error for the Product of Two Estimates In some instances, data users may need to derive an estimate by multiplying a published count by a published percentage.

**Node B** — `Concept` · *Understanding and Using American Community Survey Data: What All Data Users Need to Know* · arm `publication_actionability`

> **ACS multiyear estimates**
>
> As an illustration, consider ACS multiyear estimates for the two time periods of 2005–2009 and 2010–2014.

**P046 — verdict (same / different / uncertain):** ______

**P046 — note:** ______

---

## P047

**Node A** — `Instrument` · *Cisco AI Readiness Assessment — Survey Instrument (web capture)* · arm `org_maturity`

> **Cisco AI Readiness Assessment**
>
> Cisco AI Readiness Assessment - Cisco

**Node B** — `Instrument` · *Cisco AI Readiness Index — Methodology (web page capture)* · arm `org_maturity`

> **AI Readiness Index**
>
> AI Readiness Index

**P047 — verdict (same / different / uncertain):** ______

**P047 — note:** ______

---

## P048

**Node A** — `Concept` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **LLM-friendly content**
>
> llms.txt logo We propose adding a `/llms.txt` markdown file to websites to provide LLM-friendly content.

**Node B** — `Concept` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **llms.txt**
>
> llms.txt logo We propose adding a `/llms.txt` markdown file to websites to provide LLM-friendly content.

**P048 — verdict (same / different / uncertain):** ______

**P048 — note:** ______

---

## P049

**Node A** — `Standard` · *M-25-05: Phase 2 Implementation of the Evidence Act — Open Government Data Access and Management* · arm `publication_actionability`

> **W3C Data Catalog Vocabulary Version 3**
>
> of the W3C Data Catalog Vocabulary Version 3, known as the DCAT-US 3.0.

**Node B** — `Standard` · *Google Search Central: Dataset (Dataset, DataCatalog, DataDownload) structured data* · arm `publication_actionability`

> **Data Catalog Vocabulary (DCAT)**
>
> equivalent structures represented in [W3C](https://www.w3.org/)'s [Data Catalog Vocabulary (DCAT) format](https://www.w3.org/TR/vocab-dcat/)

**P049 — verdict (same / different / uncertain):** ______

**P049 — note:** ______

---

## P050

**Node A** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **fair with their harmful biases managed**
>
> Next, AI risks and trustworthi- ness are analyzed, outlining the characteristics of trustworthy AI systems, which include Page 2 NIST AI 100-1 AI RMF 1.0 valid and reliable, safe, secure and resilient, accountable and transparent, explainable and interpretable, privacy enhanced, and fair with their harmful biases managed.

**Node B** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **trustworthy AI systems**
>
> Next, AI risks and trustworthi- ness are analyzed, outlining the characteristics of trustworthy AI systems, which include Page 2 NIST AI 100-1 AI RMF 1.0 valid and reliable, safe, secure and resilient, accountable and transparent, explainable and interpretable, privacy enhanced, and fair with their harmful biases managed.

**P050 — verdict (same / different / uncertain):** ______

**P050 — note:** ______

---

## P051

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **AI system overseers**
>
> 85 of 142 Defining and differentiating various human roles and responsibilities for AI systems’ governance, and differentiating AI system overseers and those using or interacting with AI systems can enhance AI risk management activities.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **AI risk management activities**
>
> 85 of 142 Defining and differentiating various human roles and responsibilities for AI systems’ governance, and differentiating AI system overseers and those using or interacting with AI systems can enhance AI risk management activities.

**P051 — verdict (same / different / uncertain):** ______

**P051 — note:** ______

---

## P052

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **diverse workforce**
>
> Without commitment from senior leadership, beneficial aspects of team diversity and inclusion can be overridden by unstated organizational incentives that inadvertently conflict with the broader values of a diverse workforce.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **team diversity**
>
> Without commitment from senior leadership, beneficial aspects of team diversity and inclusion can be overridden by unstated organizational incentives that inadvertently conflict with the broader values of a diverse workforce.

**P052 — verdict (same / different / uncertain):** ______

**P052 — note:** ______

---

## P053

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **AI system oversight and governance**
>
> Effective risk management efforts include: • clear definitions and differentiation of the various human roles and responsibilities for AI system oversight and governance • recognizing and clarifying differences between AI system overseers and those using or interacting with AI systems.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **AI risk management activities**
>
> 85 of 142 Defining and differentiating various human roles and responsibilities for AI systems’ governance, and differentiating AI system overseers and those using or interacting with AI systems can enhance AI risk management activities.

**P053 — verdict (same / different / uncertain):** ______

**P053 — note:** ______

---

## P054

**Node A** — `Concept` · *NIST Generative AI Profile (AI 600-1)* · arm `org_maturity`

> **explainable AI (XAI) techniques**
>
> MG-3.2-001 Apply explainable AI (XAI) techniques (e.g., analysis of embeddings, model compression/distillation, gradient-based attributions, occlusion/term reduction, counterfactual prompts, word clouds) as part of ongoing continuous improvement processes to mitigate risks related to unexplainable GAI systems.

**Node B** — `Concept` · *Arm AI Readiness Index* · arm `org_maturity`

> **explainable AI**
>
> Explainable AI (XAI): XAI is a special research direction in AI, which aims at making the operations and outcomes of AI models transparent and understandable by users.

**P054 — verdict (same / different / uncertain):** ______

**P054 — note:** ______

---

## P055

**Node A** — `Concept` · *Knowing When to Ask - Bridging Large Language Models and Data* · arm `publication_actionability`

> **United States**
>
> INPUT: Question:- Tell me one statistic about California, San Francisco,Alabama and the US.Answer:-California is 1st as the nation's most populous state, with about39 million people in 2020.In San Francisco, the diabetes rate is 9.2 cases per 10000people.San Francisco and the surrounding San Francisco Bay Area are aglobal center of economic activity and the arts and sciences.In 1861, Alabama seceded from the United States to become part ofthe Confederate States of America.As of 2022, the United States receives approximately 81% of itsenergy from fossil fuel and the largest source of the country'senergy came from petroleum (35.8%), followed by natural gas(33.4%) and renewable sources (13.3%).

**Node B** — `Concept` · *Knowing When to Ask - Bridging Large Language Models and Data* · arm `publication_actionability`

> **California**
>
> INPUT: Question:- Tell me one statistic about California, San Francisco,Alabama and the US.Answer:-California is 1st as the nation's most populous state, with about39 million people in 2020.In San Francisco, the diabetes rate is 9.2 cases per 10000people.San Francisco and the surrounding San Francisco Bay Area are aglobal center of economic activity and the arts and sciences.In 1861, Alabama seceded from the United States to become part ofthe Confederate States of America.As of 2022, the United States receives approximately 81% of itsenergy from fossil fuel and the largest source of the country'senergy came from petroleum (35.8%), followed by natural gas(33.4%) and renewable sources (13.3%).

**P055 — verdict (same / different / uncertain):** ______

**P055 — note:** ______

---

## P056

**Node A** — `Standard` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMx 1.0 Technical Specifications**
>
> **SDMx 1.0 Technical Specifications** The SDMx Standards Version 1.0 provide the technical specification for a set of XML and EDIFACT syntax data formats based on a common information model.

**Node B** — `Standard` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMX Standards**
>
> The SDMx Standards Version 1.0 provide the technical specification for a set of XML and EDIFACT syntax data formats based on a common information model.

**P056 — verdict (same / different / uncertain):** ______

**P056 — note:** ______

---

## P057

**Node A** — `Concept` · *Are LLMs ready to help non-expert users to make charts of official statistics data?* · arm `publication_actionability`

> **data manipulation**
>
> Through systematic experiments with eight LLMs across 25 tasks, we found that while base models, under one-shot conditions, achieve ade- quate code generation (mean score: 8.3/10), they exhibit substan- tial deficiencies in data manipulation (5.9/10) and visual design (6.5/10).

**Node B** — `Concept` · *Are LLMs ready to help non-expert users to make charts of official statistics data?* · arm `publication_actionability`

> **visual design**
>
> Through systematic experiments with eight LLMs across 25 tasks, we found that while base models, under one-shot conditions, achieve ade- quate code generation (mean score: 8.3/10), they exhibit substan- tial deficiencies in data manipulation (5.9/10) and visual design (6.5/10).

**P057 — verdict (same / different / uncertain):** ______

**P057 — note:** ______

---

## P058

**Node A** — `Concept` · *QuanTemp: A real-world open-domain benchmark for fact-checking numerical claims* · arm `publication_actionability`

> **MNLI data**
>
> Our baseline system for numerical fact-checking, informed by infor- mation retrieval and fact-checking best practices, reveals that claim decomposition, models pre fine-tuned using MNLI data, and models specialized in numerical understanding enhance performance for numerical claims.

**Node B** — `Concept` · *QuanTemp: A real-world open-domain benchmark for fact-checking numerical claims* · arm `publication_actionability`

> **numerical claim**
>
> To remedy this, we require more QuanTemp: A real-world open-domain benchmark for fact-checking numerical claims SIGIR ’24, July 14–18, 2024, Washington, DC, USA than one quantitative segment, excluding any nouns like “Covid-19” mentions, to qualify as a numerical claim.

**P058 — verdict (same / different / uncertain):** ______

**P058 — note:** ______

---

## P059

**Node A** — `Concept` · *Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation)* · arm `publication_actionability`

> **conformance degree**
>
> This section shows different modeling patterns combining [VOCAB-DQV] with [PROV-O] and EARL [EARL10-Schema] to represent the conformance degree to a stated quality standard and the details about the conformance tests.

**Node B** — `Concept` · *Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation)* · arm `publication_actionability`

> **conformance test**
>
> Example 47 specifies some newly minted concepts representing the degree of conformance (i.e., conformant, not conformant) and declares the `dcterms:type` for indicating the result of conformance test.

**P059 — verdict (same / different / uncertain):** ______

**P059 — note:** ______

---

## P060

**Node A** — `Standard` · *Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation)* · arm `publication_actionability`

> **DCAT-2014 vocabulary**
>
> The DCAT-2014 vocabulary [VOCAB-DCAT-1] and DCAT 2 [VOCAB-DCAT-2] have been extended for application in data catalogs in different domains.

**Node B** — `Standard` · *Data Cards for Standardized Metadata Across DOE-Aligned Data Initiatives* · arm `publication_actionability`

> **Data  Catalog  Vocabulary  (DCAT)  –  Version  3**
>
> Available: https://bidenwhitehouse.archives.gov/wp-content/uploads/2022/08/08-2022-OSTP-Public-Access-Memo.pdf [10] W3C, Data Catalog Vocabulary (DCAT) – Version 3, W3C Recommendation, 2024.

**P060 — verdict (same / different / uncertain):** ______

**P060 — note:** ______

---

## P061

**Node A** — `Framework` · *AI-REAL Toolkit: AI Readiness Assessment Guide* · arm `org_maturity`

> **National AI governance framework**
>
> national AI governance framework

**Node B** — `Framework` · *Arm AI Readiness Index* · arm `org_maturity`

> **Model AI Governance Framework**
>
> the Model AI Governance Framework, first introduced in 2019 and updated in 2020

**P061 — verdict (same / different / uncertain):** ______

**P061 — note:** ______

---

## P062

**Node A** — `Framework` · *AI Watch: Revisiting Technology Readiness Levels for Relevant AI Technologies* · arm `org_maturity`

> **Readiness-vs-generality chart methodology**
>
> We introduce and use two-dimensional plots called readiness-vs-generality charts in which we define the degree of generality of specific AI technologi es on the x -axis vs the readiness level (the TRLs) on the y axis.

**Node B** — `Framework` · *A framework for AI-ready data* · arm `training_data_readiness`

> **AI-readiness  Framework**
>
> As described above, we assessed this dataset against the criteria outlined in the AI-readiness Framework:

**P062 — verdict (same / different / uncertain):** ______

**P062 — note:** ______

---

## P063

**Node A** — `Instrument` · *Data Readiness for AI: A 360-Degree Survey* · arm `training_data_readiness`

> **UCI coherence score**
>
> 21 CSUR ’22, June 03–05, 2022, Woodstock, NY Hiniduma et al. Newman et al. proposed “UCI coherence score” [99] to assess the coherence of topics generated by a topic model.

**Node B** — `Instrument` · *Data Readiness for AI: A 360-Degree Survey* · arm `training_data_readiness`

> **CV coherence score**
>
> propose the “CV coherence score” [117] to quantify topic coherence in textual

**P063 — verdict (same / different / uncertain):** ______

**P063 — note:** ______

---

## P064

**Node A** — `Framework` · *Data Readiness for Scientific AI at Scale* · arm `training_data_readiness`

> **360-degree data readiness framework**
>
> 360-degree survey of data readiness

**Node B** — `Framework` · *Data Readiness Levels* · arm `training_data_readiness`

> **Data Readiness Levels**
>
> Data Readiness Levels

**P064 — verdict (same / different / uncertain):** ______

**P064 — note:** ______

---

## P065

**Node A** — `Concept` · *Executive Order 13960: Promoting the Use of Trustworthy AI in the Federal Government* · arm `org_maturity`

> **Agency inventory of AI use cases**
>
> Agency Inventory of AI Use Cases

**Node B** — `Concept` · *M-24-10: Advancing Governance, Innovation, and Risk Management for Agency Use of AI* · arm `org_maturity`

> **AI use case inventory**
>
> AI use case inventory

**P065 — verdict (same / different / uncertain):** ______

**P065 — note:** ______

---

## P066

**Node A** — `Concept` · *Executive Order 14110: Safe, Secure, and Trustworthy Development and Use of AI* · arm `org_maturity`

> **Federal Government use of AI**
>
> Federal Government use of AI

**Node B** — `Concept` · *M-24-18: Advancing the Responsible Acquisition of AI in Government* · arm `org_maturity`

> **artificial intelligence (AI)**
>
> The use of artificial intelligence (AI) in the Federal Government presents tremendous

**P066 — verdict (same / different / uncertain):** ______

**P066 — note:** ______

---

## P067

**Node A** — `Standard` · *FAIR Principles: Interpretations and Implementation Considerations* · arm `publication_actionability`

> **Resource Description Framework (RDF)**
>
> Resource Description Framework (RDF)

**Node B** — `Standard` · *The RDF Data Cube Vocabulary (W3C Recommendation, 16 January 2014)* · arm `publication_actionability`

> **RDF (Resource Description Framework)**
>
> the W3C RDF (Resource Description Framework) standard

**P067 — verdict (same / different / uncertain):** ______

**P067 — note:** ______

---

## P068

**Node A** — `Standard` · *LinkChecker README* · arm `publication_actionability`

> **robots.txt exclusion protocol**
>
> honors robots.txt exclusion protocol

**Node B** — `Standard` · *The /llms.txt file (llmstxt.org)* · arm `publication_actionability`

> **robots.txt**
>
> robots.txt lets automated tools know what access to a site is considered acceptable, such as for search indexing bots.

**P068 — verdict (same / different / uncertain):** ______

**P068 — note:** ______

---

## P069

**Node A** — `Concept` · *NIST AI 100-3: The Language of Trustworthy AI — An In-Depth Glossary of Terms* · arm `org_maturity`

> **Interdisciplinary field of trustworthy and responsible AI**
>
> interdisciplinary feld of trustworthy and responsible AI

**Node B** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **trustworthy AI systems**
>
> Effectively managing the risk of potential harms could lead to more trustworthy AI systems and unleash potential benefits to people (individ- uals, communities, and society), organizations, and systems/ecosystems.

**P069 — verdict (same / different / uncertain):** ______

**P069 — note:** ______

---

## P070

**Node A** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **identification of incidents**
>
> GOVERN 4.3: Organizational practices are in place to enable AI testing, identification of incidents, and information sharing.

**Node B** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **information sharing**
>
> GOVERN 4.3: Organizational practices are in place to enable AI testing, identification of incidents, and information sharing.

**P070 — verdict (same / different / uncertain):** ______

**P070 — note:** ______

---

## P071

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **data minimizing methods**
>
> Privacy-enhancing technologies (“PETs”) for AI, as well as data minimizing methods such as de-identification and aggregation for certain model outputs, can support design for privacy- enhanced AI systems.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **Privacy-enhancing technologies**
>
> Privacy-enhancing technologies (“PETs”) for AI, as well as data minimizing methods such as de-identification and aggregation for certain model outputs, can support design for privacy- enhanced AI systems.

**P071 — verdict (same / different / uncertain):** ______

**P071 — note:** ______

---

## P072

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **range of system validity**
>
> Possible actions may include: • alerting other relevant AI actors before action, • requesting subsequent human review of action, • alerting downstream users and stakeholder that the system is operating outside it’s defined validity limits, • tracking and mitigating possible error propagation • action logging • Log input data and relevant system configuration information whenever there is an attempt to use the system beyond its well-defined range of system validity.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **error propagation**
>
> Possible actions may include: • alerting other relevant AI actors before action, • requesting subsequent human review of action, • alerting downstream users and stakeholder that the system is operating outside it’s defined validity limits, • tracking and mitigating possible error propagation • action logging • Log input data and relevant system configuration information whenever there is an attempt to use the system beyond its well-defined range of system validity.

**P072 — verdict (same / different / uncertain):** ______

**P072 — note:** ______

---

## P073

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **subject protection**
>
> MEASURE 2.2 Evaluations involving human subjects meet applicable requirements (including human subject protection) and are representative of the relevant population.

**Node B** — `Concept` · *NIST Generative AI Profile (AI 600-1)* · arm `org_maturity`

> **human subject protection**
>
> 30 MEASURE 2.2: Evaluations involving human subjects meet applicable requirements (including human subject protection) and are representative of the relevant population.

**P073 — verdict (same / different / uncertain):** ______

**P073 — note:** ______

---

## P074

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **diversity, equity, and inclusion**
>
> To extend the benefits of diversity, equity, and inclusion to both the users and AI actors, it is recommended that teams are composed of a diverse group of individuals who reflect a range of backgrounds, perspectives and expertise.

**Node B** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **diverse team**
>
> Having a diverse team contributes to more broad and open sharing of ideas and assumptions about the purpose and function of the technology being designed and developed – making these implicit aspects more explicit.

**P074 — verdict (same / different / uncertain):** ______

**P074 — note:** ______

---

## P075

**Node A** — `Concept` · *How an AI-ready National Data Library would help UK science* · arm `publication_actionability`

> **Governance of data**
>
> Governance of data can look different across different organisations and diverse types of data and require different mechanisms to ensure that data is accessed, used, and shared in the right way.

**Node B** — `Concept` · *AI-Readiness for Official Data and Statistics (UN Statistical Commission side event)* · arm `publication_actionability`

> **data governance**
>
> This session will discuss AI readiness from a data governance perspective

**P075 — verdict (same / different / uncertain):** ______

**P075 — note:** ______

---

## P076

**Node A** — `Standard` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMx 2.0 Technical Specifications**
>
> **SDMx 2.0 Technical Specifications** SDMx Technical Standards Version 2.0 provide the technical specifications for the exchange of data and metadata based on a common information model.

**Node B** — `Standard` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMX Technical Standards**
>
> SDMx Technical Standards Version 2.0 provide the technical specifications for the exchange of data and metadata based on a common information model.

**P076 — verdict (same / different / uncertain):** ______

**P076 — note:** ______

---

## P077

**Node A** — `Standard` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMx 3.1 Technical Specifications**
>
> **SDMx 3.1 Technical Specifications** The SDMx 3.1 Technical Specifications were released in May 2025.

**Node B** — `Standard` · *SDMX Standards (sdmx.org standards page)* · arm `publication_actionability`

> **SDMX Technical Specifications**
>
> The SDMx 3.1 Technical Specifications were released in May 2025.

**P077 — verdict (same / different / uncertain):** ______

**P077 — note:** ______

---

## P078

**Node A** — `Concept` · *Communicating uncertainty about facts, numbers and science* · arm `publication_actionability`

> **the object about which there is uncertainty**
>
> Factors related to what is being communicated are (§3): — the object about which there is uncertainty, in terms of facts, numbers or scientific models and hypotheses — the source of the uncertainty, as in the reasons for the lack of knowledge — the level of the uncertainty communicated: from direct uncertainty about a fact, to the indirect uncertainty or lack of confidence in the underlying science — the magnitude of the uncertainty, from a small lack of precision to a substantial degree of ignorance.

**Node B** — `Concept` · *Communicating uncertainty about facts, numbers and science* · arm `publication_actionability`

> **communication of uncertainty**
>
> The individual elements of it are those factors which we believe (either through direct empirical evidence or suggestive evidence from other fields) could affect the communication of uncertainty and thus should be considered individually.

**P078 — verdict (same / different / uncertain):** ______

**P078 — note:** ______

---

## P079

**Node A** — `Concept` · *State Fidelity Validity for Reproducible AI Systems and Workflows* · arm `training_data_readiness`

> **validity construct**
>
> It is a validity construct: a structured way of asking whether the inferential claims a pipeline makes are warranted by the actual history of its operations.

**Node B** — `Concept` · *State Fidelity Validity for Reproducible AI Systems and Workflows* · arm `training_data_readiness`

> **construct validity**
>
> Second, there is no validated instrument for measuring SFV itself, and there may never be one; the history of construct validity (Cronbach and Meehl 1955) shows that defining the right questions outlasts every attempt to reduce them to a single score.

**P079 — verdict (same / different / uncertain):** ______

**P079 — note:** ______

---

## P080

**Node A** — `Concept` · *Fostering AI-Readiness and Responsible Redistribution of Official Statistics* · arm `publication_actionability`

> **Metadata mapping**
>
> • Metadata mapping.

**Node B** — `Concept` · *OMB M-23-22: Delivering a Digital-First Public Experience* · arm `publication_actionability`

> **Descriptive metadata**
>
> contain rich, descriptive metadata; feature machine-readable content to the extent practicable; and follow search engine optimization (SEO) practices

**P080 — verdict (same / different / uncertain):** ______

**P080 — note:** ______

---

## P081

**Node A** — `Concept` · *Arm AI Readiness Index* · arm `org_maturity`

> **transparency**
>
> transparency

**Node B** — `Concept` · *Webb: NIST x FCSM Crosswalk (Data Quality <-> AI Trustworthiness)* · arm `publication_actionability`

> **Transparency**
>
> Transparency Open documentation of methods, sources, and limitations

**P081 — verdict (same / different / uncertain):** ______

**P081 — note:** ______

---

## P082

**Node A** — `Concept` · *Croissant: A Metadata Format for ML-Ready Datasets* · arm `publication_actionability`

> **Croissant**
>
> r e c t a n g l e (( x1 , y1 , x1 + w , y1 + h ) , outline =(0 , 255 , 0) , width =2) 95 display ( image ) 7.2 Croissant Health Metrics Croissant Health is a framework to automatically scrape and compute metrics about Croissant from online dataset repositories.

**Node B** — `Standard` · *A framework for AI-ready data* · arm `training_data_readiness`

> **Croissant**
>
> Each DOI landing page additionally carries a block of DataCite ‑ JSON metadata, but there is no Croissant or JSON ‑ LD metadata bundle.

**P082 — verdict (same / different / uncertain):** ______

**P082 — note:** ______

---

## P083

**Node A** — `Standard` · *Croissant: A Metadata Format for ML-Ready Datasets* · arm `publication_actionability`

> **Croissant**
>
> During our user study, we instructed annotators to use the Croissant specifications [5, 27] and prompted them afterwards with questions.

**Node B** — `Standard` · *A framework for AI-ready data* · arm `training_data_readiness`

> **Croissant**
>
> Each DOI landing page additionally carries a block of DataCite ‑ JSON metadata, but there is no Croissant or JSON ‑ LD metadata bundle.

**P083 — verdict (same / different / uncertain):** ______

**P083 — note:** ______

---

## P084

**Node A** — `Concept` · *America's DataHub RFS Topic MLMU-25: Measuring LLM Understanding of Federal Statistical Data* · arm `publication_actionability`

> **Machine-readability**
>
> machine-readability

**Node B** — `Concept` · *A framework for AI-ready data* · arm `training_data_readiness`

> **machine-readability**
>
> machine-readability 39 .

**P084 — verdict (same / different / uncertain):** ______

**P084 — note:** ______

---

## P085

**Node A** — `Concept` · *AI and Open Government Data Assets Request for Information (RFI)* · arm `org_maturity`

> **reliability**
>
> transparency in data sourcing and processing methods to enhance trust and reliability?

**Node B** — `Concept` · *Statistics Canada Quality Guidelines, Sixth Edition* · arm `publication_actionability`

> **reliability**
>
> Related to accuracy, reliability reflects the degree to which statistical information, consistently over time, correctly describes the phenomena it was designed to measure.

**P085 — verdict (same / different / uncertain):** ______

**P085 — note:** ______

---

## P086

**Node A** — `Concept` · *GAO AI Accountability Framework (Ariga testimony)* · arm `org_maturity`

> **Bias**
>
> Bias: Identify potential biases, inequities, and other societal concerns resulting from the AI system.

**Node B** — `Concept` · *AI-ready data action plan* · arm `publication_actionability`

> **Bias**
>
> - **Bias as clinical safety:** Bias and representativeness in training data are clinical safety issues. NHS stresses the need for demographic coverage and ongoing monitoring.

**P086 — verdict (same / different / uncertain):** ______

**P086 — note:** ______

---

## P087

**Node A** — `Concept` · *M-24-18: Advancing the Responsible Acquisition of AI in Government* · arm `org_maturity`

> **interoperability**
>
> interoperability

**Node B** — `Concept` · *SDMX 3.0 Technical Specifications, Section 1: Framework for SDMX Technical Standards* · arm `publication_actionability`

> **interoperability**
>
> The SDMX Information Model works equally well with any statistical 802 concept, but to encourage interoperability, it is also necessary to standardize and harmonize 803 the use of specific concepts and terminology.

**P087 — verdict (same / different / uncertain):** ______

**P087 — note:** ______

---

## P088

**Node A** — `Concept` · *M-24-18: Advancing the Responsible Acquisition of AI in Government* · arm `org_maturity`

> **interoperability**
>
> interoperability

**Node B** — `Concept` · *The FAIR Guiding Principles for scientific data management and stewardship* · arm `publication_actionability`

> **Interoperability**
>
> This article describes four foundational principles —Findability, Accessibility, Interoperability, and Reusability—that serve to guide data producers and publishers as they navigate around these obstacles, thereby helping to maximize the added-value gained by contemporary, formal scholarly digital publishing.

**P088 — verdict (same / different / uncertain):** ______

**P088 — note:** ______

---

## P089

**Node A** — `Concept` · *MITRE AI Maturity Model* · arm `org_maturity`

> **Accessibility**
>
> Accessibility

**Node B** — `Concept` · *Statistical Policy Working Paper 46: Data Quality Assessment Tool for Administrative Data* · arm `publication_actionability`

> **Accessibility**
>
> Accessibility refers to the ease with which the data file extract can be obtained from the administrative agency.

**P089 — verdict (same / different / uncertain):** ______

**P089 — note:** ______

---

## P090

**Node A** — `Concept` · *MITRE AI Maturity Model* · arm `org_maturity`

> **Accessibility**
>
> Accessibility

**Node B** — `Concept` · *The FAIR Guiding Principles for scientific data management and stewardship* · arm `publication_actionability`

> **Accessibility**
>
> This article describes four foundational principles —Findability, Accessibility, Interoperability, and Reusability—that serve to guide data producers and publishers as they navigate around these obstacles, thereby helping to maximize the added-value gained by contemporary, formal scholarly digital publishing.

**P090 — verdict (same / different / uncertain):** ______

**P090 — note:** ______

---

## P091

**Node A** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **accuracy**
>
> accuracy

**Node B** — `Concept` · *Understanding and Using American Community Survey Data: What All Data Users Need to Know* · arm `publication_actionability`

> **Accuracy**
>
> Accuracy. One of four key dimensions of survey qual- ity.

**P091 — verdict (same / different / uncertain):** ______

**P091 — note:** ______

---

## P092

**Node A** — `Concept` · *NIST AI Risk Management Framework (AI RMF)* · arm `org_maturity`

> **bias**
>
> bias

**Node B** — `Concept` · *AI-ready data action plan* · arm `publication_actionability`

> **Bias**
>
> - **Bias as clinical safety:** Bias and representativeness in training data are clinical safety issues. NHS stresses the need for demographic coverage and ongoing monitoring.

**P092 — verdict (same / different / uncertain):** ______

**P092 — note:** ______

---

## P093

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **privacy-enhancing techniques**
>
> • Use privacy-enhancing techniques such as differential privacy, when publicly sharing dataset information.

**Node B** — `Concept` · *Foundations for Evidence-Based Policymaking Act of 2018 (Evidence Act)* · arm `publication_actionability`

> **Privacy enhancing techniques**
>
> privacy enhancing techniques

**P093 — verdict (same / different / uncertain):** ______

**P093 — note:** ______

---

## P094

**Node A** — `Concept` · *NIST AI RMF Playbook* · arm `org_maturity`

> **Documentation**
>
> Documentation enables repeatability and consistency, and can enhance AI risk management decisions.

**Node B** — `Concept` · *FCSM 19-01: Transparent Reporting for Integrated Data Quality* · arm `publication_actionability`

> **documentation**
>
> FoodAPS users had relatively high ratings for quality of documentation.

**P094 — verdict (same / different / uncertain):** ______

**P094 — note:** ______

---

## P095

**Node A** — `Standard` · *pySHACL README* · arm `publication_actionability`

> **RDF**
>
> [RDF](https://www.w3.org/2001/sw/wiki/RDF)

**Node B** — `Standard` · *A framework for AI-ready data* · arm `training_data_readiness`

> **RDF**
>
> No Parquet or JSON ‑ LD derivatives are provided, so users targeting AI pipelines may have to convert the RDF graph to a tabular or embedding ‑ friendly format for greater ease.

**P095 — verdict (same / different / uncertain):** ______

**P095 — note:** ______

---

## P096

**Node A** — `Concept` · *schema.org: SoftwareApplication* · arm `publication_actionability`

> **structured data**
>
> the structured data is derived automatically from existing published content

**Node B** — `Concept` · *Data Readiness for AI: A 360-Degree Survey* · arm `training_data_readiness`

> **structured data**
>
> While structured data poses unique challenges regarding standardization, interpretability, and sensitivity, unstructured datasets present additional complexities due to their diverse formats, varying modalities, and contextual nuances.

**P096 — verdict (same / different / uncertain):** ______

**P096 — note:** ______

---

## P097

**Node A** — `Concept` · *Technology Readiness Levels for Machine Learning Systems (MLTRL)* · arm `org_maturity`

> **epistemic uncertainty**
>
> epistemic uncertainty, accounting for uncertainty in the model itself

**Node B** — `Concept` · *Communicating uncertainty about facts, numbers and science* · arm `publication_actionability`

> **epistemic uncertainty**
>
> Overall, it appears that more research is needed in order to gain a better understanding of the effects of epistemic uncertainty about science, facts and numbers on people’s affective and emotional reactions.

**P097 — verdict (same / different / uncertain):** ______

**P097 — note:** ______

---

## P098

**Node A** — `Concept` · *Technology Readiness Levels for Machine Learning Systems (MLTRL)* · arm `org_maturity`

> **epistemic uncertainty**
>
> epistemic uncertainty, accounting for uncertainty in the model itself

**Node B** — `Concept` · *Communicating uncertainty about facts, numbers and science* · arm `publication_actionability`

> **epistemic uncertainty**
>
> Until then, our best advice to both researchers and practitioners is summarized in boxes 5 a and 5 b. We hope this structured approach will aid people to communicate the epistemic uncertainty that exists about facts, numbers and science confidently and unapologetically—an approach we like to call ‘muscular uncertainty’.

**P098 — verdict (same / different / uncertain):** ______

**P098 — note:** ______

---

## P099

**Node A** — `Concept` · *Technology Readiness Levels for Machine Learning Systems (MLTRL)* · arm `org_maturity`

> **sensitivity analysis**
>
> sensitivity analysis

**Node B** — `Concept` · *FCSM 20-04: A Framework for Data Quality* · arm `publication_actionability`

> **Sensitivity analysis**
>
> Sensitivity analysis (discussed in more detail below in section B.4) is commonly used to evaluate statistical models, par - ticularly those that rely on unverifable assumptions (Goldsmith 2015).

**P099 — verdict (same / different / uncertain):** ______

**P099 — note:** ______

---

## P100

**Node A** — `Concept` · *Technology Readiness Levels for Machine Learning Systems (MLTRL)* · arm `org_maturity`

> **synthetic data**
>
> the ability to generate synthetic datasets for anomaly detection can accelerate the level 6-9 pipeline

**Node B** — `Concept` · *AI-ready data action plan* · arm `publication_actionability`

> **Synthetic data**
>
> - **Synthetic data:** DWP uses synthetic data to accelerate AI readiness, especially when access to real data is restricted.

**P100 — verdict (same / different / uncertain):** ______

**P100 — note:** ______

---

