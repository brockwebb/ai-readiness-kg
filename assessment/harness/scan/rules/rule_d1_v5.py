"""D1 v5 — a licence token is a word a reader sees, never a substring of the markup.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 1, from
`cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md` §2. `RULE-D1-v4` tests
`tok in blob.upper()` over the terms page's raw HTML. On the declared terms pages of the
recollection it found `CC0` inside a script asset hash on
`https://www.census.gov/data/developers/about/terms-of-service.html` and `MIT` inside "permit"
and "Limit" on `https://www.eia.gov/opendata/terms-of-service.php`. Neither page states a
licence; seven surfaces passed falsely and the recollection's composite withheld the leg.

**What v5 decides differently.**

* **Tokens at word boundaries, in their own case.** Every `recognised_tokens` match, in all three
  sources, goes through `_text.find_token`: `MIT` is not in "permit". A recognised URL prefix is
  still matched as a substring, because a URL is one token.
* **The terms endpoint is read as a reader reads it**: its visible text (`_text.visible_text`;
  scripts, styles and attributes removed), plus the one attribute that IS a licence statement by
  definition, an `href` under the HTML `license` link type (`_text.licence_links`).
* **A truncated read is a partial search.** The collector keeps the first characters of a terms
  page (`terms_text`), not all of it: census.gov's page is 302,319 bytes and its first 20,000
  characters hold 18 characters of visible text. When nothing is recognised in what was kept and
  the page was longer than what was kept, the absence verdict is `error`, naming how much was
  read (DN-012 d1), never `fail`.

Every other branch and every reason fragment `scripts/tag_prescriptions.py` keys on is v4's.
`RULE-D1-v4` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
import json as _json
from . import _common as c
from . import _scope as s
from . import _text as t

RULE_ID, LEG = "RULE-D1-v5", "D1"

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


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
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
        if parsed.get("probe") == "terms" and c.served(o):
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
    remainder = s.terms_scope(obs, s.declared(obs))
    terms = [o for o in obs if (o.parsed or {}).get("probe") == "terms"]
    blind = [o for o in terms if c.unobserved(o, params)]
    if remainder:
        guessed = len(params["d1_sources"]["terms_paths"])
        remainder.append(f"{len(terms)} of {guessed} guessed terms path(s) on the product host "
                         f"probed (`d1_sources.max_terms_probed` "
                         f"{params['d1_sources']['max_terms_probed']})")
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder + partial)
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=terms, blind=blind,
                              found=None, what=what)
    if scope is not None:
        return scope
    if partial:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, partial)
    if free_text_at:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a licence statement is present at {free_text_at} but its value is "
                      f"free text, not a recognised identifier (the declared API terms "
                      f"endpoint was read)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no licence in the product page's markup, in an HTTP Link header, or at a "
                  "probed terms endpoint, the declared API terms endpoint included", params)
