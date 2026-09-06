"""A11 declared leg — the DECLARED layer of the three-layer crawler-access comparison.

The enforced and observed layers need edge/WAF logs and are `agency_instrumented`; only the
declared layer is public-tier, which is why this rule exists and A11 as a whole does not.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A11-declared-v1", "A11-declared"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the declared layer could not be observed: {obs[0].error_class}", params)
    parsed = obs[0].parsed or {}
    if not parsed.get("present"):
        return c.make(RULE_ID, LEG, obs, "fail",
                      "nothing is DECLARED: no robots.txt is served, so the declared layer of "
                      "the A11 triad is empty", params)
    per_ua = parsed.get("per_ua") or {}
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"a declared policy exists and resolves for all {len(per_ua)} AI-crawler "
                  f"user agents; enforced and observed layers require edge logs "
                  f"(agency_instrumented)", params)
