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

from support.sourcescan import strip_prose

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
    """The cycle's matrix, or a SKIP with the reason (`cc_tasks/2026-09-10_harness_v5_blind.md`
    decision 6).

    This file is written around `params.cycle.name`, so a task that measures a cycle and then
    stops before reporting it leaves every figure test erroring on a missing file — 2 failures
    and 8 collection errors, which is what `2026-09-10_scan_run_4.md`'s deliberate gate stop
    looked like in the suite. A gate that cannot distinguish "the figures are wrong" from "there
    are no figures yet" is a gate that trains its reader to ignore it.

    A skip, not a pass: the figures are unverified and the suite says so.
    """
    path = REPO / cfg(cycle)["matrix_json"]
    if not path.is_file():
        pytest.skip(f"cycle {cycle or 'params.cycle.name'} has not been reported: "
                    f"{path.relative_to(REPO)} does not exist, so there are no figures to "
                    f"check. Run §4/§5 of the cycle's task, or point params.cycle.name at a "
                    f"reported cycle.")
    return json.loads(path.read_text(encoding="utf-8"))


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
    src = strip_prose((SCAN / "stats.py").read_text(encoding="utf-8"))
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
    """The rendered figures, or the same skip `matrix()` gives — decision 6.

    `build` reads the cycle's matrix, so an unreported cycle errors here at FIXTURE SETUP, which
    pytest reports as 8 errors rather than 8 skips. Asking for the matrix first turns that into
    one legible reason.
    """
    matrix()
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


#: The SVG namespace name. A namespace name is an IDENTIFIER, not a location: no conforming
#: processor dereferences it (Namespaces in XML 1.0 §2.1 — "the attribute's value... is a URI
#: reference... it is not a goal that it be directly usable for retrieval"). It appears on the
#: root element because a standalone `.svg` file needs it to be SVG at all, which is why
#: `figures.py` emits it at source rather than a build step patching it in afterwards.
SVG_NS_DECL = ' xmlns="http://www.w3.org/2000/svg"'


def test_no_figure_reaches_the_network(figures):
    """Static, inline, no CDN — the operator's constraint. A progress page that needed a fetch
    to render its own measurement would be a poor advertisement for machine-readable
    publication."""
    for name, body in figures.items():
        assert body.count(SVG_NS_DECL) == 1, (
            f"{name} declares the SVG namespace {body.count(SVG_NS_DECL)} times; exactly one, on "
            "the root element, is what makes the file SVG standalone")
        body = body.replace(SVG_NS_DECL, "", 1)
        for forbidden in ("http://", "https://", "<script", "<image", "xlink:href", "@import"):
            assert forbidden not in body, f"{name} contains {forbidden!r}"


# ------------------------------------------------------------------ 4. re-derivation

def _tier_doc_ids(tier: str) -> set:
    """The doc_ids of one tier, from the targets DataFile — the same join
    `scripts/scan_report.py::tier_of` makes, and the same authority."""
    from scan import load_params
    src = REPO / "state" / f"{load_params()['cycle']['targets']}.json"
    rows = json.loads(src.read_text(encoding="utf-8"))["rows"]
    return {r["doc_id"] for r in rows if r.get("doc_id") and r.get("tier", "A") == tier}


def test_each_legs_registered_counts_re_derive_from_the_graph(session, results):
    """The registry is checked against the Findings themselves, through the
    `Rule -[:MEASURES]-> AssessmentIndicator` edge the repair task added. Without that edge
    this check could not be written at all, which is why it is here and not in the scan-run
    task.

    **Both families, and each against its own population.** The query excluded `control:` and
    nothing else, which was the whole answer while a cycle held two populations. Cycle 3 added
    a third — Tier C reference hosts, judged on tier-0 legs, in no Tier A denominator
    (DD-059) — and their six Findings per leg landed in a comparison against Tier A's
    registered counts and read as drift (A4 graph 39 against registry 33, and five more, each
    difference exactly the Tier C rows). Excluding them and leaving it there would have made
    the Tier C Results the one family nothing re-derives, so `scan_tierc_*` is checked here
    too, against the Findings the Tier C rows actually produced.
    """
    mx = matrix()
    ph = mx["params_hash"]
    tier_c = _tier_doc_ids("C")
    assert tier_c, "no Tier C surfaces; the split this test makes would be vacuous"
    checked_c = 0
    q = ("MATCH (f:Finding)-[:RULED_BY]->(:Rule)-[:MEASURES]->"
         "(:AssessmentIndicator {code: $code}) "
         "WHERE f.params_hash = $ph AND NOT f.target_doc_id STARTS WITH 'control:' "
         "RETURN f.verdict AS v, f.target_doc_id AS d, count(*) AS c")
    bad = []
    for leg in mx["legs"]:
        code = parse_rule_id(CURRENT[leg])["indicator_code"]
        rows = list(session.run(q, code=code, ph=ph))
        got: dict = {}
        got_c: dict = {}
        for r in rows:
            sink = got_c if r["d"] in tier_c else got
            sink[r["v"]] = sink.get(r["v"], 0) + r["c"]
        s = leg.replace("-", "_").lower()
        # Tier C, where a Result exists for this leg. `scan_tierc_*` is registered only for
        # the tier-0 legs a reference host is judged on, and `not_applicable` is not in the
        # family (`scripts/scan_report.py::results`), so the absent name is the answer rather
        # than a lookup failure.
        from scan.figures import rname as _rname
        for verdict in ("pass", "fail", "error"):
            key_c = _rname(f"scan_tierc_{s}_{verdict}", cfg())
            if key_c not in results:
                continue
            checked_c += 1
            if got_c.get(verdict, 0) != results[key_c]:
                bad.append(f"TIER C {leg} {verdict}: graph {got_c.get(verdict, 0)}, "
                           f"registry {key_c} = {results[key_c]}")
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
    assert checked_c, ("no `scan_tierc_*` Result resolved, so the Tier C half of this check "
                       "verified nothing")

