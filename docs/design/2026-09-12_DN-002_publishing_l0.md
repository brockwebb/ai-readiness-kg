# DN-002 — Design note: publishing the L0 report

**Date:** 2026-09-12. Desktop design note; not a task. Governs `2026-09-12_cited_documents_metadata.md` and `2026-09-12_publish_l0.md`. Under DD-001 (stranger rule), DN-001 (citation floor, met as of `6acce1c5`), and the 2026-09-08 L0 product shape note.

## Decision

1. **Machine-first, the PDF is a projection.** What publishes is the data: the matrices as JSON and CSV, the per-check source appendix as JSON, the registered Results the report tags, the framework record, and a pointer to the corpus manifest. The PDF and the built markdown are human views of those and link to them. The site index says so in one sentence.
2. **The site passes its own checks.** The published host carries `robots.txt` that admits the identified AI clients the instrument uses, `llms.txt`, and a sitemap. The harness's six tier-0 legs run against the published host with the identified client, the verdicts are registered under `self_`-prefixed names, and the index prints them outside the agency matrix, the way the three reference hosts are shown. A host that publishes an AI-readiness instrument and fails its own level-0 checks has no standing.
3. **Result states are real before publication.** Every Result the report tags moves `proposed → verified` on a fresh re-derivation that reproduces its value, and `verified → published` in the publish commit, each with an event. A tagged Result that cannot be re-derived is a stop, not a footnote. If the registry has no state transitions, that is a Seldon defect and publication waits on it.
4. **Cited documents carry citation metadata.** Every doc_id in the appendix has author or issuing body, title, year, `source_url`, and `acquisition.acquired_at` (recovered, or recorded as unrecoverable with `integrity.checked_at` as the earliest attestation). Nothing is back-filled by guess.
5. **DOI and version.** `CITATION.cff` and a Zenodo metadata file are prepared; the mint is the operator's action under his name. The report carries its own version identifier (the snapshot cycle and the git commit) on the title page.
6. **Enabling or configuring GitHub Pages is the operator's.** The task prepares the tree Pages serves; it does not change account settings.

## What publishing does not wait for

`44ba0fd0` (measurement-spec regenerator, E5 write-back), the KG extraction and entity-resolution debt, product-level completeness, the January G1 pilot. Those are the next big steps, not conditions of this one.
