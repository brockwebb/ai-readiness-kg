#!/usr/bin/env python3
"""The two DN-020 audience documents: the ICSP one-page and the working-group explainer.
**Zero spend, no network.**

`cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md`
Part C, implementing DN-020 section 6. Both are built from the framework record, the cycle of
record and the roll-up's computed per-rung counts (imported from `readiness_rollup_build`, not
recomputed). Each is one Markdown source rendered to PDF (the `render_report` pattern) and to
Word.

Pictures (DN-020 section 7) are generated outside the repository and dropped into
`reports/figures/dn020/<n>.png`. Until a file is there the builder places a captioned placeholder
frame; when it is there the builder places the image. The build report says, per picture, which
was placed. The captions carry the facts (DN-020 section 7); the ICSP's figure-3 caption carries
the per-rung agency counts, spelled as words so the page stays free of bare digits.

Vocabulary (DN-016 / the task): readiness diagnostic, check, rung, track, prerequisite; SI for
government material; AI only inside USAFacts' own titles and the framework captions quoted here.
The banned-word scan (`D.banned_hits_prose`) runs over the project's prose, not over the verbatim
USAFacts captions (Access II's reads "agents can crawl"); captions are the quoted zone.

The "SI use" statement (DN-020 section 6, attributed to FCSM 26-01) is appended to both. FCSM
26-01's own text is not in this corpus or the federal statistical policy KG (a premise recorded
in the RESULT), so the statement is composed from DN-018's SI framing (SI = statistical
information, the machine user's data) and the task's vocabulary rule.

    /opt/anaconda3/bin/python3 scripts/dn020_documents_build.py
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
import readiness_rollup_build as R  # noqa: E402
import sixteen_checks_build as S  # noqa: E402
import instrument as I  # noqa: E402
import yaml  # noqa: E402

GENERATOR = "scripts/dn020_documents_build.py"
TASK = "cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md"
OUT = REPO / "reports" / "dn020"
FIGURES = REPO / "reports" / "figures" / "dn020"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"

ICSP_STEM = "ICSP_SI_Readiness_One_Page"
EXPLAINER_STEM = "SI_Readiness_Working_Group_Explainer"

ICSP_TITLE = "Statistical-information readiness: the USAFacts ladder and where agencies stand"
EXPLAINER_TITLE = "A readiness diagnostic on the USAFacts ladder: a working-group explainer"

#: The "SI use" statement (DN-020 section 6, attributed to FCSM 26-01). Composed from DN-018's
#: SI framing because FCSM 26-01's own text is not in the corpus (RESULT premise).
SI_USE = ("SI use: in these pages SI means statistical information, the data a federal "
          "statistical agency publishes for the public; the readiness described is whether a "
          "program acting for a member of the public can reach that statistical information and "
          "the documentation that travels with it. The letters AI appear only inside USAFacts' "
          "own titles and the framework captions quoted here.")

#: The worked check for the explainer: the simplest sensor on the ladder. A6 reads the data
#: page's own markup from a single request, follows no link and visits no seeded location, so a
#: reader can follow it end to end in one picture.
WORKED_LEG = "A6"

#: DN-020 section 7 picture specs. `caption_core` is the facts the caption carries; figure 3's
#: caption is completed at build time from the roll-up's counts. Heights keep the ICSP to one
#: page.
PICTURES = {
    1: {"caption": "Three tracks, three levels in each, and three prerequisites that hold before "
                   "any level applies.", "height_cm": 3.0, "width_frac": 78},
    2: {"caption": "FAIR, 2016; the USAFacts guide, 2025; the USAFacts framework, 2026; and this "
                   "project's sensor on the ladder.", "height_cm": 3.8, "width_frac": 82},
    3: {"caption": None, "height_cm": 2.8, "width_frac": 82},  # completed from the counts
    4: {"caption": "A check end to end: the question, the sensor, the reading, the state.",
        "height_cm": 4.2, "width_frac": 82},
}

#: The measured rungs in order, each mapped to the rung whose caption answers "what the next rung
#: asks for". A prerequisite's next step is the first level of its track's foot (Access I); the
#: top measured level points at the level above it.
NEXT_RUNG = {
    "usaf:pre:discoverable": "usaf:access:1",
    "usaf:pre:licensed": "usaf:access:1",
    "usaf:access:1": "usaf:access:2",
    "usaf:access:2": "usaf:access:3",
    "usaf:context:1": "usaf:context:2",
    "usaf:context:2": "usaf:context:3",
}


# --------------------------------------------------------------------------------- data

def load_cycle() -> dict:
    pub = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))
    return {"cycle": pub["snapshot_cycle"]}


def usaf_nodes(g: dict) -> dict:
    return {n["id"]: n for n in g["nodes"]
            if set(n["labels"]) & {"UsafactsTrack", "UsafactsLevel", "UsafactsPrerequisite"}}


def level_caption(nodes: dict, rid: str) -> str:
    """The deck caption for a rung, verbatim from the record (house-dash normalised)."""
    return S.house_dashes(str(nodes[rid]["properties"]["name"]))


def rollup_rows(g: dict, grid: dict) -> list[dict]:
    """The roll-up's rung rows, imported from `readiness_rollup_build` (not recomputed)."""
    return R.rung_rows(g, grid)


