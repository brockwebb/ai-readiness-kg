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
import os
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
#: Crossref still runs a polite pool and still honours `mailto`. OpenAlex does NOT: it retired
#: the polite pool and the `mailto` parameter and made an API key mandatory on 2026-02-13.
#: Measured 2026-08-29 against the live API, not taken on faith — see the RESULT for the probe:
#:   mailto, no key -> HTTP 429 "Insufficient budget ... you only have $0 remaining"
#:   no key at all  -> HTTP 429, identical (so `mailto` now buys exactly nothing)
#:   invalid key    -> HTTP 401 "Invalid or missing API key"
#:   valid key      -> HTTP 200, X-RateLimit-Limit: 10000
MAILTO = "brockwebb45@gmail.com"          # Crossref polite pool ONLY
UA = f"ai-readiness-kg/1.0 (mailto:{MAILTO})"
OPENALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"
SLEEP = 0.12                              # courtesy
MAX_BACKOFF_S = 90                        # beyond this a Retry-After is a budget exhaustion

#: One constant per failure class, used at BOTH the write end (the message) and the detect end
#: (the classifier), so a detector can never drift away from the text it is looking for.
#: These are three different states and only one of them is a reason to stop for the night:
#:   AUTH    — the key is missing or rejected. Waiting does not fix it. A hard exit.
#:   QUOTA   — the day's credits are spent. Waiting until the UTC reset DOES fix it.
#:   (transient) — 5xx/network. Retry now.
#: Conflating the first two is what the previous version did, and it turned "you have no key"
#: into "come back tomorrow", which is a claim about the world that was simply untrue.
AUTH_NOTE = "OpenAlex API key missing or rejected — a key fixes this, waiting does not"
QUOTA_NOTE = "daily quota exhausted, retry after reset"

#: Resolution states for the three, distinct in the record and in `retryable_by_provider`.
AUTH_ERROR = "provider_auth_error"
QUOTA_ERROR = "provider_quota_exhausted"
TRANSIENT_ERROR = "harvest_error"

#: States `--retry-unresolved` re-harvests. Named so the three failure classes cannot drift
#: out of the resume set — a state that is retryable in `kg/biblio.py` but absent here would
#: be permanently stuck: reported as pending, never actually retried.
#: `bibliographic_partial` is included because the guard that produced it has been revised
#: more than once; OUT_OF_SCOPE is deliberately absent, being terminal.
RETRY_STATES = frozenset({"bibliographic_partial", "harvest_error",
                          "provider_auth_error", "provider_quota_exhausted", None})

#: Terminal, NOT retryable: this document is not the kind of thing a scholarly index holds,
#: so no number of retries will ever find it. Distinct from `bibliographic_partial`, which is
#: the stronger claim that every provider was asked and none had a record.
OUT_OF_SCOPE = "bibliographic_out_of_scope"

#: doc_type values whose documents plausibly carry a scholarly index record. The manifest
#: field is `doc_type` (178/178 populated); the task specifies `source_type`, which does not
#: exist on any entry — reported as a discrepancy, implemented against the real field.
ACADEMIC_DOC_TYPES = frozenset({"academic", "preprint"})

#: Consecutive documents that may fail on quota ALONE before the sweep gives up for the night.
#: Once a provider answers "retry in 6.7h", every remaining request is known-doomed, and this
#: harvest is now scheduled nightly (task 2026-08-29_biblio_cron) — so without a stop, one
#: exhausted night is 149 pointless requests against a polite-pool API, every night. 3 matches
#: the repo's existing systemic-failure idiom (BURN_QUARANTINE_STOP_MODE=systemic halts on 3
#: consecutive over-threshold documents): one failure is an incident, three is a condition.
#: It is deliberately not 1 — the provider ladder can still resolve a document through
#: Crossref while OpenAlex is quota-dead, and stopping on the first would forfeit those.
CONSECUTIVE_QUOTA_STOP = 3


def openalex_key() -> str | None:
    """`OPENALEX_API_KEY` from the environment, else from ~/.wintermute/.env.

    Same idiom as `build_projection._neo4j_creds` (env first, dotenv fallback, value never
    printed) so there is one way credentials enter this repo, not two."""
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        return key.strip() or None
    wm_env = Path.home() / ".wintermute" / ".env"
    if wm_env.is_file():
        for line in wm_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() == "OPENALEX_API_KEY":
                    return v.strip().strip('"').strip("'") or None
    return None


