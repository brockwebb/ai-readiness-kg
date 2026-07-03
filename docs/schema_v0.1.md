# ai-readiness-kg — Extraction Schema v0.1

**Status:** Draft for review. Nothing extracts until this is locked and piloted.
**Pattern lineage:** forks fss-policy-kg (manifest ingestion, JSONL event sourcing, verbatim grounding, FastMCP verbs). Schema is new: claims-and-constructs, not obligations.

**Changelog (draft, unlocked):**
- 2026-07-03 (task `2026-07-03_extraction_module`, rider R1): added `intergovernmental` to Document `source_type` for policy bodies (OECD, UNESCO, UNDP, IADB, PARIS21, EU JRC, UN). Standards bodies / SDOs (ITU, ISO) stay `standard`.
- 2026-07-03 (task `2026-07-03_pilot_extraction_run`, precondition rider): schema.yaml edge types now carry explicit `pairs` (legal endpoint pairs); the parser enforces strict index-pairing. A whitelisted edge with an illegal endpoint pair routes to `proposed_relationships` (§9 expressiveness signal), not the graph.
- 2026-07-03 (task `2026-07-03_pilot_extraction_run_v4/v5`, §5 rider): §5 made model-agnostic — the whole-document protocol lives here; the extraction model is pinned in `kg/extraction/model_config.yaml` and stamped per item (§4), not named in the schema.

---

## 1. Purpose

The graph is the validity layer under the FSS AI readiness survey and the definitions work. It must answer, with citations a stranger can verify:

1. What definitions of AI readiness / AI-ready data exist, from whom, dated, and where they conflict.
2. What constructs (readiness dimensions) the literature proposes, and which instruments have operationalized them.
3. The crosswalk: survey item to construct to definition to primary source.

## 2. Node types

| Type | What it is | Key properties |
|---|---|---|
| Document | A manifest entry. Primary source only. | doc_id, title, authors, pub_date, source_type (federal / academic / industry / standard / intergovernmental), primary_url, content_hash, manifest_event_id |
| Definition | A verbatim definition of a term as given by one source. | term, verbatim_text, grounding_span, normative_status (statute / policy / standard / academic / industry), as_of_date |
| Concept | Any substantive idea a document uses. Exhaustive layer, extracted first-class from event one. | name, aliases, description, grounding_span |
| Construct | A measurable readiness dimension (e.g. discoverability, provenance completeness). A Concept promoted to measurability. | name, description, measurement_notes |
| Instrument | An existing assessment, survey, index, or benchmark. | name, owner, year, method |
| Measure | An individual item or metric inside an Instrument. | text, response_type, grounding_span |
| Claim | A falsifiable assertion a document makes (X improves Y, A requires B). | claim_text, grounding_span, claim_type (empirical / normative / speculative) |
| Standard | A technical spec (DCAT, ISO 19115, schema.org, llms.txt, MCP). | name, version, steward, as_of_date |
| Framework | A conceptual structure (NIST AI RMF, FAIR, Data Readiness Levels). | name, owner, year |

Notes:
- Concept vs Construct: every Construct is a Concept, promoted only when someone has measured it or plausibly could. Promotion is an explicit event, not an extraction decision.
- Document scope is a property, not a partition. One graph, whole problem space.

## 3. Edge types

| Edge | From → To | Meaning |
|---|---|---|
| defines | Document → Definition | Source gives this definition |
| mentions | Document → Concept | Concept appears substantively (not keyword match) |
| asserts | Document → Claim | Source makes this claim |
| about | Claim → Concept | What the claim concerns |
| operationalizes | Instrument → Construct | Instrument measures this dimension |
| measures | Measure → Construct | Item-level mapping |
| grounds | Construct → Definition | Construct's authority traces to this definition |
| extends | Definition → Definition, Framework → Framework | Builds on, adds to |
| conflicts_with | Definition ↔ Definition, Claim ↔ Claim | Incompatible. The "no shared definition" evidence layer |
| cites | Document → Document | Citation within the corpus |
| builds_on | Standard/Framework → Standard/Framework | e.g. FCSM 25-03 builds_on OPEN Gov Data Act |
| implements | Standard → Concept | Spec realizes a concept |

Cardinality is open everywhere. Constraint enforcement is type-validity only: an edge type not in this table cannot be written to the graph.

## 4. Universal provenance properties

Every node and edge extracted from a document carries:

- grounding_span: verbatim quote from the source
- location: section heading or page as available
- extraction_event_id, model_id, schema_version, timestamp

No grounding span, no write. Curated nodes (Construct promotions, the North Star definition artifact) carry a rationale and operator id instead.

## 5. Extraction protocol (whole-document, model-agnostic)

The protocol below is model-agnostic. The extraction model is **not** fixed in this schema — it
is pinned in `kg/extraction/model_config.yaml` and stamped on every extracted item per §4
(model_id read from the response envelope, not the model's text). A model change is a config
change plus a preflight identity check, never a schema change.

For documents under a size threshold (set at pilot; expect nearly all of this corpus):

1. Single call, full document in context.
2. Model first emits an extract plan: section map plus candidate concept inventory.
3. Then emits layers in order: Concepts (exhaustive), Definitions, Claims, Instruments/Measures, edges among them, cites.
4. Plus a proposed_relationships block: any relationship the schema cannot express, with the grounding span and a suggested edge name. Staged, never written directly.
5. Mechanical grounding validation: script string-matches every grounding_span against source text (whitespace/OCR-tolerant). Miss = item quarantined, not ingested.
6. Build metrics recorded per document: concepts per 1k tokens, definitions count, quarantine rate. The concept-density metric is the guard against a repeat of the 13% thin layer.

Large documents (books, long reports): out of scope for v0.1 protocol; handled case-by-case with a chunked plan when one appears.

## 6. Schema evolution

- schema.yaml is versioned; every event records schema_version.
- proposed_relationships reviewed by operator in batches. Accepted names bump the schema version.
- Docs extracted under an older schema version that plausibly contain the new edge are flagged for targeted re-run, not blanket re-extraction.

## 7. State machine

Document lifecycle: discovered (staging, from harvesters or manual) → manifest_added (event, with provenance + inclusion rationale) → extracted → validated (grounding pass clean) → ingested.

Nothing skips manifest_added. Harvester finds are inert until that event exists.

## 8. External anchoring (reference, don't ingest)

Constructs, Concepts, and Standards may carry external identifier properties (SKOS URI, DCAT term, NIST glossary ref). External ontologies are never imported as node forests.

## 9. Pilot gate

Before bulk extraction: run the protocol on 5 documents spanning source types (suggest: FCSM 25-03, MLMU-25 topic doc, Lawrence DRL, one industry readiness paper, one academic instrument paper). Audit:

- What couldn't the schema express? (proposed_relationships volume and content)
- Concept density sane?
- Quarantine rate?

Patch schema, bump version, then bulk. No bulk extraction on an unpiloted schema.

## 10. Deliverable mapping

- Literature review deliverable = report generated from the graph (Documents + Claims + Concepts, quarterly re-run of harvest → stage → manifest_add).
- Definitions repository deliverable = Definition layer export plus the curated North Star artifact.
- North Star actionability rule: every clause of the adopted definition must map to at least one Construct with at least one Measure or probe. Unoperationalizable clauses get cut.
