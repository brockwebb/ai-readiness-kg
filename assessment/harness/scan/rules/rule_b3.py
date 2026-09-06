"""B3 — methodology legibility: structured text, not PDF-only, retrievable without JS."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-B3-v1", "B3"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the methodology surface could not be observed: {obs[0].error_class}",
                      params)
    # The runner appends the METHODOLOGY document after the product page, so a methodology
    # observation is any observation past the first. Accepting the product page itself was
    # what made `fails_all` pass B3 — a PDF-only site with no methodology at all scored as
    # having a legible one, because its landing page happens to be HTML.
    for o in obs[1:]:
        ct = ((o.parsed or {}).get("content_type") or "")
        st = (o.response or {}).get("status")
        if st and st < 400 and (ct.startswith("text/html") or ct.startswith("text/markdown")):
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"methodology served as {ct} at {o.target_url}", params)
    pdf = [o.target_url for o in obs
           if ((o.parsed or {}).get("content_type") or "") in
           params["a1_formats"]["pdf_content_types"]]
    if pdf:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"methodology is PDF-only: {pdf[0]}", params)
    if len(obs) == 1:
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no link to a methodology document from the product surface", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no structured-text methodology document reachable from the product surface",
                  params)
