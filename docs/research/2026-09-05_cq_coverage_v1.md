# Competency-question coverage of the ai-readiness KG — set v1, 2026-09-05

**Task:** `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md` · **Zero model spend** · **CQ set:** `assessment/cq/cq_set_v1.yaml`, authored and committed before any query ran.

**The answerability verdicts below are an LLM judge's** — the session that authored the questions also read the returned grounding spans and judged them against pass criteria it had written first and did not revise (§1.7). Every other metric on this page is counted, not judged.

## The decision

- `A_raw` = **0.923077** · `A_collapsed` = **0.884615**
- `flip` = **0.307692** (8 of 26): CQ-05, CQ-06, CQ-09, CQ-10, CQ-20, CQ-22, CQ-23, CQ-24
- `C` (total duplicate groups unioned) = **125**
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
| CQ-02 | construct_definition | yes | yes | 7→7 | 0 | 1.00 |  |
| CQ-03 | construct_definition | yes | yes | 14→14 | 0 | 1.00 |  |
| CQ-04 | construct_definition | yes | yes | 4→4 | 0 | 1.00 |  |
| CQ-05 | measure_lookup | yes | yes | 5→2 | 1 | 1.00 | yes |
| CQ-06 | measure_lookup | yes | yes | 18→8 | 3 | 1.00 | yes |
| CQ-07 | measure_lookup | yes | yes | 46→33 | 7 | — |  |
| CQ-08 | instrument_coverage | yes | yes | 10→10 | 0 | — |  |
| CQ-09 | instrument_coverage | yes | yes | 10→5 | 1 | 1.00 | yes |
| CQ-10 | instrument_coverage | partial | yes | 502→377 | 66 | 1.00 |  |
| CQ-11 | claim_evidence | yes | yes | 5→5 | 0 | 1.00 |  |
| CQ-12 | claim_evidence | yes | yes | 112→110 | 2 | 1.00 |  |
| CQ-13 | claim_evidence | yes | partial | 11→2 | 2 | 1.00 | yes |
| CQ-14 | conflict_detection | partial | partial | 5→5 | 0 | — |  |
| CQ-15 | conflict_detection | yes | yes | 2→2 | 0 | — |  |
| CQ-16 | conflict_detection | yes | yes | 14→14 | 0 | 1.00 |  |
| CQ-17 | provenance_traceback | yes | yes | 25→25 | 0 | 1.00 |  |
| CQ-18 | provenance_traceback | yes | yes | 121→115 | 5 | 1.00 |  |
| CQ-19 | provenance_traceback | yes | yes | 50→47 | 3 | 1.00 |  |
| CQ-20 | discovery_stack | yes | yes | 58→31 | 8 | 1.00 | yes |
| CQ-21 | discovery_stack | yes | partial | 37→8 | 3 | 1.00 | yes |
| CQ-22 | discovery_stack | yes | yes | 111→35 | 17 | 1.00 | yes |
| CQ-23 | frontier_candidate | yes | yes | 20→7 | 2 | 1.00 | yes |
| CQ-24 | frontier_candidate | yes | yes | 13→6 | 1 | 1.00 | yes |
| CQ-25 | frontier_candidate | yes | yes | 8→6 | 2 | 1.00 |  |
| CQ-26 | frontier_candidate | yes | yes | 31→29 | 2 | 1.00 |  |

## Judge reasons

**CQ-01** (yes / yes) — How do documents in the corpus define uncertainty legibility, or its nearest terms (uncertainty, margin of error, confidence interval)?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: 36 rows against 3. census-acs-general-handbook-2020 states what the quantity MEANS for a published data product, which is what the criterion asks and what the 3 earlier rows did not do: 'The margin of error is the measure of the magnitude of sampling error provided with all published ACS estimates.' du-2026-possible-or-definite adds an operational definition of an uncertainty level over cue-target pairs. Both documents are from this task's extraction; the verdict moves partial -> yes on their spans.

**CQ-02** (yes / yes) — How does the corpus define "AI-ready data"?

> CHANGED, partial -> yes. The criterion is two or more DISTINCT documents returning a span that defines the term so the definitions can be compared; the previous run had one document defining it twice in the training sense plus one vendor sentence, and failed. Four documents now return defining spans and, more to the point, two of them define it in the sense the framework means: worldbank-blog-open-data-to-ai-ready-2025 — 'AI-ready data means that development data is continuously open, discoverable, and reusable, while ensuring that it is systematically organized and well-documented, to facilitate seamless use by both people *and* AI systems' — and uk-ai-ready-data-action-plan-2026 — 'AI-ready datasets that are technically fit for modern AI capabilities, intelligible beyond their original operational purpose, and governed in ways that are lawful, ethical, and worthy of public trust'. Those two are comparable to each other AND contrast with the training-data sense still held by data-readiness-for-scientific-ai-at-scale ('cleaned, labeled, normalized, feature-engineered, and formatted for scalable training'), which is what makes the answer a definition landscape rather than a single quote. No dup groups, no collapse shrink, so raw and collapsed agree.

**CQ-03** (yes / yes) — What definitions does the corpus give for data quality, and do they agree on its dimensions?

