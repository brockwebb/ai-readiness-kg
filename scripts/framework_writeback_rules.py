#!/usr/bin/env python3
"""Point every `MeasurementSpec` at the rule that implements it, and move the indicators it
covers to `measurement_status: harness_built`. **Zero model spend, idempotent.**

Task `cc_tasks/2026-09-06_harness_scaffold.md` §3, last bullet. The framework JSON is the
framework of record (DD-050), so the fact that a leg now HAS a harness is a fact about the
framework and belongs in that file — but it is *derived* from `assessment/harness/scan/rules`,
not authored, so it gets a script rather than an edit. The first pass of this task did the
write-back from an ad-hoc command and left `counts.collectors_none_known` at 5 after E5 had
stopped being `none_known`; that is exactly the drift DD-040 exists to stop, and re-running
this script is what fixes it.

What it will NOT touch, per the task's "zero edits to" line: indicator content, criteria,
constructs, edges, evidence. Only `rule_id`, `measurement_status`, E5's collector block, and
the two `counts` entries derived from them.

    /opt/anaconda3/bin/python3 scripts/framework_writeback_rules.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
TASK = "cc_tasks/2026-09-06_harness_scaffold.md"

#: E5 is not a surface measurement and never was: it asks whether the cycle's own controls
#: fired. §4 makes the control fixtures that collector, so the spec stops saying `none_known`.
E5 = {
    "collector": "control_fixtures",
    "collector_pin": "assessment/harness/scan/fixtures (passes_all, fails_all)",
    "signal": ("Both control fixtures are scanned before any real host. A cycle in which "
               "either produced an unexpected verdict is INVALID."),
    "evidence_kind": "per-fixture verdict map for every rule in the cycle",
    "note": ("Was `none_known`: a seeded canary is a property of the harness's own cycle, not "
             f"an observation of an external surface. Task §4 makes the fixtures that property."),
}


def writeback(g: dict, by_leg: dict) -> dict:
    specs = [n for n in g["nodes"] if "MeasurementSpec" in n["labels"]]
    inds = {n["properties"].get("code"): n for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]}
    touched = {"specs_rule_id": 0, "indicators_status": 0, "e5_collector": 0}
    for s in specs:
        p = s["properties"]
        rule = by_leg.get(p.get("leg") or p.get("code"))
        if not rule:
            continue
        if p.get("rule_id") != rule:
            p["rule_id"] = rule
            touched["specs_rule_id"] += 1
        if p.get("leg") == "E5" and p.get("collector") != E5["collector"]:
            p.update(E5)
            touched["e5_collector"] += 1
        # An indicator already `measured` (G1-D, G1-O under DD-036) is NOT demoted: a real
        # measurement outranks the fact that a harness now exists for it.
        ind = inds.get(p.get("leg", "").split("-")[0]) or inds.get(p.get("leg"))
        if ind is not None and ind["properties"].get("measurement_status") == "specified":
            ind["properties"]["measurement_status"] = "harness_built"
            touched["indicators_status"] += 1
    g["counts"]["collectors_none_known"] = sum(
        1 for s in specs if s["properties"].get("collector") == "none_known")
    g["counts"]["rules_built"] = len(by_leg)
    return touched


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    from assessment.harness.scan.rules import BY_LEG
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    before = json.dumps(g["counts"], sort_keys=True)
    touched = writeback(g, BY_LEG)
    out = {"touched": touched, "counts_before": json.loads(before), "counts": g["counts"]}
    print(json.dumps(out, indent=1))
    if not a.dry_run:
        FRAMEWORK.write_text(json.dumps(g, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"-> {FRAMEWORK.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
