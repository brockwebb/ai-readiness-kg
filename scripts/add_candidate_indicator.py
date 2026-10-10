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

**Generalised for a second candidate** (`cc_tasks/2026-10-07_seed_known_locations_and_split_
discoverability.md` decision 3): `--code A13` adds the DISCOVERABILITY candidate, DN-013-R1's
other half of what the harness used to measure as one thing. Each candidate is one entry in
`CANDIDATES` (indicator, spec, construct, evidence), written by the same `add`, so a third
candidate is a table entry rather than a third copy of the writer. `--code` defaults to A12,
so the invocation above is unchanged and remains a no-op on a record that holds A12.

    /opt/anaconda3/bin/python3 scripts/add_candidate_indicator.py --code A13 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw                                    # noqa: E402

FRAMEWORK = fw.FRAMEWORK
TASK = "cc_tasks/2026-09-06_scan_targets.md"
SCRIPT = "scripts/add_candidate_indicator.py"
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


# ------------------------------------------------------------------ A13, discoverability
A13_TASK = "cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md"

A13_INDICATOR = {
    "code": "A13",
    "construct": "Discoverability from the product page",
    "indicator": ("A machine client starting from the product page reaches the body's API, its "
                  "terms, its changelog and its inventory without being told where they are"),
    "type": "AUTO",
    "tier": "public",
    "tier_raw": "`public`",
    "status": "candidate",
    "measurement_status": "specified",
    "criterion_code": "A",
    "evidence_raw": (
        "`w3c-dwbp-2017` (Abstract: \"Data should be discoverable and understandable by humans "
        "and machines.\"); `dcat-us-1-1-schema` (Introduction: the Project Open Data metadata "
        "\"to list agency datasets and application programming interfaces (APIs) as hosted at "
        "agency.gov/data\", the inventory's convention location); "
        "`m-25-05-phase-2-implementation-of-the-evidence-act-open-gove` (section 4a iii: \"host "
        "it publicly on the agency's website at the address: www.agency.gov/data.json\"); "
        "`llmstxt-proposal` (Proposal: discovery links \"can be provided as HTML `<link>` "
        "elements, or as an HTTP `Link:` response header\"); "
        "`wilkinson-2016-fair-guiding-principles` (FAIR F4, metadata registered or indexed in a "
        "searchable resource). RFC 9727 (the well-known api-catalog URI, June 2025) is the API's "
        "convention location and is named, not admitted: this task fetched nothing"),
    "candidate_rationale": (
        "DN-013-R1: existence is not discoverability. The harness tested whether a stranger "
        "could find an agency's API, inventory, terms or changelog from the product page and "
        "reported the failure of that search as the absence of the thing, while "
        "api.census.gov, api.bls.gov, api.eia.gov and the BEA API are public knowledge. The "
        "existence legs (A2, D1, F4, D4 and D4's consumers) now read recorded and seeded "
        "locations only; what the link probe and the guessed paths measured is this indicator: "
        "a machine that knows only the product page, and the conventions, gets there or it "
        "does not."),
    "candidate_provenance": (
        "Found by the harness, from the operator's objection of 2026-10-06 (DN-013 §1), not "
        "crosswalked from a published framework. The literature asks for data to be "
        "discoverable by machines (W3C DWBP; FAIR F4) and names the convention locations "
        "(OMB M-13-13's /data.json, RFC 9727's api-catalog); none states this test of a "
        "product page as an AI-readiness indicator."),
    "candidate_promotion": (
        "Operator decision (DD-054). The framework goes out under his name, and an indicator "
        "the instrument derived from its own defect is the kind that needs a human to accept "
        "it."),
}

A13_SPEC = {
    "indicator_code": "A13",
    "leg": "A13",
    "mode": "auto",
    "rule_id": "RULE-A13-v1",
    "collector": "none of its own (`params.link_probe.legs_served`)",
    "collector_pin": ("the shared link probe's product-page Observation and the A2, D1, F4 and "
                      "D4 Observations (`RULE-A13-v1.CONSUMES`)"),
    "signal": (
        "Per surface, per object (the API, its terms, its changelog, the inventory): pass when "
        "an object that exists (an Observation at a recorded location served it, or the record "
        "says verified) has a recorded URL among the product page's links, on-host or "
        "off-host and past the link probe's cap, or sits at a convention location "
        "(the well-known api-catalog URI served as a Linkset, or a `Link: rel=\"api-catalog\"` "
        "header, RFC 9727; the data.json inventory at the host root, OMB M-13-13); fail when it "
        "exists, "
        "the page was read whole and neither holds; error when existence is not settled, the "
        "page was not read, or the API's convention location was not fetched; not_applicable "
        "when no object is shown to exist. The surface's verdict is the first of fail, error, "
        "pass, not_applicable that any object returns."),
    "evidence_kind": "the product page's link set and response headers, plus the recorded "
                     "locations and the fetches of them",
    "prior_art": ("W3C DWBP 2017 (data discoverable by machines); OMB M-13-13 and DCAT-US 1.1 "
                  "(the data.json inventory at the host root); RFC 9727 (api-catalog); RFC 8288 "
                  "(Link header)"),
}

#: code -> what `add` writes for it. A12 is the first candidate and is kept exactly as it was
#: written; A13 is the second.
CANDIDATES = {
    "A12": {"indicator": INDICATOR, "spec": SPEC, "task": TASK,
            "construct_id": "con:A12-access-policy-coherence",
            "evidenced_by": EVIDENCED_BY, "evidenced_by_internal": EVIDENCED_BY_INTERNAL},
    "A13": {"indicator": A13_INDICATOR, "spec": A13_SPEC, "task": A13_TASK,
            "construct_id": "con:A13-discoverability-from-the-product-page",
            "evidenced_by": ["w3c-dwbp-2017", "dcat-us-1-1-schema",
                             "m-25-05-phase-2-implementation-of-the-evidence-act-open-gove",
                             "llmstxt-proposal", "wilkinson-2016-fair-guiding-principles"],
            "evidenced_by_internal": [
                "docs/design/2026-10-06_DN-013_parallelism_known_endpoints_and_prose.md §1",
                "docs/design/2026-10-07_DN-013_ADDENDUM_01_split_r1_and_r3_premise.md A1",
                "cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md §1"]},
}


