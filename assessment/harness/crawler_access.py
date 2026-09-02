"""The crawler-access triad: declared / enforced / observed (skeleton A11).

A4 in the crosswalk asks whether crawlers are permitted. A11 upgrades that to a
three-layer comparison, because the layers can disagree and the disagreement is
the finding, not an error state:

  declared         what robots.txt says a client may fetch (RFC 9309 semantics via
                   stdlib `urllib.robotparser`; page-level meta/X-Robots-Tag
                   directives are read by `d1_robots_directives`, not here).
  enforced         what the edge / WAF / bot-management layer does to a client.
                   Visible only in the agency's own edge logs, so the PUBLIC tier
                   cannot measure it; this module reads an optional operator-
                   supplied observation file (agencies.toml
                   `enforced_observations_file`) and reports null otherwise.
  observed_public  what the harness's own requests actually receive, per client
                   identity, across the multi-attempt fetches `d2_no_barriers`
                   already makes (so the intermittency machinery is reused and no
                   request is added for the default identity).

Every function here is pure: it takes robots.txt text, already-fetched attempts,
and an already-loaded observation map. The runner does the fetching.

Observed facts and calculated warnings are kept apart (skeleton §6b.5). The fact
is `effective_crawler_access`; the warning is `crawler_policy_mismatch_warning`,
produced by a rule with a version id, so the rule can change and history can be
re-scored. The rule: robots.txt ALLOWS a client that the observed requests
REFUSE. The reverse (robots disallows, the edge serves anyway) is recorded as an
observation on the same record but fires no warning, because a site that serves
more than it promised has not gated anyone.

Prior art: the D0-r2 annotation in census-web-concept-inventory (2026-09-01),
which measured census.gov/quickfacts refusing 5 of 8 sampled pages under a `*`
group that disallows nothing there. That is the mismatch this module names.
"""
from __future__ import annotations

import json
import urllib.robotparser
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .probes._formats import has_barrier_markers

# Identifier and version of the mismatch rule, carried in every warning.
MISMATCH_RULE_ID = "crawler_policy_mismatch"
MISMATCH_RULE_VERSION = "1"

# Body markers of an interstitial challenge page (bot-management "checking your
# browser" screens). A 200 carrying one of these is a refusal in disguise: the
# client did not receive the resource. Kept beside BARRIER_MARKERS as a code
# constant because these are recognizers, not thresholds.
CHALLENGE_MARKERS = (
    "checking your browser", "just a moment", "cf-chl", "challenge-platform",
    "attention required", "access denied", "request unsuccessful. incapsula",
    "verify you are human", "ddos-guard",
)

ENFORCED_SCHEMA = "enforced_observations/1"
ENFORCED_ACTIONS = ("allow", "block", "challenge", "rate_limit")


class EnforcedObservationsError(Exception):
    """The operator-supplied enforced-observations file is malformed. Names the
    path and the defect; never silently treated as 'no observations'."""


def declared_access(robots_body: str, url: str, user_agents: Iterable[str]) -> Dict[str, str]:
    """robots.txt eligibility of `url` for each client token: "allow" / "disallow".

    Missing or empty robots.txt allows everything (RFC 9309 §2.3.1.3, the
    unavailable-file case treated as full access), which is what `robotparser`
    does with no rules. An "allow" here is therefore a declaration, not a
    promise that the edge will serve.
    """
    parser = urllib.robotparser.RobotFileParser()
    parser.parse((robots_body or "").splitlines())
    out: Dict[str, str] = {}
    for ua in user_agents:
        token = ua if ua else "*"
        out[ua] = "allow" if parser.can_fetch(token, url) else "disallow"
    return out


def _attempt_outcome(attempt, refusal_statuses: Iterable[int]) -> str:
    """One attempt's outcome vocabulary: served / refused / challenge / unreachable."""
    if attempt.error is not None or attempt.status is None:
        return "unreachable"
    if attempt.status in tuple(refusal_statuses):
        return "refused"
    body = (attempt.body or "").lower()
    if any(m in body for m in CHALLENGE_MARKERS) or has_barrier_markers(body):
        return "challenge"
    if 200 <= attempt.status < 300:
        return "served"
    # 3xx that did not resolve, 4xx other than refusals, 5xx.
    return "unreachable"


def observed_access(attempts_by_ua: Dict[str, List], refusal_statuses: Iterable[int]) -> Dict[str, dict]:
    """What each client identity received across its attempts.

    `outcome` collapses the attempts: "served" only when every attempt was
    served; "refused" / "challenge" when every attempt was that; "mixed" when
    attempts disagree, with the per-attempt outcomes and statuses kept so a
    reviewer sees the intermittency rather than a summary of it.
    """
    out: Dict[str, dict] = {}
    for ua, attempts in attempts_by_ua.items():
        outcomes = [_attempt_outcome(a, refusal_statuses) for a in attempts]
        statuses = [a.status for a in attempts]
        distinct = set(outcomes)
        if not outcomes:
            collapsed = "unobserved"
        elif len(distinct) == 1:
            collapsed = outcomes[0]
        else:
            collapsed = "mixed"
        refused_like = sum(1 for o in outcomes if o in ("refused", "challenge"))
        out[ua] = {
            "outcome": collapsed,
            "attempts": len(outcomes),
            "per_attempt": outcomes,
            "statuses": statuses,
            "refusal_fraction": (round(refused_like / len(outcomes), 4)
                                 if outcomes else None),
        }
    return out


