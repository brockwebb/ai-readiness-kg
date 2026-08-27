#!/usr/bin/env python3
"""Preemptive shared spend guard (task 2026-08-26_preemptive_spend_guard, DD-022).

Fixes the DD-019 §5 defect class: the 2026-08-23 batched repair enforced its 12M ceiling as
process-local state (two shard workers spent 22.03M) and the TrustGraph v2 run checked its
8M ceiling after each call returned (consumed 8.11M). Both checks were *reactive* and
*local*. This module is the replacement: *preemptive* (reserve an estimated cost before
dispatch; the call runs only if the reservation was granted) and *shared* (one append-only
ledger, cross-process atomic via an exclusive ``fcntl.flock`` held for the whole
read → compute → append of every operation).

Prior art (named in the task, not invented here): reserve-then-settle admission control —
the two-phase pattern of quota systems and connection/credit pools. Single-host advisory
file locking suffices because fleet workers run on one machine (``BURN_MAX_FLEET_WORKERS``).

Ledger: ``state/spend_ledger.jsonl``. It is the truth for spend *admission*; ``model_call``
events in the graph shards remain provenance for the calls themselves — the two are
reconciled (``python -m kg.spend reconcile``), never merged.

    committed(run) = Σ settle.actual + Σ outstanding reserve.estimate
    committed(day) = the same sum over records stamped in the UTC day

Refusal is a returned object, not an exception, at the ``SpendLedger`` API; the model-stub
choke point wraps it in ``SpendRefusalStop`` so every runner can turn it into the same clean
stop (exit 0) contract as the STOP file and cap exhaustion.

CLI:
    python -m kg.spend status [--run-id R]
    python -m kg.spend reconcile --run-id R
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import socket
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import yaml

# Module path globals, read at call time so tests can monkeypatch them onto tmp_path
# (repo convention — see kg/manifest.py, kg/eventlog.py). Do not inline into functions.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_LEDGER_PATH = _REPO_ROOT / "state" / "spend_ledger.jsonl"
_CONTROLS_PATH = _REPO_ROOT / "controls.yaml"

_LEDGER_SCHEMA = 1
_ESTIMATE_WINDOW_N = 10   # running mean over the last N *measured* settles in the run
# Env var carrying the current run id: set by the runner at declare time, inherited by
# fleet worker subprocesses, read by the model-stub choke point. No env var = no run =
# every reserve refuses `undeclared_run` — there is no unmetered path.
RUN_ENV = "AIRKG_SPEND_RUN_ID"


class SpendConfigError(RuntimeError):
    """Misdeclared run / missing config. Loud (standard 4), never a silent default."""


@dataclass(frozen=True)
class Reservation:
    run_id: str
    reservation_id: str
    estimate_tokens: int


@dataclass(frozen=True)
class Refusal:
    run_id: str | None
    estimate_tokens: int
    committed_tokens: int
    ceiling_tokens: int
    scope: str            # "run" | "daily"
    reason: str           # "over_ceiling" | "over_daily" | "undeclared_run"


class SpendRefusalStop(RuntimeError):
    """Raised by the model-stub choke point when reserve() refuses. Callers treat it as a
    clean stop (exit 0) — the same contract as the STOP file and cap exhaustion."""

    def __init__(self, refusal: Refusal):
        self.refusal = refusal
        super().__init__(
            f"spend guard refused dispatch ({refusal.reason}, scope={refusal.scope}): "
            f"committed {refusal.committed_tokens:,} + estimate {refusal.estimate_tokens:,} "
            f"vs ceiling {refusal.ceiling_tokens:,} [run {refusal.run_id}]")


def current_run_id() -> str | None:
    return os.environ.get(RUN_ENV) or None


def set_current_run(run_id: str) -> None:
    os.environ[RUN_ENV] = run_id


def default_run_id(slug: str) -> str:
    return f"{slug}-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _utc_day(ts: str) -> str:
    return ts[:10]


def _spend_config() -> dict:
    """The controls.yaml `spend:` block, read at call time, never cached (config-first)."""
    doc = yaml.safe_load(_CONTROLS_PATH.read_text(encoding="utf-8")) or {}
    spend = doc.get("spend")
    if not spend:
        raise SpendConfigError(f"no `spend:` block in {_CONTROLS_PATH}")
    for key in ("daily_tokens", "call_class_floors"):
        if key not in spend:
            raise SpendConfigError(f"controls.yaml spend block missing {key!r}")
    return spend


class SpendLedger:
    """The flock-guarded append-only spend ledger. All five operations take the exclusive
    lock for the duration of read → compute → append; no read outside the lock decides
    anything."""

    def __init__(self, path: Path | None = None):
        self._explicit_path = Path(path) if path else None

    @property
    def path(self) -> Path:
        return self._explicit_path or _LEDGER_PATH

    # ---------------------------------------------------------------- internals
    def _open_locked(self):
        p = self.path
        p.parent.mkdir(parents=True, exist_ok=True)
        fh = p.open("a+", encoding="utf-8")
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        return fh

    @staticmethod
    def _read_all(fh) -> list[dict]:
        fh.seek(0)
        out = []
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                # A corrupt admission ledger must stop admissions, not skip lines.
                raise SpendConfigError(f"corrupt spend ledger line {lineno}: {exc}") from exc
        return out

    @staticmethod
    def _append(fh, record: dict) -> None:
        record = {**record, "ts": _now(), "pid": os.getpid(), "host": socket.gethostname()}
        fh.seek(0, os.SEEK_END)
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    @staticmethod
    def _tally(records: list[dict], run_id: str | None = None,
               day: str | None = None) -> tuple[int, int, int]:
        """(committed, settled_total, outstanding_estimates) filtered by run and/or UTC day.
        committed = Σ settle.actual + Σ outstanding reserve.estimate."""
        reserves: dict[str, dict] = {}
        settled_total = 0
        for r in records:
            if run_id is not None and r.get("run_id") != run_id:
                continue
            kind = r.get("record")
            if kind == "reserve":
                if day is None or _utc_day(r["ts"]) == day:
                    reserves[r["reservation_id"]] = r
            elif kind == "settle":
                reserves.pop(r["reservation_id"], None)
                if day is None or _utc_day(r["ts"]) == day:
                    settled_total += int(r["actual_tokens"])
            elif kind == "release":
                reserves.pop(r["reservation_id"], None)
        outstanding = sum(int(r["estimate_tokens"]) for r in reserves.values())
        return settled_total + outstanding, settled_total, outstanding

    @staticmethod
    def _declare_of(records: list[dict], run_id: str) -> dict | None:
        for r in records:
            if r.get("record") == "declare" and r.get("run_id") == run_id:
                return r
        return None

    def _estimate(self, records: list[dict], run_id: str, call_class: str) -> int:
        """max(call-class floor, mean of the last N measured settles in this run).
        Settles flagged settled_as_estimate are estimates, not measurements — excluded."""
        floors = _spend_config()["call_class_floors"]
        if call_class not in floors:
            raise SpendConfigError(
                f"call_class {call_class!r} has no floor in controls.yaml spend.call_class_floors")
        floor = int(floors[call_class])
        actuals = [int(r["actual_tokens"]) for r in records
                   if r.get("record") == "settle" and r.get("run_id") == run_id
                   and not r.get("settled_as_estimate")]
        window = actuals[-_ESTIMATE_WINDOW_N:]
        mean = int(sum(window) / len(window)) if window else 0
        return max(floor, mean)

    # ---------------------------------------------------------------- operations
    def declare(self, run_id: str, ceiling_tokens: int, declared_by: str,
                call_class: str) -> None:
        """Idempotent for an identical re-declare (fleet workers re-declaring the shared
        run); a conflicting re-declare is a config fault and raises."""
        with self._open_locked() as fh:
            records = self._read_all(fh)
            prior = self._declare_of(records, run_id)
            if prior is not None:
                if (int(prior["ceiling_tokens"]) == int(ceiling_tokens)
                        and prior["call_class"] == call_class):
                    return
                raise SpendConfigError(
                    f"run {run_id!r} already declared with ceiling "
                    f"{prior['ceiling_tokens']:,}/{prior['call_class']}; refusing "
                    f"conflicting re-declare {ceiling_tokens:,}/{call_class}")
            self._append(fh, {"record": "declare", "run_id": run_id,
                              "ceiling_tokens": int(ceiling_tokens),
                              "declared_by": declared_by, "call_class": call_class})

    def reserve(self, run_id: str | None, estimate_tokens: int | None = None):
        """Reservation | Refusal. Refuse iff committed(run)+estimate > ceiling(run) or
        committed(day)+estimate > daily_tokens. A refusal is recorded on the ledger."""
        with self._open_locked() as fh:
            records = self._read_all(fh)
            declared = self._declare_of(records, run_id) if run_id else None
            if declared is None:
                refusal = Refusal(run_id=run_id, estimate_tokens=int(estimate_tokens or 0),
                                  committed_tokens=0, ceiling_tokens=0,
                                  scope="run", reason="undeclared_run")
                self._append(fh, {"record": "refuse", "run_id": run_id,
                                  "estimate_tokens": refusal.estimate_tokens,
                                  "committed_tokens": 0, "ceiling_tokens": 0,
                                  "scope": "run", "reason": "undeclared_run"})
                return refusal
            estimate = (int(estimate_tokens) if estimate_tokens is not None
                        else self._estimate(records, run_id, declared["call_class"]))
            ceiling = int(declared["ceiling_tokens"])
            committed_run, _, _ = self._tally(records, run_id=run_id)
            daily_cap = int(_spend_config()["daily_tokens"])
            committed_day, _, _ = self._tally(records, day=_utc_day(_now()))
            scope = None
            if committed_run + estimate > ceiling:
                scope, cap, committed = "run", ceiling, committed_run
            elif committed_day + estimate > daily_cap:
                scope, cap, committed = "daily", daily_cap, committed_day
            if scope:
                self._append(fh, {"record": "refuse", "run_id": run_id,
                                  "estimate_tokens": estimate, "committed_tokens": committed,
                                  "ceiling_tokens": cap, "scope": scope,
                                  "reason": "over_ceiling" if scope == "run" else "over_daily"})
                return Refusal(run_id=run_id, estimate_tokens=estimate,
                               committed_tokens=committed, ceiling_tokens=cap, scope=scope,
                               reason="over_ceiling" if scope == "run" else "over_daily")
            reservation = Reservation(run_id=run_id, reservation_id=uuid.uuid4().hex,
                                      estimate_tokens=estimate)
            self._append(fh, {"record": "reserve", "run_id": run_id,
                              "reservation_id": reservation.reservation_id,
                              "estimate_tokens": estimate})
            return reservation

    def settle(self, reservation: Reservation, actual_tokens: int,
               model_call_event_id: str | None = None, **flags) -> None:
        """Replace the reservation's estimate with the actual cost. `model_call_event_id`
        is nullable at the choke point (the event does not exist yet when the stub settles);
        runners that write model_call events stamp reservation_id/run_id ON the event, and
        reconcile joins by run (task §4)."""
        with self._open_locked() as fh:
            rec = {"record": "settle", "run_id": reservation.run_id,
                   "reservation_id": reservation.reservation_id,
                   "actual_tokens": int(actual_tokens),
                   "model_call_event_id": model_call_event_id}
            for key in ("settled_as_estimate", "usage_fields_missing"):
                if flags.get(key):
                    rec[key] = True
            self._append(fh, rec)

    def release(self, reservation: Reservation, reason: str) -> None:
        """For a reserved call that never dispatched (exception before the CLI ran)."""
        with self._open_locked() as fh:
            self._append(fh, {"record": "release", "run_id": reservation.run_id,
                              "reservation_id": reservation.reservation_id,
                              "reason": reason})

    # ---------------------------------------------------------------- readouts
    def committed(self, run_id: str) -> int:
        with self._open_locked() as fh:
            return self._tally(self._read_all(fh), run_id=run_id)[0]

    def committed_today(self) -> int:
        with self._open_locked() as fh:
            return self._tally(self._read_all(fh), day=_utc_day(_now()))[0]

    def status(self, run_id: str | None = None) -> dict:
        with self._open_locked() as fh:
            records = self._read_all(fh)
        today = _utc_day(_now())
        out = {"ledger": str(self.path),
               "daily_tokens": int(_spend_config()["daily_tokens"]),
               "committed_today": self._tally(records, day=today)[0]}
        run_ids = ([run_id] if run_id else
                   sorted({r["run_id"] for r in records
                           if r.get("record") == "declare"}))
        runs = {}
        for rid in run_ids:
            declared = self._declare_of(records, rid)
            committed, settled, outstanding = self._tally(records, run_id=rid)
            refusals = sum(1 for r in records
                           if r.get("record") == "refuse" and r.get("run_id") == rid)
            runs[rid] = {
                "ceiling_tokens": declared and int(declared["ceiling_tokens"]),
                "call_class": declared and declared["call_class"],
                "committed": committed, "settled": settled, "outstanding": outstanding,
                "remaining": (max(0, int(declared["ceiling_tokens"]) - committed)
                              if declared else None),
                "refusals": refusals,
            }
        out["runs"] = runs
        return out

    def reconcile(self, run_id: str, model_call_tokens: int | None = None) -> dict:
        """Σ settle.actual for the run vs Σ token counts on model_call events tagged with
        the run across the graph shards. Mismatch → a `reconcile_mismatch` record and
        ok=False (CLI exits non-zero). A run with NO tagged model_call events gets a
        `reconcile_note` and passes — the repair-class scripts persist raw usage JSONs but
        write no model_call events (reported in the task RESULT), so there is nothing to
        compare against."""
        if model_call_tokens is None:
            from kg import eventlog   # local import: kg.spend must not need eventlog to admit
            model_call_tokens, tagged = 0, 0
            for ev in eventlog.replay():
                if ev.get("event_type") == "model_call" and ev.get("run_id") == run_id:
                    tagged += 1
                    u = ev.get("usage") or {}
                    model_call_tokens += sum(int(u.get(k, 0) or 0) for k in
                                             ("inputTokens", "outputTokens",
                                              "cacheCreationInputTokens",
                                              "cacheReadInputTokens"))
        else:
            tagged = None   # caller-supplied total (tests)
        with self._open_locked() as fh:
            records = self._read_all(fh)
            settled = sum(int(r["actual_tokens"]) for r in records
                          if r.get("record") == "settle" and r.get("run_id") == run_id)
            if tagged == 0:
                self._append(fh, {"record": "reconcile_note", "run_id": run_id,
                                  "note": "no model_call events tagged with this run",
                                  "settled_total": settled})
                return {"ok": True, "run_id": run_id, "settled_total": settled,
                        "model_call_total": 0, "note": "no_tagged_model_call_events"}
            ok = settled == model_call_tokens
            if not ok:
                self._append(fh, {"record": "reconcile_mismatch", "run_id": run_id,
                                  "settled_total": settled,
                                  "model_call_total": int(model_call_tokens)})
            return {"ok": ok, "run_id": run_id, "settled_total": settled,
                    "model_call_total": int(model_call_tokens)}

    def open_ledger(self) -> None:
        """Write the ledger_open header record if the ledger is empty (idempotent)."""
        with self._open_locked() as fh:
            if not self._read_all(fh):
                self._append(fh, {"record": "ledger_open", "ledger_schema": _LEDGER_SCHEMA})


def default_ledger() -> SpendLedger:
    return SpendLedger()


# ------------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m kg.spend",
                                 description="Shared preemptive spend guard (DD-022).")
    sub = ap.add_subparsers(dest="command", required=True)
    p_status = sub.add_parser("status", help="Ceilings, committed, outstanding, refusals.")
    p_status.add_argument("--run-id", default=None)
    p_rec = sub.add_parser("reconcile",
                           help="Ledger settles vs model_call events for one run.")
    p_rec.add_argument("--run-id", required=True)
    args = ap.parse_args(argv)
    ledger = default_ledger()
    if args.command == "status":
        print(json.dumps(ledger.status(args.run_id), indent=1))
        return 0
    if args.command == "reconcile":
        report = ledger.reconcile(args.run_id)
        print(json.dumps(report, indent=1))
        return 0 if report["ok"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
