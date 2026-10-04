# Node-key fusion audit: what the `<doc>::<local id>` key has overwritten

**Date:** 2026-10-04. **Task:** `cc_tasks/2026-10-04_node_key_fusion_audit.md`, from `cc_tasks/2026-10-02_commerce_guidance_admission_RESULT.md` §7 premise 6. **Layer:** the validity layer (the KG under the framework; DN-005 §1). **Script:** `scripts/audit_node_key_fusion.py`; `--check` recomputes and compares byte for byte. **Data:** `2026-10-04_node_key_fusion_audit.csv`, one row per overwritten (span, identity) pair. This audit measures. It changes nothing on the log, the graph or the record.

## 1. The defect and how it was measured

DD-020 keys every non-Document node `<doc_id>::<item_id>`. `build_projection.py` writes each `node_asserted` as `MERGE (n:<label> {key}) SET n += props`. Under the chunked extraction contract (DD-023) the model mints item ids per chunk. Ids such as `d1`, `cl4` or `c3` therefore recur across the chunks of one document, every such assertion lands on one node, and the last one's grounding span and text replace the earlier ones. DD-020 closed the cross-document form of this. The within-document form was never addressed.

**Method.** The script reads every shard `eventlog.replay()` reads, applies the projection's own filters (`is_projectable`, then whole-extraction and stratum supersession, then the label whitelist), and groups assertions by **(label, key)**. That is the unit the projection's `MERGE` fuses on: a Claim and a Concept that share a key are two nodes. The survivor is the last assertion. The projection's repair overlays (`grounding_relocated`, `attribute_nulled`, and accepted `attribute_restored`) are applied after it, as `build` applies them. Each overwritten pair is classed by script, with no model:

- `benign_duplicate`: same span as the survivor after `grounding.normalize`.
- `same_term_lost_evidence`: different span, same identity text. Identity is `term` for Definition, `claim_text` for Claim, `text` for Measure and Practice, and `name` otherwise, compared after normalisation and case-folding.
- `collision`: different span and different identity text. This is a wrong node, not a lost span.

**Positive controls, all reproduced before any alternative was trusted:**

- The replay-derived node count equals the live graph (`seldon-ai-readiness-kg`, queried 2026-10-04) for all ten labels: Claim 6,906, Concept 11,604, Definition 2,064, Framework 512, Instrument 502, Measure 1,429, Platform 334, Practice 1,446, Standard 975, Tool 263.
- For all 2,312 fused non-Instrument nodes, the simulated surviving span and identity equal what Neo4j holds, 2,312 of 2,312.
- The stored figures recompute exactly under the current keying: Q1 19 from 11 documents, all ten Q2 construct tallies, Q4 29, and the Commerce glossary 48.
- The Commerce document's 102 asserted Definitions are 89 nodes, as the source RESULT said.

The first run did not reproduce Q1 (it gave 22). Two causes: an `attribute_nulled` overlay on `term`, and the two instrument names Q1 lists apart. The overlays and that exclusion were added, and only then were the alternatives computed.

## 2. What it found

- **2,396 of 26,035 nodes (9.2%) are fused, and 2,283 of them (8.8%) lost at least one span: 4,511 distinct grounding spans are no longer on the graph** (G2). Every overwritten pair comes from a different chunk of the survivor's run (4,182) or from a different run (479); none from the survivor's own chunk (G3), and every survivor sits in one of two runs: `bulk_v038` (62 documents) or the v1 run in `batch-004` (3 documents). That is 63 documents in all, since two have survivors in both runs (G4, G8).
- **2,703 of the 4,661 overwritten pairs are classed `collision`. That is an upper bound on wrong nodes, not a count of them (§5).** In each, one item id carried two different items, and the node shows one item's text with the other's evidence gone. 2,180 of the 2,703 sit on a positional id (`d1`, `cl4`, `c3`): an id the model numbers per chunk, not one derived from the item's text. 331 are narrower or wider names for one item (one identity text contains the other), such as `AIDRIN` and `AI Data Readiness Inspector (AIDRIN)` (G5).
- **By label:**

  | label | fused nodes | spans lost | collisions |
  |---|---|---|---|
  | Definition | 162 of 2,064 | 222 | 132 |
  | Claim | 331 of 6,906 | 865 | 861 |
  | Concept | 1,395 | 2,655 | 1,283 |
- **Edges inherit the error.** 3,322 of 38,485 projectable `edge_asserted` events were asserted in a chunk whose own assertion of an endpoint was overwritten by a different item, so each of those edges now attaches to a node whose identity text differs from the item the edge was asserted about. This includes 130 `defines` and 853 `asserts` edges, and it carries the same upper bound as `collision` (G5).
- **Repair overlays inherit it too.** Of the `grounding_relocated` overlays on fused nodes, 209 were written against an assertion that a later chunk overwrote. The projection applies overlays last, so each of those puts an earlier item's relocated span onto a different surviving item (G5).
- **31 documents carry nodes from two or three extraction runs** (v1 `batch-004`, `batch-006` v0.3.0, `batch-002`, and `bulk_v038`). Where their ids coincide, the runs fuse: these are the 479 `other_run` rows. That is a supersession question, not a chunking one (§4).
- **Reconciliation with the source RESULT.** It reported 4,070 spans on 1,966 keys in 64 documents (815 Claim, 184 Definition) for the `bulk_v038` shard, from a query that was not committed. Restricted to `bulk_v038` survivors, this audit's comparable figures are 4,469 non-benign pairs on 2,238 nodes in 62 documents (863 Claim, 218 Definition). Under the definitions tried (key, or key plus label, over `bulk_v038` events), the earlier figure does not reproduce exactly. This audit's figures replace it, and their definitions are stated here.

## 3. Impact on the record (task decision 3): stated, not fixed

Every value below was recomputed from the log by the script (G6), and the current-keying column reproduces the stored figure in each row. "(a)" is chunk-qualified keys; "(b)" is first-wins with refusal (§4).

