"""D4 — no dark data: the product is enumerable from a public catalog."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-D4-v1", "D4"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog could not be observed: {obs[0].error_class}", params)
    for o in obs:
        p = o.parsed or {}
        if p.get("present") and p.get("contains_product"):
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"the product appears in {o.target_url} "
                          f"({p.get('dataset_count')} datasets, "
                          f"{p.get('complete_entries')} with all required fields)", params)
    served = [o.target_url for o in obs if (o.parsed or {}).get("present")]
    if served:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a catalog is served at {served[0]} but the product is not in it",
                      params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no public data.json catalog served on this host", params)
