"""Per-link HEAD: what each download link on a product page actually serves.

Task `cc_tasks/2026-09-06_scan_targets.md` §2, for the A1-v2 and A3-v2 clauses. Both specs say
"for each, HEAD and read Content-Type and file extension" and both `v1` rules classified on
the href suffix alone. The consequences are opposite and both wrong: a link to
`/api/dataset?format=csv` served as `text/csv` is structured data the harness could not see,
and a link ending `.csv` that 404s is structured data the harness credited without checking.

Reports `content_type`, `content_length`, `status` and the mechanical bulk/filtered
discriminators. It decides nothing — `a3_bulk`'s floors live in params and the verdict lives
in the rule.

**The candidate set is every on-host link, ranked, with the remainder recorded** (DN-012 d2,
`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 2). Until 0.2.0 the probe HEADed the
first 25 on-host links in document order and `break`, which on federal pages is mostly
navigation, and the links after the 25th left no record: an absence verdict over 25 of 244
links could not see the other 219 (audit C-01). The ranking is the classic focused-crawler
move, ordering the frontier by a cheap relevance estimate before the budget is spent
(Chakrabarti, van den Berg & Dom 1999; Cho, Garcia-Molina & Page 1998). Here the estimate is
the href's extension and a token, both read from params.
"""
from __future__ import annotations

import urllib.parse

from .. import manners
from ..errors import classify_exception, classify_status
from ..model import Observation

#: 0.2.0: candidates ranked before the cap, and every on-host candidate past it recorded as
#: `unprobed_over_cap` (`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 2).
VERSION = "0.2.0"


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


def _dotted(params: dict, name: str):
    """`params["a3_bulk"]["archive_extensions"]` for `"a3_bulk.archive_extensions"`."""
    node = params
    for k in name.split("."):
        node = node[k]
    return node


def rank_key(href: str, text, params: dict) -> dict:
    """`{tier, matched}`: how data-like one candidate looks, from its href and anchor alone.
    **Pure.** DN-012 d2: tier 0 is a path ending in an archive or data extension, tier 1 a
    `link_probe.rank.tokens` token in the path or the anchor text, tier 2 everything else.
    Nothing is fetched to rank; ranking is what decides which candidates the bound fetches."""
    r = params["link_probe"]["rank"]
    path = urllib.parse.urlsplit(href).path.lower()
    for name in r["extension_lists"]:
        for ext in _dotted(params, name):
            if path.endswith(ext.lower()):
                return {"tier": 0, "matched": ext}
    anchor = str(text or "").lower()
    for tok in r["tokens"]:
        if tok in path or tok in anchor:
            return {"tier": 1, "matched": tok}
    return {"tier": 2, "matched": None}


def candidates(links: list, page_url: str, params: dict,
               admitted: frozenset = frozenset()) -> tuple:
    """`(on_host, off_host)`: the page's distinct http(s) links, split by the one same-host gate
    and the on-host side RANKED. **Pure** (`manners.on_roster_host` reads only its arguments).

    Each entry is `{href, text, doc_order}` and, on the on-host side, `rank` (1-based) and
    `rank_key`. `doc_order` is the position among the page's distinct links, so ties in a tier
    keep the agency's own order. One function for the collector and for `scan/reread.py`, so a
    stored cycle's candidate set is computed exactly as a new cycle's is.
    """
    from .. import manners
    on, off, seen = [], [], set()
    for link in links or []:
        href = (link.get("href") or "").split("#")[0]
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        entry = {"href": href, "text": link.get("text"), "doc_order": len(seen) - 1}
        if manners.on_roster_host(href, page_url or "", params, admitted):
            on.append({**entry, "rank_key": rank_key(href, link.get("text"), params)})
        else:
            off.append(entry)
    on.sort(key=lambda e: (e["rank_key"]["tier"], e["doc_order"]))
    for i, e in enumerate(on, 1):
        e["rank"] = i
    return on, off


