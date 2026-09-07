"""A3 v3 — bulk access: a WHOLE-PRODUCT download, not a filtered export.

`v1` deviated: the spec says "classify links as bulk (whole-product archive or full dataset
file) vs filtered query" and `v1` accepted any href ending in an A1 structured extension. A
200-row preview passed; a genuine `.zip` archive was missed, because archives are not in
`a1_formats.structured_extensions`; and the Content-Length that would size a candidate was
never read. `collectors/links.py` now computes the three discriminators in `a3_bulk`.


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

RULE_ID, LEG = "RULE-A3-v3", "A3"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    links = [o for o in obs if (o.parsed or {}).get("probe") == "link"
             and c.served(o)]
    bulk = [o for o in links if (o.parsed or {}).get("is_bulk")]
    if bulk:
        o = bulk[0]
        p = o.parsed or {}
        how = ("archive" if p.get("is_archive")
               else f"unfiltered file of {p.get('content_length')} bytes")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"whole-product download linked from the product page: "
                      f"{o.target_url} ({how})", params)
    filtered = [o for o in links if (o.parsed or {}).get("filtered_by_query")]
    small = [o for o in links if (o.parsed or {}).get("content_length") is not None
             and not (o.parsed or {}).get("meets_size_floor")]
    if filtered:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(filtered)} download link(s) are filtered queries, not "
                      f"whole-product downloads; first: {filtered[0].target_url}", params)
    if small:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the largest linked download is below the "
                      f"{params['a3_bulk']['min_bulk_bytes']}-byte whole-product floor; "
                      f"first: {small[0].target_url}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no whole-product download linked from the product page "
                  f"({len(links)} link(s) probed)", params)
