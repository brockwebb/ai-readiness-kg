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
