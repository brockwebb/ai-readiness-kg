"""Is the search an absence verdict stands on complete? What generation 14 shares. **Pure.**

`cc_tasks/2026-10-06_absence_verdicts_rules.md`, DN-012 d1: *an absence verdict is never
reached over a partial search.* A rule that would say `fail` on "nothing found" says `error`
instead, naming what was not searched, whenever

1. the candidate set was TRUNCATED: a cap left links unprobed (`link_candidates`), or the
   collector followed the first of several candidates;
2. the search never reached the place the indicator NAMES: the department inventory data.gov
   reads, the API's terms endpoint, "any changelog endpoint";
3. a documented location was DECLARED and not followed: an `api_base` nobody probed.

This is the general form of `_common.absence_verdict`, which already said it for one cause
(a BLIND candidate): blind is blind whether the cause is a refused fetch or a cap. Prior art is
the same: ISA 705 / AU-C 705's scope limitation, and the open-world assumption (negation as
failure is unsound over a set known to be incomplete).

Every function here returns the REMAINDER: a list of sentences, each naming one part of the
search that was not made. An empty list means the search was complete and the caller's `fail` is
a measurement. The rule writes its own `fail` sentences; `remainder_error` writes the `error`.
"""
from __future__ import annotations

from . import _common as c

#: The `declared` block scheme (`scan.declarations.SCHEME`) and the `link_candidates` scheme
#: (`params.link_probe.rank.candidates_scheme`) these functions understand. A rule may not import
#: `scan.declarations` (a rule reaches nothing but its arguments), so the number is restated here
#: and `tests/test_absence_verdicts_rules.py` holds the two equal.
DECLARED_SCHEME = 1
CANDIDATES_SCHEME = 1
#: Every `declared` scheme this module reads. Scheme 2 (`cc_tasks/2026-10-07_seed_known_locations_
#: and_split_discoverability.md` decision 5) is scheme 1 plus provenance fields (`seeded_from`,
#: `status`, `verified_at`, `searched`); every key a function here reads means what it meant, so a
#: generation-14 or -15 rule judges a scheme-2 block as it judges the same locations in scheme 1.
#: No stored Observation carries scheme 2 before this task, so no Finding re-derives differently.
DECLARED_SCHEMES = (DECLARED_SCHEME, 2)


def declared(observations: list) -> dict | None:
    """The body's `declared` block from the first Observation carrying one of this scheme, or
    `None` when none does: the Observations predate DN-012 d3."""
    for o in observations:
        d = (o.parsed or {}).get("declared") if isinstance(o.parsed, dict) else None
        if isinstance(d, dict) and d.get("scheme") in DECLARED_SCHEMES:
            return d
    return None


def _same(a: str, b: str) -> bool:
    """Two URLs name one resource for this purpose: equal but for case and a trailing slash.
    String work only, because a rule may not import `urllib` (`_common.host_of`)."""
    return str(a or "").rstrip("/").lower() == str(b or "").rstrip("/").lower()


def _unresolved(decl: dict) -> list:
    return [f"not declared ({u.get('role')}): {u.get('why')}" for u in decl.get("unresolved") or []]


def remainder_error(rule_id: str, leg: str, obs: list, params: dict, what: str,
                    remainder: list, **counts):
    """The `error` an absence verdict owes over an incomplete search, naming the remainder."""
    return c.make(rule_id, leg, obs, "error",
                  f"absence not established: {what}: {'; '.join(remainder)}. A `fail` is "
                  f"reached only over a complete search; what was not searched may hold what "
                  f"is being looked for (DN-012 d1)", params, **counts)


def link_scope(observations: list, params: dict) -> list:
    """The remainder of a link-probe candidate set (A1, A3): the on-host candidates the cap
    left unprobed, from the page's `link_candidates` block (DN-012 d2).

    A page whose links were never read (not HTML, not served) offers no candidate set and has
    no remainder; the rule's other branches judge it. A page whose links WERE read and that
    carries no block was collected before candidates were accounted, so how many went unprobed
    is not known, and that is itself the remainder.
    """
    page = next((o for o in observations
                 if o.leg == "link_probe" and isinstance(o.parsed, dict)
                 and "links" in o.parsed), None)
    if page is None:
        return []
    block = page.parsed.get("link_candidates")
    if not isinstance(block, dict) or block.get("scheme") != CANDIDATES_SCHEME:
        return ["the page's on-host candidates were not accounted (collected before DN-012 d2 "
                "recorded `link_candidates`), so how many went unprobed is unknown"]
    if not block.get("unprobed"):
        return []
    first = (block.get("unprobed_first") or [None])[0]
    return [f"{block['probed']} of {block['on_host']} on-host links probed, "
            f"{block['unprobed']} unprobed, cap {block['cap']}"
            + (f" (first unprobed by rank: {first})" if first else "")]


