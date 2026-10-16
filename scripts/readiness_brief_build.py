#!/usr/bin/env python3
"""Build the readiness brief for the 2026-10-16 working group: one Markdown source and, from the
same content, a Word document of at most four pages and a deck of at most eight slides. No PDF.
**Zero spend, no network.**

`cc_tasks/2026-10-16_readiness_brief.md` Part A (and the page-four render of Part B), patterned on
`scripts/diagnostic_package_build.py`: the same font, colour, vocabulary and digit checks, the same
token discipline. Every table cell is a query:

* **page one** prose from `reports/diagnostic/brief/brief_source.yaml`, every number a
  `{{result:NAME:value}}` token checked against the value computed here; the user-agent string
  checked against the configuration line it quotes.
* **the check table** (pages one and two) from the framework record: each `spec:<leg>`
  MeasurementSpec's `rf_name_brief`, `rf_ask_plain`, `rf_tells_plain`, `rf_why_short` (written by
  `scripts/apply_instrument_fields.py` from `assessment/instrument/brief_fields.yaml`), grouped by
  the `crit:<letter>` AssessmentCriterion node the spec's leg names. A missing field exits
  non-zero.
* **results by agency** (page three) from `reports/summary/grid.json` under the four-state rule
  of DN-015 §6 (`instrument.four_state`, the function the audit's Part D used), body names from
  the registered frame, reference hosts from the Tier C matrix of the same cycle. Each not
  measured cell carries a footnote: the reason class (`instrument.not_measured_class` over the
  Finding's reason) and, where the cell's Observation receipts carry one, the HTTP status the host
  returned. The receipts are the `observation_recorded` events in `events/cycle-*.jsonl` and the
  base cycle's `state/scan_2026-09-10.json`.
* **page four** from `reports/diagnostic/brief/api_terms.yaml` when it exists and passes
  `scripts/api_terms_check.py`; otherwise the deck carries a slide saying it follows next week and
  the document stops at page three.

    /opt/anaconda3/bin/python3 scripts/readiness_brief_build.py [--register]

`--register` registers the results-summary counts as Seldon Results (generated from grid.json)
before the brief cites them; an existing Result with the same name must carry the same value.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import diagnostic_package as D  # noqa: E402
import diagnostic_package_build as B  # noqa: E402
import instrument as I  # noqa: E402

GENERATOR = "scripts/readiness_brief_build.py"
TASK = "cc_tasks/2026-10-16_readiness_brief.md"
OUT = REPO / "reports" / "diagnostic" / "brief"
SOURCE = OUT / "brief_source.yaml"
API_TERMS = OUT / "api_terms.yaml"
PARAMS = REPO / "assessment" / "harness" / "scan" / "params.yaml"
TIER_C_MATRIX = "docs/reports/scan_matrix_tierC_{suffix}.json"

#: The ceilings the task sets on the products.
MAX_DOCX_PAGES = 4
MAX_PPTX_SLIDES = 8

#: The new reader-facing fields the check table renders; every spec must carry all four.
BRIEF_FIELDS = ["rf_name_brief", "rf_ask_plain", "rf_tells_plain", "rf_why_short"]

#: The reason classes of a not measured page, in plain words (the task's three classes; the
#: fourth, "other_error", is the class function's fallback and is worded as plainly).
REASON_PLAIN = {
    "access_denial": "the website refused the identified client",
    "robots_kept_scanner_out": "the site's robots.txt asked the client not to fetch the page",
    "unconfirmed_absence": "the client could not confirm that the item is absent",
    "server_or_network_error": "a server or network error stopped the client",
    "other_error": "the client could not complete the request",
}
NOT_RUN_NOTE = ("reference hosts are checked at the site level only, so this page-level check "
                "is not run on them")

#: Receipt error classes whose HTTP status explains a not measured page, in preference order: a
#: refusal's status first, and a plain 4xx only when no refusal receipt exists for the page (a 404
#: at another recorded location is not why a refused page went unmeasured). A 404 on a followed
#: link explains nothing about why the page could not be judged.
STATUS_CLASSES = {"access_denial": [{"refused"}, {"http_4xx"}], "server_or_network_error": [{"http_5xx"}]}
STATE_WORD = {"pass": "Pass", "fail": "Fail", "partial": "Partial",
              "could_not_measure": "Not measured", "not_run": "Not run"}
FOOTNOTE_MARKS = "abcdefghijklmnopqrstuvwxyz"
MARKERS = {"scored": "Scored", "shown": "Not scored, shown for openness",
           "declaration": "The site's own statement, not scored", "under_review": "Under review, not scored"}

#: Dashes used as dashes, and the banned words (the vocabulary engine of diagnostic_package).
_DASHES = re.compile("[–—]| -- ")


# ------------------------------------------------------------------------------------- the record

def criterion_word(crit_node: dict) -> str:
    """The plain criterion word from the AssessmentCriterion node's name: its first word in
    sentence case ("ACCESSIBLE" -> "Accessible", "release engineering" -> "Release")."""
    return crit_node["properties"]["name"].split()[0].capitalize()


def check_rows(g: dict | None = None) -> list[dict]:
    """The sixteen checks grouped by criterion (criterion code order), scored first within a
    group, each with its four brief fields and its marker. Exits non-zero on a missing field."""
    g = g or D.load_framework()
    by_id = {n["id"]: n for n in g["nodes"]}
    rows, missing = [], []
    for s in D.instrument_specs(g):
        props = by_id[s["spec_id"]]["properties"]
        crit = by_id.get(f"crit:{s['leg'][0]}")
        if crit is None:
            raise SystemExit(f"FATAL: {s['spec_id']} names criterion {s['leg'][0]!r}, absent from the record")
        for f in BRIEF_FIELDS:
            if not str(props.get(f) or "").strip():
                missing.append(f"{s['spec_id']}.{f}")
        leg = s["leg"]
        # The task's markers were "Declaration", "Under review", "Scored" and "Shown, not scored";
        # the critic's page-one reading flagged "Declaration" and "Shown, not scored" as not
        # understood, and the task's rule is that a flagged word is replaced (RESULT).
        if leg in B.DECLARATION_LEGS:
            marker = MARKERS["declaration"]
        elif leg in B.UNDER_REVIEW_LEGS:
            marker = MARKERS["under_review"]
        elif s["rf_state"] == "specified":
            marker = MARKERS["scored"]
        else:
            marker = MARKERS["shown"]
        rows.append({"leg": leg, "criterion": crit["properties"]["code"],
                     "criterion_word": criterion_word(crit), "marker": marker,
                     "scored": marker == MARKERS["scored"], "state": s["rf_state"],
                     "name": props.get("rf_name_brief"), "ask": props.get("rf_ask_plain"),
                     "tells": props.get("rf_tells_plain"), "why": props.get("rf_why_short")})
    if missing:
        raise SystemExit("FATAL: the record lacks brief fields (run scripts/apply_instrument_fields.py): "
                         + ", ".join(missing))
    leg_rank = {r["leg"]: i for i, r in enumerate(rows)}
    rows.sort(key=lambda r: (r["criterion"], not r["scored"], leg_rank[r["leg"]]))
    return rows


def groups_of(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    out: dict = {}
    for r in rows:
        out.setdefault(r["criterion_word"], []).append(r)
    return list(out.items())


# ------------------------------------------------------------------------------------ the results

def _receipt_index(obs_ids: set) -> dict:
    """`{obs_id: (status, error_class)}` for the wanted Observations, read from every cycle log's
    `observation_recorded` events and the base cycle's state file."""
    out = {}
    for fn in sorted(glob.glob(str(REPO / "events" / "cycle-*.jsonl"))):
        with open(fn, encoding="utf-8") as fh:
            for line in fh:
                if '"observation_recorded"' not in line:
                    continue
                d = json.loads(line)
                if d.get("obs_id") in obs_ids:
                    out[d["obs_id"]] = ((d.get("response") or {}).get("status"), d.get("error_class"))
    for fn in sorted(glob.glob(str(REPO / "state" / "scan_2026-09-10.json"))):
        for d in json.loads(Path(fn).read_text(encoding="utf-8")).get("observations_detail") or []:
            if d.get("obs_id") in obs_ids and d["obs_id"] not in out:
                out[d["obs_id"]] = ((d.get("response") or {}).get("status"), d.get("error_class"))
    return out


