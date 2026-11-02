#!/usr/bin/env python3
"""The sixteen-check one-pager as a build product. **Zero spend, no network.**

`cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md` Part B, implementing
DN-018 (a view of the validity layer, DN-005 section 2.1). One landscape page in three forms —
Markdown (the source), Word, and a PDF rendered from the Markdown (the `render_report` pattern,
task d3de4348) — with a row per instrument check and a sixth column naming the FCSM 20-04
Accessibility concern that check serves (the `SERVES_FCSM_CONCERN` edges written by
`scripts/apply_fcsm_concerns.py`).

Every cell is a query over the framework record, never typed: the check name, what the diagnostic
looks at, what makes it pass and why it matters are the spec's `rf_*` fields (`diagnostic_package`
and `readiness_brief_build`), and the Quality concern is the spec's primary (and, where present,
`also`) `SERVES_FCSM_CONCERN` edge. A missing field exits non-zero. The font, colour, vocabulary,
dash and digit checks are reused by import from `readiness_brief_build` and `diagnostic_package`,
not copied.

Row order is the readiness brief's (`RB.check_rows`: by criterion, scored first within a group),
so the working group sees the same order as on 2026-10-16; the one-pager's `#` column numbers
those rows 1..16 and does not show the code.

    /opt/anaconda3/bin/python3 scripts/sixteen_checks_build.py
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
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import diagnostic_package as D  # noqa: E402
import diagnostic_package_build as B  # noqa: E402
import readiness_brief_build as RB  # noqa: E402

GENERATOR = "scripts/sixteen_checks_build.py"
TASK = "cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md"
OUT = REPO / "reports" / "diagnostic" / "one_pager"
STEM = "Readiness_Diagnostic_16_Checks"
PREFACE_SOURCE = REPO / "reports" / "diagnostic" / "preface_source.yaml"

TITLE = "Readiness diagnostic: the sixteen checks"
#: First rendered use of the word is the qualified phrase DN-018 section 2.1 mandates; the
#: Section 508 sense is never named (the build greps the Markdown to prove it).
SUBTITLE = ("Each check maps to a concern of accessibility in the FCSM data-quality sense "
            "(FCSM 20-04).")
#: The footnote text the task fixes verbatim (Part B item 3).
CONCERN_FOOTNOTE = ("The concern each check serves in the FCSM Framework for Data Quality "
                    "(FCSM 20-04), Accessibility dimension, after Webb 2026.")
#: The four concerns' short labels, from the task's Part B item 3. Keyed by the concern node's
#: id suffix (`fcsm_20_04_accessibility_c3` -> `c3`).
CONCERN_SHORT = {"c1": "find and obtain", "c2": "understand", "c3": "usable format",
                 "c4": "metadata"}

#: A dash used as a dash: normalised out of any text pulled from a source before it is rendered,
#: so the one-pager keeps the house rule (no em/en dash) even when its source carries one. The
#: record's `rf_*` text is never edited for this (out of scope); the normalisation happens only in
#: what is rendered. Any em/en dash (`readiness_brief_build._DASHES`), with or without the spaces
#: around it, becomes the house comma; a `--` written for a dash is caught too.
_DASH_AS_DASH = re.compile(r"\s+[–—]\s+")
_HOUSE_DASH = re.compile(r"\s*(?:--|[–—])\s*")


def house_dashes(text: str) -> str:
    """`text` with every em/en dash (or `--`) used as a dash replaced by the house comma."""
    return _HOUSE_DASH.sub(", ", text)

MAX_PAGES = 1
#: The fit ladder, tried in order as `(body_pt, where_mode, passes_mode)`. It follows the task's
#: prescription first — 10pt, then 9.5pt, then 9.5pt with "What we look at" cut to its first
#: clause — and only then makes the further changes the task allows ("before any other change"):
#: cutting "It passes when" to its first clause too, then stepping the font down. The winner is
#: the first setting whose Word and PDF are both one page; the build report and the RESULT name it.
FIT_LADDER = [
    (10.0, "full", "sentence"),
    (9.5, "full", "sentence"),
    (9.5, "first_clause", "sentence"),
    (9.5, "first_clause", "clause"),
    (9.0, "first_clause", "clause"),
    (8.5, "first_clause", "clause"),
    (8.0, "first_clause", "clause"),
    (7.5, "first_clause", "clause"),
    (7.0, "first_clause", "clause"),
    (6.5, "first_clause", "clause"),
]


# --------------------------------------------------------------------------------- the rows

def first_sentence(text: str) -> str:
    """The text up to and including the first sentence-ending period — one followed by a space
    and a capital, or the end. Dotted tokens like `data.json`, `robots.txt` and `M-25-05` are
    not boundaries, because the period is not followed by a space-then-capital."""
    m = re.search(r"\.\s+(?=[A-Z])", text)
    return text[:m.start() + 1] if m else text


def first_clause(text: str) -> str:
    """The first clause of `text`: up to the first comma or semicolon, or the whole sentence."""
    m = re.search(r"[,;]", text)
    return (text[:m.start()].rstrip() + ".") if m else text


def concern_of(g: dict) -> dict:
    """`{leg: {"primary": "cN", "also": "cN"|None}}` from the SERVES_FCSM_CONCERN edges."""
    out: dict = {}
    for e in g["edges"]:
        if e["type"] != "SERVES_FCSM_CONCERN":
            continue
        leg = e["from"].split("spec:", 1)[1]
        code = e["to"].split("accessibility_", 1)[1]
        out.setdefault(leg, {})[e["properties"]["role"]] = code
    return out


def concern_cell(entry: dict) -> str:
    """The Quality concern column value: the primary concern's short label, with the also-concern
    in parentheses where present. First letter capitalised."""
    primary = CONCERN_SHORT[entry["primary"]]
    cell = primary + (f" ({CONCERN_SHORT[entry['also']]})" if entry.get("also") else "")
    return cell[0].upper() + cell[1:]


def rows(g: dict | None = None, *, where_mode: str = "full", passes_mode: str = "sentence") -> list[dict]:
    """The sixteen rows in the brief's order, each with its six columns. Exits non-zero on a
    missing field; the Quality concern comes from the record's SERVES_FCSM_CONCERN edges.

    `where_mode` and `passes_mode` are the fit levers. "What we look at" is always cut to one
    sentence (`full`) and, when space is tight, to its first clause (`first_clause`) — the
    rule DN-018's task names. "It passes when" is one sentence (`sentence`) and, only when the
    page still overflows after the where-column cut, its first clause (`clause`) — an "other
    change" the task allows after the where rule, recorded in the build report and the RESULT."""
    g = g or D.load_framework()
    by_id = {n["id"]: n for n in g["nodes"]}
    concerns = concern_of(g)
    brief_rows = RB.check_rows(g)                       # brief order, scored-first within group
    missing, out = [], []
    for i, r in enumerate(brief_rows, start=1):
        leg = r["leg"]
        props = by_id[f"spec:{leg}"]["properties"]
        where = props.get("rf_where_we_look")
        passes = props.get("rf_pass")
        for f, v in (("rf_where_we_look", where), ("rf_pass", passes),
                     ("rf_name_brief", r["name"]), ("rf_why_short", r["why"])):
            if not str(v or "").strip():
                missing.append(f"spec:{leg}.{f}")
        if leg not in concerns or "primary" not in concerns.get(leg, {}):
            raise SystemExit(f"FATAL: spec:{leg} has no primary SERVES_FCSM_CONCERN edge; "
                             "run scripts/apply_fcsm_concerns.py and re-project")
        where_text = first_sentence(str(where or ""))
        if where_mode == "first_clause":
            where_text = first_clause(where_text)
        passes_text = first_sentence(str(passes or ""))
        if passes_mode == "clause":
            passes_text = first_clause(passes_text)
        # House dash rule, applied to the rendered cell only (the record is not edited): a cell
        # whose rf_* source uses an em/en dash as a dash still renders with the house comma.
        out.append({
            "n": i, "leg": leg, "scored": r["scored"],
            "check": house_dashes(str(r["name"])),
            "where": house_dashes(where_text),
            "passes": house_dashes(passes_text),
            "why": house_dashes(str(r["why"])),
            "concern": concern_cell(concerns[leg]),
            "concern_primary": concerns[leg]["primary"],
            "concern_also": concerns[leg].get("also"),
        })
    if missing:
        raise SystemExit("FATAL: the record lacks one-pager fields: " + ", ".join(missing))
    return out


