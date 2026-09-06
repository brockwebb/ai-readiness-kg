"""DCAT / data.json catalog observation for A6's SHACL leg and D4, via `rdflib` + `pyshacl`.

For D4 the object is the Project Open Data `/data.json` catalog and whether the product is in
it; for A6 it is whether an extracted DCAT graph validates. Neither verdict is taken here.
"""
from __future__ import annotations

import json
import urllib.parse

from ..manners import error_class_for
from ..model import Observation, store_evidence

VERSION = "0.1.0"


def fetch_catalog(fetcher, leg: str, doc_id: str, product_url: str, params: dict,
                  spec_code: str | None = None) -> list:
    parts = urllib.parse.urlsplit(product_url)
    base = f"{parts.scheme}://{parts.netloc}"
    out = []
    for p in params["d4_catalog"]["paths"]:
        url = urllib.parse.urljoin(base, p)
        try:
            r = fetcher.raw_get(url)
        except Exception as exc:
            out.append(Observation.make(spec_code or leg, leg, doc_id, url, "dcat", VERSION,
                                        params, {"method": "GET", "url": url},
                                        {"status": None, "headers": {}, "body_sha256": None,
                                         "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                         "error": f"{type(exc).__name__}: {exc}"},
                                        error_class="dns"))
            continue
        digest, path = store_evidence(r["body"])
        ctype = (r["headers"].get("content-type") or "").split(";")[0].strip().lower()
        # Same rule as robots.py: a catalog path answered with HTML is a host without a
        # catalog, not a catalog we failed to parse.
        wrong_type = bool(ctype) and "json" not in ctype
        parsed = {"present": r["status"] < 400 and not wrong_type,
                  "served_content_type": ctype, "wrong_content_type": wrong_type}
        err = None
        if parsed["present"]:
            try:
                doc = json.loads(r["body"].decode("utf-8", "replace"))
                datasets = doc.get("dataset") if isinstance(doc, dict) else None
                datasets = datasets if isinstance(datasets, list) else []
                required = params["d4_catalog"]["required_dataset_fields"]
                parsed["dataset_count"] = len(datasets)
                parsed["complete_entries"] = sum(
                    1 for d in datasets if isinstance(d, dict) and all(f in d for f in required))
                parsed["contains_product"] = any(
                    isinstance(d, dict) and product_url in json.dumps(d) for d in datasets)
            except Exception as exc:
                err = "parse_error"
                parsed["error"] = f"{type(exc).__name__}: {exc}"
        out.append(Observation.make(spec_code or leg, leg, doc_id, url, "dcat", VERSION, params,
                                    {"method": "GET", "url": url},
                                    {"status": r["status"], "headers": r["headers"],
                                     "body_sha256": digest, "body_path": path,
                                     "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                                    parsed=parsed,
                                    error_class=err or error_class_for(r["status"])))
    return out
