"""A12 — access policy coherence. **CANDIDATE (DD-054): reported, never in any fraction.**

*An identified, robots-compliant machine client that robots.txt permits is served — not
refused by a WAF or bot manager.*

Task `cc_tasks/2026-09-07_scan_run.md` §1. This judges a SYNTHETIC HOST surface, not a
document: the question is whether one host's declared layer and its enforced layer agree, and
that is a property of the host rather than of any product on it.

The branch order matters and is not the order §1 lists, for a reason worth stating: §1 names
three cases (permits+served, permits+refused, disallows) and a real host produced a fourth on
the very run this rule was written for — `www.bls.gov` refuses **`/robots.txt` itself**. A rule
that only asked "does robots permit?" would have to answer "unknown" and fall through. It is
handled first, because a host that will not serve the file declaring its policy, and will not
serve the product either, is the maximal case of the incoherence this indicator names.

Absence of robots.txt is `fail`, and that is not a new decision: it is the one already written
onto A4's `MeasurementSpec` by `2026-09-06_scan_targets` §2 — *"a host that has declared
nothing has not declared permission"*. A12 asks whether the declared and enforced layers
cohere; with nothing declared there is no declaration to cohere with, and reading absence as
`pass` would score silence as compliance.

`not_applicable` is reserved for a robots.txt that DISALLOWS us: that is A4's measurement, and
a host obeyed is not a host in conflict with itself.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A12-v1", "A12"

#: This rule's Findings never enter a numerator or a denominator. A12 is a `candidate`
#: indicator and the framework has not adopted it (DD-054); the reporting layer reads this.
CANDIDATE = True


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    refused = tuple((params.get("manners") or {}).get("unobservable_statuses") or ())
    robots = next((o for o in obs if "present" in (o.parsed or {})), None)
    probe = next((o for o in obs if (o.parsed or {}).get("probe") == "a12_target"), None)
    if robots is None or probe is None:
        return c.make(RULE_ID, LEG, obs, "error",
                      "the robots/probe pair for this host was not collected", params)

    r = robots.parsed or {}
    robots_status = r.get("robots_status")
    probe_status = (probe.response or {}).get("status")

    # 1. The host refuses the file that would declare its policy.
    if robots_status in refused:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the host answered HTTP {robots_status} to /robots.txt itself for "
                      f"{r.get('self_ua') or params['manners']['user_agent']}: the declared "
                      f"layer is not observable and the enforced layer refuses", params)
    # 2. Neither observed at all — that is ours, not the product's (§3 of the scaffold task).
    if robots_status is None and probe_status is None:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"neither /robots.txt nor the probe path could be observed: "
                      f"{robots.error_class or probe.error_class}", params)
    # 3. Nothing declared. Same reading as A4-v1's recorded `decision`.
    if not r.get("present"):
        why = ("robots.txt is served with a content type that cannot be robots.txt"
               if r.get("wrong_content_type") else
               f"no robots.txt is served (HTTP {robots_status})")
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{why}, so nothing is DECLARED for this client and there is no "
                      f"declaration for the enforced layer to cohere with", params)
    # 4. Declared and obeyed. A4's measurement, not a coherence failure.
    if r.get("self_ua_allowed") is False:
        return c.make(RULE_ID, LEG, obs, "not_applicable",
                      f"robots.txt disallows {r.get('self_ua')} for {r.get('probe_url')}; "
                      f"a host obeyed is not a host in conflict with itself (that reading is "
                      f"A4's)", params)
    # 5. The incoherence itself: permitted in the file, refused at the edge.
    if probe_status in refused:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt PERMITS {r.get('self_ua')} for {probe.target_url} and the "
                      f"host answered HTTP {probe_status} to that same path: the declared and "
                      f"enforced layers disagree", params)
    if probe_status is None:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt permits the path but it could not be fetched: "
                      f"{probe.error_class}", params)
    if probe_status >= 500:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt permits the path and the host answered HTTP "
                      f"{probe_status}; a server error is not a refusal", params)
    # 6. Coherent. A 404 counts: the path is not there, and we were not turned away.
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"robots.txt permits {r.get('self_ua')} for {probe.target_url} and the host "
                  f"served it (HTTP {probe_status}): the declared and enforced layers agree",
                  params)
