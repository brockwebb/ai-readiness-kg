#!/usr/bin/env python3
"""Pre-flight over the frame's hosts: robots.txt, and one HEAD on the home. **Zero spend.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §3, over the 19 hosts `..._ADDENDUM-05.md` fixes
as the frame — 16 Tier A statistical agencies and units plus 3 Tier C reference hosts. Nothing
else is contacted.

Two probes per host and no more. `robots.txt` gives its status, its size, and whether it
permits this scanner's identified UA on `/`; one HEAD on the home gives reachability. That is
the whole of what a pre-flight is for: knowing, before a cycle runs, which hosts will answer
and which will not.

**A refusal is a measurement, not a blocker.** `www.bls.gov`, `www.bts.gov` and `www.ssa.gov`
answer 403 to an identified, robots-compliant client and have done so across both prior cycles.
Their surfaces stay in the frame and will produce `error` Findings, because dropping a surface
we were refused would quietly restrict the instrument to the agencies that let us look — the
worst possible sampling rule for an accessibility assessment. **The task does not retry under
any other identity.**

    /opt/anaconda3/bin/python3 scripts/preflight.py --dry-run
    /opt/anaconda3/bin/python3 scripts/preflight.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
ADDENDUM = "cc_tasks/2026-09-08_scan_frame_fss_ADDENDUM-05.md"
TARGETS = REPO / "state" / "scan_targets_fss_2026-09.json"
OUT = REPO / "state" / "fss_preflight_2026-09.json"


def probe(fetcher, host: str, home: str, params: dict) -> dict:
    """`robots.txt` then one HEAD on the home. Both failures are recorded, never raised."""
    from scan.errors import classify_exception, classify_status
    out = {"host": host, "home": home}
    try:
        r = fetcher.raw_get(f"https://{host}/robots.txt")
        body = r["body"].decode("utf-8", "replace")
        out.update({"robots_status": r["status"], "robots_bytes": len(r["body"]),
                    "robots_error_class": classify_status(r["status"], params),
                    "robots_sitemaps": [l.split(":", 1)[1].strip()
                                        for l in body.splitlines()
                                        if l.lower().startswith("sitemap:")]})
    except Exception as exc:                                        # noqa: BLE001
        out.update({"robots_status": None, "robots_bytes": 0,
                    "robots_error_class": classify_exception(exc),
                    "robots_error": f"{type(exc).__name__}: {exc}"})
    # Whether OUR identified UA may fetch `/`. Read through the same Protego-backed check the
    # collectors obey, so the pre-flight cannot disagree with what a cycle will actually do.
    try:
        out["ua_permitted_on_root"] = bool(fetcher.allowed(f"https://{host}/"))
    except Exception as exc:                                        # noqa: BLE001
        out["ua_permitted_on_root"] = None
        out["ua_check_error"] = f"{type(exc).__name__}: {exc}"
    try:
        h = fetcher.raw_head(home or f"https://{host}/")
        out.update({"home_status": h["status"], "home_method": h.get("method", "HEAD"),
                    "home_error_class": classify_status(h["status"], params)})
    except Exception as exc:                                        # noqa: BLE001
        out.update({"home_status": None, "home_error_class": classify_exception(exc),
                    "home_error": f"{type(exc).__name__}: {exc}"})
    st = out.get("home_status")
    out["reachable"] = int(isinstance(st, int))
    out["refuses_identified_client"] = int(
        out.get("home_error_class") == "refused" or out.get("robots_error_class") == "refused")
    out["unreachable"] = int(not out["reachable"])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    params = load_params()
    doc = json.loads(TARGETS.read_text(encoding="utf-8"))
    homes = {r["host"]: r["url"] for r in doc["rows"] if r["surface_kind"] == "home"}
    hosts = doc["hosts"]
    if a.dry_run:
        print(json.dumps({"hosts": len(hosts),
                          "probes": 2 * len(hosts),
                          "list": [h["host"] for h in hosts]}, indent=1))
        return 0
    from scan.manners import Fetcher
    fetcher = Fetcher(params)
    rows = []
    for h in hosts:
        got = probe(fetcher, h["host"], homes.get(h["host"], ""), params)
        rows.append({**h, **got})
        print(f"  {h['tier']} {h['host']:26s} robots {str(got['robots_status']):>4} "
              f"home {str(got['home_status']):>4} "
              f"ua_ok={got['ua_permitted_on_root']}", flush=True)
    summary = {
        "task": TASK, "addendum": ADDENDUM,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": params["manners"]["user_agent"],
        "hosts": len(rows),
        "reachable": sum(r["reachable"] for r in rows),
        "unreachable": [r["host"] for r in rows if r["unreachable"]],
        "refusing_identified_client": [r["host"] for r in rows
                                       if r["refuses_identified_client"]],
        "robots_served": sum(1 for r in rows if r["robots_status"] == 200),
        "ua_permitted_on_root": sum(1 for r in rows if r["ua_permitted_on_root"]),
        "note": ("A refusal is a measurement, not a blocker; no host is retried under any "
                 "other identity, and no surface is dropped for having refused us."),
        "rows": rows}
    OUT.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
