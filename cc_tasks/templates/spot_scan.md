# CC Task — spot cycle {cycle_name}: {target} measured again, on request

**Date:** {created_at}
**Project:** ai-readiness-kg
**Authored by:** `scripts/render_spot_scan.py --target {target}`, rendering
`cc_tasks/templates/spot_scan.md`. A spot cycle runs when a publisher asks to see its fixes
measured; it is requested, never scheduled, and its date is the day it was rendered.
**Implements:** `cc_tasks/2026-09-19_spot_scan.md` decisions 1 to 3 (a spot is a first-class
measurement of the bodies it names and never stands in for the frame), DD-041 (byte-identical
re-derivation), DD-059 (Tier C stays out of product legs), DD-066 (the frame gives each surface
its legs), DN-003 (a cycle's judgements go on the append-only log), DN-004 (the report's
snapshot is a decision, not a side effect).
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M, per body. The measured tier for one
publisher: the answer to "we fixed it — does the instrument see it now".
**Fulfils:** its own ResearchTask, registered when this file was rendered.
**Spend:** zero model calls. A spot cycle is a fetch, a judgement and a projection; nothing in it
calls a model, and a session that finds itself about to is executing the wrong task.
**Network:** allowlist: {network_hosts}
These are the netlocs of {target}'s rows on the target list `params.cycle.targets` binds today, plus 127.0.0.1 for the control fixtures, and no other. Robots-first through the fetcher (DD-062), same-site by RFC 6265 §5.1.3 domain matching (DD-063), one identified client at `params.manners.user_agent`, the standing rate limit in `params.manners`, one worker. **The instrument never varies its identity to get a better answer** (DD-060): a refusal is recorded as a refusal and its legs return `error`, which is never `fail` (DD-052 §6).

---

## Decisions standing for every instance of this template (operator overrides later)

1. **Nothing new is frozen and no rule changes.** The spot runs the instrument as `params.yaml`
   binds it on the day it fires, over {target}'s surfaces only: `run.py --target {target}`
   keeps exactly the rows of the frame whose `agency` is {target}, each with the legs the frame
   gives it, controls first. A spot is a measurement, not an instrument change. If the gate
   shows the instrument is wrong, this task **writes no Results and reports**.
2. **The cycle's name is `{cycle_name}`**, derived by `scan.spot.spot_name`, never `scan_…`.
   If `state/{cycle_name}.json` exists, a spot of {target} already ran today: **stop and report**
   — a second one is a second cycle and takes DD-041's rerun letter (`--rerun b`).
3. **It publishes to the log beside the cycle of record and replaces nothing.** Observations and
   Findings go on `events/cycle-{cycle_name}.jsonl` as generation 0 of a new cycle. No
   `finding_supersedes` is written: a spot is a later measurement of one body, not a judgement
   of the frame, and `publish.py` refuses a spot and a frame cycle in one supersession pair.
4. **It is never the report's snapshot.** `docs/reports/publication.yaml:snapshot_cycle` is not
   touched, and the report, site and view builders refuse a spot named there. The views show
   the spot beside the snapshot on their own: `scripts/score.py --body {target}`, the MCP
   `get_body` and `get_prescriptions(body=…)` report {target}'s latest measurement and the
   per-leg diff against the snapshot; `get_overview` lists the spot apart from full cycles.

**Zero edits to:** shipped rule modules, the target list, `params.yaml`, prior Results, prior
RESULTs, prior payloads, report prose, the PDF, `publication.yaml`, the site, `framework/`,
`controls.yaml`, `CLAUDE.md`.

**Immutable once written. Glob `cc_tasks/{instance_stem}_ADDENDUM*.md` before starting and
again before §3.**

---

## 1. Pre-flight (loopback only)

1. `state/{cycle_name}.json` does not exist (decision 2).
2. The control gate runs first inside §2's command and stops it on failure — *a cycle with zero
   fired controls is INVALID*.

## 2. Run

`/opt/anaconda3/bin/python3 assessment/harness/scan/run.py --target {target} --task cc_tasks/{instance_stem}.md`,
detached, logged, polled to `EXIT=` (CLAUDE.md long-running protocol).

## 3. The gate (every clause a hard stop; a failure publishes nothing and reports)

1. Byte-identical re-derivation of `state/{cycle_name}.json`
   (`assessment/harness/scan/rederive.py --from state/{cycle_name}.json`).
2. **No verdict rests on an unobserved probe**: every `pass` and `fail` cites an Observation the
   collector actually made.
3. Manners, replayed from the payload: every netloc's `robots.txt` read before its first fetch,
   zero off-site requests; the request count per netloc is reported.
4. `make gate-task`, `seldon verify`, the protected-paths diff. Detached, logged, polled.

## 4. Publish and register

1. `publish.py --from state/{cycle_name}.json`, then `--project`.
2. `scripts/build_l0_matrices.py --cycle {cycle_name}`: the matrices, restricted to {target},
   under `docs/reports/`, and the spot's L0 Results registered `proposed`, every name suffixed
   `_{cycle_name}`.
3. **Nothing else moves**: not the snapshot, the report, the PDF, the site or the abstract.

## 5. Report

RESULT at `cc_tasks/{instance_stem}_RESULT.md`, written after the logs show `EXIT=0`, never
with a placeholder. It carries the gate clause by clause with log paths; the request count per
netloc; `scripts/score.py --body {target}` verbatim — what passed since the snapshot, what is
still failing, and whether the **instrument** or the **host** moved each leg; and every premise
this template got wrong. Then `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → glob addenda → §2 → §3 (hard stop) → §4 → §5 → push.
