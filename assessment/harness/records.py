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

# Third enumeration: a proposition elicited from a model consumer (the G1 EVAL
# observed leg, task 2026-09-02_g1_eval_probe_family_v0 step 1). Eval results are
# partitioned out of BOTH composites in rollup.py exactly as WEB_SURFACE_SOURCES
# are — their own vector, their own denominator, never summed into D1–D4.
SOURCE_EVAL = "eval"
EVAL_SOURCES = (SOURCE_EVAL,)
# Dimensions reported as their own block, never as a fifth core dimension.
EVAL_DIMENSIONS = ("G1",)
# The fourth outcome beside the three scores (design D5): a restatement the
# deterministic parser cannot classify. Counted, reported, never coerced.
UNPARSEABLE = "unparseable"


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


class QualifierClass(enum.Enum):
    """The closed set of uncertainty carriers a proposition may publish (design D1;
    producer definitions: ACS handbook 2020 MOE at 90 %; ONS SE/CI/CV; StatCan
    12-539-X 6e CV bands and suppression; Census DAS handbook 2021 rho/epsilon)."""

    MOE = "MOE"
    CI = "CI"
    SE = "SE"
    CV = "CV"
    RELIABILITY_FLAG = "RELIABILITY_FLAG"
    SUPPRESSION = "SUPPRESSION"
    DP_NOISE = "DP_NOISE"
    VINTAGE = "VINTAGE"


# Qualifier families (design D9, task 2026-09-03_g1_eval_v2 step 3; the table is also in
# harness.toml [g1.families], which the config loader checks against this one). The family
# is the scored unit in v2; the published forms inside it are deterministic transforms of
# one another given the confidence level.
FAMILIES = {
    "interval": ("SE", "MOE", "CI"),
    "relative": ("CV",),
    "reliability": ("RELIABILITY_FLAG", "SUPPRESSION"),
    "dp": ("DP_NOISE",),
    "vintage": ("VINTAGE",),
}
FAMILY_OF = {cls: fam for fam, classes in FAMILIES.items() for cls in classes}
# Compression budget levels (design D12); `none` is the v0/v1 indirect prompt verbatim.
COMPRESSION_LEVELS = ("none", "short", "tight")


class Level(enum.IntEnum):
    """Preservation level of ONE qualifier in ONE restatement (design D2, v0).

    Structure adopted from Du 2026 (ordinal preservation levels, adjacent-level
    confusion as a finding) and van der Bles 2019 (form of expression: numeric
    range / verbal qualifier / none); the numeric levels themselves are G1's
    contribution (memo §4 "open"). Mapped to the harness's three-point Score by
    `level_to_score`: PASS = L4 | L3, PARTIAL = L2, FAIL = L1 | L0. The level and
    the failure class always travel in `observations`, never collapsed into the
    score alone (skeleton §6b.5).
    """

    CORRUPTED = 0              # qualifier present and wrong
    OMITTED = 1                # estimate restated, qualifier absent
    DEGRADED_VERBAL = 2        # numeric qualifier -> verbal band, no number
    PRESERVED_TRANSFORMED = 3  # numeric, correct, under a legitimate transformation
    PRESERVED_EXACT = 4        # class, value, level and binding all restated

    @property
    def label(self) -> str:
        return _LEVEL_LABELS[self]


_LEVEL_LABELS = {
    Level.CORRUPTED: "corrupted",
    Level.OMITTED: "omitted",
    Level.DEGRADED_VERBAL: "degraded_verbal",
    Level.PRESERVED_TRANSFORMED: "preserved_transformed",
    Level.PRESERVED_EXACT: "preserved_exact",
}


def level_to_score(level: "Level") -> "Score":
    """D2 mapping. PASS = L4 or L3; PARTIAL = L2; FAIL = L1 or L0."""
    if level >= Level.PRESERVED_TRANSFORMED:
        return Score.PASS
    if level == Level.DEGRADED_VERBAL:
        return Score.PARTIAL
    return Score.FAIL


class EstimateStatus(enum.Enum):
    """Fidelity of the ESTIMATE, scored separately from qualifier preservation
    (Zhao 2020 quantity-hallucination class; Cao 2024 numeric sub-taxonomy).
    Recorded on every eval record; never feeds the G1 score (design D2)."""

    EXACT = "exact"
    ROUNDED = "rounded"
    WRONG = "wrong"
    ABSENT = "absent"


# Failure-class vocabulary (memo §4.3 first; G1-native names only where no memo
# class fits — see probes/g1_preservation.py for the mapping and its docstring).
FAILURE_CLASSES = (
    "certainty_assertion",      # Du 2026: cue removed, claim restated as definite
    "omission",                 # Du 2026: the uncertainty-bearing proposition dropped
    "decontextualization",      # Lee 2026: number survives, caveat separated
    "overgeneralization",       # Peters & Chin-Yee 2025: scope qualifier widened
    "quantity_hallucination",   # Zhao 2020: a number (or date) not supported by source
    "form_shift",               # G1 (van der Bles form axis): numeric -> verbal band
    "level_change",             # G1: wrong confidence level
    "binding_error",            # G1: qualifier attached to the wrong estimate
    "fabricated_qualifier",     # G1: a qualifier the source does not carry
    "suppression_override",     # G1 (StatCan 6e): suppressed/flagged estimate restated as usable
)


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


