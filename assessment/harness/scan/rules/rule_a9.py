"""A9 — M2M agent surface. FRONTIER (as_of 2026-01): reported, never in a core score."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A9-v1", "A9"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"no machine-first entry point could be probed: {obs[0].error_class}",
                      params)
    html_shells = []
    for o in obs:
        st = (o.response or {}).get("status")
        ct = ((o.parsed or {}).get("content_type") or "")
        if not (st and st < 400 and (o.response or {}).get("bytes")):
            continue
        # A soft-404 host answers every probe with HTTP 200 and an HTML error page. Counting
        # that as an agent surface is the failure the control fixture caught: a machine-first
        # entry point is a MACHINE format, so an HTML body disqualifies it whatever the status.
        if ct.startswith("text/html"):
            html_shells.append(o.target_url)
            continue
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"machine-first entry point served at {o.target_url} "
                      f"({ct or 'unknown type'}, HTTP {st})", params)
    if html_shells:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(html_shells)} probed path(s) answer with HTML rather than a "
                      f"machine format; first: {html_shells[0]}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"none of the {len(obs)} probed machine-first paths is served", params)
