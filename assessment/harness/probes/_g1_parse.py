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

# Instrument version of this parser (task 2026-09-03 step 4.4, DD-034): stamped on every
# EvalResult so records scored under different rule sets are never pooled. Bumped on any
# rule change; the old stamp stays valid for the results files it produced.
PARSER_VERSION = "g1-parse-v2"   # v2 opened 2026-09-03 (task g1_eval_v2 step 3): legend-symbol
                                   # vocabulary from the admitted surfaces; frozen at g1-v2-frozen

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
    normalised: str = ""
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
    r"(?P<pm>" + _PM + r")\s*(?:about|roughly|approximately|around|some)?\s*(?P<cur>" + _CUR + r")?\s*(?P<moe>" + NUM + r"|" + NUMWORD + r")"
    r"\s*(?P<ms>" + _SCALE + r")?\s*(?P<mu>" + _UNIT + r")?", re.I)
# 2. "margin of error (of|is|was|=) [±] <moe>"
# A keyword may be followed by a "for/of/on <subject>" tail ONLY when a connector then
# introduces the value ("the CV for Subgroup 1 drops to 18 percent"); without a tail the
# connector is optional ("CV of 1.1 percent", "standard error (0.122)", "MOE = 0.2").
_CONN = r"(?:of|is|was|were|:|=|≈|~|\(|equal(?:s|ed)?\s+to|at|comes\s+to|drops\s+to|falls\s+to|rises\s+to|stands\s+at)"
# In the tail form a bare "(" counts only when the parenthesis holds just the number
# ("the standard errors for Florida (0.122)"), not a label's own parenthetical.
_CONN_TAIL = r"(?:of|is|was|were|:|=|≈|~|\((?=\s*" + _CUR + r"?" + NUM + r"\s*(?:%|percent)?\))|equal(?:s|ed)?\s+to|at|comes\s+to|drops\s+to|falls\s+to|rises\s+to|stands\s+at)"
# A value immediately followed by an arithmetic operator is a formula term, not a value
# ("MOE = 1.645 × SE", acs-ch8-tricounty.indirect.…json).
_NOT_FORMULA = r"(?!\d|\.\d|,\d)(?!\s*[×÷*/])"
_HEDGE_IN = r"(?:about|roughly|approximately|around|some|only|just)?"


def _kw_value(keyword: str, value_group: str, extra: str = "") -> tuple:
    """Two compiled forms (a named group may appear once per pattern): no-tail, and
    tail-with-required-connector."""
    head = r"\b(?:" + keyword + r")\b(?:\s*\([^)\n]{0,40}\))?"
    vg = value_group + _NOT_FORMULA
    return (re.compile(head + r"\s*" + _CONN + r"?\s*" + _HEDGE_IN + r"\s*" + extra + vg, re.I),
            re.compile(head + r"\s+(?:for|on|of|around)\s+[^.;:]{0,80}?\s*" + _CONN_TAIL + r"\s*" + _HEDGE_IN
                       + r"\s*" + extra + vg, re.I))


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
    r"\b(?:between|from|of|lies?\s+between|falls?\s+(?:somewhere\s+)?between|range\s+of|runs\s+from|"
    r"(?:interval|range|bounds?|CI)[^:\n]{0,40}:)\s*"
    r"(?:about|roughly|approximately|around)?\s*(?P<c1>" + _CUR + r")?(?P<lo>" + NUM + r")\s*(?P<s1>" + _SCALE + r")?\s*(?P<u1>" + _UNIT + r")?"
    r"\s*(?:\s(?:and|to)\s|–|—|-)\s*(?P<c2>" + _CUR + r")?(?P<hi>" + NUM + r")\s*(?P<s2>" + _SCALE + r")?\s*(?P<u2>" + _UNIT + r")?",
    re.I)
_LOWER_UPPER_RE = re.compile(
    r"\b(?P<which>lower|upper)\s+(?:bound|limit)\b[^.;:\d]{0,40}?(?P<cur>" + _CUR + r")?(?P<v>" + NUM + r")\s*(?P<s>" + _SCALE + r")?",
    re.I)
