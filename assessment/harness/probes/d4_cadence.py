"""D4 Trust/freshness — update cadence declared.

PASS    `accrualPeriodicity` present (an ISO 8601 recurrence or recognized term).
PARTIAL present but an unrecognized / freeform value.
FAIL    absent.
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe

# Common DCAT-US accrualPeriodicity encodings (ISO 8601 recurrence) + plain terms.
_RECOGNIZED_PREFIXES = ("R/P", "R/")
_RECOGNIZED_TERMS = {
    "annual", "monthly", "weekly", "daily", "quarterly", "biannual",
    "irregular", "continuous", "hourly", "as needed",
}


class CadenceProbe(MetadataProbe):
    probe_id = "d4_cadence"
    dimension = "D4"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        value = dataset.get("accrualPeriodicity")
        if not value:
            return Score.FAIL, "no update cadence declared (accrualPeriodicity)"
        v = str(value).strip()
        if v.startswith(_RECOGNIZED_PREFIXES) or v.lower() in _RECOGNIZED_TERMS:
            return Score.PASS, f"update cadence declared: {v}"
        return Score.PARTIAL, f"cadence present but non-standard value: {v}"
