"""A3 — bulk access: a whole-product download exists and is linked from the product page."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A3-v1", "A3"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    exts = params["a1_formats"]["structured_extensions"]
    for o in obs:
        for link in ((o.parsed or {}).get("links") or [])[:params["crawl"]["max_links_followed"]]:
            href = (link.get("href") or "").lower()
            if any(href.endswith(e) for e in exts):
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"bulk download linked from the product page: {link['href']}",
                              params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no whole-product download linked from the product page", params)
