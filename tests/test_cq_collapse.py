"""The CQ collapse fragment and the harness's metric derivation (task
2026-09-04_kg_diagnostic_and_cq_harness §3).

The collapse is the whole measurement: `flip` — the statistic the entity-resolution decision
turns on — is the difference between two views, and if the collapse is wrong the decision is
wrong. So the group counts are pinned against fixtures whose right answer is obvious by
inspection, and the two ways the metric can lie are given their own tests:

* **counting members instead of size.** Fourteen nodes all named "AI readiness" share one
  canonical key, so a group has ONE distinct member string and FOURTEEN rows. A
  `dup_groups` that counts distinct members reads zero exactly where duplication is worst.
  This was the first implementation's bug and it silently reported C = 9 instead of C = 98.
* **aliases that do not link.** The alias level is where non-obvious merging lives; a
  one-directional alias must still union both ways, and a chain must be transitive, or the
  collapsed view under-reports what a real dedup would buy.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "assessment" / "cq"))

from collapse import build_groups, canonical_key, collapse_rows  # noqa: E402


def _rows(*names):
    return [{"name": n, "span": f"span for {n}"} for n in names]


# ---------------------------------------------------------------------------
# the canonical key
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("AI readiness", "ai readiness"),
    ("  AI Readiness  ", "ai readiness"),
    ("AI\treadiness", "ai readiness"),
    ("AI  readiness", "ai readiness"),
    ("", None),
    ("   ", None),
    (None, None),
])
def test_canonical_key(raw, expected):
    assert canonical_key(raw) == expected


# ---------------------------------------------------------------------------
# group counting
# ---------------------------------------------------------------------------

def test_exact_duplicates_form_one_group_of_known_size():
    rows = _rows("AI readiness", "ai readiness", "  AI Readiness ", "data quality", "metadata")
    out = collapse_rows(rows, "name")
    assert out["rows_raw"] == 5
    assert out["rows_collapsed"] == 3          # ai readiness, data quality, metadata
    assert out["dup_groups"] == 1              # only the ai-readiness group has size > 1


def test_dup_groups_counts_group_SIZE_not_distinct_member_strings():
    """The regression that matters: fourteen identically named nodes are one canonical key
    and one distinct member string, but fourteen rows. Counting members reads 0."""
    rows = _rows(*(["AI readiness"] * 14))
    out = collapse_rows(rows, "name")
    assert out["rows_collapsed"] == 1
    assert out["rows"][0]["_row_count"] == 14
    assert len(out["rows"][0]["_members"]) == 1     # one distinct string...
    assert out["dup_groups"] == 1                   # ...but the group is still a duplicate group


def test_no_duplicates_means_no_dup_groups():
    out = collapse_rows(_rows("a", "b", "c"), "name")
    assert out["rows_collapsed"] == 3 and out["dup_groups"] == 0


def test_null_keys_are_kept_as_their_own_rows_never_merged():
    """Rows whose collapse column is null are not all 'the same entity'."""
    rows = [{"name": None}, {"name": None}, {"name": "x"}]
    out = collapse_rows(rows, "name")
    assert out["rows_collapsed"] == 3 and out["dup_groups"] == 0


def test_empty_input():
    out = collapse_rows([], "name")
    assert out == {"rows": [], "groups": {}, "dup_groups": 0, "rows_raw": 0, "rows_collapsed": 0}


# ---------------------------------------------------------------------------
# the alias level
# ---------------------------------------------------------------------------

def test_alias_merges_two_names_in_either_direction():
    rows = _rows("AI readiness", "AI-readiness")
    forward = collapse_rows(rows, "name", {"ai readiness": ["ai-readiness"]})
    assert forward["rows_collapsed"] == 1 and forward["dup_groups"] == 1
    reverse = collapse_rows(rows, "name", {"ai-readiness": ["ai readiness"]})
    assert reverse["rows_collapsed"] == 1 and reverse["dup_groups"] == 1


def test_alias_links_are_transitive():
    rows = _rows("a", "b", "c")
    out = collapse_rows(rows, "name", {"a": ["b"], "b": ["c"]})
    assert out["rows_collapsed"] == 1          # a~b, b~c => one group
    assert out["dup_groups"] == 1


def test_an_alias_to_something_absent_from_the_answer_changes_nothing():
    rows = _rows("a", "b")
    out = collapse_rows(rows, "name", {"a": ["not-in-this-answer"]})
    assert out["rows_collapsed"] == 2 and out["dup_groups"] == 0


def test_groups_map_covers_every_non_null_key():
    rows = _rows("A", "a", "B")
    groups = build_groups(rows, "name")
    assert set(groups) == {"a", "b"}
    assert groups["a"] == groups["a"]


# ---------------------------------------------------------------------------
# the decision statistic
# ---------------------------------------------------------------------------

def _rec(cid, cat, raw, col, misleading=False):
    return {"id": cid, "category": cat, "answerable_raw": raw, "answerable_collapsed": col,
            "misleading_raw": misleading, "dup_groups_unioned": 0}


def test_flip_counts_partial_no_and_misleading_raw_that_become_yes():
    import run_cq
    recs = [_rec("A", "x", "no", "yes"),            # flip
            _rec("B", "x", "partial", "yes"),       # flip
            _rec("C", "x", "yes", "yes", True),     # flip: misleading raw
            _rec("D", "x", "yes", "yes"),           # not a flip
            _rec("E", "x", "no", "no")]             # not a flip: still unanswerable
    agg = run_cq.aggregates(recs)
    assert agg["flip_ids"] == ["A", "B", "C"]
    assert agg["flip"] == pytest.approx(0.6)


@pytest.mark.parametrize("flip_ids,n,expected", [
    (["A", "B", "C", "D"], 10, "P0"),          # 0.40 >= 0.30
    (["A", "B"], 10, "scheduled"),             # 0.20, middle band
    (["A"], 20, "deferred"),                   # 0.05 < 0.10
])
def test_the_rule_branches_exactly_as_pre_registered(flip_ids, n, expected):
    import run_cq
    recs = [_rec(f"CQ-{i}", "x", "no", "yes" if f"CQ-{i}" in
                 [f"CQ-{j}" for j in range(len(flip_ids))] else "no") for i in range(n)]
    # build the flip set directly rather than by luck of the loop above
    for i, r in enumerate(recs):
        r["answerable_collapsed"] = "yes" if i < len(flip_ids) else "no"
    agg = run_cq.aggregates(recs)
    branch = agg["rule_branch"]
    assert (("P0" in branch) if expected == "P0" else
            ("deferred" in branch) if expected == "deferred" else
            ("scheduled" in branch))


def test_category_flip_is_reported_per_category():
    import run_cq
    recs = [_rec("A", "cat1", "no", "yes"), _rec("B", "cat1", "yes", "yes"),
            _rec("C", "cat2", "yes", "yes")]
    agg = run_cq.aggregates(recs)
    assert agg["by_category"]["cat1"]["flip"] == pytest.approx(0.5)
    assert agg["by_category"]["cat2"]["flip"] == pytest.approx(0.0)
    assert agg["by_category"]["cat1"]["ids"] == ["A"]


# ---------------------------------------------------------------------------
# the committed set and the committed run
# ---------------------------------------------------------------------------

def test_the_cq_set_meets_its_own_pre_registered_minimums():
    import yaml
    d = yaml.safe_load((REPO / "assessment/cq/cq_set_v1.yaml").read_text(encoding="utf-8"))
    qs = d["questions"]
    assert len(qs) >= 24
    cats: dict = {}
    for q in qs:
        cats.setdefault(q["category"], []).append(q["id"])
        for field in ("id", "question", "category", "cypher_raw", "collapse_on",
                      "expected_shape", "pass_criterion", "judge_notes"):
            assert field in q, f"{q['id']} missing {field}"
    assert len(cats) >= 8, cats
    assert min(len(v) for v in cats.values()) >= 3, cats
    assert len({q["id"] for q in qs}) == len(qs)


def test_registration_rows_name_every_aggregate_and_are_unique():
    """§1.6: every aggregate and every per-CQ metric is a named Result."""
    sys.path.insert(0, str(REPO / "assessment" / "cq"))
    import register_cq_results as reg
    rows = reg.rows("2026-09-04")
    names = [n for n, _v, _d in rows]
    assert len(names) == len(set(names)), "duplicate Result name"
    for required in ("cq_v1_A_raw", "cq_v1_A_collapsed", "cq_v1_flip",
                     "cq_v1_C_dup_groups_unioned_total", "cq_v1_misleading_raw_count"):
        assert required in names
    assert any(n.startswith("cq_v1_flip_") for n in names)          # per category
    assert "cq_v1_CQ_01_rows_raw" in names                          # per CQ
    judged = [d for n, _v, d in rows if n in ("cq_v1_A_raw", "cq_v1_A_collapsed", "cq_v1_flip")]
    assert all("LLM judge" in d for d in judged), "judged metrics must say so"
