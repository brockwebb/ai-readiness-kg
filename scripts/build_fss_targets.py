#!/usr/bin/env python3
"""Targets from the Enterprise Data Inventory, not from scraping. **Zero model spend.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §2 as REPLACED by `..._ADDENDUM-02.md`. The rule
this replaces scraped agency home pages for anchor substrings and its own output falsified it;
`assessment/harness/scan/frame.py` carries that history. What runs now reads each department's
own DCAT-US declaration at `/data.json` (OPEN Government Data Act, 44 U.S.C. 3511).

**Network:** one GET per candidate inventory host, at most two per Tier A agency and
de-duplicated across agencies that share a department, plus nothing at all for Tier B and Tier
C (their probes are §3's). Identified UA, 1 req/s per host, robots obeyed.

**Which hosts carry an inventory is itself derived, and the derivation is the weak point.**
The department -> domain mapping is on NEITHER named roster source: the ICSP charter and the
statspolicy.gov About page both name departments in prose and neither carries a URL for one.
So the rule probes the agency's own host and its registrable domain and records which served.
Where a department's domain is not the agency's registrable domain — `census.gov` sits under
Commerce, `bls.gov` under Labor — the result is a RECORDED null, never an invented host. The
proper resolver is the organization list at `catalog.data.gov`, and it is named for the next
task rather than reached for here.

    /opt/anaconda3/bin/python3 scripts/build_fss_targets.py --dry-run
    /opt/anaconda3/bin/python3 scripts/build_fss_targets.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

from scan import frame, load_params                                 # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
ADDENDUM = "cc_tasks/2026-09-08_scan_frame_fss_ADDENDUM-02.md"
ROSTER = REPO / "state" / "fss_roster_2026-09.json"
OUT = REPO / "state" / "scan_targets_fss_2026-09.json"
SHORTLIST = REPO / "docs" / "design" / "fss_flagship_shortlist.md"
EVIDENCE = REPO / "corpus" / "evidence" / "frame"
EPOCH = "scan-fss-2026-09"
CYCLE1_TARGETS = REPO / "state" / "scan_targets_2026-09.json"


def _slug(text: str, n: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:n].strip("-")


def retain(body: bytes) -> tuple:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    d = hashlib.sha256(body).hexdigest()
    p = EVIDENCE / d[:2] / d
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_bytes(body)
    return d, str(p.relative_to(REPO))


def cycle1_rows() -> list:
    """The operator's cycle-1 declaration, which ADDENDUM-02 §2.b makes the flagship source."""
    if not CYCLE1_TARGETS.is_file():
        return []
    return json.loads(CYCLE1_TARGETS.read_text(encoding="utf-8"))["rows"]


def cycle1_code_for(entry: dict, rows: list) -> str | None:
    """The cycle-1 agency CODE for a roster entry, matched on host.

    On the HOST, not on a derived acronym. My first pass derived codes from the unit name and
    produced `NAHMAPHIS`, `SAMHSACBHSQ` and `RES`, none of which is any cycle-1 code, so only
    4 of 26 cycle-1 surfaces carried forward and the rest looked dropped. The host is the one
    thing both records state the same way.
    """
    host = (entry.get("host") or "").lower()
    if not host:
        return None
    for r in rows:
        if urllib.parse.urlsplit(r.get("url") or "").netloc.lower() == host:
            return str(r.get("agency"))
    for r in rows:                                   # registrable-domain fallback, recorded
        if frame.registrable_domain(urllib.parse.urlsplit(r.get("url") or "").netloc.lower()) \
                == frame.registrable_domain(host):
            return str(r.get("agency"))
    return None


def code_for(entry: dict, rows: list, taken: set) -> tuple:
    """(code, source). Cycle 1's code where the agency is one cycle 1 measured — so its
    `doc_id`s and its two cycles of Findings stay attached — else derived from the unit name.
    """
    got = cycle1_code_for(entry, rows)
    if got and got.upper() not in taken:
        return got.upper(), "cycle-1 target list, matched on host"
    words = [w for w in re.sub(r"[^A-Za-z ]", " ", entry["unit_name"]).split()
             if w[:1].isupper() and w.lower() not in
             ("of", "the", "and", "for", "department", "office", "division", "board",
              "governors", "system", "administration", "service", "services")]
    base = ("".join(w[0] for w in words) or _slug(entry["unit_name"])[:6]).upper()
    code, i = base, 2
    while code in taken:
        code, i = f"{base}{i}", i + 1
    return code, "derived from the unit name (not measured in cycle 1)"


