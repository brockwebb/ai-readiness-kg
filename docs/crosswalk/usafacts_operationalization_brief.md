# Making "AI-Ready Data" Testable

**A crosswalk from the USAFacts AI-ready criteria to a runnable assessment instrument**

Brock Webb · 2026-08-29 · v0.1, for review
Companion document: `docs/crosswalk/usafacts_operationalization_skeleton.md` (the full indicator tables)
Audience: the USAFacts team and FCSM-adjacent colleagues

---

## Purpose

The USAFacts guide to AI-ready data (USAFacts 2026) sets out four criteria — accessible, understandable, accurate, open — and, under each, a list of practices agencies should adopt. It is a good frame and, as far as I can tell, the only short document aimed squarely at the right audience. What it does not do, and does not claim to do, is give an agency a **test**: something you can run against a specific data product and get back a score, a gap list, and a citation for why each gap matters.

This crosswalk is an attempt at that test. It keeps the four criteria as the top-level structure, decomposes each into constructs and then into concrete indicators, and grounds each indicator in primary literature through a knowledge graph built for the purpose. The design constraint I set myself is that **every indicator must be citable by a stranger** — a doc_id, a content hash, a page. Where I could not find a source, the cell says `gap` rather than filling in something plausible.

The result is 45 indicators in seven groups. Twenty-five currently resolve to at least one admitted source document; twenty are open gaps. I am circulating it at this stage precisely because the gaps and the disagreements are the useful part.

## The stance underneath it: the machine is the first-class user

One design commitment runs through every indicator, so it is worth stating plainly rather than leaving implicit: **design the data product for machine consumption first, and derive the human surface from it** — not the other way around.

This is not a prediction about where things are heading. It is the original thesis of the FAIR principles (Wilkinson et al. 2016), which put machine-actionability at the centre a decade ago and which most of government has still not implemented. The 2026 instantiation is machine-to-machine protocol surfaces — documented APIs, agent endpoints of the MCP/A2A class, `llms.txt` — with generative interfaces closing the last mile to a human reader. I have a working existence proof rather than an argument: a federal statistical-policy corpus whose primary interface is an MCP server, with the human view derived from it.

The USAFacts guide is already machine-oriented in its intent — it asks for machine-readable formats, machine-understandable documentation, and documentation reachable by web crawlers. What I am adding is narrower than it may sound: an explicit **derivation order**, and an indicator (A9) that makes agent-protocol access auditable rather than aspirational. The boundary is worth stating too: Section 508 keeps the human surface mandatory. This is about which surface is generated from which, not about removing interfaces people use.

## Shape of the instrument

Each indicator is typed by how it is checked — `AUTO` (machine-checkable from the public surface), `DOC` (a documented attribute a human confirms), or `EVAL` (measured by an evaluation harness) — and tiered by what it costs to run: `public` (anyone, no permission), `agency_instrumented` (needs agency cooperation), `paid` (needs funded tooling). Seventeen indicators are `public`, twenty-one `agency_instrumented`, seven `paid`.

The seven groups, with one indicator each as an exemplar:

- **A — Accessible (9).** Machine-readable formats, programmatic access, bulk download, crawler policy, discoverability, structured markup, stable identifiers, surface timeliness, agent surface. *Exemplar A6:* schema.org/Dataset, DCAT, or Croissant markup validates on the product page. `AUTO`, `public`.
- **B — Understandable (6).** Variable-level semantics, a definitions surface, methodology legibility, quality metadata, semantic consistency across vintages, plain-language summaries. *Exemplar B4:* data-quality attributes published as metadata rather than prose. `DOC`, `agency_instrumented`.
- **C — Accurate as consumed by AI (5).** Retrieval-grounded QA accuracy, faithfulness of AI restatement, vintage disambiguation, citation quality, readiness-metric baseline. *Exemplar C2:* are model statements about the product entailed by the product's own text? `EVAL`, `paid`.
- **D — Open (4).** Licence clarity, reuse permissions for AI, provenance completeness, no dark data. *Exemplar D1:* an explicit machine-readable licence on both product and API. `AUTO`, `public`.
- **E — TEVV loop (9).** Verification/validation split, pre-registered acceptance thresholds, instrument versioning, contamination policy, positive controls, failure attribution, corrective-action closure, drift sentinels, adversarial evaluation. *Exemplar E5:* seeded known-bad items in every evaluation cycle; a cycle where none fires is invalid, not passing. `AUTO`, `public`.
- **F — Release engineering (6).** Pre-release gates, contract stability, vintage-transition regression, change legibility, staged rollout, release authenticity. *Exemplar F3:* series identifiers and endpoints survive a new vintage, or a crosswalk ships with it. `AUTO`, `public`.
- **G — Statistical-system constructs (6).** Uncertainty legibility, revision semantics, classification identity, authority metadata, disclosure semantics, measurement-protocol provenance. *Exemplar G1:* error measures published as structured fields beside estimates, plus an evaluation of whether AI restatements carry them. `DOC`+`EVAL`, `agency_instrumented`.

