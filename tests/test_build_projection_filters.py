"""build_projection.py pure filters (task 2026-08-22_kernel_tevv): TEVV retest events never
project; document_annotation projects only whitelisted properties."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_projection as bp  # noqa: E402


def test_tevv_retest_events_are_not_projectable():
    assert not bp.is_projectable({"event_type": "node_asserted", "purpose": "tevv_retest"})
    assert not bp.is_projectable({"event_type": "build_metrics", "purpose": "tevv_retest"})


def test_ordinary_events_are_projectable():
    assert bp.is_projectable({"event_type": "node_asserted"})
    assert bp.is_projectable({"event_type": "node_asserted", "purpose": None})


def test_annotation_update_whitelists_property():
    ev = {"event_type": "document_annotation", "doc_id": "d", "property": "is_platform_operator", "value": True}
    assert bp.annotation_update(ev) == ("d", "is_platform_operator", True)
    bad = dict(ev, property="title; DETACH DELETE n")
    assert bp.annotation_update(bad) is None
    assert bp.annotation_update({"event_type": "node_asserted"}) is None


def test_probe_judge_label_events_are_not_projectable():
    assert not bp.is_projectable({"event_type": "judge_label", "purpose": "probe"})


def test_historical_overlays_are_not_quarantine_events():
    # Enforcement is extraction-time only (repair Phase 5): overlays and the unrepairable
    # annotation are ordinary graph events that project; nothing about them is filtered.
    for et in ("grounding_relocated", "span_unrepairable", "attribute_nulled"):
        assert bp.is_projectable({"event_type": et})
    # and the overlay whitelist keeps payload-driven property names out of Cypher
    assert "description" in bp.NULLABLE_ATTRIBUTES and "id" not in bp.NULLABLE_ATTRIBUTES


# --- composite keying (task 2026-08-23_batched_repair_resume Phase 1; DD-020) -----------

def test_mutation_same_item_id_across_docs_no_longer_fuses():
    # defect reproduced: the OLD keying (bare item id) gives both items the same graph key
    old_key = lambda doc, item: item
    assert old_key("doc-a", "c_ai") == old_key("doc-b", "c_ai")          # fused (the bug)
    # fixed keying yields two distinct nodes
    assert bp.node_key("doc-a", "c_ai") != bp.node_key("doc-b", "c_ai")
    assert bp.node_key("doc-a", "c_ai") == "doc-a::c_ai"


def test_resolve_endpoint_document_scope_vs_item_scope():
    docs = {"fcsm-25-03", "w3c-dcat-3"}
    aliases = {"doc-fcsm-framework": "fcsm-25-03"}
    assert bp.resolve_endpoint("w3c-dcat-3", "fcsm-25-03", docs, aliases) == "fcsm-25-03"
    assert bp.resolve_endpoint("w3c-dcat-3", "doc-fcsm-framework", docs, aliases) == "fcsm-25-03"
    assert bp.resolve_endpoint("w3c-dcat-3", "c_catalog", docs, aliases) == "w3c-dcat-3::c_catalog"
    # dangling doc-like id never manifested stays scoped to the asserting doc
    assert bp.resolve_endpoint("w3c-dcat-3", "doc-omb-m-25-05", docs, {}) == "w3c-dcat-3::doc-omb-m-25-05"


def test_attribute_restored_projects_only_behind_the_acceptance_gate():
    # The 2026-08-23 acceptance measure FAILED (0.78 < 0.90): v1 restorations are reversed
    # by rule and attribute_restored is NOT an annotation. v0.3.4 (overnight burn Lane 4,
    # gate-before-wire): restorations live in the TAGGED shard batch-014_restoration_v2 and
    # the sole projection path is the block guarded by a `restoration_class_accepted` event
    # — untagged attribute_restored events (the reversed v1 ones) still never project.
    import inspect
    src = inspect.getsource(bp)
    assert bp.annotation_update({"event_type": "attribute_restored", "doc_id": "d",
                                 "property": "description", "value": "x"}) is None
    # exactly one handler, and it sits inside the acceptance-gated restoration_v2 block
    assert src.count('"attribute_restored"') == 1
    gated = src.split('restoration_class_accepted', 1)
    assert len(gated) == 2 and '"attribute_restored"' in gated[1], \
        "attribute_restored handling must be behind the restoration_class_accepted gate"
    assert 'replay(tag="restoration_v2")' in gated[1], \
        "accepted restorations must come from the tagged shard, never the untagged log"


# ---------------------------------------------------------------------------
# shard-order independence (task 2026-09-04_extract_g1eval_17_and_rerun §1.4)
# ---------------------------------------------------------------------------

class _RecordingSession:
    """Records every Cypher call. `build()` only ever consumes the result of the reset and
    the MERGEs, none of which this projection path reads back, so returning an empty list is
    faithful — the assertions are about the ORDER of the writes."""

    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((" ".join(query.split()), params))
        return []


def _shard(events_dir, n, rows):
    import json
    (events_dir / f"batch-{n:03d}.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_a_document_manifested_after_its_extraction_still_owns_its_edges(tmp_path, monkeypatch):
    """REGRESSION. The 17 `g1eval` documents were extracted into the OPEN bulk shard
    (batch-023) while their `manifest_add` sat in a LATER shard (batch-025, admitted
    2026-09-02). `replay()` yields shards in batch order, so every `ASSERTS`/`MENTIONS`/
    `DEFINES` edge reached `MERGE (a {key: $from_id})` before any node carried that key —
    which CREATED an unlabelled node and left the real `Document` node, merged later on
    `(:Document {id})`, with degree zero. All 17 read `run_ok_no_edges` in the gap diagnostic
    after a clean extraction and a full replay: 293 edges hanging off a label-less twin.

    The graph must not depend on which shard a document's admission landed in."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)

    prov = {"model_id": "m", "source_sha256": "sha"}
    _shard(events, 1, [{"event_type": "edge_asserted", "doc_id": "late-doc", "provenance": prov,
                        "payload": {"type": "asserts", "from_id": "late-doc", "to_id": "cl_x",
                                    "item": {"grounding_span": "span"}}}])
    _shard(events, 2, [{"event_type": "manifest_add",
                        "payload": {"doc_id": "late-doc", "title": "t", "source_type": "academic",
                                    "pub_date": "2026", "primary_url": "u", "content_hash": "h"}}])

    session = _RecordingSession()
    bp.build(session, ["Document", "Concept", "Claim"], {"asserts"})

    merges = [i for i, (q, p) in enumerate(session.calls)
              if "MERGE (d:Document {id: $id})" in q and p.get("id") == "late-doc"]
    edges = [i for i, (q, p) in enumerate(session.calls)
             if q.startswith("MERGE (a {key: $from_id})") and p.get("from_id") == "late-doc"]
    assert merges and edges, "fixture must exercise both paths"
    assert min(merges) < min(edges), (
        "the Document node must exist before an edge merges on its key, or the edge creates "
        "an unlabelled twin and the Document ends up with no edges at all")


