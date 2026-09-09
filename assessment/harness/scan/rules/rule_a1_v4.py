"""A1 v4 — a link nobody observed is not a format the product fails to offer.

`cc_tasks/2026-09-08_scan_run_3.md` §1.2, closing the gap `RULE-A10-v3` left open one leg over
and that `cc_tasks/2026-09-08_scan_harness_v4_RESULT.md` §7.1 named rather than fixed.

`v3` filters link observations through `_common.served()`, which is right — a blind probe is
not a served content type — and then, if none survives, returns **fail**: *"no probed link
serves a structured content type"*. A product page that WAS served while every one of its 25
link HEADs was reset is scored as offering no structured data. That is the harness-v4 defect
pointed the other way: `_common.only_errors` does not catch it, because the page observation is
real.

**What v4 decides differently, and only this.** A link probe whose class is blind is
UNOBSERVED for that link, not absent. If every link on the surface is blind the leg is `error`.
If some are, the verdict is computed over the links that WERE observed and the blind count
rides on the Finding, so a reader can see how much of the page the rule could actually see.
Where nothing is blind, `v4` returns exactly what `v3` returned, reason string included.

`v3` is untouched and stays in `REGISTRY`.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A1-v4", "A1"

#: The shared per-surface link probe (`params.link_probe.shared_leg`), as `v3`.
CONSUMES = ("link_probe",)


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in (LEG,) + CONSUMES]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    links = [o for o in obs if (o.parsed or {}).get("probe") == "link"]
    # `off_host` is a scope boundary, not a failed observation: the scanner declined to look
    # because the URL is outside the surface being measured (`errors.CLASSES`), so it is
    # neither blind nor a link this product offers.
    on_scope = [o for o in links if not (o.parsed or {}).get("off_host")]
    blind = [o for o in on_scope if c.unobserved(o, params)]
    seen = [o for o in on_scope if o not in blind]
    if on_scope and not seen:
        return c.make(RULE_ID, LEG, obs, "error",
                      f"all {len(blind)} link(s) on this surface were unobserved "
                      f"({blind[0].error_class}); the page was served but nothing it links to "
                      f"could be probed, so what it offers is unmeasured — not absent", params, blind_links=len(blind) or None)
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
    tail = (f" ({len(blind)} of {len(on_scope)} link(s) were unobserved and are excluded)"
            if blind else "")
    if struct:
        url, how = struct[0]
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"structured data SERVED at {url} ({how}); classified on the response, "
                      f"not on the href{tail}", params, blind_links=len(blind) or None)
    if pdf:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"only PDF served; first: {pdf[0][0]}{tail}", params, blind_links=len(blind) or None)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no probed link serves a structured content type ({len(seen)} link(s) "
                  f"observed){tail}", params, blind_links=len(blind) or None)
