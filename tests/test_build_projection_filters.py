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
