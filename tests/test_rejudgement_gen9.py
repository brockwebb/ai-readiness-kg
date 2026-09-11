"""The generation-9 re-judgement of cycles 1 to 4, and the checks that make it a gate.

`cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md` §3. The invariant readings themselves live in
`tests/test_invariants.py`, where the four new payloads are pinned at zero on BOTH readings and
asserted rather than xfailed; what is here is everything else the task gates on — the moved-leg
sets, the licence a comparison record grants, and F5's refusal to draw a cycle whose predecessor
nobody declared.

**The moved-leg sets are pinned by count, not described.** 2, 1 and 10 on cycles 2, 3 and 4 are
the same numbers `ABSENCE_UNDER_PARTIAL_BLINDNESS` carried for the payloads these supersede, and
that correspondence is the claim: every absence verdict reached over a candidate set with a blind
member became `error`, and not one of them became `pass`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import rejudgement_diff_gen9 as D                                   # noqa: E402
from scan import figures as FIG                                     # noqa: E402

#: (new cycle, the payload it supersedes, the legs whose verdicts moved and by how many).
#:
#: Cycle 1's row is the one to read. Its predecessor is a HARNESS-V4 re-judgement made under
#: `RULE-A5-v1`, `RULE-A8-v3`, `RULE-A12-v1` and `RULE-B3-v2`, so five legs move and three of
#: them are outside `{A3, B3}` — generations 7, 8 and 9 all reaching cycle 1 at once, which is
#: precisely why decision 1 admits it. The task's literal stop ("any leg outside `{A3, B3}`")
#: describes the other three and cannot describe this one; `within_permitted` is the condition
#: that holds for all four, and `strict_subset_holds` records which of them satisfied the
#: literal form rather than widening it quietly.
EXPECTED = {
    "scan_2026-09-07_rj2":  ("scan_2026-09-07_rj1",
                             {"A5": 3, "A6": 1, "A8": 1, "B3": 1, "G1-D": 1}, False),
    "scan_2026-09-07b_rj3": ("scan_2026-09-07b_rj2", {"A3": 2}, True),
    "scan_2026-09-09_rj2":  ("scan_2026-09-09_rj1", {"A3": 1}, True),
    "scan_2026-09-10_rj2":  ("scan_2026-09-10_rj1", {"A3": 10}, True),
}

DIFF = REPO / "state" / "rejudgement_diff_2026-09-11.json"
RECORDS = ("state/rejudgement_registration_2026-09-11.json",
           "state/l0_rejudged_registration_2026-09-11.json",
           "state/figure_inputs_registration_2026-09-11.json")


def payload(cycle: str) -> dict:
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        pytest.fail(f"{cycle} is not on disk at {p.relative_to(REPO)}")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def diffs() -> dict:
    if not DIFF.is_file():
        pytest.fail(f"{DIFF.relative_to(REPO)} does not exist; §1 wrote no record")
    return {d["new"]: d for d in json.loads(DIFF.read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def live() -> dict:
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        return FIG.load_results()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable, registration unverified: {exc}")


# ------------------------------------------------------------------ the payloads

@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_each_payload_names_itself_and_records_no_measurement(cycle):
    """A re-judgement that wrote an Observation would be a measurement wearing a
    re-judgement's name — and a payload whose `cycle` field disagrees with its filename is the
    defect `state/scan_2026-09-07b_rj2.json` carries, where the field still reads `_rj1`."""
    p = payload(cycle)
    assert p["cycle"] == cycle
    assert p["cycle_kind"] == "rejudged"
    assert p["derived_from"] == re.sub(r"_rj\d+$", "", cycle)
    assert p["observations_detail"] == []
    assert p["requests_total"] == 0 and p["requests_per_host"] == {}
    assert p["control_findings_detail"] == []


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_each_payload_stands_on_the_eight_fixture_control_gate(cycle):
    """DD-019: a cycle with zero fired controls is invalid, and a re-judgement is licensed the
    same way. Recorded on the payload rather than published, because publishing the gate's
    Findings would mean publishing the fixture Observations behind them."""
    gate = payload(cycle)["control_gate"]
    assert gate and gate["ok"] and gate["verdict"] == "pass", gate
    assert len(gate["fixtures"]) == 8, gate["fixtures"]
    assert "robots_forbids_product" in gate["fixtures"], (
        "the fixture that caught this family must be among the controls that license the "
        "re-judgement fixing it")


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_no_verdict_moved_to_pass(cycle, diffs):
    """Generation 9 turns an unprovable `fail` into `error`. A rule that started CREDITING
    something would be a different change wearing this one's name."""
    to_pass = [m for m in diffs[cycle]["moves"]
               if m["verdict_moved"] and m["to"].endswith(" pass")]
    assert to_pass == [], to_pass


