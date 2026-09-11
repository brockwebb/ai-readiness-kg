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
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

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


#: The cycle that bound the bare names above. Named so `name_for` can tell "this is that
#: cycle re-registering its own Result" from "a later cycle reaching for a bound name".
FIRST_CYCLE = "scan_2026-09-07"


def name_for(base: str, cycle: str) -> str:
    """The Result name a cycle registers a metric under. **The single point of suffixing.**

    DD-041's amendment is the prior art and the reason this is one function: the CQ harness
    suffixed its FILES and not its Result NAMES, so a rerun would have overwritten a
    registered measurement, and the fix was "applied at the single point where the name list
    is returned so no emitter can forget it". Same shape here — an emitter names the metric
    and never the cycle.

    The first cycle keeps the bare names it already bound (DD-056 §"What is not renamed"):
    they are immutable and cited, and re-registering them suffixed would leave two records of
    one measurement. Every other cycle, including a re-run of a metric the first cycle never
    bound, is suffixed.
    """
    if cycle == FIRST_CYCLE and base in FIRST_CYCLE_EXCEPTIONS:
        return base
    suffix = cycle_suffix(cycle)
    return base if base.endswith(f"_{suffix}") else f"{base}_{suffix}"


class ResultNameError(ValueError):
    """A per-cycle Result name that does not carry its cycle."""


#: The name shape that let three populations share one Result. `scan_leg_rate_<leg>_<stat>` was
#: emitted by `build_l0_matrices.leg_results` without saying WHICH family's rate it was; the
#: shipped builder was safe only by coincidence (its host legs and its product legs are
#: disjoint), and the first caller to ask a third family for the stat registered six Tier C
#: values under host-family names — `cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §1, six
#: Results that cannot be corrected because a name binds once (AD-028).
#:
#: Refused HERE rather than in the emitter, because the emitter is one caller and this is the
#: choke point every caller passes through. `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md`
#: decision 4. The already-registered unprefixed names are untouched and keep resolving; what is
#: refused is minting another one.
_UNPREFIXED_LEG_RATE = re.compile(r"^scan_leg_rate_[a-z0-9_]+$")


class UnprefixedLegRateName(ValueError):
    """A leg-rate Result name that does not say which family's rate it is."""


def refuse_unprefixed_leg_rate(name: str, cycle: str) -> None:
    """Raise on `scan_leg_rate_<leg>_<stat>_<cycle>`, whatever the caller."""
    stem = name
    suffix = cycle_suffix(cycle)
    if stem.endswith(f"_{suffix}"):
        stem = stem[: -(len(suffix) + 1)]
    if _UNPREFIXED_LEG_RATE.match(stem):
        raise UnprefixedLegRateName(
            f"Result name {name!r} does not say which family's leg rate it is. Three "
            f"populations compute one — the 16 Tier A host surfaces, the declared flagship "
            f"surfaces, and the 3 Tier C reference hosts — and an unprefixed name lets whichever "
            f"caller runs first bind it for all of them. Use "
            f"`scan_l0_<host|product|tierc>_leg_rate_{stem.removeprefix('scan_leg_rate_')}`. "
            f"The unprefixed names already in the registry are not affected and are not edited.")


def check_name(name: str, cycle: str) -> None:
    """Raise unless `name` carries `cycle`, or is the FIRST cycle re-registering its own name.

    The exception is scoped to `FIRST_CYCLE`, and that scoping is the enforcement. Without it
    the allow-list was a loophole exactly where DD-056 says it must not be: this module's own
    docstring promises the bare names "are never reused by a later cycle", and a bare
    `check_name` let cycle 2 through to `seldon result register`, which refuses a bound name at
    a new value (AD-028) — mid-run, after the measurement, which is the incident DD-056 was
    written about. Found by `tests/test_scan_run_2.py`; the hole shipped with the check.
    """
    suffix = cycle_suffix(cycle)
    if name in FIRST_CYCLE_EXCEPTIONS:
        if cycle == FIRST_CYCLE:
            return
        raise ResultNameError(
            f"Result name {name!r} is bound by the {FIRST_CYCLE} cycle and is a first-cycle "
            f"exception, not a free name. DD-056: cycle {cycle} registers it as "
            f"{name}_{suffix}. A Result name is bound once (AD-028), so reusing it here is "
            f"refused by the registry after the measurement rather than before it.")
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
            refuse_unprefixed_leg_rate(n, cycle)
            check_name(n, cycle)
        except (ResultNameError, UnprefixedLegRateName) as exc:
            bad.append(str(exc))
    if bad:
        raise ResultNameError("\n".join(bad))


def ensure_data_file(name: str, path: str, description: str) -> str:
    """The DataFile a cycle's Results are computed from, created if this cycle has none.

    Every cycle writes a new matrix under a new name, so every cycle needs a new DataFile —
    and `seldon result register` resolves every reference BEFORE writing an event (AD-028), so
    a missing one refuses the whole batch rather than dropping a link. Cycle 2 hit exactly
    that: 143 Results refused, 0 registered, which is the right failure and the wrong place to
    discover the artifact was missing. Creating it here means the registrar that needs it is
    the one that guarantees it.
    """
    from seldon_artifacts import live_artifact
    found = live_artifact(name)
    if found:
        return found
    r = subprocess.run(["seldon", "artifact", "create", "DataFile", "--actor", "cc",
                        "-p", f"name={name}", "-p", f"path={path}",
                        "-p", f"description={description}"],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot create DataFile {name}: {r.stderr.strip()[-400:]}")
    made = live_artifact(name)
    if not made:
        raise SystemExit(f"FATAL: created DataFile {name} but cannot resolve it")
    return made


def register(rows, cycle: str, script: str, data: str, data_path: str | None = None,
             data_description: str | None = None) -> dict:
    """Register a cycle's Results after checking every name. `rows` is (name, value, note).

    Idempotent in the only sense AD-028 allows: a name already bound AT THE SAME VALUE is this
    script re-running; at a different value it is drift and stays an error.

    References are resolved to UUIDs here rather than passed as names, because
    `--script-name` matches over superseded artifacts too: a name that was ever duplicated
    stays unresolvable even after the twin is superseded.
    """
    from seldon_artifacts import live_artifact
    check_names([n for n, _v, _note in rows], cycle)
    data_id = (ensure_data_file(data, data_path, data_description)
               if data_path else live_artifact(data))
    script_id = live_artifact(script)
    for label, ident, nm in (("Script", script_id, script), ("DataFile", data_id, data)):
        if not ident:
            raise SystemExit(f"FATAL: no live {label} artifact named {nm!r}; "
                             f"nothing was registered")
    ok, already, failed = 0, [], []
    for n, v, note in rows:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description", note,
                            "--script-id", script_id, "--data-ids", data_id],
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
