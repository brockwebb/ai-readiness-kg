"""`cc_tasks/2026-09-19_resnapshot_rj4.md`: the report moves onto `scan_2026-09-10_rj4`.

Decisions 3 to 6 are what the re-snapshot is checked with, and they are tested here (decision
3, the guard walking the chain, lives beside the guard in `tests/test_snapshot_successor.py`):

* **decision 4** — every view that prints a rank prints beside it the one leg whose reversal
  would move that rank most (`score.concentration`). DRSMSU is first on `scan_2026-09-10_rj4`
  because of a single G4 pass, and a rank that rests on one verdict is the rank a reader
  quotes;
* **decision 5** — the 22 `_rj3` G1-D Findings that DD-066 withdrew from the `home` and Tier C
  surfaces carry a `finding_withdrawn` overlay, so `current` on the graph means "the
  instrument's answer today" and not only "nothing superseded it";
* **decision 6** — `oasdiff-readme` and `wayback-cdx-server-api-readme` have `manifest_add`
  events, so the projection holds their `Document` nodes and a `document` locator to either
  resolves against the graph rather than through the MCP's manifest fallback.

Decisions 1 and 2 are tested by the suites that already guard the published tree
(`tests/test_publication.py`, `tests/test_snapshot_successor.py`, `tests/test_prescriptions.py`)
once `publication.yaml` names the new cycle; the pins that are this task's own are at the end.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "mcp"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

RJ4 = "scan_2026-09-10_rj4"
RJ3 = "scan_2026-09-10_rj3"
TOOL_DOCS = ("oasdiff-readme", "wayback-cdx-server-api-readme")


def _session():
    try:
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        s = driver.session(database=cfg["neo4j"]["database"])
        s.run("RETURN 1").single()
        return driver, s
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")


@pytest.fixture(scope="module")
def graph():
    driver, s = _session()
    yield s
    s.close()
    driver.close()


# ====================================================== decision 4: the concentration sentence

@pytest.fixture(scope="module")
def score():
    import score as S
    return S


@pytest.fixture(scope="module")
def scored(score):
    return score.compute(RJ4)


def _rank_if_reversed(score, r: dict, body: str, leg: str) -> int:
    """Written apart from `score.concentration`: reverse one body's verdicts on one leg, re-score
    that body alone, and rank it against every other body's score as it stands."""
    cells = {k: dict(v) for k, v in r["bodies"][body]["cells"].items()}
    c = cells.get(leg, {})
    c["pass"], c["fail"] = c.get("fail", 0), c.get("pass", 0)
    cells[leg] = c
    new = score.score_body(cells, r["structure"], r["framework"]["criteria"])["score"]
    others = [v["score"] for b, v in r["bodies"].items() if b != body and v["score"] is not None]
    return 1 + sum(1 for w in others if w > new)


def test_drsmsu_is_first_on_g4s_single_pass(scored):
    """The case the decision was written for (`2026-09-18_rejudge_seven_legs_RESULT.md` §4)."""
    v = scored["bodies"]["DRSMSU"]
    assert v["rank"] == 1
    c = v["concentration"]
    assert c["leg"] == "G4"
    assert (c["pass"], c["judged"]) == (1, 1)
    assert c["rank_if_reversed"] > 1
    assert "G4" in c["sentence"] and "one pass" in c["sentence"]


def test_every_ranked_body_has_the_leg_that_moves_its_rank_most(score, scored):
    """The choice re-derived: no other judged leg of the body moves its rank further."""
    ranked = [b for b, v in scored["bodies"].items() if v["rank"] is not None]
    assert len(ranked) == 13
    for b in ranked:
        v = scored["bodies"][b]
        c = v["concentration"]
        judged = [l["leg"] for l in scored["structure"] if l["scored"]
                  and v["legs"][l["leg"]]["judged"]]
        shifts = {l: abs(_rank_if_reversed(score, scored, b, l) - v["rank"]) for l in judged}
        assert c["leg"] in judged, b
        assert c["rank_if_reversed"] == _rank_if_reversed(score, scored, b, c["leg"]), b
        assert abs(c["rank_if_reversed"] - v["rank"]) == max(shifts.values()), (b, shifts)


def test_an_unscored_body_has_no_concentration(scored):
    for b in ("BLS", "BTS", "ORES"):
        assert scored["bodies"][b]["rank"] is None
        assert scored["bodies"][b]["concentration"] is None


def _printed(fn, *a) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*a)
    return buf.getvalue()


