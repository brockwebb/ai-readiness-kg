# TrustGraph benchmark v2 — Phase 2, TrustGraph side (task `2026-08-23_trustgraph_benchmark_v2`, Seldon 36a5c0e1)

**Date:** 2026-08-26 (Phase 1 deployed 2026-08-25; see `2026-08-23_tgbench2_phase1_deploy.md`).
**Scope:** ontology load + ontology-driven extraction of the 5 pilot documents through the
`claude-cli-completion` backend (model pinned `claude-opus-4-8`, subscription OAuth, no API key)
+ per-document export of triples/provenance/evidence. Our extractor's side runs elsewhere
(orchestrator); nothing here touches `kg/`, `events/`, or the live graph.

## 1. Ontology load + fidelity

**Format conversion.** TrustGraph's ontology store is not OWL/Turtle: ontologies live in the
config service (type `ontology`) as JSON parsed by
`trustgraph-flow/trustgraph/extract/kg/ontology/ontology_loader.py`
(`metadata` / `classes` / `objectProperties` / `datatypeProperties`; ids are bare local
names; `rdfs:domain`/`rdfs:range` hold a SINGLE class id). The UI's Turtle import is a
client-side converter; there is no server-side Turtle ingestion API. Converter written for
this task: `benchmarks/trustgraph/owl_to_tg_ontology.py`
(`airkg_schema.ttl` → `airkg_ontology.json`), loaded via
`tg-put-config-item --type ontology --key airkg --stdin`.

**Round-trip (their API).** `tg-get-config-item` returned the stored ontology
**byte-identical**: 12 classes / 23 object properties / 33 datatype properties, matching the
generator's counts exactly. Their loader confirmed in the ingest container's logs:
`Loaded ontology airkg with 12 classes, 23 object properties, 33 datatype properties`,
no validation warnings. The config/store layer mangles nothing.

**What the FORMAT cannot express (lossy conversion, recorded not silent —
`benchmarks/trustgraph/airkg_ontology_losses.json`):**

| loss class | count | members |
|---|---|---|
| `owl:unionOf` domain dropped (their `rdfs:domain` is a single class id; policy: omit rather than mis-state) | 14 props (6 object, 8 datatype) | applies_to, builds_on, conflicts_with, extends, has_component, measures; as_of_date, description, grounding_span, name, owner, steward, text, year |
| `owl:unionOf` range dropped | 4 object props | builds_on, conflicts_with, extends, measures |
| `owl:SymmetricProperty` not representable | 1 | conflicts_with |
| `rdfs:seeAlso` external alignments not representable | 12 props | see losses file |

The v1 ontology doc's recorded limitation compounds here: OWL already loosened the schema's
strict index-pairing to unions; TrustGraph's format then drops even the union, leaving those
properties domain/range-free for extraction guidance. The count-based fidelity check
(12/23/33) is blind to all of this — counts survive perfectly while constraint semantics
thin out at each hop (schema.yaml → OWL → TG JSON).

## 2. Extraction runs

Flow `onto-bench` (blueprint `ontology`, the OntoRAG pipeline: NLTK segment → fastembed
similarity vs FAISS-embedded ontology elements, threshold 0.3 / top-k → ontology-subset
prompt `extract-with-ontologies` → prompt service → text-completion queue → **host
claude-cli backend**, concurrency 1). Chunker: recursive, 2000 chars / 50 overlap.
Documents ingested one at a time via `tg-add-library-document` (+ per-doc collection) and
`tg-start-library-processing -i onto-bench`. All text entered the librarian exactly as our
runner reads it: `.md` raw; the PDF via pypdf `extract_text` per page joined with `\n`
(`scripts/run_bulk_extraction.py::doc_text` parity; 12 pages → 69,692 chars).

### Per-document metrics (from the backend's per-call usage JSONL, `benchmarks/trustgraph/usage/`)

