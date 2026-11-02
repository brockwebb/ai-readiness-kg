#!/usr/bin/env python3
"""The ICSP roll-up of the sixteen checks as a build product. **Zero spend, no network.**

`cc_tasks/2026-11-02_icsp_rollup_of_the_sixteen_checks.md` Part B, implementing DN-005 section
2.1 (the validity layer) one level above the sixteen-check one-pager: the buckets, why each
matters, and the line from each bucket back to the AI-ready data framework an ICSP member already
knows (USAFacts 2026, which the operator operationalized and extended). One portrait page in three
forms, Markdown (the source), Word, and a PDF rendered from the Markdown (the `render_report`
pattern), patterned on `scripts/sixteen_checks_build.py` (the sixteen checks are imported from it,
not copied).

Every cell is a query over the framework record or a verbatim quotation with its source; the
builder types no prose of its own beyond the column headers, the fixed two-sentence intro and the
fixed two-line footer the task names:

* the **Criterion** and **What the framework asks for** columns are the `AiReadyCriterion` /
  `ExtensionGroup` node's `name` and `text`, written by `scripts/add_aiready_lineage.py` (Part A);
* the **Checks** column is the count and the plain names (`rf_name_brief`) of the checks that
  DESCEND_FROM that node, Scored ones (`instrument_state == specified`) marked;
* the **Quality concern** column is the distinct FCSM 20-04 concern short labels those checks
  serve (`sixteen_checks_build.CONCERN_SHORT` over the `SERVES_FCSM_CONCERN` edges), so the
  bucket's "why it matters" is FCSM's language, not the project's;
* the **Agencies passing** column is, from the cycle of record the brief's grid uses, the count of
  the sixteen agencies with no fail in the bucket, under the four-state rule (`instrument.four_state`).

Numbers are spelled as words so the page stays free of bare digits (the digit audit); the only
digits on it are in the fixed title/intro/footer citations.

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
TASK = "cc_tasks/2026-11-02_icsp_rollup_of_the_sixteen_checks.md"
OUT = REPO / "reports" / "diagnostic" / "rollup"
STEM = "Readiness_Diagnostic_Rollup"

TITLE = "Readiness diagnostic: what it measures, at a glance"
#: The two-sentence intro the task fixes verbatim (Part B item 2).
INTRO = [
    "The readiness diagnostic checks whether a program acting for a member of the public can get "
    "an agency's data and the documentation that goes with it.",
    "Its checks descend from the four criteria of the USAFacts guide to AI-ready data; the "
    "diagnostic measures the criteria that can be measured from outside and adds one check from "
    "release practice.",
]
#: The two-line footer the task fixes verbatim (Part B item 4). Line one names the lineage and the
#: concern source; line two names the two kinds of user. `*AI-ready data*` is rendered italic.
FOOTER = [
    "Checks descend from USAFacts (2026), *AI-ready data*; concerns from FCSM 20-04, "
    "Accessibility dimension, after Webb 2026.",
    "Standard user: no key. API user: a free key by open registration, a person completes an "
    "email step.",
]
#: The passing-column footnote (Part B item 3): a check not measured is excluded, never a fail.
PASSING_FOOTNOTE = ("An agency passes a bucket when none of the bucket's checks that could be "
                    "measured for it comes back fail; a check not measured for an agency, or not "
                    "measured on the cycle of record at all, is left out of that agency's count "
                    "and is never read as a fail.")
#: Accurate carries no runnable check; its indicators are evaluation-harness checks (EVAL). The
#: cell reads this (Part B item 3), guarded by the record's EVAL typing, not typed on a whim.
EVAL_NOTE = "no check yet; needs an evaluation harness"

#: Numbers nought to sixteen as words, so the page carries no bare digit (digit audit). `0` is
#: "no" in the check-count phrase ("No checks") and "zero" in the passing phrase ("zero of sixteen").
_WORD = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
         14: "fourteen", 15: "fifteen", 16: "sixteen"}

#: USAFacts' four criteria in the guide's order, then the extension groups that carry a check.
CRITERION_ORDER = ["A", "B", "C", "D"]


def word(n: int) -> str:
    if n not in _WORD:
        raise SystemExit(f"FATAL: {n} is outside the spelled-number range nought to sixteen")
    return _WORD[n]


# --------------------------------------------------------------------------------- the data

def lineage_nodes(g: dict) -> dict:
    """`{letter: node}` for the four `AiReadyCriterion` and three `ExtensionGroup` nodes."""
    out = {}
    for n in g["nodes"]:
        if set(n["labels"]) & {"AiReadyCriterion", "ExtensionGroup"}:
            out[n["properties"]["letter"]] = n
    return out


def descends(g: dict) -> dict:
    """`{lineage_node_id: [leg, ...]}` from the DESCENDS_FROM edges, in brief order within a
    bucket (scored first within a criterion, `RB.check_rows`)."""
    by_id = {n["id"]: n for n in g["nodes"]}
    order = {r["leg"]: i for i, r in enumerate(RB.check_rows(g))}
    out: dict = {}
    for e in g["edges"]:
        if e["type"] != "DESCENDS_FROM":
            continue
        leg = by_id[e["from"]]["properties"]["leg"]
        out.setdefault(e["to"], []).append(leg)
    for nid in out:
        out[nid].sort(key=lambda l: order.get(l, 999))
    return out


def criterion_eval_typed(g: dict, letter: str) -> bool:
    """True when the criterion's indicators are evaluation-harness (EVAL) typed — the record
    fact behind Accurate's `no check yet; needs an evaluation harness` cell."""
    return any("EVAL" in str(n["properties"].get("type") or "")
               for n in g["nodes"] if "AssessmentIndicator" in n["labels"]
               and n["properties"].get("criterion_code") == letter)


