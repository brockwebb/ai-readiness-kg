#!/usr/bin/env python3
"""Host pre-flight and flagship harvest for the scan target list. **Zero model spend.**

Task `cc_tasks/2026-09-06_scan_targets.md` §3.1 and §3.3. Two things, in one pass, because
they are the same fetches:

1. **Pre-flight, which is manners and not evasion.** Per host: robots.txt, then a HEAD and a
   GET of the home page under the identified UA, then `<host>/data.json`. A host that answers
   401/403/429 to an identified compliant client is **unobservable** — it stays on the target
   list, its surfaces will produce `error` Findings, and it is reported as such.
   **No UA spoofing, no proxying, no retry storms.** The harness RESULT already recorded
   `www.bls.gov` refusing 60 of 60 requests while its own robots.txt permits the paths; that
   asymmetry is the observation, and disguising the client to get around it would destroy it.

2. **Host identity, verified rather than asserted.** `publisher.name` from `<host>/data.json`
   (Project Open Data / OPEN Government Data Act metadata) where the host serves one, else the
   home page `<title>`. "bls.gov is the Bureau of Labor Statistics" then rests on a stored
   capture rather than on the author's memory.

3. **Flagship harvest.** The agency's own listing page is fetched and its product links
   extracted, so §3.2's selection is made FROM the agency's listing and can cite the anchor
   text it was read from. A listing that cannot be read is recorded `listing_unreadable`; no
   flagship is substituted from elsewhere.

    /opt/anaconda3/bin/python3 scripts/scan_preflight.py --dry-run
    /opt/anaconda3/bin/python3 scripts/scan_preflight.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import yaml                                                       # noqa: E402
from scan import load_params                                      # noqa: E402
from scan.collectors import http, robots                          # noqa: E402
from scan.manners import Fetcher                                  # noqa: E402

TASK = "cc_tasks/2026-09-06_scan_targets.md"
ROSTER = REPO / "assessment" / "harness" / "scan" / "targets.yaml"
OUT = REPO / "state" / "scan_preflight_2026-09.json"
LEG = "host_preflight"

#: Statuses at which the host refused an identified compliant client. Read from params so the
#: pre-flight and the rules cannot drift apart on what "unobservable" means.
def _refusal_statuses(params: dict) -> tuple:
    return tuple((params.get("manners") or {}).get("unobservable_statuses") or ())


def roster() -> dict:
    return yaml.safe_load(ROSTER.read_text(encoding="utf-8"))


def _publisher(obs) -> str | None:
    """`publisher.name` from a served data.json. The catalog names its own publisher; that is
    the mechanical half of host verification."""
    p = (obs.response or {}).get("body_path")
    if not p or (obs.response or {}).get("status") != 200:
        return None
    try:
        cat = json.loads((REPO / p).read_bytes().decode("utf-8", "replace"))
    except Exception:
        return None
    pub = cat.get("publisher") if isinstance(cat, dict) else None
    if isinstance(pub, dict) and pub.get("name"):
        return str(pub["name"])
    ds = (cat.get("dataset") or []) if isinstance(cat, dict) else []
    for d in ds[:1]:
        pub = (d or {}).get("publisher") or {}
        if isinstance(pub, dict) and pub.get("name"):
            return str(pub["name"])
    return None


def _title(obs) -> str | None:
    p = (obs.response or {}).get("body_path")
    if not p:
        return None
    try:
        text = (REPO / p).read_bytes().decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    return " ".join(m.group(1).split())[:200] if m else None


def _candidates(obs, agency: dict, cfg: dict) -> list:
    """Product links on the agency's own listing page, filtered by anchor text. A filter, not
    a ranking — the point is that the selection is made from the agency's links."""
    links = ((obs.parsed or {}).get("links") or [])
    host = urllib.parse.urlsplit(agency["host"]).netloc
    keep, seen = [], set()
    for l in links:
        text = (l.get("text") or "").strip()
        href = l.get("href") or ""
        low = text.lower()
        if not text or len(text) < 4 or href in seen:
            continue
        if urllib.parse.urlsplit(href).netloc != host:
            continue
        if any(t in low for t in cfg["reject_link_tokens"]):
            continue
        if not any(t in low for t in cfg["candidate_link_tokens"]):
            continue
        seen.add(href)
        keep.append({"text": text, "href": href})
    return keep


#: Anchor text on an agency HOME page that names its data listing. Discovery beats a typed
#: URL: five of the fourteen configured listings were wrong or unreadable on the first pass,
#: and "the page the agency's own home page calls its data page" is a citable selection source
#: where "the URL the author guessed" is not.
LISTING_ANCHORS = ("data & statistics", "data and statistics", "data tools", "browse data",
                   "data products", "explore data", "data releases", "publications and products",
                   "statistics", "data")


