#!/usr/bin/env python3
"""Load the framework JSON into Neo4j under the v0.4.0 assessment labels. **Zero spend.**

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §2.3. The assessment layer is a
projection of `framework/ai_readiness_framework.json`, exactly as the KG layer is a projection
of the event log: this script resets its own labels and rebuilds, so the graph holds no
assessment state its source does not.

`build_projection.py` does NOT touch these labels — they are not in `kg_labels` and not in the
parser's whitelist (DD-051) — so the two projections are independent and neither can delete
the other's nodes.

    /opt/anaconda3/bin/python3 scripts/load_framework_graph.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
JSON_PATH = REPO / "framework" / "ai_readiness_framework.json"

ASSESSMENT_LABELS = ("AssessmentCriterion", "AssessmentConstruct", "AssessmentIndicator",
                     "MeasurementSpec", "Observation", "Finding")
#: Edge types this loader may write. A literal whitelist, never a payload value — invariant 4.
ASSESSMENT_EDGES = ("DECOMPOSES_INTO", "EVIDENCED_BY", "EVIDENCED_BY_INTERNAL",
                    "MEASURED_BY", "OBSERVED_ON", "SUPPORTS", "RULED_BY")


def load(session, g: dict) -> dict:
    counts = {"reset": 0, "nodes": 0, "edges": 0, "evidenced_by_resolved": 0,
              "evidenced_by_missing_document": 0}
    pred = " OR ".join(f"n:{l}" for l in ASSESSMENT_LABELS)
    session.run(f"MATCH (n) WHERE {pred} DETACH DELETE n")
    for n in g["nodes"]:
        label = n["labels"][0]
        if label not in ASSESSMENT_LABELS:
            raise SystemExit(f"FATAL: {label!r} is not an assessment-layer label")
        props = {k: v for k, v in n["properties"].items() if v is not None}
        session.run(f"MERGE (x:{label} {{id: $id}}) SET x += $props", id=n["id"], props=props)
        counts["nodes"] += 1
    for e in g["edges"]:
        t = e["type"]
        if t not in ASSESSMENT_EDGES:
            raise SystemExit(f"FATAL: {t!r} is not an assessment-layer edge type")
        if t == "EVIDENCED_BY":
            doc_id = (e.get("properties") or {}).get("doc_id")
            hit = session.run("MATCH (d:Document {doc_id: $d}) RETURN count(d) AS n",
                              d=doc_id).single()["n"]
            if not hit:
                # The manifest holds it (the builder checked) but the GRAPH does not — an
                # admitted document with no Document node. Counted, never silently dropped.
                counts["evidenced_by_missing_document"] += 1
                continue
            session.run(f"MATCH (i:AssessmentIndicator {{id: $f}}) "
                        f"MATCH (d:Document {{doc_id: $d}}) "
                        f"MERGE (i)-[:EVIDENCED_BY]->(d)", f=e["from"], d=doc_id)
            counts["evidenced_by_resolved"] += 1
            counts["edges"] += 1
            continue
        if t == "EVIDENCED_BY_INTERNAL":
            session.run("MATCH (i:AssessmentIndicator {id: $f}) "
                        "MERGE (r:AssessmentInternalRef {id: $to}) SET r.artifact_path = $p "
                        "MERGE (i)-[:EVIDENCED_BY_INTERNAL]->(r)",
                        f=e["from"], to=e["to"], p=(e.get("properties") or {}).get("artifact_path"))
            counts["edges"] += 1
            continue
        session.run(f"MATCH (a {{id: $f}}) MATCH (b {{id: $t}}) MERGE (a)-[:{t}]->(b)",
                    f=e["from"], t=e["to"])
        counts["edges"] += 1
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(JSON_PATH))
    a = ap.parse_args(argv)
    g = json.loads(Path(a.json).read_text(encoding="utf-8"))

    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            counts = load(s, g)
            counts["criteria_in_graph"] = s.run(
                "MATCH (n:AssessmentCriterion) RETURN count(n)").single()[0]
            counts["indicators_in_graph"] = s.run(
                "MATCH (n:AssessmentIndicator) RETURN count(n)").single()[0]
            counts["constructs_in_graph"] = s.run(
                "MATCH (n:AssessmentConstruct) RETURN count(n)").single()[0]
            counts["indicators_reachable_from_a_criterion"] = s.run(
                "MATCH (:AssessmentCriterion)-[:DECOMPOSES_INTO]->(:AssessmentConstruct)"
                "-[:DECOMPOSES_INTO]->(i:AssessmentIndicator) RETURN count(DISTINCT i)").single()[0]
    finally:
        driver.close()
    print(json.dumps(counts, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
