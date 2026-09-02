"""D4 Trust/freshness — integrity signal (checksum / signing / canonical source).

PASS    a distribution carries a `checksum` (or sha/md5) a machine can verify against.
PARTIAL no checksum, but a canonical identifier/landingPage (e.g. DOI) lets a
        machine confirm it has the authoritative source.
FAIL    neither — no way to confirm integrity or canonicity.

Realistically most federal catalogs lack checksums today; PARTIAL/FAIL here is an
honest signal, not a harness defect.
"""
from __future__ import annotations

from ..records import Score, Track
from .base import MetadataProbe

_CHECKSUM_KEYS = ("checksum", "sha256", "sha1", "md5", "hash")


class IntegrityProbe(MetadataProbe):
    probe_id = "d4_integrity"
    dimension = "D4"
    track = Track.CORE

    def evaluate(self, dataset: dict):
        for dist in dataset.get("distribution", []) or []:
            if isinstance(dist, dict) and any(dist.get(k) for k in _CHECKSUM_KEYS):
                return Score.PASS, "distribution carries a verifiable checksum"
        identifier = str(dataset.get("identifier", ""))
        canonical = "doi.org" in identifier or bool(dataset.get("landingPage"))
        if canonical:
            return Score.PARTIAL, "no checksum, but canonical identifier/landingPage present"
        return Score.FAIL, "no integrity signal (no checksum, no canonical identifier)"
