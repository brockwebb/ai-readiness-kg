"""B3 v2 — a methodology document that is actually retrievable without JavaScript.

`v1` deviated: the signal ends "and whether it is retrievable without JS" and `v1` decided on
HTTP status and Content-Type alone, never inspecting the body it had already stored and
sha256'd. A client-rendered shell served as `text/html` — or the control fixture's HTTP-200
soft-404 page — scored `pass`.

The floors are DD-030's corpus extent gate (Kohlschütter, Fankhauser & Nejdl, WSDM 2010),
reused rather than invented: a methodology page that would have been refused admission to the
corpus as a navigation surface cannot be scored here as a legible methodology.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-B3-v2", "B3"


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
