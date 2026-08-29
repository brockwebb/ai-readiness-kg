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
RETRYABLE = {"harvest_error", None}
#: A finding: every provider answered and none had a record.
FINDING = "bibliographic_partial"


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
    if res in RETRYABLE:
        return "unresolved:provider_unavailable"
    if res == FINDING:
        return "unresolved:no_record_at_source"
    return f"{res}@{rec.get('metadata_source') or 'unknown'}"


def coverage() -> dict:
    recs = records()
    by_res = Counter(r.get("resolution") for r in recs)
    by_provider = Counter(r.get("metadata_source") for r in recs if r.get("metadata_source"))
    resolved = [r for r in recs if r.get("resolution") not in RETRYABLE | {FINDING}]
    blocked = blocked_docs()
    # Provider breakdown of the retryable pile: which provider is holding each one up.
    retry_by_provider = Counter()
    for r in recs:
        if r.get("resolution") in RETRYABLE:
            for e in (r.get("provider_errors") or []) or ["(none recorded)"]:
                retry_by_provider[e.split(":")[0]] += 1
    return {
        "total": len(recs),
        "resolved": len(resolved),
        "retryable": sum(v for k, v in by_res.items() if k in RETRYABLE),
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


def coupling_candidates() -> list[dict]:
    """Non-corpus works cited by >= N corpus members (task §2.2, bibliographic coupling —
    Kessler 1963). Quality is bounded by T0 coverage and the ranking is labelled with it."""
    recs = records()
    have_doi = {(r.get("work") or {}).get("doi", "").replace("https://doi.org/", "").lower()
                for r in recs if (r.get("work") or {}).get("doi")}
    cited_by = defaultdict(set)
    for r in recs:
        for d in ((r.get("work") or {}).get("referenced_dois") or []):
            d = d.lower()
            if d and d not in have_doi:
                cited_by[d].add(r["doc_id"])
    return sorted(({"doi": d, "n_corpus_citers": len(v), "citers": sorted(v)}
                   for d, v in cited_by.items()), key=lambda x: -x["n_corpus_citers"])


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
         "provisional": cov["resolved"] < cov["total"],
         "label": f"provisional (T0 coverage {cov['resolved']}/{cov['total']})"}, indent=1))
    _write_candidates(cands, cov)
    if verbose:
        print(json.dumps(cov, indent=1))
        print(f"\nt2_priority written to {PRIORITY.relative_to(_REPO)} "
              f"(provisional: T0 coverage {cov['resolved']}/{cov['total']})")
    return {"coverage": cov, "n_candidates": len(cands)}


def _write_candidates(cands: list[dict], cov: dict) -> None:
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    strong = [c for c in cands if c["n_corpus_citers"] >= 3]
    L = ["# Acquisition candidates (T0 coupling expansion)", "",
         f"**PROVISIONAL — T0 coverage {cov['resolved']}/{cov['total']} documents.** "
         f"Generated by `python -m kg.biblio resume`; regenerated automatically whenever the "
         f"harvest advances. Do not hand-edit.", "",
         f"Non-corpus works ranked by how many corpus members cite them (bibliographic "
         f"coupling to the corpus, Kessler 1963). Reference lists were available for "
         f"**{cov['docs_with_references']} of {cov['total']}** documents "
         f"({cov['referenced_dois']} referenced DOIs total), so this ranking rests on a "
         f"small fraction of the corpus and is not yet decision-grade.", "",
         "**Nothing here is auto-admitted** (task §2.2): candidates are a reviewed list and "
         "the operator's admission rules still gate entry.", ""]
    if not strong:
        L += [f"## No candidate reaches the >= 3 corpus-citer bar", "",
              f"Highest observed: **{cands[0]['n_corpus_citers'] if cands else 0}** citers. "
              f"With reference lists for only {cov['docs_with_references']} documents this is "
              f"the expected result and is a statement about coverage, not about the "
              f"literature. The bar is not lowered to manufacture a list.", ""]
    L += ["| rank | DOI | corpus citers | cited by |", "|---|---|---|---|"]
    for i, c in enumerate(cands[:40], 1):
        L.append(f"| {i} | `{c['doi']}` | {c['n_corpus_citers']} | "
                 f"{', '.join(f'`{x}`' for x in c['citers'][:4])} |")
    if not cands:
        L.append("| — | *(no referenced-DOI data yet)* | — | — |")
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
