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


def _verdict_for(probe, prop, case):
    verdicts, est, _ = probe.evaluate_qualifiers(_elicited(case["text"]), prop, only_class=case["class"])
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


def test_case(dev, cases, prompts, case, tmp_path):
    probe = PreservationProbe(prompts, tmp_path)
    prop = _prop(dev, cases, case["prop"])
    v, est = _verdict_for(probe, prop, case)
    assert est.value == case["expect_estimate"], (case["text"], v.evidence, v.observations.get("estimate"))
    if case.get("expect_outcome") == UNPARSEABLE:
        assert v.outcome == UNPARSEABLE and v.level is None and v.score is None, (case["text"], v.evidence)
        return
    level = case.get("expect_level_override", case["expect_level"])
    failure = case.get("expect_failure_override", case.get("expect_failure"))
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
    # The readiness floor (D5): parse coverage on the cases a human labelled parseable.
    labelled = [c for c in cases["cases"] if c.get("expect_outcome") != UNPARSEABLE]
    parsed = [c for c, v in _all_verdicts(dev, cases, prompts, tmp_path)
              if c.get("expect_outcome") != UNPARSEABLE and v.outcome != UNPARSEABLE]
    coverage = len(parsed) / len(labelled)
    assert coverage >= 0.90, f"parse coverage {coverage:.3f} < 0.90 — probe not ready (D5)"


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
    assert path.exists() and path.name == "g1-acs-moe-001.indirect.g1-v0-2026-09-02.scripted-model.json"
    record = json.loads(path.read_text())
    assert record["prompt"] == el.prompt and record["response_text"] == text
    assert record["prompt_epoch"] == "g1-v0-2026-09-02" and record["model_id"] == "scripted-model"
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
    assert {v["qualifier_class"] for v in obs["per_qualifier"]} == {"MOE", "VINTAGE"}
    out, _, _ = probe.evaluate(_elicited("Colorado had 564,757 one-person households in 2015; a margin of error is published."), prop)
    assert out == UNPARSEABLE


def test_record_without_epoch_or_model_is_invalid():
    with pytest.raises(ValueError):
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=4, failure_class=None, estimate_status="exact",
                   model_id="", prompt_epoch="e", evidence="", timestamp="t", evidence_path="x")
    with pytest.raises(ValueError):
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=4, failure_class=None, estimate_status="exact",
                   model_id="m", prompt_epoch=" ", evidence="", timestamp="t", evidence_path="x")
    with pytest.raises(ValueError):                # score must follow from level
        EvalResult(probe_id="g1_preservation", target="p", qualifier_class="MOE", mode="indirect",
                   outcome="pass", score=Score.PASS, level=1, failure_class=None, estimate_status="exact",
                   model_id="m", prompt_epoch="e", evidence="", timestamp="t", evidence_path="x")


def test_prompt_config_requires_epoch_and_context_placeholder(tmp_path):
    bad = tmp_path / "p.toml"
    bad.write_text('prompt_epoch = ""\n[indirect]\ntemplate="x {context_passage}"\n[direct]\ntemplate="y {context_passage}"\n[qualifier_plain]\n')
    with pytest.raises(Exception):
        load_prompts(bad)
