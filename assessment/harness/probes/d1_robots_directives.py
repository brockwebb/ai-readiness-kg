"""D1 Discovery — page-level robots directives: <meta name="robots">, bot-specific
meta, and the X-Robots-Tag header.

The page-level leg of the robots question. `d1_robots` reads robots.txt once per
site and stays as it is; this probe reads what each fetched page says about
itself, which robots.txt cannot show. The D0-r2 annotation in
census-web-concept-inventory (2026-09-01) found 77 of 98 sampled QuickFacts pages
carrying a `nofollow` meta robots directive while census.gov's robots.txt scored
PASS: a site that permits crawling at the door and withdraws its product pages
from discovery one at a time.

PASS    page retrievable; no discovery-blocking directive in any robots meta or
        X-Robots-Tag.
PARTIAL page retrievable; a discovery-blocking directive (noindex / nofollow /
        none, the configured list) is present, with the directive as evidence.
        The page is reachable but has asked to be withdrawn from discovery.
FAIL    page not retrievable, so no directive could be read.

Observations (SEO Machine Diagnostic field names): `robots_meta`, a map from the
meta name that carried directives (robots, googlebot, ...) to its parsed
directive list; `x_robots_tag`, the header value(s) parsed the same way, keyed by
the token prefix when the header names one (`googlebot: noindex`) and by `*`
otherwise. Directives are recorded whether or not they block, so a reviewer sees
`max-snippet:-1` beside `nofollow`.

Which meta names count, and which directives block, are config
([probes.d1_robots_directives]); the reading rule "any name ending in bot" is
structural, not a threshold, and lives here.
"""
from __future__ import annotations

from html.parser import HTMLParser
from typing import Dict, Iterable, List, Tuple

from ..fetch import Fetched
from ..records import SOURCE_SITEMAP, Score, Track
from .base import DistributionProbe


class _MetaCollector(HTMLParser):
    """Every <meta name=... content=...> in the document, name lowercased."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metas: List[Tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        attr = {k.lower(): (v or "") for k, v in attrs}
        name = attr.get("name", "").strip().lower()
        if name:
            self.metas.append((name, attr.get("content", "")))

    # <meta ... /> arrives as startendtag in HTMLParser; route it the same way.
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def parse_directives(content: str) -> List[str]:
    """Split a robots directive string into lowercased directives.

    `noindex, nofollow` -> ["noindex", "nofollow"]; `max-snippet:-1` kept whole.
    """
    return [d.strip().lower() for d in (content or "").split(",") if d.strip()]


def is_directive_meta_name(name: str, directive_meta_names: Iterable[str]) -> bool:
    n = (name or "").strip().lower()
    return n in {m.lower() for m in directive_meta_names} or n.endswith("bot")


def robots_meta(html: str, directive_meta_names: Iterable[str]) -> Dict[str, List[str]]:
    """`robots_meta`: meta name -> directives, for every robots-class meta tag.

    Multiple tags with the same name are concatenated in document order, which
    is how search engines combine them (most restrictive wins), so nothing is
    dropped.
    """
    collector = _MetaCollector()
    try:
        collector.feed(html or "")
        collector.close()
    except Exception:  # pragma: no cover - HTMLParser is lenient by design
        pass
    out: Dict[str, List[str]] = {}
    for name, content in collector.metas:
        if is_directive_meta_name(name, directive_meta_names):
            out.setdefault(name, []).extend(parse_directives(content))
    return out


def x_robots_tag(headers: dict) -> Dict[str, List[str]]:
    """`x_robots_tag`: token -> directives from the X-Robots-Tag header.

    The header may name a token (`googlebot: noindex`); un-prefixed directives
    apply to every client and are keyed `*`. urllib folds repeated headers into
    one comma-joined value, and a token prefix can appear mid-string, so each
    comma-separated piece is checked for a `token:` prefix; a piece whose
    prefix is a known directive-with-value (`max-snippet:-1`,
    `unavailable_after: ...`) is kept as a directive, not read as a token.
    """
    value = ""
    for k, v in (headers or {}).items():
        if k.lower() == "x-robots-tag":
            value = v or ""
            break
    out: Dict[str, List[str]] = {}
    if not value.strip():
        return out
    valued_directives = ("max-snippet", "max-image-preview", "max-video-preview",
                         "unavailable_after")
    current = "*"
    for piece in value.split(","):
        piece = piece.strip()
        if not piece:
            continue
        head, sep, tail = piece.partition(":")
        if sep and head.strip().lower() not in valued_directives and tail.strip():
            # A token prefix scopes THIS piece and the pieces after it.
            current = head.strip()
            piece = tail.strip()
        out.setdefault(current, []).append(piece.lower())
    return out


class RobotsDirectivesProbe(DistributionProbe):
    probe_id = "d1_robots_directives"
    dimension = "D1"
    track = Track.CORE
    # A directive withdraws a PAGE from discovery; a catalog distribution (a CSV,
    # an API endpoint) is not a page intended for discovery, so the question is
    # asked of the web surface only.
    sources = (SOURCE_SITEMAP,)

    def __init__(self, directive_meta_names: Iterable[str],
                 blocking_directives: Iterable[str]):
        # Both from config; a probe built without them is a defect, not a default.
        self.directive_meta_names = tuple(directive_meta_names)
        self.blocking_directives = tuple(d.lower() for d in blocking_directives)
        if not self.blocking_directives:
            raise ValueError("d1_robots_directives needs at least one blocking directive")

    def observe(self, fetched: Fetched) -> dict:
        """The pure observation, independent of the score."""
        return {
            "robots_meta": robots_meta(fetched.body, self.directive_meta_names),
            "x_robots_tag": x_robots_tag(fetched.headers),
        }

    def evaluate(self, fetched: Fetched, distribution: dict):
        if not fetched.ok:
            return (Score.FAIL,
                    f"page not retrievable, no directive readable "
                    f"(status={fetched.status}, error={fetched.error})",
                    {"robots_meta": {}, "x_robots_tag": {}})
        obs = self.observe(fetched)
        blocking: List[str] = []
        for name, directives in obs["robots_meta"].items():
            for d in directives:
                if d in self.blocking_directives:
                    blocking.append(f"meta[{name}]={d}")
        for token, directives in obs["x_robots_tag"].items():
            for d in directives:
                if d in self.blocking_directives:
                    blocking.append(f"x-robots-tag[{token}]={d}")
        if blocking:
            return (Score.PARTIAL,
                    f"page withdraws itself from discovery: {', '.join(blocking)}",
                    obs)
        seen = (f"robots_meta={obs['robots_meta']}" if obs["robots_meta"] else
                "no robots meta")
        seen += (f"; x_robots_tag={obs['x_robots_tag']}" if obs["x_robots_tag"] else
                 "; no X-Robots-Tag")
        return Score.PASS, f"no discovery-blocking directive ({seen})", obs
