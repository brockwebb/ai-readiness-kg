#!/usr/bin/env python3
"""The ICSP roll-up of the sixteen checks, placed on USAFacts' three-track ladder. **Zero spend, no network.**

`cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md`
Part B item 7, implementing DN-020. The roll-up's bucket column WAS the four criteria of the
USAFacts guide plus a "release engineering" bucket; DN-020 section 4 re-parents the sixteen
measured checks onto USAFacts' August 2026 framework — three tracks, three levels each, three
prerequisites — and dissolves the "release engineering" bucket (its one measured check, a change
history a program can follow, is Access II in USAFacts' own words, "lineage/change notes").

One portrait page in three forms, Markdown (the source), Word, and a PDF rendered from the
Markdown (the `render_report` pattern), patterned on `scripts/sixteen_checks_build.py`. Every cell
is a query over the framework record or the cycle of record; the builder types no prose of its own
beyond the column headers, the fixed two-sentence lineage intro and the fixed footer:

* the **USAFacts rung** column is the rung's short label (DN-020 section 4 order);
* the **What the framework asks for** column quotes the rung's caption from the record (a
  `UsafactsLevel` node's `name`, a `UsafactsPrerequisite` node's `text`) — USAFacts' own words,
  the one place the vocabulary rule lets USAFacts' terminology stand (e.g. Access II's verbatim
  caption says "agents can crawl"), so the banned-word scan runs over the project's prose, not
  over these quoted captions (DN-016 / the task's vocabulary rule; recorded in the RESULT);
* the **Checks** column is the count and the plain names (`rf_name_brief`) of the checks that
  DESCEND_FROM that rung on USAFacts' ladder (the `basis: DN-020 §4` edges), Scored ones marked;
* the **Quality concern** column is the distinct FCSM 20-04 concern short labels those checks
  serve (the `SERVES_FCSM_CONCERN` edges);
* the **Agencies passing** column is, from the cycle of record, the count of the sixteen agencies
  with no fail in the rung, under the four-state rule — DN-020 T3 is the roll-up's old rule
  unchanged. A rung with no measured check reads "none measured" (Access III, Context III and
  Evaluation I to III: the tracks the sensor does not reach yet, DN-020 T4).

    /opt/anaconda3/bin/python3 scripts/readiness_rollup_build.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import diagnostic_package as D  # noqa: E402
import diagnostic_package_build as B  # noqa: E402
import readiness_brief_build as RB  # noqa: E402
import sixteen_checks_build as S  # noqa: E402
import instrument as I  # noqa: E402

GENERATOR = "scripts/readiness_rollup_build.py"
TASK = "cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md"
OUT = REPO / "reports" / "diagnostic" / "rollup"
STEM = "Readiness_Diagnostic_Rollup"

TITLE = "Readiness diagnostic: what it measures, placed on the USAFacts ladder"
#: The two-sentence lineage intro (Part B item 7): the August 2026 framework in one sentence, the
#: predecessor guide in one. `*AI-ready data*` renders italic; "AI" stands only inside USAFacts'
#: own title (the vocabulary rule).
INTRO = [
    "The readiness diagnostic places its checks on USAFacts' August 2026 framework for "
    "AI-ready government data: three tracks, Agentic Access, Agentic Context and Agentic "
    "Evaluation, three levels in each, with three prerequisites that hold before any level "
    "applies.",
    "That framework grew from USAFacts' earlier guide to *AI-ready data*, whose four criteria "
    "the diagnostic first used; the checks are the same readings, re-parented onto the ladder "
    "an agency climbs at its own pace.",
]
#: The footer: line one names the lineage and the concern source; line two names the two kinds of
#: user. `*AI-ready data*` renders italic.
FOOTER = [
    "Checks are placed on USAFacts (2026), *AI-ready data*, August 2026 framework; concerns from "
    "FCSM 20-04, Accessibility dimension, after Webb 2026.",
    "Standard user: no key. API user: a free key by open registration, a person completes an "
    "email step.",
]
#: The passing-column footnote (Part B item 7, DN-020 T3): a check not measured is excluded,
#: never a fail.
PASSING_FOOTNOTE = ("An agency passes a rung when none of the rung's checks that could be "
                    "measured for it comes back fail; a check not measured for an agency, or not "
                    "measured on the cycle of record at all, is left out of that agency's count "
                    "and is never read as a fail.")
#: A rung the sensor does not reach yet carries no measured check (DN-020 T4). Its passing cell
#: reads this rather than a count; honestly empty, not a zero.
NONE_MEASURED = "none measured"

#: The eleven rungs in DN-020 section 4 order: the two prerequisites that carry a check, the four
#: measured levels, then the five rungs with no measured check. `(node_id, short_label)`.
RUNG_ORDER = [
    ("usaf:pre:discoverable", "Prerequisite, discoverable"),
    ("usaf:pre:licensed", "Prerequisite, clearly licensed"),
    ("usaf:access:1", "Access I"),
    ("usaf:access:2", "Access II"),
    ("usaf:context:1", "Context I"),
    ("usaf:context:2", "Context II"),
    ("usaf:access:3", "Access III"),
    ("usaf:context:3", "Context III"),
    ("usaf:evaluation:1", "Evaluation I"),
    ("usaf:evaluation:2", "Evaluation II"),
    ("usaf:evaluation:3", "Evaluation III"),
]

#: Numbers nought to sixteen as words, so the page carries no bare digit (the digit audit).
_WORD = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
         14: "fourteen", 15: "fifteen", 16: "sixteen"}


def word(n: int) -> str:
    if n not in _WORD:
        raise SystemExit(f"FATAL: {n} is outside the spelled-number range nought to sixteen")
    return _WORD[n]


# --------------------------------------------------------------------------------- the data

def usafacts_nodes(g: dict) -> dict:
    """`{node_id: node}` for the `UsafactsTrack`/`UsafactsLevel`/`UsafactsPrerequisite` nodes."""
    return {n["id"]: n for n in g["nodes"]
            if set(n["labels"]) & {"UsafactsTrack", "UsafactsLevel", "UsafactsPrerequisite"}}


def descends_usafacts(g: dict) -> dict:
    """`{rung_id: [leg, ...]}` from the DESCENDS_FROM edges that place a check on USAFacts' ladder
    (`to` a `usaf:*` node), in the leg convention's order within a rung."""
    by_id = {n["id"]: n for n in g["nodes"]}
    order = {leg: i for i, leg in enumerate(
        ["A1", "A2", "A3", "A4", "A5", "A6", "A8", "A9", "A10", "A11-declared",
         "A12", "A13", "B3", "D1", "D4", "F4"])}
    out: dict = {}
    for e in g["edges"]:
        if e["type"] != "DESCENDS_FROM" or not str(e["to"]).startswith("usaf:"):
            continue
        leg = by_id[e["from"]]["properties"]["leg"]
        out.setdefault(e["to"], []).append(leg)
    for rid in out:
        out[rid].sort(key=lambda l: order.get(l, 999))
    return out


