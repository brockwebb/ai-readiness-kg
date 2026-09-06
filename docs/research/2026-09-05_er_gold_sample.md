# Entity-resolution gold sample — 100 pairs, LABELLED

**Labelled by `claude-fable-5-1`** — an independent model rater that took no part in any pipeline decision on these pairs: the vocabulary seed, the alias-first links, the clerical-band judgments and the homograph scores were all `claude-opus-5` or deterministic code. One pair per call, hermetic empty cwd, no repo access, and the pair block below is all the rater saw — no cosine, no vocabulary term, no stratum, no pipeline decision. Raw exchanges under `assessment/evidence/er_gold/`. **Limitation, stated where the numbers are:** a same-family rater bounds correctness RELATIVE TO THAT RATER, not to ground truth (DD-045 addendum-01). Task `cc_tasks/2026-09-05_er_gold_fable_labels_and_score.md`. 100 of 100 pairs answered.

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

**P001 — verdict (same / different / uncertain):** same

**P001 — note:** [claude-fable-5-1, confidence 0.85] Node A names "traditional data quality parameters" as the generic data-quality dimension and Node B's bare label "Data quality" denotes that same generic concept, with no narrowing qualifier in either span.

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

**P002 — verdict (same / different / uncertain):** same

**P002 — note:** [claude-fable-5-1, confidence 0.75] Both spans use the identical general concept "data quality" as an overarching property of data — Node A's "traditional data quality parameters" and Node B's "the evaluation of data quality" — with neither narrowing it to a species, even though AIDRIN extends it with AI-readiness metrics.

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

**P003 — verdict (same / different / uncertain):** same

**P003 — note:** [claude-fable-5-1, confidence 0.9] Both spans name the Bing search engine as the platform — "access information about their website on Bing search and index" and "10.4 million distinct Bing" (results/queries on Bing) — the same web search platform referenced twice.

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

**P004 — verdict (same / different / uncertain):** same

**P004 — note:** [claude-fable-5-1, confidence 0.92] Both spans name the identical statistical concept "Nonsampling error" — A's "Nonsampling error is extremely difficult, if not impos- sible, to measure directly" and B's "potential nonsampling errors (e.g., nonresponse, coverage, processing, and measurement)" refer to the same class of survey error, differing only in that B enumerates its components.

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

**P005 — verdict (same / different / uncertain):** same

**P005 — note:** [claude-fable-5-1, confidence 0.85] Node A's span is the bare label "Metadata" and Node B defines "Metadata is any description of a resource"; both name the generic concept of metadata with no narrowing qualifier in either span.

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

**P006 — verdict (same / different / uncertain):** same

**P006 — note:** [claude-fable-5-1, confidence 0.9] Node A's "potential nonsampling errors (e.g., nonresponse, coverage, processing, and measurement)" and Node B's "traditional typology that distinguishes sampling from nonsampling errors" both name the standard survey-methodology category of error that is not attributable to sampling, with neither span narrowing it to a subtype.

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

**P007 — verdict (same / different / uncertain):** same

**P007 — note:** [claude-fable-5-1, confidence 0.95] Both spans name the same product, "AI- powered systems such as ChatGPT, Perplexity" in A and "the free-tier versions of ChatGPT (GPT-4.1)" in B, and specifying a version or tier does not make B a different platform.

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

**P008 — verdict (same / different / uncertain):** same

**P008 — note:** [claude-fable-5-1, confidence 0.8] Both spans use "accuracy" in the same general data-quality sense, Node A as "accuracy and relevancy of LLM responses" and Node B as "threats to the accuracy and reliability of these crowdsourced data," differing only in the object measured rather than in the concept itself.

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

**P009 — verdict (same / different / uncertain):** same

**P009 — note:** [claude-fable-5-1, confidence 0.85] Both spans name the data quality dimension "relevance" — Node A's "limitations can have effects on relevance" and Node B's "Relevance Fitness for user needs" — the latter being the FCSM definition of the same dimension Node A discusses.

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

**P010 — verdict (same / different / uncertain):** same

**P010 — note:** [claude-fable-5-1, confidence 0.95] Both spans name the identical platform "Google Search" — A's "appearing in Google Search results" and B's "how they are performing on Google Search" both refer to Google's web search engine as a platform, not a narrower species.

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

**P011 — verdict (same / different / uncertain):** same

**P011 — note:** [claude-fable-5-1, confidence 0.8] Node A's "Metadata means" and Node B's "metadata," both name the same general concept of metadata (data describing data) with no narrowing qualifier in either span, so a reader counting distinct concepts would count one.

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

