# ai-readiness-kg — Extraction Schema v0.3

*(File path retained as `schema_v0.1.md` for reference stability; the authoritative version is `schema_version` in `kg/schema.yaml` and this changelog.)*

**Status:** Draft, unlocked. v0.2 promoted from the Fable pilot §9 audit (2026-07-03); v0.3 (2026-08-21) adds the machine-visibility kernel types, append-only.
**Pattern lineage:** forks fss-policy-kg (manifest ingestion, JSONL event sourcing, verbatim grounding, FastMCP verbs). Schema is new: claims-and-constructs, not obligations.

**Changelog (draft, unlocked):**
- 2026-08-24 (task `2026-08-24_source_triage`, Phase 0 → **v0.3.3**): append-only. Two Document properties. `construct_arm` (enum: `publication_actionability` / `training_data_readiness` / `org_maturity`) — which of the three survey construct arms the document primarily serves; carried on every `manifest_add` from that task onward, and backfilled for the pre-existing corpus by rule via `document_annotation` events (`events/batch-014.jsonl`, rule file `scripts/construct_arm_backfill.yaml`). `grounding_surface` (enum: `document` / `transcript` / `slides`, default `document`) — the surface class the document's grounding text comes from; slides and transcripts are admissible but flagged so their extraction quality gets its own stratum in any future TEVV run. Both `span_entailable: false` (harness/rule-set fields, never extracted). The same `grounding_surface` field also appears on candidate-register entries from the 2026-08-24 triage onward.
- 2026-07-03 (task `2026-07-03_extraction_module`, rider R1): added `intergovernmental` to Document `source_type` for policy bodies (OECD, UNESCO, UNDP, IADB, PARIS21, EU JRC, UN). Standards bodies / SDOs (ITU, ISO) stay `standard`.
- 2026-07-03 (task `2026-07-03_pilot_extraction_run`, precondition rider): schema.yaml edge types now carry explicit `pairs` (legal endpoint pairs); the parser enforces strict index-pairing. A whitelisted edge with an illegal endpoint pair routes to `proposed_relationships` (§9 expressiveness signal), not the graph.
- 2026-07-03 (task `2026-07-03_pilot_extraction_run_v4/v5`, §5 rider): §5 made model-agnostic — the whole-document protocol lives here; the extraction model is pinned in `kg/extraction/model_config.yaml` and stamped per item (§4), not named in the schema.
- 2026-07-03 (task `2026-07-03_schema_v02_promotion_rebaseline`, §9 pilot audit → **v0.2**): append-only edge additions — `uses_measure`, `measures` (extended to Concept endpoints), `has_component`, `subtype_of`, `precedes` — each with an `external_alignment` URI (schema.yaml). **No new node types:** `Organization` and `Project` were proposed in the pilot but REJECTED (document scope is a property, not a node forest; external ontologies are referenced via §8, never imported as node forests). Prompt template bumped to require character-exact grounding spans (v0.2.0), stamped in extraction events.
- 2026-08-22 (task `2026-08-22_faithfulness_probe`, Phase 0 → **v0.3.2**, DD-015/DD-016): append-only. Per-attribute `span_entailable` map on every node type (`kg/schema.yaml`): true for text/name/steward/owner/year/version/operator/license/url-class attributes, false for `as_of_date`, ids, enum classification fields and `grounding_span` itself; Document attributes all false (never extracted). New **non-graph event type `judge_label`** (shard `events/batch-009_probe_judge.jsonl`, `purpose: probe`, excluded from projection): `{item_id, event_id_judged, fact_id, label: entailed|not_entailed, class: doc_level_attribute|span_truncated|subject_dropped|filled_attribute|fabrication|grade_misassigned|null, confidence: 0..1|null, batch_id, batch_position, agent: {type: prov:SoftwareAgent|prov:Person, id, model_version|orcid, prompt_template_sha, call_id|null}, rated_at}` — one per (fact, rater); attribution per PROV-O (DD-016).
- 2026-08-22 (task `2026-08-22_kernel_tevv`, Phase 0 → **v0.3.1**, DD-014): append-only. `Document.is_platform_operator` (boolean, nullable): true when the issuing organization operates a search engine, crawler, CDN/bot-control product, or LLM retrieval system. Populated by rule through `document_annotation` events in `events/batch-007.jsonl` — a harness annotation, never an extractor output. Ground truth for the `platform_official` evidence-grade calibration gate (`dixie_evidence.yaml: tevv_gates`).
- 2026-08-21 (task `2026-08-21_v03_visibility_kernel`, Phase 1, AUTH-1 → **v0.3**, DD-009/DD-010): append-only. The machine-visibility / machine-actionability literature joins this graph (one graph, DD-009). **Node types added:** `Practice`, `Tool`, `Platform`. **Properties added:** `Claim.evidence_grade` (REQUIRED on every Claim extracted under v0.3; absent or outside the enum ⇒ quarantine — DD-010), `Measure.tier` (optional; enum-enforced when present), `Document.source_type` gains `practitioner`. **Edge types added:** `recommends`, `supported_by`, `implemented_by`, `consumes`, `applies_to`, `targets`, `supersedes` — each with `pairs`, `meaning`, and an `external_alignment` (PROV / DCTERMS / SOSA / schema.org) in `kg/schema.yaml`. Enum lists and the required-property rule live in `kg/schema.yaml` (`property_values`, `required_properties`) and are read by the parser, never duplicated in code. Prompt template bumped to v0.3.0 (describes the new types/edges, requires `evidence_grade`), stamped in extraction events as before. Nothing existing renamed or removed (`tests/test_schema_append_only.py` freezes the v0.2 catalogue as the reference).

