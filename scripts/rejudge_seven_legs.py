#!/usr/bin/env python3
"""Cycle 4's fourth re-judgement, `scan_2026-09-10_rj4`: the whole current registry, the seven
new legs included, over the Observations of 2026-09-10. **Zero spend. No network.**

Task `cc_tasks/2026-09-18_rejudge_seven_legs.md` decision 1. One re-judgement under
`rules.CURRENT` as it stands: generation 11 (`RULE-B1-v1`→`v2`, `B4`, `D3`, `G4`),
generation 12 (`B2`, `B5`, `D2`) and generation 13 (`RULE-D4-v3`), with every other leg under
the rule `scan_2026-09-10_rj3` already used. Findings only: not one byte is fetched and not one
Observation is created.

**Two things differ from `rejudge_gen10.py`, and each is recorded on the payload.**

* `reread_retained=True` (`scan/reread.py`). D4's `membership` and `dcat_fields` blocks and
  A4's `content_signal` block are computed from each Observation's retained, sha256-checked
  body, with the same functions the collector now calls at collection. Without them every one
  of those rules returns `error`, "stored before the block existed", over evidence that is
  sitting in `corpus/evidence/scan/`.
* `frame=run.targets(params)`. Each surface is judged on the legs the frame gives it and on no
  other. Without that, `RULE-D2-v1` (it reads A4) lands on the six Tier C reference surfaces,
  which DD-059 limits to `tier0.legs`.

**The gate on the judgement, run before anything is written.** `stop_reasons` checks four
things, and a stop writes nothing.

1. Every Finding of a leg whose rule is the same in `_rj3` and here is identical to `_rj3`'s
   in every field but `finding_id` and `params_hash`. Those two are functions of the whole
   `params.yaml` (`model.params_hash`), and `params.yaml` has moved since `_rj3` (the
   generation-11 to -13 blocks). So "byte-identical ids" is not a property any re-judgement
   can have, and the real invariant is checked in its place (RESULT §5).
2. Such a leg judges exactly the surfaces it judged in `_rj3`, except where the frame took it
   away. Each of those exceptions is listed with its reason.
3. The payload re-derives byte-identically through `rederive.rederive` (DD-041).
4. It carries no Observation and records no request.

    /opt/anaconda3/bin/python3 scripts/rejudge_seven_legs.py --dry-run
    /opt/anaconda3/bin/python3 scripts/rejudge_seven_legs.py
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-09-18_rejudge_seven_legs.md"
SOURCE = "scan_2026-09-10"
NEW = "scan_2026-09-10_rj4"
PREDECESSOR = "scan_2026-09-10_rj3"
#: The published report's snapshot (`docs/reports/publication.yaml`), compared too, because
#: decision 1 names it and §4 sets the two side by side.
SNAPSHOT = "scan_2026-09-10_rj2"
DIFF_OUT = REPO / "state" / "rejudgement_diff_2026-09-18.json"

#: The fields a Finding's identity is made of and that a parameter change moves by construction.
#: Everything else a Finding carries is compared.
IDENTITY_FIELDS = ("finding_id", "params_hash")


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rederive_mod():
    return _mod("rederive_rj7", REPO / "assessment" / "harness" / "scan" / "rederive.py")


def run_mod():
    return _mod("run_rj7", REPO / "assessment" / "harness" / "scan" / "run.py")


def payload(cycle: str) -> dict:
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        raise SystemExit(f"REFUSING: {cycle} is not on disk at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def rules_of(p: dict) -> dict:
    out: dict = {}
    for f in p["findings_detail"]:
        out.setdefault(f["leg"], set()).add(f["rule_id"])
    return {leg: sorted(r) for leg, r in out.items()}


def _strip(f: dict) -> dict:
    return {k: v for k, v in f.items() if k not in IDENTITY_FIELDS}


def identity(old: dict, new: dict, old_name: str, surface_legs: dict) -> dict:
    """Per leg whose rule is the same in `old` and `new`: how many Findings are identical in
    every field but the two identity fields, which differ, and which (surface, leg) cells one
    judged and the other did not, each with the reason the frame gives.

    Legs whose rule changed are listed apart with their verdict moves. Those are the legs the
    re-judgement exists to move."""
    ro, rn = rules_of(old), rules_of(new)
    a = {(f["target_doc_id"], f["leg"]): f for f in old["findings_detail"]}
    b = {(f["target_doc_id"], f["leg"]): f for f in new["findings_detail"]}
    unchanged = sorted(l for l in set(ro) & set(rn) if ro[l] == rn[l])
    changed = sorted(l for l in set(ro) & set(rn) if ro[l] != rn[l])
    new_legs = sorted(set(rn) - set(ro))
    per_leg, differing, only_old, only_new = {}, [], [], []
    for leg in unchanged:
        keys_a = {k for k in a if k[1] == leg}
        keys_b = {k for k in b if k[1] == leg}
        same = 0
        for k in sorted(keys_a & keys_b):
            if _strip(a[k]) == _strip(b[k]):
                same += 1
            else:
                differing.append({"target": k[0], "leg": leg,
                                  "fields": sorted(f for f in set(a[k]) | set(b[k])
                                                   if f not in IDENTITY_FIELDS
                                                   and a[k].get(f) != b[k].get(f))})
        for k in sorted(keys_a - keys_b):
            legs_here = surface_legs.get(k[0])
            only_old.append({"target": k[0], "leg": leg,
                             "why": ("the frame does not put this leg on this surface "
                                     f"(its legs: {legs_here})" if legs_here is not None
                                     else "the surface is not in the frame")})
        for k in sorted(keys_b - keys_a):
            only_new.append({"target": k[0], "leg": leg})
        per_leg[leg] = {"rule": ro[leg], "compared": len(keys_a & keys_b), "identical": same,
                        "only_in_old": len(keys_a - keys_b), "only_in_new": len(keys_b - keys_a)}
    moves = []
    for leg in changed:
        for k in sorted(k for k in set(a) & set(b) if k[1] == leg):
            if a[k]["verdict"] != b[k]["verdict"]:
                moves.append({"target": k[0], "leg": leg,
                              "from": f"{a[k]['rule_id']} {a[k]['verdict']}",
                              "to": f"{b[k]['rule_id']} {b[k]['verdict']}",
                              "reason": b[k]["reason"][:400]})
    return {"old": old_name, "new": NEW,
            "unchanged_legs": per_leg,
            "unchanged_findings_compared": sum(v["compared"] for v in per_leg.values()),
            "unchanged_findings_identical": sum(v["identical"] for v in per_leg.values()),
            "unchanged_findings_differing": differing,
            "cells_only_in_old": only_old, "cells_only_in_new": only_new,
            "changed_legs": {l: {"old": ro[l], "new": rn[l]} for l in changed},
            "changed_leg_verdict_moves": moves,
            "new_legs": {l: rn[l] for l in new_legs},
            "params_hash": {"old": old.get("params_hash"), "new": new.get("params_hash")}}


def distribution(p: dict, legs) -> dict:
    c = collections.Counter((f["leg"], f["verdict"]) for f in p["findings_detail"])
    return {l: {v: c[(l, v)] for v in ("pass", "fail", "not_applicable", "error")}
            for l in legs}


def stop_reasons(vs_pred: dict, rederived: dict, body: dict) -> list:
    out = []
    if vs_pred["unchanged_findings_differing"]:
        out.append(f"{len(vs_pred['unchanged_findings_differing'])} Finding(s) of an unchanged "
                   f"leg differ from {PREDECESSOR} beyond the identity fields: "
                   f"{vs_pred['unchanged_findings_differing'][:5]}")
    if vs_pred["cells_only_in_new"]:
        out.append(f"an unchanged leg judges {len(vs_pred['cells_only_in_new'])} surface(s) "
                   f"{PREDECESSOR} did not: {vs_pred['cells_only_in_new'][:5]}")
    unexplained = [c for c in vs_pred["cells_only_in_old"]
                   if not c["why"].startswith("the frame does not put")]
    if unexplained:
        out.append(f"{len(unexplained)} cell(s) of an unchanged leg are gone with no frame "
                   f"reason: {unexplained[:5]}")
    if not rederived["identical"]:
        out.append(f"the payload does not re-derive byte-identically: "
                   f"{json.dumps(rederived)[:600]}")
    if body["observations_detail"] or body["requests_total"]:
        out.append("the payload records evidence or a request; a re-judgement creates neither")
    return out


def build(rd, params: dict, gate: dict | None) -> tuple:
    dest = REPO / "state" / f"{NEW}.json"
    run = run_mod()
    # `refuse_clobber` is the runner's guard and it refuses only a payload under DIFFERENT
    # params. A re-judgement refuses ANY existing payload of its name: a second run has nothing
    # to add to the first, and the first is the record.
    run.refuse_clobber(dest, params)
    if dest.exists():
        raise SystemExit(f"REFUSING: {dest.relative_to(REPO)} already exists. A re-judged "
                         f"cycle never overwrites a stored payload.")
    src = payload(SOURCE)
    if src.get("targets") != params["cycle"]["targets"]:
        raise SystemExit(
            f"REFUSING: {SOURCE} was measured over {src.get('targets')!r} and params bind "
            f"{params['cycle']['targets']!r}; the frame's legs per surface would be another "
            f"frame's")
    frame = run.targets(params)
    body = rd.rejudge(src, params, cycle=NEW, control_gate=gate, reread_retained=True,
                      frame=frame)
    body["task"] = TASK
    if body["cycle"] != NEW:
        raise SystemExit(f"REFUSING: payload names itself {body['cycle']!r}, not {NEW!r}")
    return body


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="judge, compare and re-derive; write nothing and run no control "
                         "gate, so a dry run is never mistaken for a licensed one")
    a = ap.parse_args(argv)

    rd = rederive_mod()
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
    vs_pred = identity(payload(PREDECESSOR), body, PREDECESSOR, body["surface_legs"])
    vs_snap = identity(payload(SNAPSHOT), body, SNAPSHOT, body["surface_legs"])
    rederived = rd.rederive(body, params)
    new_legs = sorted(vs_pred["new_legs"])
    record = {"task": TASK, "cycle": NEW, "derived_from": SOURCE,
              "findings": body["findings"], "verdict_counts": body["verdict_counts"],
              "observations_reread": body["observations_reread"],
              "rederive": rederived,
              "distribution_new_legs": distribution(body, new_legs),
              "distribution_d4": {c: distribution(payload(c), ["D4"])["D4"]
                                  for c in (SNAPSHOT, PREDECESSOR)} | {
                  NEW: distribution(body, ["D4"])["D4"]},
              "vs_predecessor": vs_pred, "vs_snapshot": vs_snap}

    print(f"== {NEW}: {body['findings']} findings, legs judged {len(body['legs_judged'])}")
    print(f"   re-read: {body['observations_reread']['observations_reread']}")
    print(f"   rederive identical: {rederived['identical']} "
          f"({rederived['recorded']} recorded, {rederived['rederived']} re-derived)")
    for name, d in ((PREDECESSOR, vs_pred), (SNAPSHOT, vs_snap)):
        print(f"   vs {name}: unchanged legs {sorted(d['unchanged_legs'])}; "
              f"{d['unchanged_findings_identical']} of {d['unchanged_findings_compared']} "
              f"identical but for {IDENTITY_FIELDS}; "
              f"{len(d['unchanged_findings_differing'])} differ; "
              f"{len(d['cells_only_in_old'])} cell(s) only in {name}; "
              f"changed legs {d['changed_legs']}; "
              f"{len(d['changed_leg_verdict_moves'])} verdict move(s) on changed legs")
    print(f"   new legs: {record['distribution_new_legs']}")
    print(f"   D4: {record['distribution_d4']}")
    for m in vs_pred["changed_leg_verdict_moves"]:
        print(f"   MOVE {m['leg']} {m['target']}: {m['from']} -> {m['to']}")

    reasons = stop_reasons(vs_pred, rederived, body)
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
