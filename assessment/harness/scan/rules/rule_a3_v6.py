"""A3 v6 — a rule that could not look at the candidate does not get to say it is not there.

`cc_tasks/2026-09-11_absence_claims_under_scope_limitation.md` decision 3, from the eighth
instance of the family, caught by a control for the first time
(`cc_tasks/2026-09-11_control_fixture_robots_forbids_product_RESULT.md` §1).

**What v5 got right and what it got wrong.** v5 filters link probes through `_common.unobserved`
and returns `error` when EVERY link is blind — right, and it is why `only_errors` is not enough.
Then, when only SOME are blind, it judges over the rest and returns `fail`: *"no whole-product
download linked from the product page (3 of 8 link(s) were unobserved and are excluded)"*. On
the `robots_forbids_product` fixture the excluded link is `/bulk/estimates-2026.zip`, anchor text
**"whole-product archive"** — v5 drops the one candidate that would have settled its question and
then answers it.

**The line moves from HOW MUCH was blind to WHAT THE VERDICT CLAIMS.** A `pass` here is an
existence claim: a bulk download was found, on a link that was actually fetched, and no number of
unfetched links can unfind it — that branch is unchanged and still fires with blind links
present. Every `fail` branch is an absence claim over the candidate set, and an absence claim
whose candidate set has a blind member is a scope limitation: `_common.absence_verdict` returns
`error` and names the candidates nobody was allowed to look at.

`RULE-A3-v5` is untouched and stays in `REGISTRY`, re-deriving the four cycles it judged.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A3-v6", "A3"

#: The shared per-surface link probe (`params.link_probe.shared_leg`), as v5.
CONSUMES = ("link_probe",)

#: **What this rule CLAIMS when it says `fail`** (decision 2). `absence`: the verdict is that no
#: whole-product download is offered, which is a statement about the candidate set as a whole and
#: is only provable over candidates that answered.
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
                      f"download is unmeasured, not absent", params, blind_links=len(blind) or None)
    tail = (f" ({len(blind)} of {len(on_scope)} link(s) were unobserved and are excluded)"
            if blind else "")
    links = [o for o in seen if c.served(o)]
    bulk = [o for o in links if (o.parsed or {}).get("is_bulk")]
    # **Asked ONCE, here, where `found` still means something.** Everything below this line is
    # either the existence verdict (`bulk` found, and it stands whatever was blind) or one of
    # three absence claims — filtered-only, too-small, none-at-all — each of which says "the
    # whole-product download is not among these candidates". Asking per branch would be three
    # chances to forget, which is exactly how v5's gap reads on review: the guard was there, it
    # just never asked what the verdict claimed.
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=on_scope, blind=blind,
                              found=bulk,
                              what="whether the product offers a whole-product download",
                              blind_links=len(blind) or None)
    if scope is not None:
        return scope
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
