# RESULT: Result name migration completed, units-matching retired, G1 instrument provenance closed

**Task:** `cc_tasks/2026-09-04_result_migration_completion.md` + **`_ADDENDUM-01.md`** (globbed; the addendum AMENDS, and base + addendum were executed as one spec). **Continues** `2026-09-03_hygiene_sweep_post_g1_freeze.md` Lane 1, which stopped at its step-4 gate. **Date:** 2026-09-04 UTC. **Spend: zero model calls.**

**Outcome: all six steps complete.** All 3,592 Results carry a `name`, nothing was renamed to satisfy a lint, both regressions are byte-identical, SI-09 fallback resolutions went **73 → 0**, and `seldon verify` passes every check.

## 0. Preconditions and the git guard

| check | result |
|---|---|
| `seldon result migrate-names --help` shows `--partial` and `--report` | **both present** |
| upstream RESULT read | `2026-09-04_ad028_grammar_amendment_migrate_atomic_RESULT.md` (§2 and §6.6) |
| seldon code SHA (ADDENDUM §3) | **`e5beffb`**, and the verification trap does not apply: `/Users/brock/Documents/GitHub/seldon` is a symlink to `/Users/brock/GitHub/seldon`, both `rev-parse HEAD` to the same commit, and the module resolves to that one checkout |
| grammar probe | replaced by ADDENDUM §0 with the step-2 dry run, which reproduces the upstream counts exactly (§2 below) |

**Git guard.** ADDENDUM §0 asks for the task file and addendum to be committed first so `cc complete` is not refused. Done as the session's first action — **commit `3a10cbc`**, carrying both files and the registration event. **Discrepancy:** the addendum specifies the message `cc task: result migration completion (registered e1a18ca0)`; the commit reads `task: Result migration completion (task file + ADDENDUM-01 + registration)`. The guard's purpose — both files tracked before `cc complete` — is satisfied; rewriting history to match a message string would cost more than it is worth, so the difference is reported rather than repaired.

## 0.5 Ontology sync (ADDENDUM §1)

| | before | after |
|---|---|---|
| `_OntologyReplicaMeta.last_epoch` | **3** | **4** |
| `synced_at` | 2026-07-04T19:10:45Z | 2026-09-04T16:14:19Z |
| the two `leibniz-pi` junk terms | `active` | **`deprecated`** |

`Synced to epoch 4: 0 new, 5 updated, 2 deprecated` — precisely the addendum's prediction.

## 1. Step 1 — the shim, and Regression A

`scripts/g1_resolve_results.py` is now a shim over `seldon.paper.build`: `load_named_artifacts` for the name index, `build_units_fallback_index` for the transitional one, and `resolve_references(..., allow_proposed=True)` for the substitution. What it retires is its own lookup — replaying `seldon_events.jsonl` and matching the token key against `units`. The entry point stays, as ADDENDUM-01 of the previous task directed: `--render` is how the deck draft is built, `--check` is cited in the memo's own header and in three task files, and this project has no `paper/` for `seldon paper build` to target.

**CLI surface preserved** (every caller grepped: `tests/test_g1_resolve_results.py`, the memo header, three task files; no launchd job or script invokes it): `--check`, `--render`, `--out`, `--get`, `--prefix`, and `--events`, which is now accepted and documented as ignored because the index is the graph.

**Two adaptations were required, and both are the reason Regression A passes.** A naive shim would have rewritten every number in three documents:

1. **Integral values.** Every Result was registered through `--value FLOAT`, so the graph holds `26.0`; the library's `str(value)` would put "26.0" into sentences that have read "26" for three tasks. The value is pre-rendered into the index handed to the library.
2. **The `(proposed)` marker.** `allow_proposed=True` is the correct call — every Result here is `proposed` and always has been — but the library also stamps `(proposed)` into the rendered text. Right for a paper going to press, wrong for these documents. Suppressed by presenting the state as accepted in the index; **no information is lost** — `--check` reports the counts, and SI-09 use is reported per token, which is what the migration is measured by.