def link_search(observations: list) -> str:
    """The search a link-probe `fail` was reached over, in words, for its reason: how many
    on-host candidates there were, all of them probed. Called only when `link_scope` returned no
    remainder."""
    page = next((o for o in observations
                 if o.leg == "link_probe" and isinstance(o.parsed, dict)
                 and isinstance(o.parsed.get("link_candidates"), dict)), None)
    if page is None:
        return "the page's links were not read, so it offers no link candidates"
    n = page.parsed["link_candidates"].get("on_host", 0)
    return (f"all {n} on-host link(s) probed" if n
            else "the page as served carries no on-host link")


def api_scope(observations: list, decl: dict | None) -> tuple:
    """`(remainder, at_base)` for an API leg (A2, A9): whether the documented API base was
    declared and probed. `at_base` is the Observations that target the declared base or its
    description; spec:A2 says GET "the documented API base", and a guessed path is not it."""
    if decl is None:
        return (["the body's declared locations were not recorded on these Observations "
                 "(collected before DN-012 d3), so its documented API base is unknown; guessed "
                 "paths do not establish absence"], [])
    api = decl.get("api_base")
    if not api:
        return (["no documented API base declared for this body; guessed paths do not "
                 "establish absence"] + _unresolved(decl), [])
    targets = [u for u in (api.get("url"), api.get("description_url")) if u]
    at = [o for o in observations
          if any(_same(o.target_url, u) or str(o.target_url or "").lower().startswith(
              u.rstrip("/").lower() + "/") for u in targets)]
    if not at:
        return ([f"documented API base declared and not probed: {api.get('url')} (read from "
                 f"{(api.get('read_from') or {}).get('page')})"], [])
    return [], at


def terms_scope(observations: list, decl: dict | None) -> list:
    """The remainder of D1's third source, "the API's terms endpoint" (spec:D1)."""
    if decl is None:
        return ["the body's declared locations were not recorded on these Observations "
                "(collected before DN-012 d3), so the API's terms endpoint spec:D1 names is "
                "unknown"]
    api = decl.get("api_base")
    if not api:
        return (["no documented API base is declared for this body, so the API's terms "
                 "endpoint spec:D1 names cannot be located"] + _unresolved(decl))
    terms = api.get("terms_url")
    if not terms:
        return [f"the API's terms endpoint spec:D1 names is not declared for the documented "
                f"API base {api.get('url')}"]
    if not any(_same(o.target_url, terms) for o in observations):
        return [f"the declared API terms endpoint was not probed: {terms}"]
    return []


def located_scope(observations: list, entries: list, noun: str, params: dict) -> list:
    """The remainder of a list of declared locations (inventories, changelogs): each entry not
    observed, or observed only blind."""
    out = []
    for e in entries:
        hit = [o for o in observations if _same(o.target_url, e.get("url"))]
        page = (e.get("read_from") or {}).get("page")
        role = f"{e.get('role')}, " if e.get("role") else ""
        if not hit:
            out.append(f"declared {noun} not observed: {e.get('url')} ({role}read from {page})")
        elif all(c.unobserved(o, params) for o in hit):
            out.append(f"declared {noun} not observed ({hit[0].error_class}): {e.get('url')}")
    return out


def inventory_scope(observations: list, decl: dict | None, params: dict) -> list:
    """The remainder of D4's search (ind:D4: "data.gov/agency inventory"): every declared
    inventory not observed, and every inventory the body could not declare."""
    if decl is None:
        return ["the body's declared inventories were not recorded on these Observations "
                "(collected before DN-012 d3), so only this host's /data.json was read"]
    entries = decl.get("inventory_urls") or []
    out = located_scope(observations, entries, "inventory", params) + _unresolved(decl)
    if not entries and not decl.get("unresolved"):
        out.append("no inventory is declared for this body")
    return out


def changelog_scope(observations: list, decl: dict | None, params: dict) -> list:
    """The remainder of F4's search (spec:F4: "any changelog or release-notes endpoint")."""
    if decl is None:
        return ["the body's declared locations were not recorded on these Observations "
                "(collected before DN-012 d3)"]
    entries = decl.get("changelog_urls") or []
    if not entries:
        return ["no changelog or release-notes location is declared for this body, and the "
                "guessed paths do not establish that none is served"] + _unresolved(decl)
    return located_scope(observations, entries, "changelog", params)
