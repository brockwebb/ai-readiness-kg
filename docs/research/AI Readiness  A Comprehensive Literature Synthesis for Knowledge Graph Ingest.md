# AI Readiness: A Comprehensive Literature Synthesis for Knowledge Graph Ingest

> **Scope:** Government, academic, and industry sources on AI readiness — definitions, frameworks, metrics, assessments, evaluations, and preprints — organized by dimension and source type for structured knowledge graph ingest.

***

## Executive Summary

"AI readiness" is a multidimensional construct describing an entity's (organization, nation, sector, or individual) preparedness to effectively adopt, integrate, and derive value from artificial intelligence. The literature does not converge on a single definition, but consistent domains emerge across sources: **data**, **infrastructure/tooling**, **governance**, **talent/workforce**, **strategy/leadership**, **culture/mindset**, and **ethics/legal compliance**. Critically, the dominant finding in 2024–2026 literature is that readiness failures are primarily *organizational and cultural* rather than technical — investment in AI capability without corresponding human and institutional transformation yields little measurable impact.[^1][^2][^3][^4]

***

## Part I: Definitional Landscape

### 1.1 Core Definition

At the broadest level, AI readiness measures **how prepared an entity is to adopt, integrate, and scale AI across its operations**. The construct operates at multiple levels of analysis:[^5][^6]

- **Individual/person-level**: cognitive, attitudinal, and skill-based readiness to work with or alongside AI systems
- **Organizational/enterprise-level**: institutional capacity across strategy, data, infrastructure, talent, governance, and culture
- **Sector-level**: domain-specific readiness (healthcare, federal statistical systems, education, public administration)
- **National/country-level**: government capacity, digital infrastructure, regulatory environment, and ecosystem maturity

### 1.2 Key Conceptual Distinctions

| Construct | Focus | Scope |
|---|---|---|
| **AI Readiness** | Organizational/national preparedness *before and during* adoption | Multidimensional |
| **AI Maturity** | Sophistication of AI capability *after* adoption | Progress/evolution |
| **Data Readiness** | Preparedness of data assets specifically for AI use | Data layer only |
| **Technology Readiness (TRL)** | Readiness of an AI/ML *system* or artifact | Model/system-level |
| **AI Literacy** | Individual cognitive/skills baseline | Person-level |

The distinction between organizational readiness (capacity to absorb AI) and model/system readiness (technical artifact quality) is explicitly drawn in recent public-sector literature.[^7][^8]

***

## Part II: Data Readiness — Foundational Frameworks

Data readiness is the most granular and technically elaborated subdimension. Multiple independent frameworks converge on a staged or leveled model.

### 2.1 Data Readiness Levels (DRL) — Lawrence (2017)

**Source:** Neil D. Lawrence, "Data Readiness Levels" — arXiv:1705.02245 (2017)
**URL:** https://arxiv.org/abs/1705.02245
**Semantic Scholar:** https://www.semanticscholar.org/paper/Data-Readiness-Levels-Lawrence/e64b8b2bb746a83a42680880b9860bf2a5b3a0c9

This foundational position paper proposed three *Bands* (A, B, C) of data preparedness, adapted from NASA's Technology Readiness Levels:[^9][^10]

- **Band C (Accessibility)**: Data exists and is physically accessible (files, databases)
- **Band B (Validity)**: Data is understood, has known quality attributes, errors and biases are characterized
- **Band A (Usability)**: Data is ready for a specific ML task — labeled, feature-engineered, documented

The DRL framework emphasizes that data quality assessment must precede problem definition, not follow it — a principle with direct relevance to statistical production environments.[^11][^9]

### 2.2 AIDRIN — AI Data Readiness Inspector

**Source:** Hiniduma et al., "AI Data Readiness Inspector (AIDRIN) for Quantitative Assessment of Data Readiness for AI" — arXiv:2406.19256 (2024); AIDRIN 2.0 — arXiv:2505.18213 (2025)
**Primary URL:** https://arxiv.org/abs/2406.19256
**AIDRIN 2.0:** https://arxiv.org/abs/2505.18213
**GitHub:** https://github.com/idtlab/aidrin
**OSTI:** https://www.osti.gov/biblio/2545803
**ACM:** https://dl.acm.org/doi/full/10.1145/3750720.3757282

AIDRIN is an open-source quantitative framework covering a broad range of readiness dimensions. Core dimensions assessed include:[^12][^13]

- **Completeness** — missing values, null rates
- **Consistency** — cross-field and cross-record coherence
- **Accuracy** — ground-truth alignment
- **Uniqueness** — deduplication
- **Timeliness** — currency and recency of records
- **Bias and Fairness** — demographic distribution, protected attribute balance
- **Lineage/Provenance** — data origin and transformation traceability
- **Licensability/Legal** — rights and usage constraints

AIDRIN 2.0 extends the framework to incorporate generative AI readiness dimensions and automated report generation.[^14][^15]

### 2.3 Data Readiness for AI — 360-Degree Survey (2024)

**Source:** Hiniduma et al., "Data Readiness for AI: A 360-Degree Survey" — arXiv:2404.05779 (2024); ACM Digital Library
**URL:** https://arxiv.org/abs/2404.05779
**ACM:** https://dl.acm.org/doi/abs/10.1145/3722214

Examines 140+ papers to produce a taxonomy of Data Readiness for AI (DRAI) metrics applicable to both structured and unstructured datasets. The taxonomy covers data quality, governance, bias, privacy, and modality-specific concerns (tabular, text, image, graph). Directly relevant to federal statistical data pipelines where structured tabular formats dominate.[^16][^17]

### 2.4 Data Readiness for Scientific AI at Scale

**Source:** "Data Readiness for Scientific AI at Scale" — arXiv:2507.23018 (2025); ACM Digital Library
**URL:** https://arxiv.org/abs/2507.23018 / https://arxiv.org/html/2507.23018v1
**ORNL:** https://impact.ornl.gov/en/publications/data-readiness-for-scientific-ai-at-scale/
**ACM:** https://dl.acm.org/doi/full/10.1145/3750720.3757282

Defines five Data Readiness Levels for leadership-scale scientific datasets: **raw → cleaned → labeled → feature-engineered → fully AI-ready**. Directly applicable to large-scale government datasets (administrative records, census microdata) feeding foundation models.[^18][^19]

### 2.5 IBM: AI-Ready Data Definition

**Source:** IBM Institute for Business Value, "What Is AI-Ready Data?" (2024)
**URL:** https://www.ibm.com/think/topics/ai-ready-data

IBM's practitioner definition specifies that AI-ready data must satisfy: **accessibility** (pipelines, APIs), **quality** (accuracy, completeness, consistency), **governance** (metadata, lineage, ownership), and **security** (access controls, privacy protection). Only 29% of technology leaders strongly agree their enterprise data meets quality standards needed for AI.[^20]

***

## Part III: Organizational & Enterprise AI Readiness Frameworks

### 3.1 Cisco AI Readiness Index (2023–2025)

**Source:** Cisco Global AI Readiness Index, annual
**2024 URL:** https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/archive/2024-m11.html
**Methodology:** https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/methodology.html
**Assessment Tool:** https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/assessment-tool.html
**2024 PDF:** https://www.cisco.com/c/dam/m/en_us/solutions/ai/readiness-index/2024-m11/documents/cisco-ai-readiness-index.pdf

The Cisco index surveys organizations globally across **six equally-weighted pillars**:[^4][^21]

1. **Strategy** — AI business strategy, leadership commitment, investment allocation
2. **Infrastructure** — compute, networking, data center, cloud readiness
3. **Data** — data quality, accessibility, governance, pipeline maturity
4. **Governance** — policies, risk management, compliance, accountability mechanisms
5. **Talent** — AI skills, hiring, upskilling programs
6. **Culture** — change management, AI adoption behaviors, experimentation mindset

