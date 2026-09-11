#!/usr/bin/env python3
"""The third re-judgement: cycles 1 to 4 under generation 9. **Zero spend. No network.**

Task `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md` decisions 1 and 2. Four stored cycles are
judged again from their own Observations under `CURRENT` — which now means `RULE-A3-v6` and
`RULE-B3-v3`, the two modules that stop an ABSENCE claim being made over a candidate set with a
blind member. Findings only: not one byte is re-fetched and not one Observation is created.

**Why a script rather than `rederive.py --under-current`.** That entry point names its output
`<cycle>_rj1` from a module constant, so a second re-judgement of the same cycle writes a payload
whose file says `_rj2` and whose `cycle` field says `_rj1` — which is what
`state/scan_2026-09-07b_rj2.json` carries today. Each cycle's suffix continues its OWN sequence
here and is passed to `rejudge(cycle=...)` explicitly, so the name inside the payload and the
name on disk are one string.

**§1 runs before anything is written.** All four are judged in memory, each is diffed against the
payload it supersedes, and a stop on any one of them writes nothing at all — not the three that
passed, not the diff. That is §3's failure clause: *"Failure writes no Results and no payloads."*

**One control gate for the task, recorded on all four.** DD-019: a cycle with zero fired controls
is invalid, and a re-judgement is licensed the same way. The gate is the eight fixtures under
this session's `CURRENT` and this session's params — one fact, and running it four times would
record it four times rather than establish it four times. Loopback only; no payload records a
request and each asserts `requests_total == 0`.

    /opt/anaconda3/bin/python3 scripts/rejudge_gen9.py --dry-run
    /opt/anaconda3/bin/python3 scripts/rejudge_gen9.py
"""
from __future__ import annotations

import argparse
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

TASK = "cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md"
DIFF_OUT = REPO / "state" / "rejudgement_diff_2026-09-11.json"

#: (source of the Observations, the new cycle's name, the payload it supersedes).
#:
#: The SOURCE is always the measured cycle, because that is the only payload that carries
#: Observations; the PREDECESSOR is the most recent judgement of the same cycle, which is what
#: §1 diffs against. They differ for every cycle here and conflating them is how a diff comes to
#: report the harness-v5 corrections a second time.
#:
#: Each name continues its own cycle's sequence — cycle 2 is on its third judgement and cycle 3
#: on its second — so the suffix is a count of judgements of THAT cycle and never a global one.
CYCLES = [
    ("scan_2026-09-07",  "scan_2026-09-07_rj2",  "scan_2026-09-07_rj1"),
    ("scan_2026-09-07b", "scan_2026-09-07b_rj3", "scan_2026-09-07b_rj2"),
    ("scan_2026-09-09",  "scan_2026-09-09_rj2",  "scan_2026-09-09_rj1"),
    ("scan_2026-09-10",  "scan_2026-09-10_rj2",  "scan_2026-09-10_rj1"),
]


def _rederive():
    spec = importlib.util.spec_from_file_location(
        "rederive_gen9", REPO / "assessment" / "harness" / "scan" / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def payload(cycle: str) -> dict:
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        raise SystemExit(f"REFUSING: {cycle} is not on disk at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def build(rd, params: dict, gate: dict | None) -> list:
    """`[(new_name, payload, diff)]` for all four, in memory. Nothing is written here."""
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
        out.append((new, body, D.diff_payloads(payload(pred), body, pred, new)))
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
        if not gate["ok"]:
            print("re-judgement INVALID; nothing written", file=sys.stderr)
            return 2

    built = build(rd, params, gate)

    stopped = False
    for new, body, d in built:
        print(f"== {new}: {body['findings']} findings, {len(d['moved_legs'])} leg(s) moved "
              f"{d['moved_legs_count']}, permitted {d['permitted_legs']}, "
              f"strict_subset={d['strict_subset_holds']}")
        for r in D.stop_reasons(d):
            stopped = True
            print(f"   STOP: {r}")
    if stopped:
        print("\n§1 STOPPED. No payload and no Result is written.", file=sys.stderr)
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
