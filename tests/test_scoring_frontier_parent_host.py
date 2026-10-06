"""Frontier indicators out of the score, parent-host cells out of unit ranks, one measured count.

`cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md` decision 4, under DN-012 d4, d5
and d7 (audit C-06, C-13, C-07). Each test names the defect it would have caught.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import parent_host as PH  # noqa: E402
import score as S  # noqa: E402

#: The cycle the audit recomputed on (C-06): its published matrices are immutable, so the
#: recomputation can be pinned. The audit's own numbers, quoted from
#: `docs/audit/2026-10-04_full_audit_findings.csv` row 4.
AUDIT_CYCLE = "scan_2026-09-10_rj4"
AUDIT = {"CENSUS": (0.080, 0.089), "EIA": (0.133, 0.160)}
AUDIT_FLAT_RANK = ("SAMHSACBHS", 7, 5)


def _record(frontier: bool = True) -> dict:
    g = S.P.load_record()
    if frontier:
        return g
    g = copy.deepcopy(g)
    for n in g["nodes"]:
        n["properties"].pop("frontier", None)
    return g


# ------------------------------------------------------------------ decision 1 (DN-012 d4)

def test_a_frontier_indicator_never_enters_the_structure():
    """C-06: `structure` selected legs by `measurement_basis` only and scored A9."""
    struct = S.structure(_record(), S.snapshot_cycle())
    a9 = [l for l in struct if l["leg"] == "A9"]
    assert a9 and not any(l["scored"] for l in a9), a9
    assert "DN-012 d4" in a9[0]["reason"]


def test_a_frontier_fixture_indicator_is_excluded_like_a_candidate():
    """Mark an ordinary scored indicator `frontier: true` in a copy of the record: its leg
    leaves the structure and a body that passes it scores as if it were not there."""
    g = copy.deepcopy(_record())
    for n in g["nodes"]:
        if n["properties"].get("code") == "A3" and "AssessmentIndicator" in n["labels"]:
            n["properties"]["frontier"] = True
            n["properties"]["as_of"] = "2026-10"
    cycle = S.snapshot_cycle()
    struct = S.structure(g, cycle)
    a3 = next(l for l in struct if l["leg"] == "A3")
    assert not a3["scored"] and "frontier" in a3["reason"]
    crit = S.framework_totals(g)["criteria"]
    body = {"A3": {"pass": 3}, "A4": {"fail": 1}}
    s = S.score_body(body, struct, crit)
    assert "A3" not in s["legs"]
    assert s["score"] == 0 and s["flat"] == 0


def _variant(monkeypatch, cycle: str, frontier: bool, parent: bool) -> dict:
    g = _record(frontier)
    monkeypatch.setattr(S.P, "load_record", lambda: g)
    if not parent:
        monkeypatch.setattr(PH, "marks_for_row", lambda *a, **k: {})
    return S.compute(cycle)["bodies"]


def test_the_audit_recomputation_reproduces(monkeypatch):
    """The task's check on decision 1: the audit's three numbers on its own cycle, before and
    after the frontier exclusion (parent-host marks held off, as the audit computed)."""
    before = _variant(monkeypatch, AUDIT_CYCLE, frontier=False, parent=False)
    monkeypatch.undo()
    after = _variant(monkeypatch, AUDIT_CYCLE, frontier=True, parent=False)
    for body, (b, a) in AUDIT.items():
        assert round(before[body]["score"], 3) == b
        assert round(after[body]["score"], 3) == a
    body, rb, ra = AUDIT_FLAT_RANK
    assert before[body]["flat_rank"] == rb and after[body]["flat_rank"] == ra


# ------------------------------------------------------------------ decision 2 (DN-012 d5)

FRAME = {
    "rows": [
        {"agency": "SHARED", "tier": "A", "surface_kind": "home", "url": "https://www.dept.gov/"},
        {"agency": "OWN", "tier": "A", "surface_kind": "home", "url": "https://www.own.gov/"},
        {"agency": "SECTION", "tier": "A", "surface_kind": "home",
         "url": "https://www.parent.gov/unit/index.htm"},
    ],
    "agency_detail": [
        {"agency": "SHARED", "agency_name": "Shared Unit", "tier": "A", "host": "www.dept.gov",
         "parent_department": "Department of Things"},
        {"agency": "OWN", "agency_name": "Own Bureau", "tier": "A", "host": "www.own.gov",
         "parent_department": "Department of Things"},
        {"agency": "SECTION", "agency_name": "Section Unit", "tier": "A",
         "host": "www.parent.gov", "parent_department": "Department of Things"},
    ],
}


def test_host_shared_with_on_the_roster_marks_the_body():
    parent = PH.bodies(FRAME, shared={"SHARED": "Parent Agency"}, registry={})
    assert set(parent) == {"SHARED", "SECTION"}, parent
    assert any("host_shared_with" in s for s in parent["SHARED"]["signals"])
    assert any("a section of" in s for s in parent["SECTION"]["signals"])
    assert "OWN" not in parent


def test_the_registry_signal_marks_a_bare_department_host():
    """ORES's case: the roster home is the host root, and only the .gov registry says the
    domain is the parent department's."""
    reg = {("www.own.gov", "own bureau"): {
        "in_registry": True, "registrable_domain": "own.gov",
        "registry_organization": "Department of Things", "registry_suborganization": "",
        "agrees_with_roster_parent": True}}
    parent = PH.bodies(FRAME, shared={}, registry=reg)
    assert "OWN" in parent and "registry" in parent["OWN"]["signals"][0]
    reg[("www.own.gov", "own bureau")]["registry_suborganization"] = "Own Bureau"
    assert "OWN" not in PH.bodies(FRAME, shared={}, registry=reg)