def rung_asks(node: dict) -> str:
    """The rung's caption from the record: a level's `name`, a prerequisite's `text` (the
    prerequisite's `name` is already the rung label, so its sentence is the more useful quote)."""
    if "UsafactsPrerequisite" in node["labels"]:
        return str(node["properties"]["text"])
    return str(node["properties"]["name"])


def bucket_pass_from_edges(legs: list[str], grid: dict) -> int | None:
    """Agencies (of sixteen) with no fail across this rung's measured checks, under the
    four-state rule. `None` when the rung has no check present on the cycle of record."""
    cols = {c["code"] for c in grid["columns"]}
    present = [l for l in legs if l in cols]
    if not present:
        return None
    n = 0
    for r in grid["rows"]:
        states = [I.four_state([p["verdict"] for p in r["cells"][leg]["pages"]]) for leg in present]
        measured = [s for s in states if s in ("pass", "fail", "partial")]
        if measured and not any(s == "fail" for s in measured):
            n += 1
    return n


#: DN-020 section 4's placement as a LITERAL rung -> display-leg map, independent of the record's
#: DESCENDS_FROM edges, for the second verification path. The legs are the record spec legs the
#: names resolve to (the roll-up's grid uses these codes); this is the cross-check that the edges
#: written in Part A agree with DN-020 section 4 as a reader reads it.
RUNG_LEGS = {
    "usaf:pre:discoverable": ["A5", "A6", "D4"],
    "usaf:pre:licensed": ["D1"],
    "usaf:access:1": ["A1", "A3", "A4", "A12", "A11-declared", "A10"],
    "usaf:access:2": ["A2", "A9", "A13", "F4"],
    "usaf:context:1": ["B3"],
    "usaf:context:2": ["A8"],
}


