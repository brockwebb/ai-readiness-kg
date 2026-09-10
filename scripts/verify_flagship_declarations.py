#!/usr/bin/env python3
"""Verify the seven declared flagship landing pages, robots-first. **Zero model spend.**

Task `cc_tasks/2026-09-10_scan_frame_v5.md` §1. The declarations are
`docs/design/fss_flagship_declarations.md`; they are PARSED from that file, never retyped here,
because a URL typed twice is a URL that can differ in one place and the declaration is the
authority.

**What this contacts, and nothing else.** Per declared landing page: one `robots.txt` read on
its netloc, then one HEAD and one GET on the page itself. Seven pages on seven netlocs, so at
most 7 + 7 + 7 = 21 requests, plus whatever the rate limiter's own backoff adds on a 429/503 —
which is counted, per host, and reported. Every request goes through `scan.manners.Fetcher`, so
robots is read BEFORE the page (DD-062) and the standing rate applies. There is no bare
`httpx` call in this file and there is no retry under any other identity.

**A 403 is a measurement.** `www.bls.gov`, `www.bts.gov` and `www.ssa.gov` have refused this
scanner's identified UA across three cycles. Decision 1 says their declared surfaces still
enter the frame, marked `refused_at_declaration`, because dropping the surfaces of the agencies
that refuse us would restrict the instrument to the agencies that permit us — the worst
sampling rule available to an accessibility assessment.

**HEAD and GET are both recorded and the GET is the verdict.** A host that answers 403 to HEAD
and 200 to GET is a host whose page is reachable, and the reverse case is a host whose page is
not; reading only one of them would report a server quirk as a property of the declaration.

    /opt/anaconda3/bin/python3 scripts/verify_flagship_declarations.py --dry-run   # no network
    /opt/anaconda3/bin/python3 scripts/verify_flagship_declarations.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.manners import netloc_of, same_site, site_key             # noqa: E402

TASK = "cc_tasks/2026-09-10_scan_frame_v5.md"
DECLARATIONS = REPO / "docs" / "design" / "fss_flagship_declarations.md"
TARGETS_V4 = REPO / "state" / "scan_targets_fss_2026-09.json"
OUT = REPO / "state" / "fss_flagship_verification_2026-09-10.json"

#: A declaration row: `| body | product | url | why |`. The body cell may carry a parenthetical
#: gloss (`DRSMSU (Federal Reserve Board)`); the CODE is the first token, and it is the code as
#: it appears in targets v4, which the loader asserts rather than assumes.
_ROW = re.compile(r"^\|\s*([A-Z][A-Za-z0-9]*)\s*(?:\([^)]*\))?\s*\|\s*([^|]+?)\s*\|\s*"
                  r"(https?://\S+?)\s*\|\s*([^|]*?)\s*\|\s*$")


def declarations() -> list:
    """`[{body, product, url, why}]` parsed from the declarations doc, or a hard stop."""
    rows = []
    for line in DECLARATIONS.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line)
        if m:
            rows.append({"body": m.group(1), "product": m.group(2), "url": m.group(3),
                         "why": m.group(4)})
    if not rows:
        raise SystemExit(f"FATAL: no declaration rows parsed from {DECLARATIONS}; the table "
                         f"shape changed and this script must be told, not left guessing")
    return rows


def site_keys_v4() -> dict:
    """`{body code: site key}` from targets v4. The declared page must be same-site to the
    body's OWN site key (DD-063), and v4 is where that key is defined."""
    doc = json.loads(TARGETS_V4.read_text(encoding="utf-8"))
    return {h["agency"]: h["site_key"] for h in doc["hosts"]}


