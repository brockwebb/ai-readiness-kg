"""robots.txt observation for A4 and A11-declared, via `protego` — Scrapy's parser, which
follows Google's own robots.txt grammar rather than a hand-rolled reading of RFC 9309.

Observes only: for each AI-crawler UA in `params.a4_crawlers.user_agents`, can the product
path be fetched. Whether that is a pass is the rule's business.
"""
from __future__ import annotations

import urllib.parse

from ..manners import error_class_for
from ..model import Observation, store_evidence

VERSION = "0.1.0"


def fetch(fetcher, leg: str, doc_id: str, product_url: str, params: dict,
          spec_code: str | None = None) -> list:
    parts = urllib.parse.urlsplit(product_url)
    url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        r = fetcher.raw_get(url)
    except Exception as exc:
        return [Observation.make(spec_code or leg, leg, doc_id, url, "robots", VERSION, params,
                                 {"method": "GET", "url": url},
                                 {"status": None, "headers": {}, "body_sha256": None,
                                  "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                  "error": f"{type(exc).__name__}: {exc}"},
                                 error_class="dns")]
    digest, path = store_evidence(r["body"])
    text = r["body"].decode("utf-8", "replace")
    ctype = (r["headers"].get("content-type") or "").split(";")[0].strip().lower()
    # A soft-404 host answers /robots.txt with HTTP 200 and an HTML error shell. Parsing that
    # as an empty (therefore permissive) ruleset is the misreading this instrument exists to
    # catch, so a content type that CANNOT be robots.txt is evidence of ABSENCE — not a parse
    # error, which would read as "we could not observe" when in fact we observed clearly.
    wrong_type = bool(ctype) and not ctype.startswith("text/plain")
    parsed = {"present": r["status"] < 400 and bool(text.strip()) and not wrong_type,
              "served_content_type": ctype, "wrong_content_type": wrong_type, "per_ua": {}}
    if parsed["present"]:
        try:
            from protego import Protego
            rp = Protego.parse(text)
            for ua in params["a4_crawlers"]["user_agents"]:
                parsed["per_ua"][ua] = bool(rp.can_fetch(product_url, ua))
            parsed["sitemaps"] = list(rp.sitemaps or [])
        except Exception as exc:
            return [Observation.make(spec_code or leg, leg, doc_id, url, "robots", VERSION,
                                     params, {"method": "GET", "url": url},
                                     {"status": r["status"], "headers": r["headers"],
                                      "body_sha256": digest, "body_path": path,
                                      "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                                     parsed={"present": True,
                                             "error": f"{type(exc).__name__}: {exc}"},
                                     error_class="parse_error")]
    return [Observation.make(spec_code or leg, leg, doc_id, url, "robots", VERSION, params,
                             {"method": "GET", "url": url},
                             {"status": r["status"], "headers": r["headers"],
                              "body_sha256": digest, "body_path": path,
                              "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                             parsed=parsed, error_class=error_class_for(r["status"]))]
