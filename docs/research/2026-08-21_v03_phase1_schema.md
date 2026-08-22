# Phase 1 sub-RESULT — Schema v0.3 (append-only)

**Task:** `cc_tasks/2026-08-21_v03_visibility_kernel.md`, Phase 1 (AUTH-1 / DD-009, DD-010)
**Date:** 2026-08-21
**LLM calls:** zero. **Git:** nothing committed (burn convention; operator commits).

## Test counts

| | count |
|---|---|
| Before (baseline, `python3 -m pytest tests/ -q`) | **75 passed**, 0 failed |
| After | **109 passed**, 0 failed |

Net +34 tests (parser +12, schema_pairs +10 incl. one renamed version assertion, append-only +9 new file, manifest +2, plus the 0.2.0→0.3.0 expectation updates in model_stub/pipeline tests).

Discrepancy vs. `CLAUDE.md`: it records `test_extract_json_tolerates_fences` as failing on main (74/75). At Phase 1 start it already passed (75/75) because `tests/test_extraction_model_stub.py` carried an uncommitted fix (`ModelConfigError` → `ModelInvocationError`) from a parallel phase / earlier session. Not mine; reported, not reconciled.

## Files touched (Phase 1 only; append-only, nothing renamed or removed)

| File | Change |
|---|---|
| `kg/schema.yaml` | `schema_version: "0.3"`; changelog entry 2026-08-21. Node types `Practice` (text, grounding_span, as_of_date, scope enum), `Tool` (name, steward, license, url, as_of_date, grounding_span), `Platform` (name, operator, as_of_date, grounding_span). `Claim.evidence_grade` enum (5 values, descending strength) + new `required_properties: [evidence_grade]` key on Claim. `Measure.tier` enum (optional). `Document.source_type` += `practitioner`. Edge types `recommends`, `supported_by`, `implemented_by`, `consumes`, `applies_to`, `targets`, `supersedes`, each with `from/to`, `pairs`, `meaning`, `external_alignment` in the existing v0.2 style. |
| `kg/extraction/schema_loader.py` | `property_values(schema, node_type)` and `required_properties(schema, node_type)` accessors — enum/required lists come from schema.yaml only. |
| `kg/extraction/parser.py` | `LAYER_TYPES` += `practices`/`tools`/`platforms`. New `_property_violation()` runs after the grounding gate: missing/empty required property ⇒ quarantine (reason names the property and "required"); enumerated property present but outside enum ⇒ quarantine (reason `Type.prop value 'x' not in schema enum [...]`). Applies generically to every node type declaring `property_values` — so `Definition.normative_status` and `Claim.claim_type` are now enum-enforced too when present (they were not before; see "Discrepancies"). |
| `kg/extraction/output_schema.json` | `practices`/`tools`/`platforms` layers (groundedNode); description note. Surgical edit, original formatting preserved. |
| `kg/extraction/prompt_template.md` | `prompt_version: 0.3.0`; emission step 7 for the three new layers; node-property list for Practice/Tool/Platform; `evidence_grade` section (REQUIRED, enum + one-line meaning each, with the "only when the source IS the operator" caveat); `Measure.tier` section; seven new edge types with endpoints; explicit note that wrong-endpoint edges go to `proposed_relationships`. |
| `kg/manifest.py` | `_SOURCE_TYPES` += `practitioner` (CLI `--source-type` choices follow automatically). |
| `docs/schema_v0.1.md` | Title/status → v0.3; changelog entry; §2 rows Practice/Tool/Platform + property additions on Document/Measure/Claim; §2 note on v0.3 property semantics; §3 rows for the seven edges; alignment sentence. Existing rows untouched. |
| `docs/design_decisions.md` | DD-009 (one graph, AUTH-1 text) and DD-010 (evidence grading) appended, dated 2026-08-21. |
| `tests/test_extraction_schema_pairs.py` | +10: legal/illegal pairs for each new edge, alignment-key presence, node-type presence, enums read from schema; `test_schema_version_is_v02` → `_v03`. |
| `tests/test_extraction_parser.py` | +12: evidence_grade missing / empty / outside enum / grounding-miss precedence / dependent edge unresolved; Measure.tier absent / valid / invalid; Practice.scope valid+invalid; Tool/Platform grounding gate; all seven v0.3 edges accepted on legal pairs and routed to `proposed_relationships` (`auto_routed_invalid_pair`) on illegal pairs; `supersedes`. |
| `tests/test_schema_append_only.py` | New. v0.2 node types, per-type properties, enum values (including order of the frozen prefix), edge types, per-edge pairs, symmetry, provenance list hardcoded as the frozen reference; asserts strict-subset for types and subset for the rest; every live edge has pairs naming known node types. |
| `tests/test_manifest.py` | +2: `practitioner` accepted; `_SOURCE_TYPES` equals schema `Document.source_type` enum (sync check). |
| `tests/test_extraction_model_stub.py`, `tests/test_extraction_pipeline.py` | prompt_version expectations 0.2.0 → 0.3.0 only. |

