# RESULT: DCAT-002 ADDENDUM_01: the FAIRness Project record and the CDO Council DSWG report admitted and extracted; the base standard and FCSM 20-04 were already held

**Task:** `cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md` (items 10 to 15), against the base task `cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md`. **Implements** DN-011-R4 (`docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`). The Desktop's uncommitted R4/R5 edit to DN-011 is committed with this RESULT.

**Ran to the end.** The operator hand-dispatched it in a Claude Code session on 2026-10-05, 10:54Z to 13:00Z, with `dispatch.enabled: true` (see §7, item 2). The base task had already run and has its own RESULT (`2026-10-04_DCAT-002_dcat_us_3_intake_and_g4_RESULT.md`), so this session executed only the addendum.

## 1. Delivery report

| # | addendum item | outcome | doc_id / reason |
|---|---|---|---|
| 10 | W3C DCAT Version 3 | **held already**, R5 dedupe | `w3c-dcat-3`, admitted 2026-08-21. Graph: 74 Definitions, 172 Claims, 250 Concepts |
| 11 | CDOC and FCSM, August 2024 (IG footnote 11) | **declined: not published** | Resolved below; no public copy exists |
| 12 | FAIRness Project wiki: findings, recommendations, sequencing plan | **2 admitted**; the findings and recommendations are not on the wiki | `fairness-project-wiki-home`, `fairness-project-wiki-project-overview` |
| 13 | FCSM 2024 session B3.3 | **admitted** | `fcsm-2024-b3-3-fairness-project` |
| 14 | CDO Council Data Sharing Working Group report | **admitted** | `cdoc-dswg-findings-and-recommendations-2022` |
| 15 | FCSM 20-04, A Framework for Data Quality | **held already**, R5 dedupe | `fcsm-20-04-a-framework-for-data-quality`, admitted 2026-07. Graph: 99 Definitions, 270 Claims |

- **Item 11 resolved.** Footnote 11 of the Implementation Guide (p. 9) reads: "Chief Data Officers Council (CDOC) and Federal Committee on Statistical Methodology (FCSM). (2024, August 5). Building Trust and FAIRness into the Process for Finding and Using Government Data Project (FAIRness Project): Implementing DCAT-US 3.0 Sequencing Plan." The guide gives no URL.
  - Searches that failed to find a public copy:
    - three web searches: the exact title, the exact subtitle "Implementing DCAT-US 3.0 Sequencing Plan", and FAIRness + sequencing plan + CDO Council + FCSM;
    - the file trees of both GitHub repositories, `DOI-DO/dcat-us` and `GSA/dcat-us`. They hold only `DCAT-US-3-Requirements-Template.docx` and `DCAT-US 3 Overview.pdf`.
  - The admitted B3.3 deck states the plan's status itself, on slide 6: "Task 2, Sequencing/Transition Plan • Status: Provided to Office of Management and Budget." Slide 7 says the same of the governance plan.
  - Decision: decline it as unpublished. It is an internal deliverable to OMB, and there is nothing to fetch.
- **Item 12.** The wiki has 10 pages. None states findings, recommendations or a sequencing plan, because those are the contents of the unpublished plan (B3.3 slide 6: "The plan includes: • Key findings and recommendations. • What OMB Needs to consider. …").
  - **Admitted** (source markdown from `raw.githubusercontent.com/wiki/...`):
    - **Home** states the project's aim and the draft 3.0's key features. Last edited 2023-10-26.
    - **Project-Overview** states the three deliverables, the problem ("out-of-date compared to current international metadata standards … generally purpose-built and focused on metadata producers") and the three-phase schema governance process. Last edited 2023-09-12.
  - **Not admitted**, being topic explainers rather than the record:
    - `FAIR-Principles` restates the FAIR principles;
    - `Resource-Identification` is a PURL/URI explainer;
    - `Licensing` is a three-sentence stub on software licences;
    - `Metadata-and-DCAT-Simplified` is a ChatGPT transcript ("Explain DCAT standards like I was 5 years old");
    - `FAIR-Vocabularies`, `Resource-Attribution` and `Spatial-Metadata` answer 404 as raw markdown.
