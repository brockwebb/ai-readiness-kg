"""E5 v2 — the controls fired, returned what they should, AND ran before any real host.

`v1` deviated: the signal's first sentence is "Both control fixtures are scanned before any
real host" and nothing in `judge` inspected ordering, so a cycle that scanned real hosts first
and its controls afterwards returned `pass`.

A pure rule cannot read a clock — but it can read TIMESTAMPS it is given. The cycle now passes
the earliest surface observation's `captured_at` alongside the control observations, and this
rule asserts every control precedes it. The ordering becomes falsifiable from stored evidence
instead of resting on the runner's control flow, which is the only way a Finding can carry it.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-E5-v2", "E5"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    fired, bad, earliest_surface = [], [], None
    for o in obs:
        p = o.parsed or {}
        fired.append(p.get("fixture"))
        bad += [f"{p.get('fixture')}:{u}" for u in (p.get("unexpected") or [])]
        ts = p.get("earliest_surface_captured_at")
        if ts and (earliest_surface is None or ts < earliest_surface):
            earliest_surface = ts
    expected_fixtures = sorted(params["e5_control"]["expected_verdicts"])
    if sorted(x for x in fired if x) != expected_fixtures:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a cycle with zero fired controls is INVALID: expected "
                      f"{expected_fixtures}, fired {sorted(x for x in fired if x)}", params)
    if bad:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"{len(bad)} control verdict(s) were not as expected: "
                      f"{', '.join(bad[:6])}", params)
    if params["e5_ordering"]["require_controls_before_surfaces"] and earliest_surface:
        late = sorted(o.captured_at for o in obs if o.captured_at > earliest_surface)
        if late:
            return c.make(RULE_ID, LEG, obs, "fail",
                          f"the controls did not all run before the first real host: "
                          f"{len(late)} control observation(s) are stamped after "
                          f"{earliest_surface} (first {late[0]}). A cycle whose canaries ran "
                          f"afterwards cannot license the surfaces it already scanned", params)
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"both control fixtures fired, every rule returned its expected verdict, "
                      f"and every control observation precedes the first real host "
                      f"({earliest_surface})", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"both control fixtures fired and every rule returned its expected verdict; "
                  f"ordering not asserted (no surface was scanned in this cycle)", params)
