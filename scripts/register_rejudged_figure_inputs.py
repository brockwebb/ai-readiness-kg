#!/usr/bin/env python3
"""Figure inputs for the re-judged cycles, registering only what moved. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 1, which says nothing
unchanged is registered and figures resolve the rest through an evidence-bound fallback. The
fallback needs evidence, and for a family nobody has compared yet there is none — so this
compares, registers the difference, and writes the comparison record the fallback reads.

`scripts/register_figure_results.py` owns the three families a figure prints and no other script
may register them (its own docstring, and `scan_report.py` §273 says the same from the other
side). This script does not compute them: it asks that one for its rows and decides only which
of them are new.

Cycle 4 has no source registration at all — its gate stopped before §4 — so every one of its
figure inputs is new. That is a fact about that cycle, not an exception to the rule.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

import cycle_results                                                # noqa: E402
import register_figure_results as F                                 # noqa: E402

TASK = "cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md"
OUT = REPO / "state" / "figure_inputs_registration_2026-09-10.json"
PAIRS = [("scan_2026-09-09_rj1", "scan_2026-09-09"), ("scan_2026-09-10_rj1", None)]
WHY = ("Re-judged under harness-v5 (DD-064): a URL inside the product that robots.txt forbids is "
       "BLIND, not scope, so no verdict rests on a page the collector was never allowed to read.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    from scan.figures import load_results
    live = load_results()
    report = {}

    for cycle, origin in PAIRS:
        rows = F.rows(cycle)
        suffix = cycle_results.cycle_suffix(cycle)
        moved, unchanged = [], []
        for name, value, script, data, note in rows:
            if origin is None:
                moved.append((name, value, script, data, f"{note} {WHY} FIRST registration of "
                                                         f"this cycle. ({TASK})"))
                continue
            base = name[: -(len(suffix) + 1)]
            old_name = cycle_results.name_for(base, origin)
            old = live.get(old_name)
            if old is not None and float(old) == float(value):
                unchanged.append(name)
                continue
            moved.append((name, value, script, data,
                          f"{note} {WHY} Supersedes `{old_name}`"
                          + (f" = {old}" if old is not None else " (never registered)")
                          + f", which is unedited. ({TASK})"))
        report[cycle] = {"candidates": len(rows), "to_register": len(moved),
                         "unchanged": len(unchanged), "unchanged_names": unchanged,
                         "moved_names": [m[0] for m in moved]}
        print(f"{cycle}: {len(rows)} candidates, {len(moved)} moved, {len(unchanged)} unchanged")
        if a.dry_run:
            continue
        if moved:
            # The payload is a DataFile like any other and every cycle writes a new one.
            # `register_figure_results.main` ensures it before registering; this caller reuses
            # `register()` and so has to do the same, or `seldon result register` refuses the
            # whole batch on an unresolvable reference (AD-028) — which is the right failure at
            # the wrong moment.
            P = F.paths(cycle)
            cycle_results.ensure_data_file(
                P["payload_name"], f"state/{cycle}.json",
                f"The {cycle} payload: the {origin or 'scan_2026-09-10'} cycle's stored "
                f"Observations re-judged under harness-v5, Findings only. {WHY} ({TASK})")
            F.register(moved, cycle)
            report[cycle]["registered"] = len(moved)

    if not a.dry_run:
        OUT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
