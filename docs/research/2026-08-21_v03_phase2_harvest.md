# Phase 2 — Kernel harvest to staging (task 2026-08-21_v03_visibility_kernel)

**Date:** 2026-08-21 (UTC run window 21:40–21:44)
**Task:** `cc_tasks/2026-08-21_v03_visibility_kernel.md`, "Phase 2 — Kernel harvest to staging"
**Spend:** zero model calls. `ANTHROPIC_API_KEY` unset throughout (the script refuses to start if it is set).
**Inclusion rule:** written verbatim before any fetch to `docs/research/2026-08-21_kernel_inclusion_rule.md` (diffed against the task text: identical).
**Config / code:** `scripts/kernel_list.yaml` (68 entries, the kernel list transcribed with per-entry `clause`, `source_type`, URLs, extent rules, task discrepancies) and `scripts/harvest_kernel.py` (bounded, idempotent; a second run skips all 63 fetched documents by sha256 and appends nothing).
**Outputs:** `corpus/staging/inbox/kernel/` (63 files + `_fetch_register.json`, the machine-readable manifest for Phase 3); 68 lines appended to `corpus/staging/candidate_register.jsonl` (lines 1–91 byte-identical to HEAD, verified by sha256; file now 159 lines); `corpus/staging/refetch_candidates.jsonl` untouched at 721 lines (nothing ended in `oversize_needs_clearance`). Nothing manifest-added; no events, kg/, tests/, schema docs, controls.yaml or dixie_evidence.yaml touched; no git commit.

## 1. Register summary by `candidate_status`

| candidate_status | count | notes |
|---|---|---|
| fetched | 63 | 21 standard (clause a), 25 industry (b), 8 academic (c), 9 federal (d) |
| fetch_failed | 1 | Akamai Bot Manager docs — SAML login-gated (see §5) |
| excluded_by_rule | 4 | Census D3/F1/F2 `already_manifested` (task said do not refetch); SME "Visibility Diagnostic" file `no_fetchable_primary_text` (not in inbox, no URL — Phase 0 recorded the same) |
| oversize_needs_clearance | 0 | both documents that exceeded 250K raw were brought under it at a stated extent (§3) |
| **total** | **68** | task expected ≈45–55; the overshoot is the schema.org 7 type pages counted individually (as the task instructs), 2 DCAT-US 3.0 pages, 2 SDMX, 2 Akamai, 2 Cloudflare, 3 Census entries that are exclusions |

**Total characters fetched (text, after extent trims): 2,615,136** across the 63 fetched documents (PDF chars = pypdf text; markdown chars = the saved markdown body, excluding the one-line provenance header comment).

## 2. Acquisition path (what was actually run)

