#!/usr/bin/env python3
"""The L0 families of cycle 3 re-judged, registering ONLY what moved. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_rejudge_2_3_4.md` decisions 2 and 4. `scripts/scan_report.py` covers
the per-cycle families; this covers the L0 report's own, which are computed over different
populations by `scripts/build_l0_matrices.py` and are the numbers the report actually quotes.

Five product legs move — A1, A3, A6, A8 and B3 — each losing one `fail` to `error` on EIA's
robots-disallowed flagship. The denominator drops 16 → 15 and every upper-95 bound rises with
it, which is the correction working: a surface the scanner was forbidden to read is no longer
counted as a product that failed.

The same discipline as the sibling registrar: compare each candidate to the value registered
under the ORIGINAL name, register the difference, leave the rest alone, and never touch the old
Result (AD-028).
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

import build_l0_matrices as B                                       # noqa: E402
import cycle_results                                                # noqa: E402

TASK = "cc_tasks/2026-09-10_rejudge_2_3_4.md"
CYCLE = "scan_2026-09-09_rj1"
ORIGIN = "scan_2026-09-09"
WHY = ("Re-judged under harness-v5 (DD-064): a URL inside the product that robots.txt forbids "
       "is BLIND, not scope. EIA's flagship was forbidden and is now `error` on the legs that "
       "read its page, so it leaves the denominator instead of counting as a product failure.")


def families(cycle: str):
    params = B.load_params()
    tiers = B.tier_of(params)
    tier0 = list(params["tier0"]["legs"])
    p = B.payload(cycle)
    product = B.product_matrix(p, tiers, B.PRODUCT_LEGS)
    declared = sum(1 for r in product if r["declared"])
    agencies = len({r["agency"] for r in product if r["declared"]})
    return {
        "host": (B.leg_counts(B.host_matrix(p, tiers, "A", tier0), tier0), "scan_l0_",
                 "the 16 Tier A bodies' HOST-LEVEL surfaces (each body's `home:` page, and its "
                 "`host:` well-known set for A12)"),
        "product": (B.leg_counts([r for r in product if r["declared"]], B.PRODUCT_LEGS),
                    "scan_l0_product_",
                    f"the {declared} DECLARED flagship surfaces of {agencies} Tier A agencies "
                    f"— a PARTIAL population, because the other agencies have declared no "
                    f"product to look at"),
        "tierc": (B.leg_counts(B.host_matrix(p, tiers, "C", tier0), tier0), "scan_l0_tierc_",
                  "the 3 Tier C reference hosts' host-level surfaces, which enter no Tier A "
                  "denominator"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    from scan.figures import load_results
    live = load_results()

    # **FIRST EMITTER WINS, and the order is `build_l0_matrices.main`'s: host, product, tierc.**
    #
    # `leg_results` emits `scan_leg_rate_<leg>_upper95` WITHOUT the family prefix, so all three
    # families compete for one name. The original run bound whichever reached the registry
    # first — host for the tier-0 legs, product for the rest — and a re-registration that let a
    # different family win would put a Tier C number under a name whose original means Tier A.
    # This registrar did exactly that for six legs before the check existed (RESULT §1), which
    # is why the rule is stated here rather than left to the dict's ordering.
    rows, unchanged, seen = [], [], set()
    for _fam, (counts, prefix, population) in families(CYCLE).items():
        for base, value, note in B.leg_results(counts, prefix, CYCLE, population,
                                               with_upper95=True):
            if base in seen:
                continue
            seen.add(base)
            new_name = cycle_results.name_for(base, CYCLE)
            old_name = cycle_results.name_for(base, ORIGIN)
            old = live.get(old_name)
            if old is not None and float(old) == float(value):
                unchanged.append(new_name)
                continue
            rows.append((new_name, value,
                         f"{note} {WHY} Supersedes `{old_name}`"
                         + (f" = {old}" if old is not None else " (never registered)")
                         + f", which is unedited and stands as the harness-v4 record. "
                           f"({TASK})"))

    print(f"{len(rows)} moved, {len(unchanged)} unchanged")
    for n, v, _ in rows:
        print(f"  + {n} = {v}")
    if a.dry_run:
        return 0
    out = cycle_results.register(
        rows, cycle=CYCLE, script="build_l0_matrices",
        data=f"scan_matrix_{cycle_results.cycle_suffix(CYCLE)}",
        data_path=f"state/scan_matrix_{cycle_results.cycle_suffix(CYCLE)}.json",
        data_description=(f"Cycle 3's stored Observations re-judged under harness-v5. {WHY} "
                          f"({TASK})"))
    print(json.dumps(out, indent=1))
    (REPO / "state" / "l0_rejudged_registration_2026-09-10.json").write_text(
        json.dumps({"moved": [n for n, _v, _n2 in rows], "unchanged": unchanged,
                    "registered": out}, indent=1) + "\n", encoding="utf-8")
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