def bucket_pass_from_edges(legs: list[str], grid: dict) -> int | None:
    """Agencies (of sixteen) with no fail across this bucket's measured checks, under the
    four-state rule. `None` when the bucket has no check present on the cycle of record. A check
    not measured for an agency (could_not_measure, or absent from the grid) is excluded for that
    agency; an agency with no measured bucket check does not count as passing."""
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


def verify_pass_by_letter(g: dict, grid: dict) -> dict:
    """The passing counts recomputed by a SECOND, independent code path: group the grid's legs by
    the check's code letter (the naming convention) rather than by the record's DESCENDS_FROM
    edges, build the full per-agency state matrix first, then count. Agreement with the rendered
    numbers (which come from the edges) cross-checks the edges against the convention."""
    letter_of_bucket = {"A": "A", "B": "B", "C": "C", "D": "D", "F": "F"}
    cols = [c["code"] for c in grid["columns"]]
    matrix = {r["agency"]: {leg: I.four_state([p["verdict"] for p in r["cells"][leg]["pages"]])
                            for leg in cols} for r in grid["rows"]}
    out: dict = {}
    for letter in letter_of_bucket:
        present = [leg for leg in cols if leg[0] == letter]
        if not present:
            out[letter] = None
            continue
        cnt = 0
        for states in matrix.values():
            vals = [states[leg] for leg in present]
            meas = [v for v in vals if v in ("pass", "fail", "partial")]
            if meas and "fail" not in meas:
                cnt += 1
        out[letter] = cnt
    return out


