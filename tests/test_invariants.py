"""The invariants that hold across every cycle, whatever the rules were.

`cc_tasks/2026-09-10_harness_v5_blind.md` decision 5. One invariant so far, and it is the one
this repo has broken seven times in different disguises:

    **No verdict about a product rests on evidence nobody collected.**

DD-052 §6 says `error` must never mean the product failed; its mirror says `error` must never
mean the product passed. A `pass`/`fail` Finding whose cited Observations are ALL blind breaks
both at once — it is a measurement of the scanner, reported as a measurement of the product.

Why this lives in its own file rather than in a per-cycle test: the check is about payloads, all
of them, under the harness version each was judged with. A test parametrised over cycles is the
only shape that makes "this has been true since 2026-09-06" a thing the suite asserts rather
than a thing a RESULT claims.

**The history is pinned, not hidden.** Cycles 2, 3 and 4 were judged under harness-v4, where
`robots_disallowed` was scope rather than blindness, and they carry 6, 6 and 11 product verdicts
that rest on nothing. Those payloads are immutable: the counts are asserted exactly, as
`xfail(strict=True)`, so the day a re-judgement changes one the suite says so instead of
quietly agreeing.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import errors                                             # noqa: E402
from scan.rules import measures                                     # noqa: E402

PARAMS_REL = "assessment/harness/scan/params.yaml"

#: **Three counts, because "does this payload break the invariant" has three honest answers.**
#:
#: `UNDER_OWN_HARNESS` — judged the way it was judged. Every stored payload is internally
#: consistent with the reading in force when it was measured, and this is 0 everywhere. That is
#: not a hollow result: it says no cycle ever broke its OWN rules, which is what makes the
#: re-derivation gate meaningful.
#:
#: `UNDER_V5` — the same payloads read with `robots_disallowed` as blindness. This is the defect
#: harness-v5 exists to fix and the work `2026-09-10_rejudge_2_3_4.md` has to clear: 6, 6 and 11
#: product verdicts resting on pages nobody was allowed to read.
#:
#: `UNDER_V5_ALL_RULES` — the same again without the host/product distinction: 9, 9 and 14, the
#: numbers `2026-09-10_scan_run_4_RESULT.md` §1 reports. The difference is A12's three per cycle,
#: whose subject IS the refusal (`MEASURES = "host"`). Both are pinned so neither can be quietly
#: dropped and the two ways of counting stay reconcilable.
CYCLES = ("scan_smoke_2026-09-06", "scan_controls_2026-09-06", "scan_2026-09-07",
          "scan_2026-09-07_controls", "scan_2026-09-07b", "scan_2026-09-07_rj1",
          "scan_2026-09-07b_rj1", "scan_2026-09-09", "scan_2026-09-10",
          # The harness-v5 re-judgements (`cc_tasks/2026-09-10_rejudge_2_3_4.md` decision 1).
          # Zero in every column, which is the point of them: the same Observations, judged by
          # a layer that knows a forbidden page was never read.
          "scan_2026-09-07b_rj2", "scan_2026-09-09_rj1", "scan_2026-09-10_rj1")

UNDER_OWN_HARNESS = {c: 0 for c in CYCLES}

#: Cycle 1 carries the same six as cycle 2 and was not in `scan_run_4`'s count, which looked at
#: the three most recent payloads only. All four measured cycles carry it; the two `_rj1`
#: re-judgements do not, because both re-judged EIA's flagship out of the set that reaches these
#: rules. That is the first evidence that a re-judgement clears the defect.
UNDER_V5 = {**{c: 0 for c in CYCLES},
            "scan_2026-09-07": 6, "scan_2026-09-07b": 6,
            "scan_2026-09-09": 6, "scan_2026-09-10": 11}

UNDER_V5_ALL_RULES = {**{c: 0 for c in CYCLES},
                      "scan_2026-09-07": 9, "scan_2026-09-07b": 9,
                      "scan_2026-09-09": 9, "scan_2026-09-10": 14}


def params_for(payload: dict) -> dict:
    """The parameter set a cycle was MEASURED under, recovered from git BY HASH.

    The same recovery `tests/test_scan_harness_v4.py` uses, and the reason harness versioning
    works at all: a payload measured before `harness_version` existed recovers a params set that
    binds none, which `errors.harness_of` reads as 4.
    """
    import yaml
    from scan.model import params_hash
    want = payload.get("params_hash")
    revs = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_REL],
                          capture_output=True, text=True, cwd=REPO).stdout.split()
    for rev in revs:
        blob = subprocess.run(["git", "show", f"{rev}:{PARAMS_REL}"],
                              capture_output=True, text=True, cwd=REPO).stdout
        if not blob:
            continue
        cand = yaml.safe_load(blob)
        if params_hash(cand) == want:
            return cand
    pytest.skip(f"no committed params.yaml hashes to {str(want)[:12]}…")


def blind_verdicts(payload: dict, product_only: bool = True, harness: int | None = None) -> list:
    """`[(rule_id, target)]` for pass/fail Findings whose every cited Observation is blind.

    `harness` defaults to the version the payload was JUDGED under, recovered from its own
    params; pass one explicitly to ask what a different reading would say of the same evidence.
    Both questions are real and they have different answers, which is the whole subject here.
    """
    harness = harness if harness is not None else errors.harness_of(params_for(payload))
    unobservable = set((params_for(payload).get("manners") or {})
                       .get("unobservable_statuses") or ())
    obs = {o["obs_id"]: o for o in payload["observations_detail"]}

    def seen(o) -> bool:
        if errors.is_blind(o.get("error_class"), harness):
            return False
        return (o.get("response") or {}).get("status") not in unobservable

    out = []
    for f in payload["findings_detail"] + payload.get("control_findings_detail", []):
        if f["verdict"] not in ("pass", "fail"):
            continue
        if product_only and measures(f["rule_id"]) != "product":
            continue
        cited = [obs[e] for e in f.get("evidence", []) if e in obs]
        if cited and not any(seen(o) for o in cited):
            out.append((f["rule_id"], f["target_doc_id"]))
    return out


def _payload(cycle: str) -> dict:
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        pytest.skip(f"{cycle} is not on disk")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.mark.parametrize("cycle", CYCLES)
def test_no_verdict_rests_on_unobserved_evidence(cycle):
    """The invariant, under the harness version each payload was actually judged with.

    Green for all nine, and that is the claim: no cycle has ever broken the reading it was
    measured under. What harness-v5 changes is the reading, and `test_the_v5_reading_…` below is
    where that shows up.
    """
    bad = blind_verdicts(_payload(cycle))
    assert len(bad) == UNDER_OWN_HARNESS[cycle], (
        f"{len(bad)} product verdict(s) in {cycle} rest on wholly blind evidence under its own "
        f"harness version: {bad[:6]}{'…' if len(bad) > 6 else ''}")


def _v5_marks(cycle: str):
    n = UNDER_V5[cycle]
    if n:
        return (pytest.mark.xfail(strict=True, reason=(
            f"{cycle} was measured under harness-v4, where a robots disallow was scope rather "
            f"than blindness. Read with v5's eyes it carries {n} product verdicts that rest on "
            f"pages nobody was allowed to read. The payload is immutable — the fix is a "
            f"re-judgement into a new payload, not an edit — so this is pinned as a strict "
            f"xfail and `test_the_v5_counts_are_exactly_what_was_measured` asserts the number.")),)
    return ()


@pytest.mark.parametrize("cycle", [pytest.param(c, marks=_v5_marks(c)) for c in CYCLES])
def test_the_v5_reading_of_every_payload(cycle):
    """The same payloads, read as harness-v5 reads them. Zero for six of the nine; the three
    that carry the defect are strict xfails with their counts asserted below."""
    bad = blind_verdicts(_payload(cycle), harness=5)
    assert bad == [], (
        f"{len(bad)} product verdict(s) in {cycle} rest on blind evidence under harness-v5: "
        f"{bad[:6]}{'…' if len(bad) > 6 else ''}")


@pytest.mark.parametrize("cycle", CYCLES)
def test_the_v5_counts_are_exactly_what_was_measured(cycle):
    """The other half of pinning: the xfail says "this still fails", this says "by this much".
    Drift in either direction is a re-judgement nobody declared."""
    assert len(blind_verdicts(_payload(cycle), harness=5)) == UNDER_V5[cycle]


@pytest.mark.parametrize("cycle", CYCLES)
def test_the_all_rules_count_matches_the_scan_run_4_result(cycle):
    """9, 9 and 14 — the numbers `2026-09-10_scan_run_4_RESULT.md` §1 reports, which count A12's
    three host verdicts per cycle alongside the product ones."""
    assert len(blind_verdicts(_payload(cycle), harness=5,
                              product_only=False)) == UNDER_V5_ALL_RULES[cycle]


def test_a12_is_the_only_leg_that_declares_a_non_product_subject():
    """`MEASURES` is a declaration, not a list of exemptions — but a declaration nobody audits is
    a list of exemptions with extra steps. This is the audit."""
    from scan.rules import REGISTRY
    host_rules = sorted(r for r in REGISTRY if measures(r) == "host")
    assert host_rules == ["RULE-A12-v1", "RULE-A12-v2"], (
        f"a rule declared a non-product subject: {host_rules}. Every such rule opts out of the "
        f"harness-v5 invariant, so each one needs a reason on its face.")

# ===================================================== the second reading (decision 4, 2026-09-11)
#
# "No verdict on WHOLLY blind evidence" is the first reading and it is not enough. A rule can
# cite an observed product page, exclude a blind candidate, and then assert that the object the
# blind candidate might have been is not there. That is the eighth instance of the family, found
# by the `robots_forbids_product` control fixture
# (`cc_tasks/2026-09-11_control_fixture_robots_forbids_product_RESULT.md` §1), and the first
# reading reports 0 on every payload that carries it.
#
# So this counts, per stored payload, the `fail` verdicts from ABSENCE-claim rules that cite at
# least one blind candidate. The numbers are the finding, and they are what decides whether
# cycles 2 to 4 need a third re-judgement — a decision for the next task, which is why THIS task
# re-judges nothing.
#
# **The harness-v5 re-judgements did not clear it.** `scan_2026-09-10_rj1` carries 10, one MORE
# than the 9 in the cycle it re-judged: under v5 `robots_disallowed` became BLIND, so more
# findings cite a blind candidate, and `RULE-A3-v5` went on excluding them and answering anyway.
#: payload -> `fail` verdicts from absence-claim rules that excluded at least one blind candidate.
ABSENCE_UNDER_PARTIAL_BLINDNESS = {
    "scan_smoke_2026-09-06": 0,
    "scan_controls_2026-09-06": 0,
    "scan_2026-09-07": 1,
    "scan_2026-09-07_controls": 0,
    "scan_2026-09-07b": 5,
    "scan_2026-09-07_rj1": 0,
    "scan_2026-09-07b_rj1": 5,
    "scan_2026-09-09": 5,
    "scan_2026-09-10": 9,
    "scan_2026-09-07b_rj2": 2,
    "scan_2026-09-09_rj1": 1,
    "scan_2026-09-10_rj1": 10,
}


def _observations(payload: dict) -> dict:
    """`{obs_id: observation}`, resolving a Findings-only payload through the cycle it names.

    A re-judgement creates no Observation — its evidence lives in `derived_from`. Reading
    `observations_detail` alone would report 0 for all three `_rj` payloads, which is not a
    measurement, it is the absence of one.
    """
    import importlib.util
    rows = payload.get("observations_detail")
    if not rows:
        spec = importlib.util.spec_from_file_location(
            "rederive_inv", REPO / "assessment" / "harness" / "scan" / "rederive.py")
        rd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rd)
        rows = [o.to_dict() if hasattr(o, "to_dict") else o
                for o in rd.observations_for(payload)]
    out = {}
    for o in rows:
        o = o if isinstance(o, dict) else o.to_dict()
        out[o["obs_id"]] = o
    return out


def absence_under_partial_blindness(payload: dict) -> list:
    """`[(rule_id, leg, target)]` for `fail` verdicts from absence-claim rules whose cited
    evidence includes a blind candidate."""
    from scan.rules import claim_of
    harness = errors.harness_of(params_for(payload))
    obs = _observations(payload)
    out = []
    for f in payload["findings_detail"]:
        if f["verdict"] != "fail" or measures(f["rule_id"]) != "product":
            continue
        if claim_of(f["rule_id"]) != "absence":
            continue
        cited = [obs[e] for e in f.get("evidence", []) if e in obs]
        if any(errors.is_blind(o.get("error_class"), harness) for o in cited):
            out.append((f["rule_id"], f["leg"], f["target_doc_id"]))
    return out


def _absence_marks(cycle: str):
    n = ABSENCE_UNDER_PARTIAL_BLINDNESS[cycle]
    if n:
        return (pytest.mark.xfail(strict=True, reason=(
            f"{cycle} carries {n} absence verdict(s) reached over a candidate set with a blind "
            f"member. `RULE-A3-v6` and `RULE-B3-v3` fix the rules; the payloads are immutable "
            f"and whether they are re-judged is the next task's decision. Pinned strict so that "
            f"decision shows up as a change here.")),)
    return ()


@pytest.mark.parametrize("cycle", [pytest.param(c, marks=_absence_marks(c)) for c in CYCLES])
def test_no_absence_verdict_rests_on_partially_blind_evidence(cycle):
    """Decision 4's reading. Zero on the payloads that carry none; a strict xfail, with its
    count asserted below, on the five that do."""
    bad = absence_under_partial_blindness(_payload(cycle))
    assert bad == [], (
        f"{len(bad)} absence verdict(s) in {cycle} were reached over a candidate set with a "
        f"blind member: {bad[:5]}{'…' if len(bad) > 5 else ''}")


@pytest.mark.parametrize("cycle", CYCLES)
def test_the_absence_counts_are_exactly_what_was_measured(cycle):
    """The other half of pinning. A drift either way is a re-judgement nobody declared."""
    assert len(absence_under_partial_blindness(_payload(cycle))) == \
        ABSENCE_UNDER_PARTIAL_BLINDNESS[cycle]