def results(g: dict | None = None) -> dict:
    """The page-three table: sixteen bodies by the scored checks under the four-state rule, the
    reference hosts below, footnotes for every not measured or not run cell, and the counts."""
    cfg = I.load_config()
    grid = I.load_grid(cfg)
    findings = I.cycle_findings(grid["cycle"])
    classes = cfg["not_measured_classes"]
    rows = check_rows(g)
    scored = [r["leg"] for r in rows if r["scored"]]
    scored = [c["code"] for c in grid["columns"] if c["code"] in scored]  # grid column order
    names = {r["leg"]: r["name"] for r in rows}
    roster = D.roster_rows()
    full_name = {b["body"]: b["name"] for b in roster}

    # every error page's evidence, so the receipts are read once
    wanted = set()
    for r in grid["rows"]:
        for leg in scored:
            for p in r["cells"][leg]["pages"]:
                f = findings[p["finding_id"]]
                if f["verdict"] == "error":
                    wanted.update(f.get("evidence") or [])
    receipts = _receipt_index(wanted)
    receipts_found = sum(1 for o in wanted if o in receipts)

    notes: dict[str, str] = {}

    def mark_for(text: str) -> str:
        if text not in notes:
            notes[text] = FOOTNOTE_MARKS[len(notes)]
        return notes[text]

    body_rows, counts, wholly = [], collections.Counter(), []
    status_seen = collections.Counter()
    for r in grid["rows"]:
        code = r["agency"]
        if code not in full_name:
            raise SystemExit(f"FATAL: grid body {code!r} is not in the frame roster")
        cells = {}
        for leg in scored:
            pages = r["cells"][leg]["pages"]
            state = I.four_state([p["verdict"] for p in pages])
            counts[state] += 1
            cell = {"state": state, "word": STATE_WORD[state], "mark": None}
            if state == "could_not_measure":
                parts = []
                for p in pages:
                    f = findings[p["finding_id"]]
                    if f["verdict"] != "error":
                        continue
                    cls = I.not_measured_class(f.get("reason") or "", classes)
                    sts = []
                    for tier in STATUS_CLASSES.get(cls, []):
                        sts = sorted({receipts[o][0] for o in f.get("evidence") or []
                                      if o in receipts and receipts[o][0] is not None
                                      and receipts[o][1] in tier})
                        if sts:
                            break
                    for st in sts:
                        status_seen[st] += 1
                    phrase = REASON_PLAIN[cls] + (f" (HTTP {', '.join(str(x) for x in sts)})" if sts else "")
                    if phrase not in parts:
                        parts.append(phrase)
                text = "; ".join(parts)
                cell["mark"] = mark_for(text[0].upper() + text[1:] + ".")
            cells[leg] = cell
        if all(c["state"] == "could_not_measure" for c in cells.values()):
            wholly.append(code)
        body_rows.append({"code": code, "name": full_name[code], "cells": cells})

    # reference hosts: the scored site-level checks from the Tier C matrix of the same cycle;
    # page-level checks are not run on them (Tier C carries tier-0 legs only, DD-059)
    suffix = Path(grid["matrices"]["tierA"]).stem.replace("scan_matrix_tierA_", "")
    tc = json.loads((REPO / TIER_C_MATRIX.format(suffix=suffix)).read_text(encoding="utf-8"))
    tc_by = {row["agency"]: row for row in tc["rows"]}
    ref_rows = []
    for b in roster:
        if not b["flagship"]:
            continue
        row = tc_by.get(b["body"])
        if row is None:
            raise SystemExit(f"FATAL: reference host {b['body']} has no Tier C matrix row")
        cells = {}
        for leg in scored:
            if leg in tc["legs"]:
                v = row["verdicts"].get(leg)
                state = I.four_state([v]) if v else "not_run"
            else:
                state = "not_run"
            cell = {"state": state, "word": STATE_WORD[state], "mark": None}
            if state == "not_run":
                cell["mark"] = mark_for(NOT_RUN_NOTE[0].upper() + NOT_RUN_NOTE[1:] + ".")
            cells[leg] = cell
        ref_rows.append({"code": b["body"], "name": b["name"], "cells": cells})

    total = sum(counts.values())
    return {
        "cycle": grid["cycle"], "grid": cfg["inputs"]["grid"], "scored": scored, "names": names,
        "rows": body_rows, "reference_rows": ref_rows,
        "footnotes": [(m, t) for t, m in notes.items()],
        "counts": {"cells_total": total, "pass": counts["pass"], "partial": counts["partial"],
                   "fail": counts["fail"], "not_measured": counts["could_not_measure"]},
        "wholly_not_measured": wholly,
        "receipts": {"wanted": len(wanted), "found": receipts_found,
                     "statuses_cited": dict(sorted(status_seen.items()))},
    }


