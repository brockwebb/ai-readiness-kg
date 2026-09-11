"""`in` and `[]` answer the same question, and a blank F5 row is licensed only by the payload.

`cc_tasks/2026-09-11_f5_membership_through_fallback.md` decisions 1 and 2.

The defect: `figures.Reads` is a `dict` subclass whose `__getitem__` resolves a missing name
through the evidence-bound fallback, and whose `in` — inherited straight from `dict` — did not.
`cycle_over_cycle` asked `if rate_key not in R` before reading, so under "register only what
moved" every leg whose pass rate had not moved was absent by name under the re-judged cycle, the
membership test said absent, and the row was drawn blank with *"not measured in this cycle"* —
the sentence DD-055 reserves for a leg nobody judged. Eleven such rows on the published graph
page; twenty-one on one of the figures drawn the same day.

Two tests, because the defect has two halves. The first pins the type: `in` is now exactly
"`[]` would not raise", over every name any comparison record licenses. The second pins the
FIGURE, and it is the one that matters, because `__contains__` cannot stop a caller branching on
`in` and drawing something else: a blank row is permitted only where the leg has no Finding in
that cycle's payload, which for these nine cycles means `{A1, A3}` on cycle 2 re-judged — cycle 1
never collected the `link_probe` leg they read — and nothing anywhere else.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import cycle_results                                                # noqa: E402
from scan import figures as FIG                                     # noqa: E402

#: Every re-judged cycle, and the blank rows its F5 is ALLOWED to draw — as `{leg}`, since a leg
#: blank on one series and drawn on the other is still a leg this figure says nothing about.
#:
#: Two cycles have no F5 to check and each has its own reason, so they are two markers and not
#: one. Both are the machinery refusing rather than guessing, and neither is a defect:
#:
#: * ``NO_PREDECESSOR`` — `figures.yaml` declares none, and since
#:   `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md` decision 5 there is no global default to fall
#:   through to, so `cycle_over_cycle` raises `UnconfiguredComparison`. Cycle 1 re-judged is the
#:   honest case: nothing precedes the first cycle.
#: * ``INPUTS_NEVER_REGISTERED`` — the cycle's figure-input Results (`…_wilson_lo_…`) were never
#:   registered under its name and no comparison record licenses a fallback for them, so F1, F3
#:   and F5 raise `UnlicensedFallback`. `scan_2026-09-07_rj1` predates the comparison-record
#:   convention entirely and has never had a figure on disk for exactly this reason.
NO_PREDECESSOR = "no F5: figures.yaml declares no predecessor"
INPUTS_NEVER_REGISTERED = "no F5: this cycle's figure inputs were never registered"

EXPECTED_BLANKS = {
    "scan_2026-09-07_rj1": INPUTS_NEVER_REGISTERED,
    "scan_2026-09-07_rj2": NO_PREDECESSOR,
    "scan_2026-09-07b_rj1": set(),
    "scan_2026-09-07b_rj2": NO_PREDECESSOR,
    # Cycle 1 collected no `link_probe`, so `RULE-A1-v4` and `RULE-A3-v6` judge nothing there and
    # its payload carries no A1 or A3 Finding. These two rows are the only blank rows this repo's
    # F5 figures are entitled to, and they are the DD-055 case the sentence was written for.
    "scan_2026-09-07b_rj3": {"A1", "A3"},
    "scan_2026-09-09_rj1": set(),
    "scan_2026-09-09_rj2": set(),
    "scan_2026-09-10_rj1": set(),
    "scan_2026-09-10_rj2": set(),
}

#: The cycles whose F5 is a figure that can be drawn and therefore checked.
DRAWABLE = sorted(c for c, v in EXPECTED_BLANKS.items() if isinstance(v, set))

RECORDS = ("state/rejudgement_registration_2026-09-10.json",
           "state/l0_rejudged_registration_2026-09-10.json",
           "state/figure_inputs_registration_2026-09-10.json",
           "state/rejudgement_registration_2026-09-11.json",
           "state/l0_rejudged_registration_2026-09-11.json",
           "state/figure_inputs_registration_2026-09-11.json")

BLANK_TEXT = "not measured in this cycle"


@pytest.fixture(scope="module")
def live() -> dict:
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        return FIG.load_results()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable, membership unverified against the registry: {exc}")


def recorded_names() -> list:
    """Every name any comparison record mentions, moved or unchanged. Both sides matter: an
    unchanged name must be `in`, a moved name must be `in` under its own name, and the test is
    only worth running over names that actually occur."""
    out = []
    for rel in RECORDS:
        p = REPO / rel
        if not p.is_file():
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        for v in doc.values():
            if not isinstance(v, dict):
                continue
            out += list(v.get("unchanged_names") or [])
            out += list(v.get("moved_names") or [])
    return sorted(set(out))


def legs_with_findings(cycle: str) -> set | None:
    """The legs a cycle actually judged, read off its Findings. `None` when the payload is not
    on disk. Deliberately NOT `legs_judged`: that key exists only on a re-judged payload, and a
    measured cycle is just as legitimate a comparison series."""
    p = REPO / "state" / f"{cycle}.json"
    if not p.is_file():
        return None
    return {f["leg"] for f in json.loads(p.read_text(encoding="utf-8"))
            .get("findings_detail") or []}


# ------------------------------------------------------------------ decision 1

def test_contains_is_exactly_getitem_not_raising(live):
    """Over every name any comparison record mentions. This is the equivalence the type now
    promises, and the reason `cycle_over_cycle` may branch on `in` at all."""
    R = FIG.Reads(live)
    names = recorded_names()
    assert len(names) > 400, f"only {len(names)} recorded names; the records did not load"
    bad = []
    for name in names:
        try:
            R[name]
            reads = True
        except (FIG.UnlicensedFallback, KeyError):
            reads = False
        if (name in R) != reads:
            bad.append(f"{name}: `in` says {name in R}, `[]` {'reads' if reads else 'raises'}")
    assert not bad, "\n".join(bad[:10])


def test_a_licensed_fallback_is_in_even_though_the_plain_dict_says_no(live):
    """The case the defect turned on, stated as one example rather than left implicit in the
    sweep: a name nobody registered under the re-judged cycle, which a comparison record lists
    as compared-and-unchanged, is present through `in` and absent through `dict.__contains__`."""
    licensed = [n for n in FIG.unchanged_names()
                if n not in live and FIG._source_name(n) in live]
    assert licensed, "no comparison record licenses a fallback; the records did not load"
    R = FIG.Reads(live)
    name = sorted(licensed)[0]
    assert dict.__contains__(R, name) is False
    assert name in R
    assert R[name] == live[FIG._source_name(name)]


def test_an_unlicensed_name_is_absent_through_in_and_raises_through_getitem(live):
    """The asymmetry `__contains__` cannot fix, pinned so it is a known shape and not a
    surprise. `test_the_blank_rows_are_licensed_by_the_payload` is what catches a caller who
    branches on `in` and draws something else."""
    R = FIG.Reads(live)
    name = "scan_a3_pass_rate_2026-09-09_rj9"           # never registered, never recorded
    assert name not in R
    with pytest.raises(FIG.UnlicensedFallback):
        R[name]


def test_get_does_not_bypass_the_fallback(live):
    """`dict.get` reaches the C-level lookup and never calls `__getitem__`, which is the same
    trap `in` was. A licensed name resolves through it; a plain absent one returns the default;
    an unlicensed one still raises rather than quietly becoming the default."""
    R = FIG.Reads(live)
    licensed = sorted(n for n in FIG.unchanged_names()
                      if n not in live and FIG._source_name(n) in live)
    assert R.get(licensed[0]) == live[FIG._source_name(licensed[0])]
    assert R.get("scan_no_such_name_at_all") is None
    with pytest.raises(FIG.UnlicensedFallback):
        R.get("scan_a3_pass_rate_2026-09-09_rj9", 0.0)


# ------------------------------------------------------------------ decision 2

def _blank_legs(cycle: str, live: dict) -> tuple:
    """`(blank legs, legs blank despite having a Finding)` for one cycle's F5.

    Computed the way the renderer computes it — the same `name_for`, the same `in R` — and
    cross-checked against the payload, which is an independent source. The pair is what §1's
    stop condition is about: a blank the payload does not explain is a third source of
    blankness and neither the fallback nor DD-055 accounts for it.
    """
    cfg = FIG.config(cycle)
    cmp_ = cfg["compare_to"]
    mx = FIG.matrix(cfg)
    blank, unexplained = set(), []
    for suffix in (cmp_["suffix"], cfg["cycle_suffix"]):
        series = f"scan_{suffix}"
        judged = legs_with_findings(series)
        R = FIG.Reads(live, cfg["cycle"])
        for leg in mx["legs"]:
            key = cycle_results.name_for(f"scan_{FIG.slug(leg)}_pass_rate", series)
            if key in R:
                continue
            blank.add(leg)
            if judged is not None and leg in judged:
                unexplained.append((series, leg, key))
    return blank, unexplained


@pytest.mark.parametrize("cycle", sorted(EXPECTED_BLANKS))
def test_the_blank_rows_are_licensed_by_the_payload(cycle, live):
    """A row may read "not measured in this cycle" only where the cycle has no Finding on that
    leg. Anything else is the figure saying something false about a measurement that exists."""
    expected = EXPECTED_BLANKS[cycle]
    if expected is NO_PREDECESSOR:
        assert FIG.config(cycle)["compare_to"] is None, (
            f"{cycle} now declares an F5 predecessor; give it a row in EXPECTED_BLANKS")
        with pytest.raises(FIG.UnconfiguredComparison):
            FIG.build(FIG.config(cycle), live, only=("cycle_over_cycle",))
        return
    if expected is INPUTS_NEVER_REGISTERED:
        # The hard error working: a figure may not resolve a missing name by convention, and
        # nothing ever recorded these as compared-and-unchanged. The cycle keeps no figure on
        # disk, which is the honest state and is why there has never been a directory for it.
        with pytest.raises(FIG.UnlicensedFallback):
            FIG.build(FIG.config(cycle), live, only=("cycle_over_cycle",))
        assert not (REPO / FIG.config(cycle)["out_dir"] / "cycle_over_cycle.svg").is_file()
        return
    if not (REPO / "state" / f"scan_matrix_{cycle.removeprefix('scan_')}.json").is_file():
        pytest.fail(f"{cycle} has no matrix, so its F5 cannot be checked")
    blank, unexplained = _blank_legs(cycle, live)
    assert not unexplained, (
        f"{len(unexplained)} blank row(s) in {cycle}'s F5 that the payload does not explain — "
        f"the leg has Findings and the row still says 'not measured': {unexplained[:5]}")
    assert blank == expected, f"{cycle}: blank legs {sorted(blank)}, expected {sorted(expected)}"


@pytest.mark.parametrize("cycle", DRAWABLE)
def test_the_rendered_figure_carries_exactly_those_blanks(cycle, live):
    """The analytic check above, tied to the bytes. One `not measured in this cycle` is drawn
    per (leg, series), so the count is over pairs and not over legs — a leg blank on one series
    and drawn on the other must not read as two."""
    if not (REPO / "state" / f"scan_matrix_{cycle.removeprefix('scan_')}.json").is_file():
        pytest.fail(f"{cycle} has no matrix, so its F5 cannot be rendered")
    cfg = FIG.config(cycle)
    mx = FIG.matrix(cfg)
    pairs = 0
    for suffix in (cfg["compare_to"]["suffix"], cfg["cycle_suffix"]):
        R = FIG.Reads(live, cfg["cycle"])
        for leg in mx["legs"]:
            key = cycle_results.name_for(f"scan_{FIG.slug(leg)}_pass_rate", f"scan_{suffix}")
            pairs += key not in R
    svg = FIG.build(cfg, live, only=("cycle_over_cycle",))["cycle_over_cycle"]
    assert svg.count(BLANK_TEXT) == pairs
    # And the rendered file on disk agrees with what the renderer produces now, which is what
    # makes "the published figure carries N blanks" a checkable sentence rather than a memory.
    path = REPO / cfg["out_dir"] / "cycle_over_cycle.svg"
    if path.is_file():
        assert path.read_text(encoding="utf-8").count(BLANK_TEXT) == pairs, (
            f"{path.relative_to(REPO)} is stale: it was rendered before the fix and carries "
            f"{path.read_text(encoding='utf-8').count(BLANK_TEXT)} blank rows, not {pairs}")


def test_the_graph_page_says_not_measured_about_nothing_that_was_measured():
    """The published page, as bytes. It inlines the finished SVG of whichever cycle it was
    rendered for, so this is the end of the chain and the only check a reader of the page is
    protected by."""
    page = REPO / "docs" / "progress" / "index.html"
    if not page.is_file():
        pytest.skip("the progress page has not been generated")
    body = page.read_text(encoding="utf-8")
    # Longest name first: `scan_2026-09-10_rj2` contains `scan_2026-09-10` as a substring, and
    # matching the shorter one would check the wrong cycle's entitlement.
    cycle = next((c for c in sorted(EXPECTED_BLANKS, key=len, reverse=True) if c in body), None)
    assert cycle, "the page names no cycle this test knows about"
    expected = EXPECTED_BLANKS[cycle]
    if not isinstance(expected, set):
        assert BLANK_TEXT not in body, (
            f"the page draws {cycle}, which has no F5, yet carries a blank F5 row")
        return
    # One blank per (leg, series). The page inlines the finished SVG, so this is the count in
    # the file the renderer wrote, checked at the end of the chain a reader actually reads.
    svg = REPO / FIG.config(cycle)["out_dir"] / "cycle_over_cycle.svg"
    on_disk = svg.read_text(encoding="utf-8").count(BLANK_TEXT) if svg.is_file() else 0
    assert body.count(BLANK_TEXT) == on_disk, (
        f"the page shows {body.count(BLANK_TEXT)} 'not measured' rows and "
        f"{svg.name} has {on_disk}; the page is stale")
    assert on_disk <= len(expected) * 2, (
        f"{cycle}'s F5 carries {on_disk} blank rows and is entitled to at most "
        f"{len(expected) * 2} — {sorted(expected)} on at most both series")


# ============================================================ decision 3, made durable
#
# Decision 3 asks that the measured-cycle figures re-render byte-identically, "the fix must move
# nothing where nothing was wrong". Two things were compared under that heading and they are not
# the same question:
#
#   * does THIS change move a figure?  Answered directly and exactly: the renderer at HEAD and
#     the renderer with `__contains__` produce byte-identical output for every measured cycle and
#     for `scan_2026-09-07b_rj1`. It moves nothing.
#   * does the committed file match what the renderer produces?  It did NOT, for eleven files,
#     and the reason predates this task by one day: `cc_tasks/2026-09-10_harness_small.md`
#     decision 3 added `xmlns` to the SVG root because typst refused every figure without it
#     ("missing root node"), and the figures of cycles 1 and 2 were never re-rendered after it.
#     Zero text nodes differed; thirty-seven bytes of root attribute did.
#
# The first question is answered once and cannot be asked again after the commit, because HEAD
# moves. The second is a standing property worth a gate: a renderer change that never reached the
# files is exactly how a published figure comes to be something no code produces any more.

FIGDIR = REPO / "assessment" / "harness" / "scan" / "figures"


def committed_figures() -> list:
    return sorted((d.name, p.stem) for d in FIGDIR.iterdir() if d.is_dir()
                  for p in d.glob("*.svg"))


@pytest.mark.parametrize("cycle", sorted({c for c, _n in committed_figures()}))
def test_every_committed_figure_is_what_the_renderer_produces_today(cycle, live):
    """No published figure is something the code no longer draws.

    Byte-for-byte, per cycle, over every SVG that cycle has on disk. This is what would have
    caught the eleven `xmlns`-less files a day earlier, and what will catch the next renderer
    change that stops short of the artifacts.
    """
    d = FIGDIR / cycle
    names = tuple(sorted(p.stem for p in d.glob("*.svg")))
    figs = FIG.build(FIG.config(cycle), live, only=names)
    stale = [n for n in names
             if (d / f"{n}.svg").read_text(encoding="utf-8") != figs[n] + "\n"]
    assert not stale, (
        f"{cycle}: {stale} on disk differ from what the renderer produces. Re-render the cycle; "
        f"a committed figure that no code produces is a picture of a measurement nobody can "
        f"reproduce.")


@pytest.mark.parametrize("cycle", sorted({c for c, _n in committed_figures()}))
def test_every_committed_figure_is_a_standalone_svg_document(cycle):
    """`xmlns` on the root, which is what makes the file a document and not only an inline
    fragment. typst refuses one without it, so a figure missing it cannot reach the PDF —
    `cc_tasks/2026-09-10_harness_small.md` decision 3, and eleven files that never got it."""
    missing = [p.name for p in sorted((FIGDIR / cycle).glob("*.svg"))
               if "xmlns=" not in p.read_text(encoding="utf-8")[:200]]
    assert not missing, f"{cycle}: {missing} carry no xmlns and cannot be rendered into the PDF"
