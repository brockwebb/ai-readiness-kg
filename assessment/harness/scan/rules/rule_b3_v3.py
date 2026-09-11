"""B3 v3 — a methodology document nobody was allowed to fetch is not a methodology document
that is not there.

`cc_tasks/2026-09-11_absence_claims_under_scope_limitation.md` decision 3, from the eighth
instance of the family (`cc_tasks/2026-09-11_control_fixture_robots_forbids_product_RESULT.md`
§1). On the `robots_forbids_product` fixture, v2 returned **fail** — *"no structured-text
methodology document reachable from the product surface"* — on two observations, one of which
was `/methodology.html` with class `robots_disallowed`. Its only substantive candidate was the
document it was forbidden to fetch.

**v2's judgement over what it CAN see is unchanged and is still right.** A methodology document
that is served, thin, PDF-only or JavaScript-dependent is a measurement, and this rule still
makes it. What changes is the conclusion drawn from an empty result: "none of the candidates
qualifies" is an absence claim, and an absence claim over a candidate set with a blind member is
a scope limitation. `_common.absence_verdict` turns it into `error` and names the candidate.

`RULE-B3-v2` is untouched and stays in `REGISTRY`, re-deriving the cycles it judged.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-B3-v3", "B3"

#: **What this rule CLAIMS when it says `fail`** (decision 2). `absence`: no legible methodology
#: document is reachable — a statement about every candidate the surface offered, provable only
#: over the candidates that answered.
CLAIM = "absence"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the methodology surface could not be observed: {obs[0].error_class}",
                      params)
    p = params["b3_without_js"]
    min_chars, max_link = int(p["min_visible_chars"]), float(p["max_link_density"])
    # The candidates are the methodology documents the runner appended after the product page.
    # `obs[0]` is the page itself and is not a candidate — accepting it is what made `fails_all`
    # pass B3 in the scaffold, and it is also why `only_errors` above cannot catch this case:
    # the page is served, so not every observation is blind, while every CANDIDATE may be.
    candidates = list(obs[1:])
    blind = [o for o in candidates if c.unobserved(o, params)]
    thin = []
    # The runner appends the METHODOLOGY document after the product page; accepting the
    # product page itself is what made `fails_all` pass B3 in the scaffold.
    for o in obs[1:]:
        ct = ((o.parsed or {}).get("content_type") or "")
        st = (o.response or {}).get("status")
        if not (st and st < 400 and (ct.startswith("text/html")
                                     or ct.startswith("text/markdown"))):
            continue
        ex = (o.parsed or {}).get("extent") or {}
        vis, dens = ex.get("visible_chars"), ex.get("link_density")
        if vis is None:
            thin.append((o.target_url, "no extent measured"))
            continue
        if vis < min_chars:
            thin.append((o.target_url, f"{vis} visible characters before JS (floor "
                                       f"{min_chars})"))
            continue
        if dens is not None and dens > max_link:
            thin.append((o.target_url, f"link density {dens} (ceiling {max_link}): the page "
                                       f"is navigation, not methodology"))
            continue
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"methodology served as {ct} at {o.target_url} and retrievable without "
                      f"JS: {vis} visible characters, link density {dens}", params)
    # Nothing qualified. Everything below is an absence claim over `candidates`, so the scope
    # limitation is asked once, here, before any of the four `fail` branches.
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=candidates, blind=blind,
                              found=None,
                              what="whether a legible methodology document is reachable from "
                                   "the product surface",
                              blind_candidates=len(blind) or None)
    if scope is not None:
        return scope
    if thin:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a methodology document is served at {thin[0][0]} but is not "
                      f"retrievable without JS: {thin[0][1]}", params)
    pdf = [o.target_url for o in obs
           if ((o.parsed or {}).get("content_type") or "") in
           params["a1_formats"]["pdf_content_types"]]
    if pdf:
        return c.make(RULE_ID, LEG, obs, "fail", f"methodology is PDF-only: {pdf[0]}", params)
    if len(obs) == 1:
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no link to a methodology document from the product surface", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no structured-text methodology document reachable from the product surface",
                  params)
