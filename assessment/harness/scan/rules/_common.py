"""Helpers every rule shares. Pure."""
from __future__ import annotations

from .. import errors as _errors
from ..model import Finding

#: The `rule_version` every rule stamped under `finding_identity: 1` — the literal `"v1"` for
#: every rule ever shipped, including `RULE-A3-v3`. Kept, never corrected: it is an INPUT to
#: the derived `finding_id` (`model.py::Finding.make`), so changing what it MEANS would
#: re-identify all 1,353 stored Findings. `finding_identity` in `params.yaml` is how it moves
#: instead — the scheme is versioned data, not an edit to the past.
RULE_VERSION = "v1"

def _version_from_rule_id(rule_id: str) -> str:
    """`RULE-A3-v4` -> `v4`. The import is local because `rules/__init__` imports the rule
    modules, which import this one: a module-level import of the package would be circular."""
    from . import parse_rule_id
    return parse_rule_id(rule_id)["version"]


#: `finding_identity` -> how `rule_version` is derived. A dispatch table rather than an
#: if-chain, so a third scheme is one new entry rather than a new branch in `make` AND `empty`.
_IDENTITY = {1: lambda rule_id: RULE_VERSION, 2: _version_from_rule_id}


def rule_version(rule_id: str, params: dict) -> str:
    """The `rule_version` to stamp on a Finding, under the params' identity scheme.

    Defaults to 1 — the scheme every stored Finding was made under — so a params set that
    predates the key re-derives byte-identically. An unknown scheme is a hard error: silently
    falling back to 1 would mint ids under a scheme the params do not name, and the
    re-derivation gate would then disagree with the log for a reason nobody could see.
    """
    scheme = params.get("finding_identity", 1)
    try:
        return _IDENTITY[int(scheme)](rule_id)
    except (KeyError, ValueError, TypeError):
        raise ValueError(
            f"finding_identity {scheme!r} is not a known Finding-id scheme "
            f"{sorted(_IDENTITY)}; see params.yaml") from None


def ids(obs: list) -> list:
    return [o.obs_id for o in obs]


def target(obs: list) -> str:
    return obs[0].target_doc_id if obs else "unknown"


#: Error classes that always mean "we did not observe". Read from `errors.CLASSES`, where each
#: class declares its own blindness beside the rule that produces it, rather than restated
#: here: `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2 added `connection_reset`, `refused` and
#: `unknown` to the closed set, and a hand-kept list here would have silently turned the 92
#: StatCan non-observations into 92 product failures the moment the classifier improved. That
#: is the exact shape of the bug the new classifier exists to close, one layer up.
#:
#: `http_4xx` is deliberately NOT blind: a 404 on a probed path IS the measurement, and folding
#: it in would leave the harness unable to report absence at all. `refused` IS blind — the host
#: declined to answer about the path, so there is no measurement — which is the same reading
#: `manners.unobservable_statuses` already gave a 403 below, now carried on the class as well.
_BLIND = tuple(c for c in _errors.BLIND if c is not None)


def unobserved(o, params: dict) -> bool:
    """True when this one observation is a non-observation. Two ways that happens: the
    collector never got a response (`_BLIND`), or it got one whose status says the host
    refused this client rather than answering about the path
    (`manners.unobservable_statuses`)."""
    if o.error_class in _BLIND:
        return True
    status = (o.response or {}).get("status")
    return status in (params.get("manners") or {}).get("unobservable_statuses", ())


def only_errors(obs: list, params: dict) -> bool:
    """True when every observation failed to observe. Distinguishes `error` (the collector
    could not see) from `fail` (it saw, and the product does not have the property).

    Takes `params` because the refusal statuses are a policy list, not a protocol constant —
    `www.bls.gov` 403s an identified scanner UA on every path, and reading that as fifteen
    product failures was the smoke run's worst defect.
    """
    return bool(obs) and all(unobserved(o, params) for o in obs)


