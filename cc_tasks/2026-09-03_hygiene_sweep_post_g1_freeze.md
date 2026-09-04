# CC Task — Hygiene sweep after the G1 freeze

**Date:** 2026-09-03
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Closes Seldon tasks (this graph):** `a74433f8`, `989daaad`, `85851bcd` (→ superseded)
**Spend:** zero model spend. No `claude -p` calls. No ceiling needed.
**SEQUENCING:** Runs AFTER `seldon/cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology.md` has a RESULT and its CLI is installed. Step 0 verifies this; if the new commands are absent, stop and report.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. Preconditions (stop if any fails)

- `seldon result register --help` shows `--name`; `seldon result migrate-names --help`, `seldon result backfill-provenance --help`, `seldon paper build --help` (shows `--allow-proposed`), `seldon task close --help`, `seldon task supersede --help`, `seldon cc rederive-description --help` all exist.
- Read `seldon/cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology_RESULT.md` — in particular the A2 dry-run report for this project and the C1 finding.
- Working tree clean except for known biblio-cron dirt (see Lane 2). Record `git status` at start.

## 1. Execution model

Four lanes as subagents; Lanes 1–3 are disjoint by file set and run in parallel; Lane 4 runs after Lane 1 (it depends on the resolver switch). Each lane writes a `_SUBRESULT.md`; integration writes the RESULT. Lane file ownership is the conflict boundary — verify it against the tree first and redraw in the RESULT if the layout differs.

## 2. Lane 1 — Result registry migration and resolver retirement

**Owns:** `seldon_events.jsonl` (append via seldon commands only), `scripts/g1_resolve_results.py`, `docs/research/2026-09-03_g1_eval_findings.md` is NOT owned here (Lane 3).

