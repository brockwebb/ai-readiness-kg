"""The injected clock: no bare wall time, an assertable limiter, and virtual == real.

`cc_tasks/2026-09-10_virtual_time.md`.

Ten tests were 91% of the suite's wall clock and every one was a loopback control cycle
sleeping for a rate limiter that exists to be polite to federal hosts
(`cc_tasks/2026-09-09_guards_earn_their_keep_RESULT.md` §4). Politeness is owed to
`www.census.gov`; it is not owed to `127.0.0.1`.

Prior art, adopted not invented: virtual-time scheduling as in Twisted's `task.Clock` and
RxJS's `TestScheduler`. Their shared rule is the one that matters — **advance time when someone
waits on it** — which is why `VirtualClock.sleep` records the wait and jumps forward rather than
returning immediately. A monkeypatched `time.sleep` would make "the limiter never asked" and
"the limiter asked and was ignored" indistinguishable, and the first is the defect.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.clock import REAL, RealClock, VirtualClock                # noqa: E402
from scan.fixtures.server import FixtureServer, MODES               # noqa: E402
from scan.manners import Fetcher                                    # noqa: E402


def _run_mod():
    spec = importlib.util.spec_from_file_location("scan_run_vt", SCAN / "run.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ §1: nothing bare left

#: The file that is ALLOWED to touch the standard library's clock, because it is the real
#: clock's implementation.
_CLOCK_IMPL = "clock.py"


def test_no_bare_wall_time_remains_under_the_scan_harness():
    """§1's source check. Every sleep and every interval read goes through the injected clock,
    or the injection is decorative: one forgotten `time.sleep` in a collector puts the suite
    back where it started and nothing would say so.

    **The needles are assembled from parts.** The last three source-scanning checks in this
    repo matched their own test file and reported it as the offender — the suffix-list
    retirement check, the self-licensing lint, and this pattern again. The task file says so in
    as many words, so this one is built not to.
    """
    needles = ["time" + ".sleep", "time" + ".monotonic", "time" + ".time("]
    offenders = []
    for py in sorted(SCAN.rglob("*.py")):
        if "__pycache__" in py.parts or py.name == _CLOCK_IMPL:
            continue
        src = py.read_text(encoding="utf-8")
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if any(n in line for n in needles):
                offenders.append(f"{py.relative_to(REPO)}:{i}: {line.strip()}")
    assert not offenders, (
        "bare wall-time calls under the scan harness; they must go through the injected "
        f"clock: {offenders}")

    # And the real clock IS the standard library, or the injection has no floor.
    impl = (SCAN / _CLOCK_IMPL).read_text(encoding="utf-8")
    assert all(n in impl for n in ("time" + ".monotonic", "time" + ".sleep")), (
        "the real clock no longer calls the standard library; every caller would be running "
        "on something that only looks like time")


def test_production_cannot_be_handed_the_virtual_clock():
    """Decision 1's structural guarantee. `run.py::main` takes no clock, so a cycle against
    real federal hosts cannot be constructed unthrottled — not by policy, by signature."""
    import inspect
    m = _run_mod()
    assert "clock" not in inspect.signature(m.main).parameters, (
        "run.py::main accepts a clock; a real cycle could then be run without the rate limit")
    assert "clock" in inspect.signature(m.run_controls).parameters, (
        "run_controls takes no clock, so the control fixtures cannot run virtual")
    assert Fetcher(load_params()).clock is REAL, "the Fetcher's default clock is not the real one"


# ------------------------------------------------------------------ §2 decision 2: the gaps

def test_the_limiter_schedules_the_standing_gap_between_requests_to_one_host():
    """**The property the real sleeps were implicitly guaranteeing, made explicit.**

    A real-clock run asserts this by taking a real second, which is why the suite cost an hour.
    Under the virtual clock the limiter's request is recorded, so the gap can be asserted in
    microseconds — and, unlike a patched-out `sleep`, a limiter that failed to ask would fail
    this test rather than passing it silently.
    """
    params = load_params()
    gap = 1.0 / float(params["manners"]["requests_per_second_per_host"])
    clock = VirtualClock()
    srv = FixtureServer("passes_all")
    base = srv.__enter__()
    try:
        f = Fetcher(params, clock=clock)
        for _ in range(4):
            f.raw_get(f"{base}/index.html")
        netloc = base.split("//", 1)[1]
    finally:
        srv.__exit__()

    stamps = f.request_times[netloc]
    assert len(stamps) >= 4, stamps
    deltas = [b - a for a, b in zip(stamps, stamps[1:])]
    assert all(d >= gap - 1e-9 for d in deltas), (
        f"consecutive requests to one netloc were spaced {deltas} apart in virtual time; the "
        f"standing limit is {gap}s")
    assert clock.waits, "the limiter never asked to wait, so the gaps came from nowhere"
    assert clock.slept >= gap * (len(stamps) - 1) - 1e-9


def test_a_virtual_sleep_is_a_jump_forward_and_not_a_no_op():
    """The distinction decision 1 turns on. A no-op clock would pass every spacing assertion
    above while the limiter did nothing at all."""
    c = VirtualClock()
    assert c.now() == 0.0
    c.sleep(1.0)
    assert c.now() == 1.0 and c.waits == [1.0]
    c.sleep(0)
    assert c.waits == [1.0], "a zero-length wait was recorded as a wait"
    c.advance(5.0)
    assert c.now() == 6.0 and c.waits == [1.0], "advance() must not record a wait"


# ------------------------------------------- §3 decision 3: one real-clock cycle survives

@pytest.mark.slow
def test_one_real_clock_cycle_still_pays_the_standing_rate():
    """Decision 3. Exactly one cycle on the real clock, over ONE fixture, asserting real
    wall-clock spacing.

    Everything else in the suite now runs virtual, which means nothing else would notice if
    `RealClock.sleep` stopped sleeping. This is the floor under all of it: the virtual clock is
    only a faithful stand-in while the real one really waits.
    """
    params = load_params()
    gap = 1.0 / float(params["manners"]["requests_per_second_per_host"])
    srv = FixtureServer("passes_all")
    base = srv.__enter__()
    try:
        f = Fetcher(params)                       # the REAL clock, by default
        assert f.clock is REAL
        t0 = time.monotonic()
        for _ in range(3):
            f.raw_get(f"{base}/index.html")
        elapsed = time.monotonic() - t0
    finally:
        srv.__exit__()
    assert elapsed >= gap * 2 - 0.05, (
        f"three requests to one host took {elapsed:.2f}s of REAL time; at {gap}s apart they "
        f"cannot take less than {gap * 2:.2f}s, so the real limiter is not waiting")


# ------------------------------------------------- §3 decision 5: virtual agrees with real

def test_the_control_gate_returns_the_same_verdicts_on_both_clocks():
    """**Decision 5, and it is the clause that licenses everything else.**

    If a rule read wall time, the two clocks would disagree and every virtual test in the
    suite would be measuring something the real cycle does not do. Compared fixture by
    fixture, leg by leg: a difference is a stop and a finding, not a tolerance.
    """
    m, params = _run_mod(), load_params()

    def verdicts(clock):
        _cf, e5, cobs, ok = m.run_controls(params, clock=clock)
        assert ok, e5.reason
        out = {}
        for o in cobs:
            p = o.parsed or {}
            if "fixture" in p:
                out[p["fixture"]] = dict(p["verdicts"])
        return out, e5.verdict

    virtual, v_e5 = verdicts(VirtualClock())
    real, r_e5 = verdicts(RealClock())

    assert set(virtual) == set(real) == set(MODES), (sorted(virtual), sorted(real))
    differences = [f"{fx}:{leg} virtual={virtual[fx][leg]} real={real[fx].get(leg)}"
                   for fx in sorted(virtual) for leg in sorted(virtual[fx])
                   if virtual[fx][leg] != real[fx].get(leg)]
    assert not differences, (
        "the control gate disagrees between the virtual and real clocks, which means "
        f"something in the harness reads wall time: {differences}")
    assert v_e5 == r_e5 == "pass"