**P012 — verdict (same / different / uncertain):** same

**P012 — note:** [claude-fable-5-1, confidence 0.7] Node A defines the generic concept "Dataset : A collection of data points or items reflecting the results of such activities as measuring, reporting, collecting..." and Node B is the schema.org type "Instances of [Dataset](https://schema.org/Dataset)" that Croissant itself builds on, so both name the one general notion of a dataset rather than a narrower Croissant-specific profile.

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

**P013 — verdict (same / different / uncertain):** same

**P013 — note:** [claude-fable-5-1, confidence 0.85] Node A "monitor AI risk and related impacts" and Node B "Responses to the AI risks deemed high priority" both denote the AI RMF's general concept of AI risk, differing only in singular/plural surface form.

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

**P014 — verdict (same / different / uncertain):** same

**P014 — note:** [claude-fable-5-1, confidence 0.85] Both spans refer to tracking configurations of human and AI working together — "tracking metrics for ... human-AI configurations" in the AI RMF and "regular tracking of human-AI teaming configurations" in the Playbook, where "teaming" merely makes explicit what "human-AI configurations" already denotes, and the Playbook is the companion document elaborating the same RMF measure.

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

**P015 — verdict (same / different / uncertain):** same

**P015 — note:** [claude-fable-5-1, confidence 0.97] Both spans name the identical document "GAO-21-519SP: AI Accountability Framework for Federal Agencies & Other Entities" (A) and "GAO-21-519SP: AI Accountability Framework for Federal Agencies & Other Entities" (B), differing only by the "AI Transparency Resources" prefix in A.

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

**P016 — verdict (same / different / uncertain):** same

**P016 — note:** [claude-fable-5-1, confidence 0.85] Both spans use "misinformation" as the same generic concept of false or misleading information, Node A in "potential misinformation" within GAI output and Node B in "potential abuse and misinformation" within documentation and data, with no narrowing qualifier in either that would make one a species of the other.

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

**P017 — verdict (same / different / uncertain):** same

**P017 — note:** [claude-fable-5-1, confidence 0.9] Both spans name the same web standard, "robots.txt" — Node A's "allowing `PerplexityBot` in your site's `robots.txt` file" and Node B's "more than one Sitemap file per robots.txt file" are two documents referring to one and the same robots.txt file convention, not two distinct standards.

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

**P018 — verdict (same / different / uncertain):** uncertain

**P018 — note:** [claude-fable-5-1, confidence 0.5] Both spans name only "Google", but A ("Google - July 2026") reads as a dated data catalog release while B ("Based on monthly aggregations from Google's web index") reads as a software application or index, and neither span identifies which specific Google product is meant.

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

**P019 — verdict (same / different / uncertain):** same

**P019 — note:** [claude-fable-5-1, confidence 0.8] Both spans name the identical concept "data readiness" — Node A "considers data readiness and availability" of data for ML systems and Node B "whether available data is suitable for AI capabilities" — the same notion of data being fit for an AI/ML use, differing only in depth of definition, not in referent.

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

**P020 — verdict (same / different / uncertain):** same

**P020 — note:** [claude-fable-5-1, confidence 0.85] Both spans name the same referent, the "FAIR principles" (findable, accessible, interoperable, reusable) — Node A describes an "approach [that] aligns with FAIR principles" and Node B describes how "The FAIR principles can equally be applied to these non-data assets"; Node B's label is simply the title of the paper that defined them, not a narrower or different thing.

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

**P021 — verdict (same / different / uncertain):** same

**P021 — note:** [claude-fable-5-1, confidence 0.85] Node A's "AI Data Readiness" and Node B's "Data Readiness for AI" are word-order variants of the same concept, and B's note that it "lacks a standard definition and is still evolving" describes the shared concept rather than a narrower species of it.

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

**P022 — verdict (same / different / uncertain):** same

**P022 — note:** [claude-fable-5-1, confidence 0.75] Node A's "Bias and fairness in AI" ("free from bias") and Node B's "Fairness in AI" defined as "concerns for equality and equity by addressing issues such as harmful bias" both denote the single fairness-with-bias-managed property of an AI system, not a narrower species of it.

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

**P023 — verdict (same / different / uncertain):** same

**P023 — note:** [claude-fable-5-1, confidence 0.97] Node A's "Public Use Microdata Areas (PUMAs)" and Node B's "Public Use Microdata Areas" are the identical Census geography, with A merely adding the acronym while B describes the same units meeting "the 65,000-population threshold".

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

