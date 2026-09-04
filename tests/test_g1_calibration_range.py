"""The genuine-loss range, the stratum agreement table, and the disagreement selection rule
(task 2026-09-03_g1_calibration_rating_agreement, steps 2 and 3).

The range is the number this task exists to produce, and it is an extrapolation — the one
kind of number that looks authoritative and is easy to get quietly wrong. So the arithmetic
is pinned against a hand-computed case, and the two rules that decide what goes into it are
pinned separately:

* U answers are excluded from the rate and counted on their own — folding a "cannot classify"
  into either bound would make the range narrower than the evidence supports;
* only queue strata contribute — a record the scorer put at L3+ was never a candidate loss,
  so it cannot become one by extrapolation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))

import register_g1_calibration_results as reg  # noqa: E402
import g1_calibration_disagreements as dis  # noqa: E402


def _key(entries):
    """entries: [(sample_id, scorer_level, reviewer_verdict)]"""
    return {"rater": "claude-fable-5-1",
            "key": {sid: {"file": "assessment/results/g1_v2_pooled_opus_reviewed.json", "index": i,
                          "split": "pooled_opus", "target": f"prop-{i}", "family": "interval",
                          "mode": "indirect", "compression_level": "none",
                          "scorer_level": sc, "reviewer_verdict": rv,
                          "evidence_path": f"evidence/{sid}.json"}
                    for i, (sid, sc, rv) in enumerate(entries)}}


def _labels(pairs):
    return {sid: {"level": lv, "note": ""} for sid, lv in pairs}


# ---------------------------------------------------------------------------
# stratum table
# ---------------------------------------------------------------------------

def test_stratum_table_counts_agreement_U_and_the_genuine_rate():
    key = _key([("C001", "L1", "genuine"), ("C002", "L1", "genuine"),
                ("C003", "L1", "genuine"), ("C004", "L1", "genuine")])
    # rater: two confirm L1, one reads it at L4 (a parser miss), one cannot classify
    labels = _labels([("C001", "L1"), ("C002", "L1"), ("C003", "L4"), ("C004", "U")])
    row = reg.stratum_table(labels, key)["L1|genuine"]
    assert row["n_sampled"] == 4 and row["n_rated"] == 4 and row["n_U"] == 1
    assert row["raw_agreement_with_scorer"] == pytest.approx(0.5)      # 2 of 4 rated hit L1 exactly
    assert row["rater_below_L3"] == 2 and row["rater_L3plus"] == 1
    assert row["rater_genuine_rate"] == pytest.approx(2 / 3)           # U excluded from the rate
    # the reviewer said genuine on all four; the rater implies parser_miss only for C003
    assert row["reviewer_n"] == 3 and row["reviewer_agree"] == 2
    assert row["raw_agreement_with_reviewer"] == pytest.approx(2 / 3)


def test_unrated_records_are_counted_as_sampled_but_never_as_agreement():
    key = _key([("C001", "L0", "genuine"), ("C002", "L0", "genuine")])
    row = reg.stratum_table(_labels([("C001", "L0")]), key)["L0|genuine"]
    assert row["n_sampled"] == 2 and row["n_rated"] == 1
    assert row["raw_agreement_with_scorer"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# the range
# ---------------------------------------------------------------------------

def test_range_is_the_weighted_sum_over_queue_strata_only():
    rows = {"L1|genuine": {"n_sampled": 4, "n_rated": 4, "n_U": 0, "rater_below_L3": 3,
                           "rater_L3plus": 1, "rater_genuine_rate": 0.75},
            "L0|parser_miss": {"n_sampled": 4, "n_rated": 4, "n_U": 0, "rater_below_L3": 1,
                               "rater_L3plus": 3, "rater_genuine_rate": 0.25},
            "L4|not_in_queue": {"n_sampled": 10, "n_rated": 10, "n_U": 0, "rater_below_L3": 2,
                                "rater_L3plus": 8, "rater_genuine_rate": 0.2}}
    weights = {("L1", "genuine"): 100, ("L0", "parser_miss"): 40, ("L4", "not_in_queue"): 300}
    out = reg.range_block(rows, weights, {"queue": 140, "genuine": 90, "parser_misses": 50})
    # 100*0.75 + 40*0.25 = 85; the 300 L4 records cannot become losses by extrapolation
    assert out["rater_implied_genuine_losses"] == 85
    assert out["queue_population"] == 140
    assert out["scorer_genuine_losses"] == 140 and out["reviewer_genuine_losses"] == 90
    assert set(out["strata"]) == {"L1|genuine", "L0|parser_miss"}
    assert out["strata_without_a_rate"] == []


def test_U_is_extrapolated_separately_and_never_folded_into_the_genuine_count():
    rows = {"L1|genuine": {"n_sampled": 4, "n_rated": 4, "n_U": 1, "rater_below_L3": 3,
                           "rater_L3plus": 0, "rater_genuine_rate": 1.0}}
    weights = {("L1", "genuine"): 100}
    out = reg.range_block(rows, weights, {"queue": 100, "genuine": 80, "parser_misses": 20})
    assert out["rater_implied_genuine_losses"] == 100     # rate is over the 3 non-U ratings
    assert out["rater_implied_U"] == pytest.approx(25.0)  # 1 of 4 rated, applied to 100
    assert "stratum homogeneity" in out["extrapolation"]


def test_a_queue_stratum_with_no_usable_rating_is_named_not_silently_zero():
    rows = {"L1|genuine": {"n_sampled": 3, "n_rated": 0, "n_U": 0, "rater_below_L3": 0,
                           "rater_L3plus": 0, "rater_genuine_rate": None}}
    weights = {("L1", "genuine"): 100, ("L2", "genuine"): 50}
    out = reg.range_block(rows, weights, {"queue": 150, "genuine": 100, "parser_misses": 50})
    assert out["rater_implied_genuine_losses"] == 0
    assert sorted(out["strata_without_a_rate"]) == ["L1|genuine", "L2|genuine"]


def test_pooled_weights_and_reviewer_counts_come_from_the_real_file():
    """The extrapolation target is the pooled Opus grid; the weights must be its own strata,
    not the sheet's (which mixes in the control arm)."""
    weights = reg.pooled_strata()
    assert sum(weights.values()) == 650
    queue = sum(n for (_, vd), n in weights.items() if vd != "not_in_queue")
    counts = reg.reviewer_counts()
    assert queue == counts["queue"] == 232
    assert counts["genuine"] == 178 and counts["parser_misses"] == 54


