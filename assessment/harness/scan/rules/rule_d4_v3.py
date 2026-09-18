"""D4 v3 — the product is enumerable from a catalog that validates, and "in the catalog" means a
record whose own URL fields name the product.

`cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 4. `v2` decides membership from
the collector's `contains_product`, which is `product_url in json.dumps(record)`: the product
URL as a substring ANYWHERE in a record. DCAT-US v1.1 (corpus/kernel/dcat-us-1-1-schema.md,
doc_id `dcat-us-1-1-schema`) defines the record fields that locate a dataset, and of the one a
home page would be mistaken for it says: `landingPage` "is not intended for an agency's homepage
(e.g. www.agency.gov), but rather if a dataset has a human-friendly hub or landing page that
users can be directed to for all resources tied to the dataset." Under the substring test
census.gov's home page was "in" 1,635 of 1,805 records
(`cc_tasks/2026-09-18_dcat_field_rules_RESULT.md` §1) — the reading that sentence rules out.

`v3` reads the collector's `membership` block instead: the number of records one of whose
DCAT-US URL fields (`params.d4_catalog.membership_fields`) EQUALS the product URL
(`collectors/dcat.product_records`). Every other branch, and every reason sentence, is `v2`'s,
so the prescription outcomes (`tag_prescriptions.OUTCOMES["D4"]`) name the same branches.

A catalog observation collected before the block existed carries no `membership`, and this rule
says `error` over it — not observed under this test — rather than reading the substring flag
as if it were the field test. `v2` stays in `REGISTRY`; every Finding recorded under it
re-derives under it.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-D4-v3", "D4"


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
        # The per-probe guard every generation-4+ rule calls. A served catalog is never blind,
        # so it does not fire here; it is what keeps the lint's promise checkable.
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
    if served:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a catalog is served at {served[0].target_url} "
                      f"but the product is not in it: no record names it in identifier, "
                      f"landingPage, accessURL or downloadURL", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no public data.json catalog served on this host", params)
