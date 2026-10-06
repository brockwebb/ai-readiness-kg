"""B3 v4 — a methodology verdict is not reached over the first of several candidates.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 5, from the absence inventory
(`docs/research/2026-10-06_absence_rules_inventory.md` §2). `runner.collect_leg` follows the
FIRST link on the product page whose href or text carries a `b3_methodology.link_tokens` token,
then returns. `v3`'s three document branches assert that NO legible methodology is reachable:
"not retrievable without JS", "PDF-only" and "no structured-text methodology document
reachable". Each judges one document while the page may link several. That is DN-012 d1's
first trigger, a truncated candidate set.

**What v4 decides differently.** The candidates are counted from the page Observation's own
`parsed.links` with the same tokens, and compared with the documents that were followed. Any
candidate left unfollowed makes those three branches `error`, naming how many. The `pass` is
v3's exactly: a legible methodology was found. The "no link to a methodology document" branch
is v3's too, because it is a complete search of every link on the page. How good the token is at
recognising a methodology link is a question about the predicate, not about the scope, and this
task does not take it on (inventory §1). `RULE-B3-v3` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-B3-v4", "B3"

#: A `fail` says no legible methodology is reachable: an absence claim.
CLAIM = "absence"


def _candidates(page, params: dict) -> list | None:
    """The distinct methodology-candidate hrefs on the product page, in page order, or None when
    the page's links were not read. The collector's own test (`runner.collect_leg`)."""
    links = (page.parsed or {}).get("links") if isinstance(page.parsed, dict) else None
    if links is None:
        return None
    toks = params["b3_methodology"]["link_tokens"]
    out = []
    for link in links:
        href = link.get("href", "")
        if any(t in (href + link.get("text", "")).lower() for t in toks) and href not in out:
            out.append(href)
    return out


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
    # `obs[0]` is the product page; the methodology documents the runner followed come after it.
    followed = list(obs[1:])
    blind = [o for o in followed if c.unobserved(o, params)]
    thin = []
    for o in followed:
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
    what = "whether a legible methodology document is reachable from the product surface"
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=followed, blind=blind,
                              found=None, what=what, blind_candidates=len(blind) or None)
    if scope is not None:
        return scope
    cands = _candidates(obs[0], params)
    if cands is None and (obs[0].parsed or {}).get("links_error"):
        return s.remainder_error(RULE_ID, LEG, obs, params, what,
                                 [f"the product page's links could not be read "
                                  f"({obs[0].parsed['links_error']})"])
    cands = cands or []
    done = {o.target_url for o in followed}
    unfollowed = [h for h in cands if h not in done]
    if unfollowed:
        return s.remainder_error(
            RULE_ID, LEG, obs, params, what,
            [f"{len(cands) - len(unfollowed)} of {len(cands)} methodology link(s) on the product "
             f"page followed, {len(unfollowed)} not followed (first: {unfollowed[0]})"])
    if thin:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a methodology document is served at {thin[0][0]} but is not "
                      f"retrievable without JS: {thin[0][1]}", params)
    pdf = [o.target_url for o in obs
           if ((o.parsed or {}).get("content_type") or "") in
           params["a1_formats"]["pdf_content_types"]]
    if pdf:
        return c.make(RULE_ID, LEG, obs, "fail", f"methodology is PDF-only: {pdf[0]}", params)
    if not followed:
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no link to a methodology document from the product surface", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no structured-text methodology document reachable from the product surface",
                  params)