_CI_CUE_RE = re.compile(r"confidence\s+interval|confidence\s+level|confident|interval|likely\s+to\s+lie|"
                        r"true\s+(?:population\s+)?value|range|\bCIs?\b", re.I)
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
    r"(?:suppressed\s+or\s+)?flagged(?:\s+for\s+review)?|category\s+[123]|"
    # paraphrases seen in lfs-reliability-categories.indirect.…json
    r"publish(?:ed)?\s+with\s+(?:a\s+)?(?:caution|warning)|publish(?:ed)?\s+freely|no\s+warning\s+label|"
    # NCHS outcome words (nchs175-standard / g1-n175-rf-001.direct.…json)
    r"(?:can|may|should)\s+be\s+presented|judged\s+reliable|presented\s+without)\b", re.I)
# Cell markers with their legends on the admitted product surfaces (task 2026-09-03_g1_eval_v2
# step 2 — fixture-driven, cited, added BEFORE any v2 elicitation like the v1 producer words):
#   StatCan cube-metadata symbol legend (statcan-13-10-0096-01 / 13-10-0113-01 / 14-10-0287-01
#   -cube-metadata-csv): A–D data quality excellent…acceptable, E "use with caution",
#   F "too unreliable to be published", x "suppressed to meet the confidentiality requirements
#   of the Statistics Act", ".." not available.
#   NCHS Data Brief 530 (nchs-data-brief-530-perinatal-mortality-2022-2023): "† Change not
#   significant (p = 0.05)." in place of a value.
# A bare letter is a flag only when it sits where a status sits: after a number / value cell
# ("37.5 E", "37.5E", "37.5 (E)", "flagged E", "status E", "STATUS: E", "an E flag").
_SYMBOL_FLAG_RE = re.compile(
    r"(?:(?<=\d)\s?|(?<=\d\s)|(?<=\d\)\s)|\bflag(?:ged|s)?(?:\s+(?:as|with))?\s+(?:an?\s+)?[\"“']?|\bstatus(?:\s+(?:of|code|is|=|:))?\s*[\"“']?|\bquality(?:\s+(?:indicator|flag|letter|code|rating))?(?:\s+(?:of|is|=|:))?\s*[\"“']?|\bmark(?:ed|er)?\s+(?:with\s+)?(?:an?\s+)?[\"“']?|\bletter\s+[\"“']?|\bsymbol\s+[\"“']?)"
    r"(?P<sym>\(?[A-F]\)?|†|‡|\*)(?![\w-])(?![.,]?\d)", re.I)
_SIGNIFICANCE_FLAG_RE = re.compile(
    r"\b(?P<flag>(?:change|difference|increase|decrease|rise|fall|drop)s?\s+(?:that\s+)?(?:was|were|is|are)?\s*"
    r"(?:not\s+(?:statistically\s+)?significant|nonsignificant|non-significant|statistically\s+insignificant)|"
    r"(?:not\s+(?:statistically\s+)?significant|nonsignificant|non-significant|statistically\s+insignificant)(?:\s+(?:change|difference|increase|decrease|rise|fall|drop))?|"
    r"no\s+(?:statistically\s+)?significant\s+(?:change|difference|increase|decrease|rise|fall|drop)s?|"
    r"(?:did|does|do)\s+not\s+(?:change|differ)\s+significantly|(?:was|were|is|are)\s+(?:statistically\s+)?similar|"
    r"(?:statistically\s+)?significant(?:ly)?\s+(?:change|difference|increase|decrease|rise|fall|drop|higher|lower)s?|"
    r"(?:change|difference|increase|decrease|rise|fall|drop)s?\s+(?:that\s+)?(?:was|were|is|are)\s+(?:statistically\s+)?significant)\b", re.I)
_SYMBOL_LEGEND = {"A": ("data quality: excellent", "reliable"), "B": ("data quality: very good", "reliable"),
                  "C": ("data quality: good", "reliable"), "D": ("data quality: acceptable", "reliable"),
                  "E": ("use with caution", "unreliable"), "F": ("too unreliable to be published", "suppressed"),
                  "†": ("change not significant", "unreliable"), "‡": ("flagged", "unreliable"), "*": ("flagged", "unreliable")}