The 2024 index found urgency rising while readiness fell — a gap driven primarily by infrastructure and data deficits.[^21]

### 3.2 Deloitte: Six Areas of AI Readiness in Government

**Source:** Deloitte Insights, "Six Areas for Assessing AI Readiness in Government" (2020)
**URL (US):** https://www.deloitte.com/us/en/insights/industry/government-public-sector-services/ai-readiness-in-government.html
**URL (AU):** https://www.deloitte.com/au/en/our-thinking/insights/industry/government-public-services/ai-readiness-for-government.html
**PDF:** https://e-govforum.e-expo.gr/wp-content/uploads/DI_AI-readiness-for-government.pdf

Deloitte's government-specific model covers six areas:[^22][^1]

1. **Strategy** — Vision, roadmap, leadership mandate
2. **People** — Skills, roles, organizational structure
3. **Process** — Workflow redesign, change management
4. **Data** — Data infrastructure, quality, governance
5. **Technology & Platforms** — Tools, APIs, integration
6. **Ethics** — Bias, fairness, accountability, explainability

### 3.3 SIO Model — Siloed-Integrated-Orchestrated

**Source:** McClure & Gerdau, "Why AI Readiness Is an Organizational Learning Problem, Not a Technology Purchase" — arXiv:2604.16369 (2026)
**URL:** https://arxiv.org/abs/2604.16369
**ChatPaper summary:** https://chatpaper.com/es/paper/270486

Drawing on 19 large-scale industry and academic sources covering nearly 10,000 organizational leaders, this paper argues AI project failure is fundamentally an **organizational learning problem** rather than a technology deficit. Only 6% of firms report significant earnings impact despite $252.3B in global corporate AI investment in 2024. The SIO model maps enterprise AI capability across five pillars:[^2][^3]

1. **Culture & Leadership**
2. **Human Capital & Operations**
3. **Data Architecture**
4. **Systems Infrastructure**
5. **Governance & Regulatory Compliance**

Stages progress from **Siloed** (disconnected pilots, no integration) → **Integrated** (cross-functional deployment) → **Orchestrated** (AI as core operating model).

### 3.4 GSA AI Capability Maturity Model (AI CMM)

**Source:** GSA AI Center of Excellence, "How We Measure AI Readiness" (2020); "AI Guide for Government"
**URL:** https://coe.gsa.gov/2020/10/28/ai-update-2.html
**Org Maturity:** https://coe.gsa.gov/coe/ai-guide-for-government/organizational-maturity-areas/index.html
**Full Guide:** https://coe.gsa.gov/coe/ai-guide-for-government/print-all/index.html

GSA's AI CMM is a planning tool to assess the current state of federal agency AI activities. Organizational maturity areas focus on both top-down strategy and bottom-up capability building. Directly applicable to federal statistical agencies.[^23][^24]

### 3.5 MITRE AI Maturity Model

**Source:** MITRE AI Maturity Model
**URL:** https://aimaturitymodel.mitre.org

Provides guidance and recommendations for building a foundation for successful AI implementation across organizations. Structured for complex operational environments including national security and government mission contexts.[^25]

### 3.6 From AI to Digital Transformation: The AI Readiness Framework

**Source:** Saarinen et al., *Business Horizons* (2022)
**ScienceDirect:** https://www.sciencedirect.com/science/article/pii/S0007681321000744
**DiVA:** http://www.diva-portal.org/smash/record.jsf?pid=diva2%3A1646069

An academic framework inviting "fuller theorizing of the roles that AI can—and will—play in digital transformation". Positions AI readiness as a precondition for digital transformation success.[^26][^27]

### 3.7 Technology Readiness and Organizational Journey Toward AI (2022)

**Source:** *International Journal of Information Management* (2022)
**URL:** https://www.sciencedirect.com/science/article/pii/S0268401222001220

Proposes that **people, process, and data readiness** are required *in addition to* technology readiness to achieve long-term operational success with AI. This four-part model (Technology + People + Process + Data) is one of the most-cited enterprise AI readiness formulations.[^28]

### 3.8 Arm AI Readiness Index

**Source:** Arm AI Readiness Index (2024)
**URL:** https://www.arm.com/resources/report/ai-readiness

Comprehensive analysis of global AI readiness and implementation for enterprises worldwide. Benchmarks adoption across industry sectors and regions.[^29]

### 3.9 Institutional Alignment Readiness (IAR) — Public Systems

**Source:** Legara, Jose & Martinez, "Beyond Model Readiness: Institutional Readiness for AI Deployment in Public Systems" — arXiv:2605.17203 (2026)
**URL:** https://arxiv.org/abs/2605.17203
**HTML:** https://arxiv.org/html/2605.17203v1
**PDF:** https://arxiv.org/pdf/2605.17203.pdf

Introduces a five-dimensional IAR framework explicitly for public-sector deployment — addressing the gap between technical viability and responsible rollout:[^8][^7]

1. **Institutional and operational compatibility**
2. **Data ecosystem maturity**
3. **Human oversight capacity**
4. **Fiscal sustainability**
5. **Regulatory alignment readiness**

Grounded in two operational cases from a large public education system. Argues existing model evaluation frameworks assess *models* not *institutions*.

***

## Part IV: National/Government-Level AI Readiness Indices

### 4.1 Oxford Insights — Government AI Readiness Index (Annual)

**Source:** Oxford Insights, Government AI Readiness Index
**2025 Report:** https://oxfordinsights.com/ai-readiness/government-ai-readiness-index-2025/
**2025 PDF:** https://oxfordinsights.com/wp-content/uploads/2026/01/Government-AI-Readiness-Report-2025-1.pdf
**Methodology PDF:** https://oxfordinsights.com/wp-content/uploads/2026/01/Methodology-Report-2025-1.pdf
**Framework PDF:** https://oxfordinsights.com/wp-content/uploads/2023/10/Shared_-Readiness-Framework-Online-Version.pdf

The most widely cited national-level index, ranking 195 countries on their capacity to harness AI for public benefit. The 2025 framework measures three clusters: **Government** (vision, strategy, procurement), **Technology Sector** (commercial AI capacity, startups), and **Data & Infrastructure** (open data, connectivity, cloud). UNESCO has endorsed use of this index for evaluating national AI readiness.[^30][^31]

### 4.2 OECD.AI Index

**Source:** OECD.AI Observatory Index (2026)
**URL:** https://oecd.ai/en/
**Technical Paper PDF:** https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/02/oecd-ai-observatory-index_8f5fa0f2/32c01014-en.pdf

A composite measurement framework to assess countries' implementation of the OECD AI Principles. Covers five OECD AI Principles across inclusive growth, human-centered values, transparency, robustness/security, and accountability.[^32]

**OECD AI Capability Indicators:**
**URL:** https://www.oecd.org/en/publications/introducing-the-oecd-ai-capability-indicators_be745f04-en/full-report/component-5.html

Introduces standardized indicators for measuring AI capabilities across countries.[^33]

**OECD Assessing Readiness for AI (Net Zero context):**
**PDF:** https://wp.oecd.ai/app/uploads/2025/05/AI-for-net-zero_assessing-readiness-for-AI.pdf

**OECD Building an AI-Ready Public Workforce (2026):**
**URL:** https://www.oecd.org/en/publications/building-an-ai-ready-public-workforce_b89244c7-en/full-report.html
**PDF:** https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/01/building-an-ai-ready-public-workforce_5cf188ee/b89244c7-en.pdf

Outlines strategies for AI-ready public sector workforces, identifying skills gaps at three levels: public sector leaders, digital/data professionals, and frontline workers.[^34][^35]

### 4.3 UNESCO AI Readiness Assessment Methodology (RAM)