def scored_legs(g: dict | None = None) -> list[str]:
    """The legs whose spec is `instrument_state == specified` — the Scored checks, read from the
    instrument and never typed. The build asserts there are exactly four."""
    g = g or D.load_framework()
    legs = [n["properties"]["leg"] for n in g["nodes"]
            if "MeasurementSpec" in n["labels"]
            and n["properties"].get("instrument_state") == "specified"]
    return sorted(legs)


def two_user_lines() -> list[str]:
    """The two kinds of user, below the table. Sourced from the diagnostic preface's
    `two_rungs_note` (the brief's source does not carry this text — a task premise corrected in
    the RESULT), split into the standard user (no key) and the API user (a key by open
    registration), with any em/en dash normalised to the house style."""
    note = yaml.safe_load(PREFACE_SOURCE.read_text(encoding="utf-8"))["two_rungs_note"]
    note = _DASH_AS_DASH.sub(", ", " ".join(note.split()))
    rung1 = next((s.strip() for s in re.split(r"(?<=\.) ", note) if s.strip().startswith("Rung one")), "")
    rung2 = next((s.strip() for s in re.split(r"(?<=\.) ", note) if s.strip().startswith("Rung two is")), "")
    standard = "Standard user: " + rung1.replace("Rung one is ", "", 1)
    api = "API user: " + rung2.replace("Rung two is ", "", 1)
    return [standard, api]