def verify_pass_by_rung(grid: dict) -> dict:
    """The passing counts recomputed by a SECOND code path: the full per-agency state matrix,
    grouped by the literal DN-020 section 4 rung map rather than by the record's edges. Agreement
    with the rendered numbers (which come from the edges) cross-checks the edges against DN-020."""
    cols = [c["code"] for c in grid["columns"]]
    matrix = {r["agency"]: {leg: I.four_state([p["verdict"] for p in r["cells"][leg]["pages"]])
                            for leg in cols} for r in grid["rows"]}
    out: dict = {}
    for rung, _ in RUNG_ORDER:
        present = [l for l in RUNG_LEGS.get(rung, []) if l in cols]
        if not present:
            out[rung] = None
            continue
        cnt = 0
        for states in matrix.values():
            vals = [states[leg] for leg in present]
            meas = [v for v in vals if v in ("pass", "fail", "partial")]
            if meas and "fail" not in meas:
                cnt += 1
        out[rung] = cnt
    return out


def rung_rows(g: dict, grid: dict) -> list[dict]:
    """One row per rung in DN-020 section 4 order. Each cell is a query over the record and the
    cycle of record."""
    nodes = usafacts_nodes(g)
    desc = descends_usafacts(g)
    check = {r["leg"]: r for r in RB.check_rows(g)}
    concerns = S.concern_of(g)
    scored = set(S.scored_legs(g))

    rows = []
    for rid, label in RUNG_ORDER:
        node = nodes.get(rid)
        if node is None:
            raise SystemExit(f"FATAL: no USAFacts rung node {rid!r}; run add_usafacts_lineage.py")
        legs = desc.get(rid, [])
        for leg in legs:
            if leg not in check:
                raise SystemExit(f"FATAL: DESCENDS_FROM names {leg}, absent from the check rows")
            if leg not in concerns or "primary" not in concerns.get(leg, {}):
                raise SystemExit(f"FATAL: {leg} has no primary SERVES_FCSM_CONCERN edge")
        checks = [{"leg": leg, "name": S.house_dashes(str(check[leg]["name"])),
                   "scored": leg in scored} for leg in legs]
        distinct = []
        for leg in legs:
            for c in (concerns[leg]["primary"], concerns[leg].get("also")):
                if c and c not in distinct:
                    distinct.append(c)
        concern_cell = "; ".join(S.CONCERN_SHORT[c] for c in sorted(distinct))
        concern_cell = (concern_cell[0].upper() + concern_cell[1:]) if concern_cell else ""
        n_pass = bucket_pass_from_edges(legs, grid)
        passing = NONE_MEASURED if n_pass is None else f"{word(n_pass)} of sixteen"
        rows.append({
            "rung": rid, "label": label,
            # the caption is USAFacts' verbatim quote; the house-dash rule still applies to the
            # rendered cell (an em/en dash becomes the house comma), the record is not edited.
            "asks": S.house_dashes(rung_asks(node)),
            "checks": checks, "check_count": len(checks),
            "concern": concern_cell, "concern_codes": sorted(distinct),
            "passing": passing, "passing_n": n_pass,
        })
    return rows


def checks_text(row: dict) -> str:
    """The Checks cell as one string (Markdown and PDF): count word, then names, Scored marked."""
    if row["check_count"] == 0:
        return "None"
    head = f"{word(row['check_count']).capitalize()} check" + ("s" if row["check_count"] != 1 else "")
    names = [c["name"] + (" (Scored)" if c["scored"] else "") for c in row["checks"]]
    return head + ": " + "; ".join(names)


# ------------------------------------------------------------------------------- markdown

def _cell(t) -> str:
    return str(t).replace("|", "/").replace("\n", " ")