1. `seldon result migrate-names --dry-run` → confirm it matches the A2 report from the seldon RESULT. Any difference is a recorded finding.
2. Resolve the `ambiguous` set using the workaround resolver as the oracle: for each ambiguous Result, what does `scripts/g1_resolve_results.py` resolve it to today? Assign `name` to match that behaviour (by the migrate command with an explicit `--assign ID=NAME` override if one exists; if not, register the assignment via the same event type the migrate command emits and report that you had to). The rule: post-migration resolution must be byte-identical to pre-migration for every token in every document listed in step 4.
3. `seldon result migrate-names` live.
4. Regression: build every document that carries `{{result:}}` tokens with the new resolver (`seldon paper build --allow-proposed --no-render` or the repo's equivalent) and with the workaround resolver; diff the resolved text. Known documents: `docs/research/2026-09-03_g1_eval_findings.md` (214 tokens per handoff — verify the count), `docs/crosswalk/usafacts_operationalization_skeleton.md`, any RESULT or memo under `docs/research/` and `docs/crosswalk/` that greps for `{{result:`. Zero diffs required. Any diff → stop this lane, report, do not retire the resolver.
5. On zero diffs: retire `scripts/g1_resolve_results.py` — move to `scripts/retired/` with a header comment naming this task and the seldon task; do not delete. Update any doc that references it (grep) to name the seldon command instead. Those doc edits are mechanical; use `seldon paper fix` if the files are tracked artifacts, otherwise direct edit with the change listed in the sub-RESULT.
6. Provenance backfill: the handoff says 515 G1 Results lack `computed_from`; `seldon go` lists 91 Results with incomplete provenance. Build the `--map` file for `seldon result backfill-provenance` from the registration scripts that created them (`scripts/register_g1_instrument_results.py` and any sibling; the RESULT files under `cc_tasks/` name the source data files per Result). Only map where the source is stated in code or a RESULT; where it isn't, leave the Result unmapped and list it. Run `--dry-run`, then live. Report before/after counts of Results lacking `computed_from`.

## 3. Lane 2 — Biblio cron commits its own writes (`989daaad`)

**Owns:** the biblio cron script and its launchd plist (locate via `scripts/jobs/` and `docs/corpus/acquisition*` references), nothing else.

1. Identify exactly which tracked files the cron modifies and why every `seldon verify` reports them dirty.
2. Fix: the cron run ends with `git add <its files> && git commit -m "biblio cron: <date>" && git push`, guarded so a failing commit/push exits non-zero and logs, and so it never commits files outside its own write set (explicit path list, not `git add -A`). If the repo has a shared "commit at end of task/burn" helper (per `~/GitHub/CLAUDE.md` §10), use it.
3. If the cron writes files that should not be tracked at all, that is a finding — report it, do not change `.gitignore` without stating the reasoning in the sub-RESULT.
4. Run the cron manually once; confirm the tree is clean afterwards and a commit exists.

## 4. Lane 3 — G1 hygiene residue (`a74433f8`)

**Owns:** `docs/research/2026-09-03_g1_eval_findings.md`, `docs/crosswalk/usafacts_operationalization_skeleton.md`, `docs/design_decisions.md` (append only).

1. Read `a74433f8`'s full description from the graph; it is the spec for this lane. Two items are known: (1) memo §3 E3 caveat — the v1 scorer sentence differs from the v2 one; state the caveat as the task describes. (2) Skeleton `{{result:}}` tokens revert to name-only references (the skeleton is a design document, not a built paper). Any further items in the task description are in scope.
2. These are tracked artifacts: use `seldon paper fix` or the mechanism `seldon go`'s behavioural contract requires for tracked-file edits; record which.
3. Bump the memo to v1.3 and the skeleton to v0.2.9 with dated change lines, matching the existing version-line convention in each file.
4. `seldon verify` clean for these files.

## 5. Lane 4 — Graph hygiene (after Lane 1)

**Owns:** graph state via seldon commands only; no file edits.

1. `seldon ontology sync` (pulls Lane B edge types from the seldon task). Confirm `_OntologyReplicaMeta` advanced.
2. Backfill the two property-carried links named in seldon task `698d1d86`: ERRATUM-01 (DesignNote `21e3d2df`) `corrects` its target(s); Issue `0d314dff` `annotates`/`disputes` its Result (pick per what the Issue text says; state the choice). Link creation by event.
3. `seldon task supersede 85851bcd --reason "premise false: operator does not label; independent-model rater per DD-037" --superseded-by 529133e4`.
4. The 30 pre-existing `superseded` ResearchTasks: apply the C1 finding from the seldon RESULT. If they are legitimate, no action; if they were written outside the state machine, record the finding and — only if the seldon RESULT provides a sanctioned repair command — apply it. Otherwise leave and report.
5. `seldon cc rederive-description` on the seven ResearchTasks whose description is `**Immutable once written. Changes require a new task file.**` (ids `fc94ae2f 080956ad ec39ac62 f7249d86 0a7bc052 3d1ccbec fd49d222` — verify by query first; the set may have changed).
6. `seldon verify --fix`; then `seldon verify`. Report every residual. Also report the "System properties 463/478" figure before and after — `seldon go` says run sync commands; do so and report what moved.
7. The six G1 RESULT files from 2026-09-02/03: confirm each has a `seldon cc complete` record in the graph (`seldon go`'s reconciliation listed only the prior-art task). Any missing → `seldon cc complete` it now with a note that completion was recorded late.

## 6. Integration

1. Merge; run `python -m pytest tests/ -v` and `assessment/` tests if separate — green.
2. `seldon verify` clean or every residual listed.
3. `seldon task close a74433f8` and `989daaad` with notes; `85851bcd` was superseded in Lane 4.
4. `seldon cc complete` this task file; write the RESULT; commit and push.

## 7. RESULT must report

- Precondition check output.
- Lane 1: migrate counts, ambiguous resolutions, regression diff result (must be zero or lane stopped), resolver retired yes/no, provenance backfill before/after counts and the unmapped list.
- Lane 2: files the cron touches; fix mechanism; manual-run clean-tree confirmation.
- Lane 3: exact edits, mechanism used, new version lines.
- Lane 4: ontology replica meta before/after; the two backfilled links; 85851bcd final state; disposition of the 30 superseded rows; rederived descriptions; `seldon verify` residuals; System-properties before/after; RESULT completion records found/added.
- Every premise here that live state contradicted.

## 8. Out of scope (do not touch)

- The four escalated calibration disagreement records (`assessment/results/g1_calibration_disagreements_2026-09-03.md`) — operator item.
- Deck draft distribution (`framework_deck_2026-09-03_draft.pptx`) — operator item.
- `73f0aa5d` v3 backlog — frozen until January.
- Methodology document — Desktop deliverable.
- Anything that spends model tokens.