| cited figure | where | depends on node keys? | under (a) | under (b) |
|---|---|---|---|---|
| **1,975 Definitions** | `2026-10-02_kg_research_questions_RESULT.md` §1, the epoch before the Commerce admission. The record now reads **2,064** (`kg_questions.yaml` epoch, `definition_pairs.md`) | yes, a node count | 1,975 → **2,180 (+205)** for that epoch; 2,064 → **2,281 (+217, +10.5%)** for the current one | 1,975 and 2,064, unchanged in count. First-wins changes which item survives on 162 fused Definition nodes, and up to 222 Definition items stay off the graph (a different set from today's) |
| **Q1: 19 definitions from 11 documents** | `kg_questions.yaml` Q1 | yes | **20** from 11. The added row is `data-readiness-for-ai-a-360-degree-survey::d1` as *"Data readiness for artificial intelligence (AI)"* (chunk `#c0002`), today a "data model" Definition after four other `d1`s were overwritten | 20, the same row |
| Q1's 19 rows themselves | G7 | per row | 17 rows are not fused. `datahub-mlmu-25::d-ai-readiness` lost a second span of the same term, and `worldbank…::d1` has a benign duplicate. The quoted spans stand | as (a) |
| **Q2 construct tallies** (provenance 1, timeliness 1, discoverability 4, machine-readable 2, others 0) | `kg_questions.yaml` Q2 | yes, through Q1's rows | all ten unchanged. The added Q1 row names no construct, so `naming_none` 13 → 14 | as (a) |
| Q3 conflict edges (12; 5 cross-document) and `definition_pairs` (151 of 158 judged) | `kg_questions.yaml` Q3, `docs/evidence/definition_pairs.*` | yes, they are over Q1's set | no existing pair moves (no judged pair's node is a collision). The added Q1 definition's pairs were never judged | as (a) |
| **Q4: 29 Instrument nodes named for readiness** | `kg_questions.yaml` Q4 | yes | **31**. Both additions are AIDRIN (`aidrin-hiniduma-2024::inst-aidrin`, `::i_aidrin`), whose survivors are named the bare acronym `AIDRIN`, which the readiness regex misses | 31 |
| Instrument nodes 502 | `kg_questions.yaml` epoch | yes | 669 (+167) | 502 |
| **Commerce two-pipelines 48/49** | `2026-10-02_commerce_guidance_two_pipelines.md` | yes | **48**, unchanged (G6's label proxy reproduces 48 now) | **38**. Ten glossary spans survive today only because the glossary chunks were ingested last |
| `CL-` entries in `claims.yaml` | `docs/evidence/claims.yaml` | **none counts KG extraction nodes or edges.** Every node or edge number cited there (CL-046, CL-047, CL-054) counts framework-record nodes (`AssessmentIndicator` 49, `EVIDENCED_BY` 147) or scan findings. CL-085's locator `…::def_ai_ready_data` is not fused | no move | no move |

**Bound.** Under (a), every KG node count rises by at most the number of distinct lost spans for its label (G2): Definition ≤ +222, Claim ≤ +865, all labels ≤ +4,511. Under (b), no node count moves. Instead, which of a fused node's items survives flips from the last to the first, in all 2,283 lossy nodes, so selections over those nodes do move (Q1, Q4 and the Commerce glossary, above).

## 4. The fix, designed and not built (task decision 4)

**Prior art.**

- *Standardizing apart*: RDF 1.1 Concepts §3.4 says blank node identifiers are local to the document that uses them. RDF 1.1 Semantics §5.2 says that merging two graphs requires renaming those identifiers apart first, because taking the union of local identifiers asserts an identity nobody made. A chunk's item ids are exactly such local identifiers.
- GraphRAG (Edge et al. 2024, arXiv 2404.16130) extracts per chunk. It keeps every instance's description, merges instances by exact name and type, and summarises them afterwards. It never lets one chunk's instance replace another's.
- This repository's own precedent: the chunked pilot (`cc_tasks/2026-08-27_chunked_pilot.md` §4) specified a within-document merge **by exact normalised surface form, not by id**, built as `kg/extraction/merge.normalized_key`. That merge was used only for pooling the pilot's metrics and never reached the projection.

The two external sources are cited as recalled, not retrieved (`Network: none`). The local Wintermute search for both terms returned nothing. The recommendation does not rest on them: it rests on this repository's own pilot rule and on the measured G6 columns.

**(a) Chunk-qualified keys `<doc>::<chunk>::<id>`, then a merge of nodes whose normalised spans are identical.**

- *Existing keys:* the 23,752 nodes that hold a single distinct span (26,035 less the 2,283 lossy nodes) need not move. The clean rule is to keep `<doc>::<id>` wherever a (label, key) group has one distinct normalised span, and to qualify only the 2,283 groups that have more. Under that rule, 18 of Q1's 19 locators and CL-085's locator stay valid; only `datahub-mlmu-25::d-ai-readiness` splits.
- *Links into the node from elsewhere* include: edge endpoints in the same chunk, cross-document `from_key`/`to_key` edges (`xdoc_conflict_held`), `term_link_judged.node_key`, the three overlay types (keyed on doc and item), and `node_key`/`grounding_span_id` in `kg_questions.yaml` and `definition_pairs.csv`. Edge events already carry `chunk_id`, so endpoint resolution can become chunk-scoped. This alone re-homes the 3,322 misattached edges. Overlays and judged links carry no chunk. For a qualified group, each must be resolved by matching its `old_span` (relocations) or node text, or refused as ambiguous.
- *Projection:* `node_key` gains a chunk argument. `resolve_endpoint` resolves local ids within the asserting chunk. Expected counts are G6's (a) column.
- *DD-020:* extended in the direction it already points: the loader never decides identity by accident of an id. Same-term nodes (1,811 pairs) become separate per-chunk nodes. Uniting them is then an explicit within-document merge, by `merge.normalized_key` or by the DD-044 vocabulary, made with provenance and never by the key.

**(b) Keep `<doc>::<id>`, accept the first assertion, and refuse a later assertion whose span differs, routing it to quarantine.**

- *Existing keys:* unchanged.
- *Links into the node:* unchanged, but they may now point at a different item. Edges asserted in the refused chunks still name the id, so they attach to the first item instead of the last. This moves the misattachment rather than removing it.
- *Projection:* one refusal branch.
- *DD-020:* untouched. But (b) turns a silent overwrite into a silent loss of extraction: 4,511 grounded items leave the graph, and the Commerce glossary drops from 48 to 38. It also gives quarantine a reason that is the harness's fault, not the model's.

**Recommendation: (a).** It is the standard answer to merging locally identified statements (standardize apart, then merge explicitly), it recovers every lost span and wrong node without discarding a grounded item, and the edges needed to re-home the misattached links already carry the chunk. (b) only changes which item is lost.

**Two decisions the fix task must make that this audit cannot:**

1. **The 31 multi-run documents.** Qualifying by chunk separates `bulk_v038` nodes from v1 and v0.3.0 nodes of the same document, which turns 479 cross-run overwrites into cross-run duplicates. Two whole-document runs (`batch-002`, `batch-004`) share the empty chunk id, so (a) alone would not even separate those. `extraction_superseded` keys on `(doc, source_sha256)` and cannot retire an older run of the same source without also dropping the newer one, so a run-scoped supersession is a prerequisite.
2. **Positional ids.** 2,180 of the collisions come from ids the prompt lets the model number per chunk. A prompt or parser change that derives ids from the item's text would stop new collisions at the source. That is a schema-review change (CLAUDE.md invariant 4) and is listed here only as the root cause.

## 5. Limits

- Identity equality is exact after normalisation and case-folding. A paraphrased claim under one id is therefore a `collision`, not `same_term_lost_evidence`. G5's containment count (331) bounds the narrower-or-wider subset only. Spelling variants escape it too: G9 holds `Relevance`/`relevant` and `Model Context Protocols (MCPs)`/`Model Context Protocol (MCP)`. So `collision` (2,703) is an **upper bound** on wrong nodes, not a count of them. Its lower bound would require judging each pair, and this task forbids a model.
- Instrument spans are the `grounding_spans` list joined, and Instrument nodes were excluded from the Neo4j span control, whose property is a list.
- The Commerce figure under (a) and (b) uses a proxy for the two-pipelines metric: a span that names `<term><fn>:`. The proxy reproduces 48 under the current keying.

## Generated tables (G1–G9)

<!-- BEGIN GENERATED: scripts/audit_node_key_fusion.py -->

### G1. What was read

`node_asserted` events on the untagged log: 30859; projected 30760 (skipped: non-graph purpose or quarantined batch 0, superseded extraction or stratum 99, label outside `kg/schema.yaml` 0). (label, key) groups: 26035; asserted more than once: 2396; with at least one span lost (a non-benign row): 2283. Keys carried by two labels (two nodes, not fusion): 83.

### G2. Overwritten (span, identity) pairs by label and class

A row is one distinct (normalised span, normalised identity) pair a later assertion replaced. The last column counts distinct normalised spans that differ from the survivor's, per node: the evidence no longer on the graph.

| label | fused (label, key) groups | benign_duplicate | same_term_lost_evidence | collision | non-benign rows | distinct spans lost |
|---|---|---|---|---|---|---|
| Claim | 331 | 22 | 5 | 861 | 866 | 865 |
| Concept | 1395 | 77 | 1373 | 1283 | 2656 | 2655 |
| Definition | 162 | 16 | 90 | 132 | 222 | 222 |
| Framework | 64 | 8 | 38 | 41 | 79 | 79 |
| Instrument | 84 | 3 | 95 | 78 | 173 | 173 |
| Measure | 91 | 14 | 25 | 77 | 102 | 101 |
| Platform | 61 | 0 | 79 | 24 | 103 | 103 |
| Practice | 52 | 3 | 1 | 89 | 90 | 90 |
| Standard | 126 | 4 | 91 | 95 | 186 | 186 |
| Tool | 30 | 0 | 14 | 23 | 37 | 37 |
| **all** | 2396 | 147 | 1811 | 2703 | 4514 | 4511 |

### G3. By origin of the overwritten assertion

| origin | benign_duplicate | same_term_lost_evidence | collision |
|---|---|---|---|
| same_chunk | 0 | 0 | 0 |
| other_chunk_same_run | 127 | 1576 | 2479 |
| other_run | 20 | 235 | 224 |

### G4. By extraction run of the survivor (shard | purpose | model | prompt)

| run | documents | benign_duplicate | same_term_lost_evidence | collision |
|---|---|---|---|---|
| `batch-004.jsonl|-|claude-opus-4-8|0.2.0` | 3 | 1 | 29 | 16 |
| `batch-023.jsonl|bulk_v038|claude-opus-5|0.3.8` | 62 | 146 | 1782 | 2687 |

### G5. Two qualifiers on the classes

Collisions where one identity text contains the other (a narrower or wider statement of one item rather than two items): 331 of 2703. Non-benign rows whose node also carries a `grounding_relocated` overlay, which the projection applies after every assertion: 432. The `grounding_relocated` overlays on fused nodes were written against the survivor's span 30 times, against an overwritten assertion's span 209 times (the overlay then puts that earlier item's relocated span onto the survivor), and against neither 62 times. Projected edges asserted in a chunk whose own assertion of an endpoint was overwritten as a collision, so the edge now attaches to a different item: 3322 of 38485 projectable `edge_asserted` events (`about` 901, `applies_to` 105, `asserts` 853, `builds_on` 23, `consumes` 5, `defines` 130, `has_component` 20, `implemented_by` 2, `implements` 6, `measures` 150, `mentions` 958, `precedes` 2, `recommends` 89, `subtype_of` 16, `supported_by` 11, `targets` 1, `uses_measure` 50). Rows on a positional local id (`POSITIONAL_ID`, e.g. `d1`, `cl4`): benign_duplicate 3 of 147; same_term_lost_evidence 45 of 1811; collision 2180 of 2703.

### G6. Cited figures recomputed from the log under each keying

`current` is today's `<doc>::<id>` last-wins and is the positive control: it must reproduce the stored figure. `chunk` is fix (a), `first` is fix (b).

| figure | stored | current | chunk (a) | first (b) |
|---|---|---|---|---|
| Definition nodes | 2064 | 2064 | 2281 | 2064 |
| Definition nodes outside the Commerce document (the 1,975 epoch) | 1975 | 1975 | 2180 | 1975 |
| Claim nodes | — | 6906 | 7768 | 6906 |
| Instrument nodes | 502 | 502 | 669 | 502 |
| Q1 definitions | 19 | 19 | 20 | 20 |
| Q1 documents |  | 11 | 11 | 11 |
| Q4 Instrument nodes named for readiness | 29 | 29 | 31 | 31 |
| Commerce glossary terms with a Definition whose span names `<term><fn>:` (of 49) | 48 (two-pipelines metric) | 48 | 48 | 38 |
| Q2 `uncertainty` | 0 | 0 | 0 | 0 |
| Q2 `provenance` | 1 | 1 | 1 | 1 |
| Q2 `license` | 0 | 0 | 0 | 0 |
| Q2 `revision` | 0 | 0 | 0 | 0 |
| Q2 `timeliness` | 1 | 1 | 1 | 1 |
| Q2 `discoverability` | 4 | 4 | 4 | 4 |
| Q2 `machine-readable` | 2 | 2 | 2 | 2 |
| Q2 `semantic consistency` | 0 | 0 | 0 | 0 |
| Q2 `authority` | 0 | 0 | 0 | 0 |
| Q2 `disclosure` | 0 | 0 | 0 | 0 |

Glossary terms the `current` keying finds and fix (b) would lose: 10: Croissant vocabulary, Data Catalog Vocabulary- United States (DCAT-US), Documentation, JavaScript Object Notation (JSON) format, JavaScript Object Notation for Linked Data (JSON-LD), Machine-readable data, Metadata, Open data, Version control, ZIP.

Q1 keys that gain a node under fix (a): `data-readiness-for-ai-a-360-degree-survey::d1`.

### G7. The stored Q1 rows and their fusion

| Q1 node key | assertions | classes of overwritten pairs |
|---|---|---|
| `ai-readiness-building-the-bridge-from-higher-education-to-wo::def-ai-readiness` | 1 | not fused |
| `ai-readiness-for-official-data-and-statistics-un-statistical::def_ai_readiness` | 1 | not fused |
| `artificial-intelligence-domain-ai-readiness-and-firm-product::d-domain-ai-readiness` | 1 | not fused |
| `data-readiness-for-ai-a-360-degree-survey::d_drai` | 1 | not fused |
| `data-readiness-for-scientific-ai-at-scale::d_airready` | 1 | not fused |
| `data-readiness-for-scientific-ai-at-scale::d_airready_state` | 1 | not fused |
| `datahub-mlmu-25::d-ai-readiness` | 2 | same_term_lost_evidence ×1 |
| `from-school-ai-readiness-to-student-ai-literacy::def_inst_ai_readiness` | 1 | not fused |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_genai_ready` | 1 | not fused |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_genai_ready_open_data` | 1 | not fused |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::def_ai_ready_data` | 1 | not fused |
| `nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data` | 1 | not fused |
| `uk-ai-ready-data-action-plan-2026::d_ai_readiness_esynergy` | 1 | not fused |
| `uk-ai-ready-data-action-plan-2026::d_ai_ready` | 1 | not fused |
| `uk-ai-ready-data-action-plan-2026::d_ai_ready_datasets` | 1 | not fused |
| `worldbank-blog-open-data-to-ai-ready-2025::d1` | 2 | benign_duplicate ×1 |
| `worldbank-blog-open-data-to-ai-ready-2025::d2` | 1 | not fused |
| `worldbank-blog-open-data-to-ai-ready-2025::def_airdd` | 1 | not fused |
| `worldbank-blog-open-data-to-ai-ready-2025::def_systems` | 1 | not fused |

### G8. By document (non-benign first)

| document | benign_duplicate | same_term_lost_evidence | collision |
|---|---|---|---|
| `nist-ai-rmf-playbook` | 44 | 169 | 270 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality` | 9 | 138 | 176 |
| `census-acs-general-handbook-2020` | 5 | 78 | 235 |
| `nist-generative-ai-profile-ai-600-1` | 7 | 200 | 98 |
| `w3c-dcat-3` | 0 | 47 | 183 |
| `fcsm-20-04-a-framework-for-data-quality` | 9 | 132 | 39 |
| `data-readiness-for-ai-a-360-degree-survey` | 1 | 61 | 103 |
| `chen-2025-geo-how-to-dominate-ai-search` | 3 | 61 | 100 |
| `ebu-bbc-2025-news-integrity-ai-assistants` | 0 | 44 | 110 |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | 0 | 61 | 85 |
| `van-der-bles-2019-communicating-uncertainty` | 1 | 22 | 120 |
| `statcan-quality-guidelines-6th-edition` | 0 | 23 | 118 |
| `ccsa-2026-ai-ready-official-statistics` | 0 | 12 | 127 |
| `webb-2026-state-fidelity-validity` | 0 | 34 | 93 |
| `nist-ai-risk-management-framework-ai-rmf` | 0 | 32 | 89 |
| `aidrin-hiniduma-2024` | 4 | 72 | 26 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de` | 2 | 28 | 54 |
| `slsa-specification-v1-0` | 2 | 38 | 41 |
| `usdc-mcp-federal-open-data-pilot-2026` | 0 | 21 | 54 |
| `statistical-policy-working-paper-46-data-quality-assessment` | 14 | 41 | 31 |
| `aggarwal-2024-geo-generative-engine-optimization` | 0 | 50 | 18 |
| `zhou-2026-loomsum-table-grounded-faithfulness` | 1 | 27 | 41 |
| `venktesh-2024-quantemp-numerical-claims` | 0 | 23 | 42 |
| `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` | 0 | 17 | 44 |
| `cao-2024-multimodal-long-form-summarization-financial-reports` | 1 | 23 | 29 |
| `doe-data-cards-standardized-metadata-2026` | 1 | 21 | 30 |
| `min-2023-factscore` | 0 | 20 | 29 |
| `odcs-open-data-contract-standard` | 1 | 5 | 44 |
| `odi-framework-for-ai-ready-data-2025` | 0 | 7 | 35 |
| `mlcommons-croissant-spec` | 1 | 24 | 11 |
| `zhao-2020-reducing-quantity-hallucinations` | 0 | 25 | 9 |
| `sdmx-3-0-section-1-framework` | 0 | 6 | 25 |
| `uk-ai-ready-data-action-plan-2026` | 4 | 23 | 8 |
| `aidrin-2-0-a-framework-to-assess-data-readiness-for-ai` | 0 | 24 | 5 |
| `mazzi-2021-measuring-communicating-uncertainty-official-economic-statistics` | 3 | 15 | 14 |
| `llmstxt-proposal` | 2 | 9 | 17 |
| `peters-2025-generalization-bias-llm-summarization` | 0 | 12 | 14 |
| `manski-2015-communicating-uncertainty-official-economic-statistics` | 0 | 8 | 17 |
| `du-2026-possible-or-definite` | 0 | 3 | 21 |
| `sitemaps-protocol` | 2 | 15 | 8 |
| `suleymanli-2025-llms-charts-official-statistics` | 0 | 4 | 19 |
| `radhakrishnan-2024-knowing-when-to-ask-data-commons` | 0 | 14 | 8 |
| `rfc-9309-robots-exclusion-protocol` | 2 | 12 | 10 |
| `datahub-mlmu-25` | 0 | 16 | 5 |
| `worldbank-blog-open-data-to-ai-ready-2025` | 1 | 2 | 18 |
| `croissant-akhtar-2024-paper` | 0 | 12 | 4 |
| `fcsm-25-03` | 1 | 8 | 7 |
| `lee-2026-when-summaries-distort-decisions` | 0 | 13 | 0 |
| `perplexity-crawlers` | 4 | 9 | 2 |
| `doc-rfi-ai-open-gov-data-2024` | 11 | 4 | 5 |
| `ons-uncertainty-and-how-we-measure-it` | 2 | 8 | 0 |
| `schema-org-dataset` | 1 | 7 | 1 |
| `wilkinson-2016-fair-guiding-principles` | 0 | 5 | 2 |
| `bandi-2025-metadata-ai-ready` | 0 | 6 | 0 |
| `schema-org-definedterm` | 0 | 5 | 0 |
| `worldbank-fostering-ai-readiness-official-statistics` | 3 | 4 | 1 |
| `cloudflare-ai-crawl-control-manage-crawlers` | 0 | 3 | 1 |
| `google-robots-txt-intro` | 0 | 1 | 3 |
| `openai-crawlers-bots` | 2 | 2 | 2 |
| `odi-ai-ready-national-data-library-2025` | 1 | 1 | 2 |
| `sdmx-standards-overview` | 2 | 2 | 0 |
| `sainz-2023-llm-data-contamination` | 0 | 1 | 0 |
| `unsc-2026-stoyanovich-open-data-responsible-reuse` | 0 | 1 | 0 |

### G9. Collisions (task decision 2: a wrong node, not a lost span)

All 2703 are listed in full in the CSV (`class == collision`, both identity texts verbatim after normalisation). The Definition collisions are listed in full here because the record cites Definition counts; every other label is counted.

| label | collisions |
|---|---|
| Claim | 861 |
| Concept | 1283 |
| Definition | 132 |
| Framework | 41 |
| Instrument | 78 |
| Measure | 77 |
| Platform | 24 |
| Practice | 89 |
| Standard | 95 |
| Tool | 23 |

| key | survivor term | overwritten term | origin | overwritten at |
|---|---|---|---|---|
| `aggarwal-2024-geo-generative-engine-optimization::d-seo` | search engine optimization | Search engine optimization (SEO) | other_run | batch-006.jsonl:665 |
| `aidrin-hiniduma-2024::d-fairness` | Fairness | Fairness (in a dataset) | other_run | batch-002.jsonl:499 |
| `cao-2024-multimodal-long-form-summarization-financial-reports::d1` | Numeric hallucinations | extractive | other_chunk_same_run | batch-023.jsonl:35021 |
| `cao-2024-multimodal-long-form-summarization-financial-reports::d1` | Numeric hallucinations | Type A | other_chunk_same_run | batch-023.jsonl:35102 |
| `cao-2024-multimodal-long-form-summarization-financial-reports::d2` | Fabricated Number | similarity(S, R) | other_chunk_same_run | batch-023.jsonl:35022 |
| `cao-2024-multimodal-long-form-summarization-financial-reports::d2` | Fabricated Number | Type B | other_chunk_same_run | batch-023.jsonl:35103 |
| `cao-2024-multimodal-long-form-summarization-financial-reports::d3` | Rounding Error | Type C | other_chunk_same_run | batch-023.jsonl:35104 |
| `cao-2024-multimodal-long-form-summarization-financial-reports::d4` | Arithmetic Error | Type D | other_chunk_same_run | batch-023.jsonl:35105 |
| `ccsa-2026-ai-ready-official-statistics::d1` | semantic searchability | Semantic versioning for datasets | other_chunk_same_run | batch-023.jsonl:52081 |
| `ccsa-2026-ai-ready-official-statistics::d1` | semantic searchability | FAIR principles | other_chunk_same_run | batch-023.jsonl:52290 |
| `census-acs-general-handbook-2020::d1` | Detailed Tables | Parishes | other_chunk_same_run | batch-023.jsonl:37272 |
| `census-acs-general-handbook-2020::d1` | Detailed Tables | County equivalents | other_chunk_same_run | batch-023.jsonl:36155 |
| `census-acs-general-handbook-2020::d1` | Detailed Tables | survey response rate | other_chunk_same_run | batch-023.jsonl:35885 |
| `census-acs-general-handbook-2020::d1` | Detailed Tables | rural | other_chunk_same_run | batch-023.jsonl:37528 |
| `census-acs-general-handbook-2020::d1` | Detailed Tables | controls | other_chunk_same_run | batch-023.jsonl:38792 |
| `census-acs-general-handbook-2020::d1` | Detailed Tables | item nonresponse | other_chunk_same_run | batch-023.jsonl:38674 |
| `census-acs-general-handbook-2020::d3` | Estimates | Custom Tables | other_chunk_same_run | batch-023.jsonl:38793 |
| `census-acs-general-handbook-2020::d3` | Estimates | Item allocation rates | other_chunk_same_run | batch-023.jsonl:38676 |
| `census-acs-general-handbook-2020::d_block_group` | block group | block groups | other_chunk_same_run | batch-023.jsonl:36255 |
| `chen-2025-geo-how-to-dominate-ai-search::d1` | Jaccard overlap | Brand | other_chunk_same_run | batch-023.jsonl:9570 |
| `chen-2025-geo-how-to-dominate-ai-search::d_geo` | Generative Engine Optimization | Generative Engine Optimization (GEO) | other_chunk_same_run | batch-023.jsonl:109 |
| `chen-2025-geo-how-to-dominate-ai-search::d_geo` | Generative Engine Optimization | Generative Engine Optimization (GEO) | other_run | batch-006.jsonl:7273 |
| `data-readiness-for-ai-a-360-degree-survey::d1` | data model | Structured data | other_chunk_same_run | batch-023.jsonl:6090 |
| `data-readiness-for-ai-a-360-degree-survey::d1` | data model | Topic coherence | other_chunk_same_run | batch-023.jsonl:6752 |
| `data-readiness-for-ai-a-360-degree-survey::d1` | data model | timeliness | other_chunk_same_run | batch-023.jsonl:6516 |
| `data-readiness-for-ai-a-360-degree-survey::d1` | data model | Data readiness for artificial intelligence (AI) | other_chunk_same_run | batch-023.jsonl:5917 |
| `data-readiness-for-ai-a-360-degree-survey::d2` | data organization | bias indicator | other_chunk_same_run | batch-023.jsonl:6753 |
| `data-readiness-for-ai-a-360-degree-survey::d2` | data organization | Completeness | other_chunk_same_run | batch-023.jsonl:6091 |
| `data-readiness-for-ai-a-360-degree-survey::d2` | data organization | Data privacy | other_chunk_same_run | batch-023.jsonl:6517 |
| `data-readiness-for-ai-a-360-degree-survey::d3` | image quality | data imputation | other_chunk_same_run | batch-023.jsonl:6092 |
| `ebu-bbc-2025-news-integrity-ai-assistants::d1` | European Broadcasting Union | ceremonial citations | other_chunk_same_run | batch-023.jsonl:40244 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d1` | relevance | false positive | other_chunk_same_run | batch-023.jsonl:23133 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d1` | relevance | proprietary data | other_chunk_same_run | batch-023.jsonl:21977 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d1` | relevance | SESTAT | other_chunk_same_run | batch-023.jsonl:23985 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d1` | relevance | positive rating | other_chunk_same_run | batch-023.jsonl:24324 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d1` | relevance | telecommunications services | other_chunk_same_run | batch-023.jsonl:23447 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d2` | Relevance | false negative | other_chunk_same_run | batch-023.jsonl:23134 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d2` | Relevance | Accuracy | other_chunk_same_run | batch-023.jsonl:22063 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d2` | Relevance | alternative data | other_chunk_same_run | batch-023.jsonl:21978 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d2` | Relevance | CPI | other_chunk_same_run | batch-023.jsonl:23448 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d3` | Accuracy | inflation | other_chunk_same_run | batch-023.jsonl:23449 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d3` | Accuracy | Corporate data | other_chunk_same_run | batch-023.jsonl:21979 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d3` | Accuracy | Timeliness | other_chunk_same_run | batch-023.jsonl:22064 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d4` | Timeliness | Accessibility | other_chunk_same_run | batch-023.jsonl:22065 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d4` | Timeliness | Secondary source data | other_chunk_same_run | batch-023.jsonl:21980 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d5` | Punctuality | Comparability | other_chunk_same_run | batch-023.jsonl:22066 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d5` | Punctuality | Web scraping data | other_chunk_same_run | batch-023.jsonl:21981 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d6` | Accessibility | coverage | other_chunk_same_run | batch-023.jsonl:21982 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d6` | Accessibility | Coherence | other_chunk_same_run | batch-023.jsonl:22067 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d7` | Clarity | Completeness | other_chunk_same_run | batch-023.jsonl:22068 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d7` | Clarity | integrated data | other_chunk_same_run | batch-023.jsonl:21983 |
| `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d8` | Coherence | data quality | other_chunk_same_run | batch-023.jsonl:22069 |
| `fcsm-20-04-a-framework-for-data-quality::d-statistical-precision-icsp` | statistical precision | statistical precision (ICSP) | other_run | batch-004.jsonl:9998 |
| `fcsm-20-04-a-framework-for-data-quality::d1` | gold standard | Data quality | other_chunk_same_run | batch-023.jsonl:11139 |
| `fcsm-20-04-a-framework-for-data-quality::d1` | gold standard | Confdentiality | other_chunk_same_run | batch-023.jsonl:11787 |
| `fcsm-20-04-a-framework-for-data-quality::d2` | sensitivity analysis | Utility | other_chunk_same_run | batch-023.jsonl:11140 |
| `fcsm-20-04-a-framework-for-data-quality::d_computer_physical_security` | Computer and physical security of data | Computer and physical security | other_chunk_same_run | batch-023.jsonl:10777 |
| `fcsm-20-04-a-framework-for-data-quality::d_relevance` | relevant | Relevance | other_chunk_same_run | batch-023.jsonl:10767 |
| `fcsm-25-03::def-mcp` | Model Context Protocols (MCPs) | Model Context Protocol (MCP) | other_run | batch-002.jsonl:201 |
| `from-accuracy-to-readiness-metrics-and-benchmarks-for-human::d1` | AI-harm | regions-of-no-use | other_run | batch-004.jsonl:4124 |
| `from-accuracy-to-readiness-metrics-and-benchmarks-for-human::d2` | near-misses | safe levers | other_run | batch-004.jsonl:4125 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d1` | Metadata | Data Quality and Integrity | other_chunk_same_run | batch-023.jsonl:57625 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_croissant` | Croissant vocabulary | Croissant | other_chunk_same_run | batch-023.jsonl:58083 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_dcat_us` | Data Catalog Vocabulary- United States (DCAT-US) | DCAT-US | other_chunk_same_run | batch-023.jsonl:58031 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_json` | JavaScript Object Notation (JSON) format | JSON | other_chunk_same_run | batch-023.jsonl:58148 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_jsonld` | JavaScript Object Notation for Linked Data (JSON-LD) | JSON-LD 1.1 | other_chunk_same_run | batch-023.jsonl:58149 |
| `generative-ai-and-open-data-guidelines-and-best-practices-de::d_machine_readable` | Machine-readable data | machine -readable formats | other_chunk_same_run | batch-023.jsonl:57697 |
| `mazzi-2021-measuring-communicating-uncertainty-official-economic-statistics::d1` | Sampling error | aleatory uncertainty | other_chunk_same_run | batch-023.jsonl:42296 |
| `min-2023-factscore::d1` | Not-supported | FACTSCORE | other_chunk_same_run | batch-023.jsonl:43524 |
| `min-2023-factscore::d1` | Not-supported | freqValue | other_chunk_same_run | batch-023.jsonl:43654 |
| `nist-ai-rmf-playbook::d1` | Risk | Disparate impact | other_run | batch-004.jsonl:3342 |
| `nist-ai-rmf-playbook::d1` | Risk | Disparate impact | other_chunk_same_run | batch-023.jsonl:26137 |
| `nist-ai-rmf-playbook::d1` | Risk | human-AI configurations | other_chunk_same_run | batch-023.jsonl:26982 |
| `odcs-open-data-contract-standard::d1` | uniqueItems | Property-level relationships | other_chunk_same_run | batch-023.jsonl:19102 |
| `odcs-open-data-contract-standard::d1` | uniqueItems | PostgreSQL | other_chunk_same_run | batch-023.jsonl:18950 |
| `odcs-open-data-contract-standard::d1` | uniqueItems | mustBeBetween | other_chunk_same_run | batch-023.jsonl:18788 |
| `odcs-open-data-contract-standard::d1` | uniqueItems | kind | other_chunk_same_run | batch-023.jsonl:18806 |
| `odcs-open-data-contract-standard::d2` | multipleOf | shorthand notation | other_chunk_same_run | batch-023.jsonl:19103 |
| `odcs-open-data-contract-standard::d2` | multipleOf | Amazon S3 | other_chunk_same_run | batch-023.jsonl:18951 |
| `odcs-open-data-contract-standard::d2` | multipleOf | id | other_chunk_same_run | batch-023.jsonl:18807 |
| `odcs-open-data-contract-standard::d3` | maxLength | Secure File Transfer Protocol | other_chunk_same_run | batch-023.jsonl:18952 |
| `odcs-open-data-contract-standard::d3` | maxLength | version | other_chunk_same_run | batch-023.jsonl:18808 |
| `odcs-open-data-contract-standard::d4` | required | Microsoft SQL Server | other_chunk_same_run | batch-023.jsonl:18953 |
| `odcs-open-data-contract-standard::d4` | required | status | other_chunk_same_run | batch-023.jsonl:18809 |
| `odcs-open-data-contract-standard::d5` | timezone | Actian Zen | other_chunk_same_run | batch-023.jsonl:18954 |
| `odcs-open-data-contract-standard::d5` | timezone | tags | other_chunk_same_run | batch-023.jsonl:18810 |
| `peters-2025-generalization-bias-llm-summarization::d1` | Prompt transformation | Undergeneralizations | other_chunk_same_run | batch-023.jsonl:44502 |
| `sdmx-3-0-section-1-framework::d1` | SDMX-CSV | Gateway exchange | other_chunk_same_run | batch-023.jsonl:15699 |
| `sdmx-3-0-section-1-framework::d1` | SDMX-CSV | reference metadata set | other_chunk_same_run | batch-023.jsonl:15787 |
| `slsa-specification-v1-0::d1` | Expectations | Completeness | other_chunk_same_run | batch-023.jsonl:20000 |
| `slsa-specification-v1-0::d1` | Expectations | SLSA | other_chunk_same_run | batch-023.jsonl:19462 |
| `slsa-specification-v1-0::d2` | Provenance verification | Authenticity | other_chunk_same_run | batch-023.jsonl:20001 |
| `slsa-specification-v1-0::d2` | Provenance verification | SLSA track | other_chunk_same_run | batch-023.jsonl:19463 |
| `slsa-specification-v1-0::df1` | verification | Pinned dependencies | other_chunk_same_run | batch-023.jsonl:19727 |
| `statcan-quality-guidelines-6th-edition::d1` | Gather evaluation inputs | Identify concepts | other_chunk_same_run | batch-023.jsonl:45710 |
| `statcan-quality-guidelines-6th-edition::d1` | Gather evaluation inputs | Statistical business process | other_chunk_same_run | batch-023.jsonl:45429 |
| `statcan-quality-guidelines-6th-edition::d1` | Gather evaluation inputs | Design outputs | other_chunk_same_run | batch-023.jsonl:45787 |
| `statcan-quality-guidelines-6th-edition::d1` | Gather evaluation inputs | Imputation | other_chunk_same_run | batch-023.jsonl:46159 |
| `statcan-quality-guidelines-6th-edition::d1` | Gather evaluation inputs | Quality | other_chunk_same_run | batch-023.jsonl:45386 |
| `statcan-quality-guidelines-6th-edition::d2` | Conduct evaluation | Crowdsourcing | other_chunk_same_run | batch-023.jsonl:45430 |
| `statcan-quality-guidelines-6th-edition::d2` | Conduct evaluation | Design data analysis | other_chunk_same_run | batch-023.jsonl:45788 |
| `statcan-quality-guidelines-6th-edition::d2` | Conduct evaluation | PUMF | other_chunk_same_run | batch-023.jsonl:46160 |
| `statcan-quality-guidelines-6th-edition::d3` | Agree on an action plan | shared file | other_chunk_same_run | batch-023.jsonl:46161 |
| `statcan-quality-guidelines-6th-edition::d3` | Agree on an action plan | Web Mapping | other_chunk_same_run | batch-023.jsonl:45431 |
| `statistical-policy-working-paper-46-data-quality-assessment::d1` | Relevance | client | other_chunk_same_run | batch-023.jsonl:16686 |
| `statistical-policy-working-paper-46-data-quality-assessment::d1` | Relevance | data quality | other_run | batch-004.jsonl:5724 |
| `statistical-policy-working-paper-46-data-quality-assessment::d1` | Relevance | Interpretability | other_chunk_same_run | batch-023.jsonl:16910 |
| `statistical-policy-working-paper-46-data-quality-assessment::d2` | Accessibility | Relevance | other_run | batch-004.jsonl:5725 |
| `van-der-bles-2019-communicating-uncertainty::d1` | hypothetical | fan chart | other_chunk_same_run | batch-023.jsonl:48398 |
| `van-der-bles-2019-communicating-uncertainty::d1` | hypothetical | Direct uncertainty | other_chunk_same_run | batch-023.jsonl:47523 |
| `van-der-bles-2019-communicating-uncertainty::d1` | hypothetical | likelihood ratio | other_chunk_same_run | batch-023.jsonl:47587 |
| `van-der-bles-2019-communicating-uncertainty::d2` | prosecutor’s fallacy | Indirect uncertainty | other_chunk_same_run | batch-023.jsonl:47524 |
| `venktesh-2024-quantemp-numerical-claims::d1` | usefulness | Numeric claims | other_chunk_same_run | batch-023.jsonl:49198 |
| `venktesh-2024-quantemp-numerical-claims::d1` | usefulness | Unleaked Evidence | other_chunk_same_run | batch-023.jsonl:49260 |
| `w3c-dcat-3::d-checksum` | Checksum | spdx:Checksum | other_run | batch-006.jsonl:3720 |
| `w3c-dcat-3::d-dataset` | dataset | dcat:Dataset | other_run | batch-006.jsonl:3714 |
| `w3c-dcat-3::d-resource` | Resource | dcat:Resource | other_run | batch-006.jsonl:3712 |
| `w3c-dcat-3::d1` | dcat:Dataset | dataset | other_chunk_same_run | batch-023.jsonl:3893 |
| `w3c-dcat-3::d1` | dcat:Dataset | homepage | other_chunk_same_run | batch-023.jsonl:4100 |
| `w3c-dcat-3::d1` | dcat:Dataset | language | other_chunk_same_run | batch-023.jsonl:4227 |
| `w3c-dcat-3::d2` | dcat:distribution | DCAT profile | other_chunk_same_run | batch-023.jsonl:3894 |
| `w3c-dcat-3::d2` | dcat:distribution | resource | other_chunk_same_run | batch-023.jsonl:4101 |
| `w3c-dcat-3::d3` | dcterms:accrualPeriodicity | dataset | other_chunk_same_run | batch-023.jsonl:4102 |
| `w3c-dcat-3::d3` | dcterms:accrualPeriodicity | identifier | other_chunk_same_run | batch-023.jsonl:4228 |
| `w3c-dcat-3::d4` | dcat:inSeries | category | other_chunk_same_run | batch-023.jsonl:4229 |
| `w3c-dcat-3::d4` | dcat:inSeries | service | other_chunk_same_run | batch-023.jsonl:4103 |
| `w3c-dcat-3::d5` | dcterms:spatial | catalog | other_chunk_same_run | batch-023.jsonl:4104 |
| `w3c-dcat-3::d5` | dcterms:spatial | genre | other_chunk_same_run | batch-023.jsonl:4230 |
| `w3c-dcat-3::d6` | dcat:spatialResolutionInMeters | record | other_chunk_same_run | batch-023.jsonl:4105 |
| `w3c-dcat-3::d6` | dcat:spatialResolutionInMeters | relation | other_chunk_same_run | batch-023.jsonl:4231 |
| `webb-2026-state-fidelity-validity::d1` | T2 | T5 | other_chunk_same_run | batch-023.jsonl:17704 |
| `zhou-2026-loomsum-table-grounded-faithfulness::d1` | † | Table-Grounded Faithfulness | other_chunk_same_run | batch-023.jsonl:50392 |

<!-- END GENERATED: scripts/audit_node_key_fusion.py -->
