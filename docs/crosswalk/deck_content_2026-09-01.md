# Framework Deck — slide content v3

**Date:** 2026-09-01 (v3: orientation-first reframe of slide 5, discovery surfaces on 8, reference implementation on 9, frontier-candidate rule on 13, June work as absorbed prior art on 16 — task `cc_tasks/2026-09-01_assessment_consolidation.md`. v2: added slides 2, 4, 8, 14 — why-now, OV-1, SV-1, knowledge architecture). Desktop-drafted content for the hybrid AI Data Readiness framework deck.
**Build:** `cc_tasks/2026-09-01_framework_deck_build.md` (python-pptx, plain text, no theme).
**Numbers:** from `docs/crosswalk/meeting_brief_2026-09-01.md` (floors — burn was in flight at read time). Verify against live graph before any external presentation.
**Architecture figures:** slides 4, 8, 14 are text renderings of diagrams; SVG versions exist (2026-09-01 Desktop thread) and can be exported to images for a later polished deck.
**Editable:** this is a design note, not a tracked artifact. Edit freely; rebuild regenerates the deck.

---

## Slide 1 — Title

**Operationalizing AI-Ready Data for the Federal Statistical System**
From principles to a runnable instrument

Subtitle: An assessment instrument agencies can execute against a data product — every indicator machine-testable where possible, every claim citable to primary literature.

---

## Slide 2 — Why this matters (and why it feels unfamiliar)

- When the public asks a question, an AI system increasingly answers it — by crawling, retrieving, interpreting, and restating someone's data. Whose data it finds, and whether it restates it correctly, is not luck. It is infrastructure.
- SEO was the discipline of being findable by search engines. AIO/GEO extends it: being findable, retrievable, understandable, and correctly cited by AI systems. Very few federal staff have training in either — the discipline exists, but not in-house.
- Absence does not create silence. If the authoritative source is not machine-ready, AI answers still get made — from aggregators, stale copies, or model memory. The result is unattributed error carrying the agency's numbers.
- The specific stakes for statistics: estimates stripped of their uncertainty, wrong vintages presented as current, restatements with no path back to the source.

---

## Slide 3 — The problem: frameworks tell you what, not how

- USAFacts names four criteria (accessible, understandable, accurate, open). FCSM extends data quality to AI-readiness. Neither hands an agency a test.
- Standard failure mode: readiness assessed by practitioner self-report. Self-assessments inflate (social-desirability bias; maturity self-ratings are the canonical case). Observed measures don't argue back.
- Survey-methodology framing: asking the public whether they can find federal data measures who answered the survey, not whether the data is findable. An administrative, tool-based audit measures what a person — or an AI agent — actually experiences.
- Goal: reframe AI readiness as a testable technical property of the data product and its surrounding infrastructure.

---

## Slide 4 — The operational picture (OV-1)

The flow being served, and the readiness question at every hop:

    Consumers (humans + AI agents)
        → Discovery (search engines, AI answer engines, direct + agent access)
        → Agency public surface (pages, data tools, APIs, files)
        → AI answers (restated, cited — or not)

- Hop 1: can machines FIND it? (crawl paths, sitemaps, discovery surfaces)
- Hop 2: can machines FETCH it? (robots policy, edge enforcement, stable URLs)
- Hop 3: can machines UNDERSTAND it? (metadata, structure, semantics, provenance)
- Hop 4: is it RESTATED and CITED correctly? (faithfulness, vintage, uncertainty, attribution)
- Readiness is the property of surviving all four hops. Most frameworks only inspect hop 3 from the inside.

---

## Slide 5 — Design stance: the machine is the first-class user

- The FAIR principles' original thesis (Wilkinson et al. 2016): machine-actionability as the primary design target. A decade old; largely unimplemented in government.
- 2026 instantiation, orientation first: the machine surface is the established discovery stack that already works and is already measured — robots exclusion (RFC 9309), sitemaps, well-known URIs (RFC 8615), schema.org Dataset/DataCatalog, DCAT/data.json, content negotiation, persistent identifiers. An agent arriving cold must be able to establish what exists, what it means, how to get it, and what it may do with it. The human surface derives from that. Not GUI abolition — derivation order. Section 508 keeps the human surface mandatory.
- A meaningful share of public contact with government data now arrives through AI answer engines and LLM crawlers, alongside search and direct visits. Both channels must be tested.
- Existence proof in production: a federal policy corpus (99 documents, 6,600+ obligations) whose primary interface is an MCP server consumed by AI agents.

