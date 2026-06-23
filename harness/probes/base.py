"""Probe base classes.

Three families, each with a pure `evaluate` so scoring is testable from fixtures
without the network:

- SiteProbe          fetches a well-known path off the agency base_url
                     (robots.txt, sitemap.xml, data.json, llms.txt, mcp) and scores
                     the response. Run once per agency.
- MetadataProbe      pure: scores a single dataset record from the catalog
                     (data.json / DCAT metadata). No network. Run per dataset.
- DistributionProbe  fetches one distribution endpoint and scores the live
                     response. Run per distribution.

Every probe declares `probe_id`, `dimension` (None for frontier), and `track`
(the core-vs-frontier firewall). `as_of_date` is derived from the track, so a
frontier probe's record always carries its dating.
"""
from __future__ import annotations

from typing import Optional, Tuple

from ..fetch import Fetched
from ..records import Score, Track


class SiteProbe:
    probe_id: str = ""
    dimension: Optional[str] = None
    track: Track = Track.CORE
    path: str = "/"

    def url_for(self, base_url: str) -> str:
        return base_url.rstrip("/") + self.path

    def evaluate(self, fetched: Fetched) -> Tuple[Score, str]:  # pragma: no cover
        raise NotImplementedError


class MetadataProbe:
    probe_id: str = ""
    dimension: Optional[str] = None
    track: Track = Track.CORE

    def evaluate(self, dataset: dict) -> Tuple[Score, str]:  # pragma: no cover
        raise NotImplementedError


class DistributionProbe:
    probe_id: str = ""
    dimension: Optional[str] = None
    track: Track = Track.CORE

    def evaluate(self, fetched: Fetched, distribution: dict) -> Tuple[Score, str]:  # pragma: no cover
        raise NotImplementedError
