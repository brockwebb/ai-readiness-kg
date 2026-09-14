# RESULT — fourteen re-judgements on the log, 6,797 supersession edges, and the published report is one generation behind

**Task:** `cc_tasks/2026-09-14_rejudgements_on_the_log.md`, implementing
`docs/design/2026-09-14_DN-003_event_log_and_rejudgements.md` decisions 1 to 6.
**No addendum exists** — `cc_tasks/2026-09-14_rejudgements_on_the_log_ADDENDUM*.md` globbed before
starting and again before §3, both times `no matches found`
(`logs/rj_addendum_glob_start.log`, `logs/rj_addendum_glob_pre_s3.log`).
**Date:** 2026-09-14. **Spend: zero model calls. Network: none** — no host was contacted, no
evidence was promoted, and every payload published was already on disk. The only remote operation
is the `git push` §4 orders.

## THE GATE: PASS

| clause (§3) | result | log |
|---|---|---|
| §1 stop — no re-judged payload cites an `obs_id` absent from the log | **PASS — 0 missing across all 14**, `stop: []` | `logs/rj_preflight.log` |
| re-judged cycles on the log, in generation order | **PASS — 14 of 14**, gen 1→4, every predecessor before its successor | `logs/rj_publish.log`, `state/rejudgements_on_the_log_2026-09-14.json` |
| 0 orphan Findings among them | **PASS — 0**; every cited `obs_id` resolves to its source cycle | `logs/rj_newtests.log` |
| `SUPERSEDES` count equals the paired count | **PASS — 6,797 = 6,797**, `supersedes_unresolved: 0`, 0 unpaired | `logs/rj_results_after.log` |
| the report snapshot's tagged Findings current | **FALSE, and the premise is wrong — see §2** | `logs/rj_newtests.log` |
| every shard append-only (byte-prefix on every pre-existing shard) | **PASS — 46 byte-identical, 2 appended to, 0 rewritten**; `shards_that_shrank: []` | `logs/rj_protected.log` |
| projection round-trip green | **PASS** (`test_framework_projection_roundtrip.py`, inside both tiers) | `logs/rj_gate_task.log` |
| 22 of 22 payloads re-derive byte-identically | **PASS — 22 of 22**, 7.17 s | `logs/rj_gate_task.log` |
| both invariant readings 0 across every re-judged payload | **PASS — 0 and 0** on all 14, under harness-5, product-only and all-rules | `logs/rj_newtests.log` |
| no Result registered or moved (count before and after) | **PASS — 7,261 live / 7,262 total, 59 published, 1 superseded**, both times | `logs/rj_results_before.log`, `logs/rj_results_after.log` |
| `make gate-task` | **PASS — 2,155 passed, 17 skipped, 25 deselected, 12 xfailed, 392.09 s**, then 22 of 22 re-derive in 7.17 s | `logs/rj_gate_task.log` |
| `make guards` | **PASS — 25 passed, 15.66 s** | `logs/rj_guards.log` |
| `make gate-full` (detached, logged, polled to EXIT) | **PASS — 2,180 passed, 17 skipped, 12 xfailed, 1,289.80 s (21:29)** | `logs/suite.log` |
| `seldon verify` | **PASS — all checks passed, 34,652 events readable** | `logs/rj_verify_seldon.log` |
| protected paths | **PASS** | `logs/rj_protected.log` |

Every log carries its own `EXIT=0` and all of them were written before this file was. The one
clause that does not pass is a wrong premise in the task's own gate, and it is wrong in a way the
task's other two decisions make unavoidable; §2 is the whole of it.

**Rehearsed before written.** The log is append-only, so a run that failed halfway would leave
events nothing can remove. The entire publication was driven once against a *copy* of
`events/` and only the counts were kept (`logs/rj_rehearse.log`); the real run reproduced them
exactly — 6,041 `finding_derived`, 6,797 `finding_supersedes`, 0 unpaired.

## 1. What went on the log

**Fourteen re-judged payloads, twelve of which had never been published.** `scan_2026-09-07_rj1`
and `scan_2026-09-07b_rj1` reached the log on 2026-09-08 and keep the numbered shards they own;
the other twelve are on the log for the first time, each on its own named shard.

