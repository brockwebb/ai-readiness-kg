"""B4 v1 — data-quality attributes published as metadata on the product's catalog record.

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

RULE_ID, LEG = "RULE-B4-v1", "B4"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "quality measurements or revision metadata"
UNMEASURED = ("not measured: the suppression-rules clause, for which no admitted document names "
              "a machine-readable field")


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
