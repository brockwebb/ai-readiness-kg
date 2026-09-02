"""D2 Retrieval — content negotiation / machine formats offered.

The harness requests the endpoint with an Accept favoring machine formats (the
runner sets that); this probe scores whether a machine format is actually on offer,
from either the declared distribution mediaType or the live response content-type.

PASS    a machine-consumable format (JSON/CSV/Parquet/XML…) is offered.
PARTIAL reachable but only HTML/PDF presentation formats.
FAIL    not retrievable.
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import SOURCE_CATALOG, SOURCE_SITEMAP, Score, Track
from .base import DistributionProbe
from ._formats import is_machine_format


class ContentNegotiationProbe(DistributionProbe):
    probe_id = "d2_content_negotiation"
    dimension = "D2"
    track = Track.CORE
    # Asking an HTML page for a machine format is exactly the negotiation test.
    sources = (SOURCE_CATALOG, SOURCE_SITEMAP)

    def evaluate(self, fetched: Fetched, distribution: dict):
        if not fetched.ok:
            return Score.FAIL, (
                f"not retrievable (status={fetched.status}, error={fetched.error})")
        media_type = (distribution or {}).get("mediaType", "")
        if is_machine_format(media_type, fetched.content_type):
            return Score.PASS, (
                f"machine format offered (mediaType={media_type!r}, "
                f"content-type={fetched.content_type!r})")
        return Score.PARTIAL, (
            f"only presentation format (mediaType={media_type!r}, "
            f"content-type={fetched.content_type!r})")
