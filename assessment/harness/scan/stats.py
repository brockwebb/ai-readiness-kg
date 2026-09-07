"""Interval arithmetic for the scan harness. **One implementation, delegated.**

`cc_tasks/2026-09-07_eda_and_charts.md` §1 asks for `wilson(k, n, z)` here. It does not ask
for a second Wilson score interval, and this repo already has one: `harness/rollup.py`
computes the G1 preservation intervals with it, `assessment/tests/test_rollup.py` pins it to
the burn-close arithmetic, and `state/scan_matrix_2026-09-07.json` was written by it. A second
copy of a formula is a second thing to be wrong, and the failure mode is silent — two figures
that disagree in the third decimal and no way to say which is the instrument.

So this is a delegate. `Z` is asserted equal to `rollup`'s own constant by
`tests/test_scan_figures.py`, so the two cannot drift apart without a red test.

**Prior art.** Wilson (1927, *JASA* 22:209). Brown, Cai & DasGupta (2001, *Statist. Sci.*
16:101) and Newcombe (1998, *Stat. Med.* 17:857) both recommend the score interval over Wald
at small n and at 0 or n successes — which is this cycle's whole situation: eight of fifteen
legs sit at 0/23, where the Wald interval is [0, 0] and says nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

#: `assessment/`, so `harness.rollup` imports. The scan package is loaded with
#: `assessment/harness` on the path (it is the top-level `scan`), so a relative import cannot
#: reach its own grandparent.
_ASSESSMENT = Path(__file__).resolve().parents[2]
if str(_ASSESSMENT) not in sys.path:
    sys.path.insert(0, str(_ASSESSMENT))

from harness.rollup import wilson_interval as _wilson_interval    # noqa: E402

#: Two-sided 95 %. Named here because callers pass it explicitly and a figure that prints an
#: interval has to be able to say which one it printed.
Z = 1.959964


def wilson(k: int, n: int, z: float = Z):
    """Wilson score interval `(lo, hi)` for k successes in n trials; `(None, None)` at n = 0.

    Values are rounded to six decimals by `rollup.wilson_interval`, which is what
    `scan_matrix_2026-09-07.json` already holds — so a figure drawn from this function and a
    number read from that file are the same number, not two roundings of one.
    """
    return _wilson_interval(k, n, z)
