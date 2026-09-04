# USAFacts AI-Ready Data Framework — Operationalization Crosswalk (Skeleton)

**Status:** v0.2.7, 2026-09-03 — G1 becomes a two-leg indicator scored as a vector (G1-D declared / G1-O observed, no composite, no product-level threshold in v0.2.x) and the instrument is frozen at v2 for the January pilot; the G1 note carries the declared→observed dissociation and the Evidence cell the DD-036 reference, the admission groups and the three pilot RESULT files (task `cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md`). Prior: v0.2.6, 2026-09-03 — G1 Evidence cell adds DD-035 and the seventeen product surfaces admitted as served under epoch `g1sfc-2026-09-03`; the G1 note gains the `surface_type` vocabulary (task `cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression.md`). Prior: v0.2.5, 2026-09-03 — G1 Evidence cell adds DD-034 and the four suppression / reliability-flag producer sources admitted under epoch `g1srp-2026-09-03`; §9 suppression / reliability-flag gap closed (task `cc_tasks/2026-09-03_g1_eval_v1_parser_fullgrid_errata.md`). Prior: v0.2.4, 2026-09-02 — G1 row `draft` → `v0 harness` (DD-033; task `cc_tasks/2026-09-02_g1_eval_probe_family_v0.md`), §9 DP-documentation gap resolved by admission of the Census DAS handbook, §9 gains the suppression/reliability-flag fixture-source gap. Prior: v0.2, 2026-08-29. Evidence cells resolved against the manifest, tiers assigned, references added (task `cc_tasks/2026-08-29_crosswalk_operationalization.md`, §1–§3). Cells fill by demand-pull adjudication against the corpus (DD-024 discipline: every filled cell carries a doc_id + grounding span captured at adjudication). v0.2.1 2026-09-01: Machine Diagnostic stub (A10, A11, §6b.5, G1 note, two §9 gaps) — task `cc_tasks/2026-09-01_machine_diagnostic_stub.md`. v0.2.2 2026-09-01: assessment layer consolidated from ai-readiness-fss (`assessment/`, `docs/crosswalk/assessment_protocol.md`) — task `cc_tasks/2026-09-01_assessment_consolidation.md`. v0.2.3 2026-09-02: housekeeping — A9 moved from §1b into the §2 table, frontier dating added to its Status cell — task `cc_tasks/2026-09-02_housekeeping.md`.

**What v0.2 changed.** Every `*corpus: ...*` prose pointer is now either a **`doc_id`** that exists in `corpus/manifest.json` or an explicit **gap**. 45 indicators: **25 resolved to at least one admitted doc_id, 20 are gaps.** A gap is a demand-pull target, not a to-do that was skipped — no gap cell was filled with a new claim to make the table look complete. Every indicator now carries a **Tier** (`public` / `agency_instrumented` / `paid`, the schema's `Measure.tier` enum per §6b.1), assigned mechanically by the §6b rules; the rule applied to each is logged in the task RESULT. Nothing was extracted: these documents are admitted to the corpus but not yet extracted into the graph, which waits on the v0.3.7 contract (DD-023).
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

## 1b. Design stance — the machine is the first-class user (operator feedback delivered to USAFacts)

The instrument's normative stance, stated once so every indicator inherits it: design the data product for machine consumption first; the human surface is *derived from* the machine surface, not the other way around. This is the FAIR principles' original thesis (Wilkinson et al. 2016 — machine-actionability as primary design target), a decade old and unimplemented in most of government; the 2026 instantiation is M2M protocol surfaces (MCP/A2A endpoints, llms.txt, API-first) with generative UI closing the human last mile. Existence proof in production: fss-policy-kg — a federal policy corpus whose primary interface is an MCP server. Boundary: Section 508 keeps the human surface mandatory; the stance is derivation order, not GUI abolition.

The indicator this stance adds, A9 (M2M agent surface), sits in the §2 Criterion A table between A8 and A10.

## 2. Criterion A — ACCESSIBLE

*USAFacts anchor: machine-readable access matters most. FCSM bridge: Utility → accessibility, timeliness.*

| # | Construct | Candidate indicator | Type | Evidence (doc_id) | Tier | Status |
|---|---|---|---|---|---|---|
| A1 | Machine-readable formats | Product available as structured data (CSV/JSON/parquet), not PDF-only | AUTO | **gap** — named source (Commerce GenAI-Open-Data guidance) is `acquisition_blocked`, batch-017 | `public` | draft |
| A2 | Programmatic access | Documented public API; auth model; rate limits stated | AUTO/DOC | **gap** | `public` | draft |
| A3 | Bulk access | Full-product bulk download exists and is linked from product page | AUTO | **gap** | `public` | draft |
| A4 | Crawler/agent access | robots.txt + AI-crawler policy permit retrieval; no soft-blocks on data paths | AUTO | `rfc-9309-robots-exclusion-protocol`; `google-robots-txt-intro`; `openai-crawlers-bots`; `anthropic-crawler-support-article`; `perplexity-crawlers`; `cloudflare-ai-crawl-control-manage-crawlers` | `public` | draft |
| A5 | Discoverability surface | llms.txt (or equivalent) present; sitemap covers data products | AUTO | `llmstxt-proposal`; `sitemaps-protocol` | `public` | draft |
| A6 | Structured markup | schema.org/Dataset (or DCAT/Croissant) markup valid on product pages | AUTO | `schema-org-dataset`; `w3c-dcat-3`; `mlcommons-croissant-spec`; `croissant-akhtar-2024-paper` | `public` | draft |
| A7 | Stable identifiers | Persistent URLs/DOIs for products and vintages | DOC | **gap** | `agency_instrumented` | draft |
| A8 | Timeliness of surface | Release date machine-readable; latest-vintage pointer resolvable | AUTO | **gap** | `public` | draft |
| A9 | M2M agent surface | Product exposes a machine-first entry point (documented API plus MCP/A2A-class endpoint or equivalent agent protocol); human pages derivable from it | AUTO | `wilkinson-2016-fair-guiding-principles`; internal existence proof: fss-policy-kg (MCP server) | `public` | draft; frontier_deep track, as_of 2026-01 |
| A10 | Application/data-tool machine surface | Interactive data tools expose stable, directly-requestable deep links; meaningful states are not fragment-only or session-dependent; invalid routes return true 404/410, not HTTP-200 shell (soft-404); page-specific content present in raw HTML before JS execution | AUTO | internal draft: FSS Machine Diagnostic spec (SEO SME, 2026-09, operator-held; admission gated) | `public` | stub |
| A11 | Effective crawler access (declared / enforced / observed) | A4 upgraded from declared-policy check to three-layer comparison: declared (robots.txt/meta directives) vs enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs). A mismatch between layers is itself the finding, not an error state | AUTO + agency_instrumented | `cloudflare-ai-crawl-control-manage-crawlers`; `rfc-9309-robots-exclusion-protocol`; internal draft: FSS Machine Diagnostic spec (as above) | `agency_instrumented` (observed leg requires edge logs; declared leg stays `public`) | stub |