**P024 — verdict (same / different / uncertain):** same

**P024 — note:** [claude-fable-5-1, confidence 0.95] Node A's "AI Risk Management Framework (NIST AI 100–1)" and Node B's "NIST AI Risk Management Framework" both name the single NIST document AI 100-1, with no narrowing qualifier in either span.

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

**P025 — verdict (same / different / uncertain):** same

**P025 — note:** [claude-fable-5-1, confidence 0.95] Both spans open with the identical sentence "The methodology for State Safety Data Quality (SSDQ) was developed by the FMCSA to", so Node A's "State Safety Data Quality (SSDQ) methodology" and Node B's "State Safety Data Quality" are the same FMCSA instrument named with and without the "methodology" suffix.

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

**P026 — verdict (same / different / uncertain):** same

**P026 — note:** [claude-fable-5-1, confidence 0.95] Node A's "FCSM Framework for Data Quality" and Node B's "the FCSM Framework for Data Quality serves as a tool" both name the single FCSM-issued framework, with the newer publication referencing rather than defining a new one.

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

**P027 — verdict (same / different / uncertain):** same

**P027 — note:** [claude-fable-5-1, confidence 0.9] Node A's "four-part taxonomy of metrics for human–AI onboarding" from Figure 1 is the same proposal as Node B's Section 2.3 "we propose a taxonomy of metrics" for "Human–AI Onboarding & Decision-Making" in the same paper, with A merely adding the "four-part" detail.

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

**P028 — verdict (same / different / uncertain):** same

**P028 — note:** [claude-fable-5-1, confidence 0.99] Both spans are the identical heading "sitemap.xml" with the identical definition "a list of all the indexable human-readable information available on a site" from the same source, so they denote one thing.

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

**P029 — verdict (same / different / uncertain):** same

**P029 — note:** [claude-fable-5-1, confidence 0.99] Both spans are the identical "sitemap.xml" heading with the identical definition "a list of all the indexable human-readable information available on a site" from the same document, so they name one thing twice.

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

**P030 — verdict (same / different / uncertain):** same

**P030 — note:** [claude-fable-5-1, confidence 0.98] Both spans name the identical publication, Node A "Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST Publication AI 100-1" and Node B "NIST AI 100-1 Artificial Intelligence Risk Management Framework (AI RMF 1.0)", differing only in word order.

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

**P031 — verdict (same / different / uncertain):** same

**P031 — note:** [claude-fable-5-1, confidence 0.75] Node A's "k-anonymity metrics, l-diversity, t-closeness" and Node B's "k-anonymity, l-diversity, t-closeness" both name the identical privacy-model triple, and "k-anonymity metrics" is not a distinct narrower entity but a surface variant of "k-anonymity" as a privacy metric.

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

**P032 — verdict (same / different / uncertain):** same

**P032 — note:** [claude-fable-5-1, confidence 0.95] Node A's heading "Model AI Governance Framework Assessment" is a truncated label for the identical bullet "WEF Model AI Governance Framework Assessment 2020" that also serves as Node B's heading, so both denote the single WEF 2020 assessment instrument.

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

**P033 — verdict (same / different / uncertain):** same

**P033 — note:** [claude-fable-5-1, confidence 0.95] Node A's "AI Risk Management Framework (AI RMF 1.0)" and Node B's "NIST AI Risk Management Framework (AI RMF)" both name the single NIST AI RMF document, with A merely adding the version number and B the publisher prefix.

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

**P034 — verdict (same / different / uncertain):** same

**P034 — note:** [claude-fable-5-1, confidence 0.85] Both spans name the same phenomenon in the same paper—"an algorithmic overgeneralization tendency" (LLM summaries producing generalized conclusions) and "increasing overall algorithmic overgeneralizations by up to 15%"—differing only in singular-abstract vs. plural-count phrasing of one concept.

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

**P035 — verdict (same / different / uncertain):** same

**P035 — note:** [claude-fable-5-1, confidence 0.97] Node A's "W3C DCAT (Data Catalog Vocabulary)" and Node B's "[W3C]'s [Data Catalog Vocabulary (DCAT) format]" both name the single W3C DCAT standard, with the same publisher and identical expansion of the acronym.

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

**P036 — verdict (same / different / uncertain):** same

**P036 — note:** [claude-fable-5-1, confidence 0.92] Node A's "Statistical Data and Metadata Exchange (SDMX)" is the expanded name of the standard that Node B's "Supporting the implementation of SDMX" refers to as a "common data exchange standard", so both denote the single SDMX standard despite the Concept/Standard type split.

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

