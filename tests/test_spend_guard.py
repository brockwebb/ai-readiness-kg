"""Mutation tests for the preemptive shared spend guard (kg/spend.py, DD-022).

Each test corresponds 1:1 to the seeded fault list in
cc_tasks/2026-08-26_preemptive_spend_guard.md §6. The stub model (a counting fake for
``subprocess.run``) asserts it was NEVER invoked on refusal. Every test fails when the
reserve check in kg/spend.py is disabled (proven once in the task RESULT).

Hermetic: ledger, controls.yaml, and event shards are all redirected onto tmp_path via the
module path globals (repo convention).
"""
from __future__ import annotations

import json
import multiprocessing
import textwrap
from pathlib import Path

import pytest

from kg import eventlog, spend
from kg.extraction import model_stub

FLOOR = 36000          # cleanup-class floor written into the tmp controls below


def _write_controls(path: Path, daily_tokens: int = 1_000_000_000) -> None:
    path.write_text(textwrap.dedent(f"""\
        schema_version: "0.2"
        spend:
          daily_tokens: {daily_tokens}
          call_class_floors:
            cleanup: {FLOOR}
            extraction: 111000
            judge: {FLOOR}
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
