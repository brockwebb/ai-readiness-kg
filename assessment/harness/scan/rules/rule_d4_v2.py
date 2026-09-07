"""D4 v2 — the product is enumerable from a catalog that VALIDATES.

`v1` deviated: the signal says "validate against the POD v1.1 schema" and no branch of `v1`
consumed a validity flag — `complete_entries` was interpolated into the pass message only, so
a catalog failing POD validation passed as long as it existed and named the product.

The schema is a STATED required-field subset (`shapes/pod_v1_1_min.schema.json`) and
`schema_profile` rides on every Finding, so a pass here can never be read as POD conformance.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-D4-v2", "D4"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog could not be observed: {obs[0].error_class}", params)
    profile = params["d4_validation"]["schema_profile"]
    for o in obs:
        p = o.parsed or {}
        if not (p.get("present") and p.get("contains_product")):
            continue
        v = p.get("pod") or {}
        if not v.get("validated"):
            return c.make(RULE_ID, LEG, obs, "error",
                          f"the product appears in {o.target_url} but the catalog could not "
                          f"be validated: {v.get('reason', 'no validation report')}", params)
        if not v.get("conforms"):
            return c.make(RULE_ID, LEG, obs, "fail",
                          f"the product appears in {o.target_url} but the catalog violates "
                          f"the {profile} schema in {v.get('violations')} place(s) over "
                          f"{v.get('datasets_validated')} of {v.get('datasets_total')} "
                          f"datasets; first: "
                          f"{(v.get('messages') or ['(none reported)'])[0]}", params)
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"the product appears in {o.target_url} and the catalog conforms to the "
                      f"{profile} schema ({v.get('datasets_validated')} of "
                      f"{v.get('datasets_total')} datasets validated)", params)
    served = [o.target_url for o in obs if (o.parsed or {}).get("present")]
    if served:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a catalog is served at {served[0]} but the product is not in it",
                      params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no public data.json catalog served on this host", params)
