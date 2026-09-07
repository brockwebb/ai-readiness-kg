"""A11-declared v2 — both declared-layer sources, and the per-UA verdicts actually read.

`v1` deviated twice: the signal names "robots.txt **and** meta-robots directives" and `v1`
branched only on whether a robots.txt was served, so a product page carrying
`<meta name="robots" content="noindex,nofollow">` under a permissive robots.txt passed; and
the pass branch used `per_ua` only for its LENGTH, never inspecting the verdicts that
`evidence_kind` calls for, so a robots.txt disallowing every AI crawler also passed.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A11-declared-v2", "A11-declared"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the declared layer could not be observed: {obs[0].error_class}", params)
    robots = next((o for o in obs if "present" in (o.parsed or {})), obs[0])
    parsed = robots.parsed or {}
    meta = next(((o.parsed or {}).get("meta") for o in obs if (o.parsed or {}).get("meta")),
                None) or {}
    if not parsed.get("present"):
        return c.make(RULE_ID, LEG, obs, "fail",
                      "nothing is DECLARED: no robots.txt is served, so the declared layer of "
                      "the A11 triad is empty", params)
    per_ua = parsed.get("per_ua") or {}
    disallowed = sorted(ua for ua, ok in per_ua.items() if ok is False)
    if disallowed:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt DISALLOWS the product path for {len(disallowed)} of "
                      f"{len(per_ua)} AI-crawler user agents: {', '.join(disallowed[:4])}",
                      params)
    if meta.get("meta_restricts"):
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt permits every AI crawler but the product page's meta-robots "
                      f"directives restrict it ({', '.join(meta['meta_restricting_tokens'])}); "
                      f"the declared layer has two sources and they disagree", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"both declared-layer sources permit: robots.txt allows all {len(per_ua)} "
                  f"AI-crawler user agents and the page declares no restricting meta-robots "
                  f"directive. Enforced and observed layers require edge logs "
                  f"(agency_instrumented)", params)
