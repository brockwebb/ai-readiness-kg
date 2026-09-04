# CC Task — Extract the 17 `g1eval-2026-09-02` prior-art sources; rerun diagnostic and CQ v1

**Date:** 2026-09-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Premise (registered):** `kg_diag_gap_never_queued` = 17, all epoch `g1eval-2026-09-02` (RESULT of `2026-09-04_extraction_gap_diagnostic`, §1, §3).
**Spend:** model spend, bounded. §3 of that RESULT priced this at 664 chunks, ≤13,280,000 tokens reserved at the DD-022 floor, 24% of the 55M daily band. Inside the standing band; no operator touchpoint. Reserve-then-settle through the guard as normal. **Claude Max OAuth only. Any path that reads `ANTHROPIC_API_KEY` is a stop condition, not a fallback.**

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. Decision recorded

The 17 are extracted because they are the sources the G1 memo cites and the two hardest CQ failures (CQ-01 uncertainty definitions, CQ-02 AI-ready definitions) have the most unextracted evidence behind them (27 and 23 documents). The 55 DD-024 deferrals stay deferred: reviving them is a reversal of a standing decision and the CQ rerun in §3 is what would justify it. Append this as a dated DD entry (`docs/design_decisions.md`).

## 1. Extract

1. Emit `extraction_request` for exactly the 17, using the sanctioned path (`kg/queue_cli.py`, or `scripts/run_bulk_extraction.py --docs` — read `cc_tasks/2026-08-30_bulk_extraction_v038*.md` and its addenda for the profile and invocation that produced the 35, and use the same). Profile `bulk_v038` unless the queue's pinned profile has moved; report which.
2. Run. Spend guard reserve-then-settle; record reserved vs settled tokens per document and in total. If settled exceeds 13.28M, stop at the document boundary where it crosses and report; do not continue.
3. Chunk-level extraction, as the pipeline does it. No whole-document single-call path.
4. Projection replay so the 17 acquire edges. Confirm `run_ok_no_edges` stays zero (rerun `scripts/extraction_gap_diagnostic.py`; its `never_queued` must read 0 and nothing else may change class).

## 2. Diagnostic rerun

`scripts/kg_diagnostic.py` → new dated snapshot and a new set of `kg_diag_*` Results (dated suffix or a `run` property — follow whatever convention the first run established for reruns; if none, `kg_diag_<metric>_2026-09-04b` and record the convention in the DD entry). Report the delta table for every figure: Concept count, duplicate groups, degree distribution, domain edges, Claims, cross-document edges.

## 3. CQ v1 rerun — same set, no edits

`assessment/cq/run_cq.py` against `cq_set_v1.yaml` at commit `369d717`, unchanged. New dated results file and new `cq_v1_*` Results; never overwrite. Report per-CQ before/after for both views, the four aggregates, and `flip`. The pre-registered rule of the harness task §1.5 is re-evaluated on the new `flip` and the branch reported. Judge caveat applies as before; cite grounding spans.

This is the before/after. Interpretation is Desktop's; do not draw the corpus-revival conclusion here.

## 4. Doc fix

`CLAUDE.md` "v1 frozen at 71 docs, 71/71 extracted" → correct to reflect the ITU cut (`extent_unremediable`), one sentence, cite the diagnostic RESULT §1.

## 5. Integration

`tests/` and `assessment/` green; `seldon verify` clean; Script/DataFile/Result registration for the run; `cc complete`; commit and push including the spend ledger delta.

## 6. RESULT must report

Per-document reserved/settled tokens and totals; extraction profile; projection replay confirmation and the gap diagnostic reread; the full diagnostic delta table; the CQ before/after table and the rule branch; premises contradicted.

## 7. Out of scope

The 55 deferred documents. The 22 fixture-epoch documents without Document nodes (`2e226acb`). Entity resolution (`93a628e8`). CQ set v2. The admission-does-not-enqueue design question (`609cb10b`).
