# CC Task — Batched repair resume: projection keying fix, relocations, attribute re-adjudication

**Date:** 2026-08-23
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Max OAuth only; `ANTHROPIC_API_KEY` unset or abort.
**Execution model:** Serial phases; Phase 2 batches are parallelizable across 2 workers max. Sub-RESULTs under `docs/research/2026-08-23_resume_*`; final `cc_tasks/2026-08-23_batched_repair_resume_RESULT.md` citing the Seldon task id.
**Immutable file. Operator contact: none; unlisted forks get a grounded decision logged in standing decisions.**

## Binding cost rule (DD-019 candidate; the reason this task exists in this shape)

Fixed per-call overhead dominates this pipeline (~36K tokens/call measured on 2026-08-23; ~111K floor measured 2026-08-21). Therefore:
1. **The unit of dispatch is the batch, never the item.** Target 40 items per call (floor 25, ceiling 50), strict JSON-array in/out contract, one retry on parse failure with the batch split in half.
2. **No tools on model calls in this task.** The relocation/adjudication prompt requires none; invoke with tool use disabled so the fixed prefix is minimal.
3. **Freeze the prefix.** Identical system/prompt prefix across all calls in a shard: run from a stable scratch cwd, no per-call injected state (git status, timestamps, file listings). Measure and report the cache-read vs cache-write token ratio on the first 3 calls; if cache reads are not dominant by call 3, stop, diagnose what is varying in the prefix, fix, then continue. Do not burn the worklist with a busted cache.
4. **Token ceiling: 12M for Phase 2.** Progress is sharded and resumable (`--shard I/N`); hitting the ceiling is a normal stop recorded with the resume command.

## Phase 0 — Preflight (zero spend)

Tests green (159 baseline); `controls.yaml` sha recorded, `extract: on` for the duration, restore byte-identical at close; baseline gate table and node/edge counts captured for Phase 3 deltas.

## Phase 1 — Projection keying fix (zero model spend; blocks everything downstream)

The 2026-08-23 benchmark RESULT found 600 of 6,988 item ids recur across documents and the Neo4j projection fuses them into single nodes. Fix the loader to key every node by `(document_id, item_id)` (stable composite, e.g. `docid::itemid` as the graph key, both parts kept as properties). Cross-document identity is dedup's job later, never the loader's.
- **Mutation test first:** seed two same-id items in two docs in a scratch log; assert the current loader fuses them (defect reproduced) and the fixed loader yields two nodes. Then rebuild the real projection.
- Expected effect: node count rises by roughly the fusion count; every gate re-run; grounding must remain 0 (STOP otherwise). Record before/after counts. Update the six monitors' baselines with the before/after pair logged (version the instrument).
- Check `kg/extraction` and gates for any other consumer keyed on bare item id; fix at source, no shims. Tests for the composite key.

## Phase 2 — Batched relocation + attribute re-adjudication (model spend, ceiling above)

**Worklists (from the live repair state, not this file's numbers — reconcile and report):** (a) ~3,041 pending model relocations including prior `span_unrepairable` NONEs under `--redo-unrepairable`; (b) all `attribute_nulled` entries (~5,270) for re-adjudication, plus the ~2,545 deferred nulls behind pending relocations, resolved in dependency order.

**Call contract:** per item send item text (or attribute value), full relevant document passage window (whole doc if under 8K chars, else the manifest-extent text), and the instruction set; per item receive `{id, verdict}`: relocation → minimal verbatim supporting passage or NONE; attribute → `supported` (with passage) or `stays_null`. Verify every returned passage is a verbatim substring of the document; non-verbatim → one re-ask inside the next batch, then NONE/stays_null.

**Seeded positive controls, in-stream:** 2% of each batch are planted decoys — synthetic items no document supports (must come back NONE/stays_null) and known-supported items with their true passage (must come back found). Batch acceptance: 100% on planted decoys per shard rolling window of 200; a miss halts the shard for diagnosis, logged, then resumes. A judging stream without live positive controls is not verified.

**Writes:** relocations → `grounding_relocated` overlays (method `model_assisted_batch`); restored attributes → `attribute_restored` overlays superseding the null, carrying the supporting passage as the attribute's grounding; confirmed nulls → no new event. All stamped with call id, batch id, prompt template version.

**Acceptance measure (pre-registered):** seeded-random 100 restored attributes judged by the probe protocol; strict entailment ≥ 0.90 or the restoration class is reported failed and its overlays are superseded back to null (reversal events, not deletions).

## Phase 3 — Rebuild, gates, monitors (zero model spend)

Projection rebuild (overlays last); all gates; grounding 0 (STOP otherwise); monitor run; updated repair ledger: relocated / unrepairable / restored / stays-null counts against Phase 0 baselines.

## Phase 4 — Close

DD-019 (batch dispatch rule, with both overhead measurements cited); DD-020 (projection composite keying; cross-document identity reserved for dedup). Seldon results: counts, acceptance measure, cache-read ratio achieved, tokens spent. Tests green; controls restored; **commit and push**.

## Out of scope

Concept dedup; construct promotion; re-extraction of the three flagged strata (separate task, which must now also inherit the batch rule); TrustGraph; new harvest; editing this file.
