"""No check the report publishes rests on an uncited indicator.

`cc_tasks/2026-09-11_a3_a10_sources.md` decision 5. `scripts/report_traceability.py` was written
as a one-off measurement for the cycle-4 revision; its finding was that two of the report's seven
checks — A10 and A3, the second being the only product check with a pass rate worth reading —
reached no source document at all. This is that measurement with an expected shape, so the next
uncited indicator fails here instead of being found by whoever reads the published PDF.

**The arrow directions are the other half of this file.** Both were written backwards on the
first pass and both produced a clean, plausible, entirely false table of zeros:

* `DECOMPOSES_INTO` runs criterion → construct → indicator, not indicator → construct;
* `DEFINES` runs document → definition, not definition → document.

"No edge" is exactly what a reversed arrow reports, so a test that only counted edges would have
passed against the reversed query and called the graph empty. Each direction is asserted here
BOTH ways: the true one connects, and the reverse connects nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import report_traceability as RT                                    # noqa: E402

#: Sources a leg must reach. Two for the pair this task cited, because a single source for a
#: check the report leans on is one retraction away from none; one for the rest, which is the
#: invariant — every published check is citable by a stranger.
MIN_SOURCES = {"A3": 2, "A10": 2}
DEFAULT_MIN_SOURCES = 1


@pytest.fixture(scope="module")
def table():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        drv = get_neo4j_driver(cfg)
        with drv.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable, traceability unverified: {exc}")
    try:
        with drv.session(database=cfg["neo4j"]["database"]) as s:
            # The SCRIPT's measurement, not a copy of it. Decision 5 turns the instrument into
            # the test; re-deriving the query here would leave the test checking its own copy.
            return RT.measure(s)
    finally:
        drv.close()


@pytest.fixture(scope="module")
def session():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        drv = get_neo4j_driver(cfg)
        with drv.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with drv.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    drv.close()


def test_the_report_measures_exactly_these_legs():
    """The six tier-0 checks the report's matrix has a column for, plus the product check its
    movement section devotes a paragraph to. A leg added to the report and not here would be
    published uncited and this file would not notice."""
    assert RT.LEGS == ["A4", "A5", "A10", "A11-declared", "A12", "G1-D", "A3"]


@pytest.mark.parametrize("leg", RT.LEGS)
def test_every_published_check_has_an_indicator_node(table, leg):
    assert table[leg]["indicator_node"] is True, (
        f"{leg} has no AssessmentIndicator node under code "
        f"{table[leg]['framework_code']!r}; `report_traceability.FRAMEWORK_CODE` is where a "
        f"leg whose framework code differs from its leg code is declared")


@pytest.mark.parametrize("leg", RT.LEGS)
def test_every_published_check_reaches_a_construct_a_spec_and_a_rule(table, leg):
    r = table[leg]
    assert r["constructs"] >= 1, f"{leg} decomposes from no construct"
    assert r["specs"] >= 1, f"{leg} has no MeasurementSpec"
    assert r["rules"] >= 1, f"{leg} is judged by no Rule"


@pytest.mark.parametrize("leg", RT.LEGS)
def test_every_published_check_reaches_a_primary_source(table, leg):
    """The repo's stated invariant, applied to the instrument rather than to the corpus: every
    assertion is citable by a stranger."""
    want = MIN_SOURCES.get(leg, DEFAULT_MIN_SOURCES)
    assert table[leg]["sources"] >= want, (
        f"{leg} reaches {table[leg]['sources']} source document(s), wanted {want}. A check the "
        f"report publishes with no cited source is the defect "
        f"`cc_tasks/2026-09-11_a3_a10_sources.md` closed for A3 and A10.")


@pytest.mark.parametrize("leg", ("A3", "A10"))
def test_the_two_cited_here_reach_the_definitions_in_their_sources(table, leg):
    """Not a count to hit — the point is that the chain CONTINUES past the document. Both were
    at zero before this task and both are in the hundreds of the corpus's extracted definitions
    now; the assertion is that the last hop resolves at all."""
    assert table[leg]["definitions"] >= 1, (
        f"{leg} reaches a source document but no definition inside one; either the document "
        f"carries no extracted Definition or the DEFINES direction is reversed again")


def test_decomposes_into_runs_criterion_to_construct_to_indicator(session):
    """Reversed on the first writing, which reported every leg as having no construct."""
    fwd = session.run(
        "MATCH (:AssessmentConstruct)-[:DECOMPOSES_INTO]->(:AssessmentIndicator) "
        "RETURN count(*) AS n").single()["n"]
    rev = session.run(
        "MATCH (:AssessmentIndicator)-[:DECOMPOSES_INTO]->(:AssessmentConstruct) "
        "RETURN count(*) AS n").single()["n"]
    assert fwd > 0 and rev == 0, f"construct→indicator {fwd}, indicator→construct {rev}"


def test_defines_runs_document_to_definition(session):
    """Reversed on the first writing, which reported every leg as reaching no definition when
    two of them reach hundreds."""
    fwd = session.run("MATCH (:Document)-[:DEFINES]->(:Definition) RETURN count(*) AS n"
                      ).single()["n"]
    rev = session.run("MATCH (:Definition)-[:DEFINES]->(:Document) RETURN count(*) AS n"
                      ).single()["n"]
    assert fwd > 0 and rev == 0, f"document→definition {fwd}, definition→document {rev}"


def test_evidenced_by_runs_indicator_to_document(session):
    fwd = session.run(
        "MATCH (:AssessmentIndicator)-[:EVIDENCED_BY]->(:Document) RETURN count(*) AS n"
    ).single()["n"]
    rev = session.run(
        "MATCH (:Document)-[:EVIDENCED_BY]->(:AssessmentIndicator) RETURN count(*) AS n"
    ).single()["n"]
    assert fwd > 0 and rev == 0, f"indicator→document {fwd}, document→indicator {rev}"


def test_every_evidenced_by_edge_points_at_an_admitted_document(session):
    """An `EVIDENCED_BY` edge to a document the corpus never admitted is a citation a stranger
    cannot follow. `scripts/load_framework_graph.py` counts those as
    `evidenced_by_missing_document` and drops them; this asserts the count stays at zero from
    the other side, in the graph."""
    import json
    manifest = set(json.loads(
        (REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"])
    rows = session.run(
        "MATCH (:AssessmentIndicator)-[:EVIDENCED_BY]->(d:Document) "
        "RETURN DISTINCT d.doc_id AS d")
    missing = sorted(r["d"] for r in rows if r["d"] not in manifest)
    assert not missing, f"cited but not in corpus/manifest.json: {missing}"
