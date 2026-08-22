"""Quality monitors (scripts/quality_monitors.py, task 2026-08-21_v03_visibility_kernel
Phase 6). Pure functions only: metrics, control limits, monitor firing, and the seeded
known-bad used by the positive control. The live-log run and the Neo4j/dixie paths are
exercised by `scripts/quality_monitors.py --mutation-test` (recorded in the phase RESULT)."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import quality_monitors as qm  # noqa: E402


def _bm(doc, epoch_hint, density, qrate, proposed, nodes=10, edges=10, q=0, sv="0.3", eid=None):
    eid = eid or f"e_{doc}"
    return {"event_type": "build_metrics", "doc_id": doc, "extraction_event_id": eid,
            "metrics": {"doc_id": doc, "estimated_tokens": 1000, "concepts": 5,
                        "concepts_per_1k_tokens": density, "definitions_count": 0,
                        "claims_count": 0, "nodes": nodes, "edges": edges, "quarantined": q,
                        "quarantine_rate": qrate, "proposed_relationships_count": proposed},
            "event_id": f"id_{doc}", "timestamp": "t", "schema_version": sv}


def _claim(doc, epoch, grade, eid=None, span="a span"):
    eid = eid or f"e_{doc}"
    item = {"id": "c1", "claim_text": "x", "grounding_span": span}
    if grade is not None:
        item["evidence_grade"] = grade
    return {"event_type": "node_asserted", "doc_id": doc, "extraction_event_id": eid,
            "provenance": {"corpus_epoch": epoch, "extraction_event_id": eid,
                           "source_sha256": "s"},
            "payload": {"id": "c1", "type": "Claim", "item": item},
            "event_id": f"n_{doc}_{grade}", "timestamp": "t", "schema_version": "0.3"}


@pytest.fixture(autouse=True)
def _no_overlays(monkeypatch):
    # live_events/_shard_of read the real log; the pure tests feed events directly.
    monkeypatch.setattr(qm, "live_events", lambda evs: evs)
    monkeypatch.setattr(qm, "_shard_of", lambda ev: 6)


def test_per_doc_metrics_epoch_from_assertions_and_shard_fallback():
    evs = [_claim("d1", "v1", "inference"), _bm("d1", None, 5.0, 0.0, 1),
           _bm("empty", None, 0.0, 0.0, 0, nodes=0, edges=0)]   # no assertions -> shard fallback
    m = qm.per_doc_metrics(evs, {"v1", "kernel-v03"}, shard_epoch={6: "kernel-v03"})
    assert m["d1"]["epoch"] == "v1"
    assert m["empty"]["epoch"] == "kernel-v03"
    assert m["d1"]["claims"]["distribution"] == {"inference": 1}
    assert m["d1"]["proposed_rate"] == pytest.approx(1 / 21)


def test_per_doc_metrics_counts_missing_and_invalid_grades():
    evs = [_claim("d", "v1", None), _claim("d", "v1", "not_a_grade"),
           _claim("d", "v1", "platform_official"), _bm("d", None, 1.0, 0.0, 0)]
    c = qm.per_doc_metrics(evs, {"v1"})["d"]["claims"]
    assert (c["total"], c["missing"], c["invalid"], c["graded"]) == (3, 1, 1, 1)


def test_control_limits_mean_sd_and_floor_at_zero():
    base = {f"d{i}": {"concepts_per_1k_tokens": x, "quarantine_rate": 0.0, "proposed_rate": 0.0}
            for i, x in enumerate([2.0, 4.0, 6.0])}
    lim = qm.control_limits(base, 3)
    d = lim["metrics"]["concepts_per_1k_tokens"]
    assert d["mean"] == 4.0 and d["sd"] == 2.0 and d["ucl"] == 10.0 and d["lcl"] == 0.0
    assert lim["metrics"]["quarantine_rate"]["sd"] == 0.0


def test_control_limits_refuses_tiny_baseline():
    with pytest.raises(SystemExit):
        qm.control_limits({"only": {"concepts_per_1k_tokens": 1, "quarantine_rate": 0, "proposed_rate": 0}}, 3)


def test_evidence_grade_monitor_fires_only_from_required_schema():
    cfg = {"evidence_grade_required_from_schema": "0.3",
           "evidence_grade_missing_stop_fraction": 0.10}
    old = {"doc_id": "old", "schema_version": "0.2",
           "claims": {"total": 4, "graded": 0, "missing": 4, "invalid": 0, "distribution": {}}}
    new = {"doc_id": "new", "schema_version": "0.3",
           "claims": {"total": 4, "graded": 3, "missing": 1, "invalid": 0, "distribution": {}}}
    r = qm.monitor_evidence_grade({"old": old}, cfg)
    assert r["fired"] is False
    r = qm.monitor_evidence_grade({"old": old, "new": new}, cfg)
    assert r["fired"] is True and r["docs"][0]["doc_id"] == "new"
    assert r["docs"][0]["over_stop_fraction"] is True   # 1/4 > 0.10


def test_limit_monitor_fires_above_ucl_and_above_hard_ceiling():
    limits = {"metrics": {"quarantine_rate": {"mean": 0.03, "sd": 0.01, "lcl": 0.0, "ucl": 0.06}}}
    docs = {"ok": {"doc_id": "ok", "epoch": "k", "quarantine_rate": 0.02},
            "ucl": {"doc_id": "ucl", "epoch": "k", "quarantine_rate": 0.07},
            "stop": {"doc_id": "stop", "epoch": "k", "quarantine_rate": 0.2}}
    r = qm._limit_monitor("quarantine", "quarantine_rate", docs, limits,
                          hard_ceiling=0.15, two_sided=False)
    hit = {d["doc_id"]: d["reasons"] for d in r["docs"]}
    assert set(hit) == {"ucl", "stop"}
    assert any("declared stop" in x for x in hit["stop"])


def test_grounding_monitor_fires_on_unmatched_span(tmp_path):
    src = tmp_path / "d.md"; src.write_text("the quick brown fox", encoding="utf-8")
    evs = [_claim("d", "k", "inference", span="quick brown"),
           _claim("d", "k", "inference", span="ZZZ not here")]
    r = qm.monitor_grounding(evs, {"d": src}, {"k"})
    assert r["fired"] and r["failure_count"] == 1 and r["checked"] == 2


def test_seed_known_bad_appends_two_events_to_scratch_shard(tmp_path):
    seed = qm.seed_known_bad(tmp_path, "doc-x", "kernel-v03", 6)
    lines = [json.loads(l) for l in (tmp_path / "batch-006.jsonl").read_text().splitlines()]
    assert [e["event_type"] for e in lines] == ["node_asserted", "build_metrics"]
    assert "evidence_grade" not in lines[0]["payload"]["item"]
    assert lines[1]["metrics"]["quarantine_rate"] > 0.15
    assert seed["extraction_event_id"] == lines[0]["extraction_event_id"]
