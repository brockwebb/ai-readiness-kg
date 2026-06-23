"""D2 Retrieval — no anti-machine barriers (no CAPTCHA / login wall / JS-render gate).

PASS    reachable (2xx) with no CAPTCHA / login / "enable JavaScript" markers.
PARTIAL reachable but body shows a JS-render dependency (app shell, little content).
FAIL    an auth/error status (401/403) or explicit CAPTCHA / login-wall markers.
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import Score, Track
from .base import DistributionProbe
from ._formats import has_barrier_markers


class NoBarriersProbe(DistributionProbe):
    probe_id = "d2_no_barriers"
    dimension = "D2"
    track = Track.CORE

    def evaluate(self, fetched: Fetched, distribution: dict):
        if fetched.status in (401, 403):
            return Score.FAIL, f"auth barrier (HTTP {fetched.status})"
        if has_barrier_markers(fetched.body):
            return Score.FAIL, "CAPTCHA / login-wall markers present in response"
        if not fetched.ok:
            return Score.FAIL, (
                f"not retrievable (status={fetched.status}, error={fetched.error})")
        # JS-render dependency heuristic: tiny body that demands a client to render.
        if "enable javascript" in fetched.body.lower():
            return Score.PARTIAL, "reachable but appears to require JS rendering"
        return Score.PASS, "no anti-machine barriers detected"
