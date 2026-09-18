#!/usr/bin/env python3
"""Fetch named URLs from the hosts a task declared, and from no other. **Zero model spend.**

`cc_tasks/2026-09-18_network_allowlist.md` decision 3. A task file may declare
`**Network:** allowlist: host1, host2, ...`; the standing dispatcher parses it (Seldon
`core/dispatch.py::parse_network`, criterion c5), records it on `dispatch_launched`, and hands
it to the session as `SELDON_NETWORK_ALLOWLIST`, comma-separated. This helper is the session
side of that contract, and it is the existing fetch discipline made checkable:

* **Refuses to run at all** when `SELDON_NETWORK_ALLOWLIST` is unset or empty. A session that
  was not launched with an allowlist has declared no network, and the absence is the answer.
* **Refuses any URL whose host is not on the list, before any socket opens.** Exact hostnames,
  compared case-insensitively (RFC 4343); no subdomain or wildcard matching, because the task
  grammar has none. The same check runs as an httpx `request` event hook, so a redirect to an
  off-list host (github.com → codeload.github.com, say) is refused at that hop too, and so is
  the `robots.txt` read, which is a request like any other.
* **Robots-first, identified UA, rate-limited**, through `scan.manners.Fetcher` exactly as
  `scripts/fetch_noaa_esip_sources.py` does (DD-060, DD-062). There is no bare `httpx` GET here
  and no alternate identity: a host that refuses this client is recorded as refusing it.
* **One log line per request**, JSONL, with URL, status, bytes and sha256 — every hop the
  client actually sent, the `robots.txt` read and redirects included, plus one line per refused
  URL with `status: null`. The RESULT of an allowlist task quotes this log whole.

**Enforcement is declarative plus audit, not a sandbox.** macOS offers no cheap per-process
egress filter, so nothing stops a session from fetching some other way; the allowlist has the
standing of the Spend header, a declared budget whose use is audited from a log. The helper
makes the declared path the easy one, and `CLAUDE.md` says corpus acquisition goes through it.

The log's `acquisition_method` / `acquired_by` fields are what a dixie ledger entry for a
document obtained here should carry, so admissions stay uniform across tasks.

    SELDON_NETWORK_ALLOWLIST=github.com /opt/anaconda3/bin/python3 scripts/fetch_allowlisted.py \\
        --out-dir corpus/<dir> --log logs/<task>_fetch.jsonl URL [URL ...]
    ... --dry-run    # check every URL against the list and print the plan; contact nothing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

#: The name Seldon's dispatcher sets (`seldon.core.dispatch.NETWORK_ALLOWLIST_ENV`). Spelled
#: out rather than imported so this helper does not depend on Seldon being importable; a
#: test asserts the two spellings agree when it is.
ALLOWLIST_ENV = "SELDON_NETWORK_ALLOWLIST"
ACQUISITION_METHOD = "scripted_fetch"
ACQUIRED_BY = "scripts/fetch_allowlisted.py"
#: Schemes a fetch may use. Anything else (ftp, file, data) is not a host fetch the grammar
#: can declare.
SCHEMES = ("http", "https")


class AllowlistUnset(RuntimeError):
    """`SELDON_NETWORK_ALLOWLIST` is unset or empty: this session declared no network."""


class OffAllowlist(RuntimeError):
    """A URL whose host is not on the declared allowlist. Raised before any request."""


def load_allowlist(env: dict | None = None) -> tuple:
    env = os.environ if env is None else env
    raw = (env.get(ALLOWLIST_ENV) or "").strip()
    if not raw:
        raise AllowlistUnset(
            f"{ALLOWLIST_ENV} is unset or empty. A session gets it only when its task declares "
            f"`**Network:** allowlist: host1, host2, ...` (cc_tasks/2026-09-18_network_allowlist"
            f".md); a task that declared `none` fetches nothing.")
    hosts = tuple(dict.fromkeys(h.strip().lower() for h in raw.split(",") if h.strip()))
    if not hosts:
        raise AllowlistUnset(f"{ALLOWLIST_ENV}={raw!r} names no host.")
    return hosts


def check_url(url: str, allowlist: tuple) -> str:
    """The URL's host, if the URL may be fetched. Raises `OffAllowlist` otherwise."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() not in SCHEMES:
        raise OffAllowlist(f"{url!r}: scheme {parts.scheme!r} is not one of {SCHEMES}")
    host = (parts.hostname or "").lower()
    if host not in allowlist:
        raise OffAllowlist(f"{url!r}: host {host!r} is not on {ALLOWLIST_ENV} "
                           f"({', '.join(allowlist)})")
    return host


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FetchLog:
    """Append-only JSONL, one line per request sent and one per URL refused."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lines: list = []

    def write(self, row: dict) -> None:
        row = {"ts": _now(), **row}
        self.lines.append(row)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def make_client(params: dict, allowlist: tuple, log: FetchLog, transport=None):
    """The same client `scan.manners.Fetcher` builds, plus the two hooks this contract needs.

    httpx calls `request` hooks for every request it is about to send, redirect hops included,
    and `response` hooks for every response it received. Raising in the first is a refusal
    before the connection; the second is the one-line-per-request log.
    """
    import httpx
    m = params["manners"]

    def guard(request):
        # Logged HERE and not by the caller, because `Fetcher._robots_for` swallows every
        # exception from the robots read: a robots.txt that redirected off the list would
        # otherwise be refused without a trace.
        try:
            check_url(str(request.url), allowlist)
        except OffAllowlist as exc:
            log.write({"event": "refused", "method": request.method, "url": str(request.url),
                       "status": None, "bytes": 0, "sha256": None, "reason": str(exc)})
            raise

    def record(response):
        body = response.read()
        log.write({"event": "request", "method": response.request.method,
                   "url": str(response.request.url), "status": response.status_code,
                   "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                   "content_type": response.headers.get("content-type")})

    kw = {} if transport is None else {"transport": transport}
    return httpx.Client(
        follow_redirects=m["follow_redirects"], max_redirects=m["max_redirects"],
        timeout=httpx.Timeout(connect=m["connect_timeout_seconds"],
                              read=m["read_timeout_seconds"],
                              write=m["read_timeout_seconds"],
                              pool=m["read_timeout_seconds"]),
        headers={"User-Agent": m["user_agent"]},
        event_hooks={"request": [guard], "response": [record]}, **kw)


def _filename(url: str) -> str:
    name = Path(urllib.parse.urlsplit(url).path).name
    return name or "index.html"


def fetch_all(urls: list, out_dir: Path, log: FetchLog, params: dict, allowlist: tuple,
              transport=None, clock=None) -> list:
    """Every URL checked against the list first; the refused are logged and never requested.
    Returns one summary row per URL. A file already at the target path is never overwritten."""
    from scan.manners import Fetcher
    rows, allowed = [], []
    for url in urls:
        try:
            check_url(url, allowlist)
        except OffAllowlist as exc:
            log.write({"event": "refused", "url": url, "status": None, "bytes": 0,
                       "sha256": None, "reason": str(exc)})
            rows.append({"url": url, "obtained": False, "refused": str(exc)})
            continue
        allowed.append(url)
    if not allowed:
        return rows

    fetcher = Fetcher(params, client=make_client(params, allowlist, log, transport), clock=clock)
    for url in allowed:
        dest = out_dir / _filename(url)
        row = {"url": url, "stored_at": None, "obtained": False}
        if dest.exists():
            row["error"] = f"{dest} exists; not overwritten"
            rows.append(row)
            continue
        try:
            r = fetcher.raw_get(url)
        except OffAllowlist as exc:
            # A redirect hop led off the list. The hook refused it before the connection and
            # logged the hop; the row records which URL it happened under.
            row["refused"] = str(exc)
            rows.append(row)
            continue
        except Exception as exc:                                    # noqa: BLE001
            # Transport failures are a record for the RESULT, not a traceback that loses the
            # log lines of the URLs that did succeed.
            row["error"] = f"{type(exc).__name__}: {exc}"
            log.write({"event": "error", "url": url, "status": None, "bytes": 0,
                       "sha256": None, "reason": row["error"]})
            rows.append(row)
            continue
        body = r["body"]
        row.update({"status": r["status"], "final_url": r.get("final_url"),
                    "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        if r["status"] == 200 and body:
            out_dir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            row.update({"stored_at": str(dest), "obtained": True,
                        "acquisition_method": ACQUISITION_METHOD, "acquired_by": ACQUIRED_BY,
                        "retrieved_at": _now()})
        rows.append(row)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path, help="JSONL fetch log (appended)")
    ap.add_argument("--dry-run", action="store_true",
                    help="check every URL against the allowlist; contact nothing")
    a = ap.parse_args(argv)
    try:
        allowlist = load_allowlist()
    except AllowlistUnset as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    if a.dry_run:
        plan = []
        for url in a.urls:
            try:
                check_url(url, allowlist)
                plan.append({"url": url, "allowed": True})
            except OffAllowlist as exc:
                plan.append({"url": url, "allowed": False, "reason": str(exc)})
        print(json.dumps({"allowlist": list(allowlist), "plan": plan}, indent=1))
        return 0 if all(p["allowed"] for p in plan) else 3

    from scan import load_params
    log = FetchLog(a.log)
    rows = fetch_all(a.urls, a.out_dir, log, load_params(), allowlist)
    print(json.dumps({"allowlist": list(allowlist), "log": str(a.log), "results": rows},
                     indent=1, default=str))
    return 0 if all(r.get("obtained") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
