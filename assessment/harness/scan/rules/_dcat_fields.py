"""What the four DCAT-US structured-field rules (B1, B4, D3, G4) share. Pure.

`cc_tasks/2026-09-18_dcat_field_rules.md`. Each rule reads the catalog D4 already fetches
(`CONSUMES = ("D4",)`), through the `dcat_fields` block `v2clauses.dcat_record_fields` puts on
the D4 observation. This module finds that block and tests clauses over it; it says nothing.
Every sentence a Finding carries is written in the rule module, because the prescription layer
anchors on reason fragments checked against the CURRENT rule module's own source
(`scripts/tag_prescriptions.py` `OUTCOMES`), and a sentence assembled here would be verbatim in
no rule at all.

**The subject is the product's catalog record** (decision 1), following D4, which reads the same
catalog and judges membership of the same product. A catalog record is D4's: a dataset entry in
which the surface's URL appears.
"""
from __future__ import annotations

from . import _common as c

#: The `dcat_fields` scheme these rules understand (`v2clauses.DCAT_FIELDS_SCHEME`). A block of
#: another scheme is not read as if it were this one.
SCHEME = 1


def read(observations: list, params: dict) -> dict:
    """The state of the product's catalog evidence, as one of these `kind`s:

    * `empty`       — no D4 observation in the group;
    * `unobserved`  — every catalog probe was blind (`_common.only_errors`);
    * `scope`       — no catalog was served AND some probe was blind: an absence over an
                      incomplete candidate set, which owes `error` (`_common.absence_verdict`);
    * `no_catalog`  — every probe answered and none served a catalog;
    * `unread`      — a catalog was served and carries no `dcat_fields` block of this scheme:
                      it was collected before the block existed, so nothing can be read from it;
    * `unparsed`    — a catalog was served and does not parse as a JSON object;
    * `no_record`   — the catalog parses and no entry in it is the product's;
    * `records`     — the product has catalog records; `fields` is the block.

    `obs` is the catalog observations and `probe` the one the verdict rests on, which every
    rule passes through `_common.unobserved_error` before scoring on it.
    """
    obs = [o for o in observations if o.leg == "D4"]
    if not obs:
        return {"kind": "empty", "obs": obs}
    if c.only_errors(obs, params):
        return {"kind": "unobserved", "obs": obs, "probe": obs[0]}
    served = [o for o in obs if (o.parsed or {}).get("present")]
    if not served:
        blind = [o for o in obs if c.unobserved(o, params)]
        if blind:
            return {"kind": "scope", "obs": obs, "blind": blind}
        return {"kind": "no_catalog", "obs": obs}
    probe = served[0]
    block = (probe.parsed or {}).get("dcat_fields")
    if not isinstance(block, dict) or block.get("scheme") != SCHEME:
        return {"kind": "unread", "obs": obs, "probe": probe}
    if not block.get("parsed"):
        return {"kind": "unparsed", "obs": obs, "probe": probe,
                "reason": block.get("reason") or "no reason recorded"}
    if not block.get("product_records"):
        return {"kind": "no_record", "obs": obs, "probe": probe, "fields": block}
    return {"kind": "records", "obs": obs, "probe": probe, "fields": block}


def satisfies(carried, clause: dict) -> bool:
    """Whether one record's carried fields satisfy one clause (`any_of` / `all_of`)."""
    have = set(carried)
    if "all_of" in clause:
        return set(clause["all_of"]) <= have
    return bool(have & set(clause.get("any_of") or ()))


def clause_counts(block: dict, clauses: dict) -> dict:
    """`{clause: records satisfying it}` over the product's catalog records."""
    out = {name: 0 for name in clauses}
    for prof in block.get("product_record_profiles") or []:
        for name, clause in clauses.items():
            if satisfies(prof.get("carried") or (), clause):
                out[name] += int(prof.get("records") or 0)
    return out


def clauses_for(leg: str, params: dict) -> dict:
    return params["dcat_fields"]["clauses"][leg]


def fields_of(clause: dict) -> str:
    """`describedBy` or `distribution.describedBy` — the clause's fields, for a sentence."""
    names = clause.get("all_of") or clause.get("any_of") or ()
    joiner = " and " if "all_of" in clause else " or "
    return joiner.join(f"`{n}`" for n in names)
