# USAFacts AI-Ready Data Framework — Operationalization Crosswalk (Skeleton)

**Status:** v0.1 skeleton, 2026-08-28. Desktop-drafted; cells fill by demand-pull adjudication against the corpus (DD-024 discipline: every filled cell carries a doc_id + grounding span captured at adjudication).
**Deliverable target:** January — an assessment instrument federal statistical agencies can run against a data product, scored, with every indicator citable to primary literature through this KG.
**Frame:** USAFacts' four criteria (accessible, understandable, accurate, open) as the top-level structure; FCSM's quality framework as the bridge into statistical-agency language; GEO/machine-visibility literature as the measurable surface layer.

---

## 1. What "operationalize" means here

USAFacts names four criteria and argues for pairing LLMs with retrieval and holding results to accuracy evaluations. It does not give an agency a test. This instrument decomposes each criterion into:

- **Constructs** — the measurable dimensions underneath the criterion.
- **Indicators** — concrete checks, each typed:
  - `AUTO` — machine-checkable from the product's public surface (no human judgment)
  - `DOC` — verifiable documented attribute (human confirms presence/quality)
  - `EVAL` — measured by an evaluation harness (retrieval-grounded QA against the product)
- **Evidence** — corpus doc_ids grounding the indicator's claim to matter. Empty = registered gap, feeds acquisition (Lane 3) or demand-pull adjudication. **No cell is filled without a doc_id.**

Scoring rubric, weighting, and pilot-product selection are §6–§7 and deliberately not designed yet — indicators first, weights after the indicator set survives review.

---

## 2. Criterion A — ACCESSIBLE

*USAFacts anchor: machine-readable access matters most. FCSM bridge: Utility → accessibility, timeliness.*

| # | Construct | Candidate indicator | Type | Evidence (doc_id) | Status |
|---|---|---|---|---|---|
| A1 | Machine-readable formats | Product available as structured data (CSV/JSON/parquet), not PDF-only | AUTO | *corpus: Commerce GenAI-Open-Data guidance — confirm slug* | draft |
| A2 | Programmatic access | Documented public API; auth model; rate limits stated | AUTO/DOC | gap | draft |
| A3 | Bulk access | Full-product bulk download exists and is linked from product page | AUTO | gap | draft |
| A4 | Crawler/agent access | robots.txt + AI-crawler policy permit retrieval; no soft-blocks on data paths | AUTO | *corpus: machine-visibility kernel docs (v0.3 arm)* | draft |
| A5 | Discoverability surface | llms.txt (or equivalent) present; sitemap covers data products | AUTO | *corpus: llms.txt Standard node* | draft |
| A6 | Structured markup | schema.org/Dataset (or DCAT/Croissant) markup valid on product pages | AUTO | *corpus: Standard nodes — DCAT, schema.org; Croissant = candidate acquisition* | draft |
| A7 | Stable identifiers | Persistent URLs/DOIs for products and vintages | DOC | gap | draft |
| A8 | Timeliness of surface | Release date machine-readable; latest-vintage pointer resolvable | AUTO | gap | draft |

## 3. Criterion B — UNDERSTANDABLE (machine-understandable, per FCSM extension)

*FCSM bridge: Utility → relevance; the FCSM.25.03 argument: machine-readable → machine-understandable, no semantic loss.*

| # | Construct | Candidate indicator | Type | Evidence | Status |
|---|---|---|---|---|---|
| B1 | Variable-level semantics | Comprehensive variable-level metadata (labels, definitions, units, universes) | DOC | *corpus: Commerce guidance; FCSM.25.03 = candidate acquisition if not admitted* | draft |
| B2 | Definitions surface | Concept/term definitions published, versioned, linked from variables | DOC | *KG Definition layer is the reference implementation* | draft |
| B3 | Methodology legibility | Methodology docs in structured text (not PDF-only); summarizable by retrieval | AUTO/DOC | gap | draft |
| B4 | Quality metadata | Data-quality attributes (error measures, suppression rules, revisions policy) published as metadata, not prose | DOC | *corpus: fcsm-23-02-a-framework-for-data-quality-case-studies* | draft |
| B5 | Semantic consistency | Same concept ⇒ same identifier across products/vintages | DOC | gap | draft |
| B6 | NL affordances | Plain-language product summary present and current (the retrieval target) | DOC | gap | draft |

## 4. Criterion C — ACCURATE (as consumed by AI systems)

