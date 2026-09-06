"""The ER gold scorer, tested on a synthetic sheet with known answers (task §5).

Written before the real sheet exists, and that ordering is the point: a scorer authored after
its inputs are visible is a scorer shaped by them. Every number below is hand-computable.

The metrics are the record-linkage literature's, not the CQ harness's — Menestrina, Whang &
Garcia-Molina (2010) PVLDB 3(1), Christen (2012) ch. 7 — because the prior task's `flip`
criterion was unsatisfiable under DD-020 (DD-045 §1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import score_er_gold as sg  # noqa: E402


def _sheet(rows) -> str:
    """rows: [(pair_id, verdict_text)] rendered in the sheet's own shape."""
    out = ["# synthetic\n"]
    for pid, v in rows:
        out.append(f"### {pid}\n")
        out.append(f"**{pid} — verdict (same / different / uncertain):** {v}\n")
        out.append(f"**{pid} — note:** \n")
    return "\n".join(out)


def _key(pairs, weights) -> dict:
    return {"stratum_weights": weights, "pairs": pairs}


def _pair(pid, stratum, sysmatch, a, b):
    return {"pair_id": pid, "stratum": stratum, "system_match": sysmatch,
            "node_a": a, "node_b": b}


# ------------------------------------------------------------------ parsing
def test_an_unfilled_blank_is_not_a_verdict():
    """A blank must parse as None. Counting it as agreement with the pipeline would let an
    untouched sheet report perfect precision."""
    got = sg.parse_sheet(_sheet([("P001", "______"), ("P002", "same")]))
    assert got["P001"]["verdict"] is None
    assert got["P002"]["verdict"] == "same"


def test_a_sheet_in_the_wrong_shape_fails_loud():
    with pytest.raises(sg.SheetError):
        sg.parse_sheet("# nothing here\n")


def test_a_key_pair_missing_from_the_sheet_fails_loud(tmp_path):
    sheet = tmp_path / "s.md"
    sheet.write_text(_sheet([("P001", "same")]), encoding="utf-8")
    key = tmp_path / "k.json"
    key.write_text(json.dumps(_key(
        [_pair("P001", "A", True, "n1", "n2"), _pair("P002", "A", True, "n3", "n4")],
        {"A": 1.0})), encoding="utf-8")
    with pytest.raises(sg.SheetError):
        sg.load(sheet, key)


# ------------------------------------------------------------------ the rates
def test_precision_and_recall_on_a_hand_computable_case():
    """One stratum, weight 1. 3 system matches of which 2 are gold-same -> precision 2/3.
    Gold-same total is 4 (2 matched, 2 the system missed) -> recall 2/4."""
    pairs = [
        {**_pair("P001", "A", True, "a", "b"), "gold": "same", "weight": 1.0},
        {**_pair("P002", "A", True, "c", "d"), "gold": "same", "weight": 1.0},
        {**_pair("P003", "A", True, "e", "f"), "gold": "different", "weight": 1.0},
        {**_pair("P004", "A", False, "g", "h"), "gold": "same", "weight": 1.0},
        {**_pair("P005", "A", False, "i", "j"), "gold": "same", "weight": 1.0},
        {**_pair("P006", "A", False, "k", "l"), "gold": "different", "weight": 1.0},
    ]
    r = sg.score(pairs)
    assert r["precision"] == pytest.approx(2 / 3)
    assert r["recall"] == pytest.approx(0.5)
    assert r["by_stratum"]["A"] == {**r["by_stratum"]["A"], "tp": 2, "fp": 1, "fn": 2, "tn": 1}


def test_uncertain_and_unfilled_rows_are_excluded_rather_than_counted_either_way():
    """Putting the operator's hesitation on one side of a threshold would be the scorer
    deciding what the sheet exists to ask."""
    pairs = [
        {**_pair("P001", "A", True, "a", "b"), "gold": "same", "weight": 1.0},
        {**_pair("P002", "A", True, "c", "d"), "gold": "uncertain", "weight": 1.0},
        {**_pair("P003", "A", True, "e", "f"), "gold": None, "weight": 1.0},
    ]
    r = sg.score(pairs)
    assert r["pairs_on_sheet"] == 3
    assert r["pairs_scored"] == 1
    assert r["pairs_uncertain_or_unfilled"] == 2
    assert r["precision"] == 1.0


