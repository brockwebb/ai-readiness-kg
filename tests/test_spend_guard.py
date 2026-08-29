"""Mutation tests for the preemptive shared spend guard (kg/spend.py, DD-022).

Each test corresponds 1:1 to the seeded fault list in
cc_tasks/2026-08-26_preemptive_spend_guard.md §6. The stub model (a counting fake for
``subprocess.run``) asserts it was NEVER invoked on refusal. Every test fails when the
reserve check in kg/spend.py is disabled (proven once in the task RESULT).

Hermetic: ledger, controls.yaml, and event shards are all redirected onto tmp_path via the
module path globals (repo convention).
"""
from __future__ import annotations

import datetime
import json
import multiprocessing
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from kg import eventlog, spend
from kg.extraction import model_stub

FLOOR = 36000          # cleanup-class floor written into the tmp controls below


def _write_controls(path: Path, daily_tokens: int = 1_000_000_000,
                    orphan_age: int = 600) -> None:
    path.write_text(textwrap.dedent(f"""\
        schema_version: "0.2"
        spend:
          daily_tokens: {daily_tokens}
          call_class_floors:
            cleanup: {FLOOR}
            extraction: 111000
            judge: {FLOOR}
          orphan_reservation_age_seconds: {orphan_age}
        """), encoding="utf-8")


