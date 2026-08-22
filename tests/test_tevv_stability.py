"""TEVV stability metrics (scripts/tevv_stability.py): identity, kappa, Jaccard."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import tevv_stability as ts  # noqa: E402


def _node(doc, nid, typ, text, span="s"):
    return {"event_type": "node_asserted", "doc_id": doc,
            "payload": {"id": nid, "type": typ, "item": {ts.PRIMARY_TEXT[typ]: text, "grounding_span": span}}}


def _edge(doc, typ, a, b, span="e"):
    return {"event_type": "edge_asserted", "doc_id": doc,
            "payload": {"type": typ, "from_id": a, "to_id": b, "item": {"grounding_span": span}}}


def test_node_identity_is_type_plus_nfkc_normalized_text():
    a = ts.node_identity({"type": "Concept", "item": {"name": "AI  readiness"}})
    b = ts.node_identity({"type": "Concept", "item": {"name": "ai readiness"}})
    assert a == b == ("Concept", "ai readiness")
    assert ts.node_identity({"type": "Claim", "item": {"claim_text": "ﬁne"}})[1] == "fine"


def test_edge_identity_uses_endpoint_identities_not_slugs():
    run1 = [_node("d", "c1", "Concept", "Crawl budget"), _edge("d", "mentions", "d", "c1")]
    run2 = [_node("d", "zz9", "Concept", "crawl budget"), _edge("d", "mentions", "d", "zz9")]
    _, e1, _ = ts.run_items(run1, "d"); _, e2, _ = ts.run_items(run2, "d")
    assert e1 == e2


def test_kappa_identical_sets_is_one_and_disjoint_is_negative_or_zero():
    a = {("Concept", "x"), ("Concept", "y")}
    assert ts.kappa_presence(a, set(a)) == 1.0
    k = ts.kappa_presence({("Concept", "x")}, {("Concept", "y")})
    assert k is not None and k <= 0.0
    assert ts.kappa_presence(set(), set()) is None


def test_kappa_half_overlap_value():
    a = {("C", "1"), ("C", "2"), ("C", "3")}; b = {("C", "1"), ("C", "2"), ("C", "4")}
    # union 4: po=2/4=.5, pa=pb=.75, pe=.5625+.0625=.625 -> kappa=(.5-.625)/(.375)=-1/3
    assert ts.kappa_presence(a, b) == pytest.approx(-1 / 3)


def test_jaccard_and_compare_doc():
    o = [_node("d", "a", "Concept", "X", "span one"), _node("d", "b", "Claim", "Y", "span two")]
    r = [_node("d", "q", "Concept", "x", "span one"), _node("d", "w", "Claim", "Z", "span three")]
    res = ts.compare_doc(o, r, "d")
    assert res["nodes"]["both"] == 1 and res["nodes"]["only_one_run"] == 2
    assert res["spans"]["jaccard"] == pytest.approx(1 / 3)
    assert res["per_type"]["Concept"]["kappa"] == 1.0


def test_pooled_across_docs_keeps_docs_disjoint():
    o = [_node("d1", "a", "Concept", "same"), _node("d2", "a", "Concept", "same")]
    r = [_node("d1", "a", "Concept", "same"), _node("d2", "b", "Concept", "other")]
    p = ts.pooled_from_events(o, r, ["d1", "d2"])
    assert p["per_type"]["Concept"]["both"] == 1 and p["per_type"]["Concept"]["orig"] == 2


def test_positive_agreement_is_dice_and_survives_kappa_paradox():
    a = {("C", str(i)) for i in range(100)}; b = {("C", str(i)) for i in range(40, 140)}
    assert ts.positive_agreement(a, b) == pytest.approx(0.6)
    assert ts.kappa_presence(a, b) < 0          # the paradox: 60% overlap, negative kappa