| cycle | gen | supersedes | `finding_derived` written | `finding_supersedes` written | unpaired | shard |
|---|---|---|---|---|---|---|
| `scan_2026-09-07_rj1` | 1 | `scan_2026-09-07` | 0 (already on the log) | 352 | 0 | `events/batch-040.jsonl` |
| `scan_2026-09-07b_rj1` | 1 | `scan_2026-09-07b` | 0 (already on the log) | 404 | 0 | `events/batch-041.jsonl` |
| `scan_2026-09-09_rj1` | 1 | `scan_2026-09-09` | 634 | 634 | 0 | `events/cycle-scan_2026-09-09_rj1.jsonl` |
| `scan_2026-09-10_rj1` | 1 | `scan_2026-09-10` | 739 | 739 | 0 | `events/cycle-scan_2026-09-10_rj1.jsonl` |
| `self_2026-09-13_rj1` | 1 | `self_2026-09-13` | 6 | 6 | 0 | `events/cycle-self_2026-09-13_rj1.jsonl` |
| `scan_2026-09-07_rj2` | 2 | `scan_2026-09-07_rj1` | 352 | 352 | 0 | `events/cycle-scan_2026-09-07_rj2.jsonl` |
| `scan_2026-09-07b_rj2` | 2 | `scan_2026-09-07b_rj1` | 404 | 404 | 0 | `events/cycle-scan_2026-09-07b_rj2.jsonl` |
| `scan_2026-09-09_rj2` | 2 | `scan_2026-09-09_rj1` | 634 | 634 | 0 | `events/cycle-scan_2026-09-09_rj2.jsonl` |
| `scan_2026-09-10_rj2` | 2 | `scan_2026-09-10_rj1` | 739 | 739 | 0 | `events/cycle-scan_2026-09-10_rj2.jsonl` |
| `scan_2026-09-07_rj3` | 3 | `scan_2026-09-07_rj2` | 352 | 352 | 0 | `events/cycle-scan_2026-09-07_rj3.jsonl` |
| `scan_2026-09-07b_rj3` | 3 | `scan_2026-09-07b_rj2` | 404 | 404 | 0 | `events/cycle-scan_2026-09-07b_rj3.jsonl` |
| `scan_2026-09-09_rj3` | 3 | `scan_2026-09-09_rj2` | 634 | 634 | 0 | `events/cycle-scan_2026-09-09_rj3.jsonl` |
| `scan_2026-09-10_rj3` | 3 | `scan_2026-09-10_rj2` | 739 | 739 | 0 | `events/cycle-scan_2026-09-10_rj3.jsonl` |
| `scan_2026-09-07b_rj4` | 4 | `scan_2026-09-07b_rj3` | 404 | 404 | 0 | `events/cycle-scan_2026-09-07b_rj4.jsonl` |
| **total** | | | **6,041** | **6,797** | **0** | 12 new shards + 2 appended |

**Not one Observation was written.** `observation_events_written` is 0 for all fourteen, which is
what makes the whole operation legitimate: the evidence was already on the log and only the
judgement is new (DN-003 decision 2).

**The projection, before and after.** `publish.py --project` ran after each cycle, so the graph was
never a generation behind the log during the run; the numbers below are the fourteenth and final
projection.

| | before | after |
|---|---|---|
| Observations | 11,332 | 11,332 |
| Findings | 4,296 | **10,337** |
| `SUPPORTS` | 17,276 | 46,876 |
| `SUPERSEDES` | — (the type did not exist) | **6,797**, 0 unresolved |
| Findings current / superseded | — | **3,540 / 6,797** |
| Findings with no `SUPPORTS` and no annotation | 0 | **0** |
| Results (live / total) | 7,261 / 7,262 | **7,261 / 7,262** |

The longest supersession chain is **4** edges (cycle 2: measured → rj1 → rj2 → rj3 → rj4). Of the
3,540 current Findings, **2,135 are re-judged** — exactly the generation-10 total
`2026-09-13_rule_a12_v3_RESULT.md` reports, arrived at here from the graph rather than from that
file — and 1,405 are pre-DN-003 events that carry no `cycle` field.

The event log now holds **138,933 events across 47 shards**, of which 10,337 are `finding_derived`,
11,332 `observation_recorded` and 6,797 `finding_supersedes`. The publication run took
**3 h 46 m** wall clock, almost all of it in the fourteen full projections.

## 2. The gate clause that is false, and why it had to be

**§3 asks that "the report snapshot's tagged Findings [be] current". They are not, and the same
task's decisions 1 and 5 are why.**