@pytest.fixture
def guard(tmp_path, monkeypatch):
    """(ledger, tmp_path): kg.spend redirected onto tmp_path; no current run in env."""
    controls = tmp_path / "controls.yaml"
    _write_controls(controls)
    monkeypatch.setattr(spend, "_LEDGER_PATH", tmp_path / "spend_ledger.jsonl")
    monkeypatch.setattr(spend, "_CONTROLS_PATH", controls)
    monkeypatch.delenv(spend.RUN_ENV, raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    return spend.SpendLedger(), tmp_path


class CountingStub:
    """Fake subprocess.run standing in for the model CLI: counts invocations and returns a
    valid envelope. On refusal the guard must keep this at zero."""

    def __init__(self):
        self.calls = 0

    def __call__(self, cmd, **kw):
        self.calls += 1

        class R:
            returncode = 0
            stdout = json.dumps({"result": '{"ok": 1}',
                                 "modelUsage": {"m": {"inputTokens": 10, "outputTokens": 5}}})
            stderr = ""
        return R()


def _records(ledger) -> list[dict]:
    return [json.loads(l) for l in ledger.path.read_text().splitlines() if l.strip()]


# 1 ------------------------------------------------------------------------------------
def test_seeded_near_ceiling_refuses_before_dispatch(guard, monkeypatch):
    ledger, _ = guard
    ceiling = 500_000
    ledger.declare("r1", ceiling, declared_by="test", call_class="cleanup")
    # seed committed = ceiling - (floor - 1): one more floor-sized call would cross
    seed = ledger.reserve("r1", estimate_tokens=ceiling - (FLOOR - 1))
    ledger.settle(seed, ceiling - (FLOOR - 1), settled_as_estimate=True)

    stub = CountingStub()
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    monkeypatch.setenv(spend.RUN_ENV, "r1")
    with pytest.raises(spend.SpendRefusalStop) as exc:
        model_stub.invoke("d", "", prompt="p", config={"model_id": "m", "cli": "claude"})
    assert stub.calls == 0, "stub model must never be invoked on refusal"
    assert exc.value.refusal.scope == "run"
    refuses = [r for r in _records(ledger) if r["record"] == "refuse"]
    assert refuses and refuses[-1]["scope"] == "run"


# 2 ------------------------------------------------------------------------------------
def _worker2(ledger_path: str, controls_path: str, granted_q) -> None:
    from kg import spend as sp
    sp._LEDGER_PATH = Path(ledger_path)          # child process: same on-disk ledger
    sp._CONTROLS_PATH = Path(controls_path)
    ledger = sp.SpendLedger()
    granted = 0
    for _ in range(50):
        if isinstance(ledger.reserve("shared"), sp.Reservation):
            granted += 1
    granted_q.put(granted)


def test_concurrent_workers_cannot_oversubscribe(guard):
    ledger, tmp = guard
    ceiling = 100 * FLOOR                        # admits exactly 100 floor-sized calls
    ledger.declare("shared", ceiling, declared_by="test", call_class="cleanup")
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    procs = [ctx.Process(target=_worker2,
                         args=(str(ledger.path), str(spend._CONTROLS_PATH), q))
             for _ in range(8)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=180)
        assert p.exitcode == 0
    granted = sum(q.get() for _ in range(8))
    assert granted == 100, f"expected exactly 100 granted reservations, got {granted}"
    records = _records(ledger)                   # every line parses = no interleaved lines
    reserves = [r for r in records if r["record"] == "reserve"]
    assert len(reserves) == 100
    assert sum(r["estimate_tokens"] for r in reserves) <= ceiling
    assert ledger.committed("shared") <= ceiling


# 3 ------------------------------------------------------------------------------------
def test_overshoot_on_settle_closes_the_door(guard):
    ledger, _ = guard
    ledger.declare("r3", 2 * FLOOR + FLOOR // 2, declared_by="test", call_class="cleanup")
    res = ledger.reserve("r3")                   # estimate = floor
    assert isinstance(res, spend.Reservation)
    ledger.settle(res, 3 * res.estimate_tokens)  # actual 3E pushes committed past ceiling
    nxt = ledger.reserve("r3")
    assert isinstance(nxt, spend.Refusal) and nxt.scope == "run"


# 4 ------------------------------------------------------------------------------------
def test_daily_cap_is_independent_of_run_ceiling(guard, monkeypatch):
    ledger, tmp = guard
    _write_controls(spend._CONTROLS_PATH, daily_tokens=4 * FLOOR)
    ledger.declare("day-a", 100 * FLOOR, declared_by="test", call_class="cleanup")
    ledger.declare("day-b", 100 * FLOOR, declared_by="test", call_class="cleanup")
    for _ in range(4):                           # run A settles 4 floors, all under ITS ceiling
        r = ledger.reserve("day-a")
        assert isinstance(r, spend.Reservation)
        ledger.settle(r, FLOOR, settled_as_estimate=True)
    refusal = ledger.reserve("day-b")            # run B is far under its own ceiling
    assert isinstance(refusal, spend.Refusal)
    assert refusal.scope == "daily" and refusal.reason == "over_daily"


# 5 ------------------------------------------------------------------------------------
def test_undeclared_run_refuses(guard, monkeypatch):
    ledger, _ = guard
    refusal = ledger.reserve("never-declared")
    assert isinstance(refusal, spend.Refusal) and refusal.reason == "undeclared_run"

    stub = CountingStub()
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    # no RUN_ENV set at all — the choke point must refuse, not dispatch unmetered
    with pytest.raises(spend.SpendRefusalStop) as exc:
        model_stub.invoke("d", "", prompt="p", config={"model_id": "m", "cli": "claude"})
    assert stub.calls == 0
    assert exc.value.refusal.reason == "undeclared_run"


# 6 ------------------------------------------------------------------------------------
def test_release_restores_capacity(guard):
    ledger, _ = guard
    ledger.declare("r6", 2 * FLOOR, declared_by="test", call_class="cleanup")
    r1 = ledger.reserve("r6")
    r2 = ledger.reserve("r6")
    assert isinstance(r1, spend.Reservation) and isinstance(r2, spend.Reservation)
    assert isinstance(ledger.reserve("r6"), spend.Refusal)   # at the ceiling
    ledger.release(r2, reason="never dispatched (test)")
    again = ledger.reserve("r6")
    assert isinstance(again, spend.Reservation)


# 7 ------------------------------------------------------------------------------------
def test_reconcile_detects_planted_mismatch(guard, tmp_path, monkeypatch):
    ledger, _ = guard
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)

    ledger.declare("r7", 10 * FLOOR, declared_by="test", call_class="cleanup")
    res = ledger.reserve("r7")
    ledger.settle(res, 1000)
    eventlog.append({"event_type": "model_call", "doc_id": "d", "run_id": "r7",
                     "usage": {"inputTokens": 900}}, batch=1)   # planted: 900 != 1000

    report = ledger.reconcile("r7")
    assert report["ok"] is False
    assert any(r["record"] == "reconcile_mismatch" for r in _records(ledger))
    assert spend.main(["reconcile", "--run-id", "r7"]) != 0     # CLI exits non-zero


# 8 ------------------------------------------------------------------------------------
def _worker8(ledger_path: str, controls_path: str) -> None:
    from kg import spend as sp
    sp._LEDGER_PATH = Path(ledger_path)
    sp._CONTROLS_PATH = Path(controls_path)
    ledger = sp.SpendLedger()
    # replay of the 22M incident shape: this worker declares the run itself (idempotent),
    # then dispatches floor-sized calls in a loop until refused
    ledger.declare("incident-22m", 12_000_000, declared_by="worker", call_class="cleanup")
    # Bounded, not `while True`: with the guard healthy the refusal ends the loop at ~334
    # grants total across both workers; with the guard disabled (mutation proof) the bound
    # makes the ceiling-breach assertion fail fast instead of looping forever.
    for _ in range(600):
        res = ledger.reserve("incident-22m")
        if not isinstance(res, sp.Reservation):
            return
        ledger.settle(res, res.estimate_tokens)


def test_regression_replay_of_the_22m_incident_shape(guard):
    ledger, _ = guard
    ctx = multiprocessing.get_context("spawn")
    procs = [ctx.Process(target=_worker8, args=(str(ledger.path), str(spend._CONTROLS_PATH)))
             for _ in range(2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=600)
        assert p.exitcode == 0
    settled = sum(r["actual_tokens"] for r in _records(ledger) if r["record"] == "settle")
    # the at-most-one-in-flight overshoot bound — NOT 22M
    assert settled <= 12_000_000 + FLOOR, f"shared ceiling breached: {settled:,}"
    assert settled >= 12_000_000 - FLOOR   # and the ceiling was actually used, not undershot


# 9 (ADDENDUM-05) --------------------------------------------------------------------
def test_operator_redeclare_raises_ceiling_and_keeps_refusal_history(guard):
    ledger, _ = guard
    ledger.declare("r9", 2 * FLOOR, declared_by="test", call_class="cleanup")
    r1 = ledger.reserve("r9"); ledger.settle(r1, FLOOR)
    r2 = ledger.reserve("r9"); ledger.settle(r2, FLOOR)
    assert isinstance(ledger.reserve("r9"), spend.Refusal)       # old ceiling binds
    with pytest.raises(spend.SpendConfigError):                  # silent conflict still refused
        ledger.declare("r9", 10 * FLOOR, declared_by="test", call_class="cleanup")
    ledger.declare("r9", 10 * FLOOR, declared_by="ADDENDUM-05 test", call_class="cleanup",
                   supersede=True)
    nxt = ledger.reserve("r9")                                   # new ceiling operative
    assert isinstance(nxt, spend.Reservation)
    records = _records(ledger)
    assert sum(1 for r in records if r["record"] == "refuse") == 1   # history retained
    declares = [r for r in records if r["record"] == "declare" and r["run_id"] == "r9"]
    assert declares[-1]["supersedes_prior_ceiling"] == 2 * FLOOR


# 10-15 (ADDENDUM-02) — orphaned-reservation release path ------------------------------
# Positive-control discipline: no monitor is trusted until a seeded known-bad fires it.
# Test 13 is that control, run in-suite rather than as a one-off manual mutation, so it
# cannot rot: with the PID-liveness test stubbed dead, the live-owner reservation that
# test 12 spares IS reaped. That is the proof the liveness condition — not the age
# condition — is what protects a running call.

def _dead_pid() -> int:
    """A PID that is genuinely dead: spawn, wait (so it is reaped), return its number."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def _seed_reservation(ledger, monkeypatch, run_id, *, age_seconds, pid, host=None):
    """Reserve through the REAL reserve() path, but stamped with a chosen age/pid/host."""
    ts = (datetime.datetime.now(datetime.timezone.utc)
          - datetime.timedelta(seconds=age_seconds)).isoformat()
    with monkeypatch.context() as m:
        m.setattr(spend, "_now", lambda: ts)
        m.setattr(spend, "_pid", lambda: pid)
        if host is not None:
            m.setattr(spend.socket, "gethostname", lambda: host)
        res = ledger.reserve(run_id)
    assert isinstance(res, spend.Reservation)
    return res


# 10 -----------------------------------------------------------------------------------
def test_seeded_orphan_is_listed_then_released_and_capacity_returns(guard, monkeypatch):
    ledger, _ = guard
    ledger.declare("orph", 2 * FLOOR, declared_by="test", call_class="cleanup")
    dead = _dead_pid()
    orphan = _seed_reservation(ledger, monkeypatch, "orph", age_seconds=3600, pid=dead)
    live = ledger.reserve("orph")                       # this process owns it, fresh
    assert isinstance(live, spend.Reservation)
    assert isinstance(ledger.reserve("orph"), spend.Refusal)      # ceiling is full

    dry = ledger.release_orphans()
    assert [o["reservation_id"] for o in dry["orphans"]] == [orphan.reservation_id]
    assert dry["tokens_returned"] == FLOOR and dry["committed"] is False
    assert not [r for r in _records(ledger) if r["record"] == "release"], "dry run wrote"

    done = ledger.release_orphans(commit=True)
    assert [o["reservation_id"] for o in done["orphans"]] == [orphan.reservation_id]
    rel = [r for r in _records(ledger) if r["record"] == "release"]
    assert len(rel) == 1
    assert rel[0]["reason"] == "orphan_pid_dead"
    assert rel[0]["estimate_tokens_returned"] == FLOOR
    assert rel[0]["orphan_evidence"]["owner_pid"] == dead
    assert rel[0]["orphan_evidence"]["liveness"] == "dead"

    assert isinstance(ledger.reserve("orph"), spend.Reservation), "capacity did not return"
    assert ledger.release_orphans()["orphans"] == [], "released reservation reaped twice"


# 11 -----------------------------------------------------------------------------------
def test_live_fresh_reservation_is_never_listed(guard):
    ledger, _ = guard
    ledger.declare("live", 10 * FLOOR, declared_by="test", call_class="cleanup")
    res = ledger.reserve("live")
    report = ledger.release_orphans()
    assert report["orphans"] == []
    assert [r["reservation_id"] for r in report["retained"]] == [res.reservation_id]
    assert report["retained"][0]["liveness"] == "alive"
    assert ledger.release_orphans(commit=True)["orphans"] == []
    assert not [r for r in _records(ledger) if r["record"] == "release"]


# 12 -----------------------------------------------------------------------------------
def test_aged_reservation_with_live_pid_is_never_released(guard, monkeypatch):
    ledger, _ = guard
    ledger.declare("aged", 10 * FLOOR, declared_by="test", call_class="cleanup")
    res = _seed_reservation(ledger, monkeypatch, "aged",
                            age_seconds=86_400, pid=os.getpid())
    report = ledger.release_orphans(commit=True)
    assert report["orphans"] == [], "age alone reaped a live owner"
    assert report["retained"][0]["retained_because"] == "owner alive"
    assert report["retained"][0]["age_seconds"] >= 86_400
    assert ledger.committed("aged") == FLOOR      # still held
    assert res.reservation_id in {r["reservation_id"] for r in report["retained"]}


# 13 — POSITIVE CONTROL ----------------------------------------------------------------
def test_mutation_disabling_pid_liveness_reaps_the_live_reservation(guard, monkeypatch):
    """Seeded known-bad: with _pid_alive stubbed to always report death — the mutation of
    ADDENDUM-02 §5.4 — the aged, LIVE-owner reservation that test 12 spares is reaped.
    If this test ever stops failing to spare it, the liveness condition has gone dead."""
    ledger, _ = guard
    ledger.declare("aged", 10 * FLOOR, declared_by="test", call_class="cleanup")
    _seed_reservation(ledger, monkeypatch, "aged", age_seconds=86_400, pid=os.getpid())
    monkeypatch.setattr(spend, "_pid_alive", lambda pid: False)
    report = ledger.release_orphans()
    assert len(report["orphans"]) == 1, (
        "mutation did not change the outcome: the PID-liveness test is not load-bearing")


# 14 -----------------------------------------------------------------------------------
def test_reservation_from_another_host_is_never_reaped(guard, monkeypatch):
    """A PID absent HERE says nothing about a process on another machine. The host guard
    is the only thing standing between a multi-host ledger and a released live call."""
    ledger, _ = guard
    ledger.declare("remote", 10 * FLOOR, declared_by="test", call_class="cleanup")
    _seed_reservation(ledger, monkeypatch, "remote", age_seconds=86_400,
                      pid=_dead_pid(), host="some-other-box.local")
    report = ledger.release_orphans(commit=True)
    assert report["orphans"] == []
    assert report["retained"][0]["liveness"] == "unknown_other_host"
    assert not [r for r in _records(ledger) if r["record"] == "release"]


# 15 -----------------------------------------------------------------------------------
def test_missing_age_threshold_is_a_loud_config_error(guard, monkeypatch):
    ledger, _ = guard
    spend._CONTROLS_PATH.write_text(textwrap.dedent(f"""\
        spend:
          daily_tokens: 1000000000
          call_class_floors:
            cleanup: {FLOOR}
        """), encoding="utf-8")
    with pytest.raises(spend.SpendConfigError) as exc:
        ledger.release_orphans()
    assert "orphan_reservation_age_seconds" in str(exc.value)


# 16 -----------------------------------------------------------------------------------
def test_status_reports_released_and_preserves_committed_invariant(guard, monkeypatch):
    ledger, _ = guard
    ledger.declare("st", 10 * FLOOR, declared_by="test", call_class="cleanup")
    _seed_reservation(ledger, monkeypatch, "st", age_seconds=3600, pid=_dead_pid())
    kept = ledger.reserve("st")
    ledger.settle(kept, 1234)
    ledger.release_orphans(commit=True)
    row = ledger.status("st")["runs"]["st"]
    assert row["released"] == FLOOR
    assert row["outstanding"] == 0
    assert row["committed"] == row["settled"] + row["outstanding"] == 1234
    assert spend.main(["release-orphans", "--run-id", "st"]) == 0


# 17 -----------------------------------------------------------------------------------
def test_dead_pid_inside_the_age_window_is_not_yet_reaped(guard, monkeypatch):
    """The age condition is load-bearing on its own, not decoration on the liveness test:
    a dead owner is NOT sufficient inside the window. Guards the probe against the
    reserve-then-dispatch startup gap and against clock skew on the recorded ts — the
    reaper waits out the window before it touches a hold. (This test is the one that
    fires when the `age > max_age_seconds` conjunct is dropped.)"""
    ledger, _ = guard
    ledger.declare("fresh-dead", 10 * FLOOR, declared_by="test", call_class="cleanup")
    _seed_reservation(ledger, monkeypatch, "fresh-dead", age_seconds=60, pid=_dead_pid())
    report = ledger.release_orphans(commit=True)          # threshold is 600s
    assert report["orphans"] == [], "reaped a hold inside the age window"
    assert report["retained"][0]["liveness"] == "dead"
    assert report["retained"][0]["retained_because"] == "not old enough"
    assert not [r for r in _records(ledger) if r["record"] == "release"]
    assert ledger.committed("fresh-dead") == FLOOR

    # ...and once the window passes, the same hold IS reaped (the window expires, the
    # condition is a delay, not a permanent exemption).
    assert ledger.release_orphans(commit=True, max_age_seconds=30)["tokens_returned"] == FLOOR
