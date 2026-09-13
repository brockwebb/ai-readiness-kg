#!/usr/bin/env python3
"""The one-host frame for the self-scan: this publication, and the authority RFC 9309 gives it.

`cc_tasks/2026-09-13_self_row.md` decision 1. **Zero model spend, no network.**

**Two rows, and the pair IS the finding.** The instrument's six tier-0 legs do not all read the
same object, and on a project Pages site they cannot:

* `home:<authority>` — the SITE, `https://<authority>/<project>/`, which is this publication.
  A Tier C row, so it carries the tier-0 legs and sits in no Tier A denominator (DD-059) — the
  same treatment the three federal reference hosts get, for the same reason: it is not a
  statistical agency and belongs on no agencies × legs matrix.
* `host:<authority>` — the well-known surface, `https://<authority>/robots.txt`. RFC 9309 §2.3
  binds a robots.txt to an AUTHORITY (scheme, host, port), not to a path prefix, so this row is
  about `<authority>` and NOT about this publication. `run.py::targets` gives a `well_known` row
  the host legs (A12) and points its probe at the home row, which is what makes A12's declared
  and enforced layers a comparison of the same path.

So A4, A5, A11-declared and A12 read the authority root — a path that belongs to a user-site
repository this publication does not own — while A10 and G1-D read the published tree. That
asymmetry is not a defect in this frame; it is the measurement
(`cc_tasks/2026-09-12_publish_l0_RESULT.md` §3), and the frame is built to make it visible per
leg rather than average it away.

**Everything is derived from the declaration.** The site URL, the authority and the project path
come from `docs/reports/publication.yaml`; nothing about this host is typed here, so a custom
domain or a user-site move changes one declaration and this frame follows.

    /opt/anaconda3/bin/python3 scripts/build_self_frame.py --cycle self_2026-09-13 [--dry-run]

Refuses a site URL that is not absolute https, and refuses to overwrite an existing frame: a
frame is the record of what a cycle was pointed at, and a cycle that silently re-pointed is a
cycle whose findings are about something else.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
TASK = "cc_tasks/2026-09-13_self_row.md"

#: The agency key for the self row. Not an agency; the matrix column it would occupy is the one
#: DD-059 keeps reference hosts out of, and this name says so wherever it is printed.
AGENCY = "self"


def publication() -> dict:
    import yaml
    return yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))


def frame(pub: dict, cycle: str) -> dict:
    site_url = pub["site_url"]
    parts = urllib.parse.urlsplit(site_url)
    if parts.scheme != "https" or not parts.netloc:
        raise SystemExit(f"FATAL: site_url {site_url!r} is not an absolute https URL; the frame "
                         f"cannot name an authority")
    authority = parts.netloc
    authority_root = f"https://{authority}/"
    is_project_site = parts.path.strip("/") != ""

    rows = [
        {"agency": AGENCY, "agency_name": pub["title"], "tier": "C",
         "host": authority, "parent_department": None,
         "surface_kind": "home", "url": site_url,
         "doc_id": f"home:{authority}",
         "selected_as": "this publication, as the host serves it",
         "selection_source": f"docs/reports/publication.yaml site_url ({TASK} decision 1)",
         "tier0_legs_only": True,
         "restriction": ("the publication under measurement by its own instrument: tier-0 legs "
                         "only, never in a Tier A or Tier B denominator and never on the "
                         "agencies x legs matrix (DD-059)")},
        {"agency": AGENCY, "agency_name": pub["title"], "tier": "C",
         "host": authority, "parent_department": None,
         "surface_kind": "well_known", "url": f"{authority_root}robots.txt",
         "doc_id": f"host:{authority}",
         "selected_as": "the authority's well-known set (synthetic surface)",
         "selection_source": ("RFC 9309 section 2.3: a robots.txt governs the AUTHORITY it is "
                             "served from, not a path prefix, so the well-known surface of a "
                             "project site is the authority root"),
         "tier0_legs_only": True,
         "restriction": ("this row is about the AUTHORITY and not about this publication: on a "
                         "project site the authority root belongs to a user-site repository "
                         "this publication does not own")},
    ]
    return {
        "task": TASK, "cycle": cycle, "targets_version": 1, "derived_from_version": None,
        "epoch": datetime.now(timezone.utc).strftime("%Y-%m"),
        "derived_from": "docs/reports/publication.yaml",
        "source_type": "self", "construct_arm": "self_measurement",
        "frame": ("one publication and the authority that serves it. The instrument applied to "
                  "itself, through the same frame shape every other host is measured in."),
        "site_url": site_url,
        "authority": authority,
        "authority_root": authority_root,
        "is_project_site": is_project_site,
        "authority_is_this_publication": not is_project_site,
        "rfc_9309_note": (
            "A project Pages site cannot serve an effective robots.txt, llms.txt or "
            "/.well-known/ probe: RFC 9309 section 2.3 scopes robots.txt to the authority, and "
            f"the authority here is the whole of {authority}. The legs that read the authority "
            f"root are therefore measuring {authority}; the legs that read {site_url} are "
            "measuring this publication. Every Finding records which."),
        "tier_a_agencies": 0, "tier_c_hosts": 1, "tier_c_netlocs": [authority],
        "site_keys": [authority], "site_count": 1,
        "hosts": [authority], "host_count": 1, "netloc_count": 1,
        "surfaces": len(rows),
        "by_kind": {"home": 1, "well_known": 1},
        "doc_id_rows_not_admitted": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/build_self_frame.py",
        "note": ("Both rows are SYNTHETIC surfaces (`home:` / `host:` doc_ids), so neither needs "
                 "a corpus admission and no Observation lands on a missing Document. The tier is "
                 "C for the same reason the federal reference hosts are: tier-0 legs, no Tier A "
                 "denominator, no agencies x legs matrix."),
        "rows": rows,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", required=True, help="the cycle this frame is built for")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    doc = frame(publication(), a.cycle)
    out = REPO / "state" / f"scan_targets_{a.cycle}.json"
    if a.dry_run:
        print(json.dumps(doc, indent=1))
        print(f"(dry run) would write {out.relative_to(REPO)}")
        return 0
    if out.exists():
        raise SystemExit(
            f"FATAL: {out.relative_to(REPO)} already exists. A frame is the record of what a "
            f"cycle was pointed at; overwriting one silently re-points a measurement. Give the "
            f"cycle a new name (CLAUDE.md section 11).")
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in doc.items() if k != "rows"}, indent=1))
    print(f"-> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