def passing_by_rung(rows: list[dict]) -> dict:
    return {r["rung"]: r["passing_n"] for r in rows}


# --------------------------------------------------------------------------------- figures

def figure_block(n: int, caption: str) -> str:
    """A pandoc Markdown fragment for picture `n`: a raw typst block drawing the image when
    `reports/figures/dn020/<n>.png` exists, or a captioned placeholder frame when it does not.
    `render_pdf` runs with cwd=REPO, so the image path is REPO-relative."""
    spec = PICTURES[n]
    png = FIGURES / f"{n}.png"
    frac = spec["width_frac"]
    if png.exists():
        # Bound the image to the SAME height as the placeholder it replaces, so a dropped-in
        # picture of any aspect ratio keeps the ICSP to one page and the explainer to its range.
        body = (f'#align(center, image("reports/figures/dn020/{n}.png", '
                f'height: {spec["height_cm"]}cm))')
    else:
        body = (f'#align(center, block(width: {frac}%, height: {spec["height_cm"]}cm, '
                f'stroke: 0.6pt + rgb("#9aa0a6"), radius: 4pt, inset: 10pt, '
                f'fill: rgb("#fbfbfb"))[#align(center + horizon)[#text(fill: rgb("#555555"), '
                f'size: 8.5pt)[Figure {_WORD[n].capitalize()} goes here. '
                f'Add reports/figures/dn020/{n}.png to place the illustration.]]])')
    cap = f"*Figure {_WORD[n]}. {caption}*"
    return "```{=typst}\n" + body + "\n```\n\n" + cap


def figure_placed(n: int) -> dict:
    png = FIGURES / f"{n}.png"
    return {"figure": n, "placed": "picture" if png.exists() else "placeholder",
            "path": f"reports/figures/dn020/{n}.png", "present": png.exists()}


_WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
         9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
         15: "fifteen", 16: "sixteen", 0: "zero"}


def word(n) -> str:
    if n is None or n not in _WORD:
        raise SystemExit(f"FATAL: {n} outside the spelled range nought to sixteen")
    return _WORD[n]


# --------------------------------------------------------------------------------- the ICSP page

def figure3_caption(passing: dict) -> str:
    """Picture 3's caption: the per-rung agency counts on the Access and Context tracks, from the
    roll-up, spelled as words. The Evaluation track carries no measured check."""
    a1, a2 = passing["usaf:access:1"], passing["usaf:access:2"]
    c1, c2 = passing["usaf:context:1"], passing["usaf:context:2"]
    return (f"Of sixteen agencies, {word(a1)} pass every measured check at Access I and "
            f"{word(a2)} at Access II; on the Context track {word(c1)} pass at Context I and "
            f"{word(c2)} at Context II. No agency is measured above these rungs, and the "
            f"Evaluation track carries no check yet.")


