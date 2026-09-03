"""Deterministic qualifier parser for the G1 observed leg (design D5).

Turns a restatement (prose returned by a model consumer) into the numbers, uncertainty
qualifiers, verbal hedges and vintage statements it carries, with NO model in the loop.
`probes/g1_preservation.py` scores the parse against the proposition; this module never
sees the proposition, so what it recognises is fixed by the patterns below and nothing
else. A restatement in which uncertainty is *mentioned* but nothing here can classify it
is the `unparseable` outcome — a fourth bucket beside the three scores, reported with
its own count and never coerced (D5). No model-judge fallback exists in v0.

Vocabulary sources (task step 4): ±, "plus or minus", "margin of error of", "between X and
Y", "X to Y", "confidence interval", "standard error", "coefficient of variation", "CV of",
"relative standard error" (ACS handbook 2020 ch. 7–8; ONS "Uncertainty and how we measure
it"); reliability / suppression language as the ACS handbook and ONS page phrase it
("quite reliable", "very reliable", "not very reliable", "very unprecise", "restricts …
from publication") — the StatCan 12-539-X 6e text held in the corpus carries no banded
vocabulary (task RESULT, discrepancy); percent-vs-point disambiguation (ACS: MOE on a
percentage is in percentage points even where the handbook prints "percent"); level
phrases ("90 percent confidence"); Census DAS handbook 2021 parameters (rho, epsilon,
delta, "within ± four people"); vintage forms (ACS "2014–2018", "1-year", "as of January
1, 2018"; ONS "July to September 2019").

Stdlib only. Every pattern is a module constant so a test can point at the rule that
fired; `ParsedQualifier.rule` names it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..records import QualifierClass

# --- number vocabulary -----------------------------------------------------------------
NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}
NUMWORD = r"(?:" + "|".join(NUMBER_WORDS) + r")"
SCALE_WORDS = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_SCALE = r"(?:thousand|million|billion|trillion)"
_CUR = r"(?:£|\$|€|USD|GBP)"
# Unit tokens that may follow a number. Order matters: longer alternatives first.
_UNIT = (r"(?:percentage\s*points?|percent(?:age)?\s*points?|%|percent|points?|"
         r"people|persons|households|employees|units)")
_PM = r"(?:±|\+/-|\+/−|\+-|plus\s+or\s+minus|plus-or-minus|give\s+or\s+take)"
_YEAR = r"(?:19|20)\d{2}"
_MONTH = (r"(?:January|February|March|April|May|June|July|August|September|October|"
          r"November|December)")


def _num(txt: str) -> Optional[float]:
    if txt is None:
        return None
    t = txt.strip().lower()
    if t in NUMBER_WORDS:
        return float(NUMBER_WORDS[t])
    try:
        return float(t.replace(",", ""))
    except ValueError:
        return None


def canon_unit(u: Optional[str]) -> Optional[str]:
    """Canonical unit class of a unit token: percent | percent_points | count | None."""
    if not u:
        return None
    t = " ".join(u.lower().split())
    if "point" in t:
        return "percent_points"
    if t in ("%", "percent", "percentage"):
        return "percent"
    if t in ("people", "persons", "households", "employees", "units"):
        return "count"
    if t in SCALE_WORDS:
        return "count"
    return None


@dataclass(frozen=True)
class ParsedNumber:
    value: float
    unit: Optional[str]      # canon_unit
    currency: bool
    span: str
    start: int
    is_year: bool = False
    is_fraction: bool = False


@dataclass(frozen=True)
class ParsedQualifier:
    cls: QualifierClass
    rule: str
    span: str
    start: int
    value: Optional[float] = None        # MOE / SE / CV / DP parameter / CI half-width
    unit: Optional[str] = None
    lower: Optional[float] = None        # CI bounds
    upper: Optional[float] = None
    level: Optional[float] = None        # 0.90, 0.95 …
    bound_estimate: Optional[float] = None   # the number the ± was attached to, if any
    form: Optional[str] = None           # "pm" | "bounds" | "phrase" | "flag" | "verbal"
    parameter: Optional[str] = None      # DP: rho | epsilon | delta | bound | coverage | plb
    text: Optional[str] = None           # flag wording / vintage text
    polarity: Optional[str] = None       # RELIABILITY_FLAG: "reliable" | "unreliable"
    years: tuple = ()                    # VINTAGE
    period: Optional[str] = None         # VINTAGE: "1-year" | "5-year" | …
    hedged: bool = False


@dataclass
class Parsed:
    text: str
    numbers: List[ParsedNumber] = field(default_factory=list)
    qualifiers: List[ParsedQualifier] = field(default_factory=list)
    hedges: List[str] = field(default_factory=list)
    cues: List[str] = field(default_factory=list)
    levels: List[float] = field(default_factory=list)
    vague_time: List[str] = field(default_factory=list)
    dp_verbal: List[str] = field(default_factory=list)

    def of_class(self, cls: QualifierClass) -> List[ParsedQualifier]:
        return [q for q in self.qualifiers if q.cls is cls]


# --- rules ------------------------------------------------------------------------------
_HEDGE_RE = re.compile(
    r"\b(about|roughly|approximately|approx\.?|around|an estimated|estimated at|nearly|"
    r"almost|close to|circa|or so|ballpark|in the region of|on the order of|"
    r"some(?=\s+[£$\d]))\b", re.I)
_CUE_RE = re.compile(
    r"\b(margin(?:s)? of error|MOEs?|error|confidence|interval|uncertain\w*|precis\w*|"
    r"reliab\w*|noise|noisy|privacy|budget|variation|CVs?|SEs?|sampling|standard error|"
    r"caution|suppress\w*|range|bounds?|rho|epsilon|delta|withheld|unpublished|confidential\w*|"
    r"release|released|caveats?|flag\w*|filter\w*|category)\b", re.I)

# 1. "<est> ± <moe>" and bare "± <moe>"
_PM_RE = re.compile(
    r"(?:(?P<cur0>" + _CUR + r")?(?P<est>" + NUM + r")\s*(?P<es>" + _SCALE + r")?\s*"
    r"(?P<eu>" + _UNIT + r")?\s*,?\s*(?:\(|—|-|–)?\s*)?"
    r"(?P<pm>" + _PM + r")\s*(?P<cur>" + _CUR + r")?\s*(?P<moe>" + NUM + r"|" + NUMWORD + r")"
    r"\s*(?P<ms>" + _SCALE + r")?\s*(?P<mu>" + _UNIT + r")?", re.I)
# 2. "margin of error (of|is|was|=) [±] <moe>"
# A keyword may be followed by a "for/of/on <subject>" tail ONLY when a connector then
# introduces the value ("the CV for Subgroup 1 drops to 18 percent"); without a tail the
# connector is optional ("CV of 1.1 percent", "standard error (0.122)", "MOE = 0.2").
_CONN = r"(?:of|is|was|were|:|=|\(|equal(?:s|ed)?\s+to|at|comes\s+to|drops\s+to|falls\s+to|rises\s+to|stands\s+at)"
_HEDGE_IN = r"(?:about|roughly|approximately|around|some|only|just)?"


def _kw_value(keyword: str, value_group: str, extra: str = "") -> tuple:
    """Two compiled forms (a named group may appear once per pattern): no-tail, and
    tail-with-required-connector."""
    head = r"\b(?:" + keyword + r")\b"
    return (re.compile(head + r"\s*" + _CONN + r"?\s*" + _HEDGE_IN + r"\s*" + extra + value_group, re.I),
            re.compile(head + r"\s+(?:for|on|of|around)\s+[^.;:]{0,80}?\s*" + _CONN + r"\s*" + _HEDGE_IN
                       + r"\s*" + extra + value_group, re.I))


def _finditer(patterns, text):
    for rx in patterns:
        yield from rx.finditer(text)


_MOE_PHRASE_RES = _kw_value(r"margins?\s+of\s+error|MOEs?",
                            r"(?P<cur>" + _CUR + r")?(?P<moe>" + NUM + r")\s*(?P<ms>" + _SCALE + r")?\s*(?P<mu>" + _UNIT + r")?",
                            extra=r"(?:±|plus\s+or\s+minus)?\s*")
# 3. standard error
_SE_RES = _kw_value(r"standard\s+errors?|sampling\s+errors?|SEs?",
                    r"(?P<cur>" + _CUR + r")?(?P<v>" + NUM + r")\s*(?P<s>" + _SCALE + r")?\s*(?P<u>" + _UNIT + r")?",
                    extra=r"(?:±)?\s*")
# 4. coefficient of variation / relative standard error
_CV_RES = _kw_value(r"coefficients?\s+of\s+variation|CVs?|relative\s+standard\s+errors?|RSEs?",
                    r"(?P<v>" + NUM + r")\s*(?P<u>%|percent)?")
# 5. bounds "between X and Y" / "from X to Y" / "X to Y"
_BOUNDS_RE = re.compile(
    r"\b(?:between|from|of|lies?\s+between|falls?\s+(?:somewhere\s+)?between|range\s+of)\s+"
    r"(?P<c1>" + _CUR + r")?(?P<lo>" + NUM + r")\s*(?P<s1>" + _SCALE + r")?\s*(?P<u1>" + _UNIT + r")?"
    r"\s+(?:and|to)\s+(?P<c2>" + _CUR + r")?(?P<hi>" + NUM + r")\s*(?P<s2>" + _SCALE + r")?\s*(?P<u2>" + _UNIT + r")?",
    re.I)
_LOWER_UPPER_RE = re.compile(
    r"\b(?P<which>lower|upper)\s+(?:bound|limit)\b[^.;:\d]{0,40}?(?P<cur>" + _CUR + r")?(?P<v>" + NUM + r")\s*(?P<s>" + _SCALE + r")?",
    re.I)
_CI_CUE_RE = re.compile(r"confidence\s+interval|confidence\s+level|confident|interval|likely\s+to\s+lie|"
                        r"true\s+(?:population\s+)?value|range", re.I)
# 6. confidence level
_LEVEL_RE = re.compile(
    r"\b(?P<lv>\d{2}(?:\.\d)?)\s*(?:%|percent|-percent|per\s+cent)?\s*(?:confidence|CI\b|level|confident)"
    r"|\bconfidence\s+(?:level|interval)\s*(?:of|at)?\s*(?:the\s+)?(?P<lv2>\d{2})\s*(?:%|percent)"
    r"|\b(?P<lv3>\d{2})\s*(?:%|percent)\s+(?:chance|certain|sure)", re.I)
# 8. reliability flags
_RELIABILITY_RE = re.compile(
    r"\b(?P<flag>(?:(?:very|quite|highly|fairly|reasonably|extremely|considered\s+(?:a\s+)?|deemed\s+(?:a\s+)?)\s+)?"
    r"(?:not\s+(?:very\s+)?)?(?:reliable|unreliable)|use(?:d)?\s+with\s+caution|low\s+reliability|"
    r"poor\s+(?:precision|reliability)|imprecise|(?:very\s+)?unprecise|not\s+(?:very\s+)?precise|"
    # Producer flag vocabulary (v1, task 2026-09-03 step 2 — fixture-driven, cited to the
    # admitted sources and added with the fixtures before any elicitation): StatCan 71-543-G
    # "no release restrictions" / "release with caveats" / "warning to users" / Category 1–3;
    # NCHS Series 2 "flagged for statistical review" / "flagged for internal review" /
    # "flagged as unreliable".
    r"no\s+release\s+restrictions?|release(?:d)?\s+with\s+(?:caveats?|a\s+warning|warnings?)|"
    r"(?:accompanied\s+by\s+)?(?:a\s+)?warning\s+to\s+users|"
    r"flagged\s+(?:for\s+(?:statistical|internal)\s+review|as\s+unreliable)|"
    r"(?:suppressed\s+or\s+)?flagged(?:\s+for\s+review)?|category\s+[123])\b", re.I)
_NEGATIVE_FLAG_RE = re.compile(r"\b(not|un|caution|poor|imprecise|unprecise|low|caveats?|warning|flag\w*|"
                               r"category\s+[23]|review)", re.I)
# 9. suppression
_SUPPRESSION_RE = re.compile(
    r"\b(?P<s>suppress(?:ed|ion|es)?|withheld|withhold|not\s+(?:be\s+)?published|not\s+releas(?:able|ed)|"
    r"too\s+unreliable\s+to\s+(?:be\s+)?publish(?:ed)?|restrict(?:ed|s)\s+[^.;]{0,40}?from\s+publication|"
    r"unpublished|not\s+recommended\s+for\s+release|(?:should\s+)?not\s+be\s+released|filtered\s+out|"
    r"minimum\s+(?:estimate\s+)?size\s+for\s+release|below\s+the\s+minimum|not\s+(?:be\s+)?presented|"
    r"do\s+not\s+present)\b", re.I)
# 10. DP parameters
_DP_PARAM_RE = re.compile(
    r"\b(?P<p>rho|ρ|epsilon|ε|delta|δ)\b\s*(?:of|=|is|was|:|equal(?:s)?\s+to|value\s+of|set\s+(?:to|at))?\s*"
    r"(?:\(\s*)?(?P<v>10\s*(?:\^|\*\*)?\s*[-−–]\s*10|1e-10|10−10|" + NUM + r")", re.I)
_DP_PLB_RE = re.compile(
    r"\bprivacy[-\s]loss\s+budget\b\s*(?:of|=|is|was|:|\(|for\s+[^.;]{0,60}?\s+(?:was|is))?\s*"
    r"(?P<sym>ε|epsilon|rho|ρ)?\s*=?\s*(?P<v>" + NUM + r")", re.I)
_DP_BOUND_RE = re.compile(
    r"\bwithin\s*(?:" + _PM + r")?\s*(?P<v>" + NUM + r"|" + NUMWORD + r")\s*(?P<u>" + _UNIT + r")", re.I)
_DP_COVERAGE_RE = re.compile(
    r"\b(?:at\s+least|in|for)\s+(?P<v>" + NUM + r")\s*(?:%|percent)\s+of\s+(?:the\s+time|counties|cases|"
    r"block\s+groups|areas|places|geographies|runs)", re.I)
_DP_VERBAL_RE = re.compile(r"\b(noise|noisy|noise-infused|perturb\w*|fuzz\w*|differential(?:ly)?\s+priva\w+|"
                           r"disclosure\s+avoidance|privacy[-\s]protect\w*)\b", re.I)
# 11. vintage
_YEAR_RANGE_RE = re.compile(r"\b(?P<y1>" + _YEAR + r")\s*(?:–|-|—|to|through|until)\s*(?P<y2>" + _YEAR + r")\b")
_MONTH_RANGE_RE = re.compile(
    r"\b(?P<m1>" + _MONTH + r")(?:\s+(?:to|through|–|-)\s+(?P<m2>" + _MONTH + r"))?\s+(?:(?P<d>\d{1,2}),?\s+)?(?P<y>" + _YEAR + r")\b")
_ISO_DATE_RE = re.compile(r"\b(?P<y>" + _YEAR + r")-(?P<m>\d{2})-(?P<d>\d{2})\b")
_YEAR_RE = re.compile(r"(?<!\d,)(?<![\d.])(?P<y>" + _YEAR + r")(?!,\d)(?!\d)")
_PERIOD_RE = re.compile(r"\b(?P<n>1|3|5)[-\s]year\b", re.I)
_AS_OF_RE = re.compile(r"\bas\s+of\s+(?:" + _MONTH + r"\s+\d{1,2},?\s+)?(?P<y>" + _YEAR + r")\b", re.I)
_VAGUE_TIME_RE = re.compile(r"\b(recent(?:ly)?|latest|current(?:ly)?|most\s+recent|today|nowadays|"
                            r"up[-\s]to[-\s]date|at\s+(?:the|that)\s+time|these\s+days|now)\b", re.I)
# 12. fractions
_FRACTION_RE = re.compile(r"(?<![\d.])(?P<a>" + NUM + r")\s*/\s*(?P<b>" + NUM + r")(?![\d.])")
# 13. all numbers
_ANY_NUM_RE = re.compile(r"(?P<cur>" + _CUR + r")?\s*(?P<n>" + NUM + r")\s*(?P<s>" + _SCALE + r")?\s*(?P<u>" + _UNIT + r")?", re.I)


def _preceding_number(text: str, pos: int, window: int = 80) -> Optional[float]:
    """Nearest number before `pos` in the same clause (no sentence boundary between),
    skipping bare years and confidence levels ('90 percent')."""
    seg = text[max(0, pos - window): pos]
    if "." in seg and re.search(r"\.\s+[A-Z]", seg):
        seg = seg[list(re.finditer(r"\.\s+[A-Z]", seg))[-1].end() - 1:]
    best = None
    for m in _ANY_NUM_RE.finditer(seg):
        raw = m.group("n")
        if re.fullmatch(_YEAR, raw) and not m.group("s") and not m.group("u"):
            continue                                   # a year
        if _LEVEL_RE.match(seg[m.start("n"):]):
            continue                                   # "90 percent confidence"
        estimate_like = bool(m.group("s") or m.group("u") or m.group("cur") or "," in raw or "." in raw
                             or len(raw) >= 4)
        if not estimate_like:
            continue                                   # "aged 65", "16 and over"
        best = _scaled(raw, m.group("s"))
    return best


def _scaled(txt: str, scale_word: Optional[str]) -> Optional[float]:
    v = _num(txt)
    if v is None:
        return None
    if scale_word:
        v *= SCALE_WORDS[scale_word.lower()]
    return v


def _delta_value(txt: str) -> Optional[float]:
    t = txt.replace(" ", "").lower()
    if t in ("1e-10", "10−10") or re.fullmatch(r"10(\^|\*\*)?[-−–]10", t):
        return 1e-10
    return _num(txt)


def _has_ci_cue(text: str, start: int, before: int = 160, after: int = 40) -> bool:
    return bool(_CI_CUE_RE.search(text[max(0, start - before): start + after]))


def parse(text: str) -> Parsed:
    """Parse one restatement. Pure; order-independent apart from de-duplication by span."""
    p = Parsed(text=text or "")
    t = p.text
    if not t.strip():
        return p
    taken: List[tuple] = []          # (start, end) spans already claimed by a qualifier rule

    def claim(m) -> bool:
        s, e = m.start(), m.end()
        for a, b in taken:
            if s < b and e > a:
                return False
        taken.append((s, e))
        return True

    p.hedges = [m.group(1).lower() for m in _HEDGE_RE.finditer(t)]
    p.cues = sorted({m.group(1).lower() for m in _CUE_RE.finditer(t)})
    p.vague_time = [m.group(1).lower() for m in _VAGUE_TIME_RE.finditer(t)]
    p.dp_verbal = [m.group(1).lower() for m in _DP_VERBAL_RE.finditer(t)]
    for m in _LEVEL_RE.finditer(t):
        lv = _num(m.group("lv") or m.group("lv2") or m.group("lv3"))
        if lv and 50 <= lv < 100:
            p.levels.append(round(lv / 100, 3))

    def nearest_level(pos: int) -> Optional[float]:
        best, dist = None, 10 ** 9
        for m in _LEVEL_RE.finditer(t):
            d = abs(m.start() - pos)
            if d < dist and d <= 220:
                lv = _num(m.group("lv") or m.group("lv2") or m.group("lv3"))
                if lv and 50 <= lv < 100:
                    best, dist = round(lv / 100, 3), d
        return best

    def hedged_before(pos: int) -> bool:
        return bool(_HEDGE_RE.search(t[max(0, pos - 30): pos]))

    # --- DP parameters first (they contain bare numbers other rules could grab) --------
    for m in _DP_PARAM_RE.finditer(t):
        sym = m.group("p").lower()
        param = {"ρ": "rho", "ε": "epsilon", "δ": "delta"}.get(sym, sym)
        val = _delta_value(m.group("v")) if param == "delta" else _num(m.group("v"))
        if val is None or not claim(m):
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.DP_NOISE, "dp_param", m.group(0), m.start(),
                                            value=val, parameter=param, form="phrase"))
    for m in _DP_PLB_RE.finditer(t):
        if not claim(m):
            continue
        sym = (m.group("sym") or "").lower()
        param = {"ρ": "rho", "ε": "epsilon"}.get(sym, sym) or "plb"
        p.qualifiers.append(ParsedQualifier(QualifierClass.DP_NOISE, "dp_plb", m.group(0), m.start(),
                                            value=_num(m.group("v")), parameter=param, form="phrase"))
    for m in _DP_BOUND_RE.finditer(t):
        if not claim(m):
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.DP_NOISE, "dp_bound", m.group(0), m.start(),
                                            value=_num(m.group("v")), unit=canon_unit(m.group("u")),
                                            parameter="bound", form="pm"))
    for m in _DP_COVERAGE_RE.finditer(t):
        if not claim(m):
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.DP_NOISE, "dp_coverage", m.group(0), m.start(),
                                            value=_num(m.group("v")), unit="percent",
                                            parameter="coverage", form="phrase"))

    # --- CV before SE (its phrase contains "standard error") ---------------------------
    for m in _finditer(_CV_RES, t):
        if not claim(m):
            continue
        v = _num(m.group("v"))
        unit = "percent" if m.group("u") else ("fraction" if v is not None and v < 1 else None)
        p.qualifiers.append(ParsedQualifier(QualifierClass.CV, "cv_phrase", m.group(0), m.start(),
                                            value=v, unit=unit, form="phrase", hedged=hedged_before(m.start("v"))))
    for m in _finditer(_SE_RES, t):
        if not claim(m):
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.SE, "se_phrase", m.group(0), m.start(),
                                            value=_scaled(m.group("v"), m.group("s")),
                                            unit=canon_unit(m.group("u")) or ("currency" if m.group("cur") else None),
                                            form="phrase", hedged=hedged_before(m.start("v"))))
    for m in _finditer(_MOE_PHRASE_RES, t):
        if not claim(m):
            continue
        # The phrase names the class: "margin of error" is MOE whatever surrounds it.
        p.qualifiers.append(ParsedQualifier(QualifierClass.MOE, "moe_phrase", m.group(0), m.start(),
                                            value=_scaled(m.group("moe"), m.group("ms")),
                                            unit=canon_unit(m.group("mu")) or ("currency" if m.group("cur") else None),
                                            level=nearest_level(m.start()), form="pm",
                                            hedged=hedged_before(m.start("moe"))))
    for m in _PM_RE.finditer(t):
        if not claim(m):
            continue
        cls = QualifierClass.CI if _has_ci_cue(t, m.start("pm")) else QualifierClass.MOE
        est = None
        if m.group("est") and not (re.fullmatch(_YEAR, m.group("est")) and not m.group("es") and not m.group("eu")):
            est = _scaled(m.group("est"), m.group("es"))
        if est is None:
            # Bind to the nearest preceding non-year number within the same clause: the
            # thing a ± is attached to is normally the last figure before it.
            est = _preceding_number(t, m.start("pm"))
        eu = canon_unit(m.group("eu"))
        mu = canon_unit(m.group("mu"))
        if mu is None and eu == "percent":
            # ACS convention: the MOE on a percentage is in percentage points even when the
            # producer prints "percent" (handbook ch. 8, "MOE of 0.1 percent (0.001)").
            mu = "percent_points"
        p.qualifiers.append(ParsedQualifier(cls, "pm", m.group(0), m.start("pm"),
                                            value=_scaled(m.group("moe"), m.group("ms")),
                                            unit=mu or ("currency" if m.group("cur") else None),
                                            level=nearest_level(m.start("pm")), bound_estimate=est,
                                            form="pm", hedged=hedged_before(m.start("moe"))))
    # bounds
    for m in _BOUNDS_RE.finditer(t):
        lo, hi = _scaled(m.group("lo"), m.group("s1")), _scaled(m.group("hi"), m.group("s2"))
        if lo is None or hi is None or lo >= hi:
            continue
        if re.fullmatch(_YEAR, m.group("lo")) and re.fullmatch(_YEAR, m.group("hi")):
            continue                                   # a year range is VINTAGE, below
        if not _has_ci_cue(t, m.start()):
            continue                                   # a bare range is not an interval claim
        if not claim(m):
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.CI, "bounds", m.group(0), m.start(),
                                            value=(hi - lo) / 2, lower=lo, upper=hi,
                                            unit=canon_unit(m.group("u2") or m.group("u1")),
                                            level=nearest_level(m.start()), form="bounds"))
    lowers = [(m.start(), _scaled(m.group("v"), m.group("s"))) for m in _LOWER_UPPER_RE.finditer(t)
              if m.group("which").lower() == "lower"]
    uppers = [(m.start(), _scaled(m.group("v"), m.group("s"))) for m in _LOWER_UPPER_RE.finditer(t)
              if m.group("which").lower() == "upper"]
    for (ls, lo), (us, hi) in zip(lowers, uppers):
        if lo is not None and hi is not None and lo < hi:
            p.qualifiers.append(ParsedQualifier(QualifierClass.CI, "lower_upper", t[min(ls, us): max(ls, us) + 40],
                                                min(ls, us), value=(hi - lo) / 2, lower=lo, upper=hi,
                                                level=nearest_level(min(ls, us)), form="bounds"))

    # --- flags ----------------------------------------------------------------------------
    for m in _RELIABILITY_RE.finditer(t):
        flag = " ".join(m.group("flag").split())
        polarity = "unreliable" if _NEGATIVE_FLAG_RE.search(flag) else "reliable"
        p.qualifiers.append(ParsedQualifier(QualifierClass.RELIABILITY_FLAG, "reliability", m.group(0),
                                            m.start(), text=flag.lower(), polarity=polarity, form="flag"))
    for m in _SUPPRESSION_RE.finditer(t):
        p.qualifiers.append(ParsedQualifier(QualifierClass.SUPPRESSION, "suppression", m.group(0), m.start(),
                                            text=" ".join(m.group("s").lower().split()), form="flag"))

    # --- vintage ----------------------------------------------------------------------------
    covered: List[tuple] = []
    period = None
    pm_ = _PERIOD_RE.search(t)
    if pm_:
        period = f"{pm_.group('n')}-year"
    for m in _YEAR_RANGE_RE.finditer(t):
        covered.append((m.start(), m.end()))
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "year_range", m.group(0), m.start(),
                                            text=f"{m.group('y1')}–{m.group('y2')}",
                                            years=(int(m.group("y1")), int(m.group("y2"))), period=period,
                                            form="phrase"))
    for m in _ISO_DATE_RE.finditer(t):
        covered.append((m.start(), m.end()))
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "iso_date", m.group(0), m.start(),
                                            text=m.group(0), years=(int(m.group("y")),), period=period, form="phrase"))
    for m in _MONTH_RANGE_RE.finditer(t):
        covered.append((m.start(), m.end()))
        txt = m.group(0)
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "month_year", txt, m.start(),
                                            text=" ".join(txt.split()), years=(int(m.group("y")),),
                                            period=period, form="phrase"))
    for m in _AS_OF_RE.finditer(t):
        covered.append((m.start(), m.end()))
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "as_of", m.group(0), m.start(),
                                            text=" ".join(m.group(0).split()), years=(int(m.group("y")),),
                                            period=period, form="phrase"))
    for m in _YEAR_RE.finditer(t):
        if any(a <= m.start() < b for a, b in covered):
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "year", m.group(0), m.start(),
                                            text=m.group("y"), years=(int(m.group("y")),), period=period,
                                            form="phrase"))
    if period and not p.of_class(QualifierClass.VINTAGE):
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "period_only", pm_.group(0), pm_.start(),
                                            text=period, period=period, form="phrase"))
    if p.vague_time and not p.of_class(QualifierClass.VINTAGE):
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "vague_time", p.vague_time[0], 0,
                                            text=p.vague_time[0], form="verbal"))

    # --- numbers ------------------------------------------------------------------------------
    fraction_spans = []
    for m in _FRACTION_RE.finditer(t):
        a, b = _num(m.group("a")), _num(m.group("b"))
        if a is None or b in (None, 0.0):
            continue
        fraction_spans.append((m.start(), m.end()))
        p.numbers.append(ParsedNumber(a / b, "fraction", False, m.group(0), m.start(), is_fraction=True))
    for m in _ANY_NUM_RE.finditer(t):
        if any(a <= m.start("n") < b for a, b in fraction_spans):
            continue
        raw = m.group("n")
        v = _scaled(raw, m.group("s"))
        if v is None:
            continue
        is_year = bool(re.fullmatch(_YEAR, raw)) and not m.group("s") and not m.group("u")
        unit = canon_unit(m.group("u"))
        if unit is None and m.group("s"):
            unit = "count"
        p.numbers.append(ParsedNumber(v, unit, bool(m.group("cur")), m.group(0).strip(), m.start("n"),
                                      is_year=is_year))
    return p


__all__ = ["parse", "Parsed", "ParsedNumber", "ParsedQualifier", "canon_unit", "NUMBER_WORDS", "SCALE_WORDS"]