**The placeholder defect, found and registered.** Seldon's `REFERENCE_PATTERN` uses `[^:}]+` for the name, so it **matches `{{result:<NAME>:value}}`** — the placeholder the findings memo's header and `docs/design_decisions.md` both carry while explaining the syntax — and reports it as SI-01 "artifact not found". Proven in a test. The shim keeps this project's stricter grammar as a pre-filter, and the defect is registered upstream as seldon ResearchTask **`3376805b`** with the suggested fix (reuse `RESULT_NAME_PATTERN`'s character class) and the removal condition for the pre-filter.

**Regression A: ZERO DIFFS.** Old body (from `git show HEAD:`) against the shim, over all **15** token-bearing files / **244** tokens, 0 unresolved on both sides. SI-09 warnings at this step, as expected while 953 rows were still unnamed: **66** in the memo, **4** in `design_decisions.md`, **3** in the deck draft, **73 total**.

**Tests rewritten, not patched.** The three tests that pinned the event-log replay described machinery that no longer exists; keeping them would have meant keeping the machinery. What replaces them tests the contract a shim owes its callers: unresolved tokens never become plausible numbers, an ambiguous name is never guessed, `26` does not become `26.0`, no `(proposed)` marker leaks, and the placeholder is not a token — with a positive control asserting seldon's pattern *does* match it, which fails and retires the pre-filter the day upstream fixes it. 10 tests, all passing.

## 2. Step 2 — the plan, and the 63

`seldon result migrate-names --dry-run --report cc_tasks/2026-09-04_migrate_plan.jsonl`, **exit 0**:

| class | count | expected (ADDENDUM §0) |
|---|---:|---|
| `migrated` | **953** | 953 |
| `name_set_units_pending` | **2576** | 2576 |
| `already_named` | 0 | — |
| `units_is_real_unit` | **23** | 23 |
| `ambiguous` | **40** | 40 |
| `no_units` | 0 | — |
| **`refused`** | **0** | 0 |

Exact agreement with the upstream dry run, which is the grammar check the addendum substituted for the `register --name` probe. Sums to 3592.

**The 63 rows, named by ADDENDUM-01 §1's deterministic rule** `name := slug(units) + "__" + artifact_id[:8]` — unique by construction, greppable by the old units string, no human input, on the standing evidence that none of the 63 is cited by any token in any tracked file. The split was checked against the packaged vocabulary rather than assumed: **not one** of the 40 ambiguous strings (`precision`, `proportion`, `fabrication_share`, …) is a real unit, so all 40 had `units` cleared; all 23 `units_is_real_unit` rows (`count` 18, `kappa` 3, `accuracy` 2) **kept** `units`, because those are units and not names.

**Per-row assignment path — reported as the task requires: there is none.** `migrate-names` exposes no `--assign`, and `--report` writes only. The assignments were emitted as the same `artifact_updated` shape the command itself emits, through seldon's own `update_artifact`, which writes the event and the graph together. A generated name that violated the grammar, or any collision, would have aborted before writing.

## 3. Step 3 — live migration

Run **without `--partial`**. **Exit 0**, `refused 0`, and the event log grew by exactly **3529** lines = 953 `migrated` + 2576 `name_set_units_pending`, with the 63 skipped as `already_named`. ADDENDUM §0's assertion holds exactly: exit 0 meant everything migrated.

**End state: 3592 Results, 0 unnamed, 23 still carrying `units`** — and those 23 are precisely the real-unit rows (`count` 18, `kappa` 3, `accuracy` 2).

## 4. Step 4 — Regression B

**ZERO DIFFS** against Step 1's pre-migration captures, same 15 files / 244 tokens.

**SI-09 warning count: 0.** Every token now resolves by `name`:

| document | tokens | resolved | via SI-09 before | after |
|---|---:|---:|---:|---:|
| findings memo | 214 | 214 | 66 | **0** |
| `docs/design_decisions.md` | 17 | 17 | 4 | **0** |
| deck content draft | 13 | 13 | 3 | **0** |
| skeleton | 0 | 0 | 0 | **0** |

## 5. Step 5 — the fallback dependency is retired

**DD-039** appended to `docs/design_decisions.md` (DesignNote `1ca7e5ee`): tokens resolve by `name` against the graph; 953 names keep their uppercase segments because the grammar changed and the names did not; the 63 were named deterministically; and the operational consequence — **73 → 0 SI-09 resolutions**, so the fallback can be removed upstream with no effect here and any future SI-09 line for this project is a regression rather than a leftover.