- PDFs: direct `httpx` GET (UA `WintermuteAcceptance/0.1 (research; brockwebb45@gmail.com)`, 60 s timeout, one retry, 1 s spacing); text via pypdf; `as_of` from PDF `/ModDate` (else `/CreationDate`, else HTTP Last-Modified).
- Web pages: crawl4ai `crwl crawl URL -o all -f <pruning filter threshold 0.48> -bc`. The saved body is crwl's **fit_markdown** (crwl's own boilerplate pruning; nothing hand-edited) unless fit is < 5 % of raw_markdown, in which case raw_markdown is kept (`fit_min_fraction_of_raw` in config; set after inspecting every page at ratio < 0.3 — Google Search Central and the Intercom help page carry 80–95 % navigation by character count and their fit output was the complete article in each case). Variant used is recorded per document (`markdown_variant`). `as_of` from page meta (`article:modified_time` etc.), else HTTP Last-Modified, else `null` with a source note.
- Plain-text sources (RFC text, GitHub READMEs, Akamai's own `<page>.md` endpoint): `httpx` GET saved as-is behind a one-line provenance comment.
- **Fallback forced by hosts:** `www.w3.org` serves a Cloudflare "Performing security verification" interstitial to the headless browser (plain httpx GET returns 200). The script detects challenge markers and falls back to httpx + a small DOM→markdown converter (`DomMarkdown` in the script: headings, paragraphs, lists, tables, code, definition lists; `nav` dropped). The same path is used for every document with an AUTH-4 extent trim, because trimming is done on the DOM by h2 section.
- `crwl_params` per entry for JS-only pages: the Bing Webmaster help center rendered a 199-char shell without `wait_until=networkidle,delay_before_return_html=4`.
- Min-content guard: < 200 chars of text → `fetch_failed`, capture not kept (fired once: Akamai Bot Manager, 14 chars = the SAML redirect shell).
- File headers carry no timestamp so identical content hashes identically on re-runs; `retrieved_at_utc` lives in the registers.

## 3. Five largest documents and the extent decision for each (AUTH-4, MAX_DOC_CHARS = 250,000)

| chars | doc_id | decision |
|---|---|---|
| 227,094 | `openapi-specification-core` (OAS 3.2.0, spec.openapis.org/oas/latest.html, as_of 2025-09-19) | Whole page is 274,781 chars of text → trimmed to the **core sections**: front matter + §1 OpenAPI Specification, §2 Introduction, §3 Format, §4 Objects and Fields, §5 Specification Extensions, §6 Security Considerations. **Excluded:** Table of Contents; Appendix A Revision History; B Data Type Conversion; C RFC6570-based serialization; D Serializing Headers and Cookies; E Percent-Encoding and Form Media Types; F Examples of Base URI Determination; G Parsing and Resolution Guidance; H References. `extent_dropped_sections` lists the exact headings removed. |
| 194,688 | `w3c-dcat-3` (W3C Rec 22 Aug 2024) | Whole Rec is 249,947 chars of text (over the cap once markdown tables are rendered) → **normative core**: §1–§18 + Appendix A Acknowledgments + Appendix B Alignment with Schema.org. **Excluded:** ToC; C. Examples; D. Change history; E–J change logs since earlier drafts; K. References. |
| 176,995 | `w3c-dwbp-2017` (W3C Rec 31 Jan 2017) | Under the cap: **whole Recommendation**; only the ToC navigation block dropped. |
| 119,318 | `chen-2025-geo-how-to-dominate-ai-search` (arXiv 2509.08919 PDF) | Whole document, no trim. |
| 114,789 | `miroyan-2025-search-arena` (arXiv 2506.05334 PDF) | Whole document, no trim. |

Other extent decisions: `w3c-rdf-data-cube` 103,544 chars — the Rec fits, so the task's "primer if oversize" fallback was not needed (whole Rec, ToC dropped). `w3c-json-ld-1-1-core` 71,277 chars — see discrepancy D2: no steward primer exists; the Rec was manifested at a primer-equivalent stated extent (§1 Introduction, §2 Conformance, §3 Basic Concepts, §8 Data Model; excluded §4 Advanced Concepts [187K of the 383K], §5–7, §9–13, appendices A–J).

During development one run registered `openapi-specification-core` as `oversize_needs_clearance` (277,030 chars) because the extent trim missed the OpenAPI site's flat section markup (appendix h3 blocks are siblings of the h2 wrapper, not children). The trim was fixed (`apply_extent` climbs to the outermost wrapper whose first h2 is the heading and removes following siblings up to the next h2). Development-run register lines and the corresponding `refetch_candidates.jsonl` lines were discarded and the registers restored to their pre-session state (candidate_register back to the 91 HEAD lines, refetch_candidates back to 721) before the single final pass whose results are reported here, so the registers carry one line per kernel entry rather than a development history. `_fetch_register.json` is from that final pass only.

## 4. Research-paper selection (the "cap 5" item)

**Selection rule (declared before ranking):**
1. Candidate pool = union of arXiv API (`export.arxiv.org/api/query`, relevance order, 40 results per query) hits for nine queries, restricted to `published >= 2025-01-01`: `"generative engine optimization"`; `"generative engines" AND citation`; `"AI search" AND citation AND web`; `"AI overviews"`; `LLM AND "web search" AND citation AND sources`; `"answer engines" AND citation`; `"search engines" AND "large language models" AND "cited sources"`; `"AI crawlers" AND web`; `"retrieval-augmented" AND "web search" AND "citation accuracy"` (0 hits). 72 distinct papers.
2. Enrich each with Semantic Scholar Graph API (`/paper/batch`, fields citationCount, venue).
3. Topical screen: the paper's object of study must be how LLM / generative-search systems retrieve or cite **web content** (citation behavior, source selection, visibility of web pages). Screened out: agent-capability benchmarks, adversarial-robustness defenses, hallucination benchmarks, domain product-ranking testbeds.
4. Rank by S2 citationCount descending; tie-break: peer-reviewed venue over arXiv-only; then earliest publication. Cap 5.
5. GEO (arXiv 2311.09735) is excluded from this pool because the task names it separately.

**Selected (all fetched as arXiv PDFs):**
1. 2509.08919 — Chen et al., *Generative Engine Optimization: How to Dominate AI Search* (30 citations, arXiv) → `chen-2025-geo-how-to-dominate-ai-search`
2. 2506.05334 — Miroyan et al., *Search Arena: Analyzing Search-Augmented LLMs* (25, arXiv) → `miroyan-2025-search-arena`
3. 2510.11438 — Wu et al., *What Generative Search Engines Like and How to Optimize Web Content Cooperatively* (14, arXiv) → `wu-2025-what-generative-search-engines-like`
4. 2509.04499 — Venkit et al., *DeepTRACE: Auditing Deep Research AI Systems for Tracking Reliability Across Citations and Evidence* (11, arXiv) → `venkit-2025-deeptrace`
5. 2511.12920 — Hu et al., *Auditing Google's AI Overviews and Featured Snippets: A Case Study on Baby Care and Pregnancy* (5, ICWSM proceedings; chosen among the nine 5-citation papers by the peer-reviewed-venue tie-break, then earliest date) → `hu-2025-auditing-google-ai-overviews`

Screened out despite higher citation counts: 2508.06600 BrowseComp-Plus (164; deep-research agent benchmark), 2509.23519 ReliabilityRAG (18, NeurIPS; robustness defense), 2511.20867 E-GEO (10; e-commerce testbed), 2602.01031 HalluHard (6; hallucination benchmark). Semantic Scholar citation counts are as of 2026-08-21 and are the ranking signal only; they are not recorded as facts about the papers.

**All 72 candidates considered:**

| arXiv | published | S2 citations | S2 venue | title | decision |
|---|---|---|---|---|---|
| 2508.06600 | 2025-08-08 | 164 | arXiv.org | BrowseComp-Plus: A More Fair and Transparent Evaluation Benchmark of Deep-Research Agent | screened out: agent-capability benchmark (deep-research evaluation), not a study of citation/retrieval behavior toward web content |
| 2509.08919 | 2025-09-10 | 30 | arXiv.org | Generative Engine Optimization: How to Dominate AI Search | SELECTED (rank 1) |
| 2506.05334 | 2025-06-05 | 25 | arXiv.org | Search Arena: Analyzing Search-Augmented LLMs | SELECTED (rank 2) |
| 2509.23519 | 2025-09-27 | 18 | Neural Information Processing Systems | ReliabilityRAG: Effective and Provably Robust Defense for RAG-based Web-Search | screened out: adversarial-robustness defense for RAG, not a study of citation/retrieval behavior |
| 2510.11438 | 2025-10-13 | 14 | arXiv.org | What Generative Search Engines Like and How to Optimize Web Content Cooperatively | SELECTED (rank 3) |
| 2509.04499 | 2025-09-02 | 11 | arXiv.org | DeepTRACE: Auditing Deep Research AI Systems for Tracking Reliability Across Citations and Evidence | SELECTED (rank 4) |
| 2511.20867 | 2025-11-25 | 10 | arXiv.org | E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | screened out: e-commerce product-ranking testbed; not web-content citation behavior |
| 2602.01031 | 2026-02-01 | 6 | arXiv.org | HalluHard: A Hard Multi-Turn Hallucination Benchmark | screened out: hallucination benchmark; web citation not its object |
| 2511.12920 | 2025-11-17 | 5 | Proceedings of the International AAAI Conference on Web and  | Auditing Google's AI Overviews and Featured Snippets: A Case Study on Baby Care and Pregnancy | SELECTED (rank 5; peer-reviewed venue tie-break among 5-citation papers) |
| 2601.12263 | 2026-01-18 | 5 | Proceedings of the 4th Workshop on Towards Knowledgeable Fou | Multimodal Generative Engine Optimization: Rank Manipulation for Vision-Language Model Rankers | not in top 5 by citations |
| 2602.12187 | 2026-02-12 | 5 | Proceedings of the 32nd ACM SIGKDD Conference on Knowledge D | SAGEO Arena: A Realistic Environment for Evaluating Search-Augmented Generative Engine Optimization | not in top 5 by citations |
| 2601.22493 | 2026-01-30 | 5 | arXiv.org | Do AI Overviews Benefit Search Engines? An Ecosystem Perspective | not in top 5 by citations |
| 2602.13415 | 2026-02-13 | 5 | arXiv.org | The Rise of AI Search: Implications for Information Markets and Human Judgement at Scale | not in top 5 by citations |
| 2603.20213 | 2026-03-02 | 5 | arXiv.org | AgenticGEO: A Self-Evolving Agentic System for Generative Engine Optimization | not in top 5 by citations |
| 2603.16138 | 2026-03-17 | 5 | arXiv.org | Answer Bubbles: Information Exposure in AI-Mediated Search | not in top 5 by citations |
| 2605.29107 | 2026-05-27 | 5 | arXiv.org | GEO-Bench: Benchmarking Ranking Manipulation in Generative Engine Optimization | not in top 5 by citations |
| 2606.20065 | 2026-06-18 | 5 | arXiv.org | Generative Engine Optimization at Scale: Measuring Brand Visibility Across AI Search Engines | not in top 5 by citations |
| 2604.27790 | 2026-04-30 | 4 | Annual International ACM SIGIR Conference on Research and De | How Generative AI Disrupts Search: An Empirical Study of Google Search, Gemini, and AI Overviews |  |
| 2507.03169 | 2025-07-03 | 4 | arXiv.org | Beyond SEO: A Transformer-Based Approach for Reinventing Web Content Optimisation |  |
| 2510.00361 | 2025-10-01 | 4 | arXiv.org | Attribution Gradients: Incrementally Unfolding Citations for Critical Examination of Attributed AI Answers |  |
| 2602.18455 | 2026-02-05 | 4 | arXiv.org | Impact of AI Search Summaries on Website Traffic: Evidence from Google AI Overviews and Wikipedia |  |
| 2604.19113 | 2026-04-21 | 3 | Annual Meeting of the Association for Computational Linguist | Think Before Writing: Feature-Level Multi-Objective Optimization for Generative Citation Visibility |  |
| 2603.09296 | 2026-03-10 | 3 | arXiv.org | Diagnosing and Repairing Citation Failures in Generative Engine Optimization |  |
| 2603.29979 | 2026-03-31 | 3 | arXiv.org | Structural Feature Engineering for Generative Engine Optimization: How Content Structure Shapes Citation Behav |  |
| 2604.07585 | 2026-04-08 | 3 | arXiv.org | Don't Measure Once: Measuring Visibility in AI Search (GEO) |  |
| 2604.25707 | 2026-04-28 | 3 | arXiv.org | From Citation Selection to Citation Absorption: A Measurement Framework for Generative Engine Optimization Acr |  |
| 2606.28356 | 2026-06-08 | 3 | arXiv.org | SafeGEO: Understanding Generative Engine Optimization Risks in Recommendation Agents |  |
| 2606.13669 | 2026-06-11 | 3 | arXiv.org | Agents-K1: Towards Agent-native Knowledge Orchestration |  |
| 2606.16344 | 2026-06-15 | 3 | arXiv.org | Whose hotel does the AI recommend? An algorithm audit of reputation signals in LLM-assisted hotel selection |  |
| 2510.10315 | 2025-10-11 | 2 | The Web Conference | Is Misinformation More Open? A Study of robots.txt Gatekeeping on the Web |  |
| 2601.13938 | 2026-01-20 | 2 | Annual Meeting of the Association for Computational Linguist | IF-GEO: Conflict-Aware Instruction Fusion for Multi-Query Generative Engine Optimization |  |
| 2604.19516 | 2026-04-21 | 2 | Annual Meeting of the Association for Computational Linguist | From Experience to Skill: Multi-Agent Generative Engine Optimization via Reusable Strategy Learning |  |
| 2605.25517 | 2026-05-25 | 2 | Annual International ACM SIGIR Conference on Research and De | What Gets Cited: Competitive GEO in AI Answer Engines |  |
| 2509.10762 | 2025-09-13 | 2 |  | AI Answer Engine Citation Behavior An Empirical Analysis of the GEO16 Framework |  |
| 2601.00912 | 2026-01-01 | 2 | arXiv.org | The Discovery Gap: How Product Hunt Startups Vanish in LLM Organic Discovery Queries |  |
| 2605.12887 | 2026-05-13 | 2 | arXiv.org | EcoGEO: Trajectory-Aware Evidence Ecosystems for Web-Enabled LLM Search Agents |  |
| 2605.23684 | 2026-05-22 | 2 | arXiv.org | Synthetic Sources?: Auditing Generative Search Engine Citations for Evidence of AI-Generated Sources |  |
| 2601.17109 | 2026-01-23 | 1 | medRxiv | Authority Signals in AI Cited Health Sources: A Framework for Evaluating Source Credibility in ChatGPT Respons |  |
| 2508.06470 | 2025-08-08 | 1 | arXiv.org | Generative AI and the Future of the Digital Commons: Five Open Questions and Knowledge Gaps |  |
| 2510.06823 | 2025-10-08 | 1 | arXiv.org | Exposing Citation Vulnerabilities in Generative Engines |  |
| 2602.02961 | 2026-02-03 | 1 | arXiv.org | Generative Engine Optimization: A VLM and Agent Framework for Pinterest Acquisition Growth |  |
| 2603.12282 | 2026-03-05 | 1 | arXiv.org | Algorithmic Trust and Compliance: Benchmarking Brand Notability for UK iGaming Entities in Generative Search E |  |
| 2603.08924 | 2026-03-09 | 1 | arXiv.org | Quantifying Uncertainty in AI Visibility: A Statistical Framework for Generative Search Measurement |  |
| 2605.09314 | 2026-05-10 | 1 | arXiv.org | How LLMs Are Persuaded: A Few Attention Heads, Rerouted |  |
| 2605.14021 | 2026-05-13 | 1 | arXiv.org | Measuring Google AI Overviews: Activation, Source Quality, Claim Fidelity, and Publisher Impact |  |
| 2606.12439 | 2026-05-18 | 1 | arXiv.org | Position: Generative Engine Optimization Creates Underexamined Risks, Governance Must Target Concentration, Di |  |
| 2605.21948 | 2026-05-21 | 1 | arXiv.org | SCI-Defense: Defending Manipulation Attacks from Generative Engine Optimization |  |
| 2606.17443 | 2026-06-16 | 1 | arXiv.org | Incumbent Advantage: Brand Bias and Cognitive Manipulation Dynamics in LLM Recommendation Systems |  |
| 2607.14035 | 2026-07-15 | 1 |  | Optimizing Visibility in Generative Engines: A Critical Survey of Generative Engine Optimization (2023-2026) |  |
| 2508.03130 | 2025-08-05 | 0 | arXiv.org | Protecting Small Organizations from AI Bots with Logrip: Hierarchical IP Hashing |  |
| 2510.09031 | 2025-10-10 | 0 | arXiv.org | Web Crawler Restrictions, AI Training Datasets \&amp; Political Biases |  |
| 2512.02665 | 2025-12-02 | 0 | arXiv.org | Input Order Shapes LLM Semantic Alignment in Multi-Document Summarization |  |
| 2602.22221 | 2025-12-15 | 0 |  | Evaluating Reliability Asymmetries in Chinese Factual Search and AI Answers |  |
| 2601.00869 | 2025-12-30 | 0 | arXiv.org | Cultural Encoding in Large Language Models: The Existence Gap in AI-Mediated Brand Discovery |  |
| 2603.29071 | 2026-03-30 | 0 | arXiv.org | An Economic Framework for Generative Engines: Advertising or Subscription? |  |
| 2604.03656 | 2026-04-04 | 0 | arXiv.org | Beyond Retrieval: Modeling Confidence Decay and Deterministic Agentic Platforms in Generative Engine Optimizat |  |
| 2605.01077 | 2026-05-01 | 0 | arXiv.org | Teaching LLMs Brazilian Healthcare: Injecting Knowledge from Official Clinical Guidelines |  |
| 2605.04949 | 2026-05-06 | 0 | arXiv.org | AllSERP: Exhaustive Per-Element Enrichment of the Versatile AdSERP Dataset |  |
| 2605.08583 | 2026-05-09 | 0 | arXiv.org | Source or It Didn't Happen: A Multi-Agent Framework for Citation Hallucination Detection |  |
| 2605.16428 | 2026-05-14 | 0 | arXiv.org | The Impact of AI Search on the Online Content Ecosystem: Evidence from Google and Reddit |  |
| 2605.27700 | 2026-05-26 | 0 | arXiv.org | CiteCheck: Retrieval-Grounded Detection of LLM Citation Hallucinations in Scientific Text |  |
| 2606.11337 | 2026-06-09 | 0 | arXiv.org | Can AI Agents Synthesize Scientific Conclusions? |  |
| 2606.27736 | 2026-06-26 | 0 | arXiv.org | ToE: A Hierarchical and Explainable Claim Verification Framework with Dynamic Multi-source Evidence Retrieval  |  |
| 2607.03421 | 2026-07-03 | 0 |  | AI Overviews in Academic Search: Evaluating AI-generated Summaries of Search Results in a Domain-specific Sear |  |
| 2607.05217 | 2026-07-06 | 0 |  | Curated retrieval versus open web search in public AI information services: a coverage-trust trade-off |  |
| 2607.12056 | 2026-07-13 | 0 |  | Designing Agent-Ready Websites for AI Web Agents: A Framework for Machine Readability, Actionability, and Deci |  |
| 2607.14197 | 2026-07-15 | 0 |  | How Artificial Intelligence LLM Engines Shape the Global Conflict Information Environment |  |
| 2607.20730 | 2026-07-22 | 0 |  | GPE: Evaluating Robust Evidence Aggregation for Fact Verification under Controllable GEO-Style Poisoning |  |
| 2608.04831 | 2026-08-05 | 0 |  | Investigating Click Behaviors On Google Search Result Pages That Produce an AI Overview |  |
| 2608.11390 | 2026-08-11 | 0 |  | Mechanism Design for Generative Engines: From Exploitation toward Win-Win Outcomes |  |
| 2608.16824 | 2026-08-17 | 0 |  | GEO-Flag: Detecting and Measuring GEO-Optimized Web Content |  |
| 2608.18352 | 2026-08-18 | 0 |  | AI in Search Reduces Publisher Referrals Without Improving User Experience: Experimental Evidence |  |

## 5. Fetch failures (every one, with URLs tried)

| doc_id | URLs tried (in order) | outcome |
|---|---|---|
| `akamai-bot-manager-bot-reports` | https://techdocs.akamai.com/bot-manager/docs → https://techdocs.akamai.com/bot-manager/docs/bot-reports → https://techdocs.akamai.com/bot-manager/docs/welcome-bot-manager → https://techdocs.akamai.com/bot-manager/reference/api (also probed: `…/bot-reports.md`, `…/welcome-bot-manager.md`, `…/bot-manager/llms.txt`) | every URL 302s to `control.akamai.com/apps/auth/?SAMLRequest=…` (the `.md`/`llms.txt` variants to `techdocs.akamai.com/dual-login`). Bot Manager documentation is customer-login-gated; min-content guard fired (14 chars). `fetch_failed`, registered `needs_source`. Operator-inbox item if wanted: an Akamai Control Center login would be required. |

Resolved before the final pass (not failures in the register, recorded here because the first URL tried did not work):
- `jacobsen-2020-fair-principles-interpretations`: `direct.mit.edu/dint/article-pdf/2/1-2/10/1893405/dint_r_00024.pdf` → 403; `direct.mit.edu/dint/article/2/1-2/10/10017/...` → 403 (httpx) / Cloudflare challenge (crwl); `doi.org/10.1162/dint_r_00024` → connection refused (twice). Fetched from the publisher's legacy open-access URL `https://www.mitpressjournals.org/doi/pdf/10.1162/dint_r_00024` (listed as `openAccessPdf` by Semantic Scholar for the DOI; served by silverchair). 65,886 chars.
- `bing-webmaster-guidelines`: 199-char JS shell on first attempt; fetched after adding a render wait (14,480 chars).
- `bing-webmaster-api-docs`: `bing.com/webmasters/help/webmaster-api-2f13c4a1` → 404; current home is `learn.microsoft.com/en-us/bingwebmaster/` (fetched).
- `cloudflare-content-signals-policy`: `www.cloudflare.com/content-signals-policy/` → 404; the policy lives at `https://contentsignals.org/` (JS-rendered; 2 KB shell to plain GET, full text via crwl — 5,669 chars).

## 6. Discrepancies vs the task text

- **D1 — "Visibility Diagnostic" SME file:** not present in `corpus/staging/inbox/` (Phase 0 found the same). Registered `excluded_by_rule` / `no_fetchable_primary_text` rather than silently omitted; there is no clause-(e) document in this harvest.
- **D2 — "JSON-LD 1.1 primer":** W3C publishes no JSON-LD 1.1 primer. `json-ld.org/primer/latest/` is an abandoned, explicitly "very incomplete … should not be relied upon" 1.0-era draft (8.7K chars) and was not taken. Per AUTH-4 the JSON-LD 1.1 Recommendation was manifested at a primer-equivalent stated extent (see §3).
- **D3 — "SDMX technical standard primer":** sdmx.org publishes no document titled "primer". Taken: the sdmx.org Standards page (`sdmx-standards-overview`) and the steward's own overview volume, *SDMX 3.0 Technical Specifications, Section 1: Framework for SDMX Technical Standards* (PDF, 68,162 chars).
- **D4 — "DCAT-US 3.0 (resources.data.gov)":** lives at `resources.data.gov/resources/dcat-us3/` (overview) plus per-class schema pages under `/standards/catalog/dcat-us-3/`; the overview and the Dataset class page were taken as two documents. The task's separate "data.gov / resources.data.gov metadata requirements (DCAT-US schema page)" item is the v1.1 schema page `resources.data.gov/resources/dcat-us/` (`dcat-us-1-1-schema`, 85,896 chars), registered under clause (d).
- **D5 — Bing "Webmaster APIs":** the bing.com help-center API page no longer exists (404); the API documentation is on Microsoft Learn (`learn.microsoft.com/en-us/bingwebmaster/`, fetched). The **AI Performance announcement** is the Bing Webmaster Blog post *Introducing AI Performance in Bing Webmaster Tools Public Preview* (February 2026 path; located via the JS-rendered blog index), fetched; its page exposes no machine-readable date (`as_of` null; the path segment `February-2026` is the only date evidence).
- **D6 — Cloudflare "Content Signals Policy":** published at contentsignals.org, not under cloudflare.com (404 there). Fetched from contentsignals.org.
- **D7 — Akamai "Bot Manager bot reports docs":** login-gated; `fetch_failed` (§5). Akamai **DataStream 2**: the docs "welcome" page is a thin landing hub (11K chars, half navigation), so the substantive log-field reference *Data set parameters* was added as a second DataStream entry via Akamai TechDocs' own `<page>.md` endpoint (60,283 chars).
- **D8 — Platform crawler docs:** OpenAI's page redirects `platform.openai.com/docs/bots` → `developers.openai.com/api/docs/bots` (fetched, 21,497 chars); Anthropic's support article now redirects to `support.claude.com` (fetched; crwl's fit output drops the H1 but the full article body, bot table and robots.txt examples are present); Perplexity's redirects to `docs.perplexity.ai/docs/resources/perplexity-crawlers` (fetched). `final_url` is recorded for each.
- **D9 — W3C Cloudflare challenge:** `www.w3.org/TR/*` served an anti-bot interstitial to crawl4ai's headless browser; fetched with plain httpx + DOM conversion (method recorded as `httpx-dom`). This is a departure from "web pages → markdown via crawl4ai" forced by the host.
- **D10 — Count:** 68 entries vs the task's ≈45–55 expectation (explained in §1).
- **D11 — `as_of` null for 24 fetched documents** (schema.org type pages, Cloudflare docs, OpenAI/Anthropic/Perplexity crawler pages, Bing pages, RFC text, GitHub raw READMEs, Akamai .md): no page-declared date and no HTTP Last-Modified. Left null with an `as_of_source` note rather than guessed; several carry a date in the body text (e.g. RFC 9309 "September 2022", Cloudflare "Aug 14, 2026", Akamai frontmatter `updatedAt: 2026-06-08`) that Phase 3 may cite from the document itself.
- **PDF `as_of` caveat:** for PDFs the recorded `as_of` is the file's `/ModDate` (e.g. P.L. 115-336 shows 2026-01-02 because govinfo re-rendered the file; Jacobsen 2020 shows 2026-08-21 from silverchair watermarking). The document's own date is carried in `year` on the register line and in the text; `as_of_source` names which field was used.

## 7. Full register (from `_fetch_register.json`)

| doc_id | status | clause | chars | as_of (source) | fetch method | local_path |
|---|---|---|---|---|---|---|
| schema-org-dataset | fetched | a | 52323 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-dataset.md |
| schema-org-datacatalog | fetched | a | 36359 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-datacatalog.md |
| schema-org-datadownload | fetched | a | 41380 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-datadownload.md |
| schema-org-datafeed | fetched | a | 41110 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-datafeed.md |
| schema-org-webapi | fetched | a | 9502 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-webapi.md |
| schema-org-softwareapplication | fetched | a | 49264 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-softwareapplication.md |
| schema-org-definedterm | fetched | a | 30100 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/schema-org-definedterm.md |
| w3c-dcat-3 | fetched | a | 194688 | 2024-08-22 (time[datetime]) | httpx-dom | corpus/staging/inbox/kernel/w3c-dcat-3.md |
| dcat-us-3-overview | fetched | a | 51582 | 2026-08-21 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/dcat-us-3-overview.md |
| dcat-us-3-dataset-schema | fetched | a | 86350 | 2026-08-21 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/dcat-us-3-dataset-schema.md |
| w3c-dwbp-2017 | fetched | a | 176995 | 2017-01-31 (time[datetime]) | httpx-dom | corpus/staging/inbox/kernel/w3c-dwbp-2017.md |
| w3c-rdf-data-cube | fetched | a | 103544 | 2014-01-16 (time[datetime]) | httpx-dom | corpus/staging/inbox/kernel/w3c-rdf-data-cube.md |
| sdmx-standards-overview | fetched | a | 11187 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/sdmx-standards-overview.md |
| sdmx-3-0-section-1-framework | fetched | a | 68162 | 2021-09-13 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/sdmx-3-0-section-1-framework.pdf |
| mlcommons-croissant-spec | fetched | a | 63880 | 2026-07-15 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/mlcommons-croissant-spec.md |
| sitemaps-protocol | fetched | a | 25687 | 2022-12-15 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/sitemaps-protocol.md |
| rfc-9309-robots-exclusion-protocol | fetched | a | 25261 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/rfc-9309-robots-exclusion-protocol.md |
| llmstxt-proposal | fetched | a | 13290 | 2026-08-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/llmstxt-proposal.md |
| indexnow-documentation | fetched | a | 10114 | 2026-02-11 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/indexnow-documentation.md |
| w3c-json-ld-1-1-core | fetched | a | 71277 | 2020-07-16 (time[datetime]) | httpx-dom | corpus/staging/inbox/kernel/w3c-json-ld-1-1-core.md |
| openapi-specification-core | fetched | a | 227094 | 2025-09-19 (time[datetime]) | httpx-dom | corpus/staging/inbox/kernel/openapi-specification-core.md |
| google-structured-data-intro | fetched | b | 9433 | 2025-12-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/google-structured-data-intro.md |
| google-dataset-structured-data | fetched | b | 34109 | 2025-12-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/google-dataset-structured-data.md |
| google-crawling-indexing-overview | fetched | b | 5050 | 2025-12-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/google-crawling-indexing-overview.md |
| google-robots-txt-intro | fetched | b | 6439 | 2025-12-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/google-robots-txt-intro.md |
| google-ai-features-and-your-website | fetched | b | 8787 | 2025-12-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/google-ai-features-and-your-website.md |
| google-search-console-start | fetched | b | 6933 | 2025-12-10 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/google-search-console-start.md |
| bing-ai-performance-public-preview-2026 | fetched | b | 6941 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/bing-ai-performance-public-preview-2026.md |
| bing-webmaster-guidelines | fetched | b | 14480 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/bing-webmaster-guidelines.md |
| bing-webmaster-api-docs | fetched | b | 3520 | 2026-08-07 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/bing-webmaster-api-docs.md |
| cloudflare-ai-crawl-control | fetched | b | 3204 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/cloudflare-ai-crawl-control.md |
| cloudflare-ai-crawl-control-manage-crawlers | fetched | b | 7352 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/cloudflare-ai-crawl-control-manage-crawlers.md |
| cloudflare-content-signals-policy | fetched | b | 5669 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/cloudflare-content-signals-policy.md |
| akamai-datastream-2-docs | fetched | b | 1815 | 2026-06-08 (meta:article:modified_time) | crwl/fit_markdown | corpus/staging/inbox/kernel/akamai-datastream-2-docs.md |
| akamai-datastream-2-data-set-parameters | fetched | b | 60283 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/akamai-datastream-2-data-set-parameters.md |
| akamai-bot-manager-bot-reports | fetch_failed | b |  | null (none (no page date, no Last-Modified)) | crwl/fit_markdown |  |
| openai-crawlers-bots | fetched | b | 21497 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/openai-crawlers-bots.md |
| anthropic-crawler-support-article | fetched | b | 4533 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/anthropic-crawler-support-article.md |
| perplexity-crawlers | fetched | b | 4316 | null (none (no page date, no Last-Modified)) | crwl/fit_markdown | corpus/staging/inbox/kernel/perplexity-crawlers.md |
| aggarwal-2024-geo-generative-engine-optimization | fetched | c | 69803 | 2024-07-01 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/aggarwal-2024-geo-generative-engine-optimization.pdf |
| wilkinson-2016-fair-guiding-principles | fetched | c | 47039 | 2019-11-11 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/wilkinson-2016-fair-guiding-principles.pdf |
| jacobsen-2020-fair-principles-interpretations | fetched | c | 65886 | 2026-08-21 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/jacobsen-2020-fair-principles-interpretations.pdf |
| chen-2025-geo-how-to-dominate-ai-search | fetched | c | 119318 | 2025-09-13 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/chen-2025-geo-how-to-dominate-ai-search.pdf |
| miroyan-2025-search-arena | fetched | c | 114789 | 2026-03-04 (http:Last-Modified) | httpx-pdf | corpus/staging/inbox/kernel/miroyan-2025-search-arena.pdf |
| wu-2025-what-generative-search-engines-like | fetched | c | 102752 | 2025-10-14 (http:Last-Modified) | httpx-pdf | corpus/staging/inbox/kernel/wu-2025-what-generative-search-engines-like.pdf |
| venkit-2025-deeptrace | fetched | c | 63806 | 2025-09-08 (http:Last-Modified) | httpx-pdf | corpus/staging/inbox/kernel/venkit-2025-deeptrace.pdf |
| hu-2025-auditing-google-ai-overviews | fetched | c | 92198 | 2026-03-24 (http:Last-Modified) | httpx-pdf | corpus/staging/inbox/kernel/hu-2025-auditing-google-ai-overviews.pdf |
| pl-115-336-21st-century-idea-act | fetched | d | 11349 | 2026-01-02 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/pl-115-336-21st-century-idea-act.pdf |
| omb-m-23-22-digital-first-public-experience | fetched | d | 104383 | 2023-09-22 (pdf:/ModDate) | httpx-pdf | corpus/staging/inbox/kernel/omb-m-23-22-digital-first-public-experience.pdf |
| digital-gov-dap-guide | fetched | d | 3555 | 2019-07-31 (meta:article:published_time) | crwl/fit_markdown | corpus/staging/inbox/kernel/digital-gov-dap-guide.md |
| digital-gov-search-gov-guide | fetched | d | 2879 | 2025-08-07 (meta:article:published_time) | crwl/fit_markdown | corpus/staging/inbox/kernel/digital-gov-search-gov-guide.md |
| digital-gov-website-standards | fetched | d | 1974 | 2025-02-20 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/digital-gov-website-standards.md |
| gsa-site-scanning-engine-readme | fetched | d | 7144 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/gsa-site-scanning-engine-readme.md |
| dcat-us-1-1-schema | fetched | d | 85896 | 2026-08-21 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/dcat-us-1-1-schema.md |
| census-api-user-guide | fetched | d | 4482 | 2026-05-14 (meta:article:modified_time) | crwl/fit_markdown | corpus/staging/inbox/kernel/census-api-user-guide.md |
| census-developers-landing | fetched | d | 9777 | 2026-08-19 (meta:article:modified_time) | crwl/fit_markdown | corpus/staging/inbox/kernel/census-developers-landing.md |
| census-quality-standard-d3 | excluded_by_rule | d |  | null (-) | - |  |
| census-quality-standard-f1 | excluded_by_rule | d |  | null (-) | - |  |
| census-quality-standard-f2 | excluded_by_rule | d |  | null (-) | - |  |
| sme-visibility-diagnostic-framework | excluded_by_rule | e |  | null (-) | - |  |
| lighthouse-docs-overview | fetched | b | 9306 | 2025-06-02 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/lighthouse-docs-overview.md |
| scrapy-docs-landing | fetched | b | 7311 | 2026-08-20 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/scrapy-docs-landing.md |
| playwright-docs-intro | fetched | b | 6980 | 2026-08-21 (http:Last-Modified) | crwl/fit_markdown | corpus/staging/inbox/kernel/playwright-docs-intro.md |
| extruct-readme | fetched | b | 35619 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/extruct-readme.md |
| spectral-readme | fetched | b | 10539 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/spectral-readme.md |
| pyshacl-readme | fetched | b | 22296 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/pyshacl-readme.md |
| linkchecker-readme | fetched | b | 2361 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/linkchecker-readme.md |
| goaccess-readme | fetched | b | 20184 | null (none (raw file; no Last-Modified header)) | httpx-raw | corpus/staging/inbox/kernel/goaccess-readme.md |

## 8. Next (Phase 3 inputs)

- Machine-readable manifest: `corpus/staging/inbox/kernel/_fetch_register.json` (`records[doc_id]` → status, local_path, sha256, bytes, chars, as_of/as_of_source, final_url, http_status, content_type, fetch_method, markdown_variant, extent_note, extent_dropped_sections, urls_tried, clause, source_type, title, authors_or_org).
- Clause per document is the per-document rationale for AUTH-2 manifest adds; `extent_note` + `extent_dropped_sections` are the AUTH-4 manifest-event fields for `openapi-specification-core`, `w3c-dcat-3`, `w3c-json-ld-1-1-core` (and the ToC-only drops on `w3c-dwbp-2017`, `w3c-rdf-data-cube`).
