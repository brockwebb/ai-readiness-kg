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
    python -m kg.spend release-orphans [--run-id R] [--commit]
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


def _pid() -> int:
    """Seam beside ``_now`` so a test can stamp a reservation with a foreign owner PID
    (repo convention: the things a test must control are module-level and read at call
    time). Production has exactly one implementation."""
    return os.getpid()


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


# ------------------------------------------------------------------ orphan reservations
# A reservation whose owning process died between reserve() and settle()/release() holds
# capacity forever: `_tally` counts it as outstanding against both the run ceiling and the
# daily band. Four such holds (1,326,274 tokens) were found by ADDENDUM-01 §0.
#
# Prior art (named, not invented here): this is *lease expiry* — Gray & Cheriton 1989,
# "Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency" —
# and the in-doubt-transaction resolution of presumed-abort two-phase commit (Mohan,
# Lindsay & Obermarck 1986). The liveness probe itself is the Unix stale-pidfile idiom
# (`kill(pid, 0)`). Internal precedent search (repo + Wintermute decision logs, 2026-08-28):
# no prior reaper here; every existing `orphan` in this repo is the graph-structural
# `orphan_rate` gate, an unrelated sense of the word.
#
# The literature prefers a *renewed lease* to a *post-hoc liveness probe*, because a probe
# races with PID recycling. We use the probe because the reservations already on disk carry
# no lease field, and because the race is safe in one direction only (below). A renewable
# lease is the right shape if this ever needs to reap while a run is live.


