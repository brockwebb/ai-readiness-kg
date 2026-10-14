"""The canonical export is an equivalence instrument (task
2026-10-12_projection_replay_measured_then_batched decision 3): it must be blind to storage
order and element ids, and see every content difference, twin and relationship endpoint."""
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "projection_canonical_export", REPO / "scripts" / "projection_canonical_export.py")
cx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cx)

NODES = [("e1", ["Document"], {"id": "d1", "key": "d1"}),
         ("e2", ["Claim"], {"key": "d1::c1", "grounding_span": "x"}),
         ("e3", ["Artifact", "Result"], {"id": "seldon-1"})]
RELS = [("e2", "e1", "PART_OF", {"prov_doc": "d1"}),
        ("e3", "e1", "ABOUT", {})]


def _hash(nodes, rels, exclude=("Artifact",), volatile=()):
    return cx.summarise(*cx.canonical(nodes, rels, exclude, volatile))


def test_blind_to_order_and_element_ids():
    renamed = {"e1": "x9", "e2": "x7", "e3": "x8"}
    nodes = [(renamed[e], l, p) for e, l, p in reversed(NODES)]
    rels = [(renamed[s], renamed[t], ty, p) for s, t, ty, p in reversed(RELS)]
    assert _hash(nodes, rels)["sha256"] == _hash(NODES, RELS)["sha256"]


def test_sees_a_property_change_and_a_twin():
    base = _hash(NODES, RELS)["sha256"]
    changed = [NODES[0], ("e2", ["Claim"], {"key": "d1::c1", "grounding_span": "y"}), NODES[2]]
    assert _hash(changed, RELS)["sha256"] != base
    twin = NODES + [("e4", ["Claim"], {"key": "d1::c1", "grounding_span": "x"})]
    out = _hash(twin, RELS)
    assert out["sha256"] != base and out["per_label"]["Claim"] == 2


def test_sees_a_rewired_relationship():
    rewired = [("e1", "e2", "PART_OF", {"prov_doc": "d1"}), RELS[1]]
    assert _hash(NODES, rewired)["sha256"] != _hash(NODES, RELS)["sha256"]


def test_excluded_labels_and_volatile_properties():
    out = _hash(NODES, RELS)
    assert out["nodes"] == 2 and "Artifact:Result" not in out["per_label"]
    # a relationship into the excluded graph is kept, its far end named out_of_scope
    _, rel_lines = cx.canonical(NODES, RELS, ["Artifact"], [])
    assert any('"start":"out_of_scope"' in ln for ln in rel_lines)
    stamped = [(e, l, {**p, "written_at": i}) for i, (e, l, p) in enumerate(NODES)]
    assert (_hash(stamped, RELS, volatile=("written_at",))["sha256"]
            == _hash(NODES, RELS)["sha256"])


def test_config_is_required(tmp_path, monkeypatch):
    bad = tmp_path / "controls.yaml"
    bad.write_text("projection:\n  progress_every: 5\n", encoding="utf-8")
    monkeypatch.setattr(cx, "CONTROLS_PATH", bad)
    with pytest.raises(SystemExit, match="canonical_export"):
        cx.export_config()


def test_repo_config_declares_scope():
    cfg = cx.export_config()
    assert "Artifact" in cfg["exclude_labels"] and cfg["volatile_properties"] == []
