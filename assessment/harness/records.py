"""The probe result data model: the score scale, the track firewall, and the
emitted record shape.

A ProbeResult is the atomic unit the harness produces. Its serialized form is the
on-disk audit record — a reviewer reads it (plus the raw evidence file it points
to) and can confirm the score without re-running anything.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

# --- Enumeration sources -----------------------------------------------------
# Which enumeration produced a target. Carried on every ProbeResult because the
# rollup partitions on it: catalog distributions and web-surface pages measure
# DIFFERENT surfaces, and the whole point of the second source is that the two
# can diverge, so summing them into one number would destroy the finding.
SOURCE_SITE = "site"          # a well-known path off base_url (robots, sitemap, ...)
SOURCE_CATALOG = "data.json"  # a distribution or dataset record from the DCAT catalog
SOURCE_SITEMAP = "sitemap"    # an HTML page sampled from the declared sitemap

# The sources whose results form the web-surface vector, partitioned out of the
# catalog composite in rollup.py the same way frontier tracks are.
WEB_SURFACE_SOURCES = (SOURCE_SITEMAP,)


class Score(enum.IntEnum):
    """Pass / partial / fail only (2 / 1 / 0).

    Deliberately a three-point scale — finer scales invite interpretation theater
    and Goodhart gaming (rubric: "Deliberately excluded (anti-PMT)").
    """

    FAIL = 0
    PARTIAL = 1
    PASS = 2


class Track(enum.Enum):
    """The core-vs-frontier firewall.

    Traces to icsp_notebook task 51fe4574, flagship term "AI-ready data":
      - CORE          = Part A, the grounded content-side definition (data a
                        consuming system can already reach). Counts toward the
                        headline composite.
      - FRONTIER_NEAR = Part B, llms.txt — readily achievable forward-lean.
      - FRONTIER_DEEP = Part B, MCP / WebMCP — visionary forward-lean.

    Only CORE feeds the composite. Frontier presence is an asset; frontier absence
    is never scored as core unreadiness.

    Each member carries `in_core_composite` and a default `as_of_date` so the
    firewall and the dating convention live in the type, not in scattered prose.
    """

    CORE = ("core", True, "")
    FRONTIER_NEAR = ("frontier_near", False, "2024-09")
    FRONTIER_DEEP = ("frontier_deep", False, "2026-01")

    def __init__(self, label: str, in_core_composite: bool, as_of_date: str):
        self.label = label
        self.in_core_composite = in_core_composite
        self.as_of_date = as_of_date

    def __str__(self) -> str:
        return self.label


@dataclass(frozen=True)
class ProbeResult:
    """One probe's outcome against one target, with the raw artifact that produced
    the score travelling alongside it."""

    probe_id: str
    target: str
    # Core dimension ("D1".."D4") or None for frontier-track probes.
    dimension: Optional[str]
    track: Track
    score: Score
    # Standardization/availability date for frontier probes; "" for core.
    as_of_date: str
    # The raw response / artifact the score was read from (auditable, not asserted).
    evidence: str
    timestamp: str
    # Path to the evidence file written to disk beside the score.
    evidence_path: str
    # Which enumeration produced this target (SOURCE_* above). Defaults to the
    # catalog so every pre-existing caller keeps its meaning.
    source: str = SOURCE_CATALOG
    # Observed facts, structured, separate from the score and from any warning
    # (assessment protocol / skeleton §6b.5: raw observations are stored apart
    # from calculated warnings, and warnings carry a versioned rule id so a
    # threshold can change and history can be re-scored). Field names follow the
    # SEO Machine Diagnostic data dictionary where one exists (`robots_meta`,
    # `x_robots_tag`, `sitemap_lastmod`, `sitemap_source`,
    # `effective_crawler_access`, `crawler_policy_mismatch_warning`) so a future
    # item-level crosswalk lines up. Empty for probes that emit none.
    observations: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """JSON-serializable record. This is the on-disk audit shape fixed by the
        CC task: {score, evidence, probe_id, target, timestamp, track, as_of_date}
        plus dimension, evidence_path and source for the rollup and reviewer."""
        return {
            "probe_id": self.probe_id,
            "target": self.target,
            "dimension": self.dimension,
            "track": self.track.label,
            "score": int(self.score),
            "as_of_date": self.as_of_date,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "evidence_path": self.evidence_path,
            "source": self.source,
            "observations": self.observations,
        }
