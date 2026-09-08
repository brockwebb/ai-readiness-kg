#!/usr/bin/env python3
"""Annotate the scan-surface `conversion_gap` events whose tasks were withdrawn. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_run_2.md` §1.3. Twenty-two of the twenty-six scan surfaces
admitted on 2026-09-07 tripped DD-030's thin-extent gate, and each minted a `conversion_gap`
event plus the ResearchTask that IS the improvement launch (`kg/ingest/gate.py`). The launches
were wrong — not the gate, the premise under it. A scan surface's extent IS the measurement:
A10 exists to catch a page with no document behind it, and B3 scores whether the methodology
is legible without JavaScript. A thin one is a finding, never a substrate to re-acquire.

`cc_tasks/2026-09-07_framework_projection_repair.md` withdrew the twenty-two ResearchTasks by
hand, and `cc_tasks/2026-09-07_scan_harness_v3.md` §1.5 stopped the gate firing on a scan
surface at all (`manifest._GATE_EXEMPT_PURPOSES`). What neither did is say so ON THE LOG. The
gap events are still there, still claiming twenty-two open gaps, and the withdrawal lives only
in the Seldon graph — which is a projection, and projections are rebuilt.

Same shape as `finding_evidence_unretained` (`scripts/annotate_orphan_findings.py`): the gap
line is never edited (invariant 1), and an append-only overlay carries the withdrawal, the
ResearchTask it withdrew, and the task that decided it.

    /opt/anaconda3/bin/python3 scripts/annotate_withdrawn_conversion_gaps.py --report
    /opt/anaconda3/bin/python3 scripts/annotate_withdrawn_conversion_gaps.py
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import eventlog                                              # noqa: E402
from kg.ingest.gate import GAP_EVENT                                 # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_run_2.md"
#: The task that actually withdrew the ResearchTasks; cited on every event so the overlay
#: names the act it records rather than only the act that wrote it down.
WITHDRAWN_BY = "cc_tasks/2026-09-07_framework_projection_repair.md"
#: Its own shard, checked to be free before use.
BATCH = 37
EVENT = "conversion_gap_withdrawn"
#: The prefix `scripts/admit_scan_targets.py` mints, read the same way
#: `scripts/declare_scan_surface_purpose.py` reads it — a typed list of doc_ids would be a
#: second definition of "which documents are scan surfaces" and the stale one would win.
PREFIX = "scan-"
REASON = ("a scan surface's extent IS the measurement (A10, B3), so DD-030's convertibility "
          "gate does not apply to it; the ResearchTask this gap launched was withdrawn and "
          "manifest._GATE_EXEMPT_PURPOSES now keeps the gate from firing on one at all")


def gaps() -> list:
    """Scan-surface `conversion_gap` events, in log order."""
    return [ev for ev in eventlog.replay()
            if ev.get("event_type") == GAP_EVENT
            and str(ev.get("doc_id", "")).startswith(PREFIX)]


def annotated() -> set:
    """`event_id`s of gap events already carrying an overlay. Makes this idempotent.

    Keyed on the GAP EVENT's id, not the doc_id: a document may legitimately have more than
    one gap event over its life, and only the ones this task withdrew are annotated.
    """
    return {ev["gap_event_id"] for ev in eventlog.replay() if ev.get("event_type") == EVENT}


def rows() -> list:
    done = annotated()
    return [{
        "event_type": EVENT,
        "gap_event_id": g["event_id"],
        "doc_id": g["doc_id"],
        "gap_class": g["gap_class"],
        "research_task_id": g.get("research_task_id"),
        "research_task_state": "withdrawn",
        "withdrawn_by": WITHDRAWN_BY,
        "reason": REASON,
        "annotated_by": TASK,
    } for g in gaps() if g["event_id"] not in done]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    all_gaps, todo = gaps(), rows()
    summary = {
        "scan_surface_conversion_gaps": len(all_gaps),
        "already_annotated": len(all_gaps) - len(todo),
        "to_annotate": len(todo),
        "gap_classes": dict(collections.Counter(g["gap_class"] for g in all_gaps)),
        "without_research_task": sum(1 for g in all_gaps if not g.get("research_task_id")),
        "shard": f"events/batch-{BATCH:03d}.jsonl",
    }
    if a.report:
        print(json.dumps({**summary, "doc_ids": sorted(g["doc_id"] for g in todo)}, indent=1))
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