---

## Slide 6 — The instrument: four criteria, seven groups, ~45 indicators

- USAFacts' four criteria as top-level structure; FCSM's quality framework as the bridge into statistical-agency language.
- Decomposed into seven indicator groups:
  - A Accessible (formats, APIs, bulk, crawler access, discoverability, markup, identifiers, application surfaces)
  - B Understandable (variable semantics, definitions, methodology legibility, quality metadata)
  - C Accurate as consumed by AI (retrieval-grounded QA, restatement faithfulness, vintage disambiguation, citation quality)
  - D Open (license clarity, AI-reuse terms, provenance, inventory completeness)
  - E TEVV loop (cross-cutting)
  - F Release engineering (cross-cutting)
  - G Statistical-product semantics (uncertainty, revisions, vintages, authority, disclosure, protocol provenance)
- Every indicator typed: AUTO (machine-checkable from the public surface) / DOC (verifiable documented attribute) / EVAL (measured by an evaluation harness).
- Machine-first rule: where a machine test exists or can be built, it replaces self-report. The human-survey component is scoped to the residual.

---

## Slide 7 — Three tiers: who can run the test

- `public` — runnable by anyone against the public surface. No permission, no cooperation. All AUTO indicators default here.
- `agency_instrumented` — requires agency cooperation: internal metadata, process artifacts, checklist answers.
- `paid` — requires funded tooling: standing eval harnesses, attestation infrastructure, monitoring. Output here is prescriptive gap-closing guidance, not a score.
- A second, independent axis: open-source vs. proprietary tooling. The tiers intersect it; they don't map onto it.
- Sequencing: `public` ships first — it needs nobody's permission and produces scored profiles immediately.

---

## Slide 8 — Capability architecture (SV-1): what the system needs, not which products

Four layers. Capabilities named by what they provide; technology choices are per-agency.

    OPERATIONAL FLOW (slide 4) — served by:

    AGENCY CAPABILITIES
      Publication            | machine-first products, metadata, markup, discovery surfaces
      Access control         | declared policy vs. enforced treatment vs. observed behavior
      Release engineering    | pre-release gates, contracts, attestation

    MEASUREMENT & FEEDBACK
      Sensor layer           | external diagnostics of the public surface (nothing internal needed)
      Evaluation harness     | TEVV: retrieval QA, restatement faithfulness, drift sentinels
      Telemetry              | crawler logs, usage metrics, AI citation tracking

    EVIDENCE BASE
      Knowledge graph        | literature (admitted, hashed) → indicators → scored profiles

- Measurement feeds back into publication and release: failed evals and sensor warnings become remediation with re-test, not reports.
- Every capability maps to indicator groups: publication ↔ A/B/G, access control ↔ A, release ↔ F, sensors ↔ AUTO tier, harness ↔ EVAL tier + E, telemetry ↔ the validation layer.

---

## Slide 9 — The public tier is runnable today (named tools per check)

- Metadata contract: DCAT-US v1.1/v3.0 JSON Schema validators against data.json — the exact contract powering Data.gov ingestion.
- Structured markup: Schema.org Markup Validator on dataset and release pages (Dataset/DCAT/Croissant).
- Crawler access: robots.txt checks against the maintained AI user-agent registries (training / search-index / user-fetch bot families per vendor); llms.txt validators.
- FAIR baseline: F-UJI — open-source, automated FAIR scoring from a persistent identifier, hosted or self-deployed, REST API for bulk runs.
- Parseability: axe-core / pa11y accessibility engines — semantic-structure failures degrade machine parsing, not just 508 compliance.
- Plain language: readability graders on key explanatory text (Plain Writing Act obligation; lower grade level, less LLM distortion).
- A working in-house reference implementation already exists: an evidence-emitting probe harness (now `assessment/harness/`, imported with its June 2026 history), run against a live Census product. Every probe returns pass/partial/fail and saves the actual response as evidence.
- Caveat carried forward: presence of llms.txt signals intent, not readiness; absence is not disqualifying. No single convention is a readiness measure.

