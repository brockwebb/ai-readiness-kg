# One document, two pipelines: Commerce's glossary in this graph and in the FSS policy graph

**Task:** `cc_tasks/2026-10-02_commerce_guidance_admission_ADDENDUM-01.md` decisions 9 to 13.
**Produced by:** `scripts/fss_airkg_reconciliation.py --phase glossary` (ground truth) and
`--phase pipelines` (the comparison); rows in `state/commerce_two_pipelines_2026-10-02.json`; the
term list in `docs/research/2026-10-02_commerce_guidance_glossary_terms.csv`. Zero model calls in
the comparison itself.

**What this is.** An illustration of how two extraction pipelines diverged on one document in one
pass each. It is not an estimate of either pipeline's fidelity: an estimate needs a sample of
documents drawn from each corpus (dozens, stratified by document type, with each defined term
adjudicated against its source), and the two pipelines differ in schema, model, prompt and
segmentation at once, so even a sampled difference could not be attributed to any one of them. No
threshold, no pass line, no winner.

**Why the document was re-extracted rather than copied over.** The FSS graph's nodes carry its
own schema and its own harness's provenance, so they cannot enter this repository's event log; the
document was extracted here under the pinned model (`claude-opus-5`), prompt epoch (v0.3.8) and
schema, and both graphs now hold the same text (sha256 `87068818…bd91` in both ledgers).

## 1. The comparison, fixed before either graph was queried

**Ground truth:** the document's own glossary, appendix A1. Parsed by script from the text this
repository's extractor reads (`run_bulk_extraction.doc_text`): an entry opens a paragraph as
`<term><footnote number>: <definition>`, footnotes run 80 to 129, 123 is a figure credit. **N = 49.**
The parser refuses to write unless the footnotes it found are exactly 80..129 minus 123, so a missed
or invented entry stops it. Entries a page break splits (`Machine learning`, which runs across the
footnote block and running header of p. 71) are rejoined.

**Metric, per graph:** how many of the 49 terms have a Definition node built from the glossary entry.

* **This graph:** a `Definition` on the document whose `grounding_span`, normalised exactly as the
  grounding validator normalises (`kg.extraction.grounding.normalize`), names the entry
  (`<term><footnote>:`) and either lies inside the entry's source text or contains the entry's first
  60 characters. A span that stops after the entry's first sentence counts; so does a span with the
  appendix heading in front of the entry.
* **FSS graph:** a `Definition` whose `def_id` is under `doc_genai_open_data_2025` and whose
  `verbatim_text`, after NFKC and whitespace folding, contains the entry's definition text.

**The repository's own cross-system rule, and where it does not fit.** The trustgraph benchmark
(`cc_tasks/2026-08-23_trustgraph_benchmark.md` line 14; decision `docs/research/2026-08-23_tgbench2_decision.md`)
matched items "by type + normalized-text similarity ≥ 0.8". Its matcher was never committed, so it is
reconstructed here as `difflib.SequenceMatcher(autojunk=False).ratio` over folded, lower-cased text,
type `Definition` on both sides, and reported as a secondary column. It fits poorly: it was built to
compare two extractors' items to each other, and against a gold glossary it penalises a correct span
for being shorter than the entry (a first-sentence span) or for carrying the heading in front, which
is why it counts 29 where the span rule counts 48. It does not measure fabrication here; nothing in
this comparison does.

**Prior art.** Matching extracted spans to a gold span set at more than one strictness is the
SemEval-2013 Task 9 scheme (Segura-Bedmar, Martínez and Herrero-Zazo 2013: strict, exact boundary,
partial boundary, type), itself from the MUC scoring tradition; extracting term-definition pairs from
glossaries and semi-structured text, with gold annotations, is the DEFT corpus and SemEval-2020 Task 6
(Spala et al. 2019, 2020). The span rule above is a partial-boundary match with a type constraint.
These are cited from the literature as known, not retrieved in this session: the task's
`Network: none` excludes a web search, and the corpus (`search_text` over this graph) and Wintermute
returned nothing on gold-span or definition-extraction evaluation.

## 2. Result

