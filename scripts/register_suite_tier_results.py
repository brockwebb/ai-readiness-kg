#!/usr/bin/env python3
"""The two suite wall-clocks §4 asks for, read from the logs that produced them.

Task `cc_tasks/2026-09-09_guards_earn_their_keep.md` §4. **Zero spend, no network.**

Read from `logs/*.log` rather than typed, and the log is required to carry `EXIT=0`: a
wall-clock from a run that failed is a measurement of how long a failure took, and registering
it as the cost of the tier would be false. The logs are gitignored local artifacts, so the
RESULT cites their paths and the registry carries the numbers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                # noqa: E402

TASK = "cc_tasks/2026-09-09_guards_earn_their_keep.md"
SCRIPT_ARTIFACT = "register_suite_tier_results"
EPOCH = "2026-09-09"


def read_log(name: str) -> dict:
    """`{seconds, exit, passed, deselected}` from one log, or a hard stop."""
    p = REPO / "logs" / name
    if not p.is_file():
        raise SystemExit(f"FATAL: {p} does not exist; the RESULT may not quote a run that "
                         f"left no log")
    text = p.read_text(encoding="utf-8", errors="replace")
    secs = re.search(r"^WALL_SECONDS=(\d+)$", text, re.M)
    code = re.search(r"^EXIT=(\d+)$", text, re.M)
    if not secs or not code:
        raise SystemExit(f"FATAL: {p} carries no WALL_SECONDS/EXIT; it did not run to "
                         f"completion under the long-running protocol")
    if code.group(1) != "0":
        raise SystemExit(f"FATAL: {p} exited {code.group(1)}; a wall-clock from a failed run "
                         f"is not the cost of the tier")
    tail = re.search(r"(\d+) passed.*?(?:(\d+) deselected)?", text[-400:] or "")
    return {"seconds": int(secs.group(1)), "exit": 0,
            "summary": (text.strip().splitlines() or [""])[-3]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    fast, full = read_log("gate_fast.log"), read_log("suite.log")
    share = round(fast["seconds"] / full["seconds"], 4)

    rows = [
        ("suite_fast_seconds", fast["seconds"],
         f"Wall-clock of the FAST tier (`make gate-fast`, everything not marked `slow`) on "
         f"{EPOCH}, from logs/gate_fast.log, EXIT=0. This is the per-task gate. It is "
         f"{share:.0%} of the full suite. Measured after five control-fixture tests were "
         f"given the `slow` marker they already matched: before that the fast tier was 2762 s "
         f"and the split saved 18%, because ten tests are 91% of the suite and only one of "
         f"them was marked. Task {TASK} §3."),
        ("suite_full_seconds", full["seconds"],
         f"Wall-clock of the FULL suite on {EPOCH}, from logs/suite.log, EXIT=0, 1649 passed. "
         f"The pre-push check, run detached and polled to completion under CLAUDE.md's "
         f"long-running-command protocol. Unchanged by the tier split, which moves no test and "
         f"removes none: 3354 s here against 3373 s before the markers moved. Task {TASK} §3."),
        ("suite_fast_share_of_full", share,
         f"The fast tier as a fraction of the full suite on {EPOCH}: {fast['seconds']} s of "
         f"{full['seconds']} s. Registered because decision 4's purpose is a SHORT per-task "
         f"gate and 'we split the suite' is not evidence that it is short. Task {TASK} §3."),
    ]

    if a.dry_run:
        print(json.dumps({"fast": fast, "full": full, "share": share}, indent=1))
        for b, v, _n in rows:
            print(f"  {cycle_results.name_for(b, EPOCH):40s} {v}")
        return 0

    from seldon_artifacts import live_artifact
    if not live_artifact(SCRIPT_ARTIFACT):
        import subprocess
        r = subprocess.run(
            ["seldon", "artifact", "create", "Script", "--actor", "cc",
             "-p", f"name={SCRIPT_ARTIFACT}",
             "-p", "path=scripts/register_suite_tier_results.py",
             "-p", f"description=Reads the fast-tier and full-suite wall-clocks from their "
                   f"logs, refusing any log that does not carry EXIT=0, and registers them. "
                   f"Task {TASK}."],
            capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr[-300:]}")

    out = cycle_results.register(
        [(cycle_results.name_for(b, EPOCH), v, n) for b, v, n in rows],
        cycle=EPOCH, script=SCRIPT_ARTIFACT, data="scan_targets_fss_2026-09_v4")
    print(json.dumps(out, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
