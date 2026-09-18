"""B5 v1 — the same concept carries the same identifier across a body's products.

`cc_tasks/2026-09-18_schema_field_rules.md` decision 5. Pre-registered before cycle 5
(2026-10-05), which is the first cycle that judges it.

**The first rule that compares collected surfaces rather than judging one.** Its subject is the
BODY at host level (`MEASURES = "host"`, `SCOPE = "body"`): the group it is handed is every A6
observation of the body's product surfaces on one cycle, assembled by `rules.body_groups` — the
one function `run.py` and `rederive.py` both call, so a cycle and a re-derivation cannot group
differently. The Finding's target is the body's well-known row, `host:<netloc>`, which is the
host-level subject A12 already judges on.

**The field.** `corpus/kernel/schema-org-definedterm.md` (doc_id `schema-org-definedterm`):
`termCode` is "A code that identifies this DefinedTerm within a DefinedTermSet" and
`inDefinedTermSet` is "A DefinedTermSet that contains this term"; "Use the name property for the
term being defined". So a term's CONCEPT is its name and its IDENTIFIER is the pair
(`inDefinedTermSet`, `termCode`) — a code identifies a term only within its set.

**The verdict**, over the body's product surfaces (`params.b5_consistency`):

* no product surface carries a `DefinedTerm` with a `termCode` → `fail`, no term codes;
* a coded term carries no `inDefinedTermSet` → `fail`: the code identifies nothing to compare;
* a concept that appears on two or more products carries different identifiers → `fail`;
* no concept appears coded on two products → `not_applicable`: nothing is compared, and a rule
  that has compared nothing has not found consistency;
* otherwise → `pass`, naming how many concepts were compared.

**What is NOT measured**, and every verdict says so: the cross-VINTAGE half of the definition.
It needs a second cycle whose product surfaces carry term codes, and the rule and the record both
declare it `unmeasured_until` that cycle (decision 5) rather than dropping it.

`fail` on the first two outcomes is an absence claim, so a blind product surface with nothing
found on the observed ones owes `error` (`_common.absence_verdict`); an inconsistency is
established by what was seen and no blind surface can unsee it.
"""
from __future__ import annotations

from . import _common as c
from . import _schema_terms as s
from ..model import Finding

RULE_ID, LEG = "RULE-B5-v1", "B5"
CONSUMES = ("A6",)
CLAIM = "absence"
MEASURES = "host"
#: Judged once per body over its product surfaces, never per surface (`rules.body_groups`).
SCOPE = "body"
#: Decision 5: the clause this version cannot reach, declared rather than dropped.
UNMEASURED_UNTIL = "second cycle with term codes"

UNMEASURED = ("not measured: the cross-vintage half (same concept, same identifier across "
              "vintages), unmeasured until a second cycle with term codes")


def target_of(obs: list) -> str:
    """The body's well-known row: `host:<netloc>` of the surfaces in the group. `body_groups`
    groups by that netloc, so every observation in a group agrees."""
    return f"host:{c.host_of(obs[0].target_url)}" if obs else "unknown"


def _make(obs: list, verdict: str, reason: str, params: dict, **counts) -> Finding:
    """`_common.make` with the BODY as the target rather than the first observation's surface."""
    return Finding.make(rule_id=RULE_ID, rule_version=c.rule_version(RULE_ID, params), leg=LEG,
                        target_doc_id=target_of(obs), verdict=verdict, evidence=c.ids(obs),
                        reason=reason, params=params, **counts)


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == "A6"]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return _make(obs, "error", f"no product surface of the body could be observed: "
                                   f"{obs[0].error_class}", params)
    blind = [o for o in obs if c.unobserved(o, params)]
    # Each surface's state; a blind one is skipped here and counted above.
    states = {o.target_doc_id: s.state(o, params) for o in obs if o not in blind}
    for o in obs:
        if o in blind:
            continue
        # The per-probe guard every generation-4+ rule calls; `blind` above already holds
        # these, so it never fires here — it is what keeps the lint's promise checkable.
        guard = c.unobserved_error(RULE_ID, LEG, obs, o, params, "a product surface")
        if guard:
            return guard
    marked = {d: st["markup"] for d, st in states.items() if st["kind"] == "markup"}
    unextracted = sorted(d for d, st in states.items() if st["kind"] == "unextracted")
    if not marked and not unextracted:
        return _make(obs, "not_applicable",
                     f"none of the body's {len(obs)} product surface(s) is an HTML page, so "
                     f"none carries embedded markup", params)
    coded = {d: [t for t in m["terms"] if t["code"]] for d, m in marked.items()}
    carrying = {d: ts for d, ts in coded.items() if ts}
    if not carrying:
        # An absence over the body's surfaces: a surface not seen, or seen and not extracted,
        # might have been the one carrying the codes.
        unseen = blind + [o for o in obs if o.target_doc_id in unextracted]
        scoped = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=obs, blind=unseen,
                                   what="whether any product of the body carries term codes")
        if scoped is not None:
            return _make(obs, "error", scoped.reason, params, blind_candidates=len(unseen))
        return _make(obs, "fail",
                     f"no term codes: none of the body's {len(marked)} product page(s) carries "
                     f"a schema.org `DefinedTerm` with a `termCode`, so no concept has an "
                     f"identifier to compare; {UNMEASURED}", params)
    unset = sorted({(d, t["name"] or "(unnamed)") for d, ts in carrying.items() for t in ts
                    if not t["set"]})
    if unset:
        return _make(obs, "fail",
                     f"codes without a set: {len(unset)} coded `DefinedTerm`(s) carry no "
                     f"`inDefinedTermSet`, and a `termCode` identifies a term only within its "
                     f"set; first: {unset[0][1]} on {unset[0][0]}; {UNMEASURED}", params)
    ids: dict = {}
    for d, ts in carrying.items():
        for t in ts:
            k = s.concept(t["name"])
            if k:
                ids.setdefault(k, {}).setdefault(d, set()).add((t["set"], t["code"]))
    shared = {k: per for k, per in ids.items() if len(per) >= 2}
    if not shared:
        return _make(obs, "not_applicable",
                     f"term codes are carried on {len(carrying)} of the body's product "
                     f"page(s) and no concept is coded on two of them, so there is nothing to "
                     f"compare; {UNMEASURED}", params)
    split = sorted(k for k, per in shared.items()
                   if len(set().union(*per.values())) > 1)
    n_blind = f"; {len(blind)} product surface(s) not observed" if blind else ""
    if split:
        k = split[0]
        seen = sorted(f"{code} in {cset}" for cset, code in set().union(*shared[k].values()))
        return _make(obs, "fail",
                     f"codes not shared across products: {len(split)} of {len(shared)} "
                     f"concept(s) coded on two or more of the body's products carry different "
                     f"identifiers; first: {k!r} as {', '.join(seen)}{n_blind}; {UNMEASURED}",
                     params)
    return _make(obs, "pass",
                 f"all {len(shared)} concept(s) coded on two or more of the body's products "
                 f"carry one identifier (`termCode` within `inDefinedTermSet`){n_blind}; "
                 f"{UNMEASURED}", params)
