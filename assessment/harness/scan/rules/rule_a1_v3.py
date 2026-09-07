"""A1 v3 — machine-readable formats, judged from the SHARED per-surface link probe.

`v2` is byte-identical in what it decides; the only change is where the evidence comes from.
A1 and A3 each collected the product page and HEADed the same 25 links independently — 559
duplicate requests against public federal hosts in the 2026-09-07 cycle, the largest single
share of its 46-minute wall time, and no additional evidence for either. The observations are
now collected once under the `link_probe` leg (`params.link_probe.shared_leg`) and this rule
declares that it reads them.

Prior art for the discipline rather than the mechanism: RFC 9309 governs what a crawler may
fetch and says nothing that licenses fetching the same object twice in one pass. One probe per
object per cycle is a manners rule the instrument owes the hosts it measures.

`v2` is untouched and stays in `REGISTRY`: every Finding recorded under it re-derives under it.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A1-v3", "A1"

#: Legs whose observations this rule reads IN ADDITION to its own. Its own leg collects nothing
#: (`runner.collect_leg`), so in practice this IS its evidence. Read by `run.py` when it builds
#: a judge group and by `rederive.py` when it rebuilds one from stored observations — one
#: declaration, both readers, so a re-derivation cannot group differently from the cycle.
CONSUMES = ("link_probe",)



def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in (LEG,) + CONSUMES]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    p = params["a1_formats"]
    struct, pdf, unprobed = [], [], 0
    for o in obs:
        parsed = o.parsed or {}
        ct = (parsed.get("content_type") or "")
        ext = "." + (parsed.get("extension") or "").lstrip(".")
        st = (o.response or {}).get("status")
        # A probed link that does not resolve is not a format the product offers.
        if parsed.get("probe") == "link" and not (st and st < 400):
            continue
        if ct in p["structured_content_types"] or ext in p["structured_extensions"]:
            struct.append((o.target_url, ct or ext))
        if ct in p["pdf_content_types"] or ext == ".pdf":
            pdf.append((o.target_url, ct or ext))
        # The page's own links that were never HEADed: counted, never credited. v1 credited
        # them on the suffix, which is the deviation this version exists to close.
        unprobed += len(parsed.get("links") or [])
    if struct:
        url, how = struct[0]
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"structured data SERVED at {url} ({how}); classified on the response, "
                      f"not on the href", params)
    if pdf:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"only PDF served; first: {pdf[0][0]}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  f"no probed link serves a structured content type "
                  f"({len([o for o in obs if (o.parsed or {}).get('probe') == 'link'])} links "
                  f"HEADed)", params)