def preflight() -> str:
    """Refuse to run without a key, naming the fix. Exits non-zero; issues no request.

    A missing key does NOT announce itself as an auth error at the API: measured 2026-08-29,
    an absent key returns HTTP 429 with a budget message, indistinguishable at the status
    line from a genuine daily exhaustion. So the only place the distinction can be made
    reliably is here, before the first request. Falling through to an unauthenticated attempt
    is precisely how "no key" got written down as "daily quota exhausted" across 149
    documents."""
    key = openalex_key()
    if not key:
        raise SystemExit(
            "FATAL: OPENALEX_API_KEY missing; set it in the environment or "
            "~/.wintermute/.env. OpenAlex retired the polite pool and made the key "
            "mandatory on 2026-02-13, so an unauthenticated run cannot resolve anything "
            "and would misreport itself as a quota exhaustion.")
    return key


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
    """A provider failure. NOT the same as 'no such work'.

    `kind` is one of "auth" | "quota" | "transient". It travels with the exception so the
    classification is decided once, where the HTTP status is actually in hand, rather than
    re-derived later by matching on message text.

    The first run of this harvest conflated the two: `get` returned None on HTTP 429 and the
    caller recorded `bibliographic_partial`, so a rate limit became a permanent statement
    that a document has no bibliographic record. 159 of 178 documents were classified that
    way and the number could not be trusted. A transient condition must never be written
    down as a finding (standard 4: no silent failures)."""

    def __init__(self, message: str, kind: str = "transient"):
        super().__init__(message)
        self.kind = kind


#: Credits left at OpenAlex, as last reported by its own headers. A real exhaustion is then
#: EVIDENCED by the provider rather than inferred from the shape of a Retry-After.
CREDITS: dict[str, str | None] = {"remaining": None, "limit": None, "reset_s": None}

#: Malformed requests this run made. A bug in the harness, never a fact about a document.
REQUEST_ERRORS: list[str] = []


def _auth_params(url: str) -> dict:
    """Per-provider authentication. OpenAlex takes `api_key`; Crossref keeps `mailto`.

    Sending `mailto` to OpenAlex is not merely useless now, it is misleading: it reads like
    authentication in the code while buying nothing at the server."""
    if "openalex.org" in url:
        key = openalex_key()
        return {"api_key": key} if key else {}
    return {"mailto": MAILTO}


