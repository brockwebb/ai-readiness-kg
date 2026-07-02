# ai-readiness-kg

A knowledge graph that serves as the **validity layer** under the FSS AI readiness
survey and the accompanying definitions work. It answers, with citations a stranger can
verify:

- What definitions of *AI readiness* / *AI-ready data* exist — from whom, dated, and where
  they conflict.
- What constructs (readiness dimensions) the literature proposes, and which instruments have
  operationalized them.
- The crosswalk from a survey item → construct → definition → primary source.

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
kg/            pipeline code (schema.yaml, eventlog.py)
corpus/        source documents (committed); corpus/staging/ is pre-manifest (gitignored)
events/        sharded JSONL event logs (committed)
controls.yaml  operational switches (forage/extract on-off, budgets)
tests/         pytest suite
docs/          schema and design decisions — start here
```

## Docs

- `docs/schema_v0.1.md` — the extraction schema (node types, edge types, provenance).
- `docs/design_decisions.md` — DD-001..DD-008, the dated decision record.

## Tests

```
python -m pytest tests/ -v
```