def served(o) -> bool:
    """True when this observation carries a real, non-error HTTP status.

    Written because four `v2` rules got it wrong the same way and one of them crashed a live
    cycle: `(o.response or {}).get("status", 999) < 400` looks like a safe default and is not.
    The key `status` is always PRESENT on an Observation — it is `None` when nothing was
    fetched (a robots disallow, a DNS failure, a timeout) — so `.get` returns `None` rather
    than the default, and the comparison raises `TypeError`. A default only fires on a MISSING
    key, never on a present one holding `None`.

    Naming the check once is the fix: a guard duplicated in four modules is a guard that will
    be wrong in four modules.
    """
    st = (getattr(o, "response", None) or {}).get("status")
    return isinstance(st, int) and st < 400


def host_of(url: str) -> str:
    """The host of a URL, by string surgery, because a rule may not import `urllib`.

    `tests/test_scan_harness.py::test_no_rule_reaches_the_network_a_clock_or_the_filesystem`
    bans the whole `urllib` PACKAGE from `rules/`, not `urllib.request` alone, and it is right
    to: a module that can reach `urllib.parse` can reach `urllib.request` on the next edit, and
    the purity of a rule is what makes re-judging history without re-measuring it meaningful.
    So the one thing a rule needs from a URL is done here, once, in pure string work.

    Not a URL parser and not trying to be. It is a COMPARATOR: both sides of every comparison
    go through this same function, so a scheme, a port or a userinfo segment that it handles
    unusually still makes the two sides agree or disagree for the same reason. The collector
    (`manners.on_roster_host`) uses `urllib.parse` and is the authority on what gets FETCHED;
    this only has to reproduce that judgement over stored records.
    """
    rest = str(url or "").split("://", 1)[-1]
    for sep in ("/", "?", "#"):
        rest = rest.split(sep, 1)[0]
    return rest.rsplit("@", 1)[-1].lower()


def make(rule_id: str, leg: str, obs: list, verdict: str, reason: str, params: dict) -> Finding:
    return Finding.make(rule_id=rule_id, rule_version=rule_version(rule_id, params), leg=leg,
                        target_doc_id=target(obs), verdict=verdict, evidence=ids(obs),
                        reason=reason, params=params)


def empty(rule_id: str, leg: str, params: dict, doc_id: str = "unknown") -> Finding:
    return Finding.make(rule_id=rule_id, rule_version=rule_version(rule_id, params), leg=leg,
                        target_doc_id=doc_id, verdict="error", evidence=[],
                        reason="no observations were collected for this leg", params=params)


def unobserved_error(rule_id: str, leg: str, obs: list, probe, params: dict, what: str):
    """The `error` Finding a rule owes when a probe it is ABOUT TO SCORE ON was never
    observed — or `None` when the probe is real and the rule may go on.

    `only_errors` asks the question of a WHOLE surface: it fires only when every observation
    is blind. That leaves the case this exists for wide open. On
    `scan-eia-flagship-1-open-data` the A10 valid-route probe returned HTTP 200 and the
    invalid-route probe raised `RemoteProtocolError` (`connection_reset`, blind), so
    `only_errors` was false, and `RULE-A10-v2` — which tests only that the invalid route is
    not 200 — read a killed connection as a correct rejection and returned **pass**
    (`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.2).

    DD-052 §6 says `error` must never mean the product FAILED. The mirror was nowhere
    enforced: `error` must never mean the product PASSED either. A verdict reached from a
    probe the collector never saw is a measurement of the scanner, not of the product, and it
    is a defect by construction whichever direction it points.

    Every rule of generation 4 and later calls this on each probe it reads; a lint over
    `rules/` (`tests/test_scan_harness_v4.py`) fails a module that does not, so the guard
    cannot be forgotten in the one rule where it matters.
    """
    if probe is None or not unobserved(probe, params):
        return None
    status = (getattr(probe, "response", None) or {}).get("status")
    named = probe.error_class or f"HTTP {status}"
    note = (_errors.CLASSES.get(probe.error_class) or {}).get(
        "note", "the host declined to answer this client about the path")
    return make(rule_id, leg, obs, "error",
                f"{what} was not observed ({named}): {note}. A verdict reached from a probe "
                f"the collector never saw would be a measurement of the scanner, not of the "
                f"product", params)