**Source:** UNESCO Ethics of AI Programme
**URL:** https://www.unesco.org/ethics-ai/en/ram
**Index Analysis:** https://www.unesco.org/ethics-ai/en/articles/evaluating-national-ai-readiness-government-ai-readiness-index

Enables countries to operationalize the UNESCO Recommendation on the Ethics of AI through a structured national assessment methodology. Covers policy, infrastructure, education, R&D, economy, culture, and ethics dimensions.[^36][^37]

### 4.4 UNDP — Artificial Intelligence Readiness Assessment (AIRA)

**Source:** UNDP/GovTech, AIRA Framework
**Bhutan 2024 PDF:** https://www.undp.org/sites/g/files/zskgke326/files/2025-01/ai_readiness_assessment_bhutan.pdf
**UNDP Publication:** https://www.undp.org/bhutan/publications/artificial-intelligence-readiness-assessment-aira-2024
**UNDP/UNESCO Offer:** https://www.undp.org/sites/g/files/zskgke326/files/2024-12/undp-unesco-offer-web-7-aug-2024.pdf
**YouTube Overview:** https://www.youtube.com/watch?v=_m-_fsT1kP8

AIRA evaluates national readiness through three pillars:[^38][^39][^40]
1. **Government as User of AI** — public service delivery, operational AI adoption
2. **Government as Enabler of AI** — policy, regulation, infrastructure, digital skills
3. **Ethical AI** — governance, accountability, rights protection

### 4.5 ITU — AI Ready: Analysis Towards a Standardized Readiness Framework (2025)

**Source:** ITU-T, *AI4G* publication
**URL:** https://www.itu.int/epublications/zh/publication/ai-ready-analysis-towards-a-standardized-readiness-framework/en
**PDF:** https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf

Built around an AI Readiness Knowledge Base mapping to six fundamental factors including AI Policy & Regulation, Regulatory Quality, and Implementation. The most recent international standardization effort.[^41][^42]

### 4.6 IADB — Adaptive AI Readiness Scorecard (AARS)

**Source:** Inter-American Development Bank, "Are We Ready for AI? From Measurement to Policy Governance"
**URL:** https://publications.iadb.org/publications/english/document/Are-We-Ready-for-AI-From-Measurement-to-Policy-Governance.pdf
**Portal:** https://publications.iadb.org/en/are-we-ready-ai-measurement-policy-governance

Proposes an AARS that calibrates to country context and policy priorities, with pilot implementation roadmap for Latin America. Bridges measurement theory with policy operationalization.[^43][^44]

### 4.7 WEF — Making Agentic AI Work for Government: A Readiness Framework (2026)

**Source:** World Economic Forum
**URL:** https://www.weforum.org/publications/making-agentic-ai-work-for-government-a-readiness-framework/
**PDF:** https://reports.weforum.org/docs/WEF_Making_Agentic_AI_Work_for_Government_A_Readiness_Framework_2026.pdf
**Digital Gov Hub:** https://digitalgovernmenthub.org/library/making-agentic-ai-work-for-government-a-readiness-framework/

Introduces a novel, department-agnostic framework specifically for **agentic AI** (autonomous AI systems) in government settings. Advances the readiness paradigm from passive AI tools to orchestrated AI agents. Published April 2026.[^45][^46]

### 4.8 Global Public Sector AI Index 2026

**Source:** Alice Labs
**URL:** https://alicelabs.ai/reports/global-public-sector-ai-index-2026

A reproducible, source-grounded, global benchmarking framework for public-sector AI maturity. Positioned as a complement to the Oxford Insights index with greater methodological transparency.[^47]

***

## Part V: Federal Government (US) AI Readiness Sources

### 5.1 GAO AI Accountability Framework

**Source:** U.S. Government Accountability Office
**Senate Testimony PDF:** https://www.hsgac.senate.gov/wp-content/uploads/Testimony-Ariga-2023-05-16-REVISED-1.pdf
**2023 Agency Inventory Report:** https://digital.library.unt.edu/ark:/67531/metadc2289522/m1/80/
**2025 Generative AI Report:** https://www.akingump.com/en/insights/ai-law-and-regulation-tracker/gao-issues-report-on-generative-ai-use-and-management-at-fede...
**Procurement Gaps (2026):** https://fedscoop.com/agency-ai-procurement-gao-report/

GAO developed an AI Accountability Framework of key practices to help ensure responsible AI use by federal agencies. The 2023 report found 15 of 20 agencies' AI use case inventories contained inaccurate and incomplete data. By 2024, documented AI use cases grew from 571 to 1,110 across 11 agencies. The 2026 GAO report identified agencies are not systematically collecting lessons learned from AI acquisitions.[^48][^49][^50][^51]

### 5.2 GSA AI Guide for Government / AI CMM

**Source:** GSA IT Modernization Centers of Excellence
**Full Guide:** https://coe.gsa.gov/coe/ai-guide-for-government/print-all/index.html
**Org Maturity:** https://coe.gsa.gov/coe/ai-guide-for-government/organizational-maturity-areas/index.html
**2020 Post:** https://coe.gsa.gov/2020/10/28/ai-update-2.html

The AI CMM developed by GSA's AI Center of Excellence is the primary US federal tool for agency self-assessment. Organizational maturity areas represent the capacity to embed AI capabilities across the organization, using both top-down and bottom-up approaches.[^24][^52][^23]

### 5.3 NIST AI Risk Management Framework (AI RMF)

**Source:** NIST
**Primary URL:** https://www.nist.gov/artificial-intelligence (external reference)
**Alignment Context:** NIST AI RMF maps to AI readiness through its GOVERN, MAP, MEASURE, MANAGE lifecycle functions. Readiness implies an organization can operationalize all four functions before deploying AI systems.

### 5.4 PARIS21 — AI Readiness for National Statistical Offices (NSOs)

**Source:** PARIS21 Task Team on AI for Official Statistics (TTAI)
**Framework PDF:** https://www.paris21.org/sites/default/files/media/document/2025-12/ai-readiness-nso-framework.pdf
**Self-Assessment (SPEEDometer) Methodology:** https://www.paris21.org/sites/default/files/media/document/2026-04/ttai-self-assessment-methodology-report.pdf
**Practical Guide:** https://www.paris21.org/knowledge-base/ai-readiness-self-assessment-practical-guide-nsos
**Framework Announcement:** https://www.paris21.org/news/new-paris21-framework-supports-nsos-becoming-ai-ready
**UNECE Presentation PDF:** https://unece.org/sites/default/files/2025-11/HLG2025_Day2_Soapbox_OECD_Fogarassy_P.pdf
**ESCAP PDF:** https://www.unescap.org/sites/default/files/d8files/event-documents/PARIS21_AI_Readiness_Tools_StatsCafe-30Mar2026.pdf
**African NSOs Webinar:** https://www.youtube.com/watch?v=YTzkD2AlXPQ

The "Towards AI-Ready NSOs" framework defines an AI-ready National Statistical Office as one that "systematically leverages AI and ML technologies to enhance statistical capacity and modernize production". Key dimensions in the NSO context include data production modernization, metadata infrastructure, AI governance, and staff capability. The SPEEDometer toolkit provides structured self-assessment. **This is the most directly relevant source for federal statistical system AI readiness.**[^53][^54][^55]

### 5.5 UN Statistical Commission — AI-Readiness for Official Data and Statistics (2026)

**Source:** UN Statistics Division, 57th Statistical Commission Side Event (February 2026)
**Concept Note PDF:** https://unstats.un.org/UNSDWebsite/statcom/session_57/side-events/Friday_Seminar_2026_AI_Readable_Data_Concept_Note.pdf
**CCSA Background Paper PDF:** https://unstats.un.org/UNSDWebsite/statcom/session_57/documents/BG-5h-CCSA_AI_Readiness_Official_Statistics_v2-E.pdf
**Web TV (Part 2):** https://webtv.un.org/en/asset/k1l/k1l0vqp1j5