def build_markdown(rows: list[dict]) -> str:
    L = [f"# {TITLE}", "",
         f"Generated by `{GENERATOR}` from the framework record and the cycle of record.", "",
         INTRO[0], "", INTRO[1], "",
         "| USAFacts rung | What the framework asks for | Checks | Quality concern | "
         "Agencies passing every check in this rung^a |",
         "|" + "|".join("-" * n for n in (14, 26, 32, 16, 20)) + "|"]
    for r in rows:
        L.append(f"| {_cell(r['label'])} | {_cell(r['asks'])} | {_cell(checks_text(r))} | "
                 f"{_cell(r['concern'])} | {_cell(r['passing'])} |")
    L += ["", f"^a {PASSING_FOOTNOTE}", "", FOOTER[0], "", FOOTER[1], ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------------- docx

def build_docx(rows: list[dict], path: Path, body_pt: float = 9.5) -> None:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor as DRGB

    BLACK, GREY, ORANGE = DRGB(0x00, 0x00, 0x00), DRGB(0x55, 0x55, 0x55), DRGB(0xC2, 0x56, 0x00)
    doc = Document()
    doc.styles["Normal"].font.name = B.FONT
    doc.styles["Normal"].font.size = Pt(body_pt)
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin = sec.bottom_margin = Inches(0.5)
    sec.left_margin = sec.right_margin = Inches(0.5)

    def run(p, text, *, bold=False, size=body_pt, color=BLACK, italic=False):
        r = p.add_run(text)
        r.font.name = B.FONT
        r.font.bold = bold
        r.font.italic = italic
        r.font.size = Pt(size)
        r.font.color.rgb = color
        return r

    def para(text="", *, bold=False, size=body_pt, color=BLACK, after=4, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(0)
        if text:
            run(p, text, bold=bold, size=size, color=color, italic=italic)
        return p

    def rich_para(segments, *, size=body_pt, after=2, color=GREY):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(0)
        for text, italic in segments:
            run(p, text, size=size, italic=italic, color=color)
        return p

    def intro_para(text, *, after):
        """An intro line that renders `*AI-ready data*` italic where it appears."""
        pre, mark, post = text.partition("*AI-ready data*")
        if mark:
            rich_para([(pre, False), ("AI-ready data", True), (post, False)],
                      size=body_pt, after=after, color=BLACK)
        else:
            para(text, size=body_pt, after=after)

    para(TITLE, bold=True, size=15, after=4)
    intro_para(INTRO[0], after=3)
    intro_para(INTRO[1], after=6)

    headers = ["USAFacts rung", "What the framework asks for", "Checks", "Quality concern",
               "Agencies passing every check in this rung"]
    widths = [1.0, 1.85, 2.55, 0.95, 1.15]
    cell_pt = body_pt - 1.5
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    mar = OxmlElement("w:tblCellMar")
    for side, w in (("top", "20"), ("bottom", "20"), ("left", "50"), ("right", "50")):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), w)
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    t._tbl.tblPr.append(mar)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.width = Inches(widths[i])
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run(p, h + ("ᵃ" if i == 4 else ""), bold=True, size=cell_pt)

    def put_plain(cell, width, text, *, color=BLACK):
        cell.width = Inches(width)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        run(p, text, size=cell_pt, color=color)

    for r in rows:
        cells = t.add_row().cells
        put_plain(cells[0], widths[0], r["label"])
        put_plain(cells[1], widths[1], r["asks"])
        cells[2].width = Inches(widths[2])
        cp = cells[2].paragraphs[0]
        cp.paragraph_format.space_after = Pt(0)
        cp.paragraph_format.space_before = Pt(0)
        if r["check_count"] == 0:
            run(cp, "None", size=cell_pt, color=GREY)
        else:
            head = f"{word(r['check_count']).capitalize()} check" + ("s" if r["check_count"] != 1 else "")
            run(cp, head, size=cell_pt, color=GREY)
            for c in r["checks"]:
                pp = cells[2].add_paragraph()
                pp.paragraph_format.space_after = Pt(0)
                pp.paragraph_format.space_before = Pt(0)
                run(pp, c["name"], size=cell_pt, color=BLACK)
                if c["scored"]:
                    run(pp, " (Scored)", size=cell_pt, color=ORANGE)
        put_plain(cells[3], widths[3], r["concern"])
        put_plain(cells[4], widths[4], r["passing"],
                  color=(GREY if r["passing_n"] is None else BLACK))

    para("ᵃ " + PASSING_FOOTNOTE, size=cell_pt, color=GREY, after=6)
    pre, _, post = FOOTER[0].partition("*AI-ready data*")
    rich_para([(pre, False), ("AI-ready data", True), (post, False)], after=1)
    rich_para([(FOOTER[1], False)], after=0)
    doc.save(str(path))


# -------------------------------------------------------------------------------------- pdf

