"""A10 — application/data-tool machine surface: no soft-404, content before JS."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A10-v1", "A10"


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
    st_invalid = (invalid.response or {}).get("status")
    if st_invalid == 200:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"soft-404: {invalid.target_url} returns HTTP 200 for a route that "
                      f"should not exist", params)
    st_valid = (valid.response or {}).get("status")
    if st_valid and st_valid >= 400:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"the product deep link itself returns HTTP {st_valid}", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"deep link HTTP {st_valid}; invalid route correctly HTTP {st_invalid}; "
                  f"{(valid.parsed or {}).get('pre_js_chars')} characters present before JS",
                  params)
