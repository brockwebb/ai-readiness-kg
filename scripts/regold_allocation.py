#!/usr/bin/env python3
"""Neyman allocation for the 200-pair regold. **Zero model spend.**

Task `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md` §3. **Neyman (1934)**, "On the two
different aspects of the representative method", *JRSS* 97(4):558-625, and **Cochran (1977),
*Sampling Techniques*, §5.5**: for a fixed total sample, the allocation that minimises the
variance of the population estimate is `n_h ∝ N_h · S_h`. `S_h` is estimated from each
stratum's observed error proportion, with **p = 0.5 where zero errors were observed** — the
task's pre-registered choice, and the maximum-variance value, so it cannot understate a
stratum's uncertainty.

The allocation is registered **before epoch 2's numbers exist**, which is the point: an
acceptance sample sized after seeing the result it will judge is not an acceptance sample.
The draw is NOT made here.

    /opt/anaconda3/bin/python3 scripts/regold_allocation.py [--total 200]
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md"
KEY = REPO / "state" / "er_gold_key.json"
LABELS = REPO / "assessment" / "results" / "er_gold_labels_2026-09-05_main.jsonl"
SCORES = REPO / "assessment" / "results" / "er_gold_scores_2026-09-05.json"
OUT = REPO / "state" / "er_regold_allocation_2026-09-06.json"

DESCRIPTIONS = {
    "A": "exact-name auto-links",
    "B": "clerical band, accepted",
    "C": "clerical band, rejected",
    "D": "near-miss, cosine in [0.70, 0.80)",
    "E": "cross-arm pairs in terms the homograph pass KEPT",
    "F": "pairs this task changed — a new alias or a split moved their resolution",
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--total", type=int, default=200)
    ap.add_argument("--objective", choices=("population", "domain"), default="population",
                    help="population: Neyman, n_h proportional to N_h*S_h — minimises the "
                         "variance of the POPULATION estimate. domain: Cochran (1977) §5.6, "
                         "n_h proportional to S_h — equal precision PER STRATUM, which is what "
                         "a per-stratum acceptance measurement actually needs (DD-048 §3).")
    ap.add_argument("--out", default=None)
    ap.add_argument("--changed-pairs", type=int, default=0,
                    help="N_F: pairs whose resolution this task changed (§1.3 + §2.4)")
    a = ap.parse_args(argv)

    key = json.loads(KEY.read_text(encoding="utf-8"))
    scores = json.loads(SCORES.read_text(encoding="utf-8"))
    pops = dict(key["stratum_population"])
    pops["F"] = a.changed_pairs

    rows = []
    for h in sorted(pops):
        N = pops[h]
        c = scores["by_stratum"].get(h, {})
        errors = (c.get("fp", 0) + c.get("fn", 0))
        scored = c.get("n", 0)
        observed_p = (errors / scored) if scored else None
        # §3: p = 0.5 where zero errors were observed — the maximum-variance value, so a
        # stratum with no observed error is never treated as certainly clean.
        p = 0.5 if (not scored or errors == 0) else observed_p
        S = math.sqrt(p * (1 - p))
        rows.append({"stratum": h, "description": DESCRIPTIONS[h], "N": N,
                     "scored_in_gold": scored, "errors_in_gold": errors,
                     "observed_error_p": None if observed_p is None else round(observed_p, 6),
                     "p_used": round(p, 6), "S": round(S, 6), "NS": round(N * S, 4)})

    # The allocation weight IS the objective, and the two objectives are different questions:
    #   population  n_h ∝ N_h·S_h  — Neyman (1934): minimise the variance of the whole-corpus
    #                                 estimate. Stratum A's N dominates, so it takes the sample.
    #   domain      n_h ∝ S_h      — Cochran (1977) §5.6: equal precision within each stratum,
    #                                 which is what a PER-STRATUM acceptance measurement needs.
    for r in rows:
        r["weight"] = r["NS"] if a.objective == "population" else r["S"]
        if r["N"] <= 0:
            r["weight"] = 0.0
    # Proportional allocation, then capped at each stratum's population with the surplus
    # redistributed — a stratum of 45 cannot yield 51 pairs however much precision it deserves.
    remaining, caps = a.total, {r["stratum"]: r["N"] for r in rows}
    alloc = {r["stratum"]: 0 for r in rows}
    live = [r for r in rows if r["weight"] > 0]
    for _ in range(10):
        tw = sum(r["weight"] for r in live if alloc[r["stratum"]] < caps[r["stratum"]])
        if not tw or remaining <= 0:
            break
        want = {r["stratum"]: alloc[r["stratum"]] + remaining * r["weight"] / tw
                for r in live if alloc[r["stratum"]] < caps[r["stratum"]]}
        changed = False
        for h, v in want.items():
            new = min(int(round(v)), caps[h])
            if new != alloc[h]:
                alloc[h], changed = new, True
        remaining = a.total - sum(alloc.values())
        if not changed:
            break
    # Rounding can OVERSHOOT as easily as undershoot — `int(round(v))` per stratum summed to
    # 201 on the first domain run. Trim before topping up, taking from the stratum with the
    # smallest weight per allocated pair so the trim costs the least precision.
    while sum(alloc.values()) > a.total:
        cand = [r for r in live if alloc[r["stratum"]] > 0]
        if not cand:
            break
        worst = min(cand, key=lambda r: r["weight"] / max(1, alloc[r["stratum"]]))
        alloc[worst["stratum"]] -= 1
    remaining = a.total - sum(alloc.values())
    # largest-remainder top-up for any rounding shortfall
    while remaining > 0:
        cand = [r for r in live if alloc[r["stratum"]] < caps[r["stratum"]]]
        if not cand:
            break
        best = max(cand, key=lambda r: r["weight"] / max(1, alloc[r["stratum"]]))
        alloc[best["stratum"]] += 1
        remaining -= 1
    for r in rows:
        r["n_allocated"] = alloc[r["stratum"]]

    method = ("Neyman (1934) n_h proportional to N_h * S_h; Cochran (1977) §5.5 "
              "— POPULATION objective"
              if a.objective == "population" else
              "Cochran (1977) Sampling Techniques §5.6, n_h proportional to S_h "
              "— DOMAIN (per-stratum) objective, DD-048 §3")
    out = {"task": TASK, "method": method, "objective": a.objective,
           "total": a.total, "seed_for_the_draw": 20260906,
           "draw_made_here": False, "strata": rows,
           "note": ("Registered BEFORE epoch 2's numbers exist. The draw belongs to the next "
                    "task. Stratum F is 0 because both this task's write gates failed and "
                    "nothing changed any node's resolution.")}
    dest = Path(a.out) if a.out else OUT
    dest.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"{'h':2s} {'N':>7s} {'err/scored':>11s} {'p':>7s} {'S':>7s} {'N*S':>10s} {'n':>5s}  what")
    for r in rows:
        print(f"{r['stratum']:2s} {r['N']:>7d} {str(r['errors_in_gold'])+'/'+str(r['scored_in_gold']):>11s} "
              f"{r['p_used']:>7.4f} {r['S']:>7.4f} {r['NS']:>10.1f} {r['n_allocated']:>5d}  {r['description']}")
    # `.resolve()` first: a RELATIVE --out is not "in the subpath of" the absolute
    # REPO, so this raised ValueError AFTER the JSON had been written. Same defect
    # class as the one fixed in extraction_gap_diagnostic.py on 2026-09-04.
    print(f"\n{method}\n-> {dest.resolve().relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
