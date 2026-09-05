"""The dispatch loop's blast radius on a systemic failure (Issue `830330b4`, task
`cc_tasks/2026-09-04_extract_g1eval_17_and_rerun_ADDENDUM-01.md` §2).

The g1eval extraction billed 286 calls / 15,073,098 tokens — 32.5% of the run — for output
that was thrown away, because `phase_extract` submitted every future up front and then called
`cancel()` on the remainder when the failure streak tripped. `cancel()` cannot stop a future
that has already started, so those calls ran, reserved, invoked the model and settled, while
the loop's `continue` skipped collecting their exceptions: 5 FAILED lines were printed for 286
failures. These tests pin both halves — the bound on extra calls, and the completeness of the
failure count.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import chunked_pilot as cp  # noqa: E402


class _Chunk:
    def __init__(self, i):
        self.chunk_id = f"doc#c{i:04d}"


def _todo(n):
    return [("doc", _Chunk(i), "sha", "title") for i in range(n)]


def _failing_from(n, calls):
    """Succeeds for the first `n` calls, then fails for every call after — the shape of a
    session limit reaching the subprocesses, which is what actually happened."""
    def run_one(d, c, sha, title):
        calls.append(c.chunk_id)
        if len(calls) > n:
            raise RuntimeError("claude -p exited 1")
        return "ok"
    return run_one


@pytest.mark.parametrize("workers", [1, 2, 8])
def test_at_most_one_wave_is_billed_after_the_streak_trips(workers):
    calls = []
    done, failures, _, streak = cp.dispatch_waves(
        _todo(400), workers, _failing_from(10, calls), stop_after=5)

    assert streak >= 5, "the systemic-failure guard must still fire"
    assert done == 10
    # 10 successes + the 5 failures that trip the streak + at most the rest of that wave.
    # The pre-fix loop ran all 400.
    assert len(calls) <= 10 + 5 + (workers - 1), (
        f"{len(calls)} calls billed with {workers} workers; the guard is supposed to bound "
        f"this to the wave in flight, not the whole worklist")
    assert len(calls) < 400


def test_every_dispatched_failure_is_counted_not_skipped():
    """The failure count is what the operator reads to know what a run cost. Under the old
    loop it undercounted by 281."""
    calls = []
    _, failures, _, _ = cp.dispatch_waves(_todo(400), 8, _failing_from(10, calls), stop_after=5)

    billed_failures = len(calls) - 10
    assert len(failures) == billed_failures, (
        f"{billed_failures} calls failed after being dispatched but only {len(failures)} were "
        f"recorded; every settled error must appear in the log")
    assert all("claude -p exited 1" in why for _, why in failures)


def test_a_clean_run_dispatches_everything():
    calls = []
    done, failures, _, streak = cp.dispatch_waves(
        _todo(37), 8, _failing_from(10**6, calls), stop_after=5)
    assert (done, len(failures), streak) == (37, 0, 0)
    assert len(calls) == 37


def test_an_isolated_failure_does_not_stop_the_pass():
    """A single bad chunk must not discard a pass whose other calls are already paid for."""
    seen = []

    def run_one(d, c, sha, title):
        seen.append(c.chunk_id)
        if c.chunk_id == "doc#c0003":
            raise RuntimeError("one bad chunk")
        return "ok"

    done, failures, _, streak = cp.dispatch_waves(_todo(20), 4, run_one, stop_after=5)
    assert (done, len(failures), streak) == (19, 1, 0)
    assert len(seen) == 20


def test_a_spend_refusal_propagates_rather_than_counting_as_a_failure():
    """`SpendRefusalStop` is a clean exit (DD-022), not a chunk failure: swallowing it would
    let a pass keep dispatching against an exhausted ceiling."""
    refusal = cp.spend.Refusal(run_id="r", estimate_tokens=20_000, committed_tokens=69_000_000,
                               ceiling_tokens=69_000_000, scope="run", reason="over_ceiling")

    def run_one(d, c, sha, title):
        raise cp.spend.SpendRefusalStop(refusal)

    with pytest.raises(cp.spend.SpendRefusalStop):
        cp.dispatch_waves(_todo(20), 4, run_one, stop_after=5)
