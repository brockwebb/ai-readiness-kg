#!/usr/bin/env python3
"""Add A12 as a CANDIDATE indicator: declared vs enforced machine access. **Zero model spend.**

Task `cc_tasks/2026-09-06_scan_targets.md` §4. The indicator:

    *An identified, robots-compliant machine client that robots.txt permits is served — not
    refused by a WAF or bot manager.*

It is a `candidate`, not part of the framework, and the distinction is load-bearing. DD-054
records why; the short version is three things:

1. **It is the public-observable leg of what A11 assumed needed edge logs.** A11 splits
   crawler access into declared / enforced / observed and puts the last two at
   `agency_instrumented`, because you cannot see an agency's WAF from outside. That is true of
   the *general* enforced layer and false of one measurable corner of it: when robots.txt
   permits a path and the host answers 403 to a compliant client asking for that same path,
   the disagreement between the two layers is visible from the public tier, with no logs.

2. **It was found by the harness, not by the literature.** The scaffold's smoke run recorded
   `www.bls.gov` refusing 60 of 60 requests, and this task's pre-flight found the same at
   `www.bts.gov` and `www.ssa.gov` — three of thirteen principal statistical agencies — while
   each host's own robots.txt permits the paths. No source in the corpus proposes this as an
   AI-readiness construct. An indicator that arrives this way has a different evidentiary
   standing from one crosswalked out of a published framework, and hiding that difference
   inside the A table would be the dishonest move.

3. **Promotion is the operator's, because the framework goes out under his name.**

    /opt/anaconda3/bin/python3 scripts/add_candidate_indicator.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
TASK = "cc_tasks/2026-09-06_scan_targets.md"
CODE = "A12"

INDICATOR = {
    "code": CODE,
    "construct": "Access policy coherence",
    "indicator": ("An identified, robots-compliant machine client that robots.txt permits is "
                  "served (not refused by a WAF or bot manager)"),
    "type": "AUTO",
    "tier": "public",
    "tier_raw": "`public`",
    "status": "candidate",
    "measurement_status": "specified",
    "criterion_code": "A",
    "evidence_raw": ("`rfc-9309-robots-exclusion-protocol` (the declared layer's semantics); "
                     "`cloudflare-ai-crawl-control-manage-crawlers` (the enforcing layer this "
                     "indicator detects from outside)"),
    "candidate_rationale": (
        "The public-observable leg of A11's enforced layer. A11 places enforced and observed "
        "access at `agency_instrumented` because a WAF is not visible from outside; that holds "
        "in general and fails for the one case where robots.txt PERMITS a path and the host "
        "REFUSES a compliant client asking for it. The disagreement between the two declared "
        "and enforced layers is then observable at the public tier with no edge logs at all."),
    "candidate_provenance": (
        "Found by the harness, not by the literature: 3 of the 13 principal statistical "
        "agencies (BLS, BTS, ORES/SSA) answered 401/403 to `ai-readiness-kg-scanner/0.1` on "
        "every probe while their own robots.txt permits the paths. No corpus source proposes "
        "this as an AI-readiness construct."),
    "candidate_promotion": (
        "Operator decision. The framework goes out under his name and an indicator the "
        "instrument invented about itself is exactly the kind that needs a human to accept it."),
}

SPEC = {
    "indicator_code": CODE,
    "leg": CODE,
    "mode": "auto",
    "rule_id": "RULE-A12-v0",
    "collector": "http + robots",
    "collector_pin": "httpx>=0.27 + protego (scripts/scan_preflight.py)",
    "signal": ("Per host: GET /robots.txt and parse it; then GET the product path under the "
               "identified UA. Coherent iff robots.txt permits the path for this UA AND the "
               "host serves it. Incoherent iff robots.txt permits and the host answers a "
               "status in `manners.unobservable_statuses` (401/403/407/429). A robots.txt "
               "that DISALLOWS the path is not incoherence — it is A4's measurement, and this "
               "indicator is `not_applicable` there."),
    "evidence_kind": "robots.txt body + per-UA verdict + the response status for the same path",
    "prior_art": ("RFC 9309 (what a declaration means); `cloudflare-ai-crawl-control-manage-"
                  "crawlers` (what an enforcing layer does)"),
}

EVIDENCED_BY = ["rfc-9309-robots-exclusion-protocol",
                "cloudflare-ai-crawl-control-manage-crawlers"]
EVIDENCED_BY_INTERNAL = [
    "cc_tasks/2026-09-06_harness_scaffold_RESULT.md §5",
    "docs/design_decisions.md DD-052 §6a",
    "state/scan_preflight_2026-09.json",
]


def add(g: dict) -> dict:
    codes = {n["properties"].get("code") for n in g["nodes"]}
    if CODE in codes:
        return {"added": False, "reason": f"{CODE} already present"}
    construct_id = f"con:{CODE}-access-policy-coherence"
    g["nodes"].append({"id": construct_id, "labels": ["AssessmentConstruct"],
                       "properties": {"name": INDICATOR["construct"],
                                      "criterion_code": "A", "status": "candidate"}})
    g["nodes"].append({"id": f"ind:{CODE}", "labels": ["AssessmentIndicator"],
                       "properties": {**INDICATOR, "recorded_by": TASK}})
    g["nodes"].append({"id": f"spec:{CODE}", "labels": ["MeasurementSpec"],
                       "properties": {**SPEC, "recorded_by": TASK}})
    g["edges"].append({"from": "crit:A", "to": construct_id, "type": "DECOMPOSES_INTO"})
    g["edges"].append({"from": construct_id, "to": f"ind:{CODE}", "type": "DECOMPOSES_INTO"})
    g["edges"].append({"from": f"ind:{CODE}", "to": f"spec:{CODE}", "type": "MEASURED_BY"})
    for doc in EVIDENCED_BY:
        g["edges"].append({"from": f"ind:{CODE}", "type": "EVIDENCED_BY", "to": f"doc:{doc}",
                           "properties": {"doc_id": doc}})
    for ref in EVIDENCED_BY_INTERNAL:
        g["edges"].append({"from": f"ind:{CODE}", "type": "EVIDENCED_BY_INTERNAL",
                           "to": ref, "properties": {"ref": ref}})
    g["counts"]["candidate_indicators"] = sum(
        1 for n in g["nodes"] if "AssessmentIndicator" in n["labels"]
        and n["properties"].get("status") == "candidate")
    # Derived counters, recomputed rather than incremented: `measurement_specs` said 21 after
    # A12's spec made it 22, which is the same drift `framework_writeback_rules` was written
    # to stop. A count that can disagree with its own data is a number computed in chat.
    g["counts"]["measurement_specs"] = sum(
        1 for n in g["nodes"] if "MeasurementSpec" in n["labels"])
    g["counts"]["indicators"] = sum(
        1 for n in g["nodes"] if "AssessmentIndicator" in n["labels"]
        and n["properties"].get("status") != "candidate")
    g["counts"]["constructs"] = sum(
        1 for n in g["nodes"] if "AssessmentConstruct" in n["labels"]
        and n["properties"].get("status") != "candidate")
    return {"added": True, "code": CODE,
            "candidate_indicators": g["counts"]["candidate_indicators"],
            "evidenced_by": EVIDENCED_BY,
            "evidenced_by_internal": EVIDENCED_BY_INTERNAL}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    out = add(g)
    print(json.dumps(out, indent=1))
    if not a.dry_run and out["added"]:
        FRAMEWORK.write_text(json.dumps(g, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        print(f"-> {FRAMEWORK.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
