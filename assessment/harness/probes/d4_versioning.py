"""D4 Trust/freshness — versioning (version or last-modified machine-readable).

PASS    `modified` present (a last-modified a machine can compare).
PARTIAL only `issued` (creation date) present — dated, but no modification signal.
FAIL    neither.
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe


class VersioningProbe(MetadataProbe):
    probe_id = "d4_versioning"
    dimension = "D4"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        if dataset.get("modified"):
            return Score.PASS, f"modified={dataset['modified']} (machine-readable)"
        if dataset.get("issued"):
            return Score.PARTIAL, "only issued date present; no modification signal"
        return Score.FAIL, "no machine-readable version or last-modified"