def render_pdf(md_path: Path, pdf_path: Path, body_pt: float, title: str) -> None:
    """Render the committed Markdown to a portrait PDF (the `render_report` pattern)."""
    size = body_pt - 1.5
    header = ("#set page(margin: (x: 1.4cm, y: 1.2cm))\n"
              "#show figure: set block(breakable: true)\n"
              f"#show heading: set text(size: {size + 3}pt)\n"
              "#show heading: set block(above: 0.5em, below: 0.4em)\n"
              "#set table(inset: (x: 3pt, y: 1.6pt), stroke: 0.4pt)\n"
              "#set text(hyphenate: false)\n"
              "#set par(justify: false, leading: 0.55em, spacing: 0.7em)")
    cmd = ["pandoc", str(md_path), "--from=markdown+pipe_tables+raw_attribute-smart",
           "--pdf-engine=typst", "--metadata", f"title={title}",
           "--variable", "papersize=us-letter", "--variable", f"fontsize={size}pt",
           "--variable", f"header-includes={header}", "-o", str(pdf_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/typst failed:\n{r.stderr[-1500:]}")


def pdf_pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def pdf_text(pdf: Path) -> str:
    from pypdf import PdfReader
    return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(pdf)).pages)


# ------------------------------------------------------------------------------------ checks

#: A citation is a name; its digits are not stray numbers (FCSM 20-04, USAFacts 2026, Webb 2026).
_CITATION = re.compile(r"FCSM \d{2}-\d{2}|USAFacts \(\d{4}\)|Webb \d{4}|\(\d{4}\)")
_CHECK_CODE = re.compile(r"\b[A-G][0-9]{1,2}\b")


def digit_audit(rows: list[dict]) -> list[str]:
    """No bare number in any record-derived cell. The title/intro/footer are fixed task constants
    with citation years and are not scanned; the rung labels (Access I/II/III) carry Roman
    numerals, not digits, so the audit never sees them as numbers."""
    bad = []
    for r in rows:
        cells = {"label": r["label"], "asks": r["asks"], "checks": checks_text(r),
                 "concern": r["concern"], "passing": r["passing"]}
        for k, v in cells.items():
            for m in B._BARE.finditer(str(v)):
                bad.append(f"{r['rung']} {k}: bare number {m.group(0)!r}")
    return bad


def project_prose(rows: list[dict]) -> str:
    """The text the vocabulary scan runs over: the project's own prose and the check names, NOT
    the verbatim USAFacts captions in the `asks` column. USAFacts' August 2026 captions are a
    quoted zone (Access II's reads "agents can crawl"), and the banned-word rule guards what the
    project writes about its own client, not what USAFacts wrote about agents (task vocabulary
    rule; RESULT). The fixed intro/footer are project prose and ARE scanned."""
    parts = list(INTRO) + list(FOOTER) + [PASSING_FOOTNOTE, TITLE]
    for r in rows:
        parts.append(r["label"])
        parts.append(r["concern"])
        parts.append(r["passing"])
        parts.extend(c["name"] for c in r["checks"])
    return "\n".join(parts)


def bucket_counts(rows: list[dict]) -> dict:
    """`{rung_label: check_count}` for the rendered rungs, to compare against Part A's edge split."""
    return {r["label"]: r["check_count"] for r in rows}


# -------------------------------------------------------------------------------------- build

