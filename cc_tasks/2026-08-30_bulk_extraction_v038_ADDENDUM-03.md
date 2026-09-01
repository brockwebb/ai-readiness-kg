# ADDENDUM-03 — 2026-08-30_bulk_extraction_v038.md

**Date:** 2026-08-31 (evening). **Immutable once written.** Operator-authorized follow-on (touchpoint 1, spend). Base task, ADDENDUM-01/-02, and the standing RESULT govern everything not named here. Append to the existing RESULT.

## Gate

Runs ONLY after the ADDENDUM-02 scoped set (b002–b013 minus deferred) is complete and no bulk process is alive. Verify both: last scoped batch's verdict on disk, and process liveness checked and recorded. If the scoped burn stopped on the corpus stop rule, this addendum is VOID — an incident report outranks a follow-on.

## The two mechanical items owned by "next burn start" (ingestion RESULT §3, extent RESULT §6)

1. **Substrate wiring:** in `run_bulk_extraction.doc_text`, consult `kg.ingest.gate.substrate_path(doc_id)` before the suffix dispatch; fall through to the existing paths when no substrate exists. One lookup; the burn scripts are editable now that no burn is running. Test: a doc with substrate reads substrate; a doc without reads exactly what it read before (no behavior change for the 194-doc status quo).
2. **Revive b014/b015** (odcs 45 chunks, slsa 32 chunks — ids frozen in `burn_plan_cut`, never renumbered): emit their `extraction_request` events under the pinned v0_3_8 profile. This executes ADDENDUM-02 §2.3's recorded decision; the substrate now exists and clears the DD-030 gate (extent RESULT §2).

## Execution

Standing rules, no exceptions: per-batch formula ceilings declared on the ledger; SPRT per batch with the fixed p0/p1/α/β; both DD-024 enforcement layers active; chunk-level resume; daily band binds. Two batches, dispatched in id order. Expected ~4M extraction + judging per the running means; if the daily band lacks headroom tonight, the batches wait for the reset — the band does not move.

## Completion

`seldon cc complete` the base task when b014/b015 verdicts are on disk (or the stop rule fires — completion WITH incident report per DD-029). Final RESULT append: full-burn reconciliation across ALL batches including these two — coverage achieved vs the ~85% now expected, total settled vs total declared, refusal totals, quarantines (expected: none), `kg queue status` totals.
