# Competency-question coverage of the ai-readiness KG — set v1, 2026-09-04

**Task:** `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md` · **Zero model spend** · **CQ set:** `assessment/cq/cq_set_v1.yaml`, authored and committed before any query ran.

**The answerability verdicts below are an LLM judge's** — the session that authored the questions also read the returned grounding spans and judged them against pass criteria it had written first and did not revise (§1.7). Every other metric on this page is counted, not judged.

## The decision

- `A_raw` = **0.807692** · `A_collapsed` = **0.769231**
- `flip` = **0.269231** (7 of 26): CQ-05, CQ-06, CQ-10, CQ-20, CQ-22, CQ-23, CQ-24
- `C` (total duplicate groups unioned) = **98**
- raw answers flagged misleading: **8**

**Rule (pre-registered, §1.5): pre-registered §1.5: flip >= 0.30 -> ER is P0; flip < 0.10 -> ER deferred; otherwise ER scheduled, not blocking**

**Branch that fired: entity resolution scheduled as a task, not blocking probe design (sift-kg three-layer pattern as the design).**

## Flip by category

| category | n | flips | flip | driving CQs |
|---|---:|---:|---:|---|
| claim_evidence | 3 | 0 | 0.0 | — |
| conflict_detection | 3 | 0 | 0.0 | — |
| construct_definition | 4 | 0 | 0.0 | — |
| discovery_stack | 3 | 2 | 0.666667 | CQ-20, CQ-22 |
| frontier_candidate | 4 | 2 | 0.5 | CQ-23, CQ-24 |
| instrument_coverage | 3 | 1 | 0.333333 | CQ-10 |
| measure_lookup | 3 | 2 | 0.666667 | CQ-05, CQ-06 |
| provenance_traceback | 3 | 0 | 0.0 | — |

## Per CQ

| CQ | category | raw | collapsed | rows raw→coll | dup groups | prov | misleading |
|---|---|---|---|---:|---:|---:|---|
| CQ-01 | construct_definition | partial | partial | 3→3 | 0 | 1.00 |  |
| CQ-02 | construct_definition | partial | partial | 3→3 | 0 | 1.00 |  |
| CQ-03 | construct_definition | yes | yes | 12→12 | 0 | 1.00 |  |
| CQ-04 | construct_definition | yes | yes | 4→4 | 0 | 1.00 |  |
| CQ-05 | measure_lookup | yes | yes | 5→2 | 1 | 1.00 | yes |
| CQ-06 | measure_lookup | yes | yes | 18→8 | 3 | 1.00 | yes |
| CQ-07 | measure_lookup | yes | yes | 46→33 | 7 | — |  |
| CQ-08 | instrument_coverage | yes | yes | 10→10 | 0 | — |  |
| CQ-09 | instrument_coverage | yes | yes | 0→0 | 0 | — |  |
| CQ-10 | instrument_coverage | partial | yes | 354→285 | 42 | 1.00 |  |
| CQ-11 | claim_evidence | yes | yes | 3→3 | 0 | 1.00 |  |
| CQ-12 | claim_evidence | yes | yes | 84→82 | 2 | 1.00 |  |
| CQ-13 | claim_evidence | yes | partial | 5→1 | 1 | 1.00 | yes |
| CQ-14 | conflict_detection | partial | partial | 3→3 | 0 | — |  |
| CQ-15 | conflict_detection | no | no | 1→1 | 0 | — |  |
| CQ-16 | conflict_detection | yes | yes | 12→12 | 0 | 1.00 |  |
| CQ-17 | provenance_traceback | yes | yes | 25→25 | 0 | 1.00 |  |
| CQ-18 | provenance_traceback | yes | yes | 121→115 | 5 | 1.00 |  |
| CQ-19 | provenance_traceback | yes | yes | 50→47 | 3 | 1.00 |  |
| CQ-20 | discovery_stack | yes | yes | 58→31 | 8 | 1.00 | yes |
| CQ-21 | discovery_stack | yes | partial | 37→8 | 3 | 1.00 | yes |
| CQ-22 | discovery_stack | yes | yes | 92→33 | 17 | 1.00 | yes |
| CQ-23 | frontier_candidate | yes | yes | 7→4 | 1 | 1.00 | yes |
| CQ-24 | frontier_candidate | yes | yes | 13→6 | 1 | 1.00 | yes |
| CQ-25 | frontier_candidate | yes | yes | 8→6 | 2 | 1.00 |  |
| CQ-26 | frontier_candidate | yes | yes | 26→24 | 2 | 1.00 |  |

## Judge reasons

**CQ-01** (partial / partial) — How do documents in the corpus define uncertainty legibility, or its nearest terms (uncertainty, margin of error, confidence interval)?

> Two spans define uncertainty as a kind ('aleatoric uncertainty, measuring the noise inherent in the observations'; 'epistemic uncertainty, accounting for uncertainty in the model itself', technology-readiness-levels-for-machine-learning-systems-mlt) but both are about ML models, not a data product's expression of uncertainty; the third row ('shall be truthful in responding to user prompts', m-26-04) is a false positive on the word. No definition of margin of error or confidence interval exists in the corpus. Partial in both views; the collapse changes nothing.