**P037 — verdict (same / different / uncertain):** same

**P037 — note:** [claude-fable-5-1, confidence 0.92] Node A's "SDMX (Statistical Data and Metadata eXchange)" standard for "the exchange of statistical data and metadata" is the same standard Node B names as a "data exchange standards such as SDMX", with no narrowing qualifier in either span.

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

**P038 — verdict (same / different / uncertain):** same

**P038 — note:** [claude-fable-5-1, confidence 0.9] Both spans point at the identical referent, Node A asking whether race questions use "the current race and ethnicity categories defined by the Office of Management and Budget (OMB)" and Node B giving the same sentence as its sole example ("Do questions asked about race use the current race and ethnicity categories defined by the Office of Management and Budget (OMB)?"), so the shorter label "race and ethnicity categories" is a name for the same OMB categories rather than a broader genus.

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

**P039 — verdict (same / different / uncertain):** same

**P039 — note:** [claude-fable-5-1, confidence 0.85] "description of a data access service to be included in a catalog" refers to the DCAT class defined under "6.9 Class: Data Service" (dcat:DataService), the same thing under two surface forms.

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

**P040 — verdict (same / different / uncertain):** same

**P040 — note:** [claude-fable-5-1, confidence 0.98] Span A's "NIST AI RMF 1.0 (Artificial Intelligence Risk Management Framework)" and Span B's "Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST Publication AI 100-1" both name the identical NIST publication and version, differing only in word order and the added document number.

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

**P041 — verdict (same / different / uncertain):** different

**P041 — note:** [claude-fable-5-1, confidence 0.95] Node A's "content visibility" is the outcome metric GEO methods "sig- nificanlty improve," whereas Node B's "SEO methods" are the rival optimization techniques GEO changes bear "some resemblance with" — a measured effect versus a class of methods, not one thing named twice.

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

**P042 — verdict (same / different / uncertain):** different

**P042 — note:** [claude-fable-5-1, confidence 0.98] Span A names "German Credit (SGC) dataset" as one of "two case studies" alongside TCGA-LUAD, while span B names the "TCGA-LUAD Case Study dataset" — two distinct datasets the paper explicitly enumerates separately.

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

**P043 — verdict (same / different / uncertain):** different

**P043 — note:** [claude-fable-5-1, confidence 0.95] Node A's span is titled "Pandas" and only mentions Matplotlib as a separate library that "enhances AIDRIN with visualization capabilities", while Node B's span denotes "plotting libraries like matplotlib" itself, so the two nodes name distinct libraries.

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

**P044 — verdict (same / different / uncertain):** different

**P044 — note:** [claude-fable-5-1, confidence 0.97] Node A names "NUM to explicitly request the inclusion of numeric values," a prompt the authors designed, while Node B names "GPT-4's performance," the model whose performance that prompt is meant to enhance.

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

**P045 — verdict (same / different / uncertain):** different

**P045 — note:** [claude-fable-5-1, confidence 0.95] Node A's span is about "numeric values" as an extraction target ("request the inclusion of numeric values"), whereas Node B's span denotes the model itself ("GPT-4 (OpenAI, 2023) is a multi-modal LM"), so a numeric-values concept and a language model are two distinct things.

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

**P046 — verdict (same / different / uncertain):** different

**P046 — note:** [claude-fable-5-1, confidence 0.9] Node A is the calculation procedure for the "Product of Two Estimates" ("multiplying a published count by a published percentage"), while Node B is the data product "ACS multiyear estimates for the two time periods of 2005–2009 and 2010–2014", so the one is a method and the other is the estimate type it may be applied to.

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

**P047 — verdict (same / different / uncertain):** different

**P047 — note:** [claude-fable-5-1, confidence 0.6] Node A is Cisco's self-service "AI Readiness Assessment" tool while Node B is the survey-based annual "AI Readiness Index" report; related Cisco artifacts built on the same framework, but a self-assessment instrument and a published index are distinct instruments.

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

**P048 — verdict (same / different / uncertain):** same

**P048 — note:** [claude-fable-5-1, confidence 0.97] Both spans carry the identical label "The /llms.txt file (llmstxt.org)" and the identical sentence "We propose adding a `/llms.txt` markdown file to websites to provide LLM-friendly content" — Node A's heading "LLM-friendly content" and Node B's heading "llms.txt" are two headings over the same passage describing one proposed file.

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

**P049 — verdict (same / different / uncertain):** different

