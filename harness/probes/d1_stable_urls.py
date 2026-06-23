"""D1 Discovery — stable, semantic URLs (addressable, not session/JS-gated).

PASS    the distribution URL resolves (2xx) and the final URL is not session-gated.
PARTIAL resolves, but the final URL looks session-gated (jsessionid, sessionid=).
FAIL    does not resolve.
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import Score, Track
from .base import DistributionProbe
from ._formats import looks_session_gated


class StableUrlProbe(DistributionProbe):
    probe_id = "d1_stable_urls"
    dimension = "D1"
    track = Track.CORE

    def evaluate(self, fetched: Fetched, distribution: dict):
        if not fetched.ok:
            return Score.FAIL, (
                f"URL not resolvable (status={fetched.status}, error={fetched.error})")
        if looks_session_gated(fetched.final_url):
            return Score.PARTIAL, f"resolves but final URL is session-gated: {fetched.final_url}"
        return Score.PASS, f"stable, addressable URL (resolved to {fetched.final_url})"
