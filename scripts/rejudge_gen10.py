#!/usr/bin/env python3
"""The fourth re-judgement: cycles 1-4 and the self cycle under generation 10. **Zero spend. No
network.**

Task `cc_tasks/2026-09-13_rule_a12_v3.md` decision 3. Five stored cycles are judged again from
their own Observations under `CURRENT` — which now means `RULE-A12-v3` — and under
`params.reason_text: 2`, which corrects what `_common.unobserved_error` prints. Findings only:
not one byte is re-fetched and not one Observation is created.

**This generation's gate is ZERO verdict moves, and that is stricter than every re-judgement
before it.** Generations 5 to 9 each corrected a JUDGEMENT and the gate was "every move lands on
`error` and something names it". Generation 10 corrects two SENTENCES; a verdict that moved would
mean the rule change reached further than its reason string, which is the one thing it must not
do. `stop_reasons` here is therefore its own function and not `rejudgement_diff_gen9`'s — the
diff MACHINERY is shared (a second copy of "what moved between two payloads" is a second thing to
be wrong), the stop condition is not.

**§1 runs before anything is written.** All five are judged in memory, each is diffed against the
payload it supersedes, and a stop on any one of them writes nothing at all.

**One control gate for the task, recorded on all five.** Nine fixtures now: the ninth,
`robots_404_html`, is the control this task adds and the first that can produce the evidence
`RULE-A12-v2` misdescribes. Loopback only; every payload asserts `requests_total == 0`.

    /opt/anaconda3/bin/python3 scripts/rejudge_gen10.py --dry-run
    /opt/anaconda3/bin/python3 scripts/rejudge_gen10.py
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import rejudgement_diff_gen9 as D                                   # noqa: E402
from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-09-13_rule_a12_v3.md"
DIFF_OUT = REPO / "state" / "rejudgement_diff_2026-09-13.json"

#: (source of the Observations, the new cycle's name, the payload it supersedes).
#:
#: The SOURCE is always the measured cycle — the only payload that carries Observations — and the
#: PREDECESSOR is the most recent judgement of the same cycle, which is what the diff is against.
#: Each name continues its OWN cycle's sequence, so the suffix counts judgements of that cycle
#: and never of the task: cycle 2 is on its fourth, cycles 1, 3 and 4 on their third, and the
#: self cycle on its first.
CYCLES = [
    ("scan_2026-09-07",  "scan_2026-09-07_rj3",  "scan_2026-09-07_rj2"),
    ("scan_2026-09-07b", "scan_2026-09-07b_rj4", "scan_2026-09-07b_rj3"),
    ("scan_2026-09-09",  "scan_2026-09-09_rj3",  "scan_2026-09-09_rj2"),
    ("scan_2026-09-10",  "scan_2026-09-10_rj3",  "scan_2026-09-10_rj2"),
    # The self cycle's first re-judgement: its predecessor IS the measured payload, because
    # nothing has judged it since it was measured yesterday.
    ("self_2026-09-13",  "self_2026-09-13_rj1",  "self_2026-09-13"),
]


def _rederive():
    spec = importlib.util.spec_from_file_location(
        "rederive_gen10", REPO / "assessment" / "harness" / "scan" / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def payload(cycle: str) -> dict:
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        raise SystemExit(f"REFUSING: {cycle} is not on disk at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def reason_only_changes(d: dict) -> dict:
    """Per leg, the Findings whose VERDICT is unchanged and whose REASON moved.

    This is the deliverable. A generation that changes sentences has to be able to say which
    sentences, and "the payload is 500 lines different" is not an answer — a re-judgement mints
    a new `finding_id` for every Finding it writes, so a byte diff of the payloads says nothing.
    Keyed on `(surface, leg)`, the same key the diff uses, for the same reason.
    """
    out = collections.Counter()
    for m in d["moves"]:
        if not m["verdict_moved"]:
            out[m["leg"]] += 1
    return dict(sorted(out.items()))


def diff_with_reasons(old: dict, new: dict, old_name: str, new_name: str) -> dict:
    """`rejudgement_diff_gen9.diff_payloads`, plus the reason-level detail this task reports.

    `diff_payloads` records a move when the verdict OR the rule id changed, which is what a
    judgement-level diff needs. A sentence-level one needs the reasons themselves, so they are
    added here rather than by editing that module: it is the record of the generation-9 pass and
    three RESULTs cite its output.
    """
    d = D.diff_payloads(old, new, old_name, new_name)
    a, b = D.index(old), D.index(new)
    reasons = []
    for key in sorted(set(a) & set(b)):
        fa, fb = a[key], b[key]
        if fa["verdict"] == fb["verdict"] and fa["reason"] != fb["reason"]:
            reasons.append({"target": key[0], "leg": key[1], "verdict": fa["verdict"],
                            "rule": f"{fa['rule_id']} -> {fb['rule_id']}",
                            "from": fa["reason"], "to": fb["reason"]})
    d["reason_only_changes"] = len(reasons)
    d["reason_only_changes_by_leg"] = dict(sorted(
        collections.Counter(r["leg"] for r in reasons).items()))
    d["reason_changes"] = reasons
    return d


def stop_reasons(d: dict) -> list:
    """Why this pair stops the task, or `[]`. **Zero verdict moves**, and the two structural
    checks every re-judgement owes."""
    out = []
    if d["verdict_moves"]:
        out.append(
            f"{d['verdict_moves']} verdict move(s) on legs {d['moved_legs']}: generation 10 "
            f"changes sentences, not judgements, so ANY move is a stop — "
            + "; ".join(f"{m['target']} {m['leg']} {m['from']} -> {m['to']}"
                        for m in d["moves"] if m["verdict_moved"])[:400])
    if d["only_in_new"] or d["only_in_old"]:
        out.append(f"the two payloads do not judge the same set: "
                   f"{len(d['only_in_old'])} only in {d['old']}, "
                   f"{len(d['only_in_new'])} only in {d['new']}")
    return out


def build(rd, params: dict, gate: dict | None) -> list:
    """`[(new_name, payload, diff)]` for all five, in memory. Nothing is written here."""
    out = []
    for src, new, pred in CYCLES:
        dest = REPO / "state" / f"{new}.json"
        if dest.exists():
            raise SystemExit(
                f"REFUSING: {dest.relative_to(REPO)} already exists. A re-judged cycle is a new "
                f"cycle and never overwrites a stored payload; if this task is being re-run, the "
                f"previous run's payloads are the record and this one has nothing to add.")
        body = rd.rejudge(payload(src), params, cycle=new, control_gate=gate)
        if body["cycle"] != new:
            raise SystemExit(f"REFUSING: payload names itself {body['cycle']!r}, not {new!r}")
        if body["observations_detail"] or body["requests_total"]:
            raise SystemExit(f"REFUSING: {new} records evidence or a request; a re-judgement "
                             f"creates neither")
        out.append((new, body, diff_with_reasons(payload(pred), body, pred, new)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="judge and diff, write nothing — including no control gate, so a "
                         "dry run is never mistaken for a licensed one")
    a = ap.parse_args(argv)

    rd = _rederive()
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

    built = build(rd, params, gate)

    stopped = False
    for new, body, d in built:
        print(f"== {new}: {body['findings']} findings, {d['verdict_moves']} verdict move(s), "
              f"{d['reason_only_changes']} reason-only change(s) "
              f"{d['reason_only_changes_by_leg']}")
        for r in stop_reasons(d):
            stopped = True
            print(f"   STOP: {r}")
    if stopped:
        print("\n§2 STOPPED. No payload is written.", file=sys.stderr)
        return 1
    if a.dry_run:
        return 0

    for new, body, _d in built:
        dest = REPO / "state" / f"{new}.json"
        dest.write_text(json.dumps(body, indent=1, default=str) + "\n", encoding="utf-8")
        print(f"-> {dest.relative_to(REPO)}")
    DIFF_OUT.write_text(json.dumps([d for _n, _b, d in built], indent=1) + "\n",
                        encoding="utf-8")
    print(f"-> {DIFF_OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
