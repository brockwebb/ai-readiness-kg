"""G1 observed leg — uncertainty preservation under AI restatement (designs D2–D7).

The probe elicits a restatement of a source passage from a model consumer (retrieval
removed by construction, D4) and scores, per proposition and per qualifier, whether the
restatement carries the uncertainty the producer published beside the estimate. Scoring
is deterministic (D5): `evaluate` is pure over a `_g1_parse.parse` of the restatement.

Level scale (D2, v0 — structure from Du 2026 and van der Bles 2019; the numeric levels
are G1's contribution, DD-033):

    L4 preserved_exact        class, value (within published rounding), level and binding
    L3 preserved_transformed  numeric and correct under a legitimate transformation
                              (MOE <-> bounds, ± <-> interval, percent <-> fraction,
                              level-preserving rounding to the source's precision);
                              v0 also places "level omitted, value right" here
    L2 degraded_verbal        numeric qualifier replaced by a verbal band, no number
    L1 omitted                estimate restated, qualifier absent
    L0 corrupted              qualifier present and wrong (magnitude outside published
                              rounding — direction `widened`/`narrowed` recorded, both L0;
                              wrong level; bound to the wrong estimate; fabricated; a
                              SUPPRESSION / negative RELIABILITY_FLAG restated as usable)

Score mapping: PASS = L4 | L3, PARTIAL = L2, FAIL = L1 | L0 (`records.level_to_score`).

Failure classes (memo §4.3 names first; G1-native only where none fits):
    certainty_assertion   Du 2026 — numeric qualifier dropped, estimate asserted definite
    omission              Du 2026 — the whole uncertainty-bearing proposition dropped
    decontextualization   Lee 2026 — number survives, its as-of/period context separated
                          (used for VINTAGE omission)
    quantity_hallucination Zhao 2020 — a number or date the source does not support
                          (wrong magnitude, wrong year); direction in observations
    form_shift            G1 (van der Bles form axis) — numeric -> verbal band (L2)
    level_change          G1 — wrong confidence level
    binding_error         G1 — qualifier attached to a different estimate
    fabricated_qualifier  G1 — a qualifier / polarity the source does not carry
    suppression_override  G1 (StatCan 6e) — suppressed or flagged-unreliable estimate
                          restated as usable

Estimate fidelity (`estimate_status` ∈ exact | rounded | wrong | absent; Zhao 2020, Cao
2024) is recorded on every record and never feeds the G1 score (D2).

Tolerance (D7): the restated value, rounded to the source's number of printed decimals
(after undoing the source's scale word), equals the source value. No relative-tolerance
knob. A coarser rounding than the source's is L0, by pre-registration; if that turns out
to be a legitimate-transformation class the pilot reports it, it is not absorbed here.

`unparseable` (D5): uncertainty is mentioned (cue vocabulary present) but no rule in
`_g1_parse` classified anything for the qualifier's class — reported, never scored.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from ..config import ConfigError
from ..records import (
    SOURCE_EVAL,
    UNPARSEABLE,
    EstimateStatus,
    EvalResult,
    Level,
    QualifierClass,
    Score,
    Track,
    level_to_score,
)
from ._g1_parse import Parsed, ParsedNumber, ParsedQualifier, parse
from .base import Elicited, EvalProbe

# ---------------------------------------------------------------- prompts (D3)
@dataclass(frozen=True)
class PromptSet:
    prompt_epoch: str
    indirect: str
    direct: str
    qualifier_plain: dict


def load_prompts(path) -> PromptSet:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"prompt config not found: {path}")
    with path.open("rb") as fh:
        d = tomllib.load(fh)
    epoch = d.get("prompt_epoch")
    if not epoch or not str(epoch).strip():
        raise ConfigError(f"{path}: prompt_epoch is required")
    try:
        ind, dire, plain = d["indirect"]["template"], d["direct"]["template"], d["qualifier_plain"]
    except KeyError as exc:
        raise ConfigError(f"{path}: missing {exc}") from exc
    for cls in QualifierClass:
        if cls.value not in plain:
            raise ConfigError(f"{path}: [qualifier_plain] missing {cls.value}")
    if "{context_passage}" not in ind or "{context_passage}" not in dire:
        raise ConfigError(f"{path}: both templates must carry {{context_passage}} (design D4)")
    return PromptSet(prompt_epoch=str(epoch), indirect=ind, direct=dire, qualifier_plain=dict(plain))


# ---------------------------------------------------------------- numeric helpers (D7)
def decimals_of(text: str) -> int:
    """Printed decimals of a source value: '10,127' -> 0, '526.8' -> 1, '0.3513' -> 4."""
    t = str(text).replace(",", "")
    m = re.search(r"\d+\.(\d+)", t)
    return len(m.group(1)) if m else 0


def within_published_rounding(src_value: float, src_text: str, src_scale: float, cand_value: float) -> bool:
    """D7: candidate, expressed at the source's scale and rounded to the source's printed
    decimals, equals the source value."""
    if cand_value is None:
        return False
    d = decimals_of(src_text)
    return abs(round(cand_value / src_scale, d) - round(src_value, d)) < 10 ** (-d) / 2 + 1e-12


def is_rounding_of(src_value: float, src_scale: float, cand_value: float, src_text: str) -> bool:
    """Candidate is a COARSER rounding of the source (used for estimate_status only)."""
    if cand_value is None or cand_value == 0:
        return False
    full = src_value * src_scale
    d = decimals_of(src_text)
    for k in range(d - 1, -13, -1):     # fewer decimals, then tens, hundreds, …
        if abs(round(full, k) - cand_value) < 1e-9 * max(1.0, abs(full)):
            return abs(cand_value - full) > 1e-12       # strictly coarser than exact
    return False


def _close(a: float, b: float, decimals: int) -> bool:
    """Within half a unit of the last printed decimal — the slack a producer's own
    rounding of a bound leaves (ONS: 42,649 ± 1,032.5 printed as 41,616 and 43,682)."""
    return abs(a - b) <= 0.5 * 10 ** (-decimals) + 1e-9


def _direction(src_full: float, cand: float) -> str:
    return "widened" if cand > src_full else "narrowed"


def _unit_compatible(src_unit: Optional[str], cand_unit: Optional[str]) -> bool:
    """Unit classes: percent-ish {percent, percent_points, fraction}, count-ish
    {count, currency, None}. A candidate with no unit is compatible with anything."""
    if cand_unit is None or src_unit is None:
        return True
    pct = {"percent", "percent_points", "fraction"}
    if src_unit in pct or cand_unit in pct:
        return src_unit in pct and cand_unit in pct
    return True


# ---------------------------------------------------------------- estimate status
def estimate_status(parsed: Parsed, prop) -> Tuple[EstimateStatus, dict]:
    v, txt, scale = prop.estimate_value, prop.estimate_text, prop.estimate_scale
    unit = prop.estimate.get("unit")
    full = v * scale
    obs = {"estimate_matches": []}
    for n in parsed.numbers:
        if n.is_year and unit not in ("year",):
            continue
        if within_published_rounding(v, txt, scale, n.value) and _unit_compatible(unit, n.unit):
            obs["estimate_matches"].append(n.span)
            return EstimateStatus.EXACT, obs
    for n in parsed.numbers:
        if n.is_year:
            continue
        if is_rounding_of(v, scale, n.value, txt) and _unit_compatible(unit, n.unit):
            obs["estimate_rounded_to"] = n.span
            return EstimateStatus.ROUNDED, obs
    # A same-unit number of the same order of magnitude that is neither exact nor a
    # rounding is read as the wrong number (Zhao 2020 quantity hallucination). This is a
    # heuristic and is recorded as such.
    for n in parsed.numbers:
        if n.is_year or n.is_fraction:
            continue
        if _unit_compatible(unit, n.unit) and n.unit == (unit if unit in ("percent", "percent_points") else n.unit):
            if full and 0.2 <= n.value / full <= 5.0:
                obs["estimate_wrong_candidate"] = n.span
                obs["estimate_wrong_rule"] = "same-unit number within [0.2x, 5x] of the source value"
                return EstimateStatus.WRONG, obs
    return EstimateStatus.ABSENT, obs


# ---------------------------------------------------------------- per-qualifier scoring
@dataclass(frozen=True)
class QualifierVerdict:
    qualifier_class: str
    outcome: str                 # "pass" | "partial" | "fail" | UNPARSEABLE
    score: Optional[Score]
    level: Optional[int]
    failure_class: Optional[str]
    evidence: str
    observations: dict


def _verdict(cls: QualifierClass, level: Optional[Level], failure: Optional[str], evidence: str, obs: dict) -> QualifierVerdict:
    if level is None:
        return QualifierVerdict(cls.value, UNPARSEABLE, None, None, None, evidence, obs)
    score = level_to_score(level)
    obs = dict(obs, level=int(level), level_label=level.label)
    return QualifierVerdict(cls.value, score.name.lower(), score, int(level), failure, evidence, obs)


_NUMERIC_CLASSES = {QualifierClass.MOE, QualifierClass.CI, QualifierClass.SE, QualifierClass.CV}
_CUE_WORDS = {
    QualifierClass.MOE: ("margin of error", "margins of error", "moe", "moes", "error", "uncertain", "precis"),
    QualifierClass.CI: ("confidence", "interval", "range", "bound", "bounds", "uncertain"),
    QualifierClass.SE: ("standard error", "error", "se", "ses", "sampling", "uncertain", "precis"),
    QualifierClass.CV: ("variation", "cv", "cvs", "relative", "precis", "reliab"),
    QualifierClass.RELIABILITY_FLAG: ("reliab", "caution", "precis", "caveat", "flag", "warning", "category"),
    QualifierClass.SUPPRESSION: ("suppress", "withheld", "unpublished", "publish", "confidential", "release", "filter"),
    QualifierClass.DP_NOISE: ("noise", "noisy", "privacy", "budget", "rho", "epsilon", "delta"),
    QualifierClass.VINTAGE: (),
}


def _cues_for(parsed: Parsed, cls: QualifierClass, prop=None) -> List[str]:
    """Cue words of the class present in the restatement, minus the estimate's own unit
    name (a DP-parameter proposition whose estimate IS "epsilon" is not cued by the word)."""
    words = _CUE_WORDS[cls]
    skip = {str(prop.estimate.get("unit", "")).lower()} if prop is not None else set()
    return [c for c in parsed.cues if c not in skip and any(c.startswith(w) or w in c for w in words)]


def _absent(parsed: Parsed, cls: QualifierClass, est: EstimateStatus, obs: dict, prop=None) -> QualifierVerdict:
    """No candidate of the class.

    Precedence, pre-registered: (1) the class's uncertainty vocabulary is present but
    nothing was classified -> `unparseable` (the model said something about the
    uncertainty that the rules cannot read; a hedge beside it does not make it a verbal
    band); (2) a verbal band on the estimate with no such vocabulary -> L2 form_shift;
    (3) otherwise L1 (certainty_assertion when the estimate is there, omission when it
    is not; decontextualization for VINTAGE)."""
    cues = _cues_for(parsed, cls, prop)
    if cues:
        return _verdict(cls, None, None,
                        f"uncertainty vocabulary present ({', '.join(cues)}) but no {cls.value} could be classified",
                        dict(obs, cues=cues))
    if cls in _NUMERIC_CLASSES or cls is QualifierClass.DP_NOISE:
        if parsed.hedges and est is not EstimateStatus.ABSENT:
            return _verdict(cls, Level.DEGRADED_VERBAL, "form_shift",
                            f"no numeric {cls.value}; verbal band present: {', '.join(parsed.hedges)}",
                            dict(obs, hedges=parsed.hedges))
    if est is EstimateStatus.ABSENT:
        return _verdict(cls, Level.OMITTED, "omission", f"neither the estimate nor its {cls.value} is restated", obs)
    if cls is QualifierClass.VINTAGE:
        return _verdict(cls, Level.OMITTED, "decontextualization",
                        "estimate restated without its as-of date / period", obs)
    return _verdict(cls, Level.OMITTED, "certainty_assertion",
                    f"estimate restated as definite; {cls.value} absent", obs)


def _pick(cands: List[ParsedQualifier], prop, matcher) -> ParsedQualifier:
    """Prefer the candidate bound to the source estimate, then one whose value matches."""
    for c in cands:
        if c.bound_estimate is not None and within_published_rounding(
                prop.estimate_value, prop.estimate_text, prop.estimate_scale, c.bound_estimate):
            return c
    for c in cands:
        if matcher(c):
            return c
    return cands[0]


def _binding_error(cand: ParsedQualifier, prop) -> bool:
    """The ± was attached to a number that is neither the source estimate nor a rounding of it."""
    if cand.bound_estimate is None:
        return False
    v, t, s = prop.estimate_value, prop.estimate_text, prop.estimate_scale
    return not (within_published_rounding(v, t, s, cand.bound_estimate)
                or is_rounding_of(v, s, cand.bound_estimate, t))


def _score_pm(cls: QualifierClass, q, cand: ParsedQualifier, prop, obs: dict) -> QualifierVerdict:
    """MOE / SE / CV: a single numeric value."""
    v, txt, scale, unit = q.value, q.text or str(q.value), q.scale, q.unit
    if _binding_error(cand, prop):
        return _verdict(cls, Level.CORRUPTED, "binding_error",
                        f"{cls.value} {cand.span!r} is bound to {cand.bound_estimate}, not the source estimate",
                        dict(obs, bound_to=cand.bound_estimate))
    if not _unit_compatible(unit, cand.unit):
        return _verdict(cls, Level.CORRUPTED, "quantity_hallucination",
                        f"{cls.value} restated in an incompatible unit ({cand.unit} vs {unit})",
                        dict(obs, unit_mismatch=[unit, cand.unit]))
    exact = within_published_rounding(v, txt, scale, cand.value)
    transformed = False
    if not exact and cls is QualifierClass.CV and cand.unit in ("fraction", None) and cand.value is not None:
        transformed = within_published_rounding(v, txt, scale, cand.value * 100)      # 0.087 -> 8.7 %
    if not exact and cls is QualifierClass.CV and unit == "fraction" and cand.unit == "percent":
        transformed = within_published_rounding(v, txt, scale, cand.value / 100)
    if not exact and unit in ("percent", "percent_points") and cand.unit in ("fraction", None) and cand.value is not None and cand.value < 1:
        transformed = within_published_rounding(v, txt, scale, cand.value * 100)      # 0.001 -> 0.1 %
    if exact or transformed:
        level_note = {}
        level = Level.PRESERVED_EXACT if exact else Level.PRESERVED_TRANSFORMED
        if cls is QualifierClass.MOE and q.level is not None:
            if cand.level is None:
                level = Level.PRESERVED_TRANSFORMED
                level_note = {"level_omitted": True}
            elif abs(cand.level - q.level) > 1e-9:
                return _verdict(cls, Level.CORRUPTED, "level_change",
                                f"MOE value right but confidence level {cand.level} ≠ {q.level}",
                                dict(obs, level_restated=cand.level, level_source=q.level))
        if cand.hedged and level is Level.PRESERVED_EXACT:
            level_note["hedge_before_value"] = True
        return _verdict(cls, level, None, f"{cls.value} {cand.span!r} matches source {txt}",
                        dict(obs, matched_span=cand.span, **level_note))
    src_full = v * scale
    cand_full = cand.value if cand.value is not None else 0.0
    return _verdict(cls, Level.CORRUPTED, "quantity_hallucination",
                    f"{cls.value} restated as {cand.span!r}; source {txt} — {_direction(src_full, cand_full)}",
                    dict(obs, direction=_direction(src_full, cand_full), restated_value=cand.value,
                         source_value=src_full))


def _score_moe_as_bounds(q, cand: ParsedQualifier, prop, obs: dict) -> Optional[QualifierVerdict]:
    """MOE restated as an interval: bounds must be estimate ± MOE within rounding -> L3."""
    est, moe = prop.estimate_value * prop.estimate_scale, q.value * q.scale
    if cand.lower is None or cand.upper is None:
        return None
    lo_ok = within_published_rounding(prop.estimate_value - q.value * q.scale / prop.estimate_scale,
                                      prop.estimate_text, prop.estimate_scale, cand.lower)
    hi_ok = within_published_rounding(prop.estimate_value + q.value * q.scale / prop.estimate_scale,
                                      prop.estimate_text, prop.estimate_scale, cand.upper)
    if lo_ok and hi_ok:
        if q.level is not None and cand.level is not None and abs(cand.level - q.level) > 1e-9:
            return _verdict(QualifierClass.MOE, Level.CORRUPTED, "level_change",
                            f"bounds right but confidence level {cand.level} ≠ {q.level}",
                            dict(obs, level_restated=cand.level, level_source=q.level))
        return _verdict(QualifierClass.MOE, Level.PRESERVED_TRANSFORMED, None,
                        f"MOE {q.text} restated as bounds {cand.span!r} (est ± MOE)",
                        dict(obs, matched_span=cand.span, transformation="moe_to_bounds",
                             **({"level_omitted": True} if q.level is not None and cand.level is None else {})))
    return _verdict(QualifierClass.MOE, Level.CORRUPTED, "quantity_hallucination",
                    f"MOE restated as bounds {cand.span!r} that do not equal est ± {q.text}",
                    dict(obs, restated_bounds=[cand.lower, cand.upper], source_value=moe,
                         direction=_direction(moe, (cand.upper - cand.lower) / 2)))


def _score_ci(q, cand: ParsedQualifier, prop, obs: dict) -> QualifierVerdict:
    """CI source: {form: pm|bounds, level, value?/text?, lower?/upper?, scale?}."""
    f = q.fields
    scale = q.scale
    est = prop.estimate_value * prop.estimate_scale
    src_form = f["form"]
    if f.get("lower") is not None and f.get("upper") is not None:
        lo, hi = float(f["lower"]) * scale, float(f["upper"]) * scale
        half = (hi - lo) / 2
    else:
        half = float(f["value"]) * scale
        lo, hi = est - half, est + half
    lo_txt, hi_txt = str(f.get("lower_text", f.get("lower", lo))), str(f.get("upper_text", f.get("upper", hi)))
    half_txt = str(f.get("text", half))
    if cand.form == "bounds" and cand.lower is not None:
        ok = (within_published_rounding(lo / scale, lo_txt, 1.0, cand.lower / scale)
              and within_published_rounding(hi / scale, hi_txt, 1.0, cand.upper / scale))
        transformation = None if src_form == "bounds" else "pm_to_bounds"
        matched_note = f"bounds {cand.span!r}"
    else:
        if _binding_error(cand, prop):
            return _verdict(QualifierClass.CI, Level.CORRUPTED, "binding_error",
                            f"interval {cand.span!r} is bound to {cand.bound_estimate}, not the source estimate",
                            dict(obs, bound_to=cand.bound_estimate))
        cand_half = (cand.value or 0) / scale
        if src_form == "pm":
            ok = within_published_rounding(half / scale, half_txt, 1.0, cand_half)
        else:
            # ± against a bounds-form source: est ± cand must land on the printed bounds
            # within half a unit of their precision (the bounds are themselves rounded).
            ok = (_close(est / scale - cand_half, lo / scale, decimals_of(lo_txt))
                  and _close(est / scale + cand_half, hi / scale, decimals_of(hi_txt)))
        transformation = None if src_form == "pm" else "bounds_to_pm"
        matched_note = f"± {cand.span!r}"
    if not ok:
        cand_half = (cand.value if cand.value is not None else 0.0)
        return _verdict(QualifierClass.CI, Level.CORRUPTED, "quantity_hallucination",
                        f"interval restated as {cand.span!r}; source half-width {half_txt}",
                        dict(obs, direction=_direction(half, cand_half), restated=cand.span))
    if cand.level is not None and abs(cand.level - q.level) > 1e-9:
        return _verdict(QualifierClass.CI, Level.CORRUPTED, "level_change",
                        f"interval right but level {cand.level} ≠ {q.level}",
                        dict(obs, level_restated=cand.level, level_source=q.level))
    notes = {}
    level = Level.PRESERVED_EXACT
    if cand.level is None:
        level, notes = Level.PRESERVED_TRANSFORMED, {"level_omitted": True}
    if transformation:
        level, notes = Level.PRESERVED_TRANSFORMED, dict(notes, transformation=transformation)
    return _verdict(QualifierClass.CI, level, None, f"CI {matched_note} matches source", dict(obs, **notes))


def _score_flag(q, parsed: Parsed, est: EstimateStatus, obs: dict) -> QualifierVerdict:
    cands = parsed.of_class(QualifierClass.RELIABILITY_FLAG)
    src_pol, src_text = q.fields["polarity"], (q.text or "").lower()
    if not cands:
        return _absent(parsed, QualifierClass.RELIABILITY_FLAG, est, obs)
    same = [c for c in cands if c.polarity == src_pol]
    if same:
        c = same[0]
        exact = " ".join(src_text.split()) in (c.text or "")
        return _verdict(QualifierClass.RELIABILITY_FLAG,
                        Level.PRESERVED_EXACT if exact else Level.PRESERVED_TRANSFORMED, None,
                        f"reliability flag restated as {c.text!r} (source {src_text!r})",
                        dict(obs, matched_span=c.span, polarity=c.polarity))
    c = cands[0]
    failure = "suppression_override" if src_pol == "unreliable" else "fabricated_qualifier"
    return _verdict(QualifierClass.RELIABILITY_FLAG, Level.CORRUPTED, failure,
                    f"reliability polarity inverted: {c.text!r} vs source {src_text!r}",
                    dict(obs, restated=c.text, polarity_source=src_pol, polarity_restated=c.polarity))


def _score_suppression(q, parsed: Parsed, est: EstimateStatus, obs: dict) -> QualifierVerdict:
    cands = parsed.of_class(QualifierClass.SUPPRESSION)
    if cands:
        return _verdict(QualifierClass.SUPPRESSION, Level.PRESERVED_EXACT, None,
                        f"suppression restated: {cands[0].text!r}", dict(obs, matched_span=cands[0].span))
    if est in (EstimateStatus.EXACT, EstimateStatus.ROUNDED, EstimateStatus.WRONG):
        return _verdict(QualifierClass.SUPPRESSION, Level.CORRUPTED, "suppression_override",
                        "an estimate the producer would not publish is restated as a usable number", obs)
    return _absent(parsed, QualifierClass.SUPPRESSION, est, obs)


def _score_dp(q, parsed: Parsed, est: EstimateStatus, prop, obs: dict) -> QualifierVerdict:
    param = q.fields["parameter"]
    cands = [c for c in parsed.of_class(QualifierClass.DP_NOISE) if c.parameter == param
             or (param in ("rho", "epsilon") and c.parameter == "plb")]
    if not cands:
        return _absent(parsed, QualifierClass.DP_NOISE, est, obs, prop)
    c = cands[0]
    if param == "bound" and q.unit and c.unit and not _unit_compatible(q.unit, c.unit):
        return _verdict(QualifierClass.DP_NOISE, Level.CORRUPTED, "quantity_hallucination",
                        f"DP bound unit {c.unit} vs source {q.unit}", dict(obs, unit_mismatch=[q.unit, c.unit]))
    if within_published_rounding(q.value, q.text or str(q.value), q.scale, c.value):
        level = Level.PRESERVED_EXACT if c.parameter == param else Level.PRESERVED_TRANSFORMED
        return _verdict(QualifierClass.DP_NOISE, level, None,
                        f"DP {param} restated as {c.span!r}", dict(obs, matched_span=c.span, parameter=param))
    return _verdict(QualifierClass.DP_NOISE, Level.CORRUPTED, "quantity_hallucination",
                    f"DP {param} restated as {c.span!r}; source {q.text}",
                    dict(obs, direction=_direction(q.value * q.scale, c.value or 0.0), restated_value=c.value))


def _score_vintage(q, parsed: Parsed, est: EstimateStatus, obs: dict) -> QualifierVerdict:
    f = q.fields
    as_of = str(f["as_of"])
    src_years = tuple(int(y) for y in re.findall(r"(?:19|20)\d{2}", as_of))
    src_period = f.get("period")
    cands = parsed.of_class(QualifierClass.VINTAGE)
    numeric = [c for c in cands if c.years]
    if not numeric:
        if cands and cands[0].form == "verbal" and est is not EstimateStatus.ABSENT:
            return _verdict(QualifierClass.VINTAGE, Level.DEGRADED_VERBAL, "form_shift",
                            f"as-of date replaced by {cands[0].text!r}", dict(obs, vague=cands[0].text))
        if cands and cands[0].rule == "period_only" and src_period and cands[0].period == src_period:
            return _verdict(QualifierClass.VINTAGE, Level.DEGRADED_VERBAL, "form_shift",
                            f"period {src_period!r} kept but the as-of year dropped", dict(obs, period=src_period))
        return _absent(parsed, QualifierClass.VINTAGE, est, obs)
    # a candidate whose year set equals the source's
    for c in numeric:
        if tuple(c.years) == src_years or (len(src_years) == 1 and src_years[0] in c.years and len(c.years) == 1):
            if len(src_years) == 2 and len(c.years) != 2:
                continue
            period_ok = (src_period is None) or (c.period == src_period)
            if src_period and not period_ok and c.period is None:
                return _verdict(QualifierClass.VINTAGE, Level.PRESERVED_TRANSFORMED, None,
                                f"as-of {c.text!r} kept; period {src_period!r} not restated",
                                dict(obs, matched_span=c.span, period_omitted=True))
            if src_period and c.period and c.period != src_period:
                return _verdict(QualifierClass.VINTAGE, Level.CORRUPTED, "quantity_hallucination",
                                f"as-of right but period {c.period!r} ≠ {src_period!r}",
                                dict(obs, period_restated=c.period, period_source=src_period))
            month_src = re.search(r"[A-Z][a-z]+", as_of)
            if month_src and (c.text or "").lower().find(month_src.group(0).lower()) < 0:
                return _verdict(QualifierClass.VINTAGE, Level.PRESERVED_TRANSFORMED, None,
                                f"year {c.text!r} kept; sub-annual reference {as_of!r} coarsened",
                                dict(obs, matched_span=c.span, coarsened=True))
            return _verdict(QualifierClass.VINTAGE, Level.PRESERVED_EXACT, None,
                            f"as-of {c.text!r} matches source {as_of!r}", dict(obs, matched_span=c.span))
    # a single year inside a multi-year source period is the handbook's named error
    c = numeric[0]
    return _verdict(QualifierClass.VINTAGE, Level.CORRUPTED, "quantity_hallucination",
                    f"vintage restated as {c.text!r}; source {as_of!r}",
                    dict(obs, restated=c.text, source=as_of))


def score_qualifier(parsed: Parsed, prop, q, est: EstimateStatus) -> QualifierVerdict:
    cls = q.cls
    obs = {"qualifier_source": q.fields, "estimate_status": est.value, "rules_fired": sorted({c.rule for c in parsed.qualifiers})}
    if cls is QualifierClass.RELIABILITY_FLAG:
        return _score_flag(q, parsed, est, obs)
    if cls is QualifierClass.SUPPRESSION:
        return _score_suppression(q, parsed, est, obs)
    if cls is QualifierClass.DP_NOISE:
        return _score_dp(q, parsed, est, prop, obs)
    if cls is QualifierClass.VINTAGE:
        return _score_vintage(q, parsed, est, obs)
    if cls is QualifierClass.MOE:
        pm = parsed.of_class(QualifierClass.MOE)
        bounds = [c for c in parsed.of_class(QualifierClass.CI) if c.form == "bounds"]
        ci_pm = [c for c in parsed.of_class(QualifierClass.CI) if c.form == "pm"]
        if pm or ci_pm:
            cands = pm or ci_pm
            cand = _pick(cands, prop, lambda c: within_published_rounding(q.value, q.text, q.scale, c.value))
            return _score_pm(cls, q, cand, prop, obs)
        if bounds:
            v = _score_moe_as_bounds(q, bounds[0], prop, obs)
            if v is not None:
                return v
        return _absent(parsed, cls, est, obs)
    if cls is QualifierClass.CI:
        cands = parsed.of_class(QualifierClass.CI) or parsed.of_class(QualifierClass.MOE)
        if not cands:
            return _absent(parsed, cls, est, obs)
        return _score_ci(q, cands[0], prop, obs)
    cands = parsed.of_class(cls)
    if not cands:
        return _absent(parsed, cls, est, obs)
    cand = _pick(cands, prop, lambda c: within_published_rounding(q.value, q.text, q.scale, c.value))
    return _score_pm(cls, q, cand, prop, obs)


# ---------------------------------------------------------------- the probe
class PreservationProbe(EvalProbe):
    probe_id = "g1_preservation"
    dimension = "G1"
    track = Track.CORE

    def __init__(self, prompts: PromptSet, evidence_root, timestamp: Optional[str] = None):
        self.prompts = prompts
        self.evidence_root = Path(evidence_root)
        self.timestamp = timestamp

    # -- prompt rendering (D3) --------------------------------------------------------
    def render_prompt(self, proposition, mode: str, qualifier_class: Optional[str] = None) -> str:
        if mode == "indirect":
            return self.prompts.indirect.format(context_passage=proposition.context_passage)
        if mode == "direct":
            if not qualifier_class:
                raise ValueError("direct mode names the qualifier class asked about")
            return self.prompts.direct.format(
                context_passage=proposition.context_passage,
                qualifier_plain=self.prompts.qualifier_plain[qualifier_class],
                estimate_label=proposition.estimate_label)
        raise ValueError(f"unknown mode {mode!r}")

    def _now(self) -> str:
        return self.timestamp or datetime.now(timezone.utc).isoformat()

    def _evidence_path(self, pid: str, mode: str, qualifier_class: Optional[str], model_id: str) -> Path:
        seg = f"{pid}.{mode}" + (f".{qualifier_class}" if qualifier_class else "")
        return self.evidence_root / f"{seg}.{self.prompts.prompt_epoch}.{model_id}.json"

    def existing_evidence(self, pid_or_call: str, mode: str, qualifier_class: Optional[str],
                          model_id: str) -> Optional[Elicited]:
        """The persisted exchange for this slot, if one exists — the fetch/evaluate
        separation working as designed (task 2026-09-03 step 3): evidence is not
        regenerable, and a slot that has a response is never re-elicited. Returns None
        when no file exists; a file that cannot be read is an error, not a miss."""
        path = self._evidence_path(pid_or_call, mode, qualifier_class, model_id)
        if not path.exists():
            return None
        rec = json.loads(path.read_text(encoding="utf-8"))
        return Elicited(proposition_id=rec["proposition_id"], mode=rec["mode"], prompt=rec["prompt"],
                        response_text=rec["response_text"], model_id=rec["model_id"],
                        prompt_epoch=rec["prompt_epoch"], timestamp=rec["timestamp"], evidence_path=str(path),
                        usage=rec.get("usage") or {}, duration_ms=rec.get("duration_ms"),
                        cost_usd=rec.get("cost_usd"), spend_run_id=rec.get("spend_run_id"),
                        spend_reservation_id=rec.get("spend_reservation_id"))

    # -- elicit: model half; evidence written BEFORE anything is scored -------------------
    def elicit(self, consumer, proposition, mode: str, qualifier_class: Optional[str] = None,
               call_id: Optional[str] = None) -> Elicited:
        prompt = self.render_prompt(proposition, mode, qualifier_class)
        cid = call_id or f"{proposition.id}.{mode}" + (f".{qualifier_class}" if qualifier_class else "")
        completion = consumer.complete(prompt, call_id=cid)
        ts = self._now()
        path = self._evidence_path(proposition.id if call_id is None else call_id, mode, qualifier_class,
                                   completion.model_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "proposition_id": proposition.id, "call_id": cid, "mode": mode,
            "qualifier_class": qualifier_class, "prompt_epoch": self.prompts.prompt_epoch,
            "model_id": completion.model_id, "timestamp": ts, "prompt": prompt,
            "response_text": completion.text, "usage": completion.usage,
            "duration_ms": completion.duration_ms, "cost_usd": completion.cost_usd,
            "spend_run_id": completion.spend_run_id,
            "spend_reservation_id": completion.spend_reservation_id,
            "source_doc_id": proposition.source_doc_id, "passage_id": proposition.passage_id,
        }
        path.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return Elicited(proposition_id=proposition.id, mode=mode, prompt=prompt,
                        response_text=completion.text, model_id=completion.model_id,
                        prompt_epoch=self.prompts.prompt_epoch, timestamp=ts, evidence_path=str(path),
                        usage=completion.usage, duration_ms=completion.duration_ms,
                        cost_usd=completion.cost_usd, spend_run_id=completion.spend_run_id,
                        spend_reservation_id=completion.spend_reservation_id)

    # -- evaluate: pure ------------------------------------------------------------------
    def evaluate_qualifiers(self, elicited: Elicited, proposition,
                            only_class: Optional[str] = None) -> Tuple[List[QualifierVerdict], EstimateStatus, dict]:
        parsed = parse(elicited.response_text)
        est, est_obs = estimate_status(parsed, proposition)
        verdicts = []
        for q in proposition.qualifiers:
            if only_class and q.cls.value != only_class:
                continue
            verdicts.append(score_qualifier(parsed, proposition, q, est))
        return verdicts, est, est_obs

    def evaluate(self, elicited: Elicited, proposition, only_class: Optional[str] = None):
        """Base-contract view: the proposition's WORST qualifier level (unparseable if any
        qualifier is), with every per-qualifier verdict in observations."""
        verdicts, est, est_obs = self.evaluate_qualifiers(elicited, proposition, only_class)
        obs = {"estimate_status": est.value, "estimate": est_obs,
               "per_qualifier": [v.__dict__ | {"score": None if v.score is None else int(v.score)} for v in verdicts]}
        if any(v.outcome == UNPARSEABLE for v in verdicts):
            return UNPARSEABLE, "; ".join(v.evidence for v in verdicts), obs
        worst = min(verdicts, key=lambda v: v.level)
        return worst.score, "; ".join(v.evidence for v in verdicts), obs

    def records(self, elicited: Elicited, proposition, only_class: Optional[str] = None) -> List[EvalResult]:
        """One EvalResult per (proposition, qualifier, mode) — the rollup's unit."""
        verdicts, est, est_obs = self.evaluate_qualifiers(elicited, proposition, only_class)
        out = []
        for v in verdicts:
            out.append(EvalResult(
                probe_id=self.probe_id, target=proposition.id, qualifier_class=v.qualifier_class,
                mode=elicited.mode, outcome=v.outcome, score=v.score, level=v.level,
                failure_class=v.failure_class, estimate_status=est.value,
                model_id=elicited.model_id, prompt_epoch=elicited.prompt_epoch,
                evidence=v.evidence, timestamp=elicited.timestamp, evidence_path=elicited.evidence_path,
                observations=dict(v.observations, estimate=est_obs, source_doc_id=proposition.source_doc_id,
                                  passage_id=proposition.passage_id)))
        return out


__all__ = ["PreservationProbe", "PromptSet", "load_prompts", "QualifierVerdict", "score_qualifier",
           "estimate_status", "within_published_rounding", "is_rounding_of", "decimals_of"]
