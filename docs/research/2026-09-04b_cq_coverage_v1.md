# Competency-question coverage of the ai-readiness KG — set v1, 2026-09-04b

**Task:** `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md` · **Zero model spend** · **CQ set:** `assessment/cq/cq_set_v1.yaml`, authored and committed before any query ran.

**The answerability verdicts below are an LLM judge's** — the session that authored the questions also read the returned grounding spans and judged them against pass criteria it had written first and did not revise (§1.7). Every other metric on this page is counted, not judged.

## The decision

- `A_raw` = **0.884615** · `A_collapsed` = **0.846154**
- `flip` = **0.307692** (8 of 26): CQ-05, CQ-06, CQ-09, CQ-10, CQ-20, CQ-22, CQ-23, CQ-24
- `C` (total duplicate groups unioned) = **121**
- raw answers flagged misleading: **9**

**Rule (pre-registered, §1.5): pre-registered §1.5: flip >= 0.30 -> ER is P0; flip < 0.10 -> ER deferred; otherwise ER scheduled, not blocking**

**Branch that fired: entity resolution is P0 and blocks probe design.**

## Flip by category

| category | n | flips | flip | driving CQs |
|---|---:|---:|---:|---|
| claim_evidence | 3 | 0 | 0.0 | — |
| conflict_detection | 3 | 0 | 0.0 | — |
| construct_definition | 4 | 0 | 0.0 | — |
| discovery_stack | 3 | 2 | 0.666667 | CQ-20, CQ-22 |
| frontier_candidate | 4 | 2 | 0.5 | CQ-23, CQ-24 |
| instrument_coverage | 3 | 2 | 0.666667 | CQ-09, CQ-10 |
| measure_lookup | 3 | 2 | 0.666667 | CQ-05, CQ-06 |
| provenance_traceback | 3 | 0 | 0.0 | — |

## Per CQ

| CQ | category | raw | collapsed | rows raw→coll | dup groups | prov | misleading |
|---|---|---|---|---:|---:|---:|---|
| CQ-01 | construct_definition | yes | yes | 36→36 | 0 | 1.00 |  |
| CQ-02 | construct_definition | partial | partial | 3→3 | 0 | 1.00 |  |
| CQ-03 | construct_definition | yes | yes | 12→12 | 0 | 1.00 |  |
| CQ-04 | construct_definition | yes | yes | 4→4 | 0 | 1.00 |  |
| CQ-05 | measure_lookup | yes | yes | 5→2 | 1 | 1.00 | yes |
| CQ-06 | measure_lookup | yes | yes | 18→8 | 3 | 1.00 | yes |
| CQ-07 | measure_lookup | yes | yes | 46→33 | 7 | — |  |
| CQ-08 | instrument_coverage | yes | yes | 10→10 | 0 | — |  |
| CQ-09 | instrument_coverage | yes | yes | 10→5 | 1 | 1.00 | yes |
| CQ-10 | instrument_coverage | partial | yes | 483→362 | 64 | 1.00 |  |
| CQ-11 | claim_evidence | yes | yes | 3→3 | 0 | 1.00 |  |
| CQ-12 | claim_evidence | yes | yes | 100→98 | 2 | 1.00 |  |
| CQ-13 | claim_evidence | yes | partial | 5→1 | 1 | 1.00 | yes |
| CQ-14 | conflict_detection | partial | partial | 5→5 | 0 | — |  |
| CQ-15 | conflict_detection | yes | yes | 2→2 | 0 | — |  |
| CQ-16 | conflict_detection | yes | yes | 12→12 | 0 | 1.00 |  |
| CQ-17 | provenance_traceback | yes | yes | 25→25 | 0 | 1.00 |  |
| CQ-18 | provenance_traceback | yes | yes | 121→115 | 5 | 1.00 |  |
| CQ-19 | provenance_traceback | yes | yes | 50→47 | 3 | 1.00 |  |
| CQ-20 | discovery_stack | yes | yes | 58→31 | 8 | 1.00 | yes |
| CQ-21 | discovery_stack | yes | partial | 37→8 | 3 | 1.00 | yes |
| CQ-22 | discovery_stack | yes | yes | 93→33 | 17 | 1.00 | yes |
| CQ-23 | frontier_candidate | yes | yes | 7→4 | 1 | 1.00 | yes |
| CQ-24 | frontier_candidate | yes | yes | 13→6 | 1 | 1.00 | yes |
| CQ-25 | frontier_candidate | yes | yes | 8→6 | 2 | 1.00 |  |
| CQ-26 | frontier_candidate | yes | yes | 28→26 | 2 | 1.00 |  |

## Judge reasons

**CQ-01** (yes / yes) — How do documents in the corpus define uncertainty legibility, or its nearest terms (uncertainty, margin of error, confidence interval)?

