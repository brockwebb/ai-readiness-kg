"""The parameter set a stored artifact was MADE under, recovered from git by hash.

Factored out of `tests/test_scan_harness_v4.py`, where it was written for the re-derivation
gate, because it is the answer to a question that keeps coming up in other tests too: **what
does this stored artifact get compared against?**

The wrong answer is `load_params()`. Today's instrument is not the instrument a cycle was
measured under, and a test that compares a stored payload to today's leg list is a test that
goes red the first time the instrument legitimately changes — which is exactly what
`cc_tasks/2026-09-15_g1d_leaves_l0.md` did to three of them. DD-052 §3 and DD-064 §2 are the
standing rule: a stored payload is judged under the params it was made under, and those are
recovered, never reconstructed by hand.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PARAMS_REL = "assessment/harness/scan/params.yaml"


def params_hash(params: dict) -> str:
    """The same digest the harness stamps on every Observation and Finding."""
    import sys
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan.model import params_hash as _ph                       # noqa: PLC0415
    return _ph(params)


def params_for(payload: dict) -> dict:
    """The parameter set this artifact was measured under, recovered from git BY HASH.

    Never reconstructed by hand: an approximation of an old parameter set makes a gate pass for
    the wrong reason.

    **A cycle may have run under an OVERLAY, and then the base is what git holds.** The self
    cycle ran under the committed `params.yaml` with its cycle identity replaced in memory, so
    such a payload records both halves — `base_params_hash`, which IS a commit of the file, and
    `params_overlay`, the exact change. The recovery is the same discipline with one more step,
    and it REFUSES unless the rebuilt set hashes to what the artifact carries.
    """
    want = payload["params_hash"]
    overlay = payload.get("params_overlay") or {}
    base_want = payload.get("base_params_hash") or want

    def rebuilt(base: dict) -> dict:
        out = {**base, **overlay}
        assert params_hash(out) == want, (
            f"{payload.get('cycle')}: base_params_hash + params_overlay hashes to "
            f"{params_hash(out)[:12]}…, not the artifact's own {want[:12]}…")
        return out

    revs = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_REL],
                          capture_output=True, text=True, cwd=str(REPO)).stdout.split()
    for rev in revs:
        txt = subprocess.run(["git", "show", f"{rev}:{PARAMS_REL}"],
                             capture_output=True, text=True, cwd=str(REPO)).stdout
        if txt.strip() and params_hash(yaml.safe_load(txt)) == base_want:
            return rebuilt(yaml.safe_load(txt))
    import sys
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import load_params                                    # noqa: PLC0415
    if params_hash(load_params()) == base_want:
        return rebuilt(load_params())
    raise AssertionError(
        f"no commit of {PARAMS_REL} hashes to {base_want[:12]}…; the parameters this artifact "
        f"was made under are not recoverable, so it can never be re-judged")


def tier0_legs_of(artifact: dict) -> list:
    """The tier-0 leg list AS OF the artifact, recovered the same way.

    This is the reference a stored matrix, payload or self row is entitled to be compared
    against. `load_params()['tier0']['legs']` is the reference for what the instrument does
    NEXT, and confusing the two is how a withdrawal (DD-066) reads as a regression.
    """
    return list(params_for(artifact)["tier0"]["legs"])
