# CC Task — T2 bulk extraction under v0_3_8: stratified confirmation, then monitored burn

**Date:** 2026-08-30. **Repo:** /Users/brock/GitHub/ai-readiness-kg. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-30_bulk_extraction_v038_ADDENDUM*.md`; read `cc_tasks/2026-08-30_ground_truth_yield_floor_RESULT.md`, `cc_tasks/2026-08-27_chunked_pilot_ADDENDUM-06.md`, and the §3 closure in the chunked-pilot RESULT.
**Result:** `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md`; `seldon cc complete` this file; commit, push.
**DISPATCH GATE:** this task does not start until `cc_tasks/2026-08-27_extraction_queue_RESULT.md` exists — worklists are ledger-derived via `kg queue` (no ad-hoc lists), and the queue build supplies that surface. If dispatched early, STOP at Phase 0 and report.

## Prior art (DD-025 block)

**External.** Lot acceptance sampling by attributes: Dodge & Romig (1959), LTPD/AOQL plans; Wald (1945) SPRT for sequential accept/reject with declared α/β and expected sample number; Dodge (1943) CSP-1 continuous sampling for in-stream inspection; Shewhart control bands for report-only process monitoring. Sequential plans are chosen over fixed-n per ADDENDUM-06 §0.
**Internal.** Wintermute G4 (bulk extraction without measurement is how a layer dies); DD-019 (batch dispatch, cached-session prefix, decoys); DD-022 (reserve-then-settle, declared ceilings, one ledger); DD-023 (chunk unit, anchor contract); DD-024 (no bulk semantic edges — unchanged by anything here); DD-026 (preconditions derived from thresholds — applied below to the SPRT's minimum batch sample); 35094dc4 RESULT (floor incommensurability; v0_3_8 selected; floor 5.16 with its limitations ON the verdict); six recorded instances of tests measuring artifacts instead of generators — every monitor here is mutation-verified before live use (methodology §7.5) and fixtures are real corpus lines driving production entry points.

## Binding facts from the re-derivation (do not re-litigate)

- Production profile: **v0_3_8** (Arm A2). Pin it (`run_profiles`, sha recorded) at Phase 0. The queue projection reads the pin (queue ADDENDUM-01 §4).
- The 5.16 node-floor is **qualification evidence only**. It is n=5, reference-heavy (29% below its comparator's average), effectively n=2 informative. It licenses starting; it is NOT a burn-time quality bar and appears in no gate below. Burn-time yield monitoring uses Phase A per-stratum bands instead.
- All gates in this task state their **unit** explicitly (node items vs edges vs facts) and name the instrument that measures that unit. A gate whose unit its instrument cannot measure is the 45.23 defect; refuse at registration (extends DD-026; recorded as DD-029 below).
- Semantic edges: none, ever, under this task (DD-024). The `cites` layer runs as part of v0_3_8's normal emission; its defect count is reported per batch (A2 baseline: 5 defects / 44 chunks).

## Phase 0 — preconditions (no model calls)

1. Queue RESULT exists; `kg queue status` reconciles against manifest (194 included at authoring; derive live).
2. Pin v0_3_8; sha in RESULT.
3. **Extract/defer cut** from `state/t2_priority.json` (label "final"): extract iff `crosswalk_demand >= 1` OR `t0_centrality > 0`. All others: `kg queue` deferral events, `reason: no consumer` — admitted, not extracted, visible on the status surface. Report cut sizes (extract / defer) in RESULT before any spend.
4. Worklist = `kg queue` derivation over the extract set, ordered by `t2_priority.json` ordering, emitted as `extraction_request` events. No document runs that is not on the ledger.
5. Declare Phase A ceiling on the ledger: `--ceiling-tokens 4000000`.

## Phase A — stratified corpus confirmation (ADDENDUM-06 §1–§2, inherited verbatim)

30 chunks, seeded deterministic draw (seed recorded, script committed before the run), from documents **never used by any arm**, stratified by manifest `source_type` collapsed to {statute/regulatory}, {agency/framework report}, {academic/preprint}, 10 chunks each, no two chunks from one document within a stratum where the stratum has ≥ 10 documents. Existing T1 store; no re-conversion.

Extract under pinned v0_3_8. Judge under the standing probe protocol (decompose 1.1.0, probe_judge 1.1.0, two raters, Dawid-Skene), randomized order, batch per DD-019.

**Gate (pooled only): F_upper < 0.10 AND item-faithful ≥ 0.70.** Unit: atomic facts of admitted node items; instrument: the standing probe. Precondition per DD-026: pooled n ≥ 35 facts (arithmetic minimum for F_upper < 0.10 under Wilson with zero events); 30 chunks at A2's admitted rate clears this by an order of magnitude — if it somehow doesn't, GATE UNREACHABLE is the recorded outcome, not a judged FAIL. Per-stratum: reported, never gated (10 chunks cannot power a stratum verdict; say so).
**Yield: admitted node items/chunk per stratum, report only.** These means and spreads become the Phase C monitoring bands. No floor verdict (the 45.23 comparator does not exist off the pilot documents and will not be manufactured; the 5.16 floor is out of scope here by the binding facts above).

**Phase A FAIL → STOP.** Report; no burn; no parameter tuning to make it pass. A FAIL here means qualification did not generalize off the pilot documents — that is a finding, and the next move is a design cycle, not this task.

## Phase B — sequential plan instantiation (no model calls; parameters computed, not chosen)

Written down here, before Phase A data, so Phase A cannot tune it:

- Per document-batch (batch = the DD-019 dispatch unit's documents, target 40 chunks of output minimum for sampling), draw a seeded random sample of admitted node items, decompose to facts, judge under the standing protocol.
- **SPRT on the batch fabrication rate:** H0 p0 = 0.05 (acceptable), H1 p1 = 0.10 (rejectable — the standing gate), α = β = 0.05. Boundaries are Wald's log-likelihood lines; both computed constants go in the RESULT. Minimum facts before a decision is possible: derived from the boundaries at zero events, stated arithmetically in the RESULT (DD-026).
- **Accept** → batch events project normally. **Reject** → batch's shard quarantined (tagged, excluded from projection by the standing purpose-flag mechanism), burn continues. **Continue** past the batch's sample budget (2× expected sample number) → treated as accept-with-flag, batch marked `sampling_inconclusive`, counted toward the consecutive rule.
- **Corpus stop rule:** 2 consecutive rejects, or 3 rejects/inconclusives in any rolling 5 batches → STOP the burn, incident-class report. This is the one operator touchpoint.
- **Yield bands (report-only):** per-stratum admitted/chunk vs Phase A mean; a batch outside ±3× Phase A stratum SD is flagged for the RESULT, never gates. Yield heterogeneity is a finding (ADDENDUM-06 §2), not a defect.
- What Phase A informs: per-stratum expected yields (band centers) and the batch sample size needed to reach the SPRT minimum. Nothing else. p0/p1/α/β are fixed above and do not move on Phase A data.

**Mutation matrix before any Phase C call:** seeded known-bad batches must (a) cross the reject boundary, (b) fire the consecutive-batch stop, (c) quarantine the shard out of projection, (d) prove the sampler reads the draw, not a committed file (the M85/M86 class — sixth instance; drive `phase_sample` style entry points with stubbed shards). All mutations restored; results in RESULT.

## Phase C — the burn

- Batches dispatch per DD-019 (headless session per document, resumed turns, cache-read ratio checked on first 3 calls, decoys per batch).
- **Spend:** each batch run declares its own ceiling on the ledger: `1.3 × (running mean settled tokens/chunk for v0_3_8 from the ledger's last 10 measured settles; bootstrap from Phase A's mean) × batch chunk count`, computed and reported at declaration. Daily band in `controls.yaml` binds globally (DD-022). No batch dispatches without its declared number.
- Order: worklist order from Phase 0. Failures carry status per the queue projection; `rate_limited`/transient get the standing retry; `parse_failed` classes quarantine per the anchor-contract parser.
- Progress is readable at any moment from `kg queue status` — that is the point of the dispatch gate.

## Out of scope

Semantic-edge extraction (DD-024); template or profile edits (a profile defect mid-burn = STOP + report, new task); the deferred no-consumer documents; dedup; serving layer; changes to p0/p1/α/β after this file is committed; anything that would touch the 5.16 floor as if it were a gate.

## Deliverables

- [ ] Phase 0 report: pin sha, cut sizes, worklist size, ledger declarations
- [ ] Phase A: confirmation gate verdict (pooled), per-stratum report, yield bands
- [ ] Phase B: SPRT constants + minimum-n derivation; mutation matrix all killed
- [ ] Phase C: per-batch ledger (accept/reject/inconclusive), quarantined shards listed, spend reconciled
- [ ] DD-028: yield-floor commensurability rule (a gate's unit must be measurable by its validating instrument; cites 35094dc4 RESULT) — verify DD-027 is taken by the queue task first; take the next free numbers and state which
- [ ] DD-029: this burn design (acceptance-sampling parameters, stop rules, what Phase A may and may not inform)
- [ ] tests green; suite count reported; commit; push; `seldon cc complete`; RESULT ends with `kg queue status` totals
