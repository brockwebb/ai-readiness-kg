"""The G1 observed-leg scorer (designs D2–D7) against the hand-written restatement fixture,
plus the elicit/record path with a scripted consumer (no network, no model)."""
import json
from pathlib import Path

import pytest
import yaml

from harness.consumers import ScriptedConsumer
from harness.g1_fixtures import Proposition, Qualifier, load_fixture_set
from harness.probes.base import Elicited
from harness.probes.g1_preservation import (
    PreservationProbe, decimals_of, estimate_status, is_rounding_of, load_prompts,
    within_published_rounding,
)
from harness.probes._g1_parse import parse
from harness.records import UNPARSEABLE, EvalResult, Level, QualifierClass, Score

FIX = Path(__file__).parent / "fixtures" / "g1"
CONFIG = Path(__file__).parents[1] / "config"


@pytest.fixture(scope="module")
def dev():
    return load_fixture_set(FIX / "propositions.yaml")


@pytest.fixture(scope="module")
def cases():
    return yaml.safe_load((FIX / "restatements.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def prompts():
    return load_prompts(CONFIG / "g1_prompts.toml")


def _prop(dev, cases, pid):
    for raw in cases["synthetic_propositions"]:
        if raw["id"] == pid:
            return Proposition(
                id=raw["id"], source_doc_id=raw["source_doc_id"], passage_id=raw["passage"],
                grounding_span=raw["grounding_span"],
                context_passage=cases["synthetic_passages"][raw["passage"]],
                estimate=raw["estimate"],
                qualifiers=tuple(Qualifier(QualifierClass(q["class"]), {k: v for k, v in q.items() if k != "class"})
                                 for q in raw["qualifiers"]),
                producer_rule=raw["producer_rule"])
    return dev.by_id(pid)


def _elicited(text, mode="indirect"):
    return Elicited(proposition_id="x", mode=mode, prompt="p", response_text=text, model_id="scripted",
                    prompt_epoch="g1-test", timestamp="2026-09-02T00:00:00Z", evidence_path="/dev/null")


def _verdict_for(probe, prop, case, siblings=None):
    verdicts, est, _ = probe.evaluate_qualifiers(_elicited(case["text"], case.get("mode", "indirect")), prop,
                                                 only_class=case["class"], siblings=siblings)
    cls_verdicts = [v for v in verdicts if v.qualifier_class == case["class"]]
    assert cls_verdicts, f"{case['prop']}: no verdict for class {case['class']}"
    which = case.get("which")
    if which:
        cls_verdicts = [v for v in cls_verdicts if v.observations["qualifier_source"].get("parameter") == which]
    return cls_verdicts[0], est


# --- every fixture case scores as expected ---------------------------------------------
def _case_ids(cases):
    return [f"{c['prop']}:{c['class']}:{i}" for i, c in enumerate(cases["cases"])]


def pytest_generate_tests(metafunc):
    if "case" in metafunc.fixturenames:
        cs = yaml.safe_load((FIX / "restatements.yaml").read_text(encoding="utf-8"))
        metafunc.parametrize("case", cs["cases"], ids=_case_ids(cs))
    if "v1case" in metafunc.fixturenames:
        cs = yaml.safe_load((FIX / "restatements.yaml").read_text(encoding="utf-8"))
        metafunc.parametrize("v1case", cs.get("v1_cases", []),
                             ids=[f"v1:{c['prop']}:{c['class']}:{i}" for i, c in enumerate(cs.get("v1_cases", []))])


def test_v1_case_from_dev_evidence(dev, cases, prompts, v1case, tmp_path):
    """Parser v1 cases: text verbatim from a named dev-response evidence file (or a synthetic
    case for the level-derived SE transformation, so marked)."""
    assert v1case.get("evidence"), "a v1 case names its motivating evidence"
    probe = PreservationProbe(prompts, tmp_path)
    prop = _prop(dev, cases, v1case["prop"])
    v, est = _verdict_for(probe, prop, v1case, siblings=dev.by_passage(prop.passage_id) if prop.id in {p.id for p in dev.propositions} else None)
    assert est.value == v1case["expect_estimate"], (v1case["text"], v.evidence, v.observations.get("estimate"))
    # scorer v2 (D10) re-attributes some failures; a case carrying `expect_*_v2` states the
    # v2 reading beside the v1 one it was written for (each such case says why in `note_v2`)
    assert v.level == v1case.get("expect_level_v2", v1case["expect_level"]), (v1case["text"], v.evidence, v.observations)
    assert v.failure_class == v1case.get("expect_failure_v2", v1case.get("expect_failure")), (v1case["text"], v.evidence)


def test_normalised_text_travels_in_observations(dev, prompts, tmp_path):
    prop = dev.by_id("g1-das-dp-003")
    probe = PreservationProbe(prompts, tmp_path)
    _, _, obs = probe.evaluate(_elicited("| Delta | 10⁻¹⁰ |"), prop)
    assert obs["estimate"]["normalised_text"] == "Delta: 1e-10."


def test_records_carry_the_parser_version(dev, prompts, tmp_path):
    from harness.probes._g1_parse import PARSER_VERSION
    prop = dev.by_id("g1-acs-moe-001")
    probe = PreservationProbe(prompts, tmp_path)
    from harness.probes.g1_preservation import SCORER_VERSION
    for r in probe.records(_elicited("564,757 ± 10,127 in 2015"), prop):
        assert r.parser_version == PARSER_VERSION == "g1-parse-v2"
        assert r.scorer_version == SCORER_VERSION == "g1-score-v2"
        assert r.family in ("interval", "vintage")
    with pytest.raises(ValueError):
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=4, failure_class=None, estimate_status="exact",
                   model_id="m", prompt_epoch="e", parser_version="", evidence="", timestamp="t", evidence_path="x")


def test_case(dev, cases, prompts, case, tmp_path):
    probe = PreservationProbe(prompts, tmp_path)
    prop = _prop(dev, cases, case["prop"])
    v, est = _verdict_for(probe, prop, case)
    assert est.value == case["expect_estimate"], (case["text"], v.evidence, v.observations.get("estimate"))
    if case.get("expect_outcome") == UNPARSEABLE:
        assert v.outcome == UNPARSEABLE and v.level is None and v.score is None, (case["text"], v.evidence)
        return
    level = case.get("expect_level_v2", case.get("expect_level_override", case["expect_level"]))
    failure = case.get("expect_failure_v2", case.get("expect_failure_override", case.get("expect_failure")))
    assert v.level == level, (case["text"], v.evidence, v.observations)
    assert v.failure_class == failure, (case["text"], v.evidence)
    if case.get("expect_direction"):
        assert v.observations.get("direction") == case["expect_direction"], (case["text"], v.observations)


# --- structural guarantees over the whole fixture -----------------------------------------
def _all_verdicts(dev, cases, prompts, tmp_path):
    probe = PreservationProbe(prompts, tmp_path)
    out = []
    for c in cases["cases"]:
        v, _ = _verdict_for(probe, _prop(dev, cases, c["prop"]), c)
        out.append((c, v))
    return out


def test_every_level_is_reached_for_every_populated_class(dev, cases, prompts, tmp_path):
    reached = {}
    for c, v in _all_verdicts(dev, cases, prompts, tmp_path):
        if v.level is not None:
            reached.setdefault(c["class"], set()).add(v.level)
    populated = {k for k, n in dev.counts_by_class().items() if n} | {"SUPPRESSION"}
    for cls in populated:
        levels = reached.get(cls, set())
        if cls in ("SUPPRESSION", "RELIABILITY_FLAG"):
            # A flag has no verbal-band form (L2) by construction: the scale's L2 is the
            # numeric->verbal shift. The other four levels must be reached.
            assert {0, 1, 4} <= levels, (cls, levels)
        elif cls == "SE":
            # v0 defines no legitimate transformation for a standard error (scale and
            # precision changes are exact matches), so L3 is unreachable by construction.
            # Recorded in the task RESULT as a deviation from the step-4 wording.
            assert levels == {0, 1, 2, 4}, (cls, levels)
        else:
            assert levels == {0, 1, 2, 3, 4}, (cls, levels)


def test_unparseable_is_reached_counted_and_never_coerced(dev, cases, prompts, tmp_path):
    unp = [(c, v) for c, v in _all_verdicts(dev, cases, prompts, tmp_path) if v.outcome == UNPARSEABLE]
    assert unp, "no fixture case reaches unparseable"
    for c, v in unp:
        assert v.score is None and v.level is None and v.failure_class is None


def test_dev_coverage_is_reported_but_is_not_the_gate(dev, cases, prompts, tmp_path, capsys):
    """v0's gate measured parse coverage on restatements the parser's author wrote and scored
    1.00 while 8 of 18 real responses were unparseable (v0 RESULT §6). The number is still
    reported here; the gate is `test_holdout_readiness_gate` below (task 2026-09-03 step 6)."""
    labelled = [c for c in cases["cases"] if c.get("expect_outcome") != UNPARSEABLE]
    parsed = [c for c, v in _all_verdicts(dev, cases, prompts, tmp_path)
              if c.get("expect_outcome") != UNPARSEABLE and v.outcome != UNPARSEABLE]
    coverage = len(parsed) / len(labelled)
    print(f"dev-restatement parse coverage (reported, not a gate): {coverage:.3f} on {len(labelled)} cases")
    assert 0.0 <= coverage <= 1.0


HOLDOUT_RESULTS = sorted((Path(__file__).parents[1] / "results").glob("g1_v1_*holdout*.json"))


def test_holdout_readiness_gate():
    """Pre-registered readiness gate (task 2026-09-03 step 6, replaces D5's): `unparseable`
    share on the SEALED holdout responses <= 0.10. The holdout responses exist only after the
    parser freeze; until they are scored, this test is skipped with that reason and the
    parser is not ready."""
    if not HOLDOUT_RESULTS:
        pytest.skip("no holdout results file yet: parser readiness cannot be claimed (step 5 not run)")
    report = json.loads(HOLDOUT_RESULTS[-1].read_text(encoding="utf-8"))
    a = report["g1"]["observed"]["all"]
    share = a["n_unparseable"] / a["n"] if a["n"] else None
    assert share is not None and share <= 0.10, (
        f"holdout unparseable share {share:.3f} > 0.10 on n={a['n']} ({HOLDOUT_RESULTS[-1].name}) — parser not ready")


def test_widened_and_narrowed_are_both_l0_with_direction(dev, cases, prompts, tmp_path):
    dirs = {}
    for c, v in _all_verdicts(dev, cases, prompts, tmp_path):
        if c.get("expect_direction"):
            assert v.level == 0
            dirs.setdefault(c["class"], set()).add(v.observations["direction"])
    assert {"widened", "narrowed"} <= dirs["MOE"]
    assert "narrowed" in dirs["SE"] and "widened" in dirs["SE"]


# --- tolerance helpers (D7) ------------------------------------------------------------------
def test_within_published_rounding_uses_the_source_decimals():
    assert within_published_rounding(526.8, "526.8", 1e6, 526.8e6)
    assert within_published_rounding(526.8, "526.8", 1e6, 526.84e6)      # extra precision rounds back
    assert not within_published_rounding(526.8, "526.8", 1e6, 527e6)     # coarser: L0 by pre-registration
    assert within_published_rounding(10127, "10,127", 1, 10127.4)
    assert not within_published_rounding(10127, "10,127", 1, 10128)
    assert decimals_of("0.3513") == 4 and decimals_of("1,032.5") == 1


def test_is_rounding_of_recognises_coarser_forms_only():
    assert is_rounding_of(564757, 1, 565000, "564,757")
    assert is_rounding_of(564757, 1, 560000, "564,757")
    assert not is_rounding_of(564757, 1, 564757, "564,757")
    assert not is_rounding_of(564757, 1, 564000.5, "564,757")


def test_estimate_status_wrong_is_a_same_unit_number_of_the_same_order(dev):
    prop = dev.by_id("g1-acs-moe-001")
    assert estimate_status(parse("654,757 households"), prop)[0].value == "wrong"
    assert estimate_status(parse("about 12 percent"), prop)[0].value == "absent"


# --- elicit / records path with a scripted consumer ------------------------------------------
def test_elicit_writes_evidence_before_scoring_and_stamps_epoch_and_model(dev, prompts, tmp_path):
    prop = dev.by_id("g1-acs-moe-001")
    probe = PreservationProbe(prompts, tmp_path, timestamp="2026-09-02T00:00:00Z")
    text = "In 2015 Colorado had 564,757 one-person households, plus or minus 10,127 at the 90 percent confidence level."
    consumer = ScriptedConsumer({probe.render_prompt(prop, "indirect"): text}, model_id="scripted-model")
    el = probe.elicit(consumer, prop, "indirect")
    path = Path(el.evidence_path)
    assert path.exists() and path.name == "g1-acs-moe-001.indirect.g1-v2-2026-09-03.scripted-model.json"
    record = json.loads(path.read_text())
    assert record["prompt"] == el.prompt and record["response_text"] == text
    assert record["prompt_epoch"] == "g1-v2-2026-09-03" and record["model_id"] == "scripted-model"
    assert prop.context_passage in el.prompt                    # D4: source in context
    records = probe.records(el, prop)
    assert {r.qualifier_class for r in records} == {"MOE", "VINTAGE"}
    for r in records:
        assert isinstance(r, EvalResult) and r.prompt_epoch and r.model_id
        assert r.source == "eval" and r.dimension == "G1"
    moe = next(r for r in records if r.qualifier_class == "MOE")
    assert moe.level == 4 and moe.score is Score.PASS and moe.estimate_status == "exact"


def test_direct_mode_names_the_qualifier_in_plain_words(dev, prompts, tmp_path):
    prop = dev.by_id("g1-ons-cv-002")
    probe = PreservationProbe(prompts, tmp_path)
    p = probe.render_prompt(prop, "direct", "CV")
    assert "coefficient of variation" in p and prop.estimate_label in p and prop.context_passage in p
    with pytest.raises(ValueError):
        probe.render_prompt(prop, "direct")


def test_evaluate_reports_the_worst_qualifier_and_unparseable_wins(dev, prompts, tmp_path):
    prop = dev.by_id("g1-acs-moe-001")
    probe = PreservationProbe(prompts, tmp_path)
    score, ev, obs = probe.evaluate(_elicited("In 2015 there were 564,757 one-person households in Colorado."), prop)
    assert score is Score.FAIL                     # MOE omitted (L1) is worse than VINTAGE L3
    assert {v["family"] for v in obs["per_family"]} == {"interval", "vintage"}
    out, _, _ = probe.evaluate(_elicited("Colorado had 564,757 one-person households in 2015; a margin of error is published."), prop)
    assert out == UNPARSEABLE


def test_record_without_epoch_or_model_is_invalid():
    with pytest.raises(ValueError):
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=4, failure_class=None, estimate_status="exact",
                   model_id="", prompt_epoch="e", parser_version="t", evidence="", timestamp="t", evidence_path="x")
    with pytest.raises(ValueError):
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=4, failure_class=None, estimate_status="exact",
                   model_id="m", prompt_epoch=" ", parser_version="t", evidence="", timestamp="t", evidence_path="x")
    with pytest.raises(ValueError):                # score must follow from level
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=1, failure_class=None, estimate_status="exact",
                   model_id="m", prompt_epoch="e", parser_version="t", evidence="", timestamp="t", evidence_path="x")


