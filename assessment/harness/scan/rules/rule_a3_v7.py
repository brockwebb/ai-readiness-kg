"""A3 v7 — "no whole-product download linked" is reached only when every link was probed.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 3, DN-012 d1, audit C-01. `v6` closed
the case of a BLIND candidate (`_common.absence_verdict`) and left open the case the audit
found: the candidates the cap never reached. They left no record, so a `fail` reading
*"no whole-product download linked from the product page (25 link(s) probed)"* stood over 25 of
115, 224 or 244 on-host links on every product surface of the cycle of record.

**What v7 decides differently.** The `pass` is unchanged (existence, from a fetched link). Every
`fail` branch first asks two things. The page's `link_candidates` (`_scope.link_scope`) gives
how many on-host candidates the cap left unprobed. `_common.absence_verdict` gives whether a
probed candidate was blind. Either one makes the verdict `error`, naming the remainder: "N of M
on-host links probed, M minus N unprobed, cap K". An unprobed candidate is counted once, through
the block, and never again as blind.

`RULE-A3-v6` stays in `REGISTRY`, unedited, re-deriving every cycle it judged.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-A3-v7", "A3"

#: The shared per-surface link probe (`params.link_probe.shared_leg`), as v6.
CONSUMES = ("link_probe",)

#: A `fail` says no whole-product download is among the candidates: an absence claim.
CLAIM = "absence"


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
    bulk = [o for o in links if (o.parsed or {}).get("is_bulk")]
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
