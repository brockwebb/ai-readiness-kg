"""Stratified allocation for the blind calibration sheet (task
2026-09-03_g1_freeze_calibration_redefinition_findings, step 1).

The draw is the part of the sheet nobody can check by eye afterwards, so the allocation rule
is pinned here: the floor is honoured for every non-empty stratum, the residual is
proportional, no stratum is ever over-drawn, and a population too small to fill the request
stops rather than quietly producing a short sheet.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import g1_calibration_sample as samp  # noqa: E402


def test_allocation_hits_the_total_honours_the_floor_and_never_over_draws():
    sizes = {"a": 18, "b": 29, "c": 112, "d": 25, "e": 59, "f": 7,
             "g": 106, "h": 372, "i": 44, "j": 6}
    alloc = samp.allocate(sizes, n=60, floor=3)
    assert sum(alloc.values()) == 60
    assert all(v >= 3 for v in alloc.values())
    assert all(alloc[k] <= sizes[k] for k in alloc)
    # proportional above the floor: the largest stratum takes the largest share
    assert max(alloc, key=lambda k: alloc[k]) == "h"


def test_empty_strata_get_no_allocation_and_no_key():
    alloc = samp.allocate({"a": 10, "b": 0, "c": 5}, n=6, floor=3)
    assert "b" not in alloc
    assert sum(alloc.values()) == 6


def test_a_small_stratum_is_capped_at_its_own_size():
    alloc = samp.allocate({"a": 100, "b": 2}, n=20, floor=3)
    assert alloc["b"] == 2 and alloc["a"] == 18


def test_population_smaller_than_the_request_stops():
    with pytest.raises(SystemExit):
        samp.allocate({"a": 5, "b": 4}, n=60, floor=3)


def test_floor_that_cannot_fit_the_sample_stops():
    with pytest.raises(SystemExit):
        samp.allocate({k: 50 for k in "abcdefghij"}, n=20, floor=3)


@pytest.mark.parametrize("rec,expected", [
    ({"outcome": "pass", "level": 4}, "L4"),
    ({"outcome": "fail", "level": 0}, "L0"),
    ({"outcome": "unparseable", "level": None}, "unparseable"),
])
def test_level_key(rec, expected):
    assert samp.level_key(rec) == expected


@pytest.mark.parametrize("rec,expected", [
    ({"genuine_loss": True, "review_note": "n"}, "genuine"),
    ({"genuine_loss": False, "review_note": "n"}, "parser_miss"),
    ({"genuine_loss": False}, "not_in_queue"),
])
def test_verdict_key_reads_the_queue_from_the_note_not_the_flag(rec, expected):
    """`genuine_loss` is False both for a parser miss and for a record never put to the
    reviewer; only `review_note` distinguishes them."""
    assert samp.verdict_key(rec) == expected
