# TEVV Phase 0 — Preflight (task 2026-08-22_kernel_tevv, Seldon de7ae80b)

- Tests at baseline: **117 passed**. After Phase 0 additions: **125 passed**.
- `controls.yaml` before: `611d5dda0834900ea77ca619f8d0cd4368efb471cd3914ac76a15378b5344684`; task-duration (`extract: on`, `extract_daily_docs: 20`): `2e25969089903b75dc5d3d8523051350bb0d12a8ff0cb05a818d5a35696e148f`. Prior copy saved for byte-identical restore.
- `ANTHROPIC_API_KEY` unset (verified).

## Schema v0.3.1 (append-only)
`Document.is_platform_operator` (boolean, nullable) added to `kg/schema.yaml` and `docs/schema_v0.1.md` (changelog + §2 row). `tests/test_schema_append_only.py` extended with a frozen v0.3 catalogue (node/edge types, the evidence_grade enum) that v0.3.1 must preserve, plus the new property. One existing test asserted the exact string `"0.3"`; relaxed to the v0.3 line (patch releases are append-only by construction).

## is_platform_operator population (DD-014)
Rule + lexicon: `scripts/platform_operators.yaml` (operators with what they operate; excluded organizations with reasons). Script: `scripts/annotate_platform_operator.py` → **134 `document_annotation` events in `events/batch-007.jsonl`** (rule version `2026-08-22.1`). Decision table: `docs/research/2026-08-22_tevv_platform_operator_decisions.md`.
- **30 true / 104 false.** True: Google Search Central ×6, Google Chrome Developers (Lighthouse), Microsoft Bing ×3, Microsoft/Playwright, IndexNow, Cloudflare ×3, Akamai ×2, OpenAI, Anthropic, Perplexity, sitemaps.org, Pearson/AWS, and every GSA document (DAP, Search.gov, website standards, Site Scanning, DCAT-US ×3, GSA AI CoE guide) — GSA resolves **true** per the task rule, note recorded per row.
- Deliberate false with reasons (in the lexicon file): U.S. Census Bureau (API, not a platform), Schema.org CG, IETF (RFC 9309 — Google-employed authors, IETF issuer), Zyte/Scrapy (tooling vendor), W3C/SDMX/MLCommons/OpenAPI/Answer.AI, policy bodies, vendors/consultancies/tool projects.
- Literal-rule artefacts flagged: `ai-readiness-building-the-bridge…` (Pearson; AWS → true because Amazon operates Amazonbot/Kendra, though the document is about higher-ed) and `gsa-ai-guide…` (v1 doc, GSA → true by the task's GSA ruling). Both noted in the decision table.

## Projection / event log support added
- `build_projection.py`: `document_annotation` events set whitelisted Document properties (only `is_platform_operator`; the property name is never taken from the payload); events flagged `purpose: tevv_retest` are skipped and counted (`skipped_non_graph_purpose`). Tests: `tests/test_build_projection_filters.py`.
- `kg/eventlog.py`: tagged shards `batch-NNN_<tag>.jsonl`; `append(..., tag=)`, `replay(tag=)`. Default replay excludes tagged shards, so the retest shard the task names (`events/batch-008_tevv_retest.jsonl`) can never reach the projection, gates or monitors by accident. Tests added; graph replay count unchanged (22,598 events).
