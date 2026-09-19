#!/usr/bin/env python3
"""Install YOUR schedule for scanning YOUR frame: a cron line or a launchd agent. **No network.**

`cc_tasks/2026-09-19_adopter_path.md` decision 2. The schedule is `params.yaml:schedule`:

    schedule:
      when: on_demand            # or a five-field cron expression, e.g. "0 6 * * 1"
      frame: frames/my_site.yaml

`on_demand` installs nothing and says so: a scan runs when you type `make scan-now FRAME=...`.
A cron expression is installed on THIS machine as the job `make scan-now FRAME=<frame>`, logged
to `out/<frame>/scheduled.log`:

* **cron** (Linux and anything with `crontab`): one line in your crontab, marked
  `# airkg-scan:<frame>` so installing again replaces it rather than adding a second;
* **launchd** (macOS, the default there): `~/Library/LaunchAgents/org.airkg.scan.<frame>.plist`
  with the cron expression as `StartCalendarInterval` entries. launchd has no cron syntax, so
  each field's list is expanded and the entries are the product of the lists; when both
  day-of-month and day-of-week are restricted, cron runs on EITHER (crontab(5)), so both sets
  of entries are written. The plist is written, not loaded: the command that loads it now is
  printed, and launchd loads it at your next login regardless.

Everything written is printed. Nothing in Seldon is involved, and this project's own
`params.yaml` says `on_demand`, so run here this installs nothing.

    python scripts/install_schedule.py [--kind cron|launchd] [--crontab-file PATH]
                                       [--launchagents-dir DIR]
"""
from __future__ import annotations

import argparse
import itertools
import os
import plistlib
import shlex
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

ON_DEMAND = "on_demand"
#: The five cron fields in order, their launchd keys (launchd.plist(5), StartCalendarInterval)
#: and their ranges (crontab(5); day-of-week 7 is Sunday, as 0 is).
FIELDS = (("minute", "Minute", 0, 59), ("hour", "Hour", 0, 23), ("day", "Day", 1, 31),
          ("month", "Month", 1, 12), ("weekday", "Weekday", 0, 7))
#: The label prefix of the launchd agent and the crontab marker. One per frame.
LABEL = "org.airkg.scan"
MARKER = "# airkg-scan:"


def parse_field(text: str, lo: int, hi: int, name: str) -> list | None:
    """One cron field as the sorted values it allows, or None for `*` (every value).

    crontab(5) grammar: `*`, a number, a range `a-b`, a step `*/n` or `a-b/n`, and comma lists
    of those. Names (`mon`, `jan`) and the `@daily` shorthands are refused rather than guessed.
    """
    if text == "*":
        return None
    out: set = set()
    for part in text.split(","):
        base, _, step = part.partition("/")
        try:
            n = int(step) if step else 1
            if base == "*":
                a, b = lo, hi
            elif "-" in base:
                a, b = (int(x) for x in base.split("-", 1))
            else:
                a = b = int(base)
        except ValueError:
            raise SystemExit(f"REFUSING: cron {name} field {text!r}: {part!r} is not a number, "
                             f"a range, a step or `*` (names are not accepted)")
        if n < 1 or not (lo <= a <= b <= hi):
            raise SystemExit(f"REFUSING: cron {name} field {text!r}: {part!r} is outside "
                             f"{lo}-{hi}")
        out.update(range(a, b + 1, n))
    return sorted(out)


def parse_cron(expr: str) -> dict:
    parts = str(expr).split()
    if len(parts) != 5:
        raise SystemExit(f"REFUSING: schedule.when {expr!r} is neither `{ON_DEMAND}` nor a "
                         f"five-field cron expression (minute hour day month weekday)")
    return {f[0]: parse_field(p, f[2], f[3], f[0]) for p, f in zip(parts, FIELDS)}


def calendar_intervals(fields: dict) -> list:
    """launchd `StartCalendarInterval` entries equivalent to the parsed cron fields."""
    def product(keys) -> list:
        chosen = [(f[1], fields[f[0]]) for f in FIELDS if f[0] in keys and fields[f[0]]]
        if not chosen:
            return [{}]
        names = [k for k, _ in chosen]
        return [dict(zip(names, combo)) for combo in
                itertools.product(*[v for _, v in chosen])]
    common = ("minute", "hour", "month")
    if fields["day"] and fields["weekday"]:
        # crontab(5): "if both fields are restricted, the command runs when EITHER matches".
        return product(common + ("day",)) + product(common + ("weekday",))
    return product(common + ("day", "weekday"))


