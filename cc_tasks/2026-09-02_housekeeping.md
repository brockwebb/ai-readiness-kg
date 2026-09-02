# CC Task: Housekeeping — A9 table placement, snapshot flags, verify clean

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_housekeeping_ADDENDUM*.md` files.**
**SEQUENCING: step 2 requires the Seldon change in `seldon/cc_tasks/2026-09-02_snapshot_artifacts_verify.md` to have landed (its RESULT gives the CLI invocation). If it has not, do step 1 and step 3 only, skip step 2, and say so in the RESULT.**

## Steps

### 1. A9 into the §2 table

`docs/crosswalk/usafacts_operationalization_skeleton.md`: A9 (M2M agent surface) currently lives in §1b as its own one-row "Added indicator" table, so §2 reads A1–A8, A10, A11. Move the A9 row into the §2 Criterion A table between A8 and A10, verbatim, formatting matched to the §2 header (`Evidence (doc_id)` column). Replace the §1b one-row table with a single sentence pointing at A9 in §2. No ID changes, no content changes. Because A9 is the agent-surface indicator, confirm its Status/notes cell carries the frontier dating the assessment protocol §4 requires (`frontier_deep track, as_of 2026-01`); if it does not, add exactly that phrase and record it in the RESULT as the one content change.

### 2. Snapshot flags

Set `snapshot` on the three snapshot artifacts identified in `cc_tasks/2026-09-01_machine_diagnostic_stub_RESULT.md` §3: `kg-schema-v0.1`, `corpus-manifest`, `corpus-manifest-round2`. Use the invocation from the Seldon RESULT. Do not run `verify --fix`.

### 3. Verify

Run `seldon verify`. Expected after step 2: file-hash check clean, snapshot line informational. If anything else fails, characterize it in the RESULT; do not fix outside this task's scope.

## Constraints

Zero model calls. Do not touch the burn, ledger, manifest, or event log.

## Completion

RESULT at `cc_tasks/2026-09-02_housekeeping_RESULT.md`; `seldon cc complete`; commit and push.