def test_stratum_weights_change_the_population_estimate():
    """Two strata sampled equally out of very different populations. Unweighted precision is
    2/4 = 0.5; weighting the clean stratum 9:1 must pull the estimate up. This is the whole
    reason the sheet is stratified and the reason an unweighted pooled rate estimates nothing."""
    pairs = [
        {**_pair("P001", "BIG", True, "a", "b"), "gold": "same", "weight": 9.0},
        {**_pair("P002", "BIG", True, "c", "d"), "gold": "same", "weight": 9.0},
        {**_pair("P003", "SMALL", True, "e", "f"), "gold": "different", "weight": 1.0},
        {**_pair("P004", "SMALL", True, "g", "h"), "gold": "different", "weight": 1.0},
    ]
    r = sg.score(pairs)
    assert r["precision"] == pytest.approx(18 / 20)          # (9*2) / (9*2 + 1*2)
    assert r["by_stratum"]["BIG"]["precision"] == 1.0
    assert r["by_stratum"]["SMALL"]["precision"] == 0.0
    # and the interval is computed on an EFFECTIVE size smaller than the raw 4
    assert 0 < r["precision_n_eff"] < 4


def test_the_interval_stays_inside_zero_one_at_perfect_precision():
    """Where a precision figure is expected to sit is exactly where the normal approximation
    degenerates; Wilson does not."""
    pairs = [{**_pair(f"P{i:03d}", "A", True, f"a{i}", f"b{i}"), "gold": "same", "weight": 1.0}
             for i in range(20)]
    r = sg.score(pairs)
    assert r["precision"] == 1.0
    lo, hi = r["precision_ci"]
    assert 0.0 < lo < 1.0 and hi == 1.0


def test_the_thresholds_are_the_dd_045_ones_and_are_asymmetric():
    assert sg.PRECISION_FLOOR == 0.95
    assert sg.RECALL_FLOOR == 0.80
    assert sg.PRECISION_FLOOR > sg.RECALL_FLOOR


def test_a_perfect_pipeline_passes_and_a_merge_happy_one_fails_on_precision():
    good = [{**_pair(f"P{i:03d}", "A", True, f"a{i}", f"b{i}"), "gold": "same", "weight": 1.0}
            for i in range(20)]
    r = sg.score(good)
    assert r["passes_precision"] and r["passes_recall"]
    bad = good[:10] + [{**_pair(f"Q{i:03d}", "A", True, f"c{i}", f"d{i}"),
                        "gold": "different", "weight": 1.0} for i in range(10)]
    r2 = sg.score(bad)
    assert r2["precision"] == 0.5 and not r2["passes_precision"]


def test_cluster_f1_is_one_when_the_system_reproduces_the_gold_clusters():
    """a~b~c is one gold cluster of three; d,e are singletons that must NOT be merged."""
    pairs = [
        {**_pair("P001", "A", True, "a", "b"), "gold": "same", "weight": 1.0},
        {**_pair("P002", "A", True, "b", "c"), "gold": "same", "weight": 1.0},
        {**_pair("P003", "A", False, "d", "e"), "gold": "different", "weight": 1.0},
    ]
    r = sg.score(pairs)
    assert r["cluster_f1"] == 1.0


def test_cluster_f1_falls_when_the_system_over_merges():
    pairs = [
        {**_pair("P001", "A", True, "a", "b"), "gold": "same", "weight": 1.0},
        {**_pair("P002", "A", True, "b", "c"), "gold": "different", "weight": 1.0},
    ]
    r = sg.score(pairs)
    assert r["cluster_f1"] < 1.0


# ------------------------------------------------------------------ end to end
def test_a_synthetic_filled_sheet_scores_end_to_end(tmp_path):
    rows, pairs = [], []
    for i in range(10):                       # stratum A: system says match, gold agrees
        rows.append((f"P{i:03d}", "same"))
        pairs.append(_pair(f"P{i:03d}", "A", True, f"a{i}", f"b{i}"))
    for i in range(10, 20):                   # stratum B: system says no match, gold agrees
        rows.append((f"P{i:03d}", "different"))
        pairs.append(_pair(f"P{i:03d}", "B", False, f"a{i}", f"b{i}"))
    sheet = tmp_path / "s.md"
    sheet.write_text(_sheet(rows), encoding="utf-8")
    key = tmp_path / "k.json"
    key.write_text(json.dumps(_key(pairs, {"A": 2.0, "B": 5.0})), encoding="utf-8")

    r = sg.score(sg.load(sheet, key))
    assert r["pairs_scored"] == 20
    assert r["precision"] == 1.0 and r["recall"] == 1.0
    assert r["passes_precision"] and r["passes_recall"]
