"""B1 v4 — "no catalog record for the product" is reached only over a complete seeded search.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1:
existence is not discoverability. D4 and its four consumers are existence legs: whether the
body's products are listed in an inventory it publishes or that data.gov harvests. `RULE-B1-v3`
reached its catalog through `_dcat_fields.read_inventory` over EVERY catalog the D4 leg
observed, the product host's own `/data.json` included, which D4's collector fetches whether or
not anyone recorded it. That host-root `/data.json` is the convention location a machine tries
first (OMB M-13-13), so it is discoverability's evidence (`rule_a13.py`), not existence's.

**What v4 decides differently, and only this.** The catalog state is read over the catalogs
observed at RECORDED inventory locations (`_existence.read_recorded_inventory`), and each of the
four absence kinds is reached as `fail` only when every recorded inventory was observed AND every
seed source was searched for the body's inventory (`_existence.remainder`). Otherwise it is
`error`, naming the inventory not verified or the sources not searched. Every field test over a
record that WAS found, and every reason fragment, is `RULE-B1-v3`'s. `RULE-B1-v3` stays in `REGISTRY`,
unedited.

`RULE-B1-v3`'s own account follows.

B1 v3 — "no catalog record for the product" is reached only over every declared inventory.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4, DN-012 d1 and d3, audit C-04. This
leg's catalog half reads D4's catalog observation (`CONSUMES`), and `RULE-B1-v2` inherited D4's
scope: the product HOST's `/data.json`, and nothing else. ind:D4 says "data.gov/agency
inventory", and data.gov reads each DEPARTMENT's data.json (`params.yaml` `dept_domains`). So
"no public data.json catalog served on this host, so there is no catalog record for the product"
was an absence over one of the places the record could be.

**What v3 decides differently, and only this.** Its catalog state is
`_dcat_fields.read_inventory`, which reads every catalog the D4 leg observed, the body's
declared inventories included, and takes the product's records from whichever holds them. Each
of the four absence kinds (`_dcat_fields.ABSENCE_KINDS`: no catalog, a blind catalog, one that
does not parse, one without the product's record) is reached as `fail` only when every declared
inventory was observed and nothing was left undeclared (`_scope.inventory_scope`). Otherwise it
is `error`, naming the inventories not searched. The field tests over records that WERE found
are `RULE-B1-v2`'s, sentence for sentence. `RULE-B1-v2` stays in `REGISTRY`, unedited.

`RULE-B1-v2`'s own account of the field follows.

B1 v2 — variable-level metadata reachable by a machine, from the catalog OR the page.

`cc_tasks/2026-09-18_schema_field_rules.md` §0: "B1's schema.org half (`variableMeasured`) joins
B1's rule from the DCAT task". `RULE-B1-v1` is the DCAT half alone and is shipped; it stays in
`REGISTRY` untouched, and this module is the whole leg.

**Two halves, each named by a document on disk.**

* **DCAT-US** — exactly `RULE-B1-v1`'s reading, over D4's catalog observation: every catalog
  record for the product carries `describedBy` on the dataset or on a distribution
  (`corpus/kernel/dcat-us-1-1-schema.md`, doc_id `dcat-us-1-1-schema`: "used to specify a data
  dictionary or schema that defines fields or column headings in the dataset").
* **schema.org** — a `Dataset` in the product page's markup carries `variableMeasured`
  (`corpus/kernel/schema-org-dataset.md`, doc_id `schema-org-dataset`: "The variableMeasured
  property can indicate (repeated as necessary) the variables that are measured in some dataset,
  either described as text or as pairs of identifier and description using PropertyValue").

**How they combine: either half passes the leg.** They are two vocabularies for one property —
the federal catalog's and the page's — and the indicator asks whether variable-level metadata
reaches a consumer, not in which vocabulary. A body publishing it in one is not failing B1 for
omitting the other. So:

* either half `pass` → `pass`, naming which: existence is established by what was read, and no
  blind or unread half can unfind it;
* otherwise, either half unobserved or unreadable → `error`: the absence claim ranges over both
  surfaces and one was not seen (ISA 705, as `_common.absence_verdict` says);
* otherwise → `fail`, and the reason carries BOTH halves' sentences, so the prescription layer
  matches the action for each (`scripts/tag_prescriptions.py` joins on those fragments).

A surface that is not HTML carries no markup: its schema.org half is not applicable and the
verdict is the DCAT half's.

**What is NOT measured**, and every verdict says so: the CONTENTS — whether the dictionary or the
listed variables carry labels, definitions, units and universes, and whether they are
"comprehensive". That would need the dictionary dereferenced and a coverage threshold
pre-registered, and neither exists.

**The subject is the product** (`MEASURES = "product"`); `fail` is an absence claim.
"""
from __future__ import annotations

from . import _common as c
from . import _dcat_fields as d
from . import _schema_terms as s
from . import _existence as ex
from . import _scope as sc

