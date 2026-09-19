#!/usr/bin/env python3
"""Backfill the citation fields of the two documents G4's appendix rows now cite. **Zero spend,
no network.**

`cc_tasks/2026-09-19_resnapshot_rj4.md`. The re-snapshot's product section quotes a G4 pass
count, so the "Sources per check" appendix now carries G4 (`report_traceability.appendix_legs`
reads the checks off the report's tags), and G4's two admitted sources had never been cited by
the report before: both still carry the ledger's `(unspecified)` / `n.d.`, which
`tests/test_report_sources_appendix.py` refuses (DN-001: a citation a stranger can follow).

Same path and same rule as `scripts/backfill_citation_metadata.py`, whose docstring this
follows: every value was read off page 1 of the PDF on disk in this session, `provenance`
quotes where, and each write is a `metadata_corrected` event on the dixie ledger through
`kg.manifest.metadata_update`, the one sanctioned second write to `identity.*`. Unlike that
script, a document whose field already holds the corrected value is SKIPPED, so a second run
writes nothing.

    /opt/anaconda3/bin/python3 scripts/backfill_g4_source_metadata.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kg import manifest as M  # noqa: E402

TASK = "cc_tasks/2026-09-19_resnapshot_rj4.md"

#: doc_id -> (sections, provenance). Sections are exactly what `metadata_update` takes.
CORRECTIONS: dict[str, tuple[dict, str]] = {
    "fcsm-19-01-transparent-reporting-for-integrated-data-quality": (
        {"identity": {"pub_year": "2019",
                      "authors_or_org": ["Prell M", "Chapman C", "Adeshiyan S", "Fixler D",
                                         "Garin T", "Mirel L", "Phipps P"]}},
        "corpus/bulk/fcsm-19-01-transparent-reporting-for-integrated-data-quality.pdf page 2, "
        "the document's own 'Recommended citation': 'Prell, Mark, Chris Chapman, Samson "
        "Adeshiyan, Dennis Fixler, Tom Garin, Lisa Mirel, and Polly Phipps. 2019. Transparent "
        "Reporting for Integrated Data Quality: Practices of Seven Federal Statistical "
        "Agencies. FCSM 19-01. Federal Committee on Statistical Methodology. September 2019.'; "
        "page 1 agrees ('Prepared by ... September 2019'). Read by " + TASK,
    ),
    "statistical-policy-working-paper-46-data-quality-assessment": (
        {"identity": {"pub_year": "2013",
                      "authors_or_org": ["Iwig W", "Berning M", "Marck P", "Prell M"]}},
        "corpus/bulk/statistical-policy-working-paper-46-data-quality-assessment.pdf page 1: "
        "'Data Quality Assessment Tool for Administrative Data / William Iwig / National "
        "Agricultural Statistics Services / Michael Berning / U.S. Census Bureau / Paul Marck / "
        "U.S. Census Bureau / Mark Prell / Economic Research Service / February 2013'; page 3 "
        "repeats the author line 'William Iwig, Michael Berning, Paul Marck, Mark Prell'. Read "
        "by " + TASK,
    ),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    _, entries, _ = M._dixie_ledger()
    written = 0
    for doc_id, (sections, provenance) in CORRECTIONS.items():
        entry = entries.get(doc_id)
        if entry is None:
            print(f"REFUSED: {doc_id} is not in the corpus ledger", file=sys.stderr)
            return 1
        before = {f"{s}.{f}": entry[s][f] for s, vs in sections.items() for f in vs}
        after = {f"{s}.{f}": v for s, vs in sections.items() for f, v in vs.items()}
        print(doc_id)
        for key in after:
            print(f"    {key}: {before[key]!r} -> {after[key]!r}")
        if before == after:
            print("    already corrected; skipped")
            continue
        if a.dry_run:
            continue
        print(f"    event {M.metadata_update(doc_id, provenance=provenance, **sections)}")
        written += 1
    print(f"\n{'DRY RUN, nothing written' if a.dry_run else f'appended {written} event(s)'}; "
          f"run `python -m kg.manifest rebuild` to project them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
