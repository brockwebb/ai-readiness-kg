# CC Task — cited documents metadata, second attempt: the entry point, the backfill, the test that follows it

**Date:** 2026-09-12
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-12_cited_documents_metadata_RESULT.md` §2.4, §3, §4, §6 item 2. Supersedes `2026-09-12_cited_documents_metadata.md` (stopped at §1) once this task registers; that task's RESULT stands as the record of why.
**Implements:** DN-002 decision 4; under DD-001 and DD-003.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs after `2026-09-12_dixie_metadata_corrected.md` and before `2026-09-12_publish_l0.md`. Closes `e6765ba6` on completion, because this is the task that does its work.
**Spend:** zero model calls. **Network: none.**

**Decisions taken here (operator overrides later):**
1. **`kg/manifest.py::metadata_update(doc_id, *, provenance, **fields)`**: validates the doc_id is admitted; refuses any field outside `identity.*` / `acquisition.*`; appends `metadata_corrected` to the Dixie ledger through `dixie.evidence.eventlog.EventLog.append`, never to `events/batch-*.jsonl`. CLI verb `python -m kg.manifest metadata-update`. Consumer picks up the dixie change the way the previous RESULT says it is pinned.
2. **Backfill the ten citation gaps** from the documents on disk, each value with the page or line it was read from in `provenance`; the previous RESULT §3 already read the two federal ones (Public Law 115-435, 2019, 115th Congress; M-25-05, 2025, OMB). A value the document does not state stays empty and is listed. Issuing body counts as author for federal, standards and vendor documents.
3. **`rebuild`, then the projection; `acquired_at` is filled for all 377 by the dixie change, not by any write here.** The RESULT reports the count filled by `file_observed` versus `inbox_ingested`, and any entry still null (expected 0).
4. **The test follows the backfill**: a manifest test forbids null `acquired_at` on every entry and forbids `method: unknown` on any entry admitted after 2026-09-12; a second test asserts every appendix doc_id has author, year, title, `source_url`, or is in a named list carrying the reason the document itself does not state the field.
5. **Report rebuilt** through `make report-pdf`; prose untouched; page counts registered under `_2026-09-12` names only if they moved.

**Zero edits to:** corpus file bytes and hashes, `events/batch-*.jsonl`, rule modules, harness, payloads, prior Results, prior RESULTs, figures, the skeleton, the record, section prose.

**Immutable once written. Glob `2026-09-12_cited_documents_metadata_2_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decision 1. The entry point; a dry run of one correction against the ledger shows the event and the projected entry. Stop if the consumer does not see the dixie change.
## 2. Decisions 2, 3, 4, 5.
## 3. Gate (the one gate of this task)
Ten corrections on the ledger with provenance; `rebuild` reproduces the manifest with exactly those fields and the `acquisition` fills changed, shown as a diff summary; `python -m kg.manifest verify` clean; 0 null `acquired_at` across 377; both new tests green; appendix regenerated with the citations; PDF numeral-multiset gate and tag-coverage lint green; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes no ledger event and no PDF: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-12_cited_documents_metadata_2_RESULT.md`: per doc_id the values and where read; the fill counts; the appendix rows before and after; every premise wrong. Close `e6765ba6` with whatever verb the CLI offers (`seldon task close` or the graph's `completed` transition); if none exists, say so and leave it `proposed`. `seldon cc complete`, commit, push. Final message states the counts and whether the push succeeded.

**SEQUENCING:** §1 (stop if the consumer lacks the dixie change) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
