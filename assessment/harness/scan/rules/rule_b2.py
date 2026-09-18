"""B2 v1 — concept definitions published as schema.org `DefinedTerm`s and linked from the
product's variables.

`cc_tasks/2026-09-18_schema_field_rules.md`, taking decisions 1 to 4 of
`cc_tasks/2026-09-18_dcat_field_rules.md` unchanged. Pre-registered before cycle 5 (2026-10-05),
which is the first cycle that judges it.

**The field.** `corpus/kernel/schema-org-definedterm.md` (doc_id `schema-org-definedterm`): "Use
the name property for the term being defined, use termCode if the term has an alpha-numeric code
allocated, use description to provide the definition of the term", with `inDefinedTermSet` "A
DefinedTermSet that contains this term" and `termCode` "A code that identifies this DefinedTerm
within a DefinedTermSet". The node's `tier_field` names all three, so a term carries the clause
only when it has a `termCode`, an `inDefinedTermSet` and a `description`.

**"Linked from variables".** `corpus/kernel/schema-org-dataset.md`: `measurementTechnique` on a
`Dataset` expects a `DefinedTerm`, and `variableMeasured` lists the variables. A term is linked
when it is reachable from a `Dataset` node on the page — which is the only place markup can say
that a variable uses a definition. A glossary page that publishes terms and no dataset carries
published terms that no variable reaches.

**The verdict.** `pass` when at least one term is linked from a `Dataset` and every linked term
carries all three properties. The failing outcomes, in the order they are tested:
no `DefinedTerm` at all; terms none of which is linked; linked terms missing a property.

**What is NOT measured**, and every verdict says so: the "versioned" clause. No admitted document
names a version property on `DefinedTerm` or `DefinedTermSet` (the node's `tier_note` records
the search), so there is no field to read.

**The subject is the product page** (`MEASURES = "product"`), the surface A6 reads; the markup
is A6's observation (`CONSUMES`). `fail` is an absence claim (`CLAIM = "absence"`).
"""
from __future__ import annotations

from . import _common as c
from . import _schema_terms as s

RULE_ID, LEG = "RULE-B2-v1", "B2"
CONSUMES = ("A6",)
CLAIM = "absence"
MEASURES = "product"

UNMEASURED = ("not measured: whether the definitions are versioned, because no admitted "
              "document names a version property on `DefinedTerm` or `DefinedTermSet`")
REQUIRED = "`termCode`, `inDefinedTermSet` and `description`"


def _complete(t: dict) -> bool:
    return bool(t["code"] and t["set"] and t["described"])


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == "A6"]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the product page's markup could not be observed: {obs[0].error_class}",
                      params)
    probe = obs[0]
    blind = c.unobserved_error(RULE_ID, LEG, obs, probe, params, "the product page")
    if blind:
        return blind
    st = s.state(probe, params)
    if st["kind"] == "not_html":
        return c.make(RULE_ID, LEG, obs, "not_applicable",
                      f"the surface is {st['content_type']}, which carries no embedded markup",
                      params)
    if st["kind"] == "unextracted":
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the product page was served and its markup was not extracted "
                      f"({st['reason']}), so whether it carries a `DefinedTerm` cannot be read",
                      params)
    terms = st["markup"]["terms"]
    if not terms:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"no schema.org `DefinedTerm` in the product page's markup at "
                      f"{probe.target_url}, so no concept definition is published there; "
                      f"{UNMEASURED}", params)
    linked = [t for t in terms if t["linked"]]
    if not linked:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(terms)} `DefinedTerm`(s) in the markup at {probe.target_url}, and "
                      f"none is reached from a `Dataset`: the terms are not linked from the "
                      f"product's variables; {UNMEASURED}", params)
    short = [t for t in linked if not _complete(t)]
    if short:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(short)} of {len(linked)} `DefinedTerm`(s) linked from a `Dataset` "
                      f"at {probe.target_url} lack a `termCode`, an `inDefinedTermSet` or a "
                      f"`description`; first: "
                      f"{short[0]['name'] or '(unnamed)'}; {UNMEASURED}", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"all {len(linked)} `DefinedTerm`(s) linked from a `Dataset` at "
                  f"{probe.target_url} carry {REQUIRED}; {UNMEASURED}", params)