---

## Slide 10 — The sensor layer: the Machine Diagnostic

- A common FSS technical diagnostic (SME-drafted, in progress): deterministic, explainable checks over public web assets — pages, datasets, APIs, data tools.
- Four sensed dimensions: discoverability; indexability & retrievability; machine understandability & citation readiness; ingestibility & computational usability.
- Two design patterns adopted into the instrument:
  1. **Observed facts vs. versioned warning rules.** Raw observations stored separately from calculated warnings; thresholds change and history re-scores without re-crawling.
  2. **Declared / enforced / observed access.** What robots.txt says vs. what the edge/WAF actually does vs. what crawler logs show. A mismatch between layers is itself the finding.
- Applications get their own diagnostic path: statistical data tools are JS-heavy; deep-link failure, fragment-only state, soft-404 shells, and canonical collapse make a tool usable by humans and invisible to machines.

---

## Slide 11 — TEVV: the loop adjacent frameworks leave open

- Their accuracy machinery is real — review, audit trails, notifications — but nothing routes a failed evaluation back into the data product, and nothing attributes a failure to its stage.
- The instrument closes it (NIST AI RMF MEASURE/MANAGE framing): verification/validation split; pre-registered acceptance thresholds; versioned instruments (results never pooled across versions); contamination policy with held-out rotation; seeded positive controls (a cycle with zero fired controls is invalid, not passing); failure attribution (retrieval / vintage / metadata / model); corrective-action closure with re-test; drift sentinels (versioned golden questions on schedule); standing adversarial bank (vintage traps, confusable series, unit traps, suppression probes).

---

## Slide 12 — Publication is a deploy

- A new vintage or page can silently break machine consumers. Software solved this: CI/CD, regression suites, contracts.
- Release-engineering indicators: pre-release expectation gates; contract stability with deprecation windows; regression on vintage transition (series IDs, geography codes, endpoints survive — or a crosswalk ships); machine-readable changelogs; staged rollout with AI-consumer regression; signed releases / provenance attestation (SLSA-class) so downstream copies trace to the authoritative artifact.
- Prior art: data contracts (ODCS), expectation-suite testing, schema registries, supply-chain attestation.

---

## Slide 13 — Flagship indicator: uncertainty legibility (G1)

- The statistical system's core differentiator is that its numbers carry error measures. No AI-readiness framework reviewed asks whether AI systems **preserve** uncertainty when restating values. Where uncertainty appears at all, it is framed as a privacy safeguard.
- G1: MOEs, CVs, DP noise parameters published as structured fields beside estimates — not footnotes — plus an EVAL: do AI restatements carry the uncertainty?
- Measurement template borrowed from the sensor layer's access triad: declared uncertainty (structured fields) vs. surfaced uncertainty (what retrieval delivers) vs. observed preservation (what restatements keep).
- Standing rule for any mechanism, old or new: every mechanism is a hypothesis about how machines actually orient. What admits or retires one is observed machine behavior — crawler and edge logs, probe results, citation telemetry — never vintage. MCP/WebMCP-class endpoints are dated frontier candidates under exactly that rule, reported separately and never scored as core unreadiness.

---

## Slide 14 — How the pieces relate: the knowledge architecture

The crosswalk is the join structure. Nothing floats:

    Literature corpus  →  Extraction        →  Crosswalk           →  Instrument       →  Assessment
    (documents admitted   (claims, concepts,    (indicator evidence     (typed, tiered      (scored product
    with reasons and      definitions — each    cells: doc_id +         indicators,         profiles +
    content hashes)       with a verbatim       grounding span; empty   frozen versions)    gap lists)
                          grounding span)       cell = registered gap)

