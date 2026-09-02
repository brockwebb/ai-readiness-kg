# CC Task — Extent remediation: re-acquire the six thin-extent documents

**Date:** 2026-08-31. **Repo:** /Users/brock/GitHub/ai-readiness-kg. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-31_extent_remediation_ADDENDUM*.md`; read `cc_tasks/2026-08-31_ingestion_conversion_RESULT.md` §0–§2 (the premise this task rests on).
**Result:** `cc_tasks/2026-08-31_extent_remediation_RESULT.md`; `seldon cc complete` this file AND the six auto-registered gap tasks (`21133dbf`, `27b65335`, `8dce1f53`, `17f166d8`, `ce774778`→verify exact id from graph, `e31c911d`) — reconcile the id list against `seldon_task_list` before closing anything; commit, push.
**Spend:** zero model tokens (`--ceiling-tokens 0`). Acquisition is fetching; conversion is the DD-030 pipeline. Any model call is a defect. Extraction is NOT this task.

## Prior art (DD-025 block)

**Internal.** Kernel harvest extent discipline (2026-08-21): `extent_note` / `extent_dropped_sections` — the recorded practice this lane failed to inherit; DD-030 (admission convertibility + extent gate — the instrument that caught all six); dixie evidence ledger admission discipline (admit-with-reason, cut-with-reason); `document-ingest` skill (the pipeline every acquisition now goes through).
**External.** llms.txt convention (the akamai index page points at one — use it; that is what it is for); W3C/standards-body canonical-source practice: prefer the publisher's native source over a rendered page when one exists.

## The rule

Re-acquisition targets the **canonical fullest source**, preferring native markdown/text over rendered HTML over PDF-of-HTML. Every acquired document passes the DD-030 gate; clearing the extent gate is this task's acceptance criterion per document. Same `doc_id`, new acquisition event with new `source_sha256`; frontmatter carries the extent decision (`extent_note`: what was included, what was deliberately not). A document that cannot be remediated gets cut-with-reason, demand and all — recorded, not silent.

## Per-document direction (verify, don't inherit — sources may have moved)

1. **`odcs-open-data-contract-standard`** (2 demand): the Bitol/LF standard is maintained as native markdown in its GitHub repo — locate the versioned spec source and acquire that, not the site rendering. Record version pinned.
2. **`slsa-specification-v1-0`** (2 demand): the RESULT enumerated the eight sub-pages with their sizes (requirements 13,858 chars, threats 21,404, terminology 16,058, levels 8,228, …). Acquire all; decide merged-single-substrate vs per-subpage substrate on the grounds of how T1 chunking and citation anchors work, record the decision and reason. Per-section source URLs in frontmatter either way.
3. **`ddi-codebook-specification`**: acquire the actual codebook specification (field-level documentation), not the landing page.
4. **`akamai-datastream-2-docs`**: follow the `llms.txt` index the page advertises; acquire what it enumerates within reason (extent decision recorded).
5. **`digital-gov-website-standards`**: the standards content behind the hero page.
6. **`itu-ai-ready-analysis-towards-a-standardized-readiness-frame`**: the capture is a navbar. Find the actual publication — likely a PDF; if so it delegates to the existing PDF path and the extent gate still applies to what lands.

Documents 3–6 carry no crosswalk demand today; remediate them anyway (the gap is real and acquisition is cheap), but if any proves unreachable or paywalled, cut-with-reason is the correct outcome, not heroics.

## Deliverables

- [ ] Six acquisition events with extent notes; substrate through the DD-030 pipeline; gate verdicts per document (target: 6/6 clear, any miss explained)
- [ ] Frontmatter re-verification green (`verify_substrate()` over the six)
- [ ] The six gap tasks closed with pointers to this RESULT; graph reconciled
- [ ] **Queue reconciliation, liveness-gated:** if and only if no bulk process is alive (check, record the check), withdraw/defer the two stale `queued` requests for odcs+slsa (they rest on the corrected premise) with reason `awaiting_reacquisition` superseded by fresh state as appropriate. If a burn is running, DO NOT touch the queue — record the deferral of this item to the next burn start and say so in the RESULT.
- [ ] Explicitly NOT done here: extraction requests, substrate wiring into `doc_text` (both owned by next burn start per ingestion RESULT §3), any edit to running-burn files
- [ ] Tests: extent gate driven with the re-acquired documents as positive controls (real spec must pass; the old TOC captures must still fail — keep them as fixtures for exactly that); suite green, count reported

## Out of scope

Extraction spend; changes to gate thresholds (six true positives is evidence they sit right — moving them needs its own task with its own measurement); PDF corpus; the three deferred W3C/crosswalk docs that passed the gate (their substrate is good; they stay deferred on demand grounds).
