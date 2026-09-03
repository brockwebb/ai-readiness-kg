"""The deterministic qualifier parser (design D5): rule-level checks. Scoring against
propositions is tests/test_g1_preservation.py."""
from harness.probes._g1_parse import canon_unit, parse
from harness.records import QualifierClass as Q


def _one(text, cls):
    got = parse(text).of_class(cls)
    assert got, f"no {cls.value} parsed from {text!r}"
    return got[0]


def test_plus_minus_symbol_and_words():
    q = _one("564,757 ± 10,127", Q.MOE)
    assert q.value == 10127 and q.bound_estimate == 564757 and q.rule == "pm"
    q = _one("564,757, plus or minus 10,127", Q.MOE)
    assert q.value == 10127
    q = _one("give or take 177,000 people", Q.MOE)
    assert q.value == 177000 and q.unit == "count"


def test_margin_of_error_phrase_is_always_moe():
    q = _one("at the 90 percent confidence level, with a margin of error of about 10,000", Q.MOE)
    assert q.value == 10000 and q.hedged is True and q.rule == "moe_phrase"
    q = _one("MOE = 0.2", Q.MOE)
    assert q.value == 0.2


def test_percent_moe_on_a_percent_estimate_is_percentage_points():
    q = _one("12.6 percent ± 0.2", Q.MOE)
    assert q.unit == "percent_points"
    q = _one("12.6% ±0.2 percentage points", Q.MOE)
    assert q.unit == "percent_points"


def test_confidence_level_attaches_to_the_nearest_qualifier():
    q = _one("564,757 ± 10,127 at the 90 percent confidence level", Q.MOE)
    assert q.level == 0.9
    q = _one("with a 95% confidence interval of plus or minus 177,000", Q.CI)
    assert q.level == 0.95 and q.value == 177000
    assert parse("there is a 95% chance that the true value lies between 41,616 and 43,682").of_class(Q.CI)[0].level == 0.95


def test_bounds_need_an_interval_cue_and_skip_year_ranges():
    p = parse("the confidence interval runs between £41,616 million and £43,682 million")
    ci = p.of_class(Q.CI)[0]
    assert (ci.lower, ci.upper) == (41616e6, 43682e6) and ci.form == "bounds"
    assert not parse("between 450 and 499 people").of_class(Q.CI)
    p = parse("data collected from 2014 to 2018")
    assert not p.of_class(Q.CI)
    assert p.of_class(Q.VINTAGE)[0].years == (2014, 2018)


def test_lower_and_upper_bound_lines_pair_up():
    p = parse("554,630 = Lower bound of the interval; 574,884 = Upper bound of the interval")
    assert not p.of_class(Q.CI) or p.of_class(Q.CI)[0].form == "bounds"
    p = parse("lower bound 554,630 and upper bound 574,884")
    ci = p.of_class(Q.CI)[0]
    assert (ci.lower, ci.upper) == (554630, 574884)


def test_standard_error_with_currency_and_scale():
    q = _one("with a standard error of £201 million", Q.SE)
    assert q.value == 201e6 and q.unit == "currency"
    q = _one("standard error: 2,347", Q.SE)
    assert q.value == 2347
    q = _one("the standard errors for Florida (0.122) and Arizona (0.182)", Q.SE)
    assert q.value == 0.122


def test_coefficient_of_variation_forms():
    assert _one("a coefficient of variation of 8.7%", Q.CV).value == 8.7
    assert _one("CV of 1.1 percent", Q.CV).value == 1.1
    q = _one("a relative standard error of 0.087", Q.CV)
    assert q.value == 0.087 and q.unit == "fraction"
    assert _one("the CV for Subgroup 1 drops to 18 percent", Q.CV).value == 18


def test_cv_phrase_is_not_swallowed_by_the_se_rule():
    p = parse("a relative standard error of 0.087")
    assert p.of_class(Q.CV) and not p.of_class(Q.SE)