## 3. Criterion B — UNDERSTANDABLE (machine-understandable, per FCSM extension)

*FCSM bridge: Utility → relevance; the FCSM.25.03 argument: machine-readable → machine-understandable, no semantic loss.*

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| B1 | Variable-level semantics | Comprehensive variable-level metadata (labels, definitions, units, universes) | DOC | `fcsm-25-03` | `agency_instrumented` | draft |
| B2 | Definitions surface | Concept/term definitions published, versioned, linked from variables | DOC | `schema-org-definedterm`; `w3c-dcat-3`; internal: this KG's Definition layer | `agency_instrumented` | draft |
| B3 | Methodology legibility | Methodology docs in structured text (not PDF-only); summarizable by retrieval | AUTO/DOC | **gap** | `public` | draft |
| B4 | Quality metadata | Data-quality attributes (error measures, suppression rules, revisions policy) published as metadata, not prose | DOC | `fcsm-23-02-a-framework-for-data-quality-case-studies`; `fcsm-20-04-a-framework-for-data-quality` | `agency_instrumented` | draft |
| B5 | Semantic consistency | Same concept ⇒ same identifier across products/vintages | DOC | **gap** | `agency_instrumented` | draft |
| B6 | NL affordances | Plain-language product summary present and current (the retrieval target) | DOC | **gap** | `agency_instrumented` | draft |

## 4. Criterion C — ACCURATE (as consumed by AI systems)

*USAFacts anchor: hold retrieval-paired systems to accuracy evaluations. FCSM bridge: Objectivity → accuracy, reliability. This is the EVAL-heavy criterion and the probe machinery's second life.*

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| C1 | Retrieval-grounded QA accuracy | Benchmark question set per product; answer accuracy of a retrieval-paired model vs published values | EVAL | `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` | `paid` | draft |
| C2 | Faithfulness of AI restatement | Entailment-judged: do model statements about the product entail from product text? (probe protocol, re-aimed) | EVAL | internal: probe protocol, `2026-08-27_chunked_vs_wholedoc_verdict.md` | `paid` | draft |
| C3 | Value-drift resistance | Version/vintage disambiguation: does retrieval return the vintage asked for? | EVAL | **gap** | `paid` | draft |
| C4 | Citation quality | Generative engines citing the product cite the authoritative page (not aggregators) | EVAL/AUTO | `aggarwal-2024-geo-generative-engine-optimization`; `chen-2025-geo-how-to-dominate-ai-search` | `public` | draft |
| C5 | Readiness metrics baseline | Product scored against published AI-data-readiness metrics | DOC | `aidrin-hiniduma-2024`; `data-readiness-for-ai-a-360-degree-survey`; `aidrin-2-0-a-framework-to-assess-data-readiness-for-ai` | `agency_instrumented` | draft |

## 5. Criterion D — OPEN

*FCSM bridge: Integrity; OPEN Government Data Act baseline ("machine-readable, no semantic meaning lost").*

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| D1 | License clarity | Explicit machine-readable license/terms on product and API | AUTO | **gap** | `public` | draft |
| D2 | Reuse permissions for AI | Terms address model training/retrieval use explicitly | DOC | **gap** | `agency_instrumented` | draft |
| D3 | Provenance completeness | Source lineage published (collection → processing → product) | DOC | **gap** — no PROV-O/W3C-PROV document is admitted; the skeleton's "PROV-aligned standards nodes" did not resolve | `agency_instrumented` | draft |
| D4 | No dark data | Statutory products enumerable from a public inventory (data.gov/agency inventory current) | AUTO | **gap** | `public` | draft |

