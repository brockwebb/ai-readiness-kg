"""D1 Discovery — sitemap.xml present, parses, and lists resources.

PASS    200, parses as XML, contains <url>/<sitemap> entries (a real index).
PARTIAL present but does not parse as a sitemap, or parses but is empty.
FAIL    absent.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from ..fetch import Fetched
from ..records import Score, Track
from .base import SiteProbe


class SitemapProbe(SiteProbe):
    probe_id = "d1_sitemap"
    dimension = "D1"
    track = Track.CORE
    path = "/sitemap.xml"

    def evaluate(self, fetched: Fetched):
        if not fetched.ok or not fetched.body.strip():
            return Score.FAIL, f"sitemap.xml not retrievable (status={fetched.status})"
        try:
            root = ET.fromstring(fetched.body)
        except ET.ParseError as exc:
            return Score.PARTIAL, f"sitemap.xml present but does not parse as XML: {exc}"
        # Namespace-agnostic: count any <url> or <sitemap> child entries.
        entries = [el for el in root.iter() if el.tag.split("}")[-1] in ("url", "sitemap")]
        if entries:
            return Score.PASS, f"sitemap.xml parses with {len(entries)} entries"
        return Score.PARTIAL, "sitemap.xml parses but lists no url/sitemap entries"