# ------------------------------------------------- the L0 report's matrices (report-draft §3)

L0_MATRICES = ("scan_matrix_tierA", "scan_matrix_tierC", "scan_matrix_product")


def _l0_csv(stem: str):
    """One L0 matrix CSV, or a skip. `cc_tasks/2026-09-09_report_draft.md` §1."""
    import csv as _csv
    from scan.figures import config as _config
    suffix = _config()["cycle_suffix"]
    path = REPO / "docs" / "reports" / f"{stem}_{suffix}.csv"
    if not path.is_file():
        pytest.skip(f"{path.relative_to(REPO)} has not been built")
    with path.open(encoding="utf-8") as fh:
        return path, list(_csv.DictReader(fh))


@pytest.mark.parametrize("stem", L0_MATRICES)
def test_every_l0_matrix_row_re_derives_from_the_graph(session, stem):
    """**Every cell of the published matrix, checked against the Finding it names.**

    The report's whole claim is that a stranger can walk back from a cell to the bytes behind
    it. That is only true if the cell names a Finding and the Finding says what the cell says,
    so this reads each row's `finding_ids` column, looks the Finding up in the graph by
    identity, and compares its verdict to the printed one. A cell whose Finding is absent from
    the graph, or disagrees with it, fails here rather than in front of a reader.

    Cells with no Finding identity are the ones that legitimately have none: `not declared` on
    an agency with no declared flagship, and `not measured` where a surface does not exist.
    They are counted, and a matrix in which EVERY cell lacked an identity would pass a
    comparison that never ran, so the count of checked cells is asserted to be non-zero.
    """
    path, rows = _l0_csv(stem)
    assert rows, f"{path.name} has no rows"
    # `leg` is not a property of a :Finding in the graph; `rule_id` and `indicator_code` are.
    # The rule id carries the leg (`RULE-A11-declared-v2`), which is the check that matters:
    # a cell must cite a Finding of ITS OWN leg on ITS OWN surface, or the matrix is
    # transposed somewhere and every verdict still resolves.
    q = ("MATCH (f:Finding {finding_id: $fid}) "
         "RETURN f.verdict AS verdict, f.rule_id AS rule_id, f.target_doc_id AS doc")
    checked, unidentified, bad = 0, 0, []
    for r in rows:
        pairs = [p for p in (r.get("finding_ids") or "").split() if "=" in p]
        by_leg = dict(p.split("=", 1) for p in pairs)
        for col, cell in r.items():
            if col in ("agency", "tier", "host_surface", "host_url", "candidate_surface",
                       "surface", "url", "declared", "finding_ids",
                       "refused_identified_client", "probes_on_host_surface"):
                continue
            fid = by_leg.get(col)
            if not fid:
                unidentified += 1
                assert cell in ("not declared", "not measured"), (
                    f"{path.name}: {r['agency']} {col} = {cell!r} names no Finding, and only "
                    f"an undeclared or unmeasured cell may do that")
                continue
            rec = session.run(q, fid=fid).single()
            assert rec is not None, (
                f"{path.name}: {r['agency']} {col} cites {fid}, which is not in the graph")
            assert rec["verdict"] == cell, (
                f"{path.name}: {r['agency']} {col} prints {cell!r}; Finding {fid} says "
                f"{rec['verdict']!r}")
            assert str(rec["rule_id"]).startswith(f"RULE-{col}-"), (
                f"{path.name}: {r['agency']} {col} cites {rec['rule_id']}, a rule for another "
                f"leg")
            want_doc = (r.get("candidate_surface") if col == "A12"
                        else r.get("host_surface") or r.get("surface"))
            assert rec["doc"] == want_doc, (
                f"{path.name}: {r['agency']} {col} is printed against {want_doc} and cites a "
                f"Finding on {rec['doc']}")
            checked += 1
    assert checked, f"{path.name}: not one cell named a Finding, so nothing was re-derived"
    print(f"{path.name}: {checked} cells re-derived, {unidentified} with no Finding by design")


def test_the_l0_matrices_and_the_report_agree_on_the_cycle():
    """The three matrices and the built report describe ONE cycle.

    A report assembled from a fresh matrix and a stale one would resolve every reference and
    still be two measurements wearing one date.
    """
    import json as _json
    from scan.figures import config as _config
    suffix = _config()["cycle_suffix"]
    report = REPO / "docs" / "reports" / f"2026-09_fss_ai_readiness_L0.md"
    hashes = set()
    for stem in L0_MATRICES:
        path = REPO / "docs" / "reports" / f"{stem}_{suffix}.json"
        if not path.is_file():
            pytest.skip(f"{path.name} has not been built")
        hashes.add(_json.loads(path.read_text(encoding="utf-8"))["params_hash"])
    assert len(hashes) == 1, f"the L0 matrices span {len(hashes)} parameter sets: {hashes}"
    if report.is_file():
        assert hashes.pop()[:12] in report.read_text(encoding="utf-8"), (
            "the built report does not carry the parameter hash its matrices were built under")
