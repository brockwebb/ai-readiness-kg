"""G1 observed leg — uncertainty preservation under AI restatement (designs D2–D7, v2 D9–D12).

The probe elicits a restatement of a source passage from a model consumer (retrieval
removed by construction, D4) and scores, per proposition and per qualifier FAMILY (D9),
whether the restatement carries the uncertainty the producer published beside the
estimate. Scoring is deterministic (D5): `evaluate` is pure over a `_g1_parse.parse` of the
restatement.

Level scale (D2, v0 — structure from Du 2026 and van der Bles 2019; the numeric levels
are G1's contribution, DD-033):

    L4 preserved_exact        class, value (within published rounding), level and binding
    L3 preserved_transformed  numeric and correct under a legitimate transformation
                              (MOE <-> bounds, ± <-> interval, percent <-> fraction,
                              level-preserving rounding to the source's precision, a
                              cross-form derivation inside the family — CI given where SE
                              was published; a value restated without its scale word)
    L2 degraded_verbal        numeric qualifier replaced by a verbal band, no number
    L1 omitted                estimate restated, qualifier absent (v2 D10: no candidate
                              BOUND to this estimate)
    L0 corrupted              a bound qualifier that is wrong (magnitude outside published
                              rounding — direction `widened`/`narrowed` recorded, both L0;
                              wrong level; fabricated; a SUPPRESSION / negative
                              RELIABILITY_FLAG restated as usable; `binding_error` only
                              when a candidate bound to ANOTHER estimate is presented as
                              this one's)

Score mapping: PASS = L4 | L3, PARTIAL = L2, FAIL = L1 | L0 (`records.level_to_score`).

v2 (task 2026-09-03_g1_eval_v2_product_surfaces_compression step 3, DD-035):

    D9  families — {SE, MOE, CI} = `interval`, {CV} = `relative`, {RELIABILITY_FLAG,
        SUPPRESSION} = `reliability`, {DP_NOISE} = `dp`, {VINTAGE} = `vintage`. The record
        unit is (proposition, family, mode[, compression]); family level = the best level any
        published form achieved; the per-form verdicts travel in observations["forms"].
        Cross-family derivations (an SE stated where only a CV was published, or a CV where
        only an interval form was) score the target family L3 only when the estimate is
        also restated correctly, recorded as `cross_family_derivation`.
    D10 binding — a candidate counts as THIS estimate's only if bound to it (a ± anchored on
        the estimate's value; the estimate's value or row label restated within the
        configured window in the same sentence or line; in direct mode the question itself
        is the explicit reference). No bound candidate -> L1 `omission` (with
        `estimate_restated` recorded, which is Du 2026's certainty assertion when true).
    D11 covariates on every record, never scored: relative_deviation, rounding_direction,
        summary_precision_consistent, compression_ratio, footnote_distance_chars,
        declared_leg_score, surface_type, compression_level, consumer_model_id.
    D12 compression — the indirect prompt has three levels (`none` = v0/v1 verbatim,
        `short`, `tight`); a slot whose prompt text is byte-identical to a v0-epoch slot
        for the same model is the same slot and its evidence is reused, never re-elicited.

Estimate fidelity (`estimate_status` ∈ exact | rounded | wrong | absent; Zhao 2020, Cao
2024) is recorded on every record and never feeds the G1 score (D2).

Tolerance (D7): the restated value, rounded to the source's number of printed decimals
(after undoing the source's scale word), equals the source value. No relative-tolerance
knob. A coarser rounding than the source's is L0, by pre-registration. v2 adds one
transformation, not a tolerance: a value restated at the surface's DISPLAY scale (a
"Persons in thousands" column restated as 2,670.0 with no scale word) is L3 with
`scale_word_omitted` recorded.

`unparseable` (D5): uncertainty is mentioned (cue vocabulary present) but no rule in
`_g1_parse` classified anything for the family's classes anywhere in the response —
reported, never scored. When candidates exist but none is bound to this estimate, that is
an omission (D10), not unparseable.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import ConfigError
from ..records import (
    COMPRESSION_LEVELS,
    FAMILIES,
    FAMILY_OF,
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
from ._g1_parse import _LEVEL_RE, PARSER_VERSION, Parsed, ParsedNumber, ParsedQualifier, parse
from .base import Elicited, EvalProbe

# Instrument version of the scorer (DD-035): versioned beside the parser; stamped on every
# record. v2 implements D9–D11; records scored under different versions are never pooled.
SCORER_VERSION = "g1-score-v2"

# The v0-epoch prompt set whose `none` indirect and direct templates the v2 set reproduces
# byte for byte (g1_prompts.toml, DD-035): evidence under this epoch is reusable for those slots.
LEGACY_EPOCHS = ("g1-v0-2026-09-02",)


# ---------------------------------------------------------------- prompts (D3, D12)
@dataclass(frozen=True)
class PromptSet:
    prompt_epoch: str
    indirect: str
    direct: str
    qualifier_plain: dict
    compression: dict           # level -> indirect template (D12); `none` == indirect

    def indirect_template(self, compression: str = "none") -> str:
        if compression not in self.compression:
            raise ValueError(f"unknown compression level {compression!r} (have {sorted(self.compression)})")
        return self.compression[compression]


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
    comp = d["indirect"].get("compression")
    if comp is None:
        comp = {"none": ind}         # a v0-shaped file: one level
    if not isinstance(comp, dict) or set(comp) != set(COMPRESSION_LEVELS):
        raise ConfigError(f"{path}: [indirect.compression] must define exactly {COMPRESSION_LEVELS}")
    if comp["none"] != ind:
        raise ConfigError(f"{path}: [indirect.compression].none must equal [indirect].template verbatim (D12)")
    for lvl, tpl in comp.items():
        if "{context_passage}" not in tpl:
            raise ConfigError(f"{path}: compression template {lvl!r} must carry {{context_passage}} (design D4)")
    return PromptSet(prompt_epoch=str(epoch), indirect=ind, direct=dire, qualifier_plain=dict(plain),
                     compression={k: str(v) for k, v in comp.items()})


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


def at_display_scale(src_value: float, src_text: str, src_scale: float, cand_value: float) -> bool:
    """v2: the candidate equals the source value as PRINTED on a scaled surface (the
    'Persons in thousands' column's 2,670.0 restated as 2,670.0 with no scale word). Only
    meaningful when the source carries a scale word; a legitimate transformation (L3), never
    exact."""
    if cand_value is None or src_scale == 1:
        return False
    d = decimals_of(src_text)
    return abs(round(cand_value, d) - round(src_value, d)) < 10 ** (-d) / 2 + 1e-12


def is_rounding_of(src_value: float, src_scale: float, cand_value: float, src_text: str) -> bool:
    """Candidate is a COARSER rounding of the source (used for estimate_status only)."""
    if cand_value is None or cand_value == 0:
        return False
    full = src_value * src_scale
    d = decimals_of(src_text)
    for k in range(d - 1, -13, -1):     # fewer decimals, then tens, hundreds, …
        rounded = round(full, k)
        if rounded == 0:
            break                        # rounding to zero identifies nothing (v2 fix: 2.3e9 "rounds" to 0.087)
        if abs(rounded - cand_value) < 1e-9 * max(1.0, abs(full)):
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
    {count, currency, rate, None}. A candidate with no unit is compatible with anything."""
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
        if at_display_scale(v, txt, scale, n.value) and _unit_compatible(unit, n.unit):
            obs["estimate_matches"].append(n.span)
            obs["scale_word_omitted"] = True
            return EstimateStatus.EXACT, obs
    for n in parsed.numbers:
        if n.is_year:
            continue
        for alt in _estimate_forms(prop)[1:]:
            if within_published_rounding(alt, txt, scale, n.value) and _unit_compatible(unit, n.unit):
                obs["estimate_matches"].append(n.span)
                obs["estimate_unit_transformed"] = True     # 0.05 stated as "5 percentage points"
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


# ---------------------------------------------------------------- binding (D10)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“(])|\n")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9,'\-]*[a-z0-9]|[a-z0-9]")
_YEAR_TOKEN = re.compile(r"^(?:19|20)\d{2}$")


def _label_tokens(prop, stop_words) -> List[str]:
    """Content tokens of the estimate's label and row key (D10 explicit reference); years
    are vintage, not row identity."""
    # parentheticals on a label are metadata ("(2015 ACS 1-year)", "(Table B19001)",
    # "(percent)", "(seasonally adjusted)"), not row identity
    src = [re.sub(r"\([^)]*\)", " ", prop.estimate_label)]
    if prop.binding:
        src.append(str(prop.binding.get("row_key") or ""))
    toks = []
    for text in src:
        for t in _TOKEN.findall(text.lower()):
            t = t.strip(",")
            if t in stop_words or len(t) < 3 or t in toks or _YEAR_TOKEN.match(t):
                continue
            toks.append(t)
    return toks


_ROW_CACHE: dict = {}
_TOK_RE_CACHE: dict = {}


def _has_tok(tok: str, text: str) -> bool:
    """Whole-word token match ("employment" is not inside "unemployment")."""
    rx = _TOK_RE_CACHE.get(tok)
    if rx is None:
        rx = _TOK_RE_CACHE[tok] = re.compile(r"(?<![a-z0-9])" + re.escape(tok) + r"(?![a-z0-9])")
    return bool(rx.search(text))


def _passage_rows(passage: str) -> List[str]:
    """The rows a passage's estimates sit in: its lines when it is a table (three or more
    lines carry digits), else its sentences."""
    key = hash(passage)
    if key in _ROW_CACHE:
        return _ROW_CACHE[key]
    lines = [ln for ln in passage.split("\n") if any(ch.isdigit() for ch in ln)]
    if len(lines) >= 3:
        rows = [ln.lower() for ln in lines]
    else:
        rows = [snt.lower() for snt in _SENTENCE_BREAK.split(passage) if any(ch.isdigit() for ch in snt)]
    _ROW_CACHE[key] = rows
    return rows


def label_token_classes(prop, stop_words) -> Tuple[List[str], List[str]]:
    """(row_specific, generic): label tokens the consumer could have seen (present in the
    passage), split by whether they pick this row out — a token in at most half of the
    passage's rows is row-specific ("youth" in three of twelve CCHS rows; "rate" in six of
    eighteen LFS rows; "$15,000" in one table row), one in most rows is generic ("Newfoundland" on every row; "Fairfax" through
    a paragraph about Fairfax). Tokens absent from the passage cannot identify the row to
    the consumer and are dropped; if none remain, every label token counts as generic."""
    toks = _label_tokens(prop, stop_words)
    rows = _passage_rows(prop.context_passage)
    low = prop.context_passage.lower()
    present = [t for t in toks if _has_tok(t, low)]
    if not present:
        return [], toks
    if not rows:
        return [], present
    specific, generic = [], []
    for t in present:
        share = sum(1 for r in rows if _has_tok(t, r)) / len(rows)
        (specific if share <= 0.5 else generic).append(t)
    return specific, generic


def _estimate_forms(prop) -> List[float]:
    """The estimate's value and its unit-transformed forms (a fraction as a percent or in
    percentage points, and back): 0.05 published as a fraction is "5 percentage points"."""
    v = prop.estimate_value
    unit = prop.estimate.get("unit")
    forms = [v]
    if unit == "fraction":
        forms.append(v * 100)
    elif unit in ("percent", "percent_points"):
        forms.append(v / 100)
    return forms


def estimate_positions(parsed: Parsed, prop) -> List[int]:
    """Character offsets (in the normalised text) of numbers that restate the estimate."""
    txt, scale = prop.estimate_text, prop.estimate_scale
    unit = prop.estimate.get("unit")
    out = []
    for n in parsed.numbers:
        if n.is_year and unit != "year":
            continue
        if not _unit_compatible(unit, n.unit):
            continue
        for v in _estimate_forms(prop):
            if within_published_rounding(v, txt, scale, n.value) or at_display_scale(v, txt, scale, n.value) \
                    or _is_close_rounding(v, scale, n.value, txt, n.span):
                out.append(n.start)
                break
    return out


def _is_close_rounding(v: float, scale: float, cand: float, txt: str, span: str = "") -> bool:
    """A rounding that still identifies the estimate: to the integer or finer always
    (37.5 -> 38), coarser only within 1 % of the value (564,757 -> 565,000; not 32.1 -> 30,
    which is another row's bound — cchs-2022-pe.indirect.indirect.…json)."""
    if not is_rounding_of(v, scale, cand, txt):
        return False
    full = v * scale
    m = re.search(r"\d[\d,]*(?:\.\d+)?", span or "")
    printed_decimals = decimals_of(m.group(0)) if m else 0
    if abs(round(full) - cand) < 1e-9 or printed_decimals > 0:
        return True
    return full != 0 and abs(cand - full) / abs(full) <= 0.01


_ANAPHORA_RE = re.compile(r"\b(?:this|that|the|its)\s+(?:estimate|figure|value|total|number|count|rate|true\s+(?:population\s+)?(?:value|figure|total|number))\b|\btrue\s+(?:population\s+)?(?:value|figure|total|number)\b", re.I)
_CLAUSE_BREAK = re.compile(r";\s+|,\s+(?:and|but|while|whereas|with)\s+|\s+(?:while|whereas)\s+|\s*[()]\s*|\s+[—–]\s+")


def _sentence_around(text: str, pos: int, window: int, clause: bool = False) -> str:
    """The sentence (or, with `clause`, the clause — split at ';' and ', and' / 'while' /
    'whereas') containing `pos`, bounded by the window."""
    lo, hi = max(0, pos - window), min(len(text), pos + window)
    seg = text[lo:hi]
    rel = pos - lo
    breaker = _SENTENCE_BREAK
    starts = [m.end() for m in breaker.finditer(seg) if m.end() <= rel]
    ends = [m.start() for m in breaker.finditer(seg) if m.start() > rel]
    sent_lo, sent_hi = (starts[-1] if starts else 0), (ends[0] if ends else len(seg))
    if not clause:
        return seg[sent_lo:sent_hi]
    sent = seg[sent_lo:sent_hi]
    rel2 = rel - sent_lo
    cs = [m.end() for m in _CLAUSE_BREAK.finditer(sent) if m.end() <= rel2]
    ce = [m.start() for m in _CLAUSE_BREAK.finditer(sent) if m.start() > rel2]
    return sent[(cs[-1] if cs else 0):(ce[0] if ce else len(sent))]


def _same_sentence(text: str, a: int, b: int) -> bool:
    lo, hi = (a, b) if a <= b else (b, a)
    return not _SENTENCE_BREAK.search(text[lo:hi])


def bound_to_estimate(parsed: Parsed, cand: ParsedQualifier, prop, cfg: dict, mode: str,
                      est_positions: Optional[List[int]] = None, siblings=None) -> Tuple[str, Optional[str]]:
    """D10. Returns (status, how): status ∈ {"bound", "other_estimate", "unbound"}.

    bound           anchored on the estimate's value (a ±), or the estimate's value / row
                    label restated within `window_chars` in the same sentence or line, or —
                    in direct mode — the question names the estimate (explicit reference).
    other_estimate  the candidate is anchored on a number that is NOT this estimate (nor a
                    rounding of it) — another row's qualifier. Presented beside this
                    estimate's label it is a `binding_error`; otherwise it is simply not
                    this estimate's.
    unbound         nothing ties the candidate to this estimate.
    """
    text = parsed.normalised
    window = int(cfg["window_chars"])
    v, txt, scale = prop.estimate_value, prop.estimate_text, prop.estimate_scale
    if est_positions is None:
        est_positions = estimate_positions(parsed, prop)
    anchored_elsewhere = False
    anchored_elsewhere_by_anchor = False        # a ± physically attached to another number
    if cand.bound_estimate is not None and cand.value is not None and abs(cand.bound_estimate - cand.value) < 1e-9:
        cand = ParsedQualifier(**{**cand.__dict__, "bound_estimate": None})    # anchored on its own value: no anchor
    if cand.bound_estimate is not None:
        if within_published_rounding(v, txt, scale, cand.bound_estimate) or at_display_scale(v, txt, scale, cand.bound_estimate) \
                or is_rounding_of(v, scale, cand.bound_estimate, txt):
            return "bound", "anchored_on_estimate"
        anchored_elsewhere = anchored_elsewhere_by_anchor = True
    # the value a qualifier follows in its own sentence is the value it qualifies (the v1 ±
    # rule generalised): "The employment figure of 2,670,000 carries a standard error of
    # about 19,800" is the count's SE, not the employment rate's
    # (lfs-2026-07-alberta.indirect.indirect.…json)
    sent = _sentence_around(text, cand.start, window)
    sent_start = text.find(sent, max(0, cand.start - window))
    est_set = set(est_positions)
    preceding = [n for n in parsed.numbers
                 if sent_start <= n.start < cand.start and _subject_value(parsed, text, n, cand)]
    if preceding and not anchored_elsewhere:
        nearest = max(preceding, key=lambda n: n.start)
        if nearest.start in est_set:
            return "bound", "estimate_in_sentence"
        # another value sits between this estimate and the candidate: the candidate is its
        if not any(n.start in est_set for n in preceding if n.start > nearest.start):
            anchored_elsewhere = True
    # the row label / estimate label restated near the candidate
    specific, generic = label_token_classes(prop, cfg["label_stop_words"])
    # a label reference counts only inside the candidate's own clause (and within the
    # window): the next clause's row is the next clause's business ("the count of unemployed
    # people has a CV of 5.0%, and the labour force count has a CV of 2.5%")
    near = _sentence_around(text, cand.start, window, clause=True).lower()
    own = set(specific) | set(generic)
    others = [sib for sib in (siblings or ()) if sib.id != prop.id]
    # label competition: the clause names THIS row when more of this label's tokens appear
    # in it than of any sibling label's ("the unemployment rate's standard error" names the
    # unemployment-rate row over the unemployment count and the participation rate; a tie
    # — "the employment figure … standard error" between the employment count and the
    # employment rate — decides nothing, and the value the qualifier follows decides)
    sib_only = set()
    for sib in others:
        sib_only |= set(_label_tokens(sib, cfg["label_stop_words"])) - own
    own_score = sum(1 for t in own if _has_tok(t, near))
    wins, loses = True, False
    for sib in others:
        st = set(_label_tokens(sib, cfg["label_stop_words"]))
        s_score = sum(1 for t in st if _has_tok(t, near))
        if s_score > own_score:
            loses = True
        elif s_score == own_score and s_score > 0:
            # a tie: this row wins only with a token the sibling lacks, or — when its label
            # is a subset of the sibling's ("Fairfax" vs "Fairfax, Arlington and Alexandria
            # combined") — when the sibling's extra tokens are absent
            own_extra = [t for t in own - st if _has_tok(t, near)]
            sib_extra = [t for t in st - own if _has_tok(t, near)]
            if not (own_extra or (own <= st and not sib_extra)):
                wins = False
    names_sibling = loses
    if names_sibling:
        return ("other_estimate" if anchored_elsewhere else "unbound"), "names_sibling_row"
    if others:
        label_near = own_score > 0 and wins
    elif specific:
        label_near = any(_has_tok(t, near) for t in specific)
    else:
        hits = [t for t in generic if _has_tok(t, near)]
        need = min(int(cfg["label_min_tokens"]), len(generic)) or 1
        if not est_positions and cand.cls in (QualifierClass.RELIABILITY_FLAG, QualifierClass.SUPPRESSION):
            # a suppressed / withheld cell with no value to anchor on: one label token near
            # the candidate is the most a restatement can offer
            need = 1
        label_near = len(hits) >= need
    if label_near and anchored_elsewhere_by_anchor:
        # an explicit label in the candidate's own clause beats a ± anchor that sits outside
        # it ("… 64.3% was employed, … (for example, ±0.4 points on the unemployment rate)")
        anchor_in_clause = any(abs(n.value - cand.bound_estimate) < 1e-9 for n in parsed.numbers
                               if cand.start - len(near) - 2 <= n.start < cand.start)
        if not anchor_in_clause:
            return "bound", "label_reference"
    elif label_near:
        return "bound", "label_reference"
    if anchored_elsewhere:
        return "other_estimate", ("label_near" if label_near else None)
    for pos in est_positions:
        if abs(pos - cand.start) <= window and _same_sentence(text, pos, cand.start):
            return "bound", "estimate_in_sentence"
    # anaphora: "for this estimate", "the true population value", "the figure" in the clause,
    # with the estimate's most recent restatement within the anaphora window and no sibling
    # row named in between (ons-ci-education.indirect.indirect.…json)
    if _ANAPHORA_RE.search(near):
        aw = int(cfg.get("anaphora_window_chars", window))
        prior = [pos for pos in est_positions if 0 <= cand.start - pos <= aw]
        if prior:
            between = text[max(prior):cand.start].lower()
            if not any(_has_tok(t, between) for t in sib_only):
                return "bound", "anaphora"
    if mode == "direct":
        # the question names the estimate: every candidate in the answer refers to it unless
        # anchored on another number (handled above)
        return "bound", "direct_question"
    # the adjacent-sentence fallback ("Colorado had 564,757 … . The margin of error is
    # 10,127.") applies only when the candidate's own sentence carries no other estimate-like
    # number: a sentence with its own subject value ("About 36% of PEI adults … between 30%
    # and 43%", cchs-2022-pe.indirect.indirect.…json) is about that value
    sent = _sentence_around(text, cand.start, window)
    sent_start = text.find(sent, max(0, cand.start - window))
    own_numbers = [n for n in parsed.numbers
                   if sent_start <= n.start < sent_start + len(sent)
                   and not (cand.start <= n.start < cand.start + len(cand.span))
                   and _subject_value(parsed, text, n, cand)]
    if not own_numbers:
        # … and the nearest preceding value in the window is this estimate (not another
        # sentence's subject: "About 36% of PEI adults … . Because this comes from a sample …
        # between 30% and 43%" is about the 36 %, cchs-2022-pe.indirect.indirect.…json)
        before = [n for n in parsed.numbers if cand.start - window <= n.start < cand.start
                  and _subject_value(parsed, text, n, cand)]
        if before:
            nearest = max(before, key=lambda n: n.start)
            return ("bound", "estimate_in_window") if nearest.start in est_set else ("unbound", "preceded_by_another_value")
        for pos in est_positions:
            if abs(pos - cand.start) <= window:
                return "bound", "estimate_in_window"
    return "unbound", None


_OPERATOR_NEAR = re.compile(r"[×÷*/=≈]")


def _subject_value(parsed: Parsed, text: str, n: ParsedNumber, cand: ParsedQualifier) -> bool:
    """A number that can be the SUBJECT a qualifier follows: estimate-like, not a year, level,
    fraction or formula term, not a rate denominator ("per 1,000"), and not the candidate's
    own value restated ("= 0.087, or 8.7% … coefficient of variation of 8.7%")."""
    if n.is_year or n.is_fraction or _LEVEL_RE.match(text[n.start:]) or not _estimate_like(n):
        return False
    if _OPERATOR_NEAR.search(text[max(0, n.start - 3):n.start]) or _OPERATOR_NEAR.search(text[n.start + len(n.span): n.start + len(n.span) + 3]):
        return False
    if re.search(r"\bper\s*$", text[max(0, n.start - 5):n.start], re.I):
        return False
    own = [cand.value, cand.lower, cand.upper]
    if any(v is not None and abs(n.value - v) < 1e-9 for v in own):
        return False
    # a value that is itself a qualifier (a ± amount, an SE, another interval's bound) is not
    # a subject: "£2,322 million, give or take about £201 million" has one subject
    for q in parsed.qualifiers:
        if q.cls is QualifierClass.VINTAGE:
            continue
        if any(v is not None and abs(n.value - v) < 1e-9 for v in (q.value, q.lower, q.upper)):
            return False
    return True


def _estimate_like(n: ParsedNumber) -> bool:
    """A number that could be an estimate: carries a unit, currency, scale word, a comma or
    a decimal, or four or more digits (the v1 `_preceding_number` test)."""
    raw = n.span
    return bool(n.unit or n.currency or "," in raw or "." in raw or len(re.sub(r"\D", "", raw)) >= 4
                or re.search(r"(?:thousand|million|billion|trillion|%|percent)", raw, re.I))


def bind_candidates(parsed: Parsed, prop, cfg: dict, mode: str, siblings=None) -> Tuple[Parsed, dict]:
    """A copy of the parse whose qualifiers are only the candidates bound to this estimate;
    the rest is reported (unbound / other-estimate spans) so the verdict can say why.
    `siblings`: the other propositions on the same passage (their labels name the rows a
    sentence must NOT be about)."""
    est_pos = estimate_positions(parsed, prop)
    keep, report = [], {"unbound": [], "other_estimate": [], "binding": {}}
    for c in parsed.qualifiers:
        if c.cls in (QualifierClass.VINTAGE, QualifierClass.DP_NOISE):
            # a date, and a disclosure-avoidance parameter (a property of the RELEASE, not
            # of one cell: the DAS handbook's global rho / epsilon / delta), bind to the whole
            # restatement (v0 rule for dates, unchanged; DD-035 for DP)
            keep.append(c)
            continue
        status, how = bound_to_estimate(parsed, c, prop, cfg, mode, est_pos, siblings)
        if status == "bound":
            keep.append(c)
            report["binding"][c.span] = how
        elif status == "other_estimate":
            report["other_estimate"].append({"span": c.span, "anchored_on": c.bound_estimate,
                                             "beside_this_label": how == "label_near", "class": c.cls.value})
        else:
            report["unbound"].append({"span": c.span, "class": c.cls.value})
    bound = Parsed(text=parsed.text, normalised=parsed.normalised, numbers=list(parsed.numbers), qualifiers=keep,
                   hedges=list(parsed.hedges), cues=list(parsed.cues), levels=list(parsed.levels),
                   vague_time=list(parsed.vague_time), dp_verbal=list(parsed.dp_verbal))
    return bound, report


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
    QualifierClass.RELIABILITY_FLAG: ("reliab", "caution", "precis", "caveat", "flag", "warning", "category", "significan"),
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
    """No BOUND candidate of the class.

    Precedence (v0 pre-registered, v2 D10 inserted as (0)): (0) candidates of the class exist
    but none is bound to this estimate -> L1 omission (the response carries the class for
    other estimates; this estimate's is missing); (1) the class's uncertainty vocabulary is
    present but nothing was classified anywhere -> `unparseable`; (2) a verbal band on the
    estimate with no such vocabulary -> L2 form_shift; (3) otherwise L1 (omission;
    decontextualization for VINTAGE). `estimate_restated` is recorded so Du 2026's
    certainty assertion (estimate restated as definite) is recoverable."""
    restated = est is not EstimateStatus.ABSENT
    obs = dict(obs, estimate_restated=restated)
    unbound = obs.get("unbound_candidates") or []
    if unbound:
        return _verdict(cls, Level.OMITTED, "omission",
                        f"no {cls.value} bound to this estimate ({len(unbound)} candidate(s) belong to other estimates)", obs)
    cues = _cues_for(parsed, cls, prop)
    if cues and not restated and cls in _NUMERIC_CLASSES:
        # v2 precedence (compressed dev responses: acs-ch7-colorado.indirect.indirect.tight.…json
        # "A margin of error shows how precise a Census survey estimate is …"): the class's
        # vocabulary about the CONCEPT, with neither this estimate nor any candidate of the class
        # in the response, is not a claim about this estimate that the rules failed to read — it
        # is the estimate and its qualifier both dropped: L1 omission, cue words recorded.
        # Numeric classes only: a flag or suppression statement has no value to restate, so its
        # wording alone is still the D5 case (syn-suppressed-001 cases). A rho asked where its
        # epsilon equivalent was given stays unparseable too (a convertible form the rules
        # cannot verify without delta).
        return _verdict(cls, Level.OMITTED, "omission",
                        f"neither the estimate nor its {cls.value} is restated (class vocabulary present: {', '.join(cues)})",
                        dict(obs, cues=cues))
    if cues:
        return _verdict(cls, None, None,
                        f"uncertainty vocabulary present ({', '.join(cues)}) but no {cls.value} could be classified",
                        dict(obs, cues=cues))
    if cls in _NUMERIC_CLASSES or cls is QualifierClass.DP_NOISE:
        if parsed.hedges and restated:
            return _verdict(cls, Level.DEGRADED_VERBAL, "form_shift",
                            f"no numeric {cls.value}; verbal band present: {', '.join(parsed.hedges)}",
                            dict(obs, hedges=parsed.hedges))
    if not restated:
        return _verdict(cls, Level.OMITTED, "omission", f"neither the estimate nor its {cls.value} is restated", obs)
    if cls is QualifierClass.VINTAGE:
        return _verdict(cls, Level.OMITTED, "decontextualization",
                        "estimate restated without its as-of date / period", obs)
    return _verdict(cls, Level.OMITTED, "omission",
                    f"estimate restated as definite; {cls.value} absent (certainty assertion)", obs)


def _pick(cands: List[ParsedQualifier], prop, matcher) -> ParsedQualifier:
    """Prefer a candidate bound to the source estimate whose value matches, then any whose
    value matches, then one bound to the estimate, then the first."""
    def _bound(c):
        return c.bound_estimate is not None and within_published_rounding(
            prop.estimate_value, prop.estimate_text, prop.estimate_scale, c.bound_estimate)
    for c in cands:
        if _bound(c) and matcher(c):
            return c
    for c in cands:
        if matcher(c):
            return c
    for c in cands:
        if _bound(c):
            return c
    return cands[0]


def _binding_error(cand: ParsedQualifier, prop) -> bool:
    """The ± was attached to a number that is neither the source estimate nor a rounding of it."""
    if cand.bound_estimate is None:
        return False
    v, t, s = prop.estimate_value, prop.estimate_text, prop.estimate_scale
    return not (within_published_rounding(v, t, s, cand.bound_estimate)
                or at_display_scale(v, t, s, cand.bound_estimate)
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
    level_note = {}
    if not exact and at_display_scale(v, txt, scale, cand.value):
        transformed = True
        level_note["scale_word_omitted"] = True
    if not exact and cls is QualifierClass.CV and cand.unit in ("fraction", None) and cand.value is not None:
        transformed = transformed or within_published_rounding(v, txt, scale, cand.value * 100)      # 0.087 -> 8.7 %
    if not exact and cls is QualifierClass.CV and unit == "fraction" and cand.unit == "percent":
        transformed = transformed or within_published_rounding(v, txt, scale, cand.value / 100)
    if not exact and unit in ("percent", "percent_points") and cand.unit in ("fraction", None) and cand.value is not None and cand.value < 1:
        transformed = transformed or within_published_rounding(v, txt, scale, cand.value * 100)      # 0.001 -> 0.1 %
    if exact or transformed:
        level = Level.PRESERVED_EXACT if exact else Level.PRESERVED_TRANSFORMED
        if cls is QualifierClass.MOE and q.level is not None:
            if cand.level is None:
                level = Level.PRESERVED_TRANSFORMED
                level_note["level_omitted"] = True
            elif abs(cand.level - q.level) > 1e-9:
                return _verdict(cls, Level.CORRUPTED, "level_change",
                                f"MOE value right but confidence level {cand.level} ≠ {q.level}",
                                dict(obs, level_restated=cand.level, level_source=q.level))
        if cand.hedged and level is Level.PRESERVED_EXACT:
            level_note["hedge_before_value"] = True
        return _verdict(cls, level, None, f"{cls.value} {cand.span!r} matches source {txt}",
                        dict(obs, matched_span=cand.span, restated_value=cand.value, **level_note))
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
                             restated_value=(cand.upper - cand.lower) / 2,
                             **({"level_omitted": True} if q.level is not None and cand.level is None else {})))
    return _verdict(QualifierClass.MOE, Level.CORRUPTED, "quantity_hallucination",
                    f"MOE restated as bounds {cand.span!r} that do not equal est ± {q.text}",
                    dict(obs, restated_bounds=[cand.lower, cand.upper], source_value=moe,
                         restated_value=(cand.upper - cand.lower) / 2,
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
        if src_form == "bounds":
            ok = (within_published_rounding(lo / scale, lo_txt, 1.0, cand.lower / scale)
                  and within_published_rounding(hi / scale, hi_txt, 1.0, cand.upper / scale))
        else:
            # bounds against a ±-form source (v2; the v1 RESULT's "pm-source / bounds-candidate
            # tolerance is not symmetric" miss — ons-ci-education.indirect.…json quotes the
            # passage's own printed bounds 41,616 / 43,682 for 42,649 ± 1,032.5): est ± half
            # must land on the restated bounds within half a unit of THEIR printed precision.
            nums = re.findall(r"\d[\d,]*(?:\.\d+)?", cand.span)
            d_lo = decimals_of(nums[0]) if nums else 0
            d_hi = decimals_of(nums[1]) if len(nums) > 1 else d_lo
            ok = (_close(est / scale - half / scale, cand.lower / scale, d_lo)
                  and _close(est / scale + half / scale, cand.upper / scale, d_hi))
        transformation = None if src_form == "bounds" else "pm_to_bounds"
        matched_note = f"bounds {cand.span!r}"
        restated = (cand.upper - cand.lower) / 2
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
        restated = cand.value if cand.value is not None else 0.0
    if not ok:
        cand_half = restated
        return _verdict(QualifierClass.CI, Level.CORRUPTED, "quantity_hallucination",
                        f"interval restated as {cand.span!r}; source half-width {half_txt}",
                        dict(obs, direction=_direction(half, cand_half), restated=cand.span, restated_value=cand_half,
                             source_value=half))
    if cand.level is not None and abs(cand.level - q.level) > 1e-9:
        return _verdict(QualifierClass.CI, Level.CORRUPTED, "level_change",
                        f"interval right but level {cand.level} ≠ {q.level}",
                        dict(obs, level_restated=cand.level, level_source=q.level))
    notes = {"restated_value": restated, "matched_span": cand.span}
    level = Level.PRESERVED_EXACT
    if cand.level is None:
        level, notes = Level.PRESERVED_TRANSFORMED, dict(notes, level_omitted=True)
    if transformation:
        level, notes = Level.PRESERVED_TRANSFORMED, dict(notes, transformation=transformation)
    return _verdict(QualifierClass.CI, level, None, f"CI {matched_note} matches source", dict(obs, **notes))


def _score_flag(q, parsed: Parsed, est: EstimateStatus, obs: dict, prop=None) -> QualifierVerdict:
    cands = parsed.of_class(QualifierClass.RELIABILITY_FLAG)
    src_pol, src_text = q.fields["polarity"], (q.text or "").lower()
    legend = (q.fields.get("legend") or "").lower()
    symbol = q.fields.get("symbol")
    if not cands:
        return _absent(parsed, QualifierClass.RELIABILITY_FLAG, est, obs, prop)
    same = [c for c in cands if c.polarity == src_pol]
    if same:
        # exact: the symbol itself, or the legend's outcome words, restated; else transformed
        def _exact(c):
            ctext = (c.text or "").lower()
            if symbol and c.parameter == symbol:
                return True
            if legend and (" ".join(legend.split()) in ctext or _legend_words_in(legend, ctext)):
                return True
            return bool(src_text) and " ".join(src_text.split()) in ctext and not symbol
        c = next((c for c in same if _exact(c)), same[0])
        exact = _exact(c)
        return _verdict(QualifierClass.RELIABILITY_FLAG,
                        Level.PRESERVED_EXACT if exact else Level.PRESERVED_TRANSFORMED, None,
                        f"reliability flag restated as {c.text!r} (source {src_text!r}{' = ' + legend if legend else ''})",
                        dict(obs, matched_span=c.span, polarity=c.polarity, restated_text=c.text))
    c = cands[0]
    failure = "suppression_override" if src_pol == "unreliable" else "fabricated_qualifier"
    return _verdict(QualifierClass.RELIABILITY_FLAG, Level.CORRUPTED, failure,
                    f"reliability polarity inverted: {c.text!r} vs source {src_text!r}",
                    dict(obs, restated=c.text, polarity_source=src_pol, polarity_restated=c.polarity))


def _legend_words_in(legend: str, text: str) -> bool:
    """The legend's outcome words ('not significant', 'use with caution') in the candidate."""
    core = re.sub(r"\(.*?\)", "", legend).strip().rstrip(".").strip()
    core = re.sub(r"^(change|difference)\s+", "", core).strip()
    return bool(core) and core in text


def _score_suppression(q, parsed: Parsed, est: EstimateStatus, obs: dict, prop=None) -> QualifierVerdict:
    cands = parsed.of_class(QualifierClass.SUPPRESSION)
    if cands:
        return _verdict(QualifierClass.SUPPRESSION, Level.PRESERVED_EXACT, None,
                        f"suppression restated: {cands[0].text!r}", dict(obs, matched_span=cands[0].span))
    if est in (EstimateStatus.EXACT, EstimateStatus.ROUNDED, EstimateStatus.WRONG):
        return _verdict(QualifierClass.SUPPRESSION, Level.CORRUPTED, "suppression_override",
                        "an estimate the producer would not publish is restated as a usable number", obs)
    return _absent(parsed, QualifierClass.SUPPRESSION, est, obs, prop)


def _score_dp(q, parsed: Parsed, est: EstimateStatus, prop, obs: dict) -> QualifierVerdict:
    param = q.fields["parameter"]
    all_dp = parsed.of_class(QualifierClass.DP_NOISE)
    cands = [c for c in all_dp if c.parameter == param
             or (param in ("rho", "epsilon") and c.parameter == "plb")]
    if not cands:
        convertible = param in ("rho", "epsilon") and any(c.parameter in ("rho", "epsilon", "plb") for c in all_dp)
        if all_dp and not convertible:
            # other parameters are stated, this one is not (das-plb-units.indirect.indirect.short
            # .…json states rho / epsilon / delta and drops the allocation share): an omission
            return _verdict(QualifierClass.DP_NOISE, Level.OMITTED, "omission",
                            f"DP {param} not restated; other parameters stated ({', '.join(sorted({c.parameter or '' for c in all_dp}))})",
                            dict(obs, other_parameters=sorted({c.parameter or "" for c in all_dp}), estimate_restated=est is not EstimateStatus.ABSENT))
        return _absent(parsed, QualifierClass.DP_NOISE, est, obs, prop)
    c = cands[0]
    if param == "bound" and q.unit and c.unit and not _unit_compatible(q.unit, c.unit):
        return _verdict(QualifierClass.DP_NOISE, Level.CORRUPTED, "quantity_hallucination",
                        f"DP bound unit {c.unit} vs source {q.unit}", dict(obs, unit_mismatch=[q.unit, c.unit]))
    if within_published_rounding(q.value, q.text or str(q.value), q.scale, c.value):
        level = Level.PRESERVED_EXACT if c.parameter == param else Level.PRESERVED_TRANSFORMED
        return _verdict(QualifierClass.DP_NOISE, level, None,
                        f"DP {param} restated as {c.span!r}", dict(obs, matched_span=c.span, parameter=param, restated_value=c.value))
    return _verdict(QualifierClass.DP_NOISE, Level.CORRUPTED, "quantity_hallucination",
                    f"DP {param} restated as {c.span!r}; source {q.text}",
                    dict(obs, direction=_direction(q.value * q.scale, c.value or 0.0), restated_value=c.value,
                         source_value=q.value * q.scale))


def _score_vintage(q, parsed: Parsed, est: EstimateStatus, obs: dict, prop=None) -> QualifierVerdict:
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
        return _absent(parsed, QualifierClass.VINTAGE, est, obs, prop)
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
            if re.fullmatch(r"(?:19|20)\d{2}-\d{2}", as_of) and not re.search(r"\d{4}-\d{2}|" + _MONTHS_RE, c.text or ""):
                return _verdict(QualifierClass.VINTAGE, Level.PRESERVED_TRANSFORMED, None,
                                f"year {c.text!r} kept; reference month {as_of!r} coarsened",
                                dict(obs, matched_span=c.span, coarsened=True))
            return _verdict(QualifierClass.VINTAGE, Level.PRESERVED_EXACT, None,
                            f"as-of {c.text!r} matches source {as_of!r}", dict(obs, matched_span=c.span))
    # a single year inside a multi-year source period is the handbook's named error
    c = numeric[0]
    return _verdict(QualifierClass.VINTAGE, Level.CORRUPTED, "quantity_hallucination",
                    f"vintage restated as {c.text!r}; source {as_of!r}",
                    dict(obs, restated=c.text, source=as_of))


_MONTHS_RE = r"January|February|March|April|May|June|July|August|September|October|November|December"
_SCALE_WORDS = {"trillion": 1e12, "billion": 1e9, "million": 1e6, "thousand": 1e3}

_NUMERIC_UNIT_OK = {
    QualifierClass.MOE: ("percent", "percent_points", "count", "currency", "fraction", None),
    QualifierClass.CI: ("percent", "percent_points", "count", "currency", None),
    QualifierClass.SE: ("percent", "percent_points", "count", "currency", "fraction", None),
    QualifierClass.CV: ("percent", "fraction", None),
}


def _direct_leading_number(parsed: Parsed, prop, q) -> Optional[ParsedQualifier]:
    """Direct-mode rule (v1, task 2026-09-03 step 4.2; motivating evidence
    g1-ons-cv-002.direct.CV.…json answered "8.7%" bare): the question names the class, so the
    first numeric token whose unit is compatible with the class — and which is not the
    estimate itself — is the qualifier even with no class keyword. Indirect mode never uses
    this; a bare number there is still not a qualifier."""
    ok_units = _NUMERIC_UNIT_OK.get(q.cls)
    if ok_units is None:
        return None
    from ._g1_parse import _LEVEL_RE
    for n in parsed.numbers:
        if n.is_year:
            continue
        if _LEVEL_RE.match(parsed.normalised[n.start:]):
            continue                                   # "95% confidence interval": a level, not a value
        if (within_published_rounding(prop.estimate_value, prop.estimate_text, prop.estimate_scale, n.value)
                or at_display_scale(prop.estimate_value, prop.estimate_text, prop.estimate_scale, n.value)) \
                and _unit_compatible(prop.estimate.get("unit"), n.unit):
            continue                                   # the estimate, not its qualifier
        if n.unit not in ok_units:
            continue
        unit = n.unit
        if q.cls is QualifierClass.CV and unit is None and n.value < 1:
            unit = "fraction"
        if q.cls is QualifierClass.MOE and unit == "percent" and prop.estimate.get("unit") == "percent":
            unit = "percent_points"
        return ParsedQualifier(q.cls, "direct_leading_number", n.span, n.start, value=n.value, unit=unit, form="pm")
    return None


def _z_for(q_or_prop, level: Optional[float], z_by_level: dict) -> Optional[float]:
    """z for a level: the producer's own factor when the qualifier carries `z`, else the
    config table (harness.toml [g1.z_by_level]); None when neither knows the level."""
    if level is None:
        return None
    return z_by_level.get(round(float(level), 4))


def _se_from_other_classes(parsed: Parsed, prop, q, z_by_level: dict) -> Optional[Tuple[ParsedQualifier, str, float]]:
    """SE restated as an MOE or as CI bounds (v1 step 4.3): SE = MOE / z or (upper − lower) / 2z,
    z from the proposition's own level (its MOE/CI qualifier's `level`, or the qualifier's `z`
    when the producer states the factor). Returns (candidate, transformation, z) or None."""
    level = q.fields.get("level")
    z = q.fields.get("z")
    if level is None or z is None:
        for other in prop.qualifiers:
            if other.cls in (QualifierClass.MOE, QualifierClass.CI):
                level = level if level is not None else other.fields.get("level")
                z = z if z is not None else other.fields.get("z")
    if z is None:
        z = _z_for(q, level, z_by_level)
    if not z:
        return None
    pm = [c for c in parsed.of_class(QualifierClass.MOE) + [c for c in parsed.of_class(QualifierClass.CI) if c.form == "pm"]
          if c.value is not None]
    if pm:
        # Prefer the ± whose derived value matches, then the one bound to this estimate, then
        # the first — a passage with several estimates has several ±s (acs-ch7-significance:
        # Florida's ±0.2 is not Arizona's SE source; acs-ch8-loudoun-83: ±931 vs ±973).
        def _matches(c):
            return within_published_rounding(q.value, q.text or str(q.value), q.scale, c.value / z)
        def _bound(c):
            return c.bound_estimate is not None and within_published_rounding(
                prop.estimate_value, prop.estimate_text, prop.estimate_scale, c.bound_estimate)
        c = next((c for c in pm if _matches(c)), None) or next((c for c in pm if _bound(c)), None) or pm[0]
        derived = ParsedQualifier(QualifierClass.SE, "se_from_moe", c.span, c.start, value=c.value / z,
                                  unit=c.unit, form="phrase", bound_estimate=c.bound_estimate)
        return derived, "moe_to_se", z
    est = prop.estimate_value * prop.estimate_scale
    for c in parsed.of_class(QualifierClass.CI):
        if c.form == "bounds" and c.lower is not None:
            # Only a SYMMETRIC interval about this estimate implies an SE (a Korn–Graubard or
            # Clopper–Pearson interval is asymmetric: nchs175-appendix-bp.indirect.…json
            # "0.3% – 6.4%" around 2.0 % does not encode the 1.17-point SE).
            d = decimals_of(prop.estimate_text)
            for e in (est, prop.estimate_value):
                if _close(e - c.lower, c.upper - e, d) and _close((c.lower + c.upper) / 2, e, d):
                    derived = ParsedQualifier(QualifierClass.SE, "se_from_bounds", c.span, c.start,
                                              value=(c.upper - c.lower) / (2 * z), unit=c.unit, form="phrase")
                    return derived, "bounds_to_se", z
    return None


def score_qualifier(parsed: Parsed, prop, q, est: EstimateStatus, mode: str = "indirect",
                    z_by_level: Optional[dict] = None, binding_report: Optional[dict] = None) -> QualifierVerdict:
    """One published FORM against the (bound) parse. `binding_report` (D10) tells `_absent`
    whether candidates of the class existed for other estimates."""
    cls = q.cls
    z_by_level = z_by_level or {}
    obs = {"qualifier_source": q.fields, "estimate_status": est.value, "rules_fired": sorted({c.rule for c in parsed.qualifiers})}
    if binding_report:
        fam_classes = FAMILIES[FAMILY_OF[cls.value]]
        unbound = [u for u in binding_report.get("unbound", []) + binding_report.get("other_estimate", [])
                   if u["class"] in fam_classes]
        if unbound:
            obs["unbound_candidates"] = unbound
        beside = [u for u in binding_report.get("other_estimate", []) if u.get("beside_this_label") and u["class"] in fam_classes]
        if mode == "indirect" and beside and not any(c.cls.value in fam_classes for c in parsed.qualifiers):
            # another estimate's qualifier presented beside THIS estimate's label (D10)
            return _verdict(cls, Level.CORRUPTED, "binding_error",
                            f"{cls.value} {beside[0]['span']!r} anchored on {beside[0]['anchored_on']} is presented as this estimate's",
                            dict(obs, bound_to=beside[0]["anchored_on"]))
    if cls is QualifierClass.RELIABILITY_FLAG:
        return _score_flag(q, parsed, est, obs, prop)
    if cls is QualifierClass.SUPPRESSION:
        return _score_suppression(q, parsed, est, obs, prop)
    if cls is QualifierClass.DP_NOISE:
        return _score_dp(q, parsed, est, prop, obs)
    if cls is QualifierClass.VINTAGE:
        return _score_vintage(q, parsed, est, obs, prop)
    if cls is QualifierClass.MOE:
        pm = parsed.of_class(QualifierClass.MOE)
        bounds = [c for c in parsed.of_class(QualifierClass.CI) if c.form == "bounds"]
        ci_pm = [c for c in parsed.of_class(QualifierClass.CI) if c.form == "pm"]
        if pm or ci_pm:
            cands = pm or ci_pm
            if mode == "direct":
                # the bare answer competes with any keyword phrase ("2628 (dollars). That's the
                # … margin of error on the … estimate of $102,772" — g1v2-acs-co-boulder.direct
                # .MOE.…json, where the phrase swallowed the estimate)
                lead = _direct_leading_number(parsed, prop, q)
                if lead is not None:
                    cands = [lead] + cands
                    obs = dict(obs, direct_leading_number=lead.span)
            cand = _pick(cands, prop, lambda c: within_published_rounding(q.value, q.text, q.scale, c.value))
            return _score_pm(cls, q, cand, prop, obs)
        if bounds:
            v = _score_moe_as_bounds(q, bounds[0], prop, obs)
            if v is not None:
                return v
        if mode == "direct":
            lead = _direct_leading_number(parsed, prop, q)
            if lead is not None:
                return _score_pm(cls, q, lead, prop, dict(obs, direct_leading_number=lead.span))
        return _absent(parsed, cls, est, obs, prop)
    if cls is QualifierClass.CI:
        # every interval-form candidate competes — a ± phrase beside rounded bounds is
        # ranked, not pre-empted (v2; the v1 RESULT's "exact 'MOE of 10,127' outranked by
        # rounded bounds" miss, acs-ch7-colorado.indirect.indirect.…json)
        cands = parsed.of_class(QualifierClass.CI) + parsed.of_class(QualifierClass.MOE)
        if not cands and mode == "direct":
            lead = _direct_leading_number(parsed, prop, q)
            if lead is not None:
                return _score_ci(q, lead, prop, dict(obs, direct_leading_number=lead.span))
        if not cands:
            return _absent(parsed, cls, est, obs, prop)
        # A response may state several intervals (LFS: 68 % and 95 %; ONS: bounds and a ±).
        # Prefer the candidate that scores best against THIS qualifier — its level, then
        # its bounds/half-width — rather than the first one parsed
        # (lfs-ci-example.indirect.…json, ons-ci-education.indirect.…json).
        def _rank(c):
            v = _score_ci(q, c, prop, obs)
            level_match = c.level is not None and abs(c.level - q.level) < 1e-9
            return (v.level if v.level is not None else -1, level_match, c.form == "bounds")
        best = max(cands, key=_rank)
        return _score_ci(q, best, prop, obs)
    cands = parsed.of_class(cls)
    if mode == "direct":
        # Direct mode (v1 step 4.2): the leading number is a candidate beside any keyword
        # candidates; `_pick` prefers the one whose value matches, so a bare correct answer
        # followed by a derivation with other numbers scores on the answer
        # (g1-lfs-cv-001.direct.CV.…json "5.0%. … 2.5%, is the CV on the labour force count").
        lead = _direct_leading_number(parsed, prop, q)
        if lead is not None:
            cands = [lead] + cands
            obs = dict(obs, direct_leading_number=lead.span)
    if not cands and cls is QualifierClass.SE:
        # SE restated in ± form with the SE's own value ("£2,322 million, give or take about
        # £201 million" — ons-cv-examples.indirect.indirect.…json): the number is the SE, the
        # form is a ±, so L3 (numeric, correct, transformed); a wrong value still scores L0.
        pm = [c for c in parsed.of_class(QualifierClass.MOE) + parsed.of_class(QualifierClass.CI)
              if c.form == "pm" and c.value is not None]
        same = [c for c in pm if within_published_rounding(q.value, q.text, q.scale, c.value)
                or at_display_scale(q.value, q.text, q.scale, c.value)]
        if same:
            c = same[0]
            v = _score_pm(cls, q, c, prop, dict(obs, transformation="se_as_pm"))
            if v.level == Level.PRESERVED_EXACT:
                v = _verdict(cls, Level.PRESERVED_TRANSFORMED, None, v.evidence + " (restated as ±)", v.observations)
            return v
        derived = _se_from_other_classes(parsed, prop, q, z_by_level)
        if derived is not None:
            cand, transformation, z = derived
            v = _score_pm(cls, q, cand, prop, dict(obs, transformation=transformation, z=z))
            if v.level == Level.CORRUPTED and transformation == "bounds_to_se" and cand.value is not None:
                # bounds are printed rounded (ONS 41,616 / 43,682 for 42,649 ± 1,032.5): an SE
                # derived from them carries half a unit of the bounds' precision divided by z
                nums = re.findall(r"\d[\d,]*(?:\.\d+)?", cand.span)
                d_b = min((decimals_of(n) for n in nums), default=0)
                span_low = cand.span.lower()
                bound_scale = next((v for w, v in _SCALE_WORDS.items() if w in span_low), 1.0)
                # half a unit of the bounds' printed precision (at their scale word), through z,
                # plus half a unit of the source SE's own precision — all in full units
                tol = 0.5 * 10 ** (-d_b) * bound_scale / z + 0.5 * 10 ** (-decimals_of(q.text or str(q.value))) * q.scale
                if abs(cand.value - q.value * q.scale) <= tol + 1e-9:
                    v = _verdict(cls, Level.PRESERVED_TRANSFORMED, None,
                                 f"{cls.value} {q.text} derived from bounds {cand.span!r} within the bounds' rounding (z={z})",
                                 dict(obs, transformation=transformation, z=z, matched_span=cand.span, restated_value=cand.value,
                                      bounds_rounding_slack=tol))
                    return v
            if v.level == Level.PRESERVED_EXACT:
                v = _verdict(cls, Level.PRESERVED_TRANSFORMED, None, v.evidence + f" (derived: {transformation}, z={z})",
                             v.observations)
            return v
    if not cands:
        return _absent(parsed, cls, est, obs, prop)
    cand = _pick(cands, prop, lambda c: within_published_rounding(q.value, q.text, q.scale, c.value))
    return _score_pm(cls, q, cand, prop, obs)


# ---------------------------------------------------------------- families (D9)
@dataclass(frozen=True)
class FamilyVerdict:
    family: str
    qualifier_class: str          # the form that achieved the family level (or the first published form)
    outcome: str
    score: Optional[Score]
    level: Optional[int]
    failure_class: Optional[str]
    evidence: str
    observations: dict            # forms: {class: verdict dict}, cross_family_derivation, covariates


def _cross_family(parsed: Parsed, prop, family: str, quals, est: EstimateStatus, z_by_level: dict) -> Optional[Tuple[QualifierVerdict, str]]:
    """D9 cross-family derivation: the target family is stated in another family's form.
    `relative` from a bound interval form (CV = SE / estimate; SE from MOE / z or bounds) and
    `interval` from a bound CV (SE = CV × estimate). Only when the estimate is restated
    correctly (exact); scored L3 with the derivation recorded."""
    if est is not EstimateStatus.EXACT:
        return None
    est_full = prop.estimate_value * prop.estimate_scale
    if family == "relative":
        se_val = None
        se_c = parsed.of_class(QualifierClass.SE)
        if se_c and se_c[0].value is not None:
            se_val, src_span = se_c[0].value, se_c[0].span
        else:
            q0 = quals[0]
            fake = type("Q", (), {"fields": dict(q0.fields), "cls": QualifierClass.SE, "value": 0.0, "text": "0", "scale": 1.0, "unit": None})()
            d = _se_from_other_classes(parsed, prop, fake, z_by_level)
            if d is None:
                return None
            se_val, src_span = d[0].value, d[0].span
        if not se_val or not est_full:
            return None
        cv_pct = se_val / est_full * 100
        for q in quals:
            unit = q.unit
            cand_val = cv_pct if unit != "fraction" else cv_pct / 100
            if within_published_rounding(q.value, q.text or str(q.value), q.scale, cand_val):
                v = _verdict(QualifierClass.CV, Level.PRESERVED_TRANSFORMED, None,
                             f"CV {q.text} derived from the restated interval form {src_span!r} (SE / estimate)",
                             {"qualifier_source": q.fields, "estimate_status": est.value, "derived_from": src_span,
                              "restated_value": cand_val})
                return v, "interval_to_relative"
        return None
    if family == "interval":
        cv_c = [c for c in parsed.of_class(QualifierClass.CV) if c.value is not None]
        if not cv_c or not est_full:
            return None
        c = cv_c[0]
        cv = c.value / 100 if (c.unit == "percent" or (c.unit is None and c.value >= 1)) else c.value
        se_val = cv * est_full
        for q in quals:
            if q.cls is QualifierClass.SE and within_published_rounding(q.value, q.text or str(q.value), q.scale, se_val):
                v = _verdict(QualifierClass.SE, Level.PRESERVED_TRANSFORMED, None,
                             f"SE {q.text} derived from the restated CV {c.span!r} (CV × estimate)",
                             {"qualifier_source": q.fields, "estimate_status": est.value, "derived_from": c.span,
                              "restated_value": se_val})
                return v, "relative_to_interval"
            lvl = q.fields.get("level")
            z = q.fields.get("z") or _z_for(q, lvl, z_by_level)
            if q.cls is QualifierClass.MOE and z and within_published_rounding(q.value, q.text or str(q.value), q.scale, se_val * z):
                v = _verdict(QualifierClass.MOE, Level.PRESERVED_TRANSFORMED, None,
                             f"MOE {q.text} derived from the restated CV {c.span!r} (CV × estimate × z)",
                             {"qualifier_source": q.fields, "estimate_status": est.value, "derived_from": c.span,
                              "restated_value": se_val * z, "z": z})
                return v, "relative_to_interval"
    return None


def score_family(parsed: Parsed, prop, family: str, est: EstimateStatus, mode: str, z_by_level: dict,
                 binding_cfg: dict, only_class: Optional[str] = None, siblings=None) -> FamilyVerdict:
    quals = [q for q in prop.qualifiers if FAMILY_OF[q.cls.value] == family and (only_class is None or q.cls.value == only_class)]
    if not quals:
        raise ValueError(f"{prop.id}: no {family} qualifier published")
    bound, report = bind_candidates(parsed, prop, binding_cfg, mode, siblings)
    forms: Dict[str, QualifierVerdict] = {}
    for q in quals:
        key = q.cls.value if q.cls.value not in forms else f"{q.cls.value}:{q.fields.get('parameter') or len(forms)}"
        forms[key] = score_qualifier(bound, prop, q, est, mode=mode, z_by_level=z_by_level, binding_report=report)
    cross = None
    if all(v.level is None or v.level < Level.PRESERVED_TRANSFORMED for v in forms.values()) and family in ("relative", "interval"):
        cross = _cross_family(bound, prop, family, quals, est, z_by_level)
    scored = {k: v for k, v in forms.items() if v.level is not None}
    unparseable = [k for k, v in forms.items() if v.level is None]
    best_key, best = (None, None)
    if scored:
        best_key = max(scored, key=lambda k: (scored[k].level, k == quals[0].cls.value))
        best = scored[best_key]
    obs = {"forms": {k: {"outcome": v.outcome, "level": v.level, "failure_class": v.failure_class, "evidence": v.evidence,
                         "observations": v.observations} for k, v in forms.items()},
           "n_forms": len(forms), "binding": report, "family": family}
    if cross is not None:
        v, kind = cross
        obs["cross_family_derivation"] = kind
        return FamilyVerdict(family, v.qualifier_class, v.outcome, v.score, v.level, v.failure_class,
                             f"[{family}] {v.evidence}", dict(obs, chosen_form=v.qualifier_class, chosen_observations=v.observations))
    if unparseable and (best is None or best.level < Level.PRESERVED_TRANSFORMED):
        # a form's vocabulary was present but unread: no loss can be claimed for the family
        k = unparseable[0]
        v = forms[k]
        return FamilyVerdict(family, quals[0].cls.value, UNPARSEABLE, None, None, None,
                             f"[{family}] {v.evidence}", dict(obs, chosen_form=k, chosen_observations=v.observations))
    assert best is not None
    return FamilyVerdict(family, best.qualifier_class, best.outcome, best.score, best.level, best.failure_class,
                         f"[{family}] {best.evidence}", dict(obs, chosen_form=best_key, chosen_observations=best.observations))


# ---------------------------------------------------------------- covariates (D11)
def _tokens(text: str) -> int:
    return len((text or "").split())


def covariates(fv: FamilyVerdict, prop, est: EstimateStatus, est_obs: dict, parsed: Parsed, elicited: Elicited,
               compression: str, passage_meta: Optional[dict]) -> dict:
    chosen = fv.observations.get("chosen_observations") or {}
    src = chosen.get("qualifier_source") or {}
    restated = chosen.get("restated_value")
    src_val = None
    if isinstance(src, dict):
        if src.get("value") is not None:
            src_val = float(src["value"]) * float(src.get("scale", 1))
        elif src.get("lower") is not None and src.get("upper") is not None:
            src_val = (float(src["upper"]) - float(src["lower"])) / 2 * float(src.get("scale", 1))
    rel_dev = None
    if isinstance(restated, (int, float)) and src_val:
        # compare at the same scale the scorer matched on
        r = float(restated)
        if src.get("scale", 1) != 1 and abs(r) < abs(src_val) / 10:
            r = r * float(src.get("scale", 1))
        rel_dev = round((r - src_val) / src_val, 6)
    direction = chosen.get("direction") or "none"
    est_span = (est_obs.get("estimate_matches") or [None])[0] or est_obs.get("estimate_rounded_to")
    spc = None
    if est_span and isinstance(chosen.get("matched_span"), str):
        m_est = re.search(r"\d[\d,]*(?:\.\d+)?", est_span)
        m_q = re.search(r"\d[\d,]*(?:\.\d+)?", chosen["matched_span"])
        if m_est and m_q:
            spc = decimals_of(m_est.group(0)) == decimals_of(m_q.group(0))
    p_tok, r_tok = _tokens(prop.context_passage), _tokens(elicited.response_text)
    return {
        "relative_deviation": rel_dev,
        "rounding_direction": direction if fv.level == Level.CORRUPTED or direction != "none" else "none",
        "summary_precision_consistent": spc,
        "compression_ratio": (round(p_tok / r_tok, 4) if r_tok else None),
        "passage_tokens": p_tok, "response_tokens": r_tok,
        "footnote_distance_chars": prop.footnote_distance_chars,
        "declared_leg_score": (passage_meta or {}).get("declared_leg_score"),
        "surface_type": prop.surface_type,
        "compression_level": compression if elicited.mode == "indirect" else None,
        "consumer_model_id": elicited.model_id,
        "estimate_restated": est is not EstimateStatus.ABSENT,
        "legend_on_surface": prop.legend_on_surface,
    }


# ---------------------------------------------------------------- the probe
class PreservationProbe(EvalProbe):
    probe_id = "g1_preservation"
    dimension = "G1"
    track = Track.CORE

    def __init__(self, prompts: PromptSet, evidence_root, timestamp: Optional[str] = None,
                 z_by_level: Optional[dict] = None, binding: Optional[dict] = None,
                 legacy_evidence_dirs: Tuple[Path, ...] = ()):
        self.prompts = prompts
        self.evidence_root = Path(evidence_root)
        self.timestamp = timestamp
        # Level -> z and the D10 binding window (config). Loaded lazily from harness.toml
        # when not injected, so neither table is hardcoded here.
        self._z_by_level = z_by_level
        self._binding = binding
        # Directories holding v0-epoch evidence whose prompt text the v2 set reproduces
        # byte for byte (D12 reuse). Searched by `existing_evidence` for `none` / direct slots.
        self.legacy_evidence_dirs = tuple(Path(d) for d in legacy_evidence_dirs)

    # -- prompt rendering (D3, D12) ---------------------------------------------------
    def render_prompt(self, proposition, mode: str, qualifier_class: Optional[str] = None,
                      compression: str = "none") -> str:
        if mode == "indirect":
            return self.prompts.indirect_template(compression).format(context_passage=proposition.context_passage)
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

    def _evidence_name(self, pid: str, mode: str, qualifier_class: Optional[str], model_id: str,
                       epoch: str, compression: str = "none") -> str:
        seg = f"{pid}.{mode}" + (f".{qualifier_class}" if qualifier_class else "")
        if mode == "indirect" and compression != "none":
            seg += f".{compression}"
        return f"{seg}.{epoch}.{model_id}.json"

    def _evidence_path(self, pid: str, mode: str, qualifier_class: Optional[str], model_id: str,
                       compression: str = "none") -> Path:
        return self.evidence_root / self._evidence_name(pid, mode, qualifier_class, model_id, self.prompts.prompt_epoch, compression)

    def existing_evidence(self, pid_or_call: str, mode: str, qualifier_class: Optional[str],
                          model_id: str, compression: str = "none") -> Optional[Elicited]:
        """The persisted exchange for this slot, if one exists — the fetch/evaluate
        separation working as designed (task 2026-09-03 step 3): evidence is not
        regenerable, and a slot that has a response is never re-elicited. Searches the run's
        directory, then (v1 rule) the parent `g1/` directory for a shared-passage slot, then
        (v2 rule, D12) the legacy directories for a byte-identical-prompt slot under a legacy
        epoch. Returns None when no file exists; a file that cannot be read is an error."""
        candidates = [self._evidence_path(pid_or_call, mode, qualifier_class, model_id, compression)]
        if self.evidence_root.parent.name == "g1":
            candidates.append(self.evidence_root.parent / candidates[0].name)
        if compression == "none":
            for d in self.legacy_evidence_dirs:
                for ep in LEGACY_EPOCHS:
                    candidates.append(Path(d) / self._evidence_name(pid_or_call, mode, qualifier_class, model_id, ep, "none"))
        path = next((c for c in candidates if c.exists()), None)
        if path is None:
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
               call_id: Optional[str] = None, compression: str = "none") -> Elicited:
        prompt = self.render_prompt(proposition, mode, qualifier_class, compression)
        cid = call_id or f"{proposition.id}.{mode}" + (f".{qualifier_class}" if qualifier_class else "")
        if mode == "indirect" and compression != "none":
            cid = f"{cid}.{compression}"
        completion = consumer.complete(prompt, call_id=cid)
        ts = self._now()
        path = self._evidence_path(proposition.id if call_id is None else call_id, mode, qualifier_class,
                                   completion.model_id, compression)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "proposition_id": proposition.id, "call_id": cid, "mode": mode,
            "qualifier_class": qualifier_class, "compression_level": compression if mode == "indirect" else None,
            "prompt_epoch": self.prompts.prompt_epoch,
            "model_id": completion.model_id, "timestamp": ts, "prompt": prompt,
            "response_text": completion.text, "usage": completion.usage,
            "duration_ms": completion.duration_ms, "cost_usd": completion.cost_usd,
            "spend_run_id": completion.spend_run_id,
            "spend_reservation_id": completion.spend_reservation_id,
            "source_doc_id": proposition.source_doc_id, "passage_id": proposition.passage_id,
            "surface_type": proposition.surface_type,
        }
        path.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return Elicited(proposition_id=proposition.id, mode=mode, prompt=prompt,
                        response_text=completion.text, model_id=completion.model_id,
                        prompt_epoch=self.prompts.prompt_epoch, timestamp=ts, evidence_path=str(path),
                        usage=completion.usage, duration_ms=completion.duration_ms,
                        cost_usd=completion.cost_usd, spend_run_id=completion.spend_run_id,
                        spend_reservation_id=completion.spend_reservation_id)

    # -- evaluate: pure ------------------------------------------------------------------
    @property
    def z_by_level(self) -> dict:
        if self._z_by_level is None:
            self._load_cfg()
        return self._z_by_level

    @property
    def binding(self) -> dict:
        if self._binding is None:
            self._load_cfg()
        return self._binding

    def _load_cfg(self):
        from ..config import load_harness_config
        cfg = load_harness_config(Path(__file__).resolve().parents[2] / "config" / "harness.toml")
        if self._z_by_level is None:
            self._z_by_level = dict(cfg.g1_z_by_level)
        if self._binding is None:
            self._binding = dict(cfg.g1_binding)

    def evaluate_qualifiers(self, elicited: Elicited, proposition,
                            only_class: Optional[str] = None, siblings=None) -> Tuple[List[QualifierVerdict], EstimateStatus, dict]:
        """Per published FORM (v1 view, now with D10 binding applied)."""
        parsed = parse(elicited.response_text)
        est, est_obs = estimate_status(parsed, proposition)
        est_obs = dict(est_obs, normalised_text=parsed.normalised)
        bound, report = bind_candidates(parsed, proposition, self.binding, elicited.mode, siblings)
        verdicts = []
        for q in proposition.qualifiers:
            if only_class and q.cls.value != only_class:
                continue
            verdicts.append(score_qualifier(bound, proposition, q, est, mode=elicited.mode,
                                            z_by_level=self.z_by_level, binding_report=report))
        return verdicts, est, est_obs

    def evaluate_families(self, elicited: Elicited, proposition, only_class: Optional[str] = None,
                          only_family: Optional[str] = None, siblings=None) -> Tuple[List[FamilyVerdict], EstimateStatus, dict, Parsed]:
        parsed = parse(elicited.response_text)
        est, est_obs = estimate_status(parsed, proposition)
        est_obs = dict(est_obs, normalised_text=parsed.normalised)
        fams: List[str] = []
        for q in proposition.qualifiers:
            f = FAMILY_OF[q.cls.value]
            if only_class and q.cls.value != only_class:
                continue
            if only_family and f != only_family:
                continue
            if f not in fams:
                fams.append(f)
        out = [score_family(parsed, proposition, f, est, elicited.mode, self.z_by_level, self.binding, only_class, siblings)
               for f in fams]
        return out, est, est_obs, parsed

    def evaluate(self, elicited: Elicited, proposition, only_class: Optional[str] = None):
        """Base-contract view: the proposition's WORST family level (unparseable if any
        family is), with every family verdict in observations."""
        fams, est, est_obs, _ = self.evaluate_families(elicited, proposition, only_class)
        obs = {"estimate_status": est.value, "estimate": est_obs,
               "per_family": [v.__dict__ | {"score": None if v.score is None else int(v.score)} for v in fams]}
        if any(v.outcome == UNPARSEABLE for v in fams):
            return UNPARSEABLE, "; ".join(v.evidence for v in fams), obs
        worst = min(fams, key=lambda v: v.level)
        return worst.score, "; ".join(v.evidence for v in fams), obs

    def records(self, elicited: Elicited, proposition, only_class: Optional[str] = None,
                only_family: Optional[str] = None, compression: str = "none",
                passage_meta: Optional[dict] = None, siblings=None) -> List[EvalResult]:
        """One EvalResult per (proposition, FAMILY, mode[, compression]) — the v2 rollup's
        unit (D9), with the per-form verdicts and the D11 covariates in observations.
        `siblings`: the passage's other propositions (D10 row identity)."""
        fams, est, est_obs, parsed = self.evaluate_families(elicited, proposition, only_class, only_family, siblings)
        out = []
        for v in fams:
            cov = covariates(v, proposition, est, est_obs, parsed, elicited, compression, passage_meta)
            out.append(EvalResult(
                probe_id=self.probe_id, target=proposition.id, qualifier_class=v.qualifier_class,
                mode=elicited.mode, outcome=v.outcome, score=v.score, level=v.level,
                failure_class=v.failure_class, estimate_status=est.value,
                model_id=elicited.model_id, prompt_epoch=elicited.prompt_epoch,
                parser_version=PARSER_VERSION, scorer_version=SCORER_VERSION,
                family=v.family, surface_type=proposition.surface_type,
                compression_level=(compression if elicited.mode == "indirect" else ""),
                evidence=v.evidence, timestamp=elicited.timestamp, evidence_path=elicited.evidence_path,
                observations=dict(v.observations, estimate=est_obs, covariates=cov,
                                  source_doc_id=proposition.source_doc_id, passage_id=proposition.passage_id,
                                  prompt_text_identical=(elicited.prompt_epoch != self.prompts.prompt_epoch))))
        return out


__all__ = ["PreservationProbe", "PromptSet", "load_prompts", "QualifierVerdict", "FamilyVerdict", "score_qualifier",
           "score_family", "bind_candidates", "bound_to_estimate", "covariates", "estimate_status",
           "within_published_rounding", "at_display_scale", "is_rounding_of", "decimals_of", "SCORER_VERSION",
           "LEGACY_EPOCHS", "label_token_classes"]
