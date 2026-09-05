# Competency-question coverage of the ai-readiness KG — set v1, 2026-09-05c

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
| CQ-21 | discovery_stack | yes | partial | 51→8 | 3 | 1.00 | yes |
| CQ-22 | discovery_stack | yes | yes | 111→35 | 17 | 1.00 | yes |
| CQ-23 | frontier_candidate | yes | yes | 20→7 | 2 | 1.00 | yes |
| CQ-24 | frontier_candidate | yes | yes | 13→6 | 1 | 1.00 | yes |
| CQ-25 | frontier_candidate | yes | yes | 8→6 | 2 | 1.00 |  |
| CQ-26 | frontier_candidate | yes | yes | 31→29 | 2 | 1.00 |  |

## Judge reasons

**CQ-01** (yes / yes) — How do documents in the corpus define uncertainty legibility, or its nearest terms (uncertainty, margin of error, confidence interval)?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 36 groups against 36 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-02** (yes / yes) — How does the corpus define "AI-ready data"?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 7 groups against 7 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-03** (yes / yes) — What definitions does the corpus give for data quality, and do they agree on its dimensions?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 14 groups against 14 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-04** (yes / yes) — Which Concepts does the corpus treat as components of "data quality", and from how many distinct documents?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 4 groups against 4 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-05** (yes / yes) — Which Measures operationalise "completeness", and in which Instruments?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 2 groups against 2 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-06** (yes / yes) — Which Measures does the corpus attach to metadata quality or documentation?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 9 groups against 8 collapsed. The canonical view merges LESS here, which is the honest direction: the collapsed view unions on the extractor's own `aliases` property, which nobody vetted, while the canonical view unions only what a term actually claims and refuses every ambiguity. Criterion still met.

**CQ-07** (yes / yes) — For the Instrument AIDRIN, which Measures does it use and which Concepts do they measure?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 33 groups against 33 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-08** (yes / yes) — Which of the framework's own constructs (by name) are measured by no Instrument in the corpus?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 10 groups against 10 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-09** (yes / yes) — Which Instruments measure uncertainty-related concepts, and who owns them?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 5 groups against 5 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-10** (partial / yes) — How many distinct Instruments does the corpus describe, and how many are traceable to a document with a content hash?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 383 groups against 377 collapsed. The canonical view merges LESS here, which is the honest direction: the collapsed view unions on the extractor's own `aliases` property, which nobody vetted, while the canonical view unions only what a term actually claims and refuses every ambiguity. Criterion still met.

**CQ-11** (yes / yes) — What Claims support the practice of publishing machine-readable metadata, and from which documents?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 5 groups against 5 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-12** (yes / yes) — What does the corpus claim about the cost or burden of preparing data for AI?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 110 groups against 110 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-13** (yes / partial) — Which Claims are about the Concept "interoperability", and which documents assert them?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: partial, and for the SAME harness defect as the collapsed view rather than anything about the vocabulary — `collapse_on` is `concept`, the shared subject, so eleven distinct interoperability claims group into three. v2 repairs it by collapsing on `claim`; v1 is left as it is because the series is frozen.

**CQ-14** (partial / partial) — Where do two Documents make conflicting Claims, and about what?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: partial. All five conflict pairs remain INTRA-document; the question asks where two DOCUMENTS conflict. The vocabulary cannot create a cross-document conflict edge and did not.

**CQ-15** (yes / yes) — Are there conflicting Definitions of the same term in the corpus?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 2 groups against 2 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-16** (yes / yes) — Do any two documents define "data quality" incompatibly, judged by reading their definitions side by side rather than by a CONFLICTS_WITH edge?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 14 groups against 14 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-17** (yes / yes) — For a given Claim, return its grounding span, its source document's content hash, and the extraction event that produced it.

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 25 groups against 25 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-18** (yes / yes) — Which Concepts lack a source hash on their own node, and how many are there?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 118 groups against 115 collapsed. The canonical view merges LESS here, which is the honest direction: the collapsed view unions on the extractor's own `aliases` property, which nobody vetted, while the canonical view unions only what a term actually claims and refuses every ambiguity. Criterion still met.

**CQ-19** (yes / yes) — For the Practices the corpus recommends, can each be traced to a document and a verbatim span?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 47 groups against 47 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-20** (yes / yes) — Which Platforms consume which Standards of the established discovery stack (robots.txt / RFC 9309, sitemaps, RFC 8615 well-known URIs, schema.org Dataset, DCAT)?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 30 groups against 31 collapsed. The vocabulary merged names the alias level could not see — a judged link or a curated alias. Criterion still met.

**CQ-21** (yes / partial) — What does the corpus say about robots.txt as a machine-access control?

> RAW ROWS CHANGED 37 -> 51 ON A BYTE-IDENTICAL QUERY. The query traverses an UNTYPED relationship, `OPTIONAL MATCH (s)-[r]-(other)`, so the 19 RESOLVES_TO edges the vocabulary layer added to these Standard nodes are now returned as things the corpus says about robots.txt. They are infrastructure, not corpus content. Raw stays `yes` — the RFC 9309 BUILDS_ON rows that satisfied the criterion are still there — but the row count is contaminated and is reported as such rather than quoted. v2 excludes the type. CANONICAL: partial, same harness defect as CQ-13 — `collapse_on` is `standard`, so 51 rows about robots.txt group into the 8 Standard nodes named for it. v2 collapses on `other_text`.

**CQ-22** (yes / yes) — Which Standards does the corpus associate with dataset discovery metadata (DCAT, schema.org, sitemaps), and which documents describe them?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 32 groups against 35 collapsed. The vocabulary merged names the alias level could not see — a judged link or a curated alias. Criterion still met.

**CQ-23** (yes / yes) — What does the corpus assert about MCP (Model Context Protocol) as a discovery or access mechanism, and with what dates?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 7 groups against 7 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-24** (yes / yes) — What does the corpus assert about llms.txt as a discovery mechanism, with dates?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 5 groups against 6 collapsed. The vocabulary merged names the alias level could not see — a judged link or a curated alias. Criterion still met.

**CQ-25** (yes / yes) — Which frontier access mechanisms does the corpus mention at all (MCP, llms.txt, agent APIs, pay-per-crawl), and how recently?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 6 groups against 6 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

**CQ-26** (yes / yes) — Does the corpus contain any Claim that a frontier mechanism is or is not yet an established practice?

> Raw and collapsed carry the 2026-09-05 verdict: the graph gained a vocabulary layer, not new extractions, and this question's raw and collapsed rows are unchanged. CANONICAL: 29 groups against 29 collapsed. Identical to the collapsed view: the vocabulary changed nothing here.

