"""What went wrong, named once. **Pure: no network, no clock, no I/O.**

Task `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2. The closed set of `error_class` values had
no member for a connection reset, so every collector's fallback —
`"timeout" if "timeout" in type(exc).__name__.lower() else "dns"`, and a bare literal `"dns"`
in five more — filed **92 observations across four StatCan targets** under `dns` when
`www150.statcan.gc.ca` began resetting the socket mid-cycle. It also filed one `TooManyRedirects`
on a Census A10 probe under `dns`, which is not a name resolution failure either.

A fallback is a guess with a default. This module is a MAP: every exception and every status
resolves to a class by an explicit rule, and anything the map does not name resolves to
`unknown`, which is counted and reported per cycle rather than absorbed into a neighbour. An
error class that is a guess cannot be aggregated, and the aggregate is the whole point — eight
legs at 0/23 read differently if the zeros are refusals than if they are failures.

**Two refusals, and they are not the same event.** `refused` is an HTTP-layer refusal: the host
answered, and the answer was 401/403/429 to an identified client on a path robots permits (the
collectors never fetch a disallowed path — a disallow is recorded as `robots_disallowed` with
no request made — so a status seen here is by construction a status on a permitted path).
`connection_reset` is TCP-layer: the peer closed the socket. `ECONNREFUSED` — nothing listening
— is neither, and it resolves to `unknown` deliberately rather than being folded into either;
folding it in would make the count of "hosts that refuse this scanner" include hosts that are
simply down.

Prior art for the split: RFC 9110 §15 puts 401/403/429 in the client-error class *the server
chose to send*, which is a statement about the request; a transport reset is not a statement at
all. Conflating them is what made `www.bls.gov`'s 60-of-60 refusal read as fifteen product
failures in the first smoke run.
"""
from __future__ import annotations

import errno as _errno

#: Every `error_class` a collector may record, and whether it means "we did not OBSERVE the
#: surface". The second field is what `rules/_common.unobserved` reads: a class that means the
#: collector could not see is a class whose Findings must be `error`, never `fail`. Declaring
#: it HERE, beside the class, is the fix for the shape of defect this module exists to close —
#: a new class added to the closed set and forgotten in a blind-list somewhere else would
#: silently turn non-observations into product failures.
#:
#: `http_4xx` is deliberately NOT blind: a 404 on a probed path IS the measurement, and folding
#: it in would leave the harness unable to report absence at all. `refused` IS blind for the
#: opposite reason: the host declined to answer about the path, so there is no measurement.
CLASSES: dict = {
    None: {"blind": False, "note": "the collector observed the surface"},
    "dns": {"blind": True, "note": "the host name did not resolve"},
    "timeout": {"blind": True, "note": "no response within the configured timeout"},
    "connection_reset": {"blind": True, "note": "the peer closed the connection (TCP reset)"},
    "refused": {"blind": True,
                "note": "the host answered 401/403/429 to this identified client on a "
                        "robots-permitted path: declined, not measured"},
    "http_4xx": {"blind": False,
                 "note": "a client-error status that IS the measurement (a 404 on a probed "
                         "path means the path is not served)"},
    "http_5xx": {"blind": True, "note": "a server error is not a product property"},
    # NOT blind, and this is the pre-existing reading preserved deliberately rather than
    # tidied. A declared disallow is not a blind spot: it IS the measurement for A4 and
    # A11-declared, and A12 reads it as `not_applicable` ("a host obeyed is not a host in
    # conflict with itself"). Marking it blind would make `only_errors` return `error` for a
    # leg whose observations are all disallows, changing the verdict of every shipped rule —
    # which `cc_tasks/2026-09-07_scan_harness_v3.md` forbids without a new module.
    "robots_disallowed": {"blind": False, "not_fetched": True,
                          "note": "not fetched, because robots.txt disallows this client; "
                                  "the refusal is evidence, not an absence"},
    # The mirror of `robots_disallowed`, one policy layer up: not fetched because the SCANNER'S
    # own same-host policy (`manners.on_roster_host`) puts the URL outside the measurement, not
    # because anyone refused us. `cc_tasks/2026-09-08_scan_harness_v4.md` §1.3.
    #
    # NOT blind, for the same reason `robots_disallowed` is not: it IS the measurement's scope
    # boundary rather than a failure to see. A1 and A3 ask what the PRODUCT offers, and a link
    # to somebody else's server is not an answer either way — marking it blind would let a
    # page whose links are all off-host return `error` ("we could not look") instead of the
    # true `fail` ("this product offers nothing of its own").
    #
    # It exists as a CLASS rather than as silence because the exclusion used to be a `continue`
    # in `links.probe`: an off-host link left no record at all, so nothing on the log could
    # show whether the policy had been applied, or to what.
    # Declared on one site and hosted on another. `cc_tasks/2026-09-09_closeout_and_manners.md`
    # decision 3: a `robots.txt` may name its sitemap anywhere, and following the name off the
    # site is not discovery, it is a second site. The declaration IS evidence and is recorded
    # with the URL; no request is made.
    #
    # Distinct from `off_host`, which is the SAME-SITE netloc policy applied to links found on
    # a page. Merging them would lose which bound refused the fetch, and the two bounds move
    # independently: `www.samhsa.gov` -> `samhsa.gov` is off-host and ON-site, and is fetched.
    "sitemap_off_site": {"blind": False, "not_fetched": True,
                         "note": "not fetched, because the robots.txt that declared this "
                                 "sitemap is on a different site; the declaration is recorded "
                                 "with its URL and nothing is requested"},
    "off_host": {"blind": False, "not_fetched": True,
                 "note": "not fetched, because the scanner's same-host policy puts this URL "
                         "outside the surface being measured; the exclusion is recorded, "
                         "not silent"},
    "parse_error": {"blind": True, "note": "a response arrived and could not be read"},
    "collector_unavailable": {"blind": True, "note": "the collector itself raised"},
    "unknown": {"blind": True,
                "note": "the map does not name this failure; counted and reported per cycle, "
                        "never absorbed into a neighbour"},
}

