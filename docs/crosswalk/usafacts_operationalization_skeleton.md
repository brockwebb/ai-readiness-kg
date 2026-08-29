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

## 5b. Cross-cutting — the TEVV loop (the framework's structural gap; operator feedback already delivered to USAFacts)

Their ACCURATE criterion is open-loop: provide eval sets → test → notify developers. TEVV (NIST AI RMF MEASURE/MANAGE framing) closes it. Indicators added to the instrument, applying across criteria:

| # | Construct | Candidate indicator | Type | Evidence | Status |
|---|---|---|---|---|---|
| E1 | Verification vs validation split | Product spec conformance (AUTO/DOC set) reported separately from fit-for-use evals (EVAL set); a product cannot pass validation while failing verification | DOC | *this instrument's own A/B/D vs C split is the implementation* | draft |
| E2 | Acceptance thresholds | Published pass/fail thresholds per eval, pre-registered before results; threshold changes are versioned events | DOC | *methodology §3 pattern* | draft |
| E3 | Instrument versioning | Eval sets and rubrics carry versions; results never pooled across versions | DOC | *methodology §4; "version the instrument or history is noise"* | draft |
| E4 | Contamination policy | Public eval sets have a held-out rotation; publication schedule assumes training-set leakage within one model generation | DOC | *benchmark-contamination literature = candidate acquisition* | draft |
| E5 | Positive controls | Seeded known-bad items (canaries/decoys) in every continuous-eval cycle; a cycle with zero fired controls is INVALID, not passing | AUTO | *DD-019 decoy discipline — caught 3 real defects 2026-08-25* | draft |
| E6 | Failure attribution | Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model; each stage instrumented | EVAL | gap | draft |
| E7 | Corrective-action closure | Documented path from failed eval back into the data product (metadata fix, vintage pointer, dictionary entry) with re-test; mean-time-to-closure tracked | DOC | gap | draft |

Additional standards critique for the feedback letter: the guide recommends NIEM for cross-agency exchange and omits SDMX, DDI, and DCAT — the actual statistical-metadata standards; and "Crossaint" is Croissant (MLCommons).

## 5c. Cross-cutting — release engineering (CI/CD for data; operator feedback already delivered to USAFacts)

TEVV (§5b) evaluates the product as AI systems consume it; this layer gates the *release cycle* — the delivered feedback: publication is a deploy, and deploys get pre-release tests, regression suites, and feedback loops so a new vintage or page can't silently break consumers. Prior art: CI/CD and shift-left testing; data contracts; expectation-suite testing (Great Expectations/dbt-class); schema-registry compatibility checks; supply-chain attestation (SLSA/in-toto/SBOM — the likely software-security inspiration behind their guide, worth confirming with them).

| # | Construct | Candidate indicator | Type | Evidence | Status |
|---|---|---|---|---|---|
| F1 | Pre-release gates | New releases pass a published expectation suite (schema validity, row/total sanity, identifier persistence) before going live | DOC | *data-contract / expectation-suite literature = candidate acquisition* | draft |
| F2 | Contract stability | API/schema changes are versioned; breaking changes announced with deprecation windows; compatibility checked mechanically | AUTO/DOC | gap | draft |
| F3 | Regression on vintage transition | Time-series identifiers, geography codes, and endpoints survive a new vintage or a crosswalk is published; tested per release | AUTO | gap | draft |
| F4 | Change legibility | Machine-readable changelog per release (what changed, why, revision class); webhooks/push for high-frequency products | AUTO | *USAFacts guide (webhooks) — doc_id pending admission* | draft |
| F5 | Staged rollout | Canary/staging surface for major product changes; AI-consumer regression run before promotion | DOC | gap | draft |
| F6 | Release authenticity | Signed releases / provenance attestations so downstream copies are traceable to the authoritative artifact (SLSA-class, adapted) | AUTO | *supply-chain attestation specs = candidate acquisition* | `paid`-tier candidate |

## 5d. FSS-derived constructs — generalizable beyond the statistical system

Starting from the federal statistical system without overfitting to it: each of these is FSS-motivated but stated so any government data holds.

