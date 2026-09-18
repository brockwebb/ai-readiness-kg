"""B1 v1 — the DCAT half: a data dictionary is linked from the product's catalog record.

`cc_tasks/2026-09-18_dcat_field_rules.md` decisions 1 to 3. Pre-registered before cycle 5
(2026-10-05), which is the first cycle that judges it.

**The field.** DCAT-US 1.1 (`corpus/kernel/dcat-us-1-1-schema.md`, doc_id `dcat-us-1-1-schema`)
names `describedBy`, "used to specify a data dictionary or schema that defines fields or column
headings in the dataset", at two levels: on the dataset ("At the dataset level it's assumed to be
a human readable HTML webpage or PDF document") and on a distribution ("If this is a machine
readable file, it's recommended to be specified with describedBy at the distribution level along
with the associated `describedByType`"). A record carries the clause when either level does.

**This is B1's DCAT half.** The schema.org half (`variableMeasured`, read by `structured_data`)
is `cc_tasks/2026-09-18_schema_field_rules.md`'s, which joins it to this leg as a new version;
this module is not edited for it.

**What is NOT measured**, and every verdict says so: the dictionary's CONTENTS. The rule reads
that a record links a data dictionary; whether that dictionary carries labels, definitions,
units and universes, and whether it is "comprehensive", would need the dictionary dereferenced
and a coverage threshold pre-registered, and neither exists.

**The subject is the product's catalog record** (`MEASURES = "product"`), following D4, which
reads the same catalog for the same product; the catalog is D4's observation (`CONSUMES`).
`fail` is an absence claim (`CLAIM = "absence"`).
"""
from __future__ import annotations

from . import _common as c
from . import _dcat_fields as d

RULE_ID, LEG = "RULE-B1-v1", "B1"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "a data dictionary (`describedBy`)"
UNMEASURED = ("not measured: the dictionary's contents (labels, definitions, units, universes) "
              "and whether they are comprehensive, which would need the dictionary dereferenced "
              "and a coverage threshold pre-registered")


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
    clause = d.clauses_for(LEG, params)["data_dictionary"]
    n = int(f["product_records"])
    k = d.clause_counts(f, {"data_dictionary": clause})["data_dictionary"]
    if k == n:
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"all {n} catalog record(s) for the product at {probe.target_url} link a "
                      f"data dictionary ({d.fields_of(clause)}); {UNMEASURED}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"{n - k} of {n} catalog record(s) for the product at {probe.target_url} "
                  f"lack a data dictionary ({d.fields_of(clause)}); {UNMEASURED}", params)
