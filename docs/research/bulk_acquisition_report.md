# Bulk Acquisition Report (candidate register → manifest)

**Task:** cc_tasks/2026-07-03_bulk_acquisition_v2.md  
**Date:** 2026-07-03 (run continued 2026-07-04)  
**Status: INCOMPLETE — Part 1 interrupted; committed at a durable checkpoint.**

**Screening decisions (of 91 candidates):** manifested 27, excluded 2, needs_source 25, pending 37.

Screening decisions live in this register (git-versioned, PRISMA-style); acquisition provenance (TEVV: fetch record, identity check, sha256 + re-hash, page count) lives in the manifest_add events. Acquired PDFs are gitignored (corpus/bulk/); provenance travels in the manifest.

## Interruption / defect (fixed)

The Part 1 driver's sha256 helper contained a dead first loop that re-opened the file each iteration, re-reading the first 64KB forever — an **infinite loop for any PDF ≥ 64KB**. Batches 1–2 never reached it (their pending entries were landing pages → needs_source before the hash step); batch 3 fetched a real PDF, passed identity, entered sha256, and hung (~5.5h, no progress) until killed. The bug is fixed in the driver. **No data corruption:** the hang precedes any write; manifest.verify() reports 0 problems, event log replays clean. **37 candidates remain pending** (mostly HTML landing pages expected to resolve to needs_source; plus the webb_nist_fcsm_crosswalk Zenodo DOI not yet acquired) — a short follow-up run with the fixed driver finishes them.

## Manifested (acquired this bulk run)

