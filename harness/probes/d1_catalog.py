"""D1 Discovery — structured catalog (Project Open Data data.json / DCAT).

PASS    200, valid JSON, non-empty `dataset` array (a real machine-readable catalog).
PARTIAL 200, valid JSON, but no recognizable `dataset` array (wrong shape).
FAIL    absent or not JSON — the "no machine-readable catalog" D1 finding.
"""
from __future__ import annotations

import json

from ..fetch import Fetched
from ..records import Score, Track
from .base import SiteProbe


class CatalogProbe(SiteProbe):
    probe_id = "d1_catalog"
    dimension = "D1"
    track = Track.CORE
    path = "/data.json"

    def evaluate(self, fetched: Fetched):
        if not fetched.ok or not fetched.body.strip():
            return Score.FAIL, f"data.json not retrievable (status={fetched.status})"
        try:
            data = json.loads(fetched.body)
        except (json.JSONDecodeError, ValueError):
            return Score.FAIL, "data.json endpoint did not return valid JSON"
        datasets = data.get("dataset") if isinstance(data, dict) else None
        if isinstance(datasets, list) and datasets:
            return Score.PASS, f"data.json catalog with {len(datasets)} datasets"
        return Score.PARTIAL, "JSON present but no non-empty 'dataset' array (not a DCAT catalog)"
