"""The readiness brief (`cc_tasks/2026-10-16_readiness_brief.md` Part A): the results table
reproduces the audit's page-two counts, the check table is a query over the record with the
criterion grouping read from the record, and a missing field fails the build.

Zero spend: reads the committed framework record, grid.json and the cycle's receipts."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import diagnostic_package as D  # noqa: E402
import readiness_brief_build as RB  # noqa: E402


@pytest.fixture(scope="module")
def record():
    return D.load_framework()


@pytest.fixture(scope="module")
def res(record):
    return RB.results(record)


def test_results_reproduce_the_audit_page_two_counts(res):
    # db464d5f RESULT Part D: "page two holds 64 cells: could not measure 41, fail 15, pass 8".
    c = res["counts"]
    assert (c["cells_total"], c["not_measured"], c["fail"], c["pass"], c["partial"]) == (64, 41, 15, 8, 0)
    assert res["scored"] == ["A1", "A3", "A5", "D4"]


def test_bodies_wholly_not_measured_on_the_scored_checks(res):
    # The task's premise named five (BLS, ORES, BTS, EIA, NASS); that list is the 13-check
    # concentration. On the four scored checks EIA has an A5 pass and NASS an A5 fail.
    assert sorted(res["wholly_not_measured"]) == ["BLS", "BTS", "ORES"]


def test_every_not_measured_cell_has_a_footnote(res):
    marks = {m for m, _ in res["footnotes"]}
    for b in res["rows"] + res["reference_rows"]:
        for c in b["cells"].values():
            if c["state"] in ("could_not_measure", "not_run"):
                assert c["mark"] in marks
            else:
                assert c["mark"] is None


def test_receipts_resolve_and_carry_status(res):
    assert res["receipts"]["found"] == res["receipts"]["wanted"]
    assert any("HTTP 403" in t for _, t in res["footnotes"])


def test_check_groups_come_from_the_criterion_nodes(record):
    rows = RB.check_rows(record)
    groups = {w: [r["leg"] for r in grp] for w, grp in RB.groups_of(rows)}
    assert list(groups) == ["Accessible", "Understandable", "Open", "Release"]
    assert [len(v) for v in groups.values()] == [12, 1, 2, 1]
    for grp in groups.values():  # scored first within a group
        flags = [next(r for r in rows if r["leg"] == leg)["scored"] for leg in grp]
        assert flags == sorted(flags, reverse=True)


def test_missing_brief_field_exits_nonzero(record):
    g = copy.deepcopy(record)
    spec = next(n for n in g["nodes"] if n["id"] == "spec:A1")
    spec["properties"].pop("rf_ask_plain")
    with pytest.raises(SystemExit, match="rf_ask_plain"):
        RB.check_rows(g)


def test_check_table_style_guards(record):
    rows = RB.check_rows(record)
    assert RB.repeated_phrase_audit(rows) == []
    assert RB.digit_audit(RB.SOURCE.read_text(encoding="utf-8"), rows) == []
    for r in rows:
        for k in ("name", "ask", "tells", "why"):
            assert not D.banned_hits_prose(r[k]) and not RB.dash_hits(r[k])
