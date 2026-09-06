"""E5 — positive controls: the harness's own cycle validity gate.

The framework recorded E5's collector as `none_known` because a seeded canary is a property of
the harness's own cycle, not an observation of an external surface. §4 turns that into
something real: the control fixtures ARE the canaries. A cycle in which either fixture produced
an unexpected verdict is INVALID (DD-019 decoy discipline), and this rule is what says so.

It is the one rule whose observations are Findings — it judges the cycle, not a surface.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-E5-v1", "E5"


def judge(observations: list, params: dict):
    """`observations` here carries one Observation per control fixture whose `parsed` holds
    `{fixture, expected, unexpected: [...]}` — built by `run.py` from the control Findings."""
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    fired, bad = [], []
    for o in obs:
        p = o.parsed or {}
        fired.append(p.get("fixture"))
        bad += [f"{p.get('fixture')}:{u}" for u in (p.get("unexpected") or [])]
    expected_fixtures = sorted(params["e5_control"]["expected_verdicts"])
    if sorted(x for x in fired if x) != expected_fixtures:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a cycle with zero fired controls is INVALID: expected "
                      f"{expected_fixtures}, fired {sorted(x for x in fired if x)}", params)
    if bad:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(bad)} control verdict(s) were not as expected: "
                      f"{', '.join(bad[:6])}", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"both control fixtures fired and every rule returned its expected verdict",
                  params)
