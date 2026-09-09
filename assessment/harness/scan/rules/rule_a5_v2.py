"""A5 v2 — a sitemap declared on another SITE is not a discovery failure, and a discovery
probe nobody observed is not an absence.

`cc_tasks/2026-09-09_closeout_and_manners.md` decision 3, plus the blind-probe guard every
rule of generation four and later owes (DD-052 §6 and its mirror).

**Two changes, and the second was found by the standing lint rather than by design.**

1. **An off-site declaration is `not_applicable`, never `fail`.** v1 asked whether a discovery
   file was SERVED and treated everything else as absence. That is right when the host declared
   nothing and right when it declared something and served it. It is wrong for the case
   decision 3 creates: a host that declares a sitemap on another site, which we record and
   decline to fetch. Under v1 that host has "no sitemap served" and fails, which reports the
   SCANNER'S bound as the PRODUCT'S omission. `not_applicable`, not `error`: the collector
   observed exactly what there was to observe, a declaration naming somebody else's site.
   Nothing failed and nothing was blind; the measurement does not apply.

2. **A blind discovery probe makes absence unprovable.** v1 returned `fail` whenever no probe
   came back `present`, whether the other candidates had answered or been killed mid-connection.
   A5 probes several paths, and a 404 on one is a real measurement; a reset or a timeout on one
   is not. If any candidate was unobserved and none of the observed ones is the sitemap, "no
   discovery file is served" is not established, because the unobserved one might have been it.
   That is the fifth instance of the defect A10, A1, A3 and A8 were each fixed for, and it was
   still here: `tests/test_scan_harness_v4.py`'s lint over `rules/` failed this module for
   never consulting the guard, which is exactly what that lint exists to do.

The off-site branch decides only when nothing else does, so an off-site declaration alongside a
served same-site sitemap that covers the product is still a `pass`.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A5-v2", "A5"

#: The class the collector records when it declines to follow a declaration off the site.
OFF_SITE = "sitemap_off_site"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)

    # An off-site declaration is neither an observation of the product nor a failure to see
    # one. It is held out of the blindness question entirely: it was not unobserved, it was
    # not looked at, and those are different things.
    off_site = [o for o in obs if o.error_class == OFF_SITE]
    on_scope = [o for o in obs if o.error_class != OFF_SITE]
    blind = [o for o in on_scope if c.unobserved(o, params)]
    seen = [o for o in on_scope if o not in blind]

    if on_scope and not seen:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"none of the {len(blind)} discovery probe(s) on this host could be "
                      f"observed ({blind[0].error_class}); whether anything is served is "
                      f"unmeasured, not absent", params)

    # A sitemap that is SERVED and lists the product settles it, whatever else was blind: the
    # thing being looked for was found.
    for o in seen:
        p = o.parsed or {}
        if p.get("kind") == "sitemap" and p.get("present") and p.get("covers_product"):
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"sitemap at {o.target_url} lists the product URL "
                          f"({p.get('url_count')} URLs)", params)

    # From here the verdict is about ABSENCE, and absence is only provable over probes that
    # answered. One blind candidate is enough to make it unprovable: it might have been the
    # sitemap, or the sitemap that covers the product.
    if blind:
        return c.unobserved_error(
            RULE_ID, LEG, obs, blind[0], params,
            f"{len(blind)} of {len(on_scope)} discovery probe(s), including "
            f"{blind[0].target_url},")

    present = [o.target_url for o in seen if (o.parsed or {}).get("present")]
    if present:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"discovery files served ({', '.join(present[:3])}) but none lists the "
                      f"product URL", params)
    if off_site:
        sites = sorted({(o.parsed or {}).get("sitemap_site") or "?" for o in off_site})
        return c.make(
            RULE_ID, LEG, obs, "not_applicable",
            f"this host DECLARES a sitemap and the declaration names another site "
            f"({', '.join(sites)}): {', '.join(o.target_url for o in off_site[:3])}. The "
            f"declaration was recorded and NOT followed, because following it would contact a "
            f"site outside the frame. Discovery-by-sitemap is not measurable here and the host "
            f"has not failed it; the bound is ours.", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no sitemap, llms.txt or well-known discovery file served", params)