_SUPPRESSION_SYMBOL_RE = re.compile(r"(?:(?<=\d)\s?|\bflag(?:ged|s)?(?:\s+(?:as|with))?\s+|\bstatus(?:\s+(?:of|code|is|=|:))?\s*|\bmarked\s+(?:as\s+)?|\bsymbol\s+|\bshown\s+as\s+|\bappears\s+as\s+)[\"“']?(?P<sym>x|F|\.\.)[\"”']?(?![\w.])", re.I)
_NEGATIVE_FLAG_RE = re.compile(r"\b(not|un|caution|poor|imprecise|unprecise|low|caveats?|warning|flag\w*|"
                               r"category\s+[23]|review)", re.I)
# 9. suppression
_SUPPRESSION_RE = re.compile(
    r"\b(?P<s>suppress(?:ed|ion|es)?|withheld|withhold|not\s+(?:be\s+)?published|not\s+releas(?:able|ed)|"
    r"too\s+unreliable\s+to\s+(?:be\s+)?publish(?:ed)?|restrict(?:ed|s)\s+[^.;]{0,40}?from\s+publication|"
    r"unpublished|not\s+recommended\s+for\s+release|(?:should\s+)?not\s+be\s+released|filtered\s+out|"
    r"minimum\s+(?:estimate\s+)?size\s+for\s+release|below\s+the\s+minimum|not\s+(?:be\s+)?presented|"
    r"do\s+not\s+present|don['’]t\s+publish|do\s+not\s+publish|not\s+(?:be\s+)?publishable|"
    # acs-filtering-rule.indirect.…json: "we drop the table entirely", "We leave out tables"
    r"drop(?:ped|s)?\s+(?:the\s+)?(?:table|estimate|cell|row)s?(?:\s+entirely)?|leaves?\s+out|left\s+out|"
    r"excluded\s+from\s+(?:publication|release))\b", re.I)
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
# "2021/2022" (StatCan two-year period estimates, statcan-13-10-0113-01) is a year range too (v2).
_YEAR_RANGE_RE = re.compile(r"\b(?P<y1>" + _YEAR + r")\s*(?:–|-|—|/|to|through|until)\s*(?P<y2>" + _YEAR + r")\b")
# "August 2021–August 2023" (NCHS Data Brief 515's NHANES cycle; v2 fixture form): a
# month-year to month-year range is one reference period with two years.
_MONTH_YEAR_RANGE_RE = re.compile(
    r"\b(?P<m1>" + _MONTH + r")\s+(?P<y1>" + _YEAR + r")\s*(?:–|-|—|to|through|until)\s*(?P<m2>" + _MONTH + r")\s+(?P<y2>" + _YEAR + r")\b")
_MONTH_RANGE_RE = re.compile(
    r"\b(?P<m1>" + _MONTH + r")(?:\s+(?:to|through|–|-)\s+(?P<m2>" + _MONTH + r"))?\s+(?:(?P<d>\d{1,2}),?\s+)?(?P<y>" + _YEAR + r")\b")
_ISO_DATE_RE = re.compile(r"\b(?P<y>" + _YEAR + r")-(?P<m>\d{2})-(?P<d>\d{2})\b")
# "2026-07" (StatCan REF_DATE, statcan-14-10-0287-01 slices): a year-month reference period (v2).
_ISO_MONTH_RE = re.compile(r"\b(?P<y>" + _YEAR + r")-(?P<m>0[1-9]|1[0-2])\b(?!-\d)")
_YEAR_RE = re.compile(r"(?<!\d,)(?<![\d.])(?P<y>" + _YEAR + r")(?!,\d)(?!\d)")
_PERIOD_RE = re.compile(r"\b(?P<n>1|3|5)[-\s]year\b", re.I)
_AS_OF_RE = re.compile(r"\bas\s+of\s+(?:" + _MONTH + r"\s+\d{1,2},?\s+)?(?P<y>" + _YEAR + r")\b", re.I)
_VAGUE_TIME_RE = re.compile(r"\b(recent(?:ly)?|latest|current(?:ly)?|most\s+recent|today|nowadays|"
                            r"up[-\s]to[-\s]date|at\s+(?:the|that)\s+time|these\s+days|now)\b", re.I)
