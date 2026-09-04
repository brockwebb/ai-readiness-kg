# CC Task — Diagnose the 72 unextracted Documents

**Date:** 2026-09-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Spend:** zero model spend. This is diagnosis only. Extraction, if warranted, is a separate task with its own spend line.
**Premise (registered, not chat):** `kg_diag_documents_without_extractions` = 72 of 211 (RESULT of `2026-09-04_kg_diagnostic_and_cq_harness`, §0.1).

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. Why this is first

Coverage precedes conciseness. A third of the admitted corpus has no extraction edges; every CQ that failed may have failed for that reason rather than for duplication, and entity resolution (`93a628e8`) must run once over a complete corpus, not twice. Nothing else in the KG line moves until the cause is known.

## 1. Classify all 72

`scripts/extraction_gap_diagnostic.py`, output `state/extraction_gap_2026-09-04.json` (register as DataFile, `snapshot: true`), every count registered as `kg_diag_gap_<class>`.

For each of the 72 Documents determine, from the acquisition ledger, the extraction event log, the spend ledger and the corpus files on disk (`docs/corpus/`, `assessment/`, wherever the pipeline keeps them — read the pipeline code, do not guess), exactly one class:

| class | meaning |
|---|---|
| `never_queued` | admitted to the corpus, never entered the extraction queue |
| `queued_not_run` | in the queue, no run event |
| `run_failed` | a run event exists with an error (record the error class) |
| `run_ok_no_edges` | extraction ran and produced output, but the projection loaded nothing (loader defect) |
| `excluded_by_design` | a documented rule excluded it (e.g. unconverted PDF, non-English, duplicate of another Document) — cite the rule |
| `source_missing` | the source text is not on disk |

Also record per Document: source format, byte size, corpus epoch, admission date, and whether the Document node has `content_hash`.

## 2. Cross-check against the CQ failures

For the 6 CQs that were `no`/`partial` in the collapsed view and the 8 flagged `misleading_raw` (from `assessment/results/cq_v1_2026-09-04.jsonl`), grep the 72 Documents' source text for the CQ's key terms. Report which CQ failures have at least one unextracted Document that mentions their terms. This is the measured overlap between the coverage gap and the conciseness finding; it is a count, not a judgment.

## 3. Estimate, do not execute

For the classes that would be closed by running extraction (`never_queued`, `queued_not_run`, `run_failed` where the error is transient), compute the chunk count under the pipeline's current chunking and the token estimate the spend guard would reserve. Report the number. Do not run extraction. If the estimate exceeds the standing spend band in `~/.wintermute/docs/decisions/2026-08-15_l4-operating-doctrine.md` or this project's equivalent, say so explicitly — that is one of the four operator touchpoints.

## 4. Findings to register (Issues, no fix)

- Any `run_ok_no_edges` Document: loader defect, one Issue for the class with sample ids.
- Any `excluded_by_design` rule that is not written down anywhere: that is a rule living in code only; Issue.
- If admission never enqueues extraction (i.e. `never_queued` is the pipeline's normal state after admission), that is the structural defect: Issue, with the code location.

## 5. Integration

Script registered; DataFile registered; Results named. `seldon verify` clean. `cc complete`; commit and push.

## 6. RESULT must report

The 72-row classification table (compact: class, count, sample ids); the per-class root cause with code/ledger citation; the CQ-overlap counts from §2; the §3 estimate and whether it is inside the standing band; Issues registered; premises contradicted.
