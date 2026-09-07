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


def make(rule_id: str, leg: str, obs: list, verdict: str, reason: str, params: dict) -> Finding:
    return Finding.make(rule_id=rule_id, rule_version=rule_version(rule_id, params), leg=leg,
                        target_doc_id=target(obs), verdict=verdict, evidence=ids(obs),
                        reason=reason, params=params)


def empty(rule_id: str, leg: str, params: dict, doc_id: str = "unknown") -> Finding:
    return Finding.make(rule_id=rule_id, rule_version=rule_version(rule_id, params), leg=leg,
                        target_doc_id=doc_id, verdict="error", evidence=[],
                        reason="no observations were collected for this leg", params=params)
