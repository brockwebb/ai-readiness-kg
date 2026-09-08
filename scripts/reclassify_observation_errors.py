#!/usr/bin/env python3
"""Overlay the correct `error_class` on observations the old fallback misfiled. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2: *do not relabel them on the log; append an
`observation_error_reclassified` overlay event and project it.* An observation line is never
edited — invariant 1 — and its `obs_id` is DERIVED from `error_class` among other things, so
editing the class in place would silently re-identify the record and orphan the Findings that
cite it. The overlay says, on its face, what the class should have been and why.

**The correction re-reads the record, it does not re-fetch.** Every collector persists
`f"{type(exc).__name__}: {exc}"` into `response.error`, so the exception's type and message
both survive on the log; `scan.errors.classify_recorded_error` resolves them under the new map.
The evidence for each correction is the observation's own stored bytes.

**Two sources, one convention.** A failure is classified from whichever record names it:

* the **recorded exception text** (`response.error`), for a transport failure — this is what
  the harness-v3 pass overlaid, 93 observations that a `dns` fallback had misfiled;
* the **recorded status**, for a response that arrived — `classify_status`. This is the pass
  `cc_tasks/2026-09-07_scan_run_2.md` §1.2 adds. 266 observations carry `http_4xx` on an HTTP
  403, which the closed set now calls `refused`.

Harness-v3 reported those 266 and deliberately did not act, because `http_4xx` was the only
answer the old closed set HAD for a 403 and nothing downstream read it wrongly. Cycle 2 acts,
for a reason that only appears once there are two cycles: `error_class_counts` is a per-cycle
metric compared ACROSS cycles, and cycle 2 will file its 403s as `refused` because the
collectors now classify by status. Two conventions on one log make that comparison a
measurement of the instrument. One convention, applied by overlay, is the alternative that
edits nothing — `error_class_recorded` keeps what the collector wrote.

**No Finding moves.** Rules read `manners.unobservable_statuses` (the status), never the class,
so a 403 was already `error` rather than `fail`. The re-derivation gate proves it: the overlay
is an event, not a change to the observation line, and `obs_id` is derived from the RECORDED
class, so every stored id is untouched.

    /opt/anaconda3/bin/python3 scripts/reclassify_observation_errors.py --report
    /opt/anaconda3/bin/python3 scripts/reclassify_observation_errors.py
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from kg import eventlog                                              # noqa: E402
from scan.errors import (classify_recorded_error,                    # noqa: E402
                         classify_status)

EVENT = "observation_error_reclassified"
OBS_EVENT = "observation_recorded"

#: One entry per PASS. A pass is a source of truth about what went wrong (a recorded exception,
#: a recorded status), the task that decided to act on it, and the shard its overlay lands on.
#: Each pass gets its OWN shard for the reason every overlay here does: the shard is the unit
#: an operator reaches for, and "the 266 status-derived corrections" has to be a file rather
#: than a query. A pass is never re-run onto another pass's shard — `misfiled` is idempotent
#: across ALL overlays on the log, so a second pass never re-corrects what a first one did.
PASSES = {
    "recorded_error": {
        "batch": 34,
        "task": "cc_tasks/2026-09-07_scan_harness_v3.md",
        "reason": ("the closed set had no member for this failure when the observation was "
                   "made, so the collector's fallback filed it under the nearest available "
                   "class; scan/errors.py now names it"),
    },
    "status": {
        "batch": 36,
        "task": "cc_tasks/2026-09-07_scan_run_2.md",
        "reason": ("the host ANSWERED, and the answer was a refusal status on a "
                   "robots-permitted path; `http_4xx` was the only class the old closed set "
                   "had for it, and `refused` is what scan/errors.py now calls it. One "
                   "convention on the log, so error_class_counts compares across cycles"),
    },
}
#: The default pass, kept as a name so the module reads the same as it did before there were two.
TASK = PASSES["recorded_error"]["task"]
BATCH = PASSES["recorded_error"]["batch"]


def misfiled(pass_name: str = "recorded_error", params: dict | None = None) -> list:
    """Observations whose recorded failure resolves to a different class under the new map.

    `recorded_error` reads `response.error` — the persisted `f"{type(exc).__name__}: {exc}"` —
    and settles a TRANSPORT failure. `status` reads `response.status` and settles a response
    that ARRIVED; it needs `params`, because which statuses count as a refusal is a policy list
    (`manners.unobservable_statuses`), not a protocol constant.
    """
    if pass_name == "status" and params is None:
        raise ValueError("the `status` pass classifies against "
                         "`params.manners.unobservable_statuses` and cannot run without params")
    out = []
    for ev in eventlog.replay():
        if ev.get("event_type") != OBS_EVENT:
            continue
        # `collector_unavailable` is the RUNNER's statement about ITSELF — `run.py`'s catch-all
        # records it when a collector raised, and it writes the same
        # `f"{type(exc).__name__}: {exc}"` text a transport failure would. The three that
        # carry it are the D1 collector's `.get("status", 999)` crash on the StatCan
        # surfaces, and `collector_unavailable` is the correct class for them: the failure was
        # ours, not the network's. The map classifies what a COLLECTOR saw, so it has no
        # standing over this class and must not overwrite it.
        if ev.get("error_class") == "collector_unavailable":
            continue
        if pass_name == "status":
            # Only a response that ARRIVED, and only one whose recorded error is absent: an
            # observation carrying both a status and a transport error is the `recorded_error`
            # pass's, and two passes correcting one record would put two overlays on it with
            # nothing saying which wins.
            if (ev.get("response") or {}).get("error"):
                continue
            # An overlay CORRECTS a recorded classification. Where the collector recorded
            # none, there is nothing to correct — and here `None` is not an omission, it is a
            # deliberate statement. All 47 such records are `lighthouse`'s `invalid_route`
            # probe, which asks for a path that should not exist: its 404 IS A10's
            # measurement, and the collector passes `error_class=None` on that branch on
            # purpose (`collectors/lighthouse.py`). Backfilling a class the collector chose
            # not to record would be a claim about what the collector saw that only the
            # collector can make, and it would relabel a passing measurement a refusal.
            if ev.get("error_class") is None:
                continue
            want = classify_status((ev.get("response") or {}).get("status"), params)
        else:
            want = classify_recorded_error((ev.get("response") or {}).get("error"))
        if want and want != ev.get("error_class"):
            out.append((ev, want))
    return out


def overlaid() -> set:
    """`obs_id`s already carrying an overlay, from ANY pass. Makes this idempotent, and keeps
    a second pass from correcting a record a first pass already corrected."""
    return {ev["obs_id"] for ev in eventlog.replay() if ev.get("event_type") == EVENT}


def rows(pass_name: str = "recorded_error", params: dict | None = None) -> list:
    spec = PASSES[pass_name]
    return [{
        "event_type": EVENT,
        "obs_id": ev["obs_id"],
        "target_doc_id": ev["target_doc_id"],
        "leg": ev["leg"],
        "error_class_recorded": ev.get("error_class"),
        "error_class": want,
        "recorded_error": (ev.get("response") or {}).get("error"),
        "recorded_status": (ev.get("response") or {}).get("status"),
        "classified_from": pass_name,
        "reason": spec["reason"],
        "reclassified_by": spec["task"],
    } for ev, want in misfiled(pass_name, params)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--pass", dest="pass_name", default="status", choices=sorted(PASSES),
                    help="which source of truth to classify from (default: status, the pass "
                         "cc_tasks/2026-09-07_scan_run_2.md adds; `recorded_error` is the "
                         "harness-v3 pass and is already applied)")
    a = ap.parse_args(argv)
    from scan import load_params
    params = load_params()
    spec = PASSES[a.pass_name]
    data = rows(a.pass_name, params)
    already = overlaid()
    todo = [r for r in data if r["obs_id"] not in already]
    summary = {
        "pass": a.pass_name,
        "misfiled_observations": len(data),
        "already_overlaid": len(data) - len(todo),
        "to_overlay": len(todo),
        "moves": dict(collections.Counter(
            f"{r['error_class_recorded']} -> {r['error_class']}" for r in data)),
        "by_status": dict(collections.Counter(r["recorded_status"] for r in data)),
        "targets": dict(collections.Counter(r["target_doc_id"] for r in data)),
        "shard": f"events/batch-{spec['batch']:03d}.jsonl",
    }
    if a.report:
        print(json.dumps(summary, indent=1, default=str))
        return 0
    shard = REPO / "events" / f"batch-{spec['batch']:03d}.jsonl"
    if shard.is_file():
        for line in shard.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            # Same shard guard as before, tightened by a pass: batch 34 holds the
            # `recorded_error` overlays and must not gain the status ones, or "the 266" stops
            # being a file. A shard whose events are all this pass's is this script re-running.
            if ev.get("event_type") != EVENT:
                raise SystemExit(f"REFUSING: {shard.name} already holds events of another "
                                 f"kind; this overlay gets its own shard")
            if ev.get("classified_from", "recorded_error") != a.pass_name:
                raise SystemExit(f"REFUSING: {shard.name} holds the "
                                 f"{ev.get('classified_from', 'recorded_error')!r} pass; the "
                                 f"{a.pass_name!r} pass gets its own shard")
    for r in todo:
        eventlog.append(r, batch=spec["batch"])
    summary["written"] = len(todo)
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
