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
