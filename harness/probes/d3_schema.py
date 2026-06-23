"""D3 Interpretability — machine-readable schema.

A `describedBy` link (on the dataset or any distribution) points to a data
dictionary / schema retrievable as data rather than buried in a prose PDF.

This probe also stands in for the rubric's "semantic clarity" and "units & types
declared" rows: both require the *retrievable schema artifact* to verify, so they
are evaluated together here — a dataset with no machine-readable schema cannot
satisfy any of the three, and one with a fetchable schema is where documented
enums/units live. (A deeper pass could fetch and lint the schema contents; this
first pass scores its presence and machine-readability.)

PASS    `describedBy` present on the dataset or a distribution.
PARTIAL only a prose `describedByType` hint (e.g. application/pdf) — a doc exists
        but is not a machine-readable schema.
FAIL    no schema reference anywhere.
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe


def _machine_schema_type(t: str) -> bool:
    t = (t or "").lower()
    return any(x in t for x in ("json", "csv", "xml", "yaml", "schema"))


class SchemaProbe(MetadataProbe):
    probe_id = "d3_schema"
    dimension = "D3"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        described = dataset.get("describedBy")
        described_type = dataset.get("describedByType", "")
        for dist in dataset.get("distribution", []) or []:
            if isinstance(dist, dict):
                described = described or dist.get("describedBy")
                described_type = described_type or dist.get("describedByType", "")
        if described:
            if described_type and not _machine_schema_type(described_type):
                return Score.PARTIAL, (
                    f"schema linked but type is non-machine ({described_type})")
            return Score.PASS, f"machine-readable schema linked (describedBy={described})"
        if described_type:
            return Score.PARTIAL, f"only a prose schema doc hint ({described_type})"
        return Score.FAIL, "no machine-readable schema (no describedBy)"