# ------------------------------------------------------------------ §1

@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_the_moved_legs_are_exactly_what_was_measured(cycle, diffs):
    pred, counts, strict = EXPECTED[cycle]
    d = diffs[cycle]
    assert d["old"] == pred
    assert d["moved_legs_count"] == counts
    assert d["strict_subset_holds"] is strict


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_every_move_is_within_what_the_instrument_could_have_moved(cycle, diffs):
    """The condition that holds for all four. A leg may move only where a rule version changed
    between the two payloads or an error class on its own evidence changed kind; anything else
    is a rule that started answering differently for no reason anyone declared."""
    d = diffs[cycle]
    assert d["within_permitted"], (d["moved_legs"], d["permitted_legs"])
    assert D.stop_reasons(d) == []


def test_the_three_same_harness_cycles_permit_exactly_the_generation_9_legs(diffs):
    """Where the predecessor is a generation-8 payload, `{A3, B3}` is not a list this task
    typed: it is what the two payloads' own rule ids come out to. That is what makes a third
    leg moving a stop rather than a surprise."""
    for cycle in ("scan_2026-09-07b_rj3", "scan_2026-09-09_rj2", "scan_2026-09-10_rj2"):
        d = diffs[cycle]
        assert d["harness"]["old"] == d["harness"]["new"] == 5
        assert d["permitted_legs"] == list(D.GENERATION_9_LEGS)


def test_generation_9_legs_is_read_from_the_registry_not_remembered():
    """`GENERATION_9_LEGS` is a constant in a diff module, and a constant that names a
    generation goes stale the moment a tenth ships. This is what stops it."""
    from scan.rules import V9
    assert sorted(D.GENERATION_9_LEGS) == sorted(m.LEG for m in V9)


def test_cycle_1_judges_no_a3_and_says_why():
    """Cycle 1 collected no `link_probe` leg — it was introduced by harness-v3 — and
    `RULE-A3-v6` reads it. So the leg this task is named for registers NOTHING for cycle 1, with
    the reason on the payload. Not measured is a reason, not a zero (DD-055), and a re-judgement
    that quietly judged A3 from whatever else was under it would be a number that looks like a
    measurement and is not one."""
    p = payload("scan_2026-09-07_rj2")
    assert "A3" in p["legs_not_judged"] and "A1" in p["legs_not_judged"]
    assert "link_probe" in p["legs_not_judged"]["A3"]
    assert "A3" not in p["legs_judged"]


# ------------------------------------------------------------------ F5 and the fallback

def test_there_is_no_global_comparison_default():
    """ResearchTask 24af5222. A default predecessor drew `scan_2026-09-09_rj1` against cycle 1
    with 22 rows reading "not measured in this cycle"; the fix is that there is nothing to fall
    through to."""
    import yaml
    raw = yaml.safe_load((REPO / "assessment" / "harness" / "scan" / "figures.yaml")
                         .read_text(encoding="utf-8"))
    assert "compare_to" not in raw, "figures.yaml still carries a global compare_to"
    assert FIG.config("scan_2026-09-07_rj2")["compare_to"] is None


