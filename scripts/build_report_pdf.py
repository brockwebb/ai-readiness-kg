#!/usr/bin/env python3
"""Render the L0 report to PDF. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_report_pdf.md` decision 1: the PDF is a BUILD PRODUCT. The markdown
is rebuilt first by `scripts/build_l0_report.py`, so every `{{result:...}}` resolves from the
graph, and this script only converts. No number is typed here and none can be.

**That rebuild is a CALL, not a sentence.** This docstring and the `report-pdf` target both said
the markdown was rebuilt first and nothing did it: `main` checked that
`2026-09_fss_ai_readiness_L0.md` exists and carries no unresolved token, which a stale file
passes trivially. `cc_tasks/2026-09-11_l0_report_cycle4_revision.md` found it the way it is
always found — the cycle-4 revision moved every tag and the figure, and `make report-pdf`
produced a PDF of the previous cycle, embedding the previous cycle's figure, with no error
anywhere. A build product whose builder does not run is a committed artifact that drifts from
its sources in silence.

**Toolchain, pinned to what is already installed** (decision 1 forbids installing one):
pandoc 3.8.3 as the converter, typst 0.14.2 as the PDF engine. There is no LaTeX on this
machine; typst is what exists, and it renders SVG natively, which matters because F5 is an SVG
the graph page already builds and decision 3 says not to redraw it.

**One build-time adaptation, which edits no shipped artifact:** the markdown is copied to a
build file so pandoc resolves the figure through `--resource-path`, and the shipped
`2026-09_fss_ai_readiness_L0.md` keeps the path the graph page uses.

There used to be a second. `figures.py` wrote SVG for inline embedding only, with no `xmlns`,
and typst refused every figure with "missing root node", so this script namespaced a copy.
`cc_tasks/2026-09-10_harness_small.md` decision 3 fixed it at source: the figures are standalone
documents now, and a build step that repaired them on the way past is a step that hid the
defect from every other consumer.

    /opt/anaconda3/bin/python3 scripts/build_report_pdf.py [--check]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
REPORTS = REPO / "docs" / "reports"
GENERATED = REPORTS / "generated"
STEM = "2026-09_fss_ai_readiness_L0"
MD = REPORTS / f"{STEM}.md"
PDF = REPORTS / f"{STEM}.pdf"
BUILD_MD = GENERATED / f"{STEM}.build.md"

PANDOC, ENGINE = "pandoc", "typst"


def tool_versions() -> dict:
    out = {}
    for t in (PANDOC, ENGINE):
        exe = shutil.which(t)
        if not exe:
            raise SystemExit(
                f"FATAL: {t} is not installed. Decision 1 forbids installing a toolchain to "
                f"build this PDF; report and stop.")
        v = subprocess.run([t, "--version"], capture_output=True, text=True).stdout
        out[t] = v.splitlines()[0].strip()
    return out


def prepare() -> tuple:
    """The build markdown, with every figure repointed at a namespaced copy."""
    md = MD.read_text(encoding="utf-8")
    figures = []
    for m in re.finditer(r"!\[[^\]]*\]\(([^)]+\.svg)\)", md):
        rel = m.group(1)
        src = (REPO / rel)
        if not src.is_file():
            raise SystemExit(f"FATAL: the report references {rel}, which does not exist")
        head = src.read_text(encoding="utf-8").split(">", 1)[0]
        if "xmlns=" not in head:
            raise SystemExit(
                f"FATAL: {rel} carries no xmlns and is not a standalone SVG document. "
                f"figures.py emits it since decision 3; re-run the figure build rather than "
                f"repairing the file here, which is what hid this from every other consumer.")
        figures.append((rel, src))
    GENERATED.mkdir(parents=True, exist_ok=True)
    BUILD_MD.write_text(md, encoding="utf-8")
    return BUILD_MD, figures


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="prepare and report, render nothing")
    a = ap.parse_args(argv)

    versions = tool_versions()
    # The markdown FIRST, through its own gate: a fatal reference, an unresolved token, a bare
    # numeral in prose or a missing fragment writes no markdown (`build_l0_report.build`), and
    # then this writes no PDF either.
    import build_l0_report
    if build_l0_report.build(check=a.check):
        raise SystemExit("FATAL: the markdown gate BLOCKED; no PDF is built from a report the "
                         "graph could not fill in")
    if not MD.is_file():
        raise SystemExit(f"FATAL: {MD} does not exist; run scripts/build_l0_report.py first")
    unresolved = re.findall(r"\{\{(?:result|figure|cite):[^}]*\}\}", MD.read_text("utf-8"))
    if unresolved:
        raise SystemExit(f"FATAL: the built markdown still carries {len(unresolved)} "
                         f"unresolved reference(s); the PDF may not be built from it")

    build_md, figures = prepare()
    print(f"toolchain : {versions}")
    print(f"figures   : {[str(d.relative_to(REPO)) for _s, d in figures]}")
    if a.check:
        return 0

    cmd = [PANDOC, str(build_md),
           "--from=markdown+pipe_tables+raw_html",
           f"--pdf-engine={ENGINE}",
           f"--resource-path={GENERATED}:{REPORTS}:{REPO}",
           "--metadata", "title=AI readiness of the federal statistical system: "
                         "host-level findings",
           "--variable", "papersize=a4",
           # LANDSCAPE, as raw typst. pandoc's typst template exposes `papersize` and no
           # `flipped`, so `-V flipped=true` is silently ignored — it was, and the first build
           # came out portrait with the agency names hyphenated mid-word. Decision 2 says
           # landscape before shrinking type below 9 pt, so this is set where typst reads it.
           "--variable", "header-includes=#set text(hyphenate: false)",
           "--variable", "margin-x=1.4cm", "--variable", "margin-y=1.6cm",
           "--variable", "fontsize=10pt",
           # NO TABLE OF CONTENTS, and that is a gate decision rather than a taste one. §3
           # requires the PDF's numerals to match the markdown's exactly; a generated contents
           # page injects page numbers that appear in no source, which would make the check
           # unsatisfiable and invite an exemption instead of a fix.
           "-o", str(PDF)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/{ENGINE} failed:\n{r.stderr[-1500:]}")
    print(f"wrote {PDF.relative_to(REPO)} ({PDF.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
