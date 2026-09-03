# CC Task: Post-burn reconciliation — errata for two RESULT arithmetic errors, corpus count after G1 admission, Result registration, projection rebuild at burn close, DD-032

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_post_burn_reconciliation_ADDENDUM*.md` files.**

## Context

Four tasks ran concurrently on 2026-09-02 and their RESULTs disagree with each other and with their own tables. RESULTs are immutable, so corrections are errata files plus registered Result artifacts, never edits.

## Findings driving this task

**F1 — two RESULTs carry a pooled-F denominator that their own tables contradict.**
`cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md` §21.6 states 37/1,474 over "fourteen judged batches, 13 accept, 1 sampling_inconclusive". `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md` §2.4 repeats 37/1,474 "as §21.6 states" — but its own 15-row table sums to **1,480** facts over the 14 batches that were judged, with **14** accepts; b010 was never judged (33 items < 55 minimum), so it is the fifteenth batch, not one of the fourteen judged. `cc_tasks/2026-09-02_deck_numbers_post_burn_RESULT.md` §2 recomputed from `state/bulk_v038_burn.json` and got 37/1,480 = 0.0250 [0.0182, 0.0343], 14 accept / 1 sampling_inconclusive, and correctly reported the disagreement without reconciling. The 6-fact / one-accept discrepancy in §21.6 is a transcription error propagated once. The measured value stands.

**F2 — slide 15 is already stale by 17 documents.** The deck task measured 194 admitted before `2026-09-02_g1_eval_prior_art` admitted 17 (batch-025, epoch `g1eval-2026-09-02`, 194 → 211). Concurrency, not error.

**F3 — nothing rebuilds the Neo4j projection when a burn closes.** The deck task found the graph held zero `bulk-v038` nodes until it ran `build_projection.py` itself. The burn's own close step should do this, or the close is not a close.

**F4 — DD-022's settlement rule was amended in behaviour (empty_failure releases) with no DD entry** (spend-guard RESULT §4).

**F5 — crosswalk demand unit total moved 41 → 43** (`state/t2_priority.json` regenerated 2026-09-02 02:30); the meeting brief's demand-ledger paragraph still says 41 / 31 of 41 / 159 deferred (deck RESULT §3 items 2–3).

## Steps

### 1. Errata files (new files; the RESULTs are not edited)

- `cc_tasks/2026-08-30_bulk_extraction_v038_ERRATUM-01.md`: §21.6 pooled-F denominator and accept count. State the wrong values, the measured values with their derivation (sum of `batches[*].facts` and `fabrications` in `state/bulk_v038_burn.json`, batch-by-batch as in the deck RESULT), and the corrected sentence. Recompute the Wilson interval yourself; do not copy the deck RESULT's.
- `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_ERRATUM-01.md`: §2.4's closing sentence copied §21.6 instead of summing its own table. State that and give the sum. The 15/15 reconstruction match is unaffected.

### 2. Register the burn's headline numbers as Seldon Result artifacts

`seldon result register` for each, with the derivation command in the description and `generated_by` the state file / query:
- pooled fabrication share F (value, Wilson 95% lower/upper as separate results, n = 1,480, fabrications = 37)
- batch tally (accept 14, sampling_inconclusive 1, reject 0, quarantine 0, judged 14, total 15)
- documents admitted after G1 admission (211) and extracted under v038 (35)
- live-graph v038 node and edge counts (10,305 / 11,914) and whole-graph KG-label counts (18,844 non-Document + 194 → recount Document nodes after step 4; 22,141 edges → recount)
- crosswalk demand units (43 of 43 over 35 docs)

Link each to `2026-09-02_deck_numbers_post_burn_RESULT.md` as evidence. Verify with `seldon result list`. These are the numbers any future deck, brief, or paper section resolves to.

### 3. Slide 15 and the brief

- `docs/crosswalk/deck_content_2026-09-01.md` slide 15: documents admitted 194 → 211, with a clause that 17 are G1-EVAL prior-art sources admitted 2026-09-02 and not yet extracted (so extracted 35 of 211, not of 194). Any other number in slide 15 that step 2 changed. Bump v4 → v5 with a one-line note. Rebuild to `docs/crosswalk/framework_deck_2026-09-02.pptx` (overwrite; same date, same day) and confirm slide 15 matches.
- `docs/crosswalk/meeting_brief_2026-09-01.md`: replace the stale demand-ledger paragraph values (41 → 43 units; 31-of-41 in-flight figure → 43 of 43; 159 deferred → current queue) and the admitted count. Nothing else.

### 4. Projection rebuild at burn close

Find the burn driver's close path (`scripts/run_chunked_bulk.py` after the last batch verdict is written, and/or the launchd wrapper `scripts/jobs/airkg_extraction_burn.sh`). Add a projection replay (`scripts/build_projection.py`) as the final step of a completed burn, gated on `NEO4J_*` being reachable; on unreachable Neo4j, write a `projection_stale` marker file under `state/` and print it, do not fail the burn. Add a check to `scripts/run_baseline_gates.py` or to the existing verify path that reads the newest `corpus_epoch` in the event log and refuses to report gate results when the projection does not contain it. Test with a fixture, no live Neo4j in tests. Then run `build_projection.py` once more now so Document count reflects the 17 G1 admissions, and recount for step 2.

### 5. DD-032

Append to `docs/design_decisions.md` (append-only, dated): DD-032 — `claude -p` outcome classes; `empty_failure` (non-zero exit, no stdout, no stderr) releases the reservation and backs off under `controls.yaml spend.empty_failure_*`, settling at the estimate only after the retry cap; `error_with_output` keeps DD-022's settle-at-estimate rule; the burn state file merges by batch id with immutable verdicts (`verdict_conflict` logged). Cite the 2026-09-01 03:01Z incident and `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md` §1.2 as the evidence that empty failures consumed nothing server-side.

### 6. Verify

`python -m pytest tests/ -q` count before/after; `seldon verify` clean.

## Constraints

Zero model calls. No edits to any `*_RESULT.md`, the burn state file, ledger, manifest, or event shards (other than what `build_projection.py` reads). No extraction of the 17 G1 documents.

## Completion

RESULT at `cc_tasks/2026-09-02_post_burn_reconciliation_RESULT.md` listing the Result artifact ids; `seldon cc complete`; commit and push.
