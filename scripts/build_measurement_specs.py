#!/usr/bin/env python3
"""MeasurementSpec nodes for the public-tier AUTO indicators. **Zero model spend.**
**No collector is installed or run here** — this is specification only.

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §3. The shape is F-UJI's
(Devaraju & Huber 2021, *Patterns* 2(10)): a metric definition with a signal, the test that
obtains it, and the evidence retained. Where an indicator genuinely overlaps a FAIR metric the
**F-UJI metric id is named rather than reimplemented**; the ids below were read off
f-uji.net's methods page, not recalled.

**`collector: none_known` is a real answer and is used six times.** It is the only thing that
licenses a commercial fallback later, and it is recorded now rather than discovered then.

Rules are NOT written here. Every spec carries a placeholder `rule_id` of the form
`RULE-<code>-v0`; the harness task writes the rules, versioned, so a rule change re-derives
Findings without re-collecting Observations (the Observation/Finding split of §2.1).

    /opt/anaconda3/bin/python3 scripts/build_measurement_specs.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
JSON_PATH = REPO / "framework" / "ai_readiness_framework.json"

#: Collector pins. A collector without a version is a collector that will drift.
PINS = {"httpx": "httpx>=0.27", "protego": "protego>=0.3", "extruct": "extruct>=0.17",
        "ultimate-sitemap-parser": "ultimate-sitemap-parser>=1.0", "scrapy": "scrapy>=2.11",
        "pyshacl": "pyshacl>=0.26", "lighthouse": "lighthouse-cli>=12",
        "project-open-data-validator": "json-schema (Project Open Data v1.1 schema)",
        "g1_declared": "assessment/harness/probes/g1_declared.py (frozen, DD-036)",
        "g1_preservation": "assessment/harness/probes/g1_preservation.py (frozen, DD-036)"}

#: One entry per indicator leg. `signal` states what is OBSERVED, not what is concluded.
SPECS = {
    "A1": dict(signal="HTTP GET the product page; extract every download link; for each, HEAD "
                      "and read Content-Type and file extension. Structured iff any of "
                      "csv/json/parquet/xlsx/xml; PDF-only iff every link is application/pdf.",
               collector="httpx", evidence_kind="response headers + link list + body sha256",
               prior_art="`usafacts-ai-ready-data-guide`"),
    "A2": dict(signal="HTTP GET the documented API base and any OpenAPI/Swagger document; "
                      "record auth scheme, declared rate limits, and whether the description "
                      "is machine-readable.",
               collector="httpx", evidence_kind="OpenAPI document + response headers",
               fuji_metric="FsF-A1-03D", prior_art="`w3c-dwbp-2017`"),
    "A3": dict(signal="Crawl the product page one hop; classify links as bulk (whole-product "
                      "archive or full dataset file) vs filtered query.",
               collector="scrapy", evidence_kind="link graph + Content-Length per candidate",
               prior_art="`w3c-dwbp-2017`"),
    "A4": dict(signal="HTTP GET /robots.txt; parse; evaluate Allow/Disallow for the product "
                      "path per user-agent in the AI-crawler list (GPTBot, ClaudeBot, "
                      "PerplexityBot, Google-Extended, CCBot, Bingbot).",
               collector="protego", evidence_kind="robots.txt body + sha256 + per-UA verdict",
               prior_art="`rfc-9309-robots-exclusion-protocol`; `openai-crawlers-bots`"),
    "A5": dict(signal="HTTP GET /sitemap.xml (and the path robots.txt declares), /llms.txt, "
                      "/.well-known/; parse the sitemap and test whether the product URL is "
                      "covered.",
               collector="ultimate-sitemap-parser",
               evidence_kind="sitemap tree + coverage verdict for the product URL",
               prior_art="`sitemaps-protocol`; `llmstxt-proposal`"),
    "A6": dict(signal="Extract embedded JSON-LD / microdata / RDFa from the product page; "
                      "test for schema.org Dataset or DCAT; validate the DCAT graph against "
                      "DCAT-AP SHACL shapes.",
               collector="extruct + pyshacl", evidence_kind="extracted graph + SHACL report",
               fuji_metric="FsF-F4-01M, FsF-I1-01M",
               prior_art="`schema-org-dataset`; `w3c-dcat-3`; `mlcommons-croissant-spec`"),
    "A8": dict(signal="Read Last-Modified and any dcterms:modified / schema.org dateModified "
                      "in the markup; test whether a latest-vintage pointer resolves.",
               collector="httpx + extruct", evidence_kind="headers + markup date fields",
               prior_art="`w3c-dwbp-2017`"),
    "A9": dict(signal="Probe for a machine-first entry point: OpenAPI at the documented base, "
                      "/.well-known/mcp or an advertised MCP/A2A endpoint, /llms.txt.",
               collector="httpx", evidence_kind="probe matrix + any served descriptor",
               frontier=True, as_of="2026-01",
               prior_art="`wilkinson-2016-fair-guiding-principles`; `fcsm-25-03`"),
    "A10": dict(signal="For an interactive data tool: request a deep link and an invalid "
                       "route; compare status codes and pre-JS HTML; a soft-404 is HTTP 200 "
                       "with an error shell. Render once to compare pre- and post-JS DOM.",
                collector="lighthouse", evidence_kind="status codes + raw HTML + rendered DOM",
                prior_art="internal draft: FSS Machine Diagnostic spec (operator-held)"),
    "A11-declared": dict(signal="The DECLARED layer only: robots.txt and meta-robots "
                                "directives for the product path. The enforced and observed "
                                "layers need edge/WAF logs and are agency_instrumented.",
                         collector="protego",
                         evidence_kind="robots.txt + meta-robots + per-UA declared verdict",
                         prior_art="`rfc-9309-robots-exclusion-protocol`; "
                                   "`cloudflare-ai-crawl-control-manage-crawlers`"),
    "B3": dict(signal="Fetch the methodology document; test whether it is structured text "
                      "(HTML/markdown) or PDF-only, and whether it is retrievable without JS.",
               collector="httpx", evidence_kind="Content-Type + body sha256",
               prior_art="`fcsm-25-03`",
               note="NOT in the task's §3 list; derived from the framework as public-tier and "
                    "AUTO/DOC. Reported as a discrepancy."),
    "C4-auto": dict(signal="Given a generative engine's answer citing the product, resolve the "
                           "cited URL and test whether it is the authoritative agency page or "
                           "an aggregator.",
                    collector="none_known",
                    evidence_kind="cited URL + resolution chain + authority verdict",
                    prior_art="`aggarwal-2024-geo-generative-engine-optimization`",
                    note="The AUTO leg needs a generative engine's citations as input, which "
                         "is the EVAL half of the indicator. No open-source collector "
                         "produces them; this is genuinely blocked on the harness."),
    "D1": dict(signal="Read the licence from schema.org/DCAT markup, an HTTP Link header, and "
                      "the API's terms endpoint; test whether it is a recognised identifier "
                      "(SPDX or a known URL) rather than free text.",
               collector="extruct + httpx", evidence_kind="licence field + resolution verdict",
               fuji_metric="FsF-R1.1-01M", prior_art="`odcs-open-data-contract-standard`"),
    "D4": dict(signal="Fetch /data.json (Project Open Data catalog); validate against the POD "
                      "v1.1 schema; test whether the product appears in it.",
               collector="project-open-data-validator",
               evidence_kind="catalog document + validation report + membership verdict",
               prior_art="`dcat-us-1-1-schema`; "
                         "`m-25-05-phase-2-implementation-of-the-evidence-act-open-gove`"),
    "E5": dict(signal="Seeded known-bad items fired per continuous-eval cycle.",
               collector="none_known",
               evidence_kind="canary definitions + per-cycle fire log",
               prior_art="internal: DD-019 decoy discipline",
               note="A property of the harness's own cycle, not an observation of an external "
                    "surface. There is nothing to collect until the harness runs."),
    "F2": dict(signal="Compare the API/schema description across two releases; detect breaking "
                      "changes and test for a declared deprecation window.",
               collector="none_known",
               evidence_kind="two dated schema documents + diff",
               prior_art="`odcs-open-data-contract-standard`",
               note="Needs a version history; a single-point scan cannot observe stability. "
                    "Becomes collectible once the scan runs twice."),
    "F3": dict(signal="Across a vintage transition, test whether series identifiers, geography "
                      "codes and endpoints survive, or a crosswalk is published.",
               collector="none_known", evidence_kind="two vintages + identifier join",
               prior_art="**gap** — no admitted source",
               note="Same shape as F2: requires two vintages."),
    "F4": dict(signal="Fetch any changelog or release-notes endpoint; test whether it is "
                      "machine-readable and carries a revision class per entry.",
               collector="httpx", evidence_kind="changelog document + parse verdict",
               prior_art="`usafacts-ai-ready-data-guide`"),
    "G1-D": dict(signal="On the captured product surface, test whether error measures (MOE, "
                        "CV, SE, CI, DP noise parameters) are present as STRUCTURED FIELDS "
                        "beside the estimates rather than as footnotes.",
                 collector="g1_declared", evidence_kind="captured surface file + per-cell verdict",
                 prior_art="DD-033; DD-036 (instrument frozen at v2)",
                 note="Already built and run — `measurement_status: measured`."),
    "G3": dict(signal="Test for stable series IDs across vintages and a published crosswalk "
                      "when a classification or geography changes.",
               collector="none_known", evidence_kind="series id sets + crosswalk document",
               prior_art="**gap** — no admitted source"),
}

#: DOC and EVAL indicators get a spec with a mode and a pointer, and no further design (§3).
MODE_ONLY = {"G1-O": ("harness", "assessment/harness/probes/g1_preservation.py "
                                 "(frozen at v2, DD-036)")}


def build(g: dict) -> tuple:
    inds = {n["properties"]["code"]: n["properties"] for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]}
    nodes, edges, rows = [], [], []
    for key, spec in SPECS.items():
        code = key.split("-declared")[0].split("-auto")[0]
        if code not in inds:
            raise SystemExit(f"FATAL: spec for {key!r} names indicator {code!r}, which is not "
                             f"in the framework")
        sid = f"spec:{key}"
        props = {"indicator_code": code, "leg": key, "mode": "auto",
                 "rule_id": f"RULE-{key}-v0",
                 "collector_pin": PINS.get(spec["collector"].split(" + ")[0], "n/a")
                 if spec["collector"] != "none_known" else "n/a", **spec}
        nodes.append({"id": sid, "labels": ["MeasurementSpec"], "properties": props})
        edges.append({"from": f"ind:{code}", "type": "MEASURED_BY", "to": sid})
        rows.append({"leg": key, "collector": spec["collector"],
                     "fuji_metric": spec.get("fuji_metric"), "rule_id": props["rule_id"],
                     "note": spec.get("note")})
    for code, (mode, pointer) in MODE_ONLY.items():
        sid = f"spec:{code}"
        nodes.append({"id": sid, "labels": ["MeasurementSpec"],
                      "properties": {"indicator_code": code, "leg": code, "mode": mode,
                                     "signal": f"see {pointer}", "collector": pointer,
                                     "collector_pin": PINS.get("g1_preservation", "n/a"),
                                     "evidence_kind": "raw consumer exchange, persisted before "
                                                      "scoring",
                                     "rule_id": f"RULE-{code}-v0",
                                     "prior_art": "DD-035; DD-036"}})
        edges.append({"from": f"ind:{code}", "type": "MEASURED_BY", "to": sid})
        rows.append({"leg": code, "collector": pointer, "fuji_metric": None,
                     "rule_id": f"RULE-{code}-v0", "note": f"mode: {mode}"})
    return nodes, edges, rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(JSON_PATH))
    a = ap.parse_args(argv)
    g = json.loads(Path(a.json).read_text(encoding="utf-8"))
    g["nodes"] = [n for n in g["nodes"] if "MeasurementSpec" not in n["labels"]]
    g["edges"] = [e for e in g["edges"] if e["type"] != "MEASURED_BY"]
    nodes, edges, rows = build(g)
    g["nodes"] += nodes
    g["edges"] += edges
    g["counts"]["measurement_specs"] = len(nodes)
    g["counts"]["collectors_none_known"] = sum(1 for r in rows if r["collector"] == "none_known")
    Path(a.json).write_text(json.dumps(g, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{'leg':14s} {'collector':32s} {'F-UJI':22s} rule")
    for r in sorted(rows, key=lambda x: x["leg"]):
        print(f"{r['leg']:14s} {r['collector'][:32]:32s} {str(r['fuji_metric'] or ''):22s} {r['rule_id']}")
    print(f"\n{len(nodes)} MeasurementSpec nodes; "
          f"{g['counts']['collectors_none_known']} collector: none_known")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