def fetch_inventory(fetcher, host: str, params: dict, cache: dict) -> dict:
    """One `/data.json` probe per host, cached across the agencies that share a department."""
    if host in cache:
        return cache[host]
    url = f"https://{host}{params['frame']['edi']['path']}"
    try:
        r = fetcher.raw_get(url)
    except Exception as exc:                                        # noqa: BLE001
        from scan.errors import classify_exception
        cache[host] = {"url": url, "status": None, "served": False,
                       "error_class": classify_exception(exc),
                       "error": f"{type(exc).__name__}: {exc}"}
        return cache[host]
    out = {"url": url, "status": r["status"], "bytes": len(r["body"]),
           "content_type": (r["headers"].get("content-type") or "").split(";")[0].strip(),
           "served": False, "catalog": None}
    if r["status"] == 200 and r["body"]:
        try:
            cat = json.loads(r["body"].decode("utf-8", "replace"))
        except Exception as exc:                                    # noqa: BLE001
            out["parse_error"] = f"{type(exc).__name__}: {exc}"
        else:
            if isinstance(cat, dict) and frame.datasets(cat):
                d, path = retain(r["body"])
                out.update({"served": True, "catalog": cat, "sha256": d, "retained": path,
                            "datasets": len(frame.datasets(cat))})
            else:
                out["parse_error"] = "200 at /data.json but no DCAT `dataset` array"
    cache[host] = out
    return out


def build(params: dict, roster: dict, fetcher) -> dict:
    prior = cycle1_rows()
    cache: dict = {}
    agencies, rows, taken = [], [], set()

    for entry in roster["tier_a"]:
        code, code_source = code_for(entry, prior, taken)
        taken.add(code)
        rec = {"agency": code, "agency_code_source": code_source,
               "agency_name": entry["unit_name"], "tier": "A",
               "parent_department": entry["parent_department"], "host": entry["host"],
               "home_url": entry["home_url"], "home_url_source": entry["home_url_source"]}

        inv, probed = None, []
        for host in frame.edi_hosts(entry["host"] or "", params):
            got = fetch_inventory(fetcher, host, params, cache)
            probed.append({"host": host, "status": got.get("status"),
                           "served": got["served"], "sha256": got.get("sha256"),
                           "datasets": got.get("datasets"),
                           "note": got.get("parse_error") or got.get("error")})
            print(f"  {code:8s} /data.json {host:28s} HTTP {got.get('status')} "
                  f"{'EDI' if got['served'] else '-'}", flush=True)
            if got["served"]:
                inv = got
                break
        rec["edi_probed"] = probed
        rec["edi_host"] = urllib.parse.urlsplit(inv["url"]).netloc if inv else None
        rec["edi_sha256"] = inv.get("sha256") if inv else None
        rec["edi_retained"] = inv.get("retained") if inv else None

        if inv:
            names = [entry["unit_name"], entry["name"]]
            got = frame.for_agency(frame.datasets(inv["catalog"]), names)
            rec.update({"edi_datasets_for_agency": got["n"],
                        "edi_matched_by": got["matched_by"],
                        "edi_datasets_total": inv["datasets"]})
            machine = frame.api_entry_point(got["datasets"], params)
            rec["shortlist"] = frame.shortlist(got["datasets"], params)
        else:
            rec.update({"edi_datasets_for_agency": 0,
                        "edi_matched_by": {}, "edi_datasets_total": 0})
            machine = {"url": None, "marker": "no_enterprise_data_inventory_found"}
            rec["shortlist"] = []
        rec["machine"] = machine

        flags = frame.declared_flagships(code, prior, params)
        rec["flagships"] = flags
        agencies.append(rec)

        base = {k: rec[k] for k in ("agency", "agency_name", "tier", "host",
                                    "parent_department")}
        for f in flags["flagships"]:
            rows.append({**base, "surface_kind": "flagship", "url": f["url"],
                         "doc_id": f["doc_id"], "selected_as": f["selected_as"],
                         "selection_source": f["selection_source"],
                         "edi_sha256": None, "carried_from_cycle_1": True})
        if machine.get("url"):
            rows.append({**base, "surface_kind": "machine", "url": machine["url"],
                         "doc_id": f"scan-{code.lower()}-machine-edi",
                         "selected_as": f"API entry point declared in the "
                                        f"{rec['edi_host']} Enterprise Data Inventory",
                         "selection_source": machine["selection_source"],
                         "edi_sha256": rec["edi_sha256"], "carried_from_cycle_1": False})
        rows.append({**base, "surface_kind": "well_known",
                     "url": f"https://{rec['host']}/robots.txt", "doc_id": None,
                     "selected_as": "agency-level well-known set (synthetic surface)",
                     "selection_source": "frame: one synthetic host surface per Tier A agency",
                     "edi_sha256": None, "carried_from_cycle_1": False})

    tier_b = [{"name": e["name"], "tier": "B", "host": e.get("host"),
               "no_host_on_source": True,
               "note": ("neither named roster source carries a URL for a department without a "
                        "recognized statistical unit, so this row has no host to probe; "
                        "resolving it needs the catalog.data.gov organization list")}
              for e in roster["tier_b"]]
    tier_c = [{**t, "tier": "C"} for t in roster.get("tier_c", [])]

    pending = [a["agency"] for a in agencies if a["flagships"]["pending"]]
    return {
        "task": TASK, "addendum": ADDENDUM, "epoch": EPOCH,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "derived_from": "fss_roster_2026-09",
        "source_type": "product_surface",
        "construct_arm": "publication_actionability",
        "agencies": len(roster["tier_a"]),
        "surfaces": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["surface_kind"] == k)
                    for k in ("flagship", "machine", "well_known")},
        "edi_hosts_serving": sorted({a["edi_host"] for a in agencies if a["edi_host"]}),
        "agencies_with_edi": sum(1 for a in agencies if a["edi_host"]),
        "agencies_with_api_distribution": sum(
            1 for a in agencies if (a["machine"] or {}).get("url")),
        "agencies_flagships_pending": pending,
        "flagships_declared": sum(len(a["flagships"]["flagships"]) for a in agencies),
        "tier_b": tier_b, "tier_c": tier_c,
        "agency_detail": agencies, "rows": rows}