def icsp_markdown(g: dict, nodes: dict, passing: dict) -> str:
    L = [f"# {ICSP_TITLE}", "",
         f"Prepared for the Interagency Council on Statistical Policy. Generated by "
         f"`{GENERATOR}` from the framework record and the cycle of record.", ""]
    # what USAFacts built and why it is worth adopting (two sentences)
    L += ["USAFacts, a heavy consumer of federal data, has set out a framework for making "
          "government data ready for the programs the public now uses to reach it: three tracks, "
          "Agentic Access, Agentic Context and Agentic Evaluation, each a short ladder an agency "
          "climbs at its own pace, with three prerequisites that hold before any rung counts.",
          "It is worth adopting because it names a destination in plain terms and lets each "
          "agency place itself and decide where to invest next, rather than asking for everything "
          "at once.", ""]
    # picture 1, the ladder
    L += [figure_block(1, PICTURES[1]["caption"]), ""]
    # where the sixteen agencies stand (picture 3)
    L += ["**Where the agencies stand today.** The readiness diagnostic has placed sixteen "
          "federal statistical agencies on the ladder from the outside, measuring the "
          "prerequisites and the lower rungs that a public request can reach.", "",
          figure_block(3, figure3_caption(passing)), ""]
    # what an agency gets (two sentences)
    L += ["**What an agency gets from the diagnostic.** For each track it receives its own rung "
          "and the single next thing that would raise it one rung, read from published criteria "
          "rather than asserted.",
          "A check that could not be measured for an agency names its reason and never counts "
          "against it, so an agency sees where it stands and what to do next, not a grade.", ""]
    # evaluation track empty (one sentence)
    L += ["The Evaluation track, where an agency would publish evaluation sets and benchmark "
          "results, carries no check yet: measuring it is a testing-and-evaluation programme, "
          "not a reading a public request can take, and it is shown empty rather than scored.", ""]
    # SI use footer
    L += ["---", "", f"*{SI_USE}*", ""]
    return "\n".join(L)


# --------------------------------------------------------------------- the working-group explainer

def worked_check(g: dict) -> dict:
    s = {x["leg"]: x for x in D.instrument_specs(g)}[WORKED_LEG]
    name = {r["leg"]: r["name"] for r in RB.check_rows(g)}[WORKED_LEG]
    return {"name": S.house_dashes(str(name)),
            "question": S.house_dashes(str(s["rf_question"])),
            "where": S.house_dashes(S.first_sentence(str(s["rf_where_we_look"]))),
            "does": S.house_dashes(S.first_sentence(str(s["rf_what_client_does"]))),
            "passes": S.house_dashes(S.first_sentence(str(s["rf_pass"]))),
            "why": S.house_dashes(str(s.get("rf_why_short") or s.get("rf_why_it_matters") or ""))}


#: DN-020 section 2's four lineage steps, each a short paragraph quoting the note. The quoted
#: fragments are from DN-020 section 2 verbatim.
LINEAGE_STEPS = [
    ("FAIR, 2016", "The FAIR principles asked that data be \"Findable, Accessible, Interoperable, "
     "Reusable, written so that machines as well as people can act on data\". They are "
     "deliberately high level and have been read many ways."),
    ("The USAFacts guide, 2025", "USAFacts' earlier guide set out four criteria, \"Accessible, "
     "Understandable, Accurate, Open\", written from its experience as a heavy consumer of "
     "federal data."),
    ("The USAFacts framework, 2026", "In the August 2026 framework \"Accessible becomes the "
     "Access track; Understandable becomes the Context track; Accurate becomes the Evaluation "
     "track; Open moves out of the ladder and becomes a prerequisite\", with levels borrowed "
     "from SLSA."),
    ("This project", "This project puts \"the ladder with a sensor on it\": each check is a "
     "measurement specification, each prerequisite is tested rather than declared, and the "
     "tracks the sensor cannot reach yet are marked as such rather than scored."),
]

