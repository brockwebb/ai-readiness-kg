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

## DD-021: TrustGraph benchmark v2 — measured; verdict harvest-components (supersedes DD-018's not-evaluable)

**Date:** 2026-08-26. Task `2026-08-23_trustgraph_benchmark_v2` (Seldon 36a5c0e1). DD-018 recorded the v1 benchmark as NOT EVALUATED (revoked Google credential). Its re-run trigger was satisfied differently: both extractors ran the **same pinned Claude model through the same CLI path** — architecture the only varied factor — via a custom `claude-cli-completion` backend implementing TrustGraph's `LlmService` contract (fork branch `claude-cli-backend`, unit-tested against a stub CLI; deploy 16.8 min, backend ~17 min — the v1 "infrastructure-weight" objection did not survive measurement either).

**Result (5 documents, `docs/research/2026-08-23_tgbench2_decision.md`):** TrustGraph's ontology-driven flow used 11.7× our extraction tokens (6.74M vs 0.58M; 168 calls vs 5 — chunked architecture), produced ~10× the typed items with coverage R = 0.33 of our admitted extractions, and fabricated at F = 0.126 [0.075, 0.204] against its own chunk evidence (edges 0.225) vs our probe-measured 0.079. **Pre-registered rule → harvest-components; no integration task.** Harvested: extraction-time ontology validation (their validator dropped 253 over-proposals — worth porting as a live gate next to our post-hoc SHACL), the demonstrated weakness of chunk-anchored provenance without entailment discipline (validates DD-015), and their ontology format's expressiveness losses (enumerated). Caveats on the face of the decision doc: our-side fact-level F on this run went unjudged at the 8M ceiling (consumed at 8.11M, 1.3% overshoot recorded); F_ours cited from the probe.

**The revision mechanism worked**: a chat-level architectural rejection (2026-08-22) was replaced by measurement within four days, at bounded cost, and the measured answer partially vindicated and partially corrected the original judgment.

## DD-022: Spend admission is preemptive and shared — reserve-then-settle on one flock-guarded ledger

**Date:** 2026-08-26/27. Task `2026-08-26_preemptive_spend_guard` (Seldon d2756bd1). Fixes the DD-019 §5 defect class.

**The defect (from the ledger, not memory).** Two incidents, one shape: `2026-08-23_batched_repair_resume` enforced its 12M ceiling as process-local state (`scripts/batch_repair.py` `TOKEN_CEILING`), so two shard workers jointly spent 22.03M; `2026-08-23_trustgraph_benchmark_v2` checked its 8M ceiling after each call returned and consumed 8.11M. Both checks were *reactive* (spend known only after dispatch) and *local* (per process). DD-017's "repair_relocate now enforces via the control plane" verified as `rbe.tokens_left() <= 0` — a between-calls poll of the *daily band* (shared file, but usage booked post-call): shared yet still reactive, and it never saw a per-run ceiling at all. Replaced.

**The design (prior art: reserve-then-settle admission control, the two-phase pattern of quota systems and connection/credit pools — named in the task, not invented).** One append-only ledger, `state/spend_ledger.jsonl`, is the truth for spend *admission*; `model_call` events remain provenance for the calls and are *reconciled* (`python -m kg.spend reconcile`), never merged. Every operation (`declare`/`reserve`/`settle`/`release` + refusal writes) holds an exclusive `fcntl.flock` for the whole read → compute → append — sufficient cross-process atomicity because fleet workers run on one machine. `committed(run) = Σ settle.actual + Σ outstanding reserve.estimate`; refuse iff `committed(run)+estimate > ceiling(run)` or `committed(day)+estimate > controls.yaml spend.daily_tokens` (55M — the control plane's declared extraction-circuit band, read 2026-08-27). Estimate = max(call-class floor from `controls.yaml` — cleanup 36K, extraction 111K, judge 36K, the DD-019 measurements — mean of the last 10 *measured* settles in the run). Per-run ceilings are never config: the runner declares them on the ledger from the dispatching task file's stated number (`--ceiling-tokens`, required, no default), so the ceiling and the spend that hit it sit in one auditable place.

**The choke point.** The guard lives in `kg/extraction/model_stub.invoke` beside the DD-007 API-key gate: reserve before `subprocess.run`, settle at the envelope's measured tokens after; a call that never dispatched (CLI unavailable) releases; a dispatched call with no measurable envelope (timeout, non-zero exit, unparseable, missing usage fields) settles *at the estimate*, flagged `settled_as_estimate` — conservative, never a content-derived guess. An undeclared run is refused — there is no unmetered path. Refusal is a clean stop (exit 0), the same contract as the STOP file. The process-local counters in `batch_repair.py`, `repair_relocate.py`, `run_bulk_extraction.py`, and `tgbench_ours.py` are **deleted, not disabled** — two mechanisms is how the 22M happened. (The TrustGraph-side backend under `benchmarks/trustgraph/` dispatches nothing through the stub — verified; the fork's backend is out of this repo.)

**Mutation evidence (tests/test_spend_guard.py, 8 tests).** With the reserve admission check disabled, 6/8 fail (near-ceiling refusal, 8-process oversubscription, overshoot-closes-door, daily-scope, release-capacity, and the 22M-shape replay — two workers on one declared 12M run stop at ≤ 12M + one floor, not 22M); the other two seeded faults fail under their own line-mutations (undeclared-run check disabled → test 5; reconcile equality forced true → test 7). All three mutations restored; suite green at 183.

## DD-023: The extraction unit is the chunk and the emission contract is anchors, not quotes — whole-document exhaustive-verbatim is retired

**Date:** 2026-08-27/28. Tasks `2026-08-27_pilot_finish` (ea7dd3bd), `2026-08-27_chunked_pilot` (64661f7a, paused 44/128). Verdicts: `2026-08-27_pilot_instrument_verdict.md`, `2026-08-27_edge_suppression_judge_verdict.md`, chunked-arm pause record in the task RESULT.

**Measurements that force the decision.** (1) Whole-document single-call under Opus 5: 108–158K-token outputs on 3/5 pilot docs, per-layer fallback re-paying the document input — single-pass docs 399–426K, fallback docs 866K–1,331K, extraction-only mean 785K/doc. (2) The same exhaustive-verbatim contract chunked: 65,637 settled/chunk (40 chunks, 2.63M), ~2.1× the whole-doc arm projected, with 33–46K-token outputs against 1,500-token chunks and 75.5% of emissions quarantined `span_partial` (much of it pypdf source damage — dropped characters). The cost driver is the contract, not the unit: the model is paid to re-type the source and the harness then discards three-quarters of it. (3) Pilot gate FAIL both strata under the whole-doc arm (Instrument F_upper 0.158 / faithful 0.292; semantic 0.607 vs 0.85). (4) Prior art, external and internal, predicted (1): extraction yield falls with chunk size (Edge et al. 2024); LLM RE degrades as output formatting dilutes attention (Gajo et al. 2026, arXiv 2604.08752); structure-aware chunking beats fixed-size for entity and relation extraction (ChemRxiv 10.26434/chemrxiv.10001546); Wintermute extracts chunk-level; production KG builders (Neo4j LLM Graph Builder, GraphRAG) emit name/type/tuple with provenance as a chunk pointer. None of it was cited at design time — see DD-025.

**The decision.** Whole-document single-call extraction and the exhaustive-verbatim emission contract are retired for all future runs (profiles retained on disk for the comparison record). The replacement contract (v0.3.7, `chunked_pilot` ADDENDUM-01 §2): section-bounded paragraph-integral chunks ≤ 1,500 tokens with 100-token overlap and breadcrumb; model emits `name + type + shortest-unique anchor (≤ 10 tokens)` per item and per Instrument attribute; the harness locates the anchor deterministically and derives the grounding span from the document text — the locate-at-birth guarantee is preserved and the span in the graph is document-derived, never model-typed; salience replaces exhaustiveness with one gleaning pass; `diversion_reason` closed list enforced in the parser (raw preserved); entity types reconciled at the deterministic-merge step. Source text re-converted with a layout-aware parser (Docling/MinerU class) before any further extraction — a validity pipeline validating against corrupted text quarantines faithful output. **The extractor model is an empirical question the judge answers** (Haiku and Sonnet arms pre-registered, same thresholds): the gate measures admitted-item faithfulness and is indifferent to which model produced the candidates.

## DD-024: Bulk semantic-edge extraction is closed; semantic edges are demand-pull adjudications

**Date:** 2026-08-27. Task ea7dd3bd, `2026-08-27_edge_suppression_judge_verdict.md`.

**Measurements.** Diverted semantic candidates 0.607 entailed (needs ≥ 0.85); ADDENDUM-06's `single_span` premise class 0.673; **live kernel-era edges 0.61 with 23/35 non-entailed facts outright fabrication**; §3a's co-occurrence proxy predicts faithfulness at 0.51–0.67 — the distant-supervision false positive (Mintz 2009; Riedel 2010). Two prompt revisions and a model change did not move the number. Chunked interim: 11 semantic edges over 10 chunks, `has_component` zero, endpoint typing unstable across chunks. Consistent with Wintermute G4 (extraction scored 0 vs embeddings baseline; RE fails at ~2× entity rate) and with the field (Wadhwa et al. 2023; Gajo et al. 2026; cross-chunk relations open — CrossAug 2026, arXiv 2605.28004).

