#!/usr/bin/env python3
"""Targets v5: the seven declared flagships enter the frame. **Zero spend. No network here.**

Task `cc_tasks/2026-09-10_scan_frame_v5.md` §2. `COMPUTED_FROM` v4: v4 is read, never rewritten,
and v5 is a new file. Three cycles of Findings hang off v4's rows and off the `doc_id`s in them;
a build that edited v4 in place would move the ground under measurements already taken.

**This build adds rows and changes nothing else.** Every v4 row is carried through byte-for-byte
(same `doc_id`, same `url`, same `selected_as`), and one `flagship` row is appended per body
whose declared landing page verified under §1. The only fields that move are the counts derived
from the rows and the `pending_operator_declaration` markers of the seven bodies that stop
pending.

**The declared URL is the surface, not the URL it redirects to.** APHIS's declared page 301s to
a different path on the same site. Decision 2 forbids substitution, and a redirect is a fact
about the surface rather than a correction to the declaration, so the row carries the declared
URL and records `verified_final_url` beside it. A cycle follows the redirect exactly as this
verification did.

**A refused page still enters.** BLS, BTS and SSA answer 403 to the identified client and have
across three cycles; decision 1 admits their surfaces marked `refused_at_declaration`. Dropping
them would restrict the instrument to the agencies that permit us.

    /opt/anaconda3/bin/python3 scripts/build_fss_targets_v5.py --dry-run
    /opt/anaconda3/bin/python3 scripts/build_fss_targets_v5.py
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan.manners import netloc_of, same_site                       # noqa: E402

TASK = "cc_tasks/2026-09-10_scan_frame_v5.md"
DECLARATIONS = "docs/design/fss_flagship_declarations.md"
VERSION = 5
V4 = REPO / "state" / "scan_targets_fss_2026-09.json"
VERIFICATION = REPO / "state" / "fss_flagship_verification_2026-09-10.json"
OUT = REPO / "state" / "scan_targets_fss_2026-09_v5.json"

#: Verdicts that put a surface in the frame. Anything else is decision 2's stop, and this build
#: refuses to run rather than dropping the body quietly — a frame that silently omits a body the
#: operator declared is worse than no v5.
ADMITTING = {"enters", "refused_at_declaration"}


def flagship_id(url: str) -> str:
    """`flagship:<netloc><path>` — the synthetic surface id (`scan.model.SYNTHETIC_PREFIXES`).

    The netloc alone will not do: a body may declare a second flagship later, and `home:` is
    already the netloc-keyed id for the same host. The path is what distinguishes the surface,
    so the path is in the id. Query and fragment are dropped: a declared landing page is a page.
    """
    parts = urllib.parse.urlsplit(url)
    return f"flagship:{parts.netloc.lower()}{parts.path or '/'}"


def flagship_rows(v4: dict, verification: dict) -> list:
    """One `flagship` row per verified declaration, on its body's own base row."""
    base_by_agency = {}
    for r in v4["rows"]:
        if r["surface_kind"] == "home":
            base_by_agency[r["agency"]] = r
    rows = []
    for v in verification["rows"]:
        body = v["body"]
        if v["verdict"] not in ADMITTING:
            raise SystemExit(f"FATAL: {body} verified as {v['verdict']}; decision 2 says the "
                             f"surface is NOT added and nothing is substituted. Re-declare "
                             f"and re-verify before building v5.")
        base = base_by_agency.get(body)
        if base is None:
            raise SystemExit(f"FATAL: {body} has no home row in v4; a flagship hangs on a "
                             f"body of the frame or on nothing")
        if not same_site(v["final_url"], base["host"]):
            raise SystemExit(f"FATAL: {body}'s page resolves off its own site: "
                             f"{v['final_url']} is not on {base['host']}")
        row = {"agency": body, "agency_name": base["agency_name"], "tier": base["tier"],
               "host": netloc_of(v["url"]), "parent_department": base["parent_department"],
               "surface_kind": "flagship",
               "url": v["url"],
               "doc_id": flagship_id(v["url"]),
               "selected_as": v["product"],
               "selection_source": f"operator declaration, {DECLARATIONS} (2026-09-10)",
               "declared_why": v["why"],
               "verified_at": verification["generated_at"],
               "verified_status": v["status"],
               "verified_method": "robots-first HEAD then GET through scan.manners.Fetcher"}
        if v["final_url"] != v["url"]:
            row["verified_final_url"] = v["final_url"]
        if v["verdict"] == "refused_at_declaration":
            row["refused_at_declaration"] = True
            row["refused_note"] = (
                "the host answered 403 to the identified, robots-compliant client at "
                "declaration time, as it has across three cycles. The surface is measured and "
                "the cycle records `error`/`refused`: the collector could not observe, which "
                "is never a statement that the product failed or passed (DD-052 §6).")
        rows.append(row)
    return rows


def build(v4: dict, verification: dict) -> dict:
    added = flagship_rows(v4, verification)
    entered = {r["agency"] for r in added}
    rows = list(v4["rows"])
    # Appended after the v4 rows, in declaration order: a diff of v5 against v4 is then exactly
    # the seven new lines plus the recomputed header.
    rows.extend(added)

    agencies = []
    for a in v4["agency_detail"]:
        if a["agency"] in entered:
            a = {**a, "declared_surfaces": a["declared_surfaces"] + 1,
                 "pending_operator_declaration": False, "marker": None,
                 "declaration_source": f"{DECLARATIONS} (2026-09-10)"}
        agencies.append(a)
    pending = sorted(a["agency"] for a in agencies if a["pending_operator_declaration"])

    doc = {k: v for k, v in v4.items()
           if k not in ("rows", "agency_detail", "generated_at")}
    doc.update({
        "task": TASK, "computed_from_task": v4["task"],
        "targets_version": VERSION, "derived_from_version": v4["targets_version"],
        "derived_from": "scan_targets_fss_2026-09_v4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "declarations": DECLARATIONS,
        "verification": str(VERIFICATION.relative_to(REPO)),
        "flagships_declared_2026_09_10": sorted(entered),
        "flagships_refused_at_declaration": sorted(
            r["agency"] for r in added if r.get("refused_at_declaration")),
        "surfaces": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["surface_kind"] == k)
                    for k in sorted({r["surface_kind"] for r in rows})},
        "doc_id_rows_not_admitted": sorted(r["doc_id"] for r in rows
                                           if r.get("doc_id") and r.get("not_admitted")),
        "agencies_pending_operator_declaration": pending,
        "agency_detail": agencies, "rows": rows})
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if not VERIFICATION.is_file():
        raise SystemExit(f"FATAL: {VERIFICATION} does not exist; §1 verifies before §2 builds, "
                         f"and a frame built from an unverified declaration is a guess")
    doc = build(json.loads(V4.read_text(encoding="utf-8")),
                json.loads(VERIFICATION.read_text(encoding="utf-8")))
    brief = {k: v for k, v in doc.items()
             if k not in ("rows", "agency_detail", "hosts", "carried_from_cycle_1",
                          "site_keys")}
    print(json.dumps(brief, indent=1))
    if a.dry_run:
        for r in doc["rows"]:
            if r["surface_kind"] == "flagship" and r.get("verified_at"):
                print(f"  + {r['agency']:12s} {r['doc_id']}")
        return 0
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