# ---------------------------------------------------------------------------
# the disagreement rule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scorer,verdict,expected", [
    ("L1", "genuine", "L1"),               # the reviewer stood by the scorer
    ("L1", "parser_miss", "L3"),           # the qualifier was there: it should have scored preserved
    ("unparseable", "parser_miss", "L3"),
    ("unparseable", "genuine", "unparseable"),
    ("L4", "not_in_queue", "L4"),          # never judged; the scorer's level stands in
])
def test_reviewer_verdict_maps_to_a_level(scorer, verdict, expected):
    assert dis.reviewer_level(scorer, verdict) == expected


def test_unparseable_and_U_sit_below_L0():
    assert dis.position("unparseable") == -1 and dis.position("U") == -1
    assert dis.position("L0") == 0 and dis.position("L4") == 4


def test_disagreement_selection_lists_wide_gaps_and_every_U():
    key = _key([("C001", "L1", "genuine"),        # rater L1 -> gap 0, not listed
                ("C002", "L1", "genuine"),        # rater L4 -> gap 3, listed
                ("C003", "L1", "parser_miss"),    # reviewer L3, rater L4 -> gap 1, not listed
                ("C004", "L4", "not_in_queue"),   # rater L2 -> gap 2, listed
                ("C005", "L2", "genuine"),        # rater U -> listed as a U
                ("C006", "unparseable", "genuine")])  # reviewer level unparseable -> listed as a U
    labels = _labels([("C001", "L1"), ("C002", "L4"), ("C003", "L4"), ("C004", "L2"),
                      ("C005", "U"), ("C006", "L4")])
    listed = dis.rows(labels, key, {}, Path("/nonexistent"), distance=2)
    # C006 (rater L4 against an `unparseable` reviewer level) is the widest; U rows still carry
    # a numeric gap for ordering, and are flagged `gave_u` so the table prints U, not a number.
    assert [r["sample_id"] for r in listed] == ["C006", "C002", "C005", "C004"]
    assert {r["sample_id"]: r["gave_u"] for r in listed} == {
        "C006": True, "C002": False, "C005": True, "C004": False}
    assert [r["gap"] for r in listed] == [5, 3, 3, 2]          # widest gap first


def test_an_unrated_record_is_not_a_disagreement():
    key = _key([("C001", "L1", "genuine")])
    assert dis.rows({"C001": {"level": None}}, key, {}, Path("/nonexistent"), 2) == []


def test_rendered_list_states_the_mapping_and_proposes_nothing():
    key = _key([("C001", "L1", "genuine")])
    listed = dis.rows(_labels([("C001", "L4")]), key, {"C001": "the block"}, Path("/nonexistent"), 2)
    text = dis.render(listed, key, n_rated=1, distance=2, reviewer_notes={})
    assert "`parser_miss` → L3" in text and "`not_in_queue` → the" in text
    assert "Nothing in this file proposes a resolution" in text
    assert "the block" in text
