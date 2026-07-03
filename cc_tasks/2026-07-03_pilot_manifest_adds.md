# CC Task — Pilot Manifest Adds (5 documents)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**

## Objective

Acquire and manifest-add the 5 pilot documents (schema_v0.1.md §9) through the existing manifest module. TEVV evidence logged per document. No extraction in this task — manifest entry only.

## Standing constraints

- All manifest writes go through the manifest module (event-sourced projection, five rejection paths, hash verify). No direct edits to any projection file.
- Primary-source acquisition only (DD-002): fetch each document from its primary URL. Do not substitute local copies from icsp_notebook or elsewhere. If a fetch fails, STOP on that document, record the failure, continue with the others, and report.
- No bulk work. Exactly these 5 documents.
- Run `seldon cc complete cc_tasks/2026-07-03_pilot_manifest_adds.md` when done, then `seldon verify`.

## The 5 pilot documents

| # | Title | Primary URL | source_type |
|---|-------|-------------|-------------|
| 1 | FCSM 25-03: AI-Ready Federal Statistical Data — An Extension of Communicating Data Quality | https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf | federal |
| 2 | America's DataHub RFS Topic MLMU-25: Measuring LLM Understanding of Federal Statistical Data | https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf | federal |
| 3 | Lawrence, Data Readiness Levels (2017) | https://arxiv.org/abs/1705.02245 (acquire PDF: https://arxiv.org/pdf/1705.02245) | academic |
| 4 | Cisco Global AI Readiness Index 2024 | Landing: https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/archive/2024-m11.html — **resolve the PDF variant from this page.** If no stable PDF can be resolved, STOP on this document and report; do not substitute another industry source. | industry |
| 5 | AIDRIN: AI Data Readiness Inspector (Hiniduma et al., arXiv 2406.19256) | https://arxiv.org/abs/2406.19256 (acquire PDF: https://arxiv.org/pdf/2406.19256) | academic |

## TEVV evidence per document (log with each manifest-add event)

- **Test:** HTTP fetch from primary URL succeeded; record final URL after redirects, HTTP status, retrieval timestamp (UTC).
- **Evaluation:** document identity check — title/authors/year in the fetched document match the candidate register entry (corpus/staging/candidate_register.jsonl). Mismatch = rejection path, not silent correction.
- **Verification:** sha256 of acquired file recorded in manifest entry; re-hash after write to disk and confirm match.
- **Validation:** file opens and is the substantive document (not an error page, redirect stub, or abstract-only page). Record page count.

Evidence lives in the manifest-add events themselves plus a short run log at `corpus/staging/pilot_adds_run_log.md` (new file, committed).

## Acceptance criteria

1. 5 manifest entries (or N entries + explicit STOP reports for failures) via the manifest module, all events in the sharded event log.
2. Register entries for the 5 docs updated in candidate_register.jsonl: status field noting manifest-added (register is local/gitignored; this is bookkeeping, not provenance).
3. Run log committed. Zero writes outside ai-readiness-kg.
4. `seldon verify` clean.

## Out of scope

- Extraction (next CC task).
- The other 84 candidates.
- The webb_nist_fcsm_crosswalk DOI fix (task cc082aaa, not a pilot doc).
- Schema edits (intergovernmental source_type value rides with the extraction-module task).
