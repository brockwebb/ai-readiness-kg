"""D3 Interpretability — access-tier metadata.

Folded in from the retired can't-vs-hasn't gate (CC task 2026-06-23, 1A): this is
an interpretability property of the *public catalog*, NOT access to protected data.
Where a public catalog points at a restricted dataset, a machine should be able to
learn *that* it is restricted and *why*. Protected data itself is out of scope.

PASS    `accessLevel` declared AND, if not public, a machine-readable `rights`
        statement explains the restriction.
PARTIAL `accessLevel` declared as non-public but no `rights` reason given.
FAIL    no `accessLevel` at all (a machine cannot tell the tier).
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe

_PUBLIC = "public"


class AccessTierProbe(MetadataProbe):
    probe_id = "d3_access_tier"
    dimension = "D3"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        level = (dataset.get("accessLevel") or "").strip().lower()
        if not level:
            return Score.FAIL, "no machine-readable accessLevel (tier undiscoverable)"
        if level == _PUBLIC:
            return Score.PASS, "accessLevel=public, tier machine-readable"
        # Non-public: a machine should learn WHY.
        if dataset.get("rights"):
            return Score.PASS, (
                f"accessLevel={level!r} with machine-readable rights/reason")
        return Score.PARTIAL, (
            f"accessLevel={level!r} declared but no machine-readable reason (rights)")
