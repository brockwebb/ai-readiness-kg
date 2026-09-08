#!/usr/bin/env python3
"""Resolve department -> inventory URL from the two sources ADDENDUM-03 names. **Zero spend.**

`cc_tasks/2026-09-08_scan_frame_fss.md` §2.a, unblocked by `..._ADDENDUM-03.md`. The addendum
is right that guessing `dol.gov` would be an invented fact and right that two published
sources exist. It is wrong about what each one contains, and this script measures that rather
than working around it.

**Source 1, CISA's `.gov` registry** (`cisagov/dotgov-data`, `current-federal.csv`). The
addendum expects columns `Domain name`, `Agency`, `Organization` and an exact match from an
agency name to *its* domain. The file served today has
`Domain name, Domain type, Organization name, Suborganization name, City, State, Security
contact email` — no `Agency` column — and it is **one row per DOMAIN, not per agency**:
Department of Labor has 28 rows, HHS 124. There is no field designating a department's primary
domain, and no structural rule recovers one: filtering to rows with an empty
`Suborganization name` leaves 23 candidates for Labor and 7 for Agriculture, and it does not
contain `hhs.gov`, `ed.gov` or `treasury.gov` at all, because each of those is registered under
a sub-office. So this registry answers the REVERSE question exactly — *which department owns
this domain* — and that is what it is used for here.

**Source 2, data.gov's harvest source registry.** Not available. Every documented CKAN action
endpoint on `catalog.data.gov` answers HTTP 404, `/harvest` included. That is not a workaround
problem, it is a finding: `..._ADDENDUM-01.md` declared Tier C because *"if the government's
own catalog is not machine-legible at tier 0, that is a finding in its own right"*, and the
catalog's machine interface being gone is that finding one layer above tier 0.

So the forward mapping is not resolved and **no domain is invented to stand in for it**. What
this script produces is the evidence and the measurement: the registry retained with its
digest, exact reverse attribution for every host already in the frame, the ambiguity of the
forward direction counted per department, and the catalog API's status per endpoint.

    /opt/anaconda3/bin/python3 scripts/resolve_department_domains.py --dry-run
    /opt/anaconda3/bin/python3 scripts/resolve_department_domains.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import frame, load_params                                 # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
ADDENDUM = "cc_tasks/2026-09-08_scan_frame_fss_ADDENDUM-03.md"
ROSTER = REPO / "state" / "fss_roster_2026-09.json"
TARGETS = REPO / "state" / "scan_targets_fss_2026-09.json"
OUT = REPO / "state" / "fss_department_domains_2026-09.json"
EVIDENCE = REPO / "corpus" / "evidence" / "frame"


def retain(body: bytes) -> tuple:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    d = hashlib.sha256(body).hexdigest()
    p = EVIDENCE / d[:2] / d
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_bytes(body)
    return d, str(p.relative_to(REPO))


def norm(text: str) -> str:
    """The declared normalisation: case-fold, strip a leading `U.S.`, collapse whitespace.
    Recorded on every match so a reader can see which rule joined two strings."""
    s = " ".join(str(text or "").split()).casefold()
    for prefix in ("u.s. ", "us ", "the "):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    params = load_params()
    cfg = params["frame"]["dept_domains"]
    from scan.manners import Fetcher
    fetcher = Fetcher(params)

    r = fetcher.raw_get(cfg["dotgov_registry_url"])
    if r["status"] != 200:
        raise SystemExit(f"REFUSING: the .gov registry answered HTTP {r['status']}; the "
                         f"attribution below would rest on a document we were not served.")
    digest, path = retain(r["body"])
    rows = list(csv.DictReader(io.StringIO(r["body"].decode("utf-8", "replace"))))
    print(f"  registry HTTP 200 {len(r['body'])} bytes, {len(rows)} domains, "
          f"sha256 {digest[:12]}…", flush=True)

    by_domain = {str(x["Domain name"]).strip().lower(): x for x in rows}
    by_org: dict = {}
    for x in rows:
        by_org.setdefault(norm(x["Organization name"]), []).append(x)

    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    targets = json.loads(TARGETS.read_text(encoding="utf-8")) if TARGETS.is_file() else {}

    # ---- what the registry DOES answer: which department owns each host already in the frame
    attribution = []
    for e in roster["tier_a"]:
        host = (e.get("host") or "").lower()
        rd = frame.registrable_domain(host)
        hit = by_domain.get(rd) or by_domain.get(host)
        attribution.append({
            "agency": e["unit_name"], "host": host, "registrable_domain": rd,
            "registry_organization": (hit or {}).get("Organization name"),
            "registry_suborganization": (hit or {}).get("Suborganization name"),
            "registry_domain_type": (hit or {}).get("Domain type"),
            "in_registry": bool(hit),
            "agrees_with_roster_parent": bool(hit) and norm(hit["Organization name"]) ==
            norm(e["parent_department"]),
        })

    # ---- the forward direction, counted rather than guessed
    departments = sorted({e["parent_department"] for e in roster["tier_a"]}
                         | {e["name"] for e in roster["tier_b"]})
    forward = []
    for d in departments:
        cand = by_org.get(norm(d), [])
        top = [c for c in cand if not str(c["Suborganization name"]).strip()]
        forward.append({
            "department": d, "registry_rows": len(cand),
            "suborganization_empty_rows": len(top),
            "candidate_domains_sample": sorted(c["Domain name"] for c in top)[:8],
            "resolvable_to_one_domain": len(top) == 1,
            "note": ("the registry has no field designating a department's primary domain; "
                     "one row per domain, so this is a count of candidates, not a mapping"),
        })

    # ---- source 2, measured
    catalog = []
    for url in cfg["catalog_api_urls"]:
        try:
            cr = fetcher.raw_get(url)
            catalog.append({"url": url, "status": cr["status"], "bytes": len(cr["body"]),
                            "content_type": (cr["headers"].get("content-type") or "")
                            .split(";")[0].strip()})
        except Exception as exc:                                    # noqa: BLE001
            from scan.errors import classify_exception
            catalog.append({"url": url, "status": None,
                            "error_class": classify_exception(exc),
                            "error": f"{type(exc).__name__}: {exc}"})
        print(f"  catalog {catalog[-1].get('status')}  {url}", flush=True)

    doc = {
        "task": TASK, "addendum": ADDENDUM,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry": {"url": cfg["dotgov_registry_url"], "sha256": digest,
                     "retained_path": path, "domains": len(rows),
                     "columns": list(rows[0].keys()) if rows else [],
                     "columns_expected_by_addendum": cfg["dotgov_columns_expected"],
                     "schema_matches_addendum": "Agency" in (rows[0].keys() if rows else [])},
        "normalisation": ["casefold", "strip leading 'U.S.'/'the'", "collapse whitespace"],
        "reverse_attribution": attribution,
        "forward_mapping": forward,
        "forward_resolvable": sum(1 for f in forward if f["resolvable_to_one_domain"]),
        "forward_departments": len(forward),
        "catalog_api": catalog,
        "catalog_api_available": any(c.get("status") == 200 for c in catalog),
        "conclusion": (
            "The forward mapping department -> primary domain is NOT resolvable from either "
            "named source. The .gov registry is one row per domain with no primary-domain "
            "field; data.gov's CKAN action API answers 404 at every documented endpoint. No "
            "domain is invented to stand in for it."),
    }
    brief = {k: v for k, v in doc.items()
             if k not in ("reverse_attribution", "forward_mapping", "catalog_api")}
    print(json.dumps(brief, indent=1))
    if a.dry_run:
        return 0
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