*USAFacts anchor: hold retrieval-paired systems to accuracy evaluations. FCSM bridge: Objectivity → accuracy, reliability. This is the EVAL-heavy criterion and the probe machinery's second life.*

| # | Construct | Candidate indicator | Type | Evidence | Status |
|---|---|---|---|---|---|
| C1 | Retrieval-grounded QA accuracy | Benchmark question set per product; answer accuracy of a retrieval-paired model vs published values | EVAL | *corpus: from-accuracy-to-readiness-metrics-and-benchmarks-for-human* | draft |
| C2 | Faithfulness of AI restatement | Entailment-judged: do model statements about the product entail from product text? (probe protocol, re-aimed) | EVAL | *methodology §4 — the instrument exists and is calibrated* | draft |
| C3 | Value-drift resistance | Version/vintage disambiguation: does retrieval return the vintage asked for? | EVAL | gap | draft |
| C4 | Citation quality | Generative engines citing the product cite the authoritative page (not aggregators) | EVAL/AUTO | *GEO literature (Aggarwal et al. 2024) = candidate acquisition* | draft |
| C5 | Readiness metrics baseline | Product scored against published AI-data-readiness metrics | DOC | *corpus: aidrin-hiniduma-2024; data-readiness-for-ai-a-360-degree-survey* | draft |

## 5. Criterion D — OPEN

*FCSM bridge: Integrity; OPEN Government Data Act baseline ("machine-readable, no semantic meaning lost").*

| # | Construct | Candidate indicator | Type | Evidence | Status |
|---|---|---|---|---|---|
| D1 | License clarity | Explicit machine-readable license/terms on product and API | AUTO | gap | draft |
| D2 | Reuse permissions for AI | Terms address model training/retrieval use explicitly | DOC | gap | draft |
| D3 | Provenance completeness | Source lineage published (collection → processing → product) | DOC | *corpus: PROV-aligned standards nodes* | draft |
| D4 | No dark data | Statutory products enumerable from a public inventory (data.gov/agency inventory current) | AUTO | gap | draft |

## 6. Maturity overlay (org-level, optional second axis)

The product-level instrument above is the core. An organizational maturity overlay (staffing, governance, pipeline practices) maps to the corpus's `org_maturity` construct arm — *corpus: mitre-ai-maturity-model* — and stays out of scope for January unless the pilot agencies ask for it.

## 7. Pilot plan (skeleton)

1. Freeze indicator set v1 after one review pass (operator + 1–2 FCSM-adjacent colleagues).
2. Select 3–5 statistical data products spanning dissemination styles (API-first, table-page, bulk-file legacy). Selection criteria, not names, are the design input here.
3. Run AUTO indicators mechanically; DOC indicators by checklist; C1/C2 with a small fixed question set per product through the existing probe/judge machinery.
4. Output per product: scored profile + gap list + the citation trail. The gap lists across products are the improvement agenda — and the empirical feedback to USAFacts on where their four criteria need decomposition their document doesn't yet have.

## 8. What this feeds back to USAFacts' design

1. **Decomposition with receipts** — four criteria → ~25 indicators, each carrying literature provenance through the KG rather than assertion.
2. **"Understandable" needs the FCSM extension** — machine-understandable (semantics, definitions, variable-level metadata), not just parseable; their current text under-specifies this.
3. **The accuracy evaluations they call for, instantiated** — a runnable harness (retrieval-grounded QA + entailment judging) rather than a principle.
4. **A measurable visibility layer** — GEO/llms.txt/Dataset-markup checks make "AI-optimization" auditable instead of vibes.

## 9. Gaps registered by this skeleton (acquisition / adjudication queue)

- FCSM.25.03 AI-Ready extension paper; Commerce GenerativeAI-Open-Data guidance (Jan 2025); USAFacts AIReadinessForGovernment PDF; USAFacts/Partnership Federal Data Excellence standards (2026); GEO paper (Aggarwal et al., KDD 2024); MLCommons Croissant spec — **verify against manifest before acquiring; some may already be admitted.**
- Every `gap` cell above is a demand-pull target: find the corpus document that grounds the indicator, or admit one, or mark the indicator as this instrument's original contribution (which is allowed — but labeled, never silently).

---

*Discipline note: this file is the proposal spine, not the evidence. Cells marked "corpus:" name documents believed admitted — CC verifies each against the manifest and replaces with doc_id + span at adjudication. Anything unverified stays marked draft.*
