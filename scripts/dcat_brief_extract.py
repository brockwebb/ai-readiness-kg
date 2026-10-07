#!/usr/bin/env python3
"""Extract the documents DCAT-004 v2 admitted, with the standing DCAT driver. **Model spend,
bounded.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decision 1: "Extract what
is admitted with the standing pipeline". The standing pipeline for a DCAT intake epoch is
`scripts/run_dcat_extraction.py` (profile `bulk_v038`, every primitive delegated to
`chunked_pilot`, chunk-level checkpoint under `events/raw/bulk_v038/`, reserve-before-dispatch
on the shared spend ledger). It takes its cohort from a `COHORTS` table; this script adds one
entry for the epoch `scripts/dcat_brief_admit.py` declared and hands over to its `main`, so
nothing is copied and the driver's file is not edited (the task's write set is
`scripts/dcat_brief_*.py`).

    /opt/anaconda3/bin/python3 scripts/dcat_brief_extract.py --phase plan
    /opt/anaconda3/bin/python3 scripts/dcat_brief_extract.py --phase extract --ceiling-tokens N [--only DOC]
    /opt/anaconda3/bin/python3 scripts/dcat_brief_extract.py --phase ingest
    /opt/anaconda3/bin/python3 scripts/dcat_brief_extract.py --phase spend
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_dcat_extraction as rde  # noqa: E402

TASK = "cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md"
COHORT = "brief"
rde.COHORTS[COHORT] = dict(
    TASK=TASK,
    RUN_ID="dcat_us_3_brief_extraction_2026-10-07",
    EPOCH="dcat-us-3-brief-2026-10-07",
    STATE=REPO / "state" / "dcat_us_3_brief_extraction_2026-10-07.json")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--cohort" in argv:
        raise SystemExit("FATAL: this wrapper runs only its own cohort; use "
                         "scripts/run_dcat_extraction.py for the others")
    return rde.main(argv + ["--cohort", COHORT])


if __name__ == "__main__":
    raise SystemExit(main())
