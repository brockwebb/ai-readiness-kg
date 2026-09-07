"""D1 v2 — a recognised licence from any of the three sources the signal names.

`v1` deviated: the signal says "read the licence from schema.org/DCAT markup, an HTTP Link
header, and the API's terms endpoint" and `v1` read only the markup. A surface declaring its
licence solely via `Link: <...>; rel="license"` (RFC 8288) was failed as having no licence
field at all.

Overlaps F-UJI's FsF-R1.1-01M, which this rule would cross-check if F-UJI were wired; it is
not (see `params.fuji`), so the cross-check stays deferred and named rather than faked.
"""
from __future__ import annotations
import json as _json
from . import _common as c

RULE_ID, LEG = "RULE-D1-v2", "D1"


def _recognised(blob: str, p: dict):
    for pref in p["recognised_prefixes"]:
        if pref in blob:
            return f"a recognised identifier ({pref}…)"
    upper = blob.upper()
    for tok in p["recognised_tokens"]:
        if tok in upper:
            return f"the recognised token {tok}"
    return None


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["d1_licence"]
    free_text_at = None
    for o in obs:
        parsed = o.parsed or {}
        # Source 1 — markup.
        keys = set(parsed.get("keys") or [])
        if keys & set(p["markup_fields"]):
            blob = _json.dumps(parsed.get("raw") or {})
            how = _recognised(blob, p)
            if how:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"markup licence field carries {how}", params)
            free_text_at = free_text_at or f"the markup licence field on {o.target_url}"
        # Source 2 — RFC 8288 Link header.
        lh = parsed.get("licence_link_header") or []
        for hit in lh:
            how = _recognised(hit["url"], p)
            if how:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"HTTP Link header rel={hit['rel']} points at {how}: "
                              f"{hit['url']}", params)
            free_text_at = free_text_at or f"the Link header rel={hit['rel']}"
        # Source 3 — the terms endpoint.
        if parsed.get("probe") == "terms" and (o.response or {}).get("status", 999) < 400:
            how = _recognised(parsed.get("terms_text") or "", p)
            if how:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"the terms endpoint {o.target_url} states {how}", params)
            free_text_at = free_text_at or f"the terms endpoint {o.target_url}"
    if free_text_at:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a licence statement is present at {free_text_at} but its value is "
                      f"free text, not a recognised identifier", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no licence in the product page's markup, in an HTTP Link header, or at a "
                  "probed terms endpoint", params)
