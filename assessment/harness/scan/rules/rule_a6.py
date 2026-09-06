"""A6 — structured markup: schema.org Dataset or DCAT on the product page."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A6-v1", "A6"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"markup could not be extracted: {obs[0].error_class}", params)
    o = obs[0]
    ct = ((o.parsed or {}).get("content_type") or "")
    if ct and not ct.startswith("text/html"):
        # A CSV surface has no HTML to carry markup. Scoring that as a failure would score
        # the format rather than the product (§3: not_applicable is a real verdict).
        return c.make(RULE_ID, LEG, obs, "not_applicable",
                      f"the surface is {ct}, which carries no embedded markup", params)
    wanted = set(params["a6_markup"]["dataset_types"])
    types = set((o.parsed or {}).get("types") or [])
    hit = sorted(types & wanted)
    if hit:
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"embedded markup declares {hit[0]}", params)
    counts = (o.parsed or {}).get("syntaxes") or {}
    if any(counts.values()):
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"markup present ({counts}) but no Dataset/DataCatalog type", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no JSON-LD, microdata or RDFa on the product page", params)
