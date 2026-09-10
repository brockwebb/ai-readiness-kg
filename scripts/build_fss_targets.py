#!/usr/bin/env python3
"""The target list, DECLARED. **Zero model spend. No network in the build itself.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §2 as finally settled by `..._ADDENDUM-05.md`,
which withdraws ADDENDUM-02, -03 and -04 and removes Tier B.

**Nothing here selects a surface.** Three rules were tried and all three were derivations the
operator never asked for: anchor-substring scraping of agency home pages (its own output
falsified it), the Enterprise Data Inventory (blocked on a department -> domain mapping), and
the CISA registry plus data.gov's harvest API (the registry has no primary-domain field and the
API is gone). Tier 0 needs none of it. What a tier-0 leg asks — is `robots.txt` served, are the
discovery files there, does a deep link behave, is the machine layer declared, do the declared
and enforced layers agree — is answered against a HOST, and the host is on the roster.

So the frame is 16 Tier A agencies plus 3 Tier C reference hosts, and every surface is either

* a **roster host** — the agency's or reference host's home, which the roster already carries
  from its own parsed source; or
* an **operator declaration** — the cycle-1 target list, carried forward with its `doc_id`s so
  two cycles of Findings stay attached to the surface they were measured on.

An agency with no cycle-1 declaration carries its home and its probes and is marked
`pending_operator_declaration`; `docs/design/fss_flagship_shortlist.md` is where that
declaration gets made. A guess is not a declaration and this script does not make one.

`assessment/harness/scan/frame.py` still exists and is still tested, and **nothing in this
build calls it** (ADDENDUM-05). Its history is why.

    /opt/anaconda3/bin/python3 scripts/build_fss_targets.py --dry-run
    /opt/anaconda3/bin/python3 scripts/build_fss_targets.py
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

from scan import load_params                                        # noqa: E402
from scan.manners import site_key                                    # noqa: E402
from scan.model import SYNTHETIC_PREFIXES                            # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
ADDENDUM = "cc_tasks/2026-09-08_scan_frame_fss_ADDENDUM-05.md"
#: v2, per `cc_tasks/2026-09-08_scan_run_3b.md` decisions 1 and 3.
TASK_V2 = "cc_tasks/2026-09-08_scan_run_3b.md"
VERSION = 4
ROSTER = REPO / "state" / "fss_roster_2026-09.json"
CYCLE1 = REPO / "state" / "scan_targets_2026-09.json"
OUT = REPO / "state" / "scan_targets_fss_2026-09.json"
EPOCH = "scan-fss-2026-09"

#: Out of the frame from here on. Its two cycles stay on the log, immutable, and are excluded
#: from every FSS denominator: it is not a federal publisher, and the tier-0 comparison holds
#: for federal hosts under ONE legal regime, which is what makes it a comparison rather than
#: decoration. Numerically nothing moves — it was `error` on every leg in both cycles.
OUT_OF_FRAME = {"STATCAN"}


def host_of(url: str) -> str:
    return urllib.parse.urlsplit(url or "").netloc.lower()


def cycle1_rows() -> list:
    if not CYCLE1.is_file():
        return []
    return [r for r in json.loads(CYCLE1.read_text(encoding="utf-8"))["rows"]
            if r.get("doc_id") and str(r.get("agency", "")).upper() not in OUT_OF_FRAME]


def build(params: dict, roster: dict) -> dict:
    declared = cycle1_rows()
    by_host: dict = {}
    for r in declared:
        by_host.setdefault(host_of(r["url"]), []).append(r)

    rows, agencies, hosts = [], [], []

    for e in roster["tier_a"]:
        host = (e.get("host") or "").lower()
        mine = by_host.get(host, [])
        code = (str(mine[0]["agency"]).upper() if mine
                else "".join(w[0] for w in e["unit_name"].split() if w[:1].isupper())[:10]
                or "UNKNOWN")
        base = {"agency": code, "agency_name": e["unit_name"], "tier": "A", "host": host,
                "parent_department": e["parent_department"]}
        hosts.append({"host": host, "tier": "A", "agency": code,
                      "site_key": site_key(host)})
        # The home row: every host gets one, and it is where the tier-0 legs land.
        rows.append({**base, "surface_kind": "home", "url": e["home_url"],
                     "doc_id": f"home:{host}",
                     "selected_as": "agency home",
                     "selection_source": "roster host (fss_roster_2026-09, "
                                         f"{e['home_url_source']})"})
        for r in mine:
            rows.append({**base, "surface_kind": r["surface_kind"], "url": r["url"],
                         "doc_id": r["doc_id"], "selected_as": r.get("selected_as"),
                         "selection_source": "operator declaration, cycle 1 target list",
                         "carried_from_cycle_1": True})
        rows.append({**base, "surface_kind": "well_known",
                     "url": f"https://{host}/robots.txt", "doc_id": f"host:{host}",
                     "selected_as": "agency-level well-known set (synthetic surface)",
                     "selection_source": "roster host: one synthetic host surface per agency"})
        agencies.append({**base, "declared_surfaces": len(mine),
                         "pending_operator_declaration": not mine,
                         "marker": None if mine else "pending_operator_declaration"})

    for t in roster.get("tier_c", []):
        host = t["host"].lower()
        base = {"agency": t["name"], "agency_name": t["name"], "tier": "C", "host": host,
                "parent_department": None}
        hosts.append({"host": host, "tier": "C", "agency": t["name"],
                      "site_key": site_key(host)})
        machine_netloc = urllib.parse.urlsplit(t["machine_entry_point"]).netloc.lower()
        # The machine entry point sits on its OWN netloc — catalog.data.gov, data.nist.gov,
        # open.gsa.gov — which v1 left out of `hosts[]`, so `manners.on_roster_host` would
        # have refused the very surfaces the operator declared. The frame is still 19 hosts in
        # the agency sense; the roster is 22 netlocs (`..._scan_run_3b.md` decision 1).
        # The machine entry point's site key is its BODY'S, not its own. `catalog.data.gov` is
        # a netloc ON the data.gov site, and keying it to itself would report 22 sites for 19
        # bodies and quietly re-create the netloc bound this decision replaces. `netloc_of`
        # already records which home it belongs to; the key follows it.
        hosts.append({"host": machine_netloc, "tier": "C", "agency": t["name"],
                      "netloc_of": host, "site_key": site_key(host)})
        for kind, url, why in (
                ("home", t["home"], "roster host (Tier C, operator declaration 2026-09-08)"),
                ("machine", t["machine_entry_point"],
                 "declared machine entry point (Tier C, operator declaration 2026-09-08)")):
            netloc = urllib.parse.urlsplit(url).netloc.lower()
            rows.append({**base, "surface_kind": kind, "url": url,
                         "doc_id": (f"home:{netloc}" if kind == "home"
                                    else f"machine:{netloc}"),
                         "host": netloc,
                         "selected_as": t["reason"], "selection_source": why,
                         "tier0_legs_only": True, "restriction": t["restriction"]})
        rows.append({**base, "surface_kind": "well_known",
                     "url": f"https://{host}/robots.txt", "doc_id": f"host:{host}",
                     "selected_as": "host-level well-known set (synthetic surface)",
                     "selection_source": "roster host: one synthetic host surface per host",
                     "tier0_legs_only": True, "restriction": t["restriction"]})

    # A doc_id row that is NOT admitted cannot produce a Finding — `OBSERVED_ON` requires a
    # `:Document` — so the target list says so on the row rather than letting a reader assume
    # every declared surface is measurable. The one case is `scan-eia-flagship-2-eia-survey-
    # forms`: `eia.gov/robots.txt` disallows it for this UA and the scanner obeys the file it
    # measures. That is a recorded property of the surface, not a gap in the frame.
    from kg import manifest as _manifest
    admitted = {e["doc_id"] for e in _manifest._load_entries()}
    for r in rows:
        # Only a CORPUS doc_id can be unadmitted. `host:`/`home:`/`machine:` are synthetic
        # surface ids — there is no Document to admit and none is required, exactly as the
        # well-known row has worked since cycle 1.
        if (r.get("doc_id") and not str(r["doc_id"]).startswith(SYNTHETIC_PREFIXES)
                and r["doc_id"] not in admitted):
            r["not_admitted"] = "robots_disallowed"
            r["not_admitted_note"] = (
                "the host's robots.txt disallows this path for the scanner's identified UA; "
                "no Document, so no Finding. RFC 9309 obeyed.")

    pending = sorted(a["agency"] for a in agencies if a["pending_operator_declaration"])
    return {
        "task": TASK_V2, "supersedes_task": TASK, "addendum": ADDENDUM,
        "targets_version": VERSION, "derived_from_version": VERSION - 1, "epoch": EPOCH,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "derived_from": "fss_roster_2026-09",
        "source_type": "product_surface",
        "construct_arm": "publication_actionability",
        "frame": "16 OMB-recognized statistical agencies and units (Tier A) + 3 reference "
                 "hosts (Tier C, tier-0 legs only). No Tier B. Nothing outside these hosts.",
        "tier_a_agencies": sum(1 for h in hosts if h["tier"] == "A"),
        "tier_c_hosts": len({h["agency"] for h in hosts if h["tier"] == "C"}),
        "tier_c_netlocs": sum(1 for h in hosts if h["tier"] == "C"),
        # v4 (`cc_tasks/2026-09-09_manners_closeout.md` decision 1): every host carries its
        # SITE KEY, the roster host with one leading `www.` stripped. v3 carried the Public
        # Suffix List's registrable domain and it merged ERS, NASS and APHIS into `usda.gov`;
        # the key keeps them apart, which is what the frame means by a body. The contact bound
        # is the site key; the denominator stays the body (DD-063).
        "site_bound": {"definition": "roster host with one leading www. stripped",
                       "match": "equal to the key, or ending in '.' + the key "
                                "(RFC 6265 §5.1.3)"},
        "site_keys": sorted({h["site_key"] for h in hosts}),
        "site_count": len({h["site_key"] for h in hosts}),
        "hosts": hosts, "netloc_count": len(hosts),
        "host_count": len({h.get("netloc_of") or h["host"] for h in hosts}),
        "surfaces": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["surface_kind"] == k)
                    for k in sorted({r["surface_kind"] for r in rows})},
        "carried_from_cycle_1": sorted(r["doc_id"] for r in rows if r.get("doc_id")),
        "doc_id_rows_not_admitted": sorted(r["doc_id"] for r in rows
                                           if r.get("doc_id") and r.get("not_admitted")),
        "agencies_pending_operator_declaration": pending,
        "statcan_excluded": sorted(OUT_OF_FRAME),
        "agency_detail": agencies, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    doc = build(load_params(), json.loads(ROSTER.read_text(encoding="utf-8")))
    brief = {k: v for k, v in doc.items()
             if k not in ("rows", "agency_detail", "hosts", "carried_from_cycle_1")}
    print(json.dumps(brief, indent=1))
    print(f"carried forward: {len(doc['carried_from_cycle_1'])} cycle-1 doc_ids")
    if a.dry_run:
        for r in doc["rows"]:
            print(f"  {r['tier']} {str(r['agency'])[:12]:14s} {r['surface_kind']:11s} "
                  f"{str(r['url'])[:64]}")
        return 0
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