def _pid_alive(pid: int) -> bool:
    """Signal-0 liveness. PermissionError means the process EXISTS under another uid —
    alive. Only ProcessLookupError is proof of death."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _liveness_of(record: dict, host: str) -> tuple[str, str]:
    """(liveness, evidence) for a reservation record.

    PID recycling can only make a dead owner look *alive* (some unrelated process now holds
    the number), which under-releases — the safe direction. The unsafe direction, calling a
    live owner dead, is impossible on the host that owns the PID, so the host guard is
    load-bearing, not decoration: a PID absent *here* says nothing about a process on
    another machine, and such a reservation is never reaped."""
    rec_host = record.get("host")
    if rec_host is not None and rec_host != host:
        return "unknown_other_host", f"reserved on {rec_host!r}, probing from {host!r}"
    pid = record.get("pid")
    if pid is None:
        return "pid_absent", "no pid recorded on the reservation"
    alive = _pid_alive(int(pid))
    return ("alive" if alive else "dead",
            f"os.kill({int(pid)}, 0) -> {'no error' if alive else 'ProcessLookupError'}")


def _outstanding_reservations(records: list[dict],
                              run_id: str | None = None) -> list[dict]:
    """Reservation records with no matching settle or release, in ledger order."""
    reserves: dict[str, dict] = {}
    for r in records:
        kind = r.get("record")
        if kind == "reserve":
            reserves[r["reservation_id"]] = r
        elif kind in ("settle", "release"):
            reserves.pop(r.get("reservation_id"), None)
    return [r for r in reserves.values()
            if run_id is None or r.get("run_id") == run_id]


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
        record = {**record, "ts": _now(), "pid": _pid(), "host": socket.gethostname()}
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
        """The run's OPERATIVE declare: the last one appended. A ceiling re-declare
        (ADDENDUM-05 pattern) appends a superseding declare rather than editing history —
        the refusal events under the old ceiling stay on the ledger as correct guard
        events, and the audit trail shows both numbers."""
        found = None
        for r in records:
            if r.get("record") == "declare" and r.get("run_id") == run_id:
                found = r
        return found

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
                call_class: str, supersede: bool = False) -> None:
        """Idempotent for an identical re-declare (fleet workers re-declaring the shared
        run); a conflicting re-declare is a config fault and raises — unless
        ``supersede=True``, which appends a superseding declare (last one wins). Supersede
        is for an OPERATOR-authorized ceiling correction (name the authority in
        ``declared_by``); code paths must never pass it to get past a refusal."""
        with self._open_locked() as fh:
            records = self._read_all(fh)
            prior = self._declare_of(records, run_id)
            if prior is not None:
                if (int(prior["ceiling_tokens"]) == int(ceiling_tokens)
                        and prior["call_class"] == call_class):
                    return
                if not supersede:
                    raise SpendConfigError(
                        f"run {run_id!r} already declared with ceiling "
                        f"{prior['ceiling_tokens']:,}/{prior['call_class']}; refusing "
                        f"conflicting re-declare {ceiling_tokens:,}/{call_class}")
            self._append(fh, {"record": "declare", "run_id": run_id,
                              "ceiling_tokens": int(ceiling_tokens),
                              "declared_by": declared_by, "call_class": call_class,
                              **({"supersedes_prior_ceiling": int(prior["ceiling_tokens"])}
                                 if (prior is not None and supersede) else {})})

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

    def release_orphans(self, commit: bool = False, run_id: str | None = None,
                        max_age_seconds: int | None = None) -> dict:
        """Find — and with ``commit=True`` release — reservations whose owning process died.

        Orphan requires ALL THREE (task ADDENDUM-02 §1): outstanding (no settle, no
        release), older than the configured age, and owning PID provably not alive on this
        host. Age alone never qualifies: a long-running call is not an orphan, and the
        chunked pilot measured a 334 s median call duration, so a short age would reap live
        work. The whole read -> probe -> append runs under the exclusive lock, so a reserve()
        racing the reaper either lands before the read (and is probed, and is alive) or
        after the append (and is untouched).

        Dry run by default; ``commit`` is what writes."""
        spend_cfg = _spend_config()
        if max_age_seconds is None:
            if "orphan_reservation_age_seconds" not in spend_cfg:
                raise SpendConfigError(
                    f"controls.yaml spend block missing 'orphan_reservation_age_seconds'; "
                    f"refusing to reap reservations against an implicit threshold")
            max_age_seconds = int(spend_cfg["orphan_reservation_age_seconds"])
        host = socket.gethostname()
        with self._open_locked() as fh:
            records = self._read_all(fh)
            now = datetime.datetime.fromisoformat(_now())
            orphans, retained = [], []
            for r in _outstanding_reservations(records, run_id=run_id):
                liveness, evidence = _liveness_of(r, host)
                age = (now - datetime.datetime.fromisoformat(r["ts"])).total_seconds()
                row = {"run_id": r.get("run_id"),
                       "reservation_id": r["reservation_id"],
                       "estimate_tokens": int(r["estimate_tokens"]),
                       "reserved_at": r["ts"], "age_seconds": int(age),
                       "pid": r.get("pid"), "host": r.get("host"),
                       "liveness": liveness, "liveness_evidence": evidence}
                if age > max_age_seconds and liveness in ("dead", "pid_absent"):
                    orphans.append(row)
                else:
                    row["retained_because"] = ("owner alive" if liveness == "alive" else
                                               "not old enough" if liveness in ("dead", "pid_absent")
                                               else "liveness not checkable from this host")
                    retained.append(row)
            if commit:
                for row in orphans:
                    self._append(fh, {"record": "release", "run_id": row["run_id"],
                                      "reservation_id": row["reservation_id"],
                                      "reason": "orphan_pid_dead",
                                      "released_by": "kg.spend release-orphans",
                                      "estimate_tokens_returned": row["estimate_tokens"],
                                      "orphan_evidence": {
                                          "reserved_at": row["reserved_at"],
                                          "age_seconds": row["age_seconds"],
                                          "max_age_seconds": int(max_age_seconds),
                                          "owner_pid": row["pid"],
                                          "owner_host": row["host"],
                                          "probe_host": host,
                                          "liveness": row["liveness"],
                                          "evidence": row["liveness_evidence"]}})
        return {"committed": bool(commit), "max_age_seconds": int(max_age_seconds),
                "probe_host": host,
                "orphans": orphans, "retained": retained,
                "tokens_returned": sum(o["estimate_tokens"] for o in orphans)}

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
            # Released reservations leave the tally entirely, so the invariant stays
            # `committed = settled + outstanding`; `released` is reported for audit — how
            # much capacity a reap handed back, not a term in the capacity arithmetic.
            released = sum(int(r.get("estimate_tokens_returned", 0) or 0) for r in records
                           if r.get("record") == "release" and r.get("run_id") == rid)
            runs[rid] = {
                "ceiling_tokens": declared and int(declared["ceiling_tokens"]),
                "call_class": declared and declared["call_class"],
                "committed": committed, "settled": settled, "outstanding": outstanding,
                "released": released,
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
def _print_orphan_report(report: dict) -> None:
    head = f"{'run_id':<24} {'reservation_id':<34} {'age':>10} {'amount':>12} {'pid':>8}  liveness"
    verb = "RELEASED" if report["committed"] else "would release (dry run)"
    print(f"orphan threshold: age > {report['max_age_seconds']}s and owner PID not alive "
          f"on {report['probe_host']}")
    print(f"\n{verb}: {len(report['orphans'])} reservation(s), "
          f"{report['tokens_returned']:,} tokens")
    if report["orphans"]:
        print(head)
        for o in report["orphans"]:
            print(f"{o['run_id']:<24} {o['reservation_id']:<34} {o['age_seconds']:>9,}s "
                  f"{o['estimate_tokens']:>12,} {str(o['pid']):>8}  {o['liveness']}")
    print(f"\nretained: {len(report['retained'])} outstanding reservation(s)")
    if report["retained"]:
        print(head)
        for o in report["retained"]:
            print(f"{o['run_id']:<24} {o['reservation_id']:<34} {o['age_seconds']:>9,}s "
                  f"{o['estimate_tokens']:>12,} {str(o['pid']):>8}  {o['liveness']} "
                  f"({o['retained_because']})")
    if not report["committed"] and report["orphans"]:
        print("\nDry run. Re-run with --commit to write the releases.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m kg.spend",
                                 description="Shared preemptive spend guard (DD-022).")
    sub = ap.add_subparsers(dest="command", required=True)
    p_status = sub.add_parser("status", help="Ceilings, committed, outstanding, refusals.")
    p_status.add_argument("--run-id", default=None)
    p_rec = sub.add_parser("reconcile",
                           help="Ledger settles vs model_call events for one run.")
    p_rec.add_argument("--run-id", required=True)
    p_orph = sub.add_parser("release-orphans",
                            help="Release reservations whose owning process died "
                                 "(dry run unless --commit).")
    p_orph.add_argument("--run-id", default=None)
    p_orph.add_argument("--commit", action="store_true",
                        help="Write the releases. Without it this only lists candidates.")
    args = ap.parse_args(argv)
    ledger = default_ledger()
    if args.command == "status":
        print(json.dumps(ledger.status(args.run_id), indent=1))
        return 0
    if args.command == "reconcile":
        report = ledger.reconcile(args.run_id)
        print(json.dumps(report, indent=1))
        return 0 if report["ok"] else 1
    if args.command == "release-orphans":
        report = ledger.release_orphans(commit=args.commit, run_id=args.run_id)
        _print_orphan_report(report)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
