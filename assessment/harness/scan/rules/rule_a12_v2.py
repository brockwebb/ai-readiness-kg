"""A12 v2 — access policy coherence, reading the refusal ON PURPOSE. **CANDIDATE (DD-054).**

`cc_tasks/2026-09-10_harness_v5_blind.md` decision 3.

Harness-v5 makes `robots_disallowed` BLIND and states the invariant that no verdict about a
product may rest on evidence nobody collected. A12 sits on the other side of that line and has
always sat there: **its subject IS the refusal.** "An identified, robots-compliant client that
robots.txt permits is served" cannot be measured without treating a 403 as data. A rule that
returned `error` whenever the host refused us would return `error` in exactly the case the
indicator exists to name, and the three hosts that refuse this scanner would vanish from the one
measurement that is about them.

So the distinction this rule draws is **a response arrived** versus **no response arrived** —
not blind versus observed, which is the product question. HTTP 403 to `/robots.txt` is an
observation of enforcement and yields a verdict. A DNS failure, a timeout or a reset is no
observation of anything and yields `error`.

`MEASURES = "host"` is how that is said mechanically rather than as an exemption in a test
(decision 3: "the generalized invariant check then has no exemption list"). The invariant is
about verdicts on a PRODUCT; a rule declares its subject and the check reads the declaration.
Any future host-level rule declares the same thing and needs no edit anywhere else.

`RULE-A12-v1` is unchanged and stays in `REGISTRY`, bound to the four cycles it judged. The
branch logic here is v1's, and only the two `error` conditions move: v1 asked "is the status
None"; v2 asks "did a response arrive", which is the same question stated so it cannot be
confused with the product one.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A12-v2", "A12"

#: This rule's Findings never enter a numerator or a denominator (DD-054).
CANDIDATE = True

#: **What this rule measures.** `host` means its subject is the host's own behaviour, so a
#: refusal is evidence rather than an absence of it. Rules that do not declare this measure a
#: PRODUCT, and the harness-v5 invariant applies to them.
MEASURES = "host"


def _answered(o) -> bool:
    """A response arrived, whatever it said. The A12 question is about what the host DID."""
    return isinstance((getattr(o, "response", None) or {}).get("status"), int)


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

    # 0. NEITHER answered. v1 asked this third, keyed on `is None`; asking it first and keying
    #    on "did a response arrive" is the whole of what v2 changes. No response is no
    #    observation of enforcement, and the coherence question has no evidence at all.
    if not _answered(robots) and not _answered(probe):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"neither /robots.txt nor the probe path returned a response: "
                      f"{robots.error_class or probe.error_class}. A12 reads what the host "
                      f"DID; a host that did nothing observable did not refuse us either",
                      params)
    # 1. The host refuses the file that would declare its policy. The maximal incoherence, and
    #    the branch that must survive harness-v5: this 403 IS the measurement.
    if robots_status in refused:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the host answered HTTP {robots_status} to /robots.txt itself for "
                      f"{r.get('self_ua') or params['manners']['user_agent']}: the declared "
                      f"layer is not observable and the enforced layer refuses", params)
    # 2. Nothing declared. Same reading as A4-v1's recorded `decision`.
    if not r.get("present"):
        why = ("robots.txt is served with a content type that cannot be robots.txt"
               if r.get("wrong_content_type") else
               f"no robots.txt is served (HTTP {robots_status})")
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{why}, so nothing is DECLARED for this client and there is no "
                      f"declaration for the enforced layer to cohere with", params)
    # 3. Declared and obeyed. A4's measurement, not a coherence failure.
    if r.get("self_ua_allowed") is False:
        return c.make(RULE_ID, LEG, obs, "not_applicable",
                      f"robots.txt disallows {r.get('self_ua')} for {r.get('probe_url')}; "
                      f"a host obeyed is not a host in conflict with itself (that reading is "
                      f"A4's)", params)
    # 4. The incoherence itself: permitted in the file, refused at the edge.
    if probe_status in refused:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"robots.txt PERMITS {r.get('self_ua')} for {probe.target_url} and the "
                      f"host answered HTTP {probe_status} to that same path: the declared and "
                      f"enforced layers disagree", params)
    if not _answered(probe):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt permits the path and no response came back: "
                      f"{probe.error_class}", params)
    if probe_status >= 500:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"robots.txt permits the path and the host answered HTTP "
                      f"{probe_status}; a server error is not a refusal", params)
    # 5. Coherent. A 404 counts: the path is not there, and we were not turned away.
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"robots.txt permits {r.get('self_ua')} for {probe.target_url} and the host "
                  f"served it (HTTP {probe_status}): the declared and enforced layers agree",
                  params)