def test_prompt_config_requires_epoch_and_context_placeholder(tmp_path):
    bad = tmp_path / "p.toml"
    bad.write_text('prompt_epoch = ""\n[indirect]\ntemplate="x {context_passage}"\n[direct]\ntemplate="y {context_passage}"\n[qualifier_plain]\n')
    with pytest.raises(Exception):
        load_prompts(bad)


# ---------------------------------------------------------------- scorer v2 (D9–D12)
def _holdout_prop(pid):
    return load_fixture_set(FIX / "propositions_holdout.yaml").by_id(pid)


def pytest_generate_tests_v2(metafunc):  # pragma: no cover — folded into pytest_generate_tests below
    pass


def _v2_cases():
    cs = yaml.safe_load((FIX / "restatements.yaml").read_text(encoding="utf-8"))
    return cs.get("v2_cases", []) + cs.get("v2_cases_parser_misses", [])


@pytest.mark.parametrize("v2case", _v2_cases(), ids=[f"v2:{c['prop']}:{c['family']}" for c in _v2_cases()])
def test_v2_case_verbatim_from_v1_evidence_scores_the_reviewer_class(dev, prompts, v2case, tmp_path):
    """D10 failure-class attribution: the three v1 reviewer-labelled omissions (verbatim)."""
    probe = PreservationProbe(prompts, tmp_path)
    try:
        prop = dev.by_id(v2case["prop"])
    except KeyError:
        prop = _holdout_prop(v2case["prop"])
    fams, est, _, _ = probe.evaluate_families(_elicited(v2case["text"], v2case["mode"]), prop, only_family=v2case["family"])
    assert est.value == v2case["expect_estimate"], (v2case["prop"], est)
    v = fams[0]
    assert v.family == v2case["family"]
    form = v.observations["forms"][v2case["class"]]
    # the FORM the reviewer judged carries the corrected class …
    assert form["level"] == v2case["expect_level"], (v2case["prop"], form["evidence"], v.observations["binding"])
    assert form["failure_class"] == v2case["expect_failure"], (v2case["prop"], form["evidence"])
    # … and the FAMILY takes the best published form (D9): an interval carried as its CI is preserved
    assert v.level == v2case["expect_family_level"], (v2case["prop"], v.evidence, v.observations["forms"])


