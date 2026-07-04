# Bulk Acquisition Report (final)

**Task:** cc_tasks/2026-07-03_bulk_acquisition_v2.md (+ crawl4ai/Wintermute-pattern recovery)  
**Date:** 2026-07-03 → 2026-07-04  
**Corpus: 71 documents manifested** (18 of them web pages captured as cited markdown via crawl4ai; the rest are PDFs — preprints, papers, statutes, EOs, OMB memos, NIST/FCSM reports, the Zenodo crosswalk).

Screening: manifested 71, excluded 2, needs_source 18 (operator inbox), pending 0.

## Method

- **Documents first** (your priority): real PDFs via deterministic patterns — govinfo statute/FR PDFs, arXiv, DOI/Zenodo.

- **Web pages → markdown** via crawl4ai (`crwl`), cited by URL, with a min-content guard (no blank captures) and Wintermute's WAF/paywall blocklist reused to route blocked hosts straight to the operator inbox (no retry-loop).

- **Blocked → operator inbox** (docs/research/operator_inbox_handoff.md): paywalled papers, JS-only SPAs, PMC, and no-URL items.


Acquired PDFs and markdown captures are gitignored (corpus/bulk, corpus/bulk_md); provenance (primary_url + content_hash + TEVV) travels in the manifest events. manifest.verify() clean.

## Operator inbox queue (18)
See docs/research/operator_inbox_handoff.md.

