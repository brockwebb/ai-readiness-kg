# ADDENDUM-06 to 2026-08-27_chunked_pilot.md — confirmation set stratified corpus-wide; acceptance sampling carried to bulk

**Date:** 2026-08-30. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-27_chunked_pilot_ADDENDUM*.md` (six including this one). This addendum supersedes ADDENDUM-05 §1.1 (set construction) and §1.3 (yield reporting) and adds a carried requirement. Everything else in -05 stands.
**Result:** append to `cc_tasks/2026-08-27_chunked_pilot_RESULT.md`.

## 0. Rationale (recorded before A3's number is known)

ADDENDUM-05's held-out set drew from the pilot documents, which patches evaluation adaptivity but not representativeness: 44 chunks from 2 documents is a cluster sample with effective n closer to the document count than the chunk count (design effect; Kish). A corpus-level qualification claim needs held-out chunks from held-out documents, stratified by document class. Separately, no qualification sample licenses an unmonitored corpus burn — production requires sequential acceptance sampling (Dodge–Romig; Wald SPRT).

## 1. Supersedes -05 §1.1 — confirmation set construction

30 chunks, seeded deterministic sample (seed recorded, script committed before the run), drawn from documents **never used by any arm** (excludes all 5 pilot documents), stratified by document class using manifest `source_type` collapsed to three strata — {statute/regulatory}, {agency/framework report}, {academic/preprint} — 10 chunks each, no two chunks from the same document within a stratum where the stratum has ≥ 10 documents. Chunks come from the existing T1 store; no re-conversion.

## 2. Supersedes -05 §1.3 — reporting on the confirmation set

Faithfulness gate at standing thresholds (F_upper < 0.10, item-faithful ≥ 0.70), pooled and per-stratum (per-stratum is reported, not gated — 10 chunks per stratum cannot power a stratum verdict; say so rather than fake one). Yield: admitted/chunk reported per stratum with no floor verdict — the 45.23 comparator does not exist off the pilot documents and will not be manufactured. Yield heterogeneity across strata is a finding that feeds the bulk task's monitoring design, not a pass/fail.

## 3. Carried requirement — the bulk task may not be written without this

Bulk extraction, when unblocked, MUST include burn-time acceptance sampling: per document-batch, a seeded random sample of admitted facts is judged under the standing protocol against pre-registered accept / continue / stop-and-quarantine-batch rules (sequential plan, parameters set in the bulk task before dispatch, informed by the confirmation run's per-stratum results). A batch whose sample fails quarantines that batch's output — it does not stop the burn corpus-wide unless consecutive-batch rules fire. One-time qualification licenses starting the burn, never finishing it unmonitored.

## 4. Out of scope

Everything listed in -05 §3; changes to the closure rule branches; the sequential plan's parameters (bulk task's job).