def bucket_rows(g: dict, grid: dict) -> list[dict]:
    """One row per criterion in USAFacts' order, then one per extension group that carries a
    check. Each cell is a query over the record and the cycle of record."""
    nodes = lineage_nodes(g)
    desc = descends(g)
    check = {r["leg"]: r for r in RB.check_rows(g)}
    concerns = S.concern_of(g)
    scored = set(S.scored_legs(g))

    extension_letters = [n["properties"]["letter"] for n in g["nodes"]
                         if "ExtensionGroup" in n["labels"]
                         and desc.get(n["id"])]          # only groups that carry a check
    row_letters = CRITERION_ORDER + sorted(extension_letters)

    rows = []
    for letter in row_letters:
        node = nodes.get(letter)
        if node is None:
            raise SystemExit(f"FATAL: no lineage node for letter {letter!r}; run add_aiready_lineage.py")
        is_ext = "ExtensionGroup" in node["labels"]
        legs = desc.get(node["id"], [])
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
        if n_pass is None:
            if not criterion_eval_typed(g, letter):
                raise SystemExit(f"FATAL: bucket {letter} has no measured check and is not EVAL-typed; "
                                 "the no-check note is not grounded")
            passing = EVAL_NOTE
        else:
            passing = f"{word(n_pass)} of sixteen"
        rows.append({
            "letter": letter, "is_extension": is_ext,
            "criterion": S.house_dashes(str(node["properties"]["name"])) + (" (added)" if is_ext else ""),
            "asks": S.house_dashes(str(node["properties"]["text"])),
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
         "| Criterion | What the framework asks for | Checks | Quality concern | "
         "Agencies passing every check in this bucket^a |",
         "|" + "|".join("-" * n for n in (12, 26, 34, 16, 20)) + "|"]
    for r in rows:
        L.append(f"| {_cell(r['criterion'])} | {_cell(r['asks'])} | {_cell(checks_text(r))} | "
                 f"{_cell(r['concern'])} | {_cell(r['passing'])} |")
    L += ["", f"^a {PASSING_FOOTNOTE}", "", FOOTER[0], "", FOOTER[1], ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------------- docx

def build_docx(rows: list[dict], path: Path, body_pt: float = 11.0) -> None:
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

    def footer_para(segments, *, size=body_pt, after=2):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(0)
        for text, italic in segments:
            run(p, text, size=size, italic=italic, color=GREY)
        return p

    para(TITLE, bold=True, size=15, after=4)
    para(INTRO[0], size=body_pt, after=3)
    para(INTRO[1], size=body_pt, after=6)

    headers = ["Criterion", "What the framework asks for", "Checks", "Quality concern",
               "Agencies passing every check in this bucket"]
    widths = [1.0, 1.85, 2.6, 0.95, 1.1]
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
        put_plain(cells[0], widths[0], r["criterion"])
        put_plain(cells[1], widths[1], r["asks"])
        # Checks cell: count word, then each name on its own line, Scored marked in orange.
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
    # Footer line one carries an italic run for *AI-ready data*.
    pre, _, post = FOOTER[0].partition("*AI-ready data*")
    footer_para([(pre, False), ("AI-ready data", True), (post, False)], after=1)
    footer_para([(FOOTER[1], False)], after=0)
    doc.save(str(path))


# -------------------------------------------------------------------------------------- pdf

def render_pdf(md_path: Path, pdf_path: Path, body_pt: float, title: str) -> None:
    """Render the committed Markdown to a portrait PDF (the `render_report` pattern: the PDF is
    the Markdown on disk, unchanged). The table is a breakable figure so it shares the page with
    the prose; the size is passed through pandoc's `fontsize` variable (the only lever its typst
    template honours), root-caused in `sixteen_checks_build.render_pdf`."""
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
    """No bare number in any record-derived cell. The title, intro and footer are fixed task
    constants that carry citation years, and are not scanned; every cell below is a query over the
    record or the cycle of record, and its numbers are spelled."""
    bad = []
    for r in rows:
        cells = {"criterion": r["criterion"], "asks": r["asks"], "checks": checks_text(r),
                 "concern": r["concern"], "passing": r["passing"]}
        for k, v in cells.items():
            for m in B._BARE.finditer(str(v)):
                bad.append(f"{r['letter']} {k}: bare number {m.group(0)!r}")
    return bad


def bucket_counts(rows: list[dict]) -> dict:
    """`{name: check_count}` for the rendered buckets, to compare against Part A's Cypher split."""
    return {r["criterion"].replace(" (added)", ""): r["check_count"] for r in rows}


# -------------------------------------------------------------------------------------- build

def build(out: Path = OUT, *, measure: bool = True, body_pt: float = 11.0) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    grid = I.load_grid(I.load_config())
    rows = bucket_rows(g, grid)

    md_path, docx_path, pdf_path = out / f"{STEM}.md", out / f"{STEM}.docx", out / f"{STEM}.pdf"
    md = build_markdown(rows)
    md_path.write_text(md, encoding="utf-8")
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    build_docx(rows, docx_path, body_pt)
    render_pdf(md_path, pdf_path, body_pt, TITLE)

    docx_pages = RB.docx_pages(docx_path) if measure else None
    ppages = pdf_pages(pdf_path) if measure else None

    # ---- the six Part B checks ----
    # Part A split, recomputed from the record's DESCENDS_FROM edges, keyed by bucket name.
    by_id = {n["id"]: n for n in g["nodes"]}
    part_a_split: dict = {}
    for e in g["edges"]:
        if e["type"] == "DESCENDS_FROM":
            name = by_id[e["to"]]["properties"]["name"]
            part_a_split[name] = part_a_split.get(name, 0) + 1
    rendered_counts = bucket_counts(rows)
    # Accurate renders with zero checks but has no DESCENDS_FROM edge, so it is absent from the
    # edge split; compare on the buckets that carry at least one check.
    counts_match = all(part_a_split.get(name) == rendered_counts.get(name)
                       for name in part_a_split)

    verify = verify_pass_by_letter(g, grid)
    rendered_pass = {r["letter"]: r["passing_n"] for r in rows}
    pass_match = all(verify.get(letter) == rendered_pass.get(letter)
                     for letter in rendered_pass)

    scored_rendered = sorted(c["leg"] for r in rows for c in r["checks"] if c["scored"])
    scored_record = sorted(S.scored_legs(g))

    md_text = md
    docx_text = RB.docx_text(docx_path)
    pdf_txt = pdf_text(pdf_path) if measure else ""
    texts = {"markdown": md_text, "docx": docx_text, "pdf": pdf_txt}

    md_check_codes = sorted(set(_CHECK_CODE.findall(md_text)))
    md_dashes = RB.dash_hits(md_text)
    md_508 = "508" in md_text

    checks = {
        "docx_pages": docx_pages, "pdf_pages": ppages,
        "digit_audit": digit_audit(rows),
        "font_colour_audit": {"docx": RB.docx_font_colour_audit(docx_path)},
        "vocabulary": {k: D.banned_hits_prose(v) for k, v in texts.items()},
        "dashes": {k: RB.dash_hits(v) for k, v in texts.items()},
        "markdown_check_codes": md_check_codes,
        "markdown_dashes": md_dashes,
        "markdown_mentions_508": md_508,
        "bucket_counts_rendered": rendered_counts,
        "part_a_split": part_a_split,
        "bucket_counts_match_part_a": counts_match,
        "agencies_passing_rendered": rendered_pass,
        "agencies_passing_verify_by_letter": verify,
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
        "rows": [{"letter": r["letter"], "criterion": r["criterion"], "check_count": r["check_count"],
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
                         "agencies_passing_verify_by_letter", "agencies_passing_match",
                         "scored_rendered", "scored_match_four_specified",
                         "markdown_check_codes", "markdown_dashes", "markdown_mentions_508")}},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