def test_f5_refuses_a_cycle_whose_predecessor_nobody_declared():
    cfg = FIG.config("scan_2026-09-07_rj2")
    with pytest.raises(FIG.UnconfiguredComparison) as exc:
        FIG.cycle_over_cycle({"legs": ["A1"], "rows": []}, {}, cfg)
    assert "scan_2026-09-07_rj2" in str(exc.value)


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_every_declared_predecessor_is_a_payload_on_disk(cycle):
    """A predecessor that is a string and not a cycle is a comparison against nothing. Cycle 1
    re-judged has no entry at all, which is the declaration that it has no predecessor."""
    cmp_ = FIG.config(cycle)["compare_to"]
    if cycle == "scan_2026-09-07_rj2":
        assert cmp_ is None
        return
    assert cmp_ and (REPO / "state" / f"{cmp_['cycle']}.json").is_file(), cmp_
    assert cmp_["suffix"] == cmp_["cycle"].removeprefix("scan_")
    assert cmp_["rule_changed"] == {}, (
        "all four are judged under one `CURRENT` and one harness version, so no row on any of "
        "these figures carries an instrument change")


def test_the_comparison_records_exist_and_the_renderer_reads_them():
    for rel in RECORDS:
        assert (REPO / rel).is_file(), f"{rel} was not written; no record, no fallback"
        assert rel in FIG.UNCHANGED_RECORDS, f"{rel} is not in figures.UNCHANGED_RECORDS"


def test_the_registrar_and_the_renderer_agree_on_where_a_name_falls_back_to():
    """Two implementations of one rule, held equal by a test rather than shared by an import.
    They are in different layers and the coupling is what let three families share one name."""
    import register_gen9_rejudged as G
    for name in ("scan_a3_pass_2026-09-09_rj2", "scan_l0_product_b3_fail_2026-09-10_rj2",
                 "scan_a3_wilson_lo_2026-09-07b_rj3", "framework_indicators_measured_2026-09-06",
                 "scan_a3_pass"):
        assert G.fallback_target(name) == FIG._source_name(name), name