def job(frame: Path, py: str) -> tuple:
    """`(argv, log, frame name)` of the scheduled job: `make scan-now` for the frame, run in
    this checkout."""
    from scan import adopt
    f = adopt.load_frame(frame)
    if f["kind"] != adopt.DECLARED:
        raise SystemExit(f"REFUSING: schedule.frame {frame} is this project's frame, whose "
                         f"cycles are dispatched tasks and whose cadence is off; a schedule "
                         f"scans a frame you declared")
    log = adopt.frame_dir(REPO / "out", f["frame"]) / "scheduled.log"
    argv = ["make", "-C", str(REPO), "scan-now", f"FRAME={frame}", f"PY={py}"]
    return argv, log, f["frame"]


def install_cron(expr: str, argv: list, log: Path, slug: str, crontab_file: Path | None) -> str:
    line = (f"{expr} {' '.join(shlex.quote(a) for a in argv)} >> {shlex.quote(str(log))} 2>&1 "
            f"{MARKER}{slug}")
    if crontab_file:
        have = crontab_file.read_text(encoding="utf-8") if crontab_file.exists() else ""
    else:
        got = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        # `crontab -l` exits non-zero when the user has no crontab yet; that is an empty one.
        have = got.stdout if got.returncode == 0 else ""
    kept = [ln for ln in have.splitlines() if not ln.endswith(f"{MARKER}{slug}")]
    text = "\n".join(kept + [line]) + "\n"
    if crontab_file:
        crontab_file.parent.mkdir(parents=True, exist_ok=True)
        crontab_file.write_text(text, encoding="utf-8")
        where = str(crontab_file)
    else:
        done = subprocess.run(["crontab", "-"], input=text, text=True, capture_output=True)
        if done.returncode != 0:
            raise SystemExit(f"FATAL: crontab refused the new table: {done.stderr.strip()}")
        where = "your crontab"
    return f"wrote to {where}:\n{line}"


def install_launchd(expr: str, argv: list, log: Path, slug: str, agents: Path) -> str:
    label = f"{LABEL}.{slug}"
    plist = {"Label": label, "ProgramArguments": argv,
             "StartCalendarInterval": calendar_intervals(parse_cron(expr)),
             "StandardOutPath": str(log), "StandardErrorPath": str(log),
             "WorkingDirectory": str(REPO)}
    agents.mkdir(parents=True, exist_ok=True)
    path = agents / f"{label}.plist"
    path.write_bytes(plistlib.dumps(plist))
    return (f"wrote {path}:\n{path.read_text(encoding='utf-8')}\n"
            f"launchd loads it at your next login. To load it now:\n"
            f"  launchctl bootstrap gui/{os.getuid()} {shlex.quote(str(path))}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", choices=("cron", "launchd"),
                    default="launchd" if sys.platform == "darwin" else "cron")
    ap.add_argument("--crontab-file", type=Path, default=None,
                    help="write the crontab to this file instead of installing it")
    ap.add_argument("--launchagents-dir", type=Path,
                    default=Path.home() / "Library" / "LaunchAgents")
    ap.add_argument("--py", default=sys.executable,
                    help="the python the scheduled job runs (default: this one)")
    a = ap.parse_args(argv)
    from scan import load_params
    sched = load_params().get("schedule") or {}
    when = str(sched.get("when") or ON_DEMAND).strip()
    if when == ON_DEMAND:
        print(f"schedule.when is {ON_DEMAND}: nothing installed. Scan when you choose with "
              f"`make scan-now FRAME=<your frame>`.")
        return 0
    parse_cron(when)  # validated before anything is resolved or written
    if not sched.get("frame"):
        raise SystemExit("REFUSING: schedule.when is a cron expression and schedule.frame is "
                         "empty; a schedule has to name the frame it scans")
    frame = Path(sched["frame"])
    frame = frame if frame.is_absolute() else REPO / frame
    cmd, log, slug = job(frame, a.py)
    log.parent.mkdir(parents=True, exist_ok=True)
    if a.kind == "cron":
        print(install_cron(when, cmd, log, slug, a.crontab_file))
    else:
        print(install_launchd(when, cmd, log, slug, a.launchagents_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
