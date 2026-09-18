"""D3 v1 — source lineage published on the product's catalog record.

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

RULE_ID, LEG = "RULE-D3-v1", "D3"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "a source lineage"
UNMEASURED = ("not measured: whether the named lineage reaches from collection through "
              "processing to the product, which would mean dereferencing the activities")


def judge(observations: list, params: dict):
    s = d.read(observations, params)
    obs = s["obs"]
    if s["kind"] == "empty":
        return c.empty(RULE_ID, LEG, params)
    if s["kind"] == "unobserved":
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog could not be observed: {s['probe'].error_class}", params)
    if s["kind"] == "scope":
        return c.absence_verdict(RULE_ID, LEG, obs, params, candidates=obs, blind=s["blind"],
                                 what=f"whether a catalog record carries {WHAT}")
    if s["kind"] == "no_catalog":
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"no public data.json catalog served on this host, so there is "
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