Not touched: `events/`, `corpus/`, `controls.yaml`, `scripts/`, the task file. (`git status` shows concurrent modifications to `scripts/run_bulk_extraction.py`, `scripts/run_baseline_gates.py`, `controls.yaml`, `dixie_evidence.yaml`, `.gitignore`, `seldon_events.jsonl` from other phases — not Phase 1 work.)

## Template version and the stamping mechanism

`prompt_template.md` header is now `prompt_version: 0.3.0`. `kg/extraction/model_stub.prompt_version()` regex-reads that header line from the file at call time; `provenance_stamp()` puts it in every extracted item's provenance as `prompt_version`, and `scripts/run_bulk_extraction.py` uses the same call both for the event payload (`"prompt_version": model_stub.prompt_version()`) and for the raw-response filename (`<doc_id>.<sha12>.<prompt_epoch>.<model_id>.json`, prompt_epoch = the same value). `build_projection.py` copies it to `prov_prompt_version`. Nothing hardcodes 0.2.0 outside tests; verified by rendering: `build_prompt()` → header `schema 0.3`, contains `evidence_grade`, `prompt_version()` returns `0.3.0`. `schema_version` is stamped independently by `kg/eventlog.py` from `schema.yaml`, so events under the next run will carry `schema_version: "0.3"` + `prompt_version: "0.3.0"` with no further change.

## Tool / Platform grounding decision

The task lists only domain properties for `Tool` (name, steward, license, url, as_of_date) and `Platform` (name, operator, as_of_date). Schema §4 says *every* node and edge extracted from a document carries `grounding_span` ("No grounding span, no write"), and the parser applies that gate uniformly per layer. **Decision:** Tool and Platform carry `grounding_span` exactly like Standard/Framework (which likewise don't list it in their §2 property column but are gated anyway). Recorded by adding `grounding_span` explicitly to both types' property lists in `schema.yaml` and the §2 table, with a comment citing §4, so the doc and the enforcement agree on their face. Test `test_v03_layers_parsed_with_grounding_gate` pins it.

## External alignments chosen

`recommends` → `prov:wasAttributedTo` (noted as inverse direction); `supported_by` → `prov:wasDerivedFrom`; `implemented_by` → `sosa:madeBySensor`; `consumes` → `dcterms:conformsTo`; `applies_to` → `dcterms:subject`; `targets` → `schema:audience`; `supersedes` → `dcterms:replaces`. None needed `external_alignment: none`; a test asserts the key is present on all seven so an omission can never be silent.

## Discrepancies / decisions the task text did not settle

1. **"Required" needed a schema home.** The task says absent `evidence_grade` ⇒ quarantine and that enums must come from `property_values` with no duplicated lists. Hardcoding "Claim requires evidence_grade" in the parser would have been a second source of truth, so a `required_properties` key was added to schema.yaml (Claim only) and the parser reads it. Additive; no existing type gains a requirement.
2. **Generic enum enforcement widened to v0.2 enums.** Reading enums from `property_values` generically means `Claim.claim_type` and `Definition.normative_status` are now enum-enforced *when present* (absent is still fine). This is stricter than v0.2 behavior. Judged correct — a value outside the doc's parenthetical enum was always a schema violation; it simply wasn't checked — and the existing 75 tests stayed green. Any Phase 4 pilot quarantines with reason `Claim.claim_type ...` or `Definition.normative_status ...` trace to this.
3. **Ordering: grounding before properties.** A Claim that is both ungrounded and ungraded is quarantined for the grounding miss (more specific reason, and matches "grounding gate applies exactly as to other nodes"). Pinned by test.
4. **`supersedes` at parse time.** Both endpoints must resolve to Document; within one extraction output the only Document id is the document itself, so an in-extraction `supersedes` can only be a self-edge. The intended producer is the Phase 7 / DD-012 manifest-level event path (refetch), not the extractor; the parser accepts the type so those events validate under the same whitelist. The prompt lists it for completeness.
5. **CLAUDE.md stale note** on the model_stub test — see Test counts.
6. `docs/schema_v0.1.md` §2 table kept its "Key properties" column compact; the full one-line meanings for the enums are in a §2 note and in `schema.yaml` comments rather than widening the table cells further.
