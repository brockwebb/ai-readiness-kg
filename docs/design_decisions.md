# ai-readiness-kg — Design Decisions

**Date:** 2026-07-02
**Status:** Living record. One entry per decision, dated. Append, don't rewrite.

---

## DD-001: Standalone repo, own database, self-contained provenance

Separate repo at ~/GitHub/ai-readiness-kg. Own Neo4j database (`ai-readiness-kg`). Never merged with fss-policy-kg or housed in ai-readiness-fss (which has a zero-dependency invariant).

Self-containment rule: the manifest cites primary sources only. Duplication with fss-policy-kg (e.g. M-25-21 in both) is acceptable redundancy. The provenance chain must survive handing the repo to a stranger.

## DD-002: Discovery is not extraction

Wintermute and other internal systems may serve as discovery indexes: candidate lists, "what do I already have" scans. Parsed source text may be reused as content prep (parsing is provenance-neutral).

Extraction events are always native to this graph, run against the primary document, under this schema, recorded in this event log. No extraction results are imported from any other system, including provenance-clean ones. Reason: the event log is the audit trail; imported extractions have no native events, wrong schema, and an external dependency in the citation chain.

## DD-003: Manifest is the gate; harvesters feed staging only

Fully sighted manifest, same discipline as fss-policy-kg. Harvesters/foragers run continuously and dump finds into staging with capture provenance. A document becomes corpus only via an explicit manifest_add event carrying source provenance and inclusion rationale. No autonomous manifest writes at current maturity level (see DD-005).

## DD-004: Wintermute control-plane hook, loose coupling

