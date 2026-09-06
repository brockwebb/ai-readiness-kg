"""F4 — change legibility: a machine-readable changelog per release."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-F4-v1", "F4"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"no changelog path could be probed: {obs[0].error_class}", params)
    ok = params["f4_changelog"]["machine_readable_content_types"]
    for o in obs:
        st = (o.response or {}).get("status")
        ct = ((o.parsed or {}).get("content_type") or "")
        if st and st < 400 and ct in ok:
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"machine-readable changelog at {o.target_url} ({ct})", params)
    human = [o.target_url for o in obs if (o.response or {}).get("status", 999) < 400]
    if human:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a changelog page is served at {human[0]} but not in a "
                      f"machine-readable content type", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no changelog or release-notes endpoint served", params)
