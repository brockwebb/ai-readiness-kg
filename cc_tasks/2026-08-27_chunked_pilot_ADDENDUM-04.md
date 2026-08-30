# ADDENDUM-04 to 2026-08-27_chunked_pilot.md — Arm A3 (character-exact restoration) and §3 closure rule

**Date:** 2026-08-30. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-27_chunked_pilot_ADDENDUM*.md` (four including this one) and the parent. `seldon cc complete` on the parent only at §3 closure per this addendum's terms.
**Result:** append to `cc_tasks/2026-08-27_chunked_pilot_RESULT.md`.

## 0. Standing

A2 (v0.3.8): faithfulness PASS (F_upper 0.0243, item-faithful 0.986), yield FAIL (24.30/chunk = 0.537 < 0.60 floor). Isolation clean: proposals 0.96×, admissions 1.55×, span_partial 0.36×. Naming diagnosis confirmed by mechanism; the 0.90 recall floor reported as pre-registered and discounted as underpowered (resolving power one entity).

Largest remaining quarantine class: `anchor_not_located` 340, split at last measurement 52% not-found / 37% non-unique / 11% over budget.

## 1. Arm A3 — single variable

New template: the character-exact elaboration (the whole-doc v0.3.5 rule text, adapted to the anchor contract so it binds the **anchor**: the anchor must be copied character-exact from the chunk) restored on top of v0.3.8. Nothing else changes. New sha, profile `v0_3_9`, own shard and raw dir. Same 44 shared chunks via `--shared-with chunked_v035`. Ceiling derived from A2 actuals (8,030 output tok/chunk basis), declared before dispatch.

## 2. Pre-registered before A3 runs

Written to the RESULT before any A3 output exists:

1. **Prediction:** proposals flat (±10%); movement confined to `anchor_not_located`, specifically its not-found and over-budget subclasses. Non-unique is expected residual — it is a property of the chunk text, and no compliance instruction reaches it. Report the subclass split for A2 and A3.
2. **Secondary prediction:** A2's single unfaithful item was `filled_attribute`; verbatim discipline should suppress that class. F not worsening at higher yield is the contract's three-arm story.
3. **Floor unchanged: 0.60 raw admitted/chunk against 45.23.** Arithmetic headroom note: converting not-found + over-budget (~63% of 340 ≈ 214 items) projects admission ≈ 0.73, yield ≈ 29/chunk — above floor with margin. 
4. **Closure rule (terminal, no A4):**
   - **A3 ≥ 0.60:** floor met on original terms. §3 closes: verdict = chunked v0.3.9 PASS on all pre-registered criteria; Arm B not run, recorded as a decision (no capability question remains open); bulk extraction decision unblocked, ordered by `state/t2_priority.json`. `seldon cc complete` the parent.
   - **A3 < 0.60:** §3 closes UNDER-EXTRACTION with the diagnosis chain recorded. The floor's target (45.23 from an arm proposing one item per 34 tokens, never validated as correct extraction) becomes the suspect. Next step is pre-registered as ground-truth annotation: 5 chunks, operator rubric (operator value input — flagged, not designed here), floor re-derived from measured value. **No further arm, including B, runs before that re-derivation.** `seldon cc complete` the parent; the annotation step is a new task, not this one.

## 3. Report

Same table as A2 (proposed/admitted/rates/output tokens, Arm A2 vs A3), quarantine subclass split, faithfulness gate conditioned on density, cost per admitted item, ledger settlement. Register Results for the gate numbers.

## 4. Out of scope

Arm B; any bulk extraction; template edits to any pinned file; the ground-truth rubric's content (operator input); T0/T1.
