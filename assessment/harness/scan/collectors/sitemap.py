"""Sitemap and discovery-surface observation for A5, via `ultimate-sitemap-parser`.

Reads the sitemap at the path robots.txt DECLARES where there is one, not only the fixed
`/sitemap.xml` — closing one of the four probe-depth gaps `assessment_protocol.md` §9 lists so
that nobody rediscovers them.
"""
from __future__ import annotations

import urllib.parse

from ..manners import error_class_for
from ..model import Observation, store_evidence

VERSION = "0.1.0"


def fetch(fetcher, leg: str, doc_id: str, product_url: str, params: dict,
          declared_sitemaps: list | None = None, spec_code: str | None = None) -> list:
    parts = urllib.parse.urlsplit(product_url)
    base = f"{parts.scheme}://{parts.netloc}"
    obs, seen = [], set()
    candidates = list(declared_sitemaps or []) + [
        urllib.parse.urljoin(base, p) for p in params["manners"]["always_fetch_paths"]
        if "sitemap" in p]
    for url in candidates + [urllib.parse.urljoin(base, p)
                             for p in params["a5_discovery"]["well_known_probes"]]:
        if url in seen:
            continue
        seen.add(url)
        try:
            r = fetcher.raw_get(url)
        except Exception as exc:
            obs.append(Observation.make(spec_code or leg, leg, doc_id, url, "sitemap", VERSION,
                                        params, {"method": "GET", "url": url},
                                        {"status": None, "headers": {}, "body_sha256": None,
                                         "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                         "error": f"{type(exc).__name__}: {exc}"},
                                        error_class="dns"))
            continue
        digest, path = store_evidence(r["body"])
        ctype = (r["headers"].get("content-type") or "").split(";")[0].strip().lower()
        kind = "sitemap" if "sitemap" in url else "discovery_file"
        # As in robots.py and dcat.py: an XML path answered with HTML is absence, not a parse
        # failure. A discovery file may legitimately be text/plain (llms.txt) or JSON.
        wrong_type = bool(ctype) and (
            ("xml" not in ctype) if kind == "sitemap" else ctype.startswith("text/html"))
        parsed = {"present": r["status"] < 400 and bool(r["body"].strip()) and not wrong_type,
                  "served_content_type": ctype, "wrong_content_type": wrong_type,
                  "kind": kind, "covers_product": None, "url_count": None}
        if parsed["present"] and parsed["kind"] == "sitemap":
            try:
                from usp.objects.page import SitemapPage  # noqa: F401
                from usp.tree import sitemap_tree_for_homepage  # noqa: F401
                # Parse the fetched bytes directly rather than re-crawling: the fetch above
                # already went through the manners layer, and usp's own tree walker would not.
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r["body"])
                locs = [e.text.strip() for e in root.iter()
                        if e.tag.endswith("}loc") or e.tag == "loc"]
                parsed["url_count"] = len(locs)
                parsed["covers_product"] = product_url in locs
                parsed["sample"] = locs[:params["a5_discovery"]["sample_urls_retained"]]
            except Exception as exc:
                parsed["parse_error"] = f"{type(exc).__name__}: {exc}"
        obs.append(Observation.make(spec_code or leg, leg, doc_id, url, "sitemap", VERSION,
                                    params, {"method": "GET", "url": url},
                                    {"status": r["status"], "headers": r["headers"],
                                     "body_sha256": digest, "body_path": path,
                                     "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                                    parsed=parsed, error_class=error_class_for(r["status"])))
    return obs