**P049 — note:** [claude-fable-5-1, confidence 0.65] Node A resolves to a specific versioned profile ("W3C Data Catalog Vocabulary Version 3, known as the DCAT-US 3.0") while Node B names the generic unversioned W3C standard ("Data Catalog Vocabulary (DCAT) format"), so A is a narrower species of B rather than the same thing.

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

**P050 — verdict (same / different / uncertain):** different

**P050 — note:** [claude-fable-5-1, confidence 0.95] Span A names one characteristic, "fair with their harmful biases managed", which is listed as one item among "the characteristics of trustworthy AI systems", while span B names the whole category "trustworthy AI systems", so A is a part/attribute of B rather than the same thing.

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

**P051 — verdict (same / different / uncertain):** different

**P051 — note:** [claude-fable-5-1, confidence 0.97] Node A names a human role, "AI system overseers," while Node B names the activities that role can "enhance," namely "AI risk management activities"; an actor and the activity it improves are two distinct referents.

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

**P052 — verdict (same / different / uncertain):** different

**P052 — note:** [claude-fable-5-1, confidence 0.75] "diverse workforce" names the organizational population as a state, while "team diversity" names a property of teams; the span treats them as distinct things, with "team diversity and inclusion" being what gets overridden and "the broader values of a diverse workforce" being what it conflicts with.

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

**P053 — verdict (same / different / uncertain):** different

**P053 — note:** [claude-fable-5-1, confidence 0.8] Node A names the activity being governed, "AI system oversight and governance", while Node B names the broader practice it feeds into, "can enhance AI risk management activities", so oversight/governance is a component of, not identical to, risk management activities.

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

**P054 — verdict (same / different / uncertain):** different

**P054 — note:** [claude-fable-5-1, confidence 0.85] Node A names a set of methods, "explainable AI (XAI) techniques (e.g., analysis of embeddings, ... gradient-based attributions ...)", while Node B names the field itself, "XAI is a special research direction in AI", so A is a narrower species of B.

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

**P055 — verdict (same / different / uncertain):** different

**P055 — note:** [claude-fable-5-1, confidence 0.97] Node A names "United States" (the nation, "receives approximately 81% of its energy from fossil fuel") while Node B names "California" ("the nation's most populous state"), a state within it — part is not whole.

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

**P056 — verdict (same / different / uncertain):** different

**P056 — note:** [claude-fable-5-1, confidence 0.6] Node A names one version, "SDMx 1.0 Technical Specifications", while Node B is titled with the family name "SDMX Standards" (which spans versions beyond 1.0), so B is the genus and A a species of it, even though B's body reuses the 1.0 sentence "The SDMx Standards Version 1.0 provide the technical specification".

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

**P057 — verdict (same / different / uncertain):** different

**P057 — note:** [claude-fable-5-1, confidence 0.97] Span A's "deficiencies in data manipulation (5.9/10)" and span B's "visual design (6.5/10)" are two separately scored capability categories in the same sentence, so they are distinct concepts rather than one thing named twice.

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

**P058 — verdict (same / different / uncertain):** different

**P058 — note:** [claude-fable-5-1, confidence 0.97] "MNLI data" is a training dataset used for pre fine-tuning models, whereas "numerical claim" is defined as a statement with "more than one quantitative segment" — a dataset and a claim type are distinct things.

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

**P059 — verdict (same / different / uncertain):** different

**P059 — note:** [claude-fable-5-1, confidence 0.9] Node A is the "conformance degree to a stated quality standard" (an outcome, e.g. conformant/not conformant), whereas Node B is the "result of conformance test" (the test procedure itself), so the degree is the result of the test, not the test.

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

**P060 — verdict (same / different / uncertain):** different

**P060 — note:** [claude-fable-5-1, confidence 0.85] Span A's heading and text name "The DCAT-2014 vocabulary [VOCAB-DCAT-1] and DCAT 2 [VOCAB-DCAT-2]" (the earlier versions being extended), while Span B cites "Data Catalog Vocabulary (DCAT) – Version 3, W3C Recommendation, 2024", a distinct later version of the standard.

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

**P061 — verdict (same / different / uncertain):** different

**P061 — note:** [claude-fable-5-1, confidence 0.8] Node A's generic "national AI governance framework" is a type/category of framework, while Node B is a specific named instrument, "the Model AI Governance Framework, first introduced in 2019 and updated in 2020" (Singapore's), so a specific instance is not the same node as the generic class.

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

**P062 — verdict (same / different / uncertain):** different

