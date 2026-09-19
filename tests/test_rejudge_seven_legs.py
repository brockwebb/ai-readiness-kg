"""Cycle 4's fourth re-judgement, `scan_2026-09-10_rj4`: the seven new legs published over the
Observations of 2026-09-10, with no host contacted.

`cc_tasks/2026-09-18_rejudge_seven_legs.md`. This file tests four things:

* the re-read of retained bodies (`scan/reread.py`): it is deterministic, it fills only
  absent blocks, it never mutates the stored rows, and it refuses a body that is missing or
  is not the one the Observation names;
* the frame restriction: a re-judgement and its re-derivation judge each surface on the
  frame's legs and nowhere else, so no Tier C Finding falls outside `tier0.legs` (DD-059);
* the published payload: every leg whose rule did not change is identical to `_rj3` in every
  field but the two identity fields, and D4 moves on exactly the two `home` surfaces that
  `RULE-D4-v3` was written for;
* the matrices: the product matrix gains the seven columns only for the cycle that judged them,
  and B5 is counted once per body.

**No network.**
"""
from __future__ import annotations

import collections
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from scan import load_params                                          # noqa: E402
from scan import reread as R                                          # noqa: E402

NEW = "scan_2026-09-10_rj4"
PRED = "scan_2026-09-10_rj3"
SNAPSHOT = "scan_2026-09-10_rj2"
SOURCE = "scan_2026-09-10"

#: The seven legs' distribution over the Tier A surfaces (the 16 bodies for B5), pinned. They
#: are the offline exercises' distributions (`2026-09-18_schema_field_rules_RESULT.md` §1,
#: `2026-09-18_manners_status_and_b5_control_RESULT.md` §2 for G4), reached here through the
#: published path. A change to a rule, a reader or the retained evidence shows up here rather
#: than being absorbed.
NEW_LEGS = {
    "B1": {"pass": 0, "fail": 37, "not_applicable": 0, "error": 9},
    "B2": {"pass": 0, "fail": 38, "not_applicable": 0, "error": 8},
    "B4": {"pass": 0, "fail": 38, "not_applicable": 0, "error": 8},
    "B5": {"pass": 0, "fail": 12, "not_applicable": 0, "error": 4},
    "D2": {"pass": 0, "fail": 40, "not_applicable": 0, "error": 6},
    "D3": {"pass": 0, "fail": 38, "not_applicable": 0, "error": 8},
    "G4": {"pass": 1, "fail": 37, "not_applicable": 0, "error": 8},
}


def payload(cycle: str) -> dict:
    return json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def params():
    return load_params()


@pytest.fixture(scope="module")
def rj4():
    return payload(NEW)


# ------------------------------------------------------------------ the re-read

def _d4_row(body_path: str, sha: str, doc: str = "scan-x") -> dict:
    return {"obs_id": "obs_test", "leg": "D4", "target_doc_id": doc,
            "target_url": "https://stats.example.gov/data.json",
            "response": {"body_path": body_path, "body_sha256": sha},
            "parsed": {"present": True}}


def _stored(tmp_path, monkeypatch, body: bytes) -> tuple:
    monkeypatch.setattr(R, "_repo_root", lambda: tmp_path)
    sha = hashlib.sha256(body).hexdigest()
    (tmp_path / "b").write_bytes(body)
    return "b", sha


def test_the_reread_fills_the_d4_blocks_and_leaves_the_row_it_was_given(tmp_path, monkeypatch,
                                                                         params):
    url = "https://stats.example.gov/products/estimates.html"
    body = json.dumps({"dataset": [{"identifier": url, "bureauCode": ["015:11"]}]}).encode()
    rel, sha = _stored(tmp_path, monkeypatch, body)
    row = _d4_row(rel, sha)
    before = copy.deepcopy(row)
    out, rec = R.reread([row], {"scan-x": url}, params)
    assert row == before, "the stored row was mutated"
    parsed = out[0]["parsed"]
    assert parsed["membership"]["records"] == 1
    assert parsed["dcat_fields"]["product_records"] == 1
    assert rec["observations_reread"]["D4"] == {"membership": 1, "dcat_fields": 1}
    again, _ = R.reread([before], {"scan-x": url}, params)
    assert again == out, "the re-read is not deterministic"


def test_a_block_the_collector_recorded_is_never_overwritten(tmp_path, monkeypatch, params):
    rel, sha = _stored(tmp_path, monkeypatch, b"{}")
    row = _d4_row(rel, sha)
    row["parsed"].update(membership={"recorded": True}, dcat_fields={"recorded": True})
    out, rec = R.reread([row], {"scan-x": "https://x.example/"}, params)
    assert out[0] == row
    assert rec["observations_reread"]["D4"] == {"membership": 0, "dcat_fields": 0}


def test_a_body_that_is_not_the_one_the_observation_names_is_refused(tmp_path, monkeypatch,
                                                                    params):
    rel, _sha = _stored(tmp_path, monkeypatch, b"{}")
    with pytest.raises(R.RetainedBodyError, match="not the body"):
        R.reread([_d4_row(rel, "0" * 64)], {"scan-x": "https://x.example/"}, params)