Defines AI-readiness for official statistics as ensuring users who search for and access data through AI receive accurate, authoritative results. The challenge for statistical offices is not control of AI outputs but ensuring their data is *discoverable, structured, and authoritative* within AI-mediated information systems.[^56][^57]

### 5.6 UNECE — AI Readiness in Official Statistics (2025–2026)

**Source:** UNECE High-Level Group on Modernization of Official Statistics
**HLG Working Paper PDF:** https://unece.org/sites/default/files/2026-04/ECE_CES-2026_11_HLG-MOS%20WP2026__ENG.pdf

Planning 2026 workshop on AI-readiness in official statistics following the 2025 UNECE Workshop on Generative AI in Official Statistics.[^58]

***

## Part VI: Sector-Specific Frameworks

### 6.1 Healthcare AI Readiness

**AIR-5D: Five Dimensions of AI Readiness (Healthcare)**
**Source:** Mishra, "Five Dimensions of AI Readiness (AIR-5D) Framework: A Preparedness Assessment Tool for Healthcare Organizations" — *PubMed* (2024)
**PubMed:** https://pubmed.ncbi.nlm.nih.gov/39543793/
**Elsevier Pure:** https://nchr.elsevierpure.com/en/publications/five-dimensions-of-ai-readiness-air-5d-framework-a-preparedness-a/fingerprints/

A five-dimensional framework validated for healthcare operational excellence. Applied to hospital and health system contexts.[^59][^60]

**Clinical AI Readiness Evaluator (CARE-L) Framework**
**Source:** PMC/NIH (2025)
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12236009/

Introduces the Clinical AI Readiness Evaluator Lifecycle — an AI-driven TRL assessment tool for clinical AI systems.[^61]

**DiMe Health AI Readiness Assessment**
**URL:** https://dimesociety.org/ai-implementation-in-healthcare-playbook/ai-evaluation-readiness/health-ai-readiness-assessment/

Seven-domain self-assessment from the Digital Medicine Society.[^62]

### 6.2 Education AI Readiness

**School AI Readiness to Student AI Literacy**
**Source:** arXiv:2603.20056 (2026)
**URL:** https://arxiv.org/html/2603.20056v1

National multilevel mediation analysis examining how institutional AI readiness (as organizational capacity) translates to student AI literacy through teacher capability.[^63]

**Pearson/AWS AI Readiness: Building the Bridge from Higher Education to Work (2026)**
**PDF:** https://www.pearson.com/content/dam/global-store/global/resources/ai-readiness/AI-Readiness-Report-2026.pdf

Addresses the skills gap between higher education and AI-ready workforce.[^64]

### 6.3 AI Readiness and Firm Productivity

**Source:** "Artificial Intelligence, Domain AI Readiness, and Firm Productivity" — arXiv:2508.09634 (2025)
**URL:** https://arxiv.org/abs/2508.09634

Creates novel constructs from patent data to measure **domain AI readiness** by analyzing co-occurrence of technological concepts — a proxy for sector-level AI absorptive capacity. Links AI readiness directly to firm productivity outcomes.[^65]

***

## Part VII: Technology/System-Level Readiness

### 7.1 Technology Readiness Levels for AI & ML (TRL4ML)

**Source:** Lavin et al., "Technology Readiness Levels for AI & ML" — arXiv:2006.12497 (2020)
**URL:** https://arxiv.org/abs/2006.12497
**PDF:** https://lavin.io/docs/TRL4ML-Cambridge2020.pdf
**Semantic Scholar:** https://www.semanticscholar.org/paper/Technology-Readiness-Levels-for-AI-&-ML-Lavin-Renard/01e46908f9459d379260a5cf987c63b723e12

Adapts NASA's 1–9 TRL scale for ML/AI system development. Provides a principled process to ensure robust ML systems while being streamlined for research.[^66]

### 7.2 Machine Learning Technology Readiness Levels (MLTRL)

**Source:** Lavin et al., "Technology Readiness Levels for Machine Learning Systems" — arXiv:2101.03989 (2021); *Nature Communications* (2022)
**arXiv:** https://arxiv.org/abs/2101.03989
**Nature:** https://www.nature.com/articles/s41467-022-33128-9
**PMC:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9585100/

MLTRL defines TRLs to guide and communicate ML/AI development and deployment, covering nine stages from basic research to full operational deployment. Published in *Nature Communications* — the most-cited technical AI readiness framework for ML systems.[^67][^68][^69]

### 7.3 EU JRC: Revisiting TRLs for AI Technologies

**Source:** EU Joint Research Centre, "AI Watch: Revisiting Technology Readiness Levels for Relevant AI Technologies"
**PDF:** https://publications.jrc.ec.europa.eu/repository/bitstream/JRC129399/JRC129399_01.pdf

Defines maturity of AI technologies through TRL assessment adapted for the European context.[^70]

### 7.4 Rethinking Technological Readiness in the Era of AI Uncertainty

**Source:** arXiv:2506.11001 (2025)
**URL:** https://arxiv.org/abs/2506.11001
**HTML:** https://arxiv.org/html/2506.11001v1

Critically examines whether traditional TRL concepts apply under AI's characteristic uncertainty and emergent behavior.[^71][^72]

### 7.5 From Accuracy to Readiness: Metrics for Human-AI Decision-Making

**Source:** Lee, "From Accuracy to Readiness: Metrics and Benchmarks for Human-AI Decision-Making" — arXiv:2603.18895 (2026)
**URL:** https://arxiv.org/abs/2603.18895

Proposes a measurement framework for evaluating human-AI decision-making centered on *team readiness* rather than model accuracy. Introduces a four-part taxonomy: outcomes, reliance behavior, safety signals, and learning over time — connected to the Understand-Control-Improve (U-C-I) lifecycle of human-AI onboarding.[^73]

***

## Part VIII: Workforce, Culture, and Organizational Dimensions

### 8.1 OECD: Building an AI-Ready Public Workforce (2026)

**URL:** https://www.oecd.org/en/publications/building-an-ai-ready-public-workforce_b89244c7-en/full-report.html

Identifies three tiers of AI-ready skills for public servants: **strategic understanding** (leaders), **technical/data proficiency** (digital professionals), and **AI literacy** (frontline workers). AI adoption improves public sector efficiency but many institutions are held back by skills gaps.[^74][^35][^34]

### 8.2 McKinsey: State of AI Reports (2024–2025)

**2025 Report:** https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai
**Superagency in Workplace:** https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/superagency-in-the-workplace-empowering-people-to-unlock-ais-full...
**2024 PDF:** https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai/2024/the-state-...

McKinsey's 2025 survey: 88% of organizations regularly use AI, but only 6% achieve significant enterprise-wide impact (5%+ revenue effect). Technology and business readiness are assessed separately, with cultural and change management readiness as the primary differentiators.[^75][^76][^77]

### 8.3 IBM: AI Readiness — Thriving Through Disruption

**URL:** https://www.ibm.com/think/insights/ai-readiness-thriving-through-ai-disruption
**Barriers:** https://www.ibm.com/think/insights/ai-readiness-overcoming-ai-barriers
**CDO Study:** https://newsroom.ibm.com/2025-11-13-ibm-study-chief-data-officers-redefine-strategies-as-ai-ambitions-outpace-readiness

IBM's 2025 CDO study finds AI ambitions outpacing readiness across the enterprise, with Chief Data Officers redefining data strategies as AI pressure mounts.[^78][^79]

### 8.4 Resistance to Change and AI Readiness

**Source:** Journals *SAGE Open* (2023)
**URL:** https://journals.sagepub.com/doi/10.1177/21582440231217731

Academic study exploring the impact of resistance to change on AI readiness, with mediating variables. Important for understanding human factors in organizational readiness assessments.[^80]

### 8.5 Prosci: Organizational AI Readiness (Change Management Lens)