def load_enforced_observations(path: Optional[str]) -> Optional[dict]:
    """Read the operator-supplied enforced-layer file, or None when no path is
    configured. A configured path that is missing or malformed fails loud."""
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        raise EnforcedObservationsError(f"enforced_observations_file not found: {p}")
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, ValueError) as exc:
        raise EnforcedObservationsError(f"enforced_observations_file is not JSON: {p}: {exc}")
    if not isinstance(data, dict) or data.get("schema") != ENFORCED_SCHEMA:
        raise EnforcedObservationsError(
            f"enforced_observations_file {p} must declare schema {ENFORCED_SCHEMA!r}; "
            f"got {data.get('schema') if isinstance(data, dict) else type(data).__name__!r}")
    obs = data.get("observations")
    if not isinstance(obs, dict):
        raise EnforcedObservationsError(
            f"enforced_observations_file {p}: 'observations' must be an object keyed by URL")
    for url, per_ua in obs.items():
        if not isinstance(per_ua, dict):
            raise EnforcedObservationsError(
                f"enforced_observations_file {p}: observations[{url!r}] must be an object keyed by user-agent token")
        for ua, rec in per_ua.items():
            if not isinstance(rec, dict) or rec.get("action") not in ENFORCED_ACTIONS:
                raise EnforcedObservationsError(
                    f"enforced_observations_file {p}: observations[{url!r}][{ua!r}].action "
                    f"must be one of {ENFORCED_ACTIONS}")
    return data


def enforced_access(enforced: Optional[dict], url: str, user_agents: Iterable[str]) -> Dict[str, Optional[dict]]:
    """The enforced leg for `url`, per token: the operator's record or None."""
    per_url = ((enforced or {}).get("observations") or {}).get(url) or {}
    return {ua: (dict(per_url[ua]) if ua in per_url else None) for ua in user_agents}


def effective_crawler_access(
    robots_body: str,
    url: str,
    attempts_by_ua: Dict[str, List],
    declared_user_agents: Iterable[str],
    refusal_statuses: Iterable[int],
    enforced: Optional[dict] = None,
) -> dict:
    """The observed fact: all three layers for every token, side by side.

    Tokens = the configured declared list plus every identity that was actually
    sent. A token with no observed attempts carries `observed_public: null`, so
    a declared-only token is never mistaken for one that was tested.
    """
    tokens: List[str] = []
    for ua in list(declared_user_agents) + list(attempts_by_ua):
        if ua not in tokens:
            tokens.append(ua)
    declared = declared_access(robots_body, url, tokens)
    observed = observed_access(attempts_by_ua, refusal_statuses)
    enforced_leg = enforced_access(enforced, url, tokens)
    return {
        "url": url,
        "layers": {
            ua: {
                "declared": declared[ua],
                "enforced": enforced_leg[ua],
                "observed_public": observed.get(ua),
            }
            for ua in tokens
        },
        "enforced_source": ((enforced or {}).get("source") if enforced else None),
        "enforced_note": (
            None if enforced else
            "enforced layer not observable from the public tier; supply "
            "agencies.toml enforced_observations_file to populate it"
        ),
    }


def mismatch_warning(access: dict) -> dict:
    """The versioned warning rule over an `effective_crawler_access` fact.

    Fires when any token is DECLARED allowed and OBSERVED refused on at least one
    attempt ("refused", "challenge", or "mixed" with any refused/challenge
    attempt). Also lists the reverse case as an observation, without firing.
    """
    allowed_but_refused: List[dict] = []
    disallowed_but_served: List[str] = []
    for ua, layers in access.get("layers", {}).items():
        obs = layers.get("observed_public")
        if not obs:
            continue
        refused_any = any(o in ("refused", "challenge") for o in obs.get("per_attempt", []))
        if layers["declared"] == "allow" and refused_any:
            allowed_but_refused.append({
                "user_agent": ua,
                "observed_outcome": obs["outcome"],
                "statuses": obs["statuses"],
                "refusal_fraction": obs["refusal_fraction"],
            })
        if layers["declared"] == "disallow" and obs["outcome"] == "served":
            disallowed_but_served.append(ua)
    return {
        "rule_id": MISMATCH_RULE_ID,
        "rule_version": MISMATCH_RULE_VERSION,
        "fired": bool(allowed_but_refused),
        "declared_vs_observed_mismatch": allowed_but_refused,
        "declared_disallowed_but_served": disallowed_but_served,
        "definition": (
            "fires when robots.txt allows a client that the harness's observed "
            "requests refuse (HTTP refusal status or challenge page) on any attempt"
        ),
    }
