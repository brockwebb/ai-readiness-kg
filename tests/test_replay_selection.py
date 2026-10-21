"""`ReplaySelection`: which events the KG replay projects, factored out of `build()` (squiddy SQ-019, Part B step 3).

squiddy's adopter admits this graph's extracted items into the kit by calling this selection rather than
re-implementing it, so the test here is the one the task asked for: the projection's selection is unchanged. A fixture
log exercises every skip `build()` makes (a non-graph purpose, a whole superseded extraction, a superseded stratum, a
label and an edge type the schema does not carry), and `build()` itself, against a recording session, writes exactly
the nodes and edges the selection says it will. The whole-log equivalence (every Cypher call `build()` makes on the
real log, hashed, before and after the factoring) is recorded in squiddy's `docs/evidence/sq019/`.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_projection as bp  # noqa: E402
from kg import eventlog  # noqa: E402

KG_LABELS = ["Document", "Concept", "Claim", "Instrument", "Measure"]
EDGES = {"mentions", "uses_measure"}


class _Result:
    def single(self):
        return {"n": 1}


class Recording:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return _Result()


def node(doc, item, typ, sha, **extra):
    return {"event_type": "node_asserted", "doc_id": doc, "event_id": f"e-{item}",
            "provenance": {"model_id": "m", "source_sha256": sha, "extraction_event_id": "x"},
            "payload": {"id": item, "type": typ, "item": {"id": item, "name": item, "grounding_span": "s"}}, **extra}


def edge(doc, typ, frm, to, sha, **extra):
    return {"event_type": "edge_asserted", "doc_id": doc, "event_id": f"e-{typ}-{frm}-{to}",
            "provenance": {"model_id": "m", "source_sha256": sha},
            "payload": {"type": typ, "from_id": frm, "to_id": to, "item": {"grounding_span": "s"}}, **extra}


@pytest.fixture
def log(tmp_path, monkeypatch):
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path)
    monkeypatch.setattr(bp, "bulk_purposes", lambda: set())
    events = [
        {"event_type": "manifest_add", "event_id": "m1", "payload": {"doc_id": "d1", "title": "D1"}},
        node("d1", "c-kept", "Concept", "A"),                                         # projects
        node("d1", "c-retest", "Concept", "A", purpose="tevv_retest"),                # non-graph purpose
        node("d1", "c-old", "Concept", "OLD"),                                        # whole extraction superseded
        node("d1", "i-old", "Instrument", "S2"),                                      # instrument stratum superseded
        node("d1", "m-kept", "Measure", "S2"),                                        # same extraction, other stratum
        edge("d1", "uses_measure", "i-old", "m-kept", "S2"),                          # instrument-anchored: superseded
        node("d1", "x-assess", "AssessmentIndicator", "A"),                           # not a KG label
        edge("d1", "mentions", "d1", "c-kept", "A"),                                  # projects
        edge("d1", "not_an_edge", "d1", "c-kept", "A"),                               # not on the whitelist
        {"event_type": "extraction_superseded", "doc_id": "d1", "superseded_source_sha256": "OLD",
         "event_id": "s1"},
        {"event_type": "extraction_superseded", "doc_id": "d1", "superseded_source_sha256": "S2",
         "superseded_strata": ["instrument"], "event_id": "s2"},
    ]
    (tmp_path / "batch-001.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return events


def selected(sel):
    """(skip reason, label or rel) for every event of the replay, in order, by the shared functions."""
    out = {}
    for stem, ev in bp.kg_events_located():
        why = sel.skip_reason(ev)
        et = ev.get("event_type")
        what = (bp.node_label(ev, KG_LABELS) if et == "node_asserted"
                else bp.edge_rel(ev, EDGES) if et == "edge_asserted" else None)
        out[ev["event_id"]] = (why, what, stem)
    return out


def test_every_skip_build_makes_is_the_selections(log):
    got = selected(bp.ReplaySelection())
    assert got["e-c-kept"] == (None, "Concept", "batch-001")
    assert got["e-c-retest"][0] == "skipped_non_graph_purpose"
    assert got["e-c-old"][0] == "skipped_superseded_extraction"
    assert got["e-i-old"][0] == "skipped_superseded_stratum"
    assert got["e-m-kept"] == (None, "Measure", "batch-001")
    assert got["e-uses_measure-i-old-m-kept"][0] == "skipped_superseded_stratum"
    assert got["e-x-assess"] == (None, None, "batch-001")                    # projects as nothing: no KG label
    assert got["e-mentions-d1-c-kept"] == (None, "mentions", "batch-001")
    assert got["e-not_an_edge-d1-c-kept"] == (None, None, "batch-001")


def test_build_writes_exactly_what_the_selection_selects(log):
    s = Recording()
    counts = bp.build(s, KG_LABELS, EDGES, progress=bp.Progress(None, out=None))
    written_nodes = sorted(p["key"] for q, p in s.calls if q.startswith("MERGE (n:") and "SET n += $props" in q)
    assert written_nodes == ["d1::c-kept", "d1::m-kept"]
    written_edges = [(p["from_id"], q.split("[r:")[1].split("]")[0], p["to_id"]) for q, p in s.calls
                     if "MERGE (a)-[r:" in q]
    assert written_edges == [("d1", "MENTIONS", "d1::c-kept")]
    sel = selected(bp.ReplaySelection())
    want = {k: sum(1 for v in sel.values() if v[0] == k)
            for k in ("skipped_non_graph_purpose", "skipped_superseded_extraction", "skipped_superseded_stratum")}
    assert {k: counts[k] for k in want} == want == {"skipped_non_graph_purpose": 1,
                                                    "skipped_superseded_extraction": 1,
                                                    "skipped_superseded_stratum": 2}
    assert counts["skipped_unknown_edge_type"] == 1


def test_replay_located_is_replay_with_its_location(log, tmp_path):
    plain = list(eventlog.replay())
    located = list(eventlog.replay_located())
    assert [e for _s, _n, e in located] == plain
    assert [n for _s, n, _e in located] == list(range(1, len(plain) + 1))
    assert {s for s, _n, _e in located} == {tmp_path / "batch-001.jsonl"}