def probe(fetcher, row: dict, key: str, params: dict) -> dict:
    """One HEAD and one GET on the declared page; robots is read first by the fetcher itself.

    Nothing raised escapes: a declaration that times out is a finding about the declaration
    (decision 2), and a traceback would lose the other six.
    """
    from scan.errors import classify_exception, classify_status
    url = row["url"]
    out = {**row, "netloc": netloc_of(url), "site_key_expected": key}
    try:
        out["robots_permits"] = bool(fetcher.allowed(url))
    except Exception as exc:                                        # noqa: BLE001
        out["robots_permits"] = None
        out["robots_check_error"] = f"{type(exc).__name__}: {exc}"
    for method, call in (("head", fetcher.raw_head), ("get", fetcher.raw_get)):
        try:
            r = call(url)
            out[f"{method}_status"] = r["status"]
            out[f"{method}_final_url"] = r.get("final_url")
            out[f"{method}_error_class"] = classify_status(r["status"], params)
            if r.get("method") == "GET" and method == "head":
                out["head_refused_status"] = r.get("head_refused_status")
        except Exception as exc:                                    # noqa: BLE001
            out[f"{method}_status"] = None
            out[f"{method}_error_class"] = classify_exception(exc)
            out[f"{method}_error"] = f"{type(exc).__name__}: {exc}"
    # The GET is the verdict; HEAD stands in only where the GET could not be observed at all.
    status = out["get_status"] if out["get_status"] is not None else out["head_status"]
    final = out.get("get_final_url") or out.get("head_final_url") or url
    out["status"] = status
    out["final_url"] = final
    out["same_site"] = bool(same_site(final, key))
    out["error_class"] = (out["get_error_class"] if out["get_status"] is not None
                          else out["head_error_class"])
    out["verdict"] = verdict(out)
    return out


def verdict(row: dict) -> str:
    """`enters`, `refused_at_declaration`, or a named stop. Decisions 1 and 2."""
    if not row["same_site"]:
        return "stop:off_site_redirect"
    if row["status"] == 200:
        return "enters"
    if row["error_class"] == "refused":                 # 401/403 — the host refuses US
        return "refused_at_declaration"
    if row["status"] is None:
        return f"stop:{row['error_class']}"
    return f"stop:http_{row['status']}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the plan; contact nothing")
    a = ap.parse_args(argv)

    rows_in, keys = declarations(), site_keys_v4()
    unknown = [r["body"] for r in rows_in if r["body"] not in keys]
    if unknown:
        raise SystemExit(f"FATAL: declared bodies absent from targets v4: {unknown}. A "
                         f"declaration names a body of the frame or it names nothing.")
    params = load_params()

    if a.dry_run:
        print(json.dumps({"pages": len(rows_in),
                          "netlocs": sorted({netloc_of(r['url']) for r in rows_in}),
                          "max_requests": 3 * len(rows_in),
                          "plan": [f"{r['body']}: robots({netloc_of(r['url'])}) + HEAD + GET "
                                   f"{r['url']}" for r in rows_in]}, indent=1))
        return 0

    from scan.manners import Fetcher
    fetcher = Fetcher(params)
    rows = []
    for r in rows_in:
        got = probe(fetcher, r, keys[r["body"]], params)
        rows.append(got)
        print(f"  {got['body']:12s} head {str(got['head_status']):>4} "
              f"get {str(got['get_status']):>4} same_site={got['same_site']} "
              f"robots_ok={got['robots_permits']} -> {got['verdict']}", flush=True)

    per_site: dict = {}
    for host, n in fetcher.requests.items():
        per_site[site_key(host)] = per_site.get(site_key(host), 0) + n
    summary = {
        "task": TASK,
        "declarations": str(DECLARATIONS.relative_to(REPO)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": params["manners"]["user_agent"],
        "pages": len(rows),
        "enters": sorted(r["body"] for r in rows if r["verdict"] == "enters"),
        "refused_at_declaration": sorted(r["body"] for r in rows
                                         if r["verdict"] == "refused_at_declaration"),
        "stopped": {r["body"]: r["verdict"] for r in rows
                    if r["verdict"].startswith("stop:")},
        "off_site": sorted(r["body"] for r in rows if not r["same_site"]),
        "requests_per_netloc": dict(sorted(fetcher.requests.items())),
        "requests_per_site": dict(sorted(per_site.items())),
        "requests_total": sum(fetcher.requests.values()),
        "requests_permitted": ("one robots.txt read plus one HEAD and one GET per declared "
                               "page; a 429/503 backoff retry is counted here and is the only "
                               "way this exceeds 3 per page"),
        "note": ("A refusal is a measurement, not a blocker; no host is retried under any "
                 "other identity, and no declaration is substituted."),
        "rows": rows}
    OUT.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
