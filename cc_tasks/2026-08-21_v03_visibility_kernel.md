# CC Task — AIRKG schema v0.3 + machine-visibility kernel corpus (harvest, pilot, bulk)

**Date:** 2026-08-21
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Max OAuth only. `ANTHROPIC_API_KEY` must remain unset — abort any phase whose code path requires it.
**Execution model:** Multi-agent / background run permitted. Phases are ordered; parallelism is stated per phase. Every phase writes its own dated sub-RESULT under `docs/research/` and the orchestrator assembles `cc_tasks/2026-08-21_v03_visibility_kernel_RESULT.md` at the end. If the run halts early, the RESULT is still written with whatever phases completed.
**This task file is immutable.** Do not edit it. Discrepancies between what it says and what is live are reported in the RESULT, never silently reconciled.

## Authorizations recorded in this task (Desktop session, 2026-08-21)

- **AUTH-1 — one graph, schema v0.3.** Decision DD-009: the machine-visibility / machine-actionability literature (SEO, GEO/AIO, web standards, platform crawler behavior, federal digital guidance) is part of *this* graph, not a sibling repo. Reason of record: the graph's first question is which readiness definitions exist and where they conflict; definitions that include discoverability conflict with definitions that stop at institutional readiness, and that conflict is only observable inside one graph. Second reason: rename-of-old-science ("AIO" = crawlability + structured data + content clarity) is provable only via Concept aliases / `subtype_of` / `extends` inside one graph. Wintermute's contamination lesson concerned unrelated projects under label isolation, not one project with two literatures.
- **AUTH-2 — rule-based manifest adds.** Phase 3 manifest-adds documents from staging **by the inclusion rule written in Phase 2**, with per-document rationale recorded in the manifest event. This is within DD-005 L2/L3 (the rule is operator-authored, the agent applies it). It is not an autonomy-level promotion; DD-005 is not amended.
- **AUTH-3 — controls.yaml.** `extract: on` and `extract_daily_docs: 60` for the duration of this task. **Restore the prior file byte-for-byte on completion or halt** (authorization-widening doctrine: resume restores prior state, never widens it). Record before/after sha256 of `controls.yaml` in the RESULT. `forage` stays `off`; harvesting in Phase 2 is a scripted, bounded fetch of a named list, not the forager.
- **AUTH-4 — oversize extent rule.** Standards specifications that exceed MAX_DOC_CHARS (250,000) are manifested at a *stated extent* (the normative core, or the spec's own primer/summary document), with `extent_note` and the excluded-sections list recorded in the manifest event. Same move as §515 (manifested at corrected extent). No blanket OVERSIZE_ALLOW additions; if a document needs a whole-doc clearance above 250K, **skip it, register it in `refetch_candidates.jsonl` with reason `oversize_needs_clearance`**, and proceed.
- **AUTH-5 — extraction window.** Target ≈5 hours wall-clock of extraction across Phases 4 and 5 combined. Phase 5 measures rate on its first document before committing the remainder (see Phase 5). Hitting the window is a normal stop, not a failure; remaining docs stay manifested-not-extracted for a follow-on task.

## Phase 0 — Preflight (serial, zero spend)

1. `python -m pytest tests/ -v` must pass at baseline. Record pass count.
2. `build_projection.py` and `run_baseline_gates.py` run clean against the current log; record the baseline gate table (expect: grounding 0, edge_endpoint_validation 747, 71 documents). These are the comparison values for Phase 6.
3. Record `controls.yaml` sha256, then apply AUTH-3.
4. Verify `corpus/staging/inbox/` contents; list them in the Phase 0 sub-RESULT. If a file whose title contains "Visibility Diagnostic" (the SME "AI Visibility Diagnostic Technical Framework") is present, it is a Phase 2 candidate with `source_type: practitioner` — see Phase 1 for that enum value.

## Phase 1 — Schema v0.3 (append-only) — parallel with Phase 2

Edit `kg/schema.yaml` and `docs/schema_v0.1.md` (changelog + tables). Append-only: nothing existing is renamed or removed. Bump `schema_version` to `"0.3"`. Every addition below is transcribed into both files; the parser's `pairs` enforcement applies to all new edges.

**Node types added**
- `Practice` — a normative recommendation a source makes about how to publish, structure, expose, or maintain data or content for machine consumers. Properties: `text`, `grounding_span`, `as_of_date`, `scope` (values: `dataset`, `api`, `bulk_file`, `tool`, `content`, `advisory`, `site`, `any`).
- `Tool` — software that implements one or more Measures (Lighthouse, Scrapy, pySHACL, LinkChecker, GoAccess, Spectral, extruct, GSA Site Scanning engine, DAP). Properties: `name`, `steward`, `license`, `url`, `as_of_date`.
- `Platform` — a machine consumer whose behavior is targeted or described: Google Search, Bing, a named crawler, an LLM vendor's retrieval system, Cloudflare/Akamai bot controls. Properties: `name`, `operator`, `as_of_date`.

**Properties added**
- `Claim.evidence_grade`, values in descending strength: `peer_reviewed_experiment`, `platform_official`, `measured_practitioner` (disclosed method and data), `practitioner_assertion` (no method), `inference`. Required on every Claim extracted under v0.3; absent = quarantine.
- `Measure.tier`, values: `public` (runnable by anyone from outside), `agency_instrumented` (needs agency-side analytics, scripts, logs), `paid` (commercial product). Optional; present when the source states or implies it.
- `Document.source_type` gains `practitioner` (SME-authored or industry-practitioner guidance that is not a vendor product page). Existing value `industry` is unchanged.

**Edge types added** (each with `pairs`, `meaning`, and an `external_alignment` URI where a reasonable one exists; absence of a URI is recorded explicitly as `external_alignment: none`)
- `recommends`: Document → Practice
- `supported_by`: Practice → Claim
- `implemented_by`: Measure → Tool
- `consumes`: Platform → Standard (platform reads/honors this spec)
- `applies_to`: [Practice, Measure] → Concept (the asset class or concept the practice/measure targets; asset classes live as Concepts anchored via §8 to DCAT 3 / schema.org terms: Dataset, Distribution, DataService, DataCatalog, WebApplication, Report, DefinedTerm)
- `targets`: Practice → Platform
- `supersedes`: Document → Document (newer platform/guidance document replaces an earlier version; distinct from the `extraction_superseded` overlay event, which is about extraction runs, not documents)

**Tests (required, must pass before Phase 3 starts)**
- Extend `tests/test_extraction_schema_pairs.py` for every new edge type and illegal-pair routing to `proposed_relationships`.
- Extend `tests/test_extraction_parser.py`: Claim without `evidence_grade` under schema 0.3 is quarantined; `evidence_grade` outside the enum is quarantined; `Measure.tier` enum enforced when present.
- Add a test that loads `schema.yaml` and asserts v0.2 node/edge types are a strict subset of v0.3 (append-only invariant).
- Prompt template: bump to require `evidence_grade` on Claims and to describe the new types; version the template, stamp it in extraction events as today.

**Docs**
- `docs/design_decisions.md`: append **DD-009** (one graph, text from AUTH-1) and **DD-010** (evidence grading: why it exists, the enum, and the rule that the diagnostic guide cites the grade). Dated 2026-08-21.

Phase 1 sub-RESULT: diff summary, test counts before/after, template version.

## Phase 2 — Kernel harvest to staging (parallel with Phase 1, zero extraction spend)

Scripted, bounded fetch into `corpus/staging/inbox/` using the repo's existing acquisition path (dixie / manifest module conventions: sha256, capture timestamp, primary_url, retrieval evidence). Every fetch, successful or not, appends to `corpus/staging/candidate_register.jsonl` with `candidate_status`: `fetched`, `fetch_failed`, `excluded_by_rule`, `oversize_needs_clearance`.

**Inclusion rule (write it verbatim to `docs/research/2026-08-21_kernel_inclusion_rule.md` before fetching):**
Include if the document is one of: (a) a normative specification or its steward-published primer; (b) platform-official documentation from the operator of a search engine, crawler, CDN, or AI retrieval system; (c) peer-reviewed or preprint research on web/dataset discoverability, retrieval, or generative-engine behavior; (d) US federal digital-service guidance or statute bearing on public web data exposure; (e) SME/practitioner guidance already in the inbox. Exclude: vendor product marketing pages, SEO-agency blog posts, listicles, anything without a stable URL or a fetchable primary text. Exclusions are registered, not silently dropped.

**Kernel list** (fetch the current version; record `as_of` from the page or publication date; do not fabricate versions):

Standards and stewards
- schema.org: Dataset, DataCatalog, DataDownload, DataFeed, WebAPI, SoftwareApplication, DefinedTerm type pages (each page is its own document; the full vocabulary is NOT fetched)
- W3C DCAT 3 Recommendation (extent: normative sections; skip examples appendices if oversize)
- DCAT-US 3.0 (resources.data.gov)
- W3C Data on the Web Best Practices (DWBP, 2017)
- W3C RDF Data Cube vocabulary (primer if the Rec is oversize)
- SDMX technical standard primer (sdmx.org)
- MLCommons Croissant specification
- sitemaps.org protocol
- RFC 9309 Robots Exclusion Protocol
- llms.txt proposal (llmstxt.org)
- IndexNow protocol documentation
- JSON-LD 1.1 primer (not the full Rec)
- OpenAPI Specification (latest; extent: core sections)

Platform-official
- Google Search Central: structured data intro, Dataset structured data, crawling/indexing overview, robots.txt docs, "AI features and your website" (or current equivalent), Search Console guide
- Bing Webmaster: AI Performance announcement (2026), Webmaster guidelines, Webmaster APIs
- Cloudflare: AI Crawl Control docs, Content Signals Policy (or current equivalent)
- Akamai: DataStream 2 docs, Bot Manager bot reports docs
- OpenAI / Anthropic / Perplexity published crawler documentation pages (user-agent and robots behavior), whichever are fetchable

Research
- Aggarwal et al., "GEO: Generative Engine Optimization", KDD 2024 (arXiv 2311.09735)
- Wilkinson et al. 2016, FAIR Guiding Principles (Scientific Data)
- Jacobsen et al. 2020, FAIR Principles: Interpretations and Implementation Considerations
- Any 2025–2026 peer-reviewed or arXiv work on LLM retrieval/citation behavior toward web content; cap 5, select by citation count and venue, register the selection rule used

Federal
- 21st Century IDEA Act (P.L. 115-336)
- OMB M-23-22 (Delivering a Digital-First Public Experience)
- digital.gov: DAP guide, Search.gov guide, website standards guidance
- GSA Site Scanning README/engine documentation (GitHub)
- data.gov / resources.data.gov metadata requirements (DCAT-US schema page)
- Census Bureau API user guide and developers documentation landing (already-held Census quality standards D3/F1/F2 are in corpus; do not refetch)

Practitioner / SME
- Any "Visibility Diagnostic" framework file found in inbox (Phase 0)

Tools (documentation pages only, so `Tool` nodes have a grounded source)
- Lighthouse docs, Scrapy docs landing, Playwright docs landing, extruct README, Spectral README, pySHACL README, LinkChecker README, GoAccess README

Expected count ≈ 45–55 candidates. Phase 2 sub-RESULT: register summary by status, total chars fetched, the five largest documents with char counts and the extent decision for each.

## Phase 3 — Manifest adds (serial; requires Phase 1 tests green and Phase 2 complete)

- Manifest-add every `fetched` candidate via `kg/manifest.py` per the established `manifest_add` event shape. Each event carries: inclusion-rule clause matched (a–e), `source_type` (including the new `practitioner` value), `as_of`, sha256, primary_url, retrieval evidence, and `extent_note` where AUTH-4 applied.
- Identity check against existing manifest: nothing already manifested is re-added (Census D3/F1/F2, OMB memos already held).
- Phase 3 sub-RESULT: count added, count skipped-already-present, count deferred with reason.

## Phase 4 — Pilot (serial)

Per schema §9: no bulk on an unpiloted schema. Extract exactly these five (substitute the nearest equivalent if one failed to fetch, and say so):
1. Google Search Central Dataset structured data page (platform-official)
2. W3C DWBP (standard, long)
3. Aggarwal et al. GEO (research)
4. The SME Visibility Diagnostic framework if present, else digital.gov DAP guide (practitioner / federal)
5. Cloudflare AI Crawl Control (platform-official, fast-moving)

Audit, written to `docs/research/2026-08-21_v03_pilot_audit.md`:
- `proposed_relationships` volume and names; concept density per 1k tokens vs the v0.2 corpus baseline; quarantine rate; `evidence_grade` distribution; fraction of Claims the model graded `platform_official` from non-platform sources (a grading-confusion signal).
- **Schema patch rule (decide, do not escalate):** a proposed relationship name appearing ≥3 times across ≥2 pilot documents with grounded spans is appended to schema as v0.3.1 with the same mechanism Phase 1 used; otherwise it stays in `proposed_relationships`. Log each decision. Re-run Phase 1 tests after any patch.
- **STOP conditions:** quarantine rate > 0.15 on any pilot doc, or `evidence_grade` missing on > 10% of Claims. Halt, write audit, skip Phase 5, proceed to Phase 6 with the pilot extractions only.

## Phase 5 — Bulk (serial; rate-gated)

- Run the standard runner over the remaining manifested kernel docs, same model config, resume keyed as today.
- **Dry-run rate:** extract the first document alone, record wall-clock and tokens, compute projected time for the remaining set. If projected time exceeds the AUTH-5 window, order the remaining docs by inclusion-rule clause priority (a, b, c, d, e) then by char count ascending, and extract in that order until the window is spent. Record the ordering and the cut point.
- Per-doc build metrics recorded as today; any doc whose quarantine rate exceeds 0.15 is flagged in the RESULT, not re-run.
- Unpriced-call warnings are recorded as **cost UNKNOWN**, never as 0.

## Phase 6 — Projection, gates, quality instrumentation (serial)

1. `build_projection.py`, then `run_baseline_gates.py`. **Thresholds frozen; fails are findings.** Expect grounding_zero_ungrounded = 0; if not, STOP, write the gate report, do not touch the log.
2. Dated gate report `docs/research/2026-08-21_v03_kernel_gate_report.md` with deltas vs the Phase 0 baseline.
3. **Quality monitors (new, required):** add to `scripts/` (or extend `run_baseline_gates.py`) per-document control metrics persisted under `corpus/staging/metrics/`: concept density, quarantine rate, evidence-grade distribution, `proposed_relationships` rate. Compute the v0.2-corpus baseline mean and SD for density and quarantine so future runs have control limits (DD-005 promotion-gate metrics). **Positive control required:** seed one synthetic known-bad extraction event in a scratch copy of the log (ungrounded span, missing evidence_grade) and show each monitor fires; record the mutation test in the sub-RESULT. A monitor that has not fired on a seeded bad is not verified.
4. Tests for the monitors added to `tests/`.

## Phase 7 — Documentation closeout (parallel with Phase 5 where it does not depend on results)

- `README.md`: scope paragraph updated for the machine-visibility arm, v0.3 node types listed, evidence-grade explained in two sentences.
- `docs/schema_v0.1.md` changelog entries for v0.3 (and v0.3.1 if Phase 4 patched).
- `docs/design_decisions.md`: DD-009, DD-010 (from Phase 1), plus **DD-011** recording AUTH-4 (extent rule for oversize specs) and **DD-012** recording the continuous-currency requirement: platform and standards documents carry `as_of`, refetch produces `supersedes` edges via new manifest events, and a harvester (future task, not this one) keeps the kernel current. DD-012 is a requirement record, not an implementation.
- Restore `controls.yaml` per AUTH-3 and record sha256 match.

## Out of scope (do not do)

- Git commits — leave uncommitted per burn convention; operator commits.
- Any re-extraction of the existing 71 documents.
- Neo4j serving layer, FastMCP verbs, HF deploy (separate task).
- Concept dedup, Construct promotion, definition-conflict adjudication (separate task, after this kernel lands).
- Manifesting anything from `refetch_candidates.jsonl` (the 721 pre-existing cites candidates).
- Threshold retuning, model config changes, forager activation.
- Editing this task file.

## Completion — `cc_tasks/2026-08-21_v03_visibility_kernel_RESULT.md`

Assembled by the orchestrator from the phase sub-RESULTs. Must contain: phase status table; test counts baseline → final; schema version and template version stamped in events; candidate register summary; manifest adds count; pilot audit headline; bulk docs extracted / manifested-not-extracted with the cut point and measured rate; gate table with deltas vs Phase 0; monitor mutation-test results; token totals with cost recorded as UNKNOWN where unpriced; `controls.yaml` sha256 before/after; every discrepancy between this task's stated numbers and live numbers, reported and not reconciled.
