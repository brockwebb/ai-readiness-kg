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

## DD-015: Faithfulness probe — atomic decomposition, multi-rater aggregation, pre-registered repair decision

**Date:** 2026-08-22. Task `2026-08-22_faithfulness_probe` (Seldon 68426971). Follows DD-013.

**Problem.** TEVV (DD-013) scored faithfulness 0.535 on n=200 with a strict item-level judge, and a second same-family rater agreed (0.525 on n=40). The sidecar notes attributed most failures to *capture* and *scoring* defects (a span that locates an item but does not carry its attributes; truncated spans; document-level attributes a span cannot hold) rather than fabrication. n=40 cannot size those classes.

**Prior art adopted.** Atomic-fact decomposition before judging — FActScore (Min et al. 2023), RAGAS faithfulness (Es et al. 2023), AlignScore (Zha et al. 2023): an item is only as faithful as its least-supported atomic fact, and classes of failure are legible only at that grain. LLM-judge biases — position and verbosity (Zheng et al. 2023, MT-Bench), self-recognition/self-preference (Panickssery et al. 2024): hence randomized batch order with `batch_position` recorded, a second model, and a cross-family lane. Batch-prompting effects (Cheng et al. 2023): hence the batch-vs-single κ calibration that *chooses* the batch size (κ ≥ 0.80 → 10; 0.60–0.80 → 5; else 1). Multi-rater aggregation with latent truth and per-rater confusion — Dawid & Skene (1979), MACE (Hovy et al. 2013): implemented with `crowd-kit` DawidSkene at fact level; per-rater estimated confusion matrices are reported, not assumed. Wilson (1927) intervals for proportions.

**Decision rule (binding on the machine, written before data).** F = estimated share of atomic facts in class `fabrication`, excluding `doc_level_attribute` and `grade_misassigned` from the denominator, per stratum and pooled, Wilson 95% CI. F_upper < 0.05 in every stratum → repair path only; F_lower > 0.10 in any stratum → that stratum `reextract_required` (repair proceeds elsewhere); otherwise repair for all strata and a post-repair re-judge decides.

**Capture defect vs fabrication.** The six classes separate *what the document supports but the span failed to carry* (`span_truncated`, `subject_dropped`), *what the extractor filled without support* (`filled_attribute`), *what the scorer should not have asked a span to carry* (`doc_level_attribute`, schema v0.3.2 `span_entailable: false`), *grading* (`grade_misassigned`), and *fabrication* (absent from span AND from the ±400-char window). Only the last is evidence against the extractor's honesty; the others are repairable by overlay (span re-location, attribute nulling) and by the span-coverage invariant (`grounding.covers`, parser reason `span_partial`, config `extraction_gates.enforce_span_coverage`), which was mutation-tested before any live use and is applied to probe items only in this task.

