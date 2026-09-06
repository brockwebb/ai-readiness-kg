"""A4 — crawler/agent access: robots.txt permits retrieval for the AI-crawler UA list."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A4-v1", "A4"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt could not be observed: {obs[0].error_class}", params)
    parsed = obs[0].parsed or {}
    per_ua = parsed.get("per_ua") or {}
    if not parsed.get("present"):
        # No robots.txt is not a disallow: RFC 9309 says absence permits. But it also means
        # the agency has declared nothing, which A4 asks about — so this is a FAIL on the
        # declaration, with the reason naming why.
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no robots.txt served; retrieval is permitted by default but nothing "
                      "is declared for AI crawlers", params)
    blocked = sorted(ua for ua, ok in per_ua.items() if not ok)
    if blocked:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt disallows the product path for {', '.join(blocked)}", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"robots.txt allows the product path for all {len(per_ua)} AI-crawler "
                  f"user agents", params)
