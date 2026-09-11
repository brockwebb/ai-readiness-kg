#!/usr/bin/env python3
"""The BEFORE end of a movement the report describes. **Zero spend, no network.**

Task `cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 4: the movement section states
that five declared flagship surfaces left A3's denominator when generation 9 stopped counting a
product whose bulk download the scanner was forbidden to look for as a product without one, and
that the instrument's claim got weaker for it — "tags for 19 → 14 and the upper bound".

**The 14 is registered and the 19 is not.** Cycle 4's L0 families were registered for the first
time under `scan_2026-09-10_rj2` (`cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §4: the
measured cycle's gate stopped before §4, and `_rj1`'s L0 family was never registered either). So
the `_rj1` end of the pair has no name, and a report that may not type a numeral cannot quote
it.

**Why not simply run `build_l0_matrices.py --cycle scan_2026-09-10_rj1`.** That would bind ~138
permanent names for a judgement that is superseded and has one consumer — the registry bloat
`register_gen9_rejudged.py` declined 264 names of, for the same reason. What this registers is
the endpoints the report NAMES and nothing else, computed by `build_l0_matrices`, which owns
the computation; nothing is typed here.

    /opt/anaconda3/bin/python3 scripts/register_superseded_l0_endpoints.py \\
        --cycle scan_2026-09-10_rj1 --superseded-by scan_2026-09-10_rj2 --leg A3 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

import build_l0_matrices as B                                       # noqa: E402
import cycle_results                                                # noqa: E402

TASK = "cc_tasks/2026-09-11_l0_report_cycle4_revision.md"


def product_counts(cycle: str) -> dict:
    params = B.load_params()
    p = B.payload(cycle)
    product = B.product_matrix(p, B.tier_of(params), B.PRODUCT_LEGS)
    declared = [r for r in product if r["declared"]]
    return {"counts": B.leg_counts(declared, B.PRODUCT_LEGS), "declared": len(declared),
            "payload": p}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", required=True, help="the SUPERSEDED judgement")
    ap.add_argument("--superseded-by", required=True)
    ap.add_argument("--leg", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    old, new = product_counts(a.cycle), product_counts(a.superseded_by)
    if old["payload"].get("derived_from") != new["payload"].get("derived_from"):
        raise SystemExit("FATAL: the two judgements do not rest on the same measured cycle; "
                         "a movement between them would not be the instrument moving")
    c_old, c_new = old["counts"][a.leg], new["counts"][a.leg]
    key = B.leg_key(a.leg)
    left = c_old["applicable_n"] - c_new["applicable_n"]
    rows = [
        (f"scan_l0_product_{key}_applicable_n", c_old["applicable_n"],
         f"Denominator for leg {a.leg} over the {old['declared']} declared flagship surfaces, "
         f"judgement {a.cycle}. **Superseded by `"
         f"{cycle_results.name_for(f'scan_l0_product_{key}_applicable_n', a.superseded_by)}` = "
         f"{c_new['applicable_n']}**: generation 9 (`RULE-A3-v6`, DD-052 §6, ISA 705) stopped "
         f"letting an ABSENCE claim rest on a candidate set with a BLIND member, so {left} "
         f"surfaces whose whole-product download the scanner was never allowed to look for "
         f"left the denominator as `error` instead of counting as products that offer none. "
         f"Registered because the report's movement section quotes both ends of that pair and "
         f"may not type either. Same stored Observations, same measured cycle "
         f"({old['payload'].get('derived_from')}); nothing was re-fetched. Task {TASK} "
         f"decision 4."),
        (f"scan_l0_product_leg_rate_{key}_upper95", round(c_old["wilson_hi"], 6),
         f"Upper bound of the 95% Wilson score interval on the pass rate for leg {a.leg} over "
         f"the {old['declared']} declared flagship surfaces, judgement {a.cycle}: "
         f"{c_old['pass']}/{c_old['applicable_n']}. **Superseded by `"
         f"{cycle_results.name_for(f'scan_l0_product_leg_rate_{key}_upper95', a.superseded_by)}"
         f"` = {round(c_new['wilson_hi'], 6)}** at {c_new['pass']}/{c_new['applicable_n']}. The "
         f"bound RISES: a smaller denominator is a weaker claim, and that is what the "
         f"correction costs. Task {TASK} decision 4."),
    ]
    rows = [(cycle_results.name_for(b, a.cycle), v, n) for b, v, n in rows]

    if a.dry_run:
        for n, v, note in rows:
            print(f"  {n:56s} {v}\n      {note[:140]}…")
        return 0

    out = cycle_results.register(
        rows, cycle=a.cycle, script="build_l0_matrices",
        data=f"scan_matrix_{cycle_results.cycle_suffix(a.cycle)}",
        data_path=f"state/scan_matrix_{cycle_results.cycle_suffix(a.cycle)}.json",
        data_description=(f"The matrix of judgement {a.cycle}, superseded by "
                          f"{a.superseded_by}. Task {TASK}."))
    print(json.dumps(out, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
