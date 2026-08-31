# ADDENDUM-01 — 2026-08-30_bulk_extraction_v038.md

**Date:** 2026-08-31. **Immutable once written.** Base file and the 2026-08-31 RESULT govern except where this addendum resolves the §5 stop. On conflict, this addendum wins. Append to the existing RESULT.

## 1. The §5 stop is resolved at admission, not in the template

The RESULT's handoff line (strip the section, re-pin, restart) is REJECTED for a reason the base task itself supplies: Phase A qualified template sha `0c6fee1d…` as sent. An edited template is a different artifact; running it on Phase A's qualification is the DD-028 defect one layer up — a qualification instrument that measured something other than the thing burning. Re-qualifying a stripped template would cost ~4.3M tokens to remove an instruction whose output we can refuse for free.

**Instead: DD-024 is enforced at its own stated boundary — graph entry.**

1. Admission refuses the five semantic-edge types (`has_component`/`subtype_of`/`consumes`/`extends`/`implements`) for any event whose profile's purpose is bulk extraction. Refusal emits a reason event (`semantic_edge_refused`, doc/chunk/type/span recorded) — an event, never silence. Demand-pull adjudication (DD-024's sanctioned path) is unaffected: the refusal keys on the emitting profile class, not the edge type globally.
2. Belt and suspenders: `build_projection` gains the blanket exclusion the RESULT found missing — semantic-edge types from bulk-profile extractions do not project even if an admission guard is bypassed. Two independent layers because §5.1 showed a single missing rule lets 190 forbidden edges through.
3. The 5 existing Phase A edges: emit `extraction_superseded` overlays naming the `semantic_edges` stratum for the emitting extractions (the mechanism §5.1 says exists). Events stay on the log; projection drops them. Verify by scoped read: semantic-edge count from batch-023 in projection = 0.
4. The template is NOT edited. The pin holds. Template hygiene (stripping the dead section) belongs to the next template revision, which bundles its own re-qualification; note it in that revision's task when it exists.

**Mutations before Phase C (extends the base task's matrix, same discipline):** (a) a seeded bulk-profile semantic-edge event is refused at admission and the reason event appears; (b) a mutated admission guard that lets it through is caught by the projection exclusion; (c) after overlays, the 5 known edges are absent from projection while their log events remain; (d) drive the admission entry point, not a committed fixture (M85/M86 class, seventh instance is not wanted).

## 2. Epoch declaration for the crosswalk lane (bit this run twice; will bite Phase C)

Phase 0 of the restart: declare a `corpus_epoch` for the 5 `corpus/crosswalk/` documents in the dixie evidence ledger (`crosswalk-2026-08-29` already exists as a declared epoch name on the event shards — reconcile with whoever's convention that was; if it covers these 5, bind them to it, else declare `crosswalk-lane-2026-08-31`). The `canonical_path` fallback stays as defense, but resolution should stop needing it.

## 3. Phase C amendments (mechanics only; gates, SPRT parameters, stop rules unchanged)

1. **Chunk-level resume.** The worklist derivation excludes chunks already extracted under `bulk_v038` (Phase A's 30 are in the graph; the RESULT's `extracted=1` shows doc-level completion already projects). No chunk runs twice under the same profile; the resume check reads the ledger, not a file.
2. **Multi-day schedule.** 55.8M measured demand vs 55.0M daily band: batches dispatch across days, each under its own declared ceiling per the base formula (1.3 × running mean × batch chunk count). No single-run ceiling covers Phase C and none is declared. The daily band is the control plane's; it does not move for this burn.
3. **`agency_framework` yield band.** The ±3 sd band (−30 to +58) is unusable (§3.3). All strata switch to the same report-only convention: flag a batch whose per-stratum mean falls outside Phase A's observed min–max envelope, labeled explicitly as decoration at n=7–8. The operative monitor is and remains the faithfulness SPRT; yield flags gate nothing (ADDENDUM-06 §2 unchanged).
4. **Zero-yield chunks are healthy** (bibliographies, navigation, front matter — §3.3 finding 2). A zero-chunk is not an anomaly signal and appears in no flag logic.

## 4. Out of scope, restated

The 2 unconvertible documents (T0/T1 substrate, separate task); the 3 inert test-written events on the tagged shard (no-delete governs); any change to p0/p1/α/β, the pooled gate, or the corpus stop rule; template edits of any kind.

## 5. Completion

Phase C runs to the base task's deliverables. `seldon cc complete` fires only when the burn finishes or the corpus stop rule fires — a stop-rule stop completes the task WITH an incident-class report (that is the design working, per DD-029). RESULT appends to the existing file; end with `kg queue status` totals and the full-burn ledger reconciliation.