**Source:** Prosci Blog (2026)
**URL:** https://www.prosci.com/blog/organizational-ai-readiness

Emphasizes that organizational AI readiness must look beyond tools and infrastructure, focusing on human adoption dynamics. Prosci's ADKAR model (Awareness, Desire, Knowledge, Ability, Reinforcement) applies to AI adoption readiness.[^81]

### 8.6 Code for America: Government AI Landscape Assessment

**Source:** Code for America
**URL:** https://codeforamerica.org/explore/government-ai-landscape-assessment/

In the "Readiness stage," the central question is who is accountable for AI, how it should be governed, and what populations it will serve — not how to deploy at scale. Emphasizes that governance and accountability precede deployment.[^82]

***

## Part IX: Psychometric and Individual-Level Measurement

### 9.1 AI Readiness Scale (AIRS) — Management Education

**Source:** *Journal of Business Research* (2026)
**URL:** https://www.sciencedirect.com/science/article/pii/S147281172600073X

Development and validation of an AI readiness scale (AIRS) with psychometric properties for management education contexts. Measures individual readiness across cognitive, affective, and behavioral dimensions.[^83]

### 9.2 Medical AI Readiness Scale for Medical Students (MAIRSE)

**Source:** *PMC* (2021)
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7890640/

Psychometric measurement tool for perceived readiness of medical students to use AI. Validated for reliability and construct validity.[^84]

### 9.3 AI Readiness in Healthcare Through Storytelling XAI

**Source:** arXiv:2410.18725 (2024)
**URL:** https://arxiv.org/abs/2410.18725

Examines AI readiness from the patient/clinician perspective using explainable AI techniques to build audience-centric readiness.[^85]

***

## Part X: Composite Frameworks and Scoring Rubrics

### 10.1 Readiness Dimension Cross-Walk

The following table maps dimensions across the major frameworks, enabling alignment for knowledge graph entity typing:

| Dimension | Cisco | Deloitte Gov | SIO Model | PARIS21 NSO | IAR (Public) | Oxford Index |
|---|---|---|---|---|---|---|
| **Strategy/Vision** | ✓ | ✓ | — | ✓ | — | ✓ |
| **Data** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Infrastructure/Tech** | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| **Governance** | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| **Talent/Workforce** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Culture/Mindset** | ✓ | — | ✓ | — | — | — |
| **Ethics/Legal** | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Process/Operations** | — | ✓ | ✓ | ✓ | ✓ | — |
| **Fiscal/Budget** | — | — | — | — | ✓ | — |
| **Human Oversight** | — | — | — | — | ✓ | — |

### 10.2 AI-REAL Toolkit

**Source:** AI-REAL Project
**PDF:** https://ai-real.dco.org/assets/frontend/images/AI-Readiness-Assessment-Guide.pdf

Practical assessment guide combining readiness dimensions into an actionable toolkit format.[^86]

### 10.3 Code for America / AI-REAL Practical Guides

**Digital Gov Hub Checklist:** http://digitalgovernmenthub.org/examples/ai-data-readiness-checklist/

Covers three checklist areas: Data Governance Framework and Policies; Data Quality and Management; and Data Security and Privacy.[^87]

***

## Part XI: Key Quantitative Findings for Knowledge Graph Population

The following statistics appear across multiple authoritative sources and are suitable as typed assertions:

| Claim | Value | Source | URL |
|---|---|---|---|
| Orgs using AI regularly (2024) | 88% | McKinsey 2025 | [^77] |
| Orgs with significant AI impact | 6% | McKinsey 2025 | [^77] |
| Global corporate AI investment (2024) | $252.3B | arXiv:2604.16369 | [^3] |
| Tech leaders agreeing data meets AI quality standards | 29% | IBM IBV 2024 | [^20] |
| Agency AI use cases (US federal, 2023→2024) | 571→1,110 | GAO 2025 | [^49] |
| AI project failures from human factors | 63% | Industry analysis | [^88] |
| Enterprise AI pilots failing to deliver P&L impact | 95% | MIT NANDA 2025 | [^76] |
| L&D professionals feeling confident integrating AI | 28% | Absorb Report 2026 | [^89] |

***

## Part XII: Preprints and Emerging Literature (arXiv / Peer Review in Progress)

| Title | arXiv ID | Year | URL |
|---|---|---|---|
| Data Readiness Levels (Lawrence) | 1705.02245 | 2017 | https://arxiv.org/abs/1705.02245 |
| Technology Readiness Levels for AI & ML | 2006.12497 | 2020 | https://arxiv.org/abs/2006.12497 |
| Technology Readiness Levels for ML Systems | 2101.03989 | 2021 | https://arxiv.org/abs/2101.03989 |
| Data Readiness for AI: 360-Degree Survey | 2404.05779 | 2024 | https://arxiv.org/abs/2404.05779 |
| AI Data Readiness Inspector (AIDRIN) | 2406.19256 | 2024 | https://arxiv.org/abs/2406.19256 |
| AI Readiness in Healthcare (XAI) | 2410.18725 | 2024 | https://arxiv.org/abs/2410.18725 |
| Bangladesh's AI Readiness: Perspectives | 2601.12934 | 2026 | https://arxiv.org/html/2601.12934v1 |
| AIDRIN 2.0 | 2505.18213 | 2025 | https://arxiv.org/abs/2505.18213 |
| Rethinking Technological Readiness (AI Era) | 2506.11001 | 2025 | https://arxiv.org/abs/2506.11001 |
| Domain AI Readiness and Firm Productivity | 2508.09634 | 2025 | https://arxiv.org/abs/2508.09634 |
| Data Readiness for Scientific AI at Scale | 2507.23018 | 2025 | https://arxiv.org/abs/2507.23018 |
| From Accuracy to Readiness (Human-AI) | 2603.18895 | 2026 | https://arxiv.org/abs/2603.18895 |
| From School AI Readiness to AI Literacy | 2603.20056 | 2026 | https://arxiv.org/html/2603.20056v1 |
| Why AI Readiness Is Org Learning Problem (SIO) | 2604.16369 | 2026 | https://arxiv.org/abs/2604.16369 |
| Institutional Readiness for AI (IAR) | 2605.17203 | 2026 | https://arxiv.org/abs/2605.17203 |
| Metrics/Benchmarks Human-AI Decision-Making | 2603.18895 | 2026 | https://arxiv.org/abs/2603.18895 |

***

## Part XIII: Analytical Synthesis — What Does "AI Ready" Mean?

Synthesizing across all sources, being "AI ready" is best understood as satisfying the following preconditions simultaneously:

### Data Layer
- Data is accessible, governed, documented, and fit for the intended AI task (DRL-A equivalent)[^9]
- Data quality dimensions (completeness, consistency, accuracy, timeliness, bias) are measurably characterized[^90][^12]
- Data pipelines, APIs, and lineage tracking are operational[^20]
- Metadata is machine-readable and aligned with semantic standards[^57][^56]

### Infrastructure/Tooling Layer
- Compute, storage, and networking capacity matches the scale of intended AI workloads[^4]
- MLOps and model lifecycle management processes exist[^23]
- Security, access control, and privacy-enhancing technologies are deployed[^87]

### Governance Layer
- AI policies, risk management protocols, and accountability mechanisms are documented and enforced[^22][^4]
- Use case inventory and impact assessments are maintained[^51][^48]
- Ethical review and bias assessment processes exist pre-deployment[^38]
- Regulatory alignment (NIST AI RMF, OMB M-24-10, sector-specific requirements) is verified[^8]

### Talent/Workforce Layer
- Tiered AI competencies exist: strategic (leadership), technical (practitioners), literacy (frontline)[^34]
- Hiring, upskilling, and reskilling programs are funded and operational[^35]
- AI augmentation roles and human oversight responsibilities are defined[^91]

