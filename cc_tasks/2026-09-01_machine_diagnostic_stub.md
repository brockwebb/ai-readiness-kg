# CC Task: Stub the FSS Machine Diagnostic (SEO SME draft) into the crosswalk — conceptual level only

**Date:** 2026-09-01
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-01_machine_diagnostic_stub_ADDENDUM*.md` files.**

## Context

An SEO SME colleague produced a draft technical specification, "FSS Technical SEO/AIO Machine Diagnostic," operationalizing the machine-diagnostic portion of the FSS Data AI Readiness Roadmap. It defines four readiness dimensions (Discoverability; Indexability & Retrievability; Machine Understandability & Citation Readiness; Ingestibility & Computational Usability), a ~60-field common data dictionary, a versioned warning-rule catalog (~70 rule IDs, HTTP_5XX through APP_MACHINE_CONTEXT_MISSING), and an application-diagnostic path for JS-heavy data tools.

**Desktop assessment (recorded, not re-litigated here):** the spec is a Tier-1 measurement instrument for the discoverability/access slice of the crosswalk. Its complexity is enumeration, not architecture. Three elements are worth adopting now at conceptual level; the item-level rule catalog is deferred.

## Provenance and admission gate (decision, already made)

The source is an **internal draft** held by the operator — no stable URL, no version identifier, not stranger-citable. Therefore:

- **NOT manifest-admitted.** Do not create a `manifest_add` event for it.
- Referenced in the crosswalk as a class-(c)-style internal source: `internal draft: FSS Machine Diagnostic spec (SEO SME, 2026-09, operator-held; admission gated on finalization/publication)`.
- Register the future admission as a gap in §9 (step 4 below).

## Steps

All edits target `docs/crosswalk/usafacts_operationalization_skeleton.md`. Keep the stub small — this task adds 2 indicator rows, 1 design-stance paragraph, 2 §9 entries, and a version-note line. Nothing else.

### 1. Add two indicator rows to the §2 Criterion A table

| # | Construct | Candidate indicator | Type | Evidence | Tier | Status |
|---|---|---|---|---|---|---|
| A10 | Application/data-tool machine surface | Interactive data tools expose stable, directly-requestable deep links; meaningful states are not fragment-only or session-dependent; invalid routes return true 404/410, not HTTP-200 shell (soft-404); page-specific content present in raw HTML before JS execution | AUTO | internal draft: FSS Machine Diagnostic spec (SEO SME, 2026-09, operator-held; admission gated) | `public` | stub |
| A11 | Effective crawler access (declared / enforced / observed) | A4 upgraded from declared-policy check to three-layer comparison: declared (robots.txt/meta directives) vs enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs). A mismatch between layers is itself the finding, not an error state | AUTO + agency_instrumented | `cloudflare-ai-crawl-control-manage-crawlers`; `rfc-9309-robots-exclusion-protocol`; internal draft: FSS Machine Diagnostic spec (as above) | `agency_instrumented` (observed leg requires edge logs; declared leg stays `public`) | stub |

Formatting must match the existing table exactly. Do not renumber or edit existing rows A1–A9.

### 2. Add one numbered item to §6b (instrument design decisions)

Append as item 5:

> 5. **Observed facts vs versioned warning rules (adopted from the Machine Diagnostic spec, 2026-09-01).** The instrument stores raw observed facts separately from calculated warnings; warnings are produced by deterministic, versioned rules so thresholds can change and history can be re-scored without re-measurement. This is the measurement-side counterpart of E2 (pre-registered thresholds) and E3 (instrument versioning), and applies to all AUTO indicators when the scoring harness is built.

### 3. Add a note to §5d G1 (do not modify the G1 row itself)

Append one sentence to the paragraph below the §5d table (the one beginning "G1 is the sharpest gap..."):

> The declared/enforced/observed triad (A11) is the candidate measurement template for G1: declared uncertainty (structured MOE/CV fields) vs surfaced uncertainty (what retrieval delivers) vs observed preservation (what AI restatements carry).

### 4. Add two entries to §9 (gaps registered)

- `FSS Machine Diagnostic spec (SEO SME) — internal draft; manifest admission gated on finalization/publication. On admission: revive item-level crosswalk of its rule catalog (~70 rule IDs) against indicators A4–A6, A10–A11, C4. Deferred 2026-09-01, reasons: source is draft + below_burn_scope.`
- `Application-diagnostic evidence gap: no admitted corpus document currently grounds A10 (soft-404 / deep-link / raw-HTML-content checks for statistical data tools). Demand-pull target; the internal draft is the placeholder, not the evidence.`

### 5. Version note

Update the file's **Status** line: append `; v0.2.1 2026-09-01: Machine Diagnostic stub (A10, A11, §6b.5, G1 note, two §9 gaps) — task cc_tasks/2026-09-01_machine_diagnostic_stub.md`.

## Constraints

- No extraction, no model calls, zero spend. File edits + registration only.
- Do not import the field dictionary or rule catalog. The ~70 rule IDs enter only as the deferred-revival note in §9.
- Do not touch `corpus/manifest.json`, the event log, or the burn (paused; leave paused).
- Any discrepancy between this task's premises and live file state goes in the RESULT, never silently reconciled.

## Completion

- Run `seldon verify` after edits.
- Write `cc_tasks/2026-09-01_machine_diagnostic_stub_RESULT.md`.
- Run `seldon cc complete cc_tasks/2026-09-01_machine_diagnostic_stub.md`.
- Commit and push (task file, RESULT, crosswalk edit together).
