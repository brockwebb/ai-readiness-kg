#!/usr/bin/env python3
"""Move an indicator to `measurement_status: measured` when the cycle earned it. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_run.md` §0 and §5. `measured` has a definition and this script
is it, so the word cannot drift:

    a cycle with FIRED CONTROLS produced, for that indicator's AUTO leg, at least one
    `pass`/`fail`/`not_applicable` Finding on an **admitted, observable** surface under
    `CURRENT` rules, with the evidence bytes committed and the Finding re-derivable.

Four things that definition deliberately excludes, each of which would otherwise be a way to
claim a measurement nobody made:

* **`error` does not count.** `error` means the collector could not observe. A leg that
  errored on every surface has measured nothing, however many Findings it produced.
* **An unadmitted surface does not count.** No `:Document`, no `OBSERVED_ON`, nothing to trace.
* **A cycle whose controls did not fire does not count** — it is INVALID (DD-019), and an
  invalid cycle cannot promote anything.
* **A candidate indicator never moves.** A12 stays `candidate` whatever it observed (DD-054);
  `measured` is a claim about the framework, and the framework has not adopted it.

An indicator that does NOT meet the bar keeps `harness_built` and the reason is recorded on
the node, because "why is A2 not measured" is the first question a reader of the progress page
will have and the answer should not require re-deriving the cycle.

    /opt/anaconda3/bin/python3 scripts/framework_writeback_measured.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw                                    # noqa: E402
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan.rules import CANDIDATE_LEGS, CURRENT                     # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_run.md"
SCRIPT = "scripts/framework_writeback_measured.py"
CYCLE = "scan_2026-09-07"
PAYLOAD = REPO / "state" / f"{CYCLE}.json"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
COUNTS_AS_MEASURED = ("pass", "fail", "not_applicable")


def evidence(payload: dict) -> dict:
    """Per leg: what this cycle actually produced on admitted product surfaces."""
    rows = [r for r in payload["matrix"]
            if r["surface_kind"] != "well_known" and r.get("admitted")]
    out = {}
    for leg in CURRENT:
        v = [r["verdicts"][leg] for r in rows if leg in r["verdicts"]]
        c = collections.Counter(v)
        out[leg] = {"counts": {k: c[k] for k in ("pass", "fail", "not_applicable", "error")},
                    "qualifying": sum(c[k] for k in COUNTS_AS_MEASURED),
                    "surfaces": len(v)}
    return out


def writeback(g: dict, payload: dict, ev: dict) -> dict:
    if payload.get("control_verdict") != "pass":
        raise SystemExit(f"REFUSING: the cycle's controls did not fire "
                         f"({payload.get('control_verdict')!r}); an INVALID cycle promotes "
                         f"nothing (DD-019)")
    specs = [n["properties"] for n in g["nodes"] if "MeasurementSpec" in n["labels"]]
    leg_of = collections.defaultdict(list)
    for s in specs:
        if s.get("leg"):
            leg_of[s["indicator_code"]].append(s["leg"])
    promoted, held = [], []
    for n in g["nodes"]:
        if "AssessmentIndicator" not in n["labels"]:
            continue
        p = n["properties"]
        code = p.get("code")
        if p.get("status") == "candidate":
            held.append((code, "candidate — `measured` is a claim about the framework, and "
                               "the framework has not adopted it (DD-054)"))
            continue
        legs = [l for l in leg_of.get(code, []) if l in CURRENT and l not in CANDIDATE_LEGS]
        # An indicator split into legs (G1) is measured when ANY leg with a current rule is.
        legs = legs or [l for l in leg_of.get(code, []) if l in CURRENT]
        if not legs:
            continue
        best = max((ev[l] for l in legs if l in ev),
                   key=lambda e: e["qualifying"], default=None)
        if best is None:
            continue
        if p.get("measurement_status") == "measured":
            continue                                  # G1-D/G1-O under DD-036; not re-derived
        if best["qualifying"] > 0:
            p["measurement_status"] = "measured"
            p["measured_by"] = {
                "cycle": CYCLE, "legs": legs, "params_hash": payload["params_hash"],
                "qualifying_findings": best["qualifying"], "counts": best["counts"],
                "definition": ("at least one pass/fail/not_applicable Finding on an admitted, "
                               "observable surface in a cycle with fired controls; `error` "
                               "does not count"),
                "recorded_by": TASK}
            promoted.append(code)
        else:
            # E5's subject is the CYCLE, not a surface, so §0's definition — which requires a
            # Finding "on an admitted, observable surface" — can never be satisfied by it.
            # That is a limitation of the definition, not a gap in the measurement: E5 fired
            # in this cycle and in every cycle, and its Finding is on the log. Recorded as
            # what it is rather than as a missing measurement.
            if "E5" in legs:
                why = ("E5 judges the CYCLE, not a surface, so DD-055's definition of "
                       "`measured` — a Finding on an admitted, observable surface — cannot "
                       "apply to it. Its control Finding fired in this cycle and every "
                       "other; the status is a limitation of the definition, not a gap in "
                       "the measurement.")
            elif best["counts"]["error"]:
                why = ("every Finding was `error` — the collector could not observe any "
                       "admitted surface")
            else:
                why = "no admitted surface produced a Finding for this leg"
            p["not_measured_reason"] = {"cycle": CYCLE, "legs": legs, "reason": why,
                                        "counts": best["counts"], "recorded_by": TASK}
            held.append((code, why))
    # See `scripts/framework_writeback.py`: one definition of every denominator, regenerated
    # on every write-back (`cc_tasks/2026-09-07_scan_hygiene.md` §3). `indicators_measured` is
    # candidate-excluded there for the reason it was here — DD-054.
    fw.apply_counts(g)
    return {"promoted": sorted(promoted), "held": sorted(held),
            "indicators_measured": g["counts"]["indicators_measured"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    out = writeback(g, payload, evidence(payload))
    print(json.dumps(out, indent=1))
    # Through the shared writer, so the write and the `framework_writeback` event that records
    # it cannot come apart.
    ev = fw.save(g, script=SCRIPT, task=TASK, changes=out, dry_run=a.dry_run)
    print(json.dumps({k: v for k, v in ev.items() if k != "counts"}, indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
