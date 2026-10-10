"""A2 v5 — an API description is a document that says it is one: `openapi` or `swagger`.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 1, from
`cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md` §2. `RULE-A2-v4` passed on
`parsed.api.openapi_parsed`, which `collectors/v2clauses.api_declarations` sets for ANY JSON
object. The declared Census base `https://api.census.gov/data` serves a `dcat:Catalog` (Project
Open Data v1.1: the API's catalog of datasets), so four Census surfaces passed as "machine-readable
API description (OpenAPI unversioned)" and the recollection's composite withheld the leg.

**What a description is.** The OpenAPI Specification 3.x makes the top-level `openapi` field
REQUIRED ("This string MUST be the version number of the OpenAPI Specification that the OpenAPI
document uses", OAS 3.1.0 §4.8.1); Swagger 2.0 makes `swagger` REQUIRED with the value `"2.0"`.
The collector records whichever is present as `openapi_version`. v5 passes only on a document
carrying one of them with a version-shaped value (`2.0`, or `3.<minor>[.<patch>]`).

**A JSON document at the base that is not a description** is a finding about the product, not a
pass: the API is present and its description is not published at the base. That is v4's
"does not parse as an API description" outcome, so the prescription it maps to ("Serve a parseable
OpenAPI description where the API is documented") is the one shown. Every other branch and every
reason fragment `scripts/tag_prescriptions.py` keys on is v4's. `RULE-A2-v4` stays in `REGISTRY`,
unedited.
"""
from __future__ import annotations
import re
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-A2-v5", "A2"

#: A `fail` says the product has no machine-readable API description: an absence claim.
CLAIM = "absence"

#: `swagger: "2.0"` (Swagger 2.0) or `openapi: "3.x[.y]"` (OAS 3.x). The collector puts either
#: field's value in `openapi_version`.
_DESCRIPTION_VERSION = re.compile(r"^(2\.0|3\.\d+(\.\d+)?)$")


def is_description(api: dict) -> bool:
    v = (api or {}).get("openapi_version")
    return bool((api or {}).get("openapi_parsed")) and isinstance(v, str) \
        and bool(_DESCRIPTION_VERSION.match(v.strip()))


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every probe failed: {obs[0].error_class}", params)
    for o in obs:
        d = (o.parsed or {}).get("api") or {}
        if not (c.served(o) and is_description(d)):
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
    # Nothing that is a description anywhere. Every branch below is an absence claim, and it
    # may only be made over the documented base.
    what = "whether the product has a machine-readable API description"
    remainder, at_base = s.api_scope(obs, s.declared(obs))
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder)
    blind = [o for o in at_base if c.unobserved(o, params)]
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=at_base, blind=blind,
                              found=None, what=what)
    if scope is not None:
        return scope
    base = at_base[0].target_url
    served = [o for o in at_base if c.served(o)]
    json_not_description = [o for o in served
                            if ((o.parsed or {}).get("api") or {}).get("openapi_parsed")]
    if json_not_description:
        o = json_not_description[0]
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the API is present: a JSON document is served at the declared API base "
                      f"{o.target_url}; but it does not parse as an API description: it carries "
                      f"neither the `openapi` field (OpenAPI 3.x) nor the `swagger` field "
                      f"(Swagger 2.0), so no description is published at the base", params)
    if served:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a document is served at {served[0].target_url} but it does not parse as "
                      f"an API description; a JSON content type alone is not a description (the "
                      f"declared API base was probed)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no OpenAPI/JSON API description served at any probed path, the declared "
                  f"API base {base} included", params)
