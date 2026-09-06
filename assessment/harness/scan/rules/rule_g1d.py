"""G1-D declared leg — error measures present as STRUCTURED FIELDS beside the estimates.

The frozen `g1_declared` probe (DD-036) is the instrument of record for this leg and is NOT
edited by this task. This rule reads the same signal off a scan Observation so the leg can
participate in a scan cycle; where the two disagree the frozen probe governs, and that
comparison is the harness task's, not this one's.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-G1-D-v1", "G1-D"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    tokens = [t.lower() for t in params["g1d_uncertainty"]["field_tokens"]]
    for o in obs:
        body_note = (o.parsed or {}).get("uncertainty_tokens")
        if body_note:
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"error-measure field(s) present on the surface: "
                          f"{', '.join(body_note[:3])}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"none of the {len(tokens)} error-measure field tokens appears as a "
                  f"structured field on the surface", params)
