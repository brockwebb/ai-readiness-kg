"""A8 v4 — four states, not one boolean: resolved, observed non-resolution, blind, out of scope.

`cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md` decision 1, from the block in
`cc_tasks/2026-09-08_scan_run_3_RESULT.md` §1.

`collectors/v2clauses.follow_latest_pointer` dereferences with `fetcher.raw_head` and records
`resolved: False` for **four different things**: the host answered a non-resolving status; the
connection failed and nobody saw anything (`status: None`, a `note` naming the exception);
`robots.txt` disallows the path so nothing was fetched; and the scanner's own same-host policy
excluded it. `latest_pointer_resolves = any(resolved)` flattens all four, and `RULE-A8-v3` read
the flat boolean and returned **fail** — publishing "this product's latest-vintage pointer is
broken" on a probe nobody observed.

That is DD-052 §6 for the fourth time: `error` means the COLLECTOR could not observe, never
that the product failed. A10 was the first (harness-v4), A1 and A3 the second and third
(`..._scan_run_3.md` §1.2), and the fixture built for those caught this one.

**The four states, and the five verdicts.**

* `off_host` — the scanner declined to look because the URL is outside the surface being
  measured. **Scope, not blindness**: excluded from every count, exactly as
  `errors.CLASSES["off_host"]` is not blind.
* **blind** — `status is None` (the fetch raised) or `note == "robots_disallowed"` (nothing was
  fetched). Unobserved.
* **resolved** — a status in `a8_latest.resolves_statuses`.
* **observed non-resolution** — any other real status. This IS a measurement.

Verdicts: no pointers at all → `v3`'s wording, unchanged. Any resolved → `pass`. None resolved,
some observed non-resolution, zero blind → `fail`. Every non-excluded pointer blind → `error`.
**Mixed observed and blind → `error`**, because a pointer that might have resolved was not
looked at, so "none of them resolves" is not established. The blind and off-host counts ride on
the Finding as fields.

`v3` is untouched and stays in `REGISTRY`; cycles 1, 2 and 2-rj1 keep re-deriving under it.
"""
from __future__ import annotations

from . import _common as c

RULE_ID, LEG = "RULE-A8-v4", "A8"

#: A `note` that means the probe was never issued. `off_host` is handled separately because it
#: is scope rather than blindness.
_NOT_FETCHED = ("robots_disallowed",)


def classify(ptr: dict, params: dict) -> str:
    """`off_host` | `blind` | `resolved` | `unresolved` for one `pointers_tried` entry."""
    if ptr.get("off_host") or str(ptr.get("note") or "").startswith("off_host"):
        return "off_host"
    if str(ptr.get("note") or "") in _NOT_FETCHED:
        return "blind"
    status = ptr.get("status")
    if status is None:
        return "blind"
    return "resolved" if status in params["a8_latest"]["resolves_statuses"] else "unresolved"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["a8_freshness"]
    declared, header_seen = None, None
    tried, found = [], 0
    for o in obs:
        blind = c.unobserved_error(RULE_ID, LEG, obs, o, params,
                                   f"the product page {o.target_url}")
        if blind is not None:
            return blind
        keys = set((o.parsed or {}).get("keys") or [])
        hit = sorted(keys & set(p["markup_fields"]))
        if hit and declared is None:
            declared = hit[0]
        hdrs = {k.lower(): v for k, v in ((o.response or {}).get("headers") or {}).items()}
        if hdrs.get("last-modified"):
            header_seen = hdrs["last-modified"]
        latest = (o.parsed or {}).get("latest") or {}
        found += int(latest.get("pointers_found") or 0)
        tried += list(latest.get("pointers_tried") or [])

    if declared is None:
        if header_seen:
            return c.make(RULE_ID, LEG, obs, "fail",
                          f"only an HTTP Last-Modified header ({header_seen}) — a fact about "
                          f"the file, not a declared product vintage", params)
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no declared release or modification date on the surface", params)

    states = [(ptr, classify(ptr, params)) for ptr in tried]
    off_host = [t for t in states if t[1] == "off_host"]
    blind = [t for t in states if t[1] == "blind"]
    resolved = [t for t in states if t[1] == "resolved"]
    unresolved = [t for t in states if t[1] == "unresolved"]
    counts = {"blind_pointers": len(blind) or None}
    scope = (f"; {len(off_host)} candidate(s) excluded as off-host" if off_host else "")

    if not states:
        # `v3`'s branch and `v3`'s wording, unchanged: the surface offers nothing to follow.
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"markup declares the vintage via {declared}, but the surface offers no "
                      f"latest-vintage pointer on its own host, which the indicator also "
                      f"requires{scope}", params, **counts)
    if resolved:
        good = resolved[0][0]
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"markup declares the vintage via {declared} and the latest-vintage "
                      f"pointer resolves ({good['url']} -> HTTP {good.get('status')}, found by "
                      f"{good.get('how')}){scope}", params, **counts)
    if blind and not unresolved:
        first = blind[0][0]
        return c.make(RULE_ID, LEG, obs, "error",
                      f"markup declares the vintage via {declared}, and every one of the "
                      f"{len(blind)} latest-vintage pointer(s) was UNOBSERVED "
                      f"(first: {first['url']}, {first.get('note') or 'no response'}). Whether "
                      f"the pointer resolves is unmeasured, not broken{scope}", params, **counts)
    if blind and unresolved:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"markup declares the vintage via {declared}; of "
                      f"{len(blind) + len(unresolved)} latest-vintage pointer(s), "
                      f"{len(unresolved)} did not resolve and {len(blind)} were UNOBSERVED. A "
                      f"pointer that might have resolved was never looked at, so 'none "
                      f"resolves' is not established{scope}", params, **counts)
    first = unresolved[0][0]
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"markup declares the vintage via {declared}, but none of the "
                  f"{len(unresolved)} latest-vintage pointer(s) resolves "
                  f"(first: {first['url']} -> HTTP {first.get('status')}){scope}",
                  params, **counts)
