#!/usr/bin/env python3
"""Does the graph link each reported check to a construct, a definition and a primary source?
**Read-only, zero spend, no network beyond Neo4j.**

`cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 5: *measured and reported, not
gated*. For each of the six tier-0 legs and A3, state by Cypher whether the rule's indicator
node reaches a construct, a definition or a source node — the survey item -> construct ->
definition -> primary source crosswalk this repo's CLAUDE.md calls the validity layer. Where the
answer is "no edge", the RESULT says so and the report is not changed for it.

    /opt/anaconda3/bin/python3 scripts/report_traceability.py [--cycle scan_2026-09-10_rj2]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

#: The report's six host-level checks, plus the product check decision 4 writes a paragraph
#: about. The report names these and no others as its own legs.
LEGS = ["A4", "A5", "A10", "A11-declared", "A12", "G1-D", "A3"]

Q = """
MATCH (i:AssessmentIndicator {code: $code})
// The construct DECOMPOSES INTO the indicator, not the other way round: a criterion
// decomposes into constructs and a construct into indicators. Written the wrong way round
// once here, which reported every leg as having no construct.
OPTIONAL MATCH (c:AssessmentConstruct)-[:DECOMPOSES_INTO]->(i)
OPTIONAL MATCH (crit:AssessmentCriterion)-[:DECOMPOSES_INTO]->(c)
OPTIONAL MATCH (i)-[:EVIDENCED_BY]->(d:Document)
OPTIONAL MATCH (i)-[:MEASURED_BY]->(m:MeasurementSpec)
OPTIONAL MATCH (r:Rule)-[:MEASURES]->(i)
// `(Document)-[:DEFINES]->(Definition)`, not the reverse: the document is where the
// definition is stated. Written the other way round once here, which reported every leg as
// reaching no definition when two of them reach hundreds.
OPTIONAL MATCH (i)-[:EVIDENCED_BY]->(:Document)-[:DEFINES]->(def:Definition)
OPTIONAL MATCH (i)-[:EVIDENCED_BY_INTERNAL]->(x:AssessmentInternalRef)
RETURN i.construct AS construct_property,
       count(DISTINCT c) AS constructs,
       count(DISTINCT crit) AS criteria,
       count(DISTINCT def) AS definitions,
       count(DISTINCT d) AS sources,
       count(DISTINCT m) AS specs,
       count(DISTINCT r) AS rules,
       count(DISTINCT x) AS internal_refs,
       collect(DISTINCT coalesce(c.name, c.construct))[..4] AS construct_names,
       collect(DISTINCT d.doc_id)[..4] AS source_ids
"""

#: A leg whose FRAMEWORK code is not its leg code. `A11-declared` is one half of indicator A11 —
#: the report measures the DECLARED layer only — and there is no `A11-declared` indicator node.
#: Declared here rather than discovered by a fuzzy match, so a leg with no indicator at all
#: reports as one instead of being silently paired with a neighbour.
FRAMEWORK_CODE = {"A11-declared": "A11"}


def measure(session) -> dict:
    """`{leg: row}` for every leg the report publishes. **The one measurement, one place.**

    `main` prints it and `tests/test_report_traceability.py` asserts its shape
    (`cc_tasks/2026-09-11_a3_a10_sources.md` decision 5). A test that re-derived the query
    would be checking its own copy of it, and the two Cypher directions this file got wrong on
    the first pass are exactly the kind of thing a second copy preserves.
    """
    out = {}
    for leg in LEGS:
        code = FRAMEWORK_CODE.get(leg, leg)
        rows = list(session.run(Q, code=code))
        row = dict(rows[0]) if rows else {}
        exists = bool(session.run(
            "MATCH (i:AssessmentIndicator {code:$c}) RETURN count(i) AS n",
            c=code).single()["n"])
        out[leg] = {"framework_code": code, "indicator_node": exists, **row}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", default="scan_2026-09-10_rj2")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    drv = get_neo4j_driver(cfg)
    try:
        with drv.session(database=cfg["neo4j"]["database"]) as s:
            out = measure(s)
    finally:
        drv.close()
    if a.json:
        print(json.dumps(out, indent=1))
        return 0
    print(f"{'leg':14s} {'code':6s} {'node':5s} {'constr':>6s} {'defin':>6s} {'source':>6s} "
          f"{'spec':>5s} {'rule':>5s}  construct")
    for leg, r in out.items():
        print(f"{leg:14s} {r['framework_code']:6s} {str(r['indicator_node']):5s} "
              f"{r.get('constructs', 0):6d} {r.get('definitions', 0):6d} "
              f"{r.get('sources', 0):6d} {r.get('specs', 0):5d} {r.get('rules', 0):5d}  "
              f"{(r.get('construct_property') or '-')[:42]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