**Schema v0.3.2** adds the per-attribute `span_entailable` map (the scorer's contract with the extractor) — append-only.

## DD-016: Judge attribution — PROV-O agents, ORCID for persons

**Date:** 2026-08-22. Task `2026-08-22_faithfulness_probe`.

Every judgment is an event (`judge_label`, non-graph shard `events/batch-009_probe_judge.jsonl`, `purpose: probe`) carrying a PROV-O agent block: `agent.type` is `prov:SoftwareAgent` or `prov:Person`; software agents are identified by model id, the model version string the CLI envelope reports, the sha256 of the judge prompt template, the template's `probe_judge_version`, and the call/session id; persons are identified by ORCID only — the value is whatever the person writes in the file, never inferred or fabricated (an absent ORCID is recorded as absent). Batch context (`batch_id`, `batch_position`, `batch_size`) rides on every label so position effects remain measurable after the fact. Raters of other families ingested from operator chat exports are `prov:SoftwareAgent` with the model name the operator records; absent → `unknown_crossfamily`, flagged. The existing TEVV sidecar rater is ingested as `claude-desktop-fable5`, a coarse (item-level) software agent. Aggregation treats every rater as a column in the Dawid-Skene confusion model; no rater is privileged by construction.

## DD-018: TrustGraph benchmark — NOT EVALUATED; the chat-level rejection stands untested; SHACL gate candidate delivered

**Date:** 2026-08-23. Task `2026-08-23_trustgraph_benchmark` (Seldon b6900da4). (DD-017 is reserved by the concurrent `2026-08-23_whole_graph_repair` task.)

**Outcome: NOT EVALUATED.** The task pre-registered a decision rule (Adopt-evaluate vs Harvest-components on F/C/R, both extractors on Gemini Flash) and bound the run to "the existing Google AI Studio credentials", with the rule *"if no Google credential is configured, STOP at Phase 1 … do not substitute another provider."* The premise is false: the Gemini key was revoked in the Google console on 2026-08-13 after a spend incident (`~/.wintermute/.env` lines 5–8; `~/.wintermute/docs/decisions/2026-08-13_google-spend-incident.md`, "vendor retirement = credential revocation"). The only copy still reachable is a stale process-inherited value whose sha256 matches the revoked fingerprint (`docs/research/2026-08-23_tgbench_phase1_blocker.md`). The Anthropic-keyed path is forbidden by DD-007 and by the task. No substitution was made. Phases 1, 3, 4, 5 did not run; deploy time 0; friction numbers not measured.

**Decision status.** The decision rule was therefore **not applied**. The 2026-08-22 chat-level rejection of TrustGraph (infrastructure weight, missing validity machinery) **stands, and stands UNTESTED** — it is not confirmed by this task, and nothing here should be cited as evidence for or against TrustGraph's extraction quality. The probe's motivating numbers (ours: F=0.079, 52% capture defects) remain unanswered by a comparator.

**What was delivered.** (1) `benchmarks/trustgraph/schema_to_owl.py` → `airkg_schema.ttl`: 12 classes, 23 object properties, 33 datatype properties, fidelity-checked by re-parse; recorded limitation that OWL domain/range loosens the schema's index-pairing to a cross product. (2) `schema_to_shacl.py` → `airkg_shapes.ttl`: the exact pairs as `sh:class`/`sh:or`, illegal edge types per class as `sh:maxCount 0`, enums as `sh:in`, `Claim.evidence_grade` as `sh:minCount 1`. (3) `export_projection_rdf.py`: event log → RDF with the same overlays as `build_projection.py` (imported, not copied), doc-scoped IRIs. (4) Gate candidate `shacl_conformance`: `scripts/run_shacl_gate.py` + `dixie_evidence.yaml::shacl_gate` (`enabled: false`, threshold 0 unknown-class violations). Realized 2026-08-23: 2,127 violations, all in two known classes (1,200 dangling `cites` to never-manifested Documents; 927 pre-v0.3 Claims without `evidence_grade`), 0 unknown; positive control (one Concept→Concept `defines`) fires the gate. Nine tests in `tests/test_shacl_gate.py`.

**Revision mechanism — exact re-run trigger.** This DD is superseded by a `2026-MM-DD_tgbench_decision.md` the moment all three hold: (a) a Google AI Studio key exists on disk in `~/.wintermute/.env` as `GEMINI_API_KEY` (not process-inherited), with its sha256 ≠ `3ee221ca4626…` and a spend cap declared in `controls.yaml`; (b) the standing rule in the spend-incident decision is satisfied for the new key (a revocation path exists before first use); (c) `cc_tasks/2026-08-23_trustgraph_benchmark.md` is re-dispatched unchanged from Phase 1 with the 2 h time-box — Phase 2's deterministic artifacts and Phase 6 are reused, not regenerated, unless `kg/schema.yaml` has bumped. Until then the rejection is a working assumption with a measured zero-evidence base, and Harvest-components is partially done regardless: the SHACL piece is in.

## DD-017: Whole-graph repair — counts, methods, the deterministic ceiling, and the success-measure outcome

**Date:** 2026-08-23. Task `2026-08-23_whole_graph_repair` (Seldon 803b024f). Generalizes the probe's Phase 7 (DD-015) from 400 items to the graph, excluding the three `reextract_required` strata.

**Detection (mechanical, both epochs, 8,858 nodes):** 5,277 span-partial (60% of nodes; the span locates the item but does not cover its text) and 7,875 unsupported `span_entailable` attributes (description 4,659, aliases 1,430 — free text paraphrased by the extractor). The filled share is ~2.9× the probe's judged share: a substring rule cannot credit paraphrase the way a judge does. Applied as pre-registered; recorded as a known over-detection on free-text attributes.

**Relocation:** deterministic (exact / NFKC substring of item text in the document) resolved **1,321 of 5,277 — the deterministic ceiling is 25%**, because 75% of item texts are paraphrases of the source, not quotes. Model-assisted relocation (Haiku 4.5, DD-006 cleanup class; one directed call; returned passage verified as a verbatim document substring, whitespace-insensitively because PDF text carries mid-word spaces the model silently heals; the stored span is the document's own slice) ran on 915 of the 3,956 forwarded items before the operator stopped it for spend: **555 relocated, 360 honest NONE** (`span_unrepairable` annotation) — a 61% hit rate at ≈36K tokens/call, almost entirely the CLI harness's cached system prompt. The remaining 3,041 are resumable (`scripts/repair_relocate.py --phase 3 --shard I/N`) under the declared daily cap, which the script now enforces via the control plane.

**Nulling:** 5,270 `attribute_nulled` overlays (plus the probe's 79); 60 entries resolved because the relocated span now carries the value; 2,545 deferred until their relocation settles. Overlays only — the assertion events are untouched; the projection applies overlays last through an attribute whitelist.

**Enforcement:** `extraction_gates.enforce_span_coverage: true` for future extraction runs (parser quarantines `span_partial`); not retroactive — historical items are repaired by overlay or annotated `span_unrepairable`, never quarantined by projection (regression tests).

**Pre-registered success measure:** 150 repaired items (50 per repair type, seed 20260823) decomposed and judged under the probe protocol (two raters, batch 10, Dawid-Skene): **strict fact-level entailment 199/216 = 0.921 [0.878, 0.950] ≥ 0.85 — PASS**; per type deterministic 0.915, model-assisted 0.897, nulled 0.955; fabrication 0/216. The repaired items are at the probe's entailed rate ceiling for the whole graph (43%) more than doubled.

**What this does not fix:** the three `reextract_required` strata; paraphrased items whose relocation has not run; descriptions nulled that a judge would have accepted (the over-detection above) — re-grounding those is re-extraction's job, not repair's.

## DD-019: The unit of model dispatch is the batch, and the cache prefix is a session

**Date:** 2026-08-25. Task `2026-08-23_batched_repair_resume` (Seldon a2d3fb42).

**Measurements that force the rule.** Per-call fixed overhead through the Claude Code CLI: ~111K-token floor observed 2026-08-21 (pilot-era single calls) and ~36K/call observed 2026-08-23 (Haiku relocation, one item per call) — the harness system prompt dwarfs the payload for cleanup-class work. Single-item dispatch multiplies that overhead by the worklist.

**The rule.** (1) Cleanup/adjudication calls dispatch batches (target 40, floor 25, ceiling 50) with a strict JSON-array contract; a parse failure gets one retry with the batch split in half, and individually-valid rows are salvaged from a malformed array rather than discarding the batch. (2) No tools on such calls. (3) The shared prefix must actually be *cached*: separate `claude -p` invocations do NOT share a mid-user-message prefix (measured 2026-08-25: three same-document calls, 0 prefix reuse, ~71K cache-write each). The working mechanism is **one headless session per document, batches as resumed turns** (`claude -p --resume`) — the document rides in the first turn and becomes cached conversation prefix (measured: reads dominant from call 2, 53–60K read vs ~7K write). (4) The cache-read ratio is checked on the first 3 calls of every run; not dominant → STOP and fix the prefix, never burn the worklist on a busted cache. (5) A per-phase token ceiling is declared up front and enforced in-process. **Defect recorded:** this task implemented its 12M ceiling per shard process, so two workers spent 22.0M — the ceiling must be enforced against a shared counter (the control plane), not process-local state. (6) 2% planted decoys per batch with a rolling acceptance window; in this task the decoy control caught three real defects (array parse loss, id-echo mismatch, malformed-row array kill) before any bad write.

## DD-020: Projection nodes key on (document, item); cross-document identity belongs to dedup

**Date:** 2026-08-25. Same task, Phase 1.

600 of 6,988 extractor-assigned item ids recur across documents (`c_ai_readiness` in dozens of them); keying the Neo4j loader on bare item id fused them into single nodes — silent cross-document merging that no adjudication ever approved. Every non-Document node now keys on the composite `doc_id::item_id` (both parts kept as properties); edge endpoints resolve to document scope only for manifested doc ids and adjudicated aliases; everything else stays scoped to the asserting document, including dangling doc-like ids. Effect measured: Concept nodes 3,537 → 4,675. The loader never decides that two documents mean the same thing by accident of id collision — that judgment is concept dedup's, made explicitly, with provenance (the task already on the critical path).