#: DN-020 section 3, "what we kept, what we changed", in six lines.
KEPT_CHANGED = [
    "Kept, as USAFacts wrote them: the three tracks and their names, the three levels, the three "
    "prerequisites, the SLSA shape, and the intended use.",
    "Changed, and why:",
    "Prerequisites are measured from the outside, not asked of the agency, because a prerequisite "
    "only asserted cannot anchor a level.",
    "Every check carries a measurement specification, so two agencies cannot claim the same rung "
    "for different reasons.",
    "A rung is reported per check and an agency's position is the highest rung at which every "
    "measured check passes; a check not measured is left out, never read as a fail.",
    "The Evaluation track is shown empty and said to be empty, because building its instrument is "
    "a testing-and-evaluation programme this diagnostic does not attempt.",
]


def placement_table(rows: list[dict]) -> list[str]:
    """DN-020 section 4's placement in plain labels: rung, then the plain check names."""
    L = ["| USAFacts rung | Checks placed here |", "|---|---|"]
    for r in rows:
        names = "; ".join(c["name"] for c in r["checks"]) if r["checks"] else "none measured yet"
        L.append(f"| {r['label']} | {names} |")
    return L


def explainer_markdown(g: dict, nodes: dict, rows: list[dict], passing: dict, cycle: dict) -> str:
    wc = worked_check(g)
    a1, a2 = passing["usaf:access:1"], passing["usaf:access:2"]
    c1, c2 = passing["usaf:context:1"], passing["usaf:context:2"]
    L = [f"# {EXPLAINER_TITLE}", "",
         f"Generated by `{GENERATOR}` from the framework record and the cycle of record.", ""]

    # page 1, the bottom line
    L += ["## The bottom line", "",
          "The readiness diagnostic asks, for a federal statistical agency, whether a program "
          "acting for a member of the public can reach the agency's data and the documentation "
          "that goes with it. It is sixteen checks, each one request from the least privileged "
          "client the public has, against published criteria.",
          "USAFacts' August 2026 framework is the ladder those checks now hang from: three "
          "tracks, Agentic Access, Agentic Context and Agentic Evaluation, three levels in each, "
          "with three prerequisites before any level applies. An agency climbs at its own pace, "
          "and the lowest level is worth having on its own.",
          f"Across sixteen agencies on the cycle of record, {word(a1)} pass every measured check "
          f"at Access I and {word(a2)} at Access II; on the Context track {word(c1)} pass at "
          f"Context I and {word(c2)} at Context II. The rungs above these carry no check yet.", ""]

    # one worked check end to end, with picture 4
    L += ["## One check, end to end", "",
          f"Take the simplest check to follow, \"{wc['name']}\". It has the simplest sensor on "
          f"the ladder: one request to the data page, reading what the page itself sends, "
          f"following no link and visiting no other location.", "",
          figure_block(4, PICTURES[4]["caption"]), "",
          f"**The question.** {wc['question']}",
          f"**The sensor.** {wc['where']} {wc['does']}",
          f"**What a pass looks like.** {wc['passes']}",
          "**The state.** The reading comes back as one of four: it passes, it partly passes, it "
          "fails, or it could not be measured and the reason is recorded. A reason is never a "
          "fail.", ""]

    # the lineage, with picture 2
    L += ["## Where the framework comes from", "",
          figure_block(2, PICTURES[2]["caption"]), ""]
    for head, body in LINEAGE_STEPS:
        L += [f"**{head}.** {body}", ""]

    # the placement table of section 4 in plain labels
    L += ["## Where the sixteen checks sit on the ladder", ""]
    L += placement_table(rows)
    L += [""]

    # for each rung with a measured check, what passing looks like and what the next rung asks for
    L += ["## What each measured rung asks, and what comes next", "",
          "Each count below is read rung by rung on its own, not as a climb: an agency can clear "
          "a level's checks and still miss a prerequisite check it was measured on, so a higher "
          "rung can show more agencies than a lower one. A check that could not be measured for "
          "an agency is left out of that rung for it, never counted as a fail.", ""]
    for r in rows:
        if not r["checks"]:
            continue
        nxt = NEXT_RUNG.get(r["rung"])
        nxt_cap = level_caption(nodes, nxt) if nxt else None
        passed = r["passing"]
        line = (f"**{r['label']}.** An agency clears this rung when none of its measured checks "
                f"here comes back a fail; on the cycle of record {passed} did.")
        if nxt_cap:
            line += f" The next rung up asks for: \"{nxt_cap}\"."
        L += [line, ""]

    # what we kept, what we changed
    L += ["## What we kept, what we changed", ""]
    L += KEPT_CHANGED
    L += [""]

    # attachments and SI use
    L += ["## For the record", "",
          "Attached: the measurement sheet (every check as a measurement specification), the "
          "roll-up (this ladder at a glance), the sixteen-check one-pager, and DN-019 (the view "
          "ladder these reports sit on).", "",
          "---", "", f"*{SI_USE}*", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------------- docx

def _add_image_or_placeholder(doc, n: int, caption: str):
    from docx.shared import Inches, Pt, RGBColor as DRGB
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    GREY = DRGB(0x55, 0x55, 0x55)
    png = FIGURES / f"{n}.png"
    if png.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(png), height=Inches(PICTURES[n]["height_cm"] / 2.54))
    else:
        t = doc.add_table(rows=1, cols=1)
        t.style = "Table Grid"
        cell = t.rows[0].cells[0]
        cell.width = Inches(5.5)
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(f"Figure {_WORD[n]} goes here. Add reports/figures/dn020/{n}.png.")
        r.font.name = B.FONT
        r.font.size = Pt(9)
        r.font.italic = True
        r.font.color.rgb = GREY
    capp = doc.add_paragraph()
    capp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = capp.add_run(f"Figure {_WORD[n]}. {caption}")
    cr.font.name = B.FONT
    cr.font.size = Pt(9)
    cr.font.italic = True
    cr.font.color.rgb = GREY


