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
        t0 = time.monotonic()
        resp = self.client.head(url)
        elapsed = int((time.monotonic() - t0) * 1000)
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


#: The registrable-domain resolver, built ONCE and **offline**.
#:
#: `suffix_list_urls=()` is not an optimisation: `tldextract`'s default is to fetch the Public
#: Suffix List over the network on first use, and this harness must be able to state that a
#: cycle contacted exactly the hosts it measured. A resolver that quietly fetched mozilla.org
#: would falsify that in the one module whose whole subject is what we may contact.
_EXTRACT = None


def _extractor():
    global _EXTRACT
    if _EXTRACT is None:
        import tldextract
        _EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), fallback_to_snapshot=True)
    return _EXTRACT


def psl_identity() -> dict:
    """What the site resolver is deciding with, so a cycle can register it.

    `cc_tasks/2026-09-09_closeout_and_manners.md` decision 2 asks for "the list snapshot's
    date". **The package carries no date**: the bundled snapshot is the raw Public Suffix List
    with an MPL header and no timestamp, and its file mtime is the install time, not the
    snapshot's. The version and the snapshot's digest identify it exactly and are recorded
    instead; a date recovered from an mtime would be a number that looks like provenance and
    is not.
    """
    import hashlib
    import tldextract
    snap = Path(tldextract.__file__).resolve().parent / ".tld_set_snapshot"
    return {"resolver": "tldextract",
            "version": getattr(tldextract, "__version__", "unknown"),
            "snapshot_sha256": (hashlib.sha256(snap.read_bytes()).hexdigest()
                                if snap.is_file() else None),
            "snapshot_date": None,
            "snapshot_date_note": ("the bundled Public Suffix List snapshot carries no date; "
                                   "version and digest identify it")}


def site_of(url_or_host: str) -> str:
    """The SITE a URL belongs to: its registrable domain under the Public Suffix List.

    Decision 2, and the definition is the one the WHATWG URL and Fetch standards use for
    "same site": scheme plus registrable domain, with the **port excluded**. `www.samhsa.gov`
    and `samhsa.gov` are one site; `127.0.0.1:1` and `127.0.0.1:2` are one site.

    An IP-literal host has no registrable domain, and `tldextract` returns an empty string for
    it. The host itself is the site key in that case, which is what makes the loopback fixture
    a same-site pair rather than two unrelated authorities.
    """
    host = url_or_host
    if "//" in host:
        host = urllib.parse.urlsplit(host).netloc
    host = (host or "").split("@")[-1].rsplit(":", 1)[0].strip("[]").lower()
    if not host:
        return ""
    reg = _extractor()(f"http://{host}").registered_domain
    return reg or host


def same_site(a: str, b: str) -> bool:
    """Whether two URLs or hosts belong to one site. Empty never matches empty."""
    sa, sb = site_of(a), site_of(b)
    return bool(sa) and sa == sb


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
    host = urllib.parse.urlsplit(surface_url or "").netloc
    if not host:
        return True
    return urllib.parse.urlsplit(url or "").netloc == host


# `error_class_for(status)` lived here and knew only 4xx/5xx, so it could not tell a 404 (the
# measurement) from a 403 (the host declining this client). It is superseded by
# `scan.errors.classify_status(status, params)`, which reads the refusal statuses from params
# rather than from a constant — see `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2.


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
