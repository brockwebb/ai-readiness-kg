"""The probe result data model: the score scale, the track firewall, and the
emitted record shape.

A ProbeResult is the atomic unit the harness produces. Its serialized form is the
on-disk audit record — a reviewer reads it (plus the raw evidence file it points
to) and can confirm the score without re-running anything.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional


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

    def to_dict(self) -> dict:
        """JSON-serializable record. This is the on-disk audit shape fixed by the
        CC task: {score, evidence, probe_id, target, timestamp, track, as_of_date}
        plus dimension and evidence_path for the rollup and reviewer."""
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
        }
