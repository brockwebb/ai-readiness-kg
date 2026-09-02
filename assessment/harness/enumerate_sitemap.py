"""Second enumeration source: the agency's public WEB SURFACE, sampled from the
sitemap the site itself declares.

Why a second source exists. `enumerate_targets.py` reads `data.json` only, so the
measurement universe is exactly the set of catalog distributions. For an agency
whose distributions all sit on one API host (Census: every one of 1,798
distributions is on api.census.gov), the site's own web products are outside that
universe entirely, and a web product that refuses automated clients at the edge is
invisible to the harness no matter how many distributions it probes. This module
widens the universe to what the site publishes about itself.

Prior art, adopted not reinvented: `census-web-concept-inventory`
`src/pipelines/01_sitemap_universe.py` (2026-09-01), which enumerated the 53,943
URL census.gov universe from 14 child sitemaps. Ported here rather than imported,
because the harness carries no third-party runtime dependency: `xml.etree` in
place of that stage's parsing helpers, plain dicts in place of pandas/parquet.
The three disciplines that came with it are kept intact:

  1. Follow what robots.txt declares TODAY; the configured `sitemap_url` is the
     recorded expectation, and a difference is recorded as drift, not silently
     preferred either way.
  2. A child sitemap that fails is a recorded finding, never fatal. The harness
     must keep going and report what it could not reach (Engineering Standards
     §4). A 403 on a child sitemap is itself a barrier observation.
  3. Reconcile the counts. Unique plus duplicates must equal parsed, or the
     enumeration is wrong and says so.

Sampling is stratified by section (one child sitemap is one section) and seeded,
so the probe count stays polite and the same seed redraws the same pages. Each
section draws from its own seeded stream, so adding or losing a section does not
shift the pages drawn for any other section.

Parsing is pure and takes already-retrieved text, the way `enumerate_targets.py`
does, so it is fully testable from fixtures. Only `enumerate_web_surfaces` needs a
fetcher, and that is injected.
"""
from __future__ import annotations

import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .records import SOURCE_SITEMAP

SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class WebSurfaceResult:
    """What the web-surface enumeration found, including what it could not reach."""

    has_sitemap: bool
    sitemap_url: str = ""
    # Where the followed sitemap URL came from: "robots.txt", "config", or "none".
    sitemap_url_source: str = "none"
    # Set when robots.txt declares a different sitemap than agencies.toml records.
    drift: Optional[str] = None
    targets: List[dict] = field(default_factory=list)
    # section -> number of <url> entries parsed from that child sitemap.
    per_section_parsed: Dict[str, int] = field(default_factory=dict)
    # section -> number sampled for probing.
    per_section_sampled: Dict[str, int] = field(default_factory=dict)
    # section -> every unique URL the section declares (after cross-section
    # dedup). Held in memory for the catalog-coverage fact (d1_catalog); it is
    # NOT written to the rollup, whose per-section counts summarize it.
    universe_by_section: Dict[str, List[str]] = field(default_factory=dict)
    child_failures: List[dict] = field(default_factory=list)
    sections_total: int = 0
    sections_parsed: int = 0
    universe_total: int = 0
    duplicate_count: int = 0
    sample_seed: Optional[int] = None
    sample_per_section: Optional[int] = None
    note: str = ""


def parse_robots_sitemaps(text: str) -> List[str]:
    """Every `Sitemap:` URL declared in robots.txt, in file order.

    The directive is case-insensitive by de facto convention; census.gov emits it
    uppercase, which is exactly the case a case-sensitive reader would miss.
    """
    found = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("sitemap:"):
            value = stripped.split(":", 1)[1].strip()
            if value:
                found.append(value)
    return found


def _root_of(xml_text: str) -> Tuple[ET.Element, str]:
    root = ET.fromstring(xml_text)
    return root, root.tag.split("}")[-1]


def parse_sitemap_index(xml_text: str) -> List[str]:
    """Child sitemap URLs from a `<sitemapindex>` document.

    Raises ValueError when the document is not a sitemap index, so a landing page
    served at the sitemap URL is a recorded finding rather than an empty universe
    that reads like a site with no pages.
    """
    root, tag = _root_of(xml_text)
    if tag != "sitemapindex":
        raise ValueError(f"expected sitemapindex root element, got {tag!r}")
    locs = []
    for sm in root.findall("s:sitemap", SITEMAP_NS):
        loc = sm.find("s:loc", SITEMAP_NS)
        if loc is None or not (loc.text or "").strip():
            raise ValueError("sitemapindex contains a <sitemap> with no <loc>")
        locs.append(loc.text.strip())
    return locs


