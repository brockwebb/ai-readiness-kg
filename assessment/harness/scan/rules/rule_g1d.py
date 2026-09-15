"""G1-D declared leg — error measures present as STRUCTURED FIELDS beside the estimates.

The frozen `g1_declared` probe (DD-036) is the instrument of record for this leg and is NOT
edited by this task. This rule reads the same signal off a scan Observation so the leg can
participate in a scan cycle; where the two disagree the frozen probe governs, and that
comparison is the harness task's, not this one's.

**Not dispatched on host-level surfaces, from cycle 5 forward (DD-066).** The rule is
unchanged and is still dispatched on PRODUCT surfaces, where it passes. What was withdrawn is
the LEVEL: a host's `home` page carries no estimate, so this rule's `fail` there says the
surface has no uncertainty fields beside estimates it does not have — 126 fail and 28 error
across every body and every reference host in cycles 1 to 4 and the self cycle, and not one
pass, against 104 passes on product surfaces in the same runs. The construct is "uncertainty
present for the human reader and absent from the markup", and it is a property of a data
product. `params.tier0.legs_withdrawn` is the declaration; `run.withdrawn_on` reads it.
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