ERROR_CLASSES = tuple(CLASSES)
BLIND = tuple(k for k, v in CLASSES.items() if v["blind"])

#: The classes recorded when NO REQUEST WAS MADE, because a policy layer excluded the URL
#: before anything was attempted. They are the two classes with nothing to classify FROM —
#: no exception text, no status — and they need none: the decision is the record.
#:
#: Declared here for the same reason `blind` is (see above), and after the same defect. A test
#: asserting "every error class is grounded in recorded text or a status" carried
#: `robots_disallowed` as a literal exemption; `off_host` arrived one task later as the second
#: member of a set nobody had named, and 164 correctly-recorded observations read as
#: ungrounded. A closed set with an unnamed subset gets re-derived by hand at every call site,
#: and one of them is always stale.
NOT_FETCHED = tuple(k for k, v in CLASSES.items() if v.get("not_fetched"))

#: Exception TYPE name -> class, for failures the type alone settles. httpx's timeout family
#: and protocol errors are unambiguous; `ConnectError` and `ReadError` are not (both cover a
#: reset and a name-resolution failure), so they are absent here and resolved by errno below.
BY_EXCEPTION_TYPE = {
    "ConnectTimeout": "timeout",
    "ReadTimeout": "timeout",
    "WriteTimeout": "timeout",
    "PoolTimeout": "timeout",
    "TimeoutException": "timeout",
    "RemoteProtocolError": "connection_reset",
    "gaierror": "dns",
    "UnsupportedProtocol": "unknown",
    "InvalidURL": "unknown",
    "TooManyRedirects": "unknown",
    "DecodingError": "parse_error",
    # Raised by `manners.Fetcher` itself when robots disallows the URL. It reaches this map
    # because the three collectors that never gated on robots record a failed fetch through a
    # bare `except Exception`, and without an entry here a refusal this scanner CHOSE would be
    # filed as `unknown` — a class that means "the map does not name this failure", which
    # would be false.
    "RobotsDisallowed": "robots_disallowed",
}


