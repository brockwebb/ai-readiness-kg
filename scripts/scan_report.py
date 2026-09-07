#!/usr/bin/env python3
"""Per-leg rates, the agency × leg matrix, and the cycle's Results. **Zero model spend.**

Task `cc_tasks/2026-09-07_scan_run.md` §4. Three disciplines are wired in rather than
remembered, because each has already cost this project something when it was left to memory:

**1. Every denominator is stated, and unobservable hosts are never silently dropped.** A pass
rate over "the surfaces that answered" is a different measurement from a pass rate over "the
surfaces we targeted", and quoting the first while implying the second is how an accessibility
assessment ends up describing only the agencies that let it look. `pass_rate` is computed over
pass + fail on **observable, admitted** surfaces; `applicable_n`, `error_n` and
`surfaces_targeted` ride alongside on every leg, and the three refusing hosts have their own
Results.

**2. Wilson, not Wald.** `assessment/harness/rollup.wilson_interval` — the repo's own, reused
rather than re-derived. At these n (8-18 per leg) a normal-approximation interval on a
proportion near 0 or 1 is not merely imprecise, it runs off the end of the scale.

**3. No composite and no ranking.** The task forbids both and the reason is worth keeping on
the face of the code: a single number over legs that measure different constructs, weighted by
nothing in particular, would be read as a score of the agency, and this instrument has not
earned that reading. The matrix is published; the league table is not.

    /opt/anaconda3/bin/python3 scripts/scan_report.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                              # noqa: E402
from harness.rollup import wilson_interval                        # noqa: E402
from scan.rules import CANDIDATE_LEGS, CURRENT                    # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_run.md"
CYCLE = "scan_2026-09-07"
PAYLOAD = REPO / "state" / f"{CYCLE}.json"
MATRIX = REPO / "state" / "scan_matrix_2026-09-07.json"
VERDICTS = ("pass", "fail", "not_applicable", "error")


def load() -> dict:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def per_leg(payload: dict) -> dict:
    """Counts and a Wilson interval per leg, over admitted product surfaces only."""
    rows = [r for r in payload["matrix"] if r["surface_kind"] != "well_known"]
    out = {}
    for leg in sorted(l for l in CURRENT if l not in CANDIDATE_LEGS and l != "E5"):
        v = [r["verdicts"][leg] for r in rows if leg in r["verdicts"]]
        if not v:
            continue
        c = collections.Counter(v)
        k, n = c["pass"], c["pass"] + c["fail"]
        lo, hi = wilson_interval(k, n)
        out[leg] = {"pass": c["pass"], "fail": c["fail"],
                    "not_applicable": c["not_applicable"], "error": c["error"],
                    "applicable_n": n, "surfaces_targeted": len(v),
                    "pass_rate": round(k / n, 4) if n else None,
                    "ci95_low": lo, "ci95_high": hi,
                    "denominator": ("pass + fail on admitted surfaces that were observable; "
                                    "`error` is excluded because the collector could not "
                                    "observe, which is ours and not the product's")}
    return out


def a12(payload: dict) -> dict:
    rows = [r for r in payload["matrix"] if r["surface_kind"] == "well_known"]
    c = collections.Counter(r["verdicts"].get("A12") for r in rows)
    return {"by_verdict": {v: c[v] for v in VERDICTS},
            "hosts": len(rows),
            "by_host": {r["agency"]: r["verdicts"].get("A12") for r in sorted(
                rows, key=lambda x: x["agency"])}}


def matrix(payload: dict) -> dict:
    """Agencies × legs. One row per agency per surface kind, so a reader can see that BEA's
    two flagships disagree rather than seeing an agency-level average that hides it."""
    # E5 judges the CYCLE, not a surface, so it has no column in a surfaces × legs matrix.
    # Leaving it in printed an empty column of "?" across every row, which reads as missing
    # data rather than as a leg with a different subject.
    legs = [l for l in CURRENT if l not in CANDIDATE_LEGS and l != "E5"]
    rows = []
    for r in sorted(payload["matrix"], key=lambda r: (r["agency"], r["surface_kind"],
                                                      r["doc_id"])):
        rows.append({"agency": r["agency"], "surface_kind": r["surface_kind"],
                     "doc_id": r["doc_id"], "url": r["url"], "admitted": r["admitted"],
                     "verdicts": r["verdicts"]})
    unobservable = sorted({r["agency"] for r in payload["matrix"]
                           if r["surface_kind"] != "well_known"
                           and r["verdicts"] and all(v == "error"
                                                     for v in r["verdicts"].values())})
    with_surfaces = {r["agency"] for r in payload["matrix"]
                     if r["surface_kind"] != "well_known"}
    all_agencies = {r["agency"] for r in payload["matrix"]}
    return {"task": TASK, "cycle": CYCLE, "params_hash": payload["params_hash"],
            "agencies_without_surfaces": sorted(all_agencies - with_surfaces),
            "legs": legs, "candidate_legs": sorted(CANDIDATE_LEGS),
            "agencies": sorted({r["agency"] for r in payload["matrix"]}),
            "agencies_wholly_unobservable": unobservable,
            "note": ("No composite and no ranking. These legs measure different constructs; a "
                     "single number over them, weighted by nothing in particular, would be "
                     "read as a score of the agency, and this instrument has not earned that "
                     "reading."),
            "rows": rows}


def results(payload: dict, legs: dict, a12v: dict, mx: dict) -> list:
    ph = payload["params_hash"][:12]
    tag = f"Cycle {CYCLE}, params_hash {ph}…."
    out = []
    for leg, s in legs.items():
        key = leg.replace("-", "_").lower()
        base = (f"{tag} Leg {leg} judged by {CURRENT[leg]} over {s['surfaces_targeted']} "
                f"admitted product surfaces.")
        out += [
            (f"scan_{key}_pass", s["pass"], f"{base} Findings of `pass`."),
            (f"scan_{key}_fail", s["fail"], f"{base} Findings of `fail` — the collector "
                                            f"observed and the property was not there."),
            (f"scan_{key}_not_applicable", s["not_applicable"],
             f"{base} Findings of `not_applicable` — there was nothing of that kind to check."),
            (f"scan_{key}_error", s["error"],
             f"{base} Findings of `error` — the COLLECTOR could not observe; never a product "
             f"failure."),
            (f"scan_{key}_applicable_n", s["applicable_n"],
             f"{base} Denominator for the pass rate: {s['denominator']}."),
        ]
        if s["applicable_n"]:
            out.append((f"scan_{key}_pass_rate", s["pass_rate"],
                        f"{base} {s['pass']}/{s['applicable_n']} = {s['pass_rate']}, Wilson "
                        f"95% [{s['ci95_low']}, {s['ci95_high']}]. Denominator: "
                        f"{s['denominator']}. NOT a score of any agency and not comparable "
                        f"across legs — these legs measure different constructs."))
    for v in ("pass", "fail", "not_applicable", "error"):
        out.append((f"scan_a12_{v}", a12v["by_verdict"][v],
                    f"{tag} **CANDIDATE indicator A12** (DD-054): reported, adopted by "
                    f"nobody, and counted in no fraction. Hosts at `{v}` of {a12v['hosts']}: "
                    f"{sorted(h for h, x in a12v['by_host'].items() if x == v)}."))
    vc = payload["verdict_counts"]
    out += [
        ("scan_surfaces", payload["surfaces"], f"{tag} Surfaces scanned, of the 41 on "
                                               f"`scan_targets_2026-09`."),
        ("scan_findings", payload["findings"], f"{tag} Findings produced: {vc}."),
        ("scan_observations", payload["observations"], f"{tag} Observations captured, each "
                                                       f"with its whole response body stored "
                                                       f"content-addressed."),
        # DD-041: a rerun never overwrites a registered measurement. `scan_control_findings`
        # is already bound to the 2026-09-06 control cycle at 31, so this cycle's 33 gets the
        # date. §4 names the cycle-level Results bare, and bare names are not cycle-unique —
        # every one of them collides on the next cycle. Recorded as a premise this task got
        # wrong rather than papered over by renaming the earlier one.
        (f"scan_control_findings_{CYCLE.split('_')[-1]}", payload["control_findings"],
         f"{tag} Control Findings, including RULE-E5-v2's own verdict on the cycle and A12 on "
         f"both fixtures. The gate ran before any real host was touched, and E5-v2 asserted "
         f"that ordering against the first surface timestamp for the first time."),
        ("scan_agencies_unobservable", len(mx["agencies_wholly_unobservable"]),
         f"{tag} Agencies on which EVERY leg of EVERY ADMITTED surface returned `error`: "
         f"{mx['agencies_wholly_unobservable']}. Read this WITH "
         f"`scan_agencies_with_no_admitted_surface`: it is not the count of agencies that "
         f"refused us. An agency that refused the scanner early enough never got an admitted "
         f"surface, so it cannot appear in a product-surface metric at all."),
        ("scan_agencies_with_no_admitted_surface", len(mx["agencies_without_surfaces"]),
         f"{tag} Agencies contributing NO admitted product surface, and therefore absent from "
         f"every per-leg denominator on this page: {mx['agencies_without_surfaces']}. Three "
         f"of them refuse an identified robots-compliant client outright and one serves a "
         f"data listing that is unreadable without JavaScript, so their own listings could "
         f"not be read and no flagship could be selected. **A refusal upstream removes an "
         f"agency from the instrument's denominators entirely** — one layer earlier than the "
         f"guard that keeps unobservable surfaces in them, and the more consequential of the "
         f"two for an accessibility assessment."),
        ("scan_hosts_refusing_or_unreachable", sum(
            1 for r in payload["matrix"] if r["surface_kind"] == "well_known"
            and r["verdicts"].get("A12") in ("fail", "error")),
         f"{tag} Hosts whose declared and enforced layers disagree, or that could not be "
         f"reached at all, of 14 — measured by the CANDIDATE indicator A12 and therefore "
         f"counted in no framework fraction (DD-054). This is the only figure in the cycle "
         f"that sees the refusing agencies at all."),
        ("scan_surfaces_unobservable", sum(
            1 for r in payload["matrix"] if r["surface_kind"] != "well_known"
            and r["verdicts"] and all(v == "error" for v in r["verdicts"].values())),
         f"{tag} Admitted surfaces on which every leg returned `error`."),
    ]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    payload = load()
    legs, a12v = per_leg(payload), a12(payload)
    mx = matrix(payload)
    data = results(payload, legs, a12v, mx)
    if a.dry_run:
        for n, v, note in data:
            print(f"{n}\t{v}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    MATRIX.write_text(json.dumps({**mx, "per_leg": legs, "a12": a12v}, indent=1) + "\n",
                      encoding="utf-8")
    # Through the shared registrar, which refuses a per-cycle name that does not carry its
    # cycle BEFORE anything is registered (DD-056, `cc_tasks/2026-09-07_scan_harness_v3.md`
    # §1.6). `scan_control_findings` was refused mid-run on 2026-09-07 for exactly this, after
    # the measurement; the check now happens before the first write.
    out = cycle_results.register([(n, v, f"{note} ({TASK})") for n, v, note in data],
                                 cycle=CYCLE, script="scan_report",
                                 data="scan_matrix_2026-09-07")
    print(json.dumps({**out, "matrix": str(MATRIX.relative_to(REPO))}, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
