#!/usr/bin/env python3
"""What moved between a cycle and its re-judgement, and what moved it. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_rejudge_2_3_4.md` §1: *"which Findings moved, from what to what, and
which class moved them. Expected: every move is a `pass`/`fail` → `error` on a robots-disallowed
probe; any other move is a stop."*

A Finding's id is derived from the rule, its version, its Observations and the params hash, so a
re-judgement under new parameters mints new ids for everything: the diff cannot be by id and is
keyed on `(target_doc_id, leg)`, which is the surface and the question. The rule VERSION may also
move, and does — that is the other half of what a re-judgement is.

Each move is attributed by looking at the evidence the NEW Finding cites: which of those
Observations changed kind between the two harness versions. A move nothing explains is exactly
the stop §1 asks for, and it is reported as `unexplained` rather than summarised away.
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

from scan import errors                                             # noqa: E402


def index(payload: dict) -> dict:
    return {(f["target_doc_id"], f["leg"]): f
            for f in payload["findings_detail"]}


def explain(new_finding: dict, payload_old: dict, payload_new: dict,
            h_old: int, h_new: int) -> list:
    """The classes on this Finding's evidence whose KIND differs between the two harnesses."""
    obs = {o["obs_id"]: o for o in payload_old["observations_detail"]}
    obs.update({o["obs_id"]: o for o in payload_new.get("observations_detail", [])})
    moved = []
    for e in new_finding.get("evidence", []):
        o = obs.get(e)
        if o is None:
            continue
        cls = o.get("error_class")
        if errors.kind_of(cls, h_old) != errors.kind_of(cls, h_new):
            moved.append(cls)
    return sorted(set(moved))


def diff(old_path: Path, new_path: Path) -> dict:
    old = json.loads(old_path.read_text(encoding="utf-8"))
    new = json.loads(new_path.read_text(encoding="utf-8"))
    h_old = errors.harness_of({"harness_version": old.get("harness_version")})
    h_new = errors.harness_of({"harness_version": new.get("harness_version")})
    a, b = index(old), index(new)

    moves, unexplained = [], []
    for key in sorted(set(a) & set(b)):
        fa, fb = a[key], b[key]
        if fa["verdict"] == fb["verdict"] and fa["rule_id"] == fb["rule_id"]:
            continue
        why = explain(fb, old, new, h_old, h_new)
        row = {"target": key[0], "leg": key[1],
               "from": f"{fa['rule_id']} {fa['verdict']}",
               "to": f"{fb['rule_id']} {fb['verdict']}",
               "verdict_moved": fa["verdict"] != fb["verdict"],
               "rule_moved": fa["rule_id"] != fb["rule_id"],
               "classes_that_changed_kind": why,
               "reason": fb.get("reason", "")[:160]}
        moves.append(row)
        # §1's stop condition. A verdict move is ACCOUNTED FOR when it lands on `error` and
        # something names it: either a class on its evidence changed kind (the harness-v5 fix),
        # or the rule itself is a newer version (decision 1 re-judges under `CURRENT`, so a
        # cycle judged with A5-v1 gets A5-v2 — that is what a re-judgement IS, and the `_rj1`
        # pair did the same thing two tasks ago).
        #
        # Both causes are recorded per row so they are never pooled: "the class moved it" and
        # "a newer rule moved it" are different facts about the instrument and the RESULT
        # reports them separately.
        row["cause"] = ("class" if why else "rule_version") if row["verdict_moved"] else None
        if row["verdict_moved"] and (fb["verdict"] != "error" or not (why or row["rule_moved"])):
            unexplained.append(row)

    return {
        "old": old_path.name, "new": new_path.name,
        "harness": {"old": h_old, "new": h_new},
        "findings": {"old": len(a), "new": len(b)},
        "only_in_old": sorted(set(a) - set(b)),
        "only_in_new": sorted(set(b) - set(a)),
        "verdict_moves": sum(1 for m in moves if m["verdict_moved"]),
        "rule_version_moves": sum(1 for m in moves if m["rule_moved"]),
        "by_transition": dict(collections.Counter(
            f"{m['from'].split()[-1]} -> {m['to'].split()[-1]}"
            for m in moves if m["verdict_moved"])),
        "by_class": dict(collections.Counter(
            c for m in moves if m["verdict_moved"] for c in m["classes_that_changed_kind"])),
        "by_cause": dict(collections.Counter(
            m["cause"] for m in moves if m["verdict_moved"])),
        "unexplained": unexplained,
        "moves": moves,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pairs", nargs="+", metavar="OLD:NEW")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = []
    for pair in a.pairs:
        o, n = pair.split(":")
        out.append(diff(REPO / "state" / f"{o}.json", REPO / "state" / f"{n}.json"))
    for d in out:
        print(json.dumps({k: v for k, v in d.items()
                          if k not in ("moves", "unexplained")}, indent=1))
        if d["unexplained"]:
            print(f"  STOP: {len(d['unexplained'])} move(s) §1 does not permit:")
            for m in d["unexplained"][:8]:
                print(f"    {m['target'][:44]} {m['leg']}: {m['from']} -> {m['to']}")
    if a.out:
        (REPO / a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
        print(f"-> {a.out}", file=sys.stderr)
    return 1 if any(d["unexplained"] for d in out) else 0


if __name__ == "__main__":
    raise SystemExit(main())