## 5b. Cross-cutting — the TEVV loop (the framework's structural gap; operator feedback already delivered to USAFacts)

Their ACCURATE criterion has real machinery — internal review, audit trails, developer notification — but the loop does not close: nothing routes a failed evaluation back into the data product, and nothing attributes a failure to its stage. TEVV (NIST AI RMF MEASURE/MANAGE framing) supplies the missing half. Indicators added to the instrument, applying across criteria:

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| E1 | Verification vs validation split | Product spec conformance (AUTO/DOC set) reported separately from fit-for-use evals (EVAL set); a product cannot pass validation while failing verification | DOC | `nist-ai-risk-management-framework-ai-rmf`; internal: this instrument's A/B/D vs C split | `agency_instrumented` | draft |
| E2 | Acceptance thresholds | Published pass/fail thresholds per eval, pre-registered before results; threshold changes are versioned events | DOC | internal: methodology §3; `nist-ai-rmf-playbook` | `agency_instrumented` | draft |
| E3 | Instrument versioning | Eval sets and rubrics carry versions; results never pooled across versions | DOC | internal: methodology §4 and §7.6 (instrument-version citation rule) | `agency_instrumented` | draft |
| E4 | Contamination policy | Public eval sets have a held-out rotation; publication schedule assumes training-set leakage within one model generation | DOC | `sainz-2023-llm-data-contamination` | `agency_instrumented` | draft |
| E5 | Positive controls | Seeded known-bad items (canaries/decoys) in every continuous-eval cycle; a cycle with zero fired controls is INVALID, not passing | AUTO | internal: DD-019 decoy discipline; methodology §7.5 | `public` | draft |
| E6 | Failure attribution | Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model; each stage instrumented | EVAL | **gap** | `paid` | draft |
| E7 | Corrective-action closure | Documented path from failed eval back into the data product (metadata fix, vintage pointer, dictionary entry) with re-test; mean-time-to-closure tracked | DOC | **gap** | `agency_instrumented` | draft |
| E8 | Drift sentinels (golden questions) | Versioned golden question/answer sets re-run on schedule against the product surface; baseline deltas alarmed; state fidelity across product versions measured, not assumed | AUTO/EVAL | `webb-2026-state-fidelity-validity` | `paid` | draft |
| E9 | Adversarial evaluation (red team) | Standing adversarial bank: vintage traps, confusable series, unit traps, DP-noise misreads, suppression probes; plus surface red team — misparse and injection resistance of pages/markup/llms.txt. Reported as break modes, not just pass rates | EVAL | `nist-generative-ai-profile-ai-600-1`; `nist-ai-risk-management-framework-ai-rmf` | `paid` | draft |

Additional standards critique for the feedback letter: the guide recommends NIEM for cross-agency exchange and omits SDMX, DDI, and DCAT — the actual statistical-metadata standards; and "Crossaint" is Croissant (MLCommons).

## 5c. Cross-cutting — release engineering (CI/CD for data; operator feedback already delivered to USAFacts)

TEVV (§5b) evaluates the product as AI systems consume it; this layer gates the *release cycle* — the delivered feedback: publication is a deploy, and deploys get pre-release tests, regression suites, and feedback loops so a new vintage or page can't silently break consumers. Prior art: CI/CD and shift-left testing; data contracts; expectation-suite testing (Great Expectations/dbt-class); schema-registry compatibility checks; supply-chain attestation (SLSA/in-toto/SBOM — the likely software-security inspiration behind their guide, worth confirming with them).

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| F1 | Pre-release gates | New releases pass a published expectation suite (schema validity, row/total sanity, identifier persistence) before going live | DOC | `odcs-open-data-contract-standard` | `agency_instrumented` | draft |
| F2 | Contract stability | API/schema changes are versioned; breaking changes announced with deprecation windows; compatibility checked mechanically | AUTO/DOC | `odcs-open-data-contract-standard` | `public` | draft |
| F3 | Regression on vintage transition | Time-series identifiers, geography codes, and endpoints survive a new vintage or a crosswalk is published; tested per release | AUTO | **gap** | `public` | draft |
| F4 | Change legibility | Machine-readable changelog per release (what changed, why, revision class); webhooks/push for high-frequency products | AUTO | `usafacts-ai-ready-data-guide` | `public` | draft |
| F5 | Staged rollout | Canary/staging surface for major product changes; AI-consumer regression run before promotion | DOC | **gap** | `agency_instrumented` | draft |
| F6 | Release authenticity | Signed releases / provenance attestations so downstream copies are traceable to the authoritative artifact (SLSA-class, adapted) | AUTO | `slsa-specification-v1-0` | `paid` | `paid`-tier candidate |

## 5d. FSS-derived constructs — generalizable beyond the statistical system

