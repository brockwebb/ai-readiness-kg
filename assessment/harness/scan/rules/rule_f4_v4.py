"""F4 v4 — "no machine-readable changelog" is reached only where a changelog was declared.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 5, from the absence inventory
(`docs/research/2026-10-06_absence_rules_inventory.md` §2). spec:F4 says fetch "any changelog
or release-notes endpoint". The collector probes five guessed paths (`f4_changelog.paths`),
and `v3` concludes from them "no changelog or release-notes endpoint served", or "a changelog
page is served ... but not in a machine-readable content type". Both claim there is no
machine-readable changelog. A guessed path list never reaches "any" endpoint: DN-012 d1's
second trigger.

**What v4 decides differently.** The `pass` is v3's exactly. So is the one `fail` that is not
an absence: a machine-readable changelog was FOUND and too few of its entries carry a revision
class, which is a statement about the file that was read. The two absence branches are reached
only when the body declares its changelog locations (`changelog_urls`, `targets.yaml`
`declared_locations`) and every one was observed (`_scope.changelog_scope`). Otherwise the
verdict is `error` naming that none is declared. No body declares one yet. `RULE-F4-v3` stays
in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-F4-v4", "F4"

#: A `fail` says no machine-readable changelog is served: an absence claim (one branch excepted,
#: and it says why above).
CLAIM = "absence"


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
    # The two branches below say no machine-readable changelog exists.
    what = "whether the product serves a machine-readable changelog"
    remainder = s.changelog_scope(obs, s.declared(obs), params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what,
                                 remainder + [f"{len(obs)} guessed path(s) probed"])
    blind = [o for o in obs if c.unobserved(o, params)]
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=obs, blind=blind,
                              found=None, what=what)
    if scope is not None:
        return scope
    human = [o.target_url for o in obs if c.served(o)]
    if human:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a changelog page is served at {human[0]} but not in a "
                      f"machine-readable content type (every declared changelog location was "
                      f"read)", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no changelog or release-notes endpoint served, at any declared location or "
                  "guessed path", params)
