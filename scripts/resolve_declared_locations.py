#!/usr/bin/env python3
"""Read a body's declared locations off the pages that publish them. **Zero model spend.**

`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` decision 1, widened by its
ADDENDUM_01 amendment 1. DN-012 d3 says a body's `api_base`, its API terms, its changelog, its
department inventory and its `catalog.data.gov` organization are READ from a page and cited on
the row; this is the tool that reads them. It decides nothing: it fetches a page, retains the
bytes, and lists the page's links (filtered by a pattern when asked), so the declaration written
into `targets.yaml` names a page, a digest and an anchor a stranger can re-check.

**Manners.** Every request goes through `scan.manners.Fetcher` (DD-060 identity, robots-first
per DD-062, 1 req/s per host), the same layer the scan cycle uses. There is no bare `httpx`
call here and no retry under another identity; a refusal is recorded as what it is.

**Evidence lane.** Bodies go to `corpus/evidence/frame/`, the lane `scripts/build_roster.py`
opened for sources a DataFile or a declaration cites and no Observation does (DD-058's
uncited-body census counts the scan store, and these bodies are not Observations).

**Checkpoint (CLAUDE.md §15).** The unit of work is one URL. Each fetch is appended to the log
(`state/declaration_fetches_2026-10-06.jsonl`), flushed and fsynced, before the next is made.
The key is the URL; a URL already logged with a status is skipped on re-run and its retained
body re-read, so re-running a command is the resume command and no page is fetched twice.
A failed fetch is a row (`error`), never a crash of the batch. No pilot or ceiling: the run is
a few dozen GETs at the standing 1 req/s, issued by hand, page by page.

    /opt/anaconda3/bin/python3 scripts/resolve_declared_locations.py fetch URL [URL ...] \
        [--grep REGEX] [--all-links]
    /opt/anaconda3/bin/python3 scripts/resolve_declared_locations.py links URL --grep REGEX
    /opt/anaconda3/bin/python3 scripts/resolve_declared_locations.py census
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md"
EVIDENCE = REPO / "corpus" / "evidence" / "frame"
LOG = REPO / "state" / "declaration_fetches_2026-10-06.jsonl"
#: One row per invocation: the socket count per host, robots reads and retries included
#: (`manners.Fetcher.requests`). Summed by `census` for the RESULT's manners accounting.
RUNS = REPO / "state" / "declaration_fetch_runs_2026-10-06.jsonl"


def _logged() -> dict:
    """`{url: last row}` from the checkpoint log, read at call time."""
    out = {}
    if LOG.is_file():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                out[row["url"]] = row
    return out


def _append(row: dict, path: Path | None = None) -> None:
    path = path or LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def retain(body: bytes) -> tuple:
    d = hashlib.sha256(body).hexdigest()
    path = EVIDENCE / d[:2] / d
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(body)
    return d, str(path.relative_to(REPO))


def fetch(url: str, fetcher) -> dict:
    """One GET, logged before it returns. A URL already on the log is not fetched again."""
    prior = _logged().get(url)
    if prior is not None:
        return dict(prior, resumed=True)
    from scan.errors import RobotsDisallowed
    row = {"url": url, "task": TASK, "fetched_at": datetime.now(timezone.utc).isoformat()}
    try:
        r = fetcher.raw_get(url)
        row.update(status=r["status"], final_url=r["final_url"], bytes=len(r["body"]),
                   content_type=(r["headers"].get("content-type") or "").split(";")[0].strip())
        if r["body"]:
            row["sha256"], row["retained_at"] = retain(r["body"])
    except RobotsDisallowed as exc:
        row.update(status=None, error=f"robots_disallowed: {exc}")
    except Exception as exc:                       # recorded as a row, never swallowed
        row.update(status=None, error=f"{type(exc).__name__}: {exc}")
    _append(row)
    return row


def links_of(row: dict) -> list:
    """`[{href, text}]` of a retained HTML body, resolved against the URL it was served at."""
    if not row.get("retained_at") or "html" not in (row.get("content_type") or ""):
        return []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup((REPO / row["retained_at"]).read_bytes(), "html.parser")
    base = row.get("final_url") or row["url"]
    return [{"href": urllib.parse.urljoin(base, a["href"]), "text": " ".join(a.get_text().split())}
            for a in soup.find_all("a", href=True)]


def text_hits(row: dict, pattern: str, width: int = 140) -> list:
    """Snippets of a retained HTML body's visible text around each match of `pattern`."""
    if not row.get("retained_at"):
        return []
    from bs4 import BeautifulSoup
    text = " ".join(BeautifulSoup((REPO / row["retained_at"]).read_bytes(),
                                  "html.parser").get_text(" ").split())
    return [text[max(0, m.start() - width):m.end() + width]
            for m in re.finditer(pattern, text, re.I)]


def show(row: dict, pattern: str | None, all_links: bool, text: str | None = None) -> None:
    head = {k: row.get(k) for k in ("url", "status", "final_url", "content_type", "bytes",
                                     "sha256", "retained_at", "error", "resumed")}
    print(json.dumps(head))
    for snip in (text_hits(row, text) if text else []):
        print(f"  TEXT: {snip}")
    if not (pattern or all_links):
        return
    rx = re.compile(pattern, re.I) if pattern else None
    seen = set()
    for ln in links_of(row):
        key = (ln["href"], ln["text"])
        if key in seen:
            continue
        seen.add(key)
        if rx is None or rx.search(ln["href"]) or rx.search(ln["text"]):
            print(f"    {ln['text'][:70]!r:74s} {ln['href']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="GET each URL through the manners layer (resume by skip)")
    f.add_argument("urls", nargs="+")
    f.add_argument("--grep", default=None, help="list the page's links matching this regex")
    f.add_argument("--all-links", action="store_true")
    f.add_argument("--text", default=None, help="print visible-text snippets matching this regex")
    ln = sub.add_parser("links", help="list a LOGGED page's links; no network")
    ln.add_argument("url")
    ln.add_argument("--grep", default=None)
    ln.add_argument("--text", default=None)
    sub.add_parser("census", help="requests per host and statuses, from the log; no network")
    a = ap.parse_args(argv)
    if a.cmd == "links":
        row = _logged().get(a.url)
        if row is None:
            raise SystemExit(f"REFUSING: {a.url} is not on {LOG.relative_to(REPO)}; fetch it")
        show(row, a.grep, a.grep is None and a.text is None, a.text)
        return 0
    if a.cmd == "census":
        rows = list(_logged().values())
        sockets = Counter()
        if RUNS.is_file():
            for line in RUNS.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    sockets.update(json.loads(line)["requests"])
        print(json.dumps({"urls": len(rows), "requests_per_host": dict(sorted(sockets.items())),
                          "requests_total": sum(sockets.values()),
                          "per_host": dict(Counter(urllib.parse.urlsplit(r["url"]).netloc
                                                   for r in rows)),
                          "per_status": dict(Counter(str(r.get("status")) for r in rows))},
                         indent=1))
        return 0
    from scan.manners import Fetcher
    fetcher = Fetcher(load_params())
    for u in a.urls:
        show(fetch(u, fetcher), a.grep, a.all_links, a.text)
    # The socket count, robots reads included, for the RESULT's manners accounting.
    run = {"at": datetime.now(timezone.utc).isoformat(), "requests": dict(fetcher.requests),
           "robots": [{k: r.get(k) for k in ("netloc", "status", "decision")}
                      for r in fetcher.robots_log]}
    _append(run, RUNS)
    print(json.dumps(run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