def test_a_missing_body_is_refused_not_skipped(tmp_path, monkeypatch, params):
    monkeypatch.setattr(R, "_repo_root", lambda: tmp_path)
    with pytest.raises(R.RetainedBodyError, match="not on disk"):
        R.reread([_d4_row("gone", "0" * 64)], {"scan-x": "https://x.example/"}, params)


def test_an_unparseable_catalog_is_recorded_as_the_collector_records_it(tmp_path, monkeypatch,
                                                                       params):
    rel, sha = _stored(tmp_path, monkeypatch, b"not json")
    out, _ = R.reread([_d4_row(rel, sha)], {"scan-x": "https://x.example/"}, params)
    assert out[0]["parsed"]["dcat_fields"]["parsed"] is False
    assert "membership" not in out[0]["parsed"], "fetch_catalog computes no membership here"


def test_the_a4_block_is_the_collectors_parse_of_the_same_bytes(tmp_path, monkeypatch, params):
    from scan.collectors import v2clauses
    body = b"User-agent: *\nContent-Signal: ai-train=no, ai-input=yes\n"
    rel, sha = _stored(tmp_path, monkeypatch, body)
    row = {"obs_id": "obs_a4", "leg": "A4", "target_doc_id": "home:x",
           "target_url": "https://x.example/robots.txt",
           "response": {"body_path": rel, "body_sha256": sha}, "parsed": {"present": True}}
    out, _ = R.reread([row], {"home:x": "https://x.example/"}, params)
    assert out[0]["parsed"]["content_signal"] == v2clauses.content_signals(
        body, "https://x.example/", params)


def test_nothing_is_reread_where_no_document_was_served(params):
    row = {"obs_id": "o", "leg": "D4", "target_doc_id": "d", "response": {},
           "parsed": {"present": False}}
    out, rec = R.reread([row], {}, params)
    assert out == [row] and rec["observations_reread"]["D4"]["membership"] == 0


# ------------------------------------------------------------------ the frame

def test_the_rederivation_gate_holds_itself_to_the_recorded_frame(rj4, params):
    """Take one leg off one surface's recorded legs, and the gate must now call that surface's
    Finding `missing`. It must not quietly re-derive it anyway."""
    rd = _mod("rederive_rj7t", REPO / "assessment/harness/scan/rederive.py")
    p = copy.deepcopy(rj4)
    doc = "home:www.census.gov"
    p["surface_legs"][doc] = [l for l in p["surface_legs"][doc] if l != "D2"]
    out = rd.rederive(p, params)
    want = [f["finding_id"] for f in rj4["findings_detail"]
            if f["target_doc_id"] == doc and f["leg"] == "D2"]
    assert out["missing_after_rederive"] == want and not out["unexpected_after_rederive"]


def test_no_tier_c_finding_is_outside_tier0(rj4, params):
    rows = json.loads((REPO / "state" / f"{rj4['targets']}.json").read_text())["rows"]
    tier_c = {r["doc_id"] for r in rows if r.get("tier") == "C"}
    allowed = set(params["tier0"]["legs"])
    bad = [(f["target_doc_id"], f["leg"]) for f in rj4["findings_detail"]
           if f["target_doc_id"] in tier_c and f["leg"] not in allowed]
    assert not bad, bad


# ------------------------------------------------------------------ the payload

def test_the_payload_is_a_rejudgement_with_no_evidence_and_no_request(rj4):
    assert rj4["cycle"] == NEW and rj4["cycle_kind"] == "rejudged"
    assert rj4["derived_from"] == SOURCE
    assert rj4["observations_detail"] == [] and rj4["requests_total"] == 0
    assert rj4["observations_reread"]["observations_reread"] == {
        "D4": {"membership": 10, "dcat_fields": 10}, "A4": {"content_signal": 44}}
    assert rj4["control_gate"]["ok"] is True and rj4["control_gate"]["verdict"] == "pass"


def test_every_finding_cites_only_observations_of_the_source_cycle(rj4):
    src = {o["obs_id"] for o in payload(SOURCE)["observations_detail"]}
    bad = [f["finding_id"] for f in rj4["findings_detail"] if not set(f["evidence"]) <= src]
    assert not bad, bad[:5]


def test_the_seven_legs_as_published(rj4):
    c = collections.Counter((f["leg"], f["verdict"]) for f in rj4["findings_detail"])
    got = {l: {v: c[(l, v)] for v in ("pass", "fail", "not_applicable", "error")}
           for l in NEW_LEGS}
    assert got == NEW_LEGS