Seldon ResearchTask **`1581c3ec`** registered: *"remove SI-09 units fallback once all projects report zero fallback resolutions"*, carrying this project's evidence line and naming the three functions the removal condition covers.

## 6. Step 6 — G1 instrument provenance

**Four DataFiles registered, not three** — the registration script reads *two* fixture YAMLs (dev and holdout), not one:

| DataFile | path | snapshot |
|---|---|---|
| `g1_v2_fixture_propositions_dev` `84c8516a` | `assessment/tests/fixtures/g1/v2/propositions.yaml` | true |
| `g1_v2_fixture_propositions_holdout` `77b1eebe` | `assessment/tests/fixtures/g1/v2/propositions_holdout.yaml` | true |
| `g1_v2_schedule` `d821509f` | `assessment/config/g1_v2_schedule.toml` | true |
| `spend_ledger` `7c07cbdc` | `state/spend_ledger.jsonl` | **true — AD-027**, the ledger is append-only and always growing, so drift is expected by design |

Script `register_g1_instrument_results` `2a0be611` registered too, since the Results needed a `generated_by` as well.

**The script is amended so this does not recur:** each of its 29 rows now carries the DataFile it is read from and registers with `--name` and `--data-name`. The gate shares cite the reviewed results files they are computed from (`g1_v1_holdout_fresh_reviewed`, `g1_v2_holdout_reviewed`) rather than the ledger.

**Backfill: 58 link events written** (29 `computed_from` + 29 `generated_by`), 0 already present.

| | before | after |
|---|---:|---:|
| Results lacking `computed_from` | 109 | **80** — exactly the predicted figure |
| Results lacking `generated_by` | 91 | **62** |

**The 80 stay unmapped, deliberately.** They are pre-G1 Results across 20 groups (`count` 18, `proportion` 9, `precision` 5, `kappa` 3, and sixteen smaller groups) whose source is stated in no script and no RESULT. Inventing one would be worse than the gap.

## 7. Integration

| check | value |
|---|---|
| root `tests/` | **729 passed** (was 727; the resolver suite went 8 → 10) |
| `assessment/` | **471 passed, 1 skipped** (unchanged; the instrument was not touched) |
| `seldon verify` | **All checks passed** — including two checks that did not exist before this week: `Relationship types  All canonical (uppercase)` and `Task source files  All 59 resolve on disk` |
| token resolution | memo 214/214 · `design_decisions.md` 17/17 · deck draft 13/13 · skeleton 0/0, **0 via SI-09** |
| ontology | epoch 4 |

## 8. Premises contradicted by live state

1. **The fixture source is two files, not one** (§6). "Register three DataFiles" became four.
2. **`migrate-names` has no per-row assignment path** (§2). The base task allowed for `--assign`, a plan-file input, or the event shape; only the third exists, and it was used.
3. **Seldon's resolver matches the documentation placeholder** (§1). The base task anticipated this as a possibility ("If seldon's resolver matches it…"); it does, so the pre-filter stays and `3376805b` is registered.
4. **Seldon's renderer differs from this project's in two ways** (§1) — `str(26.0)` and the `(proposed)` marker — neither of which the task anticipated, and both of which would have failed the zero-diff gate had the shim not preserved the contract.
5. **The commit message for the git guard differs** from the string ADDENDUM §0 specifies (§0); the guard's purpose is met.
6. **The token inventory is 15 files / 244 tokens**, up from the 13 / 244 of the previous task — this task's own file and addendum carry prose tokens. The four substantive documents are unchanged at 244 resolvable tokens.
7. **`already_named` is a class the base task's expected-class list did not include** (§2); it is how the 63 pre-named rows were correctly skipped by the live run.

## 9. Out of scope, untouched

Everything §8 of the base hygiene task lists — the four escalated calibration records, the deck draft's distribution, the `73f0aa5d` v3 backlog, the methodology document. And, as §4 of this task requires: **no Result was renamed to satisfy the old grammar.** The grammar changed; the names did not.
