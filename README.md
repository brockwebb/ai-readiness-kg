# ai-readiness-kg

A knowledge graph that serves as the **validity layer** under the FSS AI readiness
survey and the accompanying definitions work. It answers, with citations a stranger can
verify:

- What definitions of *AI readiness* / *AI-ready data* exist — from whom, dated, and where
  they conflict.
- What constructs (readiness dimensions) the literature proposes, and which instruments have
  operationalized them.
- The crosswalk from a survey item → construct → definition → primary source.
- **Machine visibility (schema v0.3, DD-009):** what the standards, platform operators,
  research, and federal digital guidance say about publishing data and content so machine
  consumers (search crawlers, AI retrieval systems, bot controls) can find, read, and cite it —
  and where those recommendations conflict with readiness definitions that stop at institutional
  readiness. Same graph, same grounding rules; scope is a document property, not a partition.

## Schema (v0.3)

Node types: `Document`, `Definition`, `Concept`, `Construct`, `Instrument`, `Measure`, `Claim`,
`Standard`, `Framework`, and — from v0.3 — `Practice` (a normative recommendation about how to
publish/structure/expose content for machine consumers), `Tool` (software implementing a Measure),
`Platform` (a machine consumer whose behavior is targeted or described). Every node and edge
carries a verbatim grounding span.

**Evidence grade.** Every `Claim` extracted under v0.3 carries `evidence_grade` — one of
`peer_reviewed_experiment`, `platform_official`, `measured_practitioner`, `practitioner_assertion`,
`inference`, in descending strength — so a recommendation derived from the graph can cite how
strong the evidence behind it is. A Claim without a valid grade is quarantined, never written
(DD-010).

## Pattern lineage

- **Manifest-gated corpus.** A document becomes corpus only via an explicit `manifest_add`
  event carrying source provenance and inclusion rationale. Harvesters feed a staging area;
  staged finds are inert until the manifest gate opens.
- **Event-sourced JSONL.** The append-only event log (`events/batch-NNN.jsonl`, sharded from
  the first event) is the source of truth. The graph is a disposable projection rebuilt by
  replaying events.
- **Verbatim-grounded extraction.** Every extracted node and edge carries a verbatim
  grounding span validated by mechanical string-match against the source. No grounding span,
  no write.

## Layout

```
kg/            pipeline code (schema.yaml, eventlog.py, manifest.py, extraction/)
scripts/       runners: run_bulk_extraction.py (--profile), build_projection.py,
               run_baseline_gates.py, quality_monitors.py, harvest_kernel.py, manifest_kernel.py
corpus/        source documents (committed); corpus/staging/ is pre-manifest (gitignored)
events/        sharded JSONL event logs (committed)
controls.yaml  operational switches (forage/extract on-off, budgets)
tests/         pytest suite
docs/          schema and design decisions — start here
```

## Docs

- `docs/schema_v0.1.md` — the extraction schema (node types, edge types, provenance).
- `docs/design_decisions.md` — DD-001..DD-012, the dated decision record.

## Tests

```
python -m pytest tests/ -v
```