---

## 1. Purpose

The graph is the validity layer under the FSS AI readiness survey and the definitions work. It must answer, with citations a stranger can verify:

1. What definitions of AI readiness / AI-ready data exist, from whom, dated, and where they conflict.
2. What constructs (readiness dimensions) the literature proposes, and which instruments have operationalized them.
3. The crosswalk: survey item to construct to definition to primary source.

## 2. Node types

| Type | What it is | Key properties |
|---|---|---|
| Document | A manifest entry. Primary source only. | doc_id, title, authors, pub_date, source_type (federal / academic / industry / standard / intergovernmental / practitioner — v0.3), primary_url, content_hash, manifest_event_id, is_platform_operator (boolean, nullable — v0.3.1, set by `document_annotation` events, DD-014), construct_arm (publication_actionability / training_data_readiness / org_maturity — v0.3.3, manifest-add field or `document_annotation` backfill), grounding_surface (document / transcript / slides — v0.3.3, default document) |
| Definition | A verbatim definition of a term as given by one source. | term, verbatim_text, grounding_span, normative_status (statute / policy / standard / academic / industry), as_of_date |
| Concept | Any substantive idea a document uses. Exhaustive layer, extracted first-class from event one. | name, aliases, description, grounding_span |
| Construct | A measurable readiness dimension (e.g. discoverability, provenance completeness). A Concept promoted to measurability. | name, description, measurement_notes |
| Instrument | An existing assessment, survey, index, or benchmark. | name, owner, year, method |
| Measure | An individual item or metric inside an Instrument. | text, response_type, grounding_span, tier (optional, v0.3: public / agency_instrumented / paid) |
| Claim | A falsifiable assertion a document makes (X improves Y, A requires B). | claim_text, grounding_span, claim_type (empirical / normative / speculative), evidence_grade (REQUIRED, v0.3: peer_reviewed_experiment / platform_official / measured_practitioner / practitioner_assertion / inference — descending strength, DD-010) |
| Standard | A technical spec (DCAT, ISO 19115, schema.org, llms.txt, MCP). | name, version, steward, as_of_date |
| Framework | A conceptual structure (NIST AI RMF, FAIR, Data Readiness Levels). | name, owner, year |
| Practice | A normative recommendation a source makes about how to publish, structure, expose, or maintain data or content for machine consumers. (v0.3) | text, grounding_span, as_of_date, scope (dataset / api / bulk_file / tool / content / advisory / site / any) |
| Tool | Software that implements one or more Measures (Lighthouse, Scrapy, pySHACL, LinkChecker, GoAccess, Spectral, extruct, GSA Site Scanning engine, DAP). (v0.3) | name, steward, license, url, as_of_date, grounding_span |
| Platform | A machine consumer whose behavior is targeted or described: Google Search, Bing, a named crawler, an LLM vendor's retrieval system, Cloudflare/Akamai bot controls. (v0.3) | name, operator, as_of_date, grounding_span |

