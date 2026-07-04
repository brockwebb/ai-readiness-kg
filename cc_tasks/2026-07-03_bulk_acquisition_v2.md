# CC Task — Bulk Acquisition v2 (register promoted to committed screening log)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Supersedes:** cc_tasks/2026-07-03_bulk_acquisition.md (fd49d222 — never executed; its "register is local/gitignored bookkeeping" premise reversed by operator decision: the register is the corpus screening log and must be committed, decision-complete provenance. Acquisition rules carry forward verbatim.)

## Part 0 — Register becomes the committed screening log (do FIRST)

Rationale on record: PRISMA-style inclusion/exclusion documentation — every candidate examined gets a durable in/out decision with reason. Screening decisions live in the register (git-versioned); acquisition decisions live in manifest events. Two layers, no gaps.

1. Un-gitignore corpus/staging/candidate_register.jsonl; verify it contains only metadata (titles, URLs, hashes, statuses — no document content), then commit.
2. Add decision fields to every entry: `status` ∈ {manifested, excluded, needs_source, pending}, `decision_reason` (one line), `decided_at`, `decided_by` ∈ {operator, desktop, cc}.
3. Backfill this session's known decisions:
   - 5 pilot docs + Cisco methodology + Cisco instrument → manifested (reasons: pilot slot / operator addition)
   - IBM think-topic page + IBM CDO blog → excluded, "thin marketing content, no stable versioning; Cisco chosen for industry slot (Desktop 2026-07-03)"
   - Cisco 2024 entry → already corrected to 2025; ensure decision_reason carries the swap note
   - MIT NANDA, Absorb press release, M-25-21, M-25-22 → needs_source with existing flags as reasons
   - webb_nist_fcsm_crosswalk → pending, DOI https://doi.org/10.5281/zenodo.18772590 recorded (acquire in Part 1; close task cc082aaa on success)
   - Everything else → pending
4. Commit before starting Part 1, so every acquisition outcome lands as a register diff.

## Part 1 — Acquisition (carried forward verbatim from fd49d222)

Manifest-add every register entry with a usable primary URL not already manifested. Fetch from primary URL only; per-doc TEVV evidence (fetch record, identity check vs register, sha256 + re-hash, substantive-document check, page count) in manifest-add events; all writes through the manifest module. Per-doc failure = record and continue; no substitutions, no guessed URLs. needs_source skipped. PDFs to gitignored corpus locations. Landing-page-only entries: attempt stable PDF resolution; else → needs_source with reason. Batch commits every ~15 docs. **Every outcome updates the register entry's decision fields in the same batch commit** (acquired → manifested; failed → needs_source or pending with reason).

## Deliverables

1. Committed decision-complete register; manifest entries + events for all acquirable candidates.
2. docs/research/bulk_acquisition_report.md: counts (manifested / excluded / needs_source / pending), full failure list with reasons and leads.
3. cc082aaa closed if crosswalk acquired. `seldon cc complete cc_tasks/2026-07-03_bulk_acquisition_v2.md`; `seldon verify` clean.

## Out of scope

Extraction. Ingested transitions. Manual-inbox items. New exclusion rulings beyond the backfill list — anything genuinely ambiguous stays pending for the operator.
