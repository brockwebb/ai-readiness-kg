# Probe Phase 0 — Preflight (task 2026-08-22_faithfulness_probe, Seldon 68426971)

- Tests at baseline **136**; after Phase 0 **140**. `ANTHROPIC_API_KEY` unset.
- `controls.yaml` before `611d5dda0834900ea77ca619f8d0cd4368efb471cd3914ac76a15378b5344684` → task `1e1654c694b578f197b96d84427067349c5baf02756380e12b94b9eab64a0a74` (`extract: on`, `extract_daily_docs: 0`). Note: the model path used here (`model_stub.invoke` → `claude -p`) does not consult `controls.yaml`; only the bulk runner reads the control plane. Judging is therefore not gated by `extract`. Restore at close.
- `crowd-kit` 1.4.2 installed into the anaconda python for Phase 5 (Dawid-Skene).
- Sidecar `corpus/staging/metrics/tevv_human_subset_labels.jsonl` present (40 lines, rater `claude-desktop-fable5`, fields `human_label`, `lenient_label`, `note`).

## Schema v0.3.2 — `span_entailable` assignment (append-only; `kg/schema.yaml`, `docs/schema_v0.1.md`)
Rule from the task: `as_of_date`, `id`, enum classification fields → false; text/name/steward/owner/year/version/operator/scale/license/url → true. Attributes the task did not list, decided here: `aliases`, `method`, `response_type`, `measurement_notes` → **true** (free text a span can carry); `grounding_span` → false (it is the evidence, not a fact); Document attributes → all false (never extracted). `schema_loader.span_entailable()` accessor; `tests/test_schema_append_only.py` checks every property on every type is mapped and the rule assignments hold.

| node type | attribute | span_entailable |
|---|---|---|
| Document | doc_id | false |
| Document | title | false |
| Document | authors | false |
| Document | pub_date | false |
| Document | source_type | false |
| Document | primary_url | false |
| Document | content_hash | false |
| Document | manifest_event_id | false |
| Document | is_platform_operator | false |
| Definition | term | true |
| Definition | verbatim_text | true |
| Definition | grounding_span | false |
| Definition | normative_status | false |
| Definition | as_of_date | false |
| Concept | name | true |
| Concept | aliases | true |
| Concept | description | true |
| Concept | grounding_span | false |
| Construct | name | true |
| Construct | description | true |
| Construct | measurement_notes | true |
| Instrument | name | true |
| Instrument | owner | true |
| Instrument | year | true |
| Instrument | method | true |
| Measure | text | true |
| Measure | response_type | true |
| Measure | grounding_span | false |
| Measure | tier | false |
| Claim | claim_text | true |
| Claim | grounding_span | false |
| Claim | claim_type | false |
| Claim | evidence_grade | false |
| Standard | name | true |
| Standard | version | true |
| Standard | steward | true |
| Standard | as_of_date | false |
| Framework | name | true |
| Framework | owner | true |
| Framework | year | true |
| Practice | text | true |
| Practice | grounding_span | false |
| Practice | as_of_date | false |
| Practice | scope | false |
| Tool | name | true |
| Tool | steward | true |
| Tool | license | true |
| Tool | url | true |
| Tool | as_of_date | false |
| Tool | grounding_span | false |
| Platform | name | true |
| Platform | operator | true |
| Platform | as_of_date | false |
| Platform | grounding_span | false |

## `judge_label` event type
Defined in `docs/schema_v0.1.md` (v0.3.2 changelog). Shard `events/batch-009_probe_judge.jsonl` via `eventlog.append(..., batch=9, tag="probe_judge")`, `purpose: probe` on every event; `build_projection.NON_GRAPH_PURPOSES` gains `probe` (test added). Tagged shards are already excluded from default replay.
