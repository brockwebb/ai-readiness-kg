"""The PDF carries exactly the numbers the built markdown carries.

`cc_tasks/2026-09-10_report_pdf.md` §3.

The report's whole claim is that every number in it is a registered Result quoted by name
(`cc_tasks/2026-09-09_report_draft.md`). The markdown build enforces that. The PDF is a second
artifact produced from it, and a conversion that dropped a table cell, truncated a wide column
or invented a page number would carry the claim without deserving it. So the PDF's text layer
is diffed against the markdown as a MULTISET of numerals: not "are the numbers there" but "are
these the numbers, each exactly as often".

**Two exclusions, both declared, neither of them a tolerance:**

* *The image reference in the markdown.* `![...](.../scan_2026-09-09/cycle_over_cycle.svg)` is
  markup naming a file; its numerals are a path, and a reader of the PDF sees the figure, not
  the path.
* *Page furniture.* typst numbers the pages, and a page number is layout by definition — §3
  says "stripped of layout". A line whose entire content is one integer is dropped, and the
  test asserts that no more lines are dropped than there are pages, so the strip cannot
  quietly swallow a table cell. pandoc's generated `Figure 1:` numbering is stripped the same
  way and for the same reason; the caption itself stays.
* *The figure's own text.* The embedded SVG contains its own numerals (`0/22`, `[0.00, 0.15]`)
  which are in the PDF and in no line of the markdown. They are not typed either: every one
  carries a `data-src` naming the Result it came from, and `tests/test_scan_figures.py` checks
  them against the registry. This test subtracts them rather than ignoring the difference, so
  the arithmetic still has to close.

If the equality ever fails, the failure names the numerals that moved and in which direction.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "docs" / "reports"
STEM = "2026-09_fss_ai_readiness_L0"

#: A numeral as a reader meets it: digits, optionally with a decimal part.
NUMERAL = re.compile(r"\d+(?:\.\d+)?")
#: A markdown image reference. Markup, not content.
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
#: The text nodes of an SVG, which is where a figure keeps its numbers.
SVG_TEXT = re.compile(r"<text[^>]*>(.*?)</text>", re.S)


#: A line that is nothing but an integer: typst's page number, sitting in the footer.
PAGE_FURNITURE = re.compile(r"^\s*\d{1,3}\s*$")
#: pandoc's generated figure numbering, `Figure 1:`. The CAPTION is content and stays; the
#: number is a cross-reference the converter invented, which is the same class of thing as a
#: page number and is stripped for the same reason.
FIGURE_NUMBER = re.compile(r"\bFigure\s+\d+\s*:")


def strip_layout(text: str) -> tuple:
    """(text without generated numbering, how many page-number lines were removed)."""
    kept, dropped = [], 0
    for line in text.splitlines():
        if PAGE_FURNITURE.match(line):
            dropped += 1
            continue
        kept.append(FIGURE_NUMBER.sub("Figure:", line))
    return "\n".join(kept), dropped


def numerals(text: str) -> collections.Counter:
    """Every numeral in `text`, as a multiset. Line-broken words are rejoined first so a
    column edge cannot split a number in two and change the count."""
    joined = text.replace("-\n", "").replace("­", "")
    return collections.Counter(NUMERAL.findall(joined))


def figure_numerals(md: str) -> collections.Counter:
    """The numerals inside every figure the markdown embeds."""
    out: collections.Counter = collections.Counter()
    for m in IMAGE.finditer(md):
        rel = re.search(r"\(([^)]+)\)", m.group(0)).group(1)
        src = REPO / rel
        if not src.is_file():
            src = REPORTS / "generated" / Path(rel).name
        if src.is_file() and src.suffix == ".svg":
            for node in SVG_TEXT.findall(src.read_text(encoding="utf-8")):
                out += numerals(re.sub(r"<[^>]+>", " ", node))
    return out


@pytest.fixture(scope="module")
def built():
    md_path, pdf_path = REPORTS / f"{STEM}.md", REPORTS / f"{STEM}.pdf"
    if not md_path.is_file() or not pdf_path.is_file():
        pytest.skip("the report has not been built to PDF")
    pypdf = pytest.importorskip("pypdf")
    md = md_path.read_text(encoding="utf-8")
    reader = pypdf.PdfReader(str(pdf_path))
    pdf = "\n".join(p.extract_text() for p in reader.pages)
    return md, pdf, len(reader.pages)


#: **The committed PDF is behind the figure it embeds, by exactly these numerals and no others.**
#:
#: `cc_tasks/2026-09-11_f5_membership_through_fallback.md`. The report embeds
#: `figures/scan_2026-09-09_rj1/cycle_over_cycle.svg`, and that figure carried eleven rows
#: reading "not measured in this cycle" about legs that WERE measured — `figures.Reads` answered
#: `in` from the plain dict and never consulted its own evidence-bound fallback. The figure is
#: fixed and re-rendered; the PDF is a build product and decision 4 of that task says in terms
#: that `docs/reports/` is not rebuilt, so the two are one rebuild apart.
#:
#: The gate above subtracts the figure's numerals READ FROM DISK, which is what makes it, among
#: other things, a staleness detector for the PDF against its own figures. It is not wrong here;
#: it is right, and what it has found is true. So it is pinned rather than weakened: a strict
#: xfail, with the shortfall asserted exactly below, in the same shape
#: `tests/test_invariants.py` pins a stored payload's known defect.
#:
#: **Rebuilding the PDF clears both.** The xfail turns XPASS (strict, so it fails) and the
#: shortfall assertion fails with an empty multiset. Both say: delete this pin.
PDF_BEHIND_ITS_FIGURE = collections.Counter(
    {"0": 7, "33": 3, "32": 2, "24": 1, "35": 1, "34": 1, "2": 1})


@pytest.mark.xfail(strict=True, reason=(
    "The PDF is one rebuild behind the figure it embeds. `scan_2026-09-09_rj1`'s F5 carried 11 "
    "rows saying 'not measured in this cycle' about legs that were measured; the figure is fixed "
    "and re-rendered, and `cc_tasks/2026-09-11_f5_membership_through_fallback.md` decision 4 "
    "forbids rebuilding docs/reports/. `test_the_pdf_is_behind_by_exactly_the_figure_rows` "
    "asserts the shortfall is that and nothing else. The cycle-4 report revision clears it."))
def test_the_pdf_carries_exactly_the_markdowns_numbers(built):
    """§3's gate. Multiset equality, with the two declared exclusions."""
    md, pdf, pages = built
    body, dropped = strip_layout(pdf)
    assert dropped <= pages, (
        f"{dropped} lines were dropped as page numbers from a {pages}-page document; the "
        f"strip is removing content")
    want = numerals(IMAGE.sub(" ", md))
    got = numerals(body) - figure_numerals(md)

    missing = want - got
    extra = got - want
    assert not missing and not extra, (
        f"the PDF and the markdown do not carry the same numbers.\n"
        f"  in the markdown, missing from the PDF: {dict(missing)}\n"
        f"  in the PDF, absent from the markdown:  {dict(extra)}")