def get(url: str, params: dict | None = None, *, tries: int = 5) -> dict | None:
    """Parsed JSON, or None for a genuine 404. Raises HarvestError on provider failure."""
    params = {**(params or {}), **_auth_params(url)}
    if "openalex.org" in url:
        # A caller may still pass mailto from the pre-2026-02-13 era; drop it rather than
        # send a parameter the server no longer honours.
        params.pop("mailto", None)
    delay = 1.0
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30)
        except requests.RequestException as exc:
            if attempt == tries:
                raise HarvestError(f"network: {exc}") from exc
            time.sleep(delay); delay *= 2; continue
        if "openalex.org" in url:                # record credits whatever the status
            for hdr, slot in (("X-RateLimit-Remaining", "remaining"),
                              ("X-RateLimit-Limit", "limit"),
                              ("X-RateLimit-Reset", "reset_s")):
                if r.headers.get(hdr) is not None:
                    CREDITS[slot] = r.headers.get(hdr)
        if r.status_code in (401, 403, 409):
            # Measured: an INVALID key returns 401 "Invalid or missing API key". Waiting
            # cannot fix this, so it must never carry the quota message and must never feed
            # the nightly quota stop.
            raise HarvestError(f"HTTP {r.status_code}: {AUTH_NOTE}", kind="auth")
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
                left = CREDITS.get("remaining")
                evidence = f", credits remaining {left}" if left is not None else ""
                raise HarvestError(
                    f"HTTP {r.status_code}: rate limit with Retry-After {wait:.0f}s "
                    f"({wait / 3600:.1f}h){evidence} — {QUOTA_NOTE}", kind="quota")
            if attempt == tries:
                raise HarvestError(f"HTTP {r.status_code} after {tries} attempts")
            print(f"    . HTTP {r.status_code}, backing off {wait:.0f}s "
                  f"(attempt {attempt}/{tries})", flush=True)
            time.sleep(wait); delay = min(delay * 2, MAX_BACKOFF_S); continue
        if r.status_code in (400, 422):
            # OUR query is wrong, not the provider's day. Still unresolved for this document,
            # so still retryable — but counted and surfaced in the run summary, because the
            # previous version filed this as ordinary provider flakiness and 7 documents sat
            # in a permanently-failing retry loop with nothing on the surface to show it.
            REQUEST_ERRORS.append(f"HTTP {r.status_code} {r.url[:120]}")
            raise HarvestError(f"HTTP {r.status_code} (malformed query) {r.url[:80]}",
                               kind="transient")
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
    a finding, failure is a state, and an error handler may never mint the former.

    Failure states are ranked by how much they explain. Auth outranks quota: with no valid
    key every request returns a budget message, so a run without a key would otherwise
    report 149 "quota exhausted" documents — which is what happened, and is a claim about
    the world that was false. Quota outranks transient for the same reason."""
    if not provider_errors:
        return "bibliographic_partial"
    if any(AUTH_NOTE in e for e in provider_errors):
        return AUTH_ERROR
    if any(QUOTA_NOTE in e for e in provider_errors):
        return QUOTA_ERROR
    return TRANSIENT_ERROR


def eligibility(entry: dict, cached_resolution: str | None = None) -> tuple[bool, str]:
    """(eligible, reason) — may this document plausibly hold a scholarly index record?

    Evaluated BEFORE any OpenAlex call. The corpus is majority gray literature (statutes,
    OMB memos, vendor blog posts, W3C specs); queueing those as retryable forever is what
    made T0 look like a blocker when it was really a category error.

    The `cached_resolution` clause is not a loophole, it is a correctness requirement: a
    document we already hold an index record for is PROVEN eligible, and writing
    `bibliographic_out_of_scope` over it would assert something the evidence in hand
    contradicts. Measured on this corpus, 9 already-resolved documents are outside the
    academic doc_types and carry no DOI in their URL — they were found by title search — so
    without this clause the gate would have demoted nine real findings."""
    if cached_resolution not in (None, "", TRANSIENT_ERROR, AUTH_ERROR, QUOTA_ERROR,
                                 OUT_OF_SCOPE):
        return True, f"already resolved ({cached_resolution}) — eligibility proven by record"
    idn = entry.get("identity") or {}
    doi, arxiv = identifiers(idn.get("source_url") or "")
    if doi:
        return True, f"DOI in or derivable from primary_url ({doi})"
    if arxiv:
        return True, f"arXiv id in primary_url ({arxiv})"
    dt = (idn.get("doc_type") or "").strip().lower()
    if dt in ACADEMIC_DOC_TYPES:
        return True, f"doc_type={dt}"
    return False, (f"doc_type={dt or 'unset'} with no DOI or arXiv id in primary_url — "
                   f"not the kind of document a scholarly index holds")


def out_of_scope_record(doc_id: str, entry: dict, why: str) -> dict:
    idn = entry.get("identity") or {}
    return {"doc_id": doc_id, "evidence_class": "bibliographic",
            "manifest_title": idn.get("title"), "manifest_year": idn.get("pub_year"),
            "primary_url": idn.get("source_url"), "doi": None, "arxiv_id": None,
            "resolution": OUT_OF_SCOPE, "metadata_source": None,
            "match_note": why, "provider_errors": [], "work": None}


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
        # arXiv assigns every submission the DOI 10.48550/arXiv.<id>. That is a documented,
        # mechanical derivation — the same class as the nature.com and aclanthology.org rules
        # in `identifiers` — so this is an EXACT identifier lookup, not a search, and it gets
        # no title guard for the same reason the plain-DOI branch above has none. A wrong
        # derivation returns nothing rather than someone else's paper.
        #
        # It replaces `filter=locations.landing_page_url.search:<id>`, which OpenAlex answers
        # HTTP 400 "not a valid field": a malformed query, permanently. That returned a
        # retryable state, so 7 documents were queued to be retried forever against a request
        # that could never succeed — the same "pending forever" pathology this task fixes,
        # one layer down. Measured 2026-08-29; 5 of the 7 resolve by this route.
        arxiv_doi = f"10.48550/arXiv.{arxiv}"
        d = soft_get(errors, OPENALEX,
                     {"filter": f"doi:{arxiv_doi}", "per-page": 1})
        cands = (d or {}).get("results") or []
        if cands:
            work = cands[0]
            rec.update(resolution="arxiv_doi", metadata_source="openalex",
                       match_note=f"arXiv {arxiv} -> DOI {arxiv_doi} (exact identifier)")
        else:
            # Not in OpenAlex under its arXiv DOI. Fall through to the guarded title search.
            d = soft_get(errors, OPENALEX, {"search": title, "per-page": 5})
            for c in (d or {}).get("results") or []:
                ok, why = title_match_ok(title, c.get("title") or c.get("display_name"),
                                         year, c.get("publication_year"))
                if ok:
                    work = c
                    rec.update(resolution="arxiv_then_title", metadata_source="openalex",
                               match_note=f"arXiv {arxiv}; {why}")
                    break
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
        kind = {"auth": AUTH_ERROR, "quota": QUOTA_ERROR}.get(
            getattr(exc, "kind", "transient"), TRANSIENT_ERROR)
        return {"doc_id": doc_id, "evidence_class": "bibliographic",
                "manifest_title": entry["identity"].get("title"),
                "manifest_year": entry["identity"].get("pub_year"),
                "primary_url": entry["identity"].get("source_url"),
                "resolution": kind, "metadata_source": None,
                "match_note": str(exc), "provider_errors": [str(exc)], "work": None}


def is_quota_exhausted(rec: dict) -> bool:
    """True when a record failed and EVERY provider that spoke reported a spent daily budget.

    `all`, not `any`: a document whose OpenAlex lookup hit the quota but whose Crossref
    lookup returned a genuine "no record" has learned something, and must not be counted
    toward a stop that means "the network is telling us to come back tomorrow".

    Keyed on the QUOTA class only. An auth failure must never reach here: it is not fixed by
    waiting, so letting it trip the nightly stop would produce a job that exits 0 every night
    for a reason that will never change on its own — which is exactly what it did."""
    if rec.get("resolution") != QUOTA_ERROR:
        return False
    errs = rec.get("provider_errors") or ([rec["match_note"]] if rec.get("match_note") else [])
    return bool(errs) and all(QUOTA_NOTE in e for e in errs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true", help="ignore cache")
    ap.add_argument("--retry-unresolved", action="store_true",
                    help="re-harvest cached bibliographic_partial and harvest_error entries "
                         "(used after the 429 defect and the guard correction)")
    a = ap.parse_args()
    preflight()                       # refuses, non-zero, before any request is issued
    CACHE.mkdir(parents=True, exist_ok=True)
    entries = json.loads(MANIFEST.read_text())["entries"]
    inc = {k: v for k, v in entries.items() if v["screening"]["decision"] == "included"}
    todo = sorted(inc)[: a.limit or None]
    stats = {"cached": 0, "doi": 0, "arxiv_then_title": 0, "title_search": 0,
             "bibliographic_partial": 0}
    quota_streak = 0
    for i, doc_id in enumerate(todo, 1):
        out = CACHE / f"{doc_id}.json"
        stale = False
        if out.exists() and a.retry_unresolved:
            stale = json.loads(out.read_text()).get("resolution") in RETRY_STATES
        if out.exists() and not a.refresh and not stale:
            stats["cached"] += 1
            stats[json.loads(out.read_text()).get("resolution") or "bibliographic_partial"] = \
                stats.get(json.loads(out.read_text()).get("resolution") or "bibliographic_partial", 0) + 1
            continue
        prior = json.loads(out.read_text()).get("resolution") if out.exists() else None
        ok, why = eligibility(inc[doc_id], prior)
        if not ok:
            rec = out_of_scope_record(doc_id, inc[doc_id], why)
            out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            stats[OUT_OF_SCOPE] = stats.get(OUT_OF_SCOPE, 0) + 1
            print(f"[{i}/{len(todo)}] {doc_id[:56]:<58} {OUT_OF_SCOPE:<26} {why[:44]}")
            quota_streak = 0          # a skipped document is no evidence about the provider
            continue
        rec = harvest_guarded(doc_id, inc[doc_id])
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        stats[rec["resolution"]] = stats.get(rec["resolution"], 0) + 1
        print(f"[{i}/{len(todo)}] {doc_id[:56]:<58} {rec['resolution']:<26} "
              f"{(rec['match_note'] or '')[:48]}")
        if rec["resolution"] == AUTH_ERROR:
            # Not a nightly no-op: no number of retries supplies a key.
            print(f"\nFATAL: {AUTH_NOTE}. Stopping — this is not a condition that clears "
                  f"on its own, and continuing would write it across every document.")
            print("\nT0 harvest:", json.dumps(stats, indent=1))
            return 2
        quota_streak = quota_streak + 1 if is_quota_exhausted(rec) else 0
        if quota_streak >= CONSECUTIVE_QUOTA_STOP:
            left = len(todo) - i
            stats["stopped_on_quota"] = left
            print(f"\nSTOP: {quota_streak} consecutive documents failed on daily quota alone. "
                  f"Every further request tonight is known-doomed, so the sweep ends here. "
                  f"{left} document(s) untouched, still retryable; the next run picks them up.")
            break
    if REQUEST_ERRORS:
        stats["malformed_requests"] = len(REQUEST_ERRORS)
        print(f"\nWARNING: {len(REQUEST_ERRORS)} malformed request(s) — a harness bug, not a "
              f"provider condition. These documents will retry forever until the query is "
              f"fixed. First: {REQUEST_ERRORS[0][:160]}")
    if CREDITS["remaining"] is not None:
        stats["openalex_credits_remaining"] = CREDITS["remaining"]
        stats["openalex_credits_limit"] = CREDITS["limit"]
    print("\nT0 harvest:", json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
