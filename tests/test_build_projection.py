"""The three controls for qualified endpoint keys in `scripts/build_projection.py`
(task `cc_tasks/2026-10-04_definition_pairs_completion.md` decision 2).

`resolve_endpoint` scopes an unqualified endpoint id to the asserting document; it honours a
fully qualified `<doc_id>::<local id>` on `from_key` / `to_key` only when the prefix is a
manifested doc_id, and refuses any other qualified key with a logged reason and no node.
Each control is one fixture that exercises exactly one of those three cases, so a regression
in one case fails one control. No test here needs Neo4j: a fake session stands in and holds
the nodes that exist.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_projection as bp  # noqa: E402

DOCS = {"doc-a", "doc-b"}
LABELS = ["Document", "Definition", "Claim"]
WHITELIST = {"conflicts_with", "cites"}


class _Session:
    """A neo4j session over a set of existing (label, key) nodes. A MERGE on bare `{key}`
    creates a label-less node, as Neo4j does; a label-exact MATCH binds only what exists."""

    def __init__(self, nodes):
        self.nodes = set(nodes)
        self.edges = []
        self.queries = []

    def run(self, query, **params):
        self.queries.append(query)
        if query.startswith("MERGE (a {key: $from_id})"):
            for k in (params["from_id"], params["to_id"]):
                if not any(key == k for _, key in self.nodes):
                    self.nodes.add((None, k))
            self.edges.append((params["from_id"], params["to_id"], {}))
            return _Result(None)
        if query.startswith("MATCH (a:"):
            ft = query.split("MATCH (a:", 1)[1].split(" ", 1)[0]
            tt = query.split("MATCH (b:", 1)[1].split(" ", 1)[0]
            ok = ((ft, params["from_id"]) in self.nodes and (tt, params["to_id"]) in self.nodes)
            if ok:
                props = {"grounding_span": params["span"], "prov_method": params["method"],
                         **params["extra"]}
                self.edges.append((params["from_id"], params["to_id"], props))
            return _Result({"n": 1 if ok else 0})
        raise AssertionError(f"unexpected query: {query}")


class _Result:
    def __init__(self, rec):
        self.rec = rec

    def single(self):
        return self.rec


def _counts():
    return {"edges": 0, "skipped_unknown_edge_type": 0, "aliased_endpoints": 0}


def _event(**payload):
    item = {"type": "conflicts_with", "from_id": payload["from_id"], "to_id": payload["to_id"],
            "grounding_span": "span of a", "grounding_span_to": "span of b",
            "kind": "object_of_readiness", "source": "cross_document_pass",
            "adjudicated": False}
    return {"event_type": "edge_asserted", "event_id": "e1", "doc_id": "doc-a",
            "provenance": {"method": "cross_document_pass"},
            "payload": {"type": "conflicts_with", "from_type": "Definition",
                        "to_type": "Definition", "item": item, **payload}}


def _project(session, ev):
    notes = []
    counts = _counts()
    bp.project_edge(session, ev, DOCS, {}, WHITELIST, LABELS, counts, note=notes.append)
    return counts, notes


def test_control_1_unqualified_id_stays_scoped_to_the_asserting_document():
    session = _Session({("Definition", "doc-a::d1"), ("Definition", "doc-a::d2")})
    counts, notes = _project(session, _event(from_id="d1", to_id="d2"))
    assert session.edges == [("doc-a::d1", "doc-a::d2", {})]
    assert counts["edges"] == 1 and not notes
    assert bp.resolve_endpoint("doc-a", "d2", DOCS, {}) == "doc-a::d2"


def test_control_2_qualified_key_with_a_manifested_prefix_reaches_the_other_document():
    session = _Session({("Definition", "doc-a::d1"), ("Definition", "doc-b::d9")})
    counts, notes = _project(session, _event(from_id="d1", to_id="d9", from_key="doc-a::d1",
                                             to_key="doc-b::d9"))
    assert not notes
    assert counts["edges"] == 1 and counts["edges_cross_document"] == 1
    [(frm, to, props)] = session.edges
    assert (frm, to) == ("doc-a::d1", "doc-b::d9")
    assert props == {"grounding_span": "span of a", "grounding_span_to": "span of b",
                     "kind": "object_of_readiness", "source": "cross_document_pass",
                     "adjudicated": False, "prov_method": "cross_document_pass"}
    assert ("Definition", "doc-a::d9") not in session.nodes and \
        (None, "doc-a::d9") not in session.nodes, "the old phantom node was created"


def test_control_3_qualified_key_with_an_unmanifested_prefix_is_refused_and_logged():
    session = _Session({("Definition", "doc-a::d1")})
    counts, notes = _project(session, _event(from_id="d1", to_id="d9", from_key="doc-a::d1",
                                             to_key="doc-zzz::d9"))
    assert session.queries == [], "a refused edge reached the graph"
    assert session.edges == [] and session.nodes == {("Definition", "doc-a::d1")}
    assert counts["edges"] == 0 and counts["refused_qualified_endpoint"] == 1
    assert len(notes) == 1 and "doc-zzz" in notes[0] and "not a manifested doc_id" in notes[0]
