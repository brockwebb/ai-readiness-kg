#!/usr/bin/env python3
"""Write the declared composite cycle of record. **No network, no model call, no re-judgement.**

`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` decision 4: "The views regenerate from
a declared composite: host checks and untouched legs from `scan_2026-09-10` rj5, the recollected
legs from this cycle. The composite is named on every matrix and in the report's methods line,
with both cycle ids." The selection rule and its refusals are `scan.composite.build`; this
script reads the two parts, writes `state/<name>.json`, and refuses to write over a composite
that already exists with different content (CLAUDE.md §11: a new version gets a new name).

    /opt/anaconda3/bin/python3 scripts/build_composite_cycle.py \
        --base scan_2026-09-10_rj5 --overlay scan_2026-10-06_recollect \
        --name scan_2026-10-06_composite_b [--withhold LEG=REASON ...] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

from scan import composite                                          # noqa: E402
from scan.rules import CURRENT, consumes                            # noqa: E402

TASK = "cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md"
STATE = REPO / "state"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--task", default=TASK)
    ap.add_argument("--withhold", action="append", default=[], metavar="LEG=REASON",
                    help="an overlay leg the composite does not take, with the reason it is "
                         "stated under (repeatable); the base's cells stand for it")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if not a.name.startswith("scan_") or a.name.startswith("spot_"):
        raise SystemExit("REFUSING: a cycle of record is named `scan_…` (cycle_results)")
    load = lambda c: json.loads((STATE / f"{c}.json").read_text(encoding="utf-8"))  # noqa: E731
    base, over = load(a.base), load(a.overlay)
    withhold = {}
    for w in a.withhold:
        leg, sep, why = w.partition("=")
        if not sep or not why.strip():
            raise SystemExit(f"REFUSING: --withhold {w!r} is not LEG=REASON")
        withhold[leg.strip()] = why.strip()
    out = composite.build(base, over, a.name, a.task,
                          lambda leg: consumes(CURRENT[leg]) if leg in CURRENT else (),
                          withhold=withhold)
    path = STATE / f"{a.name}.json"
    text = json.dumps(out, indent=1, default=str) + "\n"
    summary = {k: out[k] for k in ("cycle", "cycle_kind", "surfaces", "findings",
                                   "verdict_counts", "control_verdict")}
    summary["overlay_legs"] = out["composed_of"]["overlay"]["legs"]
    summary["findings_by_part"] = {
        c: sum(1 for f in out["findings_detail"] if composite.finding_part(out, f) == c)
        for c, _ in composite.parts(out)}
    print(json.dumps(summary, indent=1))
    if a.dry_run:
        return 0
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"REFUSING: {path.relative_to(REPO)} exists with different content; a "
                         f"different composite is a different name")
    path.write_text(text, encoding="utf-8")
    print(f"-> {path.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