The pipeline reads its operational switches from a local control file (controls.yaml): forage on/off, extract on/off, budget caps per work stream. External systems (Wintermute's circuit-breaker panel) may flip switches by writing that file. Nothing reaches inside the pipeline; the file is the entire interface. Operational infrastructure, not provenance — does not violate DD-001.

## DD-005: Autonomy ramp with SQC gates

Target working state is supervised autonomy (level 4): system forages, stages, extracts, and proposes manifest adds; human monitors metrics and reviews by exception.

Ramp:
- L2 (now): manual, one document at a time. Human runs each step. Purpose: tune prompts, validate schema, establish metric baselines.
- L3: batch operation. Human approves manifest adds and reviews quarantines; extraction runs unattended within budget.
- L4: system proposes manifest adds with rationale; human review is event-driven (metric out of control limits, quarantine spike, budget trip) or ad hoc.
- L5 (self-directed search expansion): aspiration, not commitment. Foragers may expand search parameters beyond initial config, but expansions are logged as proposals.

Promotion gate between levels: build metrics (concept density, quarantine rate, grounding-validation pass rate, dedup hit rate) stable within control limits over a defined run count. Metrics and limits defined at pilot; promotion is an explicit dated decision recorded here.

## DD-006: Extraction protocol decisions (see schema_v0.1.md §5)

- Whole-document single-pass extraction (Fable-class model) for standard-length documents. Segmentation dropped as a pipeline stage.
- Verbatim grounding retained as an output requirement; mechanical string-match validation, quarantine on miss.
- Concepts extracted first-class from event one, with a density metric. Direct response to the fss-policy-kg thin concept layer (~13%).
- proposed_relationships staging block: controlled schema-expressiveness valve. Response to the Wintermute bridge-ensemble lesson (label vocabulary, not rater disagreement, was the bottleneck).
- Cheap models (Haiku-class) reserved for cleanup/validation jobs, not primary extraction.

## DD-007: Budget and infrastructure

Personal project on Claude Max OAuth for now. Never ANTHROPIC_API_KEY. USAi is a possible later fork path for a Census-internal variant; keep provenance clean enough that such a fork requires no archaeology.

## DD-008: Event log sharding from day one

Event log sharded by ingest batch (events/batch-NNN.jsonl or equivalent) from the first event. Response to fss-policy-kg's 53.8 MB single-file events.jsonl hitting GitHub limits.

## DD-009: One graph — the machine-visibility literature is part of this graph (schema v0.3)

**Date:** 2026-08-21. Recorded from AUTH-1 in task `2026-08-21_v03_visibility_kernel`.

The machine-visibility / machine-actionability literature (SEO, GEO/AIO, web standards, platform crawler behavior, federal digital guidance) is part of *this* graph, not a sibling repo. Reason of record: the graph's first question is which readiness definitions exist and where they conflict; definitions that include discoverability conflict with definitions that stop at institutional readiness, and that conflict is only observable inside one graph. Second reason: rename-of-old-science ("AIO" = crawlability + structured data + content clarity) is provable only via Concept aliases / `subtype_of` / `extends` inside one graph. Wintermute's contamination lesson concerned unrelated projects under label isolation, not one project with two literatures.

Mechanism: schema v0.3, append-only (`kg/schema.yaml`, `docs/schema_v0.1.md` changelog). New node types `Practice`, `Tool`, `Platform`; new edge types `recommends`, `supported_by`, `implemented_by`, `consumes`, `applies_to`, `targets`, `supersedes`; `Document.source_type` gains `practitioner`. Document scope remains a property, not a partition (schema §2 note) — no label isolation, no second database. The append-only invariant is machine-checked (`tests/test_schema_append_only.py`, v0.2 catalogue frozen in the test).

## DD-010: Evidence grading on Claims

**Date:** 2026-08-21. Task `2026-08-21_v03_visibility_kernel`, Phase 1.

**Why it exists.** The machine-visibility literature mixes platform operators documenting their own behavior, peer-reviewed experiments, practitioners with measured results, practitioners with unsupported assertions, and inference. The diagnostic guide built from this graph must be able to cite the *strength* of the evidence behind each recommendation (a `Practice` is `supported_by` a `Claim`; the Claim's grade is the strength of the recommendation), and platform-official claims must be separable from practitioner assertions — otherwise "Google says X" and "a blog says Google does X" collapse into the same node type and the guide cannot tell the reader which it is relying on.

**The enum** (`Claim.evidence_grade`, `kg/schema.yaml` `property_values`), in descending strength:

1. `peer_reviewed_experiment` — published, peer-reviewed experimental result.
2. `platform_official` — the platform operator's own documentation or statement about its own behavior (only when the source *is* that operator).
3. `measured_practitioner` — practitioner result with a disclosed method and data.
4. `practitioner_assertion` — practitioner statement with no disclosed method.
5. `inference` — reasoned from other evidence, not observed.

**Rules.**
- Required on every Claim extracted under schema v0.3 and later. Absent, empty, or outside the enum ⇒ the Claim is quarantined at parse (`kg/extraction/parser.py`, driven by `required_properties` / `property_values` in `schema.yaml` — the lists are never duplicated in code). Edges that reference the quarantined Claim fail endpoint resolution and are quarantined with it.
- The diagnostic guide cites the grade alongside every recommendation it derives from the graph. A recommendation whose best supporting Claim is `practitioner_assertion` or `inference` is presented as such, never laundered into a stronger statement.
- Claims extracted under v0.1/v0.2 (the 71-document corpus) carry no grade; they are not re-extracted for this (schema §6: targeted re-run, never blanket). Their absence of a grade is a known, dated gap, not a quarantine condition retroactively applied.
- Grading confusion is a measured pilot signal (task Phase 4: fraction of Claims graded `platform_official` from non-platform sources).

## DD-011: Stated-extent rule for oversize specifications

**Date:** 2026-08-21. Recorded from AUTH-4 in task `2026-08-21_v03_visibility_kernel`.

Standards specifications that exceed the runner's `MAX_DOC_CHARS` (250,000) are manifested at a *stated extent* — the normative core, or the steward's own primer/summary document — with `extent_note` and the excluded-sections list recorded in the `manifest_add` event (`acquisition.extent_note`, `acquisition.excluded_sections`). This is the same move as the §515 Data Quality Act re-acquisition (manifested at corrected extent, 2026-07-17): the citable unit is the part of the document the graph actually read, and the manifest says so.

No blanket `OVERSIZE_ALLOW` additions. A document that would need a whole-document clearance above 250K is skipped, registered in `refetch_candidates.jsonl` with reason `oversize_needs_clearance`, and left for a follow-on decision. Truncation remains forbidden (grounding integrity): an extent is a *named* subset chosen before extraction, never a character cut. The kernel run profile (`scripts/run_profiles.yaml: kernel_v03`) therefore carries an empty allowlist; the v1 profile's allowlist is preserved as the ledgered history it is.

## DD-012: Continuous currency for platform and standards documents (requirement record)

**Date:** 2026-08-21. Task `2026-08-21_v03_visibility_kernel`, Phase 7. **Requirement, not implementation.**

Platform documentation (search engines, crawlers, CDN bot controls, AI-retrieval vendors) and living standards change without notice, and a claim grounded in a page as it stood on one date is only citable *as of* that date. Therefore:

1. Every platform-official and standards document in the manifest carries `as_of` (from the page or publication date, else the HTTP `Last-Modified`, else `null` with a note — never fabricated). Recorded in `acquisition.as_of` on the `manifest_add` event.
2. A refetch that yields new content is a **new manifest event** under the same doc lineage and produces a `supersedes` edge (Document → Document, schema v0.3) from the new capture to the old. The old capture's extraction stays in the log; the projection follows the newest (the same overlay pattern as `extraction_superseded`, which is about extraction runs, not documents).
3. A harvester (future task — not this one) keeps the kernel current on a declared cadence, writing to staging and proposing manifest events; it does not manifest autonomously until DD-005 promotes the level. The kernel list (`scripts/kernel_list.yaml`) is the input it re-walks.
4. The diagnostic guide cites `as_of` with any platform-behavior claim.

Until (3) exists, currency is manual: the kernel is as current as its last scripted harvest, and the RESULT of each harvest records the `as_of` per document.

## DD-013: TEVV pre-registration; the same-family judge limitation

**Date:** 2026-08-22. Task `2026-08-22_kernel_tevv` (Seldon de7ae80b).

Extraction validity is measured, not assumed, on three pre-registered axes: **test-retest stability** (Cohen's κ on item presence per node type, Jaccard on grounded-span sets; Landis & Koch 1977 "substantial" floor 0.61 / 0.70), **faithfulness** (judge-scored entailment of each item by its own grounding span; ≥ 0.90 pooled, ≥ 0.85 per stratum — no looser than the admission floor implied by the 0.15 quarantine ceiling), and **evidence-grade calibration** (`platform_official` precision against `Document.is_platform_operator`; `peer_reviewed_experiment` precision against `source_type = academic`; ≥ 0.90). Thresholds live in `dixie_evidence.yaml: tevv_gates`, written before any data, with the task file as source; realized values are recorded beside them and a FAIL is a finding that triggers investigation or a follow-on task, never a threshold change.

Mechanics that keep the measurement out of the graph: re-extractions go to a **tagged shard** (`events/batch-008_tevv_retest.jsonl`), flagged `purpose: tevv_retest` on every event; `kg/eventlog.replay()` excludes tagged shards by default and `build_projection.py` skips the purpose flag as a second guard. Re-extraction pins the *original* model, prompt-template version and schema version per document, read from its events (pinned copies in `scripts/tevv_pins/`, sha-verified against git on every run).

**Known limitation, recorded not solved:** the faithfulness judge is the same model family as the extractor (Opus 4.8 judging Opus 4.8 output). Shared blind spots inflate agreement. The 40-item human calibration subset (`corpus/staging/metrics/tevv_human_subset.jsonl`) exists for that reason; judge-only precision carries status `uncalibrated_pending_human` until the operator fills `human_label`, after which a follow-on recomputes judge–human agreement. The judge prompt is versioned (`kg/extraction/judge_template.md`, `judge_version`) and stamped on every judgment.

**Statistic note:** κ on item presence uses the union of both runs as the universe (an item absent from both runs does not exist), so there is no both-absent cell; the value is the chance-corrected agreement over the union, reported alongside Jaccard/Dice-style overlap so readers can see both.

## DD-014: `Document.is_platform_operator` — the rule and why it is a harness annotation

**Date:** 2026-08-22. Task `2026-08-22_kernel_tevv`, Phase 0. Schema v0.3.1 (append-only).

The kernel RESULT's grading-confusion signal measured `platform_official` Claims against *harvest clause b*, and the DAP guide (GSA, federal clause) showed the conflation: GSA operates DAP. The graph needs a document-level fact — **does the issuing organization operate a machine consumer** (search engine, crawler, CDN / bot-control product, LLM retrieval system)? — independent of how the document was harvested or extracted.

**Rule:** `is_platform_operator = true` iff the manifest `authors` name an organization in the operator lexicon `scripts/platform_operators.yaml`, each entry stating *what it operates* (seeded from the `operator` property of the Platform nodes the extractor asserted: Google, Microsoft/Bing, OpenAI, Anthropic, Perplexity, Cloudflare, Akamai, GSA/data.gov, AWS; plus sitemaps.org and IndexNow as operator consortia). Ambiguous GSA cases resolve **true** (task ruling). Deliberate negatives are listed in the same file with reasons (Census Bureau: API, not a platform; Schema.org CG; IETF; Zyte; standards and policy bodies; vendors/tool projects).

**Why an annotation, not an extraction:** the value is a property of the *issuer*, not of the text; an extractor grounding it in a span would be guessing. It is emitted by `scripts/annotate_platform_operator.py` as `document_annotation` events (`events/batch-007.jsonl`, rule-versioned, rationale per doc) and projected onto the Document node through a property whitelist. Changing the rule = a new rule version and new events; prior annotations stay in the log.

**Realized 2026-08-22:** 30 true / 104 false over 134 documents (`docs/research/2026-08-22_tevv_platform_operator_decisions.md`).
