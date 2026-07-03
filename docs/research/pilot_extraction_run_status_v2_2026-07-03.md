# Pilot Extraction Run v2 — Status: STOPPED at doc 1 (pipeline defect)

**Task:** cc_tasks/2026-07-03_pilot_extraction_run_v2.md
**Date:** 2026-07-03
**Outcome:** Invocation path implemented and verified; **run STOPPED at document 1** on a
pipeline defect (parser envelope contract). **0/5 documents extracted.** No extraction events,
metrics, proposed_relationships, or state transitions were written — the failure occurred in
`parse_extraction` before the pipeline emits anything. Task NOT marked complete.

## Done and verified

- **`claude -p` invocation path** (`model_stub.invoke`): subprocess to `claude -p --model
  claude-fable-5 --output-format json --allowed-tools NoTool`, prompt via stdin, JSON envelope
  parsed, extraction JSON extracted from `result` (tolerant of ``` fences). Never passes
  `--bare`. Guard hard-fails if `ANTHROPIC_API_KEY` **or** `ANTHROPIC_AUTH_TOKEN` is set.
- **Preflight** (`claude -p` "reply OK"): succeeded, `modelUsage."claude-fable-5"`, no fallback.
- **Live smoke** on a 3-sentence doc: full envelope, all layers, grounded concepts/edges.
- Pipeline threads the envelope's reported model_id into §4 provenance and emits a `model_call`
  usage event; metrics gained `claims_count`. **61 tests pass.**

## The STOP (run protocol step 2 — pipeline defect at doc 1)

Document 1 (Lawrence DRL, 34,078 chars ~ 8.5k tokens) invoked cleanly:
`model=claude-fable-5, output_tokens=30,921, cost=$2.231415, ~278s`. The pipeline then raised:

```
ValueError: extraction output missing 'document_id'
```

**Root cause (my latent defect from the module build):** `parser.parse_extraction` hard-requires
a top-level `document_id`, but (a) the prompt template lists `document_id` only as *context*,
not as a required emitted key, and (b) Fable does not echo it — the smoke-test output confirmed
the top-level keys are `concepts/definitions/claims/.../proposed_relationships`, no `document_id`.
So every document would fail identically at parse. The integrity checkpoint's purpose — catch a
pipeline defect before proceeding — was served: the run stopped before any writes.

This is a **pipeline/contract defect, not a bad extraction.** The extraction itself was
substantial (30k tokens of nodes/edges); it was discarded only because the harness rejected the
envelope over an id the harness already owns.

## Clean-STOP verification

- `events/batch-002.jsonl`: absent (no extraction events written).
- `state.current_state('lawrence-data-readiness-levels-2017')` = `manifest_added` (unchanged).
- No `corpus/staging/metrics/` or `corpus/staging/proposed_relationships/` files created.
- Gates (quarantine > 10%, concept density < 2.0/1k) never evaluated — the run stopped before
  a single document was parsed.

## Cost incurred

- Doc-1 Fable call (discarded): **$2.23**. Preflight + live smoke: ~**$1.0**. Total ≈ **$3.2**.

## Recommended fix (for the new task / v3)

Do **not** trust the model to restate the document id. Inject the harness-authoritative
`doc_id` into the extraction output before parsing:

```python
# in pipeline.extract_document, before parse_extraction:
output = {**output, "document_id": doc_id}   # harness owns the id; overrides any model value
```

Optionally also add `document_id` as the required first emitted key in `prompt_template.md`,
but injection is the robust fix (extraction-neutral — it changes no extracted content). With
that one line, the invocation path is ready to drive the full 5-document run unchanged.

**Per-run cost estimate:** ~$2–3/document (doc size + Fable output), ~$10–12 for all 5.