- **Item 13.** The addendum's URL served the deck (200). The same file is also listed at `assets.fcsm.gov`, which was not fetched.
  - The deck is by the project co-chairs Thomas Dabolt (DOI) and Michael Ratcliffe (Census), 8 slides, PDF dated 2024-10-30.
  - It names the core team, which includes the U.S. Census Bureau, NCES and NCHS, and the advisory group, which includes the ICSP.
- **Item 14.** The addendum said to look on cdo.gov or councils.gov.
  - `www.cdo.gov/news/data-sharing-report/` was refused before any request: its robots.txt was unreachable, which RFC 9309 §2.3.1.4 treats as complete disallow.
  - The report was found on `resources.data.gov` (landing page "DSWG Recommendations and Findings", "Originally published 2022"), and its PDF was admitted.
  - **Date:** PDF created 2022-03-28 and modified 2022-03-30; the file name says "2021"; the addendum says April 2022, the month GAO-23-105514 gives. `pub_date` is 2022-03-30, from the PDF, and the notes carry the other two dates.
- **A FAIRness Project deck not admitted:** the NGAC April 2024 deck at `www.fgdc.gov`. That host's robots.txt disallows the path, so it was not fetched. The refusal is recorded, not worked around.
- All four admissions:
  - are `included` and `verified` in `corpus/crosswalk/`, epoch `dcat-us-3-a01-2026-10-05`, each with one `manifest_add` (`events/batch-001.jsonl`, last 4 lines);
  - follow criterion R1 of `cc_tasks/2026-08-24_source_triage.md`;
  - were done by `scripts/admit_dcat_002_a01.py`, which follows the path of `scripts/admit_dcat_us_3.py`.
- Corpus: 274 → 278 admitted (`docs/figures/numbers.json`). Ledger entries: 389 → 393.

## 2. Extraction and spend

- **Cohort:** 4 documents, 27 chunks (DSWG 20, Project-Overview 5, Home 1, B3.3 1).
  - `scripts/run_dcat_extraction.py` gained `--cohort base|a01`. The default is the base run, unchanged, so nothing was copied.
  - Same profile as the base: `bulk_v038`, prompt v0.3.8. Run `dcat_us_3_a01_extraction_2026-10-05`, state at `state/dcat_us_3_a01_extraction_2026-10-05.json`.
- **Ceiling (DD-042):** 1,657,045 = 27 × 53,367 × 1.15. The 53,367 tokens per chunk is the base run's measured rate on the same profile (24,388,534 / 457).
- **Pilot:** Project-Overview, 5 chunks, 0 failures, 249,111 settled (49,822 per chunk). That projected about 1.35M for the cohort, and the run continued.
- **Actual: 1,486,348 settled**, all 27 chunks, `success`; 0 outstanding, 0 released, 0 refusals (`python -m kg.spend status`). The day's commitment after the run was 26,134,987 of 55,000,000.
- **Ingested:**
  - pilot: 51 nodes, 55 edges, 17 diverted;
  - main pass: 320 nodes, 386 edges, 64 diverted, 5 `semantic_edge_refused`;
  - 0 extraction failures.
- **Graph after projection** (`build_projection.py`): 34,878 nodes and 43,032 edges, up from the base run's 34,507 and 42,591.
  - The four documents hold 328 non-Document nodes, 9 of them Definitions:
    - DSWG 236 (4 Definitions);
    - Project-Overview 48 (3);
    - B3.3 22 (1);
    - Home 22 (1).
  - Each Document node has relationships: DSWG 220, Project-Overview 36, Home 20, B3.3 14.

## 3. Framework record

Unchanged. The addendum asked for no indicator change, `framework/ai_readiness_framework.json` is byte-identical to HEAD (protected-paths check), and no write-back was made.

## 4. Check by query (`search_text`, MCP, after projection)

| query | new hit from this addendum |
|---|---|
| FAIRness | `fairness-project-wiki-home::d-fairness`, "the FAIRness, or Findability, Accessibility, Interoperability, and Reusability of all types of federal data" |
| governance | `fairness-project-wiki-project-overview::d-pre-release-governance` and `::d-post-release-governance` |

The other new Definitions:
- B3.3: "FAIR principles".
- DSWG: "Human-centered design", "Jamboard", "'luxury' items" and "'strategic' items".
- Project-Overview: "Initial schema development".

`search_text` reads only Definitions and the record, so the Claims (DSWG 83; the three FAIRness documents 33) need `run_cypher`.