# --------------------------------------------------------------------------- values and tokens

def compute_values(rows: list[dict], res: dict) -> dict:
    params = yaml.safe_load(PARAMS.read_text(encoding="utf-8"))["manners"]
    rps = params["requests_per_second_per_host"]
    c = res["counts"]
    return {
        "rate_per_second_per_host": int(rps) if float(rps).is_integer() else rps,
        "user_agent": params["user_agent"],
        "readiness_brief_checks_total": len(rows),
        "readiness_brief_checks_scored": len(res["scored"]),
        "readiness_brief_cells_total": c["cells_total"],
        "readiness_brief_cells_pass": c["pass"],
        "readiness_brief_cells_partial": c["partial"],
        "readiness_brief_cells_fail": c["fail"],
        "readiness_brief_cells_not_measured": c["not_measured"],
        "readiness_brief_bodies_wholly_not_measured": len(res["wholly_not_measured"]),
    }


#: The tokens registered as Seldon Results (the results-summary counts), with descriptions.
REGISTERED = {
    "readiness_brief_cells_total": "agency results on the scored checks (16 bodies x scored checks), cycle of record, four-state rule",
    "readiness_brief_cells_pass": "agency results on the scored checks in state pass",
    "readiness_brief_cells_partial": "agency results on the scored checks in state partial",
    "readiness_brief_cells_fail": "agency results on the scored checks in state fail",
    "readiness_brief_cells_not_measured": "agency results on the scored checks in state not measured",
    "readiness_brief_bodies_wholly_not_measured": "bodies with no scored check measured on the cycle of record",
}


def load_source(values: dict) -> dict:
    src = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    ua = src["user_agent"]
    line = PARAMS.read_text(encoding="utf-8").splitlines()[ua["config_line"] - 1]
    if ua["string"] not in line:
        raise SystemExit(f"FATAL: brief user-agent is not on {ua['config_file']}:{ua['config_line']}: {line!r}")
    if ua["string"] != values["user_agent"]:
        raise SystemExit("FATAL: brief user-agent != the harness's configured user_agent")
    used = []

    def R(v):
        if isinstance(v, str):
            r, u = B.resolve_tokens(v, values)
            used.extend(u)
            return r
        if isinstance(v, list):
            return [R(x) for x in v]
        if isinstance(v, dict):
            return {k: R(x) for k, x in v.items()}
        return v

    out = {k: R(v) for k, v in src.items() if k != "user_agent"}
    out["user_agent"] = ua
    out["_tokens_used"] = sorted(set(used))
    return out


