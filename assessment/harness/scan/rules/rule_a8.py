"""A8 — timeliness of surface: a machine-readable release/modification date."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A8-v1", "A8"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["a8_freshness"]
    header_seen = None
    for o in obs:
        # A MARKUP date is the product's declared vintage; an HTTP Last-Modified is a fact
        # about a FILE that almost every web server emits unasked. The control fixture caught
        # this: `fails_all` passed A8 on a transport header alone, which would have scored
        # every ordinary web server as publishing a machine-readable release date.
        keys = set((o.parsed or {}).get("keys") or [])
        hit = sorted(keys & set(p["markup_fields"]))
        if hit:
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"markup declares the product vintage via {hit[0]}", params)
        hdrs = {k.lower(): v for k, v in ((o.response or {}).get("headers") or {}).items()}
        if hdrs.get("last-modified"):
            header_seen = hdrs["last-modified"]
    if header_seen:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"only an HTTP Last-Modified header ({header_seen}) — a fact about the "
                      f"file, not a declared product vintage; no dateModified in the markup",
                      params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no declared release or modification date on the surface", params)