### Culture/Mindset Layer
- Leadership commitment to AI as a strategic capability (not just a tool) is visible and sustained[^2]
- Psychological safety for experimentation and failure exists[^81]
- Resistance to change is actively managed through structured change management[^80]
- AI is understood as a *learning process* requiring iterative organizational adaptation[^3][^2]

### Strategy/Operational Layer
- Business cases for AI are tied to measurable outcomes, not just deployment metrics[^22]
- Process redesign (not just overlay) accompanies AI introduction[^1]
- A roadmap from pilot to scale with governance gates exists[^82]

### Ethics/Legal Layer
- Compliance with applicable AI law, regulation, and executive order is documented[^51]
- Affected communities and stakeholders have been engaged[^38]
- Explainability and transparency requirements are built into the deployment plan[^85]

***

## Part XIV: Knowledge Graph Design Notes

For structured ingest, the following entity types and relationship patterns are recommended based on the literature synthesis:

**Core Entity Types:**
- `AIReadinessFramework` (name, publisher, year, scope, URL, dimension_count)
- `AIReadinessDimension` (name, canonical_label, framework_source, measurement_approach)
- `AIReadinessMetric` (name, unit, data_type, source_framework, measurement_level)
- `AIReadinessAssessmentTool` (name, format, target_entity, dimensions_covered, URL)
- `AIReadinessIndex` (name, publisher, country_coverage, year, methodology_URL)
- `DataReadinessLevel` (band, level_number, label, description, framework)

**Key Relationships:**
- `FRAMEWORK hasComponent DIMENSION`
- `DIMENSION measuredBy METRIC`
- `ASSESSMENT_TOOL implements FRAMEWORK`
- `FRAMEWORK appliesTo ENTITY_TYPE` (Organization | Nation | Dataset | MLSystem | Individual)
- `INDEX ranks ENTITY using FRAMEWORK`
- `DIMENSION subclassOf DIMENSION` (e.g., DataQuality → Completeness, Accuracy, Timeliness)
- `READINESS_LEVEL precedes READINESS_LEVEL` (ordinal progression)

**Canonical Dimension Taxonomy (cross-framework consensus):**
1. Data Readiness (→ Quality, Governance, Architecture, Discoverability, Privacy)
2. Infrastructure Readiness (→ Compute, Networking, Cloud, MLOps)
3. Governance Readiness (→ Policy, Risk, Accountability, Compliance)
4. Talent Readiness (→ Strategic, Technical, Literacy)
5. Culture Readiness (→ Leadership, Change Management, Psychological Safety)
6. Strategy Readiness (→ Vision, Roadmap, Business Case, Alignment)
7. Ethics/Legal Readiness (→ Bias, Fairness, Explainability, Regulation)
8. Operational Readiness (→ Process, Workflow, Human Oversight, Fiscal)

---

## References