def test_parent_host_cells_are_marked_only_on_the_parent_host():
    parent = PH.bodies(FRAME, shared={"SHARED": "Parent Agency"}, registry={})
    hf = PH.host_file_legs()
    legs = ["A4", "A6", "D4", "D2", "A10"]
    on = PH.marks_for_row("SHARED", "https://www.dept.gov/x", legs, parent, hf)
    assert on == {"A4": PH.MARK, "D4": PH.MARK, "D2": PH.MARK}
    # A flagship the unit publishes on a host of its own is the unit's.
    assert PH.marks_for_row("SHARED", "https://data.unit.gov/x", legs, parent, hf) == {}
    assert PH.marks_for_row("OWN", "https://www.own.gov/", legs, parent, hf) == {}


def test_score_body_ignores_parent_host_cells(tmp_path, monkeypatch):
    """A matrix row marked `parent_host` reaches `score_body` under that name, and the body
    scores exactly as it would without the cell."""
    cycle = "scan_2026-09-10_rj5"
    real = {m["_kind"]: m for m in S.matrices(cycle)}
    suffix = cycle.replace("scan_", "")
    for kind in ("tierA", "product"):
        src = REPO / "docs" / "reports" / f"scan_matrix_{kind}_{suffix}.json"
        doc = json.loads(src.read_text(encoding="utf-8"))
        for r in doc["rows"]:
            r["marks"] = {}
            if r["agency"] == "CENSUS" and kind == "tierA":
                r["marks"] = {"A4": PH.MARK}
        (tmp_path / src.name).write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(S.P, "REPORTS", tmp_path)
    c = S.cells(cycle)["CENSUS"]
    assert c["A4"] == {PH.MARK: 1}
    struct = S.structure(_record(), cycle)
    crit = S.framework_totals(_record())["criteria"]
    with_mark = S.score_body(c, struct, crit)
    without = S.score_body({k: v for k, v in c.items() if k != "A4"}, struct, crit)
    assert with_mark["score"] == without["score"] and with_mark["flat"] == without["flat"]
    assert with_mark["excluded"].get(PH.MARK) == 1
    assert with_mark["legs"]["A4"]["judged"] == 0
    assert real  # the published matrices were read, not invented


def test_a_body_with_zero_scorable_legs_is_unranked_with_a_reason():
    struct = S.structure(_record(), S.snapshot_cycle())
    crit = S.framework_totals(_record())["criteria"]
    body = {"A4": {PH.MARK: 1}, "A5": {"error": 1}}
    s = S.score_body(body, struct, crit)
    assert s["score"] is None and s["flat"] is None
    parent = {"X": {"host": "www.dept.gov", "answers_for": "Department of Things"}}
    why = S.unranked_reason(s, parent, "X", {"fail": 1})
    assert why and PH.MARK in why and "www.dept.gov" in why and "1 fail" in why
    assert S.ranks({"X": s["score"], "Y": 0.0}) == {"Y": 1}


def test_the_cycle_of_record_ranks_no_body_on_parent_host_cells():
    """On the published cycle: no ranked body's score rests on a parent-host cell, every body
    the roster places on a parent host carries the marks, and an unranked body says why."""
    r = S.compute()
    parent = PH.bodies()
    assert parent, "the roster places no body on a parent host"
    for b, v in r["bodies"].items():
        for leg, x in v["legs"].items():
            if v["cells"].get(leg, {}).get(PH.MARK):
                assert x["judged"] == sum(v["cells"][leg].get(k, 0) for k in S.JUDGED)
        if v["score"] is None:
            assert v["unranked_reason"], b
            assert v["rank"] is None
        if b in parent:
            assert v["parent_host"] and v["parent_host"]["host"] == parent[b]["host"]


def test_the_parent_host_legs_are_the_runners_host_file_readers():
    """`parent_host.yaml` names the legs whose collector reads a host-root file. Re-derived
    from the dispatch in `runner.py`, so a leg that starts reading `/robots.txt` or
    `/data.json` cannot stay off the list."""
    src = (REPO / "assessment" / "harness" / "scan" / "runner.py").read_text(encoding="utf-8")
    blocks = re.split(r"\n    if leg == ", src)
    readers = set()
    for b in blocks[1:]:
        leg = b.split(":", 1)[0].strip().strip('"')
        body = b.split("\n    if ", 1)[0]
        if re.search(r"\b(robots\.fetch|sitemap\.fetch|dcat\.fetch_catalog)\(", body):
            readers.add(leg)
    assert readers == set(PH.config()["host_file_legs"]), readers


