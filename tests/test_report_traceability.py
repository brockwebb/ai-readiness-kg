"""No check the report publishes rests on an uncited indicator.

`cc_tasks/2026-09-11_a3_a10_sources.md` decision 5. `scripts/report_traceability.py` was written
as a one-off measurement for the cycle-4 revision; its finding was that two of the report's seven
checks — A10 and A3, the second being the only product check with a pass rate worth reading —
reached no source document at all. This is that measurement with an expected shape, so the next
uncited indicator fails here instead of being found by whoever reads the published PDF.

**The list of checks is now twelve and is READ, not typed** (`cc_tasks/2026-09-12_a1_a8_b3_d4_
sources.md` decision 2, under DN-001). The seven-leg version of this file passed while four
product checks the report quotes a rate for in words — A1, A8, B3, D4 — reached no source at
all, because they were not in the list. A list somebody has to remember to extend is not a pin;
`RT.LEGS` is what `appendix_legs()` reads off the section prose, and this file asserts what that
read produces.

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

#: Sources a leg must reach. Two for the pair `2026-09-11_a3_a10_sources` cited and the four
#: `2026-09-12_a1_a8_b3_d4_sources` cited, because a single source for a check the report leans
#: on is one retraction away from none; one for the rest, which is the invariant — every
#: published check is citable by a stranger.
MIN_SOURCES = {"A3": 2, "A10": 2, "A1": 2, "A8": 2, "B3": 2, "D4": 2}
DEFAULT_MIN_SOURCES = 1

#: **Legs allowed to reach zero sources, each with the reason named here.** DN-001 decision 3:
#: a check printed as uncited is a true statement and is publishable, so an uncited leg is not
#: a blocker — but it is not silent either. It is EMPTY, and that is the state of play, not an
#: oversight: `2026-09-12_a1_a8_b3_d4_sources` cited all four legs it set out to cite, including
#: B3, whose script-execution half the task expected to find no standards-grade source for.
#: Adding a leg here means writing down why the corpus cannot cite it; an empty dict means the
#: floor of one applies to every check the report publishes.
ALLOW_ZERO_SOURCES: dict = {}


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
    """The six tier-0 checks the report's matrix has a column for, the product check its
    movement section devotes a paragraph to, and the five product legs whose pass rate the prose
    quotes in words.

    **Twelve, not seven.** The seven-leg pin was what let A1, A8, B3 and D4 be published with a
    quoted rate and no cited source: they were outside the list while the prose made a claim
    about each (`cc_tasks/2026-09-11_report_sources_appendix_RESULT.md` §5). So `RT.LEGS` is no
    longer typed — `appendix_legs()` reads the product half off the section files — and this
    asserts what that read PRODUCES. A leg added to the prose with a
    `{{result:scan_l0_product_<leg>_...}}` tag lands here on the next run and fails this
    assertion until somebody looks at it, which is the alarm the seven-leg list did not have.
    """
    assert RT.LEGS == ["A4", "A5", "A10", "A11-declared", "A12", "G1-D", "A3",
                       "A1", "A6", "A8", "B3", "D4"]
    assert RT.LEGS == RT.appendix_legs(), (
        "the measured legs and the appendix's legs have come apart; the appendix would then "
        "print a row for a check no test pins")


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
    if leg in ALLOW_ZERO_SOURCES:
        pytest.skip(f"{leg} is allowed zero sources: {ALLOW_ZERO_SOURCES[leg]}")
    want = MIN_SOURCES.get(leg, DEFAULT_MIN_SOURCES)
    assert table[leg]["sources"] >= want, (
        f"{leg} reaches {table[leg]['sources']} source document(s), wanted {want}. A check the "
        f"report publishes with no cited source is the defect "
        f"`cc_tasks/2026-09-11_a3_a10_sources.md` closed for A3 and A10 and "
        f"`cc_tasks/2026-09-12_a1_a8_b3_d4_sources.md` closed for A1, A8, B3 and D4. If the "
        f"corpus genuinely cannot cite this check, name it in ALLOW_ZERO_SOURCES with the "
        f"reason rather than lowering the floor.")


@pytest.mark.parametrize("leg", ("A3", "A10", "A1", "A8", "B3", "D4"))
def test_the_cited_legs_reach_the_definitions_in_their_sources(table, leg):
    """Not a count to hit — the point is that the chain CONTINUES past the document. All six
    were at zero before the task that cited them and all six are in the tens or hundreds of the
    corpus's extracted definitions now; the assertion is that the last hop resolves at all."""
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
