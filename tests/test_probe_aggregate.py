"""Probe aggregation (scripts/probe_aggregate.py): Wilson CI, MAP class, decision-rule edges."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import probe_aggregate as pa  # noqa: E402


def test_wilson_known_values():
    p, lo, hi = pa.wilson(0, 50)
    assert p == 0 and lo == 0.0 and hi == pytest.approx(0.0713, abs=1e-3)
    p, lo, hi = pa.wilson(10, 100)
    assert lo == pytest.approx(0.0552, abs=1e-3) and hi == pytest.approx(0.1744, abs=1e-3)
    assert pa.wilson(0, 0) == (None, None, None)


def test_map_class_majority_then_confidence_tiebreak():
    rows = [{"label": "not_entailed", "class": "fabrication", "confidence": 0.9},
            {"label": "not_entailed", "class": "span_truncated", "confidence": 0.6},
            {"label": "entailed", "class": None, "confidence": 0.8}]
    assert pa.map_class(rows) == "fabrication"        # tie 1-1 -> higher confidence
    rows.append({"label": "not_entailed", "class": "span_truncated", "confidence": 0.5})
    assert pa.map_class(rows) == "span_truncated"     # 2-1 majority
    assert pa.map_class([{"label": "entailed", "class": None, "confidence": 1}]) is None


def test_dawid_skene_recovers_obvious_truth():
    rows = []
    for i in range(30):
        truth = "entailed" if i % 3 else "not_entailed"
        rows.append({"fact_id": f"f{i}", "rater": "good", "label": truth})
        rows.append({"fact_id": f"f{i}", "rater": "good2", "label": truth})
        rows.append({"fact_id": f"f{i}", "rater": "noisy", "label": truth if i % 5 else ("not_entailed" if truth == "entailed" else "entailed")})
    post, conf, method = pa.dawid_skene(rows)
    assert all((post[f"f{i}"] >= 0.5) == bool(i % 3) for i in range(30))
    assert method
