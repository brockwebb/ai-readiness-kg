# CC Task — Cisco Inbox Add v2 (2025 edition + methodology + instrument capture)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Supersedes:** cc_tasks/2026-07-03_cisco_inbox_add.md (fc94ae2f — never executed; operator acquired the 2025 third edition instead of the 2024 index, plus the methodology page and the survey instrument as browser printouts. Desktop triage decision: 2025 replaces 2024 as pilot doc #4.)

## Inbox contents (operator-acquired, manual browser)

```
corpus/staging/inbox/
├── cisco-ai-readiness-index-2025-realizing-the-value-of-ai.pdf   (report)
├── Cisco AI Readiness Index Methodology - Cisco.pdf               (methodology page printout)
├── Cisco AI Readiness Assessment - Cisco.pdf                      (instrument printout, likely page 1)
└── Cisco AI Readiness Assessment - Cisco page 2..6.pdf            (instrument printouts, pages 2–6)
```

## Objective

Three manifest entries via the module:

**A. Cisco AI Readiness Index 2025 — "Realizing the Value of AI" (PILOT DOC #4)**
- Canonical download_url (Desktop-verified): https://www.cisco.com/c/dam/m/en_us/solutions/ai/readiness-index/2025-m10/documents/cisco-ai-readiness-index-2025-realizing-the-value-of-ai.pdf
- Landing: https://www.cisco.com/c/m/en_us/solutions/ai/readiness-index.html
- Identity check against 2025 edition: title "Realizing the Value of AI", third edition, six pillars, 8,000+ leaders / 30 markets. NOT the 2024 identity from the superseded task.
- **Register correction:** update the existing Cisco 2024 register entry to the 2025 edition (title, year, URLs), and record the change as a triage decision in the entry (e.g. `triage_note: "2026-07-03 Desktop: 2025 third edition replaces 2024 as pilot industry doc; 2024 landing page blocked automated fetch"`).
- source_type: industry. acquisition_method: manual_browser.

**B. Cisco AI Readiness Index Methodology (web page capture) — non-pilot**
- New register entry (discovered_via: operator) + manifest-add.
- Extract the source URL from the printout's browser header/footer; if absent, STOP on this item and report — do not guess.
- source_type: industry. acquisition_method: manual_browser_print. Note in evidence: web page capture, not a versioned publication.

**C. Cisco AI Readiness Assessment — survey instrument (web capture) — non-pilot**
- Merge the 6 instrument printouts into a single PDF, ordered by content continuity (verify the unnumbered file is page 1; record the final order in the run log). Merged file is the manifest artifact; record each component file's sha256 in the acquisition evidence block.
- Extract source URL from printout headers; STOP if absent.
- source_type: industry. acquisition_method: manual_browser_print. Note: this is the survey instrument itself — relevant to the ai-readiness-fss instrument design work; tag accordingly if the register schema supports tags.

## Rules

- All writes through the manifest module. Primary provenance = URLs above / extracted from printouts, never guessed.
- Pilot extraction set remains exactly 5 documents; B and C are manifest-only, not pilot.
- Acquired files move inbox → corpus/pilot/ (A) and corpus/cisco/ or similar gitignored location (B, C — CC's choice, gitignored, documented). Inbox empty after processing.
- Append run log (corpus/staging/pilot_adds_run_log.md). `seldon cc complete cc_tasks/2026-07-03_cisco_inbox_add_v2.md`; `seldon verify`.

## Acceptance criteria

1. 3 manifest entries (or N + explicit STOPs), events in sharded log, evidence blocks populated.
2. Register: Cisco entry corrected to 2025 with triage note; 2 new operator entries.
3. Inbox empty, gitignore intact, run log appended, zero writes outside ai-readiness-kg.