- Two loops close the system:
  1. **Evidence loop** — empty evidence cells are registered gaps that target the next acquisition round. The corpus grows by measured demand, not by intuition.
  2. **Remediation loop** — failed indicators on a product become corrective actions with re-test (the TEVV closure), and recurring failures across products become the improvement agenda fed back to framework authors.
- The rule that makes the structure trustworthy: no cell filled without a document; no claim without a span; no number without its interval or its n.

---

## Slide 15 — Evidence discipline: the instrument stands on a measured corpus

- Every indicator is citable to primary literature through a knowledge graph: 194 documents admitted with reasons and content hashes; extraction ongoing (31 docs, ~4,800 nodes at last read — a floor, burn in flight).
- Nothing enters without a verbatim grounding span. Every claim passed a pre-registered faithfulness gate (fabrication 95% upper bound < 0.10) and every batch passed acceptance sampling before entering. Every quality number ships with its interval or its n — the graph practices G1's own discipline.
- The measurement layer finds its own gaps: Group D (openness) names zero evidence documents. License clarity, AI-reuse terms, provenance, inventory completeness — thinnest slice of the corpus AND of the literature. A finding, not a bug: the next acquisition round is targeted by measurement, not intuition.

---

## Slide 16 — Positioning against prior art

- **F-UJI / FAIR assessment tools:** genuine prior art for automated readiness scoring; adopted as the FAIR baseline, not rebuilt. This instrument's additions: statistical-native constructs (uncertainty, revisions, vintage identity, disclosure semantics), the TEVV loop, and AI-restatement EVALs — none of which FAIR scoring touches.
- **Commercial AI-visibility platforms** (Profound, Otterly, Rankscale class): the only current instruments for whether content surfaces in AI answers. Built for brand marketing; no validated methodology for government data. Used as directional signals in the paid tier, never as authoritative scores.
- **The June 2026 FSS assessment work (absorbed, not cited):** probe harness, benchmark rubric, three-stream assessment spec, covariate/peer-cohort schema. Imported into this repo with history as `assessment/`; the merged live design is `docs/crosswalk/assessment_protocol.md`. It is the AUTO-tier reference implementation rather than an external comparator.
- **Enterprise SEO suites:** commodity crawling is commodity. The specification is tool-neutral; agencies satisfy it with whatever their governance approves.

---

## Slide 17 — What's still missing (the honest slide)

Four foundational layers no framework — including this one — has built yet:

1. **Reuse semantics (FAIR's R).** All four openness indicators are gaps in corpus and literature alike. Machine-readable license/AI-training terms (RAIL, TDM-reservation class, PROV-O) are the field's thinnest layer.
2. **Consumption telemetry.** Everything above is supply-side or harness-side. Observed demand exists today for free — Data.gov's per-agency metrics dashboard (views, downloads, harvest cadence) — plus server-log AI-bot analysis; the paid tier adds AI-answer citation tracking. Readiness that never validates against observed use is an untested construct.
3. **System-level arbitration.** The instrument scores products one at a time. Nothing answers: which product, vintage, geography is the canonical machine answer? SDMX-class registries are the prior art; an AI-ready statistical *system* needs the registry layer.
4. **Consumer-side verifiability.** Signing releases is not enough; the consumer holding a cited number needs an affordance to verify it back to the authoritative artifact (C2PA-class content credentials, adapted to statistics). Without it, authority metadata is an assertion aggregators can copy.

---

## Slide 18 — January deliverable and pilot

- Freeze indicator set v1 after one review pass (operator + 1–2 FCSM-adjacent colleagues).
- Select 3–5 statistical data products spanning dissemination styles (API-first, table-page, bulk-file legacy).
- Run AUTO mechanically; DOC by checklist; accuracy EVALs with a small fixed question set through existing probe/judge machinery.
- Output per product: scored profile + gap list + citation trail. Gap lists across products = the improvement agenda.
- `public` tier ships first; `agency_instrumented` piloted with willing partners; `paid` documented as roadmap with cost classes.

---

*End of content. Slide count: 18. Tone: declarative, no marketing. Numbers carry intervals or are marked as floors. Slides 4, 8, 14 use preformatted text blocks — build task renders them in monospace if the layout survives, otherwise as indented bullets.*
