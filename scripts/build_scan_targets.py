#!/usr/bin/env python3
"""Select the scan targets from each agency's own listing, and admit them. **Zero model spend.**

Task `cc_tasks/2026-09-06_scan_targets.md` §3.1 and §3.2. The selection rule is written in
`targets.yaml` **before** any product was chosen, because §3.1 is explicit: *"Do not choose
products because they look good or bad for the instrument; choose by the agency's own
'principal products' or 'featured data' listing, and cite where each came from."* A selection
made by an author reading fourteen listings and picking what seems representative is not a
sample, it is a preference; every row here instead carries the listing URL it was read from and
the verbatim anchor text it was read as.

Three surface kinds per agency (§3.1):
  * `flagship`  — the page a human would call the product.
  * `machine`   — the documented API root, bulk-download index, or `data.json` catalog.
  * `well_known`— the agency-level `/robots.txt`, `/sitemap*.xml`, `/llms.txt`, `/data.json`,
                  `/.well-known/` set. A SYNTHETIC surface, one per host, not a document, and
                  therefore not admitted to the manifest — there is no document to admit.

Admission (§3.2): every flagship and machine entry point is fetched once, hashed, and written
to `corpus/manifest.json` under epoch `scan-2026-09`. `OBSERVED_ON` requires a `:Document`, so
a target that is not admitted cannot be scanned; an unobservable host's targets are admitted
all the same, with the refusal recorded, because a surface we were refused is still a surface
the instrument has something to say about.

    /opt/anaconda3/bin/python3 scripts/build_scan_targets.py --dry-run
    /opt/anaconda3/bin/python3 scripts/build_scan_targets.py --admit
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

import yaml                                                        # noqa: E402
from scan import load_params                                       # noqa: E402
from scan.collectors import http                                   # noqa: E402
from scan.manners import Fetcher                                   # noqa: E402

TASK = "cc_tasks/2026-09-06_scan_targets.md"
ROSTER = REPO / "assessment" / "harness" / "scan" / "targets.yaml"
PREFLIGHT = REPO / "state" / "scan_preflight_2026-09.json"
OUT = REPO / "state" / "scan_targets_2026-09.json"
MAX_FLAGSHIPS = 2


def _slug(text: str, n: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:n].strip("-")


def _is_product(text: str, href: str, listing_url: str, cfg: dict) -> bool:
    low = text.lower()
    if any(t in low for t in cfg["section_link_tokens"]):
        return False
    if any(t in low for t in cfg["reject_link_tokens"]):
        return False
    # A link back to the listing, or shallower than it, is a section and not a product.
    lp = urllib.parse.urlsplit(listing_url).path.rstrip("/")
    hp = urllib.parse.urlsplit(href).path.rstrip("/")
    return hp != lp and len(hp) > len(lp) and len(text.split()) >= 2


def select(row: dict, cfg: dict) -> dict:
    listing = row["listing_used"]
    flagships, machine = [], None
    for c in row["candidates"]:
        text, href = c["text"], c["href"]
        low = (text + " " + href).lower()
        if machine is None and any(t in low for t in cfg["machine_entry_tokens"]):
            machine = {"url": href, "anchor_text": text, "how": "machine_entry_tokens"}
            continue
        if len(flagships) < MAX_FLAGSHIPS and _is_product(text, href, listing, cfg):
            flagships.append({"url": href, "anchor_text": text})
    if machine is None and row.get("data_json_status") == 200:
        machine = {"url": urllib.parse.urljoin(row["host"], "/data.json"),
                   "anchor_text": None, "how": "host serves /data.json"}
    return {"flagships": flagships, "machine": machine}


def build(cfg: dict, pre: dict, fetcher, admit: bool) -> list:
    rows = []
    for r in pre["rows"]:
        sel = select(r, cfg)
        base = {"agency": r["agency"], "agency_name": r["name"],
                "department": r.get("department"), "spd1_segment": r.get("spd1_segment"),
                "host": r["host"], "unobservable": r["unobservable"],
                "listing_url": r["listing_used"],
                "selection_source": r["listing_selection_source"],
                "listing_unreadable_reason": r.get("listing_unreadable_reason")}
        for i, f in enumerate(sel["flagships"], 1):
            rows.append({**base, "surface_kind": "flagship", "url": f["url"],
                         "selected_as": f["anchor_text"],
                         "doc_id": f"scan-{r['agency'].lower()}-flagship-{i}-"
                                   f"{_slug(f['anchor_text'])}"})
        if sel["machine"]:
            m = sel["machine"]
            rows.append({**base, "surface_kind": "machine", "url": m["url"],
                         "selected_as": m["anchor_text"] or m["how"],
                         "selection_source": (r["listing_selection_source"]
                                              if m["anchor_text"] else m["how"]),
                         "doc_id": f"scan-{r['agency'].lower()}-machine"})
        # The well-known set is synthetic: one per host, not a document, not admitted.
        rows.append({**base, "surface_kind": "well_known",
                     "url": urllib.parse.urljoin(r["host"], "/robots.txt"),
                     "selected_as": "agency-level well-known set (synthetic surface)",
                     "selection_source": "targets.yaml well_known_paths",
                     "doc_id": None,
                     "well_known_paths": cfg["well_known_paths"]})
    if admit:
        for row in rows:
            if row["doc_id"] is None:
                continue
            obs = http.fetch(fetcher, "admit", row["doc_id"], row["url"], load_params())
            resp = obs[0].response or {}
            row["first_capture"] = {
                "status": resp.get("status"), "content_hash": resp.get("body_sha256"),
                "bytes": resp.get("bytes"), "captured_at": obs[0].captured_at,
                "error_class": obs[0].error_class}
            print(f"  {row['doc_id'][:52]:54s} HTTP {resp.get('status')}", flush=True)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--admit", action="store_true", help="fetch and hash each target")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(ROSTER.read_text(encoding="utf-8"))
    pre = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    rows = build(cfg, pre, Fetcher(load_params()) if a.admit else None, a.admit)
    kinds = {k: sum(1 for r in rows if r["surface_kind"] == k)
             for k in ("flagship", "machine", "well_known")}
    summary = {"task": TASK, "epoch": cfg["epoch"],
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "source_type": cfg["source_type"], "construct_arm": cfg["construct_arm"],
               "agencies": len({r["agency"] for r in rows}),
               "agencies_unobservable": sorted({r["agency"] for r in rows if r["unobservable"]}),
               "agencies_without_a_flagship": sorted(
                   {r["agency"] for r in rows} -
                   {r["agency"] for r in rows if r["surface_kind"] == "flagship"}),
               "agencies_without_a_machine_entry_point": sorted(
                   {r["agency"] for r in rows} -
                   {r["agency"] for r in rows if r["surface_kind"] == "machine"}),
               "surfaces": len(rows), "by_kind": kinds,
               "admitted_documents": sum(1 for r in rows if r["doc_id"]),
               "rows": rows}
    if a.dry_run:
        print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
        for r in rows:
            print(f"  {r['agency']:8s} {r['surface_kind']:11s} {str(r['selected_as'])[:44]:46s} "
                  f"{r['url'][:64]}")
        return 0
    OUT.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