# --------------------------------------------------------------------------------- page four

def load_api_terms() -> dict | None:
    """Part B's table, only when the file exists and passes its checker; None otherwise."""
    if not API_TERMS.is_file():
        return None
    import api_terms_check as AT
    problems = AT.check(yaml.safe_load(API_TERMS.read_text(encoding="utf-8")))
    if problems:
        raise SystemExit("FATAL: api_terms.yaml fails its check:\n  " + "\n  ".join(problems))
    return yaml.safe_load(API_TERMS.read_text(encoding="utf-8"))


def api_rows(api: dict | None) -> list[dict]:
    if not api:
        return []
    import api_terms_check as AT
    return AT.table_rows(api)


API_COLUMNS = [("body", "Body"), ("api", "API"), ("how_called", "How a machine calls it"),
               ("key_obtained", "How a key is obtained"), ("key_changes", "What a key changes"),
               ("announced", "Where it is announced to machines")]


# ----------------------------------------------------------------------------------- markdown

def _cell(t) -> str:
    return str(t).replace("|", "/").replace("\n", " ")


def build_markdown(src: dict, rows: list, res: dict, api: list) -> str:
    L = [f"# {src['title']}", "", f"*{src['subtitle']}*", "",
         f"Generated by `{GENERATOR}` from the framework record, `{res['grid']}` and the cycle of "
         f"record `{res['cycle']}`.", "", "## Why", ""]
    for w in src["why"]:
        L += [f"**{w['heading']}** {w['text']}", ""]
    L += ["## Who", "", src["who"][0], "", f"`{src['user_agent']['string']}`", "",
          src["who_note"], "", src["who"][1], "", f"## {src['never_heading']}", ""]
    L += [f"- {x}" for x in src["never"]] + ["", src["not_measured_line"], "",
                                              f"## {src['checks_heading']}", "", src["checks_intro"], ""]
    L += ["| Check | What we ask your site for | What it tells us | Why it matters |",
          "|---|---|---|---|"]
    for word, grp in groups_of(rows):
        L.append(f"| **{word}** | | | |")
        for r in grp:
            L.append(f"| {_cell(r['name'])} ({r['marker']}) | {_cell(r['ask'])} | "
                     f"{_cell(r['tells'])} | {_cell(r['why'])} |")
    L += ["", f"## {src['results_heading']}", "", src["results_summary"], ""]
    hdr = "| Agency | " + " | ".join(_cell(res["names"][leg]) for leg in res["scored"]) + " |"
    L += [hdr, "|---|" + "---|" * len(res["scored"])]

    def word(c):
        return c["word"] + (f" ({c['mark']})" if c["mark"] else "")

    def label(b):
        return b["name"] if b["name"] == b["code"] else f"{b['name']} ({b['code']})"

    for b in res["rows"]:
        L.append(f"| {_cell(label(b))} | " + " | ".join(word(b["cells"][leg]) for leg in res["scored"]) + " |")
    L += ["", f"*{src['reference_hosts_line']}*", "", hdr, "|---|" + "---|" * len(res["scored"])]
    for b in res["reference_rows"]:
        L.append(f"| {_cell(label(b))} | " + " | ".join(word(b["cells"][leg]) for leg in res["scored"]) + " |")
    L += [""] + [f"({m}) {t}" for m, t in res["footnotes"]] + [""]
    L += [f"## {src['api_heading']}", ""]
    if api:
        L += [src["api_note"], "", "| " + " | ".join(h for _, h in API_COLUMNS) + " |",
              "|" + "---|" * len(API_COLUMNS)]
        for a in api:
            L.append("| " + " | ".join(_cell(a[k]) for k, _ in API_COLUMNS) + " |")
    else:
        L.append(src["api_pending"])
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------------------- docx

