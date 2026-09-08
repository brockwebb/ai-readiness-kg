"""The gate on the cycle figures: no figure prints a number nobody can trace.

`cc_tasks/2026-09-07_eda_and_charts.md` §4. The motivating defect is in the record: the
scan-run RESULT §4 quoted fifteen Wilson intervals, and not one of them existed in the Result
registry. A number in a figure is a claim, and a claim with no artifact behind it is prose
with a rectangle around it.

Four checks, and the third is the one that matters: every text node in every generated SVG
that contains a digit carries `data-src`, and this test RESOLVES it — against the registry by
name, against the cycle's matrix JSON, against the declared axis scale, or as a label
from the framework's own code vocabulary. An unresolvable numeral fails with the numeral and
the figure named.

Neo4j-dependent checks skip cleanly when the database is unreachable.
"""
from __future__ import annotations

import ast
import json
import math
import re
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO))

from scan.rules import CURRENT, parse_rule_id                        # noqa: E402
from scan.stats import Z, wilson                                     # noqa: E402

#: Same allowance as the collectors' lint. Anything else numeric belongs in `figures.yaml`.
ALLOWED_INTS = {0, 1, 2, 3, 200, 400, 404, 410, 429, 500, 503, 999}

#: A text node's numerals: the runs this test has to account for.
_NUM = re.compile(r"\d+(?:\.\d+)?")
_TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
_ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')


def cfg(cycle: str | None = None) -> dict:
    """The renderer's OWN config, not a second read of `figures.yaml`.

    `cycle`, `cycle_suffix`, `out_dir` and `matrix_json` are derived from `params.cycle.name`
    by `figures.config()` (`cc_tasks/2026-09-07_scan_run_2.md` §5). A test that re-read the
    YAML directly would be checking a file the renderer no longer treats as complete, and
    would keep passing against the previous cycle's matrix.
    """
    from scan.figures import config
    return config(cycle)


