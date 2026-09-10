"""The harness-v5 re-judgements, and the registration defect this task shipped.

`cc_tasks/2026-09-10_rejudge_2_3_4.md` §3.
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
sys.path.insert(0, str(REPO / "scripts"))

REJUDGED = ("scan_2026-09-07b_rj2", "scan_2026-09-09_rj1", "scan_2026-09-10_rj1")

#: Six Results this task bound to a value from the WRONG POPULATION, and the reason they are
#: named here rather than fixed. `build_l0_matrices.leg_results` emits
#: `scan_leg_rate_<leg>_upper95` with NO family prefix, so the host, product and Tier C families
#: all compete for one name; the original run bound the first emitter (host, for these six) and
#: `register_l0_rejudged.py` compared the LAST (Tier C) against it, saw a difference where the
#: host value had not moved, and registered a Tier C number under a Tier A name.
#:
#: A Result name binds once (AD-028), so these cannot be corrected — only superseded. They are
#: pinned here so that (a) nothing quotes them, asserted below, and (b) the next task inherits an
#: exact list rather than a description.
MISBOUND = {
    "scan_leg_rate_a4_upper95_2026-09-09_rj1": (1.0, 0.985135),
    "scan_leg_rate_a5_upper95_2026-09-09_rj1": (0.561497, 0.532305),
    "scan_leg_rate_a10_upper95_2026-09-09_rj1": (1.0, 0.985135),
    "scan_leg_rate_a11_declared_upper95_2026-09-09_rj1": (1.0, 0.953035),
    "scan_leg_rate_a12_upper95_2026-09-09_rj1": (1.0, 0.891025),
    "scan_leg_rate_g1_d_upper95_2026-09-09_rj1": (0.561497, 0.242494),
}


def _payload(cycle: str) -> dict:
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        pytest.skip(f"{cycle} has not been built")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.mark.parametrize("cycle", REJUDGED)
def test_a_re_judgement_creates_no_observation(cycle):
    """`--under-current` re-judges stored evidence. A re-judgement that minted an Observation
    would be claiming to have looked at something, which is the one thing it must never do."""
    p = _payload(cycle)
    assert not p.get("observations_detail"), (
        f"{cycle} carries {len(p['observations_detail'])} Observations; a re-judgement reads "
        f"the source cycle's and creates none")
    assert p.get("derived_from"), "a re-judged payload must name the cycle whose evidence it read"


@pytest.mark.parametrize("cycle", REJUDGED)
def test_the_re_judgement_contacted_nothing(cycle):
    """§'s network claim, checked on the payload rather than asserted in prose: a re-judgement
    issues no request, so there is no per-host request count to carry."""
    p = _payload(cycle)
    assert not p.get("requests_per_host"), f"{cycle} records requests; nothing was fetched"
    assert not p.get("requests_total")


@pytest.mark.parametrize("cycle", REJUDGED)
def test_every_verdict_move_landed_on_error(cycle):
    """§1's stop condition, re-run from the stored diff. A move to anything but `error` is not
    the fix — it is a rule doing something else — and it stops the task."""
    diff_file = REPO / "state" / "rejudgement_diff_2026-09-10.json"
    if not diff_file.is_file():
        pytest.skip("the diff has not been computed")
    diffs = {d["new"].removesuffix(".json"): d
             for d in json.loads(diff_file.read_text(encoding="utf-8"))}
    d = diffs[cycle]
    assert d["unexplained"] == [], d["unexplained"]
    assert set(d["by_transition"]) <= {"fail -> error", "pass -> error"}, d["by_transition"]


def test_no_report_tag_quotes_a_misbound_result():
    """The six of §1 are junk. Nothing may resolve through one, and this is the assertion that
    keeps that true as the report is edited."""
    quoted = set()
    for f in (REPO / "docs" / "reports" / "sections").glob("*.md"):
        quoted |= set(re.findall(r"\{\{result:([a-z0-9_.:-]+?):", f.read_text(encoding="utf-8")))
    hit = sorted(quoted & set(MISBOUND))
    assert hit == [], f"the report quotes a misbound Result: {hit}"


def test_the_registrar_can_no_longer_let_a_later_family_win():
    """The fix, exercised. `scan_leg_rate_<leg>_upper95` is emitted by three families under one
    name; the registrar must take the FIRST, which is the one the original run bound."""
    import register_l0_rejudged as R
    fams = R.families("scan_2026-09-09_rj1")
    assert list(fams) == ["host", "product", "tierc"], (
        "the family order IS the precedence; changing it re-binds names to a different "
        "population")
    seen, first = set(), {}
    for _fam, (counts, prefix, population) in fams.items():
        for base, value, _note in R.B.leg_results(counts, prefix, "scan_2026-09-09_rj1",
                                                  population, with_upper95=True):
            if base in seen:
                continue
            seen.add(base)
            first[base] = value
    # G1-D is the case that went wrong: host 0.242494, Tier C 0.561497, and host must win.
    assert first["scan_leg_rate_g1_d_upper95"] == pytest.approx(0.242494)
    assert first["scan_leg_rate_a5_upper95"] == pytest.approx(0.532305)
