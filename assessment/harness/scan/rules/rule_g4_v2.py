"""G4 v2 — "no catalog record for the product" is reached only over every declared inventory.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4, DN-012 d1 and d3, audit C-04. This
leg reads D4's catalog observation (`CONSUMES`), and `RULE-G4-v1` inherited D4's scope: the
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
are `RULE-G4-v1`'s, sentence for sentence. `RULE-G4-v1` stays in `REGISTRY`, unedited.

`RULE-G4-v1`'s own account of the field follows.

G4 v1 — the issuing authority is carried as structured metadata on the product's catalog record.

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
from . import _scope as sc

RULE_ID, LEG = "RULE-G4-v2", "G4"
CONSUMES = ("D4",)
CLAIM = "absence"
MEASURES = "product"

WHAT = "the issuing authority as `bureauCode` and `programCode`"
UNMEASURED = ("not measured: the statutory mandate and the statistical-versus-administrative "
              "provenance, for which no admitted document names a field")


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
