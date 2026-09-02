"""D4 Trust/freshness — license machine-readable (use rights expressed as data).

PASS    `license` present (a URL/identifier a machine can resolve to terms).
PARTIAL only freeform `rights` prose — rights stated but not as a resolvable license.
FAIL    neither.

On a web surface the record is normalized from the page's in-page JSON-LD by
`harness/jsonld.py`: schema.org `license` maps to `license`, and the freeform
`usageInfo` / `conditionsOfAccess` map to `rights`, so page prose scores PARTIAL
the same way DCAT `rights` prose does.
"""
from __future__ import annotations

from ..records import SOURCE_CATALOG, SOURCE_SITEMAP, Score, Track
from .base import MetadataProbe


class LicenseProbe(MetadataProbe):
    probe_id = "d4_license"
    dimension = "D4"
    track = Track.CORE
    # On a web surface the license comes from the page's JSON-LD license field.
    sources = (SOURCE_CATALOG, SOURCE_SITEMAP)

    def evaluate(self, dataset: dict):
        if dataset.get("license"):
            return Score.PASS, f"license expressed as data: {dataset['license']}"
        if dataset.get("rights"):
            return Score.PARTIAL, "only freeform rights prose; no resolvable license"
        return Score.FAIL, "no machine-readable license or rights"