> 36 rows against 3. census-acs-general-handbook-2020 states what the quantity MEANS for a published data product, which is what the criterion asks and what the 3 earlier rows did not do: 'The margin of error is the measure of the magnitude of sampling error provided with all published ACS estimates.' du-2026-possible-or-definite adds an operational definition of an uncertainty level over cue-target pairs. Both documents are from this task's extraction; the verdict moves partial -> yes on their spans.

**CQ-02** (partial / partial) — How does the corpus define "AI-ready data"?

> Unchanged at 3 rows, and the criterion (two or more DISTINCT documents each returning a defining span) is still not met. data-readiness-for-scientific-ai defines it twice in the training sense ('cleaned, labeled, normalized, feature-engineered, and formatted for scalable training'); the only other row, odcs-open-data-contract-standard, is a vendor sentence about 'a fully managed, AI-ready data analytics platform', which describes a product and defines nothing. One defining document = partial, as pre-registered.

**CQ-03** (yes / yes) — What definitions does the corpus give for data quality, and do they agree on its dimensions?

> 12 rows, comparable definitions from different documents: fcsm-19-01 'data quality refers to the data's fitness for use for a user's own needs' against fcsm-20-04 'the degree to which data capture the desired information using appropriate methodology in a manner that sustains public trust'. Unchanged.

**CQ-04** (yes / yes) — Which Concepts does the corpus treat as components of "data quality", and from how many distinct documents?

> 4 components with spans showing the source treating them as parts of data quality — ai-data-readiness-checklist: 'Is your data accurate, complete, consistent, and reliable?'. Unchanged.

**CQ-05** (yes / yes) — Which Measures operationalise "completeness", and in which Instruments?

> aidrin-hiniduma-2024 'AIDRIN quantifies this by measuring the proportion of ...' names both the measure and the Instrument, which is what makes the answer useful under the criterion. Unchanged.

**CQ-06** (yes / yes) — Which Measures does the corpus attach to metadata quality or documentation?

> dcat-us-1-1-schema 'Validate that agency metadata conforms to the DCAT-US schema using the data.gov validator' states how metadata quality is assessed. Unchanged.

**CQ-07** (yes / yes) — For the Instrument AIDRIN, which Measures does it use and which Concepts do they measure?

> AIDRIN traverses end to end: 'FAIR compliance score: proportion of fulfilled metadata checks out of total possible checks across Findable, Accessible, Interoperable, Reusable'. Unchanged.

**CQ-08** (yes / yes) — Which of the framework's own constructs (by name) are measured by no Instrument in the corpus?

> All ten framework terms return a row and the zero-instrument ones are identifiable, so the question is answerable. The ANSWER changed: the uncovered list is now six terms (provenance, license, revision, discoverability, machine-readable, semantic consistency) and no longer contains 'uncertainty', which sat at zero instruments in the first run.

**CQ-09** (yes / yes) — Which Instruments measure uncertainty-related concepts, and who owns them?

> Was an empty result — a pass only under the clause that an agreed-empty answer is itself the finding. It is no longer empty: 10 rows, 5 after collapse. mazzi-2021 'Comunikos is designed to evaluate alternative ways of measuring and communicating data uncertainty specifically in contexts relevant to official economic statistics', owner Eurostat; van-der-bles-2019 names GRADE as 'a system designed to communicate indirect uncertainty'. The pass is now on the first limb of the criterion, with an owner attached, and the corpus's claim that NO instrument measures uncertainty is falsified.

**CQ-10** (partial / yes) — How many distinct Instruments does the corpus describe, and how many are traceable to a document with a content hash?

> Raw returns 483 Instrument rows and collapse gives 362 distinct — the raw count overstates, exactly as the criterion anticipates, so raw is partial and the collapsed count is the honest answer. Every row carries a doc_id and a content_hash (census-acs-general-handbook-2020, hash d2b7ba1b...). The corpus now describes 362 distinct instruments against 285 before.

**CQ-11** (yes / yes) — What Claims support the practice of publishing machine-readable metadata, and from which documents?

> mlcommons-croissant-spec: 'Croissant JSON-LD metadata needs to be embedded inside a web page in order to be indexed', a claim supporting the practice and naming its document. Unchanged.

**CQ-12** (yes / yes) — What does the corpus claim about the cost or burden of preparing data for AI?

> aidrin-hiniduma-2024 'Computer scientists who use AI invest a considerable amount of time and effort in preparing the data for AI' asserts burden and is attributable. 100 rows against 84; the new ones include census-acs on the cost of decisions made without current data.

**CQ-13** (yes / partial) — Which Claims are about the Concept "interoperability", and which documents assert them?

> Raw: 5 claims about interoperability with readable spans and asserting documents (w3c-dcat-3 'In order to ensure interoperability, it is important to consistently use the IRIs identifying the reference standards'). Collapsed still shrinks 5 rows to 1 because collapse_on is the shared subject Concept rather than the listed claim — the harness defect recorded in the first run's RESULT and deliberately NOT repaired after seeing answers. Verdict unchanged.

