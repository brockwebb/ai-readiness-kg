"""D2 Retrieval — bulk availability (whole dataset retrievable, not just paginated UI).

DCAT distinguishes `downloadURL` (a direct, whole-file download) from `accessURL`
(a service/landing endpoint, often paginated). Bulk readiness keys on the former.

PASS    distribution exposes a `downloadURL` (direct, whole-file) and it resolves.
PARTIAL only an `accessURL` (a service endpoint — bulk not guaranteed).
FAIL    neither resolves / no usable endpoint.
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import Score, Track
from .base import DistributionProbe


class BulkAvailabilityProbe(DistributionProbe):
    probe_id = "d2_bulk"
    dimension = "D2"
    track = Track.CORE

    def evaluate(self, fetched: Fetched, distribution: dict):
        dist = distribution or {}
        if dist.get("downloadURL"):
            if fetched.ok:
                return Score.PASS, "direct downloadURL (whole-file bulk) resolves"
            return Score.PARTIAL, "downloadURL declared but did not resolve this run"
        if dist.get("accessURL"):
            return Score.PARTIAL, "only an accessURL (service endpoint; bulk not guaranteed)"
        return Score.FAIL, "no downloadURL or accessURL — no bulk path"