## 5. Ripple, by generator, none by hand (`logs/2026-10-05_DCAT-002_A01_regenerate.log`, each rc=0)

- **Generators run:** `build_l0_report.py`, `build_brief_pack.py`, `build_l0_site.py`, `build_evidence_map.py`, `build_figures.py`, `build_report_pdf.py`, `build_scan_catalog.py`, `mcp/airkg_doc.py`, `run_kg_questions.py`, `run_definition_pairs.py --render`.
- **What moved:**
  - the corpus count, 274 → 278;
  - the KG-questions epoch, 275 → 279 documents and 2,541 → 2,550 Definitions;
  - every `docs/brief/` page header. The brief pack stamps the commit that last touched the framework record. The base DCAT-002 commit `688451fb` became that commit after its generators had run, so the pack was one commit behind at HEAD. Only the stamp changed, `9ffcffddbf8f` → `688451fb0012`.
- `run_definition_pairs.py --check`: 158 pairs, both controls pass, drift `[]`. The new Definitions add no definition of AI readiness to the cohort, so no model pass is owed.
- The L0 report markdown and PDF did not change.

## 6. Gate (logs under `logs/`, gitignored)

- **Full suite** (`make gate-full`, copied to `2026-10-05_DCAT-002_A01_gate_full_suite.log`): **2932 passed, 0 failed, 3 skipped, 0 deselected, 37 xfailed, EXIT=0**, 2398.20 s. The three skips:
  - `test_dispatch_config.py:373`: dirty tree and the STOP file, expected mid-task;
  - `test_scan_harness.py:283` and `test_g1_preservation.py:337`: both standing, and the same as the base run's.
- **`seldon verify`** (`2026-10-05_DCAT-002_A01_verify.log`): all checks passed, EXIT=0.
- **Protected paths** (`scripts/check_protected_dcat_002_a01.sh`, `2026-10-05_DCAT-002_A01_protected.log`): PASS, EXIT=0, re-run after the suite. **`kg.manifest verify`** (`_manifest_verify.log`): clean, EXIT=0.
- **Projection** (`2026-10-05_DCAT-002_A01_projection.log`): EXIT=0, `evidenced_by_missing_document` 0. **Round-trip** (`_roundtrip.log`): 9 passed, 0 skipped, EXIT=0.
- **Extraction:** `_pilot.log` and `_extract.log`, both EXIT=0.
- **New tests:** `tests/test_dcat_002_a01_intake.py`, 6 passed, 0 skipped (also inside the full suite). They cover:
  - admission and the epoch;
  - one `manifest_add` per document, tied to the fetch log;
  - held items 10 and 15 not admitted a second time;
  - no source taken from a robots-refused host;
  - the driver's `a01` cohort.

## 7. Premises wrong, and findings outside the task

1. **"Written 2026-10-05, before DCAT-002 was dispatched."** That is false.
   - DCAT-002 had already run and was committed as `688451fb` at 08:58Z. Its RESULT says "no addendum exists".
   - The addendum file is dated 10:40Z, and task 1e19fa62 was already `completed` on the graph.
   - Executing it meant a second intake pass on top of the finished base, with a RESULT of its own. The base RESULT was not edited.
2. **Dispatch.** This was again a hand dispatch with `dispatch.enabled: true`.
   - I touched `.seldon/DISPATCH_STOP` at 10:54:46Z; the dispatcher logged `dispatch_observed_stop` at 10:58:21Z. It is removed at close.
   - DCAT-003 is not dispatchable as written: it has `**Model spend:**`, not `**Spend:**`, and no `**Framework layer served` header.
3. **Items 10 and 15 were already corpus,** and the addendum allowed for that only on item 15. Item 10 sat in the graph before the base task: the base RESULT §4 counts `w3c-dcat-3` as the one "DatasetSeries" hit.
4. **Items 11 and 12 assumed a published plan.** The project's "findings and recommendations" are a section of the sequencing plan, which went to OMB unpublished (§1). Answering what FCSM asked for therefore rests on:
   - the wiki's aims and deliverables;
   - the B3.3 deck;
   - the DSWG report, whose "improved data awareness" and "data trustworthiness" findings name data cataloging and current inventories;
   - FCSM 20-04 and 25-03.
