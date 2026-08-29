#!/usr/bin/env python3
"""Cross-chunk type reconciliation (v0.3.7; ADDENDUM-01 §2.4, built under ADDENDUM-03 §1.4).

Chunk-local extraction sees each entity several times, once per chunk that mentions it, and
the type it receives can differ between those views: a named metric is a `Concept` where a
chunk merely refers to it and an `Instrument` where a chunk describes it being applied. That
is not model error — it is the honest consequence of a local view — so it is resolved once, at
the deterministic merge step, instead of being pushed back onto the model as an instruction it
cannot reliably follow.

The rule, in order, mechanical and logged per entity:

  1. **Instrument evidence wins.** If any chunk grounded the entity as an Instrument, it is an
     Instrument. Asymmetric on purpose: describing something as an applied instrument is a
     *positive* observation, while typing it as a Concept is the default a chunk falls back to
     when it says nothing more. Presence of evidence outranks absence of evidence, so a
     majority of uninformative views must not outvote one informative one.
  2. **Majority** of the remaining observations.
  3. **`type_conflict`** on a tie: flagged, excluded from strata pooling, never silently
     resolved by ordering. A coin flip here would put an arbitrary type into the graph and
     leave no trace that it was arbitrary.

No LLM adjudication: that is the sift-kg three-layer design and a separate pilot (parent task
§4). Everything here is deterministic and replayable from the shard.
"""
from __future__ import annotations

from collections import Counter

#: The type whose evidence outranks a count. See rule 1.
PRIVILEGED_TYPE = "Instrument"

#: Flag for an unresolved entity. Excluded from strata pooling by `poolable`.
TYPE_CONFLICT = "type_conflict"


def normalized_key(name: str) -> str:
    """Merge key: NFKC + case-fold + whitespace collapse (parent task §4, unchanged)."""
    from .grounding import normalize
    return " ".join(normalize(str(name or "")).casefold().split())


def reconcile_type(observations: list[dict]) -> dict:
    """Resolve one entity's type across its per-chunk observations.

    Each observation is `{"type": str, "chunk_id": str, "instrument_evidence": bool}`.
    Returns the decision plus the rule that produced it, so the log is a record of *why*,
    not just what."""
    obs = [o for o in observations if o.get("type")]
    if not obs:
        return {"type": None, "rule": "no_typed_observation", "conflict": True,
                "observed": {}, "n_observations": 0}

    counts = Counter(o["type"] for o in obs)
    instrument_evidence = [o for o in obs
                           if o.get("instrument_evidence") and o["type"] == PRIVILEGED_TYPE]
    if instrument_evidence:
        return {"type": PRIVILEGED_TYPE, "rule": "instrument_evidence_wins", "conflict": False,
                "observed": dict(counts), "n_observations": len(obs),
                "evidence_chunks": [o.get("chunk_id") for o in instrument_evidence]}

    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return {"type": None, "rule": TYPE_CONFLICT, "conflict": True,
                "observed": dict(counts), "n_observations": len(obs),
                "tied": sorted(t for t, c in top if c == top[0][1])}
    return {"type": top[0][0], "rule": "majority", "conflict": False,
            "observed": dict(counts), "n_observations": len(obs)}


def reconcile_document(items: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    """(decisions by merge key, per-entity log) for one document's chunk-local items.

    Each item is `{"name", "type", "chunk_id", "instrument_evidence"?}`."""
    grouped: dict[str, list[dict]] = {}
    names: dict[str, str] = {}
    for it in items:
        key = normalized_key(it.get("name"))
        if not key:
            continue
        grouped.setdefault(key, []).append(it)
        names.setdefault(key, it.get("name"))

    decisions, log = {}, []
    for key, obs in grouped.items():
        d = reconcile_type(obs)
        decisions[key] = d
        log.append({"merge_key": key, "name": names[key], **d,
                    "chunks": [o.get("chunk_id") for o in obs]})
    log.sort(key=lambda r: r["merge_key"])
    return decisions, log


def poolable(decision: dict) -> bool:
    """May this entity enter a stratum? A conflicted type may not — pooling an entity whose
    type is unresolved would put the conflict into the denominator of a gate."""
    return not decision.get("conflict") and bool(decision.get("type"))