**The decision.** No bulk semantic-edge extraction under any profile. Semantic edges (`has_component`/`subtype_of`/`consumes`/`extends`/`implements` class) enter the graph only by demand-pull adjudication: a named need pulls a candidate, retrieval surfaces evidence, the edge is adjudicated with its grounding span captured at adjudication time. Live kernel-epoch semantic edges carry a `faithfulness_epoch` flag and are never cited as validated. Standing revision trigger, pre-registered: if the v0.3.7 chunked pilot's semantic stratum clears F_upper < 0.10 / faithful ≥ 0.70 at pooled ≥ 20, this decision reopens with that verdict on the table — it does not reopen for any other reason. **[AMENDED 2026-08-29 per DD-026: the pooled minimum is 35, not 20 — at one fact per edge, F_upper < 0.10 is arithmetically unreachable below n = 35 (zero fabrications at n = 20 returns 0.1611). The trigger's substance is unchanged; 20 was an unsatisfiable number.]** G4-class disposition: this closes bulk extraction of these edge types, not graph relations as a concept.

## DD-025: Pilot registration requires a prior-art block — external literature and internal precedent

**Date:** 2026-08-27. Defect: the whole-document unit (schema §5) was written as a design rule with no prior-art search; the field's chunk-size measurements (2024), the RE-degradation mechanism (Gajo 2026), and this operator's own Wintermute G4 kill and "RE fails at 2× entity rate" finding all existed and none were cited. Cost of the miss: ~one week and on the order of 60M tokens across extraction, fallback turns, and repair of a layer that measured 0.61.

**The rule (methodology §7.1, binding on registration).** A CC task that registers a pilot — any pre-registered gate run — must carry a `prior_art` block with (a) external literature for the design's central choice and (b) an internal-precedent search across Wintermute and Seldon decision logs, with hits cited or the failed search described. A task without the block is refused at registration. "No prior art" is a claim requiring the search that failed, never a default. First task carrying the block: `2026-08-27_chunked_pilot.md`.

## DD-023 ERRATUM (2026-08-29): measurement (3), the faithfulness FAIL, is superseded — the decision stands on cost alone

**Date:** 2026-08-29. Task `2026-08-27_chunked_pilot` ADDENDUM-01 §1. Verdict:
`docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md`.

DD-023 cited four measurements. **Measurement (3) — "Pilot gate FAIL both strata under the
whole-doc arm (Instrument F_upper 0.158 / faithful 0.292)" — is withdrawn.** Re-judged through
the fixed probe (decompose 1.1.0, probe_judge 1.1.0) on the **same banked extraction, with no
re-extraction, the same two raters and the same pre-registered thresholds**, the whole-document
Instrument stratum measures **F = 0.0000 [0.0000, 0.0487], item-faithful 22/24 = 0.917 —
PASS**. The chunked arm measures F = 0.0000 [0.0000, 0.0458], item-faithful 30/30 = 1.000 —
PASS. The earlier FAIL was an artifact of how the probe cut the spans it judged (methodology
§6.3: 26/34 non-entailments were truncated `method` spans), not a property of the extraction.

**What this does and does not change.** Measurements (1) and (2) — 108–158K-token outputs, the
per-layer fallback, 785K/doc extraction-only mean, and 65,637 settled/chunk under the same
contract chunked — are untouched; they measure cost, not faithfulness, and they carry the
decision on their own. **DD-023 therefore stands, on cost.** It may no longer be cited as
resting on a faithfulness failure of whole-document extraction: on the evidence now in hand,
whole-document extraction is faithful at the Instrument stratum. The magnitude in (2) is also
sharpened by §1: on the one document with a complete chunked pass the ratio is **1.52x**, not
the 2.1x projected from a partial arm.

**Why this is an erratum and not a reopening.** The retirement was decided on the emission
contract's cost pathology, which §1 does not touch. Nothing here bears on it. The correction is
filed because a decision that cites a withdrawn measurement will be re-derived wrongly by
whoever reads it next.

**The generalizable defect.** A validity instrument mis-measured its own subject and produced a
FAIL that stood for two days and propagated into a design decision. `2026-08-27_pilot_instrument_verdict.md`
and the ADDENDUM-05 §2 verdict are superseded for comparison purposes, not retracted. Standing
consequence: **a gate verdict may not be cited in a design decision until the instrument that
produced it has been mutation-checked against a known-good sample** — the same positive-control
discipline already required of monitors (methodology §7.5), extended to the judge.

## DD-026: A pre-registered precondition must be consistent with the threshold it gates

**Date:** 2026-08-29. Task `2026-08-27_chunked_pilot` ADDENDUM-01 §1.

**Measurement.** The pilot pre-registered `F_upper < 0.10` with a precondition of `pooled >= 20`
items per stratum. For `semantic_edge`, `probe_decompose` emits exactly one fact per edge, so
n_facts = n_items. Under the aggregator's Wilson 95% interval a **perfect result — zero
fabrications — returns F_upper = 0.1611 at n = 20** and 0.1546 at n = 21. The minimum n at
which the threshold is attainable at all is **35**. Both arms' semantic strata landed at exactly
20 and 21: precondition satisfied, gate unreachable. A stratum sampled at exactly the
pre-registered minimum could only ever FAIL.

**The rule, binding on registration.** A pre-registered gate must declare a precondition that is
**derived from** its threshold and its interval method, not chosen independently of them. For a
one-sided upper bound the derivation is the binomial bound with zero events (Louis 1981; Hanley
& Lippman-Hand 1983 — the rule of three, of which Wilson is the exact form); it is arithmetic,
and a task that states a threshold already implies its own minimum n. A registration whose
precondition is below that minimum is **refused at registration**, because it can only produce
uninformative FAILs and the spend that buys them.

**Applied, not retrofitted.** The 20 in this pilot is not raised after the fact — the strata it
gated were recorded GATE UNREACHABLE and not judged, which is what ADDENDUM-01 §1 already
required of a sub-minimum sample. The rule binds the NEXT registration, including the v0.3.7
pilot's semantic stratum, whose reopen trigger in DD-024 ("clears F_upper < 0.10 / faithful >=
0.70 at pooled >= 20") **must be read as pooled >= 35** to be satisfiable at one fact per edge.

## DD-023 ERRATUM 2 (2026-08-29): re-conversion does not repair the `span_partial` class it was prescribed for

**Date:** 2026-08-29. Task `2026-08-29_corpus_t0_t1_substrate` §1.1. Evidence:
`state/t1_fidelity_diff.json`, `scripts/t1_fidelity_diff.py` (`named_instance_check`).

DD-023 measurement (2) attributed the chunked pilot's **75.5% `span_partial` quarantine rate**
to "pypdf source damage — dropped characters", and ADDENDUM-01 §2.5 prescribed re-converting
the corpus with a layout-aware parser as the fix. The whole corpus has now been re-converted
with Docling and the named instance re-tested as a positive control.

**Result: both converters extract the identical truncated token from the same bytes.**
`Heterogeneous Euclidean-Overlap Metri` — the missing `c` that DD-023 cites by name — appears
in pypdf's output *and* in Docling's. The character is absent from the PDF's own text layer.
Re-conversion cannot repair this class, and no converter choice will.

**What still stands.** Docling earns its place on other grounds and remains the T1 converter:
on the 5-document fidelity sample it recovers 4–24% more text than pypdf (169,576 vs 163,016
chars on the 360-degree survey; 127,424 vs 102,301 on the MITRE model) because it reconstructs
tables, headings and reading order that pypdf flattens or drops. That is a real gain in
retrievable structure. It is not the gain DD-023 claimed.

**What does not stand.** Any expectation that the v0.3.7 pilot's quarantine rate will fall
because the source was re-converted. The `span_partial` diagnosis needs re-deriving from the
quarantine records themselves, separating (a) genuine PDF text-layer loss, which no pipeline
step can fix and which must be handled by admitting a better copy — the operator pickup list
exists for exactly this — from (b) the model quoting a fragment cut mid-noun-phrase, which the
v0.3.7 anchor contract does address. Those two were merged under one cause and are now known
to be different problems. **Nothing in DD-023's decision changes**: the emission contract, not
the converter, was always the cost argument, and ADDENDUM-01 §1 already showed the
faithfulness argument was an instrument artifact (ERRATUM 1). This erratum removes the third
leg — the fidelity remedy — from the same decision, which now rests on cost alone and on
nothing else.

Generalized as methodology §7.8: before naming a component as the cause of a defect, run both
candidates on the same bytes.

## DD-027: Admission is not a request — extraction is queued by explicit, prioritized events

