"""The report's prose and its figures quote the same cycle, and the same Result where they share one.

`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` §3: *"the clause that makes the PDF a read
that ships"*. The PDF went out once with prose quoting cycle 3 re-judged (A1 n=15) beside a figure
drawn from cycle 3 as measured (n=16) — two numbers for one leg, in one document, neither wrong on
its own.

**"Agree" cannot mean "print the same number", and saying why is the substance of this file.**
The prose quotes the L0 PRODUCT family — the declared flagship surfaces, n=15 — and the movement
figure plots the CYCLE family — every Tier A product surface, n=35. Those are different
populations of the same leg and `build_l0_matrices.leg_results` exists to keep them under
different names. Forcing them equal would be the error one layer down.

What must hold is that neither side is stale: both resolve to REGISTERED Results of the SAME
cycle, and where they name the same Result they read the same value.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

MD = REPO / "docs" / "reports" / "2026-09_fss_ai_readiness_L0.md"
SECTIONS = REPO / "docs" / "reports" / "sections"

#: The cycle the report speaks for. Its prose was re-pointed at the harness-v5 re-judgement by
#: `cc_tasks/2026-09-10_rejudge_2_3_4.md` decision 4, and moved to the generation-9 judgement of
#: cycle 4 by `cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 1. This pair is the
#: single place the report's cycle is written down for the tests; moving the report without
#: moving it here is what makes a stale figure invisible.
REPORT_CYCLE = "2026-09-10_rj2"
SOURCE_CYCLE = "2026-09-10"


@pytest.fixture(scope="module")
def results():
    try:
        from scan.figures import load_results
        # `fss_` too: `load_results` defaults to the prefixes the FIGURES read, and the report's
        # prose also quotes frame facts (`fss_scan_surfaces_…`, `fss_agencies_tier_a`). A view
        # narrower than the document it checks reports registered Results as missing.
        # `noaa_` and `esip_` joined the list when the report came to quote the two published
        # definitions of AI-ready data in "what the matrix cannot see"
        # (`cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 3c). A view narrower than
        # the document it checks reports registered Results as missing.
        return load_results(prefixes=("scan_", "framework_", "fss_", "noaa_", "esip_"))
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")


def prose_tags() -> set:
    out = set()
    for f in SECTIONS.glob("*.md"):
        out |= set(re.findall(r"\{\{result:([a-z0-9_.:-]+?):", f.read_text(encoding="utf-8")))
    return out


def embedded_figures() -> list:
    if not MD.is_file():
        pytest.skip("the report markdown has not been built")
    return re.findall(r"!\[[^\]]*\]\(([^)]+\.svg)\)", MD.read_text(encoding="utf-8"))


def figure_reads(rel: str) -> set:
    svg = (REPO / rel).read_text(encoding="utf-8")
    m = re.search(r'data-reads="([^"]*)"', svg)
    return set((m.group(1) if m else "").split())


def test_every_embedded_figure_is_drawn_from_the_cycle_the_prose_quotes():
    """The stale-figure clause. A figure from another cycle under prose from this one is the
    defect this task exists to close, and it is invisible in the PDF."""
    for rel in embedded_figures():
        assert f"/scan_{REPORT_CYCLE}/" in rel, (
            f"{rel} is not drawn from scan_{REPORT_CYCLE}, which is the cycle the prose quotes")


def test_report_text_and_figures_agree_per_leg(results):
    """For every leg named by both a prose tag and a figure read: each side resolves to a
    registered Result, and where both name the SAME Result the value is one value."""
    figs = {rel: figure_reads(rel) for rel in embedded_figures()}
    prose = prose_tags()
    assert prose, "the report quotes no Results at all"

    leg = re.compile(r"_(a\d+|a11_declared|a12|b3|d1|d4|f4|g1_d)_")
    prose_legs = {leg.search(t).group(1) for t in prose if leg.search(t)}
    fig_legs = {leg.search(n).group(1) for names in figs.values() for n in names
                if leg.search(n)}
    shared = sorted(prose_legs & fig_legs)
    assert shared, "no leg is named by both prose and a figure; the check would be vacuous"

    # **A figure may read through the evidence-bound fallback; prose may not.** The figure of a
    # re-judged cycle also reads its COMPARISON cycle's names, which are another re-judgement's,
    # so the fallback this has to allow is the general one and not "strip THIS report's cycle".
    # It is asked of `figures.Reads`, the one implementation of the rule
    # (`cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 2), rather than re-derived
    # here where it would go stale the next time a cycle is re-judged.
    from scan.figures import Reads
    view = Reads(results)
    unresolved, disagreed = [], []
    for names in figs.values():
        for n in names:
            base = n.removeprefix("result:")
            if base not in view:
                unresolved.append(base)
    for n in prose:
        if n.removeprefix("result:") not in results:
            unresolved.append(n.removeprefix("result:"))
    assert unresolved == [], f"names that resolve to no registered Result: {sorted(set(unresolved))}"

    for rel, names in figs.items():
        for n in names & prose:
            if results.get(n) != results.get(n):
                disagreed.append((rel, n))
    assert disagreed == [], disagreed


def test_the_prose_and_the_figures_never_mix_two_cycles_of_one_leg(results):
    """The specific shape the PDF shipped: `..._a1_..._2026-09-09` in a figure beside
    `..._a1_..._2026-09-09_rj1` in the prose. Either is fine alone; together they are two
    answers to one question in one document."""
    figs = {n for names in (figure_reads(r) for r in embedded_figures()) for n in names}
    both = []
    for t in prose_tags():
        if not t.endswith("_" + REPORT_CYCLE):
            continue
        stale = f"{t[: -(len(REPORT_CYCLE) + 1)]}_{SOURCE_CYCLE}"
        if stale in figs:
            both.append((t, stale))
    assert both == [], (
        f"prose quotes the re-judged Result and a figure prints the original for the same "
        f"metric: {both}")
