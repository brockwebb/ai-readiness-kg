"""A2 v3 — programmatic access: a machine-readable description that declares its auth model.

`v1` deviated: the spec says "record auth scheme, declared rate limits, and whether the
description is machine-readable" and `v1` implemented only the third, inferring it from a JSON
content type. Any 2xx `application/json` passed, so an API documenting neither its auth model
nor its rate limits was indistinguishable from one documenting both.

The verdict now requires a description that PARSES as an API description. Auth scheme and rate
limits are recorded on every Finding, because the spec says record — it does not say gate —
and inventing a threshold the spec does not state would be the opposite deviation.


**v3 (2026-09-07):** `v2` crashed a live cycle. Its guard was
`(o.response or {}).get("status", 999) < 400`, which looks safe and is not: `status` is always
PRESENT on an Observation and holds `None` whenever nothing was fetched — a robots disallow, a
DNS failure, a timeout — so `.get` returns `None` rather than the default and the comparison
raises `TypeError: '<' not supported between instances of 'NoneType' and 'int'`. A default
fires on a MISSING key, never on a present one holding `None`. It stopped the 2026-09-07 cycle
dead on `scan-eia-flagship-1-open-data`, whose links include paths `eia.gov/robots.txt`
disallows for this UA. Four `v2` modules carried the identical bug; the guard is now
`_common.served()`, named once rather than duplicated in four places. `v2` is untouched and
stays in `REGISTRY` — no Finding recorded under it is re-scored.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A2-v3", "A2"


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
                if c.served(o)
                and not ((o.parsed or {}).get("api") or {}).get("openapi_parsed")]
    if unparsed:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a document is served at {unparsed[0]} but it does not parse as an API "
                      f"description; a JSON content type alone is not a description", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no OpenAPI/JSON API description served at any probed path", params)
