#!/usr/bin/env python3
"""Apply the pre-registered surface-selection rule to the parsed roster. **Zero model spend.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §2. `assessment/harness/scan/frame.py` is the
rule — pure, tested on stored bodies — and this is the only impure part: two GETs per Tier A
agency (its home, then the listing page the rule finds on that home), through the harness's own
manners. Tier B is host-level only and is fetched by `preflight.py` in §3, not here.

**Everything the rule decides is recorded with what it decided from.** Each selected surface
carries the listing URL, that listing body's digest, the verbatim anchor text, the matched
token and the link's POSITION on the page — because "the first three in the agency's own order"
is a claim about a page, and a claim about a page that does not record the order cannot be
checked against it.

**Carried forward, not re-picked.** A cycle-1 surface the rule selects again keeps its existing
`doc_id`, so its two cycles of Findings stay attached to it. A cycle-1 surface the rule does
NOT select stays admitted — history is immutable — and is listed in
`cycle1_surfaces_not_selected` rather than quietly dropped.

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
ROSTER = REPO / "state" / "fss_roster_2026-09.json"
OUT = REPO / "state" / "scan_targets_fss_2026-09.json"
EVIDENCE = REPO / "corpus" / "evidence" / "frame"
EPOCH = "scan-fss-2026-09"
CYCLE1_TARGETS = REPO / "state" / "scan_targets_2026-09.json"


def _slug(text: str, n: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:n].strip("-")


def _code(entry: dict) -> str:
    """A short agency code from the unit name's initials — `Bureau of Labor Statistics` -> BLS.

    Derived, not tabled: a hand-kept code table is a second roster, and the one that went stale
    would be the one that mattered. Collisions are resolved by appending the parent's initials,
    and a collision that survives that is a hard error rather than a silent overwrite.
    """
    words = [w for w in re.sub(r"[^A-Za-z ]", " ", entry["unit_name"]).split()
             if w[:1].isupper() and w.lower() not in
             ("of", "the", "and", "for", "department", "office", "division", "board",
              "governors", "system")]
    return ("".join(w[0] for w in words) or _slug(entry["unit_name"])[:6]).upper()


def codes(tier_a: list) -> dict:
    out, seen = {}, {}
    for e in tier_a:
        c = _code(e)
        if c in seen:
            c = f"{c}-{_code({'unit_name': e['parent_department']})}"
        if c in seen:
            raise SystemExit(f"FATAL: agency code {c!r} collides between {seen[c]!r} and "
                             f"{e['name']!r}; the derivation needs another discriminator, not "
                             f"a silent overwrite.")
        seen[c] = e["name"]
        out[e["name"]] = c
    return out


def retain(body: bytes) -> tuple:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    d = hashlib.sha256(body).hexdigest()
    p = EVIDENCE / d[:2] / d
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_bytes(body)
    return d, str(p.relative_to(REPO))


def links_of(body: bytes, base_url: str) -> list:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")
    return [{"href": urllib.parse.urljoin(base_url, a["href"]),
             "text": " ".join(a.get_text().split())}
            for a in soup.find_all("a", href=True)]


def get(fetcher, url: str) -> dict:
    """One GET, or a recorded non-observation. A host that refuses us is a MEASUREMENT, and the
    agency keeps its roster row: dropping a surface because we were refused would restrict the
    frame to the agencies that let us look, which is the worst possible sampling rule for an
    accessibility assessment (the argument `admit_scan_targets.py` already makes)."""
    try:
        r = fetcher.raw_get(url)
    except Exception as exc:                                  # noqa: BLE001
        from scan.errors import classify_exception
        return {"url": url, "status": None, "error_class": classify_exception(exc),
                "error": f"{type(exc).__name__}: {exc}", "body": b"", "bytes": 0}
    return {"url": url, "final_url": r["final_url"], "status": r["status"],
            "body": r["body"], "bytes": len(r["body"]),
            "content_type": (r["headers"].get("content-type") or "").split(";")[0].strip(),
            "error_class": None}


def cycle1_by_url() -> dict:
    if not CYCLE1_TARGETS.is_file():
        return {}
    doc = json.loads(CYCLE1_TARGETS.read_text(encoding="utf-8"))
    return {r["url"].rstrip("/"): r for r in doc["rows"] if r.get("doc_id")}


def build(params: dict, roster: dict, fetcher) -> dict:
    code_of = codes(roster["tier_a"])
    prior = cycle1_by_url()
    rows, agencies, reused = [], [], set()
    for entry in roster["tier_a"]:
        code, home = code_of[entry["name"]], entry["home_url"]
        rec = {"agency": code, "agency_name": entry["unit_name"], "tier": "A",
               "parent_department": entry["parent_department"],
               "host": entry["host"], "home_url": home,
               "home_url_source": entry["home_url_source"]}
        if not home:
            rec.update({"selection": "no_home_url", "flagships": [], "machine": None})
            agencies.append(rec)
            continue
        cap = get(fetcher, home)
        print(f"  {code:10s} home     HTTP {cap['status']} {cap['bytes']:>7}b", flush=True)
        if not cap["body"]:
            rec.update({"selection": cap["error_class"] or f"home_http_{cap['status']}",
                        "flagships": [], "machine": None})
            agencies.append(rec)
            continue
        home_digest, home_path = retain(cap["body"])
        hl = links_of(cap["body"], cap.get("final_url") or home)
        machine = frame.machine_entry_point(hl, home, params)
        listing = frame.listing_page(hl, home, params)
        rec.update({"home_digest": home_digest, "home_retained": home_path,
                    "home_links": len(hl), "machine": machine, "listing": listing})

        flagships = {"products": [], "marker": "no_listing_page"}
        if listing["url"]:
            lcap = get(fetcher, listing["url"])
            print(f"  {code:10s} listing  HTTP {lcap['status']} {lcap['bytes']:>7}b "
                  f"{listing['url'][:60]}", flush=True)
            if lcap["body"]:
                ldigest, lpath = retain(lcap["body"])
                ll = links_of(lcap["body"], lcap.get("final_url") or listing["url"])
                flagships = frame.flagship_products(ll, listing["url"], params)
                rec.update({"listing_digest": ldigest, "listing_retained": lpath,
                            "listing_links": len(ll)})
            else:
                flagships = {"products": [],
                             "marker": lcap["error_class"] or f"listing_http_{lcap['status']}"}
        rec["flagships"] = flagships
        agencies.append(rec)

        for i, p in enumerate(flagships.get("products") or [], 1):
            prior_row = prior.get(p["url"].rstrip("/"))
            doc_id = (prior_row["doc_id"] if prior_row
                      else f"scan-{code.lower()}-flagship-{i}-{_slug(p['anchor_text'])}")
            if prior_row:
                reused.add(doc_id)
            rows.append({**{k: rec[k] for k in ("agency", "agency_name", "tier", "host",
                                                "parent_department")},
                         "surface_kind": "flagship", "url": p["url"], "doc_id": doc_id,
                         "selected_as": p["anchor_text"], "position_on_listing": p["position"],
                         "listing_url": listing["url"],
                         "listing_digest": rec.get("listing_digest"),
                         "selection_source": p["selection_source"],
                         "carried_from_cycle_1": bool(prior_row)})
        if machine.get("url"):
            prior_row = prior.get(machine["url"].rstrip("/"))
            doc_id = prior_row["doc_id"] if prior_row else f"scan-{code.lower()}-machine"
            if prior_row:
                reused.add(doc_id)
            rows.append({**{k: rec[k] for k in ("agency", "agency_name", "tier", "host",
                                                "parent_department")},
                         "surface_kind": "machine", "url": machine["url"], "doc_id": doc_id,
                         "selected_as": machine["anchor_text"],
                         "position_on_listing": machine["position"],
                         "listing_url": home, "listing_digest": rec.get("home_digest"),
                         "selection_source": machine["selection_source"],
                         "carried_from_cycle_1": bool(prior_row)})
        rows.append({**{k: rec[k] for k in ("agency", "agency_name", "tier", "host",
                                            "parent_department")},
                     "surface_kind": "well_known", "url": f"https://{rec['host']}/robots.txt",
                     "doc_id": None, "selected_as": "agency-level well-known set (synthetic)",
                     "position_on_listing": None, "listing_url": None,
                     "listing_digest": None,
                     "selection_source": "frame: one synthetic host surface per Tier A agency",
                     "carried_from_cycle_1": False})

    not_selected = sorted({r["doc_id"] for r in prior.values()} - reused)
    return {
        "task": TASK, "epoch": EPOCH,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "derived_from": "fss_roster_2026-09",
        "source_type": "product_surface",
        "construct_arm": "publication_actionability",
        "agencies": len(roster["tier_a"]),
        "surfaces": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["surface_kind"] == k)
                    for k in ("flagship", "machine", "well_known")},
        "agencies_without_machine_entry_point": sorted(
            a["agency"] for a in agencies if not (a.get("machine") or {}).get("url")),
        "agencies_without_flagships": sorted(
            a["agency"] for a in agencies if not (a.get("flagships") or {}).get("products")),
        "carried_from_cycle_1": sorted(reused),
        "cycle1_surfaces_not_selected": not_selected,
        "agency_detail": agencies, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    params = load_params()
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    from scan.manners import Fetcher
    doc = build(params, roster, Fetcher(params))
    brief = {k: v for k, v in doc.items() if k not in ("rows", "agency_detail")}
    print(json.dumps(brief, indent=1))
    if a.dry_run:
        for r in doc["rows"]:
            print(f"  {r['agency']:10s} {r['surface_kind']:11s} "
                  f"{str(r['selected_as'])[:40]:42s} {r['url'][:60]}")
        return 0
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
