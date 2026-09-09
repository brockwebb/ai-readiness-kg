"""A3 v5 — a link nobody observed is not a bulk download the product fails to offer.

`cc_tasks/2026-09-08_scan_run_3.md` §1.2. The same correction as `RULE-A1-v4`, on the leg
`cc_tasks/2026-09-08_scan_harness_v4_RESULT.md` §7.1 named it on: `v4` filters through
`_common.served()` and then returns **fail** — *"no whole-product download linked from the
product page (0 link(s) probed)"* — when every link HEAD was reset. The page was served, so
`only_errors` is false, and a surface nobody could see through is scored as offering no bulk
download.

A blind link is unobserved for that link. All blind → `error`. Some blind → judge over the
observed ones and carry the blind count on the Finding. None blind → exactly `v4`'s decision.

`v4` is untouched and stays in `REGISTRY`.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A3-v5", "A3"

CONSUMES = ("link_probe",)


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
                      f"download is unmeasured, not absent", params, blind_links=len(blind) or None)
    tail = (f" ({len(blind)} of {len(on_scope)} link(s) were unobserved and are excluded)"
            if blind else "")
    links = [o for o in seen if c.served(o)]
    bulk = [o for o in links if (o.parsed or {}).get("is_bulk")]
    if bulk:
        o = bulk[0]
        p = o.parsed or {}
        how = ("archive" if p.get("is_archive")
               else f"unfiltered file of {p.get('content_length')} bytes")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"whole-product download linked from the product page: "
                      f"{o.target_url} ({how}){tail}", params, blind_links=len(blind) or None)
    filtered = [o for o in links if (o.parsed or {}).get("filtered_by_query")]
    small = [o for o in links if (o.parsed or {}).get("content_length") is not None
             and not (o.parsed or {}).get("meets_size_floor")]
    if filtered:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(filtered)} download link(s) are filtered queries, not "
                      f"whole-product downloads; first: {filtered[0].target_url}{tail}", params, blind_links=len(blind) or None)
    if small:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the largest linked download is below the "
                      f"{params['a3_bulk']['min_bulk_bytes']}-byte whole-product floor; "
                      f"first: {small[0].target_url}{tail}", params, blind_links=len(blind) or None)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no whole-product download linked from the product page "
                  f"({len(links)} link(s) probed){tail}", params, blind_links=len(blind) or None)
