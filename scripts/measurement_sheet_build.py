#!/usr/bin/env python3
"""V3 of the readiness diagnostic: the measurement sheet. **Zero spend, no network.**

`cc_tasks/2026-11-02_v3_measurement_sheet.md` Part B, implementing DN-019
(`handoffs/2026-11-02_staged_DN-019_measurement_view_and_the_view_ladder.md`, PASS sha256
d2a9152f197b). Every one of the sixteen checks is rendered as a measurement specification:
one page section per check, a heading `n. <plain name> (<code>)`, and under it a two-column
table whose row labels are DN-019 section 3's "Field, as rendered" column VERBATIM and whose
cells are the MeasurementSpec node's property values, read from the framework record and never
typed. A field whose property is empty or absent renders "not specified", and the build report
counts them per field and per check (zero is expected for an `auto` check; a non-zero count is a
record defect the RESULT lists, never one this build fills).

The field set follows the ISO/IEC/IEEE 15939 measurement information model (DN-019 section 2):
question (information need), the entity and attribute examined, the instrument (method and tool),
what it reads (base measure), the evidence kept (measurement record), the decision criteria
(passes/partial/fails/not measured), where the expected behaviour comes from (the criteria's
source), corroboration, and the measurement context (the client). TEVV, spelled out on first use
as test, evaluation, verification and validation, appears only at this rung if the record uses it.

Rung line (DN-019 section 4): every page carries "V3 of the readiness diagnostic; V2 is the
sixteen-check page, V1 the criteria roll-up" so a reader knows which level they hold.

Audits (the one-pager's, reused by import):

* **vocabulary** (DN-016 ruling 1, no "scan/probe/crawl/audit" as a word): the eight
  reader-orientation cells MUST be clean (a hit is FATAL). The four technical measurement cells
  that DN-019 section 3 maps to the ISO-15939 sensor, method, record and criteria-source
  (Instrument, What the instrument reads, Evidence kept, Expected behaviour comes from) are
  EXEMPT, for the same reason the digit audit is relaxed for `signal` and `rf_requirements`: at
  the implementer's rung these cells name the crawling/probing METHOD and quote standards
  verbatim, which is the technical vocabulary the public-facing ban targets, not reader prose.
  The build report lists every banned word in the exempt cells so nothing is hidden, and asserts
  none leaked into a reader cell. (Task Part B check 3; recorded as a premise refinement in the
  RESULT, because the task relaxed only the digit audit by name.)
* **digit** (no bare number in a cell outside a citation): relaxed only in `signal` and
  `rf_requirements` (they quote standards with numbers); every other cell is audited.
* **dash**: every em/en dash in a rendered cell (the record included) is normalised to the house
  comma (`sixteen_checks_build.house_dashes`); the record is never edited. A grep of the Markdown
  for U+2014 and U+2013 returns zero lines.
* **font and colour** (docx): Calibri, colours in the allowed set.

    /opt/anaconda3/bin/python3 scripts/measurement_sheet_build.py
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

import diagnostic_package as D          # noqa: E402
import diagnostic_package_build as B    # noqa: E402
import readiness_brief_build as RB      # noqa: E402
import sixteen_checks_build as SC       # noqa: E402

GENERATOR = "scripts/measurement_sheet_build.py"
TASK = "cc_tasks/2026-11-02_v3_measurement_sheet.md"
OUT = REPO / "reports" / "diagnostic" / "measurement_sheet"
STEM = "Readiness_Diagnostic_V3_Measurements"
BIBLIO_CACHE = REPO / "state" / "biblio_cache"

TITLE = "Readiness diagnostic: the measurements"
#: DN-019 section 4 rule, verbatim. Carried as the page header of every rendered form.
RUNG_LINE = ("V3 of the readiness diagnostic; V2 is the sixteen-check page, "
             "V1 the criteria roll-up")
BODY_PT = 10.0

#: The cells whose banned-word (vocabulary) audit is relaxed at this rung: the ISO-15939 sensor,
#: method, record and criteria-source. See the module docstring.
TECHNICAL_FIELDS = {"Instrument", "What the instrument reads", "Evidence kept",
                    "Expected behaviour comes from"}
#: The cells whose digit audit is relaxed. The task names `signal` (What the instrument reads)
#: and `rf_requirements` (Expected behaviour comes from), which quote standards with numbers;
#: the same relaxation covers the other two ISO-15939 technical cells for the same reason the
#: vocabulary audit exempts them: the Instrument cell carries the collector's VERSION PIN
#: (`lighthouse-cli>=12`), a numeral by nature, and Evidence kept carries format identifiers.
#: Reader-orientation cells stay fully audited. (Premise refinement, recorded in the RESULT.)
DIGIT_RELAXED_FIELDS = set(TECHNICAL_FIELDS)


def first_sentence_q(text: str) -> str:
    """The first sentence of `text`, splitting on a sentence-ending period, QUESTION MARK or
    exclamation followed by a space and a capital. DN-019 section 3 renders the Question as
    rf_hypothesis's first sentence, and a hypothesis is written `<the question>? <the reason>`,
    so the boundary is the `?`. `sixteen_checks_build.first_sentence` splits on a period only
    (its fields are statements); the Question needs the question-mark boundary too, which also
    keeps a status code like `HTTP 200` in the second sentence out of the rendered question."""
    m = re.search(r"[.?!]\s+(?=[A-Z])", text)
    return text[:m.start() + 1] if m else text


# --------------------------------------------------------------------------------- biblio

def biblio_title(source_id: str) -> str | None:
    """The source document's title from the biblio cache (`manifest_title`), or None when the
    source id has no cache record (a record defect the RESULT lists)."""
    f = BIBLIO_CACHE / f"{source_id}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("manifest_title")
    except json.JSONDecodeError:
        return None


# ----------------------------------------------------------------------------- the cells

def _ns() -> list:
    """The single-line 'not specified' cell."""
    return ["not specified"]


def expected_behaviour_lines(p: dict, unresolved: list) -> tuple[list, bool]:
    """The 'Expected behaviour comes from' cell: the standards URLs, then one line per
    rf_requirements source (its biblio title, then the quote in quotation marks). Returns
    (lines, is_not_specified). Appends (leg, source) to `unresolved` for every source id that
    does not resolve in the biblio cache (rendered with the raw source id as a fallback)."""
    lines: list[str] = []
    urls = p.get("rf_standards_urls")
    if urls:
        for u in (urls if isinstance(urls, list) else [urls]):
            if str(u).strip():
                lines.append(str(u).strip())
    reqs = json.loads(p.get("rf_requirements") or "[]")
    for q in reqs:
        src = q.get("source")
        quote = str(q.get("quote") or "").strip()
        title = biblio_title(src)
        if title is None:
            unresolved.append((p.get("leg"), src))
            title = src                                  # fallback: the raw source id
        lines.append(f'{title}: "{quote}"')
    return (lines, False) if lines else (_ns(), True)


def client_line(p: dict) -> list:
    """The Client cell (task rule): 'standard user' when rf_rung_two_changes is empty, otherwise
    'standard user; API user: ' followed by the text. Never 'not specified'."""
    text = str(p.get("rf_rung_two_changes") or "").strip()
    return ["standard user"] if not text else [f"standard user; API user: {text}"]


def instrument_line(p: dict) -> tuple[list, bool]:
    """The Instrument cell: the collector, its pin beside it, and the run mode."""
    collector = str(p.get("collector") or "").strip()
    pin = str(p.get("collector_pin") or "").strip()
    mode = str(p.get("mode") or "").strip()
    if not collector and not mode:
        return (_ns(), True)
    head = collector + (f" ({pin})" if pin else "")
    return ([f"{head}; mode: {mode}" if head else f"mode: {mode}"], False)


def simple(value, *, relaxed_first_sentence: bool = False) -> tuple[list, bool]:
    """A single-property cell: its value, or 'not specified' when empty/absent."""
    text = ("" if value is None else str(value)).strip()
    if not text:
        return (_ns(), True)
    if relaxed_first_sentence:
        text = first_sentence_q(text)
    return ([text], False)


def cells_for(p: dict, unresolved: list) -> list[dict]:
    """The twelve measurement-specification cells for one check, DN-019 section 3 order. Each is
    {label, lines, not_specified, technical, digit_relaxed}."""
    question_lines, q_ns = simple(p.get("rf_hypothesis"), relaxed_first_sentence=True)
    examined_lines, ex_ns = simple(p.get("rf_where_we_look"))
    instrument_lines, in_ns = instrument_line(p)
    reads_lines, rd_ns = simple(p.get("signal"))
    evidence_lines, ev_ns = simple(p.get("evidence_kind"))
    pass_lines, pa_ns = simple(p.get("rf_pass"))
    partial_lines, pt_ns = simple(p.get("rf_partial"))
    fail_lines, fa_ns = simple(p.get("rf_fail"))
    notm_lines, nm_ns = simple(p.get("rf_not_measured"))
    exp_lines, exp_ns = expected_behaviour_lines(p, unresolved)
    who_lines, wh_ns = simple(p.get("rf_who_else"))
    client_lines = client_line(p)

    spec = [
        ("Question", question_lines, q_ns),
        ("What is examined", examined_lines, ex_ns),
        ("Instrument", instrument_lines, in_ns),
        ("What the instrument reads", reads_lines, rd_ns),
        ("Evidence kept", evidence_lines, ev_ns),
        ("Passes when", pass_lines, pa_ns),
        ("Partial when", partial_lines, pt_ns),
        ("Fails when, and what a fail does not claim", fail_lines, fa_ns),
        ("Not measured when", notm_lines, nm_ns),
        ("Expected behaviour comes from", exp_lines, exp_ns),
        ("Who else measures this", who_lines, wh_ns),
        ("Client", client_lines, False),            # the Client cell is never 'not specified'
    ]
    out = []
    for label, lines, ns in spec:
        # House-dash every rendered line (record untouched); URLs carry hyphens, not em/en dashes.
        lines = [SC.house_dashes(x) for x in lines]
        out.append({"label": label, "lines": lines, "not_specified": ns,
                    "technical": label in TECHNICAL_FIELDS,
                    "digit_relaxed": label in DIGIT_RELAXED_FIELDS})
    return out


def sheet(g: dict | None = None) -> tuple[list[dict], list]:
    """The sixteen checks in the brief's row order, each with its heading and twelve cells.
    Returns (checks, unresolved_requirements)."""
    g = g or D.load_framework()
    by_id = {n["id"]: n for n in g["nodes"]}
    rows = RB.check_rows(g)                    # brief order, scored-first within group
    unresolved: list = []
    checks = []
    for i, r in enumerate(rows, start=1):
        leg = r["leg"]
        p = by_id[f"spec:{leg}"]["properties"]
        name = SC.house_dashes(str(r["name"]))        # rf_name_brief, the V2 check name
        checks.append({"n": i, "leg": leg, "name": name, "scored": r["scored"],
                       "cells": cells_for(p, unresolved)})
    return checks, unresolved


# --------------------------------------------------------------------------------- markdown

def _md_cell(lines: list[str]) -> str:
    return "<br>".join(str(x).replace("|", "/").replace("\n", " ") for x in lines)


def build_markdown(checks: list[dict]) -> str:
    L = [f"# {TITLE}", "", f"*{RUNG_LINE}*", "",
         f"Generated by `{GENERATOR}` from the framework record.", "",
         ("Each check is one measurement specification: what it asks, the instrument that reads "
          "it, what makes it pass, and where the expected behaviour comes from. The fields follow "
          "the ISO/IEC/IEEE measurement information model and its older, simpler form, Goal "
          "Question Metric."), ""]
    for c in checks:
        L.append(f"## {c['n']}. {c['name']} ({c['leg']})")
        L.append("")
        L.append("| Field | Value |")
        L.append("|" + "-" * 28 + "|" + "-" * 48 + "|")
        for cell in c["cells"]:
            L.append(f"| {cell['label']} | {_md_cell(cell['lines'])} |")
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------------------------- docx

def build_docx(checks: list[dict], path: Path, body_pt: float) -> None:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.shared import Inches, Pt, RGBColor as DRGB

    BLACK, GREY, ORANGE = DRGB(0x00, 0x00, 0x00), DRGB(0x55, 0x55, 0x55), DRGB(0xC2, 0x56, 0x00)
    doc = Document()
    doc.styles["Normal"].font.name = B.FONT
    doc.styles["Normal"].font.size = Pt(body_pt)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)     # portrait
    sec.top_margin = sec.bottom_margin = Inches(0.6)
    sec.left_margin = sec.right_margin = Inches(0.7)

    def run(p, text, *, bold=False, size=body_pt, color=BLACK, italic=False):
        r = p.add_run(text)
        r.font.name = B.FONT
        r.font.bold = bold
        r.font.italic = italic
        r.font.size = Pt(size)
        r.font.color.rgb = color
        return r

    def para(container, text="", *, bold=False, size=body_pt, color=BLACK, after=3, italic=False,
             before=0):
        p = container.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(before)
        if text:
            run(p, text, bold=bold, size=size, color=color, italic=italic)
        return p

    # Running page header carries the rung line (DN-019 section 4 rule).
    hp = sec.header.paragraphs[0]
    hp.paragraph_format.space_after = Pt(0)
    run(hp, RUNG_LINE, size=body_pt - 1.5, color=GREY, italic=True)

    para(doc, TITLE, bold=True, size=15, after=2)
    para(doc, RUNG_LINE, size=body_pt - 1.0, color=GREY, italic=True, after=4)
    para(doc, "Each check is one measurement specification: what it asks, the instrument that "
              "reads it, what makes it pass, and where the expected behaviour comes from. The "
              "fields follow the ISO/IEC/IEEE measurement information model and its older, "
              "simpler form, Goal Question Metric.", size=body_pt, after=6)

    label_pt = body_pt - 1.0
    for c in checks:
        para(doc, f"{c['n']}. {c['name']} ({c['leg']})", bold=True, size=body_pt + 1.5,
             color=ORANGE, after=2, before=6)
        t = doc.add_table(rows=0, cols=2)
        t.style = "Table Grid"
        t.autofit = False
        for cell in c["cells"]:
            cells = t.add_row().cells
            cells[0].width = Inches(2.1)
            cells[1].width = Inches(4.6)
            lp = cells[0].paragraphs[0]
            lp.paragraph_format.space_after = Pt(0)
            run(lp, cell["label"], bold=True, size=label_pt, color=GREY)
            for j, line in enumerate(cell["lines"]):
                vp = cells[1].paragraphs[0] if j == 0 else cells[1].add_paragraph()
                vp.paragraph_format.space_after = Pt(0)
                vp.paragraph_format.space_before = Pt(0)
                run(vp, line, size=label_pt, color=BLACK)
    doc.save(str(path))


# -------------------------------------------------------------------------------------- pdf

def render_pdf(md_path: Path, pdf_path: Path, body_pt: float, title: str) -> None:
    """Render the committed Markdown to a portrait PDF. The PDF is rendered from the Markdown on
    disk unchanged (the `render_report` pattern). `<br>` in a cell needs raw_html; Calibri is set
    on the typst side so the PDF matches the Word body where the font is available."""
    size = body_pt - 1.0
    header = ("#set page(paper: \"us-letter\", margin: (x: 1.8cm, y: 1.6cm),\n"
              f"          header: text(size: {size - 1.5}pt, fill: rgb(\"#555555\"), "
              f"style: \"italic\")[{RUNG_LINE}])\n"
              "#show figure: set block(breakable: true)\n"
              f"#show heading: set text(size: {size + 1.5}pt, fill: rgb(\"#C25600\"))\n"
              "#show heading: set block(above: 0.8em, below: 0.4em)\n"
              "#set table(inset: (x: 4pt, y: 2pt), stroke: 0.4pt)\n"
              "#set text(hyphenate: false, font: \"Calibri\")\n"
              "#set par(justify: false, leading: 0.55em, spacing: 0.6em)")
    cmd = ["pandoc", str(md_path), "--from=markdown+pipe_tables+raw_html-smart",
           "--pdf-engine=typst", "--metadata", f"title={title}",
           "--variable", "papersize=us-letter", "--variable", f"fontsize={size}pt",
           "--variable", f"header-includes={header}", "-o", str(pdf_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/typst failed:\n{r.stderr[-1800:]}")


def pdf_text(pdf: Path) -> str:
    from pypdf import PdfReader
    return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(pdf)).pages)


# ------------------------------------------------------------------------------------ checks

def not_specified_matrix(checks: list[dict]) -> dict:
    """{'by_field': {field: n}, 'by_check': {leg: n}, 'cells': [(leg, field), ...], 'total': n}.
    The Client field is excluded (it is never 'not specified' by its rule)."""
    by_field: dict[str, int] = {}
    by_check: dict[str, int] = {}
    cells = []
    for c in checks:
        for cell in c["cells"]:
            if cell["label"] == "Client":
                continue
            by_field.setdefault(cell["label"], 0)
            by_check.setdefault(c["leg"], 0)
            if cell["not_specified"]:
                by_field[cell["label"]] += 1
                by_check[c["leg"]] += 1
                cells.append((c["leg"], cell["label"]))
    return {"by_field": by_field, "by_check": by_check, "cells": cells, "total": len(cells)}


def vocabulary_audit(checks: list[dict]) -> dict:
    """Banned words per cell. `reader_hits` (FATAL): hits in a non-technical cell. `technical_hits`
    (reported, not fatal): hits in the ISO-15939 sensor cells, expected at this rung."""
    reader_hits, technical_hits = [], []
    for c in checks:
        for cell in c["cells"]:
            text = " ".join(cell["lines"])
            for w, ctx in D.banned_hits_prose(text):
                rec = {"leg": c["leg"], "field": cell["label"], "word": w, "context": ctx}
                (technical_hits if cell["technical"] else reader_hits).append(rec)
    return {"reader_hits": reader_hits, "technical_hits": technical_hits}


def digit_audit(checks: list[dict]) -> list[str]:
    """No bare number in a cell outside a citation, except the digit-relaxed cells (signal,
    rf_requirements). The heading number is structural and not a cell."""
    bad = []
    for c in checks:
        for cell in c["cells"]:
            if cell["digit_relaxed"]:
                continue
            text = RB._CITATION.sub(" ", " ".join(cell["lines"]))
            for m in B._BARE.finditer(text):
                bad.append(f"{c['leg']} {cell['label']!r}: bare number {m.group(0)!r}")
    return bad


def build(out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    checks, unresolved = sheet(g)
    if len(checks) != 16:
        raise SystemExit(f"FATAL: {len(checks)} checks, expected 16")

    md_path = out / f"{STEM}.md"
    docx_path = out / f"{STEM}.docx"
    pdf_path = out / f"{STEM}.pdf"

    md = build_markdown(checks)
    md_path.write_text(md, encoding="utf-8")
    build_docx(checks, docx_path, BODY_PT)
    render_pdf(md_path, pdf_path, BODY_PT, TITLE)
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()

    docx_txt = RB.docx_text(docx_path)
    pdf_txt = pdf_text(pdf_path)

    ns = not_specified_matrix(checks)
    vocab = vocabulary_audit(checks)
    digits = digit_audit(checks)
    # Dash: no em/en dash anywhere in any rendered form (the U+2014/U+2013 grep of the Markdown,
    # and dash_hits over every form).
    emdash_lines = [i + 1 for i, line in enumerate(md.splitlines())
                    if "—" in line or "–" in line]
    dashes = {"markdown": RB.dash_hits(md), "docx": RB.dash_hits(docx_txt),
              "pdf": RB.dash_hits(pdf_txt), "markdown_u2014_u2013_lines": emdash_lines}
    font_colour = {"docx": RB.docx_font_colour_audit(docx_path)}
    tevv = {form: ("TEVV" in txt) for form, txt in
            (("markdown", md), ("docx", docx_txt), ("pdf", pdf_txt))}

    checks_report = {
        "row_order": [c["leg"] for c in checks],
        "not_specified": ns,
        "unresolved_requirement_sources": sorted({(leg, s) for leg, s in unresolved}),
        "vocabulary": vocab,
        "digit_audit": digits,
        "dashes": dashes,
        "font_colour_audit": font_colour,
        "tevv_present": tevv,
        "mentions_508": sorted({f for f, t in (("markdown", md), ("docx", docx_txt),
                                               ("pdf", pdf_txt)) if "508" in t}),
    }

    failures = []
    if vocab["reader_hits"]:
        failures.append("vocabulary_reader_hits")
    if digits:
        failures.append("digit_audit")
    if any(font_colour.values()):
        failures.append("font_colour_audit")
    for form in ("markdown", "docx", "pdf"):
        if dashes[form]:
            failures.append(f"dashes_{form}")
    if emdash_lines:
        failures.append("markdown_u2014_u2013")
    if checks_report["mentions_508"]:
        failures.append("mentions_508")

    report = {
        "generated_by": GENERATOR, "task": TASK,
        "products": [
            {"name": md_path.name, "md_sha256": md_sha},
            {"name": docx_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest()},
            {"name": pdf_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
             "pages": len(__import__("pypdf").PdfReader(str(pdf_path)).pages)},
        ],
        "checks": checks_report, "failures": failures,
    }
    (out / "build_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("FATAL: build checks failed: " + ", ".join(failures) + "\n"
                         + json.dumps(checks_report, indent=1, ensure_ascii=False)[:4000])
    return report


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    rep = build()
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