**Date:** 2026-08-31. **Task:** `cc_tasks/2026-08-27_extraction_queue.md` + ADDENDUM-01
(binding; the addendum renumbered this from the base file's DD-023, which was already taken).

**Decision.** A document being in the corpus and a document being *worked on* are two different
facts, recorded by two different events. `manifest_add` admits; `extraction_request`
{document_id, priority, requested_by, reason, profile, superseding} asks for work at a
priority, under a named sha-pinned profile; `extraction_withdrawn` cancels. Both are appended
to `kg/schema.yaml` as v0.3.5 `event_types` (the file's first event-type block; it previously
catalogued only nodes and edges).

**Why.** Curation pipelines that work at scale keep the stages apart — Wikidata's
proposal → review → ingest, UniProt's triage → curate. That separation is what lets spend
follow priority instead of arrival order. Before this, worklists were built ad hoc in the
runner and in each burn task's lanes, so "what runs next, and why" had no answer that survived
the session that decided it.

**Consequences, binding.**

1. **No worklist may be built from a list that is not on the ledger.**
   `run_bulk_extraction.py` derives its worklist as
   `included ∧ (queued ∨ (stale ∧ superseding)) ∧ ¬skipped_oversize`, ordered by priority.
   `--docs` remains as an operator override *and emits the requests it ran on*, so the reason
   is on the log. `--no-queue` exists as an escape hatch for a projection defect and says on
   the run that nothing justifies its worklist.
2. **`extraction_state` is derived, never stored as truth** — recomputed from the event log
   plus the spend ledger on every projection, into Neo4j `Document` properties and the SQLite
   bundle's `extraction_queue` table. Delete both and they rebuild.
3. **The pinned profile is read at projection time, never captured.** Flipping the pin flips
   `extracted` → `stale` with no code change (ADDENDUM-01 §4). The production profile moved
   twice while this task was open; a held pin would have kept reporting documents as extracted
   under something that had stopped being current.
4. **Preconditions are enforced at emit, and a refusal is a refusal.** A request for a
   document the manifest has not admitted, or against a profile that is not sha-pinned, raises
   with the reason and writes no event. Queueing future work against a prompt that can drift
   is how a burn silently changes instrument mid-flight.
5. **An extraction's profile is resolved, never guessed.** Legacy events record only
   `corpus_epoch`, and several profiles can share one. Where `prompt_version` cannot
   disambiguate, the profile is reported unknown *and flagged ambiguous* — because a guessed
   profile silently decides `extracted` versus `stale`.

**Scope.** This decides how work is *selected and recorded*, not how it runs. Prompts, gates,
thresholds and the extraction pipeline are untouched.

## DD-028: A gate's unit must be measurable by the instrument that validates it

**Date:** 2026-08-31. **Task:** `cc_tasks/2026-08-30_bulk_extraction_v038.md`.
**Cites:** `cc_tasks/2026-08-30_ground_truth_yield_floor_RESULT.md` (task 35094dc4); extends
DD-026 (a precondition must be consistent with the threshold it gates).

**Decision.** Every registered gate states its **unit** and names the **instrument** that
measures that unit. A gate whose unit its validating instrument cannot measure is refused at
registration, not discovered on the data.

**Why.** The chunked pilot chased an admitted-yield floor of 45.23 items/chunk for three arms
across four sessions. The number counted *nodes plus edges*; the ground-truth rubric that was
supposed to validate it annotates *node items only*. The two are not comparable, so no arm
could have "met" the floor in the sense anyone intended, and the three-arm chase (0.347 →
0.537 → 0.560) was measuring a gap the instrument could not see. The re-derivation found the
real shortfall was in edge volume — v0.3.5 was already at 0.93× ground truth on nodes. Four
sessions of work, one unit error.

This is the same defect class as DD-026: there, a precondition that its own threshold made
unreachable; here, a threshold that its own instrument cannot read. Both are caught by
arithmetic *before* spend, and both were caught only after it.

**Consequences, binding.**

1. **Registration form.** A gate is registered as (threshold, unit, instrument). All three, or
   it is not a gate. The bulk task's own gates carry theirs: the Phase A faithfulness gate is
   `F_upper < 0.10` on *atomic facts of admitted node items*, instrument = the standing probe
   protocol; the Phase C acceptance rule is a fabrication rate on the *same* unit, instrument =
   the same probe.
2. **A comparator is part of the unit.** "60% of v0.3.5" is not a unit; "60% of v0.3.5's
   admitted nodes per chunk on the 44 shared chunks" is. Where a comparator does not exist for
   the material under test — as it does not off the pilot documents — the correct report is
   *no verdict*, never a manufactured one (ADDENDUM-06 §2, applied in Phase A).
3. **Qualification evidence is not a burn-time bar.** The re-derived 5.16 node floor is n=5,
   reference-heavy, effectively n=2 informative. It licensed starting the burn and appears in
   no gate in the burn. Promoting qualification evidence to a running threshold is how a
   tripwire becomes a target.

## DD-029: A one-time qualification licenses starting a burn, never finishing it unmonitored

**Date:** 2026-08-31. **Task:** `cc_tasks/2026-08-30_bulk_extraction_v038.md`.
**Prior art:** Wald (1945) SPRT; Dodge & Romig (1959) lot acceptance by attributes; Dodge
(1943) CSP-1 continuous sampling; Shewhart bands for report-only process monitoring.
**Internal:** Wintermute G4 (bulk extraction without measurement is how a layer dies);
ADDENDUM-06 §3 of the chunked pilot, which carried this requirement forward as binding.

**Decision.** Corpus-scale extraction runs under **sequential acceptance sampling per batch**,
with parameters fixed before any qualification data exists, and a corpus stop rule that is the
single operator touchpoint.

- **Plan.** Wald SPRT on the batch fabrication rate: p0 = 0.05 acceptable, p1 = 0.10
  rejectable (p1 is the standing faithfulness gate), α = β = 0.05. Accept when
  d ≤ −3.9406 + 0.07236·n; reject when d ≥ +3.9406 + 0.07236·n, for d fabrications in n judged
  facts. **55 facts** is the arithmetic minimum before a perfect batch can be accepted at all
  (DD-026 applied to this plan); expected sample number is 159 at p0 and peaks at 231 at the
  indifference rate.
- **Batch outcomes.** Accept → the batch projects. Reject → that batch's shard is quarantined
  out of projection and the burn continues. Still `continue` at 2× ASN → accept-with-flag,
  marked `sampling_inconclusive`, counted toward the consecutive rule.
- **Corpus stop.** 2 consecutive rejects, or 3 rejects/inconclusives in any rolling 5 batches.
- **What qualification may inform.** Per-stratum expected yields (the report-only Shewhart
  bands) and the sample size needed to reach the SPRT minimum. **Nothing else.** p0, p1, α and
  β were fixed in the task file before Phase A ran and do not move on Phase A data.

**Why the parameters are expensive, recorded rather than tuned away.** Discriminating 5% from
10% at α = β = 0.05 is a small effect size, so it costs ~159 judged facts per batch in
expectation. That is the price of the pre-registered discrimination, and the alternative —
widening p1 after seeing the data — is exactly the retuning a pre-registered gate exists to
forbid. A failed gate triggers investigation, never retuning (bulk-v1 closeout, standing).

**Consequences, binding.**

1. Yield is **monitored, never gated**. Per-stratum admitted/chunk against Phase A bands;
   outside ±3 SD is flagged for the RESULT. Yield heterogeneity across document classes is a
   finding (ADDENDUM-06 §2), not a defect.
2. **Every monitor is mutation-verified before live use.** This project has recorded instances
   of a test measuring a committed artifact instead of the generator; a monitor with that
   defect reports health it never checked.
3. Semantic edges remain out of bulk entirely (DD-024, unchanged). The `cites` layer runs as
   part of normal emission and is reported by defect count per batch.

## DD-030: Admission requires convertibility, and "converted" is not the same as "usable"

**Date:** 2026-08-31. **Task:** `cc_tasks/2026-08-31_ingestion_conversion.md` (subsumes
ResearchTask `6c39a235`). **Status:** accepted.

**Rule.** The canonical substrate format is markdown with YAML frontmatter. A document is
admitted only when (a) it is already markdown, or (b) the converter registry declares its
format and conversion succeeds *adequately*, or (c) neither holds — in which case admission
still records the document, and the system emits `conversion_gap` and auto-registers a
ResearchTask naming the gap. Detection at admission; improvement launched by the system;
per-item operator review nowhere.

**Why the adequacy clause is the load-bearing half.** The task that installed this rule was
written from a burn report saying two documents were "HTML with no markdown conversion".
Measured against the store, that premise was false: T1's Docling pass had already converted
all five crosswalk HTML documents. What it produced for three of them was a *faithful
conversion of a navigation page*. `slsa-specification-v1-0.html` is 16,566 bytes of markup
carrying 2,016 characters of visible text, 30% of it anchor text; the specification lives on
eight sub-pages the acquired page merely links to. Docling did not fail. There was no error to
catch. A success/failure signal cannot see this class at all, and that is exactly how a table
of contents reached an extraction queue and sat there for eight days.

So the gate measures **extent**, not exit status. It uses the two shallow features the
boilerplate-detection literature settled on — text density and link density (Kohlschütter,
Fankhauser & Nejdl, *Boilerplate Detection using Shallow Text Features*, WSDM 2010) — and
invents no third. Thresholds flag for review and never silently drop or admit: a document
below them is still admitted, still citable, and now carries a task to fix its extent.

**Both features are required, and one document proves it.** `slsa-specification-v1-0` clears
the visible-text floor by 16 characters (2,016 against 2,000). A length-only gate misses it. A
link-density-only gate misses the three markdown landing pages the corpus-wide run found
(`akamai-datastream-2-docs`, `digital-gov-website-standards`,
`itu-ai-ready-analysis-towards-a-standardized-readiness-frame`), whose link density is low
because crawl4ai already stripped the anchors. Six of six flags were true positives on
inspection.

**Consequence for extraction.** A document with an open `conversion_gap` has no substrate, so
it cannot be queued for extraction by construction rather than by anyone remembering to
exclude it. The `unconvertible_source` failures recorded at burn time in
`2026-08-30_bulk_extraction_v038_RESULT.md` §0/§7 are the counterexample this rule exists to
prevent, and the prevention is structural, not procedural.

**Not decided here.** Which converter wins for a given format is a measurement, re-run when a
format earns it, not a standing commitment — see the recorded head-to-head in
`kg/ingest/convert.py CONVERTER_CHOICE`. Re-conversion of the working PDF corpus stays out of
scope; a working substrate is not a defect.

## DD-031: The assessment layer is consolidated into this repo, the unit of analysis is two-level, and a discovery mechanism is scored on evidence of machine use rather than on vintage

**Date:** 2026-09-01. **Task:** `cc_tasks/2026-09-01_assessment_consolidation.md`.

The June 2026 project at `brock_projects/ai-readiness-fss` (probe harness, benchmark rubric,
three-stream assessment spec, survey drafts, covariate schema) was not a separate project. It is
the assessment-instrument layer of this framework, and maintaining it as a sibling repository
guaranteed divergence between a rubric and the harness implementing it. It is imported under
`assessment/` by `git subtree` with its four June commits intact, the old location is
tombstoned, and no divergent copy remains. The imported documents are record and are not
edited; the merged live design is `docs/crosswalk/assessment_protocol.md`.

Three substantive decisions come with it.

**Two-level unit of analysis.** The data product is the measurement unit and yields a scored
profile; products aggregate to agency-level dimension vectors; agency vectors are read within
peer cohorts and never as a naked cross-agency ranking. This reconciles June's agency-level
design with September's product-level pilot rather than choosing between them: the product is
where evidence is collected and remediation happens, the agency is where the picture becomes
actionable.

**Orientation first, replacing mechanism naming.** June's Part B named the access axis by three
then-current mechanisms (`llms.txt`, MCP, WebMCP), which dates the construct to the month it was
written. The construct is discoverability and retrievability: an agent arriving cold must be
able to establish what exists, what it means, how to obtain it, and what may be done with it.
The established discovery stack (RFC 9309, sitemaps, RFC 8615 well-known URIs, schema.org
Dataset/DataCatalog, DCAT/data.json, content negotiation, persistent identifiers) is the
core-scored mechanism set.

**The evidence criterion for admitting a mechanism.** Every mechanism, established or emerging,
is a hypothesis about how machines actually orient. What admits one to the core set, or retires
it, is observed machine behavior: crawler and edge logs, D0-class probe results, citation
telemetry. Vintage and fashion are evidence in neither direction. `llms.txt` and MCP/WebMCP-class
endpoints are therefore dated frontier candidates, admitted on evidence of agent use, and
equally liable to retirement if that evidence does not arrive. June's core/frontier firewall with
per-probe `as_of` dating is the mechanism that keeps a post-corpus standard out of the core score,
and it is carried forward unchanged.

**Superseded by this decision:** the probe-depth design on the discovery and web surface, shown
shallow by the census-web-concept-inventory D0-r2 run (meta-robots not read; sitemap read from a
fixed path rather than the robots-declared one; catalog presence scored where coverage is the
property; no declared/enforced/observed triad). Those four gaps are open items in
`assessment_protocol.md` §9, and the FSS Machine Diagnostic stub (A10, A11) is the specification
they grow toward.

## DD-032: `claude -p` failures are classified before settlement; an empty failure releases and backs off; the burn state file merges by batch id

**Date:** 2026-09-02. **Task:** `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge.md`; recorded by `cc_tasks/2026-09-02_post_burn_reconciliation.md` (finding F4: the behaviour shipped with no DD entry). Amends DD-022's settlement rule; DD-022 is otherwise unchanged.

**The incident (from the ledger, not memory).** 2026-09-01 03:01Z, run `bulk_v038_b009`: five consecutive `claude -p` calls returned exit 1 with empty stdout and empty stderr (the Max usage window closing). `_looks_rate_limited` matched nothing, so DD-022's conservative rule applied — each reservation was *settled at the estimate* — booking 140,000 tokens for no output, and the driver's five-in-a-row systemic-failure rule stopped the pass. The relaunch succeeded with no code change. The evidence that those calls consumed nothing server-side is in `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md` §1.2: seven reserve→settle pairs at the 20,000 estimate with ~3 s gaps (a real chunk call settles at ~36k after 8–10 s), zero raw responses in the window (raws are written only on a parsed envelope), zero `model_call` events, and normal per-chunk usage immediately on relaunch.

**The decision.** Every `claude -p` return is classified by a pure function, `classify_cli_outcome(returncode, stdout, stderr)` in `kg/extraction/model_stub.py`, into one of four named outcomes before any ledger write: `success`; `rate_limited` (the existing marker matcher, which wins when it matches); `empty_failure` (non-zero exit, stdout empty or whitespace, stderr empty or whitespace); `error_with_output` (non-zero exit with anything on either stream). The outcomes settle differently:

- `empty_failure` is treated like `rate_limited`: the reservation is **released**, not settled; the stub backs off and retries under `controls.yaml spend.empty_failure_backoff_seconds` (default `[60, 300, 900]`) up to `spend.empty_failure_max_retries` (default 3). After the cap it settles at the estimate exactly as before and the chunk failure counts toward the driver's systemic-failure rule. Both keys are required config; a missing policy is a `SpendConfigError` before any reservation.
- `error_with_output` keeps DD-022's rule unweakened: settle at the estimate, because a CLI that produced output may have consumed tokens.
- The cost of being wrong about `empty_failure` is bounded by `max_retries × estimate` per chunk; the cost of the old rule was a driver stop plus 140k phantom tokens per five-chunk run. If a future ledger shows an empty failure that *did* bill, the override is to remove `empty_failure` from the release set, not to touch the classifier.

Ledger `settle` and `release` records carry `outcome_class`; `kg spend status` and `kg spend reconcile` report tokens booked per class (`unclassified` for pre-DD-032 records), so the phantom-token shape is visible rather than inferred.

**The state file.** The same task closed the second §21.6 defect: `scripts/run_chunked_bulk.py` rewrote `state/bulk_v038_burn.json` wholesale from the rows the current loop had reached, so the tome run (pid 46272, launched 2026-09-01 20:58Z) dropped b010–b015's verdicts and the post-relaunch driver re-walked them from persisted judge labels at zero cost. Writes now go through one function, `merge_burn_state`, keyed by batch id: a run may add or update its own batches and may never drop another's; a verdict in {`accept`, `reject`, `sampling_inconclusive`, `quarantine`} is immutable once written, and a second write with a different verdict is refused and logged as `verdict_conflict` (in the file and on stderr). Re-verdicting is a new event with provenance, consistent with the event-log invariant. Positive control and mutation evidence (merge disabled → 6 of 11 tests fail) are in the task RESULT §2.

**Prior art.** Outcome classification before accounting is the ordinary shape of retry policy in client libraries (idempotent-retry on connection-level failures without a response, no retry once a response body exists); the rate-limited path already implemented that split for one marker class. This entry generalises it to the no-response case rather than inventing a policy.

## DD-033: G1 EVAL v0 — a pre-registered level scale for numeric-uncertainty preservation, retrieval removed by construction, a deterministic parser with an honest `unparseable`, and no product-level threshold before calibration

**Date:** 2026-09-02. **Task:** `cc_tasks/2026-09-02_g1_eval_probe_family_v0.md` (steps 0–5; frozen at the `g1-eval-v0-frozen` commit before any model call). **Prior art:** `docs/research/2026-09-02_g1_eval_prior_art.md` (162 logged queries; §4 fixes eight constraints this entry adopts) and its F7 addendum `docs/research/2026-09-02_g1_eval_prior_art_F7_addendum.md` (24 further queries + 6 named lookups). Indicator G1 is skeleton §5d.

**What is settled by found prior art and adopted, not re-derived.** The unit of analysis is the proposition — one published estimate plus its qualifier set (`min-2023-factscore`; `du-2026-possible-or-definite`). Preservation is ordinal, with the level structure of Du 2026 and the form-of-expression axis of `van-der-bles-2019-communicating-uncertainty`. Failure names come from the memo's vocabulary first: certainty assertion and omission (Du 2026), decontextualization (`lee-2026-when-summaries-distort-decisions`), overgeneralization (`peters-2025-generalization-bias-llm-summarization`), quantity hallucination (`zhao-2020-reducing-quantity-hallucinations`, sub-taxonomy `cao-2024-multimodal-long-form-summarization-financial-reports`). Both elicitation routes are run (Du 2026: the indirect route is where preservation fails). The producer's published rule is the ground truth (`census-acs-general-handbook-2020` MOE at 90 %; `ons-uncertainty-and-how-we-measure-it` SE/CI/CV; `census-2020-disclosure-avoidance-handbook-2021` rho/epsilon/delta). No NLI/QA faithfulness score stands in for the metric (they are number- and qualifier-blind, memo §2.2). Accuracy prompting is not tested (Peters & Chin-Yee 2025 settled it).

**What is G1's contribution (open in the memo), decided here as v0:**

1. **Level scale for numeric forms** (`records.Level`, scorer `probes/g1_preservation.py`): L4 preserved_exact (class, value within published rounding, confidence level and binding all restated); L3 preserved_transformed (numeric and correct under a legitimate transformation — MOE↔bounds, ±↔interval, percent↔fraction, precision that rounds back to the source's, and, in v0, a right value with the confidence level omitted); L2 degraded_verbal (verbal band, no number); L1 omitted; L0 corrupted (magnitude outside published rounding with `widened`/`narrowed` recorded, wrong level, wrong binding, fabricated qualifier, suppressed or flagged-unreliable estimate restated as usable). Score mapping PASS = L4|L3, PARTIAL = L2, FAIL = L1|L0; the level and failure class always travel in observations. Estimate fidelity (exact/rounded/wrong/absent) is recorded separately and never feeds the score. SE has no legitimate-transformation class in v0, so L3 is unreachable for SE by construction; SE↔MOE conversion under the producer's factor is a candidate for v1, not absorbed here.
2. **Retrieval separated by construction.** The source passage is always in context; no retrieval, browsing or tools. Every failure the observed leg records is a restatement failure (memo §4.8). The surfaced leg (live answer engines) is a separate proposal.
3. **Deterministic parse with `unparseable`.** `probes/_g1_parse.py` is rule-based; a restatement in which the class's uncertainty vocabulary appears but nothing is classified is `unparseable` — a fourth outcome with its own count, never coerced. Precedence, pre-registered: class vocabulary without a parse → unparseable, even beside a hedge; a hedge with no such vocabulary → L2; otherwise L1. No model judge in v0 (a judge is a separate proposal with a calibration gate). Readiness floor: parse coverage ≥ 0.90 on the development restatements — met at 1.00 (`tests/test_g1_preservation.py`).
4. **Tolerance = the source's own rounding.** The restated value, at the source's scale and rounded to the source's printed decimals, equals the source value. No relative-tolerance knob. A coarser rounding than the source's is L0 by pre-registration; if the pilot shows it to be a legitimate-transformation class, that is reported, not absorbed. Bounds restated as ± (and vice versa) are compared within half a unit of the printed bound's precision, because producers round the bounds themselves (ONS 42,649 ± 1,032.5 printed as 41,616 / 43,682).
5. **No product-level threshold.** The rollup reports the L3+ preservation rate per class × mode with a Wilson 95 % interval and the denominator, plus the `unparseable` count — no PASS/PARTIAL/FAIL at product level (protocol §3). A threshold is set from the January calibration run against a stated rationale and frozen before the second run.
6. **Eval firewall.** `SOURCE_EVAL` records and the `G1` declared-leg dimension are partitioned out of the rollup before any composite sums (`rollup.py`), exactly as web-surface results are; positive-control and mutation tests in `tests/test_rollup.py`.

**Fixture sources, and where the task's premise did not hold.** The DP_NOISE class is built from the Census Bureau's DAS handbook, resolved by step 0's named lookup and admitted through the standing path (batch-026, epoch `g1dp-2026-09-02`) — not from an invented example. The StatCan 12-539-X 6e text held in the corpus carries no CV band, letter flag or suppressed cell (a corpus-wide scan of 207 documents found none anywhere), so RELIABILITY_FLAG holds the ACS handbook's own verbal verdicts and SUPPRESSION is empty with a Seldon ResearchTask recording the gap; the enum, parser and scorer implement both classes regardless.

**F7 gate outcome (step 0).** No hit meets the pre-registered falsifier for any class. Temporal-knowledge benchmarks (FreshQA, TimeQA, RealTime QA, HoH) score whether an answer is *current*; G1's VINTAGE class scores whether the restatement *carries the as-of date the source states* — that distinction is the recorded finding. arXiv refused this host (HTTP 429) for F7's six boolean queries across three attempts; recorded as errors, not zeros.

**Spend.** Every consumer call goes through `kg/extraction/model_stub.invoke` (DD-007, DD-022, invariant 5) with `parse_json=False`; the pilot ceiling is the task's 200,000 tokens, declared on the ledger. A minimal `claude -p` call books ~30k tokens (the CLI's cached system prompt), so the ceiling admits about six calls; the pilot walks a pre-registered schedule (`assessment/config/g1_pilot.toml`) and stops cleanly at the first refusal. Raising the ceiling is an operator decision, not a code path.

## DD-034: The G1 parser is a versioned instrument; readiness is measured on sealed held-out model output elicited after the parser freeze; pre-normalisation precedes NFKC; z comes from the proposition's level; the memo's StatCan claim is withdrawn until held

**Date:** 2026-09-03. **Task:** `cc_tasks/2026-09-03_g1_eval_v1_parser_fullgrid_errata.md`. Amends DD-033's D5 readiness rule; DD-033 is otherwise unchanged.

**The defect this corrects (from the v0 RESULT, `cc_tasks/2026-09-02_g1_eval_probe_family_v0_RESULT.md` §6).** The v0 readiness gate measured parse coverage on restatements the parser's author had written, scored 1.00, and then 8 of 18 real model responses were unparseable and both scored failures in the run were parser readings (Seldon Issue `0d314dff`). A gate that the instrument's author can satisfy by writing the test is not a gate.

**Decisions.**

1. **Parser version is an instrument version.** `harness/probes/_g1_parse.PARSER_VERSION` is stamped on every `EvalResult` as `parser_version`, a required field beside `prompt_epoch` and `model_id`; records scored under different parser versions are never pooled, and a re-score under a new version writes a new results file (the old file and its Results stand). The v0 prefix was re-scored under `g1-parse-v0` with the stamp (`assessment/results/g1_v0rescore_g1_eval_pilot_v0_2026-09-03.json`, reproducing the pilot: 18 / 10 / 8 / 8) so the v0→v1 delta on the same six responses is a registered pair.
2. **Readiness is measured on sealed held-out model output only.** The held-out propositions are not elicited until the parser is frozen (commit tagged `g1-parser-v1-frozen`); the gate is the `unparseable` share on the holdout responses, ≤ 0.10, pre-registered here. Development-set coverage is reported, never the gate. Every rule in a parser version is motivated by a named development response (cited in the rule's docstring and reproduced verbatim as a test case); a rule motivated by a holdout response belongs to the next version, in a later task.
3. **Pre-normalisation before any NFKC-style pass.** Superscript exponents (`10⁻¹⁰`) are rewritten to `1e-10` *before* NFKC, which maps `⁻¹⁰` to `-10` and turns the exponent into a subtraction — the reading that produced v0's one "quantity hallucination". Markdown emphasis, currency abbreviations, pipe tables (column headers naming and scaling their cells), label-then-list and derivation-line forms, and equation chains are each a named, tested transform; the normalised text travels in the record's observations beside the raw response so a reviewer sees what was parsed.
4. **Direct mode names the class.** In `direct` mode the first number whose unit is compatible with the asked class (and which is not the estimate) is the qualifier even with no keyword; a bare number in `indirect` mode is still not a qualifier.
5. **z from the proposition's level, never hardcoded.** SE ↔ MOE and SE ↔ symmetric CI bounds are L3 transformations with z read from `harness.toml [g1.z_by_level]` or, where the producer states its own factor (StatCan LFS: one SE = 68 %, two SEs = 95 %), from the qualifier's `z`. Tolerance remains D7. A coarser rounding of a bound by the model is still L0 (one dev response did this); D7 is not loosened.
6. **The memo's StatCan claim is withdrawn until held.** `docs/research/2026-09-02_g1_eval_prior_art_ERRATUM-01.md` (DesignNote `21e3d2df`, `corrects` → the memo's DesignNote `54dee043`): the CV bands and suppression rule attributed to 12-539-X 6e came from a web-search snippet; the bands live in product-level guides. Held now (epoch `g1srp-2026-09-03`): NCHS Series 2 No. 175 and No. 200, StatCan 71-543-G 2025, ACS Data Release Rules. Memo §4.5's StatCan constraint is supported by those, not by 12-539-X.

**Registry limits, recorded.** Seldon's ontology has no DesignNote→DesignNote `corrects` and no Issue→Result relationship (every candidate type probed 2026-09-03 rejected the pairing); the erratum's correction is a `corrects` property and the Issue's affected Results are an `affected_result_ids` property plus the description. No Result value or state was changed.

**What the dev grid showed before the gate ran** (development set, parser v1, `assessment/results/g1_v1_dev.json`): 84 responses, 132 records, 131 scored, 1 unparseable, 130 at L3+. Whether that generalises is exactly what the sealed holdout measures; the RESULT reports the gate first.

## DD-035: G1's observed leg is a product test — qualifier families are the scored unit, failures are attributed by binding, rounding and compression are covariates not scores, splits seal by passage, one control consumer is a control arm not a factor, and the v1 gate is restated on fresh responses only

**Date:** 2026-09-03. **Task:** `cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression.md`. Amends DD-033 (D1 fixtures, D2 scoring unit, D7 rounding) and DD-034 (readiness on the holdout); both are otherwise unchanged. Instrument versions: parser `g1-parse-v2`, scorer `g1-score-v2` (a scorer version is stamped on every record beside the parser version from here on), prompt epoch `g1-v2-2026-09-03`. v1's numbers stand; every v0/v1 response is re-scored under the v2 pair as a registered comparison.

**The decision.** The skeleton defines G1 as "MOEs/CVs as structured fields, not footnotes" — a property of a data product's presentation. v1 measured a frontier consumer on handbook prose with the source in context and found it near ceiling (holdout 0.919, pooled 0.969, six genuine losses in 193, zero L2 in 196). Every genuine loss was a compression-class event. So v2 fixtures come from **product surfaces captured as served** — a Census Data API JSON table whose fields are codes (`table_coded`), StatCan long-format CSV slices whose rows are labelled "Estimate" / "Standard error of estimate" (`table_labeled`), NCHS Data Briefs and BLS Employment Situation releases whose estimate sits in the body and whose CI/SE sits in an appendix table or Technical Note (`footnoted`), StatCan CSV cells carrying `E` / `F` quality letters and an NCHS state table whose change column is replaced by `†` (`flagged_cell`), and Census QuickFacts / the 2020 DHC counts, which publish no uncertainty at all (`no_declared`, declared leg only) — with a **compression budget** as a pre-registered factor (`none` = the v1 indirect prompt verbatim, `short` ≤ two sentences, `tight` one sentence ≤ 30 words). The v1 handbook stratum is the `prose_labeled` control stratum. The declared leg (`g1_declared`) ran on every captured surface file, so the declared → observed join exists for the first time (`declared_leg_score` rides on every observed record). The surface vocabulary is the closed set in `harness/g1_fixtures.SURFACE_TYPES`.

1. **Families (D9).** {SE, MOE, CI} = `interval`, {CV} = `relative`, {RELIABILITY_FLAG, SUPPRESSION} = `reliability`, {DP_NOISE} = `dp`, {VINTAGE} = `vintage` (`harness.toml [g1.families]`, checked against `records.FAMILIES`). The record unit is (proposition, family, mode[, compression]); the family level is the best level any published form achieved; the per-form verdicts travel in `observations.forms`. A cross-form derivation inside the family (bounds quoted where an SE was published, an SE within the bounds' own rounding through z) is L3; an exact published form is L4. Cross-family derivations (an SE stated where only a CV was published, or the reverse) score the target family L3 only when the estimate is restated exactly, and are recorded as `cross_family_derivation`. v2 Results count families; the qualifier-form count is reported beside them. The v1 defect this closes: an interval carried correctly recorded an SE "omission".
2. **Binding (D10).** A candidate counts as this estimate's only if it is bound to it: a ± anchored on the estimate's value (or its display-scale or rounded form); the estimate's value in the candidate's sentence or line; a label reference in the candidate's own sentence — a row-specific label token (one in at most a third of the passage's rows, e.g. "youth", "$15,000") or, when no row-specific token exists, a generic one with no sibling row named; or, in direct mode, the question itself. Parentheticals on labels ("(2015 ACS 1-year)") are metadata, not identity. No bound candidate → L1 `omission` with `estimate_restated` recorded (Du 2026's certainty assertion is recoverable from the record; the v1 `certainty_assertion` label is retired). A bound candidate that is wrong → L0 with its own class. `binding_error` is reserved for a candidate anchored on another estimate and presented beside this estimate's label. The three v1 records the reviewer called omissions and the scorer called `binding_error` / `quantity_hallucination` are verbatim test cases (`restatements.yaml v2_cases`); one of them turned out, under families, not to be a loss at all (the ONS interval quoted as its printed bounds). The window and token rules live in `harness.toml [g1.binding]`.
3. **Covariates, not scores (D11).** Every record carries `relative_deviation`, `rounding_direction`, `summary_precision_consistent`, `compression_ratio` (passage tokens / response tokens), `footnote_distance_chars`, `declared_leg_score`, `surface_type`, `compression_level`, `consumer_model_id`. D7 stays strict: a coarser rounding than the source's is L0. The one transformation v2 adds is a value restated at the surface's display scale (a "Persons in thousands" column's 2,670.0 with no scale word): L3 with `scale_word_omitted`, never L4.
4. **Compression (D12)** is a factor on the indirect prompt only; direct mode has none. Because the `none` template and the direct template are byte-identical to the v0 epoch's, a slot elicited under `g1-v0-2026-09-02` for the same passage / proposition and the same model is the same slot: the v2 runner reuses that evidence and the record carries the evidence file's own epoch plus `prompt_text_identical = true`. This is what makes the grid affordable (221 new calls, 7.5M tokens at the floor, against 11.2M without reuse); it is a spend decision on identical prompts, not a loosening of the epoch rule (records under different prompt TEXT are still never pooled).
5. **Split by passage.** A passage belongs to exactly one split. The twelve v1 passages shared by the v1 dev and holdout files — whose `none` responses were development evidence the parser author read — belong to dev in v2 with every proposition on them (`split_origin` records where each came from); the v2 product-surface passages are disjoint by construction and dev and holdout are different files (different state, reference month or brief). Nothing in the v2 holdout is reused from dev.
6. **One control arm, not a factor (D13).** `claude-haiku-4-5-20251001` is pinned as `[control]` in `g1_consumer.toml`, runs through the same choke point and gates, on the holdout grid only, and is reported beside the pinned consumer's results, never pooled with them.
7. **The v1 gate, restated on fresh responses.** The v1 holdout gate (2 of 64) included records scored on twelve shared-passage responses the parser author had read. Restricted to the 35 responses elicited after the freeze (`assessment/results/g1_v1_holdout_fresh_reviewed.json`, `fresh_only = true`; Results `g1_v1_holdout_fresh_*`): 37 records, 1 unparseable (share 0.027 ≤ 0.10, the gate still passes), 33 of 36 scored at L3+ (0.917 [0.782, 0.971]), 2 genuine losses. The v1 RESULT is not edited.
8. **Readiness (pre-registered, unchanged in form).** `unparseable` share of the pinned consumer's holdout family records ≤ 0.10, computed on holdout evidence only, reported first; rules motivated by holdout responses belong to v3.

**Prior art this implements or departs from.** Families are the equivalence-class view of what the producers themselves state (ACS: MOE = 1.645 × SE; ONS: CI = estimate ± 1.96 × SE; StatCan LFS: one SE = 68 %, two = 95 %) — the transforms are theirs, not the scorer's. Binding is the atomic-claim discipline of FActScore (`min-2023-factscore`) applied to the qualifier: a qualifier is a claim about one estimate. Compression as a factor follows `lee-2026-when-summaries-distort-decisions` (decontextualization under summarization) and `peters-2025-generalization-bias-llm-summarization`. The product-surface framing is the skeleton's own G1 definition (A11's declared leg), not new.

**Acquisition record.** `scripts/g1sfc_list_2026-09-03.yaml` → `harvest_triage.py` → `manifest_triage.py`, batch-028, epoch `g1sfc-2026-09-03`: 17 surfaces admitted, 2 routed `needs_source` (data.census.gov's CSV export — HTTP 403 "Request Rejected"; BLS `laucntycur14.txt` — HTTP 404), 2 cut with reason (the Census newsroom ACS release and every ONS bulletin probed carry no MOE or CI on the surface). The Census Data API requires a key: the harvester gained `secret_env` — the key is read from the environment at request time and every recorded string (register, event, capture header) carries `{CENSUS_API_KEY}` in its place (`harvest_kernel.secret_values`; `ANTHROPIC_API_KEY` is refused by name, DD-007). The BLS releases and QuickFacts were reachable only through the browser fetcher.

**Execution note (2026-09-03, end of task).** The freeze commit `281421c` was amended once by `6976464`, before any holdout response had been read: the step-5a re-score of the v0/v1 evidence exposed binding defects in the frozen scorer (a rounding-to-zero bug in `is_rounding_of`; qualifier values, table references, range members and thresholds counted as the value a qualifier follows; uncertainty vocabulary in a sibling's label winning the label contest). The amendment is on record as an amendment, not folded into the freeze. Results: holdout gate 7/128 = 0.055 (passed); pinned consumer holdout 71/121 families at L3+ (0.587 [0.498, 0.671]); pooled indirect preservation none 0.843 → short 0.563 → tight 0.278 (E4, E5, E6 supported; H3 supported — coded tables lose more than handbook prose); control arm 60/112 (0.536), reported beside, never pooled. The RESULT is `cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression_RESULT.md`.

## DD-036: The G1 instrument is frozen at v2 for the January pilot, G1 becomes two legs scored as a vector with no composite, the LLM reviewer is calibrated against the operator on a blind stratified sample, and a freeze is the last act of the task that declares it

**Date:** 2026-09-03. **Task:** `cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md` (zero model calls). **Amends** DD-033 (D5: G1's reported shape) and the skeleton's G1 definition; DD-034 and DD-035 stand unchanged. **Findings memo:** `docs/research/2026-09-03_g1_eval_findings.md` (DesignNote `6760baaf`; internal). **Instrument versions at freeze:** parser `g1-parse-v2`, scorer `g1-score-v2`, prompt epoch `g1-v2-2026-09-03`, pinned consumer `claude-opus-5`.

1. **The instrument is frozen at v2 for the pilot.** No parser rule, scorer rule, prompt, fixture or consumer changes before the January calibration run. The v3 items — the twelve parser misses the sealed holdout produced, the thirteen from the control arm, suppressed cells as a proposition unit, a wider footnote-distance range — are a registered backlog (ResearchTask `73f0aa5d`), not queued work. The reason to freeze rather than keep improving: the remaining parser misses are qualifiers the response *did* state and the parser did not read, so correcting them moves the measured loss **down**. They bias the loss rate upward, which is against the finding, so the direction of every supported statement survives them. What further scorer work changes is magnitudes — and magnitudes are what a calibration run is for, not what a fifth uncalibrated iteration is for.

2. **G1 is two legs, scored as a vector, with no composite.** **G1-D (declared)** is the existing `g1_declared` probe: error measures present as structured fields beside the estimates on the product surface (AUTO, `public`). **G1-O (observed)** is the v2 EVAL: the family preservation rate — the L3+ share of scored qualifier families (D9) — at indirect compression `none` for the pinned consumer on that same captured surface, reported per surface with the `unparseable` share and the `short` / `tight` rates beside it (EVAL, `paid`). The two are reported side by side and never summed; protocol §3's no-composite-before-intended-use rule governs, and there is **no product-level PASS/PARTIAL/FAIL in v0.2.x** — the rate and its Wilson interval are the score until the January calibration run sets a boundary. **Compression is a reported condition, not a scored one**, until intended use says which condition the consumer of the assessment cares about. Skeleton v0.2.7 (G1 row, G1 note, §5d Evidence cell) and `assessment_protocol.md` §9 carry it.

   The reason G1 cannot stay single-legged: **the legs dissociate.** The surfaces the declared probe scores PASS — the Census Data API's paired `_E` / `_M` coded fields, exactly the "structured fields, not footnotes" the skeleton asked for — are the surfaces the observed leg loses most on (H3 supported: `g1_v2_expect_H3_table_coded_loss_rate` against `g1_v2_expect_H3_prose_labeled_loss_rate`; per file, `g1_v2_join_*_loss_rate` beside `g1_v2_join_*_declared_score`). Structured fields are necessary for G1-D and are not sufficient for G1-O. A single-leg G1 would have scored those API tables at the top.

3. **The reviewer is an instrument too, and it is uncalibrated.** The v2 genuine-loss counts come from an LLM reviewer judging the review queue against a criterion recorded on each results file; its agreement with a human has never been measured, which is the same defect DD-034 named when a parser was scored on its author's own restatements. The protocol, pre-registered here: a **blind stratified sample of 60 records** (`scripts/g1_calibration_sample.py`; strata = scorer level {L0…L4, unparseable} × reviewer verdict {genuine, parser_miss, not_in_queue}, proportional allocation with a floor of 3 per non-empty stratum, fixed seed printed on the sheet) carrying only the prompt the consumer saw, the response, the estimate, the qualifier family and its published forms, the mode and the compression level — never the scorer's level, the reviewer's verdict, the failure class, the surface type or the model id; the sample-id → record key is gitignored and the sheet does not reference it. The operator labels each record L0–L4 or U. `scripts/g1_calibration_agreement.py` then reports **Cohen's quadratic-weighted kappa** on the ordinal levels (Cohen 1960, 1968; Fleiss & Cohen 1973) with a percentile bootstrap interval (Efron & Tibshirani 1993), an unweighted six-category kappa that includes `unparseable`/`U`, and — over the review queue only — agreement with the reviewer's binary verdict through a pre-registered implied-verdict rule (the operator implies `parser_miss` when they read a higher level than the scorer recorded). **No kappa threshold is pre-registered and no verbal band is applied** (Landis & Koch's bands are cited and not used): naming a band would set a threshold by the back door. Kappa never travels alone — raw agreement, the confusion table, and positive specific agreement on the minority call go with it, because this repo has already recorded a kappa paradox on skewed marginals (`scripts/tevv_stability.py`; Cicchetti & Feinstein 1990; the TEVV run's kappa = -0.5904 at PA = 0.4092), and the calibration population is dominated by L4. Prior art for measuring an LLM judge by human agreement rather than by its own confidence: Han et al., arXiv:2510.09738. Sheet `assessment/results/g1_calibration_sheet_2026-09-03.md` (DataFile `09517e34`); ResearchTask `85851bcd` holds the labelling and the run. Until it runs, every genuine-loss count is a count made by an uncalibrated judge; the preservation rates do not depend on it.

4. **A freeze is the last act of the task that declares it.** v2's freeze commit was amended once, before any holdout response was read, because a deliverable the freeze itself required — re-scoring the v0/v1 evidence under the new pair — exposed binding defects in the frozen scorer. The amendment was correct and is on the record as an amendment (DD-035 execution note; v2 RESULT §9.1), but the sequencing was not: **every re-score, back-test and self-check that the frozen instrument is required to pass must run before the freeze commit, not after it.** A freeze that still has work behind it is a draft. From here, the ordering in a task that freezes an instrument is: build, back-test on all prior evidence, fix, *then* tag; and the sealed split is elicited only after the tag.

5. **What does not change.** The construct, the D2 level scale, D7 (tolerance is the source's own printed rounding; a coarser rounding is L0), retrieval removed by construction, the `unparseable` fourth outcome and its refusal to be coerced into a score, the eval firewall that keeps `SOURCE_EVAL` and the `G1` declared leg out of every composite, and the absence of any product-level threshold before calibration.

**Numbers.** Every number behind this entry is a registered Result; the memo cites them as `{{result:<NAME>:value}}` tokens resolved by `scripts/g1_resolve_results.py` against `properties.units` on the Seldon event log (Seldon's own resolver matches an artifact `name` property, which `seldon result register` cannot set — recorded in the RESULT). This task registered 162 further Results: the instrument-at-freeze description and the two gate shares (`g1_v2_instrument_*`, `g1_v1_holdout_fresh_gate_unparseable_share`, `g1_v2_holdout_gate_unparseable_share`), the declared→observed join per surface file and per surface type (`g1_v2_join_*`, `g1_v2_surface_*`), and the D14 statement counts behind E5, H3, H4, H5 and C1 (`g1_v2_expect_*`).

## DD-037: The G1 reviewer is calibrated against an independent MODEL, not the operator; the consequence is a reported range rather than a verdict; the operator's only touchpoint is an optional disagreement list

**Date:** 2026-09-03. **Task:** `cc_tasks/2026-09-03_g1_calibration_rating_agreement.md`. **Amends** DD-036 item 3, which pre-registered the calibration protocol with the operator as the labeler; the sheet, the stratification, the coefficients and the no-threshold rule are unchanged, and only the identity of the second rater and the consequence rule are settled here. Instrument versions unchanged and still frozen: `g1-parse-v2`, `g1-score-v2`, epoch `g1-v2-2026-09-03`, consumer `claude-opus-5`.

**Prior art, searched first.** In this repo's own record: `scripts/tevv_stability.py` measures agreement with Cohen's kappa and records the kappa paradox on skewed marginals (Cicchetti & Feinstein 1990); the Results named `kappa` under task `68426971` already treat an LLM judge as an instrument with measurable reliability (judge self-consistency 0.957, batch-vs-single 0.915); DD-036 pre-registered this sheet and its statistics. From the literature: Cohen (1960, 1968) and Fleiss & Cohen (1973) for the quadratic-weighted coefficient on an ordinal scale, Efron & Tibshirani (1993) for the percentile bootstrap, and Han et al., *Judge's Verdict* (arXiv:2510.09738, held in Wintermute as `harvest-arxiv-e2a16615`) for evaluating an LLM judge by its agreement with labels rather than by its own confidence. **What the search did not find:** a named method for calibrating an LLM reviewer inside a measurement instrument against a second model when no human labels exist. Han et al. is the nearest and its criterion is human agreement, which is exactly the thing this design does not have. That gap is why item 4 below is stated as plainly as it is, rather than being papered over with a coefficient.

1. **The second rater is an independent model.** `claude-fable-5-1` rated all 60 sheet records; `scripts/g1_calibration_rate.py` refuses the reviewer's own model by name, because an Opus rater would be the reviewer's model measuring itself. **The independence conditions are enforced, not asserted:** a different model family; the call made through `kg/extraction/model_stub.invoke`, whose hermetic empty cwd keeps CLAUDE.md, the design decisions and every results file out of the rater's context; **one record per call**, so the rater cannot see a distribution and rate to it; and a prompt built from the blind sheet's own instruction paragraph with the D2 and D9 definitions verbatim, carrying the passage, the response, the estimate, the family and its published forms, the mode and the compression level — and no scorer level, reviewer verdict, failure class, surface type or model id. Same three gates as every other model call here (DD-007 OAuth only, DD-022 reserve-before-dispatch, invariant-5 identity gate); raw exchanges persisted per record before the filled sheet exists.

2. **The consequence is a range, and there is no threshold.** From here on the reviewer's genuine-loss count is never reported alone: it is reported inside a range bounded by the **scorer's** count (every record it put below L3 or could not parse) and the **rater-implied** count (the rater's judgments extrapolated to the grid by stratum weights), with κ and its interval stating how wide the disagreement between the instruments is. A low κ widens the range. It does not trigger a redesign, a reweighting, or a discount factor, and no Landis & Koch band is named — naming one would set a threshold by the back door, which DD-033 item 5 and DD-036 item 2 both refuse until the January calibration run. Measured here: κ_w 0.392 [0.205, 0.614] rater vs scorer on the levels, κ 0.421 [0.206, 0.665] rater vs reviewer on the queue verdict, and the range 173 — 178 — 232 of 232 queued records on the pooled Opus grid.

3. **The operator does not label, and his only touchpoint is optional.** His judgment is a narrow-band sensor for genuine novelty, spend above the declared cap, external sends, and value inputs the system is designed to measure rather than guess. Sixty labelling decisions are none of those: the question is well-defined, the criterion is written down, and a second instrument can answer it. What a second instrument cannot do is adjudicate the cases where the instruments disagree, so that — and only that — is escalated: `assessment/results/g1_calibration_disagreements_2026-09-03.md`, every sampled record where the rater and the reviewer are two or more levels apart or where either had no level to give, with no commentary and no proposed resolution. **The touchpoint list for G1 is now closed:** the operator is asked for the January threshold (a value input), for anything over the declared spend cap, and for whether the findings memo or the deck slide goes anywhere. Nothing else.

4. **What the coefficient establishes, and what it does not.** It measures agreement between two instruments. It does not establish that either is correct. Both raters are language models and can share an error a human would not make; a different model family with no shared context reduces that risk without removing it, and no human has labelled any of these records. So the range is a statement about instrument disagreement, not about truth, and it is written that way in the memo. A human-labelled sample remains the only thing that would make it a statement about accuracy — the escalation list is where that would start, if the operator chooses.

5. **The extrapolation is stated with its assumption.** The rater-implied bound is the sum over queue strata of (the grid's stratum population) x (the share of that stratum's rated sample the rater put below L3, U answers excluded and counted separately). It **assumes stratum-homogeneity** — that the rater's genuine share within a stratum is the same in the grid as in the 60-record sample, which mixes pooled-Opus and control-arm records. Every weight and every rate is registered separately (`g1_cal_fable_range_weight_*`, `g1_cal_fable_range_rate_*`) so the arithmetic can be redone rather than believed. Only the pooled grid has a rater-implied bound; the holdout, dev and control reviewer counts stand alone and are read against the agreement measured here.

**Recorded limits of the pre-registered implied-verdict rule.** On the scorer's `unparseable` records the rule cannot distinguish agreement from disagreement: `unparseable` has no position on the level scale, so ANY level the rater gives is "above" it and implies `parser_miss`, even when the rater's level (L1, L2) says plainly that the qualifier is missing and the reviewer's `genuine` says the same. All five `unparseable | genuine` sample records are forced disagreements for that reason, and they are the bulk of the escalation list. The rule was frozen before the ratings existed and is **not** patched here; the range is unaffected, because it reads the rater's level directly rather than through the rule. A v3 item.

## DD-038: G1-O's score is the binary L3+ share; the five-level scale beneath it is descriptive, and a level-based claim carries the calibration's level agreement or is not made

**Date:** 2026-09-03. **Task:** `cc_tasks/2026-09-03_g1_memo_v1_2_level_caveat.md` (zero model calls). **Builds on** DD-033 (the D2 level scale and the PASS/PARTIAL/FAIL mapping) and DD-037 (the independent rater); neither is amended, and no record was re-scored. Instrument unchanged and still frozen.

The calibration found the instrument robust at one grain and not at another, and the two grains are already different things: **G1-O's score has always been the binary** — the L3+ share of qualifier families — while the five levels beneath it describe *how* a family was lost. The independent rater and the scorer agree almost completely on the binary (`g1_cal_fable_preserved_exact_agreed` {{result:g1_cal_fable_preserved_exact_agreed:value}} of {{result:g1_cal_fable_preserved_exact_n:value}} preserved-exact records; {{result:g1_cal_fable_parser_miss_reviewer_agreed:value}} of {{result:g1_cal_fable_parser_miss_reviewer_n:value}} records the reviewer called parser misses; the genuine-loss range {{result:g1_cal_fable_range_rater_implied_genuine_losses:value}}–{{result:g1_v2_pooled_opus_genuine_losses:value}} of {{result:g1_cal_fable_range_queue_population:value}} queued) and disagree on which sub-L3 level a loss is (exact-level agreement {{result:g1_cal_fable_stratum_scorer_agreed_L2_genuine:value}} of {{result:g1_cal_fable_stratum_n_L2_genuine:value}} in the L2 stratum and {{result:g1_cal_fable_stratum_scorer_agreed_L0_genuine:value}} of {{result:g1_cal_fable_stratum_n_L0_genuine:value}} in the L0 stratum; quadratic-weighted κ {{result:g1_cal_fable_scorer_kappa_w:value}} [{{result:g1_cal_fable_scorer_kappa_w_ci_lower:value}}, {{result:g1_cal_fable_scorer_kappa_w_ci_upper:value}}] against κ {{result:g1_cal_fable_reviewer_kappa:value}} [{{result:g1_cal_fable_reviewer_kappa_ci_lower:value}}, {{result:g1_cal_fable_reviewer_kappa_ci_upper:value}}] on the binary verdict). **So the levels stay in the record and out of the score.** The pre-registered statements that are level claims — E5 (omission modal under `tight`) and E6 (the verbal band appearing under compression) — keep their coded verdicts, unchanged and unwithdrawn, each printed with the level agreement measured on its own level and labelled plainly as the scorer's reading rather than a rater-robust one; E4, H3, H4, H5 and C1 are L3+/below-L3 claims and are untouched. **From here, a new claim about levels needs a level-agreement estimate first** — a claim resting on the part of the instrument two raters do not reproduce is not made until the reproducibility is measured, at the grain the claim uses. No threshold is set on any κ, here or anywhere in G1 (DD-033 item 5, DD-036 item 2, DD-037 item 2): low agreement qualifies a claim, it does not gate one.

## DD-039: Result tokens resolve by `name` against the graph; this project no longer depends on the transitional units fallback

**Date:** 2026-09-04. **Task:** `cc_tasks/2026-09-04_result_migration_completion.md` (zero model spend). **Implements** seldon AD-028 (Result `name` as the token key) and its 2026-09-04 grammar amendment; **completes** the migration that `cc_tasks/2026-09-03_hygiene_sweep_post_g1_freeze.md` Lane 1 stopped at its own gate.

Every one of this project's 3,592 Results now carries a `name`, and `{{result:<NAME>:field}}` resolves against the graph's name index rather than by matching the token key against a `units` property — the shape Results had only because `seldon result register` had no `--name` when the G1 work started. 953 of those names carry uppercase level and qualifier-class segments (`L0`–`L4`, `MOE`, `CI`, `SE`, `CV`, `DP_NOISE`, `RELIABILITY_FLAG`, `VINTAGE`) from DD-035 and DD-037; the earlier grammar forbade them, the amendment admits them, and **no Result was renamed to satisfy a lint** — a name that documents cite is part of the record. 63 rows the migration declines to name automatically (40 whose `units` string is shared by several Results, 23 whose `units` is a real unit of measurement) were named `slug(units)__<artifact_id[:8]>`, deterministically and without human input, on the evidence that none of them is cited by any token in any tracked file; the 23 real-unit rows keep their `units`, because `count` and `kappa` and `accuracy` are units and not names.

**The operational consequence, which is the reason this entry exists:** seldon's resolver carries a transitional fallback (`SI-09`) that answers a token from an unnamed Result's `units` string, to keep projects building mid-migration. Before this task, 73 token resolutions across three documents went through it — 66 in the findings memo, 4 in this file, 3 in the deck draft. **After it, zero.** This project's documents resolve entirely by `name`, so the SI-09 fallback can be removed upstream with no effect here, and a build that ever emits an SI-09 line for this project again is reporting a regression rather than a leftover. Registered upstream as the removal condition's evidence. `scripts/g1_resolve_results.py` remains as a thin shim over the library — its entry point is how the deck is built and how the memo is checked — and what it retired is its own lookup, not its callers.


## DD-040: A graph figure that lives only in a chat transcript is not a measurement; every quoted KG number resolves to a `kg_diag_*` or `cq_v1_*` Result

**Date:** 2026-09-04. **Task:** `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md` §0 (zero model spend). **Mechanism:** `scripts/kg_diagnostic.py` (Script `ca49df59`), `state/kg_snapshot_2026-09-04.json` (DataFile `af95a178`, snapshot), 52 Results named `kg_diag_*`.

**The defect.** On 2026-09-04 a Desktop session ran four diagnostic Cypher queries against `seldon-ai-readiness-kg` through an MCP client, in chat, and reasoned from the answers — duplicate counts, degree distributions, edge totals, corpus completeness. Every figure was quoted in the task file that followed. None could be re-derived by anyone else, and none was registered. This project already refuses that shape everywhere else: an extraction writes an event before it is scored, a Result carries the script and data it came from, and a number in the memo is a token that resolves or the build fails. A graph query typed into a chat window is the same class of claim with none of that discipline, and the fact that it is read-only makes it easier to do, not safer to trust.

**What the re-derivation found, which is the argument for the rule rather than against it.** Nineteen of the twenty quoted figures reproduce exactly. So the chat numbers were *right* — and that is the point: they were right by nobody's verification, and the one that was wrong ("211 Documents, 0 without extractions") was wrong in a way that matters, because **72 of the 211 Documents have no extraction edges at all**. A third of the corpus is admitted and unextracted, which changes what an unanswerable question means: it may be unanswerable because the source was never read, not because entities are duplicated. Three further figures differed on the first run because of defects in the *new* script, not the old numbers — degree and per-document counts grouped by `n.name` and by nothing, which in a graph with 1,122 duplicate-name groups silently merges nodes. Both bugs are recorded in the script's comments where they happened, because the same mistake is available to the next person who writes a Cypher aggregate here.

**The rule, going forward.** Any graph figure quoted in a handoff, a memo, a design decision or a task file must resolve by name to a `kg_diag_*` Result (structure) or a `cq_v1_*` Result (coverage). Re-run the script and register a new dated snapshot rather than quoting a stale one; a rerun is a new file and new Results, never an overwrite. Reading the graph interactively to orient is fine and expected — what is not fine is a conclusion whose evidence exists only in a transcript.


## DD-041: The 17 `g1eval` prior-art sources are extracted; the 55 demand-pull deferrals stay deferred

**Date:** 2026-09-04. **Task:** `cc_tasks/2026-09-04_extract_g1eval_17_and_rerun.md` §0. **Builds on** DD-024 (bulk extraction closed; semantic edges are demand-pull) and DD-040 (a graph figure must resolve to a Result). **Premise:** `kg_diag_gap_never_queued` = 17, all epoch `g1eval-2026-09-02`, from the extraction-gap diagnostic.

**What is decided.** The 17 are extracted. They are the sources the G1 prior-art memo cites, and the two competency questions that failed hardest on substance — CQ-01, how the corpus defines uncertainty, and CQ-02, how it defines AI-ready data — have the most unextracted evidence behind them (27 and 23 of the 72 gap documents mention their terms). A corpus that holds the memo's own sources but cannot answer the memo's own questions is a coverage failure with a known, priced fix.

**What is not decided.** The 55 documents deferred under DD-024 with reason `no consumer` **stay deferred**. Reviving them reverses a standing decision, and the thing that would justify it is evidence, not intuition: the CQ rerun in this task's §3 is that evidence, and it comes after the extraction rather than before. Pricing them was done (1,024 chunks, 20,480,000 tokens at the DD-022 floor, also inside the standing band) so the option is costed and available, not so it is exercised here.

**Why this is not an operator touchpoint.** The extraction was priced at 664 chunks and ≤ 13,280,000 reserved tokens — 24 % of the standing 55,000,000 daily band. Under the cap, the run proceeds and is reported; only spend *above* the declared cap is the operator's call.

**Rerun naming convention, recorded because the first run established none.** A rerun of a registered measurement writes a NEW dated artifact and NEW Results; it never overwrites. Where a metric name would otherwise collide with the first run's, the rerun suffixes the run: `kg_diag_<metric>_2026-09-04b` for the post-extraction diagnostic, against the un-suffixed pre-extraction names. The CQ harness already carried this rule (`cq_v1_<date>` files) and needed no new convention; the diagnostic did.