**P062 — note:** [claude-fable-5-1, confidence 0.97] Node A is a plotting method for "the degree of generality of specific AI technologies on the x-axis vs the readiness level (the TRLs) on the y axis", while Node B is a dataset-assessment instrument with "criteria outlined in the AI-readiness Framework", so they are two distinct frameworks despite sharing the word "readiness".

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

**P063 — verdict (same / different / uncertain):** different

**P063 — note:** [claude-fable-5-1, confidence 0.97] Node A is the "UCI coherence score" proposed by "Newman et al." [99], while Node B is the "CV coherence score" [117] — two distinct, separately cited topic-coherence metrics (UCI is PMI-based, CV is NPMI/cosine-based), not one metric named twice.

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

**P064 — verdict (same / different / uncertain):** different

**P064 — note:** [claude-fable-5-1, confidence 0.85] "360-degree data readiness framework" is a survey-style framework from one paper, while "Data Readiness Levels" is a distinct named maturity-scale construct, so the spans name two different frameworks rather than one thing twice.

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

**P065 — verdict (same / different / uncertain):** same

**P065 — note:** [claude-fable-5-1, confidence 0.9] "Agency Inventory of AI Use Cases" and "AI use case inventory" both name the single OMB-mandated federal inventory of AI use cases, with M-24-10 explicitly carrying forward the EO 13960 inventory requirement.

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

**P066 — verdict (same / different / uncertain):** different

**P066 — note:** [claude-fable-5-1, confidence 0.85] Node A names the specific activity "Federal Government use of AI" while Node B names the general technology "artificial intelligence (AI)", so A is a narrower application-in-context of B rather than the same concept.

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

**P067 — verdict (same / different / uncertain):** same

**P067 — note:** [claude-fable-5-1, confidence 0.98] Node A's "Resource Description Framework (RDF)" and Node B's "the W3C RDF (Resource Description Framework) standard" both name the identical W3C standard, with the same expansion and acronym.

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

**P068 — verdict (same / different / uncertain):** same

**P068 — note:** [claude-fable-5-1, confidence 0.9] Node A's "honors robots.txt exclusion protocol" and Node B's "robots.txt lets automated tools know what access to a site is considered acceptable" both denote the single Robots Exclusion Protocol file, one named by protocol and one by filename.

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

**P069 — verdict (same / different / uncertain):** different

**P069 — note:** [claude-fable-5-1, confidence 0.8] Node A names a field of study, "interdisciplinary field of trustworthy and responsible AI", while Node B refers to the artifacts that field produces, "more trustworthy AI systems", so a discipline and the systems it aims to build are two distinct things.

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

**P070 — verdict (same / different / uncertain):** different

**P070 — note:** [claude-fable-5-1, confidence 0.97] Node A names "identification of incidents" while Node B names "information sharing"; they are two separate items in the same GOVERN 4.3 list ("AI testing, identification of incidents, and information sharing"), so they denote distinct organizational practices, not one thing named twice.

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

**P071 — verdict (same / different / uncertain):** different

**P071 — note:** [claude-fable-5-1, confidence 0.9] Span A names "data minimizing methods such as de-identification and aggregation" while Span B names "Privacy-enhancing technologies ("PETs") for AI", and the sentence lists them as coordinate items ("PETs ... as well as data minimizing methods"), so they are two distinct classes of technique rather than one thing named twice.

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

**P072 — verdict (same / different / uncertain):** different

**P072 — note:** [claude-fable-5-1, confidence 0.9] Node A names the boundary condition "beyond its well-defined range of system validity" while Node B names a consequence to mitigate, "tracking and mitigating possible error propagation"; both spans share identical context text but the head terms denote distinct things (an operating envelope versus a failure-cascade phenomenon).

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

**P073 — verdict (same / different / uncertain):** same

**P073 — note:** [claude-fable-5-1, confidence 0.9] Both spans quote the identical MEASURE 2.2 text "meet applicable requirements (including human subject protection)", and Node A's "subject protection" is merely a truncated surface form of Node B's "human subject protection" naming the same requirement.

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

**P074 — verdict (same / different / uncertain):** different

**P074 — note:** [claude-fable-5-1, confidence 0.85] Node A names the principle "diversity, equity, and inclusion" extended to users and AI actors, while Node B names the organizational means "a diverse team" that contributes to sharing of ideas, so the team is one instrument toward the broader DEI goal rather than the same thing.

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

**P075 — verdict (same / different / uncertain):** same

