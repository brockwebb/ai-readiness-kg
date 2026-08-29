#!/usr/bin/env python3
"""T0 — bibliographic harvest (task 2026-08-29_corpus_t0_t1_substrate §0).

Third-party bibliographic metadata for every admitted document, cached raw so the harvest is
replayable without re-fetching. **Zero model calls**: OpenAlex/Crossref are metadata APIs.

Evidence class is `bibliographic` on every record written here — third-party asserted, never
derived from the document's own text by this project. Per the task's binding rule these
records never enter a validated stratum, are never pooled with gated (T2) items, and are
excluded from faithfulness reporting by construction. Author keywords and topic assignments
are retrieval features, not graph claims.

Resolution ladder, most to least reliable, with the server recorded per document:
  1. DOI in the manifest's source_url        -> OpenAlex /works/doi:...
  2. arXiv id in the source_url              -> OpenAlex /works/  filtered by arxiv id
  3. title search                            -> ACCEPTED ONLY under the guard below
  4. nothing matched                         -> bibliographic_partial

The title-search guard matters more than the ladder. A loose title match asserts that some
other paper IS this document, which would be a fabrication in the bibliographic layer — the
exact failure mode DD-024 recorded for distant supervision. Acceptance requires normalized
title equality or containment plus a year check; near-misses are rejected and land in
bibliographic_partial, which is a smaller claim than a wrong one.

GROBID (task §0.2) is NOT available in this environment — no server on :8070 and it needs a
Java runtime this task has no mandate to install. Header/reference extraction for DOI-less
PDFs is therefore not performed; those documents fall to step 3 and then to
bibliographic_partial. Reported in the RESULT rather than silently substituted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import requests                                                     # noqa: E402

CACHE = REPO / "state" / "biblio_cache"
MANIFEST = REPO / "corpus" / "manifest.json"
MAILTO = "brockwebb45@gmail.com"          # OpenAlex polite pool (task §0.4)
UA = f"ai-readiness-kg/1.0 (mailto:{MAILTO})"
OPENALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"
SLEEP = 0.12                              # polite-pool courtesy
MAX_BACKOFF_S = 90                        # beyond this a Retry-After is a daily quota


def norm_title(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).casefold()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


def identifiers(url: str) -> tuple[str | None, str | None]:
    """(doi, arxiv_id) parsed from the manifest's primary_url."""
    u = url or ""
    doi = None
    m = re.search(r"doi\.org/(10\.[^\s?#]+)", u)
    if m:
        doi = m.group(1).rstrip("/.")
    # Deterministic publisher URL -> DOI derivations. These are documented, mechanical URL
    # schemes, not guesses: the DOI is a rearrangement of characters already in the URL, and
    # a wrong derivation fails loudly as a 404 rather than resolving to another work. Only
    # the two publishers actually present in this corpus are handled.
    if doi is None:
        m = re.search(r"nature\.com/articles/([a-z]+)(\d{4})(\d+)", u)      # sdata201618
        if m:
            doi = f"10.1038/{m.group(1)}.{m.group(2)}.{m.group(3)}"
    if doi is None:
        m = re.search(r"aclanthology\.org/([0-9]{4}\.[a-z-]+\.[0-9]+)", u)  # 2023.findings-emnlp.722
        if m:
            doi = f"10.18653/v1/{m.group(1)}"
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", u)
    return doi, (m.group(1) if m else None)


class HarvestError(RuntimeError):
    """A transient failure (rate limit, 5xx, network). NOT the same as 'no such work'.

    The first run of this harvest conflated the two: `get` returned None on HTTP 429 and the
    caller recorded `bibliographic_partial`, so a rate limit became a permanent statement
    that a document has no bibliographic record. 159 of 178 documents were classified that
    way and the number could not be trusted. A transient condition must never be written
    down as a finding (standard 4: no silent failures)."""


