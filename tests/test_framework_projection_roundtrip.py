"""The graph's framework layer IS `framework/ai_readiness_framework.json`, cell for cell.

`cc_tasks/2026-09-07_framework_projection_repair.md` §3. The Desktop protocol says to verify a
handoff's premises against the graph before trusting them. On 2026-09-07 that instruction was
hollow for this layer: two write-backs (the rule review at 02:16Z, the scan-run measurement at
11:03Z) had changed the JSON of record and neither had reached Neo4j, because
`scripts/load_framework_graph.py` was a manual step nothing called. The graph said 48
indicators, 2 measured; the JSON said 49, 16.

This is the gate that makes "verify against the graph" mean something. It is the DD-050
skeleton round-trip discipline applied one layer down: not "the counts look right" but every
property of every node, compared to its source.

Skipped, never failed, when Neo4j is unreachable — a developer without the database gets a
green suite, and the projection claim is simply unverified rather than falsely green.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "framework" / "ai_readiness_framework.json"

#: The distribution the framework of record carries as of the 2026-09-07 scan cycle. Written
#: as a literal because a gate that reads its expectation out of the artifact under test can
#: only ever pass: this one fails if a write-back moves an indicator without a task saying so.
EXPECTED_MEASUREMENT_STATUS = {"measured": 16, "harness_built": 1, "specified": 32}


def _loader():
    """`scripts/load_framework_graph.py` by path — `scripts/` is not a package."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_load_framework_graph", REPO / "scripts" / "load_framework_graph.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def graph():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                    # noqa: BLE001 - see docstring
        pytest.skip(f"Neo4j unreachable, framework projection unverified: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


@pytest.fixture(scope="module")
def doc():
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def test_every_json_node_is_in_the_graph_cell_for_cell(graph, doc):
    """Not counts: values. A stale projection with the right node count is the exact state
    this gate was written to catch."""
    flatten = _loader().flatten
    mismatches = []
    for n in doc["nodes"]:
        label = n["labels"][0]
        rec = graph.run(f"MATCH (x:{label} {{id: $id}}) RETURN properties(x) AS p",
                        id=n["id"]).single()
        if rec is None:
            mismatches.append((n["id"], "MISSING FROM GRAPH", None, None))
            continue
        got = dict(rec["p"])
        got.pop("id", None)
        want = flatten(n["properties"])
        for k in sorted(set(want) | set(got)):
            if want.get(k) != got.get(k):
                mismatches.append((n["id"], k, want.get(k), got.get(k)))
    assert not mismatches, "\n".join(
        f"{i}.{k}: json={w!r} graph={g!r}" for i, k, w, g in mismatches[:25])


def test_node_and_edge_counts_match_the_json_exactly(graph, doc):
    import collections
    want_nodes = collections.Counter(n["labels"][0] for n in doc["nodes"])
    # AssessmentInternalRef is minted from the edges, not listed among the nodes.
    want_nodes["AssessmentInternalRef"] = len(
        {e["to"] for e in doc["edges"] if e["type"] == "EVIDENCED_BY_INTERNAL"})
    got_nodes = {r["l"]: r["c"] for r in graph.run(
        "MATCH (n) WHERE n:AssessmentCriterion OR n:AssessmentConstruct "
        "OR n:AssessmentIndicator OR n:MeasurementSpec OR n:AssessmentInternalRef "
        "RETURN labels(n)[0] AS l, count(*) AS c")}
    assert got_nodes == dict(want_nodes)

    want_edges = collections.Counter(e["type"] for e in doc["edges"])
    got_edges = {r["t"]: r["c"] for r in graph.run(
        "MATCH (a)-[x]->(b) WHERE a:AssessmentCriterion OR a:AssessmentConstruct "
        "OR a:AssessmentIndicator RETURN type(x) AS t, count(*) AS c")}
    assert got_edges == dict(want_edges)


def test_every_rule_measures_exactly_one_indicator(graph):
    """The edge that makes evidence traversable to the framework. Its absence was why the
    operator's standing requirement — progress visible at every level of the framework — could
    not be answered from the graph at all."""
    rules = graph.run("MATCH (r:Rule) RETURN count(r) AS c").single()["c"]
    assert rules, "no Rule nodes: the scan layer is not projected, so this proves nothing"
    edges = graph.run(
        "MATCH (:Rule)-[m:MEASURES]->(:AssessmentIndicator) RETURN count(m) AS c").single()["c"]
    assert edges == rules
    orphans = [r["rid"] for r in graph.run(
        "MATCH (r:Rule) WHERE NOT (r)-[:MEASURES]->(:AssessmentIndicator) "
        "RETURN r.rule_id AS rid")]
    assert not orphans, f"rules with no indicator: {orphans}"
    many = [r["rid"] for r in graph.run(
        "MATCH (r:Rule)-[:MEASURES]->(i:AssessmentIndicator) "
        "WITH r, count(DISTINCT i) AS n WHERE n > 1 RETURN r.rule_id AS rid")]
    assert not many, f"rules measuring more than one indicator: {many}"


def test_rule_version_comes_from_the_rule_id_not_from_the_finding(graph):
    """Every stored Finding carries `rule_version: "v1"` (`rules/_common.py`), and that field
    is an input to the derived `finding_id`, so it cannot be corrected in the events. The
    graph therefore derives the version, and this asserts the derivation actually ran: before
    the repair all 29 Rule nodes read `v1`, including the four `-v3`."""
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan.rules import parse_rule_id
    rows = list(graph.run("MATCH (r:Rule) RETURN r.rule_id AS rid, r.version AS v, "
                          "r.indicator_code AS code, r.current AS cur"))
    assert rows
    for r in rows:
        want = parse_rule_id(r["rid"])
        assert r["v"] == want["version"], r["rid"]
        assert r["code"] == want["indicator_code"], r["rid"]
        assert isinstance(r["cur"], bool), r["rid"]
    assert {r["v"] for r in rows} != {"v1"}, "no rule version above v1 reached the graph"


def test_measurement_status_distribution(graph, doc):
    got = {r["s"]: r["c"] for r in graph.run(
        "MATCH (n:AssessmentIndicator) RETURN n.measurement_status AS s, count(*) AS c")}
    assert got == EXPECTED_MEASUREMENT_STATUS
    import collections
    in_json = collections.Counter(n["properties"].get("measurement_status")
                                 for n in doc["nodes"]
                                 if n["labels"][0] == "AssessmentIndicator")
    assert dict(in_json) == EXPECTED_MEASUREMENT_STATUS, "the JSON of record moved, not the graph"


def test_the_candidate_indicator_is_present_and_marked(graph):
    """A12 is in the graph (it was absent entirely) and carries `status: candidate`, which is
    how every fraction excludes it mechanically rather than by remembering a code (DD-054)."""
    rec = graph.run("MATCH (i:AssessmentIndicator {code: 'A12'}) "
                    "RETURN i.status AS s, i.measurement_status AS ms").single()
    assert rec is not None and rec["s"] == "candidate"
    assert rec["ms"] == "specified"
    n = graph.run("MATCH (i:AssessmentIndicator {status: 'candidate'}) "
                  "RETURN count(i) AS c").single()["c"]
    assert n == 1


def test_the_measured_indicators_carry_their_cycle(graph):
    """`measured_by` is a MAP in the JSON and Neo4j has no map property. Flattening it is only
    correct if a query can still answer "which cycle measured this, under which params" —
    which is the question the second scan cycle will ask of the first."""
    rows = list(graph.run(
        "MATCH (i:AssessmentIndicator) WHERE i.measured_cycle IS NOT NULL "
        "RETURN i.code AS code, i.measured_cycle AS cyc, i.measured_params_hash AS ph, "
        "i.measured_legs AS legs"))
    assert len(rows) == 14, "14 of the 16 measured are from this cycle; G1-D/G1-O predate it"
    for r in rows:
        assert r["cyc"] == "scan_2026-09-07"
        assert isinstance(r["ph"], str) and len(r["ph"]) == 64
        assert r["legs"] and all(isinstance(x, str) for x in r["legs"])
