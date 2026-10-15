#!/usr/bin/env python3
"""Build the executive summary: SUMMARY.md and SUMMARY.pdf. **Zero spend, no network.**

`cc_tasks/2026-10-12_executive_summary_from_brief_v2.md` step 5. Reads the authored source
(`reports/summary/summary_source.yaml`) and writes, into `reports/summary/`:

* `SUMMARY.md`: the whole document. Page 1 is the message; page 2 is one table of results, each
  with one free action; then an appendix with the fuller definition and the source list. Claim
  markers (`[c:CL-...]`), which the verification reads, are stripped from the reader-facing text.
* `SUMMARY.pdf`: rendered from SUMMARY.md by THIS script (pandoc and typst, the concise report's
  and DCAT brief's call), so the PDF cannot drift from its Markdown. The body (pages 1 and 2) is
  rendered on its own to a scratch PDF to count its pages; the gate requires exactly 2.
* `build_report.json`: the Markdown and PDF sha256s (git keeps no file times, so a test checks
  the pair by hash), the body page count and the whole-document page count.

The build refuses to write on any text-check finding: `scripts/summary_text_check.py` (the four
the brief cuts: process words, indicator codes, AI outside a published title, dashes) and
`scripts/dcat_faq_lint.py` (repository paths, file names, the operator's banned words).

    /opt/anaconda3/bin/python3 scripts/summary_build.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

import dcat_brief_build as BB  # noqa: E402
import dcat_faq_build as FB  # noqa: E402
import dcat_faq_lint as LINT  # noqa: E402
import summary_text_check as TC  # noqa: E402

GENERATOR = "scripts/summary_build.py"
TASK = "cc_tasks/2026-10-14_executive_summary_v3_grid.md"
OUT = REPO / "reports" / "summary"
SOURCE = OUT / "summary_source.yaml"
PAGEBREAK = "```{=typst}\n#pagebreak()\n```"
MARKER_RE = re.compile(r"\s*\[c:[^\]]*\]")


def strip_markers(s: str) -> str:
    return MARKER_RE.sub("", s).strip()


# ------------------------------------------------------------------------------------- sources

def plain_title(t: str) -> str:
    """Typesetting only: an em dash or en dash inside a published title becomes a colon (the
    operator's rule bars the character from his output, and the text check skips the Sources
    section only because the builder has already normalised it)."""
    t = re.sub(r"\s*[–—]\s*", ": ", t or "")
    return " ".join(t.split())


def fmt_source(title: str, who: str | None, year: str | None, url: str | None) -> str:
    head = plain_title(title).rstrip(".")
    by = ", ".join(x for x in (who, year) if x).rstrip(".")
    return f"{head}." + (f" {by}." if by else "") + (f" <{url}>" if url else "")


def source_line(entry: dict, manifest: dict) -> str:
    """One source line. A corpus document is cited by id and read from the manifest; a standard
    not in the corpus carries its title and URL inline."""
    if "id" in entry:
        ent = (manifest.get("entries") or {}).get(entry["id"])
        if not ent:
            raise SystemExit(f"FATAL: source {entry['id']!r} is not in the corpus manifest")
        idn = ent["identity"]
        who = ", ".join(a for a in (idn.get("authors_or_org") or []) if a)
        year = str(idn.get("pub_year") or idn.get("pub_date") or "")[:4]
        return fmt_source(idn.get("title") or entry["id"], who, year, idn.get("source_url"))
    return fmt_source(entry["title"], entry.get("who"), entry.get("year"), entry.get("url"))


# ------------------------------------------------------------------------------------ markdown

def page1_md(blocks: list) -> list[str]:
    out = []
    for b in blocks:
        if "heading" in b:
            out += [f"## {b['heading']}", ""]
        else:
            out += [" ".join(strip_markers(s) for s in b["para"]), ""]
    return out


# ---------------------------------------------------------------------------- the page-2 grid
# Page two is one grid (DN-014 ADDENDUM 01 §2): 16 agencies by the public-tier checks, a glyph
# and a colour in every cell, the fix line under each check, a legend, a three-sentence footnote.
# Two renderings, ONE source (reports/summary/grid.json): a raw typst block for the coloured
# landscape PDF, and clean text for the reader (Fable) and the text check. Both carry the same
# human strings, so the check that reads the text covers what the PDF shows.
GLYPH = {"pass": "●", "partial": "◐", "fail": "○"}  # ● ◐ ○ (shape distinguishes)
COLOR = {"pass": "#1b5e9c", "partial": "#c77d0a", "fail": "#b22222"}  # blue, amber, red
_TZ = {c: "\\" + c for c in "\\#$*_`@<>[]~"}


def tz(s: str) -> str:
    """Escape the characters typst reads as markup, so a plain string shows verbatim."""
    return "".join(_TZ.get(ch, ch) for ch in str(s))


def _row_label(r: dict) -> str:
    return r["display_name"] + (f" ({r['page_count']} pages)" if r["page_count"] > 1 else "")


def grid_typst(src: dict, grid: dict) -> str:
    """The colourful landscape grid, as a raw typst block for the PDF."""
    cols, rows = grid["columns"], grid["rows"]
    n = len(cols)

    def mark(state: str) -> str:
        return f'#text(fill: rgb("{COLOR[state]}"))[{GLYPH[state]}]'

    header = ", ".join(f"[*{tz(c['plain_name'])}*]" for c in cols)
    body_rows = []
    for r in rows:
        cells = ", ".join(f"[{mark(r['cells'][c['leg']]['state'])}]" for c in cols)
        body_rows.append(f"[{tz(_row_label(r))}], {cells}")
    rows_block = ",\n  ".join(body_rows)
    fixes = "\n".join(f"  [*{tz(c['plain_name'])}.* {tz(c['fix_line'])}]," for c in cols)
    lg = grid["legend"]
    legend = (f'*Key.* #text(fill: rgb("{COLOR["pass"]}"))[{GLYPH["pass"]}] pass: {tz(lg["pass"])}; '
              f'#text(fill: rgb("{COLOR["partial"]}"))[{GLYPH["partial"]}] partial: {tz(lg["partial"])}; '
              f'#text(fill: rgb("{COLOR["fail"]}"))[{GLYPH["fail"]}] fail: {tz(lg["fail"])}.')
    return (
        "```{=typst}\n"
        "#pagebreak(weak: true)\n"
        "#page(flipped: true, margin: (x: 1.1cm, y: 1.0cm))[\n"
        f'#align(center)[#text(size: 12pt, weight: "bold")[{tz(src["page2"]["heading"])}]]\n'
        "#v(4pt)\n"
        "#set text(size: 6pt)\n"
        "#table(\n"
        f"  columns: (4.5cm,) + (1fr,)*{n},\n"
        f"  align: (left + horizon,) + (center + horizon,)*{n},\n"
        '  stroke: 0.3pt + rgb("#bbbbbb"),\n'
        "  inset: 2.1pt,\n"
        f"  table.header([*Agency*], {header}),\n"
        f"  {rows_block}\n"
        ")\n"
        "#v(6pt)\n"
        '#text(size: 7pt)[*The fix under each check.*]\n'
        "#v(2pt)\n"
        "#set text(size: 6.2pt)\n"
        "#grid(columns: (1fr, 1fr), gutter: 9pt, row-gutter: 2.4pt,\n"
        f"{fixes}\n"
        ")\n"
        "#v(6pt)\n"
        f'#text(size: 6.3pt)[{legend}]\n'
        "#v(3pt)\n"
        f'#text(size: 6pt, style: "italic")[{tz(grid["footnote"])}]\n'
        "]\n"
        "```"
    )


def grid_plaintext(src: dict, grid: dict) -> list[str]:
    """The grid as clean markdown the reader and the text check read. Same strings as the PDF."""
    cols, rows = grid["columns"], grid["rows"]
    lg = grid["legend"]
    out = [f"## {src['page2']['heading']}", "",
           (f"Key: {GLYPH['pass']} pass, {lg['pass']}; {GLYPH['partial']} partial, "
            f"{lg['partial']}; {GLYPH['fail']} fail, {lg['fail']}."), ""]
    head = ["Agency"] + [c["plain_name"] for c in cols]
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "|".join([" --- "] * len(head)) + "|")
    for r in rows:
        cells = [_row_label(r)] + [GLYPH[r["cells"][c["leg"]]["state"]] for c in cols]
        out.append("| " + " | ".join(x.replace("|", "\\|") for x in cells) + " |")
    out += ["", "The fix under each check:", ""]
    for c in cols:
        out.append(f"- {c['plain_name']}: {c['fix_line']}")
    out += ["", grid["footnote"], ""]
    return out


# ------------------------------------------------------------------------------------ markdown 2

def appendix_md(ap: dict, manifest: dict) -> list[str]:
    out = [f"## {ap['sources_heading']}", ""]
    for n, e in enumerate(ap["sources"], 1):
        out.append(f"{n}. {source_line(e, manifest)}")
    out.append("")
    if ap.get("provenance"):
        out += [ap["provenance"], ""]
    return out


def page1_lines(src: dict) -> list[str]:
    return [f"# {src['title']}", "", f"Prepared {src['prepared']}.", ""] + page1_md(src["page1"])


def body_markdown(src: dict, grid: dict) -> str:
    """PDF body: page-1 prose, then the typst grid (page 2)."""
    lines = page1_lines(src) + ["", grid_typst(src, grid), ""]
    return "\n".join(lines).rstrip() + "\n"


def body_plaintext(src: dict, grid: dict) -> str:
    """Reader/text-check body: page-1 prose, a page break, the grid as clean text."""
    lines = page1_lines(src) + ["", PAGEBREAK, ""] + grid_plaintext(src, grid)
    return "\n".join(lines).rstrip() + "\n"


def full_markdown(src: dict, grid: dict, manifest: dict) -> str:
    lines = [body_markdown(src, grid).rstrip(), "", PAGEBREAK, ""]
    lines += appendix_md(src["appendix"], manifest)
    return "\n".join(lines).rstrip() + "\n"


def full_plaintext(src: dict, grid: dict, manifest: dict) -> str:
    lines = [body_plaintext(src, grid).rstrip(), "", PAGEBREAK, ""]
    lines += appendix_md(src["appendix"], manifest)
    return "\n".join(lines).rstrip() + "\n"


# ------------------------------------------------------------------------------------- outputs

def text_findings(md: str) -> list:
    return [{**f, "src": "text_check"} for f in TC.check(md)] + \
           [{**f, "src": "lint"} for f in LINT.lint(md)]


def render(md_path: Path, pdf_path: Path, md: str, out_dir: Path) -> dict:
    build_dir = out_dir / "build"
    build_dir.mkdir(exist_ok=True)
    scratch = build_dir / md_path.name
    try:
        scratch.write_text(FB.strip_title(md), encoding="utf-8")
        BB.render_pdf(scratch, pdf_path, BB.h1(md))
    finally:
        scratch.unlink(missing_ok=True)
        if not any(build_dir.iterdir()):
            build_dir.rmdir()
    return {"md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
            "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            "pages": BB.pdf_pages(pdf_path)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=None, help="test seam (default: reports/summary)")
    ap.add_argument("--source", default=None, help="test seam (default: reports/summary/summary_source.yaml)")
    ap.add_argument("--no-pdf", action="store_true", help="test seam: skip the pandoc render")
    a = ap.parse_args(argv)
    out = Path(a.out_dir) if a.out_dir else OUT
    src = yaml.safe_load((Path(a.source) if a.source else SOURCE).read_text(encoding="utf-8"))
    manifest = json.loads((REPO / src["inputs"]["manifest"]).read_text(encoding="utf-8"))
    grid = json.loads((REPO / src["inputs"]["grid"]).read_text(encoding="utf-8"))

    body = body_markdown(src, grid)
    full = full_markdown(src, grid, manifest)
    # The text check reads the CLEAN TEXT of both pages (page-1 prose and the grid as text) plus
    # the sources, not the raw typst of the PDF grid: the two carry the same human strings.
    plain = full_plaintext(src, grid, manifest)
    findings = text_findings(plain)
    if findings:
        for f in findings:
            print(f"page:{f['line']} [{f['src']}:{f['rule']}] {f['match']!r} in {f.get('context','')!r}")
        raise SystemExit(f"FATAL: the summary fails the text check ({len(findings)} finding(s)); nothing is written")

    md_path = out / "SUMMARY.md"
    md_path.write_text(full, encoding="utf-8")
    report = {"generated_by": GENERATOR, "task": TASK, "text_check": "0 findings"}
    if not a.no_pdf:
        body_pdf = out / "build_body.pdf"
        body_info = render(md_path.with_name("SUMMARY_body.md"), body_pdf, body, out)
        report["body"] = {"pages": body_info["pages"], "md_sha256": body_info["md_sha256"]}
        full_info = render(md_path, out / "SUMMARY.pdf", full, out)
        report["render"] = {"markdown": "SUMMARY.md", "pdf": "SUMMARY.pdf", **full_info}
        body_pdf.unlink(missing_ok=True)
        report["body_pages"] = body_info["pages"]
        report["total_pages"] = full_info["pages"]
    (out / "build_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
