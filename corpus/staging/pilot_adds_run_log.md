# Pilot Manifest Adds — Run Log

**Task:** cc_tasks/2026-07-03_pilot_manifest_adds.md  
**Date:** 2026-07-03  
**Outcome:** 4/5 manifest-added, 1 STOP (Cisco). All adds via the manifest module (event-sourced; events in `events/batch-001.jsonl`).

TEVV evidence rides in each `manifest_add` event's `payload.acquisition` block; this log is the human-readable summary. Acquired PDFs are kept local (gitignored `corpus/pilot/`); provenance (primary_url + content_hash) is committed in `corpus/manifest.json`.

## Added (4)

| doc_id | source_type | http | final URL | pages | bytes | sha256 (first 16) |
|---|---|---|---|---|---|---|
| `fcsm-25-03` | federal | 200 | https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf | 5 | 236247 | `ba8901ed2dac0abe` |
| `datahub-mlmu-25` | federal | 200 | https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf | 4 | 197595 | `06438cb775a1e751` |
| `lawrence-data-readiness-levels-2017` | academic | 200 | https://arxiv.org/pdf/1705.02245 | 10 | 134094 | `6bf740664e86e754` |
| `aidrin-hiniduma-2024` | academic | 200 | https://arxiv.org/pdf/2406.19256 | 12 | 4240792 | `790a524c6bfc9941` |

Per-document TEVV:

- **fcsm-25-03** — FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality
  - **Test:** fetched https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf at 2026-07-03T13:44:07.211427+00:00, HTTP 200, final URL `https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf`.
  - **Evaluation (identity):** PASS — matched title/author tokens ['ai-ready', 'data quality'] in fetched text.
  - **Verification:** sha256 `ba8901ed2dac0abe36976c27c91bc78b2f00ca88b22c94af976033e266350797`; re-hash after write via `manifest.verify()` = match.
  - **Validation:** valid PDF, 5 pages, 236247 bytes (substantive document, not an error/abstract stub).
  - event_id `659bc80c0738408e82f0acd85fc10141` @ 2026-07-03T13:44:10.832148+00:00
- **datahub-mlmu-25** — America's DataHub RFS Topic MLMU-25: Measuring LLM Understanding of Federal Statistical Data
  - **Test:** fetched https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf at 2026-07-03T13:45:27.865150+00:00, HTTP 200, final URL `https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf`.
  - **Evaluation (identity):** PASS — matched title/author tokens ['measuring large language model understanding'] in fetched text.
  - **Verification:** sha256 `06438cb775a1e7516357324b79579ab8f7ae6a149987a2c1e3738abebcb94543`; re-hash after write via `manifest.verify()` = match.
  - **Validation:** valid PDF, 4 pages, 197595 bytes (substantive document, not an error/abstract stub).
  - event_id `c35a56ebfe6943eb8e8bd47151bb764a` @ 2026-07-03T13:45:28.094038+00:00
- **lawrence-data-readiness-levels-2017** — Data Readiness Levels
  - **Test:** fetched https://arxiv.org/pdf/1705.02245 at 2026-07-03T13:44:11.501738+00:00, HTTP 200, final URL `https://arxiv.org/pdf/1705.02245`.
  - **Evaluation (identity):** PASS — matched title/author tokens ['data readiness levels', 'lawrence'] in fetched text.
  - **Verification:** sha256 `6bf740664e86e7547d6e70723e2f2497e203809bbfeea7159d01b6be6ac907d1`; re-hash after write via `manifest.verify()` = match.
  - **Validation:** valid PDF, 10 pages, 134094 bytes (substantive document, not an error/abstract stub).
  - event_id `611fe70c3a4348ff987fe2f7d6455705` @ 2026-07-03T13:44:11.697057+00:00