def test_the_reset_clears_unlabelled_endpoint_nodes_too(tmp_path, monkeypatch):
    """REGRESSION, found by the fix above. `MERGE (a {key: ...})` creates endpoint nodes that
    carry NO label — scoped item keys, cited-document ids, and (before the fix above) twins of
    real Documents. The reset deleted only KG-LABELLED nodes, so every one of those survived
    every replay: the live graph held 1,201 degree-zero nodes carrying only an `id`, left by an
    older keying scheme, and 17 labelless twins that still matched `MERGE (a {key: ...})` —
    which then attached the SAME edge to both the twin and the real Document.

    A projection that is rebuilt by replay must be rebuilt entirely, or it is not a projection.
    Seldon's own artifacts are unaffected: every one of them carries a label."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    _shard(events, 1, [])

    session = _RecordingSession()
    bp.build(session, ["Document", "Concept"], set())

    deletes = [q for q, _ in session.calls if "DETACH DELETE" in q]
    assert any("size(labels(n)) = 0" in q for q in deletes), (
        "the reset must clear unlabelled endpoint nodes, or they accumulate across replays "
        f"and across code generations; deletes were {deletes}")


# --- vocabulary resolution at write time (task 2026-09-05_vocabulary_and_entity_linking §1.4)

def test_a_node_whose_name_is_a_vocabulary_term_gets_a_resolves_to_edge(tmp_path, monkeypatch):
    """§1.4: the loader resolves at WRITE time, alias-first, against the current vocabulary
    epoch. Doing it here rather than in a later pass is the whole point — a node that reaches
    the graph unresolved and is linked afterwards has a window in which every query over it
    silently reads the per-document duplicate."""
    from kg import eventlog, vocab
    events = tmp_path / "events"
    events.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)

    prov = {"model_id": "m"}
    _shard(events, 1, [
        {"event_type": "term_added", "term_id": "air:concept/dcat", "pref_label": "DCAT",
         "scope_note": "W3C Data Catalog Vocabulary.", "source": "graph: 3 Concept nodes",
         "alt_labels": [], "node_labels": ["Concept"], "ts": "2026-09-05T00:00:00+00:00"},
        {"event_type": "term_alias_added", "term_id": "air:concept/dcat",
         "alias": "Data Catalog Vocabulary", "source": "s", "ts": "2026-09-05T00:00:00+00:00"},
        {"event_type": "vocabulary_epoch", "epoch": 1, "note": "seed",
         "ts": "2026-09-05T00:00:00+00:00"},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": prov,
         "payload": {"type": "Concept", "id": "c1", "item": {"name": "Data Catalog Vocabulary"}}},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": prov,
         "payload": {"type": "Concept", "id": "c2", "item": {"name": "a novel term nobody indexed"}}},
    ])

    session = _RecordingSession()
    bp.build(session, ["Document", "Concept"], set())
    qs = [q for q, _ in session.calls]

    # the hit: a RESOLVES_TO edge to the term
    resolved = [(q, p) for q, p in session.calls if "RESOLVES_TO" in q]
    assert len(resolved) == 1, qs
    assert resolved[0][1]["term"] == "air:concept/dcat"
    assert resolved[0][1]["key"] == bp.node_key("d1", "c1")

    # the miss: flagged, never guessed
    unresolved = [(q, p) for q, p in session.calls if "unresolved" in q]
    assert len(unresolved) == 1
    assert unresolved[0][1]["key"] == bp.node_key("d1", "c2")

    # and the Term node itself is projected from the log, so the graph stays disposable
    assert any("MERGE (t:Term" in q for q in qs)


def test_the_reset_clears_term_nodes_so_a_replay_rebuilds_the_vocabulary(tmp_path, monkeypatch):
    """`Term` is not a KG schema label, so it is not in `kg_labels` and the label reset misses
    it. Left alone, a deprecated or renamed term would survive every replay forever — the
    graph would stop being a projection of the log, which is invariant 1."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    _shard(events, 1, [])
    session = _RecordingSession()
    bp.build(session, ["Concept"], set())
    deletes = [q for q, _ in session.calls if "DETACH DELETE" in q]
    assert any("n:Term" in q for q in deletes), deletes