**P075 — note:** [claude-fable-5-1, confidence 0.85] Both spans name the general concept of data governance as a framework for how data is handled, with A saying "Governance of data ... require different mechanisms to ensure that data is accessed, used, and shared in the right way" and B saying "AI readiness from a data governance perspective," neither narrowing to a species.

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

**P076 — verdict (same / different / uncertain):** same

**P076 — note:** [claude-fable-5-1, confidence 0.9] Both spans describe the identical artifact — Node A's "SDMx 2.0 Technical Specifications... SDMx Technical Standards Version 2.0 provide the technical specifications for the exchange of data and metadata" and Node B's "SDMX Technical Standards... SDMx Technical Standards Version 2.0 provide the technical specifications for the exchange of data and metadata" share the same body text naming Version 2.0, so B's shorter title is a label for the same document rather than a broader genus.

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

**P077 — verdict (same / different / uncertain):** different

**P077 — note:** [claude-fable-5-1, confidence 0.6] Node A names a specific version, "SDMx 3.1 Technical Specifications", while Node B's label is the unversioned family "SDMX Technical Specifications", of which 3.1 is one release, so A is a species of B even though B's body happens to mention the 3.1 release.

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

**P078 — verdict (same / different / uncertain):** different

**P078 — note:** [claude-fable-5-1, confidence 0.85] Span A names "the object about which there is uncertainty", one factor within the framework, while Span B names "the communication of uncertainty" itself, the whole activity those factors affect, so they are a part and its whole rather than one thing.

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

**P079 — verdict (same / different / uncertain):** different

**P079 — note:** [claude-fable-5-1, confidence 0.8] Span A describes SFV as "a validity construct: a structured way of asking whether the inferential claims a pipeline makes are warranted," i.e. a specific proposed construct, whereas Span B invokes "the history of construct validity (Cronbach and Meehl 1955)," the general psychometric concept of whether a measure captures its intended construct, so one is an instance-level construct and the other is the field-level notion of validity.

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

**P080 — verdict (same / different / uncertain):** different

**P080 — note:** [claude-fable-5-1, confidence 0.8] "Metadata mapping" (Node A) names a crosswalk/alignment activity between metadata schemes, whereas "rich, descriptive metadata" (Node B) names a property of content that describes it for discovery and SEO, so they are distinct concepts rather than one thing named twice.

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

**P081 — verdict (same / different / uncertain):** same

**P081 — note:** [claude-fable-5-1, confidence 0.8] Node A is bare "transparency" and Node B is "Transparency Open documentation of methods, sources, and limitations" — the same general trustworthiness property named twice, with B merely glossing it rather than narrowing it.

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

**P082 — verdict (same / different / uncertain):** same

**P082 — note:** [claude-fable-5-1, confidence 0.85] Both spans refer to the Croissant ML dataset metadata format — Node A's "compute metrics about Croissant from online dataset repositories" and Node B's "no Croissant or JSON-LD metadata bundle" both use "Croissant" as the name of the same metadata standard, the label-type mismatch (Concept vs Standard) being an extraction artifact rather than a different referent.

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

**P083 — verdict (same / different / uncertain):** same

**P083 — note:** [claude-fable-5-1, confidence 0.95] Node A's "use the Croissant specifications" and Node B's "no Croissant or JSON-LD metadata bundle" both refer to the same Croissant ML dataset metadata format.

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

**P084 — verdict (same / different / uncertain):** same

**P084 — note:** [claude-fable-5-1, confidence 0.9] Both spans name the identical concept, "Machine-readability" in Node A and "machine-readability" in Node B, with no qualifier narrowing either to a species of the other.

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

**P085 — verdict (same / different / uncertain):** same

**P085 — note:** [claude-fable-5-1, confidence 0.7] Both nodes are the bare term "reliability" used as a data/statistical quality property, with span A invoking it as "trust and reliability" of data sourcing and span B defining it as "the degree to which statistical information, consistently over time, correctly describes the phenomena"; the RFI's undefined usage is a loose instance of the same quality-dimension concept rather than a distinct thing, though the RFI span is too thin to be certain.

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

**P086 — verdict (same / different / uncertain):** same

**P086 — note:** [claude-fable-5-1, confidence 0.7] Both spans name the concept "Bias" in an AI system: A asks to "Identify potential biases, inequities" while B frames "Bias and representativeness in training data" as a safety issue, so both denote the same AI-bias concept from different documents' perspectives.

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

**P087 — verdict (same / different / uncertain):** same

