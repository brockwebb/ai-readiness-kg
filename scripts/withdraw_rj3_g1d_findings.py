#!/usr/bin/env python3
"""Withdraw, on the log, the 22 `_rj3` G1-D Findings no later judgement reaches. **Zero spend,
no network. Nothing is deleted; no Finding line is edited.**

`cc_tasks/2026-09-19_resnapshot_rj4.md` decision 5, closing
`cc_tasks/2026-09-18_rejudge_seven_legs_RESULT.md` §5 premise 5 and "Open" item 4.

**What is wrong without this.** DD-066 withdrew the G1-D leg from the 16 `home` surfaces and the
6 Tier C surfaces: the surface cannot carry the property. `scan_2026-09-10_rj4` therefore judges
G1-D on the flagships only (DD-067 §3), and the 22 G1-D Findings `scan_2026-09-10_rj3` recorded
on those surfaces have no successor. DD-065's rule, "no successor is current", then calls them
current for ever — "current" meaning "nothing superseded it" where a reader of `Finding.current`
takes it to mean "the instrument's answer today".

**What this writes.** One `finding_withdrawn` event per such Finding, on the shard the Finding
already sits on (`publish.shard_for`, the rule every overlay of a cycle follows), carrying the
Finding's identity, its leg and surface, the reason citing DD-066, and this task. The projection
reads the overlay and sets `withdrawn` / `withdrawn_reason`, and `current` becomes
`NOT withdrawn AND no successor` (`scan/publish.py::project`).

**Selected by construction, never by list.** A Finding is withdrawn here exactly when it is a
G1-D Finding of `_rj3`, the successor judgement `_rj4` holds no Finding on its (surface, leg),
and the frame `_rj4` was judged under gives that surface no G1-D leg (`surface_legs` on the
`_rj4` payload). All three are checked, and the count must be the 22 DD-067 §3 names or nothing
is written.

    /opt/anaconda3/bin/python3 scripts/withdraw_rj3_g1d_findings.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

TASK = "cc_tasks/2026-09-19_resnapshot_rj4.md"
CYCLE = "scan_2026-09-10_rj3"
SUCCESSOR = "scan_2026-09-10_rj4"
LEG = "G1-D"
#: DD-067 §3's count: 16 `home` surfaces and 6 Tier C surfaces. The selection below derives the
#: set; this is the stop condition that it derived the set the decision record names.
EXPECTED = 22
REASON = ("G1-D withdrawn from this surface, DD-066: the surface cannot carry the property. "
          "The successor judgement scan_2026-09-10_rj4 is framed without G1-D here (DD-067 §3), "
          "so nothing supersedes this Finding; it stands as measured and is not the "
          "instrument's answer today.")


def payload(cycle: str) -> dict:
    return json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))


def select() -> list:
    """The `_rj3` G1-D Findings with no `_rj4` counterpart on a surface `_rj4` frames without
    G1-D. Refuses unless there are exactly `EXPECTED`."""
    old, new = payload(CYCLE), payload(SUCCESSOR)
    judged_now = {(f["target_doc_id"], f["leg"]) for f in new["findings_detail"]}
    legs_now = new.get("surface_legs")
    if not legs_now:
        raise SystemExit(f"FATAL: {SUCCESSOR} records no `surface_legs`; which surfaces its "
                         f"frame gives G1-D cannot be read, and nothing is withdrawn on a guess")
    out = []
    for f in old["findings_detail"]:
        if f["leg"] != LEG or (f["target_doc_id"], LEG) in judged_now:
            continue
        if LEG in (legs_now.get(f["target_doc_id"]) or []):
            raise SystemExit(f"FATAL: {f['target_doc_id']} carries G1-D in {SUCCESSOR}'s frame "
                             f"and {SUCCESSOR} has no G1-D Finding on it; that is a missing "
                             f"judgement, not a withdrawal")
        out.append(f)
    if len(out) != EXPECTED:
        raise SystemExit(f"FATAL: {len(out)} Findings selected, DD-067 §3 names {EXPECTED}; "
                         f"nothing is written")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    from kg import eventlog
    from scan import publish
    chosen = select()
    ids = [f["finding_id"] for f in chosen]
    log = list(eventlog.replay())
    on_log = {e["finding_id"] for e in log if e.get("event_type") == publish.FIND_EVENT}
    missing = [i for i in ids if i not in on_log]
    if missing:
        raise SystemExit(f"FATAL: {len(missing)} selected Finding(s) are not on the log: "
                         f"{missing[:3]}")
    superseded = {e["supersedes_finding_id"] for e in log
                  if e.get("event_type") == publish.SUPERSEDES_EVENT}
    if set(ids) & superseded:
        raise SystemExit("FATAL: a selected Finding has a successor on the log; a superseded "
                         "Finding is not withdrawn, it is replaced")
    already = {e["finding_id"] for e in log
               if e.get("event_type") == publish.WITHDRAWN_EVENT}
    where = publish.shard_for(CYCLE, ids)
    written = 0
    for f in chosen:
        if f["finding_id"] in already:
            continue
        if not a.dry_run:
            eventlog.append({"event_type": publish.WITHDRAWN_EVENT,
                             "finding_id": f["finding_id"], "cycle": CYCLE, "leg": f["leg"],
                             "rule_id": f["rule_id"], "target_doc_id": f["target_doc_id"],
                             "verdict": f["verdict"], "not_judged_by": SUCCESSOR,
                             "reason": REASON, "decision": "DD-066", "task": TASK}, **where)
        written += 1
    print(json.dumps({"selected": len(chosen), "already_withdrawn": len(already & set(ids)),
                      "written": written, "dry_run": a.dry_run,
                      "shard": publish.shard_name(where),
                      "surfaces": sorted(f["target_doc_id"] for f in chosen)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
