"""The entity collapse, implemented ONCE (task 2026-09-04_kg_diagnostic_and_cq_harness §1.3).

§1.3 permits "a Cypher fragment **or a Python post-join**" and forbids per-CQ collapse logic.
This is the post-join: every CQ declares `collapse_on`, the column whose entity duplicates are
unioned, and every CQ goes through `collapse_rows`. No CQ carries collapse logic of its own,
which is why the CQ records have no `cypher_collapsed` field — a second hand-written query per
question is exactly the thing §1.3 rules out.

**Two levels, in order:**

1. `canonical_key(text)` — `toLower(trim(text))` with internal whitespace normalised. This is
   the same weak key `scripts/kg_diagnostic.py` counts duplicates with: it merges only what
   nobody could dispute is the same string, so the collapse is a floor on redundancy rather
   than a guess at identity.
2. `aliases` — if row A's entity name appears in row B's `aliases`, or the reverse, the two
   join the same group. Transitive: A~B and B~C puts all three together, by union-find. The
   graph carries `aliases` on 8,129 of 8,662 Concepts, so this level is where most of the
   non-obvious merging is available.

What this is NOT: entity resolution. There is no embedding, no edit distance, no type
checking, no disambiguation of a name that legitimately denotes two different things. That is
deliberate — the point of the collapsed view is to measure what the *cheapest defensible*
merge would buy, so the decision rule in §1.5 is not reading an optimistic upper bound.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

_WS = re.compile(r"\s+")


def canonical_key(text: Any) -> Optional[str]:
    """`toLower(trim(text))` with internal whitespace collapsed. None for a null/blank."""
    if text is None:
        return None
    s = _WS.sub(" ", str(text)).strip().lower()
    return s or None


class _Union:
    """Union-find over group keys, so alias links are transitive."""

    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def build_groups(rows: Sequence[dict], collapse_on: str,
                 alias_index: Optional[Dict[str, Iterable[str]]] = None) -> Dict[str, str]:
    """value-key -> group-key, for every distinct value of `collapse_on` in `rows`.

    `alias_index` maps a canonical name to the canonical names it lists as aliases; it is
    built once per run from the graph, not per CQ.
    """
    keys = {k for k in (canonical_key(r.get(collapse_on)) for r in rows) if k}
    uf = _Union()
    for k in keys:
        uf.find(k)
    if alias_index:
        for k in keys:
            for alias in alias_index.get(k, ()):  # A lists B
                a = canonical_key(alias)
                if a in keys:
                    uf.union(k, a)
        for other, aliases in alias_index.items():   # B lists A
            if other not in keys:
                continue
            for alias in aliases:
                a = canonical_key(alias)
                if a in keys:
                    uf.union(other, a)
    return {k: uf.find(k) for k in keys}


def collapse_rows(rows: Sequence[dict], collapse_on: str,
                  alias_index: Optional[Dict[str, Iterable[str]]] = None) -> dict:
    """Collapse `rows` on `collapse_on`. Returns:

        rows              one row per group, carrying `_members` (the distinct raw values that
                          merged) and `_row_count` (raw rows behind the group)
        groups            value-key -> group-key
        dup_groups        number of groups of SIZE > 1 — groups into which more than one raw
                          row (i.e. more than one graph node) merged. This is §1.4's
                          `dup_groups_unioned`: the Zaveri conciseness cost this question
                          actually paid. Counting distinct member STRINGS instead would read
                          zero for the commonest case in this graph — fourteen nodes all
                          named "AI readiness" share one canonical key — which is the
                          duplication the measurement exists to see.
        rows_raw / rows_collapsed
    """
    groups = build_groups(rows, collapse_on, alias_index)
    out: Dict[str, dict] = {}
    for r in rows:
        k = canonical_key(r.get(collapse_on))
        g = groups.get(k) if k else None
        if g is None:                       # null key: never merged, kept as its own row
            out[f"\x00null\x00{len(out)}"] = dict(r, _members=[], _row_count=1)
            continue
        if g not in out:
            out[g] = dict(r, _members=[], _row_count=0)
        if k not in out[g]["_members"]:
            out[g]["_members"].append(k)
        out[g]["_row_count"] += 1
    collapsed: List[dict] = list(out.values())
    return {"rows": collapsed,
            "groups": groups,
            "dup_groups": sum(1 for r in collapsed if (r.get("_row_count") or 0) > 1),
            "rows_raw": len(rows),
            "rows_collapsed": len(collapsed)}


def load_alias_index(session) -> Dict[str, List[str]]:
    """canonical name -> canonical aliases, from every node carrying `aliases`. Built once
    per run and passed to every CQ, so the alias level is not re-queried per question."""
    index: Dict[str, List[str]] = {}
    rows = session.run(
        "MATCH (n) WHERE n.aliases IS NOT NULL AND n.name IS NOT NULL "
        "RETURN n.name AS name, n.aliases AS aliases").data()
    for r in rows:
        key = canonical_key(r["name"])
        if not key:
            continue
        aliases = r["aliases"]
        if isinstance(aliases, str):
            aliases = [aliases]
        vals = [canonical_key(a) for a in (aliases or [])]
        index.setdefault(key, []).extend([v for v in vals if v and v != key])
    return index


def load_canonical_index(session) -> Dict[str, List[str]]:
    """canonical name -> the other canonical names that RESOLVE TO THE SAME vocabulary term.

    The third view (task 2026-09-05_vocabulary_and_entity_linking §4). It is deliberately the
    SAME shape as `load_alias_index`, so `collapse_rows` needs no new code path and no CQ
    carries view-specific logic — the module's own rule, restated: the collapse is implemented
    once. What changes between the collapsed and canonical views is only which index is
    handed in, which is exactly the difference the two views are meant to measure:

        collapsed   what the CHEAPEST DEFENSIBLE merge buys — identical strings, plus the
                    model's own `aliases` property. A floor on redundancy.
        canonical   what a CURATED VOCABULARY buys — every name a `RESOLVES_TO` edge points
                    at one term, whether it got there by the deterministic alias-first rule
                    or by a judged decision in the clerical band.

    Names on nodes carrying no `RESOLVES_TO` edge appear in no group here, so an unresolved
    entity stays its own group and the canonical view never merges what the vocabulary
    declined to name. That is the property that keeps this view honest: it can only look
    better than `collapsed` where the vocabulary actually did work.
    """
    index: Dict[str, List[str]] = {}
    rows = session.run(
        "MATCH (n)-[:RESOLVES_TO]->(t:Term) WHERE n.name IS NOT NULL "
        "RETURN t.term_id AS term, collect(DISTINCT n.name) AS names").data()
    for r in rows:
        keys = sorted({k for k in (canonical_key(n) for n in r["names"]) if k})
        if len(keys) < 2:
            continue
        for k in keys:
            index.setdefault(k, []).extend([o for o in keys if o != k])
    return index
