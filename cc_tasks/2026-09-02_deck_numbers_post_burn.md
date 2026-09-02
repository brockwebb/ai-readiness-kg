# CC Task: Replace the deck's floor numbers with measured post-burn counts; correct the acceptance-sampling claim

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_deck_numbers_post_burn_ADDENDUM*.md` files.**

## Context

The v038 burn closed 2026-09-02 (`cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md` §21.6): 41/41 crosswalk demand units, 14 judged batches, 13 accept, 1 `sampling_inconclusive` (b010), 0 rejects. The deck (`docs/crosswalk/deck_content_2026-09-01.md`, slide 15) and the meeting brief (`docs/crosswalk/meeting_brief_2026-09-01.md`) still carry floors read while the burn was in flight, and slide 15 contains a sentence that is now false as written.

## Steps

### 1. Measure, do not transcribe

Derive every number from the live graph and the event log, not from the RESULT prose. Record the derivation (query or command, and the value) in the RESULT so the next reader can re-run it.

- Documents admitted (manifest): `python -m kg.manifest verify` / manifest projection count.
- Documents extracted under v038: `kg queue status` (extracted / deferred / skipped_oversize / stale).
- Node and edge counts admitted to the graph: Neo4j `seldon-ai-readiness-kg`, KG-schema labels only (the labels `build_projection.py` owns); state the label set you counted.
- Pooled fabrication F over the full burn with its Wilson 95% interval and n: from `state/bulk_v038_burn.json`, recomputed, not copied. If your recomputation disagrees with §21.6 (0.0251 [0.0183, 0.0344], 37/1,474), report both; do not reconcile.
- Batch verdict tally (accept / sampling_inconclusive / reject / quarantine).
- Group D evidence count (the "zero evidence documents" claim on slide 15): recount from the crosswalk skeleton's Criterion D rows. If it is no longer zero, the slide's finding changes and the RESULT says so.

### 2. Edit slide 15 in `deck_content_2026-09-01.md`

- Replace `194 documents admitted` and `31 docs, ~4,800 nodes at last read — a floor, burn in flight` with the measured values. Drop the floor language.
- The sentence `every batch passed acceptance sampling before entering` is false: b010 is `sampling_inconclusive` (unsatisfiable minimum-n, §20.3). Rewrite to state the actual tally and what `sampling_inconclusive` means in one clause. Do not soften it into a pass.
- Every number on the slide keeps its interval or its n (the slide's own rule).
- Update the header `**Numbers:**` line: source is now the measurement in this task's RESULT; remove "floors — burn was in flight".
- Bump the content version in the header (v3 → v4) with a one-line note.

### 3. Meeting brief

Apply the same corrections to `docs/crosswalk/meeting_brief_2026-09-01.md` wherever the same floors or the acceptance-sampling claim appear. Nothing else in the brief changes.

### 4. Rebuild the deck

`python scripts/build_framework_deck.py` → `docs/crosswalk/framework_deck_2026-09-02.pptx` (new dated file; leave the 09-01 pptx in place). Confirm 18 slides and that slide 15 text matches the content file.

### 5. Verify

`seldon verify` clean. Root test suite unchanged.

## Constraints

Zero model calls. Do not touch the burn state file, ledger, manifest, event log, or `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md`. No edits to any slide other than 15 and the header block, unless a measured number contradicts another slide, in which case list the contradiction in the RESULT and do not edit.

## Completion

RESULT at `cc_tasks/2026-09-02_deck_numbers_post_burn_RESULT.md` with the derivation table (quantity, source, command/query, value); `seldon cc complete`; commit and push.
