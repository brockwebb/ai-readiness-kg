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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import framework_writeback as fw                                    # noqa: E402

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
TASK = "cc_tasks/2026-09-06_harness_scaffold.md"
SCRIPT = "scripts/framework_writeback_rules.py"

def _fixture_pin() -> str:
    """The fixtures E5 actually judges, read from the fixture table rather than listed.

    It said "(passes_all, fails_all)" from the day it was written and was wrong twice over
    before anyone noticed: harness-v3 added `refuses_identified_client` and
    `resets_connection`, and harness-v4 added `invalid_route_unobserved`. A `collector_pin` in
    the framework of record that names two of five fixtures is a provenance claim that is
    simply false, and it is exactly the kind of hand-kept list DD-040 exists to stop.
    """
    from scan.fixtures.server import MODES
    return f"assessment/harness/scan/fixtures ({', '.join(sorted(MODES))})"


#: E5 is not a surface measurement and never was: it asks whether the cycle's own controls
#: fired. Task `2026-09-06_harness_scaffold.md` §4 makes the control fixtures that collector,
#: so the spec stops saying `none_known`.
E5 = {
    "collector": "control_fixtures",
    "collector_pin": _fixture_pin(),
    "signal": ("Every control fixture is scanned before any real host. A cycle in which any "
               "of them produced an unexpected verdict is INVALID."),
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
        # Written whenever ANY field differs, not only when the collector name does. The
        # narrower test made the write-back non-idempotent in the one direction that matters:
        # `collector_pin` names the fixtures E5 judges, the fixture set grew twice, and a
        # guard keyed on the collector NAME would have left the framework of record naming two
        # of five forever.
        if p.get("leg") == "E5" and any(p.get(k) != v for k, v in E5.items()):
            p.update(E5)
            touched["e5_collector"] += 1
        # An indicator already `measured` (G1-D, G1-O under DD-036) is NOT demoted: a real
        # measurement outranks the fact that a harness now exists for it.
        ind = inds.get(p.get("leg", "").split("-")[0]) or inds.get(p.get("leg"))
        # A CANDIDATE indicator does not move on the strength of a rule existing for it. A12
        # has a rule and is not the framework (DD-054); promoting it to `harness_built` here
        # would adopt it by side effect of registering its rule.
        if ind is not None and ind["properties"].get("status") == "candidate":
            continue
        if ind is not None and ind["properties"].get("measurement_status") == "specified":
            ind["properties"]["measurement_status"] = "harness_built"
            touched["indicators_status"] += 1
    # `rules_built` is a fact about the rules PACKAGE, not about the JSON, so it stays here:
    # five spec `rule_id`s name rules that were never built, and deriving it from the specs
    # would overcount by five. Everything derivable from nodes/edges — `collectors_none_known`
    # among them — is regenerated by the shared writer instead
    # (`scripts/framework_writeback.py`, `cc_tasks/2026-09-07_scan_hygiene.md` §3).
    g["counts"]["rules_built"] = len(by_leg)
    fw.apply_counts(g)
    return touched


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--task", default=TASK,
                    help="the task that ORDERED this run, recorded on the "
                         "`framework_writeback` event. Defaults to the task this script "
                         "implements; a later task that moves a rule id should name itself, "
                         "so the log says who caused the change rather than only what it does.")
    a = ap.parse_args(argv)
    from assessment.harness.scan.rules import BY_LEG
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    before = json.dumps(g["counts"], sort_keys=True)
    touched = writeback(g, BY_LEG)
    out = {"touched": touched, "counts_before": json.loads(before), "counts": g["counts"]}
    print(json.dumps(out, indent=1))
    # Through the shared writer, so the write and the `framework_writeback` event that records
    # it cannot come apart.
    ev = fw.save(g, script=SCRIPT, task=a.task, changes=out["touched"], dry_run=a.dry_run)
    print(json.dumps({k: v for k, v in ev.items() if k != "counts"}, indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
