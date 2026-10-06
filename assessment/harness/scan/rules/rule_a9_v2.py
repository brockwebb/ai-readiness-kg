"""A9 v2 — M2M agent surface. FRONTIER (as_of 2026-01): reported, never in a core score.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 5, from the absence inventory
(`docs/research/2026-10-06_absence_rules_inventory.md` §2). spec:A9 names three entry points:
"OpenAPI at the documented base, /.well-known/mcp or an advertised MCP/A2A endpoint, /llms.txt".
`v1` probed the two fixed paths and three GUESSED OpenAPI paths, and failed "none of the N
probed machine-first paths is served" without ever reaching the documented base. That is
DN-012 d1's second trigger, with the same cause as A2's (audit C-14).

**What v2 decides differently.** The `pass` is v1's exactly: a non-HTML 2xx body at any probe.
Both `fail` branches are absence claims and are reached only when the body's declared
`api_base` was probed (`_scope.api_scope`). Otherwise the verdict is `error` naming what was not
searched. `RULE-A9-v1` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-A9-v2", "A9"

#: A `fail` says no machine-first entry point is served: an absence claim.
CLAIM = "absence"


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
        # A soft-404 host answers every probe with HTTP 200 and an HTML error page; an HTML
        # body disqualifies a MACHINE entry point whatever the status (v1's reading, kept).
        if ct.startswith("text/html"):
            html_shells.append(o.target_url)
            continue
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"machine-first entry point served at {o.target_url} "
                      f"({ct or 'unknown type'}, HTTP {st})", params)
    what = "whether the product serves a machine-first entry point"
    remainder, at_base = s.api_scope(obs, s.declared(obs))
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder)
    blind = [o for o in at_base if c.unobserved(o, params)]
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=at_base, blind=blind,
                              found=None, what=what)
    if scope is not None:
        return scope
    if html_shells:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(html_shells)} probed path(s) answer with HTML rather than a "
                      f"machine format; first: {html_shells[0]} (the declared API base was "
                      f"probed)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"none of the {len(obs)} probed machine-first paths is served, the declared "
                  f"API base included", params)
