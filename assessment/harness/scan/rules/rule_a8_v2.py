"""A8 v2 — a declared vintage AND a latest-vintage pointer that resolves.

`v1` deviated: the spec has two clauses — read the declared date, and "test whether a
latest-vintage pointer resolves" — and `v1` implemented only the first, so a surface with a
`dateModified` and a broken latest pointer returned `pass`. That is also the second half of
the indicator itself ("latest-vintage pointer resolvable").

The `v1` Last-Modified discipline is kept verbatim: an HTTP header is a fact about a FILE that
almost every web server emits unasked, and the control fixture caught `v1.0` passing on one.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A8-v2", "A8"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["a8_freshness"]
    declared, header_seen, ptr = None, None, {}
    for o in obs:
        keys = set((o.parsed or {}).get("keys") or [])
        hit = sorted(keys & set(p["markup_fields"]))
        if hit and declared is None:
            declared = hit[0]
        hdrs = {k.lower(): v for k, v in ((o.response or {}).get("headers") or {}).items()}
        if hdrs.get("last-modified"):
            header_seen = hdrs["last-modified"]
        if (o.parsed or {}).get("latest"):
            ptr = (o.parsed or {}).get("latest")
    if declared is None:
        if header_seen:
            return c.make(RULE_ID, LEG, obs, "fail",
                          f"only an HTTP Last-Modified header ({header_seen}) — a fact about "
                          f"the file, not a declared product vintage", params)
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no declared release or modification date on the surface", params)
    if not ptr.get("pointers_found"):
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"markup declares the vintage via {declared}, but the surface offers no "
                      f"latest-vintage pointer, which the indicator also requires", params)
    if not ptr.get("latest_pointer_resolves"):
        tried = ptr.get("pointers_tried") or []
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"markup declares the vintage via {declared}, but none of the "
                      f"{len(tried)} latest-vintage pointer(s) resolves "
                      f"(first: {tried[0]['url']} -> HTTP {tried[0].get('status')})", params)
    good = next(t for t in ptr["pointers_tried"] if t["resolved"])
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"markup declares the vintage via {declared} and the latest-vintage pointer "
                  f"resolves ({good['url']} -> HTTP {good['status']}, found by {good['how']})",
                  params)
