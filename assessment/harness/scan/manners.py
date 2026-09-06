"""Crawler manners: the scanner obeys the file it measures. **No model calls.**

Task §2.4. RFC 9309 — an instrument that measures robots.txt compliance and then ignores
robots.txt is not an instrument, it is a hypocrite with a user agent. Identified UA, one
request per second per host, exponential backoff on 429/503, no forms, no logins, no
query-string fuzzing.

The one carve-out is stated in `params.yaml` and is not a loophole: `/robots.txt`,
`/sitemap*.xml`, `/llms.txt`, `/data.json` and `/.well-known/*` are always fetched, because
they ARE the object of measurement. A robots.txt that disallows `/robots.txt` cannot thereby
hide it from a measurement OF robots.txt. Every other path is fetched only if allowed for this
UA, and a disallow is recorded as an Observation with `error_class: robots_disallowed` — a
refusal is evidence, not an absence.
"""
from __future__ import annotations

import time
import urllib.parse
from pathlib import Path

VERSION = "0.1.0"


class Fetcher:
    """A rate-limited, robots-respecting HTTP client. One per run."""

    def __init__(self, params: dict, client=None) -> None:
        import httpx
        self.p = params["manners"]
        self.params = params
        self._last: dict = {}
        self._robots: dict = {}
        self.client = client or httpx.Client(
            follow_redirects=self.p["follow_redirects"],
            max_redirects=self.p["max_redirects"],
            timeout=httpx.Timeout(connect=self.p["connect_timeout_seconds"],
                                  read=self.p["read_timeout_seconds"],
                                  write=self.p["read_timeout_seconds"],
                                  pool=self.p["read_timeout_seconds"]),
            headers={"User-Agent": self.p["user_agent"]})

    # ---------------------------------------------------------------- rate
    def _wait(self, host: str) -> None:
        gap = 1.0 / float(self.p["requests_per_second_per_host"])
        last = self._last.get(host)
        if last is not None:
            delta = time.monotonic() - last
            if delta < gap:
                time.sleep(gap - delta)
        self._last[host] = time.monotonic()

    # ---------------------------------------------------------------- robots
    def _robots_for(self, base: str):
        if base in self._robots:
            return self._robots[base]
        from protego import Protego
        try:
            r = self.raw_get(urllib.parse.urljoin(base, "/robots.txt"))
            txt = r["body"].decode("utf-8", "replace") if r["body"] else ""
            self._robots[base] = Protego.parse(txt) if txt.strip() else None
        except Exception:
            self._robots[base] = None
        return self._robots[base]

    def allowed(self, url: str) -> bool:
        parts = urllib.parse.urlsplit(url)
        path = parts.path or "/"
        if any(path.startswith(p) for p in self.p["always_fetch_paths"]):
            return True
        rp = self._robots_for(f"{parts.scheme}://{parts.netloc}")
        if rp is None:
            return True
        return bool(rp.can_fetch(url, self.p["user_agent"]))

    # ---------------------------------------------------------------- fetch
    def raw_get(self, url: str) -> dict:
        """One GET, rate-limited, with backoff. Returns a dict; raises nothing for HTTP
        status. `body` is the WHOLE body — `max_body_bytes` is null by default and a cap must
        be set explicitly to exist (§2.3)."""
        host = urllib.parse.urlsplit(url).netloc
        attempts = 0
        while True:
            self._wait(host)
            t0 = time.monotonic()
            resp = self.client.get(url)
            elapsed = int((time.monotonic() - t0) * 1000)
            if resp.status_code in self.p["backoff_on_status"] and attempts < self.p["max_retries"]:
                time.sleep(float(self.p["backoff_base_seconds"]) ** (attempts + 1))
                attempts += 1
                continue
            body = resp.content
            cap = self.p.get("max_body_bytes")
            if cap is not None:
                body = body[:int(cap)]
            return {"status": resp.status_code, "headers": dict(resp.headers), "body": body,
                    "elapsed_ms": elapsed, "final_url": str(resp.url)}


def error_class_for(status: int) -> str | None:
    if status >= 500:
        return "http_5xx"
    if status >= 400:
        return "http_4xx"
    return None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