class RobotsDisallowed(Exception):
    """`robots.txt` disallows this URL for this user agent, so no request was made.

    An exception rather than a return value because `Fetcher.raw_get`/`raw_head` return a
    response dict and every caller reads it positionally; a sentinel dict would be read as a
    response by the collectors that do not check for it, which is precisely the set of
    collectors this exception exists to protect.
    """

#: OS errno -> class, read from the exception chain. Named through the `errno` module rather
#: than as integers: ECONNRESET is 54 on Darwin and 104 on Linux, and a hard-coded 54 would
#: quietly stop classifying anything the day this runs in CI.
BY_ERRNO = {
    _errno.ECONNRESET: "connection_reset",
    _errno.EPIPE: "connection_reset",
    _errno.ETIMEDOUT: "timeout",
    _errno.EHOSTUNREACH: "unknown",
    _errno.ENETUNREACH: "unknown",
    _errno.ECONNREFUSED: "unknown",
}

#: Substrings in an exception's own message that settle a class the type and errno do not.
#: Last resort before `unknown`, and ordered: the first match wins.
BY_MESSAGE = (
    ("nodename nor servname", "dns"),
    ("name or service not known", "dns"),
    ("temporary failure in name resolution", "dns"),
    ("connection reset", "connection_reset"),
    ("server disconnected", "connection_reset"),
    ("broken pipe", "connection_reset"),
    ("timed out", "timeout"),
)


def _errnos(exc: BaseException) -> list:
    """Every errno on the exception and its `__cause__`/`__context__` chain. httpx wraps the
    OSError, so the number that names the failure is never on the outermost object."""
    out, seen, cur = [], set(), exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        n = getattr(cur, "errno", None)
        if isinstance(n, int):
            out.append(n)
        for a in getattr(cur, "args", ()):
            if isinstance(a, OSError) and isinstance(getattr(a, "errno", None), int):
                out.append(a.errno)
        cur = cur.__cause__ or cur.__context__
    return out


def classify_exception(exc: BaseException) -> str:
    """The `error_class` for a transport failure. Never `None`, never a guess."""
    for cur in (exc, exc.__cause__, exc.__context__):
        if cur is None:
            continue
        hit = BY_EXCEPTION_TYPE.get(type(cur).__name__)
        if hit:
            return hit
    for n in _errnos(exc):
        if n in BY_ERRNO:
            return BY_ERRNO[n]
    msg = f"{type(exc).__name__}: {exc}".lower()
    for needle, cls in BY_MESSAGE:
        if needle in msg:
            return cls
    return "unknown"


def classify_status(status, params: dict) -> str | None:
    """The `error_class` for a response that ARRIVED. `None` means it was a real observation.

    Replaces `manners.error_class_for`, which knew only 4xx/5xx and so could not tell a 404
    (the measurement) from a 403 (the refusal). The refusal statuses are a policy list in
    `params.manners.unobservable_statuses`, not a protocol constant, and they are read from
    there so the same list drives the class and the rules' `unobserved` check.
    """
    if not isinstance(status, int):
        return None
    if status in tuple((params.get("manners") or {}).get("unobservable_statuses") or ()):
        return "refused"
    if status >= 500:
        return "http_5xx"
    if status >= 400:
        return "http_4xx"
    return None


def classify_recorded_error(error_text: str | None) -> str | None:
    """The class for an error a collector already PERSISTED, from its stored text alone.

    Every collector writes `f"{type(exc).__name__}: {exc}"` into `response.error`, so the type
    name and the message both survive on the log even though the exception object does not.
    That is what makes an append-only reclassification of past observations possible without
    re-fetching anything: the evidence for the correction is the record's own bytes.

    `None` when there is no recorded transport error — a response that ARRIVED is classified
    from its status by `classify_status`, which needs params this function is not given.
    """
    if not error_text:
        return None
    head, _, _rest = str(error_text).partition(":")
    hit = BY_EXCEPTION_TYPE.get(head.strip())
    if hit:
        return hit
    low = str(error_text).lower()
    for needle, cls in BY_MESSAGE:
        if needle in low:
            return cls
    return "unknown"
