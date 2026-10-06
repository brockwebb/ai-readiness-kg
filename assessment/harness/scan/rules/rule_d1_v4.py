"""D1 v4 — "no machine-readable licence" is reached only once the API's terms endpoint is read.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 5, from the absence inventory
(`docs/research/2026-10-06_absence_rules_inventory.md` §2). spec:D1 reads the licence from
three sources: "schema.org/DCAT markup, an HTTP Link header, and the API's terms endpoint".
The collector reads the first two, and stands in for the third with `d1_sources.terms_paths`
guessed on the PRODUCT host, of which it probes at most `max_terms_probed` (3 of 7). Both
`fail` branches of `v3` ("free text, not a recognised identifier" and "no licence ... at a
probed terms endpoint") assert that no recognised identifier exists among the sources. Neither
search reached the place spec:D1 names, which is DN-012 d1's second trigger, and the guesses
were capped, which is its first.

**What v4 decides differently.** The `pass` is v3's exactly: a recognised identifier found in
any source stands. The two `fail` branches are reached only when the API's terms endpoint was
declared (`api_base.terms_url`, `targets.yaml` `declared_locations`) and probed
(`_scope.terms_scope`). Otherwise the verdict is `error`, naming what is missing: no API base
declared, no terms endpoint declared for it, or one declared and not probed. No body declares
one yet, so on the cycle of record every D1 absence is `error`. The inventory records that this
is what would unlock it. `RULE-D1-v3` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
import json as _json
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-D1-v4", "D1"

#: A `fail` says no recognised licence identifier is published: an absence claim.
CLAIM = "absence"


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
        # Source 3 — the terms endpoint, guessed or declared.
        if parsed.get("probe") == "terms" and c.served(o):
            how = _recognised(parsed.get("terms_text") or "", p)
            if how:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"the terms endpoint {o.target_url} states {how}", params)
            free_text_at = free_text_at or f"the terms endpoint {o.target_url}"
    # Both branches below say no recognised identifier exists among the sources.
    remainder = s.terms_scope(obs, s.declared(obs))
    terms = [o for o in obs if (o.parsed or {}).get("probe") == "terms"]
    blind = [o for o in terms if c.unobserved(o, params)]
    if remainder:
        guessed = len(params["d1_sources"]["terms_paths"])
        remainder.append(f"{len(terms)} of {guessed} guessed terms path(s) on the product host "
                         f"probed (`d1_sources.max_terms_probed` "
                         f"{params['d1_sources']['max_terms_probed']})")
        return s.remainder_error(RULE_ID, LEG, obs, params,
                                 "whether the product publishes a machine-readable licence",
                                 remainder)
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=terms, blind=blind,
                              found=None,
                              what="whether the product publishes a machine-readable licence")
    if scope is not None:
        return scope
    if free_text_at:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a licence statement is present at {free_text_at} but its value is "
                      f"free text, not a recognised identifier (the declared API terms "
                      f"endpoint was read)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no licence in the product page's markup, in an HTTP Link header, or at a "
                  "probed terms endpoint, the declared API terms endpoint included", params)
