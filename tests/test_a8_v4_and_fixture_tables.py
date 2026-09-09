"""`RULE-A8-v4`'s five branches, and control tables derived rather than written.

`cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md`.

Two properties, and the second is the one that generalises:

1. **A blind latest-vintage pointer is `error`.** `follow_latest_pointer` records
   `resolved: False` for four different things — an observed non-resolving status, a fetch that
   raised, a robots disallow, and the scanner's own off-host policy — and `RULE-A8-v3` read the
   flattened boolean and returned `fail`. Fourth instance of DD-052 §6 after A10, A1 and A3.
2. **The control tables are DERIVED from collector dispatch.** The `resets_links_only:A8` row
   was written by reading rule source, and it was wrong. A pre-registration method that
   produced one wrong row will produce another, so the method is retired and the table is
   checked against `fixture_expectations.py` — with neither side edited to match the other.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                          # noqa: E402
from scan.fixture_expectations import (check, collector_probes,       # noqa: E402
                                       leg_blocks, leg_probes)
from scan.model import Finding, Observation                           # noqa: E402
from scan.rules import CURRENT, REGISTRY, judge as judge_rule         # noqa: E402


def _run_module():
    spec = importlib.util.spec_from_file_location(
        "scan_run_a8v4", REPO / "assessment" / "harness" / "scan" / "run.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _a8_obs(params, pointers, declared=True):
    """One A8 observation carrying a `pointers_tried` list, built directly."""
    return Observation.make(
        "A8", "A8", "scan-x", "https://x/product", "structured_data", "0.1.0", params,
        {"method": "GET", "url": "https://x/product"},
        {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
         "bytes": 1, "elapsed_ms": 1},
        parsed={"keys": ["dateModified"] if declared else [],
                "latest": {"pointers_found": len(pointers),
                           "latest_pointer_resolves": any(p.get("resolved") for p in pointers),
                           "pointers_tried": pointers}})


# ------------------------------------------------------------------ 1. the five branches

def test_a_resolved_pointer_passes():
    params = load_params()
    f = judge_rule("RULE-A8-v4", [_a8_obs(params, [
        {"how": "href token", "url": "https://x/latest.csv", "status": 200,
         "resolved": True}])], params)
    assert f.verdict == "pass", f.reason
    assert f.blind_pointers is None


def test_an_observed_non_resolution_fails():
    """A status the host actually sent IS a measurement, and `fail` is the right answer."""
    params = load_params()
    f = judge_rule("RULE-A8-v4", [_a8_obs(params, [
        {"how": "href token", "url": "https://x/latest.csv", "status": 404,
         "resolved": False}])], params)
    assert f.verdict == "fail", f.reason
    assert "none of the 1" in f.reason
    assert f.blind_pointers is None


@pytest.mark.parametrize("ptr,why", [
    ({"how": "href token", "url": "https://x/latest.csv", "status": None,
      "resolved": False, "note": "ReadError"}, "the fetch raised"),
    ({"how": "href token", "url": "https://x/latest.csv", "status": None,
      "resolved": False, "note": "robots_disallowed"}, "nothing was fetched"),
])
def test_an_entirely_blind_pointer_is_error_not_fail(ptr, why):
    """The block. `RULE-A8-v3` returned `fail` on exactly this record
    (`cc_tasks/2026-09-08_scan_run_3_RESULT.md` §1) — a broken-pointer claim about a probe
    nobody observed."""
    params = load_params()
    obs = [_a8_obs(params, [ptr])]
    v3 = judge_rule("RULE-A8-v3", obs, params)
    v4 = judge_rule("RULE-A8-v4", obs, params)
    assert v3.verdict == "fail", "the recorded defect no longer reproduces under v3"
    assert v4.verdict == "error", (why, v4.reason)
    assert "UNOBSERVED" in v4.reason
    assert v4.blind_pointers == 1


def test_mixed_observed_and_blind_is_error_because_none_resolves_is_not_established():
    """The branch that is easy to get wrong: one pointer 404s and another was never seen. The
    404 is a measurement, but the unseen one might have resolved, so the rule may not conclude
    that the product has no working pointer."""
    params = load_params()
    f = judge_rule("RULE-A8-v4", [_a8_obs(params, [
        {"how": "href token", "url": "https://x/a.csv", "status": 404, "resolved": False},
        {"how": "anchor", "url": "https://x/b.csv", "status": None, "resolved": False,
         "note": "ReadError"}])], params)
    assert f.verdict == "error", f.reason
    assert "not established" in f.reason
    assert f.blind_pointers == 1


def test_off_host_is_scope_not_blindness():
    """`errors.CLASSES['off_host']` is not blind, and this rule must agree: an excluded
    candidate is out of the measurement, not unobserved within it. One resolved same-host
    pointer plus an off-host one is still a `pass`."""
    params = load_params()
    f = judge_rule("RULE-A8-v4", [_a8_obs(params, [
        {"how": "anchor", "url": "https://other.gov/signup", "status": None,
         "resolved": False, "off_host": True, "note": "off_host: not fetched"},
        {"how": "href token", "url": "https://x/latest.csv", "status": 200,
         "resolved": True}])], params)
    assert f.verdict == "pass", f.reason
    assert "excluded as off-host" in f.reason
    assert f.blind_pointers is None


def test_no_pointer_at_all_keeps_v3s_wording():
    """The branch v4 does NOT change. A surface that declares a date and offers nothing to
    follow fails for the reason it always failed for."""
    params = load_params()
    obs = [_a8_obs(params, [])]
    v3, v4 = (judge_rule("RULE-A8-v3", obs, params), judge_rule("RULE-A8-v4", obs, params))
    assert v3.verdict == v4.verdict == "fail"
    assert "offers no latest-vintage pointer on its own host" in v4.reason


def test_v4_agrees_with_v3_wherever_nothing_was_blind():
    """v4 changes the blind cases and nothing else."""
    params = load_params()
    for pointers in ([{"how": "h", "url": "https://x/a", "status": 200, "resolved": True}],
                     [{"how": "h", "url": "https://x/a", "status": 404, "resolved": False}],
                     []):
        obs = [_a8_obs(params, pointers)]
        assert (judge_rule("RULE-A8-v3", obs, params).verdict
                == judge_rule("RULE-A8-v4", obs, params).verdict), pointers


# ------------------------------------------------------------------ 2. derived tables

def test_the_derivation_reads_the_collectors_not_the_rules():
    """The three facts the derivation rests on, each read from source."""
    probes = collector_probes()
    deref = {fq for fq, i in probes.items() if i["dereference"]}
    assert deref == {"links.probe", "v2clauses.follow_latest_pointer"}, (
        "the set of collectors that dereference a discovered URL changed; the fixture tables "
        "derive from it")
    assert probes["links.probe"]["methods"] == {"HEAD"}
    assert probes["v2clauses.follow_latest_pointer"]["methods"] == {"HEAD"}
    # The shared link probe is dispatched through a PARAMETER, `if leg == lp["shared_leg"]`.
    # Resolving it is what makes A1 and A3 derivable rather than silently deferred.
    assert "link_probe" in leg_blocks()
    lp = leg_probes(["A1", "A3", "A8"])
    for leg in ("A1", "A3"):
        assert lp[leg]["consumes"] == ["link_probe"]
        assert lp[leg]["dereference_methods"] == {"HEAD"}
    assert lp["A8"]["dereference_methods"] == {"HEAD"}


def test_every_checked_in_table_agrees_with_the_derivation():
    """**Neither side is edited to match the other** (DD-061). A difference is a stop, reported
    line by line, and it is either a new blind-probe instance or a defect in the derivation."""
    run_mod = _run_module()
    out = check(load_params(), run_mod.CONTROL_FIXTURE_LEGS)
    assert out["derived"] > 0, "the derivation decided nothing; it is not checking anything"
    assert not out["differences"], "\n".join(
        f"{d['fixture']}:{d['leg']} table={d['table']} derived={d['derived']} — {d['why']}"
        for d in out["differences"])


def test_the_derivation_says_which_rows_it_stands_behind():
    """It derives blindness and defers content judgements, and every row says which. A script
    that claimed to derive `A12 = fail` on a refusing host would be guessing with a provenance
    trail, which is the method being retired."""
    run_mod = _run_module()
    out = check(load_params(), run_mod.CONTROL_FIXTURE_LEGS)
    assert out["deferred"] > 0
    hows = {i["how"] for f in out["per_fixture"].values() for i in f.values()}
    assert hows == {"derived", "deferred"}
    resets = out["per_fixture"]["resets_connection"]
    assert all(i["how"] == "derived" and i["verdict"] == "error" for i in resets.values()), (
        "a fixture that blinds every request must be fully derivable")


# ------------------------------------------------------------------ 3. the record

def test_the_blind_counts_are_fields_and_absent_when_unset():
    """Decision 3, and the property that keeps history re-derivable: a Finding that reports no
    blind count carries no such key, so its dict is what it was before the fields existed."""
    params = load_params()
    plain = Finding.make(rule_id="RULE-X-v1", rule_version="v1", leg="A8",
                         target_doc_id="d", verdict="pass", evidence=[], reason="r",
                         params=params)
    assert "blind_pointers" not in plain.to_dict()
    assert "blind_links" not in plain.to_dict()
    counted = Finding.make(rule_id="RULE-X-v1", rule_version="v1", leg="A8",
                           target_doc_id="d", verdict="error", evidence=[], reason="r",
                           params=params, blind_pointers=3)
    assert counted.to_dict()["blind_pointers"] == 3
    # …and the count is not an input to the id, or reporting it would re-identify the Finding.
    assert plain.finding_id == Finding.make(
        rule_id="RULE-X-v1", rule_version="v1", leg="A8", target_doc_id="d", verdict="pass",
        evidence=[], reason="r", params=params, blind_pointers=9).finding_id


def test_generation_six_is_new_modules_and_predecessors_are_untouched():
    import subprocess
    from scan.rules import V6
    assert {m.RULE_ID for m in V6} == {"RULE-A1-v4", "RULE-A3-v5", "RULE-A8-v4"}
    for rid in ("RULE-A8-v3", "RULE-A1-v3", "RULE-A3-v4", "RULE-A10-v3"):
        rel = Path(REGISTRY[rid].__file__).resolve().relative_to(REPO)
        r = subprocess.run(["git", "diff", "--stat", "HEAD", "--", str(rel)],
                           capture_output=True, text=True, cwd=str(REPO))
        assert not r.stdout.strip(), f"{rel} was edited: {r.stdout.strip()}"
    assert CURRENT["A8"] == "RULE-A8-v4"
