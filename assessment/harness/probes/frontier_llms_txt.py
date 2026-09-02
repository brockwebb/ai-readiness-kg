"""FRONTIER (near) — llms.txt present & valid.

Part B access axis, readily-achievable tier (icsp_notebook 51fe4574 forward
interpretation). A low-effort, already-circulating convention; failing it reads
as "hasn't bothered," not "ahead of the standard." NEVER folded into core.

PASS    present, non-trivial, looks like an llms.txt (markdown headers and/or links).
PARTIAL present but trivial/empty.
FAIL    absent.
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import Score, Track
from .base import SiteProbe


class LlmsTxtProbe(SiteProbe):
    probe_id = "frontier_llms_txt"
    dimension = None  # frontier track is off the core dimensions
    track = Track.FRONTIER_NEAR
    path = "/llms.txt"

    def evaluate(self, fetched: Fetched):
        if not fetched.ok:
            return Score.FAIL, f"llms.txt absent (status={fetched.status})"
        body = fetched.body
        looks_structured = ("#" in body) or ("](" in body) or ("http" in body.lower())
        if looks_structured and len(body.strip()) > 20:
            return Score.PASS, "llms.txt present and structured (headers/links)"
        return Score.PARTIAL, "llms.txt present (200) but trivial / unstructured"
