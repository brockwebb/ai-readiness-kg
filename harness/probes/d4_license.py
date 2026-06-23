"""D4 Trust/freshness — license machine-readable (use rights expressed as data).

PASS    `license` present (a URL/identifier a machine can resolve to terms).
PARTIAL only freeform `rights` prose — rights stated but not as a resolvable license.
FAIL    neither.
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe


class LicenseProbe(MetadataProbe):
    probe_id = "d4_license"
    dimension = "D4"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        if dataset.get("license"):
            return Score.PASS, f"license expressed as data: {dataset['license']}"
        if dataset.get("rights"):
            return Score.PARTIAL, "only freeform rights prose; no resolvable license"
        return Score.FAIL, "no machine-readable license or rights"
