#!/usr/bin/env python3
"""The two DN-020 audience documents, rewritten for an executive reader (DN-020 section 10).
**Zero spend, no network.**

`cc_tasks/2026-11-13_the_icsp_page_and_explainer_rewritten_for_an_executive_reader.md`,
implementing DN-020 section 10 (amendments A1 to A7), its ADDENDUM 01 (the four drawn figures) and
ADDENDUM 02 (SI means superintelligence). Both documents are built from the framework record, the
project's round of measurements, and the roll-up's computed per-level counts (imported from
`readiness_rollup_build`, never recomputed). Each is one Markdown source rendered to PDF (the
`render_report` pattern) and to Word.

What the rewrite changed, against the 2026-11-05 build:

* **SI means superintelligence** (ADDENDUM 02 / DN-020 A1). First use on each document reads
  "SI (superintelligence), the federal term that replaced AI on 29 September 2026", then "SI"
  alone. The old "statistical information" gloss is gone and the build fails if it returns.
* **An executive reader** (DN-020 A4 to A7). No letter codes, record ids, script paths or file
  names in the body of either document; the generator and the record commit go in the build
  report, and on the explainer only in one small footer line. The words A4 keeps out (sensor,
  measurement specification, cycle of record, least privileged client, markup, rung-by-rung) join
  the DN-016 list (scan/probe/crawl/audit/unmeasurable/ruling); the build fails on any of them in
  the project's prose. USAFacts' own captions are the one quoted zone (A3): each is taken from
  `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md` and its line is in the build
  report.
* **The ICSP page answers five questions** in A6's order; **the explainer follows A7's order** and
  its level table carries each measured level once, so no sentence repeats. The build fails if a
  sentence appears twice.
* **The figures are the four drawn SVGs** (ADDENDUM 01). The PDF embeds the SVG; the Word file
  needs a raster, so the SVG is rendered to a PNG beside it when a converter is on the machine.

    /opt/anaconda3/bin/python3 scripts/dn020_documents_build.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
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
TASK = "cc_tasks/2026-11-13_the_icsp_page_and_explainer_rewritten_for_an_executive_reader.md"
OUT = REPO / "reports" / "dn020"
FIGURES = REPO / "reports" / "figures" / "dn020"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
DECK_MD = REPO / "state" / "docling_md" / "usafacts-ai-ready-framework-deck-2026-08.md"

ICSP_STEM = "ICSP_SI_Readiness_One_Page"
EXPLAINER_STEM = "SI_Readiness_Working_Group_Explainer"

ICSP_TITLE = "SI readiness of federal statistical data: a ladder, and where agencies stand"
EXPLAINER_TITLE = "SI readiness on the USAFacts ladder: a working-group explainer"

#: The first-use gloss, verbatim from ADDENDUM 02. The build fails if "SI (" is ever followed by
#: anything but "superintelligence", so this is the only expansion that may appear.
SI_FIRST_USE = "SI (superintelligence), the federal term that replaced AI on 29 September 2026"

#: The plain question A4 fixes for each track, introduced once with USAFacts' name.
TRACK_QUESTIONS = [
    ("Access", "can a program get the data?"),
    ("Context", "can it understand what it got?"),
    ("Evaluation", "has anyone checked the answers it gives?"),
]

#: The credit line (Part B) and the closing statement (A2). The closing statement states the facts
#: of production only — which model drafted the wording, from what record — and claims no human
#: review, because the record cannot show one. Modelled on `scripts/dcat_brief_build.py`'s
#: FCSM 26-01 statement.
CREDIT = "Built on USAFacts' framework (August 2026) and the FAIR principles (2016)."
CLOSING = ("How this was made. These pages were produced by a program from the project's framework "
           "record and its most recent round of public web requests, made in October 2026; every "
           "count on them is read from that record, not typed by hand. The wording was drafted with "
           "Anthropic's Claude Opus 4.8, through Claude Code under a commercial subscription, on "
           "13 November 2026, and is the project's own. This note follows FCSM 26-01 on disclosing "
           "the use of generative SI.")

#: The four drawn figures (ADDENDUM 01). `caption_core` is the facts the caption carries; figure 3's
#: caption is completed at build time from the counts. Heights keep the ICSP to one page and the
#: explainer in range; the ICSP heights are set by the fit ladder, these are the explainer's.
PICTURES = {
    1: {"caption": "Three tracks, three levels on each, and three basics that come first.",
        "height_cm": 3.4},
    2: {"caption": "FAIR in 2016, the USAFacts guide in 2025, the USAFacts framework in 2026, and "
                   "this diagnostic's check on each step.", "height_cm": 3.4},
    3: {"caption": None, "height_cm": 3.0},  # completed from the counts
    4: {"caption": "One check from start to finish: the question, what we look at, the reading, the "
                   "result.", "height_cm": 3.8},
}

#: The measured levels in order, each mapped to the level whose caption answers "what the next step
#: up asks for" (A7). The top measured level points at the level above it.
NEXT_LEVEL = {
    "usaf:access:1": "usaf:access:2",
    "usaf:access:2": "usaf:access:3",
    "usaf:context:1": "usaf:context:2",
    "usaf:context:2": "usaf:context:3",
}

#: The four basics, in the order the basics table shows them (DN-020 section 4: the three
#: discoverability checks, then the licensing check). Plain names come from the record; the "bar"
#: is "a published requirement" when the record Scores the check, "this project's reading" when it
#: does not (Part A).
BASIC_LEGS = ["A5", "A6", "D4", "D1"]

#: Short noun phrases for the ICSP's one basics bullet, so "most meet X" reads as a sentence (the
#: record's plain names are full clauses that would not). The explainer's basics table uses the
#: record names; these are only the one-line summary on the page.
ICSP_BASIC_PHRASE = {
    "A5": "having each data page in the site's own list of pages",
    "A6": "a page that labels itself a dataset",
    "D4": "a listing in the agency's data inventory",
    "D1": "a clear licence on the page",
}

#: Numbers nought to sixteen as words, so neither page carries a bare digit in a sentence.
_WORD = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
         14: "fourteen", 15: "fifteen", 16: "sixteen"}


def word(n) -> str:
    if n is None or n not in _WORD:
        raise SystemExit(f"FATAL: {n} outside the spelled range nought to sixteen")
    return _WORD[n]


def fig_word(n: int) -> str:
    return {1: "one", 2: "two", 3: "three", 4: "four"}[n]


# --------------------------------------------------------------------------------- data

def git_out(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FATAL: git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def record_commit() -> str:
    """The commit that last wrote the framework record — the ref a reader can check out."""
    return git_out("log", "-1", "--format=%H", "--", "framework/ai_readiness_framework.json")[:12]


def load_cycle() -> dict:
    pub = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))
    return {"cycle": pub["snapshot_cycle"]}


def usaf_nodes(g: dict) -> dict:
    return {n["id"]: n for n in g["nodes"]
            if set(n["labels"]) & {"UsafactsTrack", "UsafactsLevel", "UsafactsPrerequisite"}}


def level_caption(nodes: dict, rid: str) -> str:
    """The deck caption for a level, verbatim from the record (house-dash normalised)."""
    return S.house_dashes(str(nodes[rid]["properties"]["name"]))


def si_vocab(text: str) -> str:
    """Project prose uses SI for the machine user; a project-authored check name that still says
    AI (A4's "let AI tools in") is rendered with SI. USAFacts' captions and the history line are
    never passed through this — they keep AI as written (DN-020 T6 / A1)."""
    return re.sub(r"\bAI\b", "SI", text)


def plain_name(check: dict, leg: str) -> str:
    return si_vocab(S.house_dashes(str(check[leg]["name"])))


def state_counts(grid: dict, leg: str) -> dict:
    """Per-check tally across the sixteen agencies under the four-state rule: pass, fail, partial,
    and not measured. `None` when the check is not a column on the cycle."""
    cols = {c["code"] for c in grid["columns"]}
    if leg not in cols:
        return {"pass": None, "fail": None, "partial": None, "not_measured": None}
    out = {"pass": 0, "fail": 0, "partial": 0, "not_measured": 0}
    for r in grid["rows"]:
        st = I.four_state([p["verdict"] for p in r["cells"][leg]["pages"]])
        out[{"pass": "pass", "fail": "fail", "partial": "partial",
             "could_not_measure": "not_measured"}[st]] += 1
    return out


def basics_rows(g: dict, grid: dict) -> list[dict]:
    """The four basics (Part A): plain name, the per-check counts, and whether the record Scores the
    check (a published requirement) or not (this project's reading)."""
    check = {r["leg"]: r for r in RB.check_rows(g)}
    scored = set(S.scored_legs(g))
    rows = []
    for leg in BASIC_LEGS:
        c = state_counts(grid, leg)
        rows.append({"leg": leg, "name": plain_name(check, leg), "counts": c,
                     "scored": leg in scored,
                     "bar": "a published requirement" if leg in scored else "this project's reading"})
    return rows


def passing_by_level(rows: list[dict]) -> dict:
    return {r["rung"]: r["passing_n"] for r in rows}


# ---------------------------------------------------------- the captions, cited to the deck (A3)

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\s*-\s*", "", s.lower())).strip()


def deck_caption_line(caption: str) -> int:
    """The 1-based line in the USAFacts deck md where `caption` appears, by a normalised match
    (the docling copy carries spacing artifacts like "machine -readable"). The build fails if a
    quoted caption cannot be located in the deck — A3's guarantee that every quotation is the
    source's words."""
    want = _norm(caption)
    lines = DECK_MD.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines, start=1):
        if want and want in _norm(ln):
            return i
    raise SystemExit(f"FATAL: caption not found verbatim in the deck (A3): {caption!r}")


# --------------------------------------------------------------------------------- figures

def ensure_docx_png(n: int) -> Path | None:
    """Render the drawn SVG to a PNG beside it for the Word route (typst embeds SVG directly; Word
    cannot). At 2x with whatever converter is on the machine; no network, nothing installed. Returns
    the PNG path, or None when there is no SVG or no converter (the Word file then keeps a
    placeholder, recorded in the build report — ADDENDUM 01 step 2)."""
    svg = FIGURES / f"{n}.svg"
    png = FIGURES / f"{n}.png"
    if not svg.exists():
        return png if png.exists() else None
    rsvg = shutil.which("rsvg-convert")
    if rsvg:
        r = subprocess.run([rsvg, "-z", "2", str(svg), "-o", str(png)],
                           capture_output=True, text=True)
        if r.returncode == 0 and png.exists():
            return png
    # typst can export an SVG to PNG too (bundle it in a one-line document).
    typst = shutil.which("typst")
    if typst:
        src = FIGURES / f"_{n}.typ"
        src.write_text(f'#set page(margin: 0pt, width: auto, height: auto)\n'
                       f'#image("{n}.svg")\n', encoding="utf-8")
        r = subprocess.run([typst, "compile", "--format", "png", "--ppi", "200",
                            str(src), str(png)], capture_output=True, text=True)
        src.unlink(missing_ok=True)
        if r.returncode == 0 and png.exists():
            return png
    return png if png.exists() else None


def figure_placed(n: int, docx_png: Path | None) -> dict:
    svg = FIGURES / f"{n}.svg"
    png = FIGURES / f"{n}.png"
    if svg.exists():
        placed, src = "svg", svg
    elif png.exists():
        placed, src = "png", png
    else:
        placed, src = "placeholder", None
    out = {"figure": n, "placed": placed,
           "svg": f"reports/figures/dn020/{n}.svg" if svg.exists() else None,
           "sha256": hashlib.sha256(src.read_bytes()).hexdigest() if src else None}
    if docx_png and docx_png.exists():
        out["docx_png"] = f"reports/figures/dn020/{n}.png"
        out["docx_png_sha256"] = hashlib.sha256(docx_png.read_bytes()).hexdigest()
    return out


def figure_block(n: int, caption: str, height_cm: float) -> str:
    """A pandoc Markdown fragment for figure `n`: a raw typst block drawing the SVG (preferred),
    the PNG, or a captioned placeholder frame. `render_pdf` runs with cwd=REPO."""
    svg = FIGURES / f"{n}.svg"
    png = FIGURES / f"{n}.png"
    if svg.exists():
        body = f'#align(center, image("reports/figures/dn020/{n}.svg", height: {height_cm}cm))'
    elif png.exists():
        body = f'#align(center, image("reports/figures/dn020/{n}.png", height: {height_cm}cm))'
    else:
        body = (f'#align(center, block(width: 80%, height: {height_cm}cm, '
                f'stroke: 0.6pt + rgb("#9aa0a6"), radius: 4pt, inset: 10pt, '
                f'fill: rgb("#fbfbfb"))[#align(center + horizon)[#text(fill: rgb("#555555"), '
                f'size: 8.5pt)[Figure {fig_word(n)} goes here.]]])')
    return "```{=typst}\n" + body + "\n```\n\n" + f"*Figure {fig_word(n)}. {caption}*"


# --------------------------------------------------------------------------------- the ICSP page

def figure3_caption(passing: dict) -> str:
    """Figure 3's caption carries the facts: where the agencies stand, from the counts."""
    a1, a2 = passing["usaf:access:1"], passing["usaf:access:2"]
    c1, c2 = passing["usaf:context:1"], passing["usaf:context:2"]
    return (f"Of sixteen agencies, {word(a1)} reach the first level of the Access track and "
            f"{word(a2)} the second; on the Context track {word(c1)} reach the first level and "
            f"{word(c2)} the second. None is higher, and the Evaluation track is not measured yet.")


def _track_sentence() -> str:
    parts = [f"{name} ({q})" for name, q in TRACK_QUESTIONS]
    return "The three tracks ask three plain questions: " + "; ".join(parts) + "."


def icsp_markdown(passing: dict, basics: list[dict], heights: dict) -> str:
    most_meet = max(basics, key=lambda b: b["counts"]["pass"])
    most_miss = max(basics, key=lambda b: b["counts"]["fail"])
    basics_bullet = (
        "- The basics come first, and no agency yet clears all three. The basic most agencies meet "
        f"is {ICSP_BASIC_PHRASE[most_meet['leg']]} ({word(most_meet['counts']['pass'])} of "
        f"sixteen); the one most miss is {ICSP_BASIC_PHRASE[most_miss['leg']]} "
        f"({word(most_miss['counts']['fail'])} of sixteen fail it).")
    L = [f"# {ICSP_TITLE}", "",
         "**What is it?** USAFacts, which gathers federal data at scale, has published a ladder for "
         f"making government data usable by {SI_FIRST_USE}. The ladder readies data for the "
         "assistants people now use to reach it. It has three tracks, three levels on each, and "
         "three basics that come first. " + _track_sentence(), "",
         figure_block(1, PICTURES[1]["caption"], heights[1]), "",
         "**How does it work?** The readiness diagnostic checks each agency from the outside, the "
         "way a member of the public's SI assistant would, making ordinary public web requests and "
         "reading what comes back. There are sixteen checks today.", "",
         "**Where do agencies stand?**", "",
         figure_block(3, figure3_caption(passing), heights[3]), "",
         basics_bullet,
        f"- On the Access track, can a program get the data, {word(passing['usaf:access:1'])} of "
        f"sixteen reach the first level and {word(passing['usaf:access:2'])} the second.",
        f"- On the Context track, can it understand what it got, {word(passing['usaf:context:1'])} "
        f"of sixteen reach the first level and {word(passing['usaf:context:2'])} the second.",
        "- The Evaluation track, has anyone checked the answers it gives, is not measured yet: that "
        "is a testing programme on its own, not something a public web request can see.", "",
        "**What does an agency do with it?** This is decision support. An agency sees its level on "
        "each track and the single next step up, read from published criteria rather than asserted, "
        "so money and staff time go where they raise the level, not to a grade. A check that could "
        "not be measured for an agency names its reason and never counts against it.", "",
        "**What does it cost to run?** The diagnostic makes ordinary public web requests, the kind "
        "any SI assistant makes for a member of the public, and puts no special load on a site.", "",
        "---", "", f"*{CREDIT}*", "", f"*{CLOSING}*", ""]
    return "\n".join(L)


# --------------------------------------------------------------------- the working-group explainer

def level_table(g: dict, nodes: dict, rows: list[dict], passing: dict) -> list[str]:
    """A7's single table: level, what USAFacts asks for (quoted caption), our checks (plain names),
    how many agencies pass every measured check, what the next step up asks for. The unmeasured
    levels close it in one row, so "not measured yet" appears once."""
    check = {r["leg"]: r for r in RB.check_rows(g)}
    label = {"usaf:access:1": "Access, level 1", "usaf:access:2": "Access, level 2",
             "usaf:context:1": "Context, level 1", "usaf:context:2": "Context, level 2"}
    out = ["| Level | What USAFacts asks for | Our checks | Agencies passing every check | "
           "What the next step up asks for |",
           "|---|---|---|---|---|"]
    for rid in ["usaf:access:1", "usaf:access:2", "usaf:context:1", "usaf:context:2"]:
        r = next(x for x in rows if x["rung"] == rid)
        cap = level_caption(nodes, rid)
        names = "; ".join(plain_name(check, c["leg"]) for c in r["checks"])
        nxt = NEXT_LEVEL.get(rid)
        nxt_cap = f"“{level_caption(nodes, nxt)}”" if nxt else ""
        out.append(f"| {label[rid]} | “{cap}” | {names} | "
                   f"{word(r['passing_n'])} of sixteen | {nxt_cap} |")
    out.append("| Access level 3, Context level 3, and all of Evaluation | not measured yet | | | |")
    return out


def basics_table(basics: list[dict]) -> list[str]:
    ask = {
        "A5": "Is the data page listed in the site's own index of pages?",
        "A6": "Does the page carry a built-in, machine-readable label naming it a dataset?",
        "D4": "Is the product listed in the agency's official data inventory?",
        "D1": "Are the terms of reuse stated on the page under a recognised name?",
    }
    out = ["| Basic check | What it asks | Agencies passing | The bar |", "|---|---|---|---|"]
    for b in basics:
        out.append(f"| {b['name']} | {ask[b['leg']]} | {word(b['counts']['pass'])} of sixteen | "
                   f"{b['bar']} |")
    return out


def explainer_markdown(g: dict, nodes: dict, rows: list[dict], passing: dict,
                       basics: list[dict], commit: str) -> str:
    a1 = passing["usaf:access:1"]
    L = [f"# {EXPLAINER_TITLE}", "",
         "## The bottom line", "",
         f"- USAFacts built a ladder for making federal data usable by {SI_FIRST_USE}: three "
         "tracks, three levels on each, and three basics that come first.",
         "- We put a working check behind each step, then measure sixteen federal statistical "
         "agencies against it from the outside, the way a member of the public's assistant would, "
         "and place each one on the ladder.",
         f"- {word(a1).capitalize()} of the sixteen reach the first level of the Access track; "
         "almost none has reached a higher level, and one whole track, checking the answers the "
         "data gives, is not measured yet.", "",
         "## The ladder", "",
         "The ladder has three tracks, each a short climb of three levels, with three basics that "
         "must hold before any level counts.", ""]
    for name, q in TRACK_QUESTIONS:
        L.append(f"- {name}: {q}")
    L += ["",
          "An agency climbs at its own pace, and the first level is worth having on its own. The "
          "three basics are that the data is open by default, that it can be found on the open web, "
          "and that it carries a clear licence on its page.", "",
          figure_block(1, PICTURES[1]["caption"], PICTURES[1]["height_cm"]), "",
          "## Where it comes from", "",
          figure_block(2, PICTURES[2]["caption"], PICTURES[2]["height_cm"]), "",
          "**FAIR, 2016.** A set of principles that data should be easy to find, to get, to combine "
          "and to reuse, by machines as much as by people.",
          "**The USAFacts guide, 2025.** USAFacts, a heavy user of federal data, set out four plain "
          "qualities it wanted: data that is accessible, understandable, accurate and open.",
          "**The USAFacts framework, August 2026.** The same four ideas, rebuilt as three tracks "
          "with levels borrowed from SLSA, a maturity ladder from the software industry where each "
          "level is a short list of things you can check. Accessible became the Access track, "
          "understandable became Context, accurate became Evaluation, and open moved down into the "
          "basics.",
          "**This diagnostic.** We put a working check behind each step, test the basics instead of "
          "taking them on trust, and mark the parts we cannot yet reach rather than scoring them.",
          "",
          "## One check, start to finish", "",
          "Take the simplest check to follow: does a data page announce, in a form built for "
          "machines, that it is a dataset with a name and a description? It needs only one request "
          "and follows no links. This is the check the earlier draft walked through, and it is "
          "still the plainest, so we keep it.", "",
          figure_block(4, PICTURES[4]["caption"], PICTURES[4]["height_cm"]), "",
          "**What we ask.** Does the page carry a built-in, machine-readable label that says it is "
          "a dataset, with a name and a description?",
          "**Where we look.** At the data page itself, reading the label the page sends, without "
          "running any of the page's scripts.",
          "**What counts as a pass.** Every data page we looked at carries that label, naming the "
          "dataset and describing it.",
          "**What the four results mean.** A check comes back as a pass, a partial pass (some pages "
          "carry the label, some do not), a fail, or not measured, when we could not read the page "
          "and the reason is recorded. Not measured is never a fail.", "",
          "## The basics, before the ladder", ""]
    L += basics_table(basics)
    L += ["",
          "A basic is passed only when every one of the agency's pages meets it; a page we could "
          "not read is left out, never counted as a fail. A check marked a published requirement "
          "rests on USAFacts' own words; one marked this project's reading is a bar we set from "
          "them.", "",
          "## The ladder, level by level", ""]
    L += level_table(g, nodes, rows, passing)
    L += ["",
          "A count is read level by level on its own, not as a climb, so a higher level can show "
          "more agencies than a lower one; a check we could not measure for an agency is left out "
          "of that level for it, never a fail.", "",
          "## What we kept, what we changed", "",
          "Kept, as USAFacts wrote it: the three tracks and their names, the three levels, the "
          "three basics, the ladder shape, and the idea that an agency places itself and decides "
          "where to invest next.",
          "Changed: we test the basics instead of taking them on trust, because a basic that is "
          "only claimed cannot anchor a level.",
          "Changed: every check has a written rule for what counts as a pass, so two agencies "
          "cannot claim the same level for different reasons.",
          "Changed: a level is reported per check, and an agency's place is the highest level where "
          "every check we could measure passes; a check we could not measure is left out, never a "
          "fail.",
          "Changed: the Evaluation track is shown empty and said to be empty, because building its "
          "test is a programme of its own that this diagnostic does not attempt.", "",
          "## For more", "",
          "The full check-by-check sheet, the one-page roll-up of this ladder, and the one-page "
          "summary for the Council are available on request.", "",
          "---", "", f"*{CLOSING}*", "",
          f"*Built by {GENERATOR} from the framework record at commit {commit}.*", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------------- docx

def _add_image_or_placeholder(doc, n: int, caption: str, docx_png: Path | None, height_cm: float):
    from docx.shared import Inches, Pt, RGBColor as DRGB
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    GREY = DRGB(0x55, 0x55, 0x55)
    if docx_png and docx_png.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(docx_png), height=Inches(height_cm / 2.54))
    else:
        t = doc.add_table(rows=1, cols=1)
        t.style = "Table Grid"
        cell = t.rows[0].cells[0]
        cell.width = Inches(5.5)
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(f"Figure {fig_word(n)} goes here.")
        r.font.name = B.FONT
        r.font.size = Pt(9)
        r.font.italic = True
        r.font.color.rgb = GREY
    capp = doc.add_paragraph()
    capp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = capp.add_run(f"Figure {fig_word(n)}. {caption}")
    cr.font.name = B.FONT
    cr.font.size = Pt(9)
    cr.font.italic = True
    cr.font.color.rgb = GREY


_MD_FIG = re.compile(r"^```\{=typst\}")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _docx_from_markdown(md: str, path: Path, *, figures: dict, body_pt: float) -> None:
    """Render the document's Markdown to Word. Figure blocks become a raster or a placeholder frame;
    headings, bold leads, tables and paragraphs render in the house font and colours."""
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor as DRGB
    BLACK, GREY = DRGB(0x00, 0x00, 0x00), DRGB(0x55, 0x55, 0x55)
    doc = Document()
    doc.styles["Normal"].font.name = B.FONT
    doc.styles["Normal"].font.size = Pt(body_pt)
    sec = doc.sections[0]
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
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            cap_line = lines[k] if k < len(lines) else ""
            m = re.search(r"Figure (\w+)\.\s*(.*?)\*?$", cap_line)
            num = {v: kk for kk, v in {1: "one", 2: "two", 3: "three", 4: "four"}.items()}.get(
                m.group(1).lower() if m else "", None)
            if num is not None:
                fi = figures[num]
                _add_image_or_placeholder(doc, num, fi["caption"], fi["docx_png"], fi["height_cm"])
            i = k + 1
            continue
        if ln.startswith("# "):
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
            run(p, ln[2:], bold=True, size=body_pt + 5)
        elif ln.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(3)
            run(p, ln[3:], bold=True, size=body_pt + 2)
        elif ln.startswith("|"):
            tbl = [ln]
            while i + 1 < len(lines) and lines[i + 1].startswith("|"):
                i += 1
                tbl.append(lines[i])
            trows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tbl
                     if set(r.strip()) - set("|-: ")]
            if trows:
                cols = max(len(r) for r in trows)
                t = doc.add_table(rows=len(trows), cols=cols)
                t.style = "Table Grid"
                for ri, rr in enumerate(trows):
                    for ci in range(cols):
                        cv = rr[ci] if ci < len(rr) else ""
                        cp = t.rows[ri].cells[ci].paragraphs[0]
                        rich(cp, cv, size=body_pt - 1)
                        if ri == 0:
                            for rn in cp.runs:
                                rn.font.bold = True
        elif ln.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            rich(p, ln[2:], size=body_pt)
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