> 12 -> 14 rows; the criterion (two documents' spans defining data quality in comparable terms) was met before and is met by the same spans now: fcsm-19-01 'data quality refers to the data's fitness for use for a user's own needs' beside fcsm-20-04 'the degree to which data capture the desired information using appropriate methodology in a manner that sustains public trust'. The two new rows do not change the verdict.

**CQ-04** (yes / yes) — Which Concepts does the corpus treat as components of "data quality", and from how many distinct documents?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: 4 components with spans showing the source treating them as parts of data quality — ai-data-readiness-checklist: 'Is your data accurate, complete, consistent, and reliable?'. Unchanged.

**CQ-05** (yes / yes) — Which Measures operationalise "completeness", and in which Instruments?

> 5/2 rows, unchanged in count; row content reordered by the replay. aidrin-hiniduma-2024 still names both the Measure and the Instrument — 'AIDRIN quantifies this by measuring the proportion', instrument AIDRIN — which is what the criterion says makes the answer useful. misleading_raw stands: 5 raw rows collapse to 2 distinct measures.

**CQ-06** (yes / yes) — Which Measures does the corpus attach to metadata quality or documentation?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: dcat-us-1-1-schema 'Validate that agency metadata conforms to the DCAT-US schema using the data.gov validator' states how metadata quality is assessed. Unchanged.

**CQ-07** (yes / yes) — For the Instrument AIDRIN, which Measures does it use and which Concepts do they measure?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: AIDRIN traverses end to end: 'FAIR compliance score: proportion of fulfilled metadata checks out of total possible checks across Findable, Accessible, Interoperable, Reusable'. Unchanged.

**CQ-08** (yes / yes) — Which of the framework's own constructs (by name) are measured by no Instrument in the corpus?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: All ten framework terms return a row and the zero-instrument ones are identifiable, so the question is answerable. The ANSWER changed: the uncovered list is now six terms (provenance, license, revision, discoverability, machine-readable, semantic consistency) and no longer contains 'uncertainty', which sat at zero instruments in the first run.

**CQ-09** (yes / yes) — Which Instruments measure uncertainty-related concepts, and who owns them?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: Was an empty result — a pass only under the clause that an agreed-empty answer is itself the finding. It is no longer empty: 10 rows, 5 after collapse. mazzi-2021 'Comunikos is designed to evaluate alternative ways of measuring and communicating data uncertainty specifically in contexts relevant to official economic statistics', owner Eurostat; van-der-bles-2019 names GRADE as 'a system designed to communicate indirect uncertainty'. The pass is now on the first limb of the criterion, with an owner attached, and the corpus's claim that NO instrument measures uncertainty is falsified.

**CQ-10** (partial / yes) — How many distinct Instruments does the corpus describe, and how many are traceable to a document with a content hash?

> 483 -> 502 raw, 362 -> 377 distinct after collapse. The criterion states the raw count is expected to overstate and that the overstatement IS the measurement, so raw stays partial and the collapsed count is the honest answer to 'how many instruments does the corpus describe'. Every row carries a doc_id and a content_hash. The strand added 15 distinct instruments.

**CQ-11** (yes / yes) — What Claims support the practice of publishing machine-readable metadata, and from which documents?

> 3 -> 5 rows. mlcommons-croissant-spec still supplies the pair the criterion asks for ('Croissant JSON-LD metadata needs to be embedded inside a web page in order to be indexed and crawled by search engines'), and the strand adds two more from odi-framework-for-ai-ready-data-2025 and uk-ai-ready-data-action-plan-2026 that read the same way. No collapse shrink.

**CQ-12** (yes / yes) — What does the corpus claim about the cost or burden of preparing data for AI?

> 100 -> 112 rows. aidrin-hiniduma-2024 'Computer scientists who use AI invest a considerable amount of time and effort in preparing the data for AI' still asserts burden and is attributable. The strand contributes ccsa-2026-ai-ready-official-statistics 'Building an AI-ready data ecosystem is a shared effort'.

**CQ-13** (yes / partial) — Which Claims are about the Concept "interoperability", and which documents assert them?

> 5 -> 11 raw, 1 -> 2 collapsed. Raw passes: readable interoperability claims with asserting documents (w3c-dcat-3 'In order to ensure interoperability, it is important to consistently use the IRIs identifying the reference standards'), and the strand adds odi-ai-ready-national-data-library-2025. Collapsed stays partial for the SAME harness defect recorded in the first run: collapse_on is the shared subject Concept rather than the listed Claim, so eleven distinct claims about interoperability shrink to two concept groups. The defect is deliberately NOT repaired in this run — repairing a harness between the two halves of a before/after would contaminate the comparison.

**CQ-14** (partial / partial) — Where do two Documents make conflicting Claims, and about what?

> 5 pairs, unchanged in count, one pair replaced. The criterion (at least one pair whose spans actually disagree) is met — manski-2015 'The estimates of GDP and GDI are accurate' against 'realtime research has shown that this assumption is false' — but the QUESTION asks where two DOCUMENTS conflict, and all five pairs are still intra-document (arm/arm, manski/manski, van-der-bles/van-der-bles, fcsm-25-03/fcsm-25-03). The strand did not produce a cross-document conflict. Partial for the same reason as the previous run, and the criterion is not revised to make it pass.

**CQ-15** (yes / yes) — Are there conflicting Definitions of the same term in the corpus?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: Was a recorded FAILURE: the single pair was two fragments of one Census household definition that did not disagree. A second pair now comes from census-acs-general-handbook-2020 and does disagree about the same term: 'The universe in the 2000 Census was "specified renter-occupied housing units," which excluded one-family houses on 10 acres or more, whereas the universe in the ACS is "renter-occupied housing units," thus, comparisons cannot be made between these two data sets.' Two incompatible definitions of the same universe, with the source saying they are not comparable. The criterion asks for a definition pair whose spans disagree about the same term; it does not re

**CQ-16** (yes / yes) — Do any two documents define "data quality" incompatibly, judged by reading their definitions side by side rather than by a CONFLICTS_WITH edge?

> 12 -> 14 rows. Definitions from different documents a reader can compare without a conflict edge, unchanged: datahub-mlmu-25's 'AI-readiness refers to the extent to which a data asset is prepared for effective analysis and querying by AI systems, particularly LLMs' beside fcsm-19-01's 'fitness for use'.

**CQ-17** (yes / yes) — For a given Claim, return its grounding span, its source document's content hash, and the extraction event that produced it.

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: provenance_complete = 1.0: every row carries a non-null span, content hash and extraction event id. Unchanged.

**CQ-18** (yes / yes) — Which Concepts lack a source hash on their own node, and how many are there?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: 121 rows, each carrying a doc_id, so the gap is attributable to documents (aidrin-hiniduma-2024, concept 'Data quality'). Unchanged.

**CQ-19** (yes / yes) — For the Practices the corpus recommends, can each be traced to a document and a verbatim span?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: Every Practice row carries a span and a doc_id (aggarwal-2024, 'need for website owners to focus on improving content presentation'). Unchanged.

**CQ-20** (yes / yes) — Which Platforms consume which Standards of the established discovery stack (robots.txt / RFC 9309, sitemaps, RFC 8615 well-known URIs, schema.org Dataset, DCAT)?

> 58/31 rows, unchanged in count, content reordered. akamai-datastream-2-docs still shows a platform consuming a standard (llms.txt), and the collapse still reduces 58 rows to 31 distinct standards, which is the material reduction the criterion expects. misleading_raw stands.

**CQ-21** (yes / partial) — What does the corpus say about robots.txt as a machine-access control?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: Raw: rfc-9309 'This document specifies and extends the "Robots Exclusion Protocol" method' plus relationships beyond the span. Collapsed shrinks 37 rows to 8 on the shared standard, the same collapse_on defect as CQ-13, not repaired post hoc. Unchanged.

**CQ-22** (yes / yes) — Which Standards does the corpus associate with dataset discovery metadata (DCAT, schema.org, sitemaps), and which documents describe them?

> 93 -> 111 raw, 33 -> 35 distinct. Two of the three families still return readable spans: DCAT (w3c-dcat-3, dcat-us-1-1-schema) and schema.org (schema-org-datafeed). The 18 new raw rows collapse to 2 new distinct standards, so the strand widened the evidence without widening the answer much — misleading_raw stands.

**CQ-23** (yes / yes) — What does the corpus assert about MCP (Model Context Protocol) as a discovery or access mechanism, and with what dates?

> 7 -> 20 raw, 4 -> 7 distinct, and this is the CQ the strand moved most. fcsm-25-03 still carries the dated assertion the criterion needs ('Model Context Protocols (MCPs)', pub_date 2025); the strand adds worldbank-blog-open-data-to-ai-ready-2025 and usdc-mcp-federal-open-data-pilot-2026, both dated, so MCP as a discovery mechanism is now asserted by four documents rather than two. misleading_raw stands (20 rows, 7 distinct).

**CQ-24** (yes / yes) — What does the corpus assert about llms.txt as a discovery mechanism, with dates?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: llmstxt-proposal, pub_date 2026-08-10, and akamai-datastream-2-docs 2026-06-08 both assert llms.txt as a discovery mechanism, dated. Unchanged.

**CQ-25** (yes / yes) — Which frontier access mechanisms does the corpus mention at all (MCP, llms.txt, agent APIs, pay-per-crawl), and how recently?

> Evidence IDENTICAL to the 2026-09-04b run — same row counts, same returned rows, same duplicate groups, same misleading_raw — so the verdict carries unchanged against the criterion pre-registered at 369d717. Prior reason: More than two distinct mechanisms with dates (llms.txt 2026-08-10 and the MCP rows dated 2025), so the frontier set can be compared by recency. Unchanged.

**CQ-26** (yes / yes) — Does the corpus contain any Claim that a frontier mechanism is or is not yet an established practice?

> 28 -> 31 rows. llmstxt-proposal, 2026-08-10, 'The `llms.txt` specification is open for community input' still takes a dated position on whether the mechanism is established, which is what the frontier-candidate rule depends on.

