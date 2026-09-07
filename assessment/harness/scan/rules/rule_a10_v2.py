"""A10 v2 — soft-404 detection that tests the SHELL, and content before JS that is measured.

`v1` deviated on both halves: it decided purely on status codes, never checking the HTML for
the "error shell" the signal names, and never used the `pre_js_chars` its own collector
records — that value was interpolated into the pass message and tested nowhere, so a deep link
whose raw HTML carries no page-specific content passed.

The pre-vs-post-JS DOM comparison the signal also names remains **unimplemented and recorded**:
no renderer is installed (`params.a10_soft404.renderer: none`), and this rule cannot invent
one. What it can do without a browser — and now does — is measure whether there is a document
present BEFORE any JavaScript runs, using DD-030's own extent features.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A10-v2", "A10"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be probed: {obs[0].error_class}", params)
    valid = next((o for o in obs if (o.parsed or {}).get("probe") == "valid"), None)
    invalid = next((o for o in obs if (o.parsed or {}).get("probe") == "invalid_route"), None)
    if invalid is None or valid is None:
        return c.make(RULE_ID, LEG, obs, "error",
                      "the valid/invalid route pair was not collected", params)
    p = params["a10_shell"]
    st_invalid = (invalid.response or {}).get("status")
    shell = (invalid.parsed or {}).get("error_shell_tokens") or []
    if st_invalid == 200:
        why = (f"and its body is an error shell ({', '.join(shell[:2])})" if shell
               else "with a body that does not even announce the error")
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"soft-404: {invalid.target_url} returns HTTP 200 for a route that "
                      f"should not exist, {why}", params)
    st_valid = (valid.response or {}).get("status")
    if st_valid and st_valid >= 400:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the product deep link itself returns HTTP {st_valid}", params)
    # The clause v1 never tested. A deep link that is a client-rendered shell has no product
    # on it until JavaScript runs, whatever its status code says.
    vis = ((valid.parsed or {}).get("extent") or {}).get("visible_chars")
    floor = int(p["min_pre_js_visible_chars"])
    if vis is not None and vis < floor:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the deep link returns HTTP {st_valid} but carries only {vis} visible "
                      f"characters before JavaScript runs (floor {floor}): the page is a "
                      f"client-rendered shell", params)
    renderer = (valid.parsed or {}).get("renderer")
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"deep link HTTP {st_valid}; invalid route correctly HTTP {st_invalid}; "
                  f"{vis} visible characters present before JS. The pre/post-JS DOM diff the "
                  f"signal also names was NOT run (renderer: {renderer})", params)