def test_every_view_that_prints_a_rank_prints_the_sentence(score, scored):
    """The grid, a body page and the sensitivity table all print a rank; each carries the
    sentence for every body whose rank it prints."""
    grid = _printed(score.print_grid, scored)
    sens = _printed(score.print_sensitivity, scored)
    for b, v in scored["bodies"].items():
        if v["rank"] is None:
            continue
        s = v["concentration"]["sentence"]
        assert s in grid, b
        assert s in sens, b
        assert s in _printed(score.print_body, scored, b), b


def test_the_design_page_says_why_at_step_ten(score):
    page = (REPO / "docs" / "design" / "scoring_model.md").read_text(encoding="utf-8")
    step = page.split("### 10. Visualisation of the results", 1)[1].split("## ", 1)[0]
    assert "concentration" in step and "reversed" in step


def test_get_body_carries_the_same_field(scored):
    import airkg_tools as T
    t = T.Tools(graph=None)
    if t.cycle != RJ4:
        pytest.skip(f"the cycle of record is {t.cycle}; decision 1 has not run")
    out = t.get_body("DRSMSU")
    assert out["score"]["rank"] == scored["bodies"]["DRSMSU"]["rank"]
    assert out["score"]["concentration"] == scored["bodies"]["DRSMSU"]["concentration"]
    assert out["score"]["concentration"]["sentence"] in out["summary"]


# ==================================== decision 5: the 22 `_rj3` G1-D Findings that no rule reaches

def _events(kind: str) -> list:
    from kg import eventlog
    return [e for e in eventlog.replay() if e.get("event_type") == kind]


def test_twenty_two_withdrawal_overlays_on_the_log():
    ws = _events("finding_withdrawn")
    assert len(ws) == 22
    assert {w["cycle"] for w in ws} == {RJ3}
    assert {w["leg"] for w in ws} == {"G1-D"}
    assert all("DD-066" in w["reason"] for w in ws)
    assert all(w["task"] == "cc_tasks/2026-09-19_resnapshot_rj4.md" for w in ws)
    assert len({w["finding_id"] for w in ws}) == 22


def test_each_withdrawn_finding_is_an_rj3_g1d_finding_nothing_supersedes():
    ids = {w["finding_id"] for w in _events("finding_withdrawn")}
    derived = {e["finding_id"]: e for e in _events("finding_derived") if e["finding_id"] in ids}
    assert set(derived) == ids
    assert all(e["cycle"] == RJ3 and e["leg"] == "G1-D" for e in derived.values())
    superseded = {e["supersedes_finding_id"] for e in _events("finding_supersedes")}
    assert not ids & superseded


def test_the_graph_calls_them_withdrawn_and_not_current(graph):
    rows = graph.run("MATCH (f:Finding) WHERE f.withdrawn RETURN f.cycle AS c, "
                     "f.current AS cur, f.withdrawn_reason AS why").data()
    assert len(rows) == 22
    assert all(r["c"] == RJ3 and r["cur"] is False and "DD-066" in r["why"] for r in rows)
    # And nothing else changed its standing: every other Finding with no successor is current.
    n = graph.run("MATCH (f:Finding) WHERE NOT f.withdrawn AND NOT EXISTS { "
                  "MATCH (:Finding)-[:SUPERSEDES]->(f) } AND NOT f.current "
                  "RETURN count(f) AS n").single()["n"]
    assert n == 0


# ======================================== decision 6: the two tool READMEs have Document nodes

def test_both_tool_readmes_have_a_manifest_add_event_matching_the_ledger():
    adds = {e["payload"]["doc_id"]: e["payload"] for e in _events("manifest_add")
            if e["payload"]["doc_id"] in TOOL_DOCS}
    assert set(adds) == set(TOOL_DOCS)
    entries = json.loads((REPO / "corpus" / "manifest.json").read_text("utf-8"))["entries"]
    for d in TOOL_DOCS:
        ident = entries[d]["identity"]
        assert adds[d]["content_hash"] == ident["sha256"]
        assert adds[d]["local_path"] == ident["canonical_path"]
        assert adds[d]["primary_url"] == ident["source_url"]


def test_both_resolve_against_the_graph_without_the_fallback(graph):
    """The MCP's manifest fallback stays as the guard for a future gap; for these two it is no
    longer what answers."""
    import airkg_tools as T
    t = T.Tools(graph=T.Graph())
    for d in TOOL_DOCS:
        n = graph.run("MATCH (d:Document {doc_id: $d}) RETURN count(d) AS n",
                      d=d).single()["n"]
        assert n == 1, d
        got = t.resolve_locator(T.document_loc(d))
        assert got["resolved"] is True, got
        assert got["detail"] == f"Document {d}", got
