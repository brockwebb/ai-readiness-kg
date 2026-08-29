#!/usr/bin/env python3
"""Scheduled entrypoint for the T0 bibliographic harvest (task 2026-08-29_biblio_cron).

Runs two legs, in order, both idempotent and both quota-safe:

    1. `python -m kg.biblio resume`            finish the harvest, recompute derived rankings
    2. `t1_build_index.py --phase project`     regenerate manifest table + operator pickup

WHY A PYTHON ENTRYPOINT AND NOT A BASH WRAPPER
`scripts/jobs/airkg_extraction_burn.sh` is the repo's other scheduled job and it is bash.
This one is not, for one reason: the §5 guardrail has to be *testable*. A guard that lives in
an untested shell script is an assertion, not a control. Everything below — the spend-ledger
postcondition, the import-closure assertion, log truncation, retention — is exercised by
tests/test_biblio_resume_job.py, which a bash wrapper could not be. The launchd plist calls
this file directly; there is no shell layer.

THE GUARDRAIL (task §5), in two parts, because they fail differently:

  * PREVENTIVE — the scheduled legs do not import `kg.extraction.model_stub`, so no
    reservation against the spend guard is reachable at all. This is the real control: it
    makes spend impossible rather than merely visible. It is enforced by test
    (`test_real_scheduled_legs_import_no_spend_path`), which imports the leg modules in a
    clean subprocess and asserts the closure. That is the right place for it, because the
    legs run as SUBPROCESSES of this job — their imports never appear in this process's
    `sys.modules`, so no run-time check here could see them.
  * DETECTIVE — the spend-ledger fingerprint. The ledger is hashed before and after the legs
    run; any change fails the job nonzero. This is what actually covers the legs at run
    time, and it catches spend arriving by any route — subprocess, lazy import, a script
    invoked by a script. It detects after the fact; it does not prevent.

  The third check below (`spend_modules_loaded` on a delta) covers only THIS process — the
  entrypoint's own imports, chiefly `kg.biblio` via the coverage note. It is scoped as a
  delta against a baseline taken at start-up, so a module already resident in the host
  process (a test runner that imported `kg.spend` for its own reasons) is not misattributed
  to this run. Deliberately the weakest of the three, and kept only because it is the one
  that would notice `kg.biblio` growing a spend import underneath us.

No model-spending job is ever scheduled without an operator-declared ceiling in the unit
itself. This task schedules none, and the checks above are what make that claim auditable
rather than merely stated.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
CONTROLS = REPO / "controls.yaml"
LEDGER = REPO / "state" / "spend_ledger.jsonl"
LOG_DIR = REPO / "state" / "logs" / "biblio_resume"

#: Dated run logs this job owns and may delete. Anything else in LOG_DIR (launchd.log, an
#: operator's saved copy) is off limits — a retention sweep that deletes what it did not
#: write is a data-loss bug waiting for its first slow week.
DATED_LOG = re.compile(r"^\d{4}-\d{2}-\d{2}\.log$")

#: Modules whose presence in the run's import closure means a spend path is reachable.
SPEND_MODULES = ("kg.extraction.model_stub", "kg.spend")


def controls() -> dict:
    """Job config from controls.yaml. Missing block is a hard error, not a default.

    Per ~/GitHub/CLAUDE.md §4: falling through to a built-in default silently produces
    behaviour the operator never chose — here, a retention window that quietly differs from
    the one written down."""
    cfg = yaml.safe_load(CONTROLS.read_text(encoding="utf-8")) or {}
    jobs = (cfg.get("jobs") or {}).get("biblio_resume")
    if not jobs:
        raise SystemExit(f"FATAL: controls.yaml has no jobs.biblio_resume block ({CONTROLS})")
    for key in ("log_max_line_chars", "log_max_run_bytes", "log_retention_days"):
        if key not in jobs:
            raise SystemExit(f"FATAL: controls.yaml jobs.biblio_resume missing '{key}'")
    return jobs


def ledger_fingerprint() -> tuple[int, str]:
    """(size, sha256) of the shared spend ledger; (-1, '') when it does not exist."""
    if not LEDGER.exists():
        return (-1, "")
    raw = LEDGER.read_bytes()
    return (len(raw), hashlib.sha256(raw).hexdigest())


def spend_modules_loaded(modules=None, baseline: set[str] | None = None) -> list[str]:
    """Spend-path modules an import closure gained, relative to `baseline`.

    The delta is the point. An absolute reading of `sys.modules` measures the whole host
    process, not this job: under the test suite it reports modules some other test imported,
    which is both a false alarm and, worse, a true alarm that means nothing. Only modules
    that appeared *during the run* are attributable to the run."""
    loaded = sys.modules if modules is None else modules
    base = baseline or set()
    return sorted(m for m in loaded if m not in base
                  and any(m == s or m.startswith(s + ".") for s in SPEND_MODULES))


class Log:
    """Tee to the dated run log and stdout, with the log-bomb guard on both.

    Truncation is per line AND per run. A single pathological line is the Docling failure
    mode already met on this project (one exception embedded a whole PDF page dict and wrote
    ~230,000 lines, taking the process down with it — scripts/t1_build_index.py `_short`).
    A flood of *ordinary* lines is the other half of the same denial of service, so the run
    cap is not redundant with the line cap: neither bound implies the other.
    """

    def __init__(self, path: Path, max_line: int, max_run: int):
        self.path, self.max_line, self.max_run = path, max_line, max_run
        self.written = 0
        self.capped = False
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = path.open("a", encoding="utf-8")

    def line(self, text: str) -> None:
        t = text.rstrip("\n")
        if len(t) > self.max_line:
            t = f"{t[:self.max_line]}… [+{len(t) - self.max_line} chars truncated]"
        if self.written >= self.max_run:
            if not self.capped:
                self.capped = True
                msg = f"… [run log cap {self.max_run} bytes reached; further output dropped]"
                self.fh.write(msg + "\n")
                print(msg, flush=True)
            return
        self.written += len(t) + 1
        self.fh.write(t + "\n")
        self.fh.flush()
        print(t, flush=True)

    def close(self) -> None:
        self.fh.close()


def run_leg(name: str, cmd: list[str], log: Log) -> int:
    """Run one leg, streaming its output through the log guard. Never raises on leg failure."""
    log.line(f"--- leg: {name}")
    log.line(f"$ {' '.join(cmd)}")
    # PYTHONUNBUFFERED: the child writes to a pipe, so its stdout is block-buffered and the
    # parent's `bufsize=1` does nothing about that — it governs this side of the pipe only.
    # Without it a long leg shows nothing in the log until it exits, which makes a hang
    # indistinguishable from progress, and a leg killed mid-run loses its buffered output
    # entirely. For a scheduled job whose only artifact IS the log, that is the whole record.
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    try:
        p = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    except OSError as exc:                       # interpreter or script missing
        log.line(f"--- leg {name} FAILED to start: {exc}")
        return 127
    assert p.stdout is not None
    for raw in p.stdout:
        log.line(raw)
    rc = p.wait()
    log.line(f"--- leg {name} rc={rc}")
    return rc


def prune(log: Log, retention_days: int, today: dt.date) -> list[str]:
    """Delete this job's own dated logs older than the retention window."""
    cutoff = today - dt.timedelta(days=retention_days)
    removed = []
    for f in sorted(LOG_DIR.glob("*.log")):
        if not DATED_LOG.match(f.name):
            continue                             # not ours; leave it alone
        try:
            stamp = dt.date.fromisoformat(f.stem)
        except ValueError:
            continue
        if stamp < cutoff:
            f.unlink()
            removed.append(f.name)
    if removed:
        log.line(f"retention: removed {len(removed)} log(s) older than "
                 f"{retention_days}d: {', '.join(removed)}")
    return removed


