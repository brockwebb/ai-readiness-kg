"""squiddy SQ-022 (DN-049 R-209, R-210 as amended): the airkg server may read the CORPUS layer from the kit graph's own
database, and only the corpus layer; the assessment layer stays scoped to the project database.

The rails are pure and test offline. The live half (a corpus reader bound to the kit database answers in its own
dialect, and its locators resolve there) needs Neo4j with both databases and skips without it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "mcp"))
sys.path.insert(0, str(REPO / "scripts"))

import airkg_guard as guard  # noqa: E402


def test_the_corpus_database_is_the_kit_graphs_own_and_never_a_project_one():
    db = guard.corpus_database()
    assert db and not db.startswith("seldon-")
    assert db == "ai-readiness"          # graphs/ai-readiness/config.yaml, rendered from its graph.yaml (SQ-022)


def test_the_assessment_layer_refuses_the_kit_database():
    with pytest.raises(SystemExit, match="assessment layer"):
        guard.assert_allowed_db(guard.corpus_database(), "assessment")
    assert guard.assert_allowed_db(guard.project_database(), "assessment") == guard.project_database()


def test_the_corpus_layer_reads_the_kit_database_or_the_old_corpus_labels_and_nothing_else():
    assert guard.assert_allowed_db(guard.corpus_database(), "corpus") == guard.corpus_database()
    assert guard.assert_allowed_db(guard.project_database(), "corpus") == guard.project_database()
    for other in ("arnold", "wintermute-intake", "seldon-squiddy"):
        with pytest.raises(SystemExit, match="refusing"):
            guard.assert_allowed_db(other, "corpus")
    with pytest.raises(SystemExit, match="unknown layer|refusing"):
        guard.assert_allowed_db(guard.project_database(), "framework")


def test_a_kit_config_naming_a_project_database_is_refused(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("engine:\n  projection:\n    backends:\n    - {name: neo4j, enabled: true, "
                   "database: seldon-ai-readiness-kg}\n", encoding="utf-8")
    monkeypatch.setattr(guard, "KIT_GRAPH_CONFIG", cfg)
    with pytest.raises(SystemExit, match="protected database"):
        guard.corpus_database()


def test_the_parity_rewrite_maps_property_and_relationship_names_and_nothing_else():
    import sq022_parity as P
    spec = P.load_spec()
    q = ("MATCH (d:Definition) WHERE NOT ()-[:DEFINES]->(d) OPTIONAL MATCH (i)-[x:USES_MEASURE]->(m) "
         "RETURN d.key AS key, d.grounding_span AS q, d.keyword AS k")
    assert P.rewrite(q, spec) == ("MATCH (d:Definition) WHERE NOT ()-[:Defines]->(d) OPTIONAL MATCH "
                                  "(i)-[x:UsesMeasure]->(m) RETURN d.id AS key, d.grounding_text AS q, "
                                  "d.keyword AS k")


def _live():
    import airkg_tools as T
    try:
        g = T.Graph(guard.corpus_database(), layer="corpus")
        if not g.available():
            pytest.skip(f"Neo4j or the kit database unreachable: {g.error}")
    except SystemExit as exc:
        pytest.skip(f"no Neo4j credentials: {exc}")
    return T, g


def test_a_kit_corpus_reader_answers_in_its_dialect_and_its_locators_resolve():
    T, kit = _live()
    tools = T.Tools(graph=T.Graph(guard.project_database()), corpus=kit)
    assert kit.dialect == T.CORPUS_DIALECTS["kit"]
    out = tools.search_text("machine-readable", limit=50)
    defs = [h for h in out["hits"] if h["kind"] == "definition"]
    assert defs and out["corpus_database"] == guard.corpus_database()
    assert all(h["locator"]["id_property"] == "id" for h in defs)
    assert all(tools.resolve_locator(h["locator"])["resolved"] for h in defs[:5])
    doc = tools.get_document("w3c-dwbp-2017")
    assert doc["corpus_database"] == guard.corpus_database() and doc["doc_id"] == "w3c-dwbp-2017"
    assert tools.run_cypher("MATCH (n:Definition) RETURN count(n) AS n", layer="corpus")["database"] == \
        guard.corpus_database()
    assert tools.run_cypher("MATCH (n) RETURN count(n) AS n", layer="framework")["refused"]