| doc | chunks | LLM calls | fresh in | cache read | cache creation | total input ctx | output | grand total | cache-read ratio | env. cost $ | model time | wall-clock |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| google-dataset-structured-data | 24 | 24 | 48 | 428,517 | 456,163 | 884,728 | 56,669 | 941,397 | 0.484 | 6.19 | 9.9 min | 15.1 min |
| w3c-dwbp-2017 | 104 | 103 | 206 | 1,847,305 | 1,990,253 | 3,837,764 | 311,846 | 4,149,610 | 0.481 | 28.62 | 52.3 min | 77.0 min |
| aggarwal-2024-geo-generative-engine-optimization | 36 | 35 | 70 | 625,802 | 680,183 | 1,306,055 | 110,078 | 1,416,133 | 0.479 | 9.87 | 17.9 min | 28.0 min |
| digital-gov-dap-guide | 4 | 4 | 8 | 71,740 | 73,689 | 145,437 | 3,331 | 148,768 | 0.493 | 0.86 | 0.7 min | 1.3 min |
| cloudflare-ai-crawl-control | 2 | 2 | 4 | 33,947 | 40,243 | 74,194 | 8,073 | 82,267 | 0.458 | 0.62 | 1.4 min | 1.8 min |
| **TOTAL** | **170** | **168** | **336** | **3,007,311** | **3,240,531** | **6,248,178** | **489,997** | **6,738,175** | **0.481** | **46.16** | **82.2 min** | **123.2 min** |

Wall-clock = library-processing submission → last extraction activity for that document.
Envelope cost is the CLI's nominal accounting (subscription OAuth — no API billing occurred).
Chunks with no ontology element above the similarity threshold make no LLM call (2 across
the run: 1 in w3c-dwbp-2017, 1 in aggarwal).

- `total input ctx` = fresh input + cache read + cache creation (all envelope-reported);
  `grand total` adds output tokens. Cache-read ratio = cache read / total input ctx.
- **Model substitution: zero** (gate armed on every call). **Retries: zero.**
- Extraction-quality counters across the run: 2 `JSONL parse error` warnings from the prompt
  service (malformed lines inside one response; per-line parsing kept the valid rows);
  2 chunks with no ontology match above threshold (skipped, no LLM call — hence 170 chunks /
  168 calls); **253 model-proposed triples dropped by their domain/range validator**
  (e.g. 43× `applies_to` with a `Construct` object where the schema range is `Concept`,
  18× `subtype_of` with a `Standard` subject where the domain is `Concept`). Spot-checked
  against `kg/schema.yaml`: the enforced constraints match the schema as converted — these
  are genuine over-proposals being gated by the ontology machinery, not conversion
  artifacts. This is exactly the constraint enforcement the benchmark exists to measure;
  the drop log (ingest container) is part of the evidence for Phase 3.

### Token gate decisions (binding rules applied)

- **Doc-1 gate:** 941,397 × 5 = 4,706,985 ≤ 5,000,000 → PASS, proceed (rule as
  pre-registered in the v2 task).
- **Ceiling tracking:** running projection recomputed before each document
  (actual chunk counts × observed avg tokens/call). Actuals: after doc 2 cumulative 5,091,007 (remaining docs projected +1.8M → proceed);
  after doc 3 cumulative 6,507,140 (docs 4–5 projected +0.25M → proceed). Final TG-side
  total **6,738,175** (+34,379 Phase-1 smoke test ≈ 6.77M), under the 7.4M stop line the
  coordinator set mid-run and leaving ≥1.2M headroom of the 8M both-sides ceiling for our
  extractor's ~0.6–1M.

## 3. Two multi-hour stalls (friction, orchestration-side — NOT TrustGraph's fault)

The pipeline itself never failed; both stalls were in THIS task's agent orchestration.

**Stall 1 (~6.2 h, 04:25→10:39 UTC).** Doc 2 ran 03:08:36→04:25:37 UTC and completed
cleanly (103rd call logged 04:25:37, stack idle after). Doc-completion waiting was
implemented as chained detached background `sleep` timers; their completion notifications
stopped being delivered after ~03:50 UTC, the agent loop received nothing until ~10:39,
and docs 3–5 sat unsubmitted.

**Stall 2 (~6.4 h, 11:16→17:38 UTC).** After recovery, doc 3 was driven with a streaming
Monitor (progress events every 2 min) which DID deliver reliably through doc 3's 28
minutes. Doc 4 was then submitted at 11:14:44 and finished at 11:16:03 (4 calls) — but
the doc-4 Monitor's QUIESCENT event was not delivered until 17:38 UTC, arriving batched
with the next coordinator message; doc 5 waited ~6.4 h.

Zero tokens burned during either stall; the cost was ~12.6 h wall-clock and operator
attention. Root cause both times: event *delivery* to the agent loop is not guaranteed
between turns — any waiting pattern that ends the agent's turn and relies on a wake-up
is fragile regardless of whether the waiter is a one-shot timer or a streaming monitor.
Doc 5 was run fully synchronously (foreground `wait_quiescent.sh` polling inside a single
tool call): submission→export in one pass, no stall. That is the pattern to standardize
for serial model-bound pipelines; reserve detached monitors for genuinely concurrent work
and never put the critical path behind them.

