# Triage decision log — 2026-08-24 SME source list + SEO/AIO gap harvest

Task: `cc_tasks/2026-08-24_source_triage.md` (Seldon 7456614d) + ADDENDUM-01/-02. Run 2026-08-26/27 UTC, zero model calls.
Rules R1–R5 as written in the task file; every verdict below names its clause.
Machine-readable record: `corpus/staging/inbox/triage_2026-08-24/_fetch_register.json` (local, gitignored staging);
durable provenance: `events/batch-014.jsonl` (34 manifest_add + 134 construct_arm document_annotation) and 72 candidate_register lines.

## FOR OPERATOR REVIEW — surfaced first

### Off-construct flag (R4) — awaiting confirmation, not fetched, not manifested
- **Census CES-WP-26-25** — *The Microstructure of AI Diffusion* (row 1): AI adoption/diffusion economics; R4 named it explicitly.

### Access-blocked (operator can supply PDFs via `corpus/staging/inbox/`; nothing waits)
- row 36 **rfi-comment-deloitte-2024** — Comment of Deloitte Consulting LLP on the DOC AI and Open Government Data Assets — blocked at `downloads.regulations.gov` (HTTP 403 / not a PDF (text/html) [final_url=https://downloads.regulati)
- row 37 **rfi-comment-leidos-2024** — Comment of Leidos on the DOC AI and Open Government Data Assets RFI — blocked at `downloads.regulations.gov` (HTTP 403 / not a PDF (text/html) [final_url=https://downloads.regulati)
- row 38 **rfi-comment-microsoft-2024** — Comment of Microsoft on the DOC AI and Open Government Data Assets RFI — blocked at `downloads.regulations.gov` (HTTP 403 / not a PDF (text/html) [final_url=https://downloads.regulati)
- row 39 **rfi-comment-openai-2024** — Comment of OpenAI on the DOC AI and Open Government Data Assets RFI — blocked at `downloads.regulations.gov` (HTTP 403 / not a PDF (text/html) [final_url=https://downloads.regulati)
- row 40 **rfi-comment-protesero-2024** — Comment of Protesero on the DOC AI and Open Government Data Assets RFI — blocked at `downloads.regulations.gov` (HTTP 403 / not a PDF (text/html) [final_url=https://downloads.regulati)
- row 41 **rfi-comment-sas-2024** — SAS Response to AI and Open Government Data Assets RFI — blocked at `downloads.regulations.gov` (HTTP 403 / not a PDF (text/html) [final_url=https://downloads.regulati)
- row 53 **verhulst-2025-fair-r** — Moving Toward the FAIR-R principles: Advancing AI-Ready Data — blocked at `papers.ssrn.com` (HTTP 403 / not a PDF (text/html; charset=UTF-8) [final_url=https://pap)
- row 59 **greenberg-2026-metadata-ecosystem-ai** — The metadata ecosystem and AI: Enabling FAIR and AI-ready data — blocked at `onlinelibrary.wiley.com` (HTTP 403 / not a PDF (text/html; charset=UTF-8) [final_url=https://onl)
- row 62 **sansone-2023-fair-making-data-ai-ready** — FAIR: Making Data AI-Ready — blocked at `worldscientific.com` (HTTP 403 / not a PDF (text/html; charset=UTF-8) [final_url=https://www)
- row 65 **brewer-2026-pipeline-patterns** — Data readiness pipeline patterns for scientific AI at scale: Insights from clima — blocked at `onlinelibrary.wiley.com` (HTTP 403 / not a PDF (text/html; charset=UTF-8) [final_url=https://onl)

### Fetch-failed (operator-suppliable the same way)
- row 21 **unece-dupriez-2025-ai-readiness-data-metadata** — HTTP 403 / not a PDF (text/html; charset=UTF-8) [final_url=https://unece.org/sites/default/files/2025-05/GenAI2025_S1_WorldBank_Dupriez_P.pdf]
- row 33 **lakefs-summit-orr-ai-ready-data-demystified** — ADDENDUM-01 routing: summit page probed 2026-08-26 — no transcript, slides, or direct media URL (sessions gated behind registration); fetch_failed.

### Awaiting operator drop (max.gov; see `2026-08-24_operator_download_list.md` — 9 decks, not the task's stated 10)

## Summary counts

| verdict class | n |
|---|---|
| fetched | 34 |
| already_held | 20 |
| excluded_by_rule | 16 |
| access_blocked | 10 |
| awaiting_operator_drop | 9 |
| fetch_failed | 2 |
| flagged_off_construct | 1 |
| — of fetched, manifest-added (epoch `triage-2026-08-24`) | 34 |

Construct arms on the 34 admitted: training_data_readiness 9, org_maturity 4, publication_actionability 21.

## Per-item verdicts

Input-1 rows carry vetting `{fss_research_group_2026-08, generalist_federal_statistics, signal_not_verdict}` — recorded, never treated as satisfying the inclusion rule by itself. Rows g1–g20 are the Phase 3 SEO/AIO-lineage gap list (2026-08-22 chat decision), reconciled against the kernel register first.

| row | doc_id | verdict | clause | arm | surface | access/dedupe |
|---|---|---|---|---|---|---|
| 1 | census-ces-wp-26-25-ai-diffusion | flagged_off_construct | R4 | — | — |  |
| 2 | esip-data-readiness-checklist | fetched | R2 | training_data_readiness | document | manifested |
| 3 | doc-rfi-ai-open-gov-data-2024 | fetched | R3 | org_maturity | document | manifested |
| 4 | doc-rfi-comments-docket-listing | excluded_by_rule | R3_listing_page | — | — |  |
| 5 | fcsm-25-03-sme-row | already_held | R5 | — | — | held: `fcsm-25-03` |
| 6 | genai-open-data-guidelines-sme-row | already_held | R5 | — | — | held: `generative-ai-and-open-data-guidelines-and-best-practices-de` |
| 7 | maxgov-2026-c2-1-webb-genai-open-data | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 8 | maxgov-2026-c2-2-hoppe-ai-ready-extension | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 9 | maxgov-2026-c2-4-belyaeva-machine-understandable | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 10 | maxgov-2026-c2-5-vanwart-nass-quick-stats | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 11 | maxgov-2026-fcsm-ai-ready-data-wg-kopp | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 12 | maxgov-2024-d1-1-harper-cdgb-best-practices | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 13 | maxgov-2024-d1-2-christensen-noaa-ai-readiness | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 14 | maxgov-2024-d1-3-haase-census-machine-understandable | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 15 | maxgov-2024-d1-4-iwugo-bea-genai-data-capture | awaiting_operator_drop | R1 | publication_actionability | slides | max.gov |
| 16 | usdc-mcp-federal-open-data-pilot-2026 | fetched | R1 | publication_actionability | document | manifested |
| 17 | nstc-desirable-characteristics-data-repositories-2022 | fetched | R1 | publication_actionability | document | manifested |
| 18 | doe-data-cards-standardized-metadata-2026 | fetched | R1 | publication_actionability | document | manifested |
| 19 | m-25-05-sme-row | already_held | R5 | — | — | held: `m-25-05-phase-2-implementation-of-the-evidence-act-open-gove` |
| 20 | croissant-akhtar-2024-paper | fetched | R1 | publication_actionability | document | manifested |
| 21 | unece-dupriez-2025-ai-readiness-data-metadata | fetch_failed | R1 | publication_actionability | slides |  |
| 22 | unsc-2026-koh-reaching-users-official-statistics | fetched | R1 | publication_actionability | slides | manifested |
| 23 | unsc-2026-stoyanovich-open-data-responsible-reuse | fetched | R1 | publication_actionability | slides | manifested |
| 24 | ccsa-2026-ai-ready-official-statistics | fetched | R1 | publication_actionability | document | manifested |
| 25 | worldbank-fostering-ai-readiness-official-statistics | fetched | R1 | publication_actionability | document | manifested |
| 26 | paris21-nso-framework-sme-row | already_held | R5 | — | — | held: `towards-ai-ready-national-statistical-offices-paris21-framew` |
| 27 | paris21-ttai-self-assessment-2026 | fetched | R3 | org_maturity | document | manifested |
| 28 | uk-building-ai-ready-datasets-2026 | fetched | R1 | publication_actionability | document | manifested |
| 29 | odi-framework-for-ai-ready-data-2025 | fetched | R2 | training_data_readiness | document | manifested |
| 30 | uk-ai-ready-data-action-plan-2026 | fetched | R1 | publication_actionability | document | manifested |
| 31 | worldbank-blog-open-data-to-ai-ready-2025 | fetched | R1 | publication_actionability | document | manifested |
| 32 | google-okf-blog-2026 | fetched | R1 | publication_actionability | document | manifested |
| 33 | lakefs-summit-orr-ai-ready-data-demystified | fetch_failed | R2 | training_data_readiness | transcript |  |
| 34 | lakefs-summit-ai-trenches-panel | excluded_by_rule | R2_domain_application | — | — |  |
| 35 | cisco-ai-readiness-index-sme-row | already_held | R5 | — | — | held: `cisco-ai-readiness-index-2025` |
| 36 | rfi-comment-deloitte-2024 | access_blocked | R3 | org_maturity | document | blocked: downloads.regulations.gov |
| 37 | rfi-comment-leidos-2024 | access_blocked | R3 | org_maturity | document | blocked: downloads.regulations.gov |
| 38 | rfi-comment-microsoft-2024 | access_blocked | R3 | org_maturity | document | blocked: downloads.regulations.gov |
| 39 | rfi-comment-openai-2024 | access_blocked | R3 | org_maturity | document | blocked: downloads.regulations.gov |
| 40 | rfi-comment-protesero-2024 | access_blocked | R3 | org_maturity | document | blocked: downloads.regulations.gov |
| 41 | rfi-comment-sas-2024 | access_blocked | R3 | org_maturity | document | blocked: downloads.regulations.gov |
| 42 | gartner-ai-ready-data-essentials-2024 | fetched | R3 | org_maturity | document | manifested |
| 43 | informatica-cdo-insights-2026 | excluded_by_rule | R3_press_release_only | — | — |  |
| 44 | data-unchained-gasper-sequeda-ai-readiness-2026 | fetched | R3 | org_maturity | transcript | manifested |
| 45 | sequeda-missing-layer-semantics-kg-2025 | fetched | R1 | publication_actionability | transcript | manifested |
| 46 | aidrin-sme-row | already_held | R5 | — | — | held: `aidrin-hiniduma-2024` |
| 47 | li-2026-rag-building-sector | excluded_by_rule | R2_domain_application | — | — |  |
| 48 | brewer-scientific-ai-at-scale-sme-row | already_held | R5 | — | — | held: `data-readiness-for-scientific-ai-at-scale` |
| 49 | thomas-2024-nutrition-obesity-big-data | excluded_by_rule | R2_domain_application | — | — |  |
| 50 | wood-charlson-2026-fair-to-cope | fetched | R2 | training_data_readiness | document | manifested |
| 51 | poduval-2022-space-science-ai-ready | excluded_by_rule | R2_domain_application | — | — |  |
| 52 | mangala-2024-fabric-lakehouse | excluded_by_rule | R2_domain_application | — | — |  |
| 53 | verhulst-2025-fair-r | access_blocked | R2 | training_data_readiness | document | blocked: papers.ssrn.com |
| 54 | kidwai-khan-2024-clinical-ai-roadmap | excluded_by_rule | R2_domain_application | — | — |  |
| 55 | mons-2026-fair-squared-scientific-production | fetched | R2 | training_data_readiness | document | manifested |
| 56 | wang-2025-sccompass | excluded_by_rule | R2_domain_application | — | — |  |
| 57 | ali-2025-zero-etl-review | excluded_by_rule | R2_domain_application | — | — |  |
| 58 | aggarwal-2025-lakehouse-strategy | excluded_by_rule | R2_domain_application | — | — |  |
| 59 | greenberg-2026-metadata-ecosystem-ai | access_blocked | R2 | training_data_readiness | document | blocked: onlinelibrary.wiley.com |
| 60 | bandi-2025-metadata-ai-ready | fetched | R2 | training_data_readiness | document | manifested |
| 61 | odi-ai-ready-national-data-library-2025 | fetched | R1 | publication_actionability | document | manifested |
| 62 | sansone-2023-fair-making-data-ai-ready | access_blocked | R2 | training_data_readiness | document | blocked: worldscientific.com |
| 63 | redi-2026-automated-data-readiness | fetched | R2 | training_data_readiness | document | manifested |
| 64 | nikolov-2024-medical-imaging-ai-ready | excluded_by_rule | R2_domain_application | — | — |  |
| 65 | brewer-2026-pipeline-patterns | access_blocked | R2 | training_data_readiness | document | blocked: onlinelibrary.wiley.com |
| 66 | scihorizon-qin-2025 | fetched | R2 | training_data_readiness | document | manifested |
| 67 | srivastava-2026-database-selection-framework | excluded_by_rule | R2_domain_application | — | — |  |
| 68 | ortiz-2024-cancer-wearables-preprocessing | excluded_by_rule | R2_domain_application | — | — |  |
| 69 | santoro-2026-eo-ai-ready-datasets | excluded_by_rule | R2_domain_application | — | — |  |
| 70 | costes-2026-space-life-sciences-ai-ready | excluded_by_rule | R2_domain_application | — | — |  |
| 71 | nalla-2025-data-readiness-cornerstone | fetched | R2 | training_data_readiness | document | manifested |
| 72 | tiger-2024-visual-analysis-data-readiness | fetched | R2 | training_data_readiness | document | manifested |
| g1 | ietf-web-bot-auth-architecture-draft | fetched | R1 | publication_actionability | document | manifested |
| g2 | mcp-specification-2025-06-18-overview | fetched | R1 | publication_actionability | document | manifested |
| g3 | nlweb-readme | fetched | R1 | publication_actionability | document | manifested |
| g4 | webmcp-readme | fetched | R1 | publication_actionability | document | manifested |
| g5 | google-okf-spec | fetched | R1 | publication_actionability | document | manifested |
| g6 | datacommons-docs-landing | fetched | R1 | publication_actionability | document | manifested |
| g7 | imf-statgpt-readme | fetched | R1 | publication_actionability | document | manifested |
| g8 | gap-google-structured-data-intro | already_held | R5 | — | — | held: `google-structured-data-intro` |
| g9 | gap-google-dataset-structured-data | already_held | R5 | — | — | held: `google-dataset-structured-data` |
| g10 | gap-google-crawling-indexing | already_held | R5 | — | — | held: `google-crawling-indexing-overview` |
| g11 | gap-google-robots-txt-intro | already_held | R5 | — | — | held: `google-robots-txt-intro` |
| g12 | gap-google-ai-features | already_held | R5 | — | — | held: `google-ai-features-and-your-website` |
| g13 | gap-google-search-console-start | already_held | R5 | — | — | held: `google-search-console-start` |
| g14 | gap-indexnow-documentation | already_held | R5 | — | — | held: `indexnow-documentation` |
| g15 | gap-bing-ai-performance | already_held | R5 | — | — | held: `bing-ai-performance-public-preview-2026` |
| g16 | gap-bing-webmaster-guidelines | already_held | R5 | — | — | held: `bing-webmaster-guidelines` |
| g17 | gap-bing-webmaster-api-docs | already_held | R5 | — | — | held: `bing-webmaster-api-docs` |
| g18 | gap-sitemaps-protocol | already_held | R5 | — | — | held: `sitemaps-protocol` |
| g19 | gap-rfc-9309-robots | already_held | R5 | — | — | held: `rfc-9309-robots-exclusion-protocol` |
| g20 | gap-llmstxt-proposal | already_held | R5 | — | — | held: `llmstxt-proposal` |

## Notable decisions and discrepancies (grounded, logged, operator overrides by addendum)

1. **72 rows, not 65** (ADDENDUM-02 expected 65): drop file is a superset of the Desktop reading; all 72 triaged. Tail row matches expectation.
2. **Croissant dedupe did NOT hit** (task expected it): corpus holds the MLCommons SPEC, not the Akhtar et al. paper — distinct primary sources; the paper was admitted under R1.
3. **Gartner fetched, not blocked** (task expected access_blocked): the article page served full text to the crawler; admitted under R3.
4. **DOC RFI + comment letters carry construct_arm `org_maturity`** because the task places them under R3; their subject matter is publication-side — flagged in case the operator wants an arm override by annotation.
5. **Row 4** (regulations.gov comment LISTING page) excluded as `R3_listing_page`: R3's evidence objects are the individual letters (rows 36–41), all registered access_blocked.
6. **Rows 33/34 share one URL** (lakefs summit). In the dixie ledger the two register lines merge by URL into a single record that shows `excluded`; the Orr keynote's own verdict (include-class, fetch_failed, no media) is preserved here and in the fetch register. Known URL-dedupe artifact, recorded.
7. **Row 55** (Mons FAIR²): the SME figshare link is a metadata-only record with zero files; the actual article was resolved from its description (policylabs.frontiersin.org) and fetched.
8. **Row 71**: SME cell held only the bare journal URL; article resolved by OJS title search to jcsts article 10198.
9. **Row 31** (World Bank blog): SME URL truncated mid-slug; canonical slug recovered from the site's sitemap.
10. **YouTube transcripts** (rows 44/45): no established ingest-youtube path exists in this repo or its siblings (searched); `scripts/harvest_triage.py` implements it via yt-dlp auto-captions with capture provenance; both flagged `grounding_surface: transcript`.
11. **`already_held` items get no new candidate_register line**: the dixie sweep re-imports the register merged by URL/title-slug, and a duplicate line under a *different* URL would mint a phantom ledger record (kernel run defect 2 precedent). Their verdicts live in this log + the fetch register.
12. **controls.yaml `forage: off` does not gate this run**: the forage switch governs autonomous foraging (DD-004); this is an operator-authored task's directed acquisition, same as the kernel harvest (harvest scripts have never read controls.yaml). Budget caps bound the runner, which made zero model calls.
13. **UK national-government docs** (rows 28/30) carry `source_type: federal` — the enum has no national-government value and `intergovernmental` would be wrong; noted for a future enum decision.

## construct_arm backfill

See `docs/research/2026-08-24_triage_backfill_report.md` (134 documents; kernel 63 → publication_actionability by epoch default, zero overrides; v1 71 → 17 publication_actionability / 5 training_data_readiness / 49 org_maturity by the listed title rule, `scripts/construct_arm_backfill.yaml` v2026-08-24.1).