_MD_FIG = re.compile(r"^```\{=typst\}")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _docx_from_markdown(md: str, path: Path, *, figures_caption: dict, body_pt: float,
                        landscape: bool = False) -> None:
    """Render the document's Markdown to Word. The figure blocks (raw typst) are replaced by a
    picture or a placeholder frame; headings, bold leads, tables and paragraphs are rendered with
    the house font and colours."""
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.shared import Inches, Pt, RGBColor as DRGB
    BLACK, GREY = DRGB(0x00, 0x00, 0x00), DRGB(0x55, 0x55, 0x55)
    doc = Document()
    doc.styles["Normal"].font.name = B.FONT
    doc.styles["Normal"].font.size = Pt(body_pt)
    sec = doc.sections[0]
    if landscape:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = Inches(11), Inches(8.5)
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

    def rich(p, text, *, size=body_pt, color=BLACK, italic=False):
        """Render a line with **bold** leads."""
        pos = 0
        for m in _BOLD.finditer(text):
            if m.start() > pos:
                run(p, text[pos:m.start()], size=size, color=color, italic=italic)
            run(p, m.group(1), bold=True, size=size, color=color, italic=italic)
            pos = m.end()
        if pos < len(text):
            run(p, text[pos:], size=size, color=color, italic=italic)

    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if _MD_FIG.match(ln):
            # a figure block: find its figure number from the caption line that follows the fence
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            # caption line is after the closing fence and a blank
            cap_line = ""
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines):
                cap_line = lines[k]
            m = re.search(r"Figure (\w+)\.\s*(.*?)\*?$", cap_line)
            num = {v: kk for kk, v in _WORD.items()}.get((m.group(1).lower() if m else ""), None)
            if num is not None:
                _add_image_or_placeholder(doc, num, figures_caption[num])
            i = k + 1
            continue
        if ln.startswith("# "):
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
            run(p, ln[2:], bold=True, size=body_pt + 5)
        elif ln.startswith("## "):
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(3)
            run(p, ln[3:], bold=True, size=body_pt + 2)
        elif ln.startswith("|"):
            # consume a markdown table
            tbl = [ln]
            while i + 1 < len(lines) and lines[i + 1].startswith("|"):
                i += 1
                tbl.append(lines[i])
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tbl
                    if set(r.strip()) - set("|-: ")]
            if rows:
                t = doc.add_table(rows=len(rows), cols=len(rows[0]))
                t.style = "Table Grid"
                for ri, rr in enumerate(rows):
                    for ci, cv in enumerate(rr):
                        cp = t.rows[ri].cells[ci].paragraphs[0]
                        rich(cp, cv, size=body_pt - 1, color=(BLACK if ri else BLACK))
                        if ri == 0:
                            for rn in cp.runs:
                                rn.font.bold = True
        elif ln.strip() == "---":
            doc.add_paragraph()
        elif ln.strip().startswith("*") and ln.strip().endswith("*") and ln.strip() != "*":
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
            rich(p, ln.strip().strip("*"), size=body_pt - 0.5, color=GREY, italic=True)
        elif ln.strip():
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
            rich(p, ln, size=body_pt)
        i += 1
    doc.save(str(path))


