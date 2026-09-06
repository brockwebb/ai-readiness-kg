"""A10's soft-404 and pre-JS observation.

**The renderer half is NOT available in this environment and that is recorded, not faked.**
Lighthouse is a Node CLI and is not installed; `params.a10_soft404.renderer` is `none`. What
IS observable without a browser is most of A10's signal and all of the falsifiable part: a
deep link and a deliberately invalid route are requested, and their status codes and pre-JS
HTML are compared. A soft-404 is HTTP 200 on a route that should not exist — visible without
rendering anything.

The pre-vs-post-JS DOM comparison yields `error_class: collector_unavailable`, which a rule
reads as `error` (the collector could not observe) and never as `fail` (§3: `error` never
means the product failed).
"""
from __future__ import annotations

import shutil
import urllib.parse

from ..manners import error_class_for
from ..model import Observation, store_evidence

VERSION = "0.1.0"


def available() -> bool:
    return shutil.which("lighthouse") is not None


def fetch(fetcher, leg: str, doc_id: str, product_url: str, params: dict,
          spec_code: str | None = None) -> list:
    out = []
    invalid = product_url.rstrip("/") + params["a10_soft404"]["invalid_path_suffix"]
    for url, kind in ((product_url, "valid"), (invalid, "invalid_route")):
        try:
            r = fetcher.raw_get(url)
        except Exception as exc:
            out.append(Observation.make(spec_code or leg, leg, doc_id, url, "lighthouse",
                                        VERSION, params, {"method": "GET", "url": url},
                                        {"status": None, "headers": {}, "body_sha256": None,
                                         "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                         "error": f"{type(exc).__name__}: {exc}"},
                                        parsed={"probe": kind}, error_class="dns"))
            continue
        digest, path = store_evidence(r["body"])
        text = r["body"].decode("utf-8", "replace")
        out.append(Observation.make(
            spec_code or leg, leg, doc_id, url, "lighthouse", VERSION, params,
            {"method": "GET", "url": url},
            {"status": r["status"], "headers": r["headers"], "body_sha256": digest,
             "body_path": path, "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
            parsed={"probe": kind, "pre_js_chars": len(text),
                    "renderer": params["a10_soft404"]["renderer"],
                    "renderer_available": available()},
            error_class=None if kind == "invalid_route" else error_class_for(r["status"])))
    return out