def discover_listing(home_obs, agency: dict) -> dict | None:
    """The data listing as the agency's own home page names it. Shortest matching path wins —
    a nav link to `/data` is the section, `/data/foo/bar` is one product inside it."""
    host = urllib.parse.urlsplit(agency["host"]).netloc
    hits = []
    for l in ((home_obs.parsed or {}).get("links") or []):
        text = " ".join((l.get("text") or "").split())
        href = l.get("href") or ""
        if urllib.parse.urlsplit(href).netloc != host:
            continue
        low = text.lower().strip(" .:|")
        for rank, anchor in enumerate(LISTING_ANCHORS):
            if low == anchor:
                hits.append((rank, len(urllib.parse.urlsplit(href).path), href, text))
                break
    if not hits:
        return None
    hits.sort()
    _, _, href, text = hits[0]
    return {"url": href, "anchor_text": text}


def preflight(cfg: dict, params: dict, fetcher) -> list:
    refusals = _refusal_statuses(params)
    rows = []
    for agency in cfg["agencies"]:
        code, host = agency["code"], agency["host"]
        doc_id = f"host:{urllib.parse.urlsplit(host).netloc}"
        obs = []
        obs += robots.fetch(fetcher, LEG, doc_id, host, params)
        obs += http.fetch(fetcher, LEG, doc_id, host, params, parse_links=True)
        dj = http.fetch(fetcher, LEG, doc_id, urllib.parse.urljoin(host, "/data.json"), params)
        obs += dj
        listing = http.fetch(fetcher, LEG, doc_id, agency["listing_url"], params,
                             parse_links=True)
        obs += listing
        used, used_source = listing[0], f"configured listing_url {agency['listing_url']}"
        cands = _candidates(used, agency, cfg) if (used.response or {}).get("status") == 200 else []
        found = discover_listing(obs[1], agency)
        # A configured listing that 404s, or that returns a page with no product links because
        # it is client-rendered, is not a listing. Fall back to the one the home page names,
        # and record WHICH was used — the selection source has to name the page it read.
        if not cands and found and found["url"] != agency["listing_url"]:
            alt = http.fetch(fetcher, LEG, doc_id, found["url"], params, parse_links=True)
            obs += alt
            alt_c = _candidates(alt[0], agency, cfg) if (alt[0].response or {}).get("status") == 200 else []
            if alt_c:
                used, cands = alt[0], alt_c
                used_source = (f"discovered from the {host} home page, anchor text "
                               f"{found['anchor_text']!r}")
        statuses = [(o.target_url, (o.response or {}).get("status")) for o in obs]
        home = obs[1]
        # Unobservable iff EVERY probe was refused. A single refused path is not a refused
        # host — www.census.gov refuses some paths and answers others, and calling the whole
        # host unobservable would throw away the evidence it did give.
        refused = [s for _, s in statuses if s in refusals]
        unobservable = bool(statuses) and len(refused) == len(statuses)
        listing_ok = bool(cands)
        rows.append({
            "agency": code, "name": agency["name"],
            "department": agency.get("department"),
            "spd1_segment": agency.get("spd1_segment"),
            "host": host, "listing_url": agency["listing_url"],
            "robots_status": (obs[0].response or {}).get("status"),
            "robots_present": ((obs[0].parsed or {}).get("present")),
            "home_status": (home.response or {}).get("status"),
            "data_json_status": (dj[0].response or {}).get("status"),
            "listing_status": (listing[0].response or {}).get("status"),
            "listing_used": used.target_url,
            "listing_selection_source": used_source,
            "listing_discovered": found,
            "listing_unreadable_reason": (
                None if cands else
                ("refused" if (listing[0].response or {}).get("status") in refusals else
                 "not_served" if (listing[0].response or {}).get("status") != 200 else
                 "no_product_links_without_js")),
            "statuses": statuses,
            "refused_probes": len(refused), "probes": len(statuses),
            "unobservable": unobservable,
            "publisher_name": _publisher(dj[0]),
            "home_title": _title(home),
            "identity_verified_by": ("data.json publisher.name" if _publisher(dj[0])
                                     else ("home page <title>" if _title(home) else None)),
            "listing_readable": listing_ok,
            "candidates": cands,
            "observations": [o.to_dict() for o in obs],
        })
        print(f"  {code:8s} home {rows[-1]['home_status']}  robots {rows[-1]['robots_status']}"
              f"  data.json {rows[-1]['data_json_status']}  listing {rows[-1]['listing_status']}"
              f"  candidates {len(rows[-1]['candidates'])}"
              f"{'  UNOBSERVABLE' if unobservable else ''}", flush=True)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    cfg, params = roster(), load_params()
    if a.dry_run:
        print(json.dumps({"agencies": len(cfg["agencies"]),
                          "probes_per_agency": 4,
                          "hosts": [x["host"] for x in cfg["agencies"]],
                          "refusal_statuses": list(_refusal_statuses(params))}, indent=1))
        return 0
    rows = preflight(cfg, params, Fetcher(params))
    summary = {
        "task": TASK, "generated_at": datetime.now(timezone.utc).isoformat(),
        "params_version": params["params_version"],
        "hosts": len(rows),
        "hosts_unobservable": sum(1 for r in rows if r["unobservable"]),
        "hosts_unobservable_ids": [r["agency"] for r in rows if r["unobservable"]],
        "listings_unreadable": [r["agency"] for r in rows if not r["listing_readable"]],
        "identity_by_data_json": sum(1 for r in rows
                                     if r["identity_verified_by"] == "data.json publisher.name"),
        "rows": rows,
    }
    OUT.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
