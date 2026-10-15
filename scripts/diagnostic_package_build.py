#!/usr/bin/env python3
"""Build the readiness diagnostic package from the graph: one Markdown source and, from the same
content, a Word document and a PowerPoint deck. No PDF (DN-016 ruling 5). **Zero spend.**

`cc_tasks/2026-10-15_readiness_diagnostic_package.md` Part D. One script, one query: the
dictionary content comes from the framework record's MeasurementSpec nodes (the `rf_*` fields
Part A wrote), the roster from the registered scan frame, the rung-two listing from the record's
Tool/Precondition nodes, the preface from `reports/diagnostic/preface_source.yaml` with every
number resolved from the record/frame/cycle and checked against the token's stated value
(`scripts/diagnostic_package.py`). Nothing is read from the RULE-*.yaml or a prior render.

Products (all under `reports/diagnostic/`):
* `READINESS_DIAGNOSTIC.md` — the canonical Markdown source; its sha256 is recorded in the build
  report beside each product it produced (the pattern of `scripts/dcat_brief_build.py`).
* `READINESS_DIAGNOSTIC.docx` — Calibri; preface; the dictionary, one check per page, the nine
  DN-016 §3 fields as labelled lines (A4/A11 marked declarations read but not scored, A12 under
  review); roster; rung-two listing; what comes next.
* `READINESS_DIAGNOSTIC.pptx` — Calibri, white background, black/grey text, one orange accent;
  the preface over two slides, the roster, the ladder, the sixteen checks one slide per criterion
  group, the rung-two listing, and what comes next. Speaker notes on each check slide carry the
  where-we-look and pass definition.

    /opt/anaconda3/bin/python3 scripts/diagnostic_package_build.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import diagnostic_package as D  # noqa: E402

GENERATOR = "scripts/diagnostic_package_build.py"
TASK = "cc_tasks/2026-10-15_readiness_diagnostic_package.md"
OUT = REPO / "reports" / "diagnostic"
PREFACE_SOURCE = OUT / "preface_source.yaml"
PARAMS = REPO / "assessment" / "harness" / "scan" / "params.yaml"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"

CRITERION_NAME = {"A": "ACCESSIBLE", "B": "UNDERSTANDABLE", "C": "ACCURATE", "D": "OPEN",
                  "E": "TEVV loop", "F": "release engineering", "G": "FSS-derived constructs"}
#: A4 and A11 are declarations read but not scored; A12 is under review (DN-016 §3, Part D).
DECLARATION_LEGS = {"A4", "A11-declared"}
UNDER_REVIEW_LEGS = {"A12"}

#: The deck's one orange, and the greys and black text may use. The font/colour test holds the
#: .pptx to exactly these plus Calibri.
from pptx.dml.color import RGBColor  # noqa: E402

ORANGE = RGBColor(0xC2, 0x56, 0x00)
BLACK = RGBColor(0x00, 0x00, 0x00)
GREY = RGBColor(0x55, 0x55, 0x55)
LIGHT_GREY = RGBColor(0x80, 0x80, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ALLOWED_RGB = {str(c) for c in (ORANGE, BLACK, GREY, LIGHT_GREY)}
FONT = "Calibri"


# --------------------------------------------------------------------- values and token resolve

def compute_values() -> dict:
    """The numbers the preface quotes, from the record, the frame and the cycle of record. Each
    is what a {{result:NAME:value}} token in preface_source.yaml must agree with."""
    params = yaml.safe_load(PARAMS.read_text(encoding="utf-8"))["manners"]
    frame = D.load_frame()
    cycle = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))["snapshot_cycle"]
    state = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    robots = {f.get("target_doc_id") for f in state["findings_detail"]
              if "robots_disallowed" in (f.get("reason") or "")}
    rps = params["requests_per_second_per_host"]
    return {
        "checks_total": len(D.instrument_specs()),
        "bodies_total": frame["tier_a_agencies"],
        "flagships_total": frame["tier_c_hosts"],
        "surfaces_total": frame["surfaces"],
        "rate_per_second_per_host": int(rps) if float(rps).is_integer() else rps,
        "crawl_delay_ceiling_s": params["crawl_delay_max_s"],
        "surfaces_robots_kept_out": len(robots),
        "cycle": cycle,
        "user_agent": params["user_agent"],
    }


_TOKEN = re.compile(r"\{\{result:([A-Za-z0-9_]+):([^}]*)\}\}")


def resolve_tokens(text: str, values: dict) -> tuple[str, list[str]]:
    """Replace each {{result:NAME:value}} with the computed value, refusing if NAME is unknown or
    the stated value disagrees with the computed one (the number-drift guard)."""
    used = []

    def sub(m):
        name, stated = m.group(1), m.group(2)
        if name not in values:
            raise SystemExit(f"FATAL: preface token {name!r} has no computed value")
        got = str(values[name])
        if stated != got:
            raise SystemExit(f"FATAL: preface token {name}: stated {stated!r} != computed {got!r} "
                             "(number drift — fix the preface or the computation)")
        used.append(name)
        return got

    return _TOKEN.sub(sub, text), used


def load_preface(values: dict) -> dict:
    """The preface source with every token resolved and the user-agent validated against the
    configuration line it quotes."""
    pf = yaml.safe_load(PREFACE_SOURCE.read_text(encoding="utf-8"))
    ua = pf["user_agent"]
    config_line = PARAMS.read_text(encoding="utf-8").splitlines()[ua["config_line"] - 1]
    if ua["string"] not in config_line:
        raise SystemExit(f"FATAL: preface user-agent {ua['string']!r} is not on "
                         f"{ua['config_file']}:{ua['config_line']} — got {config_line!r}")
    if ua["string"] != values["user_agent"]:
        raise SystemExit("FATAL: preface user-agent != the harness's configured user_agent")
    used = []

    def R(v):
        if isinstance(v, str):
            r, u = resolve_tokens(v, values)
            used.extend(u)
            return r
        if isinstance(v, list):
            return [R(x) for x in v]
        return v

    out = {k: R(v) for k, v in pf.items() if k != "user_agent"}
    out["user_agent"] = ua
    out["_tokens_used"] = sorted(set(used))
    return out


# ---------------------------------------------------------------------------------- the content

def _partial_fail_nm(s: dict) -> str:
    return (f"Partial — {s['rf_partial']} Fail — {s['rf_fail']} "
            f"Not measured — {s['rf_not_measured']}")


def _how_counts(leg: str, state: str) -> str:
    """How a check's result counts, in plain words — so the standing of a check is explicit and a
    'Fail' on a check the project does not score is not mistaken for a finding (the hostile
    reader's recurring objection; DN-015 §3 and §5)."""
    if leg in DECLARATION_LEGS:
        return "A declaration: this records what the agency states, read but not scored."
    if leg in UNDER_REVIEW_LEGS:
        return "Under review: this check is not scored yet."
    if state == "specified":
        return "Scored: a pass or fail here is a finding about the agency."
    if state == "project_defined":
        return ("Shown for transparency, not scored as a finding about the agency: at least one "
                "part of this check rests on a rule this project chose, not a published standard.")
    if state == "invalid":
        return ("Not scored as a finding about the agency: this version of the check measures "
                "something other than its question and is being revised.")
    return "Not scored."


def dict_entries(vocab: dict) -> list[dict]:
    """The sixteen dictionary entries, each with its nine DN-016 §3 fields and its marker."""
    out = []
    for s in D.instrument_specs():
        marker = ("a declaration, read but not scored" if s["leg"] in DECLARATION_LEGS
                  else "under review, not scored yet" if s["leg"] in UNDER_REVIEW_LEGS else None)
        scored = marker is None and s["rf_state"] == "specified"
        # The hostile reader's standing objection: a 'Fail' printed next to an agency for a check
        # the project does not score reads as a finding however much fine print follows it. So a
        # non-scored check (project_defined, invalid, a declaration, under review) shows NO
        # pass/partial/fail verdict words — it states plainly that it produces no finding (DN-015
        # §5: such checks are not shown as findings about a publisher). A scored check keeps the
        # full four-state breakdown, where a pass or fail really is a finding.
        if scored:
            outcome = [("What passing looks like", s["rf_pass"]),
                       ("What partial, fail and not measured look like", _partial_fail_nm(s))]
        else:
            outcome = [("How a result is reported",
                        "This check is not scored as a finding about your agency: it yields no "
                        "pass, partial or fail about you. What it examines is described under "
                        "'The question' and 'Where we look' above.")]
        out.append({
            "state": s["rf_state"], "how_counts": _how_counts(s["leg"], s["rf_state"]),
            "scored": scored, "outcome": outcome,
            "leg": s["leg"], "criterion": s["leg"][0], "marker": marker,
            "plain_name": D.rendered_plain_name(s, vocab) or "(no short name)",
            "question": s["rf_question"], "where_we_look": s["rf_where_we_look"],
            "what_client_does": s["rf_what_client_does"],
            "why_it_matters": s["rf_why_it_matters"], "who_else": s["rf_who_else"],
            "rung_two_changes": s["rf_rung_two_changes"],
            "where_we_look_raw": s["rf_where_we_look"],
            "pass_raw": s["rf_pass"] if scored else "(not scored; no verdict)",
        })
    return out


WHAT_NEXT = [
    ("The access check", "Whether the host answers an anonymous, identified client at all — the "
     "FAIR letter's first rung (A1 and A1.1). It is specified and not yet run; it is its own task."),
    ("The first measured rung-two cycle", "The same checks run by the public client registered as "
     "any member of the public registers, presenting a key obtained by open registration. The "
     "surfaces that take a key are listed here; no rung-two result is shown before a measured "
     "cycle exists. It is its own task, with its own pre-registration."),
]


# ------------------------------------------------------------------------------------- markdown

def build_markdown(values: dict, preface: dict, entries: list, roster: list, rung2: list,
                   vocab: dict) -> str:
    L = [f"# {preface['title']}", "",
         f"Generated by `{GENERATOR}` from the framework record, the measurement frame and the cycle of "
         f"record `{values['cycle']}`, under DN-016. The run is a *readiness diagnostic*; its unit "
         "is a *check*; the client that runs it is the *public client*.", "",
         "## The public client, and what it never does", "", preface["what_it_is"], ""]
    L += ["**How it behaves.**", ""] + [f"- {x}" for x in preface["how_it_behaves"]]
    L += ["", "**What it never does.**", ""] + [f"- {x}" for x in preface["what_it_never_does"]]
    L += ["", f"It identifies itself as `{preface['user_agent']['string']}` "
          f"(`{preface['user_agent']['config_file']}` line {preface['user_agent']['config_line']}).", ""]
    L += ["**The four states.**", "", preface["four_states_note"], "",
          "**The two rungs.**", "", preface["two_rungs_note"], "",
          "**What this is not.**", "", preface["what_it_is_not"], "",
          "**Not a league table.**", "", preface["not_a_league_table"], "",
          "**A few terms.**", ""]
    for gl in preface["glossary"]:
        L.append(f"- **{gl['term']}** — {gl['plain']}")
    L += ["", "## The dictionary: sixteen checks", ""]
    for e in entries:
        head = f"### {e['plain_name']}"
        if e["marker"]:
            head += f"  — {e['marker']}"
        L += [head, "",
              f"- **How this check counts.** {e['how_counts']}",
              f"- **The question.** {e['question']}",
              f"- **Where we look.** {e['where_we_look']}",
              f"- **What the client does.** {e['what_client_does']}"]
        L += [f"- **{label}.** {text}" for label, text in e["outcome"]]
        L += [f"- **Why it matters.** {e['why_it_matters']}",
              f"- **Who else runs this check.** {e['who_else']}",
              f"- **What rung two changes.** {e['rung_two_changes']}", ""]
    L += ["## The roster", "",
          f"The {values['bodies_total']} statistical bodies the diagnostic measures, with the "
          f"{values['flagships_total']} reference hosts (flagships) shown beside them, in the order "
          "the frame holds them. Where we look is each body's home surface and the machine "
          "locations recorded for it.", "",
          "| Body | Host | Role | Surfaces | Where we look (home) |",
          "|---|---|---|---|---|"]
    for b in roster:
        role = "reference host (flagship)" if b["flagship"] else "statistical body"
        L.append(f"| {b['body']} | {b['host']} | {role} | {len(b['surfaces'])} | {b['home'] or '—'} |")
    L += ["", "## The rung-two listing", "",
          "Every roster surface that could take a key, with whether a key is required and whether "
          "registration is open to the public, from the record's tool and precondition nodes. "
          "Where the record is silent the cell reads \"to be confirmed\"; nothing is inferred.", "",
          "| Body | Surface | Key required | Registration open | Source |",
          "|---|---|---|---|---|"]
    for r in rung2:
        L.append(f"| {r['body']} | {r['surface']} | {r['key_required']} | "
                 f"{r['registration_open']} | {r['source']} |")
    L += ["", "## What comes next", ""]
    for title, body in WHAT_NEXT:
        L.append(f"- **{title}.** {body}")
    L.append("")
    return "\n".join(L).rstrip() + "\n"


# ----------------------------------------------------------------------------------------- docx

def _docx_set_font(run, *, bold=False, size=None):
    run.font.name = FONT
    run.font.bold = bold
    if size is not None:
        from pptx.util import Pt as _Pt  # noqa
    return run


def build_docx(values: dict, preface: dict, entries: list, roster: list, rung2: list, path: Path) -> dict:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_BREAK
    doc = Document()
    doc.styles["Normal"].font.name = FONT
    doc.styles["Normal"].font.size = Pt(10.5)

    def para(text, *, bold=False, size=10.5, style=None):
        p = doc.add_paragraph(style=style)
        r = p.add_run(text)
        r.font.name = FONT
        r.font.bold = bold
        r.font.size = Pt(size)
        return p

    def field(p, label, body):
        r = p.add_run(f"{label} ")
        r.font.name = FONT
        r.font.bold = True
        r.font.size = Pt(10.5)
        r2 = p.add_run(body)
        r2.font.name = FONT
        r2.font.size = Pt(10.5)

    para(preface["title"], bold=True, size=16)
    para(preface["what_it_is"])
    para("How it behaves", bold=True, size=12)
    for x in preface["how_it_behaves"]:
        para(x, style="List Bullet")
    para("What it never does", bold=True, size=12)
    for x in preface["what_it_never_does"]:
        para(x, style="List Bullet")
    para(f"It identifies itself as {preface['user_agent']['string']} "
         f"({preface['user_agent']['config_file']} line {preface['user_agent']['config_line']}).")
    para("The four states", bold=True, size=12)
    para(preface["four_states_note"])
    para("The two rungs", bold=True, size=12)
    para(preface["two_rungs_note"])
    para("What this is not", bold=True, size=12)
    para(preface["what_it_is_not"])
    para("Not a league table", bold=True, size=12)
    para(preface["not_a_league_table"])
    para("A few terms", bold=True, size=12)
    for gl in preface["glossary"]:
        field(doc.add_paragraph(style="List Bullet"), f"{gl['term']} —", gl["plain"])

    pages = 1
    head_fields = [("How this check counts.", "how_counts"), ("The question.", "question"),
                   ("Where we look.", "where_we_look"), ("What the client does.", "what_client_does")]
    tail_fields = [("Why it matters.", "why_it_matters"), ("Who else runs this check.", "who_else"),
                   ("What rung two changes.", "rung_two_changes")]
    for e in entries:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        pages += 1
        h = e["plain_name"] + (f"  — {e['marker']}" if e["marker"] else "")
        para(h, bold=True, size=13)
        for label, key in head_fields:
            field(doc.add_paragraph(), label, e[key])
        for label, text in e["outcome"]:
            field(doc.add_paragraph(), f"{label}.", text)
        for label, key in tail_fields:
            field(doc.add_paragraph(), label, e[key])

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    pages += 1
    para("The roster", bold=True, size=13)
    t = doc.add_table(rows=1, cols=5)
    for i, h in enumerate(["Body", "Host", "Role", "Surfaces", "Where we look (home)"]):
        c = t.rows[0].cells[i].paragraphs[0].add_run(h)
        c.font.bold = True
        c.font.name = FONT
    for b in roster:
        cells = t.add_row().cells
        vals = [b["body"], b["host"],
                "reference host (flagship)" if b["flagship"] else "statistical body",
                str(len(b["surfaces"])), b["home"] or "—"]
        for i, v in enumerate(vals):
            rr = cells[i].paragraphs[0].add_run(v)
            rr.font.name = FONT
            rr.font.size = Pt(9)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    pages += 1
    para("The rung-two listing", bold=True, size=13)
    para("Where the record is silent the cell reads \"to be confirmed\"; nothing is inferred.",
         size=9)
    t2 = doc.add_table(rows=1, cols=5)
    for i, h in enumerate(["Body", "Surface", "Key required", "Registration open", "Source"]):
        c = t2.rows[0].cells[i].paragraphs[0].add_run(h)
        c.font.bold = True
        c.font.name = FONT
    for r in rung2:
        cells = t2.add_row().cells
        for i, v in enumerate([r["body"], r["surface"], r["key_required"],
                               r["registration_open"], r["source"]]):
            rr = cells[i].paragraphs[0].add_run(v)
            rr.font.name = FONT
            rr.font.size = Pt(8)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    pages += 1
    para("What comes next", bold=True, size=13)
    for title, body in WHAT_NEXT:
        field(doc.add_paragraph(style="List Bullet"), f"{title}.", body)
    doc.save(str(path))
    return {"pages": pages}


def docx_text(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for tb in doc.tables:
        for row in tb.rows:
            parts += [c.text for c in row.cells]
    return "\n".join(parts)


# ----------------------------------------------------------------------------------------- pptx

def _pptx_textframe(tf, lines: list[tuple], *, base_size=14):
    """lines: list of (text, bold, color, size_delta)."""
    from pptx.util import Pt
    tf.word_wrap = True
    first = True
    for text, bold, color, dsize in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run()
        r.text = text
        r.font.name = FONT
        r.font.bold = bold
        r.font.size = Pt(base_size + dsize)
        r.font.color.rgb = color


def build_pptx(values: dict, preface: dict, entries: list, roster: list, rung2: list, path: Path) -> dict:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def slide(title, notes=None):
        s = prs.slides.add_slide(blank)
        # white background
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = WHITE
        tb = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9))
        _pptx_textframe(tb.text_frame, [(title, True, ORANGE, 12)])
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def body(s, lines, *, top=1.4, height=5.6, base=14):
        tb = s.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(height))
        _pptx_textframe(tb.text_frame, lines, base_size=base)

    # preface, two slides
    s = slide("A readiness diagnostic: the public client")
    body(s, [(preface["what_it_is"], False, BLACK, 2), ("", False, BLACK, 0),
             ("How it behaves", True, ORANGE, 2)]
         + [(f"• {x}", False, BLACK, -2) for x in preface["how_it_behaves"]])
    s = slide("The public client: what it never does, and the four states")
    body(s, [("What it never does", True, ORANGE, 2)]
         + [(f"• {x}", False, BLACK, -2) for x in preface["what_it_never_does"]]
         + [("", False, BLACK, 0), ("The four states", True, ORANGE, 2),
            (preface["four_states_note"], False, GREY, -3),
            ("", False, BLACK, 0), ("Not a league table", True, ORANGE, 2),
            (preface["not_a_league_table"], False, GREY, -3)])

    # roster
    s = slide(f"The roster: {values['bodies_total']} bodies and {values['flagships_total']} reference hosts")
    lines = []
    for b in roster:
        tag = " (reference host)" if b["flagship"] else ""
        lines.append((f"• {b['body']}{tag} — {b['host']}", False, BLACK, -4))
    body(s, lines, base=12)

    # the ladder
    s = slide("The client ladder: two rungs")
    body(s, [("Rung one", True, ORANGE, 2),
             (preface["two_rungs_note"], False, BLACK, -2)])

    # sixteen checks, one slide per criterion group, in frame order
    groups: dict = {}
    for e in entries:
        groups.setdefault(e["criterion"], []).append(e)
    check_slides = 0
    for crit in ["A", "B", "D", "F"]:
        if crit not in groups:
            continue
        check_slides += 1
        grp = groups[crit]
        s = slide(f"{CRITERION_NAME[crit]}: {len(grp)} check(s)")
        lines, notes = [], []
        for e in grp:
            lines.append((e["plain_name"] + (f"  ({e['marker']})" if e["marker"] else ""),
                          True, BLACK, -4))
            lines.append((e["question"], False, GREY, -5))
            lines.append((f"How it counts: {e['how_counts']}", False, ORANGE, -6))
            lines.append((f"Why: {e['why_it_matters']}", False, GREY, -5))
            notes.append(f"{e['plain_name']}\n  Where we look: {e['where_we_look_raw']}\n"
                         f"  Pass: {e['pass_raw']}")
        body(s, lines, base=12)
        s.notes_slide.notes_text_frame.text = "\n\n".join(notes)

    # rung-two listing
    s = slide("The rung-two listing (specified; measured in its own cycle)")
    lines = [("Surface | key required | registration open | source", True, ORANGE, -3)]
    for r in rung2:
        lines.append((f"{r['body']}: {r['surface']} — {r['key_required']} / "
                      f"{r['registration_open']} / {r['source']}", False, BLACK, -5))
    body(s, lines, base=12)

    # what comes next
    s = slide("What comes next")
    lines = []
    for title, b in WHAT_NEXT:
        lines.append((title, True, ORANGE, 0))
        lines.append((b, False, BLACK, -3))
    body(s, lines)

    prs.save(str(path))
    return {"slides": len(prs.slides._sldIdLst), "check_slides": check_slides}


