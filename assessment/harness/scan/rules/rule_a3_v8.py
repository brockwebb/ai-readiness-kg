"""A3 v8 — an HTML page is not a file, however large it is.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 1, from
`cc_tasks/2026-10-06_absence_verdicts_recollection_RESULT.md` §5.5. `RULE-A3-v7`'s "unfiltered
file" branch passes any linked response the collector marks `is_bulk` (`collectors/links.py`:
not filtered by a query, at or above `a3_bulk.min_bulk_bytes`). It never asks what the response
IS. `https://www.bea.gov/research/special-sworn-researcher-program/papers` is a 110,118-byte
`text/html` page of research papers, and it passed A3 as the whole-product download of four BEA
surfaces in `scan_2026-09-10_rj5` (published) and again in the recollection, beside NCES's
bibliography and its Digest table index.

**What v8 decides differently.** The unfiltered-file branch skips a candidate whose Content-Type
is an HTML media type (`text/html`, `application/xhtml+xml`; `_text.is_html`). An HTML page is a
page, which is what A3 asks the product to offer an alternative to. The archive branch is
unchanged: an archive is recognised by its extension.

**Sniffing the body is not possible here, and that is stated rather than implied.** The task asks
for a body that "sniffs as HTML" to be refused too (WHATWG MIME Sniffing §7.1). A link record
carries no body a rule can read: the collector probes with `HEAD` and keeps only the headers and
`parsed.content_type`. So the media type is the whole of the evidence, and a candidate served
with no media type is judged as v7 judged it. `_text.is_html` takes a body head for the day a
collector records one.

Every other branch and every reason fragment `scripts/tag_prescriptions.py` keys on is v7's,
including generation 14's remainder (`_scope.link_scope`). `RULE-A3-v7` stays in `REGISTRY`,
unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s
from . import _text as t

RULE_ID, LEG = "RULE-A3-v8", "A3"

#: The shared per-surface link probe (`params.link_probe.shared_leg`), as v6 and v7.
CONSUMES = ("link_probe",)

#: A `fail` says no whole-product download is among the candidates: an absence claim.
CLAIM = "absence"


def _is_page(o) -> bool:
    """True when a link's response is an HTML page: by its media type, recorded by the collector
    (`parsed.content_type`) or in the response headers."""
    p = o.parsed or {}
    headers = {k.lower(): v for k, v in ((o.response or {}).get("headers") or {}).items()}
    return t.is_html(p.get("content_type") or headers.get("content-type"))


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in (LEG,) + CONSUMES]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    all_links = [o for o in obs if (o.parsed or {}).get("probe") == "link"]
    on_scope = [o for o in all_links if not (o.parsed or {}).get("off_host")]
    blind = [o for o in on_scope if c.unobserved(o, params)]
    seen = [o for o in on_scope if o not in blind]
    if on_scope and not seen:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"all {len(blind)} link(s) on this surface were unobserved "
                      f"({blind[0].error_class}); whether the product offers a whole-product "
                      f"download is unmeasured, not absent", params,
                      blind_links=len(blind) or None)
    links = [o for o in seen if c.served(o)]
    bulk = [o for o in links if (o.parsed or {}).get("is_bulk")
            and ((o.parsed or {}).get("is_archive") or not _is_page(o))]
    if bulk:
        o = bulk[0]
        p = o.parsed or {}
        how = ("archive" if p.get("is_archive")
               else f"unfiltered file of {p.get('content_length')} bytes")
        tail = (f" ({len(blind)} of {len(on_scope)} link record(s) were unobserved and are "
                f"excluded)" if blind else "")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"whole-product download linked from the product page: "
                      f"{o.target_url} ({how}){tail}", params, blind_links=len(blind) or None)
    # Everything below is an absence claim, asked about once: first the candidates the cap left
    # unprobed, then a probed candidate that was blind.
    what = "whether the product offers a whole-product download"
    remainder = s.link_scope(obs, params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder,
                                 blind_links=len(blind) or None)
    probed_blind = [o for o in blind if o.error_class != "unprobed_over_cap"]
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=on_scope,
                              blind=probed_blind, found=None, what=what,
                              blind_links=len(blind) or None)
    if scope is not None:
        return scope
    filtered = [o for o in links if (o.parsed or {}).get("filtered_by_query")]
    small = [o for o in links if (o.parsed or {}).get("content_length") is not None
             and not (o.parsed or {}).get("meets_size_floor")]
    if filtered:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(filtered)} download link(s) are filtered queries, not "
                      f"whole-product downloads; first: {filtered[0].target_url} "
                      f"({s.link_search(obs)})", params)
    if small:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the largest linked download is below the "
                      f"{params['a3_bulk']['min_bulk_bytes']}-byte whole-product floor; "
                      f"first: {small[0].target_url} ({s.link_search(obs)})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no whole-product download linked from the product page "
                  f"({len(links)} link(s) probed; {s.link_search(obs)})", params)
