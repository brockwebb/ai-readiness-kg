"""Which collector observes which leg, and how one cycle runs. **No judgements here.**"""
from __future__ import annotations

import urllib.parse

from .collectors import dcat, http, lighthouse, robots, sitemap, structured_data

#: leg -> the collector call that observes it. One place, so a leg cannot silently acquire a
#: second collector or lose the one it had.
def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
    from .manners import Fetcher
    f = fetcher or Fetcher(params)
    leg, doc_id, url = spec["leg"], target["doc_id"], target["url"]
    base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    join = lambda p: urllib.parse.urljoin(base, p)          # noqa: E731

    if leg == "A1":
        return http.fetch(f, leg, doc_id, url, params, parse_links=True)
    if leg == "A2":
        out = []
        for p in params["a9_m2m"]["probes"]:
            if "openapi" in p or "swagger" in p:
                out += http.fetch(f, leg, doc_id, join(p), params)
        return out
    if leg == "A3":
        return http.fetch(f, leg, doc_id, url, params, parse_links=True)
    if leg == "A4":
        return robots.fetch(f, leg, doc_id, url, params)
    if leg == "A5":
        r = robots.fetch(f, "A4", doc_id, url, params)
        declared = ((r[0].parsed or {}).get("sitemaps") or []) if r else []
        return sitemap.fetch(f, leg, doc_id, url, params, declared_sitemaps=declared)
    if leg == "A6":
        return structured_data.fetch(f, leg, doc_id, url, params)
    if leg == "A8":
        return structured_data.fetch(f, leg, doc_id, url, params)
    if leg == "A9":
        return [o for p in params["a9_m2m"]["probes"]
                for o in http.fetch(f, leg, doc_id, join(p), params)]
    if leg == "A10":
        return lighthouse.fetch(f, leg, doc_id, url, params)
    if leg == "A11-declared":
        return robots.fetch(f, leg, doc_id, url, params)
    if leg == "B3":
        obs = http.fetch(f, leg, doc_id, url, params, parse_links=True)
        for link in ((obs[0].parsed or {}).get("links") or []):
            if "methodolog" in (link.get("href", "") + link.get("text", "")).lower():
                return obs + http.fetch(f, leg, doc_id, link["href"], params)
        return obs
    if leg == "D1":
        return structured_data.fetch(f, leg, doc_id, url, params)
    if leg == "D4":
        return dcat.fetch_catalog(f, leg, doc_id, url, params)
    if leg == "F4":
        return [o for p in params["f4_changelog"]["paths"]
                for o in http.fetch(f, leg, doc_id, join(p), params)]
    if leg == "G1-D":
        obs = http.fetch(f, leg, doc_id, url, params)
        toks = params["g1d_uncertainty"]["field_tokens"]
        for o in obs:
            body_path = (o.response or {}).get("body_path")
            if not body_path:
                continue
            from .manners import repo_root
            try:
                text = (repo_root() / body_path).read_bytes().decode("utf-8", "replace").lower()
            except Exception:
                continue
            # Structured FIELD, not prose. Where the field lives depends on the surface, and
            # the first smoke run failed all 17 surfaces by looking only at `<th>`: a StatCan
            # CSV declares its standard errors in the header ROW and has no HTML at all.
            import re
            ct = ((o.parsed or {}).get("content_type") or "")
            if ct.startswith("text/html") or "<th" in text:
                field_text = " ".join(re.findall(r"<th[^>]*>(.*?)</th>", text, re.S))
            elif ct.startswith("text/csv") or ct.startswith("application/csv"):
                field_text = text.split("\n", 1)[0]
            elif "json" in ct:
                # A JSON API declares its fields as keys; the Census API returns a header row
                # as the first array element.
                field_text = text[:4000]
            else:
                field_text = text.split("\n", 1)[0]
            o.parsed = dict(o.parsed or {},
                            uncertainty_field_source=ct or "unknown",
                            uncertainty_tokens=[t for t in toks if t.lower() in field_text])
        return obs
    raise KeyError(f"no collector wired for leg {leg!r}")
