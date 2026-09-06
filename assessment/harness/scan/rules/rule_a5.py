"""A5 — discoverability surface: a sitemap covering the product, or an equivalent."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A5-v1", "A5"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"no discovery file could be observed: {obs[0].error_class}", params)
    for o in obs:
        p = o.parsed or {}
        if p.get("kind") == "sitemap" and p.get("present") and p.get("covers_product"):
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"sitemap at {o.target_url} lists the product URL "
                          f"({p.get('url_count')} URLs)", params)
    present = [o.target_url for o in obs if (o.parsed or {}).get("present")]
    if present:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"discovery files served ({', '.join(present[:3])}) but none lists the "
                      f"product URL", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no sitemap, llms.txt or well-known discovery file served", params)
