# Design note — the L0 product: shape, length, critical path

**Date:** 2026-09-08. Desktop design note; not a task. Governs the authoring of `report-draft` (`2517cda8`).

## What L0 is
The six host-level legs (`params.tier0.legs`: A4, A5, A10, A11-declared, A12, G1-D) over the 16 OMB-recognized statistical agencies, one cycle, identified client. Three reference hosts (data.gov, NIST, GSA) shown separately, never in the agency denominator. Nothing else is L0.

## The product
One matrix. 16 rows (agencies), 6 columns (legs), verdict cells (pass / fail / error / n.a.), plus one column for "refused the identified client." A second, smaller block for the three reference hosts. That matrix is the report. Everything else exists to let a stranger trust one cell.

Length target: the matrix on one page, and at most six pages around it:
1. What was measured and why (the frame: who the 16 are, why these 6 checks, one paragraph each).
2. The matrix.
3. What the matrix cannot see (non-claims): product-level readiness, rendered pages, whether any machine actually used the data, and anything about hosts that refused us.

   **How much that is, measured against an outside instrument** (`cc_tasks/2026-09-10_corpus_noaa_esip.md`, `state/crosswalk_esip_ai_readiness_2026-09-10.json`). The ESIP Data Readiness Cluster's *Checklist to Examine AI-readiness for Open Environmental Datasets* v.1.0 asks **58** assessable questions of a dataset. Of those, this instrument measures **9 fully** and **13 by a public-surface proxy**; **36 it cannot see at all**. The 36 are not a gap in the framework — 14 framework indicators cover them — they are the difference between reading a SURFACE and reading the DATA: completeness, consistency, bias, resolution, gridding, labels, provenance and the data dictionary are properties of the dataset, and nothing published on a product page settles them. Section by section the split is stark: Data Access is 6 full of 14, Data Quality is 0 full of 18, Data Preparation is 0 of 4.
   That is the honest statement of this instrument's reach, and it is a reason to publish the crosswalk beside the matrix rather than a reason to widen the matrix.
   **Against NOAA's own definition** (`state/crosswalk_noaa_ai_ready_2026-09-10.json`). NAO 216-128 §3.01 — signed and effective 2026-04-16 — defines AI-Ready Data as *"discoverable, machine-readable and machine-understandable, and has sufficient quality, documentation, and access methods to support the full AI application development and use life cycle."* Of its five components this instrument measures **three in full** (discoverable → A4/A5/A11; machine-readable and machine-understandable → A1/A2/A6/A8/D1; access methods → A9/B3/F4), **documentation in part** (licence and vintage, not variable-level metadata), and **quality not at all** — the definition's word is *sufficient*, a judgement about the data against a use, and no leg inspects the data.
   Three of five is the honest coverage claim for a surface instrument against a data definition, and the one component it cannot reach is the one that would need the data itself.
   The document was fetched from the operator's copy, not from the source: `www.noaa.gov` answered HTTP 403 to the identified client on both NAO URLs while its own robots.txt permitted the path. It is a scanned image, so every span above is grounded against an OCR reading (tesseract 5.5.0, mean word confidence 94.52) whose engine, rasterisation and one known substitution are recorded in `corpus/noaa_esip/NAO_216-128.ocr.json`.
4. What moved between cycles and whether the instrument or the host moved it.
5. Future research, one sentence each, each backed by evidence already in hand: refusal-by-identity (`ae58c74e`), third-party observed access (`43108db6`), product-level legs, EVAL.
6. Method appendix: pointer to the graph, the rules by version, the fixtures, the request counts per host.

No figure that restates the matrix. F1 to F6 are working charts for the graph page; the report carries the matrix and at most one figure of movement across cycles.

## Numbers
Every number in the report is a registered Result quoted by name via `{{result:NAME:value}}`. No prose number. The matrix is rendered from `scan_matrix_<cycle>` and `scan_matrix_tierc_<cycle>`, not typed.

## Critical path to L0
`f7cfc43f` (A8-v4 + derived fixture tables) → `3b47290e` (scan-run-3b) → `2517cda8` (report-draft) → operator reads → ships. Three tasks. Nothing else is on it. `43108db6` and `ae58c74e` are behind it.

## Above L0
Product-level legs (A1, A2, A3, A6, A8, A9, B3, D1, D4, F4) already run in cycles 1 and 2 on the earlier surface list and stay in the graph. Levels above that (rendered DOM, log-file access, Search Console, EVAL) need owner access or paid tooling and are linked into the same graph when acquired, not redesigned. The graph is the product that scales; the report is a projection of it at one date.

## Publishing the product as AI-ready
The report and matrix are published so they pass the instrument's own host-level checks: a machine-readable matrix beside the PDF (CSV + JSON), schema.org `Dataset` markup on the page, a declared license, a `data.json` entry, robots.txt permitting identified crawlers, and the graph reachable by an LLM through the existing MCP/Cypher path. The report's own L0 row is the last row of the matrix.
