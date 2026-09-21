"""The punctuation fold in scripts/measure_grounding_punctuation.py is measurement-only: it must
flip curly-quote/dash misses and must not touch kg.extraction.grounding.normalize."""
import importlib.util
from pathlib import Path

from kg.extraction import grounding

_spec = importlib.util.spec_from_file_location(
    "mgp", Path(__file__).resolve().parent.parent / "scripts" / "measure_grounding_punctuation.py")
mgp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mgp)


def test_curly_apostrophe_flips_under_fold_but_not_under_live_gate():
    src = "the firm’s capability"
    span = "the firm's capability"
    assert not grounding.is_grounded(span, src)      # live gate unchanged: the miss is real today
    assert mgp.grounded_folded(span, src)


def test_em_dash_and_nbsp_fold():
    assert mgp.grounded_folded("a - b c", "a — b c")


def test_fold_does_not_ground_a_real_miss():
    assert not mgp.grounded_folded("something else entirely", "the firm’s capability")
