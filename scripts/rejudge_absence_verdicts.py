#!/usr/bin/env python3
"""Cycle 4's fifth re-judgement, `scan_2026-09-10_rj5`: generation 14 over the Observations of
2026-09-10. **Zero spend. No network.**

Task `cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 6, DN-012 d1 to d3. One
re-judgement under `rules.CURRENT` as it stands. The twelve generation-14 rules
(A1, A2, A3, A9, B1, B3, B4, D1, D3, D4, F4, G4) are judged under their new versions, and every
other leg under the rule `scan_2026-09-10_rj4` used. Findings only: not one byte is fetched and
not one Observation is created.

**What differs from `rejudge_seven_legs.py`.** The re-read is scheme 2 (`scan/reread.py`). It
puts on each stored Observation what the collector now records at collection: the
`link_candidates` accounting on each link-probe page (DN-012 d2), computed from the page's own
`parsed.links`, and the body's `declared` block on every leg that reads a declared location
(DN-012 d3), from `targets.yaml` `declared_locations`. The declarations are COPIED onto the
payload's `observations_reread`, so a later edit to `targets.yaml` cannot move this payload's
re-derivation.

**The gate on the judgement, run before anything is written.** `stop_reasons` checks the same
four things `rejudge_seven_legs.py` does, and a stop writes nothing:

1. Every Finding of a leg whose rule is unchanged since `_rj4` is identical to `_rj4`'s in every
   field but `finding_id` and `params_hash`, both functions of the whole `params.yaml`.
2. Such a leg judges exactly the surfaces it judged in `_rj4`.
3. The payload re-derives byte-identically (DD-041).
4. It carries no Observation and records no request.

It also checks one thing of its own: no verdict on a changed leg moves AWAY from `error` or
INTO `pass`. Generation 14 changes absence branches only, so the one legal move is `fail` to
`error`.

    /opt/anaconda3/bin/python3 scripts/rejudge_absence_verdicts.py --dry-run
    /opt/anaconda3/bin/python3 scripts/rejudge_absence_verdicts.py
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

from scan import declarations, load_params                          # noqa: E402

import rejudge_seven_legs as base                                   # noqa: E402

TASK = "cc_tasks/2026-10-06_absence_verdicts_rules.md"
SOURCE = "scan_2026-09-10"
NEW = "scan_2026-09-10_rj5"
#: The predecessor and the published report's snapshot (`docs/reports/publication.yaml`) are the
#: same judgement here.
PREDECESSOR = "scan_2026-09-10_rj4"
DIFF_OUT = REPO / "state" / "rejudgement_diff_2026-10-06.json"

#: The legs generation 14 versions. A move on any other leg is a stop.
GEN14_LEGS = ("A1", "A2", "A3", "A9", "B1", "B3", "B4", "D1", "D3", "D4", "F4", "G4")


def declared_for(src: dict, frame: list) -> dict:
    """`{"block": ..., "bodies": {doc_id: body}}`: the declarations this re-judgement applies,
    and which body each surface belongs to, from the frame `run.targets` builds today."""
    bodies = {t["doc_id"]: t["agency"] for t in frame}
    missing = sorted({r["doc_id"] for r in src.get("matrix") or []} - set(bodies))
    if missing:
        raise SystemExit(f"REFUSING: {len(missing)} surface(s) of {SOURCE} are not in the frame, "
                         f"so their body is unknown: {missing[:5]}")
    return {"block": declarations.load(), "bodies": bodies}


def build(rd, params: dict, gate: dict | None) -> dict:
    dest = REPO / "state" / f"{NEW}.json"
    run = base.run_mod()
    run.refuse_clobber(dest, params)
    if dest.exists():
        raise SystemExit(f"REFUSING: {dest.relative_to(REPO)} already exists. A re-judged "
                         f"cycle never overwrites a stored payload.")
    src = base.payload(SOURCE)
    if src.get("targets") != params["cycle"]["targets"]:
        raise SystemExit(f"REFUSING: {SOURCE} was measured over {src.get('targets')!r} and "
                         f"params bind {params['cycle']['targets']!r}")
    frame = run.targets(params)
    body = rd.rejudge(src, params, cycle=NEW, control_gate=gate, reread_retained=True,
                      frame=frame, declared=declared_for(src, frame))
    body["task"] = TASK
    if body["cycle"] != NEW:
        raise SystemExit(f"REFUSING: payload names itself {body['cycle']!r}, not {NEW!r}")
    return body


def flips(vs_pred: dict, new: dict) -> dict:
    """Verdict moves on the generation-14 legs, per leg, per body and per move."""
    agency = {r["doc_id"]: r.get("agency") for r in new["matrix"]}
    per_leg = collections.Counter()
    per_body = collections.Counter()
    per_move = collections.Counter()
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
    stray = sorted(set(vs_pred["changed_legs"]) - set(GEN14_LEGS))
    if stray:
        out.append(f"legs outside generation 14 changed rule: {stray}")
    bad = [m for m in vs_pred["changed_leg_verdict_moves"]
           if (m["from"].split()[-1], m["to"].split()[-1]) != ("fail", "error")]
    if bad:
        out.append(f"{len(bad)} move(s) on a generation-14 leg other than fail -> error: "
                   f"{bad[:5]}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="judge, compare and re-derive; write nothing and run no control gate")
    a = ap.parse_args(argv)
    # The base script's identity() names its own cycle on the record; point it at this one.
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
              "observations_reread": {k: v for k, v in body["observations_reread"].items()
                                      if k != "declared"},
              "rederive": rederived,
              "distribution_gen14": {c: base.distribution(base.payload(c), GEN14_LEGS)
                                     for c in (PREDECESSOR,)} | {
                  NEW: base.distribution(body, GEN14_LEGS)},
              "flips": fl, "vs_predecessor": vs_pred}

    print(f"== {NEW}: {body['findings']} findings, legs judged {len(body['legs_judged'])}")
    print(f"   re-read: {body['observations_reread']['observations_reread']}")
    print(f"   declared re-read: {body['observations_reread']['declared_reread']}")
    print(f"   rederive identical: {rederived['identical']} "
          f"({rederived['recorded']} recorded, {rederived['rederived']} re-derived)")
    print(f"   vs {PREDECESSOR}: unchanged legs {sorted(vs_pred['unchanged_legs'])}; "
          f"{vs_pred['unchanged_findings_identical']} of {vs_pred['unchanged_findings_compared']}"
          f" identical but for {base.IDENTITY_FIELDS}; "
          f"{len(vs_pred['unchanged_findings_differing'])} differ; "
          f"{len(vs_pred['cells_only_in_old'])} cell(s) only in {PREDECESSOR}; "
          f"changed legs {sorted(vs_pred['changed_legs'])}")
    print(f"   flips: {json.dumps(fl)}")
    for leg in GEN14_LEGS:
        print(f"   {leg}: {PREDECESSOR} {record['distribution_gen14'][PREDECESSOR][leg]} -> "
              f"{NEW} {record['distribution_gen14'][NEW][leg]}")

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
