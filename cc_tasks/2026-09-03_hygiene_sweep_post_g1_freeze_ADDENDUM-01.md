# ADDENDUM-01 to `2026-09-03_hygiene_sweep_post_g1_freeze.md`

**Date:** 2026-09-04
**Authored by:** Desktop session
**Status:** AMENDS the base task. Does not supersede it. Base task + this addendum = the spec.
**Reason:** First dispatch stopped correctly at step 0 (RESULT dated 2026-09-03). The upstream seldon sweep has since completed (`seldon/cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology_RESULT.md`, 934 tests green, CLI live on PATH per its §10). This addendum folds in the first RESULT's §3 findings and the seldon RESULT's §5/§6 so the lanes run as intended.

**Immutable once written.**

---

## 0. Preconditions — amended

- Step 0 command checks stand. Note that `seldon task supersede`, `seldon task withdraw`, `seldon cc rederive-description` now exist; `seldon_task_update` refuses terminal states by design, so use the verb commands.
- Drop the "working tree clean" precondition. Known dirt: the four biblio-cron files (Lane 2's target). Record `git status` at start and proceed.
- Read the seldon RESULT §5 (A2 dry-run classes) and §6 (contradicted premises) before Lane 1.

## 1. Lane 1 — amendments

**Ambiguous and real-unit Results (seldon RESULT §5): assign names deterministically, no human input.** The first RESULT §3.6 established that none of the 63 affected Results (40 `ambiguous`, 23 `units_is_real_unit`) is cited by any `{{result:}}` token in any tracked file, so the byte-identity regression is unaffected by how they are named. Rule, Desktop decision:

`name := slug(units) + "__" + artifact_id[:8]`

Deterministic, unique by construction, greppable by the old units string. For `units_is_real_unit` rows keep `units` as is and add `name`; for `ambiguous` rows apply the same rule and clear `units` only if it is not a real unit under the packaged vocabulary (`seldon/domain/result_units_vocabulary.yaml`). Emit via `migrate-names` if it accepts per-row assignment; otherwise the same `artifact_updated` event shape the command emits, and report that you had to.

**Regression is resolver-output vs resolver-output, never grep counts** (first RESULT §3.4). The documentation placeholder `{{result:<NAME>:value}}` is excluded by the workaround resolver's regex; the seldon resolver must exclude it too (angle brackets are not legal in a name). If it does not, that is a seldon defect: report it, register a seldon ResearchTask, and keep the shim below in place until it lands.

**Token inventory is 11 files, not 2** (first RESULT §3.5). Regress every one: the findings memo (214), `docs/design_decisions.md` (17), `docs/crosswalk/deck_content_2026-09-03_draft.md` (14), the skeleton (3), and the seven `cc_tasks/*.md` files. The cc_tasks tokens are quoted prose; confirm both resolvers leave them untouched or both resolve them identically.

**Step 5 replaced — do not move `scripts/g1_resolve_results.py` to `retired/`.** `build_framework_deck.py` calls it with `--render`, and ai-readiness-kg has no `paper/` directory for `seldon paper build` to target. Instead: replace the script's body with a thin shim over seldon's resolver library function (find the import path in `seldon/paper/build.py`; call it with `allow_proposed=True`), preserving the script's CLI surface (`--check`, `--render`, and whatever else callers use — grep for every invocation). The debt being retired is the name-in-`units` matching logic, not the entry point. Header comment names this task and seldon `0bc41cfc`. After the swap, rerun the 11-file regression through the shim: zero diffs required.

**Step 6 unchanged.** Note the seldon RESULT's finding that the 91 incomplete-provenance Results reported by `seldon go` and the 515 in the handoff are different denominators; report both before/after.

## 2. Lane 3 — amendment

`a74433f8`'s own text says "fold into the next G1 task, not standalone". Overridden by the operator's cleanup instruction of 2026-09-03: execute it here. Spec is the two items quoted in the first RESULT §3.7; no third item.

## 3. Lane 4 — amendments

- Step 4: the `superseded` state was always legitimate (seldon RESULT §4: 31 rows, all via `proposed → superseded` through the state machine, 8 by `desktop`, 23 by `human`). No repair. Report the 31 count and that all lack `terminal_reason`; do not backfill reasons.
- Step 5: the boilerplate-description set is 17, not 7 (first RESULT §3.2 lists the ids). Re-query at run time — the seldon sweep's D3 fix stops new instances, so the set should be static now. `rederive-description` each; report any whose source file is missing (exit 1 is the correct behaviour, per seldon RESULT §7).
- Step 3 command form: `seldon task supersede 85851bcd --reason "..." --superseded-by 529133e4` as written in the base task; confirm the `superseded_by` edge exists afterwards by query.
- Step 1: `seldon ontology sync` — the seldon sweep changed no vocabulary and the master is at epoch 3; if this project's replica is already at epoch 3, sync is a no-op and that is the expected result. The relationship types Lane B was about live in `seldon/domain/research.yaml`, not the ontology (seldon RESULT §6.2); they are already available to this project through the installed package. Step 2's two link backfills therefore need no sync to succeed.

## 4. Integration — amendment

- `seldon cc complete` this task's base file. The RESULT file for this dispatch is `…_hygiene_sweep_post_g1_freeze_RESULT-02.md` so the first (gate-stop) RESULT is preserved.
- Commit the base task file, this addendum, both RESULTs, and `seldon_events.jsonl` together.