Notes:
- Concept vs Construct: every Construct is a Concept, promoted only when someone has measured it or plausibly could. Promotion is an explicit event, not an extraction decision.
- Document scope is a property, not a partition. One graph, whole problem space.
- v0.3 property semantics: `Claim.evidence_grade` is the strength of the evidence behind the claim, in descending order — `peer_reviewed_experiment` (published, reviewed experiment), `platform_official` (the platform operator's own statement about its own behavior), `measured_practitioner` (disclosed method and data), `practitioner_assertion` (no method), `inference` (reasoned, not observed). Required on every Claim extracted under v0.3; a Claim without it is quarantined (DD-010). `Measure.tier` says who can run the measure — `public` (anyone, from outside), `agency_instrumented` (needs agency-side analytics, scripts, logs), `paid` (commercial product); optional, present when the source states or implies it. `Practice.scope` is the asset class the recommendation is about. `Tool` and `Platform` carry `grounding_span` because §4 applies to every extracted node; the task listed only their domain properties.

## 3. Edge types

| Edge | From → To | Meaning |
|---|---|---|
| defines | Document → Definition | Source gives this definition |
| mentions | Document → Concept | Concept appears substantively (not keyword match) |
| asserts | Document → Claim | Source makes this claim |
| about | Claim → Concept | What the claim concerns |
| operationalizes | Instrument → Construct | Instrument measures this dimension |
| measures | Measure → Construct; Measure → Concept; Instrument → Concept | Item/instrument mapping to the construct or concept it measures (v0.2 extended endpoints) |
| grounds | Construct → Definition | Construct's authority traces to this definition |
| extends | Definition → Definition, Framework → Framework | Builds on, adds to |
| conflicts_with | Definition ↔ Definition, Claim ↔ Claim | Incompatible. The "no shared definition" evidence layer |
| cites | Document → Document | Citation within the corpus |
| builds_on | Standard/Framework → Standard/Framework | e.g. FCSM 25-03 builds_on OPEN Gov Data Act |
| implements | Standard → Concept | Spec realizes a concept |
| uses_measure | Instrument → Measure | Instrument uses this measure/item (v0.2) |
| has_component | Framework → Concept; Concept → Concept | Part-whole component, **never** is-a (v0.2) |
| subtype_of | Concept → Concept | Is-a / subclass, **never** part-whole (v0.2) |
| precedes | Concept → Concept | Ordinal/temporal precedence (v0.2) |
| recommends | Document → Practice | Source makes this normative recommendation (v0.3) |
| supported_by | Practice → Claim | The practice rests on this claim; the claim's `evidence_grade` is the strength behind the recommendation (v0.3) |
| implemented_by | Measure → Tool | This software computes / runs the measure (v0.3) |
| consumes | Platform → Standard | Platform reads / honors this spec (v0.3) |
| applies_to | Practice → Concept; Measure → Concept | The asset class or concept the practice/measure targets; asset classes live as Concepts anchored via §8 to DCAT 3 / schema.org terms (Dataset, Distribution, DataService, DataCatalog, WebApplication, Report, DefinedTerm) (v0.3) |
| targets | Practice → Platform | Practice is aimed at this machine consumer (v0.3) |
| supersedes | Document → Document | Newer platform/guidance document replaces an earlier version. Distinct from the `extraction_superseded` overlay event, which is about extraction runs, not documents (v0.3) |

Cardinality is open everywhere. Constraint enforcement is type-validity only: an edge type not in this table cannot be written to the graph. Each v0.2 edge carries an `external_alignment` URI in `kg/schema.yaml` (SOSA / BFO / RDFS) — a reference anchor, not an imported ontology (§8). Each v0.3 edge likewise carries one (PROV `wasAttributedTo` / `wasDerivedFrom`, SOSA `madeBySensor`, DCTERMS `conformsTo` / `subject` / `replaces`, schema.org `audience`); where no reasonable anchor exists the key is written literally as `external_alignment: none`, never omitted.

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