The full tables are in the companion document. I have deliberately not reproduced them here — the point of the brief is the argument, not the inventory.

## Eleven points of feedback on the guide

These are offered as a reader who has tried to operationalize the document, and each one is a place where I had to add something to make an indicator testable. I have re-read the passages each item targets before writing it; where the guide already does the thing, I say so.

**1. Decomposition with receipts.** Four criteria become 45 indicators, each carrying literature provenance rather than assertion. This is the whole contribution and the rest of these items are its by-products.

**2. "Understandable" needs a conformance test, not more scope.** The guide does address machine-understandability directly, and asks for data dictionaries, taxonomies, ontologies, Data Cards, and semantic labelling — this is not a missing criterion. What is missing is the level of specification that makes it checkable: variable-level metadata (labels, definitions, units, universes) as a named requirement, and a test that says whether a given product has it. FCSM 25-03 supplies exactly that bridge from machine-readable to machine-understandable in statistical-agency language, and is the natural citation.

**3. The accuracy evaluations, instantiated.** The guide asks agencies to define what a good model response looks like and to benchmark systems against their own evaluations. That is the right ask; C1 and C2 turn it into a harness — a fixed question set per product, retrieval-grounded, with answers judged for entailment against the product's own text. This machinery already exists and is calibrated in the companion project; re-aiming it at data products is engineering, not research.

**4. A measurable visibility layer.** The guide encourages AI developers to cite official endpoints and asks that documentation be reachable by crawlers. Both are about what *developers* should do. A4–A6 make the *agency's* side auditable: robots and AI-crawler policy, `llms.txt`, sitemap coverage, and valid dataset markup are all checkable from outside with no cooperation, which is what makes them a good first tier.

**5. ACCURATE needs a closed loop.** The guide is not open-loop — it asks for internal review, automated validation, and audit trails, and it asks agencies to notify developers of discrepancies. But notification is where the model-facing path ends, and there is no defined route from a failed evaluation back into the *data product* (a metadata fix, a vintage pointer, a dictionary entry) with a re-test. Group E adds that route along with the things that make a loop trustworthy rather than merely present: pre-registered thresholds, versioned instruments, and a contamination policy. That last one matters more than it sounds — a public evaluation set should be assumed to be inside the next model generation's training data (Sainz et al. 2023), so "release a public test set" needs a held-out rotation or it decays into a memorization check.

**6. Statistical metadata standards.** The guide recommends aligning with "standard schemas like NIEM and Crossaint" (§UNDERSTANDABLE). Two notes. *Croissant* is the MLCommons ML-dataset metadata format — the spelling looks like a slip worth fixing, since the actual spec is a good citation for A6. And NIEM is a justice-and-public-safety exchange standard; the statistical metadata standards are SDMX (data and structure exchange, including break-in-series metadata), DDI (variable and study documentation), and DCAT (catalog discovery). DCAT is a notable omission given the same section asks for improved centralized catalogs — data.gov's own profile is DCAT-US.

**7. Publication is a deploy.** The guide asks for versioning so developers can track updates, and for webhooks on frequently updated data. Group F treats the release cycle the way software treats a deploy: a published expectation suite that a new vintage must pass before it goes live, announced deprecation windows for breaking schema changes, regression on vintage transitions, a machine-readable changelog, and staged rollout. The prior art here is ordinary — CI/CD, data contracts, expectation-suite testing, schema-registry compatibility — and the Open Data Contract Standard gives the contract half a specification to point at.

**8. Uncertainty legibility.** This is the sharpest gap I found, and it is a gap in every adjacent framework I have reviewed, not only this one. The guide addresses differential privacy and suppressed-data documentation, both under OPEN and both framed as privacy protections. Neither is the same as publishing *uncertainty* — margins of error, coefficients of variation, the noise parameters themselves — as structured fields beside the estimates, so that a consuming system can carry them. Uncertainty communication is the statistical system's core differentiator, and no AI-readiness guidance I have found asks whether AI systems preserve it. G1 is my candidate flagship indicator for January.

**9. The machine as first-class user.** Covered above; the addition is derivation order plus an agent-surface indicator, on a FAIR footing rather than a forecast.

