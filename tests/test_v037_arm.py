"""v0.3.7 ARM WIRING (chunked_pilot ADDENDUM-03 §3).

ADDENDUM-03 §1 built the contract as modules with unit tests. This file tests that the
production path actually USES them: the arm's shard/raw-dir/emission come from the profile,
`parse_chunk_raw` derives spans from the source before the parser sees them, an unlocatable
anchor is quarantined as `anchor_not_located` rather than as "missing grounding_span", type
conflicts are excluded from the judged stratum, and the pre-registered admitted-yield floor
fires.

Every test below enters through the real entrypoint. That is the whole point: the recurring
M2 failure mode in this project is a guard test that calls a helper directly and therefore
measures the helper rather than the guard. A test here that passes with the wiring deleted is
a broken test.

Zero model spend: nothing here calls model_stub.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg.extraction import anchors, merge  # noqa: E402

CHUNK = ("AIDRIN is a data readiness tool.\n"
         "It scores six dimensions on a 0-1 scale. The tool was released in 2024.\n"
         "Other systems exist too.")


@pytest.fixture
def cp():
    """The pilot script with its arm globals restored after each test — they are module
    state by design (so every function reads them at call time) and a leaked binding would
    silently point a later test at another arm's shard."""
    import chunked_pilot as mod
    keep = {k: getattr(mod, k) for k in
            ("PROFILE", "RUN_ID", "JUDGE_RUN_ID", "SHARD_NO", "TAG", "RAW_DIR",
             "CORPUS_EPOCH", "EMISSION", "ARM_MODEL")}
    yield mod
    for k, v in keep.items():
        setattr(mod, k, v)


# ---------------------------------------------------------------- 1. arm selection

def test_apply_arm_binds_every_arm_scoped_global_from_the_profile(cp):
    """A second arm on a second shard must not inherit the first arm's shard, raw dir or
    emission contract: two experiments interleaved on one append-only log cannot be
    separated afterwards."""
    cp.apply_arm("v0_3_7", "claude-haiku-4-5-20251001", "pilot_v037_arm_a_haiku")
    assert (cp.SHARD_NO, cp.TAG) == (17, "v0_3_7")
    assert cp.RAW_DIR == REPO / "events/raw/v0_3_7"
    assert cp.EMISSION == "anchor"
    assert cp.RUN_ID == "pilot_v037_arm_a_haiku"
    assert cp.JUDGE_RUN_ID == "pilot_v037_arm_a_haiku_judge"
    assert cp.model_cfg()["model_id"] == "claude-haiku-4-5-20251001"


def test_banked_arm_still_binds_to_its_own_shard(cp):
    """The v0.3.5 comparator is banked material; the arm switch must leave it exactly where
    it was or the comparison silently changes."""
    cp.apply_arm("chunked_v035", None, None)
    assert (cp.SHARD_NO, cp.TAG, cp.EMISSION) == (16, "chunked_v035", "verbatim")
    assert cp.ARM_MODEL is None


