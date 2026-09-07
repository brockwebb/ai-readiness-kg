#!/usr/bin/env python3
"""The registrar every scan cycle registers its Results through. **Zero spend, no network.**

Task `cc_tasks/2026-09-07_scan_harness_v3.md` §1.6, enforcing DD-056: *a cycle-level Result
name carries its cycle, because a Result name is immutable and a cycle repeats.*

The rule existed and nothing enforced it. A Seldon Result name is bound once (AD-028): the
2026-09-07 cycle found that out mid-run, when `scan_control_findings` was already bound at 31
by the 2026-09-06 control cycle and its own 33 was refused — after the measurement, at the
point where the cheapest response is to invent a name under pressure. Cycle 2 would hit the
same wall 101 times.

Names are checked BEFORE any of them is registered, which is the same discipline
`seldon result register` applies to its own references: a run that binds half a cycle's Results
and then refuses is worse than one that refuses first.

**The allow-list is the record of an exception, not a loophole.** DD-056 settled that the bare
names the FIRST cycle bound stand — they are immutable and they are cited in
`cc_tasks/2026-09-07_scan_run_RESULT.md`, and renaming them would leave two records of one
measurement. They are listed here by exact string, they are never reused by a later cycle, and
a name that is not on the list and not cycle-suffixed is refused whatever it looks like.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: `scan_2026-09-07` -> `2026-09-07`. The cycle name is the parameter; the suffix is its date
#: part, which is what DD-056's examples use (`scan_surfaces_2026-09-07`).
_CYCLE_PREFIX = "scan_"


def cycle_suffix(cycle: str) -> str:
    return cycle[len(_CYCLE_PREFIX):] if cycle.startswith(_CYCLE_PREFIX) else cycle


#: Bound by the 2026-09-07 cycle before the convention existed. DD-056 §"What is not renamed".
#: Frozen: this list may only SHRINK (if a name is ever retired), never grow — a new entry
#: would be a new exception, and the whole point is that there are no new exceptions.
FIRST_CYCLE_EXCEPTIONS = frozenset({
    "scan_a10_applicable_n", "scan_a10_error", "scan_a10_fail", "scan_a10_not_applicable",
    "scan_a10_pass", "scan_a10_pass_rate", "scan_a11_declared_applicable_n",
    "scan_a11_declared_error", "scan_a11_declared_fail", "scan_a11_declared_not_applicable",
    "scan_a11_declared_pass", "scan_a11_declared_pass_rate", "scan_a12_error",
    "scan_a12_fail", "scan_a12_not_applicable", "scan_a12_pass", "scan_a1_applicable_n",
    "scan_a1_error", "scan_a1_fail", "scan_a1_not_applicable", "scan_a1_pass",
    "scan_a1_pass_rate", "scan_a2_applicable_n", "scan_a2_error", "scan_a2_fail",
    "scan_a2_not_applicable", "scan_a2_pass", "scan_a2_pass_rate", "scan_a3_applicable_n",
    "scan_a3_error", "scan_a3_fail", "scan_a3_not_applicable", "scan_a3_pass",
    "scan_a3_pass_rate", "scan_a4_applicable_n", "scan_a4_error", "scan_a4_fail",
    "scan_a4_not_applicable", "scan_a4_pass", "scan_a4_pass_rate", "scan_a5_applicable_n",
    "scan_a5_error", "scan_a5_fail", "scan_a5_not_applicable", "scan_a5_pass",
    "scan_a5_pass_rate", "scan_a6_applicable_n", "scan_a6_error", "scan_a6_fail",
    "scan_a6_not_applicable", "scan_a6_pass", "scan_a6_pass_rate", "scan_a8_applicable_n",
    "scan_a8_error", "scan_a8_fail", "scan_a8_not_applicable", "scan_a8_pass",
    "scan_a8_pass_rate", "scan_a9_applicable_n", "scan_a9_error", "scan_a9_fail",
    "scan_a9_not_applicable", "scan_a9_pass", "scan_a9_pass_rate",
    "scan_agencies_unobservable", "scan_agencies_with_no_admitted_surface",
    "scan_b3_applicable_n", "scan_b3_error", "scan_b3_fail", "scan_b3_not_applicable",
    "scan_b3_pass", "scan_b3_pass_rate", "scan_d1_applicable_n", "scan_d1_error",
    "scan_d1_fail", "scan_d1_not_applicable", "scan_d1_pass", "scan_d1_pass_rate",
    "scan_d4_applicable_n", "scan_d4_error", "scan_d4_fail", "scan_d4_not_applicable",
    "scan_d4_pass", "scan_d4_pass_rate", "scan_f4_applicable_n", "scan_f4_error",
    "scan_f4_fail", "scan_f4_not_applicable", "scan_f4_pass", "scan_f4_pass_rate",
    "scan_findings", "scan_g1_d_applicable_n", "scan_g1_d_error", "scan_g1_d_fail",
    "scan_g1_d_not_applicable", "scan_g1_d_pass", "scan_g1_d_pass_rate",
    "scan_hosts_refusing_or_unreachable", "scan_observations", "scan_surfaces",
    "scan_surfaces_unobservable"
})


class ResultNameError(ValueError):
    """A per-cycle Result name that does not carry its cycle."""


def check_name(name: str, cycle: str) -> None:
    """Raise unless `name` carries `cycle`, or is a recorded first-cycle exception."""
    if name in FIRST_CYCLE_EXCEPTIONS:
        return
    suffix = cycle_suffix(cycle)
    if name.endswith(f"_{suffix}"):
        return
    raise ResultNameError(
        f"Result name {name!r} is a per-cycle metric with no cycle in it. DD-056: name it "
        f"{name}_{suffix}. A bare metric name is a column heading, and a Result name is bound "
        f"once (AD-028) — the second cycle to use it is refused mid-run, after the measurement.")


def check_names(names, cycle: str) -> None:
    """Every name, before any of them is registered. Reports ALL offenders, not the first."""
    bad = []
    for n in names:
        try:
            check_name(n, cycle)
        except ResultNameError as exc:
            bad.append(str(exc))
    if bad:
        raise ResultNameError("\n".join(bad))


def register(rows, cycle: str, script: str, data: str) -> dict:
    """Register a cycle's Results after checking every name. `rows` is (name, value, note).

    Idempotent in the only sense AD-028 allows: a name already bound AT THE SAME VALUE is this
    script re-running; at a different value it is drift and stays an error.
    """
    check_names([n for n, _v, _note in rows], cycle)
    ok, already, failed = 0, [], []
    for n, v, note in rows:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description", note,
                            "--script-name", script, "--data-name", data],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        elif "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
            already.append(n)
        else:
            failed.append(n)
            print("FAILED:", n, r.stderr.strip()[-180:])
    return {"registered": ok, "already_at_this_value": len(already),
            "failed": len(failed), "of": len(rows)}
