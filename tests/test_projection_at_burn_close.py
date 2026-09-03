"""A completed burn ends with a projection replay, and the gate report refuses to stand on a
projection that lacks the newest corpus epoch (task 2026-09-02_post_burn_reconciliation §4).

The deck task of 2026-09-02 found the graph holding ZERO `bulk-v038` nodes after the burn
had closed: nothing rebuilt the projection when the last verdict was written, so every count
read from Neo4j was a count of the previous burn. No live Neo4j here — the reachability
probe and the replay are injected.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import build_projection as proj  # noqa: E402
import run_baseline_gates as rbg  # noqa: E402
import run_chunked_bulk as rcb  # noqa: E402


@pytest.fixture
def pcfg(tmp_path, monkeypatch):
    cfg = {"stale_marker": tmp_path / "projection_stale.json",
           "replay_script": tmp_path / "build_projection.py",
           "python": sys.executable}
    monkeypatch.setattr(proj, "projection_config", lambda: cfg)
    return cfg


# --- the close hook ---------------------------------------------------------------------
def test_unreachable_neo4j_writes_the_stale_marker_and_does_not_fail_the_burn(pcfg, capsys):
    calls = []
    out = rcb.close_burn(probe=lambda: False, replay=lambda: calls.append("replay") or 0)
    assert out["projection"] == "stale" and calls == []
    marker = json.loads(pcfg["stale_marker"].read_text(encoding="utf-8"))
    assert marker["reason"] == "neo4j_unreachable" and marker["profile"] == rcb.PROFILE
    assert str(pcfg["stale_marker"]) in capsys.readouterr().out


def test_reachable_neo4j_replays_the_projection_and_leaves_no_marker(pcfg):
    calls = []
    out = rcb.close_burn(probe=lambda: True, replay=lambda: calls.append("replay") or 0)
    assert out["projection"] == "rebuilt" and calls == ["replay"]
    assert not pcfg["stale_marker"].exists()


def test_a_failed_replay_is_a_marker_not_a_burn_failure(pcfg):
    out = rcb.close_burn(probe=lambda: True, replay=lambda: 3)
    assert out["projection"] == "stale"
    assert json.loads(pcfg["stale_marker"].read_text(encoding="utf-8"))["reason"] == \
        "replay_failed"


def test_the_default_replay_is_the_configured_interpreter_and_script(pcfg, monkeypatch):
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        return type("R", (), {"returncode": 0})()
    monkeypatch.setattr(rcb.subprocess, "run", fake_run)
    rcb.close_burn(probe=lambda: True)
    assert seen["cmd"] == [sys.executable, str(pcfg["replay_script"])]


def test_only_a_burn_whose_every_dispatched_batch_is_settled_is_complete():
    plan = [{"batch_id": "b1", "dispatch": ["d"]}, {"batch_id": "b2", "dispatch": []},
            {"batch_id": "b3", "dispatch": ["e"]}]
    assert rcb.burn_complete(plan, {"b1": "accept", "b3": "sampling_inconclusive"})
    assert not rcb.burn_complete(plan, {"b1": "accept"})          # b3 unjudged
    assert not rcb.burn_complete(plan, {"b1": "accept", "b3": "accept"}, halted=True)


# --- the freshness check ----------------------------------------------------------------
def test_missing_members_is_the_set_difference_in_declared_order():
    assert proj.missing_epoch_members({"a", "c"}, ["a", "b", "c", "d"]) == ["b", "d"]
    assert proj.missing_epoch_members({"a", "b"}, ["a", "b"]) == []


def test_the_newest_epoch_is_the_latest_declaration_by_timestamp(tmp_path, monkeypatch):
    lines = [
        {"event_type": "corpus_epoch_declared", "timestamp": "2026-08-30T01:00:00+00:00",
         "payload": {"epoch": "older", "member_doc_ids": ["x"]}},
        {"event_type": "corpus_epoch_declared", "timestamp": "2026-09-02T22:00:00+00:00",
         "payload": {"epoch": "newest", "member_doc_ids": ["a", "b"]}},
        {"event_type": "corpus_epoch_declared", "timestamp": "2026-09-02T22:05:00+00:00",
         "payload": {"epoch": "newest", "member_doc_ids": ["c"]}},
        {"event_type": "manifest_add", "timestamp": "2026-09-03T00:00:00+00:00",
         "payload": {"doc_id": "z"}},
    ]
    p = tmp_path / "decisions.jsonl"
    p.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    monkeypatch.setattr(proj, "DIXIE_DECISIONS", p)
    # the shard-shaped declaration (top-level epoch/members) is read too
    monkeypatch.setattr(proj.eventlog, "replay", lambda: iter([
        {"event_type": "corpus_epoch_declared", "timestamp": "2026-08-29T12:00:00+00:00",
         "epoch": "shard-shaped", "members": ["s"]}]))
    assert proj.newest_corpus_epoch() == ("newest", ["a", "b", "c"])


def test_the_gate_report_refuses_a_projection_missing_the_newest_epoch(tmp_path, monkeypatch):
    monkeypatch.setattr(proj, "newest_corpus_epoch", lambda: ("g1eval", ["a", "b"]))
    monkeypatch.setattr(proj, "projected_document_ids_live", lambda: {"a"})
    with pytest.raises(SystemExit) as ei:
        rbg.refuse_if_projection_stale()
    assert "g1eval" in str(ei.value) and "b" in str(ei.value)


def test_the_gate_report_stands_when_the_projection_carries_the_newest_epoch(monkeypatch):
    monkeypatch.setattr(proj, "newest_corpus_epoch", lambda: ("g1eval", ["a", "b"]))
    monkeypatch.setattr(proj, "projected_document_ids_live", lambda: {"a", "b", "extra"})
    assert rbg.refuse_if_projection_stale() == ("g1eval", 2)


def test_main_writes_no_report_on_a_stale_projection(tmp_path, monkeypatch):
    """The refusal sits between the checks and the report: nothing is written."""
    ok = {"check_id": "x", "value": 0, "threshold": 0, "passed": True}
    for name in ("check_min_corpus", "check_grounding", "check_quarantine", "check_edges",
                 "check_empty"):
        monkeypatch.setattr(rbg, name, lambda *a, **k: dict(ok))
    monkeypatch.setattr(rbg, "check_orphans_and_drift", lambda *a, **k: (dict(ok), dict(ok)))
    monkeypatch.setattr(rbg, "scope_profiles", lambda names: {})
    monkeypatch.setattr(rbg, "_events", lambda: [])
    monkeypatch.setattr(rbg, "_gate_config", lambda: {"preregistered": True})
    monkeypatch.setattr(proj, "newest_corpus_epoch", lambda: ("g1eval", ["a"]))
    monkeypatch.setattr(proj, "projected_document_ids_live", lambda: set())
    report = tmp_path / "report.md"
    monkeypatch.setattr(sys, "argv", ["run_baseline_gates.py", "--report", str(report)])
    with pytest.raises(SystemExit):
        rbg.main()
    assert not report.exists()
