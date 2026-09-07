"""A1 v2 — machine-readable formats, classified on what each link SERVES.

`v1` deviated (rule review 2026-09-06): the spec says "extract every download link; for each,
HEAD and read Content-Type and file extension" and `v1` classified on the href suffix alone.
Both errors follow: `/api/dataset?format=csv` served as `text/csv` was invisible, and a dead
link ending `.csv` was credited without being checked. `collectors/links.py` now HEADs each
link and this rule reads the served type.
"""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A1-v2", "A1"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
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
