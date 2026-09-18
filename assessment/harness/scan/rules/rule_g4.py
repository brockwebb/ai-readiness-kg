"""G4 v1 — the issuing authority is carried as structured metadata on the product's catalog record.

`cc_tasks/2026-09-18_dcat_field_rules.md` decisions 1 to 3. Pre-registered before cycle 5
(2026-10-05), which is the first cycle that judges it.

**The field.** DCAT-US 1.1 (`corpus/kernel/dcat-us-1-1-schema.md`, doc_id `dcat-us-1-1-schema`)
requires two authority codes on every federal dataset record: `bureauCode`, "combined agency and
bureau code from OMB Circular A-11, Appendix C ... in the format of `015:11`", and `programCode`,
"the primary program related to this data asset, from the Federal Program Inventory ... Use the
format of `015:001`". It says why it added them: "to ensure every dataset is connected in a
standard way with an agency bureau" and "with an agency program office". A record carries the
clause when it carries BOTH, each well-formed in the stated format (`params.dcat_fields`).

**The subject is the product's catalog record** (`MEASURES = "product"`), following D4, which
reads the same catalog for the same product. It reads nothing of its own — the catalog is D4's
observation (`CONSUMES`) — so the host is asked for `/data.json` once.

**Two of the definition's three clauses are NOT measured,** and every verdict says so: no
admitted document names a field for the statutory mandate or for the statistical-versus-
administrative distinction (the failed search is `cc_tasks/2026-09-17_unassigned_indicators_
RESULT.md` §2). A pass here is a pass on the authority clause alone.

`fail` is an absence claim (`CLAIM = "absence"`): no catalog, no record for the product, or a
record without the codes. An absence over a candidate set with a blind member is `error`
(`_common.absence_verdict`).
"""
from __future__ import annotations

from . import _common as c
from . import _dcat_fields as d

RULE_ID, LEG = "RULE-G4-v1", "G4"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "the issuing authority as `bureauCode` and `programCode`"
UNMEASURED = ("not measured: the statutory mandate and the statistical-versus-administrative "
              "provenance, for which no admitted document names a field")


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
    clause = d.clauses_for(LEG, params)["authority_codes"]
    n = int(f["product_records"])
    k = d.clause_counts(f, {"authority_codes": clause})["authority_codes"]
    cat = f.get("catalog_records_carrying") or {}
    context = (f"(across the whole catalog, `bureauCode` is carried on "
               f"{cat.get('bureauCode', 0)} and `programCode` on {cat.get('programCode', 0)} of "
               f"{f.get('catalog_records')} record(s))")
    if k == n:
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"all {n} catalog record(s) for the product at {probe.target_url} carry "
                      f"{d.fields_of(clause)}, well-formed {context}; {UNMEASURED}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"{n - k} of {n} catalog record(s) for the product at {probe.target_url} "
                  f"lack a valid `bureauCode` and `programCode` {context}; {UNMEASURED}",
                  params)