RULE_ID, LEG = "RULE-B1-v4", "B1"
CONSUMES = ("D4", "A6")
CLAIM = "absence"
MEASURES = "product"

WHAT = "a data dictionary (`describedBy`)"
UNMEASURED = ("not measured: the contents of the dictionary or of the listed variables (labels, "
              "definitions, units, universes) and whether they are comprehensive, which would "
              "need them dereferenced and a coverage threshold pre-registered")


def _dcat_half(observations: list, params: dict) -> tuple:
    """`(kind, sentence)` for the catalog half; kind is pass / fail / error."""
    st = ex.read_recorded_inventory(observations, params, d.read_inventory)
    obs = st["obs"]
    if st["kind"] == "empty":
        return "error", "no catalog observation was collected"
    if st["kind"] == "unobserved":
        return "error", f"the catalog could not be observed: {st['probe'].error_class}"
    if st["kind"] in d.ABSENCE_KINDS:
        remainder = ex.remainder(observations, st["decl"], "inventory", params)
        if remainder:
            return "error", (f"absence not established: whether a catalog record carries "
                             f"{WHAT}: {'; '.join(remainder)}")
    if st["kind"] == "scope":
        return "error", (f"whether a catalog record carries {WHAT} cannot be established: "
                         f"{len(st['blind'])} of {len(obs)} catalog probe(s) were not observed")
    if st["kind"] == "no_catalog":
        return "fail", (f"no public data.json catalog served at any declared inventory, so "
                        f"there is no catalog record for the product to carry {WHAT}")
    probe = st["probe"]
    blind = c.unobserved_error(RULE_ID, LEG, obs, probe, params, "the catalog")
    if blind:
        return "error", blind.reason
    if st["kind"] == "unread":
        return "error", (f"the catalog at {probe.target_url} was served and carries no field "
                         f"extraction: it was collected before `dcat_fields` existed, so {WHAT} "
                         f"cannot be read from it")
    if st["kind"] == "unparsed":
        return "fail", (f"a catalog is served at {probe.target_url} and does not parse "
                        f"({st['reason']}), so there is "
                        f"no catalog record for the product to carry {WHAT}")
    f = st["fields"]
    if st["kind"] == "no_record":
        return "fail", (f"a catalog is served at {probe.target_url} and holds "
                        f"no catalog record for the product among its "
                        f"{f.get('catalog_records')} record(s), so none carries {WHAT}")
    clause = d.clauses_for(LEG, params)["data_dictionary"]
    n = int(f["product_records"])
    k = d.clause_counts(f, {"data_dictionary": clause})["data_dictionary"]
    if k == n:
        return "pass", (f"all {n} catalog record(s) for the product at {probe.target_url} link "
                        f"a data dictionary ({d.fields_of(clause)})")
    return "fail", (f"{n - k} of {n} catalog record(s) for the product at {probe.target_url} "
                    f"lack a data dictionary ({d.fields_of(clause)})")


def _schema_half(observations: list, params: dict) -> tuple:
    """`(kind, sentence)` for the markup half; kind is pass / fail / error / not_applicable."""
    obs = [o for o in observations if o.leg == "A6"]
    if not obs:
        return "error", "no markup observation of the product page was collected"
    probe = obs[0]
    blind = c.unobserved_error(RULE_ID, LEG, obs, probe, params, "the product page")
    if blind:
        return "error", blind.reason
    st = s.state(probe, params)
    if st["kind"] == "not_html":
        return "not_applicable", (f"the surface is {st['content_type']}, which carries no "
                                  f"embedded markup")
    if st["kind"] == "unextracted":
        return "error", (f"the product page was served and its markup was not extracted "
                         f"({st['reason']})")
    m = st["markup"]
    if m["variable_measured"]:
        return "pass", (f"{m['variable_measured']} of {m['datasets']} schema.org `Dataset`(s) "
                        f"in the markup at {probe.target_url} list `variableMeasured`")
    if m["datasets"]:
        return "fail", (f"the {m['datasets']} schema.org `Dataset`(s) in the markup at "
                        f"{probe.target_url} list no `variableMeasured`")
    return "fail", (f"the product page at {probe.target_url} carries no schema.org `Dataset`, "
                    f"so its markup lists no `variableMeasured`")


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in CONSUMES]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    dk, ds = _dcat_half(obs, params)
    sk, ss = _schema_half(obs, params)
    if dk == "pass" or sk == "pass":
        which = "; ".join(x for k, x in ((dk, ds), (sk, ss)) if k == "pass")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"variable-level metadata is reachable: {which}; {UNMEASURED}", params)
    if "error" in (dk, sk):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"whether variable-level metadata is reachable cannot be established: "
                      f"catalog half — {ds}; markup half — {ss}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"variable-level metadata is not reachable by a machine: {ds}; and {ss}; "
                  f"{UNMEASURED}", params)