| # | Construct | Candidate indicator | Type | Evidence | Status |
|---|---|---|---|---|---|
| G1 | Uncertainty legibility | Error measures (MOEs, CVs, DP noise parameters) published as structured fields beside estimates — not footnotes; EVAL: do AI restatements carry the uncertainty? | DOC + EVAL | *fcsm-23-02 quality dimensions; DP documentation = candidate acquisition* | draft |
| G2 | Revision semantics | Revision status machine-readable per value (preliminary/revised/final/benchmark), with scheduled-revision dates; EVAL: vintage disambiguation (ties C3) | DOC + EVAL | gap | draft |
| G3 | Classification/vintage identity | Stable series IDs; machine-readable crosswalks when classifications or geographies change (industry codes, boundary revisions) | AUTO/DOC | gap | draft |
| G4 | Authority metadata | Issuing authority, statutory mandate, and statistical-vs-administrative provenance carried as structured metadata — the trust signal AI rankers need to prefer authoritative sources over aggregators | DOC | *statspolicy.gov / SPD-class docs = candidate acquisition* | draft |
| G5 | Disclosure semantics | Suppression and disclosure-avoidance documented machine-readably with unique identifiers (strengthens the guide's own bullet from prose to spec) | DOC | *USAFacts guide — doc_id pending admission* | draft |

G1 is the sharpest gap in every framework reviewed so far: uncertainty communication is the statistical system's core differentiator and no AI-readiness guidance addresses whether AI systems preserve it. Candidate flagship indicator for the January instrument.

## 6. Maturity overlay (org-level, optional second axis)

The product-level instrument above is the core. An organizational maturity overlay (staffing, governance, pipeline practices) maps to the corpus's `org_maturity` construct arm — *corpus: mitre-ai-maturity-model* — and stays out of scope for January unless the pilot agencies ask for it.

## 6b. Tiering and mode — instrument design decisions (2026-08-28)

1. **Tier vocabulary = the schema's existing `Measure.tier` enum** (`public` / `agency_instrumented` / `paid`, schema v0.3) — the instrument reuses it rather than inventing a parallel one:
   - `public`: runnable by anyone against the public surface, no permission, no cooperation. All AUTO indicators default here.
   - `agency_instrumented`: requires agency cooperation (internal metadata, process artifacts, DOC checklist items agencies must answer or expose).
   - `paid`: requires funded tooling/capability (attestation infrastructure, standing eval harnesses, monitoring). The instrument's output for this tier is prescriptive gap-closing guidance, not a score.
2. **Machine-first rule.** Where a `public` machine test exists or can be built, it replaces practitioner self-report. Rationale from survey methodology, not preference: organizational self-assessments inflate (social-desirability and self-report bias; maturity self-ratings are the canonical case) while observed measures don't argue back. The human-survey component is scoped to the residual — what no machine can see from outside and no artifact documents.
3. **Per-indicator tier assignment** is mechanical against these rules and happens at the v1 freeze pass (CC), not cell-by-cell now.
4. **Sequencing for January:** `public` tier ships first — it needs nobody's permission and produces scored profiles immediately; `agency_instrumented` piloted with willing partners; `paid` documented as roadmap with capability descriptions and rough cost classes.

## 7. Pilot plan (skeleton)

1. Freeze indicator set v1 after one review pass (operator + 1–2 FCSM-adjacent colleagues).
2. Select 3–5 statistical data products spanning dissemination styles (API-first, table-page, bulk-file legacy). Selection criteria, not names, are the design input here.
3. Run AUTO indicators mechanically; DOC indicators by checklist; C1/C2 with a small fixed question set per product through the existing probe/judge machinery.
4. Output per product: scored profile + gap list + the citation trail. The gap lists across products are the improvement agenda — and the empirical feedback to USAFacts on where their four criteria need decomposition their document doesn't yet have.

## 8. What this feeds back to USAFacts' design

1. **Decomposition with receipts** — four criteria → ~30 indicators, each carrying literature provenance through the KG rather than assertion.
2. **"Understandable" needs the FCSM extension** — machine-understandable (semantics, definitions, variable-level metadata), not just parseable; their current text under-specifies this.
3. **The accuracy evaluations they call for, instantiated** — a runnable harness (retrieval-grounded QA + entailment judging) rather than a principle.
4. **A measurable visibility layer** — GEO/llms.txt/Dataset-markup checks make "AI-optimization" auditable instead of vibes.
5. **ACCURATE becomes a closed TEVV loop (§5b)** — verification/validation split, pre-registered thresholds, versioned instruments, contamination policy, positive controls, failure attribution, corrective-action closure. This is the operator's delivered feedback, now with an indicator set and NIST AI RMF framing behind it.
6. **Statistical-standards correction** — SDMX/DDI/DCAT where the guide says NIEM.
7. **Publication is a deploy (§5c)** — the CI/CD feedback operationalized: pre-release gates, contract stability, vintage regression, staged rollout, signed releases.
8. **Uncertainty legibility (§5d G1)** — the statistical system's differentiator, absent from their guide and every adjacent framework: structured error measures plus an eval for whether AI systems preserve them.

## 9. Gaps registered by this skeleton (acquisition / adjudication queue)

- FCSM.25.03 AI-Ready extension paper; Commerce GenerativeAI-Open-Data guidance (Jan 2025); USAFacts AIReadinessForGovernment PDF (read 2026-08-28, admitted? — verify); USAFacts/Partnership Federal Data Excellence standards (2026); GEO paper (Aggarwal et al., KDD 2024); MLCommons Croissant spec (the guide's "Crossaint"); NIST AI RMF (MEASURE/MANAGE); SDMX / DDI / DCAT specs; benchmark-contamination literature — **verify against manifest before acquiring; some may already be admitted.**
- Every `gap` cell above is a demand-pull target: find the corpus document that grounds the indicator, or admit one, or mark the indicator as this instrument's original contribution (which is allowed — but labeled, never silently).

---

*Discipline note: this file is the proposal spine, not the evidence. Cells marked "corpus:" name documents believed admitted — CC verifies each against the manifest and replaces with doc_id + span at adjudication. Anything unverified stays marked draft.*