def pptx_text(path: Path) -> str:
    from pptx import Presentation
    prs = Presentation(str(path))
    parts = []
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
        if s.has_notes_slide:
            parts.append(s.notes_slide.notes_text_frame.text)
    return "\n".join(parts)


def pptx_font_colour_audit(path: Path) -> list[str]:
    """Every run in the deck is Calibri and one of the allowed colours (ruling: Calibri only, no
    colour outside black, greys and the one orange)."""
    from pptx import Presentation
    prs = Presentation(str(path))
    bad = []

    def check(tf, where):
        for p in tf.paragraphs:
            for r in p.runs:
                if r.font.name not in (FONT, None):
                    bad.append(f"{where}: font {r.font.name!r} (not {FONT})")
                col = r.font.color
                try:
                    rgb = col.rgb if col and col.type is not None else None
                except Exception:
                    rgb = None
                if rgb is not None and str(rgb) not in ALLOWED_RGB:
                    bad.append(f"{where}: colour #{rgb} not in allowed {sorted(ALLOWED_RGB)}")

    for i, s in enumerate(prs.slides):
        for sh in s.shapes:
            if sh.has_text_frame:
                check(sh.text_frame, f"slide {i+1}")
    return bad


# ------------------------------------------------------------------------------- digit discipline

#: A run of digits that is NOT part of an identifier (letter adjacent, e.g. W3C), a date, or a
#: version/URL. Used only over the prose the preface and dictionary contribute.
_BARE = re.compile(r"(?<![A-Za-z0-9/.\-])\d[\d,]*(?![A-Za-z0-9/.\-])")


