#!/usr/bin/env python3
"""Register the harness-v5 re-judgements, and ONLY what moved. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_rejudge_2_3_4.md` decisions 2 and 3.

**Decision 2's discipline is the whole point of this script.** A re-judged cycle recomputes every
Result the original registered — 142 of them for cycle 4 — and most are identical, because the
defect touched a handful of Findings on a handful of surfaces. Registering all of them would
double the registry and leave a reader unable to tell which numbers the fix actually moved. So
each candidate is compared to the value registered under the ORIGINAL cycle's name, and only a
difference is registered.

**Cycle 4 is the exception and it is not one.** Nothing was ever registered for `scan_2026-09-10`
— scan-run-4's gate stopped before §4 — so every one of its numbers is new and all of them are
registered. There is nothing to compare against, which is a fact about that cycle and not a
special case in the rule.

The old Results are NEVER touched (AD-028, and decision 2 says so explicitly). Each new Result's
description names the one it replaces and the reason, so the supersession is legible from the new
record without editing the old one.

    /opt/anaconda3/bin/python3 scripts/register_rejudged_cycles.py --dry-run
    /opt/anaconda3/bin/python3 scripts/register_rejudged_cycles.py
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
import scan_report                                                  # noqa: E402

TASK = "cc_tasks/2026-09-10_rejudge_2_3_4.md"

#: (re-judged cycle, the cycle it re-judges). The second is where the comparison values live —
#: and `None` where there are none, which is cycle 4: its gate stopped before registration.
PAIRS = [
    ("scan_2026-09-07b_rj2", "scan_2026-09-07b"),
    ("scan_2026-09-09_rj1", "scan_2026-09-09"),
    ("scan_2026-09-10_rj1", None),
]

WHY = ("Re-judged under harness-v5 (DD-064): a URL inside the product that robots.txt forbids "
       "is BLIND, not scope, so no verdict rests on a page the collector was never allowed to "
       "read. Same Observations, same evidence, a judgement layer that knows what it did not "
       "see.")


def candidates(cycle: str) -> list:
    """`[(name, value, note)]` for one re-judged cycle, through the shipped reporter."""
    payload = scan_report.load(cycle)
    tiers = scan_report.tier_of(scan_report.load_params())
    legs = scan_report.per_leg(payload, tiers, "A")
    legs_c = scan_report.per_leg(payload, tiers, "C")
    a12v = scan_report.a12(payload)
    blinds = scan_report.blind_counts(payload)
    mx = scan_report.matrix(payload, cycle, tiers, "A")
    return [(cycle_results.name_for(base, cycle), v, note)
            for base, v, note in scan_report.results(payload, legs, a12v, mx, cycle,
                                                     None, legs_c, blinds)]


def write_matrices(cycle: str) -> list:
    """The Tier A and Tier C matrix files, written the way `scan_report.main` writes them.

    The registrar names a matrix file as the DataFile every Result is computed from, so the file
    has to EXIST — a DataFile pointing at a path nobody wrote is a provenance trail that ends in
    the air, and `figures.py` reads the same file to draw the cycle. This was missed on the
    first pass here because the registration path and the file-writing path live in the same
    function in `scan_report` and only one of them was reused.
    """
    payload = scan_report.load(cycle)
    tiers = scan_report.tier_of(scan_report.load_params())
    legs = scan_report.per_leg(payload, tiers, "A")
    legs_c = scan_report.per_leg(payload, tiers, "C")
    mx = scan_report.matrix(payload, cycle, tiers, "A")
    mx_c = scan_report.matrix(payload, cycle, tiers, "C")
    suffix = cycle_results.cycle_suffix(cycle)
    a = scan_report.matrix_path(cycle)
    c = REPO / "state" / f"scan_matrix_tierc_{suffix}.json"
    a.write_text(json.dumps({**mx, "per_leg": legs, "a12": scan_report.a12(payload),
                             "requests_per_host": payload.get("requests_per_host"),
                             "error_class_counts": payload.get("error_class_counts")},
                            indent=1) + "\n", encoding="utf-8")
    c.write_text(json.dumps({**mx_c, "per_leg": legs_c,
                             "note": ("Tier C reference hosts, tier-0 legs only. In no Tier A "
                                      "denominator and on no agencies x legs matrix "
                                      "(DD-059).")}, indent=1) + "\n", encoding="utf-8")
    return [str(a.relative_to(REPO)), str(c.relative_to(REPO))]


def registered() -> dict:
    from scan.figures import load_results
    return load_results()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    try:
        live = registered()
    except Exception as exc:                                        # noqa: BLE001
        raise SystemExit(f"FATAL: cannot read the registry, so 'did this value change' cannot "
                         f"be answered and nothing may be registered: {exc}")

    report = {}
    for cycle, origin in PAIRS:
        rows, moved, same, new = candidates(cycle), [], [], []
        for name, value, note in rows:
            base = name[: -(len(cycle_results.cycle_suffix(cycle)) + 1)]
            if origin is None:
                new.append((name, value))
                moved.append((name, value, f"{note} {WHY} FIRST registration of cycle 4: "
                                           f"`{cycle.removesuffix('_rj1')}` was measured and "
                                           f"its gate stopped before §4, so nothing was ever "
                                           f"registered under its own name. ({TASK})"))
                continue
            old_name = cycle_results.name_for(base, origin)
            old = live.get(old_name)
            if old is not None and float(old) == float(value):
                same.append((name, old_name, value))
                continue
            moved.append((name, value,
                          f"{note} {WHY} Supersedes `{old_name}`"
                          + (f" = {old}" if old is not None else " (never registered)")
                          + f", which is unedited and stands as the harness-v4 record. "
                            f"({TASK})"))
        report[cycle] = {"candidates": len(rows), "to_register": len(moved),
                         "unchanged": len(same), "new_cycle": bool(origin is None),
                         "unchanged_names": [n for n, _o, _v in same][:400],
                         "moved_names": [n for n, _v, _note in moved]}
        if a.dry_run:
            print(f"{cycle}: {len(rows)} candidates, {len(moved)} moved, {len(same)} unchanged")
            for n, v, _ in moved[:14]:
                print(f"    + {n} = {v}")
            if len(moved) > 14:
                print(f"    … and {len(moved) - 14} more")
            continue

        matrix_file = scan_report.matrix_path(cycle)
        report[cycle]["matrices"] = write_matrices(cycle)
        out = cycle_results.register(
            moved, cycle=cycle, script="scan_report",
            data=f"scan_matrix_{cycle_results.cycle_suffix(cycle)}",
            data_path=str(matrix_file.relative_to(REPO)),
            data_description=(f"The {cycle} matrix: the {origin or 'scan_2026-09-10'} cycle's "
                              f"stored Observations re-judged under harness-v5. {WHY} "
                              f"Written by scripts/scan_report.py. ({TASK})"))
        report[cycle]["registered"] = out
        print(f"{cycle}: {json.dumps(out)}")

    (REPO / "state" / "rejudgement_registration_2026-09-10.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
