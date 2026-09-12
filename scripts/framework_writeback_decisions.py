#!/usr/bin/env python3
"""Write the decisions the rules had to make into the specs that did not settle them.

Task `cc_tasks/2026-09-06_scan_targets.md` §2, disposition of `spec_underspecified`:

    *"write the decision the rule made into the `MeasurementSpec` as a `decision` property
    with the rule version that made it, so the spec and the rule agree and the gap is closed
    in the framework of record, not in code."*

Three of the sixteen `v1` rules came back `spec_underspecified` in the 2026-09-06 conformance
review — A4, A5 and A9. In each the rule had to settle something the `signal` does not, and a
different reasonable implementation would return a different verdict on some real surface
while both control fixtures still landed on their stated verdicts. That is the definition of a
gap the controls cannot see, and closing it in code would be closing it in the wrong place:
the framework is the record, and a decision recorded only in a Python module is a decision the
framework does not know it made.

**No rule is edited and no verdict changes.** A `decision` is a statement of what the existing
`v1` rule already does, promoted from implicit to written, so the next reader can disagree with
it on the record rather than discover it by reading the code.

    /opt/anaconda3/bin/python3 scripts/framework_writeback_decisions.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw                                    # noqa: E402

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
TASK = "cc_tasks/2026-09-06_scan_targets.md"
SCRIPT = "scripts/framework_writeback_decisions.py"

DECISIONS = {
    "A4": {
        "decided_by": "RULE-A4-v1",
        "question": ("The signal says to fetch and evaluate robots.txt but does not settle "
                     "the verdict when no robots.txt is served at all."),
        "decision": ("Absence is `fail`. RFC 9309 is clear that absence PERMITS retrieval, so "
                     "a rule reading the crawler's question would return `pass`; A4 does not "
                     "ask what a crawler may do, it asks whether the agency has DECLARED a "
                     "policy, and a host that has declared nothing has not declared "
                     "permission. The reading matters: it flips the verdict on every real "
                     "surface with no robots.txt and no soft-blocks, and both control "
                     "fixtures land on their stated verdicts either way."),
        "alternative": ("Read A4 as a compliance question and absence becomes `pass`. If the "
                        "operator prefers that reading it is a `v2`, not an edit."),
    },
    "A5": {
        "decided_by": "RULE-A5-v1",
        "question": ("The signal says to fetch /llms.txt and /.well-known/ alongside the "
                     "sitemap but states a coverage test only for the sitemap, leaving "
                     "unsettled what a served llms.txt contributes to the verdict."),
        "decision": ("A covering sitemap is the SOLE pass path. A served llms.txt is recorded "
                     "as evidence and cannot satisfy the leg on its own. Rationale: the "
                     "sitemap is the only one of the three with a standardised way to assert "
                     "that a specific URL is covered; llms.txt has no such semantics, and "
                     "accepting its mere presence would score having the file rather than "
                     "being discoverable. Consequence: a site whose llms.txt lists the data "
                     "product but which serves no sitemap gets `fail`, where an implementation "
                     "reading the indicator's 'llms.txt (or equivalent) present' as an "
                     "alternative satisfier would return `pass`."),
        "alternative": ("Treat llms.txt as an alternative satisfier. That is a change to what "
                        "the indicator MEANS, not to how it is measured, and belongs to the "
                        "operator."),
    },
    "A9": {
        "decided_by": "RULE-A9-v1",
        "question": ("The signal names which paths to probe but does not settle what counts "
                     "as a served machine-first entry point."),
        "decision": ("A non-HTML content type on a 2xx response with a non-empty body. The "
                     "descriptor is NOT parsed. Rationale: A9 is FRONTIER (as_of 2026-01) and "
                     "is reported, never scored, so the cheapest test that excludes the "
                     "failure the control fixture caught — a soft-404 HTML shell counted as "
                     "an agent surface — is the right one for now. Consequence: a text/plain "
                     "'Not Found' body, or a JSON error blob, passes; an implementation that "
                     "parsed the descriptor would fail those same real surfaces."),
        "alternative": ("Parse the descriptor (validate as OpenAPI / MCP / llms.txt). Worth "
                        "doing when A9 stops being frontier and enters a score; until then it "
                        "would buy precision nobody is reading."),
    },
}


def writeback(g: dict) -> dict:
    touched = []
    for n in g["nodes"]:
        if "MeasurementSpec" not in n["labels"]:
            continue
        d = DECISIONS.get(n["properties"].get("leg"))
        if not d:
            continue
        payload = {**d, "recorded_by": TASK,
                   "why_here": ("The review returned `spec_underspecified`: a different "
                                "reasonable implementation would return a different verdict "
                                "on some real surface, and neither control fixture can see "
                                "the difference.")}
        if n["properties"].get("decision") != payload:
            n["properties"]["decision"] = payload
            touched.append(n["properties"]["leg"])
    # Counters are regenerated once, by the shared writer, on save
    # (`scripts/framework_writeback.py`, `cc_tasks/2026-09-07_scan_hygiene.md` §3). Four
    # write-backs each recomputing their own handful is how the one nobody recomputed drifted.
    fw.apply_counts(g)
    return {"decisions_written": touched,
            "specs_with_recorded_decision": g["counts"]["specs_with_recorded_decision"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    out = writeback(g)
    print(json.dumps(out, indent=1))
    # Through the shared writer, so the write and the `framework_writeback` event that records
    # it cannot come apart.
    ev = fw.save(g, script=SCRIPT, task=TASK, changes=out, dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({k: v for k, v in ev.items() if k != "counts"}, indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
