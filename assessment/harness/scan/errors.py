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

#: **Three kinds, named here and nowhere else** (`cc_tasks/2026-09-10_harness_v5_blind.md`
#: decision 1). Every `error_class` a collector may record is exactly one of them:
#:
#: * ``OBSERVED`` — a response was received. The measurement happened.
#: * ``BLIND``    — either a request was made and no usable answer came back, OR a request to a
#:                  URL **inside the product** was forbidden by policy and never made. Both mean
#:                  the same thing to a rule: nobody read that page, so no verdict about the
#:                  product may rest on it.
#: * ``SCOPE``    — the URL is **outside the product** and was not requested by design. Not a
#:                  failure to see; a boundary of what is being measured.
#:
#: The line between BLIND and SCOPE is inside-the-product versus outside it, and getting it
#: wrong in the other direction is what harness-v4 did: `robots_disallowed` was treated as
#: scope, so a page the scanner was forbidden to read counted as a page it had read and found
#: wanting. Cycle 4 shipped the consequence — `RULE-A10-v3` returned **pass** from "deep link
#: HTTP None; invalid route correctly HTTP None", two probes that were never issued
#: (`cc_tasks/2026-09-10_scan_run_4_RESULT.md` §1) — and 14 verdicts across three cycles rested
#: on evidence nobody collected.
#:
#: `http_4xx` is deliberately OBSERVED: a 404 on a probed path IS the measurement, and folding
#: it into BLIND would leave the harness unable to report absence at all. `refused` is BLIND for
#: the opposite reason: the host declined to answer about the path, so there is no measurement.
OBSERVED, BLIND, SCOPE = "observed", "blind", "scope"

#: The harness version a payload with no recorded version was judged under. Every stored
#: payload before harness-v5 carries none, and every one of them was measured when
#: `robots_disallowed` meant SCOPE. Defaulting to 4 is what makes "re-derive each payload under
#: its own harness version" true without editing a single stored payload (decision 2).
HARNESS_DEFAULT = 4
HARNESS_CURRENT = 5

#: `kind` is a string, or a `{harness_version: kind}` map for the one class whose meaning moved.
#: `requested` answers "was a request actually made" — the question `NOT_FETCHED` used to
#: answer as a class list, kept as an attribute because collectors report it and the manners
#: accounting needs it. It is INDEPENDENT of `kind`: a robots disallow is BLIND and unrequested,
#: an off-host link is SCOPE and unrequested, a timeout is BLIND and requested.
CLASSES: dict = {
    None: {"kind": OBSERVED, "requested": True,
           "note": "the collector observed the surface"},
    "dns": {"kind": BLIND, "requested": True,
            "note": "the host name did not resolve"},
    "timeout": {"kind": BLIND, "requested": True,
                "note": "no response within the configured timeout"},
    "connection_reset": {"kind": BLIND, "requested": True,
                         "note": "the peer closed the connection (TCP reset)"},
    "refused": {"kind": BLIND, "requested": True,
                "note": "the host answered 401/403/429 to this identified client on a "
                        "robots-permitted path: declined, not measured"},
    "http_4xx": {"kind": OBSERVED, "requested": True,
                 "note": "a client-error status that IS the measurement (a 404 on a probed "
                         "path means the path is not served)"},
    "http_5xx": {"kind": BLIND, "requested": True,
                 "note": "a server error is not a product property"},
    # The class whose meaning moved, and the whole reason harness-v5 exists. Under v4 it was
    # scope, on the argument that a declared disallow IS the measurement for A4 and
    # A11-declared. That is true of the DECLARATION and false of everything else: the URL is
    # inside the product and we were forbidden to look at it, so a rule asking what the product
    # OFFERS there is asking about a page nobody read.
    #
    # A4, A11-declared and A12 are unaffected because they read the declaration itself, not the
    # page behind it — and A12-v2 reads the refusal ON PURPOSE (decision 3).
    "robots_disallowed": {"kind": {4: SCOPE, 5: BLIND}, "requested": False,
                          "note": "not fetched, because robots.txt disallows this client: "
                                  "forbidden to look at a URL inside the product"},
    # SCOPE, and it stays scope under every harness version. A1 and A3 ask what the PRODUCT
    # offers, and a link to somebody else's server is not an answer either way — marking it
    # blind would let a page whose links all point elsewhere return `error` ("we could not
    # look") instead of the true `fail` ("this product offers nothing of its own").
    #
    # It exists as a CLASS rather than as silence because the exclusion used to be a `continue`
    # in `links.probe`: an off-host link left no record at all, so nothing on the log could show
    # whether the policy had been applied, or to what.
    "off_host": {"kind": SCOPE, "requested": False,
                 "note": "not fetched, because the scanner's same-host policy puts this URL "
                         "outside the surface being measured; the exclusion is recorded, "
                         "not silent"},
    # Declared on one site and hosted on another (`cc_tasks/2026-09-09_closeout_and_manners.md`
    # decision 3): a `robots.txt` may name its sitemap anywhere, and following the name off the
    # site is not discovery, it is a second site. Distinct from `off_host`, which is the
    # same-site netloc policy applied to links found on a page — the two bounds move
    # independently: `www.samhsa.gov` -> `samhsa.gov` is off-host and ON-site, and is fetched.
    "sitemap_off_site": {"kind": SCOPE, "requested": False,
                         "note": "not fetched, because the robots.txt that declared this "
                                 "sitemap is on a different site; the declaration is recorded "
                                 "with its URL and nothing is requested"},
    "parse_error": {"kind": BLIND, "requested": True,
                    "note": "a response arrived and could not be read"},
    # New in harness-v5 (decision 4). Cycle 4 filed `httpx.TooManyRedirects` on Census's A10
    # invalid-route probe as `unknown` — correctly, because the map did not name it, and the
    # rule refused to reach a verdict and said so. Naming it is the fix the `unknown` count
    # exists to prompt.
    "redirect_loop": {"kind": BLIND, "requested": True,
                      "note": "the server redirected past the configured maximum; no final "
                              "response was received"},
    "collector_unavailable": {"kind": BLIND, "requested": True,
                              "note": "the collector itself raised"},
    "unknown": {"kind": BLIND, "requested": True,
                "note": "the map does not name this failure; counted and reported per cycle, "
                        "never absorbed into a neighbour"},
}

