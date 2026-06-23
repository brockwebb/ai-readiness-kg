"""D1 Discovery — robots.txt permits agents and declares a sitemap.

PASS    present, not blanket-blocking all agents, AND declares a Sitemap.
PARTIAL present and not blanket-blocking, but no Sitemap declared.
FAIL    absent, OR blanket-blocks all agents (User-agent: * / Disallow: /).
"""
from __future__ import annotations

from ..fetch import Fetched
from ..records import Score, Track
from .base import SiteProbe


class RobotsProbe(SiteProbe):
    probe_id = "d1_robots"
    dimension = "D1"
    track = Track.CORE
    path = "/robots.txt"

    def evaluate(self, fetched: Fetched):
        if not fetched.ok or not fetched.body.strip():
            return Score.FAIL, f"robots.txt not retrievable (status={fetched.status})"

        # Find the wildcard agent group and check whether it blanket-disallows root.
        blanket_block = False
        declares_sitemap = "sitemap:" in fetched.body.lower()
        current_agent_is_wildcard = False
        for raw in fetched.body.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            field, _, value = line.partition(":")
            field = field.strip().lower()
            value = value.strip()
            if field == "user-agent":
                current_agent_is_wildcard = value == "*"
            elif field == "disallow" and current_agent_is_wildcard and value == "/":
                blanket_block = True

        if blanket_block:
            return Score.FAIL, "robots.txt blanket-blocks all agents (User-agent: * / Disallow: /)"
        if declares_sitemap:
            return Score.PASS, "robots.txt permits agents and declares a Sitemap"
        return Score.PARTIAL, "robots.txt permits agents but declares no Sitemap"
