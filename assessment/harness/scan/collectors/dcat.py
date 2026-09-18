"""DCAT / data.json catalog observation for A6's SHACL leg and D4, via `rdflib` + `pyshacl`.

For D4 the object is the Project Open Data `/data.json` catalog and whether the product is in
it; for A6 it is whether an extracted DCAT graph validates. Neither verdict is taken here.
"""
from __future__ import annotations

import json
import urllib.parse

from ..errors import classify_exception, classify_status
from ..model import Observation, store_evidence

VERSION = "0.1.0"

#: The name of the membership test `product_records` applies, recorded beside its count so a
#: reader of an Observation knows which test produced it. The substring test that preceded it
#: stays on the record as `contains_product`, which `RULE-D4-v1`/`-v2` read.
MEMBERSHIP_TEST = "dcat-us-url-fields-v1"

def normalize_url(url, params: dict) -> str | None:
    """A URL in the form two equivalent URLs share, by RFC 3986 §6 and no further.

    §6.2.2.1: scheme and host are case-insensitive, so both are lowercased; nothing else is.
    §6.2.3 (scheme-based): an empty path is "/" and a scheme's default port is no port. That is
    the whole normalisation. `http` and `https` stay distinct (RFC 9110 §4.2.4 makes them
    different origins), a trailing slash on a non-empty path stays significant, and `www.` is
    not stripped: each would be a guess that two URLs name one dataset, which is what the
    record's author, not this instrument, gets to say.
    """
    if not isinstance(url, str) or not url.strip():
        return None
    parts = urllib.parse.urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if not scheme or not host:
        return None
    try:
        port = parts.port
    except ValueError:
        return None
    # The default ports are protocol constants, read from params like every number a
    # collector uses (`d4_catalog.default_ports`, with their RFC 9110 sections).
    default = params["d4_catalog"]["default_ports"].get(scheme)
    netloc = host if port in (None, default) else f"{host}:{port}"
    return urllib.parse.urlunsplit((scheme, netloc, parts.path or "/", parts.query,
                                    parts.fragment))


def _field_values(record: dict, field: str) -> list:
    """The string values of one `membership_fields` entry: `name` on the record, or
    `distribution.name` on each of its distributions."""
    head, _, tail = field.partition(".")
    if not tail:
        v = record.get(head)
        return [v] if isinstance(v, str) else []
    out = []
    for dist in record.get(head) or []:
        if isinstance(dist, dict) and isinstance(dist.get(tail), str):
            out.append(dist[tail])
    return out


def product_records(datasets, product_url: str, params: dict) -> list:
    """The catalog records that ARE the product: one of the record's own URL fields names it.

    `cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 4. The test this replaces
    was `product_url in json.dumps(record)` — a substring anywhere in the record — and
    DCAT-US v1.1 (corpus/kernel/dcat-us-1-1-schema.md, doc_id `dcat-us-1-1-schema`) says what
    a record's URLs mean. `landingPage`: "This field is not intended for an agency's homepage
    (e.g. www.agency.gov), but rather if a dataset has a human-friendly hub or landing page
    that users can be directed to for all resources tied to the dataset." The substring test
    made census.gov's home page the product of 1,635 of its 1,805 records
    (`cc_tasks/2026-09-18_dcat_field_rules_RESULT.md` §1), which is the reading the document
    rules out, and it matched a product URL inside any longer URL or free-text field.

    So a record is the product's when a field DCAT-US defines as a URL OF THE DATASET equals
    the product URL (`normalize_url` both sides): `params.d4_catalog.membership_fields`, each
    with its DCAT-US definition beside it there. Pure: no fetch, no clock.
    """
    target = normalize_url(product_url, params)
    if target is None:
        return []
    fields = params["d4_catalog"]["membership_fields"]
    return [d for d in datasets if isinstance(d, dict)
            and any(normalize_url(v, params) == target
                    for f in fields for v in _field_values(d, f))]


def membership_block(datasets, product_url: str, params: dict) -> dict:
    """The `membership` block `RULE-D4-v3` reads, from a catalog's `dataset` list. Pure.

    One function because two callers compute it: `fetch_catalog` at collection, and
    `scan/reread.py` when a re-judgement re-reads a catalog body stored before the block
    existed (`cc_tasks/2026-09-18_rejudge_seven_legs.md`). Two copies of "which records are
    the product's" would be two answers to it.
    """
    return {"test": MEMBERSHIP_TEST,
            "fields": list(params["d4_catalog"]["membership_fields"]),
            "records": len(product_records(datasets, product_url, params))}


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
                                        error_class=classify_exception(exc)))
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
                # The substring test `RULE-D4-v1`/`-v2` read, kept so every Observation carries
                # what those rules need; `membership` is the DCAT-US field test `RULE-D4-v3`
                # reads (`product_records`).
                parsed["contains_product"] = any(
                    isinstance(d, dict) and product_url in json.dumps(d) for d in datasets)
                parsed["membership"] = membership_block(datasets, product_url, params)
            except Exception as exc:
                err = "parse_error"
                parsed["error"] = f"{type(exc).__name__}: {exc}"
        out.append(Observation.make(spec_code or leg, leg, doc_id, url, "dcat", VERSION, params,
                                    {"method": "GET", "url": url},
                                    {"status": r["status"], "headers": r["headers"],
                                     "body_sha256": digest, "body_path": path,
                                     "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                                    parsed=parsed,
                                    error_class=err or classify_status(r["status"], params)))
    return out
