"""F4 v5 — a changelog exists where it is recorded; a guessed path is discoverability's.

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1.
F4 is an existence leg: does the body publish a machine-readable changelog? `RULE-F4-v4` judged
over five guessed paths on the product host (`f4_changelog.paths`) and the body's declared
changelog locations together, and a `pass` could rest on a guess. Guessed paths are what a
machine tries when nobody told it where to look, which is the discoverability indicator's
question (`rule_a13.py`), not this one.

**What v5 decides differently, and only this.** It judges the Observations at RECORDED changelog
locations (`targets.yaml` `declared_locations` `changelog_urls`, read from the body's pages or
seeded; `_existence.recorded_only`). Its absence branches are reached as `fail` only when every
recorded changelog location was observed and every seed source was searched for the body's
changelog (`_existence.remainder`); otherwise `error`, naming what was not. The one `fail` that is
not an absence (a machine-readable changelog was read and too few entries carry a revision class)
and every reason fragment are v4's. `RULE-F4-v4` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _existence as ex
from . import _scope as s

RULE_ID, LEG = "RULE-F4-v5", "F4"

CLAIM = "absence"


def judge(observations: list, params: dict):
    every = [o for o in observations if o.leg == LEG]
    if not every:
        return c.empty(RULE_ID, LEG, params)
    decl = ex.declared(every)
    recorded = ex.recorded_only(every, decl, ("changelog",), params)
    # The evidence a verdict cites: the recorded locations' Observations when there are any. With
    # none, the verdict rests on the record and its search, and cites what the leg observed.
    obs = recorded or every
    if recorded and c.only_errors(recorded, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"no changelog path could be probed: {obs[0].error_class}", params)
    ok = params["f4_changelog"]["machine_readable_content_types"]
    floor = float(params["f4_entries"]["min_entries_classified_fraction"])
    unclassified = None
    for o in recorded:
        ct = ((o.parsed or {}).get("content_type") or "")
        if not (c.served(o) and not c.unobserved(o, params) and ct in ok):
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
    # The branches below say no machine-readable changelog exists.
    what = "whether the product serves a machine-readable changelog"
    remainder = ex.remainder(every, decl, "changelog", params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder)
    human = [o.target_url for o in recorded if c.served(o)]
    if human:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"a changelog page is served at {human[0]} but not in a "
                      f"machine-readable content type (every declared changelog location was "
                      f"read; {ex.search(decl, 'changelog', params)})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no changelog or release-notes endpoint served at a recorded location: "
                  f"{ex.search(decl, 'changelog', params)}", params)
