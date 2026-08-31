# ADDENDUM-01 — 2026-08-27_extraction_queue.md

**Date:** 2026-08-30. Base task immutable; this addendum corrects stale bindings accumulated since 08-27. Binding. Read with the base file; on conflict, this addendum wins.

## 1. DD renumbering (the blocking defect)

The base task reserves **DD-023**. That number is occupied (DD-023: chunk unit / anchor contract, 2026-08-27/28, plus two errata). The design-decision log's high-water mark verified 2026-08-30 is **DD-026**.

**This task's DD is DD-027.** Every occurrence of "DD-023" in the base file (Result header, Deliverables checklist) reads DD-027. Verify DD-027 is still free by reading `docs/design_decisions.md` at start; if occupied by then, take the next free number and state which in the RESULT.

## 2. Stale numbers — derive, don't trust the base prose

- **Manifest count:** base file's "currently 168" is stale; acquisition round 2 landed the manifest at **194 included** (commit 750a2b6). §7's reconciliation test reads the live included count from the event ledger at test time. No hardcoded totals anywhere in tests.
- **Backfill counts (134 + 34):** epoch-scoped and probably still correct, but derive both from the ledger (kernel-epoch extraction events; `triage-2026-08-24` manifest epoch), report the derived counts in the RESULT, and note any discrepancy against the base prose. Discrepancies reported, never reconciled (base rule stands).
- **Schema version:** base says "schema v0.3.5 append". Read `kg/schema.yaml`'s current version at start and append to whatever it actually is. The append-only test binds to the observed version, not v0.3.5.

## 3. Moot coordination clause

The base header's "runs in parallel with cd8449de's lanes" is moot — that burn task completed 2026-08-27. The coordinate-by-reading-fresh discipline on `kg/extraction/state.py` and `scripts/run_bulk_extraction.py` still applies (other tasks may be in flight); the specific cd8449de reference does not.

## 4. Profile pin is about to move — projection must read it, never hold it

Task 35094dc4 (ground-truth yield re-derivation) is in flight and will select the production profile (v0_3_8 or v0_3_9) by measurement. The `extraction_state` projection's "current pinned profile" MUST be read from the pin source (`run_profiles` / config) at projection time, never captured as a constant. Add a test: flipping the pinned profile flips `extracted` → `stale` for documents extracted under the old pin, with no code change.

## 5. Erratum, from the 2026-08-30 session close

`source_type` is what you pass in (admission API); `doc_type` is what you read back (projection). Both names are live in the codebase. Do not "fix" this by renaming either — use each on its own side.

## 6. Spend declaration (DD-022)

Zero-model-spend task, restated as a ledger fact: declare `--ceiling-tokens 0` on the ledger at start. Any model call under this task is a defect, not an overage.

## 7. Preamble (standard, restated)

Glob and read every `cc_tasks/2026-08-27_extraction_queue_ADDENDUM*.md` before starting (this file and any later siblings). RESULT filename unchanged: `cc_tasks/2026-08-27_extraction_queue_RESULT.md`. `seldon cc complete` the base file at the end; commit, push.
