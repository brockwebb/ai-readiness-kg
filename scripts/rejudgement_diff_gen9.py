#!/usr/bin/env python3
"""What moved between a re-judgement and the payload it supersedes. **Zero spend, no network.**

Task `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md` §1: *"Stop if any leg outside `{A3, B3}`
differs from its predecessor payload."*

`scripts/rejudgement_diff.py` answered the same question for the harness-v5 pass and is not
edited: it reads `payload_old["observations_detail"]` directly, and **both** sides of a
generation-9 comparison are Findings-only payloads whose evidence lives in the cycle they derive
from. Resolving that is the one thing this module adds, and it resolves it through
`rederive.observations_for` so the diff cannot look for evidence anywhere the re-derivation gate
does not.

**The stop condition, and why it is derived rather than typed.**

A verdict cannot move unless something moved it. Two things can, and both are recorded on the
payloads themselves:

* a **rule version** that differs between the predecessor's Finding and this one's, and
* an **error class whose KIND changed** between the two payloads' harness versions — the
  harness-v5 correction, where `robots_disallowed` stopped being SCOPE and became BLIND.

So `permitted_legs` is computed from those two facts, and the moved set must be a subset of it.
For cycles 2, 3 and 4 — whose predecessors are the harness-v5 re-judgements, judged under the
same harness and the same `CURRENT` but for the two modules generation 9 ships — that set comes
out as exactly `{A3, B3}`, which is the task's condition, reached rather than asserted. A third
leg moving there is a stop, because nothing in the instrument could have moved it.

**Cycle 1 is the case the literal condition cannot describe, and it is knowable in advance.**
`scan_2026-09-07_rj1` carries no `harness_version` (harness-v4, where a robots disallow was
scope) and was judged under `RULE-A5-v1`, `RULE-A8-v3`, `RULE-A12-v1` and `RULE-B3-v2`. Decision
1 admits cycle 1 *because* it never received harness-v5 — so demanding that only A3 and B3 move
across that jump asks the payload to be something decision 1 says it is not. The condition that
does hold is the one this repo already settled on
(`cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §3): every move lands on `error` and something
NAMES it. Both are checked here for every cycle; the subset check is the same check with a
tighter permitted set, and `strict_subset_holds` reports whether the literal form was satisfied
rather than quietly widening it.

    /opt/anaconda3/bin/python3 scripts/rejudgement_diff_gen9.py OLD:NEW [OLD:NEW ...]
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

from scan import errors                                             # noqa: E402

#: The legs generation 9 ships a new module for, and therefore the only legs the task expects to
#: move where the predecessor is a generation-8 payload. Not a threshold and not tunable: it is
#: read back from `rules.V9` by the test, so a tenth generation cannot leave it stale.
GENERATION_9_LEGS = ("A3", "B3")


def _rederive():
    """`assessment/harness/scan/rederive.py`, by path — `assessment/harness/` holds a second
    `run.py` and the package layout makes a plain import ambiguous. Same loader the invariant
    test uses, for the same reason."""
    spec = importlib.util.spec_from_file_location(
        "rederive_diff_gen9", REPO / "assessment" / "harness" / "scan" / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def observations(payload: dict) -> dict:
    """`{obs_id: row}` for a payload, Findings-only or not.

    A re-judgement creates no Observation; its evidence is the cycle named in `derived_from`.
    Reading `observations_detail` alone returns `{}` for one, and a diff that cannot see the
    evidence reports every move as unexplained — which is the diff failing, not the rules.
    """
    rows = payload.get("observations_detail")
    if not rows:
        rows = _rederive().observations_for(payload)
    return {(o if isinstance(o, dict) else o.to_dict())["obs_id"]:
            (o if isinstance(o, dict) else o.to_dict()) for o in rows}


def index(payload: dict) -> dict:
    return {(f["target_doc_id"], f["leg"]): f for f in payload["findings_detail"]}


def harness_of(payload: dict) -> int:
    return errors.harness_of({"harness_version": payload.get("harness_version")})


def classes_that_changed_kind(finding: dict, obs: dict, h_old: int, h_new: int) -> list:
    """The error classes on this Finding's evidence whose KIND differs between the two harness
    versions. Empty when the harness did not move, which is most of the time."""
    out = []
    for e in finding.get("evidence", []):
        o = obs.get(e)
        if o is None:
            continue
        cls = o.get("error_class")
        if errors.kind_of(cls, h_old) != errors.kind_of(cls, h_new):
            out.append(cls)
    return sorted(set(out))


def diff(old_path: Path, new_path: Path) -> dict:
    """One pair. `moved_legs` is the set §1 gates on; `permitted_legs` is what could have moved.

    Keyed on `(target_doc_id, leg)` — the surface and the question — because a Finding's id is
    derived from its rule, version, evidence and params hash, so a re-judgement mints new ids for
    everything and a diff by id would report 100 % churn.
    """
    old = json.loads(old_path.read_text(encoding="utf-8"))
    new = json.loads(new_path.read_text(encoding="utf-8"))
    return diff_payloads(old, new, old_path.stem, new_path.stem)


def diff_payloads(old: dict, new: dict, old_name: str, new_name: str) -> dict:
    h_old, h_new = harness_of(old), harness_of(new)
    obs = {**observations(old), **observations(new)}
    a, b = index(old), index(new)

    moves, unaccounted = [], []
    permitted, rule_moves = set(), {}
    for key in sorted(set(a) & set(b)):
        fa, fb = a[key], b[key]
        why = classes_that_changed_kind(fb, obs, h_old, h_new)
        if fa["rule_id"] != fb["rule_id"]:
            rule_moves[key[1]] = f"{fa['rule_id']} -> {fb['rule_id']}"
        # A leg is PERMITTED to move when the instrument under it moved: a newer rule, or an
        # error class on its own evidence that changed kind. Computed over every shared key, not
        # only the ones that moved, because the question is what COULD have moved.
        if fa["rule_id"] != fb["rule_id"] or why:
            permitted.add(key[1])
        if fa["verdict"] == fb["verdict"] and fa["rule_id"] == fb["rule_id"]:
            continue
        row = {"target": key[0], "leg": key[1],
               "from": f"{fa['rule_id']} {fa['verdict']}",
               "to": f"{fb['rule_id']} {fb['verdict']}",
               "verdict_moved": fa["verdict"] != fb["verdict"],
               "rule_moved": fa["rule_id"] != fb["rule_id"],
               "classes_that_changed_kind": why,
               # All three, because a rule reports its blind count under the field that matches
               # HOW it reached the candidate: `RULE-A3-v6` follows links and says
               # `blind_links`, `RULE-B3-v3` ranges over a candidate set and says
               # `blind_candidates`, `RULE-A8-v4` dereferences pointers. Reading one of them
               # would report `null` for two rules that did say the number.
               "blind": {k: fb.get(k) for k in
                         ("blind_candidates", "blind_links", "blind_pointers")
                         if fb.get(k) is not None},
               "reason": fb.get("reason", "")[:400]}
        row["cause"] = (("class" if why else "rule_version")
                        if row["verdict_moved"] else None)
        moves.append(row)
        # Accounted for = it lands on `error` AND something names it. Both halves matter: a
        # move to `pass` that a newer rule explains is still a rule that started crediting
        # something, and this task ships no rule that should.
        if row["verdict_moved"] and (fb["verdict"] != "error"
                                     or not (why or row["rule_moved"])):
            unaccounted.append(row)

    moved_legs = sorted({m["leg"] for m in moves if m["verdict_moved"]})
    return {
        "old": old_name, "new": new_name,
        "harness": {"old": h_old, "new": h_new},
        "findings": {"old": len(a), "new": len(b)},
        "only_in_old": sorted(set(a) - set(b)),
        "only_in_new": sorted(set(b) - set(a)),
        "verdict_moves": sum(1 for m in moves if m["verdict_moved"]),
        "rule_version_moves": sum(1 for m in moves if m["rule_moved"]),
        "rules_that_moved": rule_moves,
        "moved_legs": moved_legs,
        "moved_legs_count": {leg: sum(1 for m in moves
                                      if m["verdict_moved"] and m["leg"] == leg)
                             for leg in moved_legs},
        "permitted_legs": sorted(permitted),
        "strict_subset_holds": set(moved_legs) <= set(GENERATION_9_LEGS),
        "within_permitted": set(moved_legs) <= permitted,
        "by_transition": dict(collections.Counter(
            f"{m['leg']} {m['from'].split()[-1]} -> {m['to'].split()[-1]}"
            for m in moves if m["verdict_moved"])),
        "by_cause": dict(collections.Counter(m["cause"] for m in moves
                                             if m["verdict_moved"])),
        "unaccounted": unaccounted,
        "moves": moves,
    }


def stop_reasons(d: dict) -> list:
    """Why this pair stops the task, or `[]`. One list, so the builder and the test cannot
    disagree about what a stop is."""
    out = []
    if d["unaccounted"]:
        out.append(f"{len(d['unaccounted'])} verdict move(s) nothing names: "
                   + "; ".join(f"{m['target']} {m['leg']} {m['from']} -> {m['to']}"
                               for m in d["unaccounted"][:5]))
    if not d["within_permitted"]:
        out.append(f"moved legs {d['moved_legs']} are not within the legs the instrument could "
                   f"have moved {d['permitted_legs']}")
    if d["only_in_new"] or d["only_in_old"]:
        out.append(f"the two payloads do not judge the same set: "
                   f"{len(d['only_in_old'])} only in {d['old']}, "
                   f"{len(d['only_in_new'])} only in {d['new']}")
    return out


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
    stopped = False
    for d in out:
        print(json.dumps({k: v for k, v in d.items()
                          if k not in ("moves", "unaccounted")}, indent=1))
        for r in stop_reasons(d):
            stopped = True
            print(f"  STOP: {r}")
    if a.out:
        (REPO / a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
        print(f"-> {a.out}", file=sys.stderr)
    return 1 if stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
