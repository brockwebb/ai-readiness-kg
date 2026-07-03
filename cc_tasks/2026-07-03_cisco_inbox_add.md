# CC Task — Cisco Manual Acquisition via Inbox

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Predecessor:** cc_tasks/2026-07-03_pilot_manifest_adds.md (Cisco STOPped on 403 bot protection; this task completes pilot doc #4 via operator manual acquisition)

## Objective

Manifest-add the Cisco Global AI Readiness Index 2024 PDF from the manual inbox. This establishes the inbox convention: `corpus/staging/inbox/` is the drop zone for operator-acquired documents that automated fetch cannot reach.

## Preconditions (STOP if unmet)

1. File present in `corpus/staging/inbox/` (operator downloads it in a browser first). If the inbox is empty or missing, STOP and report — do not fetch, do not substitute.
2. Operator-confirmed source URL available. Check the top of `corpus/staging/pilot_adds_run_log.md` or ask via report if not recorded; do not guess the URL.

## Steps

1. Create `corpus/staging/inbox/` if absent; ensure it is gitignored (extend .gitignore if needed).
2. Identity check the PDF against the register entry (title text in document body: "Cisco AI Readiness Index" / 2024; six-pillar methodology present). Mismatch = STOP, not correction.
3. sha256 hash; manifest-add through the module with the acquisition evidence block:
   - `acquisition_method: manual_browser`
   - `primary_url:` the landing page https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index/archive/2024-m11.html
   - `download_url:` the operator-confirmed direct PDF URL
   - retrieval timestamp (operator download date if known, else file mtime), page count
4. Move file from inbox to `corpus/pilot/` (gitignored, same as the other four).
5. Update the register entry `register_status` for Cisco; append a dated entry to the run log (append only — the log is a log, not an immutable task file).
6. `seldon cc complete cc_tasks/2026-07-03_cisco_inbox_add.md`; `seldon verify`.

## Acceptance criteria

1. 5th manifest entry via the module, event in the sharded log, acquisition evidence block populated with manual_browser method.
2. Inbox exists, gitignored, empty after processing.
3. Run log appended; zero writes outside ai-readiness-kg.

## Out of scope

- Extraction. Everything else.
