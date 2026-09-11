"""An absence claim over a candidate set with a blind member is a scope limitation.

`cc_tasks/2026-09-11_absence_claims_under_scope_limitation.md`.

**The prior art is the auditor's, not ours.** ISA 705 / AU-C 705: where sufficient appropriate
evidence cannot be obtained on a material item, the response is a qualified opinion or a
disclaimer — never an adverse opinion on the item nobody examined. In knowledge representation
it is the open-world assumption: negation as failure is unsound over a set known to be
incomplete. `error` is this harness's disclaimer, and DD-052 §6 is why.

The distinction the whole task turns on: **existence verified from what was observed stands;
absence asserted over a set with forbidden members does not.** `RULE-A1-v4` returns `pass` on the
`robots_forbids_product` fixture with three of its links forbidden, and that is right — it found
`text/csv` on a link it fetched, and unfetched links cannot unfind it. `RULE-A3-v5` returned
`fail` on the same evidence, and that is not.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "tests"))

from scan.rules import CURRENT, REGISTRY, claim_of, measures     # noqa: E402
from support.sourcescan import strip_prose                       # noqa: E402

CLAIMS = ("existence", "absence")

#: A blind guard, by any of its names. `absence_verdict` is the shared helper this task adds;
#: `unobserved_error` is what `rule_a5_v2` and `rule_a8_v4` already used to do the same job by
#: hand, before there was a helper to share. The lint asks whether the rule GUARDS, not whether
#: it calls one particular function — a lint that demanded the new name would report two correct
#: rules as defective and would have stopped this task for nothing.
GUARDS = ("absence_verdict", "unobserved_error")


def dereferencing_legs() -> set:
    """Legs that fetch something beyond the surface page, read from collector dispatch."""
    import importlib.util
    from scan.fixture_expectations import leg_probes
    spec = importlib.util.spec_from_file_location(
        "runmod_abs", REPO / "assessment" / "harness" / "scan" / "run.py")
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    probes = leg_probes(R.CONTROL_FIXTURE_LEGS)
    legs = {leg for leg, v in probes.items() if v.get("dereference_methods")}
    # B3's candidates are the methodology documents the RUNNER appends after the product page,
    # so they do not show up as a `dereference` on its collector. Named here rather than
    # inferred, because the runner's behaviour is not visible in `leg_probes`.
    return legs | {"B3"}


def source_of(rule_id: str) -> str:
    return strip_prose(Path(REGISTRY[rule_id].__file__).read_text(encoding="utf-8"))


def test_every_current_leg_resolves_a_claim():
    """Decision 2. `existence` or `absence` for every leg a cycle judges — from the module where
    it declares one, from `CLAIM_BY_LEG` where its current module is shipped and may not be
    edited."""
    unclassified = {leg: rid for leg, rid in CURRENT.items()
                    if claim_of(rid) not in CLAIMS}
    assert unclassified == {}, unclassified


def test_the_module_wins_over_the_table():
    """New modules declare on themselves, as `rule_a12_v2` declares its own `MEASURES`. The
    table answers only where no module speaks, so it shrinks as modules turn over."""
    from scan.rules import CLAIM_BY_LEG
    assert getattr(REGISTRY["RULE-A3-v6"], "CLAIM", None) == "absence"
    assert getattr(REGISTRY["RULE-B3-v3"], "CLAIM", None) == "absence"
    assert claim_of("RULE-A3-v6") == "absence"
    assert set(CLAIM_BY_LEG) <= set(CURRENT), "the table names a leg no cycle judges"


def test_every_absence_rule_that_dereferences_guards_its_claim():
    """**The lint, and §1's stop condition.** An absence-claim rule that fetches candidates
    beyond the surface page must route its `fail` through a blind guard. Anything else is a
    rule that could not look at the candidate deciding it is not there."""
    deref = dereferencing_legs()
    unguarded = []
    for leg, rid in sorted(CURRENT.items()):
        if claim_of(rid) != "absence" or leg not in deref:
            continue
        if not any(g in source_of(rid) for g in GUARDS):
            unguarded.append((leg, rid))
    assert unguarded == [], (
        f"absence-claim rules that dereference and never consult a blind guard: {unguarded}. "
        f"Each is an instance of the family: a verdict about the product from a probe the "
        f"collector was not allowed to make.")


def test_an_existence_rule_does_not_call_the_absence_helper():
    """The other half of decision 2. `absence_verdict` turns a not-found into `error`; an
    existence rule's `pass` is established by what it saw and must not be disclaimed away."""
    wrong = [(leg, rid) for leg, rid in sorted(CURRENT.items())
             if claim_of(rid) == "existence" and "absence_verdict" in source_of(rid)]
    assert wrong == [], wrong


def test_the_four_absence_rules_that_dereference_are_the_expected_ones():
    """Pinned. §1 stops on a fifth appearing — that would be a ninth instance of the family and
    the RESULT names it before anything else is written.

    The task file expected three: A3, A8 and B3. **A5 is a fourth** and was already compliant;
    it is the rule that stated the principle before there was a helper. Recorded here so the
    next reader inherits the corrected list rather than the task file's.
    """
    deref = dereferencing_legs()
    absence_deref = sorted(leg for leg, rid in CURRENT.items()
                           if claim_of(rid) == "absence" and leg in deref)
    assert absence_deref == ["A3", "A5", "A8", "B3"], absence_deref


def test_the_helper_is_the_three_cases_it_claims_to_be():
    """`absence_verdict` itself, on synthetic candidates: found → caller proceeds; none found
    with a blind candidate → `error`; none found with nothing blind → caller proceeds."""
    from scan import load_params
    from scan.model import Observation
    from scan.rules import _common as c
    params = load_params()

    def obs(cls):
        return Observation.make("A3", "A3", "control:x", "http://127.0.0.1/x", "links", "0.1.0",
                                params, {"method": "HEAD", "url": "http://127.0.0.1/x"},
                                {"status": None, "headers": {}, "body_sha256": None,
                                 "body_path": None, "bytes": 0, "elapsed_ms": 0},
                                error_class=cls)

    blind_one, seen_one = obs("robots_disallowed"), obs(None)
    assert c.absence_verdict("RULE-A3-v6", "A3", [seen_one], params,
                             candidates=[seen_one, blind_one], blind=[blind_one],
                             found=[seen_one], what="x") is None, "a found object stands"
    assert c.absence_verdict("RULE-A3-v6", "A3", [seen_one], params,
                             candidates=[seen_one], blind=[], found=None,
                             what="x") is None, "nothing blind: the caller's fail is a measurement"
    f = c.absence_verdict("RULE-A3-v6", "A3", [seen_one], params,
                          candidates=[seen_one, blind_one], blind=[blind_one], found=None,
                          what="whether the product offers a whole-product download")
    assert f is not None and f.verdict == "error"
    assert "cannot be established" in f.reason and "robots_disallowed" in f.reason