Starting from the federal statistical system without overfitting to it: each of these is FSS-motivated but stated so any government data holds.

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| G1 | Uncertainty legibility (two legs, scored as a vector) | **G1-D (declared)** — error measures (MOEs, CVs, DP noise parameters) present as structured fields beside the estimates on the product surface, not as footnotes (`assessment/harness/probes/g1_declared.py`); unchanged. **G1-O (observed)** — the family preservation rate (the L3+ share of scored qualifier families, D9) when the pinned consumer restates that same captured surface at indirect compression `none`, reported per surface with the `unparseable` share and the `short` / `tight` rates beside it, every record stamped with consumer, prompt epoch, `parser_version` and `scorer_version` (`g1_preservation.py`). The two legs are reported as a vector and are never composited (protocol §3). **No product-level PASS/PARTIAL/FAIL in v0.2.x:** the rate and its Wilson interval are the score until the January calibration run sets a boundary. Compression is a reported condition, not a scored one, until intended use says which condition the consumer of the assessment cares about | G1-D: AUTO · G1-O: EVAL | `fcsm-23-02-a-framework-for-data-quality-case-studies`; DD-033 (v0 harness: `assessment/harness/probes/g1_declared.py`, `g1_preservation.py`); prior art (memo 2026-09-02): `du-2026-possible-or-definite`, `peters-2025-generalization-bias-llm-summarization`, `lee-2026-when-summaries-distort-decisions`, `zhao-2020-reducing-quantity-hallucinations`, `cao-2024-multimodal-long-form-summarization-financial-reports`, `zhou-2026-loomsum-table-grounded-faithfulness`, `venktesh-2024-quantemp-numerical-claims`, `min-2023-factscore`, `van-der-bles-2019-communicating-uncertainty`, `manski-2015-communicating-uncertainty-official-economic-statistics`, `mazzi-2021-measuring-communicating-uncertainty-official-economic-statistics`, `census-acs-general-handbook-2020`, `ons-uncertainty-and-how-we-measure-it`, `statcan-quality-guidelines-6th-edition`, `ebu-bbc-2025-news-integrity-ai-assistants`, `radhakrishnan-2024-knowing-when-to-ask-data-commons`, `suleymanli-2025-llms-charts-official-statistics`; DP: `census-2020-disclosure-avoidance-handbook-2021`; DD-034 (parser v1, sealed-holdout readiness); suppression / reliability-flag rules: `nchs-2017-data-presentation-standards-proportions`, `nchs-2023-data-presentation-standards-rates-counts`, `statcan-71-543-g-guide-labour-force-survey-2025`, `census-acs-data-suppression-rules`; DD-035 (v2: product surfaces × compression, families, binding, control arm); DD-036 (instrument frozen at v2 for the January pilot; two-leg G1; reviewer-calibration protocol); product surfaces (epoch `g1sfc-2026-09-03`, captured as served): `census-api-acs5-2023-b19013-counties-colorado`, `census-api-acs5-2023-b19013-counties-idaho`, `statcan-14-10-0287-01-lfs-2026-07-provinces-estimate-se-csv`, `statcan-14-10-0287-01-lfs-2025-12-provinces-estimate-se-csv`, `statcan-14-10-0287-01-cube-metadata-csv`, `statcan-13-10-0096-01-cchs-2022-provinces-percent-ci-csv`, `statcan-13-10-0096-01-cube-metadata-csv`, `statcan-13-10-0113-01-cchs-2021-2022-quebec-health-regions-percent-ci-csv`, `statcan-13-10-0113-01-cube-metadata-csv`, `nchs-data-brief-530-perinatal-mortality-2022-2023`, `nchs-data-brief-500-dental-visits-adults-65-2022`, `nchs-data-brief-515-high-total-cholesterol-2021-2023`, `bls-employment-situation-2026-08-news-release`, `bls-employment-situation-2026-05-news-release-archive`, `census-quickfacts-denver-county-colorado`, `census-quickfacts-denver-county-colorado-csv`, `census-api-dec2020-dhc-p1-counties-colorado`; admissions behind the fixtures, by epoch: 17 prior-art sources (`g1eval-2026-09-02`, the memo), 4 suppression / reliability-flag producer rules (`g1srp-2026-09-03`), 17 product surfaces (`g1sfc-2026-09-03`, listed above); pilot execution records: `cc_tasks/2026-09-02_g1_eval_probe_family_v0_RESULT.md`, `cc_tasks/2026-09-03_g1_eval_v1_parser_fullgrid_errata_RESULT.md`, `cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression_RESULT.md` | G1-D `public` · G1-O `paid` | v2 harness, frozen for the pilot (DD-036) |
| G2 | Revision semantics | Revision status machine-readable per value (preliminary/revised/final/benchmark), with scheduled-revision dates; EVAL: vintage disambiguation (ties C3) | DOC + EVAL | **gap** | `agency_instrumented` | draft |
| G3 | Classification/vintage identity | Stable series IDs; machine-readable crosswalks when classifications or geographies change (industry codes, boundary revisions) | AUTO/DOC | **gap** | `public` | draft |
| G4 | Authority metadata | Issuing authority, statutory mandate, and statistical-vs-administrative provenance carried as structured metadata — the trust signal AI rankers need to prefer authoritative sources over aggregators | DOC | `statistical-policy-working-paper-46-data-quality-assessment`; `fcsm-19-01-transparent-reporting-for-integrated-data-quality` | `agency_instrumented` | draft |
| G5 | Disclosure semantics | Suppression and disclosure-avoidance documented machine-readably with unique identifiers (strengthens the guide's own bullet from prose to spec) | DOC | `usafacts-ai-ready-data-guide` | `agency_instrumented` | draft |
| G6 | Measurement-protocol provenance | Collection instrument/protocol carried as a versioned epoch on the series; changes annotated machine-readably with reason and inter-epoch crosswalk (SDMX break-in-series class metadata). The consumer-side test: an AI system asked to compare values across a break must surface the break | DOC + EVAL | `sdmx-3-0-section-1-framework`; `sdmx-standards-overview`; `odcs-open-data-contract-standard` | `agency_instrumented` | draft |

G1 is the sharpest gap in every framework reviewed so far: where uncertainty appears at all it is framed as a privacy safeguard, and no AI-readiness guidance asks whether AI systems *preserve* uncertainty when restating values — the statistical system's core differentiator. Candidate flagship indicator for the January instrument. The declared/enforced/observed triad (A11) is the candidate measurement template for G1: declared uncertainty (structured MOE/CV fields) vs surfaced uncertainty (what retrieval delivers) vs observed preservation (what AI restatements carry). **Surface types (DD-035, the closed `surface_type` vocabulary of `assessment/harness/g1_fixtures.py`):** `table_coded` (estimate and uncertainty as coded fields with no label on the surface — a Census Data API row), `table_labeled` (columns or rows whose headers name them — a StatCan CSV slice), `footnoted` (the estimate in body text, its MOE/CI in a footnote, appendix table or technical note elsewhere on the surface — an NCHS Data Brief, a BLS release), `flagged_cell` (cells carrying a reliability or suppression marker with its legend — StatCan `E`/`F`, NCHS `†`), `no_declared` (an estimate with no uncertainty at all — QuickFacts, 2020 DHC counts; declared leg only), `prose_labeled` (the v1 handbook passages, the control stratum). v2 measures observed preservation per surface type × compression budget with the declared-leg score joined on the surface file. **The two legs dissociate, and that is the finding the indicator now carries:** on the pooled pinned-consumer grid the coded API tables the declared probe scores PASS are the surface the observed leg loses most on, while the handbook prose the declared probe does not reward holds up (`g1_v2_pooled_opus_table_coded_none_preservation_rate` / `…_short_…` / `…_tight_…` against `g1_v2_pooled_opus_prose_labeled_none_preservation_rate` / `…_short_…` / `…_tight_…`; H3 supported, `assessment/results/g1_v2_pooled_opus_reviewed.json` `expectations_v2.H3`; the per-surface join is §6.5 of the v2 RESULT, computed from `assessment/tests/fixtures/g1/v2/declared_leg.json`). Structured fields are necessary for G1-D and are not sufficient for G1-O. The instrument is frozen at (`g1-parse-v2`, `g1-score-v2`, prompt epoch `g1-v2-2026-09-03`, consumer `claude-opus-5`) for the January pilot (DD-036); the v3 parser items are a registered backlog (ResearchTask `73f0aa5d`), and the reviewer's genuine-loss counts are an LLM judge whose agreement with the operator is issued as a blind sheet and not yet measured (`assessment/results/g1_calibration_sheet_2026-09-03.md`, ResearchTask `85851bcd`).

## 6. Maturity overlay (org-level, optional second axis)

The assessment protocol for everything above is `docs/crosswalk/assessment_protocol.md`: unit of analysis, scoring model, the core/frontier firewall with as_of dating, enumeration and scope, the three evidence streams, and the reference implementation at `assessment/harness/`. It is the merged live design, reconciling the June 2026 ai-readiness-fss work (imported verbatim under `assessment/` as record) with the product-level instrument here. Where the two differ, the protocol governs.

The product-level instrument above is the core. An organizational maturity overlay (staffing, governance, pipeline practices) maps to the corpus's `org_maturity` construct arm — *corpus: mitre-ai-maturity-model* — and stays out of scope for January unless the pilot agencies ask for it.

## 6b. Tiering and mode — instrument design decisions (2026-08-28)

1. **Tier vocabulary = the schema's existing `Measure.tier` enum** (`public` / `agency_instrumented` / `paid`, schema v0.3) — the instrument reuses it rather than inventing a parallel one:
   - `public`: runnable by anyone against the public surface, no permission, no cooperation. All AUTO indicators default here.
   - `agency_instrumented`: requires agency cooperation (internal metadata, process artifacts, DOC checklist items agencies must answer or expose).
   - `paid`: requires funded tooling/capability (attestation infrastructure, standing eval harnesses, monitoring). The instrument's output for this tier is prescriptive gap-closing guidance, not a score.
2. **Machine-first rule.** Where a `public` machine test exists or can be built, it replaces practitioner self-report. Rationale from survey methodology, not preference: organizational self-assessments inflate (social-desirability and self-report bias; maturity self-ratings are the canonical case) while observed measures don't argue back. The human-survey component is scoped to the residual — what no machine can see from outside and no artifact documents.
3. **Per-indicator tier assignment** is mechanical against these rules and happens at the v1 freeze pass (CC), not cell-by-cell now.
4. **Sequencing for January:** `public` tier ships first — it needs nobody's permission and produces scored profiles immediately; `agency_instrumented` piloted with willing partners; `paid` documented as roadmap with capability descriptions and rough cost classes.
5. **Observed facts vs versioned warning rules (adopted from the Machine Diagnostic spec, 2026-09-01).** The instrument stores raw observed facts separately from calculated warnings; warnings are produced by deterministic, versioned rules so thresholds can change and history can be re-scored without re-measurement. This is the measurement-side counterpart of E2 (pre-registered thresholds) and E3 (instrument versioning), and applies to all AUTO indicators when the scoring harness is built.

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
8. **Uncertainty legibility (§5d G1)** — in their guide, error and noise appear only as privacy safeguards (DP, suppression); no framework treats uncertainty as something the AI consumer must *preserve*. G1 supplies that: structured error measures plus an eval for whether AI restatements keep them.
9. **Machine as first-class user (§1b)** — delivered feedback, grounded in FAIR rather than prediction: machine-actionability as primary design target, human surface derived; A9 makes it auditable.
10. **Protocol as contract (§5d G6)** — delivered feedback: measurement-protocol epochs with machine-readable breaks and reasons; SDMX + ODCS give it standards footing.
11. **Red teaming (§5b E9)** — delivered feedback: the framework tests what works; it must also enumerate how products break, with a standing adversarial bank.

## 9. Gaps registered by this skeleton (acquisition / adjudication queue)

- FCSM.25.03 AI-Ready extension paper; Commerce GenerativeAI-Open-Data guidance (Jan 2025); USAFacts AIReadinessForGovernment PDF (read 2026-08-28, admitted? — verify); USAFacts/Partnership Federal Data Excellence standards (2026); GEO paper (Aggarwal et al., KDD 2024); MLCommons Croissant spec (the guide's "Crossaint"); NIST AI RMF (MEASURE/MANAGE) + GenAI profile; SDMX / DDI / DCAT specs; benchmark-contamination literature; FAIR principles (Wilkinson et al. 2016); Open Data Contract Standard (ODCS); SFV paper (operator's own, doi:10.5281/zenodo.22111334) — **verify against manifest before acquiring; some may already be admitted.**
- Tool evaluations (queue, not adoptions): Databricks DQX (quality rules in-pipeline, quarantine patterns, MCP-exposed tools, ODCS rule generation — the likely "Databricks QA tool" from the USAFacts meeting); Databricks Data Quality Monitoring (freshness/completeness anomaly detection). Evaluate as reference implementations for E-layer and F1 indicators, and as evidence that the E/F indicator classes are commercially instantiable.
- Every `gap` cell above is a demand-pull target: find the corpus document that grounds the indicator, or admit one, or mark the indicator as this instrument's original contribution (which is allowed — but labeled, never silently).
- **DP documentation gap (G1) — closed 2026-09-02:** `census-2020-disclosure-avoidance-handbook-2021` (Census Bureau, *Disclosure Avoidance for the 2020 Census: An Introduction*, Nov 2021) admitted through the standing path (batch-026, epoch `g1dp-2026-09-02`) as the G1 DP_NOISE fixture source: publishes rho / epsilon / delta and per-geography allocations beside the counts. **Suppression / reliability-flag gap (G1) — closed 2026-09-03:** NCHS Data Presentation Standards for Proportions (Series 2 No. 175) and for Rates and Counts (No. 200), the StatCan *Guide to the Labour Force Survey 2025* (71-543-G, CV categories 16.5 % / 33.3 % and the minimum-size release table) and the ACS *Data Release Rules* admitted (epoch `g1srp-2026-09-03`); the 12-539-X 6e text never carried the bands (memo ERRATUM-01). The StatCan LFS methodology chapter (71-526-X ch. 8) is staged-not-admitted as the duplicate construct.
- FSS Machine Diagnostic spec (SEO SME) — internal draft; manifest admission gated on finalization/publication. On admission: revive item-level crosswalk of its rule catalog (~70 rule IDs) against indicators A4–A6, A10–A11, C4. Deferred 2026-09-01, reasons: source is draft + below_burn_scope.
- Application-diagnostic evidence gap: no admitted corpus document currently grounds A10 (soft-404 / deep-link / raw-HTML-content checks for statistical data tools). Demand-pull target; the internal draft is the placeholder, not the evidence.

---

*Discipline note: this file is the proposal spine, not the evidence. Cells marked "corpus:" name documents believed admitted — CC verifies each against the manifest and replaces with doc_id + span at adjudication. Anything unverified stays marked draft.*

---

## 10. References

Author-date. Every entry carries the strongest identifier available, in the order DOI > arXiv ID > stable URL. Three classes, per the task's §3 citation discipline; every claim in this document traces to exactly one of them.

### (a) Admitted corpus documents

In `corpus/manifest.json`; cited by `doc_id` and content hash so a stranger can verify the exact bytes this instrument read. Admission is not extraction — none of these is in the graph yet (DD-023: extraction waits on the v0.3.7 contract).

- **Pranjal Aggarwal, Vishvak Murahari, Tanmay Rajpurohit et al.** (2024). *GEO: Generative Engine Optimization*. arXiv:2311.09735 — `aggarwal-2024-geo-generative-engine-optimization` · sha256 `beb95332fcbc`
- **Hiniduma et al.** (2025). *AIDRIN 2.0: A Framework to Assess Data Readiness for AI*. arXiv:2505.18213 — `aidrin-2-0-a-framework-to-assess-data-readiness-for-ai` · sha256 `5a4b54a1871f`
- **Hiniduma et al.** (2024). *AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)*. arXiv:2406.19256 — `aidrin-hiniduma-2024` · sha256 `790a524c6bfc`
- **Anthropic** (n.d.). *Does Anthropic crawl data from the web, and how can site owners block the crawler? (Anthropic support)*. https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler — `anthropic-crawler-support-article` · sha256 `21b26d793875`
- **Mahe Chen, Xiaoxuan Wang, Kaiwen Chen et al.** (2025). *Generative Engine Optimization: How to Dominate AI Search*. arXiv:2509.08919 — `chen-2025-geo-how-to-dominate-ai-search` · sha256 `d68922e12759`
- **Cloudflare** (n.d.). *Cloudflare AI Crawl Control: Manage AI crawlers*. https://developers.cloudflare.com/ai-crawl-control/features/manage-ai-crawlers/ — `cloudflare-ai-crawl-control-manage-crawlers` · sha256 `a501cf050513`
- **Akhtar et al.** (2024). *Croissant: A Metadata Format for ML-Ready Datasets*. arXiv:2403.19546 — `croissant-akhtar-2024-paper` · sha256 `462f157c2338`
- **Hiniduma et al.** (2024). *Data Readiness for AI: A 360-Degree Survey*. arXiv:2404.05779 — `data-readiness-for-ai-a-360-degree-survey` · sha256 `80696c90ad2c`
- **(unspecified)** (n.d.). *FCSM 19-01: Transparent Reporting for Integrated Data Quality*. https://statspolicy.gov/assets/fcsm/files/docs/Transparent_Reporting_FCSM_19_01_092719.pdf — `fcsm-19-01-transparent-reporting-for-integrated-data-quality` · sha256 `b646efbbd55a`
- **(unspecified)** (n.d.). *FCSM 20-04: A Framework for Data Quality*. https://statspolicy.gov/assets/fcsm/files/docs/FCSM.20.04_A_Framework_for_Data_Quality.pdf — `fcsm-20-04-a-framework-for-data-quality` · sha256 `aa75fa223354`
- **(unspecified)** (n.d.). *FCSM 23-02: A Framework for Data Quality: Case Studies*. https://statspolicy.gov/assets/fcsm/files/docs/FCSM.23.02_DQ_case_studies_FINAL.pdf — `fcsm-23-02-a-framework-for-data-quality-case-studies` · sha256 `8e8abe1cda4b`
- **Federal Committee on Statistical Methodology (FCSM)** (2025). *FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality*. https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf — `fcsm-25-03` · sha256 `ba8901ed2dac`
- **Lee** (2026). *From Accuracy to Readiness: Metrics and Benchmarks for Human-AI Decision-Making*. arXiv:2603.18895 — `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` · sha256 `d8dfd4e5249f`
- **Google Search Central** (2025). *Google Search Central: Introduction to robots.txt*. https://developers.google.com/search/docs/crawling-indexing/robots/intro — `google-robots-txt-intro` · sha256 `73a5386012cd`
- **Jeremy Howard / Answer.AI** (2026). *The /llms.txt file (llmstxt.org)*. https://llmstxt.org/ — `llmstxt-proposal` · sha256 `04c6d4c860a3`
- **MLCommons Croissant Working Group** (2026). *Croissant Format Specification (MLCommons)*. https://docs.mlcommons.org/croissant/docs/croissant-spec.html — `mlcommons-croissant-spec` · sha256 `56411897c563`
- **NIST** (n.d.). *NIST AI Risk Management Framework (AI RMF)*. DOI 10.6028/NIST.AI.100-1 — `nist-ai-risk-management-framework-ai-rmf` · sha256 `7576edb531d9`
- **(unspecified)** (n.d.). *NIST AI RMF Playbook*. https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook — `nist-ai-rmf-playbook` · sha256 `65d6101d8065`
- **(unspecified)** (n.d.). *NIST Generative AI Profile (AI 600-1)*. DOI 10.6028/NIST.AI.600-1 — `nist-generative-ai-profile-ai-600-1` · sha256 `6e73620ab6b6`
- **Bitol (Linux Foundation AI & Data)** (2026). *Open Data Contract Standard (ODCS) — Definition*. https://bitol-io.github.io/open-data-contract-standard/latest/ — `odcs-open-data-contract-standard` · sha256 `8a140f031b7b`
- **OpenAI** (n.d.). *OpenAI: Overview of OpenAI crawlers (developers.openai.com/api/docs/bots)*. https://platform.openai.com/docs/bots — `openai-crawlers-bots` · sha256 `91bfb8234592`
- **Perplexity AI** (n.d.). *Perplexity crawlers (docs.perplexity.ai)*. https://docs.perplexity.ai/guides/bots — `perplexity-crawlers` · sha256 `9e1bb529e33d`
- **M. Koster, G. Illyes, H. Zeller et al.** (n.d.). *RFC 9309: Robots Exclusion Protocol*. https://www.rfc-editor.org/rfc/rfc9309 — `rfc-9309-robots-exclusion-protocol` · sha256 `aea78e3b6eec`
- **Sainz, O., Campos, J.A., García-Ferrero, I. et al.** (2023). *NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark*. https://aclanthology.org/2023.findings-emnlp.722/ — `sainz-2023-llm-data-contamination` · sha256 `54ec9661a921`
- **Schema.org Community Group** (n.d.). *schema.org: Dataset*. https://schema.org/Dataset — `schema-org-dataset` · sha256 `7155f56214c5`
- **Schema.org Community Group** (n.d.). *schema.org: DefinedTerm*. https://schema.org/DefinedTerm — `schema-org-definedterm` · sha256 `5d166c7e09c1`
- **SDMX Technical Working Group** (2021). *SDMX 3.0 Technical Specifications, Section 1: Framework for SDMX Technical Standards*. https://sdmx.org/wp-content/uploads/SDMX_3-0-0_SECTION_1_FINAL-1_0.pdf — `sdmx-3-0-section-1-framework` · sha256 `d18ca164fa07`
- **SDMX Sponsors (BIS, ECB, Eurostat, IMF, OECD, UN, World Bank)** (n.d.). *SDMX Standards (sdmx.org standards page)*. https://sdmx.org/standards-2/ — `sdmx-standards-overview` · sha256 `cc86447d3a58`
- **sitemaps.org** (2022). *Sitemaps XML format (sitemaps.org protocol)*. https://www.sitemaps.org/protocol.html — `sitemaps-protocol` · sha256 `8e9d1f33dfbf`
- **OpenSSF SLSA project** (2023). *SLSA Specification v1.0 (Supply-chain Levels for Software Artifacts)*. https://slsa.dev/spec/v1.0/ — `slsa-specification-v1-0` · sha256 `94a6630c0ec4`
- **(unspecified)** (n.d.). *Statistical Policy Working Paper 46: Data Quality Assessment Tool for Administrative Data*. https://statspolicy.gov/assets/fcsm/files/docs/DataQualityAssessmentTool.pdf — `statistical-policy-working-paper-46-data-quality-assessment` · sha256 `1b1f030dbb7e`
- **USAFacts** (2026). *AI-Ready Data: Ensuring Public Data Meets the Needs of AI and the American Public — The USAFacts Guide to AI-Ready Data for Government Agencies*. https://media.usafacts.org/m/634ac133d72ded81/original/USAFacts_AIReadinessForGovernment.pdf — `usafacts-ai-ready-data-guide` · sha256 `02ceecd47c8f`
- **W3C Dataset Exchange Working Group** (2024). *Data Catalog Vocabulary (DCAT) - Version 3 (W3C Recommendation)*. https://www.w3.org/TR/vocab-dcat-3/ — `w3c-dcat-3` · sha256 `c3ed530b3806`
- **Webb, B.** (2026). *State Fidelity Validity for Reproducible AI Systems and Workflows*. DOI 10.5281/zenodo.22111334 — `webb-2026-state-fidelity-validity` · sha256 `849d45f705fa`
- **Mark D. Wilkinson, et al.** (2019). *The FAIR Guiding Principles for scientific data management and stewardship*. https://www.nature.com/articles/sdata201618 — `wilkinson-2016-fair-guiding-principles` · sha256 `cdddd9f4808f`


