"""Surface selection from the Enterprise Data Inventory. **Pure. No network.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §2 as REPLACED by `..._ADDENDUM-02.md`.

**The rule this file used to hold was thrown away, and the reason is worth keeping.** It
scanned an agency's home page for anchor SUBSTRINGS. Run over the sixteen-agency frame it
found 12 flagships where cycle 1's hand list had 26 for thirteen agencies, left 12 of 16
agencies with none at all, and matched `api` inside *"Capital Markets"* on the Federal
Reserve's staff page. A rule that finds fewer real surfaces than the list it replaces, and
finds some of those by accident, is not a sampling statement — it is noise with a provenance
trail. Its own output falsified it, which is the one thing a pre-registered rule is for.

**What replaces it is prior art, not a better scraper.** Every CFO Act department must publish
a machine-readable Enterprise Data Inventory at `/data.json` under the OPEN Government Data Act
(44 U.S.C. 3511, continuing OMB M-13-13), in DCAT-US. That inventory is the department's OWN
declaration of its datasets — `publisher`, `bureauCode`, `landingPage`, and typed
`distribution` entries that say which are APIs. It is uniform across the frame, it is
machine-parseable, and it is already the object of a framework indicator.

**Two things this module will not do.**

* It will not rank datasets. The inventory carries no field that ranks them, so a "top" product
  is a value judgment the source does not make. `shortlist` orders by `modified` and is offered
  to the operator; `select` never reads it. Flagships are DECLARED (cycle 1's target list is
  the operator's declaration) or they are `pending_operator_declaration`.
* It will not match a token inside a word. `word_match` is the only matcher here, every caller
  goes through it, and `tests/test_scan_frame.py` pins it against the "Capital Markets" case
  that killed the previous rule.
"""
from __future__ import annotations

import re
import urllib.parse

VERSION = "0.2.0"


def _clean(text: str) -> str:
    return " ".join(str(text or "").split())


def word_match(text: str, tokens: list) -> str | None:
    """The token that matches `text` on WORD BOUNDARIES, or None.

    The only matcher in this module, and the reason it exists is on the record: the rule this
    file replaced matched `api` inside "Capital Markets" and made a staff biography page an
    agency's machine entry point. Hyphens and slashes are word boundaries here — `data-access`
    and `/api/` are single tokens in a URL — so `\\b` over a string where separators have been
    normalised to spaces is the whole of it.
    """
    hay = re.sub(r"[^a-z0-9]+", " ", str(text or "").lower())
    for t in tokens:
        needle = re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()
        if needle and re.search(rf"\b{re.escape(needle)}\b", hay):
            return t
    return None


def registrable_domain(host: str) -> str:
    """`www.ers.usda.gov` -> `usda.gov`. The last two labels.

    Deliberately naive and deliberately NOT a public-suffix lookup: every host in this frame is
    a `.gov` second-level registration, so two labels is exact here, and a PSL dependency would
    be a library carried for a case the frame does not contain. It is used only to PROBE for an
    inventory, and a wrong guess yields a recorded null rather than a wrong host.
    """
    parts = [p for p in str(host or "").split(".") if p]
    return ".".join(parts[-2:]) if len(parts) >= 2 else str(host or "")


def edi_hosts(agency_host: str, params: dict) -> list:
    """The hosts to probe for this agency's inventory, in order, without duplicates."""
    cfg = params["frame"]["edi"]
    out = []
    if cfg.get("probe_agency_host") and agency_host:
        out.append(agency_host)
    if cfg.get("probe_registrable_domain") and agency_host:
        rd = registrable_domain(agency_host)
        if rd and rd not in out:
            out.append(rd)
    return out


# ------------------------------------------------------------------ DCAT-US reading

def datasets(catalog: dict) -> list:
    """The `dataset` array of a DCAT-US catalog, or []. Shape-tolerant: a host may serve
    something at `/data.json` that is not an inventory at all, and that is a measurement."""
    got = (catalog or {}).get("dataset")
    return [d for d in got if isinstance(d, dict)] if isinstance(got, list) else []


def _publisher_names(ds: dict) -> list:
    """Every publisher name on a dataset, including the `subOrganizationOf` chain — DCAT-US
    nests the bureau under the department, and the agency we are looking for is usually the
    innermost one."""
    out, node = [], ds.get("publisher")
    while isinstance(node, dict):
        if node.get("name"):
            out.append(_clean(node["name"]))
        node = node.get("subOrganizationOf")
    return out


