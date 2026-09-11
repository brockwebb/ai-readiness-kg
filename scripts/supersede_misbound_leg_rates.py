#!/usr/bin/env python3
"""Give the six misbound Tier C values a correct home. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 3, superseding the six
`cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §1 records.

**What is superseded and what is not.** Six Results named `scan_leg_rate_<leg>_upper95_…_rj1`
hold Tier C upper bounds. Their names mean the host family, because that is what every earlier
`scan_leg_rate_*` name meant. A Result name binds once (AD-028) so they cannot be corrected —
they are left exactly as they are, and each gets a successor that says what the number actually
measures.

**Decision 3's wording is ambiguous and this is the reading.** It says to register the TIER C
name "at the value the RESULT §1 table says it should be", and that table's "should be" column
holds the HOST value. Registering a host value under a Tier C name would repeat the defect
one column over, so the Tier C name gets the Tier C value — which is the number that was
misfiled and now has somewhere correct to live. The host values are unchanged from cycle 3 and
stay unregistered under decision 2 of the previous task, which forbids re-registering what did
not move.

**No state machine exists to walk them to.** `Result` in Seldon's research domain has a
`properties` block and no `states` block, so there is no `superseded` state — checked, not
assumed. The record is therefore the successor's description plus the pin in
`tests/test_rejudgement_2_3_4.py`, exactly as decision 3's second branch says.
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
import register_l0_rejudged as R                                    # noqa: E402

TASK = "cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md"
CYCLE = "scan_2026-09-09_rj1"
#: leg -> the unprefixed Result it supersedes, and the host value that name's siblings mean.
MISBOUND = {
    "A4": ("scan_leg_rate_a4_upper95_2026-09-09_rj1", 0.985135),
    "A5": ("scan_leg_rate_a5_upper95_2026-09-09_rj1", 0.532305),
    "A10": ("scan_leg_rate_a10_upper95_2026-09-09_rj1", 0.985135),
    "A11-declared": ("scan_leg_rate_a11_declared_upper95_2026-09-09_rj1", 0.953035),
    "A12": ("scan_leg_rate_a12_upper95_2026-09-09_rj1", 0.891025),
    "G1-D": ("scan_leg_rate_g1_d_upper95_2026-09-09_rj1", 0.242494),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    counts, prefix, population, family = R.families(CYCLE)["tierc"]
    emitted = {b: v for b, v, _n in B.leg_results(counts, prefix, CYCLE, population,
                                                  with_upper95=True, family=family)}
    host_counts = R.families(CYCLE)["host"][0]

    rows = []
    for leg, (old_name, host_value) in MISBOUND.items():
        base = f"scan_l0_tierc_leg_rate_{B.leg_key(leg)}_upper95"
        value = emitted[base]
        # §1's stop condition, re-checked here rather than trusted from the other script.
        if round(host_counts[leg]["wilson_hi"], 6) != round(host_value, 6):
            raise SystemExit(f"FATAL: the host value for {leg} does not reproduce: "
                             f"{host_counts[leg]['wilson_hi']} vs {host_value}")
        rows.append((cycle_results.name_for(base, CYCLE), value, (
            f"Upper bound of the 95% Wilson score interval on the pass rate for leg {leg} over "
            f"{population}, cycle {CYCLE}. "
            f"**Supersedes `{old_name}`**, which holds this same Tier C value under a name that "
            f"means the HOST family: `build_l0_matrices.leg_results` emitted "
            f"`scan_leg_rate_<leg>_upper95` without saying which of three populations computed "
            f"it, and `scripts/register_l0_rejudged.py` asked Tier C for a stat the shipped "
            f"builder only ever asked host and product for. The host family's bound for this "
            f"leg is {host_value} and did not move between scan_2026-09-09 and its "
            f"re-judgement, so it is not re-registered (decision 2 of "
            f"cc_tasks/2026-09-10_rejudge_2_3_4.md). The misbound Result is NOT edited — a "
            f"Result name binds once (AD-028) — and Seldon's `Result` type has no state "
            f"machine, so this description and the pin in tests/test_rejudgement_2_3_4.py are "
            f"the supersession record. Task {TASK} decision 3."))
        )

    if a.dry_run:
        for n, v, note in rows:
            print(f"  {n} = {v}")
            print(f"      {note[:150]}…")
        return 0

    out = cycle_results.register(
        rows, cycle=CYCLE, script="build_l0_matrices",
        data=f"scan_matrix_{cycle_results.cycle_suffix(CYCLE)}",
        data_path=f"state/scan_matrix_{cycle_results.cycle_suffix(CYCLE)}.json",
        data_description=("Cycle 3's stored Observations re-judged under harness-v5; the Tier C "
                          f"reference hosts' leg rates. Task {TASK}."))
    print(json.dumps(out, indent=1))
    (REPO / "state" / "misbound_supersessions_2026-09-10.json").write_text(
        json.dumps({"superseded": {old: {"by": cycle_results.name_for(
            f"scan_l0_tierc_leg_rate_{B.leg_key(leg)}_upper95", CYCLE),
            "tierc_value": emitted[f"scan_l0_tierc_leg_rate_{B.leg_key(leg)}_upper95"],
            "host_value_unchanged": hv}
            for leg, (old, hv) in MISBOUND.items()},
            "result_state_machine": "none — Seldon's Result type has no states block",
            "registered": out}, indent=1) + "\n", encoding="utf-8")
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
