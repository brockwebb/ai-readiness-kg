"""Figure registration resolves a read through ONE implementation, and every edge it writes
resolves to a Result that exists.

`cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 2.

**The incident.** `scripts/register_scan_figures.py::_resolve_read` was a THIRD implementation of
the evidence-bound fallback, and it carried a hardcoded list of three cycles —
`scan_2026-09-09_rj1`, `scan_2026-09-10_rj1`, `scan_2026-09-07b_rj2`. A figure of any other
re-judged cycle resolved every fallback name to itself, so the `CONTAINS` edge pointed at a name
nobody had registered and the link failed; 93 of them did on its first run
(`cc_tasks/2026-09-11_f5_membership_through_fallback_RESULT.md` §8 item 5). A list of cycle names
inside a resolver goes stale the next time a cycle is re-judged, and that one went stale the same
day it was written.

So the rule lives in `assessment/harness/scan/figures.py` and the registrar ASKS it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import figures as FIG                                     # noqa: E402
import register_scan_figures as R                                   # noqa: E402

#: The cycles whose Figure artifacts this task registered, and which the report may embed.
RJ2_CYCLES = ("scan_2026-09-09_rj2", "scan_2026-09-10_rj2")

#: Anything that turns `…_rjN` into `…` — the resolution rule, however it is spelled.
_STRIPPERS = (re.compile(r"_rj\\d\+\$"), re.compile(r'removesuffix\(["\']_rj\d+["\']\)'))

#: Every module allowed to carry one, with the reason it is not a duplicate to be deleted.
#:
#: The rule of decision 2 is that FIGURE REGISTRATION has one resolver. It does. The second
#: entry is a different question in a different layer — *what should I register?*, asked before
#: any figure exists — and it is deliberately not an import: coupling the registrar to the
#: renderer is what let three families share one Result name
#: (`cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §1). It is held equal to the renderer's by
#: `tests/test_rejudgement_gen9.py::test_the_registrar_and_the_renderer_agree_on_where_a_name_falls_back_to`,
#: which is the shape that reports a divergence instead of propagating it.
ALLOWED = {
    "assessment/harness/scan/figures.py":
        "`_source_name` and `_rj_source` ARE the rule; `Reads.__getitem__` is its only user.",
    "scripts/register_gen9_rejudged.py":
        "`fallback_target`, the registrar's paired implementation, held equal by a test.",
    "scripts/register_rejudged_cycles.py":
        "`cycle.removesuffix('_rj1')` inside a DESCRIPTION string, naming the measured cycle "
        "in prose. It resolves nothing and its input is a literal from this module's own "
        "`PAIRS`; the harness-v5 registrar is not re-run.",
}


def _modules():
    for base in ("scripts", "assessment", "kg"):
        for p in sorted((REPO / base).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            yield p


def test_no_module_but_figures_py_strips_an_rj_suffix():
    """Decision 2's clause, scoped to what it is about: a module that re-derives where a name
    falls back to, rather than asking. A test file may hold one — a test that re-derives the rule
    is how the rule gets checked."""
    offenders = []
    for p in _modules():
        rel = str(p.relative_to(REPO))
        if rel in ALLOWED:
            continue
        body = p.read_text(encoding="utf-8")
        # Comments and docstrings name `_rj1` constantly; only code that MATCHES counts.
        code = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("#"))
        for pat in _STRIPPERS:
            if pat.search(code):
                offenders.append(f"{rel}: {pat.pattern}")
    assert not offenders, (
        "a second implementation of the fallback rule: " + "; ".join(offenders)
        + ". Ask `scan.figures.Reads` instead — decision 2, and the 93 failed links that "
          "made it a decision.")


def test_the_deleted_resolver_stays_deleted():
    assert not hasattr(R, "_resolve_read"), (
        "`_resolve_read` is back. It is the hardcoded three-cycle list; deleting it is "
        "decision 2.")
    src = (REPO / "scripts" / "register_scan_figures.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    for cyc in ("scan_2026-09-09_rj1", "scan_2026-09-10_rj1", "scan_2026-09-07b_rj2"):
        assert f'"{cyc}"' not in code and f"'{cyc}'" not in code, (
            f"{cyc} is named in the registrar's code again")


def test_resolve_read_is_exactly_what_the_renderer_resolved():
    """The registrar's answer and the renderer's are the same object's answer, not two that
    agree today."""
    view = FIG.Reads({"scan_a3_pass_2026-09-09": 3.0, "scan_a3_pass_2026-09-10_rj2": 7.0})
    view._licensed = {"scan_a3_pass_2026-09-09_rj2"}
    assert R.resolve_read(view, "scan_a3_pass_2026-09-10_rj2") == "scan_a3_pass_2026-09-10_rj2"
    assert R.resolve_read(view, "scan_a3_pass_2026-09-09_rj2") == "scan_a3_pass_2026-09-09"
    with pytest.raises(FIG.UnlicensedFallback):
        R.resolve_read(view, "scan_a5_pass_2026-09-09_rj2")


# ------------------------------------------------------------------ the graph

@pytest.fixture(scope="module")
def session():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        c = load_project_config(REPO)
        driver = get_neo4j_driver(c)
        with driver.session(database=c["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with driver.session(database=c["neo4j"]["database"]) as s:
        yield s
    driver.close()


@pytest.mark.parametrize("cycle", RJ2_CYCLES)
def test_every_figure_of_the_rj2_cycles_is_registered(session, cycle):
    suffix = FIG._suffix(cycle)
    on_disk = {f"{stem}_{suffix}" for stem in R.figures(cycle)}
    assert on_disk, f"no SVG on disk for {cycle}"
    rows = session.run(
        "MATCH (f:Figure) WHERE f.name ENDS WITH $s AND f.state <> 'superseded' "
        "RETURN f.name AS n", s=f"_{suffix}")
    assert {r["n"] for r in rows} >= on_disk, (
        f"{cycle}: a figure on disk with no live Figure artifact")


@pytest.mark.parametrize("cycle", RJ2_CYCLES)
def test_every_contains_edge_resolves_to_a_live_result(session, cycle):
    """A provenance edge that names a Result nobody registered is the failure decision 2 is
    about. This asks the graph, not the script."""
    suffix = FIG._suffix(cycle)
    rows = session.run(
        "MATCH (f:Figure)-[:CONTAINS]->(r) WHERE f.name ENDS WITH $s "
        "RETURN f.name AS f, r.name AS r, labels(r) AS lb", s=f"_{suffix}")
    edges = [(r["f"], r["r"], r["lb"]) for r in rows]
    assert edges, f"{cycle}: no CONTAINS edge at all"
    bad = [e for e in edges if "Result" not in e[2] or not e[1]]
    assert not bad, f"{cycle}: edges to something that is not a Result: {bad[:5]}"


@pytest.mark.parametrize("cycle", RJ2_CYCLES)
def test_every_read_the_svg_declares_has_an_edge(session, cycle):
    """`data-reads` is what the figure looked up; every one of them, resolved through the one
    resolver, must be on the far end of a `CONTAINS` edge."""
    try:
        view = R.reads_view()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"registry unreadable: {exc}")
    suffix = FIG._suffix(cycle)
    rows = session.run(
        "MATCH (f:Figure)-[:CONTAINS]->(r:Result) WHERE f.name ENDS WITH $s "
        "RETURN f.name AS f, collect(DISTINCT r.name) AS rs", s=f"_{suffix}")
    have = {r["f"]: set(r["rs"]) for r in rows}
    missing = []
    for stem, f in R.figures(cycle).items():
        if not f["reads"]:
            continue
        want = {R.resolve_read(view, n) for n in f["reads"]}
        got = have.get(f"{stem}_{suffix}", set())
        missing += [f"{stem}_{suffix} -> {n}" for n in sorted(want - got)]
    assert not missing, f"{cycle}: reads with no edge: {missing[:10]}"