def render_pdf(md_path: Path, pdf_path: Path, *, body_pt: float, margin_y: float) -> None:
    header = ("#set text(hyphenate: false)\n"
              "#show figure: set block(breakable: true)\n"
              "#show heading: set block(above: 0.7em, below: 0.4em)\n"
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


# --------------------------------------------------------------------------------- the checks

#: The words A4 keeps out of the project's prose, on top of DN-016's list (which
#: `D.banned_hits_prose` enforces: scan/probe/crawl/audit/unmeasurable/ruling). Phrases and single
#: words; case-insensitive; USAFacts' quoted captions are removed before this runs.
_A4_BANNED = re.compile(
    r"\bsensors?\b|\bmeasurement specifications?\b|\bcycle of record\b"
    r"|\bleast privileged clients?\b|\bmarkup\b|\brung-by-rung\b", re.IGNORECASE)

#: Internal codes, record ids, script paths and file names that must not reach the body of either
#: document. Uppercase check legs (A6, D1, F4), colon record ids, internal doc codes, tailoring
#: codes, file names and repository paths. The explainer's one allowed footer line is removed
#: before this runs.
_CODE_PATTERNS = [
    re.compile(r"\b[A-F][0-9]{1,2}\b"),
    re.compile(r"\b(?:usaf|spec|crit|aiready):[\w:.-]+"),
    re.compile(r"\b(?:DN|DD|AD|PL|AR)-[0-9]{2,3}\b"),
    re.compile(r"\bT[1-6]\b"),
    re.compile(r"\b\S+\.(?:py|json|jsonl|svg|png|md|ya?ml)\b"),
    re.compile(r"\b(?:scripts|reports|state|framework|docs|cc_tasks)/\S+"),
]


def captions_in(g: dict, nodes: dict) -> list[str]:
    """Every USAFacts level caption the documents may quote — the quoted zone (A3), removed before
    the vocabulary scan so USAFacts' own "agents can crawl" does not trip the DN-016 list."""
    return [level_caption(nodes, n["id"]) for n in nodes.values() if "UsafactsLevel" in n["labels"]]


def project_prose(md: str, captions: list[str], *, drop_lines: list[str] = ()) -> str:
    """The text the vocabulary scan runs over: the document's prose with figure blocks removed, the
    verbatim USAFacts captions removed, and any explicitly allowed line (the explainer footer)
    removed."""
    out, in_fig = [], False
    for ln in md.split("\n"):
        if ln.startswith("```"):
            in_fig = not in_fig
            continue
        if in_fig or ln in drop_lines:
            continue
        out.append(ln)
    text = "\n".join(out)
    for cap in captions:
        text = text.replace(cap, " ")
    return text


def a4_banned_hits(prose: str) -> list[str]:
    return [m.group(0) for m in _A4_BANNED.finditer(prose)]


def code_hits(body_wo_footer: str) -> list[str]:
    hits = []
    for pat in _CODE_PATTERNS:
        hits += [m.group(0) for m in pat.finditer(body_wo_footer)]
    return sorted(set(hits))


def si_expansion_hits(full_text: str) -> list[str]:
    """Every expansion of SI in the text; the build fails on any that is not "superintelligence"
    (ADDENDUM 02)."""
    return [g for g in re.findall(r"\bSI \(([^)]*)\)", full_text) if g.strip() != "superintelligence"]


def statistical_information_hits(full_text: str) -> bool:
    return "statistical information" in full_text.lower()


_SENT = re.compile(r"(?<=[.?!])\s+")


def repeated_sentences(prose: str) -> list[str]:
    """Any sentence of real length that appears twice in the document's prose (Part D, expected
    none). Runs over paragraph prose, not headings, bullets or table rows."""
    seen, dupes = {}, []
    for raw in prose.split("\n"):
        ln = raw.strip()
        if not ln or ln.startswith(("#", "-", "|", "*")):
            continue
        for s in _SENT.split(ln):
            key = re.sub(r"\s+", " ", s.strip().lower())
            if len(key) < 30:
                continue
            seen[key] = seen.get(key, 0) + 1
    for key, n in seen.items():
        if n > 1:
            dupes.append(key)
    return dupes


def longest_sentence(prose: str) -> str:
    best = ""
    for raw in prose.split("\n"):
        ln = raw.strip()
        if not ln or ln.startswith(("#", "|")):
            continue
        for s in _SENT.split(ln.lstrip("-* ")):
            s = s.strip()
            if len(s) > len(best):
                best = s
    return best


def run_text_checks(name: str, md: str, pdf_txt: str, docx_txt: str, captions: list[str],
                    *, footer_line: str | None, failures: list[str]) -> dict:
    prose = project_prose(md, captions, drop_lines=[footer_line] if footer_line else [])
    body_wo_footer = md if not footer_line else md.replace(footer_line, " ")
    all_texts = {"md": md, "pdf": pdf_txt, "docx": docx_txt}

    banned = D.banned_hits_prose(prose) + [(w, "") for w in a4_banned_hits(prose)]
    codes = code_hits(project_prose(body_wo_footer, captions))
    dashes = RB.dash_hits(prose)
    repeats = repeated_sentences(prose)
    si_exp = {k: si_expansion_hits(v) for k, v in all_texts.items()}
    stat_info = {k: statistical_information_hits(v) for k, v in all_texts.items()}

    checks = {
        "banned_vocabulary": banned,
        "codes_paths_filenames": codes,
        "dashes": dashes,
        "repeated_sentences": repeats,
        "si_expansions_not_superintelligence": si_exp,
        "statistical_information_present": stat_info,
        "longest_sentence": longest_sentence(prose),
    }
    if banned:
        failures.append(f"{name}: banned_vocabulary")
    if codes:
        failures.append(f"{name}: codes_paths_filenames {codes}")
    if dashes:
        failures.append(f"{name}: dashes")
    if repeats:
        failures.append(f"{name}: repeated_sentences")
    if any(si_exp.values()):
        failures.append(f"{name}: si_expansions_not_superintelligence")
    if any(stat_info.values()):
        failures.append(f"{name}: statistical_information_present")
    return checks


# --------------------------------------------------------------------------------- build

#: The ICSP fit ladder: (body_pt, figure-1 height cm, figure-3 height cm). The first setting whose
#: PDF is one page wins; the build report and the RESULT name it.
ICSP_FIT = [(9.5, 3.0, 2.6), (9.5, 2.7, 2.4), (9.0, 2.6, 2.3), (9.0, 2.4, 2.1),
            (8.5, 2.4, 2.1), (8.5, 2.2, 1.9), (8.0, 2.2, 1.9), (8.0, 2.0, 1.7)]


def build(out: Path = OUT, *, measure: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    grid = I.load_grid(I.load_config())
    cycle = load_cycle()
    nodes = usaf_nodes(g)
    rows = R.rung_rows(g, grid)
    passing = passing_by_level(rows)
    basics = basics_rows(g, grid)
    commit = record_commit()
    captions = captions_in(g, nodes)

    # The docx rasters (ADDENDUM 01 step 2): rendered once, reused by both documents.
    docx_png = {n: ensure_docx_png(n) for n in (1, 2, 3, 4)}

    # ---- the ICSP page, fit to one page ----
    icsp_md_path = out / f"{ICSP_STEM}.md"
    icsp_pdf = out / f"{ICSP_STEM}.pdf"
    chosen = None
    for body_pt, h1, h3 in (ICSP_FIT if measure else ICSP_FIT[:1]):
        heights = {1: h1, 3: h3}
        icsp_md = icsp_markdown(passing, basics, heights)
        icsp_md_path.write_text(icsp_md, encoding="utf-8")
        render_pdf(icsp_md_path, icsp_pdf, body_pt=body_pt, margin_y=0.8)
        if not measure:
            chosen = (body_pt, h1, h3, None)
            break
        pages = pdf_pages(icsp_pdf)
        if pages == 1:
            chosen = (body_pt, h1, h3, pages)
            break
        chosen = (body_pt, h1, h3, pages)
    icsp_body_pt, icsp_h1, icsp_h3, icsp_pages = chosen
    icsp_md = icsp_md_path.read_text(encoding="utf-8")
    icsp_figs = {
        1: {"caption": PICTURES[1]["caption"], "docx_png": docx_png[1], "height_cm": icsp_h1},
        3: {"caption": figure3_caption(passing), "docx_png": docx_png[3], "height_cm": icsp_h3},
    }
    icsp_docx = out / f"{ICSP_STEM}.docx"
    _docx_from_markdown(icsp_md, icsp_docx, figures=icsp_figs, body_pt=10.0)

    # ---- the explainer ----
    expl_md = explainer_markdown(g, nodes, rows, passing, basics, commit)
    expl_md_path = out / f"{EXPLAINER_STEM}.md"
    expl_md_path.write_text(expl_md, encoding="utf-8")
    expl_pdf = out / f"{EXPLAINER_STEM}.pdf"
    render_pdf(expl_md_path, expl_pdf, body_pt=11.0, margin_y=1.4)
    expl_figs = {n: {"caption": PICTURES[n]["caption"] if n != 3 else figure3_caption(passing),
                     "docx_png": docx_png[n], "height_cm": PICTURES[n]["height_cm"]}
                 for n in (1, 2, 3, 4)}
    expl_docx = out / f"{EXPLAINER_STEM}.docx"
    _docx_from_markdown(expl_md, expl_docx, figures=expl_figs, body_pt=11.0)

    # ---- captions cited to the deck (A3) ----
    quoted = []
    for rid in ["usaf:access:1", "usaf:access:2", "usaf:context:1", "usaf:context:2",
                "usaf:access:3", "usaf:context:3"]:
        cap = level_caption(nodes, rid)
        quoted.append({"caption": cap, "deck_md_line": deck_caption_line(cap)})

    # ---- the text checks ----
    icsp_pdf_txt = pdf_text(icsp_pdf) if measure else ""
    icsp_docx_txt = RB.docx_text(icsp_docx)
    expl_pdf_txt = pdf_text(expl_pdf) if measure else ""
    expl_docx_txt = RB.docx_text(expl_docx)
    expl_footer = f"Built by {GENERATOR} from the framework record at commit {commit}."

    failures: list[str] = []
    icsp_checks = run_text_checks("icsp", icsp_md, icsp_pdf_txt, icsp_docx_txt, captions,
                                  footer_line=None, failures=failures)
    expl_checks = run_text_checks("explainer", expl_md, expl_pdf_txt, expl_docx_txt, captions,
                                  footer_line=expl_footer, failures=failures)

    expl_pages = pdf_pages(expl_pdf) if measure else None
    if measure:
        if icsp_pages != 1:
            failures.append(f"icsp is {icsp_pages} pages, must be 1")
        if expl_pages is None or not (4 <= expl_pages <= 6):
            failures.append(f"explainer is {expl_pages} pages, must be 4 to 6")

    figures_report = {
        "icsp": [figure_placed(n, docx_png[n]) for n in (1, 3)],
        "explainer": [figure_placed(n, docx_png[n]) for n in (1, 2, 3, 4)],
    }
    # Figure 3 must not contradict the counts (ADDENDUM 01 step 3). The picture shows most figures
    # on the ground and the first level, a few on the second, none on the third, a few on the
    # basics. It is NOT misleading while the first Access level holds more agencies than the second
    # (so the crowd is low on the ladder) and the second holds only a few (the warned-against case
    # is "the counts put most agencies on the second level"). Recorded, not silently assumed.
    fig3_not_misleading = (passing["usaf:access:1"] >= passing["usaf:access:2"]
                           and passing["usaf:access:2"] <= 3
                           and passing["usaf:context:2"] <= 3)
    fig3_consistent = fig3_not_misleading
    figures_report["figure3_counts"] = {
        "access_1": passing["usaf:access:1"], "access_2": passing["usaf:access:2"],
        "context_1": passing["usaf:context:1"], "context_2": passing["usaf:context:2"],
        "basics_pass": {b["leg"]: b["counts"]["pass"] for b in basics},
        "not_misleading": bool(fig3_consistent),
    }

    def prod(md_path, docx_path, pdf_path, pages):
        md = md_path.read_text(encoding="utf-8")
        md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
        return [
            {"name": md_path.name, "md_sha256": md_sha},
            {"name": docx_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest()},
            {"name": pdf_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(), "pages": pages},
        ]

    report = {
        "generated_by": GENERATOR, "task": TASK, "cycle": cycle["cycle"],
        "record_commit": commit,
        "icsp_fit": {"body_pt": icsp_body_pt, "figure1_cm": icsp_h1, "figure3_cm": icsp_h3,
                     "pages": icsp_pages},
        "documents": {
            "icsp": prod(icsp_md_path, icsp_docx, icsp_pdf, icsp_pages),
            "explainer": prod(expl_md_path, expl_docx, expl_pdf, expl_pages),
        },
        "basics": [{"leg": b["leg"], "name": b["name"], "counts": b["counts"],
                    "scored": b["scored"], "bar": b["bar"]} for b in basics],
        "passing_by_level": {rid: passing[rid] for rid in passing},
        "captions_cited": quoted,
        "figures": figures_report,
        "checks": {"icsp": icsp_checks, "explainer": expl_checks,
                   "explainer_pages": expl_pages},
        "failures": failures,
    }
    (out / "build_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("FATAL: build checks failed: " + "; ".join(failures) + "\n"
                         + json.dumps(report["checks"], indent=1, ensure_ascii=False)[:3500])
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-measure", action="store_true")
    a = ap.parse_args(argv)
    rep = build(measure=not a.no_measure)
    print(json.dumps({"icsp_fit": rep["icsp_fit"], "documents": rep["documents"],
                      "basics": rep["basics"], "passing_by_level": rep["passing_by_level"],
                      "figures": rep["figures"], "checks": rep["checks"],
                      "failures": rep["failures"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