**10. Protocol as contract.** When a measurement instrument changes — a survey redesign, a case-definition revision, a reclassification — the series has a break, and a consumer that compares across it is simply wrong. The guide asks agencies to disclose methodologies for derived datasets, which is adjacent but not the same. G6 asks for the collection protocol as a versioned epoch on the series with machine-readable break annotations (SDMX has the vocabulary), and adds the consumer-side test: an AI system asked to compare across a break must surface it.

**11. Red teaming.** The guide asks that documentation and data be regularly reviewed “to find and correct potential abuse and misinformation” (USAFacts 2026, ACCURATE), which is a real if informal version of this. E9 makes it a standing bank with named break modes: vintage traps, confusable series, unit traps, misreads of privacy-protected values, suppression probes — plus a surface red team for the markup and `llms.txt` layer, which is newly attack-relevant now that agents parse it. Frameworks tend to test what works; enumerating how a product breaks is the other half.

## What is actually novel here

Most of the above is assembly: known standards, known testing discipline, pointed at a new object. One part is not, and it is worth naming once.

**Producer-surface audits exist. Consumer-behaviour audits do not.** Every readiness framework I have reviewed — including this one — evaluates what the agency *publishes*: is it machine-readable, is it documented, is it licensed. None evaluates what AI systems actually *do* with it. The `EVAL` indicators in groups C and G ask the second question: does a retrieval-paired model preserve the margin of error, surface the series break, return the vintage that was asked for, and restate the product faithfully? Those are measurable today with existing entailment-judging machinery, and they are the difference between a data product that is *formatted* for AI and one that is *understood* by it. That is the contribution I would most like reviewed, because if it is wrong it is wrong at the foundation.

## Pilot and sequencing

The tiering is the sequencing plan. The `public` tier — seventeen indicators — needs nobody's permission and can be run against any agency's live surface today, which makes it both the fastest path to a real result and the honest way to avoid a self-assessment. Organizational self-ratings inflate; observed measures do not argue back. So wherever a public machine test exists, it replaces practitioner self-report, and the human questionnaire is scoped to the residual that no outside test can see.

`agency_instrumented` indicators come next, piloted with willing partners, since they need internal artifacts. `paid` indicators — standing evaluation harnesses, monitoring, attestation infrastructure — are documented as a roadmap with capability descriptions, not scored.

For the pilot: freeze the indicator set after one review pass, then select three to five data products spanning dissemination styles (API-first, table-page, legacy bulk file). Output per product is a scored profile, a gap list, and the citation trail. The gap lists across products are the improvement agenda — and the empirical version of this feedback.

**January milestone:** the frozen indicator set with the `public` tier runnable, pilot profiles for the selected products, and every indicator resolving to a citation. Scoring weights are deliberately not designed yet; weighting before the indicator set survives review is how instruments acquire false precision.

## What this document does not claim

The instrument has not been run against anything. The 45 indicators are candidates, twenty of them without a source document yet. The `public` tier is the only part I would expect to survive contact unchanged. And the source documents behind it are admitted to the corpus but not yet extracted into the knowledge graph — that waits on an extraction-contract revision, so the citations here are document-level, not span-level. Span-level grounding is the January target, not a present claim.

Corrections to any of the eleven items above are more useful to me than agreement, particularly item 5 and item 8, where I may be describing a gap that exists in the document but not in your practice.

---

## References

**(a) Admitted corpus documents** — in `corpus/manifest.json`, cited by doc_id and content hash.