**CQ-02** (partial / partial) — How does the corpus define "AI-ready data"?

> Only ONE document actually defines the term: data-readiness-for-scientific-ai-at-scale ('AI-ready data - cleaned, labeled, normalized, feature-engineered, and formatted for scalable training'). The odcs-open-data-contract-standard row is a vendor phrase ('BigQuery is a fully managed, AI-ready data analytics platform'), not a definition. The criterion required two or more documents, so partial in both views.

**CQ-03** (yes / yes) — What definitions does the corpus give for data quality, and do they agree on its dimensions?

> Eight distinct documents return definitions, and they are comparable: fcsm-19-01 'data quality refers to the data’s fitness for use for a user’s own needs', with fcsm-20-04, statistical-policy-working-paper-46 and fcsm-25-03 also present. Criterion (two or more comparable) exceeded. Collapse changes nothing.

**CQ-04** (yes / yes) — Which Concepts does the corpus treat as components of "data quality", and from how many distinct documents?

> Components returned with spans that show the source treating them as parts of data quality: 'Data Accuracy and Consistency: Is your data accurate, complete, consistent, and reliable?' (ai-data-readiness-checklist-digital-government-hub). Criterion met. Worth recording: all four components come from ONE document, so the HAS_COMPONENT edge does not aggregate across the corpus.

**CQ-05** (yes / yes) — Which Measures operationalise "completeness", and in which Instruments?

> AIDRIN is returned with a span operationalising completeness ('AIDRIN quantifies this by measuring the proportion of missing values within each feature of the dataset', aidrin-hiniduma-2024), so the criterion is met in both views. The raw view is MISLEADING: 5 rows for 2 distinct measures, the AIDRIN row repeated three times, so a reader counts five operationalisations where there are two.

**CQ-06** (yes / yes) — Which Measures does the corpus attach to metadata quality or documentation?

> A measure states how documentation is assessed: 'To what extent has the entity documented the AI system’s development, testing methodology, metrics, and performance' (nist-ai-rmf-playbook). Criterion met. Raw is misleading at 18 rows for 8 distinct measures.

**CQ-07** (yes / yes) — For the Instrument AIDRIN, which Measures does it use and which Concepts do they measure?

> AIDRIN traverses end to end: instrument -> measure -> concept, with the span 'AIDRIN quantifies this by measuring the proportion of missing values within each feature of the dataset'. 46 raw rows collapse to 33; below the pre-registered 0.30 misleading threshold.

**CQ-08** (yes / yes) — Which of the framework's own constructs (by name) are measured by no Instrument in the corpus?

> All ten terms return a row and the uncovered constructs are identifiable: nine of ten (uncertainty, provenance, license, revision, discoverability, machine-readable, semantic consistency, authority, disclosure) have ZERO instruments; only timeliness has 2. Criterion met. This is the coverage answer the framework needs and it is a negative one.

**CQ-09** (yes / yes) — Which Instruments measure uncertainty-related concepts, and who owns them?

> Empty in both views, which the criterion pre-registered as a PASS when raw and collapsed agree - and they do. The finding is substantive: no Instrument in the corpus measures an uncertainty-related concept, which is the graph independently supporting the skeleton's claim that G1 is the sharpest gap.

**CQ-10** (partial / yes) — How many distinct Instruments does the corpus describe, and how many are traceable to a document with a content hash?

> Every row carries a doc_id and a content hash (checked: 354/354), so traceability holds. But the question asks HOW MANY distinct instruments: raw answers 354, collapsed answers 285. The raw number overstates by 69 (19.5%) and is the wrong answer to the question as asked; the collapsed number is right. Flip driven by the count, not by the traceability.

**CQ-11** (yes / yes) — What Claims support the practice of publishing machine-readable metadata, and from which documents?

> Practice-Claim pairs with readable spans and named sources: 'the provision of metadata is a fundamental requirement' (w3c-dwbp-2017) supporting 'Provide metadata for both human users and computer applications.' Criterion met.

**CQ-12** (yes / yes) — What does the corpus claim about the cost or burden of preparing data for AI?

> 'Computer scientists who use AI invest a considerable amount of time and effort in preparing the data' (aidrin-hiniduma-2024) is a dated, attributable claim about preparation burden. Criterion met.

**CQ-13** (yes / partial) — Which Claims are about the Concept "interoperability", and which documents assert them?

> Raw returns 5 claims about interoperability, all with an asserting document and readable spans ('In order to ensure interoperability, it is important to consistently use the IRIs', w3c-dcat-3). The COLLAPSED view is worse, not better: collapsing on the concept merges all five claims into one row and four claims disappear. A harness finding, not a graph finding - collapse_on must never be the entity a list-of-items question is grouped by.

**CQ-14** (partial / partial) — Where do two Documents make conflicting Claims, and about what?

