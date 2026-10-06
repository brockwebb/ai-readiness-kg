"""A1 v5 — "no probed link serves structured data" is reached only when every link was probed.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 3, DN-012 d1, audit C-01. `v4` said
*"no probed link serves a structured content type (25 link(s) observed)"* on pages carrying 38
to 871 on-host links. `links.probe` HEADed the first 25 in document order, mostly navigation,
and the rest left no record. On `scan-census-flagship-2-american-community-survey-acs` that was
25 of 115, while this project's own `sources_per_check.json` cites JSON from the Census Data
API for that product.

**What v5 decides differently.** The `pass` is unchanged: structured data SERVED on a link that
was fetched is established by what was seen, and nothing unprobed can unfind it. Both `fail`
branches ("only PDF", "no structured link") are absence claims over the candidate set, so this
rule now declares `CLAIM = "absence"`. Each is reached only when the search was complete: every
on-host candidate probed (the page's `link_candidates`, `_scope.link_scope`) and none of the
probed ones blind. Otherwise the verdict is `error`, and the reason gives the count, for example
"absence not established: 25 of 115 on-host links probed, 90 unprobed, cap 25".

`v4` treated a blind link as excluded and judged over the rest. That is the generation-6 reading,
and generation 9 already retired it for A3 (`rule_a3_v6`). v5 applies the same reading to A1,
because A1's `fail` claims exactly what A3's does. `RULE-A1-v4` stays in `REGISTRY`, unedited.
"""
from __future__ import annotations
from . import _common as c
from . import _scope as s

RULE_ID, LEG = "RULE-A1-v5", "A1"

#: The shared per-surface link probe (`params.link_probe.shared_leg`), as v4.
CONSUMES = ("link_probe",)

#: A `fail` says no structured format is offered among the candidates: an absence claim.
CLAIM = "absence"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in (LEG,) + CONSUMES]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    links = [o for o in obs if (o.parsed or {}).get("probe") == "link"]
    # `off_host` is a scope boundary, not a failed observation (`errors.CLASSES`).
    on_scope = [o for o in links if not (o.parsed or {}).get("off_host")]
    blind = [o for o in on_scope if c.unobserved(o, params)]
    seen = [o for o in on_scope if o not in blind]
    if on_scope and not seen:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"all {len(blind)} link(s) on this surface were unobserved "
                      f"({blind[0].error_class}); the page was served but nothing it links to "
                      f"could be probed, so what it offers is unmeasured — not absent", params,
                      blind_links=len(blind) or None)
    p = params["a1_formats"]
    struct, pdf = [], []
    for o in obs:
        parsed = o.parsed or {}
        if parsed.get("probe") == "link" and (o in blind or parsed.get("off_host")):
            continue
        ct = (parsed.get("content_type") or "")
        ext = "." + (parsed.get("extension") or "").lstrip(".")
        st = (o.response or {}).get("status")
        if parsed.get("probe") == "link" and not (st and st < 400):
            continue
        if ct in p["structured_content_types"] or ext in p["structured_extensions"]:
            struct.append((o.target_url, ct or ext))
        if ct in p["pdf_content_types"] or ext == ".pdf":
            pdf.append((o.target_url, ct or ext))
    if struct:
        url, how = struct[0]
        tail = (f" ({len(blind)} of {len(on_scope)} link record(s) were unobserved and are "
                f"excluded)" if blind else "")
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"structured data SERVED at {url} ({how}); classified on the response, "
                      f"not on the href{tail}", params, blind_links=len(blind) or None)
    # Everything below is an absence claim, asked about once: first the candidates the cap left
    # unprobed, then a probed candidate that was blind (`_common.absence_verdict`, as A3).
    what = "whether the product page offers a structured data format"
    remainder = s.link_scope(obs, params)
    if remainder:
        return s.remainder_error(RULE_ID, LEG, obs, params, what, remainder,
                                 blind_links=len(blind) or None)
    probed_blind = [o for o in blind if o.error_class != "unprobed_over_cap"]
    scope = c.absence_verdict(RULE_ID, LEG, obs, params, candidates=on_scope,
                              blind=probed_blind, found=None, what=what,
                              blind_links=len(blind) or None)
    if scope is not None:
        return scope
    if pdf:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"only PDF served; first: {pdf[0][0]} ({s.link_search(obs)})", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no probed link serves a structured content type ({len(seen)} link(s) "
                  f"observed; {s.link_search(obs)})", params)
