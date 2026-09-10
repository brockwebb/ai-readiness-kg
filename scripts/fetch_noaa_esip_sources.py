#!/usr/bin/env python3
"""Fetch the three sources of `cc_tasks/2026-09-10_corpus_noaa_esip.md` §1. **Zero model spend.**

**Three source fetches and nothing else**, each robots-first through `scan.manners.Fetcher` so
the identified UA is the only identity used and `robots.txt` is read before the document
(DD-062, DD-060). There is no bare `httpx` call in this file, no alternate UA, and no retry
under a different identity: if a host refuses this client, the refusal is the record.

`www.noaa.gov` is NOT on the scan roster and is not being scanned. It is fetched once per
document, as a source. The task anticipates a refusal — the identified client was blocked from
the Desktop session while plain `curl` was not — and says to record it and fall back to the
operator's copies rather than to disguise the scanner.

**The third source's location is recovered from the corpus, not from the task file.** The task
names it "Christensen et al., ESIP, 2021, v1.0.1 (Figshare)" and gives no URL; the corpus
already holds the cluster's README (`esip-data-readiness-checklist`), which names both the
published checklist's path in the repository and the citation the cluster asks to be used. §1
says to record the exact citation AS FOUND, and what is found is the authority.

    /opt/anaconda3/bin/python3 scripts/fetch_noaa_esip_sources.py --dry-run   # no network
    /opt/anaconda3/bin/python3 scripts/fetch_noaa_esip_sources.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.manners import netloc_of                                  # noqa: E402

TASK = "cc_tasks/2026-09-10_corpus_noaa_esip.md"
#: One directory for this task's three sources, added to `dixie_evidence.yaml`
#: `document_dirs` with its task citation, the way every document directory here has
#: been added. Named for the task and not for NOAA, because one of the three is ESIP's.
OUT_DIR = REPO / "corpus" / "noaa_esip"
RECORD = REPO / "state" / "noaa_esip_fetch_2026-09-10.json"

SOURCES = [
    {"key": "nao-216-128",
     "url": "https://www.noaa.gov/sites/default/files/2026-04/NAO_216-128.pdf",
     "filename": "NAO_216-128.pdf",
     "note": "NAO 216-128, Artificial Intelligence in NOAA, signed and effective 2026-04-16. "
             "Scanned image PDF; OCR required; the definition text is in §3.01."},
    {"key": "nao-201-118",
     "url": "https://www.noaa.gov/sites/default/files/2024-11/"
            "NAO_201-118-Software_Governance_and_Public_Release_Policy.pdf",
     "filename": "NAO_201-118_Software_Governance_and_Public_Release_Policy.pdf",
     "note": "NAO 201-118, Software Governance and Public Release Policy, 2024-11. Text PDF."},
    {"key": "esip-checklist",
     "url": "https://raw.githubusercontent.com/ESIPFed/data-readiness/main/"
            "checklist-published/ai-ready-data-checklist-v.1.0.md",
     "filename": "esip-ai-ready-data-checklist-v1.0.md",
     "note": "The published checklist itself. Located from the corpus record "
             "`esip-data-readiness-checklist`, which is the cluster's README and not the "
             "checklist; the README names this path and this citation."},
]


def fetch_one(fetcher, src: dict, params: dict) -> dict:
    """One GET, robots-first. Nothing raised escapes: a refusal is a record, not a traceback."""
    from scan.errors import classify_exception, classify_status
    out = {**src, "netloc": netloc_of(src["url"])}
    try:
        out["robots_permits"] = bool(fetcher.allowed(src["url"]))
    except Exception as exc:                                        # noqa: BLE001
        out["robots_permits"] = None
        out["robots_check_error"] = f"{type(exc).__name__}: {exc}"
    try:
        r = fetcher.raw_get(src["url"])
        body = r["body"]
        out.update({"status": r["status"], "final_url": r.get("final_url"),
                    "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                    "content_type": (r.get("headers") or {}).get("content-type"),
                    "error_class": classify_status(r["status"], params)})
        if r["status"] == 200 and body:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            path = OUT_DIR / src["filename"]
            path.write_bytes(body)
            out["stored_at"] = str(path.relative_to(REPO))
        else:
            out["stored_at"] = None
    except Exception as exc:                                        # noqa: BLE001
        out.update({"status": None, "bytes": 0, "sha256": None, "stored_at": None,
                    "error_class": classify_exception(exc),
                    "error": f"{type(exc).__name__}: {exc}"})
    out["obtained"] = bool(out.get("stored_at"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the plan; contact nothing")
    a = ap.parse_args(argv)
    params = load_params()

    if a.dry_run:
        print(json.dumps({"fetches": len(SOURCES),
                          "netlocs": sorted({netloc_of(s["url"]) for s in SOURCES}),
                          "plan": [f"robots({netloc_of(s['url'])}) + GET {s['url']}"
                                   for s in SOURCES]}, indent=1))
        return 0

    from scan.manners import Fetcher
    fetcher = Fetcher(params)
    rows = [fetch_one(fetcher, s, params) for s in SOURCES]
    for r in rows:
        print(f"  {r['key']:16s} robots_ok={r['robots_permits']} "
              f"status={r.get('status')} bytes={r.get('bytes')} "
              f"-> {r.get('stored_at') or r.get('error_class')}", flush=True)

    record = {
        "task": TASK,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": params["manners"]["user_agent"],
        "identity_note": ("one identity, never varied. A host that refuses this client is "
                          "recorded as refusing it; DD-060."),
        "requests_per_netloc": dict(sorted(fetcher.requests.items())),
        "requests_total": sum(fetcher.requests.values()),
        "obtained": [r["key"] for r in rows if r["obtained"]],
        "refused": {r["key"]: r.get("error_class") for r in rows if not r["obtained"]},
        "sources": rows,
    }
    RECORD.write_text(json.dumps(record, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "sources"}, indent=1))
    print(f"-> {RECORD.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
