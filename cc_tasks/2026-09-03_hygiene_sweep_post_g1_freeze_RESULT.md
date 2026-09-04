# RESULT: Hygiene sweep after the G1 freeze — **STOPPED AT STEP 0**, preconditions not met

**Task:** `cc_tasks/2026-09-03_hygiene_sweep_post_g1_freeze.md` (no addenda: globbed `…_ADDENDUM*.md`, none found). **Date:** 2026-09-03 UTC. **Spend: zero model calls** — no `claude -p`, no ledger reservation. **Outcome: the task's own step-0 gate failed and the task stopped there.** No lane was executed; no file was edited; no graph state was changed.

Step 0 says: *"Runs AFTER `seldon/cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology.md` has a RESULT and its CLI is installed. Step 0 verifies this; if the new commands are absent, stop and report."* Every required command is absent and the upstream task has not been executed. Gates bind the machine; this one is doing its job, so the report is the deliverable.

## 1. Precondition check — output verbatim

**The upstream task has not run.** Its task file exists but is **untracked** in the seldon repo, and there is no RESULT:

```
$ ls /Users/brock/Documents/GitHub/seldon/cc_tasks/ | grep 2026-09-03
2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology.md

$ git -C /Users/brock/Documents/GitHub/seldon status --short
 M seldon_events.jsonl
?? cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology.md
?? docs/design/guarded_incremental_change_cycle.md

$ ls cc_tasks/ | grep -c "2026-09-03.*RESULT"     →  0
```

**The CLI it would deliver is not installed.** `seldon` is an editable install resolving to `/Users/brock/Documents/GitHub/seldon/seldon` at HEAD `dd66519` ("track_cc_tasks…"), which predates the sweep:

| required capability | status |
|---|---|
| `seldon result register --name` | **ABSENT** (only `--units`, `--script-name`, `--data-name`, …) |
| `seldon result migrate-names` | **ABSENT** |
| `seldon result backfill-provenance` | **ABSENT** |
| `seldon paper build --allow-proposed` | **ABSENT** |
| `seldon task close` | **ABSENT** |
| `seldon task supersede` | **ABSENT** |
| `seldon cc rederive-description` | **ABSENT** |

6 of 6 subcommands and both new flags are missing. The A2 dry-run report and the C1 finding that Lanes 1 and 4 are built on do not exist to be read.

**Working tree at start** (the third precondition, also not met — see §3.1):

```
 M docs/corpus/acquisition_candidates.md      ← known biblio-cron dirt
 M docs/corpus/operator_pickup.md             ← known biblio-cron dirt
 M events/batch-024.jsonl                     ← known biblio-cron dirt
 M state/t2_priority.json                     ← known biblio-cron dirt
 M seldon_events.jsonl                        ← NOT cron dirt; see §3.1
?? cc_tasks/2026-09-03_hygiene_sweep_post_g1_freeze.md
HEAD: 4259ff7
```

## 2. What was not done

Lanes 1–4 were not started, so none of the RESULT-must-report items in §7 of the task can be answered: no migration counts, no ambiguous resolutions, no regression diff, no resolver retirement, no provenance backfill, no cron fix, no memo/skeleton edits, no ontology sync, no link backfill, no `85851bcd` supersede, no rederived descriptions, no `seldon verify --fix`. `scripts/g1_resolve_results.py` stays in place and stays the resolver of record. `a74433f8`, `989daaad` and `85851bcd` remain open, in the states they were in.

**This task file's own ResearchTask is left `proposed`.** `seldon cc complete` was deliberately not run: the task did not complete, and recording a completion for work that stopped at its gate is precisely the false-premise closure this project refused for `85851bcd` two tasks ago.

## 3. Premises the live state contradicted

Everything below was found while verifying preconditions — read-only, no lane executed. Each is recorded so the next attempt does not have to rediscover it.

### 3.1 The working tree was not clean of anything but cron dirt

