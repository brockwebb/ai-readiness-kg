"""The five research questions asked of the graph (`docs/evidence/kg_questions.yaml`).

`cc_tasks/2026-10-02_kg_research_questions.md`, gate. Three properties:

1. every row carries the three citation fields (decision 3) and `complete` says whether all three
   are present — a row that lacks one can never sit under an `answered` grade;
2. every grade is in the closed set `answered` / `partial` / `cannot_answer`;
3. the generator's output equals the stored files byte for byte, while the corpus epoch the
   answers were computed over is unchanged.

The third needs Neo4j and is skipped, never failed, when the database is unreachable — the
same rule as `tests/test_framework_projection_roundtrip.py`. It is also skipped when the epoch
moved: the stored file is then the answer of an older corpus, and a re-run is a new task.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
STORED = REPO / "docs" / "evidence" / "kg_questions.yaml"
STORED_MD = REPO / "docs" / "evidence" / "kg_questions.md"


def _gen():
    spec = importlib.util.spec_from_file_location(
        "_run_kg_questions", REPO / "scripts" / "run_kg_questions.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def doc():
    return yaml.safe_load(STORED.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gen():
    return _gen()


def test_five_questions_in_order(doc):
    assert [q["id"] for q in doc["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"]


def test_every_grade_is_in_the_closed_set(doc, gen):
    for q in doc["questions"]:
        assert q["grade"] in gen.GRADES, (q["id"], q["grade"])
        assert q["reason"], q["id"]
        assert q["route"], q["id"]
        if q["grade"] != "answered":
            assert q["to_close"], f"{q['id']} is {q['grade']} and names nothing that closes it"


def test_every_row_has_the_three_citation_fields(doc, gen):
    for q in doc["questions"]:
        assert q["rows"], q["id"]
        for r in q["rows"]:
            missing = [f for f in gen.CITATION_FIELDS if f not in r]
            assert not missing, (q["id"], r, missing)
            values = [r[f] for f in gen.CITATION_FIELDS]
            flat = [x for v in values for x in (v if isinstance(v, list) else [v])]
            assert r["complete"] == (all(v for v in values) and all(flat)), (q["id"], r)


def test_an_incomplete_row_is_never_under_an_answered_grade(doc):
    for q in doc["questions"]:
        if any(not r["complete"] for r in q["rows"]):
            assert q["grade"] != "answered", q["id"]


def test_quotes_stay_under_fifteen_words(doc, gen):
    for q in doc["questions"]:
        for r in q["rows"]:
            if r.get("quote"):
                words = r["quote"].removesuffix(" …").split()
                assert len(words) <= gen.QUOTE_MAX_WORDS < 15, (q["id"], r["quote"])


def test_q1_positive_control_finds_a_known_definition(doc):
    """NOAA NAO 216-128 §3.01 entered the graph on batch-043 as a curated definition of
    AI-Ready Data. A selection rule that misses it is broken, whatever else it returns."""
    q1 = doc["questions"][0]
    keys = {r["node_key"] for r in q1["rows"]}
    assert "nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data" in keys


def test_terminology_note_is_carried(doc):
    assert "DN-009 decision 4" in doc["terminology"]


@pytest.fixture(scope="module")
def graph(gen):
    sys.path.insert(0, str(REPO / "mcp"))
    try:
        import airkg_tools as T
        g = T.Graph()
        ok = g.available()
    except Exception as exc:                                    # noqa: BLE001 - see docstring
        pytest.skip(f"Neo4j unreachable, kg_questions regeneration unverified: {exc}")
    if not ok:
        pytest.skip(f"Neo4j unreachable, kg_questions regeneration unverified: {g.error}")
    return g


def test_generator_output_equals_the_stored_files(gen, graph, doc):
    text, md = gen.render(graph)
    fresh = yaml.safe_load(text)
    if fresh["epoch"] != doc["epoch"]:
        pytest.skip(f"corpus epoch moved under the stored answers: stored {doc['epoch']}, "
                    f"now {fresh['epoch']}")
    assert text == STORED.read_text(encoding="utf-8")
    assert md == STORED_MD.read_text(encoding="utf-8")
