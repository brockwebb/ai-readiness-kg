"""`scripts/audit_node_key_fusion.py` (task `cc_tasks/2026-10-04_node_key_fusion_audit.md`).

A fixture shard holding one benign duplicate, one lost span and one collision, each on its own
`<doc>::<id>` key across two chunks, plus one event the projection never writes. Each must be
counted in exactly its class, and `--check` must be byte-for-byte.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import audit_node_key_fusion as A  # noqa: E402
from kg import eventlog  # noqa: E402

DOC = "fx-fusion-doc"


def _node(chunk: str, item_id: str, term: str, span: str, purpose: str = "bulk_v038") -> dict:
    return {"event_type": "node_asserted", "purpose": purpose, "doc_id": DOC,
            "chunk_id": f"{DOC}#{chunk}",
            "provenance": {"model_id": "m", "prompt_version": "p", "source_sha256": "s",
                           "chunk_id": f"{DOC}#{chunk}"},
            "payload": {"id": item_id, "type": "Definition",
                        "item": {"id": item_id, "term": term, "verbatim_text": span,
                                 "grounding_span": span}}}


def _edge(chunk: str, to_id: str) -> dict:
    return {"event_type": "edge_asserted", "purpose": "bulk_v038", "doc_id": DOC,
            "chunk_id": f"{DOC}#{chunk}",
            "provenance": {"model_id": "m", "prompt_version": "p", "source_sha256": "s"},
            "payload": {"type": "defines", "from_id": DOC, "to_id": to_id,
                        "item": {"grounding_span": "x"}}}


FIXTURE = [
    # benign: one item, one sentence, whitespace differs only
    _node("c0001", "d_same", "Open data", "Open data is data that is\nfreely available."),
    _node("c0002", "d_same", "Open data", "Open data is data that is freely   available."),
    # lost span: one term, two different sentences
    _node("c0001", "d_term", "Metadata", "Metadata: data about data."),
    _node("c0003", "d_term", "metadata", "Metadata describes a dataset's structure."),
    # collision: two terms numbered d1 by two chunks
    _node("c0001", "d1", "Data readiness for AI", "Data readiness for AI is the state of data."),
    _node("c0004", "d1", "Data model", "The data model is the schema of the data."),
    # an edge from the chunk whose d1 was overwritten: it now lands on "Data model"
    _edge("c0001", "d1"),
    _edge("c0004", "d1"),
    # never projected (non-graph purpose): must not count as an assertion of d_term
    _node("c0009", "d_term", "Something else", "Unrelated text.", purpose="tevv_retest"),
]


@pytest.fixture
def fused_log(tmp_path, monkeypatch):
    events = tmp_path / "events"
    events.mkdir()
    (events / "batch-001.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in FIXTURE), encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    return events


def _groups(assertions):
    g = defaultdict(list)
    for a in assertions:
        g[(a["label"], a["key"])].append(a)
    return g


def test_each_fixture_key_is_counted_in_exactly_its_class(fused_log):
    assertions, edges, stats = A.projected_assertions()
    assert stats["skipped_non_graph"] == 1          # the tevv_retest event
    rows = A.classify(_groups(assertions), {})
    by_key = {r["key"]: r["class"] for r in rows}
    assert by_key == {f"{DOC}::d_same": "benign_duplicate",
                      f"{DOC}::d_term": "same_term_lost_evidence",
                      f"{DOC}::d1": "collision"}
    assert Counter(r["class"] for r in rows) == Counter(
        {"benign_duplicate": 1, "same_term_lost_evidence": 1, "collision": 1})


def test_survivor_is_the_last_assertion_and_locations_are_shard_lines(fused_log):
    assertions, _edges, _stats = A.projected_assertions()
    row = next(r for r in A.classify(_groups(assertions), {}) if r["class"] == "collision")
    assert row["survivor_identity"] == "Data model"
    assert row["overwritten_identity"] == "Data readiness for AI"
    assert row["survivor_shard_line"] == "batch-001.jsonl:6"
    assert row["overwritten_shard_lines"] == "batch-001.jsonl:5"
    assert row["origin"] == "other_chunk_same_run"
    assert row["positional_id"] == "true"


def test_fix_a_recovers_every_distinct_span_and_fix_b_keeps_the_first(fused_log):
    assertions, _edges, _stats = A.projected_assertions()
    g = _groups(assertions)
    alt = A.alternative_nodes(g[("Definition", f"{DOC}::d1")], "Definition", [])
    assert [p["term"] for p in alt["current"]] == ["Data model"]
    assert sorted(p["term"] for p in alt["chunk"]) == ["Data model", "Data readiness for AI"]
    assert [p["term"] for p in alt["first"]] == ["Data readiness for AI"]
    # identical normalised spans merge back to one node under fix (a)
    same = A.alternative_nodes(g[("Definition", f"{DOC}::d_same")], "Definition", [])
    assert len(same["chunk"]) == 1


def test_check_is_byte_for_byte(fused_log, tmp_path, monkeypatch):
    monkeypatch.setattr(A, "OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(A, "OUT_CSV", tmp_path / "out" / "audit.csv")
    monkeypatch.setattr(A, "OUT_MD", tmp_path / "out" / "audit.md")
    monkeypatch.setattr(A, "REPO", tmp_path)
    assert A.main([]) == 0
    md = A.OUT_MD.read_text(encoding="utf-8")
    assert "edge now attaches to a different item: 1 of 2" in md
    # prose outside the generated block is the author's, and --check leaves it alone
    A.OUT_MD.write_text("intro prose\n" + md + "closing prose\n", encoding="utf-8")
    assert A.main(["--check"]) == 0
    A.OUT_CSV.write_text(A.OUT_CSV.read_text(encoding="utf-8") + "x\n", encoding="utf-8")
    assert A.main(["--check"]) == 1