def test_the_pdf_is_behind_by_exactly_the_figure_rows(built):
    """The other half of the pin: the xfail says "this still fails", this says "by this much".

    The PDF is short of the markdown by the numerals its figure gained when eleven blank rows
    became rates, intervals and `k/n` again — and it is short by NOTHING ELSE, and carries no
    numeral the markdown lacks. That is what makes "the PDF is one rebuild behind" a measurement
    rather than an explanation: any other drift in either direction fails here.
    """
    md, pdf, _pages = built
    body, _dropped = strip_layout(pdf)
    want = numerals(IMAGE.sub(" ", md))
    got = numerals(body) - figure_numerals(md)
    assert got - want == collections.Counter(), (
        f"the PDF carries numerals the markdown does not: {dict(got - want)}. That is not "
        f"staleness in the figure; it is drift, and the pin does not cover it.")
    assert want - got == PDF_BEHIND_ITS_FIGURE, (
        f"the shortfall moved: {dict(want - got)}, pinned {dict(PDF_BEHIND_ITS_FIGURE)}. If the "
        f"PDF was rebuilt, delete this test and the xfail above it.")


def test_the_pdf_resolved_every_reference_and_kept_every_matrix_row(built):
    """§2's rendering checks, asserted rather than eyeballed: no `{{` token survived the two
    builds, and every body in the frame still has a row."""
    md, pdf, pages = built
    assert "{{" not in pdf, "an unresolved reference token reached the PDF"
    assert "{{" not in md
    agencies = ["BEA", "BJS", "BLS", "BTS", "CENSUS", "DRSMSU", "EIA", "ERS", "NAHMSAPHIS",
                "NASS", "NCES", "NCHS", "NCSES", "ORES", "SAMHSACBHS", "SOI"]
    flat = pdf.replace("-\n", "").replace("\n", " ")
    absent = [a for a in agencies if a not in flat]
    assert not absent, f"the matrix lost rows in conversion: {absent}"
    assert "this report" in flat, "the self-assessment row is missing"
    assert "GitHub Pages" in flat, "the self row does not name the planned host"
    assert 1 <= pages <= 20, pages
