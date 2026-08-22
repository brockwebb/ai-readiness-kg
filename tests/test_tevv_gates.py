"""TEVV gate evaluation (scripts/run_baseline_gates.py, task 2026-08-22_kernel_tevv)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import run_baseline_gates as g  # noqa: E402

CFG = {"checks": [
    {"check_id": "stability_kappa_pooled", "comparator": "gte", "threshold": 0.61},
    {"check_id": "stability_kappa_per_type_min", "comparator": "gte", "threshold": 0.61},
    {"check_id": "stability_jaccard_pooled", "comparator": "gte", "threshold": 0.70},
    {"check_id": "faithfulness_precision_pooled", "comparator": "gte", "threshold": 0.90},
    {"check_id": "faithfulness_precision_stratum_min", "comparator": "gte", "threshold": 0.85},
    {"check_id": "grade_platform_official_precision", "comparator": "gte", "threshold": 0.90, "phase_stop_below": 0.70},
    {"check_id": "grade_peer_reviewed_precision", "comparator": "gte", "threshold": 0.90},
]}


def test_faithfulness_precision_pooled_and_per_stratum_ignores_errors():
    j = [{"stratum": "A", "entailed": True}, {"stratum": "A", "entailed": False},
         {"stratum": "B", "entailed": True}, {"stratum": "B", "entailed": None}]
    f = g.faithfulness_precision(j)
    assert f["pooled"] == 2 / 3 and f["per_stratum"] == {"A": 0.5, "B": 1.0} and f["errors"] == 1


def test_evaluate_tevv_gates_realized_values_and_verdicts():
    stab = {"pooled": {"kappa_all_items_pooled": 0.7, "jaccard_spans_mean": 0.65,
                       "per_type": {"Concept": {"kappa": 0.5}, "Claim": {"kappa": 0.9}}}}
    judg = [{"stratum": "A", "entailed": True}] * 9 + [{"stratum": "B", "entailed": False}]
    cal = {"platform_official": {"precision": 0.65}, "peer_reviewed_experiment": {"precision": 1.0}}
    res = {r["check_id"]: r for r in g.evaluate_tevv_gates(CFG, stab, judg, cal)}
    assert res["stability_kappa_pooled"]["passed"] is True
    assert res["stability_kappa_per_type_min"]["value"] == 0.5 and res["stability_kappa_per_type_min"]["passed"] is False
    assert res["stability_jaccard_pooled"]["passed"] is False
    assert res["faithfulness_precision_pooled"]["value"] == 0.9 and res["faithfulness_precision_pooled"]["passed"] is True
    assert res["faithfulness_precision_stratum_min"]["value"] == 0.0
    assert res["grade_platform_official_precision"]["phase_stop_triggered"] is True
    assert res["grade_peer_reviewed_precision"]["passed"] is True


def test_missing_inputs_are_not_evaluated_never_pass():
    res = g.evaluate_tevv_gates(CFG, None, None, None)
    assert all(r["passed"] is None and r["value"] is None for r in res)