def account(observations: list, links: list, page_url: str, params: dict,
            admitted: frozenset = frozenset()) -> dict:
    """The `link_candidates` block for one surface: on-host candidates, how many were probed,
    how many were not, and the cap. **Pure.** DN-012 d2: "Report per surface".

    PROBED means a link Observation exists for the candidate that is neither a scope record
    (`off_host`) nor `unprobed_over_cap`: the cap was spent on it, whatever came back. A stored
    cycle collected before this function existed recorded nothing past the cap and recorded a
    now-admitted declared host as `off_host`, so both read as unprobed here, which is what they
    were.
    """
    on, off = candidates(links, page_url, params, admitted)
    probed = {o.target_url for o in observations
              if (o.parsed or {}).get("probe") == "link"
              and o.error_class not in ("off_host", "unprobed_over_cap")}
    done = [e for e in on if e["href"] in probed]
    left = [e for e in on if e["href"] not in probed]
    return {"scheme": int(params["link_probe"]["rank"]["candidates_scheme"]),
            "on_host": len(on), "probed": len(done), "unprobed": len(left),
            "cap": int(params["link_probe"]["max_links_probed"]), "off_host": len(off),
            "admitted_hosts": sorted(admitted),
            "ranked_by": "tier (archive/data extension, then link_probe.rank.tokens), then "
                         "document order",
            "unprobed_first": [e["href"] for e in left[:int(params["reporting"]
                                                            ["validator_messages_retained"])]]}


def probe(fetcher, leg: str, doc_id: str, links: list, params: dict,
          spec_code: str | None = None, page_url: str | None = None,
          admitted: frozenset = frozenset()) -> list:
    """One Observation per distinct link. On-host candidates are ranked by data-likeness
    (`rank_key`) and the first `link_probe.max_links_probed` get a HEAD; every on-host
    candidate past the cap is RECORDED as `unprobed_over_cap` with its rank, and fetched never
    (DN-012 d2). The cap bounds requests; it no longer hides candidates. A link
    `manners.on_roster_host` excludes gets a fetch-free record with `parsed.off_host: true` and
    `error_class: off_host`, as before.

    `admitted` is the body's declared hosts for this leg (`declarations.admitted_hosts`).
    """
    out = []
    on, off = candidates(links, page_url or "", params, admitted)
    # The ONE same-host gate (`cc_tasks/2026-09-08_scan_harness_v4.md` §1.3). An off-host link
    # used to leave NO record, so nothing could show whether the policy had been applied.
    for e in off:
        href = e["href"]
        out.append(Observation.make(
            spec_code or leg, leg, doc_id, href, "links", VERSION, params,
            {"method": None, "url": href, "fetched": False},
            {"status": None, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 0},
            parsed={"probe": "link", "anchor_text": e["text"], "off_host": True,
                    "surface_host": urllib.parse.urlsplit(page_url or "").netloc},
            error_class="off_host"))
    # The cap bounds REQUESTS, so only a link that is actually fetched spends it. Counting the
    # off-host records against it would let a page full of outbound links shrink the number of
    # the product's own downloads the probe ever reaches.
    cap = int(params["link_probe"]["max_links_probed"])
    for e in on[cap:]:
        href = e["href"]
        out.append(Observation.make(
            spec_code or leg, leg, doc_id, href, "links", VERSION, params,
            {"method": None, "url": href, "fetched": False},
            {"status": None, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 0},
            parsed={"probe": "link", "anchor_text": e["text"], "rank": e["rank"],
                    "rank_key": e["rank_key"], "unprobed_over_cap": True},
            error_class="unprobed_over_cap"))
    for e in on[:cap]:
        href, ranked = e["href"], {"rank": e["rank"], "rank_key": e["rank_key"]}
        if not fetcher.allowed(href):
            out.append(Observation.make(
                spec_code or leg, leg, doc_id, href, "links", VERSION, params,
                {"method": "HEAD", "url": href}, {"status": None, "headers": {},
                 "body_sha256": None, "body_path": None, "bytes": 0, "elapsed_ms": 0},
                parsed={"probe": "link", "anchor_text": e["text"], **ranked},
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
                parsed={"probe": "link", "anchor_text": e["text"], **ranked},
                error_class=classify_exception(exc)))
            continue
        hdrs = {k.lower(): v for k, v in (r["headers"] or {}).items()}
        ctype = (hdrs.get("content-type") or "").split(";")[0].strip().lower()
        path = urllib.parse.urlsplit(r["final_url"]).path
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else None
        parsed = {"probe": "link", "anchor_text": e["text"],
                  "content_type": ctype, "extension": ext, "final_url": r["final_url"],
                  "method_used": r.get("method", "HEAD"), **ranked,
                  **_classify(r["final_url"], ctype, hdrs.get("content-length"), params)}
        out.append(Observation.make(
            spec_code or leg, leg, doc_id, href, "links", VERSION, params,
            {"method": r.get("method", "HEAD"), "url": href},
            {"status": r["status"], "headers": r["headers"], "body_sha256": None,
             "body_path": None, "bytes": 0, "elapsed_ms": r["elapsed_ms"]},
            parsed=parsed, error_class=classify_status(r["status"], params)))
    return out