def build(out: Path = OUT, *, measure: bool = True, body_pt: float = 9.5) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    grid = I.load_grid(I.load_config())
    rows = rung_rows(g, grid)

    md_path, docx_path, pdf_path = out / f"{STEM}.md", out / f"{STEM}.docx", out / f"{STEM}.pdf"
    md = build_markdown(rows)
    md_path.write_text(md, encoding="utf-8")
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    build_docx(rows, docx_path, body_pt)
    render_pdf(md_path, pdf_path, body_pt, TITLE)

    docx_pages = RB.docx_pages(docx_path) if measure else None
    ppages = pdf_pages(pdf_path) if measure else None

    # ---- the Part B checks ----
    # Part A split, recomputed from the record's USAFacts DESCENDS_FROM edges, keyed by rung label.
    label_of = {rid: label for rid, label in RUNG_ORDER}
    part_a_split: dict = {}
    for e in g["edges"]:
        if e["type"] == "DESCENDS_FROM" and str(e["to"]).startswith("usaf:"):
            part_a_split[label_of[e["to"]]] = part_a_split.get(label_of[e["to"]], 0) + 1
    rendered_counts = bucket_counts(rows)
    # Rungs with zero checks have no edge and are absent from the edge split; compare on the rungs
    # that carry at least one check.
    counts_match = all(part_a_split.get(label) == rendered_counts.get(label)
                       for label in part_a_split)

    verify = verify_pass_by_rung(grid)
    rendered_pass = {r["rung"]: r["passing_n"] for r in rows}
    pass_match = all(verify.get(rid) == rendered_pass.get(rid) for rid in rendered_pass)

    scored_rendered = sorted(c["leg"] for r in rows for c in r["checks"] if c["scored"])
    scored_record = sorted(S.scored_legs(g))

    md_text = md
    docx_text = RB.docx_text(docx_path)
    pdf_txt = pdf_text(pdf_path) if measure else ""
    # The vocabulary and dash scans run over the project's prose only; the verbatim USAFacts
    # captions (the `asks` column) are a quoted zone the banned-word rule exempts.
    prose = project_prose(rows)
    texts = {"project_prose": prose}

    md_check_codes = sorted(set(_CHECK_CODE.findall(md_text)))
    md_dashes = RB.dash_hits(prose)
    md_508 = "508" in md_text

    checks = {
        "docx_pages": docx_pages, "pdf_pages": ppages,
        "digit_audit": digit_audit(rows),
        "font_colour_audit": {"docx": RB.docx_font_colour_audit(docx_path)},
        "vocabulary": {k: D.banned_hits_prose(v) for k, v in texts.items()},
        "dashes": {"project_prose": RB.dash_hits(prose)},
        "markdown_check_codes": md_check_codes,
        "markdown_dashes": md_dashes,
        "markdown_mentions_508": md_508,
        "bucket_counts_rendered": rendered_counts,
        "part_a_split": part_a_split,
        "bucket_counts_match_part_a": counts_match,
        "agencies_passing_rendered": rendered_pass,
        "agencies_passing_verify_by_rung": verify,
        "agencies_passing_match": pass_match,
        "scored_rendered": scored_rendered,
        "scored_record": scored_record,
        "scored_match_four_specified": scored_rendered == scored_record and len(scored_record) == 4,
    }

    failures = []
    if measure:
        if docx_pages is None or docx_pages > 2:
            failures.append(f"docx has {docx_pages} pages, over 2")
        if ppages is None or ppages > 2:
            failures.append(f"pdf has {ppages} pages, over 2")
    if checks["digit_audit"]:
        failures.append("digit_audit")
    if checks["font_colour_audit"]["docx"]:
        failures.append("font_colour_audit")
    for k in ("vocabulary", "dashes"):
        if any(checks[k].values()):
            failures.append(k)
    if md_check_codes:
        failures.append("markdown_check_codes")
    if md_dashes:
        failures.append("markdown_dashes")
    if md_508:
        failures.append("markdown_mentions_508")
    if not counts_match:
        failures.append("bucket_counts_match_part_a")
    if not pass_match:
        failures.append("agencies_passing_match")
    if not checks["scored_match_four_specified"]:
        failures.append("scored_match_four_specified")

    report = {
        "generated_by": GENERATOR, "task": TASK, "cycle": grid["cycle"],
        "body_pt": body_pt,
        "rows": [{"rung": r["rung"], "label": r["label"], "check_count": r["check_count"],
                  "legs": [c["leg"] for c in r["checks"]], "scored": [c["leg"] for c in r["checks"] if c["scored"]],
                  "concern": r["concern"], "passing": r["passing"]} for r in rows],
        "products": [
            {"name": md_path.name, "md_sha256": md_sha},
            {"name": docx_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(), "pages": docx_pages},
            {"name": pdf_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(), "pages": ppages},
        ],
        "checks": checks, "failures": failures,
    }
    (out / "build_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("FATAL: build checks failed: " + ", ".join(failures) + "\n"
                         + json.dumps(checks, indent=1, ensure_ascii=False)[:4000])
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-measure", action="store_true", help="skip page measurement (fast)")
    a = ap.parse_args(argv)
    rep = build(measure=not a.no_measure)
    print(json.dumps({k: rep[k] for k in ("rows", "products", "failures")}
                     | {"checks": {k: rep["checks"][k] for k in (
                         "docx_pages", "pdf_pages", "bucket_counts_rendered", "part_a_split",
                         "bucket_counts_match_part_a", "agencies_passing_rendered",
                         "agencies_passing_verify_by_rung", "agencies_passing_match",
                         "scored_rendered", "scored_match_four_specified",
                         "markdown_check_codes", "markdown_dashes", "markdown_mentions_508")}},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
