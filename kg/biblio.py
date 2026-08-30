#!/usr/bin/env python3
"""T0 bibliographic layer — coverage, resumable harvest, and the derived rankings.

ADDENDUM-02 §1 to task 2026-08-29_corpus_t0_t1_substrate makes availability a queue rather
than a gate (methodology §7.10): T0 completeness is NOT an exit criterion, so the harvest has
to be finishable later by one command with no session context.

    python -m kg.biblio coverage     # resolved / retryable / partial, per provider
    python -m kg.biblio resume       # finish the harvest, then recompute everything derived

`resume` is idempotent and safe to run under quota: it only touches documents in a RETRYABLE
state, the provider ladder degrades rather than aborts, and a daily quota surfaces as a
retryable error instead of a multi-hour sleep. On completion it recomputes the §2.2 coupling
ranking and the §2.3 t2_priority ordering, so a later run silently upgrades the provisional
numbers instead of leaving them stale — which is the only reason a provisional number is
safe to publish at all.

Zero model calls.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
CACHE = _REPO / "state" / "biblio_cache"
CROSSWALK = _REPO / "docs" / "crosswalk" / "usafacts_operationalization_skeleton.md"
CANDIDATES = _REPO / "docs" / "corpus" / "acquisition_candidates.md"
PRIORITY = _REPO / "state" / "t2_priority.json"

#: States that assert nothing about the world and may be retried.
#: States that assert nothing about the world and may be retried. All three are provider
#: failures; they differ in what would fix them (a key / the UTC reset / a retry now), which
#: is why they are separate states rather than one bucket (task 2026-08-29_openalex §2.3).
RETRYABLE = {"harvest_error", "provider_auth_error", "provider_quota_exhausted", None}
#: A finding: every provider answered and none had a record.
FINDING = "bibliographic_partial"
#: Terminal and NOT pending: this document is not the kind of thing a scholarly index holds.
#: Excluded from the retryable count and from any denominator that implies it is waiting.
OUT_OF_SCOPE = "bibliographic_out_of_scope"


def records() -> list[dict]:
    return [json.loads(f.read_text()) for f in sorted(CACHE.glob("*.json"))]


def blocked_docs() -> list[str]:
    """Documents whose ACQUISITION is blocked — a different failure from a bibliographic
    miss, and ADDENDUM-02 §1 requires it in the same coverage table so the two are not read
    as one number. Sourced from the event log, where the block was recorded."""
    from kg import eventlog
    out = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == "acquisition_blocked":
            out[ev.get("doc_id")] = ev.get("primary_url")
    return sorted(out)


def biblio_method(rec: dict) -> str:
    """ADDENDUM-02 §4 — the method that produced (or failed to produce) this record, as one
    field. GROBID is deliberately absent from the ladder in this environment; naming the
    method per document is what makes that visible in the data instead of only in a RESULT."""
    res = rec.get("resolution")
    if res == OUT_OF_SCOPE:
        return "unresolved:out_of_scope"
    if res in RETRYABLE:
        return "unresolved:provider_unavailable"
    if res == FINDING:
        return "unresolved:no_record_at_source"
    return f"{res}@{rec.get('metadata_source') or 'unknown'}"


def coverage() -> dict:
    recs = records()
    by_res = Counter(r.get("resolution") for r in recs)
    by_provider = Counter(r.get("metadata_source") for r in recs if r.get("metadata_source"))
    resolved = [r for r in recs
                if r.get("resolution") not in RETRYABLE | {FINDING, OUT_OF_SCOPE}]
    out_of_scope = [r for r in recs if r.get("resolution") == OUT_OF_SCOPE]
    # The honest denominator. A document that cannot be in a scholarly index is not
    # "pending"; counting it as such is what made T0 read as a blocker rather than a
    # category error (task 2026-08-29_openalex §3).
    eligible = len(recs) - len(out_of_scope)
    blocked = blocked_docs()
    # Provider breakdown of the retryable pile: which provider is holding each one up.
    retry_by_provider = Counter()
    for r in recs:
        if r.get("resolution") in RETRYABLE:
            for e in (r.get("provider_errors") or []) or ["(none recorded)"]:
                retry_by_provider[e.split(":")[0]] += 1
    return {
        "total": len(recs),
        "eligible": eligible,
        "out_of_scope": len(out_of_scope),
        "resolved": len(resolved),
        "resolved_of_eligible": f"{len(resolved)}/{eligible}",
        "retryable": sum(v for k, v in by_res.items() if k in RETRYABLE),
        "auth_error": by_res.get("provider_auth_error", 0),
        "quota_exhausted": by_res.get("provider_quota_exhausted", 0),
        "transient_error": by_res.get("harvest_error", 0),
        "partial_finding": by_res.get(FINDING, 0),
        "blocked": len(blocked),
        "blocked_docs": blocked,
        "by_resolution": dict(by_res),
        "by_provider": dict(by_provider),
        "retryable_by_provider": dict(retry_by_provider),
        "referenced_dois": sum(len((r.get("work") or {}).get("referenced_dois") or [])
                               for r in recs),
        "docs_with_references": sum(
            1 for r in recs if (r.get("work") or {}).get("referenced_dois")),
    }


# ---------------------------------------------------------------- derived rankings
def crosswalk_demand() -> dict[str, int]:
    """How many crosswalk evidence cells name each doc_id. Coverage-INDEPENDENT: it reads the
    crosswalk, not the citation graph, so ADDENDUM-02 §1 requires it reported now regardless
    of T0 coverage."""
    if not CROSSWALK.exists():
        return {}
    import re
    text = CROSSWALK.read_text("utf-8", "ignore")
    body = text.split("## 10. References")[0]          # citations there are not demand
    return dict(Counter(re.findall(r"`([a-z0-9][a-z0-9\-]{6,})`", body)))


def norm_title(s: str) -> str:
    """Same normalization the T0 harvester uses (`t0_biblio_harvest.norm_title`), restated
    here so this module does not import a script for one helper."""
    import unicodedata
    s = unicodedata.normalize("NFKC", str(s or "")).casefold()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


def corpus_identifiers() -> tuple[set[str], set[str], dict[str, str]]:
    """(DOIs, arXiv ids, normalized-title -> doc_id) the corpus already holds. A work the
    corpus HAS is not a candidate to acquire; without this the ranking recommends buying
    what is on the shelf.

    The title index exists because identifier matching alone does NOT catch the
    preprint/published pair: `liu-2023-evaluating-verifiability-generative-search` is held
    as arXiv 2304.09848, and its EMNLP Findings DOI `10.18653/v1/2023.findings-emnlp.467`
    is a DIFFERENT DOI on a DIFFERENT OpenAlex work — it reached 3 corpus citers and topped
    the ranking as a candidate to acquire on 2026-08-30, hours after the same paper was
    admitted. Title matching is how record linkage joins versions (and it is fallible: the
    FAIR "Faculty Opinions recommendation of ..." wrapper defect is the standing warning),
    so a title hit MARKS the row `held_title_match` rather than deleting it.
    """
    dois, arx, titles = set(), set(), {}
    for r in records():
        w = r.get("work") or {}
        d = (w.get("doi") or "").replace("https://doi.org/", "").lower().strip()
        if d:
            dois.add(d)
        a = (r.get("arxiv_id") or "").lower().strip()
        if a:
            arx.add(a)
        u = (r.get("primary_url") or "")
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", u, re.I)
        if m:
            arx.add(m.group(1).lower())
        for t in (r.get("manifest_title"), w.get("title")):
            nt = norm_title(t)
            if len(nt) >= 20:              # too-short titles collide by accident
                titles.setdefault(nt, r["doc_id"])
    return dois, arx, titles


def coupling_candidates() -> list[dict]:
    """Non-corpus works cited by >= N corpus members (task §2.2, bibliographic coupling —
    Kessler 1963).

    Two evidence classes feed this and are **never pooled into one count**
    (2026-08-30_acquisition_round2 §1): `bibliographic` is a third-party index asserting a
    document's reference list; `bibliographic_derived` is OUR regex reading the document's
    own printed bibliography out of the Docling markdown. They fail differently — a wrong
    index record versus a wrong pattern — so every row carries both counts and the total is
    a union of citing DOCUMENTS, which is the quantity coupling is defined over.
    """
    from kg import refparse

    have_doi, have_arx, have_title = corpus_identifiers()
    enr = load_enrichment()
    cited: dict[tuple[str, str], dict[str, set]] = defaultdict(
        lambda: {"bibliographic": set(), "bibliographic_derived": set()})
    for r in records():
        for d in ((r.get("work") or {}).get("referenced_dois") or []):
            d = d.lower()
            if d and d not in have_doi:
                cited[("doi", d)]["bibliographic"].add(r["doc_id"])
    for r in refparse.records():
        for d in r.get("referenced_dois") or []:
            if d and d not in have_doi:
                cited[("doi", d)]["bibliographic_derived"].add(r["doc_id"])
        for a in r.get("referenced_arxiv") or []:
            if a and a not in have_arx:
                cited[("arxiv", a)]["bibliographic_derived"].add(r["doc_id"])
    out = []
    for (kind, ident), v in cited.items():
        union = v["bibliographic"] | v["bibliographic_derived"]
        e = enr.get(f"{kind}:{ident}") or {}
        held = have_title.get(norm_title(e.get("title") or ""))
        out.append({"id_type": kind, "id": ident,
                    "held_title_match": held,
                    # `doi` retained for the pre-existing callers and for arXiv rows it is
                    # None rather than a fabricated identifier.
                    "doi": ident if kind == "doi" else None,
                    "n_corpus_citers": len(union),
                    "n_citers_bibliographic": len(v["bibliographic"]),
                    "n_citers_derived": len(v["bibliographic_derived"]),
                    "citers": sorted(union)})
    return sorted(out, key=lambda x: (-x["n_corpus_citers"], x["id_type"], x["id"]))


#: Coupling rows enriched with open-access metadata are cached here; the enrichment is a
#: network call per candidate and the ranking is regenerated on every `recompute`.
#: NOT inside `state/biblio_cache/`: `records()` globs that directory for per-document T0
#: records, and a sidecar file there is read as a document with no `doc_id`.
ENRICH = _REPO / "state" / "candidate_oa.json"
#: Pre-registered coupling bar (task 2026-08-29_corpus_t0_t1_substrate §2.2). It is a
#: REVIEW gate, not an admission rule: rows at or above it get individually evaluated
#: against the AUTH-2 inclusion rule; rows below it are cut without review. The bar is not
#: lowered to manufacture a list.
COUPLING_BAR = 3
#: Rows below the bar but at this level are still REPORTED (cut, with the tier named), so a
#: near-miss is visible to the operator instead of vanishing into a count.
NEAR_MISS = 2


#: Round-2 evaluation decisions (task 2026-08-30_acquisition_round2 §3), keyed by the
#: identifier the coupling ranking uses, so the candidates file can show every row's
#: disposition instead of leaving it in limbo.
ROUND2_LIST = _REPO / "scripts" / "round2_list_2026-08-30.yaml"


def evaluation_decisions() -> dict[str, dict]:
    """{'doi:...'|'arxiv:...' -> {verdict, clause, doc_id}} from the round-2 list."""
    if not ROUND2_LIST.exists():
        return {}
    import yaml
    out = {}
    for e in (yaml.safe_load(ROUND2_LIST.read_text(encoding="utf-8")) or {}).get("entries", []):
        url = e.get("primary_url") or ""
        keys = []
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", url, re.I)
        if m:
            keys.append("arxiv:" + m.group(1).lower())
        m = re.search(r"doi\.org/(10\.[^\s?#]+)", url, re.I)
        if m:
            keys.append("doi:" + m.group(1).rstrip("/.").lower())
        for k in keys:
            out[k] = {"verdict": e["verdict"], "clause": e.get("clause"),
                      "doc_id": e["doc_id"], "notes": e.get("notes")}
    return out


def load_enrichment() -> dict:
    if ENRICH.exists():
        return json.loads(ENRICH.read_text())
    return {}


def enrich_candidates(cands: list[dict], min_citers: int = NEAR_MISS,
                      verbose: bool = True) -> dict:
    """Open-access status and fetchability for the candidates a human will actually read.

    Bounded to `min_citers` and above on purpose: the 1-citer tail is hundreds of rows that
    the coupling bar cuts unreviewed, and spending a network request per row to decorate a
    decision already made is waste, not diligence.
    """
    import sys as _sys
    _sys.path.insert(0, str(_REPO / "scripts"))
    import t0_biblio_harvest as t0                                    # noqa: E402

    cache = load_enrichment()
    todo = [c for c in cands if c["n_corpus_citers"] >= min_citers
            and f"{c['id_type']}:{c['id']}" not in cache]
    for c in todo:
        key = f"{c['id_type']}:{c['id']}"
        try:
            if c["id_type"] == "doi":
                import urllib.parse
                w = t0.get(f"{t0.OPENALEX}/doi:{urllib.parse.quote(c['id'], safe='')}")
            else:
                d = t0.get(t0.OPENALEX, {"filter": f"doi:10.48550/arxiv.{c['id']}"})
                res = (d or {}).get("results") or []
                w = res[0] if res else None
        except Exception as exc:                     # provider failure, not a finding
            cache[key] = {"resolution": "provider_error", "error": str(exc)[:200]}
            if verbose:
                print(f"  ?? {key}: {exc}")
            continue
        if not w:
            # arXiv ids always have a fetchable primary text even when no index holds a
            # record; a DOI with no record is genuinely unknown.
            cache[key] = ({"resolution": "no_index_record", "is_oa": True,
                           "oa_status": "arxiv", "title": None,
                           "pdf_url": f"https://arxiv.org/pdf/{c['id']}",
                           "landing_url": f"https://arxiv.org/abs/{c['id']}"}
                          if c["id_type"] == "arxiv" else
                          {"resolution": "no_index_record", "is_oa": None,
                           "oa_status": None, "title": None,
                           "pdf_url": None, "landing_url": None})
        else:
            oa = w.get("open_access") or {}
            best = w.get("best_oa_location") or {}
            cache[key] = {
                "resolution": "resolved", "title": w.get("title"),
                "year": w.get("publication_year"),
                "type": w.get("type"),
                "venue": ((w.get("primary_location") or {}).get("source") or {}
                          ).get("display_name"),
                "cited_by_count": w.get("cited_by_count"),
                "is_oa": oa.get("is_oa"), "oa_status": oa.get("oa_status"),
                "pdf_url": best.get("pdf_url") or oa.get("oa_url"),
                "landing_url": best.get("landing_page_url"),
            }
        if verbose:
            e = cache[key]
            print(f"  ok {key}: oa={e.get('oa_status')} "
                  f"{(e.get('title') or '')[:60]}")
    ENRICH.parent.mkdir(parents=True, exist_ok=True)
    ENRICH.write_text(json.dumps(cache, indent=1))
    return cache


def t2_priority() -> list[dict]:
    """Ordering for the eventual v0.3.7 bulk decision (task §2.3): crosswalk demand FIRST,
    T0 centrality (corpus-internal citations) second. Demand is coverage-independent;
    centrality is not, so a row says which components it actually had."""
    demand = crosswalk_demand()
    recs = {r["doc_id"]: r for r in records()}
    internal = Counter()
    doi_owner = {}
    for d, r in recs.items():
        doi = ((r.get("work") or {}).get("doi") or "").replace("https://doi.org/", "").lower()
        if doi:
            doi_owner[doi] = d
    for d, r in recs.items():
        for ref in ((r.get("work") or {}).get("referenced_dois") or []):
            owner = doi_owner.get(ref.lower())
            if owner and owner != d:
                internal[owner] += 1
    out = []
    for d, r in recs.items():
        res = r.get("resolution")
        out.append({"doc_id": d, "crosswalk_demand": demand.get(d, 0),
                    "t0_centrality": internal.get(d, 0),
                    "t0_state": res, "biblio_method": biblio_method(r),
                    "centrality_measurable": res not in RETRYABLE})
    out.sort(key=lambda x: (-x["crosswalk_demand"], -x["t0_centrality"], x["doc_id"]))
    return out


def recompute(verbose: bool = True) -> dict:
    """Everything derived from T0. Called at the end of `resume` so provisional numbers
    upgrade themselves rather than going stale."""
    cov = coverage()
    prio = t2_priority()
    cands = coupling_candidates()
    PRIORITY.parent.mkdir(parents=True, exist_ok=True)
    PRIORITY.write_text(json.dumps(
        {"coverage": cov, "t2_priority": prio,
         # Provisional means "this number can still move", i.e. the harvest has work left.
         # It previously meant resolved < total, which counts the 134 documents no scholarly
         # index will ever hold — so the label was permanently "provisional" for a harvest
         # that had in fact finished.
         "provisional": cov["retryable"] > 0,
         "label": (f"provisional (T0 {cov['resolved_of_eligible']} eligible)"
                   if cov["retryable"] else
                   f"final (T0 {cov['resolved_of_eligible']} eligible; "
                   f"{cov['out_of_scope']} out of scope)")}, indent=1))
    _write_candidates(cands, cov)
    if verbose:
        print(json.dumps(cov, indent=1))
        state = "provisional" if cov["retryable"] else "final"
        print(f"\nt2_priority written to {PRIORITY.relative_to(_REPO)} "
              f"({state}: T0 {cov['resolved_of_eligible']} eligible, "
              f"{cov['out_of_scope']} out of scope)")
    return {"coverage": cov, "n_candidates": len(cands)}


def _write_candidates(cands: list[dict], cov: dict) -> None:
    """The candidate file is a DECISION record, not a queue (task 2026-08-30 §3): every row
    carries its disposition, and nothing is left pending at close."""
    from kg import refparse

    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    enr = load_enrichment()
    dec = evaluation_decisions()
    rp = refparse.records()
    derived_docs = sum(1 for r in rp if r.get("referenced_dois") or r.get("referenced_arxiv"))
    derived_ids = sum(len(r.get("referenced_dois") or []) + len(r.get("referenced_arxiv") or [])
                      for r in rp)
    strong = [c for c in cands if c["n_corpus_citers"] >= COUPLING_BAR]
    near = [c for c in cands if NEAR_MISS <= c["n_corpus_citers"] < COUPLING_BAR]
    tail = [c for c in cands if c["n_corpus_citers"] < NEAR_MISS]

    def _oa(c) -> tuple[str, str]:
        e = enr.get(f"{c['id_type']}:{c['id']}") or {}
        status = e.get("oa_status") or ("unknown" if e.get("resolution") != "resolved"
                                        else "unknown")
        if e.get("pdf_url"):
            fetch = f"fetchable ([pdf]({e['pdf_url']}))"
        elif e.get("resolution") == "provider_error":
            fetch = "unknown (provider error)"
        else:
            fetch = "`manual_download_needed`"
        return status, fetch

    L = ["# Acquisition candidates (T0 coupling expansion)", "",
         f"**{'PROVISIONAL' if cov['retryable'] else 'FINAL'} — T0 "
         f"{cov['resolved_of_eligible']} eligible documents "
         f"({cov['out_of_scope']} out of scope).** "
         f"Generated by `python -m kg.biblio recompute`; regenerated automatically whenever "
         f"the harvest or the reference parse advances. Do not hand-edit.", "",
         "Non-corpus works ranked by how many corpus members cite them (bibliographic "
         "coupling to the corpus, Kessler 1963).", "",
         "## Evidence base — two classes, never pooled", "",
         "| class | what asserts it | documents with a reference list | identifiers |",
         "|---|---|---|---|",
         f"| `bibliographic` | a third-party scholarly index | {cov['docs_with_references']} "
         f"of {cov['total']} | {cov['referenced_dois']} DOIs |",
         f"| `bibliographic_derived` | our regex over the document's own printed "
         f"bibliography (`kg.refparse`, `derivation: docling_refparse`) | {derived_docs} "
         f"of {cov['total']} | {derived_ids} DOIs + arXiv ids |", "",
         "The two are reported separately because they fail differently: an index record can "
         "be wrong about a document, a parse can be wrong about a page. The union column "
         "counts citing DOCUMENTS, which is the quantity coupling is defined over.", "",
         f"## Disposition — bar is >= {COUPLING_BAR} corpus citers", "",
         f"- **{len(strong)}** at or above the bar, reviewed individually against the "
         f"standing R1-R5 rules ({sum(1 for c in strong if c.get('held_title_match'))} of "
         f"them already held under another identifier).",
         f"- **{len(near)}** near-miss at {NEAR_MISS} citers. "
         f"{sum(1 for c in near if dec.get(c['id_type'] + ':' + c['id']))} were reached "
         f"individually by the round-2 evaluation and carry its clause; the rest are cut "
         f"`below_coupling_bar` and reopen if reference coverage rises.",
         f"- **{len(tail)}** at 1 citer — **cut** unreviewed with reason "
         f"`below_coupling_bar`. Coupling at one citer is not coupling; it is a single "
         f"document's bibliography.", "",
         "An ADMITTED work leaves this list: its identifier is then held, so it is no "
         "longer a non-corpus work. Rows below therefore show cuts and already-held "
         "duplicates only — the admissions are in `corpus/manifest.json`.", "",
         "**Nothing here is auto-admitted**: candidates are a reviewed list and the "
         "operator's admission rules still gate entry.", ""]
    if not strong:
        top = cands[0]["n_corpus_citers"] if cands else 0
        L += [f"### No candidate reaches the >= {COUPLING_BAR} corpus-citer bar", "",
              f"Highest observed: **{top}** citers, over "
              f"{cov['docs_with_references'] + derived_docs} documents with a reference list "
              f"of either class. The bar is not lowered to manufacture a list.", ""]
    def _row(i, c):
        e = enr.get(f"{c['id_type']}:{c['id']}") or {}
        status, fetch = _oa(c)
        ident = (f"`{c['id']}`" if c["id_type"] == "doi" else f"`arXiv:{c['id']}`")
        d = dec.get(f"{c['id_type']}:{c['id']}")
        if c.get("held_title_match"):
            disp = f"**already held** as `{c['held_title_match']}`"
        elif d and d["verdict"] == "fetch":
            disp = f"**ADMITTED** as `{d['doc_id']}` ({d['clause']})"
        elif d:
            disp = f"cut — `{d['clause']}`"
        else:
            disp = "cut — `below_coupling_bar`"
        return (f"| {i} | {ident} | {(e.get('title') or '—')[:64]} | "
                f"{c['n_corpus_citers']} ({c['n_citers_bibliographic']} / "
                f"{c['n_citers_derived']}) | {status} | {fetch} | {disp} | "
                f"{', '.join(f'`{x}`' for x in c['citers'][:3])} |")

    hdr = ["| rank | candidate | title | citers (biblio / derived) | OA | fetch | "
           "disposition | cited by |", "|---|---|---|---|---|---|---|---|"]
    L += [f"## At or above the bar ({COUPLING_BAR}+ citers)", ""] + hdr
    for i, c in enumerate(strong, 1):
        L.append(_row(i, c))
    if not strong:
        L.append("| — | *(none)* | — | — | — | — | — | — |")
    L += ["", f"## Near-miss tier ({NEAR_MISS} citers)", "",
          "Below the review bar. Every row still carries a disposition: rows the round-2 "
          "evaluation reached individually show the standing-rule clause they were decided "
          "on; the remainder are cut `below_coupling_bar`.", ""] + hdr
    for i, c in enumerate(near, 1):
        L.append(_row(i, c))
    if not near:
        L.append("| — | *(none)* | — | — | — | — | — | — |")
    L += ["", f"## Cut tail (1 citer): {len(tail)} works", "",
          "Not enumerated: a single citer is one document's bibliography, and the list would "
          "be a copy of it. The identifiers survive in `state/refparse/*.json` and "
          "`state/biblio_cache/*.json`, so the tail regenerates if the bar or the coverage "
          "changes.", ""]
    CANDIDATES.write_text("\n".join(L) + "\n", encoding="utf-8")


def resume(limit: int = 0) -> int:
    script = _REPO / "scripts" / "t0_biblio_harvest.py"
    cmd = [sys.executable, str(script), "--retry-unresolved"]
    if limit:
        cmd += ["--limit", str(limit)]
    print(f"$ {' '.join(cmd[1:])}", flush=True)
    r = subprocess.run(cmd, cwd=_REPO)
    if r.returncode != 0:
        print(f"harvest exited {r.returncode}; recomputing on what landed anyway")
    recompute()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m kg.biblio")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("coverage")
    p_r = sub.add_parser("resume")
    p_r.add_argument("--limit", type=int, default=0)
    sub.add_parser("recompute")
    a = ap.parse_args(argv)
    if a.cmd == "coverage":
        print(json.dumps(coverage(), indent=1)); return 0
    if a.cmd == "recompute":
        recompute(); return 0
    return resume(a.limit)


if __name__ == "__main__":
    raise SystemExit(main())
