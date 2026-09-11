"""Leg-rate Result names say which family's rate they are.

`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decisions 2 and 4, from the six Results
`cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §1 records as bound to the wrong population.

**The cause is narrower than the previous RESULT stated, and the fix is wider.** The shipped
`build_l0_matrices` emitted `scan_leg_rate_<leg>_upper95` from two families — host and product —
whose legs are DISJOINT (tier 0 versus `PRODUCT_LEGS`), so no name ever collided there. It was
safe by coincidence. `register_l0_rejudged.py` then asked a third family, Tier C, for the same
stat over tier-0 legs, and the coincidence ran out: six Tier C values went in under names whose
originals were host values.

A scheme that is correct only while two lists stay disjoint is a scheme waiting for a third
caller. So the family is in the name, and the registrar refuses the unprefixed form at the choke
point every caller passes through rather than in the one emitter that happened to be careful.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import build_l0_matrices as B                                       # noqa: E402
import cycle_results                                                # noqa: E402

CYCLE = "scan_2026-09-09_rj1"


def _emitted(cycle: str) -> dict:
    """`{family: [name, …]}` for every name the three families emit for one cycle."""
    import register_l0_rejudged as R
    out = {}
    for fam, (counts, prefix, population, family) in R.families(cycle).items():
        out[fam] = [cycle_results.name_for(base, cycle)
                    for base, _v, _n in B.leg_results(counts, prefix, cycle, population,
                                                      with_upper95=True, family=family)]
    return out


def test_no_two_families_emit_the_same_name():
    """The collision test decision 2 asks for. Not 'these two happen not to overlap' — no pair,
    for any leg, ever."""
    emitted = _emitted(CYCLE)
    fams = sorted(emitted)
    for i, a in enumerate(fams):
        for b in fams[i + 1:]:
            shared = sorted(set(emitted[a]) & set(emitted[b]))
            assert shared == [], f"{a} and {b} both emit {shared}"


def test_every_leg_rate_name_carries_its_family():
    emitted = _emitted(CYCLE)
    for fam, names in emitted.items():
        for n in names:
            if "leg_rate" in n:
                assert n.startswith(f"scan_l0_{fam}_leg_rate_"), n


def test_the_emitter_refuses_to_compute_a_rate_with_no_family():
    """`with_upper95` without a `family` is the exact call that produced the six. It raises now
    rather than emitting a name that cannot say what it measures."""
    with pytest.raises(ValueError, match="needs a `family`"):
        B.leg_results({"A4": {"pass": 1, "fail": 0, "error": 0, "not_applicable": 0,
                              "applicable_n": 1, "wilson_hi": 1.0, "wilson_lo": 0.0}},
                      "scan_l0_", CYCLE, "a population", with_upper95=True)


@pytest.mark.parametrize("name", [
    "scan_leg_rate_a4_upper95_2026-09-09_rj1",
    "scan_leg_rate_g1_d_upper95_scan_2026-09-11",
])
def test_the_registrar_refuses_an_unprefixed_leg_rate_name(name):
    """Decision 4, at the choke point. Every registrar in the repo goes through `check_names`,
    so this cannot be reintroduced by a new caller that forgets."""
    cycle = "scan_2026-09-09_rj1" if name.endswith("_rj1") else "scan_2026-09-11"
    with pytest.raises(Exception) as exc:
        cycle_results.check_names([name], cycle)
    assert "which family" in str(exc.value) or "cycle" in str(exc.value)


def test_a_prefixed_name_is_accepted():
    cycle_results.check_names(
        ["scan_l0_host_leg_rate_a4_upper95_2026-09-09_rj1",
         "scan_l0_tierc_leg_rate_a4_upper95_2026-09-09_rj1",
         "scan_l0_product_leg_rate_a1_upper95_2026-09-09_rj1"], CYCLE)
