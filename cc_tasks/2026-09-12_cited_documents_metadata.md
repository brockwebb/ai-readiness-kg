# CC Task — every document the report cites carries citation metadata and a retrieval date

**Date:** 2026-09-12
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-12_a1_a8_b3_d4_sources_RESULT.md` §6 decision 5, §9 items 1, 2; and `2026-09-11_a3_a10_sources_RESULT.md` §10 item 1.
**Implements:** DN-002 decision 4 (`docs/design/2026-09-12_DN-002_publishing_l0.md`); under DD-001 and DD-003. Absorbs ResearchTask `e6765ba6`, closed as superseded in §4.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs before `2026-09-12_publish_l0.md`.
**Spend:** zero model calls. **Network: none.** Metadata comes from the documents already on disk and the harvest logs; nothing is fetched.

**Why this task exists.** Ten cited documents render in the appendix as title + URL because the manifest holds `n.d.` or `(unspecified)`; two of them are the statute and the current OMB guidance the report leans on for three checks. And `acquisition.acquired_at` is null for every kernel-harvested document, so no citation can answer "as of when". Followable is not citable.

**Decisions taken here (operator overrides later):**
1. **Author, year, title, `source_url` for every doc_id the appendix names.** Values are read from the document on disk (title page, colophon, front matter, RFC header, statute enactment date) and recorded with the page or line they were read from in the manifest entry's provenance note. A value that is not on the document is not typed; the field stays empty and the RESULT lists it. Issuing body counts as author for federal and standards documents.
2. **`acquired_at` is recovered from the harvest logs** (`scripts/harvest_kernel.py` output, Dixie ledger, git history of the corpus file) where a timestamp exists; where none does, the field is set to the literal `unrecoverable` and `acquisition.earliest_attestation` is set to `integrity.checked_at`. A manifest test forbids null `acquired_at` on every entry from now on and forbids `unrecoverable` on any entry added after 2026-09-12.
3. **Manifest edits go through `kg/manifest.py`**, appending a `manifest_update` event per entry with before/after; if the module has no update verb, §1 stops and the RESULT says what the verb would need. Then `rebuild`, then the projection; the appendix regenerates on the next report build and the RESULT shows the rows before and after.
4. **The report is rebuilt** so the appendix carries the citations; prose untouched; page counts registered under `_2026-09-12` names only if they moved.

**Zero edits to:** corpus file bytes and hashes, rule modules, harness, payloads, prior Results, prior RESULTs, figures, the skeleton, the record, section prose.

**Immutable once written. Glob `2026-09-12_cited_documents_metadata_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decision 3. The manifest path. Stop if there is no event-bearing update verb.
## 2. Decisions 1, 2, 4. Read, record, recover, rebuild.
## 3. Gate (the one gate of this task)
Every appendix doc_id has author, year, title, `source_url`, and a non-null `acquired_at` (timestamp or `unrecoverable` with attestation); the manifest test is green; every metadata change is on an event with provenance; corpus file hashes unchanged; appendix regenerated with 0 placeholder-omitted fields for cited documents (or the RESULT's list of what the documents themselves do not state); PDF numeral-multiset gate and tag-coverage lint green; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes no manifest change and no PDF: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-12_cited_documents_metadata_RESULT.md`: per doc_id, each value and where on the document it was read; recovered versus unrecoverable dates with the source of each timestamp; the appendix rows before and after; every premise wrong. Close `e6765ba6` as superseded by this task via the CLI. `seldon cc complete`, commit, push. Final message states the counts of recovered and unrecoverable dates and whether the push succeeded.

**SEQUENCING:** §1 (stop on no update verb) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
