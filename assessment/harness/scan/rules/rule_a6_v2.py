"""A6 v2 — structured markup that VALIDATES, not markup that merely names a type.

`v1` deviated: the spec says "validate the DCAT graph against DCAT-AP SHACL shapes" and `v1`
stopped at type membership, so a graph declaring `dcat:Dataset` while violating every shape
returned `pass` and no SHACL report was produced despite `evidence_kind` requiring one.

The shapes are a STATED minimal subset (`shapes/dcat_ap_min.ttl`) and `shapes_profile` rides
on every Finding, so a pass here can never be read as DCAT-AP conformance.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A6-v2", "A6"


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
        return c.make(RULE_ID, LEG, obs, "not_applicable",
                      f"the surface is {ct}, which carries no embedded markup", params)
    wanted = set(params["a6_markup"]["dataset_types"])
    types = set((o.parsed or {}).get("types") or [])
    hit = sorted(types & wanted)
    rep = (o.parsed or {}).get("shacl") or {}
    profile = rep.get("shapes_profile") or params["a6_shacl"]["shapes_profile"]
    if not hit:
        counts = (o.parsed or {}).get("syntaxes") or {}
        if any(counts.values()):
            return c.make(RULE_ID, LEG, obs, "fail",
                          f"markup present ({counts}) but no Dataset/DataCatalog type", params)
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no JSON-LD, microdata or RDFa on the product page", params)
    if not rep.get("loaded"):
        # We could not READ the graph. That is our failure, not the product's (§3).
        return c.make(RULE_ID, LEG, obs, "error",
                      f"markup declares {hit[0]} but the graph could not be validated: "
                      f"{rep.get('reason', 'no SHACL report')}", params)
    if rep.get("conforms"):
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"markup declares {hit[0]} and the graph conforms to the {profile} "
                      f"shapes ({rep.get('triples')} triples)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"markup declares {hit[0]} but violates the {profile} shapes "
                  f"({rep.get('violations')} violation(s)); first: "
                  f"{(rep.get('messages') or ['(none reported)'])[0]}", params)
