#!/usr/bin/env python3
"""Load the framework JSON into Neo4j under the v0.4.0 assessment labels. **Zero spend.**

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §2.3. The assessment layer is a
projection of `framework/ai_readiness_framework.json`, exactly as the KG layer is a projection
of the event log: this script resets its own labels and rebuilds, so the graph holds no
assessment state its source does not.

These labels are not in `kg_labels` and not in the parser's whitelist (DD-051), so the KG
replay cannot delete a framework node and an extraction cannot mint one. What that
independence cost, until `cc_tasks/2026-09-07_framework_projection_repair.md`, was freshness:
this script was a MANUAL step nothing called, so the graph's framework layer was a snapshot of
the JSON as of the last time someone remembered to run it — two write-backs stale on
2026-09-07, while `seldon go` was verifying framework state against it. `build_projection.py`
now calls `load()` as its last step; run this directly only to re-project the framework layer
alone.

**This loader owns the framework labels and nothing else.** It used to reset `Observation` and
`Finding` too, which the framework JSON has never contained: running it after a scan cycle
would have silently deleted every stored Observation and Finding, because a reset that owns a
label it cannot rebuild is a delete with extra steps. Those two labels belong to
`assessment/harness/scan/publish.py`, which projects them from the event log.

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

#: The labels this loader OWNS: it deletes them and rebuilds them from the JSON, so every one
#: of them must be reconstructible from the JSON alone. `AssessmentInternalRef` is here
#: because it is minted from the `EVIDENCED_BY_INTERNAL` edges; `Observation` and `Finding`
#: are NOT, because they come from the event log (see the module docstring).
ASSESSMENT_LABELS = ("AssessmentCriterion", "AssessmentConstruct", "AssessmentIndicator",
                     "MeasurementSpec", "AssessmentInternalRef")
#: Edge types this loader may write. A literal whitelist, never a payload value — invariant 4.
ASSESSMENT_EDGES = ("DECOMPOSES_INTO", "EVIDENCED_BY", "EVIDENCED_BY_INTERNAL", "MEASURED_BY")

#: A property whose value is a MAP is flattened onto named scalars rather than dropped or
#: str()-ed. Neo4j has no map property type, and the write-backs of 2026-09-07 put three maps
#: into the JSON (`measured_by` on 14 indicators, `not_measured_reason` on E5, `decision` on
#: three specs) — enough that the old `SET x += $props` would now raise on its first node.
#: `measured_by` gets named scalars because queries ask "which cycle measured this?"; every
#: map ALSO keeps a canonical-JSON twin, so the projection stays lossless and the round-trip
#: gate can compare cell for cell instead of comparing what survived.
_MEASURED_BY_SCALARS = {"cycle": "measured_cycle", "params_hash": "measured_params_hash",
                        "legs": "measured_legs"}


def flatten(props: dict) -> dict:
    """Node properties as Neo4j can store them. Nulls dropped, maps flattened, lists kept."""
    out = {}
    for k, v in props.items():
        if v is None:
            continue
        if isinstance(v, dict):
            out[f"{k}_json"] = json.dumps(v, sort_keys=True, ensure_ascii=False)
            if k == "measured_by":
                for src, dest in _MEASURED_BY_SCALARS.items():
                    if v.get(src) is not None:
                        out[dest] = v[src]
            continue
        if isinstance(v, list) and any(isinstance(x, (dict, list)) for x in v):
            raise SystemExit(f"FATAL: property {k!r} is a nested list; extend flatten()")
        out[k] = v
    return out


def load(session, g: dict) -> dict:
    counts = {"nodes": 0, "edges": 0, "evidenced_by_resolved": 0,
              "evidenced_by_missing_document": 0}
    pred = " OR ".join(f"n:{l}" for l in ASSESSMENT_LABELS)
    session.run(f"MATCH (n) WHERE {pred} DETACH DELETE n")
    for n in g["nodes"]:
        label = n["labels"][0]
        if label not in ASSESSMENT_LABELS:
            raise SystemExit(f"FATAL: {label!r} is not an assessment-layer label")
        session.run(f"MERGE (x:{label} {{id: $id}}) SET x += $props",
                    id=n["id"], props=flatten(n["properties"]))
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
            # Two writers, two key names: `build_framework_graph.py` writes `artifact_path`,
            # `add_candidate_indicator.py` writes `ref`. Reading only the first left A12's
            # three internal references pointing at nodes with a null path.
            props = e.get("properties") or {}
            session.run("MATCH (i:AssessmentIndicator {id: $f}) "
                        "MERGE (r:AssessmentInternalRef {id: $to}) SET r.artifact_path = $p "
                        "MERGE (i)-[:EVIDENCED_BY_INTERNAL]->(r)",
                        f=e["from"], to=e["to"],
                        p=props.get("artifact_path") or props.get("ref"))
            counts["edges"] += 1
            continue
        session.run(f"MATCH (a {{id: $f}}) MATCH (b {{id: $t}}) MERGE (a)-[:{t}]->(b)",
                    f=e["from"], t=e["to"])
        counts["edges"] += 1
    # The bridge between the two projections, rebuilt by whichever ran last. See its docstring.
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan.publish import link_rules_to_indicators
    counts.update(link_rules_to_indicators(session))
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
            counts["specs_in_graph"] = s.run(
                "MATCH (n:MeasurementSpec) RETURN count(n)").single()[0]
            counts["internal_refs_in_graph"] = s.run(
                "MATCH (n:AssessmentInternalRef) RETURN count(n)").single()[0]
            counts["measurement_status"] = {r["s"]: r["c"] for r in s.run(
                "MATCH (n:AssessmentIndicator) RETURN n.measurement_status AS s, "
                "count(*) AS c ORDER BY s")}
            counts["edges_by_type"] = {r["t"]: r["c"] for r in s.run(
                "MATCH (a)-[x]->(b) WHERE a:AssessmentCriterion OR a:AssessmentConstruct "
                "OR a:AssessmentIndicator OR a:Rule "
                "RETURN type(x) AS t, count(*) AS c ORDER BY t")}
    finally:
        driver.close()
    print(json.dumps(counts, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
