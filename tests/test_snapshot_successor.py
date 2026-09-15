"""DN-004: what the report says about its snapshot's standing, and when the build refuses.

`cc_tasks/2026-09-14_standing_guards.md` decisions 2 and 3, over
`docs/design/2026-09-14_DN-004_report_snapshot_policy.md`.

**The situation.** `docs/reports/publication.yaml` names `scan_2026-09-10_rj2` as the cycle the
published report is a view of. Since `2026-09-14_rejudgements_on_the_log.md` put the fourteen
re-judgements on the event log, the graph also holds `scan_2026-09-10_rj3`, a later judgement of
the same evidence, superseding all 739 of the snapshot's Findings. Before that task nothing
could say so; after it, a RESULT said so in prose and the published document did not.

DN-004 decision 1 is that a successor moving no published number does not force a
republication — otherwise a corrected sentence in a rule becomes a publication event and the
project learns to leave corrections unpublished. Decisions 2 and 3 are what make that safe, and
they are the two halves of this file:

* the report SAYS the snapshot has a successor, from a query, with nothing typed;
* the build REFUSES if that successor ever moves a number the report publishes.

The second is the load-bearing one. Without it decision 1 is an invitation to publish under an
ever-staler snapshot, and the line the version block carries would be a sentence about a
comparison nobody makes.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

REPORTS = REPO / "docs" / "reports"
STEM = "2026-09_fss_ai_readiness_L0"
NUMERAL = re.compile(r"\d+(?:\.\d+)?")


def _yaml(path: Path) -> dict:
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def snapshot() -> str:
    return _yaml(REPORTS / "publication.yaml")["snapshot_cycle"]


@pytest.fixture(scope="module")
def succ():
    import snapshot_successor
    return snapshot_successor


@pytest.fixture(scope="module")
def live(succ, snapshot):
    """The query, run now. Skips rather than passes when Neo4j is down: a test that cannot ask
    the graph has not checked that the document agrees with it."""
    try:
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            info = succ.successor_info(s, snapshot)
        driver.close()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    return info


@pytest.fixture(scope="module")
def report_md() -> str:
    path = REPORTS / f"{STEM}.md"
    if not path.is_file():
        pytest.skip("the report has not been built")
    return path.read_text(encoding="utf-8")


#: Transformations the RENDERER makes on the way to the page, undone so a comparison is
#: about the sentence and not about typography. `pandoc --from=markdown` has smart quotes
#: on by default, so `snapshot's` reaches the PDF as a right single quotation mark; the
#: soft hyphen and the hyphen-newline are typst line breaking. None of them can touch a
#: numeral — the render boxes those — which is why the multiset gate next door needs only
#: the last two and this, which compares whole words, needs all four.
_RENDERED = (("-\n", ""), ("­", ""), ("’", "'"), ("‘", "'"),
             ("“", '"'), ("”", '"'))


def _norm(text: str) -> str:
    for a, b in _RENDERED:
        text = text.replace(a, b)
    return " ".join(text.split())


# ================================================== decision 2: the line IS the query's answer

def test_the_report_carries_the_supersession_line_the_query_answers(live, succ, report_md):
    """Decision 2, at build time and again here. The sentence in the shipped markdown is the
    one `supersession_line` builds from `successor_info`, character for character once the
    value markers are stripped — which is what "generated from a query, nothing typed" has to
    mean if it is to be checkable."""
    succ.set_value_marker(lambda t: t)
    want = _norm(succ.supersession_line(live))
    assert want in _norm(report_md), (
        f"the report does not carry the line the graph answers.\n  want: {want}")


def test_the_line_names_the_successor_the_graph_names(live, snapshot, succ, report_md):
    """The cheap sanity check the line exists to make cheap: a reader of the report can see the
    successor's name without opening the graph, and it is the successor the graph holds."""
    assert live, f"{snapshot} has no successor on the graph; this file's premise has changed"
    assert live["successor"] in report_md
    assert live["successor"] != snapshot


def test_the_lines_numerals_all_came_from_the_graph(live, succ):
    """Decision 2's lint clause. Every numeral in the sentence is one of the query's answers,
    so the bare-numeral lint's value markers cover all of them and the line needs no exemption
    region of its own. A numeral in it that the query did not produce would be a number typed
    into the report's title page."""
    succ.set_value_marker(lambda t: t)
    text = succ.supersession_line(live)
    from_query = {str(live[k]) for k in ("snapshot_findings", "successor_generation",
                                         "superseded_findings", "verdict_moves",
                                         "reason_only_changes")}
    # The cycle names and the decision reference are inside backticks, which the lint reads as
    # names; strip them the way `_mask` does and what is left must be query answers only.
    prose = re.sub(r"`[^`]*`", " ", text)
    assert set(NUMERAL.findall(prose)) <= from_query, (
        f"{sorted(set(NUMERAL.findall(prose)) - from_query)} appear in the line and in no "
        f"answer the query gave")


