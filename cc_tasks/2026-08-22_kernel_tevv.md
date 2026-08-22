# CC Task — Kernel TEVV: stability, faithfulness, evidence-grade calibration

**Date:** 2026-08-22
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Max OAuth only; `ANTHROPIC_API_KEY` unset or abort.
**Execution model:** Multi-agent permitted (stability re-extraction and faithfulness judging are independent once the sample is drawn). Phases write sub-RESULTs under `docs/research/2026-08-22_tevv_*`; orchestrator assembles `cc_tasks/2026-08-22_kernel_tevv_RESULT.md`, citing Seldon task id from registration.
**This file is immutable.** Discrepancies are reported in the RESULT, never reconciled.
**Operator contact policy:** None expected. Every decision below has a rule. If a situation arises that no rule covers, make a grounded choice, log it under "Standing decisions" in the RESULT, and continue. Do not stop to ask. The only halt conditions are the two STOPs in Phase 4 and Phase 6, and both halt the phase, not the task.

## Goal

Measure whether the extractions are valid, not merely whether the process is stable. Three measurements, all pre-registered here before data: (1) test-retest stability of extraction, (2) faithfulness of extracted items to their grounding spans, (3) calibration of `Claim.evidence_grade` against document-level ground truth. Results become pre-registered gates in `dixie_evidence.yaml` and, where useful, monitors.

## Pre-registered thresholds (set here, not after data; fails are findings)

- **Stability:** Cohen's κ on item presence per node type ≥ 0.61 (Landis & Koch 1977 "substantial" band lower bound); mean Jaccard on grounded-span sets per document ≥ 0.70. Both computed per document and pooled.
- **Faithfulness:** judge-scored entailment precision ≥ 0.90 pooled and ≥ 0.85 in every stratum. Rationale: same order as the repo's existing quarantine ceiling (0.15 = 0.85 admitted); a validity floor should not be looser than the admission floor.
- **Grade calibration:** `platform_official` precision ≥ 0.90 against `is_platform_operator`; `peer_reviewed_experiment` precision ≥ 0.90 against `source_type in {academic, preprint}` (use the actual enum values in `schema.yaml`).
- Thresholds are written to `dixie_evidence.yaml` under a new `tevv_gates` block **before** Phase 3 runs, with this task file cited as source.

## Phase 0 — Preflight (zero spend)

1. `python -m pytest tests/ -q` green; record count.
2. Record `controls.yaml` sha256; set `extract: on`, `extract_daily_docs: 20` (AUTH pattern from 2026-08-21 task); restore byte-identical at end.
3. Add `Document.is_platform_operator` (boolean, nullable) to `kg/schema.yaml` and `docs/schema_v0.1.md` as v0.3.1, append-only; extend `tests/test_schema_append_only.py`. Populate it for all 134 documents by rule: true if the issuing organization operates a search engine, crawler, CDN/bot-control product, or LLM retrieval system named in the document's `Platform` nodes or in its `authors`/`publisher`; else false. Emit as one `document_annotation` event per doc in a new shard `events/batch-007.jsonl`. Log the rule's decision for each doc in the Phase 0 sub-RESULT. Ambiguous cases (e.g., GSA for DAP/Search.gov): **true**, with note; the grading-confusion finding in the kernel RESULT is the reason this field exists.

## Phase 1 — Sample draw (zero spend, deterministic)

- Seed: `20260822`. Record it.
- **Stability set:** 8 documents, stratified 4 from `v1` and 4 from `kernel_v03`; within each epoch, one per `source_type` stratum where available, selected by seeded random. Exclude the two 0.10–0.15 quarantine docs and any doc >120K chars (cost control; note the exclusion). Write the list to `docs/research/2026-08-22_tevv_sample.md`.
- **Faithfulness set:** 200 items (nodes and edges) drawn seeded-random, stratified proportionally by node/edge type and by `evidence_grade` (v1 Claims form their own "ungraded" stratum). Minimum 10 per stratum; merge strata smaller than 10 into "other" and say so. Write to `corpus/staging/metrics/tevv_faithfulness_sample.jsonl` with item id, type, text, grounding span, doc id.
- **Human calibration subset:** 40 of the 200, seeded-random, written to `corpus/staging/metrics/tevv_human_subset.jsonl` with a blank `human_label` column. This is produced for the operator to rate at any later time; **it does not block anything**. The RESULT reports judge-only precision with status `uncalibrated_pending_human` until the file has labels, at which point a follow-on recomputes.

