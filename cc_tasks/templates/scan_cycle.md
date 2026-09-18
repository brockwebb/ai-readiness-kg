# CC Task — scan cycle {cycle_name}: the standing measured cycle for {period}

**Date:** {created_at}
**Project:** ai-readiness-kg
**Authored by:** the standing dispatcher, rendering `cc_tasks/templates/scan_cycle.md` under
cadence `{cadence_name}` for period `{period}`. A cycle runs when the operator asks for one,
and its date is the day it was rendered.
**Implements:** DD-060 (monthly, first Monday UTC), DN-006 decision 8 (a schedule produces a
task; it does not bypass the queue), DN-003 (a cycle's judgements go on the append-only log),
DN-004 (what a new cycle does **not** do to the published report), DN-005 §4 item 1.
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M. The measured tier's cadence is the
thing this advances: January's numbers are January's only if the January cycle ran in January.
**Fulfils:** its own ResearchTask, registered by the dispatcher when this file was rendered.
**Spend:** zero model calls. A cycle is a fetch, a judgement and a projection; nothing in it
calls a model, and a session that finds itself about to is executing the wrong task.
**Network:** hosts, under cadence {cadence_name} — the netlocs of the target list
`params.cycle.targets` binds today and no other. Robots-first through the fetcher (DD-062),
same-site by RFC 6265 §5.1.3 domain matching (DD-063), one identified client at
`params.manners.user_agent` with a reachable contact URL (DD-060), the standing rate limit in
`params.manners`, one worker, shared `link_probe`, one HEAD per link. **The instrument never
varies its identity to get a better answer** (DD-060): a refusal is recorded as a refusal, the
refused surfaces stay in the frame, and their legs return `error` — which is never `fail`
(DD-052 §6).

---

## Decisions standing for every instance of this template (operator overrides later)

1. **Nothing new is frozen and no rule changes.** This cycle runs the instrument as
   `params.yaml` binds it on the day it fires — after DD-066 that is the five host-level legs
   in `params.tier0.legs` (`A4`, `A5`, `A10`, `A11-declared`, `A12`, with `A12` a candidate
   indicator under DD-054 and in no fraction) plus the product-surface legs the rule registry
   dispatches, and `G1-D` withdrawn from `home`/`well_known` surfaces by
   `params.tier0.legs_withdrawn`. A cycle is a measurement, not an instrument change. If the
   gate shows the instrument is wrong, this task **writes no Results and reports**; the fix and
   the re-judgement are the next task's, authored from the failure.
2. **`cycle.name` is `{cycle_name}` and the target list is whatever `params.cycle.targets`
   already binds.** The name is the UTC day this file was rendered, which is the convention
   every payload path, Result suffix and `refuse_clobber` key already follows. If
   `state/{cycle_name}.json` exists, the cycle has already run today: **stop and report**,
   because a second payload under one name would destroy the evidence the re-derivation gate
   compares against (DD-041).
3. **The cycle publishes to the log, and the log is the record of every judgement** (DN-003
   decisions 1 and 6). Observations and Findings go on this cycle's own named shard as
   generation 1; a re-judgement this cycle's gate commissions is published too, before the
   RESULT, in generation order. A payload that sits in `state/` and on no shard is a gate
   failure for this task, not a housekeeping item for the next one.
4. **This task does not move the published report's snapshot, the site's published Results, or
   the abstract.** A new measured cycle is on the log and in the matrices the moment it lands;
   promoting it to the published snapshot is a DN-004 decision — it re-snapshots only when a
   number the report publishes would change, and deciding that is the Desktop OODA's, not this
   file's, until DN-005 §4 items 2 and 3 exist. The standing snapshot-successor guard
   (DN-004 decision 3) is what tells the next OODA whether a re-snapshot is owed; running it is
   §5 below, acting on it is not this task.
5. **Refusals are expected and are findings.** The hosts that answer 403 to an identified,
   robots-compliant client have done so in every cycle since 2026-09-07. Their host-level and
   flagship rows are recorded as refused and
   `scan_refusal_consecutive_measurements_{cycle_name}` continues the count. A host that has
   *stopped* refusing is a finding too, and the RESULT says so.
6. **Every verdict rests on an observation that was actually made.** `error` never means the
   product failed, and it never means the product passed: a `pass` or `fail` derived from a
   probe that was never issued is the defect family this project has now met eight times, and
   §3's clause on it is a hard stop rather than a note in the RESULT.

**Zero edits to:** shipped rule modules, `assessment/cq/*.yaml`, the target list, `params.yaml`
beyond `cycle.*`, prior Results, prior RESULTs, prior payloads, report prose, the PDF,
`publication.yaml`, the site, `framework/`, `controls.yaml`, `CLAUDE.md`, the G1 harness.

**Immutable once written. Glob `cc_tasks/{instance_stem}_ADDENDUM*.md` before starting and
again before §3** — the dispatcher checks the same glob for the supersession marker before it
launches anything (DN-006 decision 2, c3), so an addendum that lands mid-run is one nothing
else has read.

---

## 1. Pre-flight (loopback only; no federal host is contacted in this section)

1. `refuse_clobber` against **every** existing `state/scan_*.json`. Decision 2's stop applies
   here: an existing payload for `{cycle_name}` ends the task.
2. The control-fixture gate: `run.py --controls-only`. Every fixture fires, every rule returns
   its pre-registered verdict, `unknown` = 0, derived tables agree, both clocks agree.
   **Hard stop on failure** — *a cycle with zero fired controls is INVALID*, and a cycle whose
   controls disagree with their table is measuring with an instrument nobody has checked.

## 2. Run

`run.py::main` over the bound target list, the whole frame, one pass. Bodies staged, not
promoted. **Detached, logged, polled to `EXIT=` (CLAUDE.md long-running protocol).**

## 3. The gate (the one gate of this task)

Every clause is a hard stop. **A failure writes no Results, refreshes no page, and reports.**

1. Byte-identical re-derivation for this cycle **and every prior payload** (`make gate-task`
   covers the re-derivation tier; this clause is what makes running it non-optional).
2. Zero Tier C Findings outside `params.tier0.legs`; zero duplicate Finding identities across
   the rows of one host.
3. **No verdict rests on an unobserved probe.** Every `pass` and every `fail` in this cycle
   cites at least one Observation the collector actually made. Decision 6; this is the clause
   that stopped cycle 4.
4. Manners, replayed from this cycle's own log (DD-062, DD-063): every request same-site to a
   roster site key, every netloc's `robots.txt` read before its first fetch, zero off-site,
   zero robots-late, zero requests the site bound refused. Report the **request count per
   site** — the site count is the number that holds, not the netloc count.
5. Hygiene: `git status --porcelain corpus/` shows only this cycle's promoted bodies; the event
   log is append-only (`+N / -0` on every shard).
6. `make gate-task` (this cycle touches stored payloads by definition), `seldon verify`, and
   the protected-paths diff against the "zero edits to" list. Detached, logged, polled.
7. The snapshot-successor guard (DN-004 decision 3) runs and its output goes in the RESULT
   whatever it says. It refusing a *report build* is information for the next OODA; it does not
   make this cycle fail, because this cycle does not rebuild the report.

## 4. Publish and register

1. `publish.py --from state/{cycle_name}.json` then `--project`: Observations and Findings to
   this cycle's named shard, evidence promoted for exactly the digests the published
   Observations cite, then projected (DN-003 decision 4).
2. The three matrices as data under `docs/reports/` (`scan_matrix_tierA/tierC/product_{cycle_name}`).
3. The cycle's L0 Results, registered in `proposed` through `scripts/cycle_results.py` — every
   name cycle-suffixed (DD-056; a Result name binds once, AD-028). Leg rates per tier, A12 per
   tier and pooled, surfaces/unobservable/refusals, `scan_l0_product_legs_at_zero_{cycle_name}`,
   the matrices, `params_hash`, `blind_pointers` per leg where A8 applies, the per-site request
   count, and upper-95 bounds per leg at the actual n (rule of three).
4. Graph page and figures refreshed from the graph. **The report, the PDF, the site's published
   Results and the abstract are not touched** (decision 4).

## 5. Report

RESULT at `cc_tasks/{instance_stem}_RESULT.md` — the name the dispatcher's finish check
looks for, so a RESULT written anywhere else leaves this cycle `blocked` on a filename. Written
**after** the logs on disk show `EXIT=0`, never with a placeholder in it, and if the session
stopped early the first section says at which line and why.

It carries: the gate clause by clause with the log path for each; the request count per site;
what moved since the previous cycle and whether the **instrument** or the **host** moved it,
leg by leg; the refused hosts and whether any has stopped refusing; the snapshot-successor
guard's output and whether a DN-004 re-snapshot now looks owed (stated, not acted on); and
**every premise this template got wrong** — a template rendered unattended every month is
exactly the artifact whose stale premises nobody notices, so naming them is this file's own
maintenance channel.

Then `seldon cc complete`, commit, push.

**SEQUENCING:** §1.1 → §1.2 (hard stop) → glob addenda again → §2 → §3 (hard stop) → §4 → §5 →
push. This task was dispatched by the standing dispatcher (DN-006 decision 10: while
`dispatch.enabled` is true the operator does not hand-dispatch), so the commit and the push at
the end are this session's own and not somebody else's.