1. [Six Areas for Assessing AI Readiness in Government | Deloitte Insights](https://www.deloitte.com/us/en/insights/industry/government-public-sector-services/ai-readiness-in-government.html)

2. [Why AI Readiness Is an Organizational Learning Problem, Not a ...](https://arxiv.org/abs/2604.16369) - This article argues that AI project failure is fundamentally an organizational learning problem rath...

3. [Why AI Readiness Is an Organizational Learning Problem, Not a ...](https://chatpaper.com/es/paper/270486) - Global corporate AI investment reached $252.3 billion in 2024, yet only 6% of firms report significa...

4. [Cisco 2024 AI Readiness Index](https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/archive/2024-m11.html) - AI readiness comprises six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture....

5. [AI Readiness: A Complete Guide, from Framework to Implementation](https://www.knack.com/blog/ai-readiness-framework-assessment-implementation/) - AI readiness measures how prepared an organization is to adopt, integrate, and scale artificial inte...

6. [What is AI readiness? - Ataccama](https://www.ataccama.com/blog/ai-readiness) - AI readiness measures how prepared your company is to adopt, integrate and create value with AI acro...

7. [Beyond Model Readiness: Institutional Readiness for AI Deployment in Public Systems](https://arxiv.org/abs/2605.17203v1?utm=screenwise) - Many public-sector artificial intelligence systems fail not at the point of model development, but a...

8. [Institutional Readiness for AI Deployment in Public Systems - arXiv](https://arxiv.org/html/2605.17203v1) - We introduce Institutional Alignment Readiness (IAR), a five-dimensional framework for assessing dep...

9. [[1705.02245] Data Readiness Levels - arXiv](https://arxiv.org/abs/1705.02245) - This position paper proposes the use of data readiness levels: it gives a rough outline of three sta...

10. [Data Readiness Levels: Turning Data from Palid to Vivid](https://opendatascience.com/data-readiness-levels-turning-data-from-palid-to-vivid/) - The idea of these levels is to increase the accountability of the process and allow the nature of th...

11. [Data Readiness Levels - Neil Lawrence](http://inverseprobability.com/talks/notes/data-readiness-levels.html) - The Grade B of data readiness ensures thought can be put into data quality before the question is de...

12. [AI Data Readiness Inspector (AIDRIN) for Quantitative Assessment ...](https://arxiv.org/abs/2406.19256) - AIDRIN is a framework covering a broad range of readiness dimensions available in the literature tha...

13. [AI Data Readiness Inspector (AIDRIN) for Quantitative Assessment ...](https://arxiv.org/html/2406.19256v2) - AIDRIN is a framework covering a broad range of readiness dimensions available in the literature tha...

14. [AIDRIN 2.0: A Framework to Assess Data Readiness for AI - arXiv](https://arxiv.org/html/2505.18213v1) - AIDRIN is a framework to evaluate and improve data preparedness for AI applications. It addresses cr...

15. [AIDRIN 2.0: A Framework to Assess Data Readiness for AI - arXiv](https://arxiv.org/abs/2505.18213) - Abstract:AI Data Readiness Inspector (AIDRIN) is a framework to evaluate and improve data preparedne...

16. [[2404.05779] Data Readiness for AI: A 360-Degree Survey - arXiv](https://arxiv.org/abs/2404.05779) - This survey aims to propose a taxonomy of data readiness for AI (DRAI) metrics for structured and un...

17. [[PDF] Data Readiness for AI: A 360-Degree Survey - Semantic Scholar](https://www.semanticscholar.org/paper/Data-Readiness-for-AI:-A-360-Degree-Survey-Hiniduma-Byna/d71464394108bf6ecbf82871e144b9dc52e9037d) - This survey examines more than 140 papers published by ACM Digital Library, IEEE Xplore, journals su...

18. [Data Readiness for Scientific AI at Scale - arXiv](https://arxiv.org/html/2507.23018v1) - This paper examines how Data Readiness for AI (DRAI) principles apply to leadership-scale scientific...

19. [Data Readiness for Scientific AI at Scale - ACM Digital Library](https://dl.acm.org/doi/full/10.1145/3750720.3757282) - To that end, we present five Data Readiness Levels—raw, cleaned, labeled, feature-engineered, and fu...

20. [What Is AI-Ready Data? - IBM](https://www.ibm.com/think/topics/ai-ready-data) - According to a 2024 survey from the IBM Institute for Business Value, only 29% of technology leaders...

21. [Cisco's 2024 AI Readiness Index: Urgency Rises, Readiness Falls](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m11/cisco-2024-ai-readiness-index-urgency-rises-readiness-falls.html) - The Index assessed respondents' AI readiness across six key pillars: strategy, infrastructure, data,...

22. [AI readiness for government | Deloitte](https://www.deloitte.com/au/en/our-thinking/insights/industry/government-public-services/ai-readiness-in-government.html) - As various government agencies prepare to deploy artificial intelligence, a six-pronged framework ca...

23. [How We Measure AI Readiness | GSA](https://coe.gsa.gov/2020/10/28/ai-update-2.html) - The AI CMM is a planning tool to assess the current state of an organization's Artificial Intelligen...

24. [Organizational maturity areas | GSA](https://coe.gsa.gov/coe/ai-guide-for-government/organizational-maturity-areas/index.html) - Organizational maturity areas represent the capacity to embed AI capabilities across the organizatio...

25. [Ai maturity model |](https://aimaturitymodel.mitre.org) - The MITRE AI MM is a methodology to provide guidance and recommendations for building a foundation f...

26. [From AI to digital transformation: The AI readiness framework](https://www.sciencedirect.com/science/article/pii/S0007681321000744)

27. [From AI to digital transformation : the AI readiness framework](http://www.diva-portal.org/smash/record.jsf?pid=diva2%3A1646069) - The AI readiness framework invites fuller theorizing of the roles that AI can—and will—play in digit...

28. [Technology readiness and the organizational journey towards AI ...](https://www.sciencedirect.com/science/article/pii/S0268401222001220) - The model suggests that people, process and data readiness are required in addition to technology re...

29. [Arm AI Readiness Index](https://www.arm.com/resources/report/ai-readiness) - The Arm AI Readiness Index report is a comprehensive analysis of global AI readiness and implementat...

30. [Government AI Readiness Index 2025 - Oxford Insights](https://oxfordinsights.com/ai-readiness/government-ai-readiness-index-2025/) - The 2025 Government AI Readiness Index ranks 195 countries on their capacity to harness AI for publi...

31. [Evaluating national AI readiness with the Government AI ... - UNESCO](https://www.unesco.org/ethics-ai/en/articles/evaluating-national-ai-readiness-government-ai-readiness-index)

32. [[PDF] The OECD.AI Index - Technical paper](https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/02/oecd-ai-observatory-index_8f5fa0f2/32c01014-en.pdf) - This technical paper introduces the OECD.AI Index, a composite measurement framework designed to ass...

33. [Introducing the OECD AI Capability Indicators: Constructing a framework to measure AI capabilities](https://www.oecd.org/en/publications/introducing-the-oecd-ai-capability-indicators_be745f04-en/full-report/component-5.html)

34. [Full Report: Building an AI-ready public workforce | OECD](https://www.oecd.org/en/publications/building-an-ai-ready-public-workforce_b89244c7-en/full-report.html) - AI adoption can improve public sector efficiency and service quality by supporting and accelerating ...

35. [Building an AI‑ready public workforce - OECD](https://www.oecd.org/en/publications/building-an-ai-ready-public-workforce_b89244c7-en.html) - The adoption of AI systems can improve public sector efficiency and service quality, but many govern...

36. [AI Readiness Assessment Methodology - UNESCO](https://www.unesco.org/ethics-ai/en/ram) - The AI Readiness Assessment Methodology (RAM) enables countries to turn the UNESCO Recommendation on...

37. [AI Readiness Assessment | Ministry of Public Administration and ...](http://mpaai.gov.tt/initiatives/ai-readiness-assessment) - The AI Readiness Assessment Methodology (RAM) is a UNESCO-developed framework that evaluates a count...

38. [[PDF] Artificial Intelligence Readiness Assessment (AIRA)](https://www.undp.org/sites/g/files/zskgke326/files/2025-01/ai_readiness_assessment_bhutan.pdf) - The AI Readiness Assessment (AIRA) framework considers the role of government as both a user of AI a...

39. [UNDP Bhutan - Facebook](https://www.facebook.com/UNDPBhutan/posts/to-gain-a-deeper-understanding-of-the-artificial-intelligence-readiness-assessme/522053477134498/) - The results were organized into three key pillars: Government as an Enabler of AI, Government as a U...

40. [Artificial Intelligence Readiness Assessment (AIRA) 2024](https://www.undp.org/bhutan/publications/artificial-intelligence-readiness-assessment-aira-2024) - The AI Readiness Assessment 2024 for Bhutan evaluates the country's preparedness to integrate AI tec...

41. [AI Ready – Analysis Towards a Standardized Readiness Framework](https://www.itu.int/epublications/zh/publication/ai-ready-analysis-towards-a-standardized-readiness-framework/en) - The ITU AI Readiness Knowledge Base functions as the brain of the toolkit. It is built with AI techn...

42. [[PDF] Analysis Towards a Standardized Readiness Framework - ITU](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf) - We selected AI Policy and Regulation, Regulatory. Quality, and Implementation as they collectively r...

43. [[PDF] Are We Ready for AI? From Measurement to Policy Governance](https://publications.iadb.org/publications/english/document/Are-We-Ready-for-AI-From-Measurement-to-Policy-Governance.pdf) - We propose an Adaptive AI. Readiness Scorecard (AARS) that calibrates to country context and policy ...

44. [Are We Ready for AI? From Measurement to Policy Governance](https://publications.iadb.org/en/are-we-ready-ai-measurement-policy-governance) - We propose an Adaptive AI Readiness Scorecard (AARS) that calibrates to country context and policy p...

45. [[PDF] Making Agentic AI Work for Government: A Readiness Framework](https://reports.weforum.org/docs/WEF_Making_Agentic_AI_Work_for_Government_A_Readiness_Framework_2026.pdf)

46. [Making Agentic AI Work for Government: A Readiness Framework](https://www.weforum.org/publications/making-agentic-ai-work-for-government-a-readiness-framework/) - This report, Making Agentic AI Work for Government: A Readiness Framework, applies a novel, departme...

47. [Public Sector AI Readiness 2026: Government Benchmarks by ...](https://alicelabs.ai/reports/global-public-sector-ai-index-2026) - The Global Public Sector AI Index 2026 is a reproducible, source-grounded, global benchmarking frame...

48. [GAO Report: Federal Agencies Are Not Complying with AI ... - Epic.org](https://epic.org/gao-report-federal-agencies-are-not-complying-with-ai-requirements/) - The report found that of the 20 federal agencies that reported planned and current uses of AI, 15 ag...

49. [Agency AI use doubled in 2024, GAO finds - Nextgov/FCW](https://www.nextgov.com/artificial-intelligence/2025/07/agency-ai-use-doubled-2024-gao-finds/407067/) - In a survey conducted across 11 different agencies, GAO found that documented AI use cases grew from...

50. [Agencies fall short on documenting AI acquisition best ... - FedScoop](https://fedscoop.com/agency-ai-procurement-gao-report/) - A new report from the congressional watchdog found that agencies are not “systematically collecting ...

51. [[PDF] ARTIFICIAL INTELLIGENCE Key Practices to Help Ensure ...](https://www.hsgac.senate.gov/wp-content/uploads/Testimony-Ariga-2023-05-16-REVISED-1.pdf) - Following the forum, GAO developed an AI Accountability Framework of key practices to help ensure re...

52. [AI Guide for Government - IT Modernization Centers of Excellence](https://coe.gsa.gov/coe/ai-guide-for-government/print-all/index.html) - AI Capability Maturity Model (AI CMM), developed by the Artificial Intelligence Center of Excellence...

53. [The AI Readiness Self-Assessment: A Practical Guide for NSOs](https://www.paris21.org/knowledge-base/ai-readiness-self-assessment-practical-guide-nsos) - This guide introduces the AI Readiness SPEEDometer, a structured self-assessment toolkit designed by...

54. [Towards AI-Ready National Statistical Offices: A Framework for ...](https://www.paris21.org/knowledge-base/towards-ai-ready-national-statistical-offices-framework-strengthening-nso-capacity) - The paper also introduces the forthcoming AI Readiness Assessment Toolkit, designed to help NSOs ben...

55. [[PDF] Towards AI-Ready National Statistical Offices - Paris21](https://www.paris21.org/sites/default/files/media/document/2025-12/ai-readiness-nso-framework.pdf) - AI readiness is not a one-time goal but an ongoing process in which the NSO uses AI to strengthen st...

56. [AI-readiness for Official Data and Statistics](https://unstats.un.org/UNSDWebsite/events-details/un57sc-ai-readiness-for-official-data-and-statistics-27Feb2026/) - The objective of AI-readiness of official data and statistics is to provide users who search for and...

57. [[PDF] AI-Ready Official Statistics: Opportunities, Challenges, and ...](https://unstats.un.org/UNSDWebsite/statcom/session_57/documents/BG-5h-CCSA_AI_Readiness_Official_Statistics_v2-E.pdf)

58. [[PDF] ECE/CES/2026/11 Economic and Social Council Distr. - UNECE](https://unece.org/sites/default/files/2026-04/ECE_CES-2026_11_HLG-MOS%20WP2026__ENG.pdf) - workshop on AI-readiness in official statistics (following the 2025 UNECE Workshop on. Generative AI...

59. [Five Dimensions of AI Readiness (AIR-5D) Framework - PubMed](https://pubmed.ncbi.nlm.nih.gov/39543793/)

60. [Five Dimensions of AI Readiness (AIR-5D) Framework- A ...](https://nchr.elsevierpure.com/en/publications/five-dimensions-of-ai-readiness-air-5d-framework-a-preparedness-a/fingerprints/)

61. [an AI-driven technology readiness level assessment tool - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC12236009/) - This paper introduces the Clinical Artificial Intelligence Readiness Evaluator Lifecycle and the Cli...

62. [Health AI Readiness Assessment - Digital Medicine Society (DiMe)](https://dimesociety.org/ai-implementation-in-healthcare-playbook/ai-evaluation-readiness/health-ai-readiness-assessment/) - This interactive self-assessment guides you through a structured review of your organization's readi...

63. [From School AI Readiness to Student AI Literacy - arXiv](https://arxiv.org/html/2603.20056v1)

64. [[PDF] AI Readiness: Building the Bridge from Higher Education to Work](https://www.pearson.com/content/dam/global-store/global/resources/ai-readiness/AI-Readiness-Report-2026.pdf) - AWS brings insight into how AI is deployed across industries and institutions. Pearson brings expert...

65. [Artificial Intelligence, Domain AI Readiness, and Firm Productivity](https://arxiv.org/abs/2508.09634) - We create novel constructs from patent data and measure the domain AI readiness of a specific domain...

66. [[2006.12497] Technology Readiness Levels for AI & ML - arXiv](https://arxiv.org/abs/2006.12497) - Our Technology Readiness Levels for ML (TRL4ML) framework defines a principled process to ensure rob...

67. [Technology Readiness Levels for Machine Learning Systems - arXiv](https://arxiv.org/abs/2101.03989) - Our "Machine Learning Technology Readiness Levels" (MLTRL) framework defines a principled process to...

68. [Technology readiness levels for machine learning systems - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9585100/) - MLTRL defines technology readiness levels (TRLs) to guide and communicate machine learning and artif...

69. [Technology readiness levels for machine learning systems](https://www.nature.com/articles/s41467-022-33128-9)

70. [[PDF] AI Watch: Revisiting Technology Readiness Levels for relevant ...](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC129399/JRC129399_01.pdf) - The aim of this paper is thus to define the maturity of an illustrative set of AI technologies throu...

71. [Rethinking Technological Readiness in the Era of AI Uncertainty](https://arxiv.org/html/2506.11001v1)

72. [Rethinking Technological Readiness in the Era of AI ...](https://arxiv.org/abs/2506.11001)

73. [Metrics and Benchmarks for Human-AI Decision-Making - arXiv](https://arxiv.org/abs/2603.18895) - Abstract page for arXiv paper 2603.18895: From Accuracy to Readiness: Metrics and Benchmarks for Hum...

74. [Building an AI-Ready Public Workforce: A New Imperative for ...](https://digital.nemko.com/news/building-an-ai-ready-public-workforce-a-new-imperative-for-governments) - Public Sector Leaders, Strategic understanding of AI, risk management, AI governance, and change man...

75. [AI in the workplace: A report for 2025 - McKinsey](https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/superagency-in-the-workplace-empowering-people-to-unlock-ais-full-potential-at-work) - This report explores companies' technology and business readiness for AI adoption (see sidebar “Abou...

76. [Is your business actually ready for what's coming in 2026? - SkillPanel](https://skillpanel.com/blog/ai-readiness-assessment/) - A 2025 MIT NANDA report found that 95% of enterprise AI pilots fail to deliver measurable P&L impact...

77. [The State of AI in 2025: Closing the Gap Between Adoption and Impact](https://www.lootzysoft.com/blog/the-state-of-ai-in-2025-closing-the-gap-between-adoption-and-impact) - McKinsey's 2025 State of AI survey reveals a stark gap: 88% of organizations regularly use AI, but o...

78. [AI Readiness - IBM](https://www.ibm.com/think/insights/ai-readiness-thriving-through-ai-disruption)

79. [IBM Study: Chief Data Officers Redefine Strategies as AI Ambitions ...](https://newsroom.ibm.com/2025-11-13-ibm-study-chief-data-officers-redefine-strategies-as-ai-ambitions-outpace-readiness)

80. [Consequence of Resistance to Change on AI Readiness: Mediating ...](https://journals.sagepub.com/doi/10.1177/21582440231217731) - The purpose of this study is to explore the impact of resistance to change on artificial intelligenc...

81. [Organizational AI Readiness - Prosci](https://www.prosci.com/blog/organizational-ai-readiness) - Organizational AI readiness encourages executives and leaders to look beyond tools and infrastructur...

82. [Government AI Landscape Assessment - Code for America](https://codeforamerica.org/explore/government-ai-landscape-assessment/) - In the Readiness stage, the central question is not yet how to deploy AI at scale, but who is accoun...

83. [Artificial intelligence readiness in management education: Scale ...](https://www.sciencedirect.com/science/article/pii/S147281172600073X) - The purpose of this study is to develop and validate an artificial intelligence readiness scale (AIR...

84. [Medical artificial intelligence readiness scale for medical students ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7890640/) - In this study, we have described the development of a valid and reliable psychometric measurement to...

85. [[2410.18725] AI Readiness in Healthcare through Storytelling XAI](https://arxiv.org/abs/2410.18725) - In this research, we have developed an approach that combines multi-task distillation with interpret...

86. [[PDF] AI Readiness Assessment Guide - AI-REAL Toolkit](https://ai-real.dco.org/assets/frontend/images/AI-Readiness-Assessment-Guide.pdf)

87. [AI Data Readiness Checklist - Digital Government Hub](http://digitalgovernmenthub.org/examples/ai-data-readiness-checklist/) - The checklist asks questions on three different areas: Data Governance Framework and Policies; Data ...

88. [Why AI Projects Fail: The 63% Human Factor Problem (And the Fix)](https://bosio.digital/articles/why-ai-projects-fail-human-factors) - 63% of AI implementation failures stem from human factors, not technology. Here's what goes wrong at...

89. [New Absorb Software Report Shows AI Ambition in L&D Outpacing Organizational Readiness, Signaling a Leadership Moment for Learning](https://www.theglobeandmail.com/investing/markets/markets-news/GlobeNewswire/36754691/new-absorb-software-report-shows-ai-ambition-in-ld-outpacing-organizational-readiness-signaling-a-leadership-moment-for-learning/) - GlobeNewswire Press Release.

90. [Data Readiness for AI: A 360-Degree Survey - arXiv](https://arxiv.org/html/2404.05779v2) - This survey aims to propose a taxonomy of data readiness for AI (DRAI) metrics for structured and un...

91. [Public Service in the Age of AI: Institutional Strategies for Future ...](https://dl.acm.org/doi/10.1145/3773002.3773648) - The research identifies that future-ready skills for public servants extend beyond technical profici...

