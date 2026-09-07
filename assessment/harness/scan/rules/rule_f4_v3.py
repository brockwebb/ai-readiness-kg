"""F4 v3 — a machine-readable changelog whose ENTRIES carry a revision class.

`v1` deviated: the signal says "test whether it is machine-readable **and carries a revision
class per entry**" and a 2xx status plus an allowed content type was sufficient. A JSON
changelog with no change-class field on any entry passed.

`f4_entries.min_entries_classified_fraction` is the threshold the signal implies but does not
state, and it is in params for that reason — a per-entry requirement read strictly would fail
a changelog with one unclassified historical entry, and read loosely would pass one with none.


**v3 (2026-09-07):** `v2` crashed a live cycle. Its guard was
`(o.response or {}).get("status", 999) < 400`, which looks safe and is not: `status` is always
PRESENT on an Observation and holds `None` whenever nothing was fetched — a robots disallow, a
DNS failure, a timeout — so `.get` returns `None` rather than the default and the comparison
raises `TypeError: '<' not supported between instances of 'NoneType' and 'int'`. A default
fires on a MISSING key, never on a present one holding `None`. It stopped the 2026-09-07 cycle
dead on `scan-eia-flagship-1-open-data`, whose links include paths `eia.gov/robots.txt`
disallows for this UA. Four `v2` modules carried the identical bug; the guard is now
`_common.served()`, named once rather than duplicated in four places. `v2` is untouched and
stays in `REGISTRY` — no Finding recorded under it is re-scored.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-F4-v3", "F4"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"no changelog path could be probed: {obs[0].error_class}", params)
    ok = params["f4_changelog"]["machine_readable_content_types"]
    floor = float(params["f4_entries"]["min_entries_classified_fraction"])
    unclassified = None
    for o in obs:
        st = (o.response or {}).get("status")
        ct = ((o.parsed or {}).get("content_type") or "")
        if not (st and st < 400 and ct in ok):
            continue
        e = (o.parsed or {}).get("changelog") or {}
        if e.get("parse_failed"):
            return c.make(RULE_ID, LEG, obs, "error",
                          f"a changelog is served at {o.target_url} ({ct}) but its body could "
                          f"not be parsed into entries", params)
        n, frac = e.get("entries", 0), e.get("classified_fraction", 0.0)
        if n and frac >= floor:
            return c.make(RULE_ID, LEG, obs, "pass",
                          f"machine-readable changelog at {o.target_url} ({ct}); "
                          f"{e.get('entries_classified')} of {n} entries carry a revision "
                          f"class", params)
        unclassified = unclassified or (o.target_url, ct, n, frac)
    if unclassified:
        url, ct, n, frac = unclassified
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a machine-readable changelog is served at {url} ({ct}) but only "
                      f"{frac:.0%} of its {n} entries carry a revision class (floor "
                      f"{floor:.0%}); the signal requires a class per entry", params)
    human = [o.target_url for o in obs if c.served(o)]
    if human:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a changelog page is served at {human[0]} but not in a "
                      f"machine-readable content type", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no changelog or release-notes endpoint served", params)
