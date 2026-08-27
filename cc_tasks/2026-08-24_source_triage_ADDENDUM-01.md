# ADDENDUM-01 to `2026-08-24_source_triage.md` (Seldon 7456614d)

**Date:** 2026-08-26
**Reason:** CC stopped at Phase 0 — the operator transmission (input 1) was not in the execute prompt and does not exist in the repo. Root cause: the source list was pasted into a Desktop chat on 2026-08-24 and never landed on disk. LLM retyping of a ~40 KB tab-separated table is not a verbatim copy; the citable record must be the operator's file, not a transcription.

## Change to Phase 0

Input 1 is delivered as a file drop, not as pasted text.

- The operator places the original export at **`docs/research/2026-08-24_sme_source_list.tsv`** (tab-separated, header row `Industry	Title	Author/Organization	Year	Publication	Link/Location	Summary	Tags (comma separated)`). If the operator drops `.xlsx` or `.md` instead, accept that filename; do not convert or reformat.
- The transmission also carried one item **above** the table, as a bare link: *The Microstructure of AI Diffusion: Evidence from Firms, Business Functions, and Worker Tasks* — https://www.census.gov/library/working-papers/2026/adrm/CES-WP-26-25.html. Treat it as an input-1 row (Industry=Government, no summary, no tags). If the drop file omits it, add it to the register from this addendum and log `source: addendum-01`.
- CC does **not** write `2026-08-24_sme_source_list.md` from context. Phase 0 instead: verify the drop file exists, record its sha256 and byte size in the Phase 0 sub-RESULT, and proceed. If the file is absent, STOP as before.
- All other Phase 0 items (schema v0.3.3 append, `grounding_surface` register field, backfill rule) unchanged.

## Premise check to log (Phase 2)

The task states 10 `community-dc.max.gov` decks. The Desktop-side reading of the transmission shows 9 (2026-C2.1 Webb, C2.2 Hoppe, C2.4 Belyaeva, C2.5 VanWart, FCSM AI-Ready Data WG Kopp, 2024-D1.1 Harper, D1.2 Christensen, D1.3 Haase, D1.4 Iwugo). Count from the drop file and report the actual number in the operator download list; a 9 vs 10 mismatch is a recorded discrepancy, not something to reconcile.

Likewise "2 YouTube, 1 vlog": count the actual video/podcast rows from the file (the Desktop reading shows two `youtube.com` rows — Presley/Data Unchained and Sequeda — plus two `lakefs.io/ai-ready-data-summit` session rows with no direct media URL). Route lakefs rows as `fetch_failed` unless a transcript or slides are fetchable from the summit page; log which.

## Execute line for the re-run

`Execute cc_tasks/2026-08-24_source_triage.md. Glob and read all cc_tasks/2026-08-24_source_triage_ADDENDUM*.md first. Input 1 is on disk per ADDENDUM-01.`
