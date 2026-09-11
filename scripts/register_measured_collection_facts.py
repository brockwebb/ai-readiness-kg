#!/usr/bin/env python3
"""The COLLECTION facts of a measured cycle whose judgements were never registered.
**Zero spend, no network.**

Task `cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 1, and the premise it got
wrong. The revision moves the report's snapshot to `scan_2026-09-10_rj2`, and eleven of its
tags had no cycle-4 name to move to. Six were L0 population counts and are registered by
`build_l0_matrices.py`; three are the ones this script exists for.

**Why cycle 4 has none, and why these three are not the reason.** Cycle 4's gate STOPPED before
registration (`cc_tasks/2026-09-10_scan_run_4_RESULT.md` §1): fourteen Findings carried a
verdict about a product whose every observation the collector never made, and registering a
JUDGEMENT known to be wrong into a name that binds once (AD-028) is what the gate refused. The
judgements have since been re-judged twice and the generation-9 payload's 274 names are
registered. What the gate never touched is the COLLECTION — the observations are sound, "they
record exactly what happened, including the refusals", and the measurement cannot be taken
again.

**Why they are not registered under the re-judgement's name.** `scripts/scan_report.py`
already decides this and its rule is adopted rather than re-argued: *"the Results that describe
the MEASUREMENT — observations captured, requests issued per host, error classes recorded — are
the source cycle's and are not re-registered under this cycle's name"*, because a re-judgement
fetched nothing. The measurement family is therefore DERIVED here, not typed: it is exactly the
set of bases `scan_report.results` emits for the measured payload and withholds for the
re-judged one.

**And only what the report names.** A name binds once, so a permanent name with no consumer is
the registry bloat `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §4 declined 264 of. The
set registered is the measurement family INTERSECTED with the `{{result:...}}` tags the report's
own sections quote — both sides read from disk, neither typed here.

    /opt/anaconda3/bin/python3 scripts/register_measured_collection_facts.py \\
        --cycle scan_2026-09-10 --rejudged scan_2026-09-10_rj2 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

import cycle_results                                                # noqa: E402
import register_l0_report_results as L                              # noqa: E402
import scan_report                                                  # noqa: E402

TASK = "cc_tasks/2026-09-11_l0_report_cycle4_revision.md"
SECTIONS = REPO / "docs" / "reports" / "sections"
_TAG = re.compile(r"\{\{result:([^:}]+):")


def report_tags() -> set:
    """Every Result name the report's sections quote, read from the sections."""
    out = set()
    for f in sorted(SECTIONS.glob("*.md")):
        out |= set(_TAG.findall(f.read_text(encoding="utf-8")))
    return out


def rows_for(cycle: str) -> list:
    """`scan_report`'s own rows for one cycle, bases bare."""
    p = scan_report.load(cycle)
    tiers = scan_report.tier_of(scan_report.load_params())
    legs = scan_report.per_leg(p, tiers, "A")
    legs_c = scan_report.per_leg(p, tiers, "C")
    return scan_report.results(p, legs, scan_report.a12(p),
                               scan_report.matrix(p, cycle, tiers, "A"), cycle,
                               None, legs_c, scan_report.blind_counts(p))


def measurement_family(measured: str, rejudged: str) -> set:
    """The bases that describe the COLLECTION, derived from `scan_report`'s own refusal.

    Not a list in this file: `scan_report.results` emits these for a measured payload and
    withholds them for a re-judged one, so the difference IS the family, and it stays right when
    that decision changes.
    """
    return ({b for b, _v, _n in rows_for(measured)}
            - {b for b, _v, _n in rows_for(rejudged)})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", required=True, help="the MEASURED cycle")
    ap.add_argument("--rejudged", required=True,
                    help="a re-judgement of it, which defines the family by what it withholds")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    p = scan_report.load(a.cycle)
    if p.get("cycle_kind") == "rejudged":
        raise SystemExit(f"FATAL: {a.cycle} is itself a re-judgement; pass the measured cycle")
    rj = scan_report.load(a.rejudged)
    if rj.get("derived_from") != a.cycle:
        raise SystemExit(f"FATAL: {a.rejudged} derives from {rj.get('derived_from')!r}, "
                         f"not from {a.cycle}")

    family = measurement_family(a.cycle, a.rejudged)
    wanted = report_tags()
    rows = [(cycle_results.name_for(b, a.cycle), v, n) for b, v, n in rows_for(a.cycle)
            if b in family and cycle_results.name_for(b, a.cycle) in wanted]

    # `fss_scan_netlocs_contacted` is the same KIND of fact — netlocs contacted, counted at the
    # socket — and is computed by `register_l0_report_results`, which owns it. It is registered
    # here under the MEASURED cycle's name for the reason above.
    #
    # **It supersedes `fss_scan_netlocs_contacted_2026-09-10_rj2`**, which this task bound
    # first, before reading `scan_report`'s rule; the description there is true and its NAME
    # files a collection fact under a cycle that opened no socket. A Result name binds once
    # (AD-028) and Seldon's Result type has no state machine, so this description and the
    # record file are the supersession, exactly as
    # `scripts/supersede_misbound_leg_rates.py` did it.
    nl = L.netlocs_contacted(p)
    mis = cycle_results.name_for("fss_scan_netlocs_contacted", a.rejudged)
    name = cycle_results.name_for("fss_scan_netlocs_contacted", a.cycle)
    if name in wanted:
        rows.append((name, nl, (
            f"Netlocs cycle {a.cycle} (params_hash {p['params_hash'][:12]}...) issued at least "
            f"one HTTP request to, counted at the socket from the payload's own per-host "
            f"counter, loopback control fixtures excluded. **Supersedes `{mis}`**, which holds "
            f"this same value under the name of a RE-JUDGEMENT — a cycle that issued no request "
            f"at all ({TASK} decision 1, and `scripts/scan_report.py`'s rule that the Results "
            f"describing a MEASUREMENT belong to the cycle that made it). The misbound Result "
            f"is not edited; a name binds once (AD-028). Task {TASK}.")))

    if a.dry_run:
        print(json.dumps({"measurement_family": sorted(family)[:12],
                          "family_size": len(family),
                          "report_tags": len(wanted)}, indent=1))
        for n, v, note in rows:
            print(f"  {n:52s} {v}\n      {note[:120]}…")
        return 0

    out = cycle_results.register(
        rows, cycle=a.cycle, script="scan_report",
        data=f"scan_matrix_{cycle_results.cycle_suffix(a.cycle)}",
        data_path=f"state/scan_matrix_{cycle_results.cycle_suffix(a.cycle)}.json",
        data_description=(f"The Tier A matrix of cycle {a.cycle}, whose JUDGEMENTS the cycle's "
                          f"gate refused to register and whose COLLECTION is what this "
                          f"registers. Task {TASK}."))
    rec = REPO / "state" / f"collection_facts_{cycle_results.cycle_suffix(a.cycle)}.json"
    rec.write_text(json.dumps({
        "task": TASK, "measured": a.cycle, "rejudged": a.rejudged,
        "measurement_family": sorted(family),
        "registered": [n for n, _v, _n in rows],
        "supersedes": {mis: name},
        "result_state_machine": "none — Seldon's Result type has no states block; the "
                                "description and this record are the supersession",
        "outcome": out}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    print(f"wrote {rec.relative_to(REPO)}")
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