# 12. fractions
# A share written as a fraction (1,440/4,099). Decimal denominators (10,127 / 1.645) and
# fractions inside arithmetic ("= 3,860 / 1.645", "(122,972 / 61,393,366) × 100") are
# formula terms, not values (g1-acs-cv-004.direct.CV.…json, g1-acs-ci-004.direct.CV.…json).
_FRACTION_RE = re.compile(r"(?<![\d.=≈(])(?<![=≈(]\s)(?P<a>" + NUM + r")\s*/\s*(?P<b>(?:\d{1,3}(?:,\d{3})+|\d+))(?![\d.])(?!\s*[×÷*/)])")
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


# --- pre-normalisation (v1, task 2026-09-03 step 4.1) ------------------------------------
# Applied to the raw restatement BEFORE any NFKC-style pass. Each transform is named and
# tested; the normalised text travels in observations beside the raw so a reviewer can see
# what was parsed. Motivating evidence (dev responses, v0 prefix):
#   superscripts   g1-das-dp-003.direct.DP_NOISE.…json      "Delta: 10⁻¹⁰"
#   emphasis       ons-cv-examples.indirect.indirect.…json  "**£2,322 million**, give or take about **£201 million**"
#   pipe tables    das-plb-people.indirect.indirect.…json   "| Global rho | 2.56 |"
#   label lists    ons-cv-examples.indirect.indirect.…json  "the **coefficient of variation**:\n- £201m ÷ £2,322m = 0.087, or **8.7%**"
_SUPER = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
          "⁻": "-", "⁺": "+"}
_SUB = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9", "₋": "-"}
_POW10_SUPER_RE = re.compile(r"10\s*(?P<e>[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)")
_POW10_CARET_RE = re.compile(r"10\s*(?:\^|\*\*)\s*\(?\s*(?P<e>[-−–+]?\d+)\s*\)?")
_POW10_UNICODE_MINUS_RE = re.compile(r"10\s*(?P<e>[−–]\d+)\b")


def normalise_superscripts(text: str) -> str:
    """`10⁻¹⁰`, `10^-10`, `10**(-10)`, `10−10` -> `1e-10` (one exponent form). Must run before
    NFKC, which maps `⁻¹⁰` to `-10` and turns the exponent into a subtraction. Other
    superscript/subscript digits (footnote markers) are mapped to plain digits."""
    def _sup(m):
        e = "".join(_SUPER.get(ch, ch) for ch in m.group("e"))
        return f"1e{e}"
    text = _POW10_SUPER_RE.sub(_sup, text)
    text = _POW10_CARET_RE.sub(lambda m: "1e" + m.group("e").replace("−", "-").replace("–", "-"), text)
    text = _POW10_UNICODE_MINUS_RE.sub(lambda m: "1e" + m.group("e").replace("−", "-").replace("–", "-"), text)
    return "".join(_SUPER.get(ch, _SUB.get(ch, ch)) for ch in text)


_EMPHASIS_RE = re.compile(r"\*\*|__|`+|(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)")
_UNDERSCORE_EMPHASIS_RE = re.compile(r"(?<!\w)_(\S(?:[^_\n]*?\S)?)_(?!\w)")


def strip_markdown_emphasis(text: str) -> str:
    """Remove `**`, `__`, backticks, single `*` used as emphasis, and `_word_` emphasis. Field
    names such as B01001_001E keep their underscores (the pattern needs a non-word boundary)."""
    text = _UNDERSCORE_EMPHASIS_RE.sub(r"\1", text)
    return _EMPHASIS_RE.sub("", text)


_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


# Column headers that name nothing ("Value", "Measure", "What it means"): the cell is emitted
# bare so "| Global rho | 0.07 | The technical budget … |" reads "Global rho: 0.07; …"
# (das-plb-units.indirect.…json).
_GENERIC_HEADER_RE = re.compile(r"^\s*(?:value|values|measure|amount|figure|number|what\s+it\s+means|meaning|note|notes|interpretation)\s*$", re.I)
_HEADER_UNIT_RE = re.compile(r"\((?P<cur>" + _CUR + r")?\s*(?P<scale>thousands?|millions?|billions?)?\)\s*$", re.I)


def _apply_header_unit(header: str, cell: str) -> str:
    m = _HEADER_UNIT_RE.search(header.strip())
    if not m or not re.match(r"^\s*" + NUM + r"\s*$", cell):
        return cell
    cur = m.group("cur") or ""
    scale = (m.group("scale") or "").lower().rstrip("s")
    out = f"{cur}{cell.strip()}"
    if scale:
        out += f" {scale}"
    return out


