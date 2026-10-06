"""B4 v2 — "no catalog record for the product" is reached only over every declared inventory.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4, DN-012 d1 and d3, audit C-04. This
leg reads D4's catalog observation (`CONSUMES`), and `RULE-B4-v1` inherited D4's scope: the
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
are `RULE-B4-v1`'s, sentence for sentence. `RULE-B4-v1` stays in `REGISTRY`, unedited.

`RULE-B4-v1`'s own account of the field follows.

B4 v1 — data-quality attributes published as metadata on the product's catalog record.

`cc_tasks/2026-09-18_dcat_field_rules.md` decisions 1 to 3. Pre-registered before cycle 5
(2026-10-05), which is the first cycle that judges it.

**The fields.** DCAT-US 3 (`corpus/kernel/dcat-us-3-dataset-schema.md`, doc_id
`dcat-us-3-dataset-schema`) names one for each of two of the definition's three clauses:

* error measures — `hasQualityMeasurement`, "List of quality measurements for the dataset (for
  example, completeness, accuracy, or timeliness) beyond spatial or temporal resolution";
* revisions policy — `versionNotes`, "Notes describing how this version differs from earlier
  versions of the dataset", beside `previousVersion`, "reference to the previous dataset
  version", and `hasCurrentVersion`, "reference to the current (latest) version of a dataset".

The definition's own test is "published as metadata, not prose"; a field in the catalog record
is the metadata. Each clause is its own failing outcome, so a record carrying one and not the
other is prescribed only the half it lacks.

**The suppression-rules clause is NOT measured**, and every verdict says so: no admitted document
names a machine-readable suppression field — the same failed search that leaves G5 unassigned
(`cc_tasks/2026-09-17_unassigned_indicators_RESULT.md` §2).

**The subject is the product's catalog record** (`MEASURES = "product"`), following D4, which
reads the same catalog for the same product; the catalog is D4's observation (`CONSUMES`).
`fail` is an absence claim (`CLAIM = "absence"`).
"""
from __future__ import annotations

from . import _common as c
from . import _dcat_fields as d
from . import _scope as sc

RULE_ID, LEG = "RULE-B4-v2", "B4"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "quality measurements or revision metadata"
UNMEASURED = ("not measured: the suppression-rules clause, for which no admitted document names "
              "a machine-readable field")


def judge(observations: list, params: dict):
    s = d.read_inventory(observations, params)
    obs = s["obs"]
    if s["kind"] == "empty":
        return c.empty(RULE_ID, LEG, params)
    if s["kind"] == "unobserved":
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the catalog could not be observed: {s['probe'].error_class}", params)
    if s["kind"] in d.ABSENCE_KINDS:
        remainder = sc.inventory_scope(obs, sc.declared(obs), params)
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
    clauses = d.clauses_for(LEG, params)
    n = int(f["product_records"])
    k = d.clause_counts(f, clauses)
    q, r = clauses["quality_measurement"], clauses["revision_metadata"]
    kq, kr = k["quality_measurement"], k["revision_metadata"]
    if kq == n and kr == n:
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"all {n} catalog record(s) for the product at {probe.target_url} carry "
                      f"a quality measurement ({d.fields_of(q)}) and revision metadata "
                      f"({d.fields_of(r)}); {UNMEASURED}", params)
    lacks = []
    if kq < n:
        lacks.append(f"{n - kq} of {n} lack a quality measurement ({d.fields_of(q)})")
    if kr < n:
        lacks.append(f"{n - kr} of {n} lack revision metadata ({d.fields_of(r)})")
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"the product's catalog record(s) at {probe.target_url} do not publish "
                  f"quality as metadata: {'; '.join(lacks)}; {UNMEASURED}", params)