def matrix(cycle: str | None = None) -> dict:
    return json.loads((REPO / cfg(cycle)["matrix_json"]).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def results():
    """`{name: value}` from the live registry, or a clean skip."""
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from scan.figures import load_results
        return load_results()
    except Exception as exc:                                  # noqa: BLE001 - see docstring
        pytest.skip(f"Neo4j unreachable, figures unverified against the registry: {exc}")


@pytest.fixture(scope="module")
def session():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        c = load_project_config(REPO)
        driver = get_neo4j_driver(c)
        with driver.session(database=c["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with driver.session(database=c["neo4j"]["database"]) as s:
        yield s
    driver.close()


# ------------------------------------------------------------------ 1. the arithmetic

def _closed_form(k: int, n: int, z: float):
    """The textbook Wilson score interval, written out here so the test does not check the
    implementation against itself. Rounded exactly as `rollup.wilson_interval` rounds, so the
    comparison can be exact rather than approximate."""
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(centre - half, 6), round(centre + half, 6)


@pytest.mark.parametrize("k,n", [(0, 23), (16, 23), (19, 23), (23, 23)])
def test_wilson_matches_the_closed_form(k, n):
    lo, hi = wilson(k, n, Z)
    want_lo, want_hi = _closed_form(k, n, Z)
    assert abs(lo - want_lo) < 1e-9 and abs(hi - want_hi) < 1e-9


def test_wilson_matches_the_two_decimal_table_in_the_scan_run_result():
    """`cc_tasks/2026-09-07_scan_run_RESULT.md` §4, transcribed. If a future change to the
    interval arithmetic moves any of these, the RESULT that quoted them stops being true and
    this test says so before a figure repeats it."""
    table = {(19, 23): (0.63, 0.93), (16, 23): (0.49, 0.84), (4, 23): (0.07, 0.37),
             (3, 23): (0.05, 0.32), (2, 23): (0.02, 0.27), (0, 23): (0.00, 0.14)}
    for (k, n), (lo2, hi2) in table.items():
        lo, hi = wilson(k, n, Z)
        assert (round(lo, 2), round(hi, 2)) == (lo2, hi2), (k, n, lo, hi)


def test_the_scan_harness_has_exactly_one_wilson_implementation():
    """`scan/stats.py` is a delegate, not a copy. Asserted structurally — the constant is the
    same object's value, and the module defines no arithmetic of its own."""
    from harness.rollup import _WILSON_Z
    assert Z == _WILSON_Z
    src = (SCAN / "stats.py").read_text(encoding="utf-8")
    assert "math.sqrt" not in src, "stats.py grew its own arithmetic; it must delegate"
    assert "wilson_interval" in src


def test_the_registered_intervals_are_the_ones_the_matrix_holds(results):
    """The matrix file and the registry were written by two runs of one function. If they ever
    disagree, one of them is a second implementation."""
    mx = matrix()
    suffix = cfg()["cycle_suffix"]
    for leg, pl in mx["per_leg"].items():
        s = leg.replace("-", "_").lower()
        assert results[f"scan_{s}_wilson_lo_{suffix}"] == pl["ci95_low"], leg
        assert results[f"scan_{s}_wilson_hi_{suffix}"] == pl["ci95_high"], leg


# ------------------------------------------------------------------ 2. no hidden constants

def test_the_figure_generator_hides_no_constant():
    """The collectors' lint (tests/test_scan_harness.py), extended to the renderer. A geometry
    constant buried in an SVG string is unswept and unversioned exactly as a threshold in a
    collector is, and a figure is where an unswept number does the most damage: it is the
    artifact a reader believes."""
    offenders = []
    for py in (SCAN / "figures.py", SCAN / "stats.py"):
        for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                    and not isinstance(node.value, bool) and node.value not in ALLOWED_INTS:
                offenders.append(f"{py.name}:{node.lineno} -> {node.value}")
    assert not offenders, offenders


# ------------------------------------------------------------------ 3. every numeral sourced

def _codes(cycle: str | None = None) -> set:
    """Every WHITESPACE TOKEN carrying a digit that a figure is allowed to print as a label:
    indicator codes, leg codes, agency codes, criterion letters, commit hashes, snapshot
    timestamps. Checked token by token rather than whole-string, because F3 prints a code list
    (`A1 A10 A11 …`) and a whole-string comparison would have to enumerate every list that
    could ever be printed — which is a vocabulary of lists, not of codes.

    Tokens without a digit are prose and carry no measurement; the gate is about numerals."""
    fw = json.loads((REPO / cfg(cycle)["framework_json"]).read_text(encoding="utf-8"))
    mx = matrix(cycle)
    c = cfg(cycle)
    out = {n["properties"]["code"] for n in fw["nodes"]
           if "AssessmentIndicator" in n["labels"]}
    out |= set(mx["legs"]) | set(mx["candidate_legs"]) | set(mx["agencies"]) | set(c["criteria"])
    for s in c["snapshots"]:
        out |= set(s["label"].split()) | set(s["note"].split()) | {s["commit"]}
    # F5's "rule changed (v2 → v3): not comparable" note. The version tokens come from
    # `figures.yaml`'s `compare_to.rule_changed`, which is where the claim lives — so the
    # vocabulary cannot drift from the label, and a version pair invented in the renderer
    # would still fail.
    for change in (c.get("compare_to") or {}).get("rule_changed", {}).values():
        out |= {f"({t}" for t in change.split()} | {f"{t}):" for t in change.split()}
        out |= set(change.split())
    # F5's re-judgement note ("re-judged under v4 from stored observations, no re-fetch").
    # From `figures.yaml`'s `compare_to.note`, where the claim lives — the same rule the
    # snapshot labels above follow, so a note invented in the renderer would still fail.
    out |= set(((c.get("compare_to") or {}).get("note") or "").split())
    out |= {c["cycle_suffix"], (c.get("compare_to") or {}).get("suffix", "")}
    return {t for t in out if _NUM.search(t)}


def _label_ok(inner: str, codes: set) -> list:
    """Tokens of a label node that carry a digit and are not in the vocabulary."""
    return [t for t in inner.split() if _NUM.search(t) and t not in codes]


def _matches(rendered: str, value: float) -> bool:
    """A rendered numeral equals a value when it is that value rounded to the decimals the
    figure actually printed. `0.14` is `0.143117` printed to two places, and demanding
    equality of the strings would forbid a figure from rounding at all."""
    decimals = len(rendered.split(".")[1]) if "." in rendered else 0
    return abs(float(rendered) - value) <= 0.5 * 10 ** -decimals


@pytest.fixture(scope="module")
def figures(results):
    from scan.figures import build
    return build(cfg(), results)


def audit(figs: dict, results: dict, cycle: str | None = None) -> list:
    """Every numeral in every figure, resolved or reported. The gate itself, extracted so a
    mutation can be run through it — a checker nobody has watched fail is not a checker."""
    mx = matrix(cycle)
    codes = _codes(cycle)
    ticks = {f'{t:.{cfg(cycle)["rate_axis"]["tick_decimals"]}f}'
             for t in cfg(cycle)["rate_axis"]["ticks"]}
    matrix_counts = {str(len(mx["rows"])), str(len(mx["agencies"])), str(len(mx["legs"]))}
    for pl in mx["per_leg"].values():
        matrix_counts |= {str(pl[k]) for k in ("pass", "fail", "error", "not_applicable",
                                               "applicable_n", "surfaces_targeted")}
    bad = []
    for figure, body in figs.items():
        for attrs, inner in _TEXT.findall(body):
            nums = _NUM.findall(inner)
            if not nums:
                continue
            a = dict(_ATTR.findall(attrs))
            src = a.get("data-src")
            if not src:
                bad.append(f"{figure}: <text> with digits and no data-src: {inner!r}")
                continue
            if src == "label":
                for token in _label_ok(inner, codes):
                    bad.append(f"{figure}: label token {token!r} is not in the code "
                               f"vocabulary (in {inner!r})")
                continue
            if src == "axis":
                if inner not in ticks:
                    bad.append(f"{figure}: axis tick {inner!r} is not a declared tick")
                continue
            names = src.split()
            if len(names) != len(nums):
                bad.append(f"{figure}: {inner!r} has {len(nums)} numerals for {len(names)} "
                           f"sources ({src})")
                continue
            for rendered, name in zip(nums, names):
                kind, _, key = name.partition(":")
                if kind == "result":
                    if key not in results:
                        bad.append(f"{figure}: {inner!r} cites unregistered Result {key!r}")
                    elif not _matches(rendered, results[key]):
                        bad.append(f"{figure}: printed {rendered!r} for Result {key} "
                                   f"= {results[key]!r}")
                elif kind == "matrix":
                    if rendered not in matrix_counts:
                        bad.append(f"{figure}: {rendered!r} is not a count in the matrix")
                else:
                    bad.append(f"{figure}: unknown data-src kind {name!r}")
    return bad


def test_every_numeral_in_every_figure_resolves_to_an_artifact(figures, results):
    assert not audit(figures, results), "\n".join(audit(figures, results))


@pytest.mark.parametrize("mutation,expect", [
    ('<text class="num" x="1" y="1" text-anchor="start" data-src="result:scan_a1_pass">'
     '<<VAL>>7</text>', "printed"),
    ('<text class="num" x="1" y="1" text-anchor="start">42</text>', "no data-src"),
    ('<text class="num" x="1" y="1" text-anchor="start" data-src="result:scan_nope">'
     '5</text>', "unregistered"),
    ('<text class="num" x="1" y="1" text-anchor="start" data-src="axis">0.33</text>',
     "not a declared tick"),
    ('<text class="lbl" x="1" y="1" text-anchor="start" data-src="label">Z9</text>',
     "not in the code vocabulary"),
])
def test_the_gate_catches_a_number_from_nowhere(figures, results, mutation, expect):
    """Five ways to smuggle a numeral into a figure, and the gate rejects all five. Without
    this the previous test would pass just as happily on four figures that print nothing."""
    mutated = dict(figures)
    mutated["per_leg_pass_rate"] += mutation.replace("<<VAL>>", "")
    bad = audit(mutated, results)
    assert any(expect in b for b in bad), (expect, bad)


def test_the_figures_print_the_things_the_task_asked_them_to(figures):
    """Cheap structural checks, so a figure cannot pass §4 by printing nothing."""
    mx = matrix()
    f1 = figures["per_leg_pass_rate"]
    for leg in mx["legs"]:
        assert f">{leg}<" in f1, f"F1 omits {leg}"
    f2 = figures["agencies_by_legs_matrix"]
    for agency in mx["agencies"]:
        assert agency in f2, f"F2 omits {agency}"
    for agency in mx["agencies_without_surfaces"]:
        assert f"{agency} · no admitted surface" in f2
    assert "passes_all" in f2 and "fails_all" in f2, "F2 has no control rows"
    f3 = figures["gap_map_by_criterion"]
    assert "candidate (not counted)" in f3 and ">A12<" in f3
    f4 = figures["progress_over_snapshots"]
    for s in cfg()["snapshots"]:
        assert s["commit"] in f4, f"F4 omits snapshot {s['commit']}"
    assert "<line" not in f4, "F4 must not draw a trend line through three points"
    # F5. The mark on the legs whose RULE changed is the whole point of the figure: two dots
    # at different heights invite "the host changed", and on those rows that reading is wrong.
    f5 = figures["cycle_over_cycle"]
    for leg in mx["legs"]:
        assert f">{leg}<" in f5, f"F5 omits {leg}"
    for leg, change in cfg()["compare_to"]["rule_changed"].items():
        assert f"rule changed ({change}): not comparable" in f5, (
            f"F5 does not mark {leg} as not comparable across the rule change")
    # No arrow and no connector between the two cycles' dots. A difference between two points
    # is not a direction of travel, and two cycles hours apart are not a rate of change; an
    # arrow would say both. (The `→` inside the rule-change TEXT is the version bump, not a
    # trend, which is why this checks drawn geometry rather than glyphs.)
    for forbidden in ("<polyline", "marker-end", "<path"):
        assert forbidden not in f5, f"F5 draws {forbidden}: that reads as a trend"


def test_no_figure_reaches_the_network(figures):
    """Static, inline, no CDN — the operator's constraint. A progress page that needed a fetch
    to render its own measurement would be a poor advertisement for machine-readable
    publication."""
    for name, body in figures.items():
        for forbidden in ("http://", "https://", "<script", "<image", "xlink:href", "@import"):
            assert forbidden not in body, f"{name} contains {forbidden!r}"


# ------------------------------------------------------------------ 4. re-derivation

def test_each_legs_registered_counts_re_derive_from_the_graph(session, results):
    """The registry is checked against the Findings themselves, through the
    `Rule -[:MEASURES]-> AssessmentIndicator` edge the repair task added. Without that edge
    this check could not be written at all, which is why it is here and not in the scan-run
    task."""
    mx = matrix()
    ph = mx["params_hash"]
    q = ("MATCH (f:Finding)-[:RULED_BY]->(:Rule)-[:MEASURES]->"
         "(:AssessmentIndicator {code: $code}) "
         "WHERE f.params_hash = $ph AND NOT f.target_doc_id STARTS WITH 'control:' "
         "RETURN f.verdict AS v, count(*) AS c")
    bad = []
    for leg in mx["legs"]:
        code = parse_rule_id(CURRENT[leg])["indicator_code"]
        got = {r["v"]: r["c"] for r in session.run(q, code=code, ph=ph)}
        s = leg.replace("-", "_").lower()
        for verdict in ("pass", "fail", "error", "not_applicable"):
            # Through `figures.rname`, the same resolver the figures use. The bare
            # `scan_<leg>_<verdict}` is the FIRST cycle's Result (DD-056's exception list), so
            # a literal here silently compared cycle 2's Findings — selected by cycle 2's
            # `params_hash`, from the matrix — against cycle 1's registered counts, and
            # reported the difference as drift. The params_hash and the Result name have to
            # name the same cycle or the check means nothing.
            from scan.figures import rname
            key = rname(f"scan_{s}_{verdict}", cfg())
            want = results[key]
            if got.get(verdict, 0) != want:
                bad.append(f"{leg} {verdict}: graph {got.get(verdict, 0)}, "
                           f"registry {key} = {want}")
    assert not bad, "\n".join(bad)
