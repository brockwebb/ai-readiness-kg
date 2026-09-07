"""A2 v2 — programmatic access: a machine-readable description that declares its auth model.

`v1` deviated: the spec says "record auth scheme, declared rate limits, and whether the
description is machine-readable" and `v1` implemented only the third, inferring it from a JSON
content type. Any 2xx `application/json` passed, so an API documenting neither its auth model
nor its rate limits was indistinguishable from one documenting both.

The verdict now requires a description that PARSES as an API description. Auth scheme and rate
limits are recorded on every Finding, because the spec says record — it does not say gate —
and inventing a threshold the spec does not state would be the opposite deviation.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A2-v2", "A2"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every probe failed: {obs[0].error_class}", params)
    for o in obs:
        st = (o.response or {}).get("status")
        d = (o.parsed or {}).get("api") or {}
        if not (st and st < 400 and d.get("openapi_parsed")):
            continue
        auth = d.get("auth_schemes_declared") or d.get("auth_headers_seen") or []
        rate = (d.get("rate_limit_headers_seen") or [])
        rate_desc = d.get("rate_limit_declared_in_description")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"machine-readable API description at {o.target_url} "
                      f"(OpenAPI {d.get('openapi_version') or 'unversioned'}); "
                      f"auth scheme {auth or 'NOT DECLARED'}; "
                      f"rate limits {'declared' if (rate or rate_desc) else 'NOT DECLARED'}",
                      params)
    unparsed = [o.target_url for o in obs
                if (o.response or {}).get("status", 999) < 400
                and not ((o.parsed or {}).get("api") or {}).get("openapi_parsed")]
    if unparsed:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a document is served at {unparsed[0]} but it does not parse as an API "
                      f"description; a JSON content type alone is not a description", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no OpenAPI/JSON API description served at any probed path", params)