## 4. Export — files and format (for the normalizer)

One JSON per document: `benchmarks/trustgraph/extractions/<doc_id>.json`, written by
`benchmarks/trustgraph/export_tg_extraction.py`. Top-level fields:

| field | content |
|---|---|
| `document_id`, `collection`, `flow`, `exported_at` | identity; collection is `bench-<doc_id>` |
| `triple_count_api`, `quad_count_store`, `chunk_count` | counts |
| `triples_api` | what their REST triples query returned (see cap note below); terms in compact wire form `{"t":"i","i":uri}` / `{"t":"l","v":value,"dt"?,"ln"?}` / `{"t":"t","tr":{s,p,o}}`; triple rows `{s,p,o,g?}` (`g` absent = default graph) |
| `quads` | **authoritative, complete** dump of their Cassandra store (table `default.quads_by_collection` read through the driver inside their triples container). Row: `{g, s, p, o, otype, dtype, lang}`; `g` `""` = default graph, `"urn:graph:source"` = provenance; `otype` `"u"` uri / `"l"` literal / `"t"` RDF-star quoted triple, in which case `o` is a JSON string `{"s":{"type":"i","iri":...},"p":{...},"o":{...}}` |
| `chunks` | evidence: librarian child documents. `{chunk_id, text, metadata{id, kind, title, parent-id, document-type}}`; `text` is the exact chunk the extractor saw (verbatim source substrings — chunker slices, no rewriting) |

**Provenance chain inside `quads` (PROV-O, `g="urn:graph:source"`):**
document ←`prov:wasDerivedFrom`— chunk URI (`urn:chunk:<uuid>`, with
`tg:chunkIndex`/`tg:charOffset`/`tg:charLength`/`tg:chunkSize`/`tg:chunkOverlap`) ←`prov:wasDerivedFrom`—
subgraph URI (one per chunk-extraction, `prov:wasGeneratedBy` activity,
`prov:wasAssociatedWith` agent `kg-extract-ontology`) —`tg:contains`→ one RDF-star quoted
triple per extracted content triple. Content triples themselves live in the default graph
(`g=""`); entity URIs are minted as `https://trustgraph.ai/airkg/<normalized-name>`,
classes/properties expand to the `airkg:` namespace
(`https://brockwebb.github.io/ai-readiness-kg/schema#`). Ontology-definition triples
(classes/properties used per chunk) are ALSO emitted into the default graph — the
normalizer must separate them from content assertions (filter: subjects under the
`schema#` namespace are ontology elements, subjects under `trustgraph.ai/airkg/` are
extracted entities).

**API caps found while exporting (friction, TrustGraph defects at v2.8.15):**
1. Non-streaming REST triples query returns at most **5000 rows** (one Cassandra fetch
   page) regardless of `limit` — doc 2's true 12,596 quads came back as 5,000. Hence the
   store dump; `triples_api` is retained as the record of what their API serves.
2. Named-graph filtering is broken: the schema comment documents `g:"*"` = all graphs, but
   the query service returns `[]` for `"*"`, `[]` for `g:"urn:graph:source"` even with
   provenance rows present; only omitting `g` (=all graphs, rows self-tagged) works.
3. `list-children` exists on the librarian processor but is not registered in the gateway's
   operation registry → gateway rejects it ("unknown operation"); worked around with
   `list-documents` + `include-children: true`, filtering by `parent-id`.

## 5. Repro commands

```bash
V=/Users/brock/GitHub/trustgraph-fork/.venv/bin; U=http://localhost:8088/; T=$IAM_BOOTSTRAP_TOKEN
# ontology
$V/python benchmarks/trustgraph/owl_to_tg_ontology.py > benchmarks/trustgraph/airkg_ontology.json
$V/tg-put-config-item -u $U -t $T --type ontology --key airkg --stdin < benchmarks/trustgraph/airkg_ontology.json
$V/tg-start-flow -u $U -t $T -n ontology -i onto-bench -d "AIRKG benchmark"
# per document
$V/tg-set-collection -u $U --token $T bench-DOC; $V/tg-add-library-document -u $U -t $T -k text/plain --identifier DOC --name DOC FILE
$V/tg-start-library-processing -u $U -t $T -i onto-bench -d DOC --id proc-DOC --collection bench-DOC
$V/python benchmarks/trustgraph/export_tg_extraction.py --doc DOC --collection bench-DOC
```
