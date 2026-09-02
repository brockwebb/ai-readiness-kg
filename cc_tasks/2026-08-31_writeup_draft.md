# CC Task — Writeup draft: chunked-pilot and bulk-burn results for external publication (f1da94c6)

**Date:** 2026-08-31 (late). **Repo:** /Users/brock/GitHub/ai-readiness-kg. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-31_writeup_draft_ADDENDUM*.md`; read `docs/research/writeup_foils.md` in full (it is the framing spec and its corrections supersede chat), then the RESULTs: chunked pilot (+§3 closure), ground_truth_yield_floor, extraction_queue, bulk_extraction_v038 (all appended sections), ingestion_conversion, extent_remediation.
**Result:** `cc_tasks/2026-08-31_writeup_draft_RESULT.md` (short); the deliverable is the draft. Close THIS registered file's task on completion; leave `f1da94c6` open — it closes when the operator accepts a final version, not when a draft exists.
**Spend:** zero extraction-ledger spend; this is authoring. Read-only against shards/ledgers (snapshot if the burn is writing). Do not touch burn files or queue.

**Deliverable:** `docs/research/writeup_draft_v1.md` — a complete first draft, FCSM-workshop register (methods-serious, federal-statistics audience), target 3,000–4,500 words. DRAFT watermark line at top with the state timestamp. Burn-dependent numbers marked `[as of <timestamp>; final at burn close]` — do not wait for the burn.

## Thesis (from the foils, restated as the spine)

Agent-memory and KG-extraction patterns ship quality operations without quality measurement. This project shipped the measurement layer — pre-registered gates, acceptance sampling, mutation-verified monitors — and the paper's credibility move is that the measurement layer's own failures are the findings: the pre-registered floor was 63% edges against a nodes-only instrument (commensurability, DD-028); a mid-task metric convention change handled by recorded sequencing; impossible values as the cheapest bug detectors; eight instances of tests measuring artifacts instead of generators; four instances of derived identity moving under provenance until identity became a logged fact. Self-implicating throughout; the Census analogy (estimates without MOEs vs estimates with) carries the frame. Foils: Karpathy LLM Wiki (lint = coherence, not correspondence — use the corrected characterization) and OKF (format, deliberately quality-agnostic).

## Structure

1. Problem and frame (measurement vs operations; Census analogy) — brief.
2. System in one page: corpus with admit/cut-with-reason, DD-030 substrate gate, pinned profiles, chunk-anchor contract (DD-023), demand-pull (DD-024), event-sourced state.
3. Qualification: arms, probe protocol with intervals, the floor saga told straight (45.23 → unit error → 5.16 → limitations ON the verdict), A2 by measurement.
4. Production: stratified confirmation gate (actual Phase A numbers), SPRT parameters fixed pre-data, batch results to date, quarantine design, spend ledger discipline.
5. Findings about the measurement layer itself (the exhibits above, each 1–2 paragraphs, dated and citable to RESULTs).
6. Related patterns (foils, fair and corrected) and what the field should adopt: gate-unit commensurability, mutation-verified monitors, sequencing-recorded judgment, identity as logged fact.
7. Limitations, honest and specific (model-defined ground truth, n, single corpus, nodes-not-edges validated).

## Constraints

Every number from a RESULT/ledger with its interval or n; no number from chat. House style: short plain sentences, no bold in prose, no em-dashes, no one-sentence paragraphs, no AI-tell phrases, "confabulation" not "hallucination". Verified numbers only; anything unverifiable is cut. No claims of semantic-edge validation. Prior-art citations from the foils and task files carried with their sources.