# --------------------------------------------------------------------------------- markdown

def _cell(t) -> str:
    return str(t).replace("|", "/").replace("\n", " ")


def build_markdown(data: list[dict], users: list[str]) -> str:
    scored_n = {1: "one", 2: "two", 3: "three", 4: "four"}[sum(1 for r in data if r["scored"])]
    intro1 = (f"A check is marked Scored when its pass line rests on a published source; "
              f"{scored_n} of the sixteen are Scored, read from the instrument's own state and "
              f"the scoring model rather than typed in.")
    intro2 = ("A check that is not measured always names a reason, and never counts as a fail.")
    # The delimiter row's dash counts set the PDF table's relative column widths (pandoc reads
    # them as proportions and emits them to typst): a thin `#` and Quality-concern column, wide
    # prose columns, so "Why it matters" and "It passes when" wrap over fewer lines and the
    # landscape page holds all sixteen rows. The proportions track the Word column widths.
    delim = "|" + "|".join("-" * n for n in (2, 15, 21, 25, 24, 11)) + "|"
    L = [f"# {TITLE}", "", f"*{SUBTITLE}*", "",
         f"Generated by `{GENERATOR}` from the framework record.", "",
         intro1, "", intro2, "",
         "| # | Check | What we look at | It passes when | Why it matters | Quality concern^a |",
         delim]
    for r in data:
        check = _cell(r["check"]) + (" (Scored)" if r["scored"] else "")
        L.append(f"| {r['n']} | {check} | {_cell(r['where'])} | {_cell(r['passes'])} | "
                 f"{_cell(r['why'])} | {_cell(r['concern'])} |")
    L += ["", f"^a {CONCERN_FOOTNOTE}", ""]
    L += [users[0], "", users[1], ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------------- docx

def build_docx(data: list[dict], users: list[str], path: Path, body_pt: float) -> None:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor as DRGB

    # docx needs its own RGBColor; `B.BLACK` etc. are python-pptx colours. Same hex values as
    # `diagnostic_package_build` (and so the same `B.ALLOWED_RGB` string set the audit checks).
    BLACK, GREY, ORANGE = DRGB(0x00, 0x00, 0x00), DRGB(0x55, 0x55, 0x55), DRGB(0xC2, 0x56, 0x00)
    doc = Document()
    doc.styles["Normal"].font.name = B.FONT
    doc.styles["Normal"].font.size = Pt(body_pt)
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Inches(11), Inches(8.5)
    sec.top_margin = sec.bottom_margin = Inches(0.3)
    sec.left_margin = sec.right_margin = Inches(0.3)

    def run(p, text, *, bold=False, size=body_pt, color=BLACK, italic=False):
        r = p.add_run(text)
        r.font.name = B.FONT
        r.font.bold = bold
        r.font.italic = italic
        r.font.size = Pt(size)
        r.font.color.rgb = color
        return r

    def para(text="", *, bold=False, size=body_pt, color=BLACK, after=3, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(0)
        if text:
            run(p, text, bold=bold, size=size, color=color, italic=italic)
        return p

    scored_n = {1: "one", 2: "two", 3: "three", 4: "four"}[sum(1 for r in data if r["scored"])]
    para(TITLE, bold=True, size=14, after=1)
    para(SUBTITLE, size=body_pt, color=GREY, after=4, italic=True)
    para(f"A check is marked Scored when its pass line rests on a published source; {scored_n} of "
         "the sixteen are Scored, read from the instrument's own state and the scoring model "
         "rather than typed in.", size=body_pt, after=2)
    para("A check that is not measured always names a reason, and never counts as a fail.",
         size=body_pt, after=4)

    headers = ["#", "Check", "What we look at", "It passes when", "Why it matters",
               "Quality concern"]
    widths = [0.28, 1.55, 2.15, 2.75, 2.55, 1.12]
    cell_pt = body_pt - 1.0
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    # tight cell margins so sixteen rows fit one landscape page (the brief's dense-table rule,
    # readiness_brief_build: zero top/bottom, so a row is only as tall as its wrapped text)
    mar = OxmlElement("w:tblCellMar")
    for side, w in (("top", "0"), ("bottom", "0"), ("left", "40"), ("right", "40")):
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
        run(p, h + ("ᵃ" if h == "Quality concern" else ""), bold=True, size=cell_pt)

    def put(cell, width, segments):
        cell.width = Inches(width)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        for j, (text, bold, color) in enumerate(segments):
            if j:
                run(p, text, bold=bold, size=cell_pt, color=color)
            else:
                run(p, text, bold=bold, size=cell_pt, color=color)

    for r in data:
        cells = t.add_row().cells
        put(cells[0], widths[0], [(str(r["n"]), False, BLACK)])
        check_segs = [(r["check"], False, BLACK)]
        if r["scored"]:
            check_segs.append((" (Scored)", True, ORANGE))
        put(cells[1], widths[1], check_segs)
        put(cells[2], widths[2], [(r["where"], False, BLACK)])
        put(cells[3], widths[3], [(r["passes"], False, BLACK)])
        put(cells[4], widths[4], [(r["why"], False, BLACK)])
        put(cells[5], widths[5], [(r["concern"], False, BLACK)])

    para("ᵃ " + CONCERN_FOOTNOTE, size=cell_pt, color=GREY, after=3)
    para(users[0], size=body_pt, after=1)
    para(users[1], size=body_pt, after=0)
    doc.save(str(path))


# -------------------------------------------------------------------------------------- pdf

def render_pdf(md_path: Path, pdf_path: Path, body_pt: float, title: str) -> None:
    """Render the committed Markdown to one landscape PDF page. The PDF is rendered from the
    Markdown on disk unchanged (`render_report`).

    Two things the `header-includes` string alone cannot do, root-caused 2026-11-02:

    * **Text size.** pandoc's typst template sets `#set text(size: fontsize)` inside the document
      wrapper, which overrides any `#set text(size: ...)` placed in `header-includes` or as a body
      raw block. The only lever the template honours is the `fontsize` variable itself, so the
      PDF's size is passed that way (`body_pt - 1.5`, the table reads a point below the body).
    * **One flowing page.** pandoc wraps a pipe table in `#figure(...)`, an unbreakable block that
      bumps whole to the next page the moment it does not fit under the preamble — which is why
      the page it fit on had the title alone above it and the footnote alone below. `#show figure:
      set block(breakable: true)` lets the table share a page with the prose, so a document that
      is under one page tall renders as one page. Landscape (`flipped: true`) does survive
      `header-includes`, the template setting no page orientation of its own."""
    size = body_pt - 1.5
    # The preamble (a level-1 heading, the subtitle, the provenance line and two intro sentences)
    # must cost as little vertical space as possible so the sixteen rows share the page with it:
    # the heading is pulled down near the body size and its surrounding block space is cut, and
    # paragraph leading and inter-paragraph spacing are tightened.
    header = ("#set page(flipped: true, margin: (x: 0.9cm, y: 0.55cm))\n"
              "#show figure: set block(breakable: true)\n"
              f"#show heading: set text(size: {size + 2.5}pt)\n"
              "#show heading: set block(above: 0.5em, below: 0.4em)\n"
              # typst's default table inset is ~5pt per side, which is most of a small row's
              # height: cut it the way the Word build zeroes its cell margins, so the rows are
              # only as tall as their wrapped text.
              "#set table(inset: (x: 3pt, y: 1.2pt), stroke: 0.4pt)\n"
              "#set text(hyphenate: false)\n"
              "#set par(justify: false, leading: 0.5em, spacing: 0.6em)")
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


# ------------------------------------------------------------------------------------ checks

def digit_audit(data: list[dict]) -> list[str]:
    """No bare number in the four prose columns outside a citation. The `#` column (1..16) is
    structural and is not scanned; the footnote's and subtitle's citation numbers (FCSM 20-04,
    Webb 2026) are not prose columns. `rf_where_we_look`/`rf_pass` spell their numbers out."""
    bad = []
    for r in data:
        for k in ("check", "where", "passes", "why"):
            for m in B._BARE.finditer(RB._CITATION.sub(" ", str(r[k]))):
                bad.append(f"row {r['n']} ({r['leg']}) {k}: bare number {m.group(0)!r}")
    return bad


def concern_column_matches_record(data: list[dict], g: dict) -> list[str]:
    """Each row's Quality concern primary, read back, equals the spec's primary edge in the
    record (which equals the projection while the roundtrip gate is green)."""
    want = concern_of(g)
    bad = []
    for r in data:
        rec = want[r["leg"]]["primary"]
        if r["concern_primary"] != rec:
            bad.append(f"row {r['n']} ({r['leg']}): rendered {r['concern_primary']} != record {rec}")
    return bad


# -------------------------------------------------------------------------------------- build

def build(out: Path = OUT, *, measure: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    specified = scored_legs(g)
    if len(specified) != 4:
        raise SystemExit(f"FATAL: {len(specified)} specs are instrument_state=specified, expected 4: {specified}")

    md_path = out / f"{STEM}.md"
    docx_path = out / f"{STEM}.docx"
    pdf_path = out / f"{STEM}.pdf"
    users = two_user_lines()

    attempts, chosen = [], None
    ladder = FIT_LADDER if measure else [(9.0, "first_clause", "clause")]
    for body_pt, where_mode, passes_mode in ladder:
        data = rows(g, where_mode=where_mode, passes_mode=passes_mode)
        md = build_markdown(data, users)
        md_path.write_text(md, encoding="utf-8")
        build_docx(data, users, docx_path, body_pt)
        render_pdf(md_path, pdf_path, body_pt, TITLE)
        if not measure:
            chosen = {"body_pt": body_pt, "where_mode": where_mode, "passes_mode": passes_mode,
                      "data": data, "md": md}
            break
        dpages = RB.docx_pages(docx_path)
        ppages = pdf_pages(pdf_path)
        attempts.append({"body_pt": body_pt, "where_mode": where_mode, "passes_mode": passes_mode,
                         "docx_pages": dpages, "pdf_pages": ppages})
        if dpages <= MAX_PAGES and ppages <= MAX_PAGES:
            chosen = {"body_pt": body_pt, "where_mode": where_mode, "passes_mode": passes_mode,
                      "data": data, "md": md}
            break
    if chosen is None:
        raise SystemExit("FATAL: the one-pager does not fit one landscape page on any ladder "
                         "setting:\n" + json.dumps(attempts, indent=1))

    data, md = chosen["data"], chosen["md"]
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    docx_pages = RB.docx_pages(docx_path) if measure else None
    pdf_pg = pdf_pages(pdf_path) if measure else None

    texts = {"markdown": md, "docx": RB.docx_text(docx_path)}
    checks = {
        "fit_ladder": attempts, "chosen": {"body_pt": chosen["body_pt"], "where_mode": chosen["where_mode"],
                                           "passes_mode": chosen["passes_mode"]},
        "docx_pages": docx_pages, "pdf_pages": pdf_pg,
        "scored_legs": specified,
        "digit_audit": digit_audit(data),
        "font_colour_audit": {"docx": RB.docx_font_colour_audit(docx_path)},
        "vocabulary": {k: D.banned_hits_prose(v) for k, v in texts.items()},
        "dashes": {k: RB.dash_hits(v) for k, v in texts.items()},
        "concern_column_vs_record": concern_column_matches_record(data, g),
        "mentions_508": sorted({k for k, v in texts.items() if "508" in v}),
    }
    failures = []
    if measure:
        if docx_pages != MAX_PAGES:
            failures.append(f"docx has {docx_pages} pages")
        if pdf_pg != MAX_PAGES:
            failures.append(f"pdf has {pdf_pg} pages")
    for k in ("digit_audit", "concern_column_vs_record", "mentions_508"):
        if checks[k]:
            failures.append(k)
    for k in ("font_colour_audit", "vocabulary", "dashes"):
        if any(checks[k].values()):
            failures.append(k)

    report = {
        "generated_by": GENERATOR, "task": TASK,
        "row_order": [r["leg"] for r in data],
        "concerns": {r["leg"]: {"primary": r["concern_primary"], "also": r["concern_also"]}
                     for r in data},
        "products": [
            {"name": md_path.name, "md_sha256": md_sha},
            {"name": docx_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(), "pages": docx_pages},
            {"name": pdf_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(), "pages": pdf_pg},
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
    print(json.dumps({k: rep[k] for k in ("row_order", "concerns", "products", "failures")}
                     | {"chosen": rep["checks"]["chosen"], "fit_ladder": rep["checks"]["fit_ladder"],
                        "scored_legs": rep["checks"]["scored_legs"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
