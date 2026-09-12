#!/usr/bin/env python3
"""The L0 report's page counts, prose and total, measured from the built PDF and registered.

Task `cc_tasks/2026-09-11_report_sources_appendix.md` decision 5. **Zero spend, no network.**
The ~7-page target governs PROSE, so the two numbers are reported apart: `total` is the
published PDF's page count; `prose` is the page count of the same markdown rendered under the
same settings with every table block and the appendix removed (`build_report_pdf.prose_only`).
Measured, not estimated, and registered rather than typed into the RESULT, so the next revision
can say whether the prose grew.

    /opt/anaconda3/bin/python3 scripts/register_report_page_counts.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import build_report_pdf                                             # noqa: E402
import cycle_results                                                # noqa: E402

TASK = "cc_tasks/2026-09-11_report_sources_appendix.md"
SCRIPT_ARTIFACT = "register_report_page_counts"
EPOCH = "2026-09-11"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if not build_report_pdf.PDF.is_file() or not build_report_pdf.BUILD_MD.is_file():
        raise SystemExit("FATAL: build the report first (make report-pdf); there is no PDF to "
                         "count pages of")
    counts = build_report_pdf.page_counts()
    rows = [
        ("l0_report_pages_total", counts["total"],
         f"Page count of docs/reports/2026-09_fss_ai_readiness_L0.pdf as built on {EPOCH}, "
         f"with the generated Sources-per-check appendix. Read from the PDF by pypdf. "
         f"Task {TASK} decision 5."),
        ("l0_report_pages_prose", counts["prose"],
         f"Page count of the report's PROSE on {EPOCH}: the built markdown with every table "
         f"block and everything from the Method appendix on removed, rendered under the "
         f"published PDF's own pandoc/typst settings (`build_report_pdf.prose_only`). The "
         f"~7-page target governs this number, not the total. Task {TASK} decision 5."),
    ]
    if a.dry_run:
        print(json.dumps(counts, indent=1))
        for b, v, _n in rows:
            print(f"  {cycle_results.name_for(b, EPOCH):40s} {v}")
        return 0

    from seldon_artifacts import live_artifact
    if not live_artifact(SCRIPT_ARTIFACT):
        import subprocess
        r = subprocess.run(
            ["seldon", "artifact", "create", "Script", "--actor", "cc",
             "-p", f"name={SCRIPT_ARTIFACT}",
             "-p", "path=scripts/register_report_page_counts.py",
             "-p", f"description=Measures the L0 report's total and prose-only page counts "
                   f"from the built PDF and registers them. Task {TASK}."],
            capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr[-300:]}")

    out = cycle_results.register(
        [(cycle_results.name_for(b, EPOCH), v, n) for b, v, n in rows],
        cycle=EPOCH, script=SCRIPT_ARTIFACT, data="scan_targets_fss_2026-09_v4")
    print(json.dumps({**counts, **out}, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
