"""A2 v4 — "no documented API" is reached only at the documented API base.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4, DN-012 d1 and d3, audit C-14.
spec:A2 says GET "the documented API base". The collector probed three guessed paths on the
surface's host (`/openapi.json`, `/swagger.json`, `/api/openapi.json`), so `v3` failed the ACS
flagship with *"no OpenAPI/JSON API description served at any probed path"*.
`docs/brief/G_census_dogfood.md` then prescribed "Expose the product through an API", while
this repository's own `docs/data/sources_per_check.json:237` cites the Census Data API for ACS.

**What v4 decides differently.**

* `pass` is unchanged. A description that parses, served at any path, guessed or declared, is a
  documented API whatever else was or was not probed.
* With nothing found, the body's `declared` block (`targets.yaml` `declared_locations`, recorded
  on the Observations by the collector or by `scan/reread.py`) decides between three cases:
  - no `api_base` declared: `error`, "no documented API base declared for this body; guessed
    paths do not establish absence";
  - an `api_base` declared and no Observation targets it: `error`, "documented API base
    declared and not probed";
  - the declared base probed: `fail` is reached here and only here, over the base. A blind
    probe of the base is still `error` (`_common.absence_verdict`).

`RULE-A2-v3` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-A2-v4", "A2"

#: A `fail` says the product has no machine-readable API description: an absence claim.
CLAIM = "absence"


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
    # Nothing parsed anywhere. Every branch below is an absence claim, and it may only be made
    # over the documented base.
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
    unparsed = [o.target_url for o in at_base
                if c.served(o)
                and not ((o.parsed or {}).get("api") or {}).get("openapi_parsed")]
    if unparsed:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a document is served at {unparsed[0]} but it does not parse as an API "
                      f"description; a JSON content type alone is not a description (the "
                      f"declared API base was probed)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no OpenAPI/JSON API description served at any probed path, the declared "
                  f"API base {base} included", params)