def for_agency(cat_datasets: list, names: list, bureau_codes: list | None = None) -> dict:
    """The datasets an inventory attributes to THIS agency, and how each was matched.

    `publisher.name` first, `bureauCode` second, and which one matched is recorded — a filter
    that cannot say why it kept a row leaves a target nobody can check.
    """
    keep, how = [], {"publisher_name": 0, "bureau_code": 0}
    wanted = {n.lower() for n in names if n}
    codes = {str(c) for c in (bureau_codes or [])}
    for ds in cat_datasets:
        pubs = {p.lower() for p in _publisher_names(ds)}
        if pubs & wanted:
            keep.append({"dataset": ds, "matched_on": "publisher_name"})
            how["publisher_name"] += 1
            continue
        if codes and codes & {str(c) for c in (ds.get("bureauCode") or [])}:
            keep.append({"dataset": ds, "matched_on": "bureau_code"})
            how["bureau_code"] += 1
    return {"datasets": keep, "matched_by": how, "n": len(keep)}


def _api_distributions(ds: dict, params: dict) -> list:
    cfg = params["frame"]["edi"]
    out = []
    for dist in (ds.get("distribution") or []):
        if not isinstance(dist, dict):
            continue
        fmt = f"{dist.get('format') or ''} {dist.get('mediaType') or ''}"
        url = dist.get("accessURL") or dist.get("downloadURL") or ""
        hit = word_match(fmt, cfg["api_format_tokens"])
        why = f"format/mediaType {hit!r}" if hit else None
        if not why and url:
            hit = word_match(urllib.parse.urlsplit(url).path, cfg["api_path_tokens"])
            why = f"accessURL path {hit!r}" if hit else None
        if why and url:
            out.append({"url": url, "why": why})
    return out


def api_entry_point(agency_datasets: list, params: dict) -> dict:
    """The agency's machine entry point: the most frequent API-type distribution prefix.

    "Most frequent" is a count over the department's own declaration, not a judgement, and the
    count is recorded so a reader can see how thin or thick the evidence is. Ties break by
    count then lexically, so the rule is deterministic; a single-dataset agency and a
    hundred-dataset agency are both answered the same way.
    """
    from collections import Counter
    seen, examples = Counter(), {}
    for row in agency_datasets:
        for dist in _api_distributions(row["dataset"], params):
            u = urllib.parse.urlsplit(dist["url"])
            if not u.netloc:
                continue
            # host + first path segment: the prefix an API is published under.
            seg = (u.path.strip("/").split("/") or [""])[0]
            prefix = f"{u.scheme or 'https'}://{u.netloc}/{seg}".rstrip("/")
            seen[prefix] += 1
            examples.setdefault(prefix, dist)
    if not seen:
        return {"url": None, "marker": "no_api_distribution_declared_in_edi",
                "declared_distributions_scanned": sum(
                    len(r["dataset"].get("distribution") or []) for r in agency_datasets)}
    prefix, count = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return {"url": prefix, "count": count, "distinct_prefixes": len(seen),
            "example": examples[prefix],
            "selection_source": (
                f"most frequent API-type distribution prefix in the department's "
                f"/data.json Enterprise Data Inventory ({count} of "
                f"{sum(seen.values())} API distributions across {len(agency_datasets)} "
                f"datasets attributed to this agency); matched by {examples[prefix]['why']}")}


def shortlist(agency_datasets: list, params: dict) -> list:
    """The operator's shortlist: most recently modified first, with landing pages.

    **Offered, never selected from.** `select` does not call this. The inventory has no field
    that ranks datasets, so any ordering this module imposes is a convenience for a human
    making a declaration and not a measurement.
    """
    n = int(params["frame"]["edi"]["shortlist_n"])
    rows = []
    for row in agency_datasets:
        ds = row["dataset"]
        rows.append({"title": _clean(ds.get("title")), "modified": _clean(ds.get("modified")),
                     "landing_page": ds.get("landingPage") or "",
                     "identifier": _clean(ds.get("identifier")),
                     "matched_on": row["matched_on"]})
    rows.sort(key=lambda r: r["modified"], reverse=True)
    return rows[:n]


def declared_flagships(agency_code: str, cycle1_rows: list, params: dict) -> dict:
    """Flagships as the operator DECLARED them in the cycle-1 target list.

    ADDENDUM-02 §2.b: a ranking of an agency's products is a value judgment the inventory does
    not carry, so the 26 cycle-1 flagship surfaces stand as the declaration and this module
    does not derive a replacement. An agency below `min_declared_flagships` is marked pending
    and gets a shortlist for the operator — it does not get a guess.
    """
    floor = int(params["frame"]["edi"]["min_declared_flagships"])
    rows = [r for r in cycle1_rows
            if r.get("surface_kind") == "flagship"
            and str(r.get("agency", "")).upper() == agency_code.upper()]
    return {"flagships": [{"url": r["url"], "doc_id": r["doc_id"],
                           "selected_as": r.get("selected_as"),
                           "selection_source": "operator declaration, cycle 1 target list"}
                          for r in rows],
            "pending": len(rows) < floor,
            "marker": None if len(rows) >= floor
            else "flagships_pending_operator_declaration"}