def coverage_note(log: Log) -> None:
    """Task §4: when T0 reaches full coverage the job keeps running and says so.

    Removal is an operator choice later, never automated — a job that deletes itself on a
    threshold takes its own evidence with it."""
    try:
        sys.path.insert(0, str(REPO))
        from kg import biblio
        cov = biblio.coverage()
    except Exception as exc:                     # coverage is a report, not the job
        log.line(f"coverage: unavailable ({type(exc).__name__}: {exc})")
        return
    log.line(f"coverage: resolved={cov['resolved']}/{cov['total']} "
             f"retryable={cov['retryable']} partial_finding={cov['partial_finding']} "
             f"blocked={cov['blocked']}")
    if cov["retryable"] == 0:
        log.line("coverage: COMPLETE — no retryable documents remain. This job now no-ops "
                 "harmlessly; unloading it is an operator decision, not an automatic one.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="biblio_resume_job.py", description=__doc__)
    ap.add_argument("--limit", type=int, default=0,
                    help="cap documents harvested this run (0 = no cap)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would run, touch nothing")
    a = ap.parse_args(argv)

    # DD-007: subscription OAuth only. Refuse inherited API credentials on every invocation,
    # not just the launchd one — the wrapper that used to do this protected one caller.
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        os.environ.pop(var, None)

    cfg = controls()
    today = dt.date.today()
    log = Log(LOG_DIR / f"{today.isoformat()}.log",
              int(cfg["log_max_line_chars"]), int(cfg["log_max_run_bytes"]))
    started = dt.datetime.now(dt.timezone.utc)
    log.line(f"=== {started.isoformat(timespec='seconds')} | biblio-resume fire "
             f"(pid {os.getpid()})")

    # Baseline for the module delta: everything already resident before the job does any
    # work of its own. See the module docstring for why this is a delta and not an absolute.
    modules_at_start = set(sys.modules)
    before = ledger_fingerprint()
    log.line(f"spend ledger before: size={before[0]} sha256={before[1][:12] or '(absent)'}")

    if a.dry_run:
        log.line("dry run: legs not executed")
        log.close()
        return 0

    rcs = []
    resume_cmd = [sys.executable, "-m", "kg.biblio", "resume"]
    if a.limit:
        resume_cmd += ["--limit", str(a.limit)]
    rcs.append(run_leg("biblio-resume", resume_cmd, log))
    rcs.append(run_leg("t1-project", [sys.executable, str(REPO / "scripts" / "t1_build_index.py"),
                                      "--phase", "project"], log))

    coverage_note(log)
    prune(log, int(cfg["log_retention_days"]), today)

    # --- §5 guardrail, both parts. A breach fails the run regardless of leg outcomes.
    breach = 0
    after = ledger_fingerprint()
    if after != before:
        log.line(f"FATAL: spend ledger changed during a job declared to spend nothing "
                 f"(before size={before[0]} sha={before[1][:12]}; "
                 f"after size={after[0]} sha={after[1][:12]}). "
                 f"No ceiling was declared for this unit, so any reservation here is "
                 f"unbudgeted by construction. Investigate before rescheduling.")
        breach = 3
    else:
        log.line("guardrail: spend ledger unchanged (no reservation, no settle)")
    loaded = spend_modules_loaded(baseline=modules_at_start)
    if loaded:
        log.line(f"FATAL: this run imported spend-path module(s): {', '.join(loaded)}. "
                 f"The scheduled path must not be able to spend.")
        breach = breach or 4
    else:
        log.line("guardrail: this run imported no spend-path module")

    rc = breach or max(rcs, default=0)
    elapsed = (dt.datetime.now(dt.timezone.utc) - started).total_seconds()
    log.line(f"=== rc={rc} legs={rcs} elapsed={elapsed:.1f}s")
    log.close()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
