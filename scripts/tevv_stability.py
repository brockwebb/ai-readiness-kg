#!/usr/bin/env python3
"""TEVV Phase 2 — stability metrics between an original extraction and its retest
(task 2026-08-22_kernel_tevv). Pure functions + a CLI that writes
docs/research/2026-08-22_tevv_stability.md and corpus/staging/metrics/tevv_stability.json.

Item identity (pre-registered): node = type + NFKC-normalized primary text; edge = type +
endpoint identities (each endpoint resolved to its node identity in the same run, so that a
run's arbitrary slug ids never enter the comparison).

Cohen's kappa on item presence: universe = union of the two runs' items. Presence vectors
have no both-absent cell, so kappa here is the chance-corrected agreement over the union —
recorded in dixie_evidence.yaml as a property of the statistic. Jaccard on grounded-span sets
(NFKC + whitespace-normalized). Prior art: Landis & Koch 1977 bands; Jaccard 1912.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

PRIMARY_TEXT = {"Concept": "name", "Definition": "verbatim_text", "Claim": "claim_text",
                "Measure": "text", "Practice": "text", "Standard": "name", "Framework": "name",
                "Instrument": "name", "Tool": "name", "Platform": "name", "Construct": "name"}
_WS = re.compile(r"\s+")


def norm(text: str) -> str:
    return _WS.sub(" ", unicodedata.normalize("NFKC", text or "")).strip().lower()


def node_identity(payload: dict) -> tuple[str, str]:
    typ = payload["type"]; item = payload.get("item") or {}
    text = item.get(PRIMARY_TEXT.get(typ, "name")) or item.get("name") or item.get("text") or ""
    return (typ, norm(text))


def run_items(events: list[dict], doc_id: str) -> tuple[set, set, set]:
    """(node identities, edge identities, normalized grounding spans) for one doc in one run."""
    ids: dict[str, tuple] = {}
    nodes, edges, spans = set(), set(), set()
    for ev in events:
        if ev.get("doc_id") != doc_id:
            continue
        if ev.get("event_type") == "node_asserted":
            p = ev["payload"]; nid = node_identity(p)
            ids[p["id"]] = nid; nodes.add(nid)
            span = (p.get("item") or {}).get("grounding_span")
            if span: spans.add(norm(span))
    for ev in events:
        if ev.get("doc_id") == doc_id and ev.get("event_type") == "edge_asserted":
            p = ev["payload"]
            a = ids.get(p.get("from_id"), ("Document", p.get("from_id"))) if p.get("from_id") != doc_id else ("Document", doc_id)
            b = ids.get(p.get("to_id"), ("Document", p.get("to_id"))) if p.get("to_id") != doc_id else ("Document", doc_id)
            edges.add((p.get("type"), a, b))
            span = (p.get("item") or {}).get("grounding_span") or p.get("grounding_span")
            if span: spans.add(norm(span))
    return nodes, edges, spans


def kappa_presence(a: set, b: set) -> float | None:
    """Cohen's kappa on presence over the union universe. None when the union is empty."""
    u = a | b
    if not u:
        return None
    n = len(u)
    both = len(a & b); only_a = len(a - b); only_b = len(b - a)
    po = both / n
    pa, pb = len(a) / n, len(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def positive_agreement(a: set, b: set) -> float | None:
    """Positive specific agreement = 2|A∩B| / (|A|+|B|) (Dice). The kappa-paradox remedy
    (Cicchetti & Feinstein 1990): with no both-absent cell, kappa is dominated by its
    chance term and goes negative even when overlap is substantial."""
    return (2 * len(a & b) / (len(a) + len(b))) if (a or b) else None


def jaccard(a: set, b: set) -> float | None:
    u = a | b
    return (len(a & b) / len(u)) if u else None


def compare_doc(orig: list[dict], retest: list[dict], doc_id: str) -> dict:
    on, oe, os_ = run_items(orig, doc_id)
    rn, re_, rs = run_items(retest, doc_id)
    per_type = {}
    for typ in sorted({t for t, _ in on | rn}):
        a = {x for x in on if x[0] == typ}; b = {x for x in rn if x[0] == typ}
        per_type[typ] = {"orig": len(a), "retest": len(b), "both": len(a & b),
                         "only_orig": len(a - b), "only_retest": len(b - a),
                         "kappa": kappa_presence(a, b), "jaccard": jaccard(a, b),
                         "positive_agreement": positive_agreement(a, b)}
    return {"doc_id": doc_id,
            "nodes": {"orig": len(on), "retest": len(rn), "both": len(on & rn),
                      "only_one_run": len(on ^ rn), "kappa": kappa_presence(on, rn),
                      "positive_agreement": positive_agreement(on, rn)},
            "edges": {"orig": len(oe), "retest": len(re_), "both": len(oe & re_),
                      "only_one_run": len(oe ^ re_), "kappa": kappa_presence(oe, re_),
                      "positive_agreement": positive_agreement(oe, re_)},
            "spans": {"orig": len(os_), "retest": len(rs), "jaccard": jaccard(os_, rs)},
            "per_type": per_type}


def pooled_from_events(orig: list[dict], retest: list[dict], doc_ids: list[str]) -> dict:
    A, B, EA, EB = set(), set(), set(), set()
    by_type: dict[str, tuple[set, set]] = defaultdict(lambda: (set(), set()))
    jac = []
    for d in doc_ids:
        on, oe, os_ = run_items(orig, d); rn, re_, rs = run_items(retest, d)
        A |= {(d,) + x for x in on}; B |= {(d,) + x for x in rn}
        EA |= {(d,) + x for x in oe}; EB |= {(d,) + x for x in re_}
        for x in on: by_type[x[0]][0].add((d,) + x)
        for x in rn: by_type[x[0]][1].add((d,) + x)
        j = jaccard(os_, rs)
        if j is not None: jac.append(j)
    per_type = {t: {"kappa": kappa_presence(a, b), "positive_agreement": positive_agreement(a, b),
                    "orig": len(a), "retest": len(b), "both": len(a & b)}
                for t, (a, b) in sorted(by_type.items())}
    return {"kappa_nodes_pooled": kappa_presence(A, B), "kappa_edges_pooled": kappa_presence(EA, EB),
            "kappa_all_items_pooled": kappa_presence(A | EA, B | EB),
            "positive_agreement_nodes_pooled": positive_agreement(A, B),
            "positive_agreement_edges_pooled": positive_agreement(EA, EB),
            "positive_agreement_all_items_pooled": positive_agreement(A | EA, B | EB),
            "jaccard_spans_mean": statistics.fmean(jac) if jac else None,
            "per_type": per_type}


def main() -> int:
    from kg import eventlog
    from run_baseline_gates import live_events
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="tevv_retest")
    ap.add_argument("--sample", default="corpus/staging/metrics/tevv_stability_sample.json")
    a = ap.parse_args()
    docs = [s["doc_id"] for s in json.loads((REPO / a.sample).read_text())["stability"]]
    orig = live_events(list(eventlog.replay()))
    retest = list(eventlog.replay(tag=a.tag))
    have = {ev["doc_id"] for ev in retest if ev.get("event_type") == "build_metrics"}
    docs = [d for d in docs if d in have]
    per_doc = [compare_doc(orig, retest, d) for d in docs]
    pool = pooled_from_events(orig, retest, docs)
    out = {"docs": per_doc, "pooled": pool, "n_docs": len(docs)}
    (REPO / "corpus/staging/metrics/tevv_stability.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(pool, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
