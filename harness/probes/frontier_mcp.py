"""FRONTIER (deep) — MCP / WebMCP endpoint advertised.

Part B access axis, visionary tier (icsp_notebook 51fe4574 forward interpretation).
WebMCP standardized ~2026-Q1, roughly three months before this assessment;
absence is explicitly NOT core unreadiness. NEVER folded into core.

Probes a conventional discovery location (`/.well-known/mcp.json`).
PASS    200, valid JSON advertising tools or resources (a usable schema).
PARTIAL 200, valid JSON, but no tools/resources advertised.
FAIL    absent.
"""
from __future__ import annotations

import json

from ..fetch import Fetched
from ..records import Score, Track
from .base import SiteProbe


class McpProbe(SiteProbe):
    probe_id = "frontier_mcp"
    dimension = None
    track = Track.FRONTIER_DEEP
    path = "/.well-known/mcp.json"

    def evaluate(self, fetched: Fetched):
        if not fetched.ok or not fetched.body.strip():
            return Score.FAIL, f"no MCP/WebMCP endpoint advertised (status={fetched.status})"
        try:
            data = json.loads(fetched.body)
        except (json.JSONDecodeError, ValueError):
            return Score.PARTIAL, "MCP discovery endpoint present but not valid JSON"
        if isinstance(data, dict) and (data.get("tools") or data.get("resources")):
            return Score.PASS, "MCP/WebMCP endpoint advertises tools/resources"
        return Score.PARTIAL, "MCP discovery JSON present but advertises no tools/resources"
