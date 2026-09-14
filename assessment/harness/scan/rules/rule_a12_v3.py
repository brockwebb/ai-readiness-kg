"""A12 v3 — access policy coherence, with a reason that describes what the host DID.
**CANDIDATE (DD-054).**

`cc_tasks/2026-09-13_rule_a12_v3.md` decision 1, from `cc_tasks/2026-09-13_self_row_RESULT.md`
§6: the instrument, applied to itself, found a false sentence under a true verdict.

**What v2 got wrong.** Its "nothing is declared" branch asks `wrong_content_type` BEFORE
`robots_status`, and `collectors/robots.py` sets `wrong_content_type` from the content type of
whatever came back — including the HTML error page a host returns with HTTP 404. So on any host
whose `/robots.txt` 404s with an HTML body, v2 says *"robots.txt is served with a content type
that cannot be robots.txt"* about a file that was never served. The verdict is right — nothing
is declared either way — and the sentence is false. One published Tier A Finding carries it
(`host:www.federalreserve.gov`, cycle 4 re-judged) and so does this publication's own row.

**What v3 changes and only what it changes.** The status is examined first: a response that is
not a 2xx did not serve a robots.txt, whatever its content type, and the sentence for that is
the one `RULE-A4-v1` already says on identical evidence — read from `_common.NO_ROBOTS_SERVED`
so the two cannot drift. The wrong-content-type branch keeps its own sentence and now fires only
on a 2xx, which is the case it was written for: the soft-404 host that answers HTTP 200 with an
HTML shell. A 2xx that is neither gets the third sentence rather than one of the other two.

Every branch's VERDICT is v2's. This is a generation that changes sentences, not judgements, and
the re-judgement's gate is zero verdict moves.

`RULE-A12-v2` is unchanged and stays in `REGISTRY`, bound to the cycles it judged.
`MEASURES = "host"` is v2's declaration and is v3's for v2's reason: A12's subject IS the
refusal, so a 403 is its evidence rather than an absence of it.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A12-v3", "A12"

#: This rule's Findings never enter a numerator or a denominator (DD-054).
CANDIDATE = True

#: **What this rule measures.** `host` means its subject is the host's own behaviour, so a
#: refusal is evidence rather than an absence of it. See `rule_a12_v2`'s docstring.
MEASURES = "host"


def _answered(o) -> bool:
    """A response arrived, whatever it said. The A12 question is about what the host DID."""
    return isinstance((getattr(o, "response", None) or {}).get("status"), int)


def _served(status) -> bool:
    """The host actually served the file: a 2xx. Not `status < 400` — a 3xx that was never
    followed to a body is not a robots.txt either, and the collector records the final status
    it got."""
    return isinstance(status, int) and 200 <= status < 300


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

    # 0. NEITHER answered.
    if not _answered(robots) and not _answered(probe):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"neither /robots.txt nor the probe path returned a response: "
                      f"{robots.error_class or probe.error_class}. A12 reads what the host "
                      f"DID; a host that did nothing observable did not refuse us either",
                      params)
    # 1. The host refuses the file that would declare its policy.
    if robots_status in refused:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the host answered HTTP {robots_status} to /robots.txt itself for "
                      f"{r.get('self_ua') or params['manners']['user_agent']}: the declared "
                      f"layer is not observable and the enforced layer refuses", params)
    # 2. Nothing declared — and WHY is decided by the status first (decision 1). A file that
    #    was not served cannot have been served with the wrong content type.
    if not r.get("present"):
        # The two 2xx sentences are v2's, VERBATIM. v3 is sent to change the order of the
        # questions and the sentence for a file that was not served; a rule version that also
        # improved the wording of a branch it was not sent to touch would make its own
        # re-judgement unreadable — every changed reason would have to be sorted into "the
        # correction" and "while I was here".
        if not _served(robots_status):
            why = f"{c.NO_ROBOTS_SERVED} (HTTP {robots_status})"
        elif r.get("wrong_content_type"):
            why = "robots.txt is served with a content type that cannot be robots.txt"
        else:
            why = f"no robots.txt is served (HTTP {robots_status})"
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
