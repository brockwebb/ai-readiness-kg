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

import collections
import urllib.parse
from pathlib import Path

VERSION = "0.1.0"


class Fetcher:
    """A rate-limited, robots-respecting HTTP client. One per run."""

    def __init__(self, params: dict, client=None, clock=None) -> None:
        """`clock` defaults to the real one. A caller that wants virtual time passes it here
        and nowhere else; `run.py::main` does not accept one, so a cycle against real hosts
        cannot be constructed unthrottled (`cc_tasks/2026-09-10_virtual_time.md` decision 1)."""
        import httpx
        from .clock import REAL
        self.p = params["manners"]
        self.params = params
        self.clock = clock or REAL
        self._last: dict = {}
        self._robots: dict = {}
        #: Per netloc, the times at which a request was issued, on THIS fetcher's clock. The
        #: limiter's contract is a minimum gap between consecutive requests to one host, and
        #: under a virtual clock that contract is assertable instead of merely slept through
        #: (decision 2).
        self.request_times: dict = {}
        #: Requests actually issued, per host. Counted here rather than derived from
        #: Observations because an Observation is not a request: A1/A3's link probe issues one
        #: HEAD per link and records them inside ONE observation's `parsed`, and a 429 retry or
        #: a HEAD-refused GET fallback issues a second request under the same record. This is
        #: the number the manners claim is about — what this scanner asked of someone else's
        #: server — so it is the number the cycle reports (`cc_tasks/2026-09-07_scan_run_2.md`
        #: §2, which asserts the shared link probe against it).
        self.requests: collections.Counter = collections.Counter()
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
            delta = self.clock.now() - last
            if delta < gap:
                self.clock.sleep(gap - delta)
        stamp = self.clock.now()
        self._last[host] = stamp
        self.request_times.setdefault(host, []).append(stamp)

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

    def ensure_robots(self, url: str) -> None:
        """Read and parse this netloc's `robots.txt` BEFORE anything else is asked of it.

        `cc_tasks/2026-09-09_closeout_and_manners.md` decision 1, and it is strictly stronger
        than `allowed()`. `always_fetch_paths` short-circuits `allowed()` to True without ever
        consulting robots, which is right for the permission question (a `robots.txt` that
        disallows `/robots.txt` cannot thereby hide it from a measurement OF robots.txt) and
        wrong for the manners question. Cycle 3 issued `GET https://samhsa.gov/sitemap.xml`,
        a carve-out path on a netloc nothing had read robots for, and `allowed()` would have
        waved it through.

        The bootstrap is the one exemption and it is structural: fetching `/robots.txt` cannot
        require having fetched `/robots.txt`.
        """
        parts = urllib.parse.urlsplit(url)
        if (parts.path or "/") == "/robots.txt":
            return
        self._robots_for(f"{parts.scheme}://{parts.netloc}")

    def _gate(self, url: str) -> None:
        """Robots-first, then obey. Raises `RobotsDisallowed` rather than returning, so a
        collector that never checked cannot mistake a refusal for a response."""
        from .errors import RobotsDisallowed
        self.ensure_robots(url)
        if not self.allowed(url):
            raise RobotsDisallowed(url)

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
        be set explicitly to exist (§2.3).

        **Robots-first is enforced here and not in the collectors** (DD-062). It was the
        collectors' job and three of them never did it: `sitemap.fetch`, `dcat.fetch_catalog`
        and `lighthouse.fetch` issued GETs with no robots read at all. An obligation every
        caller must remember is an obligation some caller will forget, and the one that forgot
        reached federal hosts.
        """
        self._gate(url)
        host = urllib.parse.urlsplit(url).netloc
        attempts = 0
        while True:
            self._wait(host)
            self.requests[host] += 1
            t0 = self.clock.now()
            resp = self.client.get(url)
            elapsed = int((self.clock.now() - t0) * 1000)
            if resp.status_code in self.p["backoff_on_status"] and attempts < self.p["max_retries"]:
                self.clock.sleep(float(self.p["backoff_base_seconds"]) ** (attempts + 1))
                attempts += 1
                continue
            body = resp.content
            cap = self.p.get("max_body_bytes")
            if cap is not None:
                body = body[:int(cap)]
            return {"status": resp.status_code, "headers": dict(resp.headers), "body": body,
                    "elapsed_ms": elapsed, "final_url": str(resp.url)}


    def raw_head(self, url: str) -> dict:
        """One HEAD, same manners. A1-v2 and A3-v2 need the per-link `Content-Type` their
        specs say to read ("for each, HEAD and read Content-Type and file extension"); v1
        classified on the href suffix alone, so an extensionless endpoint serving `text/csv`
        was invisible to it.

        A host that answers 405/501 is retried once as a GET, because refusing HEAD is a
        server quirk and reading it as "this link has no content type" would score the quirk
        as a property of the product.

        Robots-first applies here too (DD-062); see `raw_get`.
        """
        self._gate(url)
        host = urllib.parse.urlsplit(url).netloc
        self._wait(host)
        self.requests[host] += 1
        t0 = self.clock.now()
        resp = self.client.head(url)
        elapsed = int((self.clock.now() - t0) * 1000)
        if resp.status_code in self.params.get("link_probe", {}).get(
                "fallback_get_on_status", []):
            got = self.raw_get(url)
            return {**got, "method": "GET", "head_refused_status": resp.status_code}
        return {"status": resp.status_code, "headers": dict(resp.headers), "body": b"",
                "elapsed_ms": elapsed, "final_url": str(resp.url), "method": "HEAD"}


#: The two spellings of the one same-host policy. `probes.same_host_only` is the key; the
#: `link_probe` one is where it used to live and is kept readable because the 2026-09-07 and
#: 2026-09-07b cycles were measured under it and their params sets are recovered from git by
#: hash for the re-derivation gate.
_SAME_HOST_KEYS = (("probes", "same_host_only"), ("link_probe", "same_host_only"))


#: One leading `www.` and nothing else. Stripping every leading label would make
#: `nces.ed.gov` into `ed.gov`, which is the merge DD-063 exists to undo.
_WWW = "www."


def netloc_of(url_or_host: str) -> str:
    """The bare, lowercased host of a URL or a host string: no scheme, no port, no userinfo."""
    host = url_or_host or ""
    if "//" in host:
        host = urllib.parse.urlsplit(host).netloc
    return host.split("@")[-1].rsplit(":", 1)[0].strip("[]").lower()


def site_key(url_or_host: str) -> str:
    """The SITE KEY of a roster host: the host with one leading `www.` stripped.

    **DD-063, superseding DD-062's registrable-domain definition.** The Public Suffix List
    answers a different question from the one this harness asks. It gave `usda.gov` for
    `www.ers.usda.gov`, `ed.gov` for `nces.ed.gov` and `ojp.gov` for `bjs.ojp.gov`, so the
    frame's 22 netlocs collapsed to 17 sites, three separately recognized statistical agencies
    became one contact unit, and every netloc under a department domain came into scope. The
    registrable domain is the right unit for cookie scope and the wrong one for "which host is
    this agency".

    The roster host IS the unit. Stripping one `www.` is the whole of the normalisation,
    because `www.samhsa.gov` and `samhsa.gov` are the same site by anyone's reading and that
    single pair is the entire real-world case cycle 3 produced.
    """
    host = netloc_of(url_or_host)
    return host[len(_WWW):] if host.startswith(_WWW) else host


def same_site(url_or_host: str, key_or_surface: str) -> bool:
    """Whether a netloc belongs to the site identified by `key_or_surface`.

    **Prior art: RFC 6265 §5.1.3 domain-matching**, adopted rather than invented. A string
    domain-matches a domain string if they are identical, or if the string is a suffix of it
    and the character immediately before the match is a dot. That is exactly the test a cookie
    uses to decide whether it may be sent to a host, and exactly the question here: does this
    netloc belong to the site we are measuring.

    `key_or_surface` may be a bare key or a full surface URL; both are reduced through
    `site_key`, so a caller cannot get the asymmetry wrong by passing the wrong one.
    """
    key = site_key(key_or_surface)
    host = netloc_of(url_or_host)
    if not key or not host:
        return False
    return host == key or host.endswith("." + key)


def same_host_only(params: dict) -> bool:
    """Whether a collector may dereference a URL it discovered on a surface but off its host.

    **One policy, read in one place.** `cc_tasks/2026-09-08_scan_harness_v4.md` §1.3: the
    switch was enforced in `collectors/links.probe` and nowhere else, so
    `collectors/v2clauses.follow_latest_pointer` dereferenced `public.govdelivery.com` from a
    Census surface (`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.1). A policy enforced in one
    of the two places it applies is not a policy; it is a comment.

    Two keys that could hold different values would be two policies again, so a disagreement is
    a hard error rather than a precedence rule. A precedence rule makes the stale key
    unreadable in exactly the way that hides the defect: the reader sees `true` and the code
    obeys `false`.
    """
    seen = {}
    for section, key in _SAME_HOST_KEYS:
        block = params.get(section) or {}
        if key in block:
            seen[f"{section}.{key}"] = bool(block[key])
    if len(set(seen.values())) > 1:
        raise ValueError(
            f"the same-host policy is declared twice and the two disagree: {seen}. There is "
            f"ONE policy (params.probes.same_host_only); `link_probe.same_host_only` is the "
            f"superseded spelling kept readable for the cycles measured under it, and it may "
            f"not diverge from it.")
    #: Default TRUE, not false. The absent-key case is a params set that predates the policy,
    #: and every such set carried `link_probe.same_host_only: true`; defaulting to false would
    #: make a missing key mean "probe the whole internet", which is the wrong direction for a
    #: default that governs what this scanner asks of hosts it does not measure.
    return next(iter(seen.values()), True)


def on_roster_host(url: str, surface_url: str, params: dict) -> bool:
    """True when `url` may be dereferenced while measuring the surface at `surface_url`.

    The single gate every collector that follows a discovered link goes through. A surface's
    own host is the subject of the measurement; anything else is somebody else's server, and
    A1, A3 and A8 all ask what the PRODUCT offers rather than what it links to.

    A surface URL with no host (the empty string a caller may pass when there is nothing to
    compare against) leaves the policy unenforceable, and the answer is True: refusing every
    URL because the caller gave us nothing to compare against would silently stop collecting.
    """
    if not same_host_only(params):
        return True
    if not netloc_of(surface_url):
        return True
    # ONE test, shared with the declaration bound (DD-063 decision 2). This used to be netloc
    # equality while `sitemap.fetch` used a different comparison for declared URLs, which is
    # two contact policies wearing one name: a sibling netloc was off-limits to a link and
    # reachable through a `Sitemap:` line.
    return same_site(url, surface_url)


# `error_class_for(status)` lived here and knew only 4xx/5xx, so it could not tell a 404 (the
# measurement) from a 403 (the host declining this client). It is superseded by
# `scan.errors.classify_status(status, params)`, which reads the refusal statuses from params
# rather than from a constant — see `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2.


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