def get(url: str, params: dict | None = None, *, tries: int = 5) -> dict | None:
    """Parsed JSON, or None for a genuine 404. Raises HarvestError on transient failure."""
    params = {**(params or {}), "mailto": MAILTO}
    delay = 1.0
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30)
        except requests.RequestException as exc:
            if attempt == tries:
                raise HarvestError(f"network: {exc}") from exc
            time.sleep(delay); delay *= 2; continue
        if r.status_code == 200:
            time.sleep(SLEEP)
            try:
                return r.json()
            except ValueError as exc:
                raise HarvestError(f"unparseable JSON from {r.url[:80]}") from exc
        if r.status_code == 404:
            time.sleep(SLEEP)
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            wait = float(r.headers.get("Retry-After") or delay)
            # A Retry-After far in the future is a DAILY QUOTA, not a transient blip:
            # OpenAlex answered 38,913s (~10.8h) once this harvest exhausted its budget.
            # Sleeping that out inside a task run is not waiting, it is hanging — so the
            # quota is surfaced as a retryable error carrying its own reset time.
            if wait > MAX_BACKOFF_S:
                raise HarvestError(
                    f"HTTP {r.status_code}: rate limit with Retry-After {wait:.0f}s "
                    f"({wait / 3600:.1f}h) — daily quota exhausted, retry after reset")
            if attempt == tries:
                raise HarvestError(f"HTTP {r.status_code} after {tries} attempts")
            print(f"    . HTTP {r.status_code}, backing off {wait:.0f}s "
                  f"(attempt {attempt}/{tries})", flush=True)
            time.sleep(wait); delay = min(delay * 2, MAX_BACKOFF_S); continue
        raise HarvestError(f"HTTP {r.status_code} {r.url[:80]}")
    raise HarvestError("exhausted retries")


#: Editorial suffixes this project's own manifest titles carry — "(Hiniduma et al., 2024)",
#: "(FCSM 2024 presentation)". They are cataloguer's annotations, not part of the published
#: title, and comparing them against a publisher's title guarantees a false mismatch.
_EDITORIAL_SUFFIX = re.compile(r"\s*\([^()]*\)\s*$")

#: Bibliographic records that WRAP a work rather than being it. Indexed under near-identical
#: titles, so a containment test accepts them and the harvest then attributes the wrapper's
#: citation count and reference list to the work. Observed, not hypothesized.
_WRAPPER_TITLES = ("faculty opinions recommendation of", "f1000prime recommendation of",
                   "correction to", "corrigendum to", "erratum to", "erratum",
                   "comment on", "reply to", "response to", "retraction notice",
                   "review of", "editorial expression of concern", "a formalization of")


def title_match_ok(want: str, got: str, want_year, got_year) -> tuple[bool, str]:
    """Strict guard. Returns (accept, why) — `why` is recorded either way.

    Two corrections after the first run, both from observed misses rather than from a wish
    for a higher hit rate:

    1. The manifest's `pub_year` is not reliably a publication year — for
       `wilkinson-2016-fair-guiding-principles` it holds `2019-11-11`, an access date, for a
       2016 paper. A year veto over an EXACT title match therefore rejects correct matches on
       bad local metadata. An exact normalized title match is accepted on its own; the year
       check is retained only for the weaker containment path, where it is doing real work.
    2. Manifest titles carry editorial suffixes the publisher's title does not.

    Neither change loosens the fuzzy path, which is where a wrong match would be a
    fabrication: containment still requires 25+ characters AND a year within one.
    """
    a = norm_title(_EDITORIAL_SUFFIX.sub("", str(want or "")))
    b = norm_title(got)
    if not a or not b:
        return False, "empty title on one side"
    if a == b:
        return True, "exact title match"
    if any(b.startswith(w) for w in _WRAPPER_TITLES):
        return False, f"wrapper record, not the work ({b[:60]!r})"
    if not ((a in b or b in a) and min(len(a), len(b)) >= 25):
        return False, f"title mismatch ({b[:60]!r})"
    # Containment alone lets a WRAPPER impersonate the work. Observed 2026-08-29: the FAIR
    # principles paper matched "Faculty Opinions recommendation of The FAIR Guiding
    # Principles..." — cited_by 3 against the real paper's thousands — because the manifest
    # title sits wholly inside the recommendation's title. The extra text must therefore be
    # a small fraction of the whole, not merely present.
    ratio = min(len(a), len(b)) / max(len(a), len(b))
    if ratio < 0.8:
        return False, (f"containment rejected: candidate carries {(1 - ratio) * 100:.0f}% extra "
                       f"text ({b[:50]!r})")
    try:
        wy, gy = int(str(want_year)[:4]), int(str(got_year)[:4])
    except (TypeError, ValueError):
        return False, "containment match but year not comparable — rejected as too weak"
    if abs(wy - gy) > 1:
        return False, f"containment match but year mismatch (manifest {wy}, cand {gy})"
    return True, f"title containment ({ratio:.2f}) + year matched"


