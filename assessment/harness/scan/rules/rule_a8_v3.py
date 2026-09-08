"""A8 v3 — a latest-vintage pointer must be ON THE PRODUCT'S HOST and must not be a mailing list.

`v2` credited any candidate that resolved. Two things it never asked, and one surface asked
both at once: on `scan-census-flagship-2-american-community-survey-acs` an anchor whose
retained text reads *"subscribe subscribe to govdelivery email"* was taken for a
latest-vintage pointer and dereferenced to `public.govdelivery.com`, HTTP 200,
`resolved: true` (`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.1). An email-signup page on a
third-party notification service is not the product's vintage pointer under any reading of the
indicator, and A8 would have credited it. It manufactured no verdict that cycle only because
A8 was 23 fail / 3 error with zero passes — luck, not design.

**Two exclusions, and they belong in different layers.**

* *Off-host* is a MANNERS and SCOPE rule, enforced in the collector
  (`manners.on_roster_host`), because it decides what may be FETCHED. This rule does not have
  to trust that: it re-derives the host comparison itself from the stored pointer URL and the
  observation's own `target_url`, which is a pure computation. So a Finding re-judged from
  evidence collected BEFORE the collector had the policy — every pointer on the log to
  2026-09-07b — is judged under the policy anyway.
* *Subscription language* is a JUDGEMENT about what counts as a vintage pointer, so it lives
  here, over `params.a8_latest.excluded_anchor_tokens`. The collector goes on recording every
  candidate it found; a collector that decided this would be deciding.

Everything else is `v2` verbatim: the declared-date clause, the Last-Modified discipline that
the control fixture caught `v1` passing on, and the reason strings. `v2` is untouched and stays
in `REGISTRY`.
"""
from __future__ import annotations

from . import _common as c

RULE_ID, LEG = "RULE-A8-v3", "A8"


def _anchor_of(ptr: dict) -> str:
    """The anchor text behind a pointer candidate, from whichever field the record has.

    `anchor_text` is recorded from this task onward. For the pointers already on the log the
    text survives inside `how` — `anchor text 'subscribe subscribe to govdelivery email'` — so
    reading both is what lets a stored cycle be re-judged without re-fetching. `href token`
    carries no anchor and contributes the empty string, which matches nothing.
    """
    return str(ptr.get("anchor_text") or ptr.get("how") or "").lower()


def _excluded(ptr: dict, surface_url: str, params: dict) -> str | None:
    """Why this candidate is not a latest-vintage pointer, or None if it is one."""
    p = params["a8_latest"]
    if ptr.get("off_host") or not _on_host(ptr.get("url") or "", surface_url, params):
        return "off-host"
    hit = next((t for t in p.get("excluded_anchor_tokens") or [] if t in _anchor_of(ptr)), None)
    return f"subscription anchor {hit!r}" if hit else None


def _on_host(url: str, surface_url: str, params: dict) -> bool:
    """The host comparison, computed here rather than imported.

    A rule reaches nothing but its arguments (`rules/__init__` docstring), and
    `tests/test_scan_harness.py::test_no_rule_reaches_the_network_a_clock_or_the_filesystem`
    bans the whole `urllib` PACKAGE from this directory rather than `urllib.request` alone —
    rightly, since a module that may reach the parser may reach the opener on the next edit.
    `_common.host_of` is the pure string comparator both sides go through;
    `manners.on_roster_host` is the same policy at the collector, where it decides what may be
    FETCHED. Same switch, read from the params the rule was handed.
    """
    if not ((params.get("probes") or {}).get(
            "same_host_only", (params.get("link_probe") or {}).get("same_host_only", True))):
        return True
    host = c.host_of(surface_url)
    return not host or c.host_of(url) == host


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"the surface could not be observed: {obs[0].error_class}", params)
    p = params["a8_freshness"]
    declared, header_seen = None, None
    counted, dropped, surface_url = [], [], None
    for o in obs:
        # The guard every generation-4-and-later rule owes each probe it scores on
        # (`_common.unobserved_error`): a `dateModified` read off a page nobody was served, or
        # a pointer list gathered from a body that never arrived, would be a verdict about the
        # scanner. `only_errors` above catches only the case where EVERY observation is blind.
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
        for ptr in latest.get("pointers_tried") or []:
            why = _excluded(ptr, o.target_url, params)
            (dropped if why else counted).append({**ptr, "excluded_because": why})
        if latest:
            surface_url = o.target_url
    if declared is None:
        if header_seen:
            return c.make(RULE_ID, LEG, obs, "fail",
                          f"only an HTTP Last-Modified header ({header_seen}) — a fact about "
                          f"the file, not a declared product vintage", params)
        return c.make(RULE_ID, LEG, obs, "fail",
                      "no declared release or modification date on the surface", params)
    if not counted:
        why = (f"; {len(dropped)} candidate(s) were not latest-vintage pointers "
               f"({', '.join(sorted({str(d['excluded_because']) for d in dropped}))})"
               if dropped else "")
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"markup declares the vintage via {declared}, but the surface offers no "
                      f"latest-vintage pointer on its own host, which the indicator also "
                      f"requires{why}", params)
    good = next((t for t in counted if t.get("resolved")), None)
    if good is None:
        first = counted[0]
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"markup declares the vintage via {declared}, but none of the "
                      f"{len(counted)} latest-vintage pointer(s) resolves "
                      f"(first: {first['url']} -> HTTP {first.get('status')})", params)
    return c.make(RULE_ID, LEG, obs, "pass",
                  f"markup declares the vintage via {declared} and the latest-vintage pointer "
                  f"resolves ({good['url']} -> HTTP {good['status']}, found by {good['how']}) "
                  f"on the product's own host ({c.host_of(surface_url)})", params)
