#!/usr/bin/env python3
"""Correct a cycle's task attribution on the log, append-only. **Zero spend, no network.**

`cc_tasks/2026-09-07_scan_run_2_ADDENDUM-01.md` defect 1. `state/scan_2026-09-07b.json` carries
`"task": "cc_tasks/2026-09-07_scan_run.md"` — the CYCLE-1 task file — because `run.py` stamped
a module constant instead of naming the task that ordered the run. The measurement is fine and
the attribution is false, and a payload that misattributes itself is the kind of provenance
error that is invisible until someone cites it.

**The payload is not edited and neither is any event.** Invariant 1, and the addendum says so
explicitly. The correction is an event carrying the cycle, the task the payload claims, the
task that actually ordered it, and how the mistake happened — the same shape as
`finding_evidence_unretained` and `observation_error_reclassified`, and for the same reason:
the record of a correction belongs beside the record it corrects, not on top of it.

The code fix is `run.py --task`, so no later cycle needs one of these.

    /opt/anaconda3/bin/python3 scripts/annotate_cycle_task.py --report
    /opt/anaconda3/bin/python3 scripts/annotate_cycle_task.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import eventlog                                              # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_run_2.md"
#: Its own shard, checked to be free before use.
BATCH = 39
EVENT = "cycle_task_corrected"

#: (cycle, what the payload says, what actually ordered it). One row, and the list exists so a
#: second instance would be data rather than a second script. It is NOT read from the payload's
#: own `task` field on both sides: the point is that the field is wrong, so the correct value
#: has to come from somewhere the field cannot reach.
CORRECTIONS = [{
    "cycle": "scan_2026-09-07b",
    "task_recorded": "cc_tasks/2026-09-07_scan_run.md",
    "task": TASK,
    "reason": ("run.py stamped the module constant `TASK` onto every payload instead of the "
               "task that invoked it, so cycle 2's payload names cycle 1's order. The "
               "measurement, its params_hash and every derived id are unaffected — `task` is "
               "not an input to any of them. Fixed at the source by `run.py --task`; this "
               "event is the append-only correction for the cycle already published."),
    "payload": "state/scan_2026-09-07b.json",
    "corrected_by": TASK,
}]


def done() -> set:
    return {ev["cycle"] for ev in eventlog.replay() if ev.get("event_type") == EVENT}


def todo() -> list:
    d = done()
    return [c for c in CORRECTIONS if c["cycle"] not in d]


def check() -> list:
    """Payloads whose `task` field still disagrees with the correction. Reported, never fixed
    in place — the disagreement IS the thing the event records."""
    out = []
    for c in CORRECTIONS:
        p = REPO / c["payload"]
        if not p.is_file():
            continue
        got = json.loads(p.read_text(encoding="utf-8")).get("task")
        out.append({"payload": c["payload"], "payload_says": got,
                    "corrected_to": c["task"], "still_disagrees": got != c["task"]})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    pending = todo()
    summary = {"corrections": len(CORRECTIONS), "already_on_log": len(CORRECTIONS) - len(pending),
               "to_write": len(pending), "payloads": check(),
               "shard": f"events/batch-{BATCH:03d}.jsonl"}
    if a.report:
        print(json.dumps(summary, indent=1))
        return 0
    shard = REPO / "events" / f"batch-{BATCH:03d}.jsonl"
    if shard.is_file():
        for line in shard.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("event_type") != EVENT:
                raise SystemExit(f"REFUSING: {shard.name} already holds events of another "
                                 f"kind; this overlay gets its own shard")
    for c in pending:
        eventlog.append({"event_type": EVENT, **c}, batch=BATCH)
    summary["written"] = len(pending)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