## Phase 2 — Stability re-extraction (extraction spend; parallel with Phase 3)

- Re-extract the 8 docs under the identical profile, model config, and prompt template version that produced their original extraction (read it from the original events; do not assume). Write to a scratch event shard `events/batch-008_tevv_retest.jsonl`, flagged `purpose: tevv_retest` on every event so `build_projection.py` can exclude it. Extend `build_projection.py` to skip `purpose: tevv_retest` events; add a test.
- Rate: extract the first doc alone, record tokens and wall-clock, project the remaining seven. Proceed regardless; this is a fixed 8.
- Compute per doc: κ on item presence per node type (item identity = type + NFKC-normalized text; edge identity = type + endpoint identities), Jaccard on grounded-span sets, count of items present in only one run. Pooled values. Write `docs/research/2026-08-22_tevv_stability.md` with the tables and a one-paragraph reading of which node types are unstable.

## Phase 3 — Faithfulness judging (model spend, cheap; parallel with Phase 2)

- Judge = the pinned extraction model under Max OAuth via the existing `model_stub` path (hermetic cwd), with a new judging prompt template versioned and stamped. One item per call; output strictly `{entailed: true|false, reason: str}`. Persist raw responses beside events as the extraction runner does.
- Precision per stratum and pooled. Write `docs/research/2026-08-22_tevv_faithfulness.md`.
- Known limitation recorded, not solved: the judge is the same model family as the extractor. The 40-item human subset exists for that reason.

## Phase 4 — Grade calibration (zero spend)

- For every kernel Claim: compare `evidence_grade` to the document signals (`is_platform_operator`, `source_type`). Confusion matrix for the two graded classes above; distribution table for the rest.
- **STOP (phase only):** if `platform_official` precision < 0.70, do not write a gate for it; write the finding and recommend a prompt-template fix as a follow-on task in the RESULT. Continue to Phase 5.

## Phase 5 — Gates and monitors

- Append `tevv_gates` results to `dixie_evidence.yaml` as realized values next to the pre-registered thresholds (thresholds unchanged regardless of outcome).
- Extend `run_baseline_gates.py` to evaluate `tevv_gates` when the retest shard exists; add tests.
- If stability κ for any node type < 0.61, add a per-type stability monitor to `scripts/quality_monitors.py` with the same mutation-test positive control requirement as the existing five; a monitor is not verified until a seeded bad fires it.

## Phase 6 — Close

- Restore `controls.yaml`; record sha256 match.
- `docs/design_decisions.md`: append **DD-013** (TEVV pre-registration and the same-family judge limitation) and **DD-014** (`is_platform_operator` signal and its rule).
- Register results in Seldon (`seldon result register` via CLI is not used from Desktop; CC runs it) for κ pooled, Jaccard pooled, faithfulness pooled, grade precisions.
- Full test suite green; **commit and push** repo and any dixie changes, per CLAUDE.md.
- **STOP (task):** grounding gate must still be 0 after projection rebuild; if not, halt before commit and write the RESULT.

## Out of scope

Concept dedup; construct promotion; proposed-relationship review; any new harvest; re-running the two high-quarantine docs; threshold changes after data; editing this file.

## RESULT must contain

Phase status table; seed; sample lists; rate measurement; κ and Jaccard tables; faithfulness precision by stratum with `uncalibrated_pending_human` status; confusion matrices; gate table with pre-registered vs realized; monitor mutation results; token totals with cost UNKNOWN where unpriced; controls sha before/after; standing decisions; commit hashes.