| | this graph | FSS graph |
|---|---:|---:|
| glossary terms with a Definition from the entry (span rule) | **48 of 49** | **0 of 49** |
| the same under the trustgraph rule (type + similarity ≥ 0.8) | 29 of 49 | 0 of 49 |
| glossary entries present in the text layer (an FSS Segment containing the entry's opening) | n/a | 43 of 49 |
| model proposed a Definition for the term | 49 of 49 | n/a |
| proposed, quarantined at parse | 1 (`Machine learning`) | n/a |
| Definition nodes on the document, any section | 89 (from 102 asserted) | 0 (778 Segments) |

**The divergence is the whole glossary.** 48 terms are Definitions here and Segments (or nothing)
there; the one term absent from this graph's Definition layer is absent from both graphs' Definition
layers. The FSS side's 6 missing segments are entries its segmenter cut so that no segment opens with
the entry's first 60 characters (rows 5 to 7, 39, 43, 48 below); they are not evidence the text is
missing there.

**The one quarantine.** `Machine learning` (footnote 111) is the entry a page break splits: its
definition runs onto p. 72 past the footnote block and the running header. The model proposed it as
`d_ml` in chunk `#c0023` with the full two-sentence verbatim; the chunk's `chunk_metrics` records
`span_partial: 2`, and no `Machine learning` Definition from `#c0023` reached the shard. The parser
persists quarantine counts by reason per chunk, not the quarantined items, so the attribution to
`span_partial` (the anchor's sentence ends at the page break and does not cover the verbatim) is by
difference and by the chunk's reason count, not read off a row.

**Something this exercise found about this graph, outside the comparison.** 102 Definitions were
asserted on this document and 89 are nodes, because node keys are `<doc_id>::<local id>` and the model
reuses local ids across chunks: `d_documentation` names a body-text definition in `#c0004`, another in
`#c0008` and the glossary entry in `#c0023`, and the projection keeps the last. The glossary chunks
are ingested last, so all 48 glossary Definitions survived and 12 body-text definition spans were
overwritten. Across the whole `bulk_v038` shard the same mechanism overwrites 4,070 distinct spans on
1,966 keys in 64 documents, 815 of them Claim spans and 184 Definition spans (Concept re-assertion,
2,415, is partly by design: one concept, many mentions). DD-020 fixed the cross-document form of this
collision; the cross-chunk form is not in the decision record. Reported, not fixed here.

## 3. The 49 terms

| n | term | this graph: Definition key | FSS: Definition | FSS: Segment holding the entry | trustgraph rule here (sim) |
|---:|---|---|---|---|---|
| 1 | AI-ready data | `def_ai_ready_data` | — | `doc_genai_open_data_2025#s583` | yes (0.892) |
| 2 | Apache Parquet | `def_apache_parquet` | — | `doc_genai_open_data_2025#s584` | no (0.677) |
| 3 | Application Program Interface (API) | `def_api` | — | `doc_genai_open_data_2025#s585` | no (0.712) |
| 4 | Artificial intelligence (AI) | `def_ai` | — | `doc_genai_open_data_2025#s586` | no (0.503) |
| 5 | Artificial intelligence and machine learning (AI/ML) systems | `d_aiml_systems` | — | `— (no segment opens with the entry)` | no (0.72) |
| 6 | Artificial intelligence and machine learning (AI/ML) model training | `d_aiml_model_training` | — | `— (no segment opens with the entry)` | no (0.579) |
| 7 | Authoritative data | `d_authoritative_data` | — | `— (no segment opens with the entry)` | no (0.783) |
| 8 | Benchmarking datasets | `d_benchmarking_datasets` | — | `doc_genai_open_data_2025#s594` | no (0.739) |
| 9 | Comma Separated Values (CSV) file format | `d_csv` | — | `doc_genai_open_data_2025#s595` | yes (0.99) |
| 10 | Commerce data | `d_commerce_data` | — | `doc_genai_open_data_2025#s601` | no (0.542) |
| 11 | Crawlable | `d_crawlable` | — | `doc_genai_open_data_2025#s602` | no (0.703) |
| 12 | Croissant vocabulary | `d_croissant` | — | `doc_genai_open_data_2025#s603` | yes (0.997) |
| 13 | Data | `d_data` | — | `doc_genai_open_data_2025#s604` | yes (0.984) |
| 14 | Data catalog | `d_data_catalog` | — | `doc_genai_open_data_2025#s605` | yes (0.989) |
| 15 | Data dictionary | `d_data_dictionary` | — | `doc_genai_open_data_2025#s612` | yes (0.855) |
| 16 | Data integrity | `d_data_integrity` | — | `doc_genai_open_data_2025#s613` | no (0.695) |
| 17 | Dataset provenance | `d_dataset_provenance` | — | `doc_genai_open_data_2025#s614` | yes (0.859) |
| 18 | Data quality | `d_data_quality` | — | `doc_genai_open_data_2025#s615` | no (0.559) |
| 19 | Data Catalog Vocabulary (DCAT) | `d_dcat` | — | `doc_genai_open_data_2025#s616` | yes (0.995) |
| 20 | Data Catalog Vocabulary- United States (DCAT-US) | `d_dcat_us` | — | `doc_genai_open_data_2025#s617` | yes (0.992) |
| 21 | Derived data | `d_derived_data` | — | `doc_genai_open_data_2025#s625` | yes (0.98) |
| 22 | Digital signature | `d_digital_signature` | — | `doc_genai_open_data_2025#s626` | yes (0.99) |
| 23 | Documentation | `d_documentation` | — | `doc_genai_open_data_2025#s627` | yes (0.99) |
| 24 | Few-shot learning | `d_few_shot` | — | `doc_genai_open_data_2025#s628` | yes (0.989) |
| 25 | Findable, Accessible, Interoperable, and Reusable (FAIR) data principles | `d_fair` | — | `doc_genai_open_data_2025#s629` | yes (0.993) |
| 26 | Generative artificial intelligence (AI) system | `d_genai_system` | — | `doc_genai_open_data_2025#s630` | no (0.636) |
| 27 | Hierarchical data | `d_hierarchical` | — | `doc_genai_open_data_2025#s637` | yes (0.98) |
| 28 | Human-readable data | `d_human_readable` | — | `doc_genai_open_data_2025#s638` | no (0.315) |
| 29 | JavaScript Object Notation (JSON) format | `d_json` | — | `doc_genai_open_data_2025#s639` | yes (0.991) |
| 30 | JavaScript Object Notation for Linked Data (JSON-LD) | `d_jsonld` | — | `doc_genai_open_data_2025#s640` | yes (0.986) |
| 31 | Large language models (LLMs) | `d_llm` | — | `doc_genai_open_data_2025#s641` | yes (0.99) |
| 32 | Machine learning | — (proposed, quarantined at parse) | — | `doc_genai_open_data_2025#s642` | no (0.37) |
| 33 | Machine-readable data | `d_machine_readable` | — | `doc_genai_open_data_2025#s650` | no (0.764) |
| 34 | Machine-understandable | `d_machine_understandable` | — | `doc_genai_open_data_2025#s653` | yes (0.993) |
| 35 | Metadata | `d_metadata` | — | `doc_genai_open_data_2025#s654` | yes (0.982) |
| 36 | Open data | `d_open_data` | — | `doc_genai_open_data_2025#s657` | no (0.323) |
| 37 | Open-source software | `d_oss` | — | `doc_genai_open_data_2025#s658` | yes (0.989) |
| 38 | Portable Document Format (PDF) | `d_pdf` | — | `doc_genai_open_data_2025#s659` | yes (0.989) |
| 39 | RESTful API | `d_restful_api` | — | `— (no segment opens with the entry)` | yes (0.991) |
| 40 | Raw data | `d_raw_data` | — | `doc_genai_open_data_2025#s661` | yes (0.989) |
| 41 | Robots.txt file | `d_robots_txt` | — | `doc_genai_open_data_2025#s662` | yes (0.985) |
| 42 | schema.org metadata standard | `d_schema_org` | — | `doc_genai_open_data_2025#s669` | no (0.648) |
| 43 | Sitemap | `d_sitemap` | — | `— (no segment opens with the entry)` | no (0.677) |
| 44 | Version control | `d_version_control` | — | `doc_genai_open_data_2025#s675` | yes (0.986) |
| 45 | Web crawler | `d_web_crawler` | — | `doc_genai_open_data_2025#s676` | no (0.76) |
| 46 | World Wide Web Consortium (W3C) | `d_w3c` | — | `doc_genai_open_data_2025#s677` | yes (0.985) |
| 47 | Extensible Markup Language (XML) | `d_xml` | — | `doc_genai_open_data_2025#s678` | yes (0.99) |
| 48 | XML Format Spreadsheet (.XLSX) files | `d_xlsx` | — | `— (no segment opens with the entry)` | yes (0.99) |
| 49 | ZIP | `d_zip` | — | `doc_genai_open_data_2025#s680` | no (0.599) |

Keys in the third column are under `generative-ai-and-open-data-guidelines-and-best-practices-de::`.
The FSS Definition column is empty in every row because the FSS graph holds no Definition for this
document.

## 4. Limits

One document, one pass each. The FSS figure is read from the local `fss-policy-kg` database; the
hosted copy was not consulted. The span rule's 60-character opening is a choice, stated so it can be
moved; it was not varied in this run. Which pipeline's output is
"right" is not asked: a glossary entry as a Segment is a faithful copy of the text and as a Definition
is a typed claim about it, and the two serve different lookups.
