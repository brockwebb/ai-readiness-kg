# ADDENDUM-02 — 2026-08-30_bulk_extraction_v038.md

**Date:** 2026-08-31. **Immutable once written.** Operator scope decision (touchpoint 1, spend; touchpoint 3, value input) recorded with its grounding. Base task, ADDENDUM-01, and the standing RESULT govern everything not named here. Append to the existing RESULT.

## 1. The value input, and why it decides the cut

The graph's first consumer is the AI Data Readiness framework operationalization (`docs/crosswalk/usafacts_operationalization_skeleton.md` and its data-gathering instruments). `crosswalk_demand` measures demand *from that work*, so the scope decision's value metric and the burn's priority metric are the same variable — no proxy, no judgment call beyond spend.

Batch-1 evidence in hand: ACCEPT at 110/463 facts, pooled F 0.0273 [0.0093, 0.0771], item-faithful 0.830, extraction 19% under ceiling. Quality is not the constraint; chunk-cost-per-demand is. Coverage is near-linear in documents and badly non-linear in chunks: b005/b008/b009 are 58% of remaining work for 16% of remaining demand.

## 2. Scope

1. **BURN:** all planned batches except b005, b008, b009 — i.e. b002, b003, b004, b006, b007, b010, b011, b012, b013, in plan order. ~437 chunks, cumulative crosswalk-demand coverage ≈ 76% (31/41) including banked b001.
2. **DEFER:** the documents of b005, b008, b009 (three long specifications, 6 demand total). Emit `extraction_deferred` with reason **`below_burn_scope`** — a NEW reason value, distinct from `no consumer`: demand exists and stays on the record; the deferral prices the document out of *bulk* scope, nothing else. Schema append if the reason vocabulary is enumerated. Revivable by any later `extraction_request`; and per DD-023 the unit is the chunk, so demand-pull adjudication may extract individual chunks of a deferred document without reviving the whole document — that is the intended consumption pattern for low-demand tomes.
3. **The two unconvertible HTML documents** (4 demand, 9.8% of total) stay with substrate task 6c39a235, whose priority rises with the operationalization named as first consumer. On conversion: `extraction_request` under the pinned profile, batched and burned under this task's standing rules (formula ceiling, SPRT, stop rule) as a final batch. No new machinery.
4. Nothing else moves. Gates, p0/p1/α/β, the corpus stop rule, per-batch declarations, chunk-level resume, and both DD-024 enforcement layers are all unchanged. This addendum touches dispatch scope only.

## 3. Execution

1. Before resuming: emit the §2.2 deferral events; verify the queue surface reads the three tomes' documents `deferred` and the burn plan drops to the §2.1 batch set with batch identity stable under the ledger-derived rule (the RESULT's batch-identity fix is load-bearing here — a moving id under a changed plan is exactly the defect it fixed; assert it with the existing test surface).
2. Resume: remove `events/bulk_v038_STOP.json`; run the §2.1 batches in order under standing rules. Multi-day as the daily band requires.
3. RESULT appends per batch as already practiced; final append reconciles: coverage achieved vs the 76% planned, full-burn ledger, refusal totals (the 0.492/chunk rate is a finding to carry, with its Phase-A-underestimates-document-effects explanation), and `kg queue status` totals.
4. `seldon cc complete` when the §2.1 set is burned or the corpus stop rule fires (stop-rule completion is completion WITH incident report, per DD-029 and ADDENDUM-01 §5). The deferred tomes and the substrate-gated docs do not block completion — they are out of this task's scope by this addendum.

## 4. For the record

The scope cut is the second application of the demand-pull principle at a new grain: the extract/defer cut priced 159 documents out on zero demand; this addendum prices three more out on demand-per-chunk. Cut-with-reason, revivable, on the ledger. If the operationalization's demand pattern later concentrates on a deferred tome, the revival path is one request event — the system was built so that decision costs nothing to reverse.