def add(g: dict, code: str = CODE) -> dict:
    cand = CANDIDATES[code]
    INDICATOR_, SPEC_, TASK_ = cand["indicator"], cand["spec"], cand["task"]
    codes = {n["properties"].get("code") for n in g["nodes"]}
    if code in codes:
        return {"added": False, "reason": f"{code} already present"}
    CODE_ = code
    construct_id = cand["construct_id"]
    g["nodes"].append({"id": construct_id, "labels": ["AssessmentConstruct"],
                       "properties": {"name": INDICATOR_["construct"],
                                      "criterion_code": "A", "status": "candidate"}})
    g["nodes"].append({"id": f"ind:{CODE_}", "labels": ["AssessmentIndicator"],
                       "properties": {**INDICATOR_, "recorded_by": TASK_}})
    g["nodes"].append({"id": f"spec:{CODE_}", "labels": ["MeasurementSpec"],
                       "properties": {**SPEC_, "recorded_by": TASK_}})
    g["edges"].append({"from": "crit:A", "to": construct_id, "type": "DECOMPOSES_INTO"})
    g["edges"].append({"from": construct_id, "to": f"ind:{CODE_}", "type": "DECOMPOSES_INTO"})
    g["edges"].append({"from": f"ind:{CODE_}", "to": f"spec:{CODE_}", "type": "MEASURED_BY"})
    for doc in cand["evidenced_by"]:
        g["edges"].append({"from": f"ind:{CODE_}", "type": "EVIDENCED_BY", "to": f"doc:{doc}",
                           "properties": {"doc_id": doc}})
    for ref in cand["evidenced_by_internal"]:
        # `artifact_path` under an `internal:`-prefixed node id — the shape
        # `build_framework_graph.py` mints and the other seventeen edges already use. This
        # script wrote `{to: <ref>, properties: {ref: <ref>}}` instead, and
        # `load_framework_graph.py` grew a two-key read to tolerate it (`:111`); the record was
        # normalised by `scripts/framework_writeback_normalize.py`
        # (`cc_tasks/2026-09-07_scan_hygiene.md` §3) and the writer fixed here, so the next
        # candidate does not need a third repair. The prefix is not decoration: `to` is the
        # node id the loader MERGEs on, and without it an internal reference could collide with
        # a corpus `doc:` reference on a bare path.
        g["edges"].append({"from": f"ind:{CODE_}", "type": "EVIDENCED_BY_INTERNAL",
                           "to": f"internal:{ref}", "properties": {"artifact_path": ref}})
    # Every derived counter, recomputed rather than incremented, and recomputed in ONE place:
    # `measurement_specs` said 21 after A12's spec made it 22, and the four write-backs each
    # recomputing the handful they touched is how the one nobody recomputed drifted. The
    # denominators — which keys exclude candidates under DD-054 and which do not — are stated
    # once in `scripts/framework_writeback.py` (`cc_tasks/2026-09-07_scan_hygiene.md` §3).
    fw.apply_counts(g)
    return {"added": True, "code": CODE_,
            "candidate_indicators": g["counts"]["candidate_indicators"],
            "evidenced_by": cand["evidenced_by"],
            "evidenced_by_internal": cand["evidenced_by_internal"]}


def refresh(g: dict, code: str) -> dict:
    """Rewrite the indicator and spec properties this script owns for an existing candidate, from
    `CANDIDATES`, and nothing else: the fields a later write-back adds (rule id, tiers, status)
    are left as they are. The same writer, so the change is on a `framework_writeback` event."""
    cand = CANDIDATES[code]
    moved = []
    for nid, props in ((f"ind:{code}", cand["indicator"]), (f"spec:{code}", cand["spec"])):
        node = next((n for n in g["nodes"] if n["id"] == nid), None)
        if node is None:
            raise SystemExit(f"REFUSING: {nid} is not in the record; add it first")
        for k, v in props.items():
            if k in ("rule_id", "measurement_status"):
                continue
            if node["properties"].get(k) != v:
                node["properties"][k] = v
                moved.append(f"{nid}.{k}")
    return {"refreshed": code, "properties_moved": moved}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--code", default=CODE, choices=sorted(CANDIDATES),
                    help="which candidate to add (default A12, the first)")
    ap.add_argument("--refresh", action="store_true",
                    help="rewrite an existing candidate's owned properties from CANDIDATES")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    if a.refresh:
        out = refresh(g, a.code)
        print(json.dumps(out, indent=1))
        if out["properties_moved"]:
            ev = fw.save(g, script=SCRIPT, task=CANDIDATES[a.code]["task"], changes=out,
                         dry_run=a.dry_run, **fw.force_kwargs(a))
            print(json.dumps({k: v for k, v in ev.items() if k != "counts"}, indent=1),
                  file=sys.stderr)
        return 0
    out = add(g, a.code)
    print(json.dumps(out, indent=1))
    if out["added"]:
        # Through the shared writer, so the write and the `framework_writeback` event that
        # records it cannot come apart.
        ev = fw.save(g, script=SCRIPT, task=CANDIDATES[a.code]["task"], changes=out,
                     dry_run=a.dry_run, **fw.force_kwargs(a))
        print(json.dumps({k: v for k, v in ev.items() if k != "counts"}, indent=1),
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
