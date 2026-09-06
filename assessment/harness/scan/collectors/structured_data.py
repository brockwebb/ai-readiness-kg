"""Embedded structured markup for A6, A8 and D1, via `extruct` — JSON-LD, microdata, RDFa.

Extracts and reports; the rules decide whether what was found satisfies the indicator.
"""
from __future__ import annotations

from ..manners import error_class_for
from ..model import Observation, store_evidence

VERSION = "0.1.0"


def _walk(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            out.setdefault(k, []).append(v)
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


def fetch(fetcher, leg: str, doc_id: str, url: str, params: dict,
          spec_code: str | None = None) -> list:
    if not fetcher.allowed(url):
        return [Observation.make(spec_code or leg, leg, doc_id, url, "structured_data", VERSION,
                                 params, {"method": "GET", "url": url},
                                 {"status": None, "headers": {}, "body_sha256": None,
                                  "body_path": None, "bytes": 0, "elapsed_ms": 0},
                                 error_class="robots_disallowed")]
    try:
        r = fetcher.raw_get(url)
    except Exception as exc:
        return [Observation.make(spec_code or leg, leg, doc_id, url, "structured_data", VERSION,
                                 params, {"method": "GET", "url": url},
                                 {"status": None, "headers": {}, "body_sha256": None,
                                  "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                  "error": f"{type(exc).__name__}: {exc}"},
                                 error_class="dns")]
    digest, path = store_evidence(r["body"])
    ctype = (r["headers"].get("content-type") or "").split(";")[0].strip().lower()
    # `content_type` is what A6 reads to decide `not_applicable`: a CSV or JSON surface
    # carries no HTML and therefore no embedded markup, and scoring that as a FAILURE scores
    # the format rather than the product. The first smoke run returned `fail` on all 17
    # surfaces and zero `not_applicable` precisely because this key was never set here.
    parsed, err = {"syntaxes": {}, "types": [], "keys": [], "content_type": ctype}, None
    if ctype and not ctype.startswith("text/html"):
        return [Observation.make(spec_code or leg, leg, doc_id, url, "structured_data", VERSION,
                                 params, {"method": "GET", "url": url},
                                 {"status": r["status"], "headers": r["headers"],
                                  "body_sha256": digest, "body_path": path,
                                  "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                                 parsed=parsed, error_class=error_class_for(r["status"]))]
    try:
        import extruct
        data = extruct.extract(r["body"].decode("utf-8", "replace"), base_url=r["final_url"],
                               syntaxes=params["a6_markup"]["syntaxes"], uniform=True)
        for syn, items in data.items():
            parsed["syntaxes"][syn] = len(items or [])
        flat: dict = {}
        _walk(data, flat)
        parsed["types"] = sorted({str(t) for v in flat.get("@type", []) for t in
                                  (v if isinstance(v, list) else [v]) if isinstance(t, str)})
        parsed["keys"] = sorted(flat)[:200]
        parsed["raw"] = data
    except Exception as exc:
        err = "parse_error"
        parsed["error"] = f"{type(exc).__name__}: {exc}"
    return [Observation.make(spec_code or leg, leg, doc_id, url, "structured_data", VERSION,
                             params, {"method": "GET", "url": url},
                             {"status": r["status"], "headers": r["headers"],
                              "body_sha256": digest, "body_path": path,
                              "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                             parsed=parsed, error_class=err or error_class_for(r["status"]))]
