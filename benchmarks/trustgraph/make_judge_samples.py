#!/usr/bin/env python3
"""TG benchmark v2 Phase 3 — fact generation + seeded judging samples for both sides
(task 2026-08-23_trustgraph_benchmark_v2). Zero model spend.

Facts (probe schema, deterministic only — both sides get identical model-free treatment):
node -> one fact per span_entailable literal attribute + one whole-field fact for the
primary text; edge -> one fact. Span-equivalents: ours = grounding_span; TG = the evidence
chunk with the highest token overlap with the fact text (their chunks impose no span
discipline — the verbatim-chunk rate is reported separately by the normalizer).
Sample: seeded (20260826) stratified by (side kept whole) × type family, 200 facts per side
(probe-n convention; judging every fact would breach the 8M ceiling — standing decision).
Outputs tg_side/our_side sample+facts files for probe_judge --prefix tgbench_{tg,ours}.
"""
from __future__ import annotations

import hashlib, json, random, re, sys, unicodedata
from collections import defaultdict, Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "benchmarks/trustgraph"))
from normalize_compare import tg_items, our_items, DOCS, PRIMARY, norm  # noqa: E402
from kg.extraction import schema_loader                                  # noqa: E402

SEED = 20260826
N = 200
MET = REPO / "corpus/staging/metrics"


def toks(t): return set(re.findall(r"[a-z0-9]+", norm(t)))


def best_chunk(fact_text: str, chunks: list[str]) -> str | None:
    ft = toks(fact_text); best = (0.0, None)
    for c in chunks:
        ct = toks(c)
        if not ct: continue
        r = len(ft & ct) / max(1, len(ft))
        if r > best[0]: best = (r, c)
    return best[1]


def facts_for(side: str, doc_id: str, schema) -> list[dict]:
    out = []
    if side == "tg":
        items, edges, meta = tg_items(doc_id)
        chunks = meta.get("chunk_texts") or []
        for it in items:
            se = schema_loader.span_entailable(schema, it["type"]) if it["type"] in schema["node_types"] else {}
            fields = [("__primary__", it["text"])] + [(k, v) for k, v in it["attrs"].items()
                                                     if se.get(k) and k != PRIMARY.get(it["type"])]
            for attr, val in fields:
                if not val: continue
                ft = f"{it['type']}: {val}" if attr == "__primary__" else f"{attr}: {val}"
                span = best_chunk(f"{it['text']} {val}", chunks)
                if not span: continue
                out.append({"attribute": None if attr == "__primary__" else attr, "fact_text": ft,
                            "span": span, "typ": it["type"], "ref": it["iri"]})
        for e in edges:
            ft = f"{e['from'].split('#')[-1]} {e['type']} {e['to'].split('#')[-1]}"
            span = best_chunk(ft, chunks)
            if span: out.append({"attribute": None, "fact_text": ft, "span": span, "typ": "edge", "ref": ft})
    else:
        items, edges, _q = our_items(doc_id)
        for it in items:
            se = schema_loader.span_entailable(schema, it["type"])
            out.append({"attribute": None, "fact_text": f"{it['type']}: {it['text']}",
                        "span": it["span"], "typ": it["type"], "ref": it["id"]})
            for k, v in it["attrs"].items():
                if se.get(k) and k != PRIMARY.get(it["type"]) and v:
                    out.append({"attribute": k, "fact_text": f"{k}: {v}", "span": it["span"],
                                "typ": it["type"], "ref": it["id"]})
        for e in edges:
            out.append({"attribute": None, "fact_text": f"{e['from']} {e['type']} {e['to']}",
                        "span": e["span"], "typ": "edge", "ref": f"{e['from']}|{e['type']}|{e['to']}"})
    for f in out:
        f["doc_id"] = doc_id
        f["fact_id"] = "tb_" + hashlib.sha1(f"{side}|{doc_id}|{f['ref']}|{f['fact_text']}".encode()).hexdigest()[:12]
    return out


def build(side: str, schema) -> dict:
    all_f = []
    for d in DOCS:
        all_f += facts_for(side, d, schema)
    fam = lambda f: ("edge" if f["typ"] == "edge" else ("Claim" if f["typ"] == "Claim" else "node"))
    by = defaultdict(list)
    for f in all_f: by[fam(f)].append(f)
    rng = random.Random(f"{SEED}:{side}")
    total = len(all_f); sample = []
    alloc = {k: max(10, round(N * len(v) / total)) for k, v in by.items()}
    while sum(alloc.values()) > N:
        k = max(alloc, key=alloc.get); alloc[k] -= 1
    for k, v in sorted(by.items()):
        pool = sorted(v, key=lambda f: f["fact_id"])
        sample += rng.sample(pool, min(alloc[k], len(pool)))
    pfx = f"tgbench_{side}"
    with (MET / f"{pfx}_sample.jsonl").open("w") as fs, (MET / f"{pfx}_facts.jsonl").open("w") as ff:
        for f in sample:
            fs.write(json.dumps({"item_id": f["ref"], "event_id": f["fact_id"], "kind": "node" if f["typ"] != "edge" else "edge",
                                 "type": f["typ"], "stratum": f"{side}:{fam(f)}", "text": f["fact_text"],
                                 "grounding_span": f["span"], "doc_id": f["doc_id"], "extra": {}, "window": None},
                                ensure_ascii=False) + "\n")
            ff.write(json.dumps({"fact_id": f["fact_id"], "item_id": f["ref"], "event_id": f["fact_id"],
                                 "attribute": f["attribute"], "fact_text": f["fact_text"], "source": "deterministic"},
                                ensure_ascii=False) + "\n")
    return {"side": side, "facts_total": total, "sampled": len(sample),
            "by_family": {k: len(v) for k, v in by.items()}, "alloc": alloc,
            "by_type": dict(Counter(f["typ"] for f in all_f))}


if __name__ == "__main__":
    schema = schema_loader.load_schema()
    for side in (sys.argv[1:] or ["tg", "ours"]):
        print(json.dumps(build(side, schema)))