def parse_urlset(xml_text: str) -> List[Tuple[str, Optional[str]]]:
    """`(loc, lastmod)` pairs from a `<urlset>` document.

    `lastmod` is kept as the raw W3C datetime string rather than parsed, so no
    precision is silently dropped.
    """
    root, tag = _root_of(xml_text)
    if tag != "urlset":
        raise ValueError(f"expected urlset root element, got {tag!r}")
    entries = []
    for url_el in root.findall("s:url", SITEMAP_NS):
        loc = url_el.find("s:loc", SITEMAP_NS)
        if loc is None or not (loc.text or "").strip():
            continue
        lastmod = url_el.find("s:lastmod", SITEMAP_NS)
        lastmod_text = lastmod.text.strip() if lastmod is not None and lastmod.text else None
        entries.append((loc.text.strip(), lastmod_text or None))
    return entries


def section_of(child_url: str) -> str:
    """Section label for a child sitemap: its filename stem.

    census.gov's QuickFacts child is `/quickfacts/fact/sitemap/US/PST045217`, with
    no extension, so the stem is the last path segment. That is the label the
    prior-art universe used, which keeps the two enumerations comparable.
    """
    stem = PurePosixPath(urlparse(child_url).path).stem
    return stem or urlparse(child_url).netloc or child_url


def sample_sections(
    per_section_entries: Dict[str, List[Tuple[str, Optional[str]]]],
    sample_per_section: int,
    seed: int,
) -> List[dict]:
    """Stratified, seeded sample: up to `sample_per_section` pages per section.

    Each section draws from its own stream, keyed by seed and section name, so a
    section appearing or disappearing between runs does not shift the pages drawn
    for any other section. Within a section the pool is sorted before sampling, so
    the draw does not depend on the order the sitemap happened to list URLs.
    """
    sampled: List[dict] = []
    for section in sorted(per_section_entries):
        pool = sorted(set(per_section_entries[section]))
        if not pool:
            continue
        k = min(sample_per_section, len(pool))
        rnd = random.Random(f"{seed}:{section}")
        for url, lastmod in sorted(rnd.sample(pool, k)):
            sampled.append(
                {
                    "url": url,
                    "lastmod": lastmod,
                    "section": section,
                    "source": SOURCE_SITEMAP,
                }
            )
    return sampled


def resolve_sitemap_url(
    robots_body: str, configured_url: str = ""
) -> Tuple[str, str, Optional[str]]:
    """Decide which sitemap to follow. Returns `(url, source, drift)`.

    robots.txt is authoritative because it is what the site declares today; the
    configured value is the recorded expectation, used to detect drift and as the
    fallback when robots.txt declares nothing.
    """
    declared = parse_robots_sitemaps(robots_body)
    if declared:
        url = declared[0]
        drift = None
        if configured_url and url != configured_url:
            drift = (
                f"robots.txt declares {url!r}; agencies.toml records "
                f"{configured_url!r}. Following robots.txt."
            )
        return url, "robots.txt", drift
    if configured_url:
        return configured_url, "config", (
            "robots.txt declares no Sitemap directive; falling back to the "
            "agencies.toml value. The absence is itself a D1 discovery finding."
        )
    return "", "none", None


