"""A10 v3 — an unobserved probe is never a pass.

`v2` decided the soft-404 half on one test — *is the invalid route HTTP 200?* — and read
anything else as a correct rejection. On `scan-eia-flagship-1-open-data` the invalid-route
probe never reached the host: `RemoteProtocolError: Server disconnected without sending a
response`, `error_class: connection_reset`, which `errors.CLASSES` marks **blind**. The rule
scored `pass` with the reason *"invalid route correctly HTTP None"*
(`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.2). The valid-route probe HAD been served, so
`_common.only_errors` — which asks the question of the whole surface — was false and never
fired.

DD-052 §6 established that `error` must never mean the product FAILED. This is the mirror, and
nothing enforced it: `error` must never mean the product PASSED. Both are the same rule —
a verdict from a probe nobody observed is a measurement of the scanner.

**What changed and only what changed.** `v3` consults `_common.unobserved_error` on each of the
two probes it scores on, in the order it reads them, and returns `error` naming the class when
either is blind. Every other branch is `v2` verbatim, down to the reason strings, so a
difference between a `v2` and a `v3` Finding on the same evidence is always the guard and never
a re-scoring of anything else. `v2` is untouched and stays in `REGISTRY`.

The pre-vs-post-JS DOM comparison the signal also names remains unimplemented and recorded:
no renderer is installed (`params.a10_soft404.renderer: none`).
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A10-v3", "A10"


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
    # The guard, on every probe this rule scores on, BEFORE any branch reads a status. The
    # invalid route first because that is the probe the false positive came through: its
    # absence is what `v2` read as a correct 404.
    blind = (c.unobserved_error(RULE_ID, LEG, obs, invalid, params,
                                f"the invalid-route probe {invalid.target_url}")
             or c.unobserved_error(RULE_ID, LEG, obs, valid, params,
                                   f"the product deep link {valid.target_url}"))
    if blind is not None:
        return blind
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