ERROR_CLASSES = tuple(CLASSES)


def harness_of(params: dict | None) -> int:
    """The harness version a params set binds. `HARNESS_DEFAULT` when it binds none.

    Every payload measured before harness-v5 was judged under parameters that say nothing about
    a harness version, and `rederive` recovers each payload's own params from git by hash. So
    this default is not a fallback — it is the statement that an unversioned params set IS a
    v4 params set, which is what makes nine stored payloads re-derive byte-identically while
    the judgement layer underneath them changes.
    """
    return int((params or {}).get("harness_version") or HARNESS_DEFAULT)


def kind_of(error_class, harness: int = HARNESS_DEFAULT) -> str:
    """`OBSERVED`, `BLIND` or `SCOPE` for one class under one harness version."""
    entry = CLASSES.get(error_class)
    if entry is None:
        # An unrecognised class is not silently observed: `unknown` is the map's own name for
        # "not named here" and it is BLIND, so anything off the map inherits that reading.
        return BLIND
    k = entry["kind"]
    if isinstance(k, dict):
        return k.get(harness) or k[max(v for v in k if v <= harness)]
    return k


def is_blind(error_class, harness: int = HARNESS_DEFAULT) -> bool:
    """True when no verdict about the product may rest on this observation."""
    return kind_of(error_class, harness) == BLIND


def classes_of_kind(kind: str, harness: int = HARNESS_DEFAULT) -> tuple:
    return tuple(c for c in CLASSES if kind_of(c, harness) == kind)


def blind_classes(harness: int = HARNESS_DEFAULT) -> tuple:
    return classes_of_kind(BLIND, harness)


def scope_classes(harness: int = HARNESS_DEFAULT) -> tuple:
    return classes_of_kind(SCOPE, harness)


#: Classes recorded when NO REQUEST WAS MADE, because a policy layer excluded the URL before
#: anything was attempted. This replaces `NOT_FETCHED`, which named the same set but named it as
#: a KIND — and it is not one: `robots_disallowed` is unrequested and BLIND, `off_host` is
#: unrequested and SCOPE. Conflating "no request went out" with "outside the measurement" is
#: precisely the confusion harness-v5 unpicks.
NOT_REQUESTED = tuple(c for c, v in CLASSES.items() if not v["requested"])


def note_for(error_class, default: str = "") -> str:
    """The class's own note. The accessor exists so no rule reaches into `CLASSES` — decision 1
    puts the table behind functions, and a `.get(...).get(...)` at a call site is how a table
    acquires a second reader with its own idea of the shape."""
    return (CLASSES.get(error_class) or {}).get("note", default)

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
    "TooManyRedirects": "redirect_loop",
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
