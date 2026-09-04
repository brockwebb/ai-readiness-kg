# ADDENDUM-01 to `2026-09-04_result_migration_completion.md`

**Date:** 2026-09-04
**Authored by:** Desktop session
**Status:** AMENDS the base task.
**Reason:** Upstream seldon RESULT (`2026-09-04_ad028_grammar_amendment_migrate_atomic_RESULT.md`) landed as `e5beffb` with three facts the base task did not anticipate.

**Immutable once written.**

---

## 0. Preconditions — amended

- Replace precondition 2 (the `register --name G1_Test_Name` grammar probe) with: the upstream RESULT §2 reports the ai-readiness-kg dry run at `refused: 0`, exit 0, with `migrated 953 / name_set_units_pending 2576 / units_is_real_unit 23 / ambiguous 40`. Re-run that dry run here as step 2 and require the same counts; that is the grammar check.
- `--partial` now exits non-zero even when valid rows are written (upstream §2). The base task's Step 3 runs without `--partial`, so exit 0 means everything migrated and non-zero means nothing was written. Assert exactly that.
- Git guard: `seldon cc register` / `cc complete` and their MCP twins now refuse untracked files without `--allow-untracked`. This task file and its addendum were registered before the guard landed. First action: `git add` and commit both files with message `cc task: result migration completion (registered e1a18ca0)` so `cc complete` at the end is not refused.

## 1. New step 0.5 — ontology sync

Before Step 1: `seldon ontology sync` from this project dir. This replica is at epoch 3 and carries two junk terms as `active` (definition literally `leibniz-pi`); master is at epoch 4 with them deprecated and 5 related terms corrected. Expected: `0 new, 5 updated, 2 deprecated`, `_OntologyReplicaMeta.last_epoch` 3 → 4. Report before/after. Nothing else in this task depends on it; it is here because the replica is wrong and the fix is one command.

## 2. Step 2 — ambiguous rows

Upstream RESULT §2 calls the 40 `ambiguous` rows "a uniqueness question for a human". Overridden: the base task's deterministic rule (`slug(units)__<artifact_id[:8]>`) stands, on the evidence that none of the 63 rows is cited by any token (RESULT-01 §3.6, RESULT-02 §1). The `--report` JSONL is the input; write the 63 assignments as a plan file and apply through whatever per-row path `migrate-names` exposes, or the `artifact_updated` shape it emits. Report which.

## 3. Verification trap

Upstream §6.6: the `seldon` console script resolves to the main checkout, not a worktree. This project is not a worktree, but if any step runs seldon from a different checkout, force the module path and record the code SHA (`e5beffb` or later) in the RESULT.
