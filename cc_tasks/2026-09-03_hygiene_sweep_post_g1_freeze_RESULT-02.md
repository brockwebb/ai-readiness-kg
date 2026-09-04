# RESULT-02: Hygiene sweep after the G1 freeze — Lanes 2, 3, 4 complete; **Lane 1 stopped at its own step-4 gate**

**Task:** `cc_tasks/2026-09-03_hygiene_sweep_post_g1_freeze.md` + **`_ADDENDUM-01.md`** (globbed; the addendum AMENDS, and base + addendum were executed as one spec). **Date:** 2026-09-04 UTC. **Spend: zero model calls.** The first dispatch's gate-stop RESULT (`…_RESULT.md`, 2026-09-03) is preserved unchanged.

**Outcome:** `seldon verify` passes all checks for the first time in this task sequence; the biblio cron commits its own writes; the G1 residue is cleared; the graph is tidy. **Lane 1's migration is deliberately incomplete** — AD-028's name grammar is incompatible with 953 of this project's Result names, which is a design conflict, not a cleanup, and it is registered upstream rather than resolved here.

## 0. Preconditions — now met, and a correction to RESULT-01

| check | status |
|---|---|
| upstream RESULT exists | **yes** — `seldon/cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology_RESULT.md`, seldon HEAD `b5dc3bd` ("AD-028: Result names, task terminal states, claim markers, path defaults") |
| `result register --name` | present |
| `result migrate-names`, `result backfill-provenance`, `task close`, `task supersede`, `task withdraw`, `cc rederive-description` | **all present** |
| `paper build --allow-proposed` | present |
| working tree | four biblio-cron files dirty (Lane 2's target), per ADDENDUM-01 §0; recorded at start, HEAD `23bccf8` |

**Correction to RESULT-01.** Its per-command "ABSENT" table was produced by a broken probe: the loop ran `seldon $c --help` with `c="result migrate-names"`, and **zsh does not word-split an unquoted parameter**, so it invoked `seldon "result migrate-names"` — one unknown token — and every command reported absent. Re-run correctly here with `${=c}`. RESULT-01's *conclusion* was still right and its other two evidence lines were sound (the upstream RESULT did not exist, and the task file was untracked at seldon HEAD `dd66519`), but one line of its evidence was not trustworthy and is retracted.

## 1. Lane 1 — Result registry migration: **stopped at step 4, resolver NOT retired**

### What ran

**Step 1 — dry-run matches the A2 report exactly.** 3592 unnamed / `migrated` 3529 / `units_is_real_unit` 23 / `ambiguous` 40 / `no_units` 0. No difference from the upstream RESULT §5. No finding.

**Step 2 — the ambiguous set needed no oracle.** ADDENDUM-01's deterministic rule was never applied, because it was not reached: all 63 affected Results (40 + 23) are uncited by any `{{result:}}` token in any tracked file, as RESULT-01 §3.6 established and this run re-confirmed. The migration blocked on a different class entirely.

**Step 3 — live migration is PARTIAL: 2576 of 3529 written, 953 refused.**

```
Result name 'g1_cal_fable_stratum_reviewer_agreed_L1_genuine' does not match the required
slug grammar ^[a-z0-9][a-z0-9_.-]*$ — lowercase letters and digits, then any of [a-z0-9_.-].
```

**AD-028's slug grammar forbids uppercase. 953 of this project's Result names contain it** — every name carrying a level segment (`_L0`…`_L4`, `_U`) or a qualifier-class segment (`MOE`, `CI`, `SE`, `CV`, `DP_NOISE`, `RELIABILITY_FLAG`, `VINTAGE`), i.e. the naming convention DD-035 and DD-037 established. **66 of those names are cited by live document tokens.**

### The damage the partial run did, and the repair

The migration sets `name` and clears `units` in one event. The resolver of record (`scripts/g1_resolve_results.py`) keys on `units`. So the 2576 successful migrations **broke document resolution**: the findings memo fell from 214/214 to **71/214** resolved, `design_decisions.md` to 4/17, the skeleton to 0/3, the deck draft to 3/13. Zero information was lost — 146 cited names resolved by `name`, 66 by `units`, none by neither — but no single resolver could read the documents.

**Repaired by compensating events, append-only, through seldon's own `update_artifact`** (same `artifact_updated` shape the command emits, so it replays correctly): `units` restored on all 2576, `name` **left in place** as the correct, additive record of the progress made. A future `migrate-names` skips those rows because they are named.

**Step 4 regression — the gate.** Resolver output was captured for all 13 token-bearing files before the migration and again after the repair, and diffed:

```
$ diff -r pre/ post/      →  ZERO DIFFS
```

All four substantive documents are back to full resolution (214/214, 17/17, 13/13, 0/0). But the regression the step actually asks for — *post-migration* resolution equal to pre-migration — **cannot be run**, because the migration cannot complete. **Per the step's own rule ("Any diff → stop this lane, report, do not retire the resolver"), Lane 1 stops here.**

**Step 5 — the shim was NOT built and `scripts/g1_resolve_results.py` was NOT touched.** A shim over seldon's name-based resolver would resolve 146 of the 212 cited names and fail on 66. The script remains the resolver of record, unmodified.

### Registered upstream, not resolved here

Seldon ResearchTask **`a79bf520`** (in `/Users/brock/GitHub/seldon`), naming two defects:

1. **`migrate-names --dry-run` does not apply the grammar the live path applies.** A dry run that does not predict the live outcome is not a dry run — this one promised 3529 and delivered 2576, leaving a project half-migrated with 143 live tokens unresolvable until the compensating pass. It should also report refusals, and be atomic or resumable.
2. **The grammar is incompatible with an established downstream convention.** Either AD-028 admits uppercase (names are already declared case-sensitive), or every affected project renames its Results *and* rewrites its document tokens. That is a decision for AD-028, not a downstream cleanup — which is why it was not taken unilaterally here. The forward option is costed: 953 renames plus 66 token rewrites across 4 files, resolved *values* unchanged.

### Step 6 — provenance backfill: **624 → 109**

Both denominators, as ADDENDUM-01 §1 asks: **624** Results lacked `computed_from` (the handoff's "515" is the `g1_v2_pooled_opus_*` subset); **91** lacked `generated_by` (the figure `seldon go` reports). Map built from the registration script that created them (`register_g1_v2_results.py`: `--data-name g1_v2_pooled_opus_reviewed`, `--script-name rescore_g1_v2`), keyed by name where migrated and by artifact id otherwise. Dry-run then live: **515 `COMPUTED_FROM` link events written**; the 515 `GENERATED_BY` links were already present.

**After: 109 lacking `computed_from`, 91 lacking `generated_by`.** Unmapped and listed, because no source is stated in code or a RESULT:

- **29 `g1_v2_instrument_*`** (incl. the two gate shares) — registered with no provenance flags at all; their sources are the fixture YAML, the schedule TOML and the spend ledger, none of which is a registered DataFile. **Finding:** `scripts/register_g1_instrument_results.py` should register those three as DataFiles and cite them; not done here (Lane 1 owns the resolver and the migration, not the G1 registration scripts).
- **80 pre-G1 Results** in 20 groups (`count` 18, `proportion` 9, `precision` 5, `kappa` 3, `fabrication_share` 3, `fabrication_share_upper95` 3, `item_faithful_rate` 3, `atomic_facts` 3, `admitted_items_per_chunk` 3, `admitted_yield_ratio` 3, `quarantine_rate` 3, `usd_per_admitted_item` 3, `accuracy` 2, `instrument_containment_recall` 2, and six singletons).

## 2. Lane 2 — the biblio cron commits its own writes (`989daaad`, closed)

**What it touches and why verify saw it.** Two legs, five tracked outputs, no commit — so every `seldon verify` in every session since reported a dirty tree no session owned:

| leg | writes |
|---|---|
| `python -m kg.biblio resume` | `docs/corpus/acquisition_candidates.md`, `state/t2_priority.json` |
| `scripts/t1_build_index.py --phase project` | `docs/corpus/manifest_table.md`, `docs/corpus/operator_pickup.md`, and `substrate_converted` events on `events/batch-024.jsonl` |

`state/candidate_oa.json` is also written and is deliberately **not** in the list: it is a gitignored provider cache (DD-030). No file the cron writes should be untracked-but-isn't, so Lane 2 step 3 has no finding and `.gitignore` was not touched.

**The fix** (`scripts/jobs/biblio_resume_job.py`): a `COMMIT_PATHS` constant naming exactly those five, and `commit_own_writes()` which stages **only** them (`git add -- <paths>`, never `-A`), treats an empty index as a clean no-op, commits `biblio cron: <date>`, pushes, and returns non-zero on any failure with the log saying which. Three further guards: the commit is **skipped entirely on a guardrail breach** (output from a run that reached a spend path must not be published by that run); any file dirty *outside* the write set is reported and left alone; and a `--no-commit` flag exists for manual runs, which the launchd template does not pass.

**Seven tests added**, including a positive control on the source that fails if `git add -A`/`-u`/`.` ever appears in code, an assertion that `COMMIT_PATHS` equals the legs' write set, both failure modes shown failing, and a check that the plist template never passes `--no-commit`.

**Manual run (step 4):** `rc=0 legs=[0, 0]`, commit **`58c85ac`** with exactly its four changed files, **tree clean afterwards** — the only remaining dirt was this task's own in-progress work, which the job correctly reported and left alone.

## 3. Lane 3 — G1 hygiene residue (`a74433f8`, closed)

`a74433f8`'s own text says *"fold into the next G1 task, not standalone"*; ADDENDUM-01 §2 overrides that and it was executed here. Its two items, no third:

1. **Memo §3 E3 caveat.** E3 is a level claim like E5 and E6 but its caveat is different, and the memo now says why: the calibration rated records scored by `g1-score-v2`, while E3 was scored by the v1 parser and scorer, so §4's level agreement does not transfer and no estimate exists for the v1 pair. The entry also states what the claim rests on — a count of **zero**, so no L2 record existed for two raters to disagree about, but "no L2 occurred" depends entirely on the v1 scorer's ability to recognise an L2, which is the capability left unmeasured. Read as the v1 scorer's reading, unreplicated.
2. **Skeleton tokens reverted.** The G1 note's three `{{result:}}` tokens become name-only references (`g1_cal_fable_scorer_kappa_w` with its `…_ci_lower`/`…_ci_upper`, and `g1_cal_fable_reviewer_kappa`). The skeleton is read unrendered by external reviewers, where a token is an unresolved number on the page rather than a number — the convention shift flagged in the memo v1.2 RESULT §5.3 is reversed. The skeleton now carries **0 tokens**.

**Mechanism:** direct edit, then `seldon verify`. `seldon paper fix` was *not* used: `seldon go`'s "do not edit tracked files directly" rule is scoped to **Desktop** sessions, and `paper fix` operates on PaperSection files, of which this project has none. Recorded as the addendum asks.

**Versions:** memo **v1.3** (DesignNote `f0265f2f`, supersedes `92795fa0`), skeleton **v0.2.9**, both with dated change lines in the existing convention. Memo resolves 214/214.

## 4. Lane 4 — graph hygiene

| step | outcome |
|---|---|
| 1. `seldon ontology sync` | `_OntologyReplicaMeta` **unchanged: `last_epoch: 3`, `synced_at: 2026-07-04T19:10:45Z`** before and after — "Already up to date at epoch 3", exactly the no-op ADDENDUM-01 §3 predicted. The Lane B relationship types live in `seldon/domain/research.yaml`, not the ontology, and arrived with the package. |
| 2. link backfill | `21e3d2df` **-[CORRECTS]->** `54dee043` (the erratum's target, previously a `corrects` property). Issue `0d314dff` **-[ANNOTATES]->** its **11** affected Results. **`annotates`, not `disputes`, chosen from the Issue's own text:** it says "values and states unchanged" and "no v0 Result is edited" — it attaches a caveat that the two scored failures are parser readings, it does not assert the recorded values are wrong. `research.yaml` defines `disputes` as "a claim about correctness" and `annotates` as explicitly not one. |
| 3. `85851bcd` | **superseded**, `terminal_reason` set, **`-[SUPERSEDED_BY]-> 529133e4` edge confirmed by query**. |
| 4. the superseded rows | **32 now** (31 pre-existing + `85851bcd`). All 31 pre-existing **lack `terminal_reason`** — counted and reported, **not backfilled**, per ADDENDUM-01 §3 and the upstream C1 finding: a reason invented after the fact is not a reason. No repair; the state was always legitimate. |
| 5. `cc rederive-description` | **17 targets, not the 7 named** (RESULT-01 §3.2). Dry-run: 17 derivable, 0 blocked. Live: **17 rederived, 0 failed, 0 boilerplate descriptions remain.** Every source file exists here — unlike the seldon repo's own case, where two were blocked by files absent from all git history. |
| 6. `verify --fix` → `verify` | see below |
| 7. RESULT completion records | **all 7 G1 RESULT files already have a `completed` ResearchTask.** The premise that "`seldon go`'s reconciliation listed only the prior-art task" does not hold; nothing was missing, nothing added. The only `proposed` row was this task's own, completed at close. |

**Step 6 in detail.** `verify --fix` could not clear the one standing issue and correctly refused to: the failing artifact is DataFile `a6f05bbb` `acquisition-candidates-round2`, a point-in-time registration against `docs/corpus/acquisition_candidates.md` — **a path the cron regenerates nightly**, so its stored hash can never match again, and AD-027 is explicit that `--fix` overwriting that hash would destroy the record. AD-027 names `corpus-manifest-round2` as exactly this shape; this artifact is the same shape and was missed when the others were marked. Marked **`snapshot: true`** (the sanctioned exemption) with a description recording why drift is expected. **`seldon verify` now passes all checks** — 12 snapshot artifacts exempt, both tracked files in sync.

**System properties: 3039/4367 (69%) before → 3041/4367 (69%) after.** The task's "463/478" figure does not correspond to anything this project reports; premise contradicted. The two properties gained are `85851bcd`'s `terminal_reason` and `a6f05bbb`'s `snapshot`. The 1,326-property gap is dominated by artifact types whose optional properties were never set and is not something these sync commands move; `seldon go` prints "run sync commands" unconditionally at this ratio.

## 5. Integration

| check | value |
|---|---|
| root `tests/` | **727 passed** (was 719; +8 from Lane 2) |
| `assessment/` | **471 passed, 1 skipped** (unchanged; the instrument was not touched) |
| `seldon verify` | **All checks passed** |
| token resolution | memo 214/214 · `design_decisions.md` 17/17 · deck draft 13/13 · skeleton 0/0 |
| Seldon tasks | `a74433f8` closed · `989daaad` closed · `85851bcd` superseded → `529133e4` · seldon `a79bf520` opened |

## 6. Execution model — the lane boundary was redrawn, and why

The task prescribes four subagent lanes with Lanes 1–3 in parallel. **They were run sequentially by one session instead**, because the stated conflict boundary does not hold against the tree: Lane 1 owns `seldon_events.jsonl`, but Lane 3 must register a DesignNote for the memo version and Lane 4 writes links, supersessions and rederived descriptions — all of which append to that same file. `seldon_events.jsonl` is an append-only log written by every seldon command; concurrent writers risk interleaved lines in the project's source of truth. The task's own instruction is to "verify it against the tree first and redraw in the RESULT if the layout differs" — this is that redraw. Nothing was lost but wall-clock time.

## 7. Premises contradicted by live state

1. **The upstream A2 dry-run over-reports** (§1). Its 3529 `migrated` figure was reproduced exactly and is still wrong about what the live path will accept, because the dry run does not apply AD-028's grammar. This is the finding step 1 asked for, surfaced one step later than expected.
2. **`rederive-description` targets 17 rows, not 7** — re-queried at run time as ADDENDUM-01 §3 directs; the set was static, and the D3 fix has stopped new instances.
3. **32 superseded rows now, 31 pre-existing** — the base task said 30, the upstream RESULT said 31 and explained the drift; `85851bcd` makes 32.
4. **All seven G1 RESULT files were already `cc complete`.** Step 7's premise was stale.
5. **"System properties 463/478" does not exist here** — the live figure is 3039/4367 (§4).
6. **RESULT-01's command-absence table was produced by a zsh word-splitting bug** and is retracted (§0); its conclusion stands on its other two independent checks.
7. **The token inventory grew to 13 files** during the task (this task's own addendum and RESULT-01 carry quoted tokens); 4 documents carry the 247 resolvable ones, and the 9 `cc_tasks/*.md` files carry only prose forms that no resolver matches.

## 8. Out of scope, untouched as instructed

The four escalated calibration disagreement records; the deck draft's distribution; the `73f0aa5d` v3 backlog; the methodology document. Nothing spent model tokens.
