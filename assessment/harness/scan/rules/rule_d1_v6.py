"""D1 v6 — the API's terms are looked for where they are recorded, and only when an API exists.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1.
D1 is an existence leg for its third source: the API's terms (spec:D1, "the API's terms
endpoint"), applicable when an API exists. `RULE-D1-v5` probed guessed terms paths on the product
host (`d1_sources.terms_paths`, three of seven) beside the declared terms endpoint, and its search
for the endpoint was "declared and probed" or `error`. A guessed path is what a machine tries when
nobody told it where to look: discoverability's question (`rule_a13.py`).

**What v6 decides differently, and only this.**

* The terms source reads only the Observations at the RECORDED terms location
  (`api_base.terms_url`, read from the body's pages or seeded; `_existence.recorded_only`).
  Markup and the RFC 8288 Link header are read as before: both are on the product page itself.
* The absence branches are reached as `fail` only when the record settles the terms source: an
  API is recorded, its terms location is recorded and was observed, or every seed source was
  searched for the terms; or no API is recorded and every seed source was searched for one, in
  which case there are no API terms to read and the verdict rests on the other two sources.
  Otherwise `error`, naming what was not settled (`_existence.remainder`).

How a licence is recognised (visible text, word boundaries, the `license` link type), the
truncated-read rule and every reason fragment are v5's. `RULE-D1-v5` stays in `REGISTRY`,
unedited.
"""
from __future__ import annotations
import json as _json
from . import _common as c
from . import _existence as ex
from . import _scope as s
from . import _text as t

RULE_ID, LEG = "RULE-D1-v6", "D1"

#: A `fail` says no recognised licence identifier is published: an absence claim.
CLAIM = "absence"


def _recognised(text: str, p: dict, urls: list | None = None):
    """How a recognised licence is stated in `text` (and, for the terms page, in its
    `license`-typed links), or None."""
    for u in urls or []:
        for pref in p["recognised_prefixes"]:
            if u.startswith(pref):
                return f"a `license` link to a recognised identifier ({u})"
    for pref in p["recognised_prefixes"]:
        if pref in text:
            return f"a recognised identifier ({pref}…)"
    for tok in p["recognised_tokens"]:
        m = t.find_token(text, tok)
        if m:
            return f"the recognised token {m.group(0)}"
    return None


def _truncated(o) -> tuple:
    """`(kept_bytes, body_bytes)` when the stored terms text is shorter than the body served,
    else None."""
    text = (o.parsed or {}).get("terms_text") or ""
    body = (o.response or {}).get("bytes")
    kept = len(text.encode("utf-8"))
    if isinstance(body, int) and kept < body:
        return (kept, body)
    return None


def _terms_remainder(observations: list, decl, params: dict) -> list:
    """What leaves the API-terms source unsettled, or [] when it is settled."""
    if decl is None:
        return ex.remainder(observations, decl, "api_terms", params)
    if not ex.entries(decl, "api_base"):
        # No API recorded: the terms source applies only when an API exists, so it is settled
        # exactly when the search for an API was complete.
        return ex.remainder(observations, decl, "api_base", params)
    return ex.remainder(observations, decl, "api_terms", params)


def judge(observations: list, params: dict):
    every = [o for o in observations if o.leg == LEG]
    if not every:
        return c.empty(RULE_ID, LEG, params)
    decl = ex.declared(every)
    # The page itself (markup, Link header) and the recorded terms location; a guessed terms
    # path is not read unless it IS the recorded location.
    terms_at = ex.recorded_only(every, decl, ("api_terms",), params)
    obs = [o for o in every if (o.parsed or {}).get("probe") != "terms"] + terms_at
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["d1_licence"]
    free_text_at = None
    partial = []
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
        # Source 3 — the terms endpoint, guessed or declared, read as visible text.
        if parsed.get("probe") == "terms" and c.served(o) and not c.unobserved(o, params):
            html = parsed.get("terms_text") or ""
            how = _recognised(t.visible_text(html), p, t.licence_links(html))
            if how:
                return c.make(RULE_ID, LEG, obs, "pass",
                              f"the terms endpoint {o.target_url} states {how}", params)
            cut = _truncated(o)
            if cut:
                partial.append(f"the terms page {o.target_url} was read to {cut[0]} of its "
                               f"{cut[1]} bytes and no recognised identifier is in the visible "
                               f"text of what was read")
            free_text_at = free_text_at or f"the terms endpoint {o.target_url}"
    # Both branches below say no recognised identifier exists among the sources.
    what = "whether the product publishes a machine-readable licence"
    remainder = _terms_remainder(every, decl, params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder + partial)
    if partial:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, partial)
    if free_text_at:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a licence statement is present at {free_text_at} but its value is "
                      f"free text, not a recognised identifier (the recorded API terms "
                      f"source was settled: {ex.search(decl, 'api_terms', params)})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no licence in the product page's markup, in an HTTP Link header, or at a "
                  f"recorded API terms endpoint ({ex.search(decl, 'api_terms', params)})",
                  params)
