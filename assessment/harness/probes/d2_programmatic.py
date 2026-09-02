"""D2 Retrieval — programmatic access (API or download without human/JS interaction).

PASS    a plain GET returns a non-trivial body and is not diverted to a login wall.
PARTIAL reachable but returns an empty/trivial body.
FAIL    unreachable, an auth/error status, or diverted to a sign-in page.
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import Score, Track
from .base import DistributionProbe
from ._formats import has_barrier_markers, looks_session_gated


class ProgrammaticAccessProbe(DistributionProbe):
    probe_id = "d2_programmatic"
    dimension = "D2"
    track = Track.CORE

    def evaluate(self, fetched: Fetched, distribution: dict):
        if not fetched.ok:
            return Score.FAIL, (
                f"not retrievable by plain GET (status={fetched.status}, "
                f"error={fetched.error})")
        if looks_session_gated(fetched.final_url) or has_barrier_markers(fetched.body):
            return Score.FAIL, "plain GET diverted to a login/sign-in wall"
        if fetched.body.strip():
            return Score.PASS, "retrievable programmatically by plain GET"
        return Score.PARTIAL, "reachable but returned an empty body"