**CQ-14** (partial / partial) — Where do two Documents make conflicting Claims, and about what?

> 5 pairs against 3, and two of the new ones genuinely disagree — manski-2015 quotes 'The estimates of GDP and GDI are accurate' against 'realtime research has shown that this assumption is false'; van-der-bles-2019 sets 'communicating uncertainty might have negative consequences' against 'such transparency might build rather than undermine trust'. But every pair still has doc_a == doc_b, and the question asks where two DOCUMENTS conflict. The graph holds no cross-document conflict edge. Unchanged at partial for the same reason as the first run.

**CQ-15** (yes / yes) — Are there conflicting Definitions of the same term in the corpus?

> Was a recorded FAILURE: the single pair was two fragments of one Census household definition that did not disagree. A second pair now comes from census-acs-general-handbook-2020 and does disagree about the same term: 'The universe in the 2000 Census was "specified renter-occupied housing units," which excluded one-family houses on 10 acres or more, whereas the universe in the ACS is "renter-occupied housing units," thus, comparisons cannot be made between these two data sets.' Two incompatible definitions of the same universe, with the source saying they are not comparable. The criterion asks for a definition pair whose spans disagree about the same term; it does not require two documents (CQ-14 is the one that does). The pass rests entirely on this new pair — the original fcsm pair still fails.

**CQ-16** (yes / yes) — Do any two documents define "data quality" incompatibly, judged by reading their definitions side by side rather than by a CONFLICTS_WITH edge?

> Definitions from different documents a reader can compare without a conflict edge: datahub-mlmu-25's 'AI-readiness refers to the extent to which a data asset is prepared for effective analysis and querying by AI systems, particularly LLMs' beside fcsm-19-01's 'fitness for use'. Unchanged.

**CQ-17** (yes / yes) — For a given Claim, return its grounding span, its source document's content hash, and the extraction event that produced it.

> provenance_complete = 1.0: every row carries a non-null span, content hash and extraction event id. Unchanged.

**CQ-18** (yes / yes) — Which Concepts lack a source hash on their own node, and how many are there?

> 121 rows, each carrying a doc_id, so the gap is attributable to documents (aidrin-hiniduma-2024, concept 'Data quality'). Unchanged.

**CQ-19** (yes / yes) — For the Practices the corpus recommends, can each be traced to a document and a verbatim span?

> Every Practice row carries a span and a doc_id (aggarwal-2024, 'need for website owners to focus on improving content presentation'). Unchanged.

**CQ-20** (yes / yes) — Which Platforms consume which Standards of the established discovery stack (robots.txt / RFC 9309, sitemaps, RFC 8615 well-known URIs, schema.org Dataset, DCAT)?

> akamai-datastream-2-docs shows a platform consuming a standard: 'visit https://techdocs.akamai.com/datastream2/llms.txt'. Collapse reduces 58 standard rows to 31, which is the material reduction the criterion expects. Unchanged.

**CQ-21** (yes / partial) — What does the corpus say about robots.txt as a machine-access control?

> Raw: rfc-9309 'This document specifies and extends the "Robots Exclusion Protocol" method' plus relationships beyond the span. Collapsed shrinks 37 rows to 8 on the shared standard, the same collapse_on defect as CQ-13, not repaired post hoc. Unchanged.

**CQ-22** (yes / yes) — Which Standards does the corpus associate with dataset discovery metadata (DCAT, schema.org, sitemaps), and which documents describe them?

> Two of the three families with readable spans: DCAT ('based on DCAT, a hierarchical vocabulary specific to datasets', dcat-us-1-1-schema) and schema.org (schema-org-datafeed). Unchanged.

**CQ-23** (yes / yes) — What does the corpus assert about MCP (Model Context Protocol) as a discovery or access mechanism, and with what dates?

> fcsm-25-03, pub_date 2025: 'One promising example are Model Context Protocols (MCPs), open-source standard...' — an assertion about MCP as an access mechanism, dated. Unchanged.

**CQ-24** (yes / yes) — What does the corpus assert about llms.txt as a discovery mechanism, with dates?

> llmstxt-proposal, pub_date 2026-08-10, and akamai-datastream-2-docs 2026-06-08 both assert llms.txt as a discovery mechanism, dated. Unchanged.

**CQ-25** (yes / yes) — Which frontier access mechanisms does the corpus mention at all (MCP, llms.txt, agent APIs, pay-per-crawl), and how recently?

> More than two distinct mechanisms with dates (llms.txt 2026-08-10 and the MCP rows dated 2025), so the frontier set can be compared by recency. Unchanged.

**CQ-26** (yes / yes) — Does the corpus contain any Claim that a frontier mechanism is or is not yet an established practice?

> llmstxt-proposal, 2026-08-10: 'The `llms.txt` specification is open for community input' takes a dated position on whether the mechanism is established. 28 rows against 26. Unchanged.

