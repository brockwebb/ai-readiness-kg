# CC Task — Source-list triage, construct tagging, and manifest decisions (zero model spend)

**Date:** 2026-08-24
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** No model calls in this task. Fetching, hashing, register writes, manifest events only. Safe to run concurrently with a2d3fb42 / 36a5c0e1; do not touch their shards or worklists.
**Immutable file. Operator contact: none — every decision below has a rule; the operator reviews the decision log afterward and overrides by addendum-driven follow-up, not mid-task.**
**Sub-RESULTs under `docs/research/2026-08-24_triage_*`; final `cc_tasks/2026-08-24_source_triage_RESULT.md` citing the Seldon task id.**

## Inputs

1. The 2026-08-24 source list provided by the FSS research group (reproduced in full in `docs/research/2026-08-24_sme_source_list.md` — Phase 0 writes this file verbatim from the operator's transmission in the task context; it is the citable record of what was received).
2. The standing SEO/AIO-lineage gap list from the 2026-08-22 chat decision (enumerated in Phase 3).
3. Existing `corpus/staging/candidate_register.jsonl` and the live manifest (dedupe targets).

## Provenance rule for this batch

Every register entry from input 1 carries `vetting: {source: "fss_research_group_2026-08", expertise: "generalist_federal_statistics", weight: "signal_not_verdict"}`. Vetting by non-domain experts is recorded and never treated as satisfying the inclusion rule by itself.

## Schema v0.3.3 (append-only, Phase 0)

- `Document.construct_arm`, enum: `publication_actionability` | `training_data_readiness` | `org_maturity`. Required on all manifest adds from this task; backfill for existing 134 documents by rule (existing kernel-v03 → `publication_actionability` unless obviously otherwise; v1 readiness corpus → tag per document by title/abstract rule, logged). Extend append-only test; update `docs/schema_v0.1.md`.
- Register field `grounding_surface`: `document` (default) | `transcript` | `slides`. Slides and transcripts are admissible but flagged; their extraction quality gets its own stratum in any future TEVV run.

## Inclusion rules (written here; every verdict logged with the clause it matched)

- **R1 (publication_actionability):** include any document whose primary subject is making published data/content discoverable, retrievable, or interpretable by machine consumers (AI-ready dissemination, metadata standards, MCP/agent access, discoverability). This is the graph's target construct; err inclusive.
- **R2 (training_data_readiness):** include only documents that define, measure, or frame readiness constructs generally (definitional papers, frameworks, metrics, reviews: e.g. Lawrence-lineage DRL work, DRAI/maturity matrices, AIDRIN, SciHorizon, FAIR-R, FAIR², metadata-ecosystem reviews). Exclude domain-application papers whose content is a specific preprocessing pipeline for a specific scientific domain (e.g. single-cell RNA, cancer wearables, EO fine-tuning, space life sciences, building-sector RAG, vendor lakehouse articles) unless they state a general readiness framework as a contribution. Exclusions are `excluded_by_rule: R2_domain_application`, individually logged.
- **R3 (org_maturity):** include instruments, indexes, and definitional statements (Gartner, Cisco if not already held, the DOC RFI itself and all listed RFI comment letters — the comment letters are primary evidence of definitional contest and are public on regulations.gov). Exclude market-survey press releases unless they carry an instrument or definition (the Informatica/Salesforce item: include the underlying report if fetchable, exclude if only the press release exists, logged either way).
- **R4 (off-construct check):** any document whose subject is AI adoption/diffusion economics or labor impacts (the Census CES-WP-26-25 working paper) is `flagged_off_construct`, not fetched into the corpus, and listed for operator confirmation in the decision log. Do not manifest.
- **R5 (dedupe):** anything whose primary URL, DOI, or normalized title matches an existing register or manifest entry is `already_held` / `already_registered`; never re-fetch. Expected hits: FCSM 25-03, Croissant (Akhtar et al.), DCAT-US 3, Cisco index, possibly M-25-05 adjacent OMB items.

## Phase 1 — Register and fetch (public items)

For every input-1 item: normalize citation, resolve URL, attempt fetch with capture provenance (sha256, timestamp, content-type). Register `candidate_status`: `fetched` | `fetch_failed` | `access_blocked` (paywall/login detected — SSRN, Wiley, ResearchGate, Gartner likely) | `excluded_by_rule` | `already_held` | `flagged_off_construct`. PDFs land in `corpus/staging/inbox/triage_2026-08-24/`.

## Phase 2 — Access-class routing

- **max.gov presentations (10 FCSM slide decks):** do not attempt credentialed fetch. Write `docs/research/2026-08-24_operator_download_list.md`: exact URLs, target filenames, drop location `corpus/staging/inbox/maxgov/`. Register each as `awaiting_operator_drop`, `grounding_surface: slides`. A later sweep ingests whatever appears; nothing waits.
- **Video/podcast (2 YouTube, 1 vlog):** transcript acquisition via the established ingest-youtube path into staging with capture provenance; register `grounding_surface: transcript`. If transcript unavailable, `fetch_failed`, logged.
- **access_blocked items:** registered with the blocking domain recorded. The decision log lists them so the operator can supply PDFs through the inbox if he has library access; nothing waits.

## Phase 3 — SEO/AIO-lineage gap harvest (same machinery, same rules)

Reconcile against the kernel register first (much of this landed in kernel-v03), then fetch what is genuinely missing, R1 governs: Google Search Central pages not yet held; Bing IndexNow and AI-performance docs; sitemaps/robots/llms.txt/Web Bot Auth drafts if missed; MCP specification; NLWeb; WebMCP; the Google Open Knowledge Format spec (github SPEC.md) from the source list; Data Commons documentation; IMF StatGPT public documentation if it exists as a fetchable primary source. Each entry logged with whether it was already-held or newly fetched.

## Phase 4 — Manifest decisions

Rule-based manifest adds (AUTH-2 pattern) for every `fetched` item passing R1–R3, carrying `construct_arm`, `grounding_surface`, vetting provenance, and the matched rule clause in the manifest event. No extraction. Items in `awaiting_operator_drop` and `access_blocked` are NOT manifested (manifest admission requires the artifact in hand with its hash — no exceptions, that is the manifest's whole meaning).

## Phase 5 — Decision log and close

`docs/research/2026-08-24_triage_decision_log.md`: one line per input item — verdict, rule clause, construct arm, access class, dedupe result. Summary counts. The off-construct flags and access-blocked lists surfaced at top for operator reading. Backfill report for `construct_arm` on the existing corpus. Seldon results: counts per verdict class. Tests green (append-only test extended); **commit and push**.

## Out of scope

Extraction (follow-on task, sized after a2d3fb42's spend accounting); manifest admission of anything not physically in staging; credentialed fetching of any kind; touching running tasks' state; SQLite/serving-layer manifest projections (separate serving-layer task); editing this file.