### (b) External sources not admitted

- **U.S. Department of Commerce** (2025). *Generative Artificial Intelligence and Open Data: Guidelines and Best Practices*. https://www.commerce.gov/news/blog/2025/01/generative-artificial-intelligence-and-open-data-guidelines-and-best-practices — **`acquisition_blocked` 2026-08-29**: commerce.gov returns HTTP 403 to every client tried (curl with browser UA, the `sites/default/files` PDF path, `data.commerce.gov`, and WebFetch); the body returned is a Cloudflare interstitial, not the document. Bot protection, not a paywall or withdrawal. **No secondary source is substituted for it**, and the cells that named it (A1, B1) are recorded as gaps rather than resolved to a stand-in.
- **Databricks** (n.d.). *DQX* (in-pipeline quality rules, quarantine patterns, ODCS rule generation) and *Data Quality Monitoring*. Queued in §9 as **tool evaluations, not adoptions**; not acquired by this pass and not cited as evidence anywhere above.

### (c) Internal artifacts

Cited by task id, filename, or DOI. These are this project's own record, and are marked as such wherever an indicator rests on them rather than on external literature.

- **Webb, B.** (2026). *State Fidelity Validity for Reproducible AI Systems and Workflows*. DOI 10.5281/zenodo.22111334 — also admitted as `webb-2026-state-fidelity-validity` (class a). Grounds E8.
- `docs/research/kg_construction_methodology.md` — §3 (pre-registration pattern, E2), §4 (instrument versioning, E3; the probe protocol, C2), §7.5 (positive controls, E5), §7.6 (instrument-version citation rule, E3).
- `docs/design_decisions.md` — DD-019 (decoy discipline, E5); DD-023 + its 2026-08-29 erratum (extraction unit and emission contract; why nothing here is extracted yet); DD-024 (demand-pull semantic edges — the discipline this crosswalk's evidence cells follow); DD-026 (a precondition must be derived from the threshold it gates, E2).
- `docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md` — the faithfulness numbers behind C2. Instrument versions on their face: decompose 1.1.0, probe_judge 1.1.0, span_checks 1.0.0.
- `cc_tasks/2026-08-29_crosswalk_operationalization.md` and its RESULT — this pass: the admission table, the evidence-resolution table, the tier log, and the plagiarism check.
- `events/batch-017.jsonl` — the `manifest_add` events for the eight documents admitted 2026-08-29, the `acquisition_blocked` event for the Commerce guidance, and the `corpus_epoch_declared` for epoch `crosswalk-2026-08-29`.
- **fss-policy-kg** — sibling project; a federal policy corpus whose primary interface is an MCP server. Cited in §1b as an existence proof for the machine-first stance, and nowhere as evidence for an indicator.