`docs/reports/publication.yaml` names `scan_2026-09-10_rj2` as the published report's snapshot, and
33 of the report's 59 tagged Results compute from that cycle's matrix. Generation 10 judged the
same evidence again on 2026-09-13 as `scan_2026-09-10_rj3` and nothing republished. Decision 1 says
every judgement the project asserts goes on the log and decision 5 says they go on in generation
order — so rj3 follows rj2, and supersession then says what is true: **all 739 Findings of the
report's snapshot have exactly one successor, and every one of them is in
`scan_2026-09-10_rj3`.** A gate clause asking for the opposite cannot be satisfied without
withholding the newest generation, which is the exact condition DN-003 exists to end.

So the assertion in `tests/test_rejudgements_on_the_log.py` is the true, stronger one:
`f.current` is 0 across the snapshot, and the successor cycle is `scan_2026-09-10_rj3` for all 739
— by one generation, named. Before this task the graph could not say any of that, because rj2 and
rj3 were both absent from the log. **The published report is one generation behind the instrument,
and that is now a query rather than a sentence in a RESULT.** Nothing here republishes it: no
Result moved, `docs/` did not move, and deciding whether to re-snapshot the report is the next
task's question, not this one's.

## 3. Every premise the task or DN-003 got wrong

**(a) Seventeen re-judgements — there are fourteen.** Both the task title and §1 say seventeen.
`state/` holds fourteen payloads for which `publish.is_rejudgement` is true, which is also what
`PRIOR_CYCLES` in `tests/test_scan_harness_v4.py` implies (22 payloads, 8 measured). Twelve were
unpublished and two were already on the log. The number is now asserted from the directory rather
than restated (`test_the_set_of_rejudged_payloads_is_the_one_this_task_published`).

**(b) "The `rejudgement_diff` records already on disk are the source of the pairing" — they cannot
be.** A diff is not a chain. `state/rejudgement_diff_2026-09-10.json` pairs
`scan_2026-09-07b_rj2` with the **measured** cycle `scan_2026-09-07b`, although
`scan_2026-09-07b_rj1` had already been published — that task's question was "what did the
harness-v5 reading change about the measurement" — and its cycle names carry a `.json` suffix the
other two records do not. Worse, a diff lists only what MOVED, so pairing from `moves` would link
the 14 to 19 Findings per cycle whose verdict or sentence changed and leave every unchanged
judgement looking current at two generations at once. The chain is derived from the names instead —
`_rjN` replaces `_rj(N-1)`, `_rj1` replaces the measurement — which is the predecessor doctrine
`scripts/rejudge_gen9.py` and `scripts/rejudge_gen10.py` already state, and it agrees with the diff
records for 11 of the 12 pairs they cover.

**(c) DN-003 decision 4's shard name was invisible to the replay.** `events/cycle-<name>.jsonl` is
the right name and `kg.eventlog.replay()` could not see it: it globbed `batch-*.jsonl` and
full-matched `batch-(\d+)`. Writing the twelve cycles to cycle shards without touching `eventlog`
would have put 12,838 events on disk that no projection, gate or monitor would ever read — the
worst shape a defect in an append-only log can take, because it looks like success. `eventlog` now
knows cycle shards (`_shard_path(cycle=...)`, `append(cycle=...)`, `shards()`), replays them by
default after the numbered batches, and refuses a cycle shard that is also tagged. Asserted in
`test_a_named_cycle_shard_is_replayed_by_default` and `test_a_cycle_shard_is_not_a_tagged_shard`.

**(d) DN-003 decision 2 names `source_cycle`; no payload has that field.** Every re-judged payload
on disk carries `cycle_kind: "rejudged"` and `derived_from`, written by `rederive.rejudge` since
2026-09-08, and the payloads are immutable. `publish.is_rejudgement` and `source_cycle_of` read
both spellings; `supersedes` and `generation` do not exist on any payload at all and are derived
from the cycle name, which is what "derived from the chain and generation, not typed" required
anyway.

**(e) Decision 5's expected `docs/data/index.json` change does not happen.** The clause is
conditional — "the event-log digest does [move] *if the site publishes one*" — and the site does
not: `index.json` hashes `framework/ai_readiness_framework.json` and `corpus/manifest.json` and
nothing else. So `docs/` moves on **no published file**: no report, no PDF, no matrix, no framework
copy, no manifest, no sitemap, no `llms.txt`, no `robots.txt`, no citation file. The site is not
rebuilt. `scripts/check_protected_rejudgements.sh` checks `docs/` whole rather than field by field,
which is the stronger check the corrected premise allows.

