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

**Scope: transport errors only.** 266 observations carry `error_class: http_4xx` on an HTTP 403
and would be `refused` under the new map. They are NOT overlaid here: `http_4xx` was the only
answer the old closed set had for a 403, so it was not a misfiling in the way `dns` for a
connection reset was; and the rules already read that refusal correctly through
`manners.unobservable_statuses`, so nothing downstream is wrong today. The count is reported so
the next cycle's task can decide whether the log should carry one convention or two.

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
from scan.errors import classify_recorded_error                      # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_harness_v3.md"
#: Its own shard, checked to be free before use.
BATCH = 34
EVENT = "observation_error_reclassified"
OBS_EVENT = "observation_recorded"


def misfiled() -> list:
    """Observations whose recorded transport error resolves to a different class now."""
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
        text = (ev.get("response") or {}).get("error")
        want = classify_recorded_error(text)
        if want and want != ev.get("error_class"):
            out.append((ev, want))
    return out


def status_derived_divergence(params: dict) -> dict:
    """Reported, never written: observations whose STATUS-derived class would move. See the
    module docstring for why these are out of scope."""
    refusal = tuple((params.get("manners") or {}).get("unobservable_statuses") or ())
    n = collections.Counter()
    for ev in eventlog.replay():
        if ev.get("event_type") != OBS_EVENT:
            continue
        st = (ev.get("response") or {}).get("status")
        if ev.get("error_class") == "http_4xx" and st in refusal:
            n[st] += 1
    return {"total": sum(n.values()), "by_status": dict(n)}


def overlaid() -> set:
    """`obs_id`s already carrying an overlay. Makes this idempotent."""
    return {ev["obs_id"] for ev in eventlog.replay() if ev.get("event_type") == EVENT}


def rows() -> list:
    return [{
        "event_type": EVENT,
        "obs_id": ev["obs_id"],
        "target_doc_id": ev["target_doc_id"],
        "leg": ev["leg"],
        "error_class_recorded": ev.get("error_class"),
        "error_class": want,
        "recorded_error": (ev.get("response") or {}).get("error"),
        "reason": ("the closed set had no member for this failure when the observation was "
                   "made, so the collector's fallback filed it under the nearest available "
                   "class; scan/errors.py now names it"),
        "reclassified_by": TASK,
    } for ev, want in misfiled()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    from scan import load_params
    data = rows()
    already = overlaid()
    todo = [r for r in data if r["obs_id"] not in already]
    summary = {
        "misfiled_observations": len(data),
        "already_overlaid": len(data) - len(todo),
        "to_overlay": len(todo),
        "moves": dict(collections.Counter(
            f"{r['error_class_recorded']} -> {r['error_class']}" for r in data)),
        "targets": dict(collections.Counter(r["target_doc_id"] for r in data)),
        "status_derived_divergence_NOT_overlaid": status_derived_divergence(load_params()),
        "shard": f"events/batch-{BATCH:03d}.jsonl",
    }
    if a.report:
        print(json.dumps(summary, indent=1))
        return 0
    shard = REPO / "events" / f"batch-{BATCH:03d}.jsonl"
    if shard.is_file():
        for line in shard.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("event_type") != EVENT:
                raise SystemExit(f"REFUSING: {shard.name} already holds events of another "
                                 f"kind; this overlay gets its own shard")
    for r in todo:
        eventlog.append(r, batch=BATCH)
    summary["written"] = len(todo)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