5. **Item 14's date.** "April 2022" is GAO's date. The PDF says March 2022 and its file name says 2021 (§1).
6. **DN-011-R4 says "Both graphs get".** This task covers ai-readiness-kg only. The fss-policy-kg side, and DCAT-001 in `icsp_notebook`, which DCAT-003 names as a prerequisite, are not touched here.
7. **The ai-readiness-kg MCP server reported `projection_gate: stale` before this run started.** That is the same start-time caching the base RESULT §7 item 5 records. A fresh process reads the round-trip green (§6). Restart the server before DCAT-003 queries it.
8. **Two robots refusals:**
   - `www.fgdc.gov`, path disallowed;
   - `www.cdo.gov`, robots.txt unreachable, so complete disallow.
   Neither was routed around. The NGAC April 2024 FAIRness deck is the one document lost to them, because the DSWG report had a second home on resources.data.gov.

## 8. Fetch log, whole (`logs/2026-10-05_DCAT-002_A01_fetch.jsonl`, 25 lines: time UTC, event, status, bytes, sha256[:12], URL)

Declared hosts (`SELDON_NETWORK_ALLOWLIST`): `github.com, raw.githubusercontent.com, statspolicy.gov, assets.fcsm.gov, www.cdo.gov, resources.data.gov, www.councils.gov`, and `www.fgdc.gov` from the third fetch call on. The base task's `**Network:**` line is prose ("fetch the public documents below"). Discovery used web search and `gh api` tree listings, and no document bytes came through either. Two `git/trees` listings went to `api.github.com`; they are not in this log.

```
10:56:04 request 200 16739 12bc55582b1d https://github.com/robots.txt
10:56:06 request 200 198195 a1fcbce225c3 https://github.com/DOI-DO/dcat-us/wiki/_pages
10:56:07 request 200 231651 70fe9dac6fe1 https://github.com/DOI-DO/dcat-us/wiki
10:56:18 request 404 14 d5558cd419c8 https://raw.githubusercontent.com/robots.txt
10:56:20 request 200 3350 6a69caf9cc43 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Project-Overview.md
10:56:21 request 200 5281 ebb0b69bef26 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Home.md
10:56:50 request 200 45 25b98f1336a7 https://statspolicy.gov/robots.txt
10:56:51 request 200 187257 a408bb196232 https://statspolicy.gov/assets/fcsm/files/docs/2024-conference-docs/B/B3.3_Dabolt.pdf
10:56:51 request 200 914 eff91ad3db9b https://www.fgdc.gov/robots.txt
10:56:51 error - 0 - https://www.fgdc.gov/ngac/meetings/april-2024/fairness-project-ngac-apr-2024.pdf (RobotsDisallowed)
10:56:51 error - 0 - https://www.cdo.gov/news/data-sharing-report/ (RobotsDisallowed: robots_status unreachable; RFC 9309 §2.3.1.4 complete disallow)
10:56:52 request 200 22 212cf4d230aa https://resources.data.gov/robots.txt
10:56:53 request 200 28052 3859185fb815 https://resources.data.gov/resources/2021_DSWG%20Recommendations_and_Findings_508/
10:56:53 request 404 14 d5558cd419c8 https://raw.githubusercontent.com/robots.txt
10:56:54 request 200 2900 b30b3f29b349 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/FAIR-Principles.md
10:56:55 request 404 14 d5558cd419c8 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/FAIR-Vocabularies.md
10:56:56 request 200 324 a12e74ea017c https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Licensing.md
10:56:57 request 200 1315 c1c363911ce8 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Metadata-and-DCAT-Simplified.md
10:56:58 request 404 14 d5558cd419c8 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Resource-Attribution.md
10:56:59 request 200 6018 0c46de534603 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Resource-Identification.md
10:57:00 request 404 14 d5558cd419c8 https://raw.githubusercontent.com/wiki/DOI-DO/dcat-us/Spatial-Metadata.md
10:57:32 request 200 22 212cf4d230aa https://resources.data.gov/robots.txt
10:57:34 request 200 5383697 db94be1764fe https://resources.data.gov/assets/documents/2021_DSWG_Recommendations_and_Findings_508.pdf
10:58:10 request 200 16739 12bc55582b1d https://github.com/robots.txt
10:58:11 request 200 231023 54249e54be1a https://github.com/DOI-DO/dcat-us/wiki/Project-Overview
```
