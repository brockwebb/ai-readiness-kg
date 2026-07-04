# CC Task — Bulk Acquisition (candidate register → manifest)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Independent of the schema v0.2 task — parallel-dispatchable.**

## Objective

Manifest-add every candidate register entry that (a) has a usable primary URL and (b) is not already in the manifest. Acquisition only — zero extraction.

## Rules (pilot-adds pattern, now at scale)

- Fetch from primary URL only. Per-doc TEVV evidence (fetch record, identity check vs register, sha256 + re-hash, substantive-document check, page count) in the manifest-add events. All writes through the manifest module.
- Per-doc failure handling: fetch failure / identity mismatch / error-page = record and continue to the next document. No substitutions, no guessed URLs, no out-of-band sources. needs-source entries skipped by definition.
- PDFs to gitignored corpus locations (pilot pattern). Landing-page-only entries (e.g. the OECD.AI Index website): attempt to resolve a stable document PDF from the page; if none resolves, record as needs-source and move on.
- The webb_nist_fcsm_crosswalk entry: DOI is https://doi.org/10.5281/zenodo.18772590 (task cc082aaa) — update its register entry and acquire via the DOI. Close cc082aaa on success.
- Batch commits every ~15 docs so a crash loses little.

## Deliverables

1. Manifest entries + events for all acquirable candidates.
2. docs/research/bulk_acquisition_report.md (committed): counts (acquired / failed / needs-source / already-manifested), the full failure list with reasons and leads, register status updates applied.
3. `seldon cc complete cc_tasks/2026-07-03_bulk_acquisition.md`; `seldon verify` clean.

## Out of scope

Extraction. Ingested transitions. Manual-inbox items (operator drops → inbox convention → follow-up task). Any content edit to register entries beyond status/URL corrections named above.
