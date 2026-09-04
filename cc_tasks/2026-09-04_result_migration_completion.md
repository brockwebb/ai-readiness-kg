# CC Task — Complete the Result name migration, retire units-matching, close G1 provenance

**Date:** 2026-09-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Continues:** `2026-09-03_hygiene_sweep_post_g1_freeze.md` Lane 1 (stopped at step 4, RESULT-02 §1)
**Spend:** zero model spend.
**SEQUENCING:** Runs AFTER `seldon/cc_tasks/2026-09-04_ad028_grammar_amendment_migrate_atomic.md` has a RESULT. Step 0 gates on it.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. Preconditions (stop if any fails; probe with `${=c}`-style word splitting or one command per line, not an unquoted loop variable — RESULT-01 §0)

- `seldon result migrate-names --help` shows `--partial` and `--report`.
- `seldon result register --name G1_Test_Name` is accepted by the grammar in a `--dry-run` or against a scratch check (do not register anything; use whatever validation-only path the seldon RESULT names).
- Read seldon RESULT for `2026-09-04_ad028_grammar_amendment_migrate_atomic`.

## 1. Order of operations (sequential, one session; `seldon_events.jsonl` is a single append-only writer — RESULT-02 §6)

### Step 1 — Shim first, while `units` still resolves
Replace the body of `scripts/g1_resolve_results.py` with a shim over seldon's resolver library function (import path per `seldon/paper/build.py`; call with `allow_proposed=True`). Preserve the script's full CLI surface — grep every caller (`build_framework_deck.py` `--render`, any `--check` use in scripts, docs, launchd jobs) and keep each invocation form working. Preserve the placeholder exclusion: `{{result:<NAME>:value}}` must remain unmatched (angle brackets illegal). If seldon's resolver matches it, register a seldon ResearchTask and add the exclusion in the shim's pre-filter; report.

Regression A: capture resolver output for the 4 substantive documents (memo, `design_decisions.md`, deck draft, skeleton) and the `cc_tasks/*.md` prose carriers with the OLD script (from git) and the shim. Zero diffs required; the seldon resolver's transitional units-fallback (SI-09) carries the not-yet-named rows, and its per-token warnings are expected at this step — record the warning count.

### Step 2 — Migration plan
`seldon result migrate-names --dry-run --report cc_tasks/2026-09-04_migrate_plan.jsonl`. Expected classes: `name_set_units_pending` ≈ 2576, `migrated` ≈ 953, `units_is_real_unit` 23, `ambiguous` 40, `refused` 0. Any `refused` > 0 → stop, report the rows, do not run live.

For the 63 `units_is_real_unit` + `ambiguous` rows apply ADDENDUM-01 §1's rule, `name := slug(units) + "__" + artifact_id[:8]`, via whatever per-row assignment path the command offers (`--assign`, a plan-file input, or the `artifact_updated` event shape it emits — report which). These rows are uncited (RESULT-01 §3.6, RESULT-02 §1); `units` stays on the 23 real-unit rows.

### Step 3 — Live migration, no `--partial`
Run live. Expect 3529 named + 3529 `units` cleared (or the 63-row variant above). Exit non-zero with nothing written is an acceptable outcome that ends this task with a report; a partial write is not.

### Step 4 — Regression B
Rerun the shim over the same file set; diff against Step 1's captures. Zero diffs required. SI-09 warning count must now be 0 — every token resolves by `name`. If > 0, list the tokens; those are names the migration missed and the task stops here with the list.

### Step 5 — Retire the fallback dependency
With warnings at 0, record in `docs/design_decisions.md` (append, dated, DD-next) that this project no longer depends on SI-09 and that the seldon fallback can be removed upstream without effect here. Register a seldon ResearchTask: "remove SI-09 units fallback once all projects report zero fallback resolutions" with this project's evidence line.

### Step 6 — G1 instrument provenance (RESULT-02 §1 step 6 finding)
Register three DataFiles: the G1 fixture YAML, the schedule TOML, the spend ledger (exact paths from `scripts/register_g1_instrument_results.py`; if the ledger is regenerated, mark `snapshot: true` per AD-027). Amend the registration script to cite them (`--data-name`) for future runs; backfill the 29 `g1_v2_instrument_*` Results with `seldon result backfill-provenance --map`. Report `computed_from` gap before/after (expect 109 → 80). The 80 pre-G1 rows stay unmapped; no source is stated anywhere and inventing one is worse than the gap.

## 2. Integration

- `tests/` and `assessment/` green, counts recorded.
- `seldon verify` clean.
- `seldon cc complete` this file. Commit and push this file, the plan JSONL, the RESULT, `seldon_events.jsonl`, and the shim together.

## 3. RESULT must report

Precondition output; Regression A and B diff results and SI-09 warning counts at each step; the migrate-names plan class counts and the live outcome; the per-row assignment path used for the 63; the DD entry appended; the seldon task registered in Step 5; provenance before/after; every premise contradicted.

## 4. Out of scope

Everything §8 of the base hygiene task lists. Also: renaming any Result to satisfy the old grammar (the grammar changed, not the names).