def digit_audit(preface_src: str, entries: list, vocab: dict) -> list[str]:
    """No digit in the preface prose except inside a {{result:...}} token or the user-agent line;
    no bare digit in a dictionary field. Roster counts, URLs and dates are out of scope."""
    bad = []
    # preface: strip tokens and the user_agent string, then any remaining digit is a stray literal
    pf = yaml.safe_load(preface_src)
    ua = pf["user_agent"]["string"]
    prose = []

    def collect(v):
        if isinstance(v, str):
            prose.append(v)
        elif isinstance(v, list):
            for x in v:
                collect(x)
        elif isinstance(v, dict):
            for x in v.values():
                collect(x)

    for k, v in pf.items():
        if k == "user_agent":
            continue
        collect(v)
    for t in prose:
        stripped = _TOKEN.sub(" ", str(t)).replace(ua, " ")
        for m in _BARE.finditer(stripped):
            bad.append(f"preface: stray number {m.group(0)!r} outside a result token")
    for e in entries:
        fields = {k: e[k] for k in ("plain_name", "question", "where_we_look", "what_client_does",
                                    "why_it_matters", "who_else", "rung_two_changes", "how_counts")}
        for label, text in e["outcome"]:
            fields[label] = text
        for key, val in fields.items():
            for m in _BARE.finditer(str(val)):
                bad.append(f"{e['leg']} {key}: bare number {m.group(0)!r}")
    return bad


