"""D1 Discovery — the sitemap the site declares is present, parses, lists
resources, and is not stale.

Which document is read. robots.txt's `Sitemap:` directive is followed when one is
declared; the fixed path `/sitemap.xml` is the fallback, recorded as
`sitemap_source: fixed_path_fallback`. The D0-r2 annotation in
census-web-concept-inventory (2026-09-01) found the two are different documents
on census.gov: the declared index yields 53,943 current URLs, while the fixed path
holds 5,408 entries whose `lastmod` values all fall in 2013-2015, and the fixed
path is what the probe used to read. When the declared sitemap is not the fixed
path, the runner fetches both and the divergence is reported as evidence
(`sitemap_divergence`), never as the score.

Staleness. The rubric's non-stale condition is implemented as: the NEWEST
`lastmod` in the document read is older than `[probes.d1_sitemap]
stale_after_days` -> PARTIAL, with that lastmod as evidence. The threshold is
config, not a constant. A document with no `lastmod` at all is recorded as
`sitemap_lastmod: null` and not scored stale: `lastmod` is optional in the
sitemap protocol, and the field's absence is an unscored D4-class observation
(rubric v1.1, D1 sitemap no-`lastmod` clause, task
2026-09-02_rubric_amendments_coverage_lastmod).

PASS    retrievable, parses as XML, contains <url>/<sitemap> entries, and the
        newest lastmod (when any is present) is within the threshold.
PARTIAL retrievable but does not parse as a sitemap, or parses but lists no
        entries, or lists entries whose newest lastmod is older than the
        threshold.
FAIL    not retrievable.

Observations: `sitemap_source` ("robots.txt" | "fixed_path_fallback"),
`sitemap_url`, `sitemap_lastmod` (newest, raw W3C datetime string or null),
`sitemap_lastmod_count`, `sitemap_entries`, `sitemap_stale_warning` (versioned
rule with the threshold that was applied), and `sitemap_divergence` when the
fixed path was also read.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from ..enumerate_sitemap import parse_robots_sitemaps
from ..fetch import Fetched
from ..records import Score, Track
from .base import SiteProbe

STALE_RULE_ID = "sitemap_stale"
STALE_RULE_VERSION = "1"

SOURCE_ROBOTS = "robots.txt"
SOURCE_FIXED_PATH = "fixed_path_fallback"


def parse_lastmod(text: Optional[str]) -> Optional[date]:
    """A W3C datetime (`2024-05-01`, `2024-05-01T10:00:00Z`, `...+02:00`) as a
    date, or None when unparseable. Only the date part decides staleness, so a
    value with a time zone and one without compare the same way."""
    if not text:
        return None
    raw = text.strip()
    try:
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            parsed = datetime.fromisoformat(raw[:10]) if len(raw) == 10 \
                else datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed.date()
    except ValueError:
        return None
    return None


def sitemap_entries(xml_text: str) -> Tuple[List[ET.Element], List[Optional[str]]]:
    """Every <url>/<sitemap> element, namespace-agnostic, with the raw lastmod
    text of each (None when the entry carries none). Raises ET.ParseError."""
    root = ET.fromstring(xml_text)
    entries = [el for el in root.iter() if el.tag.split("}")[-1] in ("url", "sitemap")]
    lastmods: List[Optional[str]] = []
    for el in entries:
        lm = next((c for c in el if c.tag.split("}")[-1] == "lastmod"), None)
        lastmods.append(lm.text.strip() if lm is not None and lm.text and lm.text.strip() else None)
    return entries, lastmods


def newest_lastmod(lastmods: List[Optional[str]]) -> Tuple[Optional[str], Optional[date], int]:
    """(raw text of the newest parseable lastmod, its date, count of entries
    carrying any lastmod)."""
    best_raw, best_date = None, None
    count = 0
    for raw in lastmods:
        if raw is None:
            continue
        count += 1
        d = parse_lastmod(raw)
        if d is not None and (best_date is None or d > best_date):
            best_raw, best_date = raw, d
    return best_raw, best_date, count


class SitemapProbe(SiteProbe):
    probe_id = "d1_sitemap"
    dimension = "D1"
    track = Track.CORE
    # The fixed path: the fallback and the divergence comparator, not the target.
    path = "/sitemap.xml"

    def __init__(self, stale_after_days: int):
        # From config; a probe built without a threshold is a defect, not a default.
        if isinstance(stale_after_days, bool) or not isinstance(stale_after_days, int) \
                or stale_after_days < 1:
            raise ValueError(f"stale_after_days must be an integer >= 1, got {stale_after_days!r}")
        self.stale_after_days = stale_after_days

    def resolve(self, base_url: str, robots_body: str) -> Tuple[str, str]:
        """Which sitemap to read: `(url, sitemap_source)`. Pure."""
        declared = parse_robots_sitemaps(robots_body)
        if declared:
            return declared[0], SOURCE_ROBOTS
        return self.url_for(base_url), SOURCE_FIXED_PATH

    def _describe(self, fetched: Fetched, today: date) -> dict:
        """Pure description of one sitemap document: parse state, entry count,
        newest lastmod, staleness against the threshold."""
        out = {
            "url": fetched.requested_url,
            "status": fetched.status,
            "retrievable": bool(fetched.ok and fetched.body.strip()),
            "parses": False,
            "entries": 0,
            "sitemap_lastmod": None,
            "sitemap_lastmod_count": 0,
            "stale": None,
            "age_days": None,
        }
        if not out["retrievable"]:
            return out
        try:
            entries, lastmods = sitemap_entries(fetched.body)
        except ET.ParseError as exc:
            out["parse_error"] = str(exc)
            return out
        raw, newest, count = newest_lastmod(lastmods)
        out.update(parses=True, entries=len(entries), sitemap_lastmod=raw,
                   sitemap_lastmod_count=count)
        if newest is not None:
            age = (today - newest).days
            out["age_days"] = age
            out["stale"] = age > self.stale_after_days
        return out

    def evaluate(self, fetched: Fetched, sitemap_source: str = SOURCE_FIXED_PATH,
                 fixed_path_fetched: Optional[Fetched] = None,
                 today: Optional[date] = None):
        """Score the sitemap that was read. `fixed_path_fetched` is the fixed
        path's document when the runner also read it (declared sitemap differed
        from the fixed path); it feeds the divergence observation only. `today`
        is injectable so staleness is testable from fixtures."""
        today = today or datetime.now(timezone.utc).date()
        read = self._describe(fetched, today)
        obs = {
            "sitemap_source": sitemap_source,
            "sitemap_url": fetched.requested_url,
            "sitemap_lastmod": read["sitemap_lastmod"],
            "sitemap_lastmod_count": read["sitemap_lastmod_count"],
            "sitemap_entries": read["entries"],
            "sitemap_stale_warning": {
                "rule_id": STALE_RULE_ID,
                "rule_version": STALE_RULE_VERSION,
                "stale_after_days": self.stale_after_days,
                "evaluated_on": today.isoformat(),
                "fired": bool(read["stale"]),
                "age_days": read["age_days"],
                "determinable": read["stale"] is not None,
            },
        }
        if fixed_path_fetched is not None:
            fixed = self._describe(fixed_path_fetched, today)
            same = (fixed["retrievable"] and read["retrievable"]
                    and fixed_path_fetched.body == fetched.body)
            obs["sitemap_divergence"] = {
                "declared_url": fetched.requested_url,
                "fixed_path_url": fixed_path_fetched.requested_url,
                "same_document": same,
                "fixed_path": fixed,
                "note": (
                    "robots.txt declares a sitemap other than /sitemap.xml; both were "
                    "read. The score is on the declared document; the fixed path is "
                    "reported so a client that guesses the path is seen for what it "
                    "gets."
                ),
            }

        label = f"{sitemap_source} sitemap {fetched.requested_url}"
        if not read["retrievable"]:
            return Score.FAIL, f"{label} not retrievable (status={fetched.status})", obs
        if not read["parses"]:
            return (Score.PARTIAL,
                    f"{label} present but does not parse as XML: {read.get('parse_error')}",
                    obs)
        if read["entries"] == 0:
            return Score.PARTIAL, f"{label} parses but lists no url/sitemap entries", obs
        if read["stale"]:
            return (Score.PARTIAL,
                    f"{label} parses with {read['entries']} entries but is stale: newest "
                    f"lastmod {read['sitemap_lastmod']} is {read['age_days']} days old "
                    f"(threshold {self.stale_after_days})",
                    obs)
        freshness = (f"newest lastmod {read['sitemap_lastmod']} ({read['age_days']} days old)"
                     if read["sitemap_lastmod"] else
                     "no lastmod on any entry (staleness not determinable)")
        return (Score.PASS,
                f"{label} parses with {read['entries']} entries; {freshness}",
                obs)
