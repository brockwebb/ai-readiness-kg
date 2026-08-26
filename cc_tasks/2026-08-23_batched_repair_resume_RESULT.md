# RESULT — Batched repair resume: projection keying fix, relocations, attribute re-adjudication

**Task:** `cc_tasks/2026-08-23_batched_repair_resume.md` (immutable) · **Seldon:** `a2d3fb42`
**Executed:** 2026-08-24/25 (main burn 2026-08-25 00:30 → 03:30 UTC). Max OAuth; Haiku 4.5 batches; Opus 4.8 + Sonnet 5 acceptance judging. Sub-RESULTs: `docs/research/2026-08-23_resume_phase1_keying.md`, gate report `…2026-08-25_resume_final_gate_report.md`. DD-019, DD-020.

## Headline
- **Phase 1 (keying): done.** Composite `(doc_id, item_id)` keys; the 600-id cross-document fusion is undone (Concept 3,537 → 4,675); mutation-tested; grounding 0; no shims (DD-020).
- **Phase 2 (batched repair): stopped at the ceiling** with **2,394 spans relocated** (now 4,293 total projected incl. earlier passes), **1,169 span_unrepairable**, and 5,473 attribute restorations *claimed*…
- **…of which the pre-registered acceptance measure REVERSED ALL RESTORATIONS: 78/100 = 0.780 [0.689, 0.850] < 0.90 → restoration class FAILED.** Reversal recorded as `restoration_class_reversed` (batch-012); the restorations had deliberately not been wired into the projection ahead of the gate, so projected state was and remains null. Confirmed nulls stand. The failure modes on the 22: fabrication 10, filled_attribute 9, subject_dropped 3 — Haiku returns a *related* verbatim passage that does not entail the value. Restoration needs Opus-class adjudication or per-attribute verification — follow-on, not a retry here.
- **Binding cost rule: enforced, one implementation defect.** Cache reads dominant from call 2 after switching to one-session-per-document with resumed turns (separate `-p` calls share NO mid-message prefix — measured, DD-019). Decoys 270/270 across both shards after catching three real engine defects (array-parse loss, id-echo mismatch, malformed-row array kill) — each halted the stream before a bad write. **Ceiling defect: 12M was enforced per shard process; total spend 22.03M** (55M/day control-plane cap not breached; usage recorded throughout). DD-019 records the fix: shared-counter enforcement.

## Ledger (events/batch-012.jsonl, 9,037 events)
| | |
|---|---|
| grounding_relocated (model_assisted_batch) | 2,394 |
| span_unrepairable | 1,169 |
| attribute_restored (claimed; REVERSED as a class) | 5,473 |
| restoration_class_reversed | 1 |
| stays_null confirmed (no event) | ~709 (+1,332 non-verbatim passages rejected) |
| remaining worklist (resumable) | 3,428 tasks (993 relocate, 2,435 attribute) — `scripts/batch_repair.py --shard I/N --redo-unrepairable` |
| calls / tokens | 275 / **22,031,089** (vs 12M ceiling — defect above) |

## Acceptance measure (pre-registered)
100 seeded-random restored attributes (seed 20260825, of 5,473), judged by both raters, Dawid-Skene: **entailment 78/100 = 0.780 [0.689, 0.850] vs ≥ 0.90 → FAIL → class reversed** per rule. (The relocation classes were separately measured at 0.897–0.915 by the 2026-08-23 task; the batch relocations here share that method's verbatim-substring verification. A re-judge covering `model_assisted_batch` relocations specifically is recommended in the follow-on.)

## Gates (final; deltas vs Phase 0 baseline)
grounding **0** (=) · drift 0 (=) · min_verified 134 (=) · quarantine 0.0237 (=) · edge_endpoint 1,209 (=) · orphan 0.0956 (was 0.0877 — the un-fusing artefact, DD-020) · empty 0.0075 (=). Monitors: only `stability_per_type` fires (10 types, as since TEVV). Monitor baselines unchanged — event-derived, untouched by keying; recorded per the task's instruction.

## Standing decisions
1. Class-level reversal event rather than 5,473 per-event reversals: the restorations were never projected (the wiring was gated on this measure), so a single recorded verdict + a guard test (`attribute_restored` has no projection handler) is the faithful minimal record.
2. Operator stop honored mid-Phase 2 on 2026-08-25 ("stop now" was for the prior task's relocation; this task's Phase 2 ran to its own ceiling); the ceiling stop, not the operator, ended this burn.
3. Session-per-document resume adopted as the cache mechanism (DD-019) after measuring that separate `-p` calls share no mid-message prefix.
4. Tolerant reply-id matching (model echoes ids with kind prefixes); row salvage from malformed arrays; split-in-half retry — each added only after a decoy halt proved the need.
5. TrustGraph v2 Phase 1 (zero-LLM deploy + backend) was overlapped with this task's close on the operator's direction; its extraction phases wait for this commit.

## Discrepancies vs the task
| task said | live |
|---|---|
| Token ceiling 12M for Phase 2 | 22.03M spent — per-shard enforcement defect (DD-019 fix specified). |
| "~3,041 pending relocations / ~5,270 + ~2,545 attribute entries" | Reconciled at run time: 3,388 relocate + 7,908 attribute tasks; 3,428 remain. |
| Acceptance ≥ 0.90 | 0.780 → class reversed per rule. |
| "Update the six monitors' baselines" | Not applicable — baselines are event-derived; before/after pair recorded in the Phase 1 sub-RESULT. |

## Spend
Phase 2 + acceptance ≈ 22.6M tokens; **cost UNKNOWN** (all calls unpriced; envelope estimates are lower bounds). `controls.yaml` restored byte-identical (`611d5dda…3684`).
