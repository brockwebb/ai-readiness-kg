"""D3 Interpretability — metadata standard (DCAT-US / Project Open Data).

Scores whether a dataset record carries the DCAT-required descriptive fields, so a
machine has standardized metadata rather than ad-hoc prose.

PASS    all four anchor fields present (title, description, keyword, and a
        publisher or contactPoint).
PARTIAL some but not all present.
FAIL    essentially none (title only / empty record).
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe

# DCAT-US required/expected descriptive fields used as the conformance anchors.
_ANCHORS = ("title", "description", "keyword")


class MetadataStandardProbe(MetadataProbe):
    probe_id = "d3_metadata_standard"
    dimension = "D3"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        present = [f for f in _ANCHORS if dataset.get(f)]
        has_contact = bool(dataset.get("publisher") or dataset.get("contactPoint"))
        score_count = len(present) + (1 if has_contact else 0)
        if score_count == len(_ANCHORS) + 1:
            return Score.PASS, f"DCAT anchors present: {present} + publisher/contactPoint"
        # Title alone (or nothing) is essentially no machine metadata.
        if score_count <= 1:
            return Score.FAIL, "essentially no DCAT descriptive metadata (title at most)"
        return Score.PARTIAL, (
            f"partial DCAT metadata: {present}"
            f"{' + contact' if has_contact else ''}")