**P087 — note:** [claude-fable-5-1, confidence 0.75] Both spans name the bare generic concept "interoperability" — Node A gives only "interoperability" and Node B uses it in the same general sense ("to encourage interoperability" via standardized concepts and terminology), with no narrowing qualifier in either that would make one a species of the other.

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

**P088 — verdict (same / different / uncertain):** uncertain

**P088 — note:** [claude-fable-5-1, confidence 0.55] Node A's span is only the bare word "interoperability" with no referent, while Node B names "Interoperability" as one of four FAIR "foundational principles" for "scientific data management", so the spans cannot show whether A means the general property or the same data-specific principle.

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

**P089 — verdict (same / different / uncertain):** different

**P089 — note:** [claude-fable-5-1, confidence 0.8] Node A's bare "Accessibility" in an AI maturity model context is an organizational-capability dimension, while Node B defines accessibility specifically as "the ease with which the data file extract can be obtained from the administrative agency", a data-quality dimension for administrative data.

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

**P090 — verdict (same / different / uncertain):** different

**P090 — note:** [claude-fable-5-1, confidence 0.85] Node A's "Accessibility" sits inside an organizational maturity model, while Node B's "Accessibility" is a FAIR data principle for "scientific data management and stewardship" — a homonymous label applied to two distinct concepts (organizational capability vs. a data-stewardship property).

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

**P091 — verdict (same / different / uncertain):** uncertain

**P091 — note:** [claude-fable-5-1, confidence 0.55] Node A is only the bare word "accuracy" with no definition, while Node B pins it down as "One of four key dimensions of survey quality", so the spans cannot show whether A means the same survey-quality sense or a general/AI-system sense.

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

**P092 — verdict (same / different / uncertain):** same

**P092 — note:** [claude-fable-5-1, confidence 0.7] Node A is the bare term "bias" and Node B's span is headed "Bias" with body "Bias and representativeness in training data," both denoting the general concept of bias in AI systems rather than a narrower species of it.

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

**P093 — verdict (same / different / uncertain):** same

**P093 — note:** [claude-fable-5-1, confidence 0.9] Both spans name the identical generic category, "privacy-enhancing techniques" in Node A and "privacy enhancing techniques" in Node B, differing only in hyphenation, and A's "such as differential privacy" is an illustrative example rather than a narrowing of the concept.

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

**P094 — verdict (same / different / uncertain):** same

**P094 — note:** [claude-fable-5-1, confidence 0.7] Node A's "Documentation enables repeatability and consistency" and Node B's "quality of documentation" both denote the generic concept of documentation as recorded material about a system or dataset, with no narrowing modifier in either span.

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

**P095 — verdict (same / different / uncertain):** same

**P095 — note:** [claude-fable-5-1, confidence 0.95] Node A links "[RDF](https://www.w3.org/2001/sw/wiki/RDF)" the W3C data model standard, and Node B's "convert the RDF graph to a tabular or embedding-friendly format" refers to that same W3C RDF data model, not a narrower species of it.

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

**P096 — verdict (same / different / uncertain):** same

**P096 — note:** [claude-fable-5-1, confidence 0.8] Both spans use "structured data" in the generic data-format sense — A's "derived automatically from existing published content" and B's "structured data poses unique challenges regarding standardization" both refer to the same general category of machine-readable, schema-organized data rather than a narrower species of it.

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

**P097 — verdict (same / different / uncertain):** same

**P097 — note:** [claude-fable-5-1, confidence 0.8] Both spans name the same general concept "epistemic uncertainty" — A as "uncertainty in the model itself" and B as "epistemic uncertainty about science, facts and numbers" — differing only in application domain, not in what the term denotes.

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

**P098 — verdict (same / different / uncertain):** same

**P098 — note:** [claude-fable-5-1, confidence 0.85] Both spans name the same standard concept of epistemic uncertainty — Node A's "uncertainty in the model itself" and Node B's "epistemic uncertainty that exists about facts, numbers and science" are the same reducible knowledge-limited uncertainty applied in different domains, not distinct concepts.

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

**P099 — verdict (same / different / uncertain):** same

**P099 — note:** [claude-fable-5-1, confidence 0.9] Span A's bare label "sensitivity analysis" and span B's "Sensitivity analysis ... is commonly used to evaluate statistical models" both name the same general statistical technique, with neither span narrowing it to a species.

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

**P100 — verdict (same / different / uncertain):** same

**P100 — note:** [claude-fable-5-1, confidence 0.85] Both spans name the general concept of artificially generated data—"the ability to generate synthetic datasets" and "DWP uses synthetic data to accelerate AI readiness"—differing only in illustrative application, not in referent.

---

