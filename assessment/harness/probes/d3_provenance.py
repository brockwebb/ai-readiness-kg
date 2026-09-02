"""D3 Interpretability — provenance (source, version, date machine-readable).

PASS    both a source signal (publisher, or bureauCode/programCode) AND a date
        (modified/issued) are machine-readable.
PARTIAL exactly one of the two signals.
FAIL    neither.
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe


class ProvenanceProbe(MetadataProbe):
    probe_id = "d3_provenance"
    dimension = "D3"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        has_source = bool(
            dataset.get("publisher")
            or dataset.get("bureauCode")
            or dataset.get("programCode")
        )
        has_date = bool(dataset.get("modified") or dataset.get("issued"))
        if has_source and has_date:
            return Score.PASS, "provenance: publisher/agency + date both machine-readable"
        if has_source or has_date:
            return Score.PARTIAL, (
                f"provenance partial: source={has_source}, date={has_date}")
        return Score.FAIL, "no machine-readable provenance (no source, no date)"
