"""D1 — licence clarity: a recognised, machine-readable licence identifier.

Overlaps F-UJI's FsF-R1.1-01M, which this rule would cross-check if F-UJI were wired; it is
not (see `params.fuji`), so the cross-check is deferred and named rather than faked.
"""
from __future__ import annotations
import json as _json
from . import _common as c

RULE_ID, LEG = "RULE-D1-v1", "D1"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["d1_licence"]
    for o in obs:
        blob = _json.dumps((o.parsed or {}).get("raw") or {})
        keys = set((o.parsed or {}).get("keys") or [])
        if not (keys & set(p["markup_fields"])):
            continue
        for pref in p["recognised_prefixes"]:
            if pref in blob:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"licence field carries a recognised identifier ({pref}…)",
                              params)
        upper = blob.upper()
        for tok in p["recognised_tokens"]:
            if tok in upper:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"licence field carries the recognised token {tok}", params)
        return c.make(RULE_ID, LEG, obs, "fail",
                      "a licence field is present but its value is free text, not a "
                      "recognised identifier", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no licence field in the product page's markup", params)