def test_a_judged_link_is_written_from_its_event_not_recomputed(tmp_path, monkeypatch):
    """§2.2's accepted merges are DECISIONS, so they are events and the loader replays them.
    The deterministic link is a DERIVATION and is recomputed. Storing the derivation would
    make the log disagree with itself the moment the vocabulary changed."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    _shard(events, 1, [
        {"event_type": "term_added", "term_id": "air:concept/x", "pref_label": "X",
         "scope_note": "", "source": "graph: 2 Concept nodes", "alt_labels": [],
         "node_labels": ["Concept"], "ts": "2026-09-05T00:00:00+00:00"},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Concept", "id": "c9", "item": {"name": "something else entirely"}}},
        {"event_type": "term_link_judged", "node_key": "d1::c9", "term_id": "air:concept/x",
         "verdict": "same", "confidence": 0.91, "ts": "2026-09-05T00:00:00+00:00"},
    ])
    session = _RecordingSession()
    bp.build(session, ["Concept"], set())
    linked = [(q, p) for q, p in session.calls if "RESOLVES_TO" in q]
    assert len(linked) == 1 and linked[0][1]["term"] == "air:concept/x"
    assert linked[0][1]["key"] == "d1::c9"


def test_a_node_with_no_name_is_neither_resolved_nor_flagged_unresolved(tmp_path, monkeypatch):
    """`Claim`, `Definition`, `Measure` and `Practice` nodes carry no `name` property at all —
    a claim is a sentence, not a named entity. Flagging 11,526 of them `unresolved: true`
    (which the first cut of §1.4 did) makes the residue read almost three times its real size
    and invites someone to go looking for vocabulary terms that could never exist."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    _shard(events, 1, [
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Claim", "id": "cl1", "item": {"claim_text": "a sentence"}}},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Concept", "id": "c1", "item": {"name": "unknown term"}}},
    ])
    session = _RecordingSession()
    counts = bp.build(session, ["Claim", "Concept"], set())
    flagged = [p["key"] for q, p in session.calls if "unresolved" in q]
    assert flagged == [bp.node_key("d1", "c1")], flagged
    assert counts["unresolved"] == 1