def enumerate_web_surfaces(
    fetcher,
    robots_body: str,
    configured_sitemap_url: str = "",
    sample_per_section: int = 3,
    max_sections: int = 0,
    seed: int = 0,
) -> WebSurfaceResult:
    """Walk the declared sitemap index and return a stratified sample of pages.

    Every failure is recorded and the walk continues: a sitemap URL that does not
    resolve, a body that is not a sitemap index, a child sitemap that is refused.
    Nothing here raises past the caller.
    """
    url, source, drift = resolve_sitemap_url(robots_body, configured_sitemap_url)
    if not url:
        return WebSurfaceResult(
            has_sitemap=False,
            sitemap_url_source="none",
            note="no sitemap declared in robots.txt and none configured "
            "(D1 Discovery finding); web surface not enumerated",
        )

    result = WebSurfaceResult(
        has_sitemap=False,
        sitemap_url=url,
        sitemap_url_source=source,
        drift=drift,
        sample_seed=seed,
        sample_per_section=sample_per_section,
    )

    index_fetched = fetcher.get(url)
    if not index_fetched.ok:
        result.note = (
            f"sitemap index not retrievable (status={index_fetched.status}, "
            f"error={index_fetched.error}); recorded, web surface not enumerated"
        )
        return result

    try:
        children = parse_sitemap_index(index_fetched.body)
    except (ET.ParseError, ValueError) as exc:
        # A flat <urlset> at the sitemap URL is legitimate: treat the document
        # itself as the single section rather than reporting no web surface.
        try:
            entries = parse_urlset(index_fetched.body)
        except (ET.ParseError, ValueError):
            result.note = (
                f"sitemap URL retrievable but not a sitemap document: {exc}; "
                f"recorded, web surface not enumerated"
            )
            return result
        children = []
        result.has_sitemap = True
        result.sections_total = 1
        result.sections_parsed = 1
        section = section_of(url)
        result.per_section_parsed[section] = len(entries)
        per_section_entries = {section: entries}
        return _finish(result, per_section_entries, sample_per_section, seed)

    result.has_sitemap = True
    result.sections_total = len(children)
    if max_sections and max_sections > 0:
        children = children[:max_sections]

    per_section_entries: Dict[str, List[Tuple[str, Optional[str]]]] = {}
    for child_url in children:
        section = section_of(child_url)
        child = fetcher.get(child_url)
        if not child.ok:
            result.child_failures.append(
                {
                    "child": child_url,
                    "section": section,
                    "status": child.status,
                    "error": child.error,
                    "reason": f"HTTP {child.status}" if child.status else str(child.error),
                }
            )
            continue
        try:
            entries = parse_urlset(child.body)
        except (ET.ParseError, ValueError) as exc:
            result.child_failures.append(
                {
                    "child": child_url,
                    "section": section,
                    "status": child.status,
                    "error": None,
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        result.per_section_parsed[section] = len(entries)
        per_section_entries[section] = entries

    result.sections_parsed = len(per_section_entries)
    return _finish(result, per_section_entries, sample_per_section, seed)


def _finish(
    result: WebSurfaceResult,
    per_section_entries: Dict[str, List[Tuple[str, Optional[str]]]],
    sample_per_section: int,
    seed: int,
) -> WebSurfaceResult:
    """Deduplicate across sections, reconcile the counts, then sample."""
    first_seen: Dict[str, str] = {}
    deduped: Dict[str, List[Tuple[str, Optional[str]]]] = {}
    duplicates = 0
    for section in sorted(per_section_entries):
        kept = []
        for loc, lastmod in per_section_entries[section]:
            if loc in first_seen:
                duplicates += 1
                continue
            first_seen[loc] = section
            kept.append((loc, lastmod))
        deduped[section] = kept

    total_parsed = sum(len(v) for v in per_section_entries.values())
    result.universe_by_section = {s: [loc for loc, _ in kept] for s, kept in deduped.items()}
    result.universe_total = len(first_seen)
    result.duplicate_count = duplicates
    if result.universe_total + duplicates != total_parsed:
        # Fail loud rather than sampling from a universe that does not add up.
        result.note = (
            f"RECONCILIATION FAILED: {result.universe_total} unique + {duplicates} "
            f"duplicates != {total_parsed} parsed entries; sample suppressed"
        )
        result.targets = []
        return result

    result.targets = sample_sections(deduped, sample_per_section, seed)
    result.per_section_sampled = {}
    for t in result.targets:
        result.per_section_sampled[t["section"]] = (
            result.per_section_sampled.get(t["section"], 0) + 1
        )
    result.note = (
        f"{result.sections_parsed}/{result.sections_total} sections parsed "
        f"-> {result.universe_total} unique public URLs "
        f"-> {len(result.targets)} sampled (seed={seed}, "
        f"{sample_per_section}/section); "
        f"{len(result.child_failures)} section(s) unreachable"
    )
    return result