def flatten_pipe_tables(text: str) -> str:
    """A markdown table row `| Global rho | 2.56 |` becomes the line `Global rho: 2.56.`; a
    wider row `| State | 1,440/4,099 | 35.1% |` becomes `State: 1,440/4,099; 35.1%.` Separator
    rows are dropped; header rows are kept as `h1: h2; h3.` (harmless to the rules)."""
    out = []
    header = None            # column headers of the table currently being read
    for line in text.splitlines():
        if "|" in line and line.count("|") >= 2:
            if _TABLE_SEP_RE.match(line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            cells = [c for c in cells if c != ""]
            if len(cells) >= 2:
                if header is None and not any(ch.isdigit() for ch in "".join(cells[1:])):
                    # a header row (no digits in the value columns): remember the column
                    # names so each data cell is emitted as `<column>: <value>`
                    # (ons-se-table1.indirect.…json: "| Industry | Total turnover (£ millions) |
                    # Standard error (£ millions) | Relative standard error |").
                    header = cells
                    out.append(f"{cells[0]}: " + "; ".join(cells[1:]) + ".")
                    continue
                if header and len(header) == len(cells) and len(cells) >= 3:
                    # three or more columns: name each value by its column; a two-column
                    # "Measure | Value" table already reads as label: value. A column header
                    # that carries a unit in parentheses — "(£ millions)", "(thousands)" —
                    # applies that unit to each cell ("Standard error (£ millions) | 526.8"
                    # -> "Standard error: £526.8 million"; ons-se-table1.indirect.…json).
                    pairs = [(_apply_header_unit(h, v) if _GENERIC_HEADER_RE.match(h) else f"{h}: {_apply_header_unit(h, v)}")
                             for h, v in zip(header[1:], cells[1:])]
                    out.append(f"{cells[0]}: " + "; ".join(pairs) + ".")
                else:
                    out.append(f"{cells[0]}: " + "; ".join(cells[1:]) + ".")
                continue
        header = None
        out.append(line)
    return "\n".join(out)


_LABEL_KEYWORDS = (r"coefficients?\s+of\s+variation|CVs?|relative\s+standard\s+errors?|standard\s+errors?|SEs?|"
                   r"margins?\s+of\s+error|MOEs?|confidence\s+intervals?|rho|epsilon|delta")
_LABEL_LIST_RE = re.compile(
    r"(?P<kw>\b(?:" + _LABEL_KEYWORDS + r")\b)(?:(?!\b(?:" + _LABEL_KEYWORDS + r")\b)[^\n:]){0,200}?:[^\S\n]*\n(?:[^\S\n]*\n)*"
    r"(?P<items>(?:[^\S\n]*(?:[-*•]|\d+[.)])[^\n]*\n?)+)", re.I)
_LAST_VALUE_RE = re.compile(r"(?P<cur>" + _CUR + r")?(?P<n>" + NUM + r")\s*(?P<s>" + _SCALE + r")?\s*(?P<u>%|percent(?:age)?\s*points?|percent)?(?![^\n]*\d)")


_ITEM_LABEL_RE = re.compile(r"^(?P<lab>[^:\n\d]{1,40}):")


def join_label_lists(text: str) -> str:
    """`coefficient of variation:` followed by list items -> one sentence per item, `<keyword>
    of <last value in the item>`, so the keyword–value rules apply. The last numeric token
    of an item is the value (an item like `£201m ÷ £2,322m = 0.087, or 8.7%` ends in the
    result). The original lines are kept; the joined sentences are appended after the list."""
    def _rep(m):
        kw = m.group("kw")
        joined = []
        for item in m.group("items").splitlines():
            body = re.sub(r"^[^\S\n]*(?:[-*•]|\d+[.)])\s*", "", item)
            last = None
            for v in _LAST_VALUE_RE.finditer(body):
                last = v
            if last:
                # keep the item's own row label ("Fairfax: 3,860 ÷ 1.645 = 2,347" -> "Fairfax:
                # standard error of 2,347.") so the sentence binds to its row (v2, D10;
                # acs-ch8-tricounty.indirect.indirect.…json)
                lab = _ITEM_LABEL_RE.match(body)
                prefix = f"{lab.group('lab').strip()}: " if lab else ""
                joined.append(f"{prefix}{kw} of {last.group(0).strip()}.")
        return m.group(0) + ("\n" + " ".join(joined) + "\n" if joined else "")
    return _LABEL_LIST_RE.sub(_rep, text)


_CURRENCY_ABBREV_RE = re.compile(r"(?P<cur>" + _CUR + r")(?P<n>" + NUM + r")(?P<a>m|bn|k)\b")
_ABBREV = {"m": "million", "bn": "billion", "k": "thousand"}


def expand_currency_abbreviations(text: str) -> str:
    """`£201m` -> `£201 million`, `£2,322m`, `$3bn`, `£5k` (motivating evidence:
    g1-ons-cv-002.direct.CV.…json "£201m ÷ £2,322m = 0.0866 ≈ 8.7%")."""
    return _CURRENCY_ABBREV_RE.sub(lambda m: f"{m.group('cur')}{m.group('n')} {_ABBREV[m.group('a')]}", text)


_DERIVATION_RE = re.compile(
    r"(?P<kw>\b(?:" + _LABEL_KEYWORDS + r")\b)(?P<mid>[^\n:]{0,400}?)(?P<lead>\b(?:For|for)\s+[^:\n]{1,60}:\s*|:\s*(?=[^\n]*[=≈]))"
    r"(?P<der>[^\n.]*?[=≈][^\n]*?)(?=\.\s|\n|$)", re.I)


def join_derivation_lines(text: str) -> str:
    """A keyword sentence followed in the same paragraph by a derivation `For <label>: <arith>
    ≈ <value>` (acs-ch7-colorado.indirect.indirect.…json: "*Coefficient of variation (CV)*
    expresses … For Colorado: 6,156 ÷ 564,757 ≈ 1.1 percent.") gains a sentence `<keyword>
    of <last value of the derivation>.` after the paragraph."""
    def _rep(m):
        last = None
        for v in _LAST_VALUE_RE.finditer(m.group("der")):
            last = v
        if not last:
            return m.group(0)
        lead = re.sub(r"^(?:For|for)\s+", "", m.group("lead")).strip().rstrip(":").strip()
        prefix = f"{lead}: " if lead and not any(ch.isdigit() for ch in lead) else ""
        return m.group(0) + f" {prefix}{m.group('kw')} of {last.group(0).strip()}."
    return _DERIVATION_RE.sub(_rep, text)


_EQ_CHAIN_RE = re.compile(
    r"(?P<kw>\b(?:" + _LABEL_KEYWORDS + r"|SE|CV|MOE)\b(?:\s*\([^)\n]{0,40}\))?)\s*[=≈]\s*"
    r"(?P<chain>(?:[^\n;,]|,(?=\d{3}))*?[=≈](?:[^\n;,]|,(?=\d{3}))*)")


def collapse_equations(text: str) -> str:
    """`SE = MOE / 1.645 = 3,860 / 1.645 = 2,346.5 ≈ 2,347` -> `SE ≈ 2,347` (the last value of
    the chain is the stated result; the intermediate terms are formula, not values).
    Motivating evidence: g1-acs-se-005.direct.SE.…json, g1-acs-cv-004.direct.CV.…json."""
    def _rep(m):
        last = None
        for v in _LAST_VALUE_RE.finditer(m.group("chain")):
            last = v
        if not last:
            return m.group(0)
        return f"{m.group('kw')} ≈ {last.group(0).strip()}"
    return _EQ_CHAIN_RE.sub(_rep, text)


def normalise_text(text: str) -> str:
    """The v1 pre-normalisation pipeline, in order: superscripts (before any NFKC), markdown
    emphasis, currency abbreviations, pipe tables, label-then-list joins."""
    if not text:
        return text or ""
    text = normalise_superscripts(text)
    text = strip_markdown_emphasis(text)
    text = expand_currency_abbreviations(text)
    text = flatten_pipe_tables(text)
    text = join_label_lists(text)
    text = join_derivation_lines(text)
    text = collapse_equations(text)
    return text


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
    p.normalised = normalise_text(p.text)
    t = p.normalised
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
        if re.match(r"\s*(?:standard\s+errors?|SEs?|sigma)\b", t[m.end():]):
            continue                                   # "± 1 standard error": a multiple, not a value
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
    # Legend symbols (v2, fixture-driven): a status letter / dagger beside a value or named as a
    # flag; the legend meaning travels in `text`, the symbol in `parameter` (reused field).
    for m in _SYMBOL_FLAG_RE.finditer(t):
        sym = m.group("sym").strip("()").upper() if m.group("sym").strip("()").isalpha() else m.group("sym")
        legend, pol = _SYMBOL_LEGEND.get(sym, ("flagged", "unreliable"))
        # a symbol anchors on a number only when it sits directly beside it ("37.5 E",
        # "7.73 †"); a named flag ("flagged E", "status: E") binds by sentence / label instead
        adjacent = bool(re.fullmatch(r"\s?\(?[A-Fa-f†‡*]\)?", m.group(0)))
        est = _preceding_number(t, m.start()) if adjacent else None
        if pol == "suppressed":
            p.qualifiers.append(ParsedQualifier(QualifierClass.SUPPRESSION, "symbol_suppression", m.group(0), m.start(),
                                                text=legend, parameter=sym, form="flag", bound_estimate=est))
            continue
        p.qualifiers.append(ParsedQualifier(QualifierClass.RELIABILITY_FLAG, "symbol_flag", m.group(0), m.start(),
                                            text=legend, parameter=sym, polarity=pol, form="flag", bound_estimate=est))
    for m in _SUPPRESSION_SYMBOL_RE.finditer(t):
        sym = m.group("sym")
        if sym.upper() == "F" and any(q.rule == "symbol_suppression" and q.start == m.start() for q in p.qualifiers):
            continue
        legend = {"x": "suppressed to meet the confidentiality requirements of the Statistics Act",
                  "F": "too unreliable to be published", "..": "not available for a specific reference period"}[sym if sym == ".." else sym.upper() if sym.upper() == "F" else "x"]
        adjacent = bool(re.fullmatch(r"\s?[\"“']?(?:x|F|\.\.)[\"”']?", m.group(0), re.I))
        p.qualifiers.append(ParsedQualifier(QualifierClass.SUPPRESSION, "symbol_suppression", m.group(0), m.start(),
                                            text=legend, parameter=sym, form="flag",
                                            bound_estimate=_preceding_number(t, m.start()) if adjacent else None))
    # Significance statements about a change (NCHS 530 †: "Change not significant"): a
    # reliability flag on the comparison; negative polarity when the change is NOT significant.
    for m in _SIGNIFICANCE_FLAG_RE.finditer(t):
        flag = " ".join(m.group("flag").lower().split())
        neg = bool(re.search(r"\bnot\b|\bnonsignificant\b|\bnon-significant\b|\binsignificant\b|\bno\s+|\bsimilar\b", flag))
        p.qualifiers.append(ParsedQualifier(QualifierClass.RELIABILITY_FLAG, "significance_flag", m.group(0), m.start(),
                                            text=flag, polarity="unreliable" if neg else "reliable", form="flag"))

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
    for m in _MONTH_YEAR_RANGE_RE.finditer(t):
        covered.append((m.start(), m.end()))
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "month_year_range", m.group(0), m.start(),
                                            text=" ".join(m.group(0).split()),
                                            years=(int(m.group("y1")), int(m.group("y2"))), period=period, form="phrase"))
    for m in _ISO_DATE_RE.finditer(t):
        covered.append((m.start(), m.end()))
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "iso_date", m.group(0), m.start(),
                                            text=m.group(0), years=(int(m.group("y")),), period=period, form="phrase"))
    for m in _ISO_MONTH_RE.finditer(t):
        if any(a <= m.start() < b for a, b in covered):
            continue
        covered.append((m.start(), m.end()))
        p.qualifiers.append(ParsedQualifier(QualifierClass.VINTAGE, "iso_month", m.group(0), m.start(),
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
    p.numbers.sort(key=lambda n: n.start)
    return p


__all__ = ["parse", "Parsed", "ParsedNumber", "ParsedQualifier", "canon_unit", "NUMBER_WORDS", "SCALE_WORDS",
           "PARSER_VERSION", "normalise_text", "normalise_superscripts", "strip_markdown_emphasis",
           "flatten_pipe_tables", "join_label_lists", "expand_currency_abbreviations", "join_derivation_lines",
           "collapse_equations"]