# ------------------------------------------------------------------------------------------- main

def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    vocab = D.load_vocab()
    values = compute_values()
    preface = load_preface(values)
    entries = dict_entries(vocab)
    roster = D.roster_rows()
    rung2 = D.rung_two_rows()

    md = build_markdown(values, preface, entries, roster, rung2, vocab)
    md_path = OUT / "READINESS_DIAGNOSTIC.md"
    md_path.write_text(md, encoding="utf-8")
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()

    docx_path = OUT / "READINESS_DIAGNOSTIC.docx"
    pptx_path = OUT / "READINESS_DIAGNOSTIC.pptx"
    docx_meta = build_docx(values, preface, entries, roster, rung2, docx_path)
    pptx_meta = build_pptx(values, preface, entries, roster, rung2, pptx_path)

    # checks
    preface_src = PREFACE_SOURCE.read_text(encoding="utf-8")
    digit_bad = digit_audit(preface_src, entries, vocab)
    font_bad = pptx_font_colour_audit(pptx_path)
    texts = {"markdown": md, "docx": docx_text(docx_path), "pptx": pptx_text(pptx_path)}
    vocab_bad = {k: D.banned_hits_prose(v) for k, v in texts.items()}
    vocab_bad = {k: v for k, v in vocab_bad.items() if v}

    report = {
        "generated_by": GENERATOR, "task": TASK, "cycle": values["cycle"],
        "values": values, "tokens_used": preface["_tokens_used"],
        "products": [
            {"name": md_path.name, "md_sha256": md_sha},
            {"name": docx_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(), **docx_meta},
            {"name": pptx_path.name, "md_sha256": md_sha,
             "sha256": hashlib.sha256(pptx_path.read_bytes()).hexdigest(), **pptx_meta},
        ],
        "checks": {
            "digit_audit": digit_bad, "font_colour_audit": font_bad,
            "vocabulary": vocab_bad,
            "docx_roundtrip_ok": bool(docx_text(docx_path)),
            "pptx_roundtrip_ok": bool(pptx_text(pptx_path)),
        },
    }
    (OUT / "build_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    if digit_bad or font_bad or vocab_bad:
        raise SystemExit("FATAL: build checks failed:\n" + json.dumps(report["checks"], indent=1))
    return report


if __name__ == "__main__":
    rep = build()
    print(json.dumps({"products": rep["products"], "checks_ok": True,
                      "tokens_used": rep["tokens_used"]}, indent=1))
