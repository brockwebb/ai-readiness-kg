#!/usr/bin/env python3
"""TrustGraph benchmark v2 — OUR side (task 2026-08-23_trustgraph_benchmark_v2 Phase 2).
Re-extract the 5 pilot documents with the pinned model + current prompt template into the
tagged shard events/batch-013_benchmark.jsonl (`purpose: benchmark`) — never the graph.
Mirrors tevv_retest mechanics (same pipeline, redirected staging/metrics), current schema."""
from __future__ import annotations

import datetime, hashlib, json, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from kg import eventlog
from kg.extraction import model_stub, pipeline, state, metrics as metrics_mod, staging
import run_bulk_extraction as rbe

DOCS = ["google-dataset-structured-data", "w3c-dwbp-2017",
        "aggarwal-2024-geo-generative-engine-optimization", "digital-gov-dap-guide",
        "cloudflare-ai-crawl-control"]
TAG, BATCH = "benchmark", 13
RAW = REPO / "events/raw/tgbench_ours"; RAW.mkdir(parents=True, exist_ok=True)
LOG = REPO / "docs/research/2026-08-23_tgbench2_ours_log.md"

orig_append = eventlog.append
def tagged(event, batch, tag=None):
    return orig_append({**event, "purpose": TAG}, BATCH, tag=TAG)
eventlog.append = tagged
state.EXTRACTION_BATCH = BATCH
metrics_mod._METRICS_DIR = REPO / "corpus/staging/metrics" / TAG
staging._REVIEW_DIR = REPO / "corpus/staging/proposed_relationships" / TAG

model_stub.guard_no_api_key()
rbe.apply_profile("kernel_v03"); members = rbe.corpus_members()
done = {ev["doc_id"] for ev in eventlog.replay(tag=TAG) if ev.get("event_type") == "build_metrics"}
if not LOG.exists():
    LOG.write_text("# tgbench v2 — our side\n\n| doc | chars | wall | tokens | n/e/q |\n|---|---|---|---|---|\n")
tot = 0
for d in DOCS:
    if d in done: print(d, "done"); continue
    text = rbe.doc_text(members[d]); sha = hashlib.sha256(members[d].read_bytes()).hexdigest()
    t0 = time.time(); meta = model_stub.invoke(d, text, timeout=1800)
    wall = round(time.time() - t0, 1); tok = rbe.usage_tokens(meta); tot += tok
    (RAW / f"{d}.{sha[:12]}.{model_stub.prompt_version()}.{meta['model_id']}.json").write_text(
        json.dumps({"doc_id": d, "purpose": TAG, "usage": meta["usage"], "cost_usd": meta["cost_usd"],
                    "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n")
    s = pipeline.extract_document(d, text, output=meta["output"], model_meta=meta,
                                  extra_provenance={"corpus_epoch": "benchmark", "source_sha256": sha})
    m = s["metrics"]
    with LOG.open("a") as fh:
        fh.write(f"| `{d}` | {len(text):,} | {wall}s | {tok:,} | {m['nodes']}/{m['edges']}/{m['quarantined']} |\n")
    print(f"{d}: {m['nodes']}n/{m['edges']}e/{m['quarantined']}q {wall}s {tok:,}tok", flush=True)
print("total tokens", tot)
