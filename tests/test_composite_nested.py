"""A composite whose base is itself a composite (`scan.composite` scheme 2).

`cc_tasks/2026-10-07_seed_known_locations_verify.md` decision 5 declares
`scan_2026-10-07_composite_d`: the seeded cycle's ten legs over `scan_2026-10-06_composite_c`,
which is the recollection's re-judgement over cycle 4's. Every reader asks the composite which
cycle a leg's verdicts come from and where its evidence is; these fix the answers on a synthetic
three-part chain, and hold the flat composite's answers to what they were.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import composite                                             # noqa: E402


def _f(doc, leg, v, fid):
    return {"finding_id": fid, "target_doc_id": doc, "leg": leg, "verdict": v,
            "rule_id": f"RULE-{leg}-v1"}


def _o(oid, leg, doc="s1"):
    return {"obs_id": oid, "leg": leg, "target_doc_id": doc}


@pytest.fixture
def chain(tmp_path):
    """measured base (cycle 4) <- re-judgement (rj5); measured overlay (recollect) <- its
    re-judgement (rj1); flat composite C = rj1 over rj5; seeded cycle; D = seeded over C."""
    c4 = {"cycle": "scan_c4", "params_hash": "4" * 64, "requests_per_host": {"h": 10},
          "observations_detail": [_o("c4a", "A1"), _o("c4b", "A4"), _o("c4c", "D1"),
                                  _o("c4d", "link_probe")]}
    rj5 = {"cycle": "scan_c4_rj5", "cycle_kind": "rejudged", "derived_from": "scan_c4",
           "params_hash": "5" * 64, "legs_judged": ["A1", "A4", "D1"],
           "control_verdict": "pass", "observations_detail": [],
           "control_gate": {"verdicts": {"A1": {"x": "pass"}, "A4": {"x": "pass"},
                                         "D1": {"x": "pass"}}},
           "matrix": [{"doc_id": "s1", "verdicts": {"A1": "error", "A4": "pass", "D1": "error"}}],
           "findings_detail": [_f("s1", "A1", "error", "b1"), _f("s1", "A4", "pass", "b2"),
                               _f("s1", "D1", "error", "b3")]}
    rec = {"cycle": "scan_rec", "params_hash": "r" * 64, "requests_per_host": {"h": 3},
           "observations_detail": [_o("ra", "A1"), _o("rb", "D1"), _o("rc", "link_probe")]}
    rj1 = {"cycle": "scan_rec_rj1", "cycle_kind": "rejudged", "derived_from": "scan_rec",
           "scope": "legs", "legs_collected": ["A1", "D1"], "params_hash": "1" * 64,
           "control_verdict": "pass", "observations_detail": [],
           "control_gate": {"verdicts": {"A1": {"x": "pass"}, "D1": {"x": "pass"}}},
           "matrix": [{"doc_id": "s1", "verdicts": {"A1": "fail", "D1": "pass"}}],
           "findings_detail": [_f("s1", "A1", "fail", "r1"), _f("s1", "D1", "pass", "r2")]}
    seeded = {"cycle": "scan_seeded", "scope": "legs", "legs_collected": ["D1", "A13"],
              "params_hash": "s" * 64, "control_verdict": "pass",
              "requests_per_host": {"h": 2, "api": 1},
              "control_findings_detail": [{"leg": "D1", "target_doc_id": "control:p",
                                           "verdict": "pass"}],
              "observations_detail": [_o("sa", "D1"), _o("sb", "link_probe")],
              "matrix": [{"doc_id": "s1", "verdicts": {"D1": "fail", "A13": "fail"}}],
              "findings_detail": [_f("s1", "D1", "fail", "s1"), _f("s1", "A13", "fail", "s2")]}
    cons = lambda leg: {"A1": ("link_probe",), "A13": ("link_probe", "D1")}.get(leg, ())  # noqa: E731
    c = composite.build(rj5, rj1, "scan_comp_c", "t", cons)
    d = composite.build(c, seeded, "scan_comp_d", "t", cons)
    for p in (c4, rj5, rec, rj1, seeded, c, d):
        (tmp_path / f"{p['cycle']}.json").write_text(json.dumps(p), encoding="utf-8")
    return {"c": c, "d": d, "state": tmp_path}


def test_a_flat_composite_is_written_and_read_as_before(chain):
    c = chain["c"]
    assert c["composed_of"]["scheme"] == composite.SCHEME == 1
    assert "parts" not in c["composed_of"]["base"]
    assert c["composed_of"]["base"]["collection"] == "scan_c4"
    assert composite.parts(c) == [("scan_rec_rj1", ["A1", "D1"]), ("scan_c4_rj5", None)]
    assert composite.collections(c, chain["state"]) == ["scan_c4", "scan_rec"]


def test_a_nested_composite_names_every_part_with_the_legs_it_supplies(chain):
    d = chain["d"]
    assert d["composed_of"]["scheme"] == composite.SCHEME_NESTED
    assert "collection" not in d["composed_of"]["base"], "a composite base is no collection"
    assert composite.parts(d) == [("scan_seeded", ["D1", "A13"]), ("scan_rec_rj1", ["A1"]),
                                  ("scan_c4_rj5", None)]
    assert composite.part_of_leg(d, "D1") == "scan_seeded"
    assert composite.part_of_leg(d, "A1") == "scan_rec_rj1"
    assert composite.part_of_leg(d, "A4") == "scan_c4_rj5"
    assert {composite.finding_part(d, f) for f in d["findings_detail"]} \
        == {"scan_seeded", "scan_rec_rj1", "scan_c4_rj5"}
    assert sorted(f["finding_id"] for f in d["findings_detail"]) == ["b2", "r1", "s1", "s2"]
    assert d["matrix"][0]["verdicts"] == {"A1": "fail", "A4": "pass", "D1": "fail",
                                          "A13": "fail"}


def test_a_nested_composite_rests_on_every_collection_base_most_first(chain):
    assert composite.collections(chain["d"], chain["state"]) == ["scan_c4", "scan_rec",
                                                                 "scan_seeded"]


def test_a_nested_composites_evidence_is_its_bases_evidence_less_what_the_overlay_replaced(
        chain):
    ev = composite.evidence(chain["d"], chain["state"])
    ids = sorted(o["obs_id"] for o in ev["observations_detail"])
    # c4: only A4 survives C (A1 and D1 are replaced by rj1's collection, and link_probe was
    # consumed only by A1, so C drops it as a flat composite always has); rec: A1 and its
    # link_probe survive D, because A1 still comes from rj1 (only D1 is replaced by the seeded
    # cycle's); and the seeded cycle's own two.
    assert ids == ["c4b", "ra", "rc", "sa", "sb"]
    assert ev["requests_per_host_by_part"] == {"scan_c4": {"h": 10}, "scan_rec": {"h": 3},
                                               "scan_seeded": {"h": 2, "api": 1}}
    assert ev["requests_per_host"] == {"api": 1, "h": 15} and ev["requests_total"] == 16
