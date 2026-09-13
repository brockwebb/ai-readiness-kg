#!/usr/bin/env python3
"""Backfill the citation fields the report's appendix cannot render without.

`cc_tasks/2026-09-12_cited_documents_metadata_2.md` decision 2. Every value below was read
off the document on disk this session; `provenance` names the page or line it was read from,
so a stranger can re-read it. A value the document does not state is NOT here — those
doc_ids are in `NOT_STATED` with what was searched and what was found instead.

One-shot and idempotent-by-refusal: re-running it appends a second correction whose `before`
is the value the first one wrote, which the ledger records honestly rather than hiding. Use
--dry-run to see the events without writing.

Nothing here is typed from knowledge. The two federal documents were re-read from page 1 of
the PDF this session rather than taken from the prior RESULT's quotation of them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kg import manifest as M  # noqa: E402

#: doc_id -> (sections, provenance). Sections are exactly what `metadata_update` takes.
CORRECTIONS: dict[str, tuple[dict, str]] = {
    "rfc-9309-robots-exclusion-protocol": (
        {"identity": {"pub_year": "2022"}},
        "corpus/kernel/rfc-9309-robots-exclusion-protocol.md line 13 (RFC header block): "
        "'September 2022'; line 43: 'Copyright (c) 2022 IETF Trust and the persons "
        "identified as the ...'",
    ),
    "schema-org-dataset": (
        {"identity": {"pub_year": "2026"}},
        "corpus/kernel/schema-org-dataset.md line 1009 (page footer): "
        "'• Schema.org • V30.0 | 2026-03-19' — the vocabulary release the "
        "captured page states it is",
    ),
    "cloudflare-ai-crawl-control-manage-crawlers": (
        {"identity": {"pub_year": "2026"}},
        "corpus/kernel/cloudflare-ai-crawl-control-manage-crawlers.md line 6: 'Jul 28, 2026' "
        "— the docs page's own last-updated stamp, which is the date of the version "
        "captured; the page states no other date",
    ),
    "fcsm-23-02-a-framework-for-data-quality-case-studies": (
        {"identity": {
            "pub_year": "2023",
            "authors_or_org": ["Mirel LB", "Singpurwalla D", "Hoppe T", "Liliedahl E",
                               "Schmitt R", "Weber J"],
        }},
        "corpus/bulk/fcsm-23-02-a-framework-for-data-quality-case-studies.pdf page 1, the "
        "document's own 'Recommended citation': 'Mirel LB, Singpurwalla D, Hoppe T, "
        "Liliedahl E, Schmitt R, Weber J. 2023. A Framework for Data Quality: Case Studies, "
        "FCSM-23-02 Data Quality Framework Implementation Subcommittee, Federal Committee on "
        "Statistical Methodology. October 2023.'",
    ),
    "foundations-for-evidence-based-policymaking-act-of-2018-evid": (
        {"identity": {"pub_year": "2019", "authors_or_org": ["115th Congress"]}},
        "corpus/bulk/foundations-for-evidence-based-policymaking-act-of-2018-evid.pdf page 1 "
        "lines 1-3: '132 STAT. 5529 PUBLIC LAW 115–435—JAN. 14, 2019' / 'Public "
        "Law 115–435' / '115th Congress'. The statute names no author; the enacting "
        "body is the issuing body.",
    ),
    "m-25-05-phase-2-implementation-of-the-evidence-act-open-gove": (
        {"identity": {"pub_year": "2025",
                      "authors_or_org": ["Office of Management and Budget"]}},
        "corpus/bulk/m-25-05-phase-2-implementation-of-the-evidence-act-open-gove.pdf page 1: "
        "'EXECUTIVE OFFICE OF THE PRESIDENT / OFFICE OF MANAGEMENT AND BUDGET / WASHINGTON, "
        "D.C. 20503', 'January 15, 2025', 'M-25-05', 'FROM: Shalanda Young / Director'. The "
        "memorandum is issued by OMB; the signer is its Director, not its author.",
    ),
}

#: Cited documents whose missing field the document itself does not state. They keep the
#: manifest's own 'n.d.', which is the truthful value. Each was searched exhaustively this
#: session for a four-digit year (the two short pages were also read end to end) and no
#: publication, revision or copyright date appears anywhere in the captured page. Guessing
#: from the harvest timestamp would record when WE fetched it, not when the publisher issued
#: it — a different claim wearing the same field name.
NOT_STATED: dict[str, str] = {
    "anthropic-crawler-support-article":
        "pub_year — 33-line help-centre article; no date, no copyright line, no "
        "'last updated' stamp anywhere in the captured page",
    "bing-webmaster-guidelines":
        "pub_year — 184 lines; the only date is a forward-looking API retirement notice "
        "('August 31, 2026'), which dates an event the page announces, not the page",
    "openai-crawlers-bots":
        "pub_year — 490 lines; the page offers an RSS feed 'for updates to this page' "
        "and states no date of its own",
    "perplexity-crawlers":
        "pub_year — 62 lines; no date, copyright line or revision stamp",
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be appended; write nothing")
    args = ap.parse_args(argv)

    _, entries, _ = M._dixie_ledger()
    written = []
    for doc_id, (sections, provenance) in CORRECTIONS.items():
        entry = entries.get(doc_id)
        if entry is None:
            print(f"REFUSED: {doc_id} is not in the corpus ledger", file=sys.stderr)
            return 1
        before = {f"{s}.{f}": entry[s][f] for s, vs in sections.items() for f in vs}
        after = {f"{s}.{f}": v for s, vs in sections.items() for f, v in vs.items()}
        print(f"{doc_id}")
        for key in after:
            print(f"    {key}: {before[key]!r} -> {after[key]!r}")
        print(f"    provenance: {provenance}")
        if args.dry_run:
            continue
        event_id = M.metadata_update(doc_id, provenance=provenance, **sections)
        written.append((doc_id, event_id))
        print(f"    event {event_id}")

    print(f"\nnot corrected — the document does not state the field ({len(NOT_STATED)}):")
    for doc_id, why in NOT_STATED.items():
        print(f"  {doc_id}: {why}")

    if args.dry_run:
        print(f"\nDRY RUN — nothing written. {len(CORRECTIONS)} corrections pending.")
    else:
        print(f"\nappended {len(written)} metadata_corrected events to the evidence ledger")
        print("run `python -m kg.manifest rebuild` to project them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
