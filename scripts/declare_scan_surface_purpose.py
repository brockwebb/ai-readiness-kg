#!/usr/bin/env python3
"""Declare the admitted scan surfaces as `purpose: scan_surface`. **Zero spend, no network.**

Task `cc_tasks/2026-09-07_scan_harness_v3.md` §1.5. `kg.manifest._convertibility_gate` now
returns early for a document admitted to be MEASURED rather than read, and `add()` carries the
purpose on new admissions — but the 26 scan surfaces admitted on 2026-09-07 predate the field.
They get it through an append-only `manifest_purpose_declared` overlay, applied over the
admission entry by `_load_entries` exactly as `content_update` is. **No batch line is edited**:
invariant 1, and the admission event is what says the document was admitted at all.

Why it matters for cycle 2: 22 of the 26 tripped DD-030's thin-extent gate on admission and
minted 22 `conversion_gap` events and 22 ResearchTasks that had to be withdrawn by hand. A
scan surface's extent IS the measurement — A10 exists to catch a page with no document behind
it, and B3 scores whether the methodology is legible without JavaScript — so a thin one is a
finding, never a substrate to re-acquire.

    /opt/anaconda3/bin/python3 scripts/declare_scan_surface_purpose.py --report
    /opt/anaconda3/bin/python3 scripts/declare_scan_surface_purpose.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import eventlog, manifest                                    # noqa: E402
from kg.ingest import gate as ingest_gate                            # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_harness_v3.md"
#: Its own shard, checked to be free before use.
BATCH = 35
PURPOSE = "scan_surface"
#: The prefix `scripts/admit_scan_targets.py` mints. Read from the ledger rather than typed as
#: a list of 26 doc_ids: a list would be a second definition of "which documents are scan
#: surfaces", and the one that went stale would be the one that mattered.
PREFIX = "scan-"
REASON = ("admitted to be MEASURED, not read: a live product surface whose extent is the "
          "measurement (A10, B3), so DD-030's convertibility gate does not apply to it")


def targets() -> list:
    """Admitted entries that are scan surfaces and do not already carry the purpose."""
    return [e for e in manifest._load_entries()
            if str(e["doc_id"]).startswith(PREFIX) and e.get("purpose") != PURPOSE]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    todo = targets()
    all_scan = [e for e in manifest._load_entries() if str(e["doc_id"]).startswith(PREFIX)]
    gaps = {d for d in ingest_gate.gaps() if str(d).startswith(PREFIX)}
    summary = {"scan_entries": len(all_scan), "to_declare": len(todo),
               "already_declared": len(all_scan) - len(todo),
               "open_conversion_gaps_on_scan_surfaces": len(gaps),
               "shard": f"events/batch-{BATCH:03d}.jsonl"}
    if a.report:
        print(json.dumps({**summary, "doc_ids": sorted(e["doc_id"] for e in todo)}, indent=1))
        return 0
    shard = REPO / "events" / f"batch-{BATCH:03d}.jsonl"
    if shard.is_file():
        for line in shard.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("event_type") != manifest._PURPOSE_DECLARED:
                raise SystemExit(f"REFUSING: {shard.name} already holds events of another kind")
    for e in todo:
        eventlog.append({"event_type": manifest._PURPOSE_DECLARED, "doc_id": e["doc_id"],
                         "purpose": PURPOSE, "reason": REASON, "task": TASK}, batch=BATCH)
    summary["written"] = len(todo)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
