"""The scan harness's clock, injected rather than patched. **Pure: no network, no I/O.**

Task `cc_tasks/2026-09-10_virtual_time.md` decision 1.

**The problem.** Ten tests were 91% of the suite's wall clock
(`cc_tasks/2026-09-09_guards_earn_their_keep_RESULT.md` §4), and every one of them is a loopback
control cycle sitting in `time.sleep` waiting for a rate limiter that exists to be polite to
federal hosts. Politeness is owed to `www.census.gov`. It is not owed to `127.0.0.1`, and the
suite was paying it anyway, one second at a time, several thousand times.

**The pattern, and it is not ours.** Virtual-time scheduling: Twisted's `twisted.internet.task
.Clock` and RxJS's `TestScheduler` both hand the code under test a clock object whose `advance`
moves time forward, so a test can exercise a scheduler's behaviour in microseconds without
changing what the scheduler does. The rule both share, and the one that matters here, is
**advance time when someone waits on it** — a virtual `sleep` is not a no-op, it is a jump
forward that the clock records.

**Why not monkeypatch `time.sleep`.** Because it destroys the evidence. A patched-out `sleep`
makes a limiter that never asked to wait indistinguishable from one that asked and was ignored,
and "the limiter asked for the right gaps" is precisely the property the real sleeps were
implicitly guaranteeing. Under an injected clock the request is recorded and can be asserted;
under a global patch there is nothing to assert.

**What this clock is and is not.** It is a MONOTONIC scheduling clock: `now()` for measuring
intervals, `sleep()` for yielding one. It is deliberately **not** a wall clock. `Observation
.captured_at` and the evidence-guard redirect log keep `datetime.now(timezone.utc)`, because a
virtual timestamp on a stored record would be a false statement about when a thing was
observed, and no amount of test speed is worth that. The §1 lint scopes itself the same way:
`time.sleep`, `time.time`, `time.monotonic`.

**Production cannot reach the virtual one.** `run.py::main` takes no clock argument, so a real
cycle against real hosts is structurally incapable of running unthrottled.
"""
from __future__ import annotations

import time


class RealClock:
    """Wall behaviour: the monotonic clock and a real sleep. The default everywhere."""

    virtual = False

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)


class VirtualClock:
    """Time advances only when something waits on it, and every wait is recorded.

    `sleep(s)` jumps `now()` forward by `s` and appends `s` to `waits`. Nothing is skipped and
    nothing is pretended: a caller that asked for a one-second gap gets a one-second gap, in
    virtual seconds, and the ledger says it asked.

    Real I/O still takes real time — the fixture servers are real sockets — but virtual time
    does not advance for it, so an `elapsed_ms` measured under this clock is the SCHEDULED
    duration and not the observed one. That is sound for control fixtures, whose payloads are
    never a measurement of a host, and it is another reason production never sees this clock.
    """

    virtual = True

    def __init__(self, start: float = 0.0) -> None:
        self._now = float(start)
        #: Every wait this clock was asked for, in order, in seconds.
        self.waits: list = []

    def now(self) -> float:
        return self._now

    def sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        self.waits.append(float(seconds))
        self._now += float(seconds)

    def advance(self, seconds: float) -> None:
        """Move time forward without recording a wait — for a test that wants to simulate
        elapsed real time between calls rather than a scheduled pause."""
        self._now += float(seconds)

    @property
    def slept(self) -> float:
        """Total virtual seconds yielded. What the real clock would have cost."""
        return sum(self.waits)


#: The default. Named once so every caller shares one instance rather than minting clocks.
REAL = RealClock()