def test_unknown_profile_and_unknown_emission_contract_are_refused(cp, tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        cp.apply_arm("no_such_profile", None, None)
    monkeypatch.setattr(cp, "profile_block",
                        lambda p: {"batch": 99, "raw_dir": "x", "corpus_epoch": "y",
                                   "emission_contract": "telepathy"})
    with pytest.raises(SystemExit) as exc:
        cp.apply_arm("chunked_v035", None, None)
    assert "telepathy" in str(exc.value)


def test_extract_on_a_second_arm_refuses_without_its_own_run_id(cp, monkeypatch):
    """Billing Arm A's calls to the banked arm's run id would charge one experiment's cost
    to another's ceiling and report it under the wrong name."""
    monkeypatch.setattr(sys, "argv",
                        ["chunked_pilot.py", "--phase", "extract", "--profile", "v0_3_7",
                         "--ceiling-tokens", "1000"])
    with pytest.raises(SystemExit) as exc:
        cp.main()
    assert "--run-id is required" in str(exc.value)


# ---------------------------------------------------------------- 2. the contract is WIRED

def _envelope():
    # No `document_id`: the harness owns provenance and injects it (pipeline strips any the
    # model emits), so a test envelope carrying one exercises the warning path, not the arm.
    return {"concepts": [{"id": "c1", "name": "data readiness",
                          "anchor": "data readiness tool"}]}


def test_parse_chunk_raw_derives_the_span_from_the_source_under_the_anchor_arm(cp):
    """Entry through the real parse path, not `apply_anchor_contract` directly."""
    cp.apply_arm("v0_3_7", None, None)
    raw = {"raw_result": json.dumps(_envelope())}
    result, _, _ = cp.parse_chunk_raw("doc-1", raw, CHUNK, CHUNK)
    assert [n["item"]["grounding_span"] for n in result.nodes] == \
        ["AIDRIN is a data readiness tool."]


def test_the_banked_arm_does_not_get_the_anchor_contract(cp):
    """MUTATION-STYLE CONTROL for the test above: under `verbatim` the same envelope has no
    span at all and is quarantined for that. If this passed under both arms, the test above
    would be measuring the parser, not the wiring."""
    cp.apply_arm("chunked_v035", None, None)
    raw = {"raw_result": json.dumps(_envelope())}
    result, _, _ = cp.parse_chunk_raw("doc-1", raw, CHUNK, CHUNK)
    assert result.nodes == []
    assert cp.reason_class(result.quarantined[0]["reason"]) == "missing_span"


def test_unlocatable_anchor_is_quarantined_as_anchor_not_located_not_as_missing_span(cp):
    """The erratum split these causes and ADDENDUM-03 §3 requires them reported apart. An
    item dropped for a bad anchor must NOT be filed under the parser's `missing_span`, which
    is a true statement naming the wrong cause."""
    cp.apply_arm("v0_3_7", None, None)
    # "tool" occurs twice in CHUNK ("readiness tool." and "The tool was"), so it violates
    # the contract's shortest-UNIQUE-substring rule and must be dropped, not disambiguated.
    env = {"concepts": [{"id": "c1", "name": "ghost", "anchor": "a phrase that is absent"},
                        {"id": "c2", "name": "twice", "anchor": "tool"}]}
    result, _, _ = cp.parse_chunk_raw("doc-1", {"raw_result": json.dumps(env)}, CHUNK, CHUNK)
    classes = [cp.reason_class(q["reason"]) for q in result.quarantined]
    assert classes == ["anchor_not_located", "anchor_not_located"]
    assert result.counts()["quarantined"] == 2       # counted, not silently dropped
    assert "ambiguous" in result.quarantined[1]["reason"]


def test_instrument_attribute_anchors_become_per_attribute_spans_on_the_parse_path(cp):
    """The per-attribute rule is the fix for the fabricated `method` values the probe found
    (F 0.25/0.17). Under the anchor contract it only survives if `attribute_anchors` are
    turned into the `grounding_spans` map the parser reads — otherwise every Instrument
    attribute is nulled at parse and the stratum is judged on names alone."""
    cp.apply_arm("v0_3_7", None, None)
    env = {"instruments": [{"id": "i1", "name": "AIDRIN", "anchor": "AIDRIN",
                            "method": "scores six dimensions", "year": "2024",
                            "attribute_anchors": {"method": "six dimensions",
                                                  "year": "released in 2024"}}]}
    result, _, _ = cp.parse_chunk_raw("doc-1", {"raw_result": json.dumps(env)}, CHUNK, CHUNK)
    assert [n["type"] for n in result.nodes] == ["Instrument"]
    item = result.nodes[0]["item"]
    assert item["method"] == "scores six dimensions"   # NOT nulled
    assert item["year"] == "2024"
    assert item["grounding_spans"]["method"] == "It scores six dimensions on a 0-1 scale."
    assert "nulled_at_parse" not in item


def test_an_instrument_attribute_with_no_anchor_is_nulled_not_kept(cp):
    """CONTROL for the test above: the rule must still bite. An attribute the model filled
    from background knowledge carries no anchor, so it gets no span and is nulled — the node
    itself stays admitted (attribute-level, never a node quarantine)."""
    cp.apply_arm("v0_3_7", None, None)
    env = {"instruments": [{"id": "i1", "name": "AIDRIN", "anchor": "AIDRIN",
                            "method": "fielded every 2 years", "attribute_anchors": {}}]}
    result, _, _ = cp.parse_chunk_raw("doc-1", {"raw_result": json.dumps(env)}, CHUNK, CHUNK)
    assert result.nodes[0]["item"]["method"] is None
    assert result.nodes[0]["item"]["nulled_at_parse"] == ["method"]


def test_reason_class_never_sweeps_an_unknown_failure_into_a_bucket(cp):
    assert cp.reason_class("something nobody has seen").startswith("other:")
    assert cp.reason_class("") == "other:unstated"


# ---------------------------------------------------------------- 3. type conflicts

def test_type_conflict_is_excluded_from_the_judged_stratum(cp):
    """merge.py rule 3: pooling an entity whose type is unresolved would put the conflict
    into the denominator of a pre-registered gate."""
    cp.apply_arm("v0_3_7", None, None)
    conflict = merge.reconcile_type([{"type": "Instrument", "chunk_id": "a"},
                                     {"type": "Concept", "chunk_id": "b"}])
    assert conflict["rule"] == merge.TYPE_CONFLICT
    decisions = {"doc-1": {merge.normalized_key("AIDRIN"): conflict}}
    assert cp.resolved_type(decisions, "doc-1", "AIDRIN", "Instrument") is None
    # and an entity the merge RESOLVED to Instrument is pooled as one even where a single
    # chunk typed it Concept — the whole point of reconciling at merge.
    resolved = merge.reconcile_type([
        {"type": "Instrument", "chunk_id": "a", "instrument_evidence": True},
        {"type": "Concept", "chunk_id": "b"}, {"type": "Concept", "chunk_id": "c"}])
    decisions = {"doc-1": {merge.normalized_key("AIDRIN"): resolved}}
    assert cp.resolved_type(decisions, "doc-1", "AIDRIN", "Concept") == "Instrument"


def test_instrument_evidence_reads_the_prompt_s_own_positive_criterion(cp):
    """Evidence is an attribute that SURVIVED the per-attribute span rule. An Instrument
    whose attributes were all nulled at parse carries no evidence, so it cannot outvote."""
    assert cp.instrument_evidence({"name": "AIDRIN", "method": "scores six dimensions"})
    assert not cp.instrument_evidence({"name": "AIDRIN", "method": None, "owner": None,
                                       "year": None, "nulled_at_parse": ["method"]})


# ---------------------------------------------------------------- 4. the yield floor

def test_admitted_yield_floor_fires_below_the_pre_registered_ratio(cp, monkeypatch):
    """Pre-registered 2026-08-29 before Arm A ran: an arm that clears the faithfulness gate
    by extracting almost nothing reports UNDER-EXTRACTION, not PASS."""
    cp.apply_arm("v0_3_7", None, None)
    base = {f"c{i}": {"admitted": 100, "doc_id": "d", "quarantined": 0, "reasons": {},
                      "output_tokens": 0, "nodes": 0, "edges": 0} for i in range(10)}
    low = {f"c{i}": {**base[f"c{i}"], "admitted": 59} for i in range(10)}
    monkeypatch.setattr(cp, "chunk_yield",
                        lambda tag: low if tag == cp.TAG else base)
    y = cp.yield_comparison()
    assert y["shared_chunks"] == 10 and y["ratio"] == 0.59
    assert y["under_extraction"] is True
    ok = {f"c{i}": {**base[f"c{i}"], "admitted": 61} for i in range(10)}
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: ok if tag == cp.TAG else base)
    assert cp.yield_comparison()["under_extraction"] is False


def test_yield_is_compared_only_on_chunks_BOTH_arms_cover(cp, monkeypatch):
    """The v0.3.5 arm banked 44 of 128 chunks. Dividing this arm's items over 128 by the
    baseline's over 44 would compare two different denominators and manufacture a verdict."""
    cp.apply_arm("v0_3_7", None, None)
    row = lambda n: {"admitted": n, "doc_id": "d", "quarantined": 0, "reasons": {},
                     "output_tokens": 0, "nodes": 0, "edges": 0}
    base = {"c1": row(100), "c2": row(100)}
    arm = {"c1": row(100), "c2": row(100), "c3": row(0), "c4": row(0)}
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: arm if tag == cp.TAG else base)
    y = cp.yield_comparison()
    assert y["shared_chunks"] == 2 and y["ratio"] == 1.0 and y["under_extraction"] is False
    assert y["arm_density_all_chunks"] == 50.0     # reported, but not the comparator
