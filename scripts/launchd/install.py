#!/usr/bin/env python3
"""Render, install, and remove the biblio-resume LaunchAgent (task 2026-08-29_biblio_cron).

The plist is generated from the committed template so the unit is reproducible: schedule
comes from controls.yaml, paths from this checkout, interpreter from whichever python is
running the installer. Nothing about the loaded unit is hand-authored, so a machine rebuild
is `--install` and not archaeology.

    python3 scripts/launchd/install.py --print       # render to stdout, touch nothing
    python3 scripts/launchd/install.py --install     # render, write, bootstrap
    python3 scripts/launchd/install.py --status      # is it loaded, when did it last run
    python3 scripts/launchd/install.py --uninstall   # bootout and remove the plist

Run with the interpreter the job should use — `/opt/anaconda3/bin/python3` on this machine,
which carries the deps the legs need. The installer records that choice into the unit rather
than guessing at run time.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
TEMPLATE = Path(__file__).resolve().parent / "com.brock.aikg.biblio-resume.plist.template"
LABEL = "com.brock.aikg.biblio-resume"
TARGET = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def render(python: str | None = None) -> str:
    cfg = yaml.safe_load((REPO / "controls.yaml").read_text(encoding="utf-8")) or {}
    job = (cfg.get("jobs") or {}).get("biblio_resume")
    if not job:
        raise SystemExit("FATAL: controls.yaml has no jobs.biblio_resume block")
    for key in ("hour", "minute"):
        if key not in job:
            raise SystemExit(f"FATAL: controls.yaml jobs.biblio_resume missing '{key}'")
    py = python or sys.executable
    if not Path(py).exists():
        raise SystemExit(f"FATAL: interpreter does not exist: {py}")
    subs = {"@LABEL@": LABEL, "@REPO@": str(REPO), "@PYTHON@": py,
            "@PYTHON_DIR@": str(Path(py).parent),
            "@HOUR@": str(int(job["hour"])), "@MINUTE@": f"{int(job['minute']):02d}"}
    text = TEMPLATE.read_text(encoding="utf-8")
    for k, v in subs.items():
        text = text.replace(k, v)
    # Scan for ANY surviving @PLACEHOLDER@, not just the keys we know about: the failure
    # worth catching is a placeholder the substitution table has never heard of (renamed in
    # the template, added without a key), and checking only known keys cannot see that one.
    left = sorted(set(re.findall(r"@[A-Z_][A-Z0-9_]*@", text)))
    if left:
        raise SystemExit(f"FATAL: unsubstituted placeholders remain: {left}")
    return text


def _launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True)


def install(python: str | None) -> int:
    text = render(python)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    (REPO / "state" / "logs" / "biblio_resume").mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8")
    print(f"wrote {TARGET}")
    domain = f"gui/{os.getuid()}"
    _launchctl("bootout", f"{domain}/{LABEL}")   # idempotent: not-loaded is fine
    r = _launchctl("bootstrap", domain, str(TARGET))
    if r.returncode != 0:
        print(f"FATAL: bootstrap failed rc={r.returncode}: {r.stderr.strip()}")
        return r.returncode
    print(f"bootstrapped {LABEL} into {domain}")
    return status()


def uninstall() -> int:
    r = _launchctl("bootout", f"gui/{os.getuid()}/{LABEL}")
    print(f"bootout rc={r.returncode} {r.stderr.strip()}".rstrip())
    if TARGET.exists():
        TARGET.unlink()
        print(f"removed {TARGET}")
    else:
        print(f"no plist at {TARGET}")
    print("NOTE: state/logs/biblio_resume/ is left in place — the run record outlives "
          "the unit that wrote it.")
    return 0


def status() -> int:
    r = _launchctl("print", f"gui/{os.getuid()}/{LABEL}")
    if r.returncode != 0:
        print(f"{LABEL}: NOT LOADED (launchctl print rc={r.returncode})")
        return 1
    keep = ("state =", "last exit code", "runs =", "path =")
    for line in r.stdout.splitlines():
        if any(k in line for k in keep):
            print(line.strip())
    print(f"plist on disk: {TARGET.exists()}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="install.py", description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--print", dest="show", action="store_true")
    g.add_argument("--install", action="store_true")
    g.add_argument("--uninstall", action="store_true")
    g.add_argument("--status", action="store_true")
    ap.add_argument("--python", default=None,
                    help="interpreter to bake into the unit (default: this one)")
    a = ap.parse_args(argv)
    if a.show:
        print(render(a.python)); return 0
    if a.install:
        return install(a.python)
    if a.uninstall:
        return uninstall()
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