`seldon_events.jsonl` carries **two uncommitted `artifact_created` ResearchTask events** written by the Desktop session that dispatched this task: `a74433f8` (the G1 hygiene residue task, which is Lane 3's spec) and the registration of *this* task file. They are legitimate graph records, not dirt, but they were uncommitted at start and the task's precondition did not anticipate them. They are committed with this RESULT.

### 3.2 The `cc rederive-description` set is 17 tasks, not 7 — and still growing

Lane 4 step 5 names seven ids and says "verify by query first; the set may have changed". It has. Replaying the event log to each ResearchTask's **current** description, **17** carry the immutability boilerplate `**Immutable once written. Changes require a new task file…**` as their whole description, of 99 ResearchTasks total:

```
080956ad 0a7bc052 0b0bc3e9 19d9697f 1d1f0673 3d1ccbec 703825e3 7fd75c3d a33acf4f
ab28a2f8 c49109b1 ca2a4457 dce5688d ec39ac62 f7249d86 fc94ae2f fd49d222
```

States: 9 `completed`, 7 `superseded`, 1 `proposed`. The seven named in the task are a subset. **The one `proposed` row is this task's own registration**, created minutes before dispatch — so the registrar's description-parsing defect (upstream Lane D3) is still producing instances, and any repair that runs before D3 lands will be overtaken. Worth sequencing D3 ahead of the rederive, not beside it.

### 3.3 There are 31 superseded ResearchTasks, not 30

Lane 4 step 4 speaks of "the 30 pre-existing `superseded` ResearchTasks". The live count is **31**. Seven of them are also in the boilerplate-description set above, so the two Lane 4 items overlap more than the task assumes.

### 3.4 The memo's token count depends on which counter you use — 214 is right

Lane 1 step 4 says "214 tokens per handoff — verify the count". Verified, and the two plausible counts differ by one for a reason the migration must not trip over:

| file | raw `grep -o '{{result:[^}]*}}'` | resolver `--check` |
|---|---:|---:|
| `docs/research/2026-09-03_g1_eval_findings.md` | 215 | **214 resolved** |
| `docs/design_decisions.md` | 18 | **17 resolved** |
| `docs/crosswalk/usafacts_operationalization_skeleton.md` | 3 | **3 resolved** |

The extra token in each of the first two files is the deliberate documentation placeholder `{{result:<NAME>:value}}`, which the resolver's regex excludes by design (angle brackets are not a legal name). **A migration or a new resolver that matches it will report a spurious unresolvable token**; the regression in Lane 1 step 4 should compare resolver output to resolver output, not grep counts.

### 3.5 The token inventory is wider than the "known documents" list

Lane 1 step 4 names two documents. Eleven tracked files carry `{{result:` today:

`docs/research/2026-09-03_g1_eval_findings.md` (215 raw) · `docs/design_decisions.md` (18) · `docs/crosswalk/deck_content_2026-09-03_draft.md` (14) · `docs/crosswalk/usafacts_operationalization_skeleton.md` (3) · and seven `cc_tasks/*.md` task and RESULT files carrying 1–5 each, where the tokens appear inside quoted prose describing the convention rather than as numbers to resolve.

The deck draft (14 real tokens) is the one substantive omission from the task's list: it is resolved at build time by `scripts/g1_resolve_results.py --render` into a scratch copy before `build_framework_deck.py` runs, so retiring the resolver breaks the deck build path unless the seldon command is wired in there too. That path is not mentioned in Lane 1 step 5.

### 3.6 The ambiguous set is 14 names, all pre-G1

Recorded for Lane 1 step 2 so the oracle pass has its inputs: of 3,543 registered Results, 14 names resolve ambiguously under the workaround resolver — `accuracy`, `admitted_items_per_chunk`, `admitted_yield_ratio`, `atomic_facts`, `count`, `fabrication_share`, `fabrication_share_upper95`, `instrument_containment_recall`, `item_faithful_rate`, `kappa`, `precision`, `proportion`, `quarantine_rate`, `usd_per_admitted_item`. All are older Results that used `units` as an actual unit; **no `g1_*` name is ambiguous**, and no token in any document listed in §3.5 resolves to one. The byte-identity requirement in Lane 1 step 2 is therefore satisfiable trivially for the documents that matter — the ambiguity is real but currently uncited.

### 3.7 Lane 3's spec, retrieved

`a74433f8`'s description reads in full: *"G1 hygiene residue (zero spend; fold into the next G1 task, not standalone): (1) memo §3 E3 entry is a level claim (0 L2 in 196, v1 scorer) without the DD-038 caveat; its caveat differs from E5/E6 because the calibration measured the v2 scorer, not v1 — say that. (2) `usafacts_operationalization_skeleton.md` v0.2.8 introduced `{{result:}}` tokens (G1 note, κ_w); revert to the skeleton's name-only convention — that file is read unrendered by external reviewers. (memo_v1_2 RESULT §5.2, §5.3)"*

Both items are the two discrepancies the memo v1.2 RESULT reported and left; the spec has no third item. Note its own instruction — **"fold into the next G1 task, not standalone"** — which sits oddly with its appearance as a parallel lane of a standalone hygiene task. Recorded, not acted on.

## 4. What unblocks this

In order: execute `seldon/cc_tasks/2026-09-03_seldon_defect_sweep_registry_lifecycle_ontology.md` in the seldon repo; commit its RESULT and its task file (both untracked today); reinstall or re-resolve the editable `seldon` package so the new subcommands are on PATH; then re-dispatch this task. Step 0 will pass and the four lanes can run as written, with §3 above folded in — in particular the D3-before-rederive sequencing (§3.2), the resolver-to-resolver regression (§3.4), and the deck build path (§3.5).

Lanes 2 and 3 do not strictly need the new CLI and could have run today. They were **not** run: step 0 is written as a gate on the whole task, not per lane, and a machine does not decide which of its own gates to honour. If the operator wants the biblio-cron fix (Lane 2) or the G1 residue edits (Lane 3) before the seldon sweep lands, that is a one-line dispatch and they can be executed standalone — Lane 3's own spec asks to be folded into the next G1 task anyway (§3.7).

## 5. Out of scope, untouched as instructed

The four escalated calibration disagreement records; the deck draft's distribution; the `73f0aa5d` v3 backlog; the methodology document. Nothing that spends model tokens ran.
