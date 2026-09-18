"""The scoring model: a documented query over the record and the cycle of record.

`cc_tasks/2026-09-18_scoring_model.md` decision 7. The OECD/JRC *Handbook on Constructing
Composite Indicators* (2008) asks of every composite that it be re-derivable from its
documented steps; these tests are what makes that true of this one:

* a synthetic body with known verdicts scores exactly what the hand computation says;
* every body's printed score re-derives, by an independent computation written here, from the
  cells printed beside it;
* no coverage line claims more measured than there is in total;
* the candidate leg (DD-054) and the `error` / `not_applicable` rows never enter a numerator
  or a denominator;
* the page in `docs/design/` is what `score.py --explain` prints, not a page somebody typed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import score as S  # noqa: E402

PY = "/opt/anaconda3/bin/python3" if Path("/opt/anaconda3/bin/python3").exists() else sys.executable


# ------------------------------------------------------------------ the synthetic body

def _leg(leg, ind, con, crit, scored=True, reason=""):
    return {"leg": leg, "indicator_id": f"ind:{ind}", "code": ind, "construct_id": f"con:{con}",
            "construct": con, "criterion": crit, "scored": scored, "reason": reason}


#: Two criteria. X has two constructs (x1 with two indicators, x2 with one); Y has one.
#: One candidate leg that must never count.
SYNTH = [
    _leg("X1", "X1", "x1", "X"),
    _leg("X2", "X2", "x1", "X"),
    _leg("X3", "X3", "x2", "X"),
    _leg("Y1", "Y1", "y1", "Y"),
    _leg("Y9", "Y9", "y1", "Y", scored=False, reason="candidate"),
]
CRITERIA = ["X", "Y", "Z"]


def _cells(**legs):
    return {leg: dict(v) for leg, v in legs.items()}


def test_a_synthetic_body_scores_what_the_hand_computation_says():
    cells = _cells(
        X1={"pass": 1, "fail": 1},                 # 0.5
        X2={"pass": 3, "fail": 1, "error": 2},     # 0.75; errors out of the denominator
        X3={"fail": 2, "not_applicable": 1},       # 0.0
        Y1={"pass": 1},                            # 1.0
        Y9={"fail": 5},                            # candidate: never counted
    )
    s = S.score_body(cells, SYNTH, CRITERIA)
    # construct x1 = mean(0.5, 0.75) = 0.625; x2 = 0.0; criterion X = mean(0.625, 0.0) = 0.3125
    # criterion Y = 1.0; Z has no measured construct and is not in the mean.
    # body = mean(0.3125, 1.0) = 0.65625
    assert s["indicators"]["ind:X1"]["score"] == pytest.approx(0.5)
    assert s["indicators"]["ind:X2"]["score"] == pytest.approx(0.75)
    assert s["constructs"]["con:x1"]["score"] == pytest.approx(0.625)
    assert s["constructs"]["con:x2"]["score"] == pytest.approx(0.0)
    assert s["criteria"]["X"]["score"] == pytest.approx(0.3125)
    assert s["criteria"]["Y"]["score"] == pytest.approx(1.0)
    assert s["criteria"]["Z"]["score"] is None
    assert s["score"] == pytest.approx(0.65625)
    assert s["excluded"] == {"error": 2, "not_applicable": 1}
    assert s["coverage"]["criteria"] == {"measured": 2, "total": 3}
    assert s["coverage"]["legs"] == {"measured": 4, "total": 4}


def test_the_gating_view_names_the_first_empty_construct():
    cells = _cells(X1={"pass": 2}, X2={"pass": 1}, X3={"fail": 2}, Y1={"pass": 1, "fail": 1})
    s = S.score_body(cells, SYNTH, CRITERIA)
    g = S.gating(s, SYNTH)
    assert g["legs_passed_outright"] == 2          # X1 and X2; Y1 is split
    assert g["first_zero_construct"] == "x2"
    assert g["zero_constructs"] == ["x2"]


def test_a_leg_with_only_error_rows_is_unmeasured_not_zero():
    cells = _cells(X1={"error": 3}, X3={"pass": 1}, Y1={"fail": 1})
    s = S.score_body(cells, SYNTH, CRITERIA)
    assert s["indicators"]["ind:X1"]["score"] is None
    assert s["constructs"]["con:x1"]["score"] is None
    assert s["criteria"]["X"]["score"] == pytest.approx(1.0)
    assert s["score"] == pytest.approx(0.5)


def test_the_candidate_leg_never_moves_a_score():
    base = _cells(X1={"pass": 1, "fail": 1}, Y1={"fail": 1}, Y9={"fail": 4})
    flipped = _cells(X1={"pass": 1, "fail": 1}, Y1={"fail": 1}, Y9={"pass": 4})
    assert S.score_body(base, SYNTH, CRITERIA)["score"] == \
        S.score_body(flipped, SYNTH, CRITERIA)["score"]


def test_a_flip_delta_is_the_rescore_of_the_flipped_cells():
    cells = _cells(X1={"pass": 1, "fail": 1}, X3={"fail": 2}, Y1={"fail": 1})
    before = S.score_body(cells, SYNTH, CRITERIA)["score"]
    d = S.flip_delta(cells, "X3", SYNTH, CRITERIA)
    after = S.score_body(_cells(X1={"pass": 1, "fail": 1}, X3={"pass": 2}, Y1={"fail": 1}),
                         SYNTH, CRITERIA)["score"]
    assert d == pytest.approx(after - before)
    assert d > 0


def test_dropping_a_criterion_removes_it_from_the_body_mean():
    cells = _cells(X1={"pass": 1}, Y1={"fail": 1})
    assert S.score_body(cells, SYNTH, CRITERIA)["score"] == pytest.approx(0.5)
    assert S.score_body(cells, SYNTH, CRITERIA, drop=("Y",))["score"] == pytest.approx(1.0)


def test_competition_ranks_tie_the_way_the_handbook_ranks():
    assert S.ranks({"a": 0.5, "b": 0.9, "c": 0.5, "d": None}) == {"b": 1, "a": 2, "c": 2}


# ------------------------------------------------------------------ the real record and cycle

@pytest.fixture(scope="module")
def run():
    r = subprocess.run([PY, str(REPO / "scripts" / "score.py"), "--json"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_the_legs_are_read_from_the_basis_field(run):
    g = json.loads((REPO / "framework" / "ai_readiness_framework.json").read_text())
    harness = {n["id"] for n in g["nodes"] if "AssessmentIndicator" in n["labels"]
               and n["properties"].get("measurement_basis") == "harness_leg"}
    assert {l["indicator_id"] for l in run["structure"]} == harness
    # The totals follow the record's DD-054 split: candidates are structured, not counted.
    candidates = {n["id"] for n in g["nodes"] if n["properties"].get("status") == "candidate"}
    assert run["framework"]["harness_leg_indicators"] == len(harness - candidates)
    assert run["framework"]["indicators"] == g["counts"]["indicators"]
    assert run["framework"]["constructs"] == g["counts"]["constructs"]


def test_the_candidate_leg_is_structured_but_never_scored(run):
    from scan import rules
    for l in run["structure"]:
        if l["leg"] in rules.CANDIDATE_LEGS:
            assert not l["scored"] and "DD-054" in l["reason"]


def _hand(cells: dict, structure: list) -> float | None:
    """The hierarchy, written again without any helper from score.py."""
    per_con: dict = {}
    for l in structure:
        if not l["scored"]:
            continue
        c = cells.get(l["leg"], {})
        judged = c.get("pass", 0) + c.get("fail", 0)
        if judged:
            per_con.setdefault((l["criterion"], l["construct_id"]), {}).setdefault(
                l["indicator_id"], []).append(c.get("pass", 0) / judged)
    per_crit: dict = {}
    for (crit, _), inds in per_con.items():
        ind_scores = [sum(v) / len(v) for v in inds.values()]
        per_crit.setdefault(crit, []).append(sum(ind_scores) / len(ind_scores))
    crits = [sum(v) / len(v) for v in per_crit.values()]
    return sum(crits) / len(crits) if crits else None


def test_every_body_score_re_derives_from_its_printed_cells(run):
    assert len(run["bodies"]) == run["cycle"]["n_bodies"]
    for name, b in run["bodies"].items():
        hand = _hand(b["cells"], run["structure"])
        if hand is None:
            assert b["score"] is None
        else:
            assert b["score"] == pytest.approx(hand), name


def test_measured_never_exceeds_total(run):
    for name, b in run["bodies"].items():
        for level, cov in b["coverage"].items():
            assert 0 <= cov["measured"] <= cov["total"], (name, level, cov)
    for level, cov in run["coverage"].items():
        assert 0 <= cov["measured"] <= cov["total"], (level, cov)


def test_every_prescription_delta_is_a_rescore(run):
    struct = run["structure"]
    crits = run["framework"]["criteria"]
    for name, b in run["bodies"].items():
        for p in b["prescriptions"]:
            assert p["delta"] == pytest.approx(
                S.flip_delta(b["cells"], p["leg"], struct, crits)), (name, p["action"])
            assert p["delta"] > 0


@pytest.mark.parametrize("mode", [[], ["--body", "NCHS"], ["--top", "10"], ["--sensitivity"],
                                  ["--explain"]])
def test_every_output_carries_the_coverage_sentence(mode):
    r = subprocess.run([PY, str(REPO / "scripts" / "score.py"), *mode],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert S.COVERAGE_SENTENCE in r.stdout


def test_the_design_page_is_generated():
    r = subprocess.run([PY, str(REPO / "scripts" / "score.py"), "--check"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_design_page_publishes_no_body_score():
    """Decision 8: a score on the site is a publication and is the operator's. `docs/` is the
    site, so the page documents the model and names no body."""
    page = (REPO / "docs" / "design" / "scoring_model.md").read_text()
    for body in S.bodies_on(S.snapshot_cycle()):
        assert f"| {body} |" not in page and f"{body}:" not in page, body