- **USAFacts** (2026). *AI-Ready Data: Ensuring Public Data Meets the Needs of AI and the American Public — The USAFacts Guide to AI-Ready Data for Government Agencies*. https://media.usafacts.org/m/634ac133d72ded81/original/USAFacts_AIReadinessForGovernment.pdf — `usafacts-ai-ready-data-guide` · sha256 `02ceecd47c8f`
- **USAFacts & Partnership for Public Service** (2026). *Standards for Excellent Data Products — Detailed User Guide*. https://media.usafacts.org/m/260cbbd653fb33ec/original/Detailed-User-Guide-Federal-Data-Excellence-Standards.pdf — `usafacts-fde-standards-detailed` · sha256 `98a092ac6f19`
- **Federal Committee on Statistical Methodology** (2025). *FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality*. https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf — `fcsm-25-03` · sha256 `ba8901ed2dac`
- **Wilkinson, M.D., et al.** (2016). *The FAIR Guiding Principles for scientific data management and stewardship*. DOI 10.1038/sdata.2016.18 — `wilkinson-2016-fair-guiding-principles` · sha256 `cdddd9f48087`
- **Sainz, O., Campos, J.A., García-Ferrero, I., Etxaniz, J., Lopez de Lacalle, O., & Agirre, E.** (2023). *NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark*. Findings of ACL: EMNLP 2023. DOI 10.18653/v1/2023.findings-emnlp.722 — `sainz-2023-llm-data-contamination` · sha256 `54ec9661a921`
- **SDMX** (2021). *SDMX 3.0 Technical Specifications, Section 1: Framework*. https://sdmx.org/wp-content/uploads/SDMX_3-0-0_SECTION_1_FINAL-1_0.pdf — `sdmx-3-0-section-1-framework` · sha256 `d18ca164fa07`
- **DDI Alliance** (2026). *DDI-Codebook (DDI-C)*. https://ddialliance.org/ddi-codebook — `ddi-codebook-specification` · sha256 `97fa0a19fad7`
- **W3C** (2024). *Data Catalog Vocabulary (DCAT) — Version 3*. https://www.w3.org/TR/vocab-dcat-3/ — `w3c-dcat-3` · sha256 `c3ed530b3806`
- **MLCommons** (2026). *Croissant Format Specification*. https://docs.mlcommons.org/croissant/docs/croissant-spec.html — `mlcommons-croissant-spec` · sha256 `56411897c563`
- **Bitol (Linux Foundation AI & Data)** (2026). *Open Data Contract Standard (ODCS)*. https://bitol-io.github.io/open-data-contract-standard/latest/ — `odcs-open-data-contract-standard` · sha256 `8a140f031b7b`
- **OpenSSF SLSA project** (2023). *SLSA Specification v1.0*. https://slsa.dev/spec/v1.0/ — `slsa-specification-v1-0` · sha256 `94a6630c0ec4`
- **NIST** (2023). *AI Risk Management Framework (AI RMF 1.0)*. DOI 10.6028/NIST.AI.100-1 — `nist-ai-risk-management-framework-ai-rmf` · sha256 `7576edb531d9`
- **NIST** (2024). *Generative AI Profile (NIST AI 600-1)*. — `nist-generative-ai-profile-ai-600-1`
- **Aggarwal, P., Murahari, V., Rajpurohit, T., et al.** (2024). *GEO: Generative Engine Optimization*. arXiv:2311.09735 — `aggarwal-2024-geo-generative-engine-optimization` · sha256 `beb95332fcbc`
- **Federal Committee on Statistical Methodology** (2023). *FCSM 23-02: A Framework for Data Quality — Case Studies*. — `fcsm-23-02-a-framework-for-data-quality-case-studies`
- **Hiniduma, K., et al.** (2024). *AIDRIN: AI Data Readiness Inspector*. arXiv:2406.19256 — `aidrin-hiniduma-2024` · sha256 `790a524c6bfc`
- **llmstxt.org** (2026). *The /llms.txt file*. https://llmstxt.org/ — `llmstxt-proposal` · sha256 `04c6d4c860a3`

The companion skeleton's §10 carries the complete list of all 36 admitted documents cited across both documents, including the crawler-policy and schema.org sources behind A4–A6.

**(b) External sources not admitted**

- **U.S. Department of Commerce** (2025). *Generative Artificial Intelligence and Open Data: Guidelines and Best Practices*. https://www.commerce.gov/news/blog/2025/01/generative-artificial-intelligence-and-open-data-guidelines-and-best-practices — accessed 2026-08-29, **HTTP 403** (bot protection; a Cloudflare interstitial, not the document). Not cited as evidence anywhere above, and no substitute was used in its place.

**(c) Internal artifacts**

- **Webb, B.** (2026). *State Fidelity Validity for Reproducible AI Systems and Workflows*. DOI 10.5281/zenodo.22111334 — the basis for E8 (drift sentinels).
- `docs/crosswalk/usafacts_operationalization_skeleton.md` v0.2 — the full indicator tables, evidence cells, and tier assignments summarized here.
- `docs/research/kg_construction_methodology.md` §3, §4, §7.5, §7.6 — the pre-registration, instrument-versioning, and positive-control discipline that groups E and F apply to data products.
- `docs/design_decisions.md` DD-023 (and its 2026-08-29 erratum), DD-024, DD-026 — why the source documents behind this brief are admitted but not yet extracted, and the demand-pull evidence discipline the crosswalk follows.
- `docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md` — the calibration behind the claim in item 3 that the entailment-judging machinery exists and works: zero fabrications, Wilson-95 upper bound 0.046, under instrument versions decompose 1.1.0 / probe_judge 1.1.0 / span_checks 1.0.0.
