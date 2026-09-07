"""A3 v4 — bulk access, judged from the SHARED per-surface link probe.

Same change as `RULE-A1-v3` and for the same reason: A1 and A3 asked different questions of the
SAME 25 objects and each HEADed all of them, which is 559 duplicate requests in one cycle and
no additional evidence. The link observations are collected once under the `link_probe` leg and
this rule declares that it reads them. What it DECIDES is `v3`'s decision, unchanged, including
`_common.served()` — the guard `v3` exists for.

`v3` is untouched and stays in `REGISTRY`.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A3-v4", "A3"

#: Legs whose observations this rule reads IN ADDITION to its own. Its own leg collects nothing
#: (`runner.collect_leg`), so in practice this IS its evidence. Read by `run.py` when it builds
#: a judge group and by `rederive.py` when it rebuilds one from stored observations — one
#: declaration, both readers, so a re-derivation cannot group differently from the cycle.
CONSUMES = ("link_probe",)



def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in (LEG,) + CONSUMES]
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
