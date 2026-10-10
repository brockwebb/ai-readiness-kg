"""D3 v3 — "no catalog record for the product" is reached only over a complete seeded search.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1:
existence is not discoverability. D4 and its four consumers are existence legs: whether the
body's products are listed in an inventory it publishes or that data.gov harvests. `RULE-D3-v2`
reached its catalog through `_dcat_fields.read_inventory` over EVERY catalog the D4 leg
observed, the product host's own `/data.json` included, which D4's collector fetches whether or
not anyone recorded it. That host-root `/data.json` is the convention location a machine tries
first (OMB M-13-13), so it is discoverability's evidence (`rule_a13.py`), not existence's.

**What v3 decides differently, and only this.** The catalog state is read over the catalogs
observed at RECORDED inventory locations (`_existence.read_recorded_inventory`), and each of the
four absence kinds is reached as `fail` only when every recorded inventory was observed AND every
seed source was searched for the body's inventory (`_existence.remainder`). Otherwise it is
`error`, naming the inventory not verified or the sources not searched. Every field test over a
record that WAS found, and every reason fragment, is `RULE-D3-v2`'s. `RULE-D3-v2` stays in `REGISTRY`,
unedited.

`RULE-D3-v2`'s own account follows.

D3 v2 — "no catalog record for the product" is reached only over every declared inventory.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4, DN-012 d1 and d3, audit C-04. This
leg reads D4's catalog observation (`CONSUMES`), and `RULE-D3-v1` inherited D4's scope: the
product HOST's `/data.json`, and nothing else. ind:D4 says "data.gov/agency inventory", and
data.gov reads each DEPARTMENT's data.json (`params.yaml` `dept_domains`). So "no public
data.json catalog served on this host, so there is no catalog record for the product" was an
absence over one of the places the record could be.

**What v2 decides differently, and only this.** Its catalog state is
`_dcat_fields.read_inventory`, which reads every catalog the D4 leg observed, the body's
declared inventories included, and takes the product's records from whichever holds them. Each
of the four absence kinds (`_dcat_fields.ABSENCE_KINDS`: no catalog, a blind catalog, one that
does not parse, one without the product's record) is reached as `fail` only when every declared
inventory was observed and nothing was left undeclared (`_scope.inventory_scope`). Otherwise it
is `error`, naming the inventories not searched. The field tests over records that WERE found
are `RULE-D3-v1`'s, sentence for sentence. `RULE-D3-v1` stays in `REGISTRY`, unedited.

`RULE-D3-v1`'s own account of the field follows.

D3 v1 — source lineage published on the product's catalog record.

`cc_tasks/2026-09-18_dcat_field_rules.md` decisions 1 to 3. Pre-registered before cycle 5
(2026-10-05), which is the first cycle that judges it.

**The fields.** DCAT-US 3 (`corpus/kernel/dcat-us-3-dataset-schema.md`, doc_id
`dcat-us-3-dataset-schema`) names `wasGeneratedBy`, "List of activities that generated, or
provide the business context for the creation of the dataset". W3C DCAT 3
(`corpus/kernel/w3c-dcat-3.md`) carries the same property as `prov:wasGeneratedBy` and names
`prov:wasDerivedFrom` among the PROV-O properties a dataset relationship may use. Both come from
the PROV ontology, admitted as `w3c-prov-o-ontology`: "Generation is the completion of
production of a new entity by an activity", and "By expressing usage and generation, one can
construct provenance chains comprising both Activities and Entities". A record carries the
lineage clause when it names at least one generating activity or source entity.

`qualifiedAttribution` ("List of agents with specific responsibilities for the dataset") is read
and REPORTED, not required: it says who was responsible, which is attribution, not lineage.

**What is NOT measured**, and every verdict says so: whether the chain the record names reaches
from collection through processing to the product. The rule reads that a lineage is named, not
how deep it goes; following the chain means dereferencing the activities, which no collector
does.

**The subject is the product's catalog record** (`MEASURES = "product"`), following D4, which
reads the same catalog for the same product; the catalog is D4's observation (`CONSUMES`).
`fail` is an absence claim (`CLAIM = "absence"`).
"""
from __future__ import annotations

from . import _common as c
from . import _dcat_fields as d
from . import _existence as ex
from . import _scope as sc

RULE_ID, LEG = "RULE-D3-v3", "D3"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "a source lineage"
UNMEASURED = ("not measured: whether the named lineage reaches from collection through "
              "processing to the product, which would mean dereferencing the activities")


def judge(observations: list, params: dict):
    s = ex.read_recorded_inventory(observations, params, d.read_inventory)
    obs = s["obs"]
    if s["kind"] == "empty":
        return c.empty(RULE_ID, LEG, params)
    if s["kind"] == "unobserved":
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog could not be observed: {s['probe'].error_class}", params)
    if s["kind"] in d.ABSENCE_KINDS:
        remainder = ex.remainder(observations, s["decl"], "inventory", params)
        if remainder:
            return sc.remainder_error(RULE_ID, LEG, obs, params,
                                      f"whether a catalog record carries {WHAT}", remainder)
    if s["kind"] == "scope":
        return c.absence_verdict(RULE_ID, LEG, obs, params, candidates=obs, blind=s["blind"],
                                 what=f"whether a catalog record carries {WHAT}")
    if s["kind"] == "no_catalog":
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"no public data.json catalog served at any declared inventory, so there is "
                      f"no catalog record for the product to carry {WHAT}; {UNMEASURED}",
                      params)
    probe = s["probe"]
    blind = c.unobserved_error(RULE_ID, LEG, obs, probe, params, "the catalog")
    if blind:
        return blind
    if s["kind"] == "unread":
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog at {probe.target_url} was served and carries no field "
                      f"extraction: it was collected before `dcat_fields` existed, so "
                      f"{WHAT} cannot be read from it", params)
    if s["kind"] == "unparsed":
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a catalog is served at {probe.target_url} and does not parse "
                      f"({s['reason']}), so there is "
                      f"no catalog record for the product to carry {WHAT}; {UNMEASURED}",
                      params)
    f = s["fields"]
    if s["kind"] == "no_record":
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a catalog is served at {probe.target_url} and holds "
                      f"no catalog record for the product among its "
                      f"{f.get('catalog_records')} record(s), so none carries {WHAT}; "
                      f"{UNMEASURED}", params)
    clause = d.clauses_for(LEG, params)["lineage"]
    n = int(f["product_records"])
    k = d.clause_counts(f, {"lineage": clause})["lineage"]
    attributed = d.clause_counts(f, {"a": {"any_of": ["qualifiedAttribution"]}})["a"]
    context = f"(`qualifiedAttribution` on {attributed} of {n})"
    if k == n:
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"all {n} catalog record(s) for the product at {probe.target_url} name "
                      f"a lineage ({d.fields_of(clause)}) {context}; {UNMEASURED}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"{n - k} of {n} catalog record(s) for the product at {probe.target_url} "
                  f"lack a lineage field ({d.fields_of(clause)}) {context}; {UNMEASURED}",
                  params)
