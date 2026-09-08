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

from .. import manners
from ..errors import classify_exception, classify_status
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
    """One Observation per link: a HEAD for the ones on the product's own host, bounded by
    `link_probe.max_links_probed`, and a fetch-free record with `parsed.off_host: true` and
    `error_class: off_host` for the ones `manners.on_roster_host` excludes."""
    out = []
    seen = set()
    probed = 0
    for link in links:
        href = (link.get("href") or "").split("#")[0]
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        # The ONE same-host gate (`cc_tasks/2026-09-08_scan_harness_v4.md` §1.3). It used to be
        # an inline `continue` on a `link_probe` key read here and nowhere else, which left an
        # off-host link with NO record — so nothing could show whether the policy had been
        # applied — while the other collector that dereferences discovered URLs
        # (`v2clauses.follow_latest_pointer`) read no key at all and probed off-host freely.
        if not manners.on_roster_host(href, page_url or "", params):
            out.append(Observation.make(
                spec_code or leg, leg, doc_id, href, "links", VERSION, params,
                {"method": None, "url": href, "fetched": False},
                {"status": None, "headers": {}, "body_sha256": None, "body_path": None,
                 "bytes": 0, "elapsed_ms": 0},
                parsed={"probe": "link", "anchor_text": link.get("text"), "off_host": True,
                        "surface_host": urllib.parse.urlsplit(page_url or "").netloc},
                error_class="off_host"))
            continue
        # The cap bounds REQUESTS, so only a link that is actually fetched spends it. Counting
        # the off-host records against it would let a page full of outbound links shrink the
        # number of the product's own downloads the probe ever reaches.
        if probed >= int(params["link_probe"]["max_links_probed"]):
            break
        probed += 1
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
                error_class=classify_exception(exc)))
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
            parsed=parsed, error_class=classify_status(r["status"], params)))
    return out