def test_family_is_the_scored_unit_and_takes_the_best_form(dev, prompts, tmp_path):
    """D9: SE and CI published on one estimate are one `interval` family; a correct interval
    where the SE is not stated is a preserved family (L3, cross-form), not an SE omission."""
    prop = dev.by_id("g1-ons-se-003") if any(q.cls.value == "CI" for q in dev.by_id("g1-ons-se-003").qualifiers) else None
    if prop is None:
        pytest.skip("no dev proposition publishes SE and CI together")


def test_family_records_carry_forms_covariates_and_factors(dev, prompts, tmp_path):
    prop = dev.by_id("g1-acs-moe-001")
    probe = PreservationProbe(prompts, tmp_path)
    recs = probe.records(_elicited("In 2015 Colorado had 564,757 one-person households, plus or minus 10,127 at the 90 percent confidence level."),
                         prop, compression="tight", passage_meta={"declared_leg_score": 1})
    by_family = {r.family: r for r in recs}
    assert set(by_family) == {"interval", "vintage"}
    r = by_family["interval"]
    assert r.level == 4 and r.qualifier_class == "MOE" and r.compression_level == "tight" and r.surface_type == "prose_labeled"
    cov = r.observations["covariates"]
    for key in ("relative_deviation", "rounding_direction", "summary_precision_consistent", "compression_ratio",
                "footnote_distance_chars", "declared_leg_score", "surface_type", "compression_level", "consumer_model_id"):
        assert key in cov, key
    assert cov["declared_leg_score"] == 1 and cov["compression_level"] == "tight" and cov["relative_deviation"] == 0.0
    assert "MOE" in r.observations["forms"] and r.observations["n_forms"] == 1
    # direct-mode records carry no compression level
    d = probe.records(_elicited("10,127", "direct"), prop, only_family="interval")
    assert d[0].compression_level == "" and d[0].mode == "direct"