def test_reliability_flags_and_polarity():
    assert _one("the estimate is quite reliable", Q.RELIABILITY_FLAG).polarity == "reliable"
    assert _one("is not very reliable", Q.RELIABILITY_FLAG).polarity == "unreliable"
    assert _one("use with caution", Q.RELIABILITY_FLAG).polarity == "unreliable"
    assert _one("very unprecise", Q.RELIABILITY_FLAG).polarity == "unreliable"


def test_suppression_vocabulary():
    for t in ("the cell is suppressed", "the value was withheld", "restricts some tables from publication",
              "too unreliable to be published", "not releasable"):
        assert parse(t).of_class(Q.SUPPRESSION), t


def test_dp_parameters():
    p = parse("rho = 2.56, epsilon of 17.14 and delta 10^-10; ε=17.41 (rho=2.56, delta=10-10)")
    got = {(q.parameter, q.value) for q in p.of_class(Q.DP_NOISE)}
    assert ("rho", 2.56) in got and ("epsilon", 17.14) in got and ("delta", 1e-10) in got
    assert ("epsilon", 17.41) in got
    q = _one("the privacy-loss budget for each run was 2.56", Q.DP_NOISE)
    assert q.parameter == "plb" and q.value == 2.56


def test_dp_bound_and_coverage():
    q = _one("within ± four people of their published total", Q.DP_NOISE)
    assert q.parameter == "bound" and q.value == 4 and q.unit == "count"
    q = _one("less than or equal to 5 percentage points at least 95 percent of the time", Q.DP_NOISE)
    assert q.parameter == "coverage" and q.value == 95


def test_vintage_forms():
    assert _one("the 2015 ACS 1-year estimates", Q.VINTAGE).period == "1-year"
    assert _one("Estimates for July to September 2019 show", Q.VINTAGE).text == "July to September 2019"
    assert _one("as of January 1, 2018", Q.VINTAGE).years == (2018,)
    assert _one("PPMF vintage 2021-06-08", Q.VINTAGE).text == "2021-06-08"
    v = parse("Colorado currently has 564,757 one-person households").of_class(Q.VINTAGE)
    assert v and v[0].form == "verbal"


def test_years_are_not_estimates_and_fractions_are_numbers():
    p = parse("In 2015 the share was 1,440/4,099 of the budget")
    years = [n for n in p.numbers if n.is_year]
    fracs = [n for n in p.numbers if n.is_fraction]
    assert years and years[0].value == 2015
    assert fracs and abs(fracs[0].value - 1440 / 4099) < 1e-9


def test_hedges_and_cues():
    p = parse("roughly 564,757 households; some sampling error applies")
    assert "roughly" in p.hedges
    assert any(c.startswith("sampling") for c in p.cues)
    assert "some" not in p.hedges              # 'some sampling' is not a numeric hedge


def test_scale_words_multiply_and_units_canonicalise():
    p = parse("32.75 million people")
    assert p.numbers[0].value == 32.75e6 and p.numbers[0].unit == "count"
    assert canon_unit("percentage points") == "percent_points"
    assert canon_unit("%") == "percent"
    assert canon_unit("households") == "count"


def test_empty_text_parses_to_nothing():
    p = parse("")
    assert not p.numbers and not p.qualifiers and not p.cues


def test_producer_flag_vocabulary_from_the_2026_09_03_sources():
    """StatCan 71-543-G and NCHS Series 2 flag/suppression wording (fixture-driven, step 2)."""
    assert _one("no release restrictions", Q.RELIABILITY_FLAG).polarity == "reliable"
    assert _one("release with caveats", Q.RELIABILITY_FLAG).polarity == "unreliable"
    assert _one("flagged for statistical review by the clearance official", Q.RELIABILITY_FLAG).polarity == "unreliable"
    assert _one("flagged as unreliable", Q.RELIABILITY_FLAG).polarity == "unreliable"
    for t in ("not recommended for release", "a table is filtered out", "should not be released",
              "the LFS suppresses estimates below the minimum size for release", "should not be presented"):
        assert parse(t).of_class(Q.SUPPRESSION), t