def _classify_unresolved(provider_errors: list[str]) -> str:
    """The ONLY code path permitted to return `bibliographic_partial`.

    Centralized so the rule is checkable in one place and testable in one place: absence is
    a finding, failure is a state, and an error handler may never mint the former."""
    return "harvest_error" if provider_errors else "bibliographic_partial"


def soft_get(errors: list[str], url: str, params: dict | None = None) -> dict | None:
    """`get`, but a provider failure is recorded and returns None instead of raising.

    The resolution ladder exists so that one provider being down does not stop the harvest.
    When OpenAlex's daily quota went on 2026-08-29, a raising `get` aborted each document
    before it ever reached Crossref — the fallback was written but unreachable, which is the
    same as not having one. Errors are collected so the document's record shows WHICH rungs
    failed and which simply had no match: those are different states and only one is retryable.
    """
    try:
        return get(url, params)
    except HarvestError as exc:
        errors.append(f"{url.split('//')[-1].split('/')[0]}: {exc}")
        return None


def _from_crossref(msg: dict) -> dict:
    """Crossref item -> the same shape the OpenAlex branch stores, so downstream code has one
    schema. `referenced_dois` is Crossref's `reference` list: the raw material for the §2
    candidate expansion, and the reason Crossref is worth normalizing rather than just
    counting."""
    return {"source": "crossref",
            "title": (msg.get("title") or [None])[0],
            "publication_year": (msg.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "doi": msg.get("DOI"),
            "host_venue": (msg.get("container-title") or [None])[0],
            "type": msg.get("type"),
            "authorships": [{"author": {"display_name":
                                        f"{a.get('given', '')} {a.get('family', '')}".strip()}}
                            for a in msg.get("author") or []],
            "cited_by_count": msg.get("is-referenced-by-count"),
            "referenced_works": [],
            "referenced_dois": [r["DOI"].lower() for r in (msg.get("reference") or [])
                                if r.get("DOI")],
            "topics": [{"display_name": s} for s in (msg.get("subject") or [])]}


def harvest_one(doc_id: str, entry: dict) -> dict:
    idn = entry["identity"]
    url, title, year = idn.get("source_url") or "", idn.get("title") or "", idn.get("pub_year")
    doi, arxiv = identifiers(url)
    errors: list[str] = []
    rec = {"doc_id": doc_id, "evidence_class": "bibliographic",
           "manifest_title": title, "manifest_year": year, "primary_url": url,
           "doi": doi, "arxiv_id": arxiv, "resolution": None,
           "metadata_source": None, "match_note": None, "provider_errors": errors,
           "work": None}

    work = None
    if doi:
        work = soft_get(errors, f"{OPENALEX}/doi:{urllib.parse.quote(doi, safe='')}")
        if work:
            rec.update(resolution="doi", metadata_source="openalex",
                       match_note=f"resolved by DOI {doi}")
    if work is None and arxiv:
        d = soft_get(errors, OPENALEX, {"filter": f"ids.openalex:null,doi:null" if False else
                           f"locations.landing_page_url.search:{arxiv}", "per-page": 5,
                           "mailto": MAILTO})
        cands = (d or {}).get("results") or []
        if not cands:
            d = soft_get(errors, OPENALEX, {"search": title, "per-page": 5})
            cands = (d or {}).get("results") or []
        for c in cands:
            ok, why = title_match_ok(title, c.get("title") or c.get("display_name"),
                                     year, c.get("publication_year"))
            if ok:
                work, _ = c, None
                rec.update(resolution="arxiv_then_title", metadata_source="openalex",
                           match_note=f"arXiv {arxiv}; {why}")
                break
        else:
            if cands:
                rec["match_note"] = f"arXiv {arxiv}: candidates rejected by guard"
    if work is None and title:
        d = soft_get(errors, OPENALEX, {"search": title, "per-page": 5})
        for c in (d or {}).get("results") or []:
            ok, why = title_match_ok(title, c.get("title") or c.get("display_name"),
                                     year, c.get("publication_year"))
            if ok:
                work = c
                rec.update(resolution="title_search", metadata_source="openalex",
                           match_note=why)
                break
        else:
            rec["match_note"] = rec["match_note"] or "no OpenAlex candidate passed the guard"
    if work is None:
        # Crossref title search. Reached when OpenAlex has no match OR is unavailable —
        # on 2026-08-29 OpenAlex's daily quota was exhausted mid-harvest, so Crossref is
        # not a decoration here, it is the path that actually served most of the corpus.
        # Same guard: a Crossref hit is accepted only on the same title/year evidence.
        d = soft_get(errors, CROSSREF, {"query.bibliographic": title, "rows": 5})
        for c in ((d or {}).get("message") or {}).get("items") or []:
            ctitle = (c.get("title") or [None])[0]
            cyear = (c.get("issued", {}).get("date-parts") or [[None]])[0][0]
            ok, why = title_match_ok(title, ctitle, year, cyear)
            if ok:
                rec.update(resolution="crossref_title_search", metadata_source="crossref",
                           match_note=why)
                work = _from_crossref(c)
                break
        else:
            rec["match_note"] = rec["match_note"] or "no Crossref candidate passed the guard"
    if work is None and doi:                       # Crossref fallback for a DOI OpenAlex lacks
        d = soft_get(errors, f"{CROSSREF}/{urllib.parse.quote(doi, safe='')}")
        if d and d.get("message"):
            msg = d["message"]
            rec.update(resolution="doi", metadata_source="crossref",
                       match_note=f"OpenAlex miss; Crossref served DOI {doi}",
                       work={"crossref": True,
                             "title": (msg.get("title") or [None])[0],
                             "publication_year": (msg.get("issued", {})
                                                  .get("date-parts", [[None]])[0][0]),
                             "host_venue": (msg.get("container-title") or [None])[0],
                             "authorships": [{"author": {"display_name":
                                                         f"{a.get('given','')} {a.get('family','')}".strip()}}
                                             for a in msg.get("author") or []],
                             "referenced_works": [], "cited_by_count": msg.get("is-referenced-by-count"),
                             "topics": []})
            return rec
    if work is None:
        # ADDENDUM-02 §4, the binding guard: `bibliographic_partial` is a CLAIM ABOUT THE
        # WORLD — this document has no third-party bibliographic record — and may only be
        # written where every provider answered cleanly and none had a match. If any provider
        # failed, the state is `harvest_error`, which is retryable and asserts nothing. The
        # first run of this harvest violated exactly this: a rate limit reached the same
        # branch as a genuine miss and 159 documents were labelled partial on the strength of
        # an HTTP 429.
        rec["resolution"] = _classify_unresolved(errors)
        if errors:
            rec["match_note"] = f"providers failed: {'; '.join(errors[:3])}"
        return rec
    rec["work"] = work
    return rec


def harvest_guarded(doc_id: str, entry: dict) -> dict:
    """harvest_one, with transient failure recorded as `harvest_error` — a retryable state,
    never `bibliographic_partial`, which is a claim about the world."""
    try:
        return harvest_one(doc_id, entry)
    except HarvestError as exc:
        return {"doc_id": doc_id, "evidence_class": "bibliographic",
                "manifest_title": entry["identity"].get("title"),
                "manifest_year": entry["identity"].get("pub_year"),
                "primary_url": entry["identity"].get("source_url"),
                "resolution": "harvest_error", "metadata_source": None,
                "match_note": str(exc), "work": None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true", help="ignore cache")
    ap.add_argument("--retry-unresolved", action="store_true",
                    help="re-harvest cached bibliographic_partial and harvest_error entries "
                         "(used after the 429 defect and the guard correction)")
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    entries = json.loads(MANIFEST.read_text())["entries"]
    inc = {k: v for k, v in entries.items() if v["screening"]["decision"] == "included"}
    todo = sorted(inc)[: a.limit or None]
    stats = {"cached": 0, "doi": 0, "arxiv_then_title": 0, "title_search": 0,
             "bibliographic_partial": 0}
    for i, doc_id in enumerate(todo, 1):
        out = CACHE / f"{doc_id}.json"
        stale = False
        if out.exists() and a.retry_unresolved:
            stale = json.loads(out.read_text()).get("resolution") in (
                "bibliographic_partial", "harvest_error", None)
        if out.exists() and not a.refresh and not stale:
            stats["cached"] += 1
            stats[json.loads(out.read_text()).get("resolution") or "bibliographic_partial"] = \
                stats.get(json.loads(out.read_text()).get("resolution") or "bibliographic_partial", 0) + 1
            continue
        rec = harvest_guarded(doc_id, inc[doc_id])
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        stats[rec["resolution"]] = stats.get(rec["resolution"], 0) + 1
        print(f"[{i}/{len(todo)}] {doc_id[:56]:<58} {rec['resolution']:<22} "
              f"{(rec['match_note'] or '')[:52]}")
    print("\nT0 harvest:", json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