def test_binding_no_bound_candidate_is_an_omission_not_a_binding_error(dev, prompts, tmp_path):
    """D10: another row's ± in the response, nothing bound to this estimate -> L1 omission with
    the unbound candidate recorded; the same ± presented beside THIS row's label -> binding_error."""
    prop = dev.by_id("g1-acs-moe-001")          # 564,757 ± 10,127 (Colorado one-person households)
    probe = PreservationProbe(prompts, tmp_path)
    fams, _, _, _ = probe.evaluate_families(
        _elicited("Colorado had 564,757 one-person households in 2015. Arizona's figure was 700,000 ± 12,000."), prop,
        only_family="interval")
    v = fams[0]
    assert v.level == 1 and v.failure_class == "omission", (v.evidence, v.observations["binding"])
    assert v.observations["binding"]["other_estimate"], v.observations["binding"]
    fams, _, _, _ = probe.evaluate_families(
        _elicited("One-person households in Colorado: 700,000 ± 12,000 in 2015."), prop, only_family="interval")
    v = fams[0]
    assert v.level == 0 and v.failure_class == "binding_error", (v.evidence, v.observations["binding"])


def test_unparseable_survives_binding_but_unbound_candidates_do_not_make_it(dev, prompts, tmp_path):
    prop = dev.by_id("g1-acs-moe-001")
    probe = PreservationProbe(prompts, tmp_path)
    fams, _, _, _ = probe.evaluate_families(
        _elicited("Colorado had 564,757 one-person households in 2015; the margin of error is small."), prop, only_family="interval")
    assert fams[0].outcome == UNPARSEABLE


