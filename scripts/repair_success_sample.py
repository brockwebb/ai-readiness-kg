#!/usr/bin/env python3
"""Whole-graph repair Phase 6 — pre-registered success-measure sample (task
2026-08-23_whole_graph_repair). 150 repaired items, seeded, stratified by repair type:
relocated_deterministic | relocated_model | attribute_nulled (nulled, not relocated).
Each item is written in the probe's sample format in its REPAIRED state (new span; nulled
attributes removed; window recomputed) so probe_decompose / probe_judge / probe_aggregate
run unchanged with --prefix repair_success."""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict, Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from kg import eventlog                                    # noqa: E402
from kg.extraction.grounding import normalize              # noqa: E402
from run_baseline_gates import live_events                 # noqa: E402
import run_bulk_extraction as rbe                          # noqa: E402

SEED = 20260823; N = 150
OUT = REPO / "corpus/staging/metrics/repair_success_sample.jsonl"
TEXT = {"Concept": "name", "Definition": "verbatim_text", "Claim": "claim_text", "Measure": "text", "Practice": "text",
        "Standard": "name", "Framework": "name", "Instrument": "name", "Tool": "name", "Platform": "name", "Construct": "name"}


def main() -> int:
    events = live_events(list(eventlog.replay()))
    reloc, nulls = {}, defaultdict(set)
    for ev in events:
        if ev.get("event_type") == "grounding_relocated" and ev.get("task", "").endswith("whole_graph_repair.md"):
            reloc[(ev["doc_id"], ev["item_id"])] = ("relocated_model" if ev["method"] == "model_assisted" else "relocated_deterministic", ev["new_span"])
        elif ev.get("event_type") == "attribute_nulled" and ev.get("task", "").endswith("whole_graph_repair.md"):
            nulls[(ev["doc_id"], ev["item_id"])].add(ev["attribute"])
    epoch_of = {}
    nodes = {}
    for ev in events:
        if ev.get("event_type") == "node_asserted":
            ep = (ev.get("provenance") or {}).get("corpus_epoch")
            if ep: epoch_of[ev["doc_id"]] = ep
            nodes[(ev["doc_id"], ev["payload"]["id"])] = ev
    strata = defaultdict(list)
    for key, (kind, span) in reloc.items():
        if key in nodes: strata[kind].append(key)
    for key in nulls:
        if key in nodes and key not in reloc: strata["attribute_nulled"].append(key)
    rng = random.Random(SEED)
    per = {k: N // 3 for k in ("relocated_deterministic", "relocated_model", "attribute_nulled")}
    per["attribute_nulled"] += N - sum(per.values())
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    texts = {}
    picked = []; counts = Counter()
    for kind, want in per.items():
        pool = sorted(strata[kind]); take = rng.sample(pool, min(want, len(pool)))
        for key in take:
            ev = nodes[key]; p = ev["payload"]; it = dict(p["item"])
            typ = p["type"]
            span = reloc[key][1] if key in reloc else it.get("grounding_span")
            for a in nulls.get(key, ()): it.pop(a, None)
            doc = key[0]
            if doc not in texts: texts[doc] = normalize(rbe.doc_text(members[doc]))
            nd = texts[doc]; k = nd.find(normalize(span)); window = nd[max(0, k - 400):k + len(normalize(span)) + 400] if k >= 0 else None
            picked.append({"item_id": p["id"], "event_id": ev["event_id"], "kind": "node", "type": typ,
                           "epoch": epoch_of.get(doc, "v1"), "stratum": kind, "repair_type": kind,
                           "text": it.get(TEXT.get(typ, "name")) or "", "grounding_span": span, "doc_id": doc,
                           "extra": {k2: v for k2, v in it.items() if k2 not in ("grounding_span", "location")},
                           "window": window, "nulled_attributes": sorted(nulls.get(key, ()))})
            counts[kind] += 1
    with OUT.open("w", encoding="utf-8") as f:
        for i in picked: f.write(json.dumps(i, ensure_ascii=False) + "\n")
    print({"pools": {k: len(v) for k, v in strata.items()}, "sampled": dict(counts), "total": len(picked), "seed": SEED})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
