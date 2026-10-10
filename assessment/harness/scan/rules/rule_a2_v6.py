"""A2 v6 — the API is looked for where it is recorded; a guessed path is discoverability's.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1.
A2 is an existence leg: does the body publish a documented API? `RULE-A2-v5` read three guessed
paths on the product host (`/openapi.json`, `/swagger.json`, `/api/openapi.json`) beside the
declared base, so a description guessed at could pass and the guesses entered the search. What a
machine finds without being told where to look is the discoverability indicator's question
(`rule_a13.py`, RFC 9727's `/.well-known/api-catalog` among its convention locations).

**What v6 decides differently, and only this.** It judges the Observations at the RECORDED API
base and its description (`targets.yaml` `declared_locations` `api_base`, read from the body's
pages or seeded; `_existence.recorded_only`). Its absence branches are reached as `fail` only
when every recorded location was observed and every seed source was searched for the body's API
(`_existence.remainder`); otherwise `error`, naming the location not verified or the sources not
searched. What a description IS, and every reason fragment, are v5's: a document carrying
`openapi` or `swagger`. `RULE-A2-v5` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _existence as ex
from . import _scope as s
from .rule_a2_v5 import is_description

RULE_ID, LEG = "RULE-A2-v6", "A2"

#: A `fail` says the product has no machine-readable API description: an absence claim.
CLAIM = "absence"


def judge(observations: list, params: dict):
    every = [o for o in observations if o.leg == LEG]
    if not every:
        return c.empty(RULE_ID, LEG, params)
    decl = ex.declared(every)
    recorded = ex.recorded_only(every, decl, ("api_base",), params)
    obs = recorded or every
    if recorded and c.only_errors(recorded, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every probe failed: {obs[0].error_class}", params)
    for o in recorded:
        d = (o.parsed or {}).get("api") or {}
        if not (c.served(o) and not c.unobserved(o, params) and is_description(d)):
            continue
        auth = d.get("auth_schemes_declared") or d.get("auth_headers_seen") or []
        rate = (d.get("rate_limit_headers_seen") or [])
        rate_desc = d.get("rate_limit_declared_in_description")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"machine-readable API description at {o.target_url} "
                      f"(OpenAPI {d.get('openapi_version')}); "
                      f"auth scheme {auth or 'NOT DECLARED'}; "
                      f"rate limits {'declared' if (rate or rate_desc) else 'NOT DECLARED'}",
                      params)
    what = "whether the product has a machine-readable API description"
    remainder = ex.remainder(every, decl, "api_base", params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder)
    served = [o for o in recorded if c.served(o)]
    json_not_description = [o for o in served
                            if ((o.parsed or {}).get("api") or {}).get("openapi_parsed")]
    if json_not_description:
        o = json_not_description[0]
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the API is present: a JSON document is served at the declared API base "
                      f"{o.target_url}; but it does not parse as an API description: it carries "
                      f"neither the `openapi` field (OpenAPI 3.x) nor the `swagger` field "
                      f"(Swagger 2.0), so no description is published at the base "
                      f"({ex.search(decl, 'api_base', params)})", params)
    if served:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a document is served at {served[0].target_url} but it does not parse as "
                      f"an API description; a JSON content type alone is not a description "
                      f"({ex.search(decl, 'api_base', params)})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no OpenAPI/JSON API description served at any probed path: "
                  f"{ex.search(decl, 'api_base', params)}", params)