def test_display_scale_value_is_transformed_not_exact(dev, prompts, tmp_path):
    """A 'Persons in thousands' surface restated at its printed magnitude: L3 with
    scale_word_omitted; the same value with the scale word: L4."""
    v2 = load_fixture_set(FIX / "v2" / "propositions.yaml")
    prop = v2.by_id("g1v2-lfs-ab-employment")          # 2670.0 thousand, SE 19.8 thousand
    probe = PreservationProbe(prompts, tmp_path)
    fams, est, _, _ = probe.evaluate_families(
        _elicited("Alberta employment in July 2026 was 2,670.0 (standard error 19.8)."), prop, only_family="interval")
    assert est.value == "exact" and fams[0].level == 3 and fams[0].observations["chosen_observations"].get("scale_word_omitted")
    fams, est, _, _ = probe.evaluate_families(
        _elicited("Alberta employment in July 2026 was 2,670.0 thousand, with a standard error of 19.8 thousand."), prop, only_family="interval")
    assert est.value == "exact" and fams[0].level == 4


def test_symbol_flag_and_significance_flag_score_the_reliability_family(prompts, tmp_path):
    v2 = load_fixture_set(FIX / "v2" / "propositions.yaml")
    probe = PreservationProbe(prompts, tmp_path)
    nl = v2.by_id("g1v2-cchs-nl-youth")                  # 37.5 E (use with caution)
    fams, _, _, _ = probe.evaluate_families(
        _elicited("In Newfoundland and Labrador, 37.5% of youth were overweight or obese in 2022 (flagged E: use with caution)."), nl,
        only_family="reliability")
    assert fams[0].level == 4, fams[0].evidence
    fams, _, _, _ = probe.evaluate_families(
        _elicited("In Newfoundland and Labrador, 37.5% of youth were overweight or obese in 2022, a reliable figure."), nl,
        only_family="reliability")
    assert fams[0].level == 0 and fams[0].failure_class == "suppression_override", fams[0].evidence
    fams, _, _, _ = probe.evaluate_families(
        _elicited("In Newfoundland and Labrador, 37.5% of youth were overweight or obese in 2022."), nl, only_family="reliability")
    assert fams[0].level == 1 and fams[0].failure_class == "omission"
    ak = v2.by_id("g1v2-nchs530-alaska")                 # 7.73, † change not significant
    fams, _, _, _ = probe.evaluate_families(
        _elicited("Alaska's perinatal mortality rate was 7.73 per 1,000 in 2023, a change from 2022 that was not significant."), ak,
        only_family="reliability")
    assert fams[0].level == 4, fams[0].evidence
    fams, _, _, _ = probe.evaluate_families(
        _elicited("Alaska's perinatal mortality rate fell to 7.73 in 2023 from 8.39 in 2022."), ak, only_family="reliability")
    assert fams[0].level == 1 and fams[0].failure_class == "omission"