def test_the_bare_numeral_lint_passes_over_the_version_block_carrying_the_line(live, succ):
    """The line goes through the lint, not around it. `_mask` is given the block exactly as the
    builder assembles it, with the generated counts wrapped in the value markers, and must find
    nothing — no `numerals-exempt` region was opened for this paragraph and none is wanted."""
    import build_l0_report as B
    succ.set_value_marker(lambda t: f"{B.MARK_OPEN}{t}{B.MARK_CLOSE}")
    block = B.version_block(B.load_publication(), today="2026-09-14",
                            standing=succ.supersession_line(live))
    assert not B.lint_bare_numerals(block), B.lint_bare_numerals(block)
    assert "lint: numerals-exempt" not in block


def test_the_pdf_carries_the_line_with_its_numerals_intact(live, succ):
    """The multiset gate next door asserts the PDF and the markdown carry the same numbers; it
    would not notice the line being dropped, because a missing line takes its numerals with it
    and both sides stay equal only if the markdown lost it too. This asserts the sentence
    itself survived typst, numerals unbroken."""
    pdf_path = REPORTS / f"{STEM}.pdf"
    if not pdf_path.is_file():
        pytest.skip("the report has not been built to PDF")
    pypdf = pytest.importorskip("pypdf")
    text = _norm("\n".join(p.extract_text()
                           for p in pypdf.PdfReader(str(pdf_path)).pages))
    succ.set_value_marker(lambda t: t)
    line = succ.supersession_line(live)
    # Backticks are markup; typst renders the content without them.
    want = _norm(line.replace("`", "").replace("**", ""))
    assert want in text, f"the supersession line is not in the PDF.\n  want: {want}"
    assert collections.Counter(NUMERAL.findall(want)) <= collections.Counter(
        NUMERAL.findall(text))


def test_results_tagged_carries_the_same_fields_as_the_line(live, snapshot):
    """Decision 2's second consumer. The site's data file and the report's title page state one
    fact, and `tests/test_publication.py`'s reason for existing is that three consumers of one
    declaration cannot be allowed to drift."""
    doc = json.loads((REPO / "docs" / "data" / "results_tagged.json").read_text("utf-8"))
    assert doc["snapshot_cycle"] == snapshot
    standing = doc["snapshot_standing"]
    for k in ("successor", "successor_generation", "superseded_findings", "verdict_moves",
              "reason_only_changes", "snapshot_findings"):
        assert standing[k] == live[k], f"{k}: file says {standing[k]}, graph says {live[k]}"
    assert doc["successor_moves_no_published_number"] is True
    assert doc["successor_comparison"]["moved"] == 0
    assert doc["successor_comparison"]["uncovered"] == []


# ============================= decision 3: the build refuses when a published number moves

def test_the_comparison_covers_every_tagged_result_of_the_snapshot_cycle(succ, snapshot):
    """The closure that makes "nothing moved" mean anything. Every `{{result:...}}` the report
    quotes that carries this cycle's suffix is recomputed under the successor; one that is not
    is reported as UNCOVERED and refuses the build."""
    cmp_ = succ.check(snapshot)["comparison"]
    if cmp_ is None:
        pytest.skip("no successor on the graph")
    assert cmp_["uncovered"] == [], cmp_["uncovered"]
    assert cmp_["recomputed_and_compared"] == cmp_["tagged_results_on_this_cycle"]
    assert cmp_["recomputed_and_compared"] == len(succ.tagged_of_snapshot(snapshot))
    assert cmp_["recomputed_and_compared"] > 0


def test_today_the_successor_moves_nothing(succ, snapshot):
    """The condition that licenses publishing under `scan_2026-09-10_rj2` while
    `scan_2026-09-10_rj3` exists. It is a measurement, re-taken on every build, not a claim
    this file makes once."""
    cmp_ = succ.check(snapshot)["comparison"]
    if cmp_ is None:
        pytest.skip("no successor on the graph")
    assert cmp_["moves"] == [], json.dumps(cmp_["moves"][:10], indent=1, default=str)


def test_a_moved_number_refuses_and_names_it(succ):
    """**Red.** The whole point of decision 3, exercised against a planted move.

    Planted rather than produced, because producing one means re-judging a cycle into a
    different verdict, and a guard that can only be tested by moving a real number is a guard
    nobody tests. What is asserted is the contract every caller depends on: a refusal comes
    back, it NAMES the number, and it names the revision route.
    """
    planted = {"comparison": {
        "snapshot": "scan_X_rj2", "successor": "scan_X_rj3", "moved": 1, "uncovered": [],
        "tagged_results_on_this_cycle": 41, "recomputed_and_compared": 41,
        "matrix_rows_compared": 42,
        "moves": [{"what": "registered Result", "name": "scan_l0_a1_pass_X_rj2",
                   "base": "scan_l0_a1_pass", "snapshot": 3.0, "successor": 4.0}]}}
    text = succ.refuse_if_moved(planted)
    assert text is not None
    assert "scan_l0_a1_pass_X_rj2" in text
    assert "scan_X_rj3" in text
    assert succ.REVISION_DOC in text
    assert "publication.yaml" in text


