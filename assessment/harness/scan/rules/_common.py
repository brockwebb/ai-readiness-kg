"""Helpers every rule shares. Pure."""
from __future__ import annotations

from ..model import Finding

RULE_VERSION = "v1"


def ids(obs: list) -> list:
    return [o.obs_id for o in obs]


def target(obs: list) -> str:
    return obs[0].target_doc_id if obs else "unknown"


#: Error classes that always mean "we did not observe". `http_4xx` is deliberately absent: a
#: 404 on a probed path IS the measurement, and folding it in here would leave the harness
#: unable to report absence at all.
_BLIND = ("dns", "timeout", "http_5xx", "parse_error", "collector_unavailable")


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


def make(rule_id: str, leg: str, obs: list, verdict: str, reason: str, params: dict) -> Finding:
    return Finding.make(rule_id=rule_id, rule_version=RULE_VERSION, leg=leg,
                        target_doc_id=target(obs), verdict=verdict, evidence=ids(obs),
                        reason=reason, params=params)


def empty(rule_id: str, leg: str, params: dict, doc_id: str = "unknown") -> Finding:
    return Finding.make(rule_id=rule_id, rule_version=RULE_VERSION, leg=leg,
                        target_doc_id=doc_id, verdict="error", evidence=[],
                        reason="no observations were collected for this leg", params=params)