- **aidrin-hiniduma-2024** — AIDRIN: AI Data Readiness Inspector (Hiniduma et al., 2024)
  - **Test:** fetched https://arxiv.org/pdf/2406.19256 at 2026-07-03T13:44:11.813595+00:00, HTTP 200, final URL `https://arxiv.org/pdf/2406.19256`.
  - **Evaluation (identity):** PASS — matched title/author tokens ['data readiness', 'aidrin'] in fetched text.
  - **Verification:** sha256 `790a524c6bfc9941ed61f489229b73ab49f6e370fd5eca18bf98a77d9e12a9bd`; re-hash after write via `manifest.verify()` = match.
  - **Validation:** valid PDF, 12 pages, 4240792 bytes (substantive document, not an error/abstract stub).
  - event_id `f2373f5b31524393859323e7ff98d7a3` @ 2026-07-03T13:44:12.579836+00:00

## STOP (1)

- **cisco-ai-readiness-index-2024** — Cisco Global AI Readiness Index 2024
  - **Primary URL:** https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/archive/2024-m11.html
  - **Reason:** Landing page returns HTTP 403 to automated fetch (browser UA + headers both blocked; Cisco bot protection). The PDF variant could not be resolved FROM the page as the task requires. Per task instruction, STOP — no out-of-band URL substituted.
  - **Lead for operator:** A stable report PDF has historically lived under cisco.com/c/dam/m/en_us/solutions/ai/readiness-index/2024-m11/documents/cisco-ai-readiness-index.pdf — unverified here because the landing page is inaccessible to automated fetch. Operator to confirm via browser and re-run acquisition with the resolved URL.

## Notes

- **MLMU-25 identity check corrected mid-run.** The first pass rejected the (correct) document because the identity token `mlmu-25` — an administrative RFS topic code from the attachment filename — does not appear in the document body. Identity was re-validated on the actual title text ("Measuring Large Language Model Understanding of…"), which matches the register entry. This was a fix to an over-strict check, not a silent correction of a genuine mismatch: the fetched PDF is the right document.
- The manifest module was extended with an optional `acquisition` evidence block (backward compatible; absent when not supplied) so TEVV lives in the event, not just this log. Covered by two new tests in `tests/test_manifest.py`.
- Acquired binaries are gitignored for this public repo (2 of 4 are arXiv author-copyright); provenance is fully reconstructable from the committed manifest entries.


---

## Cisco inbox add v2 — 2026-07-03 (task: cisco_inbox_add_v2)

Outcome: 3/3 added.

- **ADDED** `cisco-ai-readiness-index-2025` — pages=27 canon_hash_match=True
- **ADDED** `cisco-ai-readiness-index-methodology` — pages=5
- **ADDED** `cisco-ai-readiness-assessment-instrument` — pages=25 from 6 components

**A. Cisco AI Readiness Index 2025 (pilot #4)** — replaces the 2024 STOP. Identity: "Realizing the Value of AI", Cisco AI Readiness Index 2025, third edition. Operator manual_browser acquisition; canonical dam URL re-fetched here (HTTP 200) and sha256 **matches** operator file (`a1b3858c2d85e66b`) — provenance confirmed against the primary source. → corpus/pilot/ (gitignored).

**B. Methodology capture** — source URL recovered from the PDF's embedded Log-in link referer (`methodology.html`); browser footer truncated it to `/methodo...`, so extracted from the link annotation, not guessed. sha256 `6215271551770bc5`. → corpus/cisco/ (gitignored).

**C. Assessment instrument** — 6 pillar printouts merged (order: unnumbered/Strategy, then pages 2-6) into one 25-page PDF, merged sha256 `c5025910ec2f69d9`. Component sha256s recorded in the event's acquisition block. Source URL `assessment-tool.html` recovered from embedded link annotation. Register tagged [instrument, ai-readiness-fss]. Components preserved (not destroyed) in corpus/cisco/assessment_components/ (gitignored).

Register: 2024 Cisco entry corrected to 2025 (title/year/URL + triage_note); 2 new operator entries (B, C).