def build_docx(src: dict, rows: list, res: dict, api: list, path: Path) -> None:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.text import WD_BREAK
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor as DRGB

    BLACK, GREY, ORANGE = DRGB(0, 0, 0), DRGB(0x55, 0x55, 0x55), DRGB(0xC2, 0x56, 0x00)
    doc = Document()
    for st in ("Normal", "List Bullet"):
        doc.styles[st].font.name = B.FONT
        doc.styles[st].font.size = Pt(10)
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Inches(0.6)
    sec.left_margin = sec.right_margin = Inches(0.65)

    def run(p, text, *, bold=False, size=10, color=BLACK, italic=False):
        r = p.add_run(text)
        r.font.name = B.FONT
        r.font.bold = bold
        r.font.italic = italic
        r.font.size = Pt(size)
        r.font.color.rgb = color
        return r

    def para(text="", *, bold=False, size=10, color=BLACK, style=None, after=3, italic=False):
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(0)
        if text:
            run(p, text, bold=bold, size=size, color=color, italic=italic)
        return p

    def shade(cell, hex_fill):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_fill)
        tcPr.append(shd)

    def table(headers, widths, size=8.5):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.autofit = False
        for i, h in enumerate(headers):
            c = t.rows[0].cells[i]
            c.width = Inches(widths[i])
            p = c.paragraphs[0]
            run(p, h, bold=True, size=size, color=BLACK)
            shade(c, "EDEDED")
        return t

    def add_row(t, vals, widths, size=8.5, bold_first=False, colors=None):
        cells = t.add_row().cells
        for i, v in enumerate(vals):
            cells[i].width = Inches(widths[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if isinstance(v, list):  # [(text, bold, color, size)]
                for j, (tx, bd, col, sz) in enumerate(v):
                    if j:
                        p = cells[i].add_paragraph()
                        p.paragraph_format.space_after = Pt(0)
                    run(p, tx, bold=bd, size=sz, color=col)
            else:
                run(p, str(v), bold=(bold_first and i == 0), size=size,
                    color=(colors[i] if colors else BLACK))
        return cells

    def page_break():
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # page one
    para(src["title"], bold=True, size=16, after=0)
    para(src["subtitle"], size=10, color=GREY, after=6)
    para("Why", bold=True, size=12, color=ORANGE, after=2)
    for w in src["why"]:
        p = para(after=4)
        run(p, w["heading"] + " ", bold=True)
        run(p, w["text"])
    para("Who", bold=True, size=12, color=ORANGE, after=2)
    p = para(after=2)
    run(p, src["who"][0] + " ")
    run(p, src["user_agent"]["string"], bold=True, size=9)
    para(src["who_note"], size=9, color=GREY, after=2)
    para(src["who"][1], after=4)
    para(src["never_heading"], bold=True, size=12, color=ORANGE, after=2)
    for x in src["never"]:
        para(x, style="List Bullet", after=0)
    para(src["not_measured_line"], after=6, italic=True)

    # the check table, pages one and two
    para(src["checks_heading"], bold=True, size=12, color=ORANGE, after=2)
    para(src["checks_intro"], after=3)
    widths = [1.55, 1.95, 1.85, 1.85]
    t = table(["Check", "What we ask your site for", "What it tells us", "Why it matters"], widths)
    for word, grp in groups_of(rows):
        cells = t.add_row().cells
        merged = cells[0].merge(cells[-1])
        run(merged.paragraphs[0], word, bold=True, size=9.5, color=ORANGE)
        for r in grp:
            add_row(t, [[(r["name"], True, BLACK, 8.5),
                         (r["marker"], r["scored"], ORANGE if r["scored"] else GREY, 7.5)],
                        r["ask"], r["tells"], r["why"]], widths)

    # page three
    page_break()
    para(src["results_heading"], bold=True, size=12, color=ORANGE, after=2)
    para(src["results_summary"], after=4)
    rw = [2.6] + [1.15] * len(res["scored"])
    hdrs = ["Agency"] + [res["names"][leg] for leg in res["scored"]]

    def word(c):
        return c["word"] + (f" ({c['mark']})" if c["mark"] else "")

    def label(b):
        return b["name"] if b["name"] == b["code"] else f"{b['name']} ({b['code']})"

    t = table(hdrs, rw, size=8)
    for b in res["rows"]:
        add_row(t, [label(b)] + [word(b["cells"][leg]) for leg in res["scored"]], rw, size=8)
    cells = t.add_row().cells
    merged = cells[0].merge(cells[-1])
    run(merged.paragraphs[0], src["reference_hosts_line"], italic=True, size=8, color=GREY)
    for b in res["reference_rows"]:
        add_row(t, [label(b)] + [word(b["cells"][leg]) for leg in res["scored"]], rw, size=8,
                colors=[GREY] * (1 + len(res["scored"])))
    para(after=2)
    for m, txt in res["footnotes"]:
        para(f"({m}) {txt}", size=8, color=GREY, after=0)

    # page four, when Part B landed
    if api:
        page_break()
        new = doc.add_section()
        new.orientation = WD_ORIENT.LANDSCAPE
        new.page_width, new.page_height = sec.page_height, sec.page_width
        new.top_margin = new.bottom_margin = Inches(0.5)
        new.left_margin = new.right_margin = Inches(0.5)
        para(src["api_heading"], bold=True, size=12, color=ORANGE, after=1)
        para(src["api_note"], size=9, color=GREY, after=3)
        aw = [1.1, 1.7, 1.6, 1.9, 1.7, 2.0]
        t = table([h for _, h in API_COLUMNS], aw, size=7)
        for a in api:
            add_row(t, [a[k] for k, _ in API_COLUMNS], aw, size=6.5, bold_first=True)
    doc.save(str(path))


def docx_text(path: Path) -> str:
    return B.docx_text(path)


def docx_font_colour_audit(path: Path) -> list[str]:
    from docx import Document
    doc = Document(str(path))
    bad = []
    allowed = B.ALLOWED_RGB

    def check(paragraphs, where):
        for p in paragraphs:
            for r in p.runs:
                if r.font.name not in (B.FONT, None):
                    bad.append(f"{where}: font {r.font.name!r}")
                rgb = r.font.color.rgb if r.font.color is not None and r.font.color.type is not None else None
                if rgb is not None and str(rgb) not in allowed:
                    bad.append(f"{where}: colour #{rgb}")

    check(doc.paragraphs, "body")
    for ti, tb in enumerate(doc.tables):
        for row in tb.rows:
            for c in row.cells:
                check(c.paragraphs, f"table {ti + 1}")
    return bad


def docx_pages(path: Path) -> int:
    """The Word document's page count, measured by rendering it (LibreOffice headless) to a PDF in
    a temporary directory and counting pages. The PDF is not a product and is not kept."""
    from pypdf import PdfReader
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", td, str(path)],
                           capture_output=True, text=True, timeout=180)
        pdf = Path(td) / (path.stem + ".pdf")
        if r.returncode != 0 or not pdf.is_file():
            raise SystemExit(f"FATAL: could not render {path.name} to count pages: {r.stderr[-400:]}")
        return len(PdfReader(str(pdf)).pages)


# --------------------------------------------------------------------------------------- pptx

def build_pptx(src: dict, rows: list, res: dict, api: list, path: Path) -> int:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    def slide(title, notes=None):
        s = prs.slides.add_slide(blank)
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = B.WHITE
        tb = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
        B._pptx_textframe(tb.text_frame, [(title, True, B.ORANGE, 14)])
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def body(s, lines, *, top=1.3, height=5.8, base=16):
        tb = s.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(height))
        B._pptx_textframe(tb.text_frame, lines, base_size=base)

    def table(s, headers, data, widths, *, top=1.25, size=10, head_size=None, row_h=None):
        n_rows = 1 + len(data)
        shp = s.shapes.add_table(n_rows, len(headers), Inches(0.4), Inches(top),
                                 Inches(sum(widths)), Inches(0.3 * n_rows))
        tbl = shp.table
        tbl.first_row = False
        tbl.horz_banding = False
        for i, w in enumerate(widths):
            tbl.columns[i].width = Inches(w)
        if row_h:
            for row in tbl.rows:
                row.height = Inches(row_h)

        def put(cell, text, bold, color, sz):
            cell.fill.solid()
            cell.fill.fore_color.rgb = B.WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = text
            r.font.name = B.FONT
            r.font.bold = bold
            r.font.size = Pt(sz)
            r.font.color.rgb = color
            cell.margin_top = cell.margin_bottom = Inches(0.01)

        for i, h in enumerate(headers):
            put(tbl.cell(0, i), h, True, B.ORANGE, head_size or size)
        for ri, vals in enumerate(data, start=1):
            for ci, v in enumerate(vals):
                if isinstance(v, tuple):
                    put(tbl.cell(ri, ci), v[0], v[1], v[2], v[3] if len(v) > 3 else size)
                else:
                    put(tbl.cell(ri, ci), str(v), False, B.BLACK, size)
        return tbl

    # 1 title
    s = slide(src["title"])
    body(s, [(src["subtitle"], False, B.GREY, 4), ("", False, B.BLACK, 0),
             (src["checks_intro"], False, B.BLACK, 0)], top=2.6)
    # 2 why
    s = slide("Why")
    lines = []
    for w in src["why"]:
        lines += [(w["heading"], True, B.ORANGE, 2), (w["text"], False, B.BLACK, 0), ("", False, B.BLACK, -8)]
    body(s, lines)
    # 3 the public client and what it never does
    s = slide("The public client, and what it never does")
    body(s, [(src["who"][0], False, B.BLACK, -1), (src["user_agent"]["string"], True, B.BLACK, -3),
             (src["who_note"], False, B.GREY, -4), (src["who"][1], False, B.BLACK, -1),
             ("", False, B.BLACK, -8), (src["never_heading"], True, B.ORANGE, 0)]
         + [(f"• {x}", False, B.BLACK, -1) for x in src["never"]]
         + [("", False, B.BLACK, -8), (src["not_measured_line"], False, B.GREY, -2)])
    # 4 and 5 the check table: the Accessible group, then the rest
    grps = groups_of(rows)
    heads = ["Check", "What we ask your site for", "What it tells us", "Why it matters"]
    widths = [2.6, 3.4, 3.2, 3.3]

    def check_data(grp_list, size):
        data = []
        for word, grp in grp_list:
            data.append(((word, True, B.ORANGE, size + 1), ("", False, B.BLACK, size),
                         ("", False, B.BLACK, size), ("", False, B.BLACK, size)))
            for r in grp:
                data.append(((f"{r['name']} ({r['marker']})", r["scored"], B.BLACK, size),
                             (r["ask"], False, B.GREY, size), (r["tells"], False, B.GREY, size),
                             (r["why"], False, B.GREY, size)))
        return data

    s = slide(f"The checks: {grps[0][0]}")
    table(s, heads, check_data(grps[:1], 7), widths, top=1.05, size=7, head_size=9)
    s = slide("The checks: " + ", ".join(w for w, _ in grps[1:]))
    table(s, heads, check_data(grps[1:], 10), widths, size=10, head_size=11)
    # 6 results by agency
    notes = "Footnotes on this slide:\n" + "\n".join(f"({m}) {t}" for m, t in res["footnotes"])
    s = slide(src["results_heading"], notes=notes)
    body(s, [(src["results_summary"], False, B.BLACK, -4)], top=0.95, height=0.6, base=16)

    def word(c):
        return c["word"] + (f" ({c['mark']})" if c["mark"] else "")

    def label(b):
        return b["name"] if b["name"] == b["code"] else f"{b['name']} ({b['code']})"

    data = [[(label(b), False, B.BLACK, 7)] + [(word(b["cells"][leg]), False, B.BLACK, 7) for leg in res["scored"]]
            for b in res["rows"]]
    data.append([(src["reference_hosts_line"], False, B.GREY, 7)] + [("", False, B.GREY, 7)] * len(res["scored"]))
    data += [[(label(b), False, B.GREY, 7)] + [(word(b["cells"][leg]), False, B.GREY, 7) for leg in res["scored"]]
             for b in res["reference_rows"]]
    table(s, ["Agency"] + [res["names"][leg] for leg in res["scored"]], data,
          [5.3] + [1.9] * len(res["scored"]), top=1.45, size=7, head_size=7, row_h=0.24)
    # 7 the API table, or a slide saying it follows
    s = slide(src["api_heading"])
    if api:
        body(s, [(src["api_note"], False, B.GREY, -4)], top=0.95, height=0.4)
        table(s, [h for _, h in API_COLUMNS], [[a[k] for k, _ in API_COLUMNS] for a in api],
              [1.3, 2.3, 2.0, 2.5, 2.2, 2.2], top=1.35, size=6, head_size=8)
    else:
        body(s, [(src["api_pending"], False, B.BLACK, 2)], top=2.8)
    prs.save(str(path))
    return len(prs.slides._sldIdLst)