# --------------------------------------------------------------------------------- pdf

def render_pdf(md_path: Path, pdf_path: Path, title: str, *, body_pt: float, margin_y: float) -> None:
    # No `--metadata title`: the document's own `# ` heading is the title, and passing the title
    # as metadata too makes pandoc's typst template render a second, large title block above it
    # (the duplicate a reader sees on the roll-up PDFs). The H1 heading carries the title once.
    header = ("#set text(hyphenate: false)\n"
              "#show figure: set block(breakable: true)\n"
              f"#show heading: set block(above: 0.7em, below: 0.4em)\n"
              "#set par(justify: false, leading: 0.62em, spacing: 0.75em)")
    cmd = ["pandoc", str(md_path), "--from=markdown+pipe_tables+raw_attribute-smart",
           "--pdf-engine=typst",
           "--variable", "papersize=us-letter", "--variable", f"fontsize={body_pt}pt",
           "--variable", "margin-x=1.6cm", "--variable", f"margin-y={margin_y}cm",
           "--variable", f"header-includes={header}", "-o", str(pdf_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/typst failed for {md_path.name}:\n{r.stderr[-1800:]}")


def pdf_pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def pdf_text(pdf: Path) -> str:
    from pypdf import PdfReader
    return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(pdf)).pages)


# --------------------------------------------------------------------------------- vocab scan

def project_prose(md: str, captions: list[str]) -> str:
    """The text the banned-word scan runs over: the document's prose with the verbatim USAFacts
    captions removed (the quoted zone), the raw typst figure blocks removed, and the markup
    stripped."""
    out = []
    in_fig = False
    for ln in md.split("\n"):
        if ln.startswith("```"):
            in_fig = not in_fig
            continue
        if in_fig:
            continue
        out.append(ln)
    text = "\n".join(out)
    for cap in captions:
        text = text.replace(cap, " ")
    return text


# --------------------------------------------------------------------------------- build