- AI Data Readiness Inspector (AIDRIN) — https://arxiv.org/abs/2406.19256
- AI Readiness in Healthcare through Storytelling XAI — https://arxiv.org/abs/2410.18725
- AI Readiness: Building the Bridge from Higher Education to Work — https://www.pearson.com/content/dam/global-store/global/resources/ai-readiness/AI-Readiness-Report-2026.pdf
- AI Watch: Revisiting Technology Readiness Levels for Relevant AI Technologies — https://publications.jrc.ec.europa.eu/repository/bitstream/JRC129399/JRC129399_01.pdf
- AI-Readiness for Official Data and Statistics (UN Statistical Commission side ev — https://unstats.un.org/UNSDWebsite/statcom/session_57/side-events/Friday_Seminar_2026_AI_Readable_Data_Concept_Note.pdf
- AIDRIN 2.0: A Framework to Assess Data Readiness for AI — https://arxiv.org/abs/2505.18213
- America's DataHub RFS (Topic MLMU-25): Measuring LLM Understanding of Federal St — https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf
- Arm AI Readiness Index — https://www.arm.com/resources/report/ai-readiness
- Artificial Intelligence, Domain AI Readiness, and Firm Productivity — https://arxiv.org/abs/2508.09634
- Beyond Model Readiness: Institutional Readiness for AI Deployment in Public Syst — https://arxiv.org/abs/2605.17203
- Cisco AI Readiness Assessment — Survey Instrument (web capture) — https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/assessment-tool.html
- Cisco AI Readiness Index 2025 — Realizing the Value of AI — https://www.cisco.com/c/dam/m/en_us/solutions/ai/readiness-index/2025-m10/documents/cisco-ai-readiness-index-2025-realizing-the-value-of-ai.pdf
- Cisco AI Readiness Index — Methodology (web page capture) — https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/methodology.html
- Data Readiness Levels — https://arxiv.org/abs/1705.02245
- Data Readiness for AI: A 360-Degree Survey — https://arxiv.org/abs/2404.05779
- Data Readiness for Scientific AI at Scale — https://arxiv.org/abs/2507.23018
- FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Da — https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf
- From Accuracy to Readiness: Metrics and Benchmarks for Human-AI Decision-Making — https://arxiv.org/abs/2603.18895
- From School AI Readiness to Student AI Literacy — https://arxiv.org/abs/2603.20056
- GAO AI Accountability Framework (Ariga testimony) — https://www.hsgac.senate.gov/wp-content/uploads/Testimony-Ariga-2023-05-16-REVISED-1.pdf
- MITRE AI Maturity Model — https://aimaturitymodel.mitre.org
- NIST AI Risk Management Framework (AI RMF) — https://doi.org/10.6028/NIST.AI.100-1
- Rethinking Technological Readiness in the Era of AI Uncertainty — https://arxiv.org/abs/2506.11001
- Technology Readiness Levels for AI & ML (TRL4ML) — https://arxiv.org/abs/2006.12497
- Technology Readiness Levels for Machine Learning Systems (MLTRL) — https://arxiv.org/abs/2101.03989
- UNESCO AI Readiness Assessment Methodology (RAM) — https://www.unesco.org/ethics-ai/en/ram
- Why AI Readiness Is an Organizational Learning Problem, Not a Technology Purchas — https://arxiv.org/abs/2604.16369

## Excluded (operator ruling)

- What Is AI-Ready Data? — thin marketing content, no stable versioning; Cisco chosen for industry slot (Desktop 2026-07-03)
- AI Readiness: Thriving Through AI Disruption (IBM) — thin marketing content, no stable versioning; Cisco chosen for industry slot (Desktop 2026-07-03)

## needs_source (no citable/fetchable primary document)

- AI Readiness Scale (AIRS) for Management Education — fetch failed (http=403) — lead: https://www.sciencedirect.com/science/article/pii/S147281172600073X
- AI Readiness in Official Statistics (UNECE HLG-MOS working paper) — fetch failed (http=403) — lead: https://unece.org/sites/default/files/2026-04/ECE_CES-2026_11_HLG-MOS%20WP2026__ENG.pdf
- Are We Ready for AI? From Measurement to Policy Governance (AARS) — fetch failed (http=403) — lead: https://publications.iadb.org/en/are-we-ready-ai-measurement-policy-governance
- Building an AI-Ready Public Workforce — fetch failed (http=403) — lead: https://www.oecd.org/en/publications/building-an-ai-ready-public-workforce_b89244c7-en/full-report.html
- Clinical AI Readiness Evaluator Lifecycle (CARE-L) — resolved PDF https://pmc.ncbi.nlm.nih.gov/articles/PMC12236009/pdf/12911_2025_Article_3099.pdf not fetchable — lead: https://pmc.ncbi.nlm.nih.gov/articles/PMC12236009/
- Consequence of Resistance to Change on AI Readiness — fetch failed (http=403) — lead: https://journals.sagepub.com/doi/10.1177/21582440231217731
- Five Dimensions of AI Readiness (AIR-5D) Framework — landing page, no PDF resolved (ctype=text/html; charset=utf-8) — lead: https://pubmed.ncbi.nlm.nih.gov/39543793/
- From AI to Digital Transformation: The AI Readiness Framework — fetch failed (http=403) — lead: https://www.sciencedirect.com/science/article/pii/S0007681321000744
- Government AI Landscape Assessment (Code for America) — fetch failed (http=403) — lead: https://codeforamerica.org/explore/government-ai-landscape-assessment/
- Government AI Readiness Index 2025 — fetch failed (http=403) — lead: https://oxfordinsights.com/ai-readiness/government-ai-readiness-index-2025/
- Health AI Readiness Assessment (DiMe) — landing page, no PDF resolved (ctype=text/html; charset=UTF-8) — lead: https://dimesociety.org/ai-implementation-in-healthcare-playbook/ai-evaluation-readiness/health-ai-readiness-assessment/
- ITU AI Ready: Analysis Towards a Standardized Readiness Framework — landing page, no PDF resolved (ctype=text/html; charset=utf-8) — lead: https://www.itu.int/epublications/zh/publication/ai-ready-analysis-towards-a-standardized-readiness-framework/en
- Introducing the OECD AI Capability Indicators — fetch failed (http=403) — lead: https://www.oecd.org/en/publications/introducing-the-oecd-ai-capability-indicators_be745f04-en/full-report/component-5.html
- M-25-21: Accelerating Federal Use of AI through Innovation, Governance — OMB memoranda landing page only; no stable PDF (needs source URL) — lead: (none)
- M-25-22: Driving Efficient Acquisition of Artificial Intelligence in G — OMB memoranda landing page only; no stable PDF (needs source URL) — lead: (none)
- MIT NANDA report: 95% of enterprise AI pilots fail to deliver P&L impa — needs source. — lead: (none)
- Making Agentic AI Work for Government: A Readiness Framework — fetch failed (http=403) — lead: https://www.weforum.org/publications/making-agentic-ai-work-for-government-a-readiness-framework/
- McKinsey State of AI 2025 — fetch failed (http=None) — lead: https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai
- Medical AI Readiness Scale for Medical Students (MAIRSE) — resolved PDF https://pmc.ncbi.nlm.nih.gov/articles/PMC7890640/pdf/12909_2021_Article_2546.pdf not fetchable — lead: https://pmc.ncbi.nlm.nih.gov/articles/PMC7890640/
- New Absorb Software Report: AI Ambition in L&D Outpacing Readiness — Only a GlobeNewswire press release URL in doc — needs primary source. — lead: (none)
- Six Areas for Assessing AI Readiness in Government — resolved PDF https://media.defense.gov/2019/Feb/12/2002088963/-1/-1/1/SUMMARY-OF-DOD-AI-STRATEGY.PDF not fetchable — lead: https://www.deloitte.com/us/en/insights/industry/government-public-sector-services/ai-readiness-in-government.html
- Technology Readiness and the Organizational Journey Towards AI Adoptio — fetch failed (http=403) — lead: https://www.sciencedirect.com/science/article/pii/S0268401222001220
- The OECD.AI Index — landing page, no PDF resolved (ctype=text/html; charset=utf-8) — lead: https://oecd.ai/en/
- Towards AI-Ready National Statistical Offices (PARIS21 framework) — fetch failed (http=403) — lead: https://www.paris21.org/sites/default/files/media/document/2025-12/ai-readiness-nso-framework.pdf
- UNDP Artificial Intelligence Readiness Assessment (AIRA) — fetch failed (http=403) — lead: https://www.undp.org/bhutan/publications/artificial-intelligence-readiness-assessment-aira-2024

## pending (not yet screened — follow-up run)

- AI Data Readiness Checklist (Digital Government Hub) — http://digitalgovernmenthub.org/examples/ai-data-readiness-checklist/
- AI Governance, Ethics and Leadership (substack) — Harvey Lab Legal AI  — https://aigovernancelead.substack.com/p/harvey-lab-legal-ai-benchmark-responsible-ai
- AI in Government Act of 2020 — https://www.govinfo.gov/app/details/PLAW-116publ260
- AI-REAL Toolkit: AI Readiness Assessment Guide — https://ai-real.dco.org/assets/frontend/images/AI-Readiness-Assessment-Guide.pdf
- Advancing American AI Act (NDAA FY2023, Div. G) — https://www.govinfo.gov/app/details/PLAW-117publ263
- Bangladesh's AI Readiness: Perspectives — https://arxiv.org/abs/2601.12934
- Census Bureau Statistical Quality Standards — Standard D3: Producing M — https://www.census.gov/about/policies/quality/standards/standardd3.html
- Census Bureau Statistical Quality Standards — Standard F1: Releasing I — https://www.census.gov/about/policies/quality/standards/standardf1.html
- Census Bureau Statistical Quality Standards — Standard F2: Providing D — https://www.census.gov/about/policies/quality/standards/standardf2.html
- Executive Order 13859: Maintaining American Leadership in AI — https://www.federalregister.gov/documents/2019/02/14/2019-02544/maintaining-american-leadership-in-artificial-intelligence
- Executive Order 13960: Promoting the Use of Trustworthy AI in the Fede — https://www.federalregister.gov/documents/2020/12/08/2020-27065/promoting-the-use-of-trustworthy-artificial-intelligence-in-the-federal-government
- Executive Order 14110: Safe, Secure, and Trustworthy Development and U — https://www.federalregister.gov/documents/2023/11/01/2023-24283/safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence
- Executive Order 14179: Removing Barriers to American Leadership in AI — https://www.federalregister.gov/documents/2025/01/31/2025-02172/removing-barriers-to-american-leadership-in-artificial-intelligence
- Executive Order 14319: Preventing Woke AI in the Federal Government — https://www.federalregister.gov/documents/2025/07/28/2025-14217/preventing-woke-ai-in-the-federal-government
- FCSM 19-01: Transparent Reporting for Integrated Data Quality — https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf
- FCSM 20-04: A Framework for Data Quality — https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf
- FCSM 23-02: A Framework for Data Quality: Case Studies — https://statspolicy.gov/assets/fcsm/files/docs/FCSM.23.02_DQ_case_studies_FINAL.pdf
- Foundations for Evidence-Based Policymaking Act of 2018 (Evidence Act) — https://www.govinfo.gov/app/details/PLAW-115publ435
- GSA AI Guide for Government / AI Capability Maturity Model (AI CMM) — https://coe.gsa.gov/coe/ai-guide-for-government/print-all/index.html
- Generative AI and Open Data: Guidelines and Best Practices (Dept. of C — https://www.commerce.gov/news/blog/2025/01/generative-artificial-intelligence-and-open-data-guidelines-and-best-practices
- Global Public Sector AI Index 2026 — https://alicelabs.ai/reports/global-public-sector-ai-index-2026
- Information Quality Act (Data Quality Act) — sec. 515 of P.L. 106-554 — https://www.govinfo.gov/app/details/PLAW-106publ554
- M-19-23: Phase 1 Implementation of the Evidence Act — https://www.whitehouse.gov/wp-content/uploads/2019/07/M-19-23.pdf
- M-24-10: Advancing Governance, Innovation, and Risk Management for Age — https://bidenwhitehouse.archives.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-and-Risk-Management-for-Agency-Use-of-Artificial-Intelligence.pdf
- M-24-18: Advancing the Responsible Acquisition of AI in Government — https://bidenwhitehouse.archives.gov/wp-content/uploads/2024/10/M-24-18-AI-Acquisition-Memorandum.pdf
- M-25-05: Phase 2 Implementation of the Evidence Act — Open Government  — https://bidenwhitehouse.archives.gov/wp-content/uploads/2025/01/M-25-05-Phase-2-Implementation-of-the-Foundations-for-Evidence-Based-Policymaking-Act-of-2018-Open-Government-Data-Access-and-Management-Guidance.pdf
- M-26-04: Increasing Public Trust in AI Through Unbiased AI Principles — https://www.whitehouse.gov/wp-content/uploads/2025/12/M-26-04-Increasing-Public-Trust-in-Artificial-Intelligence-Through-Unbiased-AI-Principles-1.pdf
- NIST AI 100-3: The Language of Trustworthy AI — An In-Depth Glossary o — https://doi.org/10.6028/NIST.AI.100-3
- NIST AI RMF Playbook — https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook
- NIST Generative AI Profile (AI 600-1) — https://doi.org/10.6028/NIST.AI.600-1
- Organizational AI Readiness (Prosci / ADKAR) — https://www.prosci.com/blog/organizational-ai-readiness
- Public Service in the Age of AI: Institutional Strategies for Future-R — https://dl.acm.org/doi/10.1145/3773002.3773648
- Statistical Policy Working Paper 46: Data Quality Assessment Tool for  — https://statspolicy.gov/assets/fcsm/files/docs/DataQualityAssessmentTool.pdf
- The Nation's Data at Risk: First Annual Report on the Federal Statisti — https://hdsr.mitpress.mit.edu/pub/m3fk4fah/release/1
- Webb: NIST x FCSM Crosswalk (Data Quality <-> AI Trustworthiness) — https://doi.org/10.5281/zenodo.18772590
- Why AI Projects Fail: The 63% Human Factor Problem — https://bosio.digital/articles/why-ai-projects-fail-human-factors
- Winning the Race: America's AI Action Plan — https://www.whitehouse.gov/wp-content/uploads/2025/07/Americas-AI-Action-Plan.pdf