@dataclass(frozen=True)
class EvalResult:
    """One (proposition, qualifier, elicitation mode) outcome from the G1 observed
    leg. Same audit shape as ProbeResult plus the eval-specific fields; carries
    `source = SOURCE_EVAL` so the rollup partitions it out of every composite.

    `score` is None exactly when `outcome == UNPARSEABLE` (design D5): the record
    is counted in its own bucket and never coerced into PASS or FAIL.

    `prompt_epoch` and `model_id` are REQUIRED (task step 4): a record missing
    either is invalid — the stamp is what makes a re-run under a changed prompt or
    a substituted model distinguishable from this one.
    """

    probe_id: str
    target: str                       # proposition id
    qualifier_class: str              # QualifierClass.value
    mode: str                         # "indirect" | "direct"
    outcome: str                      # Score name lowercased, or UNPARSEABLE
    score: Optional[Score]
    level: Optional[int]              # Level value, None when unparseable
    failure_class: Optional[str]
    estimate_status: str              # EstimateStatus.value
    model_id: str
    prompt_epoch: str
    evidence: str
    timestamp: str
    evidence_path: str
    # Instrument version of the deterministic parser/scorer that produced the record
    # (task 2026-09-03 step 4.4): required, like prompt_epoch and model_id.
    parser_version: str = ""
    # v2 (task 2026-09-03_g1_eval_v2 step 3): the scorer is versioned separately from the
    # parser (`g1-score-v2` implements D9–D11); required on every record. `family` is the
    # scored unit (D9) — for a v2 record `qualifier_class` names the published form that
    # achieved the family's level (or the family's first published form when none did).
    # `surface_type` / `compression_level` are the v2 factors (D11 covariates on the record).
    scorer_version: str = ""
    family: str = ""
    surface_type: str = ""
    compression_level: str = ""
    dimension: str = "G1"
    track: Track = Track.CORE
    source: str = SOURCE_EVAL
    as_of_date: str = ""
    observations: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.prompt_epoch or not str(self.prompt_epoch).strip():
            raise ValueError(f"EvalResult {self.target}/{self.mode}: prompt_epoch is required")
        if not self.model_id or not str(self.model_id).strip():
            raise ValueError(f"EvalResult {self.target}/{self.mode}: model_id is required")
        if not self.parser_version or not str(self.parser_version).strip():
            raise ValueError(f"EvalResult {self.target}/{self.mode}: parser_version is required")
        if not self.scorer_version or not str(self.scorer_version).strip():
            raise ValueError(f"EvalResult {self.target}/{self.mode}: scorer_version is required")
        if self.family and self.family not in FAMILIES:
            raise ValueError(f"unknown qualifier family {self.family!r}")
        if self.compression_level and self.compression_level not in COMPRESSION_LEVELS:
            raise ValueError(f"unknown compression level {self.compression_level!r}")
        if self.outcome == UNPARSEABLE:
            if self.score is not None or self.level is not None:
                raise ValueError("an unparseable record carries no score and no level")
        else:
            if self.score is None or self.level is None:
                raise ValueError("a scored record must carry both score and level")
            if level_to_score(Level(self.level)) is not self.score:
                raise ValueError(f"score {self.score} does not follow from level {self.level}")
        if self.source not in EVAL_SOURCES:
            raise ValueError(f"EvalResult source must be one of {EVAL_SOURCES}")
        if self.qualifier_class not in {q.value for q in QualifierClass}:
            raise ValueError(f"unknown qualifier class {self.qualifier_class!r}")
        if self.failure_class is not None and self.failure_class not in FAILURE_CLASSES:
            raise ValueError(f"unknown failure class {self.failure_class!r}")

    def to_dict(self) -> dict:
        return {
            "probe_id": self.probe_id,
            "target": self.target,
            "qualifier_class": self.qualifier_class,
            "mode": self.mode,
            "outcome": self.outcome,
            "score": None if self.score is None else int(self.score),
            "level": self.level,
            "level_label": None if self.level is None else Level(self.level).label,
            "failure_class": self.failure_class,
            "estimate_status": self.estimate_status,
            "model_id": self.model_id,
            "prompt_epoch": self.prompt_epoch,
            "parser_version": self.parser_version,
            "scorer_version": self.scorer_version,
            "family": self.family,
            "surface_type": self.surface_type,
            "compression_level": self.compression_level,
            "dimension": self.dimension,
            "track": self.track.label,
            "source": self.source,
            "as_of_date": self.as_of_date,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "evidence_path": self.evidence_path,
            "observations": self.observations,
        }
