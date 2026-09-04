"""The reviewer-calibration agreement statistic, exercised on synthetic filled sheets
(task 2026-09-03_g1_freeze_calibration_redefinition_findings, step 1).

No operator labels exist yet, and the script must not be run on real ones in that task, so
everything here is synthetic and hand-checkable. What is actually being defended:

  * kappa is arithmetic, so one hand-computed 2x2 pins it (po = 0.7, pe = 0.5, kappa = 0.4);
  * quadratic weights must reward a near miss over a distant one, or the ordinal scale is
    being thrown away (the failure this whole exercise exists to avoid);
  * undefined must come back as undefined. A kappa that silently becomes 0.0 when one rater
    used a single category would read as "no agreement" when the truth is "not computable"
    (standard 4);
  * a blank answer line is 'not labelled', a garbage one is an error, and the two must never
    be confused — a sheet half-filled and silently scored is the whole risk of this format.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import g1_calibration_agreement as agree  # noqa: E402

LEVELS = agree.LEVELS


# ---------------------------------------------------------------------------
# kappa itself
# ---------------------------------------------------------------------------

def test_unweighted_kappa_matches_a_hand_computed_two_by_two():
    # 20 agree "yes", 15 agree "no", 5 A-yes/B-no, 10 A-no/B-yes over n = 50.
    # po = 35/50 = 0.7; pe = 0.5*0.6 + 0.5*0.4 = 0.5; kappa = (0.7-0.5)/0.5 = 0.4.
    pairs = ([("yes", "yes")] * 20 + [("no", "no")] * 15
             + [("yes", "no")] * 5 + [("no", "yes")] * 10)
    assert agree.kappa(pairs, ("yes", "no"), weights="none") == pytest.approx(0.4)


def test_perfect_agreement_is_one_under_both_weightings():
    pairs = [(lv, lv) for lv in LEVELS] * 4
    assert agree.kappa(pairs, LEVELS, "quadratic") == pytest.approx(1.0)
    assert agree.kappa(pairs, LEVELS, "none") == pytest.approx(1.0)


def test_quadratic_weights_reward_a_near_miss_over_a_distant_one():
    """The point of the ordinal scale: L3-vs-L4 must cost less than L0-vs-L4."""
    base = [(lv, lv) for lv in LEVELS] * 3
    near = base + [("L4", "L3")] * 4
    far = base + [("L4", "L0")] * 4
    k_near = agree.kappa(near, LEVELS, "quadratic")
    k_far = agree.kappa(far, LEVELS, "quadratic")
    assert k_near > k_far
    # unweighted cannot tell them apart — the reason weights are pre-registered
    assert agree.kappa(near, LEVELS, "none") == pytest.approx(agree.kappa(far, LEVELS, "none"))


def test_kappa_is_undefined_not_zero_when_a_rater_used_one_category():
    pairs = [("L4", "L4")] * 10
    assert agree.kappa(pairs, LEVELS, "quadratic") is None
    assert agree.kappa(pairs, LEVELS, "none") is None
    assert agree.kappa([], LEVELS, "quadratic") is None


def test_disagreement_worse_than_chance_is_negative():
    pairs = [("L0", "L4")] * 10 + [("L4", "L0")] * 10
    assert agree.kappa(pairs, LEVELS, "none") < 0


def test_confusion_table_is_dense_and_totals_the_pairs():
    pairs = [("L0", "L1"), ("L4", "L4"), ("L0", "L1")]
    table = agree.confusion(pairs, LEVELS)
    assert len(table) == len(LEVELS) ** 2
    assert table[("L0", "L1")] == 2 and table[("L4", "L4")] == 1
    assert sum(table.values()) == len(pairs)


def test_bootstrap_interval_brackets_the_point_estimate():
    pairs = ([(lv, lv) for lv in LEVELS] * 6) + [("L4", "L2"), ("L1", "L3"), ("L0", "L1")]
    point = agree.kappa(pairs, LEVELS, "quadratic")
    ci = agree.bootstrap_ci(pairs, LEVELS, "quadratic", b=400, seed=1)
    assert ci["lower"] <= point <= ci["upper"]
    assert ci["b"] == 400


def test_bootstrap_is_seed_deterministic():
    pairs = [(a, b) for a, b in zip(LEVELS * 4, ("L1", "L1", "L2", "L4", "L3") * 4)]
    a1 = agree.bootstrap_ci(pairs, LEVELS, "quadratic", b=200, seed=7)
    a2 = agree.bootstrap_ci(pairs, LEVELS, "quadratic", b=200, seed=7)
    assert a1 == a2


# ---------------------------------------------------------------------------
# the implied-verdict rule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("op,scorer,expected", [
    ("L4", "L1", "parser_miss"),        # operator read a qualifier the parser did not credit
    ("L3", "unparseable", "parser_miss"),
    ("L1", "L1", "genuine"),
    ("L0", "L2", "genuine"),            # operator harsher than the scorer is still not a miss
    ("L0", "unparseable", "parser_miss"),  # unparseable sits below every level by construction
    ("U", "L1", None),
])
def test_implied_verdict(op, scorer, expected):
    assert agree.implied_verdict(op, scorer) == expected


# ---------------------------------------------------------------------------
# reading a filled sheet
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows):
    head = "sample_id,mode,compression_level,estimate_label,estimate_value,qualifier_family,published_forms,prompt_shown,response,level,note\n"
    body = "".join(f"{sid},indirect,none,label,1,interval,SE = 1,prompt,response,{lvl},{note}\n"
                   for sid, lvl, note in rows)
    path.write_text(head + body, encoding="utf-8")


def test_csv_sheet_reads_levels_blanks_and_notes(tmp_path):
    p = tmp_path / "sheet.csv"
    _write_csv(p, [("C001", "L4", "clean"), ("C002", "", ""), ("C003", "u", "cannot classify"),
                   ("C004", "3", "")])
    got = agree.read_sheet(p)
    assert got["C001"]["level"] == "L4" and got["C001"]["note"] == "clean"
    assert got["C002"]["level"] is None            # blank is unlabelled, not a level
    assert got["C003"]["level"] == "U"
    assert got["C004"]["level"] == "L3"            # a bare digit is the level


def test_csv_sheet_rejects_an_unreadable_level(tmp_path):
    p = tmp_path / "sheet.csv"
    _write_csv(p, [("C001", "mostly fine", "")])
    with pytest.raises(agree.SheetError) as e:
        agree.read_sheet(p)
    assert "C001" in str(e.value)


def test_markdown_sheet_reads_the_answer_lines(tmp_path):
    p = tmp_path / "sheet.md"
    p.write_text(
        "## C001\n\n**C001 — Level (L0 / L1 / L2 / L3 / L4 / U):** L2\n\n"
        "**C001 — Note:** verbal only\n\n---\n"
        "## C002\n\n**C002 — Level (L0 / L1 / L2 / L3 / L4 / U):** ______\n\n"
        "**C002 — Note:** ______\n", encoding="utf-8")
    got = agree.read_sheet(p)
    assert got["C001"] == {"level": "L2", "note": "verbal only"}
    assert got["C002"]["level"] is None             # the unfilled rule is not a label


def test_empty_sheet_is_an_error_not_an_empty_result(tmp_path):
    p = tmp_path / "sheet.md"
    p.write_text("# nothing here\n", encoding="utf-8")
    with pytest.raises(agree.SheetError):
        agree.read_sheet(p)


# ---------------------------------------------------------------------------
# end to end on a synthetic sheet + key
# ---------------------------------------------------------------------------

def _key(entries):
    return {"key": {sid: {"file": "f.json", "index": i, "split": "pooled_opus", "target": "t",
                          "family": "interval", "mode": "indirect", "compression_level": "none",
                          "scorer_level": sc, "reviewer_verdict": rv, "evidence_path": "e.json"}
                    for i, (sid, sc, rv) in enumerate(entries)}}


def test_end_to_end_perfect_operator_reproduces_the_scorer(tmp_path):
    entries = [("C001", "L4", "not_in_queue"), ("C002", "L3", "not_in_queue"),
               ("C003", "L1", "genuine"), ("C004", "L0", "genuine"),
               ("C005", "L2", "genuine"), ("C006", "unparseable", "genuine")]
    sheet = tmp_path / "s.csv"
    _write_csv(sheet, [(sid, "U" if sc == "unparseable" else sc, "") for sid, sc, _ in entries])
    report = agree.analyse(agree.read_sheet(sheet), _key(entries), bootstrap=200, seed=3)
    assert report["labelled"] == 6
    assert report["operator_vs_scorer_ordinal"]["kappa"] == pytest.approx(1.0)
    assert report["operator_vs_scorer_ordinal"]["raw_agreement"] == pytest.approx(1.0)
    assert report["operator_vs_scorer_six_category"]["n"] == 6
    # every queued record the operator confirmed reads as `genuine`; the U one is excluded
    ovr = report["operator_vs_reviewer_queue"]
    assert ovr["excluded_operator_U"] == 1
    assert ovr["n"] == 3 and ovr["raw_agreement"] == pytest.approx(1.0)
    assert ovr["kappa"] is None          # one category on both sides: undefined, not 1.0


def test_end_to_end_operator_who_finds_parser_misses_disagrees_with_the_reviewer(tmp_path):
    entries = [("C001", "L1", "genuine"), ("C002", "L1", "genuine"),
               ("C003", "L1", "parser_miss"), ("C004", "L0", "parser_miss"),
               ("C005", "L4", "not_in_queue")]
    # the operator reads a qualifier in C001 and C002 (implied parser_miss) and agrees on C003;
    # C004 they confirm as a genuine corruption.
    sheet = tmp_path / "s.csv"
    _write_csv(sheet, [("C001", "L4", ""), ("C002", "L3", ""), ("C003", "L4", ""),
                       ("C004", "L0", ""), ("C005", "L4", "")])
    report = agree.analyse(agree.read_sheet(sheet), _key(entries), bootstrap=200, seed=3)
    ovr = report["operator_vs_reviewer_queue"]
    assert ovr["n"] == 4
    assert ovr["confusion"]["parser_miss|genuine"] == 2     # operator says miss, reviewer said genuine
    assert ovr["confusion"]["parser_miss|parser_miss"] == 1
    assert ovr["confusion"]["genuine|parser_miss"] == 1
    assert ovr["raw_agreement"] == pytest.approx(0.25)
    assert report["operator_vs_scorer_ordinal"]["kappa"] < 1.0


def test_unlabelled_and_missing_records_are_named_not_dropped_silently(tmp_path):
    entries = [("C001", "L4", "not_in_queue"), ("C002", "L1", "genuine"), ("C003", "L2", "genuine")]
    sheet = tmp_path / "s.csv"
    _write_csv(sheet, [("C001", "L4", ""), ("C002", "", "")])     # C003 absent, C002 blank
    report = agree.analyse(agree.read_sheet(sheet), _key(entries), bootstrap=50, seed=3)
    assert report["unlabelled"] == ["C002"]
    assert report["missing_from_sheet"] == ["C003"]
    assert report["labelled"] == 1


def test_report_serialises_and_renders(tmp_path):
    entries = [("C001", "L4", "not_in_queue"), ("C002", "L1", "genuine"),
               ("C003", "L2", "genuine"), ("C004", "L0", "parser_miss")]
    sheet = tmp_path / "s.csv"
    _write_csv(sheet, [("C001", "L4", ""), ("C002", "L2", ""), ("C003", "L2", ""), ("C004", "L3", "")])
    report = agree.analyse(agree.read_sheet(sheet), _key(entries), bootstrap=100, seed=5)
    json.dumps(report)                                   # must be JSON-serialisable as written
    text = agree.render(report)
    assert "operator vs scorer" in text and "operator (implied) vs reviewer" in text