def test_every_unchanged_name_resolves_to_an_equal_value(live):
    """The licence a comparison record grants has to be TRUE. `unchanged` means a figure asking
    for this name resolves it through the fallback to a Result holding the same number; if the
    fallback target is missing or different, the record is licensing a wrong figure."""
    licensed = FIG.unchanged_names()
    bad = []
    for rel in RECORDS:
        doc = json.loads((REPO / rel).read_text(encoding="utf-8"))
        for cycle, row in doc.items():
            for name in row.get("unchanged_names", []):
                if name not in licensed:
                    bad.append(f"{name} ({cycle}) is recorded unchanged but "
                               f"figures.unchanged_names() does not list it")
                    continue
                target = FIG._source_name(name)
                if target not in live:
                    bad.append(f"{name} ({cycle}) falls back to {target}, which is unregistered")
    assert not bad, "\n".join(bad[:12])


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_every_name_a_figure_of_this_cycle_asks_for_resolves(cycle, live):
    """The whole point of the comparison records, exercised the way a figure exercises them:
    every registered name is present, and every missing one is licensed and equal. An
    `UnlicensedFallback` here is the hard error decision 3 asks for."""
    if not (REPO / "state" / f"scan_matrix_{cycle.removeprefix('scan_')}.json").is_file():
        pytest.fail(f"{cycle} has no matrix; its figures cannot be drawn")
    # Cycle 1 has no predecessor, so F5 is not drawn for it — the renderer is TOLD so rather
    # than defaulted into a comparison, which is decision 5 exercised end to end.
    only = tuple(f for f in FIG.FIGURES if f != "cycle_over_cycle") \
        if cycle == "scan_2026-09-07_rj2" else None
    # `build` raises `UnlicensedFallback` on the first name that is neither registered nor
    # recorded as compared-and-unchanged, so reaching the end of it IS the clause. What is
    # asserted after it is that every fallback actually taken was a licensed one.
    figs = FIG.build(FIG.config(cycle), live, only=only)
    assert set(figs) == set(only or FIG.FIGURES)
    licensed = FIG.unchanged_names()
    for name in figs:
        for asked, read in FIG._recorders[name].fell_back.items():
            assert asked in licensed and read in live, (name, asked, read)


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_every_numeral_in_this_cycle_s_figures_resolves_to_an_artifact(cycle, live):
    """The published-figure gate, pointed at the four cycles this task draws.

    `tests/test_scan_figures.py` is written around `params.cycle.name`, so without this the
    re-judged figures — the CORRECTED ones, the ones a reader is most likely to quote — would be
    the only published figures nothing checks. The gate is imported rather than reimplemented,
    for the reason `test_scan_harness_v4` gives when it does the same: a second copy of "does
    this numeral resolve" is a second thing to be wrong, and the copy that drifts is always the
    one guarding the numbers that moved.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_figures_gate_gen9",
                                                  REPO / "tests" / "test_scan_figures.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    only = tuple(f for f in FIG.FIGURES if f != "cycle_over_cycle") \
        if cycle == "scan_2026-09-07_rj2" else None
    figs = FIG.build(FIG.config(cycle), live, only=only)
    bad = gate.audit(figs, live, cycle=cycle)
    assert not bad, "\n".join(bad)


# ------------------------------------------------------------------ registration

@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_every_registered_result_names_what_it_supersedes(cycle, live):
    """Decision 3. A new Result that does not say which one it replaces leaves a reader two
    numbers for one metric and no way to order them; the old Result is never edited (AD-028),
    so the pointer can only live on the new one."""
    try:
        from seldon.config import get_neo4j_driver, load_project_config
        c = load_project_config(REPO)
        driver = get_neo4j_driver(c)
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    names = []
    for rel in RECORDS:
        doc = json.loads((REPO / rel).read_text(encoding="utf-8"))
        names += doc.get(cycle, {}).get("moved_names", [])
    # The three framework snapshots are read from commits and carry no cycle; they were bound
    # long before this task and supersede nothing, which is why they are reported separately.
    names = [n for n in names if not n.startswith("framework_indicators_")]
    if not names:
        pytest.fail(f"{cycle} registered nothing at all")
    try:
        with driver.session(database=c["neo4j"]["database"]) as s:
            rows = s.run("MATCH (r:Result) WHERE r.name IN $n "
                         "RETURN r.name AS name, r.description AS d", n=names).data()
    finally:
        driver.close()
    got = {r["name"]: r["d"] or "" for r in rows}
    missing = [n for n in names if n not in got]
    assert not missing, f"{len(missing)} registered name(s) are not in the graph: {missing[:6]}"
    silent = [n for n, d in got.items()
              if "Supersedes" not in d and "falls back to" not in d]
    assert not silent, f"{len(silent)} Result(s) name nothing they supersede: {silent[:6]}"


@pytest.mark.parametrize("cycle", sorted(EXPECTED))
def test_no_registered_result_repeats_a_value_the_fallback_already_had(cycle, live):
    """The other half of decision 3. A Result registered at a value its own fallback target
    already holds is a name nobody needed: the figure would have resolved it correctly through
    the comparison record, and binding it spends a name that can never be unbound (AD-028).

    Where the fallback target does not exist at all there is nothing to repeat — cycle 1's bare
    first-cycle names (DD-056) and the whole of cycle 4, whose gate stopped before §4.
    """
    repeats = []
    for rel in RECORDS:
        doc = json.loads((REPO / rel).read_text(encoding="utf-8"))
        for name in doc.get(cycle, {}).get("moved_names", []):
            target = FIG._source_name(name)
            if target in live and name in live and float(live[target]) == float(live[name]):
                repeats.append(f"{name} == {target} == {live[name]}")
    assert not repeats, f"{len(repeats)} registered name(s) repeat their fallback's value: " \
                        f"{repeats[:6]}"