def test_every_unchanged_leg_is_the_predecessors_judgement(rj4):
    """Decision 1's identity check, stated as the property that can hold. `finding_id` and
    `params_hash` are functions of the whole `params.yaml` (`model.params_hash`), which has
    moved since `_rj3`, so they differ by construction. Every other field of every Finding of a
    leg whose rule is unchanged must be `_rj3`'s."""
    S = _mod("rj7_script", REPO / "scripts" / "rejudge_seven_legs.py")
    d = S.identity(payload(PRED), rj4, PRED, rj4["surface_legs"])
    assert d["unchanged_findings_differing"] == []
    assert d["cells_only_in_new"] == []
    assert d["unchanged_findings_identical"] == d["unchanged_findings_compared"] == 671
    # The only cells an unchanged leg lost are G1-D's on the surfaces DD-066 withdrew it from.
    assert collections.Counter(c["leg"] for c in d["cells_only_in_old"]) == {"G1-D": 22}
    assert d["changed_legs"] == {"D4": {"old": ["RULE-D4-v2"], "new": ["RULE-D4-v3"]}}


def test_d4_moves_on_exactly_the_two_home_surfaces_v3_was_written_for(rj4):
    S = _mod("rj7_script2", REPO / "scripts" / "rejudge_seven_legs.py")
    d = S.identity(payload(PRED), rj4, PRED, rj4["surface_legs"])
    assert sorted((m["target"], m["from"], m["to"]) for m in d["changed_leg_verdict_moves"]) == [
        ("home:www.bea.gov", "RULE-D4-v2 pass", "RULE-D4-v3 fail"),
        ("home:www.census.gov", "RULE-D4-v2 pass", "RULE-D4-v3 fail")]


# ------------------------------------------------------------------ the matrices

def test_the_product_matrix_gains_the_seven_columns_only_where_they_were_judged():
    import build_l0_matrices as M
    assert M.product_legs(payload(SNAPSHOT)) == M.PRODUCT_LEGS
    assert M.product_legs(payload(PRED)) == M.PRODUCT_LEGS
    assert M.product_legs(payload(NEW)) == M.PRODUCT_LEGS + M.FIELD_LEGS


def test_b5_is_counted_once_per_body(params):
    import build_l0_matrices as M
    c = M.compute(NEW, params)
    b5 = c["product_counts"]["B5"]
    assert b5["fail"] + b5["error"] + b5["pass"] + b5["not_applicable"] == 16
    assert (b5["fail"], b5["error"]) == (12, 4)
    # Every declared surface of a body shows the body's one B5 Finding.
    fids = collections.defaultdict(set)
    for r in c["product"]:
        if r["declared"]:
            fids[r["agency"]].add(r["finding_ids"]["B5"])
    assert all(len(v) == 1 and None not in v for v in fids.values())


def test_a_non_snapshot_cycle_writes_no_report_fragment(tmp_path, params):
    import build_l0_matrices as M
    w = M.write_matrices(M.compute(NEW, params), out_dir=tmp_path,
                         gen_dir=tmp_path / "generated", fragments=False)
    assert w["fragments"] == [] and not (tmp_path / "generated").exists()
    assert len(w["files"]) == 3


def test_the_published_rj4_matrices_are_what_compute_says(params):
    import build_l0_matrices as M
    c = M.compute(NEW, params)
    got = json.loads((REPO / "docs/reports/scan_matrix_product_2026-09-10_rj4.json").read_text())
    assert got["legs"] == c["product_legs"] and got["rows"] == c["product"]


def test_the_snapshot_guard_sees_the_new_columns(params):
    import build_l0_matrices as M
    import snapshot_successor as SS
    moves = SS._cell_moves(M.compute(SNAPSHOT, params), M.compute(NEW, params))
    new_cols = {m["column"] for m in moves if m.get("matrix") == "product"
                and m["what"] == "matrix cell" and m["snapshot"] is None}
    assert new_cols == {f"verdict:{l}" for l in M.FIELD_LEGS}


# ------------------------------------------------------------------ the views, --cycle

def test_prescriptions_on_the_snapshot_are_the_records_own_values():
    import prescriptions as P
    acts = P.actions(P.load_record())
    # The CURRENT snapshot, read where every view reads it: since
    # `cc_tasks/2026-09-19_resnapshot_rj4.md` it is no longer `SNAPSHOT` above, which names the
    # cycle this file's task compared against.
    assert P.on_cycle(acts, P.snapshot_cycle()) is acts


def test_prescriptions_on_another_cycle_count_by_the_records_definition():
    """The recompute is the record's definition (per leg, bodies with a `fail` row), so run on
    the snapshot's matrices it reproduces every stored value. Run on `_rj4` it gives the seven
    new legs the counts their matrices carry."""
    import prescriptions as P
    import tag_prescriptions as TP
    acts = P.actions(P.load_record())
    fails = TP.matrix_fail_bodies(P.snapshot_cycle())
    for a in acts:
        want = fails[a["leg"]][0] if a["leg"] in fails else 0
        assert a["value"]["bodies_failing_now"] == want, a["id"]
    per_leg = {a["leg"]: a["value"]["bodies_failing_now"] for a in P.on_cycle(acts, NEW)}
    rj4 = TP.matrix_fail_bodies(NEW)
    assert {l: per_leg[l] for l in ("B1", "B2", "B4", "B5", "D2", "D3", "G4")} == {
        l: rj4[l][0] for l in ("B1", "B2", "B4", "B5", "D2", "D3", "G4")}