def test_the_matrices_carry_the_marks_the_derivation_gives():
    """The published matrices of the cycle of record are marked by the same function the score
    reads them through, and A9 is marked `frontier` on every product row."""
    for m in S.matrices(S.snapshot_cycle()):
        assert all("marks" in r for r in m["rows"]), m["_path"]
        assert "parent_host" in m, m["_path"]
        parent, hf = PH.bodies(), PH.host_file_legs()
        for r in m["rows"]:
            url = r.get("host_url") if m["_kind"] != "product" else r.get("url")
            want = PH.marks_for_row(r["agency"], url, m["legs"], parent, hf)
            got = {l: k for l, k in r["marks"].items() if k == PH.MARK}
            assert got == want, (r["agency"], got, want)
            if m["_kind"] == "product":
                assert r["marks"].get("A9") == "frontier"


# ------------------------------------------------------------------ decision 3 (DN-012 d7)

def test_every_scan_measured_node_points_at_the_cycle_of_record():
    g = S.P.load_record()
    cycle = S.snapshot_cycle()
    for n in g["nodes"]:
        p = n["properties"]
        if "AssessmentIndicator" in n["labels"] and p.get("measurement_status") == "measured" \
                and p.get("measured_by"):
            assert p["measured_by"]["cycle"] == cycle, (n["id"], p["measured_by"]["cycle"])


def _printed(path: Path, pattern: str) -> int:
    m = re.search(pattern, path.read_text(encoding="utf-8"))
    assert m, f"{path.relative_to(REPO)} prints no count matching {pattern!r}"
    return int(m.group(1))


def test_the_counts_block_equals_the_generators_count_on_both_surfaces():
    """C-07: the progress page said 16/48 measured while the brief said 21 of 48 measured.
    `indicators measured` now has one value: the record's counts block, which the single
    writer recomputes, and every surface that prints the name prints it."""
    import framework_writeback as fw
    g = S.P.load_record()
    n = g["counts"]["indicators_measured"]
    assert n == fw.recount(g)["indicators_measured"]
    assert _printed(REPO / "docs" / "progress" / "index.html",
                    r"<b>(\d+)/\d+</b>\s*<span>measured</span>") == n
    assert _printed(REPO / "docs" / "figures" / "fig1_usafacts_to_framework.caption.md",
                    r"(\d+) are measured,") == n
    assert _printed(REPO / "docs" / "brief" / "G_census_dogfood.md",
                    r"The record marks (\d+) of the \d+ framework indicators measured") == n


def test_writeback_follows_the_cycle_and_keeps_the_history():
    """DD-069: a node the new cycle does not earn returns to `harness_built` with its old
    `measured_by` kept; a body leg qualifies on the body's well-known row."""
    import framework_writeback_measured as W
    old = {"cycle": "scan_old", "legs": ["A1"]}
    g = {"nodes": [
        {"id": "ind:A1", "labels": ["AssessmentIndicator"],
         "properties": {"code": "A1", "measurement_status": "measured", "measured_by": old}},
        {"id": "ind:A4", "labels": ["AssessmentIndicator"],
         "properties": {"code": "A4", "measurement_status": "measured",
                        "measured_by": {"cycle": "scan_old"}}},
        {"id": "ind:B5", "labels": ["AssessmentIndicator"],
         "properties": {"code": "B5", "measurement_status": "harness_built"}},
        *[{"id": f"spec:{c}", "labels": ["MeasurementSpec"],
           "properties": {"leg": c, "indicator_code": c}} for c in ("A1", "A4", "B5")]],
        "edges": []}
    payload = {"control_verdict": "pass", "params_hash": "h", "matrix": [
        {"agency": "X", "surface_kind": "flagship", "admitted": True,
         "verdicts": {"A1": "error", "A4": "pass"}},
        {"agency": "X", "surface_kind": "well_known", "admitted": False,
         "verdicts": {"B5": "fail"}}]}
    out = W.writeback(g, payload, W.evidence(payload, frozenset(), set()), "scan_new")
    p = {n["properties"]["code"]: n["properties"] for n in g["nodes"]
         if "AssessmentIndicator" in n["labels"]}
    assert out["demoted"] == ["A1"] and p["A1"]["measurement_status"] == "harness_built"
    assert p["A1"]["measured_previously"] == [old] and "measured_by" not in p["A1"]
    assert p["A1"]["not_measured_reason"]["cycle"] == "scan_new"
    assert p["A4"]["measured_by"]["cycle"] == "scan_new" and out["repointed"] == ["A4"]
    assert p["B5"]["measurement_status"] == "measured" and out["promoted"] == ["B5"]
    assert g["counts"]["indicators_measured"] == 2