def write_shortlist(doc: dict) -> str:
    """The operator's shortlist. **Offered, never selected from** (ADDENDUM-02 §2.b)."""
    out = [
        "# Flagship shortlist for operator declaration",
        "",
        f"Generated by `scripts/build_fss_targets.py` from each department's `/data.json`",
        f"Enterprise Data Inventory. Task {doc['task']}, {doc['addendum']} §2.b.",
        "",
        "**This is a shortlist, not a selection.** The inventory carries no field that ranks",
        "datasets, so ranking them would be a value judgment the source does not make. The rows",
        "below are ordered by the inventory's own `modified` date, most recent first, purely so",
        "a human has somewhere to start. Nothing here enters the target list until the operator",
        "declares it; until then these agencies carry a machine entry point and tier-0 host",
        "probes only, marked `flagships_pending_operator_declaration`.",
        "",
        f"Agencies pending: **{len(doc['agencies_flagships_pending'])}** of {doc['agencies']} "
        f"— {', '.join(doc['agencies_flagships_pending']) or 'none'}.",
        "",
    ]
    for a in doc["agency_detail"]:
        if not a["flagships"]["pending"]:
            continue
        out += [f"## {a['agency']} — {a['agency_name']}", "",
                f"Parent: {a['parent_department']}. Host: `{a['host']}`. "
                f"Inventory: `{a['edi_host'] or 'none found'}`"
                + (f" (sha256 `{a['edi_sha256'][:12]}…`, "
                   f"{a['edi_datasets_for_agency']} of {a['edi_datasets_total']} datasets "
                   f"attributed to this agency)" if a["edi_sha256"] else ""), ""]
        if not a["shortlist"]:
            out += ["_No dataset in any reachable inventory is attributed to this agency._", ""]
            continue
        out += ["| modified | title | landing page |", "|---|---|---|"]
        for r in a["shortlist"]:
            out.append(f"| {r['modified'][:10]} | {r['title'][:70]} | {r['landing_page']} |")
        out.append("")
    SHORTLIST.parent.mkdir(parents=True, exist_ok=True)
    SHORTLIST.write_text("\n".join(out) + "\n", encoding="utf-8")
    return str(SHORTLIST.relative_to(REPO))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    params = load_params()
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    from scan.manners import Fetcher
    doc = build(params, roster, Fetcher(params))
    brief = {k: v for k, v in doc.items()
             if k not in ("rows", "agency_detail", "tier_b", "tier_c")}
    print(json.dumps(brief, indent=1))
    if a.dry_run:
        for r in doc["rows"]:
            print(f"  {r['agency']:8s} {r['surface_kind']:11s} "
                  f"{str(r['selected_as'])[:44]:46s} {r['url'][:58]}")
        return 0
    doc["shortlist_path"] = write_shortlist(doc)
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)} and {doc['shortlist_path']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
