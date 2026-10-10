"""D4 v5 — the product's inventory is searched for where it is recorded, and nowhere else.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1.
D4 is an existence leg: are the body's products listed in an inventory it publishes or that
data.gov harvests? `RULE-D4-v4` judged over every catalog the D4 leg observed, the product host's
own `/data.json` included, which the collector fetches by convention whether or not the body's
record names it. That convention location is discoverability's evidence (`rule_a13.py`).

**What v5 decides differently, and only this.** It judges the catalogs observed at RECORDED
inventory locations (`targets.yaml` `declared_locations`, read from the body's pages or seeded;
`_existence.recorded_only`). Its two absence branches are reached as `fail` only when every
recorded inventory was observed and every seed source was searched for the body's inventory
(`_existence.remainder`); otherwise `error`, naming what was not. The `pass`, the validation
branches and every reason fragment are v4's. `RULE-D4-v4` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _existence as ex
from . import _scope as s

RULE_ID, LEG = "RULE-D4-v5", "D4"

#: A `fail` says the product is not enumerable from any public inventory: an absence claim.
CLAIM = "absence"


def _members(p: dict):
    """Records of the product under the DCAT-US field test, or None when not collected."""
    m = p.get("membership")
    if not isinstance(m, dict) or not isinstance(m.get("records"), int):
        return None
    return m["records"]


def judge(observations: list, params: dict):
    every = [o for o in observations if o.leg == LEG]
    if not every:
        return c.empty(RULE_ID, LEG, params)
    decl = ex.declared(every)
    obs = ex.recorded_only(every, decl, ("inventory",), params)
    if not obs:
        # No recorded inventory was observed: what the record says, and how far the seeds were
        # searched, decides between `error` and `fail`, over every D4 Observation as evidence.
        remainder = ex.remainder(every, decl, "inventory", params)
        if remainder:
            return s.remainder_error(RULE_ID, LEG, every, params,
                                     "whether the product is enumerable from a public "
                                     "inventory", remainder)
        return c.make(RULE_ID, LEG, every, "fail",
                      f"no public data.json catalog served at any of the body's recorded "
                      f"inventories: {ex.search(decl, 'inventory', params)}", params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog could not be observed: {obs[0].error_class}", params)
    profile = params["d4_validation"]["schema_profile"]
    served = [o for o in obs if (o.parsed or {}).get("present")]
    unmeasured = [o for o in served if _members(o.parsed or {}) is None]
    if unmeasured:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"a catalog is served at {unmeasured[0].target_url} but was collected "
                      f"before the DCAT-US membership test existed, so whether a record names "
                      f"the product in its identifier, landingPage, accessURL or downloadURL "
                      f"was not observed", params)
    for o in served:
        p = o.parsed or {}
        if not _members(p):
            continue
        blind = c.unobserved_error(RULE_ID, LEG, obs, o, params, "the catalog")
        if blind:
            return blind
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
                      f"the product appears in {o.target_url} in {_members(p)} record(s) "
                      f"naming it in a DCAT-US URL field, and the catalog conforms to the "
                      f"{profile} schema ({v.get('datasets_validated')} of "
                      f"{v.get('datasets_total')} datasets validated)", params)
    # The product's record is in no catalog that was read. Both branches below are absence
    # claims over the body's inventories, asked about once, here.
    remainder = ex.remainder(every, decl, "inventory", params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params,
                                 "whether the product is enumerable from a public inventory",
                                 remainder)
    read = [e["url"] for e in (decl or {}).get("inventory_urls") or []]
    if served:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a catalog is served at {served[0].target_url} "
                      f"but the product is not in it: no record names it in identifier, "
                      f"landingPage, accessURL or downloadURL, in any of the {len(read)} "
                      f"declared inventories ({', '.join(read)})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no public data.json catalog served at any of the {len(read)} declared "
                  f"inventories ({', '.join(read)})", params)