> All three conflict pairs do disagree on reading ('665 business leaders' vs 'n=655'; '10-15% of total electricity' vs '10-20 percent'), so the edge is not spurious. But every pair is INTRA-document (doc_a == doc_b in all three), and the question asks where two DOCUMENTS conflict. The graph holds no cross-document conflict at all, so the question as asked is unanswered.

**CQ-15** (no / no) — Are there conflicting Definitions of the same term in the corpus?

> The single returned pair does not disagree: both fragments are parts of the SAME Census household definition in fcsm-19-01 ('all persons who live together and share food' / 'at a given address, regardless of whether there are family connections'). A false positive by the pre-registered criterion, so this CQ fails. Recorded as a failure, not rationalised: the corpus certainly holds competing definitions of AI readiness (CQ-02, CQ-03) and the CONFLICTS_WITH edge is not capturing them.

**CQ-16** (yes / yes) — Do any two documents define "data quality" incompatibly, judged by reading their definitions side by side rather than by a CONFLICTS_WITH edge?

> Eight distinct documents return comparable data-quality definitions without using the conflict edge, so conflict detection by retrieval works where the edge does not (contrast CQ-15). Criterion met.

**CQ-17** (yes / yes) — For a given Claim, return its grounding span, its source document's content hash, and the extraction event that produced it.

> All 25 rows carry a non-null grounding span, content hash and extraction event id (checked: 0 nulls in each), plus the model id. Provenance traceback holds for every row, which is what the criterion demanded.

**CQ-18** (yes / yes) — Which Concepts lack a source hash on their own node, and how many are there?

> 121 Concepts lack prov_source_sha256 on their own node, and all 121 still carry a doc_id (checked: 0 nulls), so the gap is attributable to documents. A countable, attributable set: criterion met.

**CQ-19** (yes / yes) — For the Practices the corpus recommends, can each be traced to a document and a verbatim span?

> All 50 returned Practices carry a non-null grounding span and doc_id (checked: 0 nulls in each). Criterion met.

**CQ-20** (yes / yes) — Which Platforms consume which Standards of the established discovery stack (robots.txt / RFC 9309, sitemaps, RFC 8615 well-known URIs, schema.org Dataset, DCAT)?

> Platform-standard pairs with spans showing consumption: 'AI crawlers' -> robots.txt ('Track the health of robots.txt files and identify which crawlers are violating your directives', cloudflare-ai-crawl-control) and 'AI agents' -> llms.txt/OpenAPI/Markdown (akamai-datastream-2-docs). Raw is misleading at 58 rows for 31 distinct standards.

**CQ-21** (yes / partial) — What does the corpus say about robots.txt as a machine-access control?

> Raw answers well: RFC 9309's own span ('This document specifies and extends the Robots Exclusion Protocol method originally defined in 1994') plus BUILDS_ON edges to the 1994 method and to RFC 3986/5234/3629. Collapsed keeps one row per standard and drops the relationship variety that made the answer informative - the same collapse_on defect as CQ-13.

**CQ-22** (yes / yes) — Which Standards does the corpus associate with dataset discovery metadata (DCAT, schema.org, sitemaps), and which documents describe them?

> All three families present (DCAT 48 rows, schema.org 32, sitemaps 12) with readable spans, e.g. 'DCAT 3 supersedes DCAT 2' (w3c-dcat-3). Criterion required two of three. Raw is misleading at 92 rows for 35 distinct standards.

**CQ-23** (yes / yes) — What does the corpus assert about MCP (Model Context Protocol) as a discovery or access mechanism, and with what dates?

> 'One promising example are Model Context Protocols (MCPs), open-source standard defined...' (fcsm-25-03, 2025) is a dated assertion about MCP as a mechanism. Criterion met. Raw is misleading at 7 rows for 4 groups - and note the weak collapse does NOT merge 'Model Context Protocol' / 'Model Context Protocols' / 'Model Context Protocols (MCPs)', so even the collapsed view still shows the same mechanism three times.

**CQ-24** (yes / yes) — What does the corpus assert about llms.txt as a discovery mechanism, with dates?

> llmstxt-proposal (2026-08-10) returns dated spans about the format and directories; akamai-datastream-2-docs (2026-06-08) shows it in use. Criterion met. Raw is misleading at 13 rows for 6 groups.

**CQ-25** (yes / yes) — Which frontier access mechanisms does the corpus mention at all (MCP, llms.txt, agent APIs, pay-per-crawl), and how recently?

> Two distinct mechanisms with dates: the llms.txt family (llmstxt-proposal 2026-08-10; akamai 2026-06-08) and Model Context Protocol (webb-fcsm-nist-crosswalk 2026; datahub-mlmu-25 2025). Criterion required two. Pay-per-crawl and agent APIs return nothing under these names.

**CQ-26** (yes / yes) — Does the corpus contain any Claim that a frontier mechanism is or is not yet an established practice?

> Dated claims that take a position: 'One promising example are Model Context Protocols (MCPs)' (2025), 'The FCSM is assessing emerging standards such as the Model Context Protocol' (2025), 'we have not yet standardized how to do so' (2023), and 'llms.txt is designed to coexist with current web standards' (2026-08-10). Criterion met.