**(f) One thing the task could not have known about its own shard rule.**
`state/scan_2026-09-07b_rj2.json` says `"cycle": "scan_2026-09-07b_rj1"` — a recorded defect
(`2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §8) in an immutable payload. Naming the shard from the
`cycle` field would have put cycle 2's second judgement into a file named after its first.
`publish.cycle_of` takes the name from the payload's **file stem**, which is what `state/`, the
matrices, the figures, `PRIOR_CYCLES` and every RESULT table already use, and carries the
disagreement onto the events as `cycle_recorded_on_payload` rather than choosing silently between
the two names.

## 4. The defect found on the way, which would have deleted the working tree

**`publish.promote_evidence` ends with `shutil.rmtree(staging)`, and for a re-judged payload
`staging` resolved to the repository root.** A re-judgement has no `evidence_root` — it fetched
nothing — so `Path(payload.get("evidence_root") or "")` is `Path("")`, which is `.`, and
`REPO / Path(".")` is `/Users/brock/GitHub/ai-readiness-kg`. `cited` is empty, so the loop and the
`missing` refusal both pass, and the last four lines of the function delete the repository.

It never fired because the only two re-judgements ever published were published with
`--no-promote` — a flag a human had to remember was the entire distance between
`publish.py --from state/<any _rj>.json` and losing the working tree. Two locks now:
`main` refuses promotion for a re-judgement outright (DN-003 decision 2 is the rule; this is where
it binds), and `promote_evidence` itself refuses an absent or repo-root staging path, which is the
lock that holds for a caller reaching the function directly. Both asserted
(`test_promote_evidence_refuses_a_payload_with_no_staging_root`,
`test_a_rejudgement_is_published_without_promotion`).

## 5. The census, per cycle kind (decision 4)

`publish.py --census` reads the log and touches no database. Each Finding is attributed by its
event's own `cycle` field where it has one, by the stored payload otherwise, and `unattributed`
where neither can answer — never guessed.

| kind | cycles | Findings | `findings_evidence_unretained` | orphan Findings | unannotated orphans |
|---|---|---|---|---|---|
| `measured` | 5 | 2,775 | 0 | **0** | 0 |
| `self` | 1 | 135 | 0 | **0** | 0 |
| `rejudged` | 14 | 6,797 | 0 | **0** | 0 |
| `unattributed` | 1 | 630 | 120 | **120** | **0** |
| **total** | | **10,337** | **120** | **120** | **0** |

**The 120 stay 120** — the 2026-09-06 scaffold's control Findings, annotated as unretained rather
than deleted. Splitting the count by kind is the point of the exercise: an orphan among the
measured Findings is that scaffold, evidence discarded before publication and admitted as gone; an
orphan among the *re-judged* Findings would be a judgement published ahead of the cycle whose
evidence it cites, which is the defect generation order exists to prevent. One number covering both
would have reported the second as normal.

The `unattributed` row is a measurement and not a shrug: 630 Findings on `batch-029.jsonl` under
three `params_hash` values, two of which match no committed revision of `params.yaml`
(`scripts/annotate_orphan_findings.py --report` reached the same conclusion from the other side).
Their payload did not survive, so no cycle name can be recovered, and the census says so.

## 6. What changed, and what was verified where

**Code.** `kg/eventlog.py` (cycle shards, `shards()`), `assessment/harness/scan/publish.py` (the
re-judgement shape, its three refusals, `shard_for` in place of the deleted `CYCLE_BATCH` /
`batch_for`, `write_supersession`, the `SUPERSEDES` projection and `Finding.current`, the census,
the promotion refusals, `Finding.cycle`/`cycle_kind`/`generation` on the node),
`tests/conftest.py` (the real-log write guard passes `cycle=` through),
`scripts/publish_rejudgements.py` (new), `scripts/check_protected_rejudgements.sh` (new),
`tests/test_rejudgements_on_the_log.py` (new, **109 tests, all passing**),
`docs/design_decisions.md` (**DD-065**, below).

**`Finding.cycle` is new and it earns its place.** `params_hash` cannot identify a cycle: four
cycles judged in one generation share one hash — generation 9 covers `scan_2026-09-07_rj2`,
`_07b_rj3`, `_09_rj2` and `_10_rj2`, the report's own snapshot — so "the Findings of this cycle" was
not a question the graph could answer. It is null for every event written before DN-003 and is
deliberately **not** backfilled from `state/`: the projection is a function of the log, and a
property invented at projection time out of a file beside it is the convention DN-003 decision 3
replaced with an edge. The census answers for the older cycles, from the payloads, and labels which
is which.

**The projection is now independent of shard order.** Cycle shards sort by name, so the old
guarantee — that a measured cycle always got a lower batch number than the re-judgement citing its
Observations — is gone. `project()` buffers the 10,337 Finding events and writes them after the
Observations of the same replay, which costs nothing measurable and makes the property hold
outright rather than by arithmetic coincidence.

**DD-065 was added.** DN-003 decision 4 changes the sharding *unit* for assessment cycles, and
DD-008 shards by ingest batch; a decision that partly supersedes another is not left implicit in a
design note. DD-065 records all five decisions, names the prior art (event sourcing's corrected
read model; bitemporality for "as of which assertion"), and says which parts of DD-008 still stand.

**Logs, so no number here has to be trusted from the summary.**

```
logs/rj_addendum_glob_start.log      addendum glob, before starting        no matches
logs/rj_addendum_glob_pre_s3.log     addendum glob, before §3              no matches
logs/rj_project_baseline.log         the projection BEFORE the task        EXIT=0
logs/rj_preflight.log                §1, dry run, 14 payloads, stop: []    EXIT=0
logs/rj_rehearse.log                 the whole run against a COPY          EXIT=0
logs/rj_gate_fast_prepublish.log     fast tier before writing anything     EXIT=0  2,046 passed / 390.85 s
logs/rj_publish.log                  the publication, 14 cycles            EXIT=0
logs/rj_newtests.log                 the new test file                     EXIT=0  109 passed / 11.05 s
logs/rj_gate_task.log                make gate-task + 22 of 22 re-derive   EXIT=0  2,155 passed / 392.09 s
logs/rj_guards.log                   make guards                           EXIT=0  25 passed / 15.66 s
logs/suite.log                       make gate-full, detached and polled   EXIT=0  2,180 passed / 1,289.80 s
logs/rj_verify_seldon.log            seldon verify                         EXIT=0  all checks passed
logs/rj_protected.log                protected paths                       EXIT=0  PASS
logs/rj_results_before.log           Results before                        EXIT=0  7,261 / 7,262
logs/rj_results_after.log            Results after                         EXIT=0  7,261 / 7,262
state/rejudgements_on_the_log_2026-09-14.json   the publication record, with every shard's bytes and sha256 before and after
```

**The fast tier was run BEFORE anything was written** (2,046 passed, 390.85 s) precisely because
the changes it covers — `eventlog`, `conftest`, `publish` — are the ones that would have made an
irreversible write wrong. Nothing was appended to the log until it was green.

## 7. Open, for the next OODA

1. **The report is one generation behind and now provably so.** §2. The decision the next task
   owes is whether to re-snapshot the report on `scan_2026-09-10_rj3` — which moves 33 tagged
   Results' provenance and the published matrices — or to record, on the report itself, that its
   snapshot is superseded and by what. This is a publication decision about bytes that go out under
   the operator's name, so it is stated here and not taken.
2. **DN-003 decision 6 is not yet enforced by anything.** "A re-judged payload in `state/` and not
   on the log is a gate failure for that task" is true of this task's own gate and of no other. The
   cheap form is a standing test — every payload in `state/` for which `is_rejudgement` holds has
   its Findings on the log — which would have failed continuously from 2026-09-10 to today. It
   belongs in `make guards`, since it guards exactly the incident this task cleaned up.
3. **`state/scan_2026-09-07b_rj2.json` still names itself `_rj1`.** Carried on the events as
   `cycle_recorded_on_payload` rather than corrected (§3f). Nothing depends on it now; it remains a
   thing a reader will trip over once.
4. **Fourteen full projections cost 3 h 46 m** for an end state identical to one. The per-cycle
   projection is what the task ordered and it is the right default for a live cadence, but a
   batch publication of N cycles does N resets of the same labels. If a future task publishes a
   comparable backlog, `--project` once at the end is the same graph for a fourteenth of the wall
   clock; a batched-Cypher projection would fix it for everyone.