def build(out: Path = OUT, *, measure: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    grid = I.load_grid(I.load_config())
    cycle = load_cycle()
    nodes = usaf_nodes(g)
    rows = rollup_rows(g, grid)
    passing = passing_by_rung(rows)

    fig3_cap = figure3_caption(passing)
    icsp_caps = {1: PICTURES[1]["caption"], 3: fig3_cap}
    expl_caps = {2: PICTURES[2]["caption"], 4: PICTURES[4]["caption"]}

    # ICSP page
    icsp_md = icsp_markdown(g, nodes, passing)
    icsp_md_path = out / f"{ICSP_STEM}.md"
    icsp_md_path.write_text(icsp_md, encoding="utf-8")
    icsp_docx = out / f"{ICSP_STEM}.docx"
    _docx_from_markdown(icsp_md, icsp_docx, figures_caption=icsp_caps, body_pt=10.0)
    icsp_pdf = out / f"{ICSP_STEM}.pdf"
    render_pdf(icsp_md_path, icsp_pdf, ICSP_TITLE, body_pt=9.5, margin_y=0.8)

    # Explainer
    expl_md = explainer_markdown(g, nodes, rows, passing, cycle)
    expl_md_path = out / f"{EXPLAINER_STEM}.md"
    expl_md_path.write_text(expl_md, encoding="utf-8")
    expl_docx = out / f"{EXPLAINER_STEM}.docx"
    _docx_from_markdown(expl_md, expl_docx, figures_caption=expl_caps, body_pt=12.0)
    expl_pdf = out / f"{EXPLAINER_STEM}.pdf"
    render_pdf(expl_md_path, expl_pdf, EXPLAINER_TITLE, body_pt=12.0, margin_y=1.6)

    # ---- checks ----
    # verbatim USAFacts captions, exempt from the banned-word scan (quoted zone)
    all_captions = [S.house_dashes(str(n["properties"]["name"])) for n in nodes.values()
                    if "UsafactsLevel" in n["labels"]]
    icsp_prose = project_prose(icsp_md, all_captions)
    expl_prose = project_prose(expl_md, all_captions)
    icsp_pages = pdf_pages(icsp_pdf) if measure else None
    expl_pages = pdf_pages(expl_pdf) if measure else None

    checks = {
        "icsp_pdf_pages": icsp_pages,
        "explainer_pdf_pages": expl_pages,
        "vocabulary": {"icsp": D.banned_hits_prose(icsp_prose),
                       "explainer": D.banned_hits_prose(expl_prose)},
        "dashes": {"icsp": RB.dash_hits(icsp_prose), "explainer": RB.dash_hits(expl_prose)},
        "figures": {"icsp": [figure_placed(n) for n in (1, 3)],
                    "explainer": [figure_placed(n) for n in (2, 4)]},
        "worked_check": WORKED_LEG,
    }
    failures = []
    if measure:
        if icsp_pages != 1:
            failures.append(f"ICSP page is {icsp_pages} pages, must be 1")
        if expl_pages is None or not (4 <= expl_pages <= 6):
            failures.append(f"explainer is {expl_pages} pages, must be 4 to 6")
    for k in ("vocabulary", "dashes"):
        if any(checks[k].values()):
            failures.append(k)

    def prod(md_path, docx_path, pdf_path, pages):
        md = md_path.read_text(encoding="utf-8")
        return [
            {"name": md_path.name, "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()},
            {"name": docx_path.name, "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest()},
            {"name": pdf_path.name, "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
             "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(), "pages": pages},
        ]

    report = {
        "generated_by": GENERATOR, "task": TASK, "cycle": cycle["cycle"],
        "documents": {
            "icsp": prod(icsp_md_path, icsp_docx, icsp_pdf, icsp_pages),
            "explainer": prod(expl_md_path, expl_docx, expl_pdf, expl_pages),
        },
        "figures": checks["figures"],
        "checks": checks, "failures": failures,
    }
    (out / "build_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("FATAL: build checks failed: " + ", ".join(failures) + "\n"
                         + json.dumps(checks, indent=1, ensure_ascii=False)[:3000])
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-measure", action="store_true")
    a = ap.parse_args(argv)
    rep = build(measure=not a.no_measure)
    print(json.dumps({"documents": rep["documents"], "figures": rep["figures"],
                      "checks": {k: rep["checks"][k] for k in (
                          "icsp_pdf_pages", "explainer_pdf_pages", "vocabulary", "dashes",
                          "worked_check")},
                      "failures": rep["failures"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
