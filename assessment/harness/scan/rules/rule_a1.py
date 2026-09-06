"""A1 — machine-readable formats: the product is available as structured data, not PDF-only."""
from __future__ import annotations
from . import _common as c

RULE_ID, LEG = "RULE-A1-v1", "A1"


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg == LEG]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error",
                      f"every fetch failed: {obs[0].error_class}", params)
    p = params["a1_formats"]
    seen_struct, seen_pdf = [], []
    for o in obs:
        parsed = o.parsed or {}
        ct = (parsed.get("content_type") or "")
        ext = "." + (parsed.get("extension") or "")
        if ct in p["structured_content_types"] or ext in p["structured_extensions"]:
            seen_struct.append(o.target_url)
        if ct in p["pdf_content_types"] or ext == ".pdf":
            seen_pdf.append(o.target_url)
        for link in (parsed.get("links") or []):
            href = link.get("href", "")
            if any(href.lower().endswith(e) for e in p["structured_extensions"]):
                seen_struct.append(href)
            if href.lower().endswith(".pdf"):
                seen_pdf.append(href)
    if seen_struct:
        return c.make(RULE_ID, LEG, obs, "pass",
                      f"structured data reachable: {seen_struct[0]}", params)
    if seen_pdf:
        return c.make(RULE_ID, LEG, obs, "fail",
                      f"only PDF found; first: {seen_pdf[0]}", params)
    return c.make(RULE_ID, LEG, obs, "fail",
                  "no structured-data link or content type on the product surface", params)