def pptx_text(path: Path) -> str:
    from pptx import Presentation
    prs = Presentation(str(path))
    parts = []
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    parts += [c.text for c in row.cells]
        if s.has_notes_slide:
            parts.append(s.notes_slide.notes_text_frame.text)
    return "\n".join(parts)


def pptx_font_colour_audit(path: Path) -> list[str]:
    """B's audit over text frames, plus every table cell's runs."""
    from pptx import Presentation
    bad = B.pptx_font_colour_audit(path)
    prs = Presentation(str(path))
    for i, s in enumerate(prs.slides):
        for sh in s.shapes:
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for c in row.cells:
                        for p in c.text_frame.paragraphs:
                            for r in p.runs:
                                if r.font.name not in (B.FONT, None):
                                    bad.append(f"slide {i + 1} table: font {r.font.name!r}")
                                rgb = r.font.color.rgb if r.font.color and r.font.color.type is not None else None
                                if rgb is not None and str(rgb) not in B.ALLOWED_RGB:
                                    bad.append(f"slide {i + 1} table: colour #{rgb}")
    return bad


# ------------------------------------------------------------------------------------- checks

def digit_audit(src_text: str, rows: list) -> list[str]:
    """No digit in page-one prose outside a result token, the user-agent string and the dated
    subtitle; no bare digit in a check-table cell. Part B's verbatim agency terms are exempt: a
    stated rate limit is the agency's number, quoted with its source."""
    bad = []
    src = yaml.safe_load(src_text)
    ua = src["user_agent"]["string"]
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

    for k, v in src.items():
        if k not in ("user_agent", "subtitle", "api_note"):
            collect(v)
    for t in prose:
        for m in B._BARE.finditer(B._TOKEN.sub(" ", t).replace(ua, " ")):
            bad.append(f"page one: stray number {m.group(0)!r} outside a result token")
    for r in rows:
        for k in ("name", "ask", "tells", "why"):
            for m in B._BARE.finditer(str(r[k])):
                bad.append(f"{r['leg']} {k}: bare number {m.group(0)!r}")
    return bad