def test_an_uncovered_tagged_result_refuses_too(succ):
    """**Red.** A number the comparison cannot speak for is not a number that did not move.

    This is the failure mode a comparison like this one dies of: a new tagged Result gets a
    name the recomputation does not produce, the loop skips it, and the gate reports zero moves
    over the subset it happened to understand.
    """
    planted = {"comparison": {
        "snapshot": "scan_X_rj2", "successor": "scan_X_rj3", "moved": 0,
        "uncovered": ["scan_something_new_X_rj2"],
        "tagged_results_on_this_cycle": 42, "recomputed_and_compared": 41,
        "matrix_rows_compared": 42, "moves": []}}
    text = succ.refuse_if_moved(planted)
    assert text is not None and "scan_something_new_X_rj2" in text


def test_no_successor_is_not_a_refusal_and_says_so(succ):
    """A report published the same day it was measured has no successor. That is the ordinary
    state, and it gets a sentence rather than an error or a silence."""
    assert succ.refuse_if_moved({"comparison": None}) is None
    line = succ.supersession_line({})
    assert "No later judgement" in line
    assert not NUMERAL.findall(re.sub(r"`[^`]*`", " ", line))


def test_two_successors_is_a_fatal_and_not_a_choice(succ):
    """Supersession is one to one (DN-003 decision 3). Two cycles claiming to replace one
    judgement is a publication defect, and picking the bigger of them is how a report comes to
    name a successor nobody decided on."""
    class _S:
        def run(self, *_a, **_k):
            return self

        def data(self):
            return [{"cycle": "a", "generation": 3, "cycle_kind": "rejudged", "pairs": 9,
                     "verdict_moves": 0, "reason_only": 0},
                    {"cycle": "b", "generation": 3, "cycle_kind": "rejudged", "pairs": 4,
                     "verdict_moves": 0, "reason_only": 0}]
    with pytest.raises(SystemExit, match="successor cycles on the graph"):
        succ.successor_info(_S(), "scan_X_rj2")


# ================================================ the refactor decision 3 needed, held in place

def test_computing_a_cycle_writes_nothing(tmp_path, snapshot):
    """`build_l0_matrices.compute` is what makes the comparison possible without side effects,
    and `--dry-run` is what it replaces: that flag wrote all six matrices and both fragments
    into the PUBLISHED tree before printing that it had not. A comparison built on it would
    have overwritten the snapshot's matrices with the successor's in order to find out whether
    they differed."""
    import build_l0_matrices as M
    before = {p: p.stat().st_mtime_ns for p in
              list((REPO / "docs" / "reports").glob("scan_matrix_*"))
              + list((REPO / "docs" / "reports" / "generated").glob("matrix_*.md"))}
    assert before, "no published matrices to guard"
    c = M.compute(snapshot)
    assert c["results"] and c["tier_a"]
    after = {p: p.stat().st_mtime_ns for p in before}
    assert after == before, [str(p) for p in before if after[p] != before[p]]
    assert M.OUT_DIR == REPO / "docs" / "reports"


def test_writing_into_a_temporary_tree_restores_the_published_one(tmp_path, snapshot):
    """The redirection is a swap, and it is restored on the way out — including on a failure,
    or the next build would write the published matrices into a directory that no longer
    exists."""
    import build_l0_matrices as M
    c = M.compute(snapshot)
    w = M.write_matrices(c, out_dir=tmp_path, gen_dir=tmp_path / "generated")
    assert M.OUT_DIR == REPO / "docs" / "reports"
    assert M.GEN_DIR == REPO / "docs" / "reports" / "generated"
    for pair in w["files"]:
        for f in pair:
            assert tmp_path in f.parents
            assert f.read_bytes() == (REPORTS / f.name).read_bytes(), f.name

    # And on the way out of a FAILURE. A payload of `None` makes `rules_fragment` raise part
    # way through the write, which is the case the `finally` exists for: without it the module
    # globals would still point at a temporary directory when the next build ran.
    with pytest.raises(TypeError):
        M.write_matrices({**c, "payload": None}, out_dir=tmp_path / "b",
                         gen_dir=tmp_path / "b" / "g")
    assert M.OUT_DIR == REPO / "docs" / "reports"
    assert M.GEN_DIR == REPO / "docs" / "reports" / "generated"
