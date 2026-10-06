"""D4 v4 — "not in any public inventory" is reached only over every declared inventory.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4, DN-012 d1 and d3, audit C-04.
ind:D4 reads "enumerable from a public inventory (data.gov/agency inventory current)". spec:D4
and `RULE-D4-v3` fetched only `<product host>/data.json`, so 28 rows of the cycle of record
failed "no public data.json catalog served on this host" and were prescribed "Publish a
data.json inventory on the host". Among them were ERS, NASS and APHIS on usda.gov subdomains,
NCES, BJS, NCHS and SOI. Yet this project's own params note that data.gov reads each
DEPARTMENT's data.json (`params.yaml` `dept_domains`). DRSMSU passed only because the Board's
catalog shares its host.

**What v4 decides differently.**

* The existence branches are v3's, sentence for sentence. The product's record is found by the
  DCAT-US URL-field test in a catalog that was read, and that catalog's validation decides
  `pass` or the schema `fail`. A catalog is now any one the D4 leg observed: the host's own, or
  a declared inventory. The first that holds the product's record is the one judged.
* The two absence branches ("no catalog", "a catalog without the product") are reached only
  when every `inventory_urls` entry the body declared was observed, and nothing was left
  `unresolved` (`_scope.inventory_scope`). Otherwise the verdict is `error`, naming the
  inventories not observed and the ones the body could not declare. B1, B4, D3 and G4 read the
  same catalogs (`CONSUMES = ("D4",)`) and apply the same test (`_dcat_fields.read_inventory`).

`RULE-D4-v3` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-D4-v4", "D4"

#: A `fail` says the product is not enumerable from any public inventory: an absence claim.
CLAIM = "absence"


def _members(p: dict):
    """Records of the product under the DCAT-US field test, or None when not collected."""
    m = p.get("membership")
    if not isinstance(m, dict) or not isinstance(m.get("records"), int):
        return None
    return m["records"]


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
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
    decl = s.declared(obs)
    remainder = s.inventory_scope(obs, decl, params)
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
