#!/usr/bin/env python3
"""`scan_2026-10-06_recollect_rj1`: the recollection's Observations judged under generation 15.
**Zero spend. No network.**

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 2. The
recollection (`scan_2026-10-06_recollect`, a targeted cycle over twelve legs) exposed three false
passes; generation 15 fixes them (`RULE-A2-v5`, `RULE-D1-v5`, `RULE-A3-v8`, decision 1). This
re-judges the recollection's stored Observations under `rules.CURRENT` as it stands, which differs
from what the recollection was judged with on those three legs only. Findings only: not one byte
is fetched and not one Observation is created. The result is itself a targeted cycle over the
same twelve legs (`rederive.rejudge` keeps `scope: legs`), so a composite can overlay it.

No re-read (`scan/reread.py`): the recollection's Observations were collected with the
`link_candidates` and `declared` blocks a re-read would add, so a re-read would change nothing
and is not run.

**The gate on the judgement, run before anything is written** (`rejudge_seven_legs.stop_reasons`,
plus this script's own):

1. Every Finding of a leg whose rule did not change is identical to the recollection's in every
   field but `finding_id` and `params_hash` (both are functions of the whole `params.yaml`).
2. Such a leg judges exactly the surfaces it judged.
3. The payload re-derives byte-identically (DD-041).
4. It carries no Observation and records no request.
5. Only A2, A3 and D1 changed rule, and every move on them is AWAY from `pass`: generation 15
   narrows what `pass` may claim and touches no other branch.

    /opt/anaconda3/bin/python3 scripts/rejudge_recollect_rj1.py --dry-run
    /opt/anaconda3/bin/python3 scripts/rejudge_recollect_rj1.py
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

from scan import load_params                                        # noqa: E402

import rejudge_seven_legs as base                                   # noqa: E402

TASK = "cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md"
SOURCE = "scan_2026-10-06_recollect"
NEW = "scan_2026-10-06_recollect_rj1"
PREDECESSOR = SOURCE
DIFF_OUT = REPO / "state" / "rejudgement_diff_2026-10-07.json"

#: The legs generation 15 versions. A rule change on any other leg is a stop.
GEN15_LEGS = ("A2", "A3", "D1")


def build(rd, params: dict, gate: dict | None) -> dict:
    dest = REPO / "state" / f"{NEW}.json"
    run = base.run_mod()
    run.refuse_clobber(dest, params)
    if dest.exists():
        raise SystemExit(f"REFUSING: {dest.relative_to(REPO)} already exists. A re-judged "
                         f"cycle never overwrites a stored payload.")
    src = base.payload(SOURCE)
    # The frame the recollection judged on, from its own record, so each surface is judged on
    # exactly the legs it was judged on (`surface_legs`).
    frame = [{"doc_id": d, "legs": list(legs)} for d, legs in src["surface_legs"].items()]
    body = rd.rejudge(src, params, cycle=NEW, control_gate=gate, frame=frame)
    body["task"] = TASK
    if body["cycle"] != NEW or body.get("scope") != "legs":
        raise SystemExit(f"REFUSING: payload names itself {body['cycle']!r} with scope "
                         f"{body.get('scope')!r}; expected {NEW!r}, a targeted cycle")
    if sorted(body["legs_collected"]) != sorted(src["legs_collected"]):
        raise SystemExit("REFUSING: the re-judgement's legs are not the recollection's")
    return body


def flips(vs_pred: dict, new: dict) -> dict:
    agency = {r["doc_id"]: r.get("agency") for r in new["matrix"]}
    per_leg, per_body, per_move = (collections.Counter() for _ in range(3))
    for m in vs_pred["changed_leg_verdict_moves"]:
        a, b = m["from"].split()[-1], m["to"].split()[-1]
        per_leg[m["leg"]] += 1
        per_body[agency.get(m["target"], "?")] += 1
        per_move[f"{a}->{b}"] += 1
    return {"per_leg": dict(sorted(per_leg.items())),
            "per_body": dict(sorted(per_body.items())),
            "per_move": dict(sorted(per_move.items())), "total": sum(per_leg.values())}


def own_stop_reasons(vs_pred: dict) -> list:
    out = []
    stray = sorted(set(vs_pred["changed_legs"]) - set(GEN15_LEGS))
    if stray:
        out.append(f"legs outside generation 15 changed rule: {stray}")
    bad = [m for m in vs_pred["changed_leg_verdict_moves"] if m["from"].split()[-1] != "pass"]
    if bad:
        out.append(f"{len(bad)} move(s) on a generation-15 leg that are not away from pass: "
                   f"{bad[:5]}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="judge, compare and re-derive; write nothing and run no control gate")
    a = ap.parse_args(argv)
    base.NEW, base.PREDECESSOR = NEW, PREDECESSOR
    rd = base.rederive_mod()
    params = load_params()
    gate = None
    if not a.dry_run:
        gate = rd.control_gate_record(params)
        print(f"CONTROL GATE: {str(gate['verdict']).upper()} — {gate['reason']}")
        print(f"  fixtures: {gate['fixtures']}")
        print(f"  unexpected: {gate['unexpected']}")
        if not gate["ok"]:
            print("re-judgement INVALID; nothing written", file=sys.stderr)
            return 2

    body = build(rd, params, gate)
    vs_pred = base.identity(base.payload(PREDECESSOR), body, PREDECESSOR, body["surface_legs"])
    rederived = rd.rederive(body, params)
    fl = flips(vs_pred, body)
    record = {"task": TASK, "cycle": NEW, "derived_from": SOURCE,
              "findings": body["findings"], "verdict_counts": body["verdict_counts"],
              "rederive": rederived,
              "distribution": {c: base.distribution(p, sorted(body["legs_collected"]))
                               for c, p in ((PREDECESSOR, base.payload(PREDECESSOR)),
                                            (NEW, body))},
              "flips": fl, "vs_predecessor": vs_pred}

    print(f"== {NEW}: {body['findings']} findings, legs judged {body['legs_judged']}")
    print(f"   rederive identical: {rederived['identical']} "
          f"({rederived['recorded']} recorded, {rederived['rederived']} re-derived)")
    print(f"   vs {PREDECESSOR}: unchanged legs {sorted(vs_pred['unchanged_legs'])}; "
          f"{vs_pred['unchanged_findings_identical']} of {vs_pred['unchanged_findings_compared']}"
          f" identical but for {base.IDENTITY_FIELDS}; "
          f"{len(vs_pred['unchanged_findings_differing'])} differ; "
          f"changed legs {sorted(vs_pred['changed_legs'])}")
    print(f"   flips: {json.dumps(fl)}")
    for leg in GEN15_LEGS:
        print(f"   {leg}: {PREDECESSOR} {record['distribution'][PREDECESSOR][leg]} -> "
              f"{NEW} {record['distribution'][NEW][leg]}")

    reasons = base.stop_reasons(vs_pred, rederived, body) + own_stop_reasons(vs_pred)
    for r in reasons:
        print(f"   STOP: {r}")
    if reasons:
        print("\nSTOPPED. No payload is written.", file=sys.stderr)
        return 1
    if a.dry_run:
        return 0
    dest = REPO / "state" / f"{NEW}.json"
    dest.write_text(json.dumps(body, indent=1, default=str) + "\n", encoding="utf-8")
    DIFF_OUT.write_text(json.dumps(record, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"-> {dest.relative_to(REPO)}")
    print(f"-> {DIFF_OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