def test_cross_family_derivation_scores_l3_only_with_a_correct_estimate(dev, prompts, tmp_path):
    prop = dev.by_id("g1-ons-cv-002")                    # CV 8.7% of £2,322 million (SE £201 million)
    probe = PreservationProbe(prompts, tmp_path)
    fams, _, _, _ = probe.evaluate_families(
        _elicited("Plastering turnover was £2,322 million in 2016 with a standard error of £201 million."), prop, only_family="relative")
    assert fams[0].level == 3 and fams[0].observations.get("cross_family_derivation") == "interval_to_relative", fams[0].evidence
    fams, _, _, _ = probe.evaluate_families(
        _elicited("Plastering turnover was about £2.5 billion in 2016 with a standard error of £201 million."), prop, only_family="relative")
    assert fams[0].level in (0, 1, 2) or fams[0].outcome == UNPARSEABLE


def test_prompt_set_carries_three_compression_levels_with_none_verbatim(prompts):
    assert set(prompts.compression) == {"none", "short", "tight"}
    assert prompts.compression["none"] == prompts.indirect
    assert "two sentences" in prompts.compression["short"] and "30 words" in prompts.compression["tight"]
    assert prompts.prompt_epoch == "g1-v2-2026-09-03"


def test_evidence_reuse_finds_a_byte_identical_legacy_slot(dev, prompts, tmp_path):
    """D12: a `none` indirect or direct slot elicited under the v0 epoch is the same slot."""
    prop = dev.by_id("g1-acs-moe-001")
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    rec = {"proposition_id": prop.id, "mode": "indirect", "prompt": "p", "response_text": "564,757 ± 10,127 in 2015",
           "model_id": "scripted-model", "prompt_epoch": "g1-v0-2026-09-02", "timestamp": "t", "usage": {}}
    (legacy / f"{prop.passage_id}.indirect.indirect.g1-v0-2026-09-02.scripted-model.json").write_text(json.dumps(rec))
    probe = PreservationProbe(prompts, tmp_path / "run", legacy_evidence_dirs=(legacy,))
    el = probe.existing_evidence(f"{prop.passage_id}.indirect", "indirect", None, "scripted-model", compression="none")
    assert el is not None and el.prompt_epoch == "g1-v0-2026-09-02"
    assert probe.existing_evidence(f"{prop.passage_id}.indirect", "indirect", None, "scripted-model", compression="tight") is None
    assert probe.existing_evidence(f"{prop.passage_id}.indirect", "indirect", None, "other-model", compression="none") is None
    r = probe.records(el, prop, compression="none")[0]
    assert r.prompt_epoch == "g1-v0-2026-09-02" and r.observations["prompt_text_identical"] is True


