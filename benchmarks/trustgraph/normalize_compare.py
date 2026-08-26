#!/usr/bin/env python3
"""TG benchmark v2 Phase 3 — normalize both sides to the probe fact schema and compute
coverage R (task 2026-08-23_trustgraph_benchmark_v2). Zero model spend.

TrustGraph side: keep triples whose predicate or object class lives in our schema namespace
(AIRKG = https://brockwebb.github.io/ai-readiness-kg/schema#). Entities typed with an AIRKG
class become items; AIRKG datatype properties become attribute facts; AIRKG object
properties become edge facts. Evidence = the chunk with the highest token-overlap with the
fact text (TG imposes no span discipline; we measure their chunks' verbatim-substring rate
against the source separately). Our side: the tagged benchmark shard, probe fact schema via
the probe decomposer conventions (deterministic facts for literals; free text kept whole —
one fact — so both sides get the same, model-free treatment here).

R = |TG items matched to our items| / |our items|, matching by type + normalized-text
similarity >= 0.8 (difflib ratio on primary text). Reported against admitted-only (the
pre-registered base) AND admitted+quarantined (context: the span-coverage gate flipped on
2026-08-23 shrinks our admitted set).
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from kg import eventlog                                   # noqa: E402
from kg.extraction.grounding import normalize             # noqa: E402
import run_bulk_extraction as rbe                         # noqa: E402

NS = "https://brockwebb.github.io/ai-readiness-kg/schema#"
EXTRACT_DIR = REPO / "benchmarks/trustgraph/extractions"
OUT = REPO / "corpus/staging/metrics/tgbench2_normalized.json"
DOCS = ["google-dataset-structured-data", "w3c-dwbp-2017",
        "aggarwal-2024-geo-generative-engine-optimization", "digital-gov-dap-guide",
        "cloudflare-ai-crawl-control"]
PRIMARY = {"Concept": "name", "Definition": "verbatim_text", "Claim": "claim_text", "Measure": "text",
           "Practice": "text", "Standard": "name", "Framework": "name", "Instrument": "name",
           "Tool": "name", "Platform": "name", "Construct": "name"}


def norm(t): return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t or "")).strip().lower()


def tg_items(doc_id: str) -> tuple[list[dict], list[dict], dict]:
    p = EXTRACT_DIR / f"{doc_id}.json"
    if not p.is_file():
        return [], [], {}
    d = json.loads(p.read_text())
    # two export generations: doc-1's original 'triples' ({s:{t,i},...}) and the final
    # 'quads' (flat s/p/o + otype). Normalize to (si, pi, o_iri|o_lit) rows.
    rows = []
    for t in (d.get("triples") or []):
        rows.append((t["s"].get("i"), t["p"].get("i") or "",
                     t["o"].get("i") if t["o"].get("t") == "i" else None,
                     t["o"].get("v") if t["o"].get("t") == "l" else None))
    for q in (d.get("quads") or []):
        rows.append((q.get("s"), q.get("p") or "",
                     q.get("o") if q.get("otype") in ("u", "i") else None,
                     q.get("o") if q.get("otype") == "l" else None))
    chunks = d.get("chunks") or []
    chunk_texts = [c.get("text") or c.get("chunk") or "" for c in chunks] if chunks else []
    typed, label, attrs, edges = {}, {}, defaultdict(dict), []
    for si, pi, o_iri, o_lit in rows:
        if pi == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" and (o_iri or "").startswith(NS):
            typed[si] = o_iri[len(NS):]
        elif pi == "http://www.w3.org/2000/01/rdf-schema#label" and o_lit is not None:
            label[si] = o_lit
        elif pi.startswith(NS):
            attr = pi[len(NS):]
            if o_lit is not None:
                attrs[si][attr] = o_lit
            else:
                edges.append({"from": si, "type": attr, "to": o_iri})
    items = []
    for iri, typ in typed.items():
        if typ == "Document":
            continue
        text = label.get(iri) or attrs[iri].get(PRIMARY.get(typ, "name")) or (iri.split("#")[-1] if iri else "")
        items.append({"iri": iri, "type": typ, "text": text, "attrs": attrs[iri]})
    ed = [e for e in edges if e["from"] in typed and e["to"] in typed]
    return items, ed, {"chunk_texts": chunk_texts,
                       "triple_count": d.get("triple_count") or d.get("quad_count_store"),
                       "chunk_count": d.get("chunk_count")}


def our_items(doc_id: str) -> tuple[list[dict], list[dict], int]:
    items, edges, quarantined = [], [], 0
    for ev in eventlog.replay(tag="benchmark"):
        if ev.get("doc_id") != doc_id:
            continue
        if ev.get("event_type") == "node_asserted":
            p = ev["payload"]; it = p["item"]
            items.append({"id": p["id"], "type": p["type"],
                          "text": it.get(PRIMARY.get(p["type"], "name")) or it.get("name") or "",
                          "attrs": {k: v for k, v in it.items() if k not in ("grounding_span", "location")},
                          "span": it.get("grounding_span")})
        elif ev.get("event_type") == "edge_asserted":
            p = ev["payload"]; edges.append({"from": p["from_id"], "type": p["type"], "to": p["to_id"],
                                             "span": (p.get("item") or {}).get("grounding_span") or p.get("grounding_span")})
        elif ev.get("event_type") == "build_metrics":
            quarantined = ev["metrics"]["quarantined"]
    return items, edges, quarantined


def match_rate(tg: list[dict], ours: list[dict]) -> tuple[int, list]:
    matched, pairs = 0, []
    for o in ours:
        best = (0.0, None)
        for t in tg:
            if t["type"] != o["type"]:
                continue
            r = difflib.SequenceMatcher(None, norm(o["text"]), norm(t["text"])).ratio()
            if r > best[0]:
                best = (r, t)
        if best[0] >= 0.8:
            matched += 1; pairs.append({"ours": o["text"][:60], "tg": best[1]["text"][:60], "ratio": round(best[0], 3)})
    return matched, pairs


def main() -> int:
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    out = {"docs": {}, "notes": "R base = our ADMITTED items (pre-registered); "
                               "R_incl_quarantined shown as context (span-coverage gate shrank admitted set)"}
    for d in DOCS:
        tg_i, tg_e, meta = tg_items(d)
        our_i, our_e, q = our_items(d)
        if not tg_i and not meta:
            out["docs"][d] = {"tg": "not extracted"}
            continue
        m, pairs = match_rate(tg_i, our_i)
        src = normalize(rbe.doc_text(members[d]))
        verbatim = sum(1 for c in meta["chunk_texts"] if c and normalize(c) in src)
        out["docs"][d] = {
            "tg": {"items": len(tg_i), "edges": len(tg_e), "triples": meta.get("triple_count") or meta.get("quad_count"),
                   "chunks": meta.get("chunk_count"),
                   "chunk_verbatim_rate": (verbatim / len(meta["chunk_texts"])) if meta["chunk_texts"] else None,
                   "types": dict(Counter(i["type"] for i in tg_i))},
            "ours": {"items": len(our_i), "edges": len(our_e), "quarantined": q,
                     "types": dict(Counter(i["type"] for i in our_i))},
            "R": (m / len(our_i)) if our_i else None,
            "R_incl_quarantined": (m / (len(our_i) + q)) if (our_i or q) else None,
            "matched": m, "sample_pairs": pairs[:8]}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for d, v in out["docs"].items():
        if not isinstance(v, dict) or "R" not in v:
            print(d[:44], "tg: not extracted"); continue
        print(d[:44], f"R={v['R']} matched={v['matched']} tg={v['tg']['items']} ours={v['ours']['items']}(+{v['ours']['quarantined']}q)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