def test_a_node_that_resolves_two_ways_across_its_assertions_resolves_to_neither(tmp_path, monkeypatch):
    """A node is asserted once per chunk that mentions it, and the extractor's spelling can
    drift between assertions — `scientifc integrity` and `scientific integrity` on one node
    key. Resolving per assertion writes BOTH edges and the node then claims two terms, which
    is the ambiguity `vocab.resolve` refuses at the term level reappearing at the node level.
    One node, one term, or none."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    _shard(events, 1, [
        {"event_type": "term_added", "term_id": "air:concept/a", "pref_label": "Alpha",
         "scope_note": "", "source": "graph: 2 Concept nodes", "alt_labels": [],
         "node_labels": ["Concept"], "ts": "2026-09-05T00:00:00+00:00"},
        {"event_type": "term_added", "term_id": "air:concept/b", "pref_label": "Beta",
         "scope_note": "", "source": "graph: 2 Concept nodes", "alt_labels": [],
         "node_labels": ["Concept"], "ts": "2026-09-05T00:00:00+00:00"},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Concept", "id": "c1", "item": {"name": "Alpha"}}},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Concept", "id": "c1", "item": {"name": "Beta"}}},
    ])
    session = _RecordingSession()
    counts = bp.build(session, ["Concept"], set())
    assert [q for q, _ in session.calls if "RESOLVES_TO" in q] == []
    assert counts["unresolved"] == 1
    assert counts["resolved"] == 0


def test_each_resolved_node_gets_exactly_one_resolves_to_write(tmp_path, monkeypatch):
    """A node asserted five times must not produce five writes. The projection is already the
    slowest step in the pipeline; one round-trip per assertion added 16,000 needless ones."""
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    _shard(events, 1, [
        {"event_type": "term_added", "term_id": "air:concept/a", "pref_label": "Alpha",
         "scope_note": "", "source": "graph: 2 Concept nodes", "alt_labels": [],
         "node_labels": ["Concept"], "ts": "2026-09-05T00:00:00+00:00"},
    ] + [
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Concept", "id": "c1", "item": {"name": "Alpha"}}}
        for _ in range(5)
    ])
    session = _RecordingSession()
    counts = bp.build(session, ["Concept"], set())
    assert len([q for q, _ in session.calls if "RESOLVES_TO" in q]) == 1
    assert counts["resolved"] == 1


def test_a_key_asserted_under_two_types_resolves_only_the_node_that_has_the_name(tmp_path, monkeypatch):
    """REGRESSION, and the same trap as the g1eval one: `MATCH (n {key: $key})` binds EVERY
    node carrying that key, so a resolution written for a Concept also lands on a Claim twin.

    DD-020 keys a node `<doc_id>::<item_id>`, and the extractor sometimes asserts one item id
    under two types in one document — 82 of them live: 75 Claim+Concept, 7 Platform+Practice.
    Every one produced a spurious write: 32 got a RESOLVES_TO edge on the twin (which is the
    whole 6,408 -> 6,440 gap the prior RESULT could not account for) and 50 got
    `unresolved: true` on it (7,569 -> 7,619). The counters were right; the writes were not.

    A `Claim` carries no `name` and can never resolve, so a RESOLVES_TO edge on one is
    meaningless — and worse, it makes the Claim a MEMBER of a vocabulary term, which any
    per-term analysis then reads as evidence.
    """
    from kg import eventlog
    events = tmp_path / "events"
    events.mkdir()
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    _shard(events, 1, [
        {"event_type": "term_added", "term_id": "air:concept/a", "pref_label": "Alpha",
         "scope_note": "", "source": "graph: 2 Concept nodes", "alt_labels": [],
         "node_labels": ["Concept"], "ts": "2026-09-05T00:00:00+00:00"},
        # one item id, two types, one document — exactly the live shape
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Concept", "id": "c4", "item": {"name": "Alpha"}}},
        {"event_type": "node_asserted", "doc_id": "d1", "provenance": {"model_id": "m"},
         "payload": {"type": "Claim", "id": "c4", "item": {"claim_text": "a sentence"}}},
    ])
    session = _RecordingSession()
    counts = bp.build(session, ["Concept", "Claim"], set())

    resolved = [(q, p) for q, p in session.calls if "RESOLVES_TO" in q]
    assert len(resolved) == 1, [q for q, _ in session.calls]
    # the write must name the label, or it binds the twin as well
    assert "n:Concept" in resolved[0][0], resolved[0][0]
    assert counts["resolved"] == 1
    # and the Claim twin is neither resolved nor flagged: it has no name
    assert [q for q, _ in session.calls if "unresolved" in q] == []