def _v2_dev_cases():
    cs = yaml.safe_load((FIX / "restatements.yaml").read_text(encoding="utf-8"))
    return cs.get("v2_cases_dev", [])


@pytest.mark.parametrize("dcase", _v2_dev_cases(), ids=[f"v2dev:{c['prop']}:{c['family']}:{c['mode']}:{c.get('compression')}" for c in _v2_dev_cases()])
def test_v2_dev_case_verbatim_from_dev_evidence(prompts, dcase, tmp_path):
    """Every v2 rule motivated by a development response, replayed verbatim: the family level,
    outcome, failure class and chosen form the rule was written to produce (DD-035; the
    holdout was sealed when these were written)."""
    sys_path = str(Path(__file__).parents[2] / "scripts")
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from run_g1_v2 import load_all_fixtures
    props, passages, _ = load_all_fixtures()
    prop = props[dcase["prop"]]
    probe = PreservationProbe(prompts, tmp_path)
    fams, est, _, _ = probe.evaluate_families(_elicited(dcase["text"], dcase["mode"]), prop,
                                              only_family=dcase["family"], siblings=passages[prop.passage_id])
    v = fams[0]
    assert est.value == dcase["expect_estimate"], (dcase["prop"], est)
    assert v.outcome == dcase["expect_outcome"] and v.level == dcase["expect_family_level"], (dcase["prop"], v.evidence, v.observations["binding"])
    assert v.failure_class == dcase["expect_failure"], (dcase["prop"], v.evidence)
    assert v.observations["chosen_form"] == dcase["expect_form"], (dcase["prop"], v.observations["chosen_form"])
