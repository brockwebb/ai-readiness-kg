"""The eighth control fixture, and the two rules it caught on its first run.

`cc_tasks/2026-09-11_control_fixture_robots_forbids_product.md`.

The seven-fixture set is UNIFORM: each is served, refused, or reset for everything. None of them
can produce the state cycle 4 shipped from a federal host — a product page that IS readable,
carrying links the scanner is FORBIDDEN to follow. That is why harness-v5's BLIND/SCOPE change
moved zero derived control rows, and why the class was found four times by reading payloads and
zero times by the gate.

**This fixture fired on its first run, which is what a positive control is for.** A10 replays the
cycle-4 incident exactly — `pass` under harness-v4, `error` under v5. And two rules that
harness-v5 did NOT fix returned a verdict about the product from a probe they were forbidden to
make. The task's decision 4 says any such rule is a stop, so this task registered no Results,
wired nothing into `make guards` or the agreement gate, and reports.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

FIXTURE = "robots_forbids_product"
DIR = REPO / "assessment" / "harness" / "scan" / "fixtures" / FIXTURE

#: The legs whose DECISIVE probe the partition forbids, and what each returned. Pinned by value
#: so the next task's fix is visible as a change here rather than as a silent improvement.
#: `expected` is `params.e5_control.expected_verdicts[FIXTURE]`, derived under decision 2.
MEASURED = {"A10": "error", "A8": "error", "A3": "fail", "B3": "fail", "A1": "pass"}

#: The two the fixture caught. Each asserts the ABSENCE of exactly the object it was forbidden
#: to fetch.
UNSOUND = {
    "A3": ("RULE-A3-v5", "fail",
           "the link anchored 'whole-product archive' (/bulk/estimates-2026.zip) is forbidden, "
           "and the verdict is 'no whole-product download'"),
    "B3": ("RULE-B3-v2", "fail",
           "/methodology.html is forbidden, and the verdict is 'no structured-text methodology "
           "document reachable from the product surface'"),
}


def _run_module():
    spec = importlib.util.spec_from_file_location(
        "runmod_rfp", REPO / "assessment" / "harness" / "scan" / "run.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def cycle(tmp_path_factory):
    """The fixture's observations and findings, from one loopback run under a virtual clock.

    **Evidence is staged into a tmp directory.** `run_surface` stores bodies through
    `model.store_evidence`, which writes to `model.EVIDENCE_ROOT` — the COMMITTED store by
    default. Only `run.py::main` may add to that (DD-063's cycle licence), so an unlicensed
    write is redirected to quarantine and logged, and `make guards` then reports the litter.
    A test that leaves 35 redirect lines behind on every suite run turns a guard into noise;
    redirecting the root is what `run.py::main` itself does before collecting anything.
    """
    from scan.clock import VirtualClock
    from scan.fixtures.server import FixtureServer
    from scan.manners import Fetcher
    from scan import load_params
    from scan import model as _model
    R = _run_module()
    params = load_params()
    staged = tmp_path_factory.mktemp("rfp_evidence")
    prior, _model.EVIDENCE_ROOT = _model.EVIDENCE_ROOT, staged
    try:
        return _run(R, params, FixtureServer, Fetcher, VirtualClock)
    finally:
        _model.EVIDENCE_ROOT = prior


def _run(R, params, FixtureServer, Fetcher, VirtualClock):
    with FixtureServer(FIXTURE) as base:
        target = {"doc_id": f"control:{FIXTURE}", "url": f"{base}/index.html"}
        obs, findings = R.run_surface(R.specs(), target, params,
                                      R.CONTROL_FIXTURE_LEGS,
                                      Fetcher(params, clock=VirtualClock()))
    return {"obs": obs, "findings": findings, "params": params,
            "by_id": {o.obs_id: o for o in obs},
            "by_leg": {f.leg: f for f in findings}}


# ------------------------------------------------------------------ the fixture itself

def test_the_partition_is_declared_and_not_inferred():
    """DD-061. The manifest names every forbidden path, which legs probe it, and which collector
    dispatches that probe — read from `leg_probes`, never from a rule module."""
    import json
    man = json.loads((DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    forbidden = {r["path"] for r in man["partition"]["forbidden"]}
    robots = (DIR / "robots.txt").read_text(encoding="utf-8")
    declared = {l.split(":", 1)[1].strip() for l in robots.splitlines()
                if l.startswith("Disallow:")}
    assert forbidden <= declared, f"the manifest names a path robots.txt does not forbid: " \
                                  f"{sorted(forbidden - declared)}"


def test_the_forbidden_invalid_route_matches_the_collectors_own_suffix():
    """The fixture and the collector may not disagree about which path is 'the invalid one'.
    `invalid_route_unobserved` reads the suffix from params when it binds; this one writes it
    into a robots rule, so it is asserted instead."""
    from scan import load_params
    suffix = load_params()["a10_soft404"]["invalid_path_suffix"]
    robots = (DIR / "robots.txt").read_text(encoding="utf-8")
    assert any(l.startswith("Disallow:") and l.strip().endswith(suffix)
               for l in robots.splitlines()), \
        f"no Disallow line ends with {suffix!r}; the fixture would not blind A10's probe"


def test_the_fixture_actually_forbids_probes(cycle):
    """§1's stop condition, as a standing check: a partition that lands on no probe path is a
    fixture that does not exercise the class."""
    forbidden = [o for o in cycle["obs"] if o.error_class == "robots_disallowed"]
    assert len(forbidden) >= 4, f"only {len(forbidden)} forbidden probes; the partition missed"
    assert {o.collector for o in forbidden} >= {"links", "http"}


def test_only_loopback_was_contacted(cycle):
    """Loopback only. Asserted from the observations' own URLs, not from intent."""
    import urllib.parse
    hosts = {urllib.parse.urlsplit(o.target_url).hostname
             for o in cycle["obs"] if (o.target_url or "").startswith("http")}
    off = sorted(h for h in hosts if h not in (None, "127.0.0.1", "localhost")
                 and o_ok(h))
    assert off == [], f"a non-loopback host was contacted: {off}"


def o_ok(host: str) -> bool:
    """An `off_host` link is RECORDED with its URL and never fetched, so its hostname appears in
    the log without a request having been made. `creativecommons.org` is such a link on the
    fixture page."""
    return host not in ("creativecommons.org",)


# ------------------------------------------------------------------ decision 3: the replay

def test_a10_replays_the_cycle_4_incident_red_under_v4_green_under_v5(cycle):
    """**The incident, at the control layer where it was missing.**

    Cycle 4 recorded `pass` from "deep link HTTP 200; invalid route correctly HTTP None" on a
    surface whose probes robots forbade. Under harness-v4 this fixture reproduces that verdict;
    under v5 the same observations yield `error`. No rule module differs between the two runs —
    one entry in `errors.CLASSES` does.
    """
    import copy
    from scan.rules import CURRENT, consumes, judge as judge_rule
    p5 = cycle["params"]
    p4 = copy.deepcopy(p5)
    p4["harness_version"] = 4
    by_leg = {}
    for o in cycle["obs"]:
        by_leg.setdefault(o.leg, []).append(o)
    rid = CURRENT["A10"]
    group = list(by_leg.get("A10", []))
    for c in consumes(rid):
        group += by_leg.get(c, [])
    assert group, "A10 collected nothing on this fixture"
    assert judge_rule(rid, group, p4).verdict == "pass", (
        "RED: harness-v4 must reproduce the incident, or the fixture is not the incident")
    assert judge_rule(rid, group, p5).verdict == "error", (
        "GREEN: harness-v5 must refuse a verdict from a probe that was never issued")


def test_exactly_one_leg_moves_between_the_harness_versions(cycle):
    """A10 and no other. If a second leg starts moving, the class has been found somewhere new
    and the RESULT's accounting is stale."""
    import copy
    from scan.rules import CURRENT, consumes, judge as judge_rule
    p5 = cycle["params"]
    p4 = copy.deepcopy(p5)
    p4["harness_version"] = 4
    by_leg = {}
    for o in cycle["obs"]:
        by_leg.setdefault(o.leg, []).append(o)
    moved = []
    R = _run_module()
    for leg in R.CONTROL_FIXTURE_LEGS:
        rid = CURRENT.get(leg)
        if not rid:
            continue
        group = list(by_leg.get(leg, []))
        for c in consumes(rid):
            group += by_leg.get(c, [])
        if not group:
            continue
        if judge_rule(rid, group, p4).verdict != judge_rule(rid, group, p5).verdict:
            moved.append(leg)
    assert moved == ["A10"], moved


# ------------------------------------------------------------------ decision 4: the stop

@pytest.mark.parametrize("leg", sorted(UNSOUND))
@pytest.mark.xfail(strict=True, reason=(
    "THE FINDING. RULE-A3-v5 and RULE-B3-v2 return `fail` — an ABSENCE claim — about the exact "
    "object the partition forbade them to fetch. Harness-v5 did not fix this: the all-blind "
    "guard does not fire, because each verdict also cites the product page, which WAS observed. "
    "Pinned strict so the next task's fix shows up as a change here. "
    "cc_tasks/2026-09-11_control_fixture_robots_forbids_product_RESULT.md §1."))
def test_no_rule_claims_absence_of_an_object_it_was_forbidden_to_fetch(cycle, leg):
    """The asymmetry this fixture exposes, stated as the property that should hold.

    A verdict from PARTIAL evidence is sound when it is positive — A1 finds structured data on a
    link it fetched, and three forbidden links cannot unfind it. It is unsound when it is an
    absence claim: A3's "no whole-product download" and B3's "no methodology document" are
    exactly the propositions the forbidden probes would have settled.

    `RULE-A1-v4`'s docstring chose "some blind → judge over the rest, with the blind count on the
    Finding", and for an existential-positive leg that is right. This is the case it does not
    cover.
    """
    f = cycle["by_leg"][leg]
    blind = [cycle["by_id"][e] for e in f.evidence
             if e in cycle["by_id"] and cycle["by_id"][e].error_class == "robots_disallowed"]
    assert not (blind and f.verdict == "fail"), (
        f"{f.rule_id} returned {f.verdict!r} while {len(blind)} of its probes were forbidden: "
        f"{UNSOUND[leg][2]}")


def test_the_measured_verdicts_are_exactly_what_the_result_reports(cycle):
    """Pinned by value. The RESULT quotes these; a change to any of them is a change to the
    finding and must move this line with it."""
    got = {leg: cycle["by_leg"][leg].verdict for leg in MEASURED}
    assert got == MEASURED, got


def test_the_pre_registered_table_was_not_edited_to_match_what_came_out(cycle):
    """`params.yaml` says it outright: a gate whose expectation is edited to match its output is
    not a gate. The table expects `error` for A3 and B3; they return `fail`; that mismatch is
    the finding and it stays."""
    table = cycle["params"]["e5_control"]["expected_verdicts"][FIXTURE]
    assert table["A3"] == "error" and table["B3"] == "error"
    assert cycle["by_leg"]["A3"].verdict == "fail"
    assert cycle["by_leg"]["B3"].verdict == "fail"