def repeated_phrase_audit(rows: list, n: int = 6) -> list[str]:
    """No phrase of `n` or more words shared by two different rows of the check table (the task:
    each cell says its own thing). Names are excluded: a group of checks may share a noun."""
    seen: dict = {}
    bad = []
    for r in rows:
        for k in ("ask", "tells", "why"):
            words = re.findall(r"[a-z0-9.']+", str(r[k]).lower())
            for i in range(len(words) - n + 1):
                sh = " ".join(words[i:i + n])
                if sh in seen and seen[sh] != r["leg"]:
                    bad.append(f"{r['leg']}.{k} repeats {sh!r} from {seen[sh]}")
                seen.setdefault(sh, r["leg"])
    return bad


def dash_hits(text: str) -> list[str]:
    return [text[max(0, m.start() - 25):m.end() + 25].replace("\n", " ") for m in _DASHES.finditer(text)]


# ------------------------------------------------------------------------------- registration

REGISTERED_FILE = OUT / "registered_results.json"


def register(values: dict) -> list[dict]:
    """Register the results-summary counts as Seldon Results (input hash = grid.json's sha256).
    `seldon result list` truncates names, so what this build registered is kept in
    `registered_results.json` beside the brief: a re-run skips a name registered with the same
    value and REFUSES one registered with another (a changed count is a new Result, by hand)."""
    grid_path = REPO / I.load_config()["inputs"]["grid"]
    h = hashlib.sha256(grid_path.read_bytes()).hexdigest()
    have = json.loads(REGISTERED_FILE.read_text(encoding="utf-8")) if REGISTERED_FILE.is_file() else {}
    out = []
    for name, desc in REGISTERED.items():
        if name in have:
            if float(have[name]["value"]) != float(values[name]):
                raise SystemExit(f"FATAL: Result {name} was registered as {have[name]['value']}, "
                                 f"computed now {values[name]}")
            out.append({"name": name, "value": values[name], "status": "already registered", "id": have[name]["id"]})
            continue
        r = subprocess.run(["seldon", "result", "register", "--name", name, "--value", str(values[name]),
                            "--units", "count", "--description", f"{desc} ({GENERATOR}, {TASK})",
                            "--input-hash", h], capture_output=True, text=True, cwd=REPO)
        if r.returncode != 0:
            raise SystemExit(f"FATAL: seldon result register {name} failed: {r.stdout}{r.stderr}")
        m = re.search(r"\b([0-9a-f]{8})[0-9a-f-]*", r.stdout)
        have[name] = {"value": values[name], "id": m.group(0) if m else None, "input_sha256": h,
                      "output": r.stdout.strip()[-300:]}
        REGISTERED_FILE.write_text(json.dumps(have, indent=1) + "\n", encoding="utf-8")
        out.append({"name": name, "value": values[name], "status": "registered", "id": have[name]["id"]})
    return out


