"""A2 — programmatic access: a documented public API with a machine-readable description."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A2-v1", "A2"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every probe failed: {obs[0].error_class}", params)
    for o in obs:
        st = (o.response or {}).get("status")
        ct = ((o.parsed or {}).get("content_type") or "")
        if st and st < 400 and ct.startswith("application/json"):
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"machine-readable API description served at {o.target_url} "
                          f"({ct}, HTTP {st})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no OpenAPI/JSON API description served at any probed path", params)
