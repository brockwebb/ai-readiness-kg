#!/usr/bin/env python3
"""The two suite wall-clocks of `cc_tasks/2026-09-10_harness_small.md` §4. **Zero spend, no network.**

A NEW script rather than an edit to `register_suite_tier_results.py`: that one carries the prose
of the measurement it made, `2026-09-10`'s, and a Result note is the record of why a number is
what it is. Rewriting its notes to describe a different run would leave one script claiming to
have said two different things. `~/GitHub/CLAUDE.md` §11: new files get new names.

Same two disciplines as its predecessor, and for the same reasons:

* the seconds are READ from the log that produced them, never typed;
* a log without `EXIT=0` is refused, because the wall-clock of a failed run is a measurement of
  how long a failure took and registering it as the cost of the tier would be false.

`b` in the epoch is DD-056 doing its job: `suite_fast_seconds_2026-09-10` is already bound to
1145 s and a Result name binds once (AD-028). The second measurement of the same day gets its
own name and both records stand.
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

TASK = "cc_tasks/2026-09-10_harness_small.md"
SCRIPT_ARTIFACT = "register_harness_small_results"
EPOCH = "2026-09-10b"


def read_log(name: str) -> dict:
    """`{seconds, exit, summary}` from one log, or a hard stop."""
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
    passed = re.search(r"(\d+) passed", text)
    return {"seconds": int(secs.group(1)), "exit": 0,
            "passed": int(passed.group(1)) if passed else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    fast, full = read_log("gate_fast.log"), read_log("gate_full.log")

    rows = [
        ("suite_fast_seconds", fast["seconds"],
         f"Wall-clock of the FAST tier (`make gate-fast`) on 2026-09-10 after the second "
         f"virtual-time pass, from logs/gate_fast.log, EXIT=0, {fast['passed']} passed. "
         f"**1145 s -> {fast['seconds']} s.** Two call sites paid for it: `merge_controls` now "
         f"takes a clock, so the merge test stopped running two seven-fixture cycles at the "
         f"standing rate (594 s -> 10.4 s), and the both-clocks agreement check runs its "
         f"real-clock side at a 20 rps test interval (302 s -> 25.7 s). No test was removed, "
         f"deselected or weakened, and the tier covers MORE tests than the 1145 s run: the "
         f"count went {fast['passed'] - 1644:+d}. Task {TASK} §3."),
        ("suite_full_seconds", full["seconds"],
         f"Wall-clock of the FULL suite on 2026-09-10 after the second virtual-time pass, from "
         f"logs/gate_full.log, EXIT=0, {full['passed']} passed, 2 skipped. The pre-push check "
         f"under CLAUDE.md's long-running-command protocol. **3354 s (2026-09-09) -> 1815 s "
         f"(first pass) -> {full['seconds']} s**, a {1 - full['seconds'] / 3354:.0%} cut from "
         f"where it started. `test_merging_controls_replaces_them_rather_than_accumulating` is "
         f"no longer in the top ten durations, which is what §3 predicted. Task {TASK} §3."),
    ]

    if a.dry_run:
        print(json.dumps({"fast": fast, "full": full}, indent=1))
        for b, v, n in rows:
            print(f"  {cycle_results.name_for(b, EPOCH):40s} {v}\n    {n[:160]}")
        return 0

    from seldon_artifacts import live_artifact
    if not live_artifact(SCRIPT_ARTIFACT):
        import subprocess
        r = subprocess.run(
            ["seldon", "artifact", "create", "Script", "--actor", "cc",
             "-p", f"name={SCRIPT_ARTIFACT}",
             "-p", "path=scripts/register_harness_small_results.py",
             "-p", f"description=Reads the fast-tier and full-suite wall-clocks of the "
                   f"harness-small task from their logs, refusing any log that does not carry "
                   f"EXIT=0, and registers them under the 2026-09-10b epoch. Task {TASK}."],
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
