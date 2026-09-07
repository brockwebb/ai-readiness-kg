"""Per-link HEAD: what each download link on a product page actually serves.

Task `cc_tasks/2026-09-06_scan_targets.md` §2, for the A1-v2 and A3-v2 clauses. Both specs say
"for each, HEAD and read Content-Type and file extension" and both `v1` rules classified on
the href suffix alone. The consequences are opposite and both wrong: a link to
`/api/dataset?format=csv` served as `text/csv` is structured data the harness could not see,
and a link ending `.csv` that 404s is structured data the harness credited without checking.

Reports `content_type`, `content_length`, `status` and the mechanical bulk/filtered
discriminators. It decides nothing — `a3_bulk`'s floors live in params and the verdict lives
in the rule.
"""
from __future__ import annotations

import urllib.parse

from ..manners import error_class_for
from ..model import Observation

VERSION = "0.1.0"


def _classify(url: str, ctype: str, length, params: dict) -> dict:
    b = params["a3_bulk"]
    path = urllib.parse.urlsplit(url).path.lower()
    query = urllib.parse.urlsplit(url).query
    is_archive = (any(path.endswith(e) for e in b["archive_extensions"])
                  or ctype in b["archive_content_types"])
    filtered = bool(query) and bool(b["query_string_is_filtered"])
    if length is None:
        big = bool(b["missing_length_is_bulk"])
    else:
        big = int(length) >= int(b["min_bulk_bytes"])
    return {"is_archive": is_archive, "has_query_string": bool(query),
            "filtered_by_query": filtered, "meets_size_floor": big,
            "content_length": None if length is None else int(length),
            # Bulk = a whole-product artefact: an archive, or a large unfiltered file.
            "is_bulk": bool(is_archive or (big and not filtered))}


def probe(fetcher, leg: str, doc_id: str, links: list, params: dict,
          spec_code: str | None = None, page_url: str | None = None) -> list:
    """One Observation per probed link, bounded by `link_probe.max_links_probed` and, when
    `same_host_only`, to the product's own host."""
    out = []
    seen = set()
    host = urllib.parse.urlsplit(page_url or "").netloc
    same_host_only = bool(params["link_probe"].get("same_host_only"))
    for link in links:
        href = (link.get("href") or "").split("#")[0]
        if not href.startswith("http") or href in seen:
            continue
        if same_host_only and host and urllib.parse.urlsplit(href).netloc != host:
            continue
        seen.add(href)
        if len(out) >= int(params["link_probe"]["max_links_probed"]):
            break
        if not fetcher.allowed(href):
            out.append(Observation.make(
                spec_code or leg, leg, doc_id, href, "links", VERSION, params,
                {"method": "HEAD", "url": href}, {"status": None, "headers": {},
                 "body_sha256": None, "body_path": None, "bytes": 0, "elapsed_ms": 0},
                parsed={"probe": "link", "anchor_text": link.get("text")},
                error_class="robots_disallowed"))
            continue
        try:
            r = fetcher.raw_head(href)
        except Exception as exc:
            out.append(Observation.make(
                spec_code or leg, leg, doc_id, href, "links", VERSION, params,
                {"method": "HEAD", "url": href},
                {"status": None, "headers": {}, "body_sha256": None, "body_path": None,
                 "bytes": 0, "elapsed_ms": 0, "error": f"{type(exc).__name__}: {exc}"},
                parsed={"probe": "link", "anchor_text": link.get("text")},
                error_class="timeout" if "timeout" in type(exc).__name__.lower() else "dns"))
            continue
        hdrs = {k.lower(): v for k, v in (r["headers"] or {}).items()}
        ctype = (hdrs.get("content-type") or "").split(";")[0].strip().lower()
        path = urllib.parse.urlsplit(r["final_url"]).path
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else None
        parsed = {"probe": "link", "anchor_text": link.get("text"),
                  "content_type": ctype, "extension": ext, "final_url": r["final_url"],
                  "method_used": r.get("method", "HEAD"),
                  **_classify(r["final_url"], ctype, hdrs.get("content-length"), params)}
        out.append(Observation.make(
            spec_code or leg, leg, doc_id, href, "links", VERSION, params,
            {"method": r.get("method", "HEAD"), "url": href},
            {"status": r["status"], "headers": r["headers"], "body_sha256": None,
             "body_path": None, "bytes": 0, "elapsed_ms": r["elapsed_ms"]},
            parsed=parsed, error_class=error_class_for(r["status"])))
    return out