# ---------------------------------------------------------------------------------------- main

def build(*, do_register: bool = False, out: Path = OUT, measure_pages: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = D.load_framework()
    rows = check_rows(g)
    res = results(g)
    values = compute_values(rows, res)
    registered = register(values) if do_register else []
    src = load_source(values)
    api_doc = load_api_terms()
    api = api_rows(api_doc)

    md = build_markdown(src, rows, res, api)
    md_path = out / "READINESS_BRIEF.md"
    md_path.write_text(md, encoding="utf-8")
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    docx_path, pptx_path = out / "READINESS_BRIEF.docx", out / "READINESS_BRIEF.pptx"
    build_docx(src, rows, res, api, docx_path)
    slides = build_pptx(src, rows, res, api, pptx_path)
    pages = docx_pages(docx_path) if measure_pages else None

    texts = {"markdown": md, "docx": docx_text(docx_path), "pptx": pptx_text(pptx_path)}
    checks = {
        "docx_pages": pages, "pptx_slides": slides,
        "digit_audit": digit_audit(SOURCE.read_text(encoding="utf-8"), rows),
        "font_colour_audit": {"docx": docx_font_colour_audit(docx_path), "pptx": pptx_font_colour_audit(pptx_path)},
        "vocabulary": {k: D.banned_hits_prose(v) for k, v in texts.items()},
        "dashes": {k: dash_hits(v) for k, v in texts.items()},
        "repeated_phrases": repeated_phrase_audit(rows),
    }
    failures = []
    if pages is not None and pages > MAX_DOCX_PAGES:
        failures.append(f"docx has {pages} pages, over {MAX_DOCX_PAGES}")
    if slides > MAX_PPTX_SLIDES:
        failures.append(f"pptx has {slides} slides, over {MAX_PPTX_SLIDES}")
    for k in ("digit_audit", "repeated_phrases"):
        if checks[k]:
            failures.append(k)
    for k in ("font_colour_audit", "vocabulary", "dashes"):
        if any(checks[k].values()):
            failures.append(k)
    report = {
        "generated_by": GENERATOR, "task": TASK, "cycle": res["cycle"], "values": values,
        "tokens_used": src["_tokens_used"], "registered": registered,
        "counts": res["counts"], "wholly_not_measured": res["wholly_not_measured"],
        "receipts": res["receipts"], "footnotes": res["footnotes"],
        "groups": {w: [r["leg"] for r in grp] for w, grp in groups_of(rows)},
        "api_rows": len(api),
        "products": [
            {"name": md_path.name, "md_sha256": md_sha},
            {"name": docx_path.name, "md_sha256": md_sha, "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(), "pages": pages},
            {"name": pptx_path.name, "md_sha256": md_sha, "sha256": hashlib.sha256(pptx_path.read_bytes()).hexdigest(), "slides": slides},
        ],
        "checks": checks, "failures": failures,
    }
    (out / "build_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("FATAL: build checks failed: " + ", ".join(failures) + "\n"
                         + json.dumps(checks, indent=1, ensure_ascii=False)[:4000])
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--register", action="store_true", help="register the results counts as Seldon Results first")
    a = ap.parse_args(argv)
    rep = build(do_register=a.register)
    print(json.dumps({k: rep[k] for k in ("counts", "wholly_not_measured", "receipts", "groups", "api_rows",
                                          "registered", "products")}, indent=1, ensure_ascii=False))
    print(json.dumps({"checks_ok": True, "docx_pages": rep["checks"]["docx_pages"],
                      "pptx_slides": rep["checks"]["pptx_slides"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
