# ADDENDUM-01 to `2026-09-04_extract_g1eval_17_and_rerun.md`

**Date:** 2026-09-04
**Authored by:** Desktop session
**Status:** AMENDS. Resume, do not restart.
**Reason:** RESULT stops at §1.3. Extraction (§1) is complete: 688/688 chunks, ingested. §2–§5 never ran; task still `proposed`; no new `cq_v1_*` Results exist.

**Immutable once written.**

---

## 0. Resume point
Do not re-emit any `extraction_request`, do not re-run extraction, do not touch the spend ledger except to read it. Verify by query that the 17 have edges and that `kg_diag_gap_never_queued` re-computed reads 0. Then execute base §2, §3, §4, §5 exactly as written. Write the output as `…_RESULT-02.md` (the partial RESULT stands as the record of §1).

## 1. Spend accounting, added to RESULT-02
Report three numbers side by side: declared ceiling (13.28M), productive settled (31.30M), wasted settled (15.07M). Register each as a named Result (`g1eval_extraction_tokens_<declared|productive|wasted>`), Script = the driver, DataFile = the spend ledger snapshot. The estimate error is a Desktop authorship defect: append to `docs/design_decisions.md` (DD-next) that any spend ceiling declared for a profile with a measured rate on the ledger must be computed from that rate, and that the guard will enforce it (task below).

## 2. Concurrency defect `830330b4` — fix after §2–§5, same session, before `cc complete`
`chunked_pilot.phase_extract`: replace submit-all-then-cancel with bounded waves (wave size = worker count), testing `streak >= STOP_AFTER_FAILURES` before each `submit()`, and collecting every completed future's outcome so failures are counted, not skipped. Test: a fake executor that fails from call N onward must show at most `workers` extra billed calls after the streak trips, and the failure count in the log equals the settled `error_with_output` count. Run the existing extraction tests. No live burn to verify; the test is the verification.

## 3. Guard enforcement — register, do not implement
`seldon_task_create` (this project): "DD-022 guard: `declare()` refuses a ceiling below `measured_rate(profile) × planned_chunks` when the ledger holds a measured rate for the profile; reports the computed floor. Estimate floors are for first-call reservation only."

## 4. Integration
As base §5, plus: RESULT-02 cites RESULT §1 for extraction and does not repeat it.
