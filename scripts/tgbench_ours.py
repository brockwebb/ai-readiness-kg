#!/usr/bin/env python3
"""TrustGraph benchmark v2 — OUR side (task 2026-08-23_trustgraph_benchmark_v2 Phase 2).
Re-extract the 5 pilot documents with the pinned model + current prompt template into the
tagged shard events/batch-013_benchmark.jsonl (`purpose: benchmark`) — never the graph.
Mirrors tevv_retest mechanics (same pipeline, redirected staging/metrics), current schema."""
from __future__ import annotations

import argparse, datetime, hashlib, json, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from kg import eventlog, spend
from kg.extraction import model_stub, pipeline, state, metrics as metrics_mod, staging
import run_bulk_extraction as rbe

# DD-022: the v2 run consumed 8.11M against an 8M ceiling because the check ran after each
# call returned. The ceiling is now declared on the shared ledger and enforced preemptively
# at the model-stub choke point. (The TrustGraph-side backend lives in the trustgraph fork
# and does not dispatch through this repo's stub — reported in the task RESULT.)
_ap = argparse.ArgumentParser()
_ap.add_argument("--ceiling-tokens", type=int, required=True,
                 help="per-run token ceiling from the task file (required; no default)")
_ap.add_argument("--run-id", default=None)
_args = _ap.parse_args()
_run_id = _args.run_id or spend.default_run_id("tgbench-ours")
spend.default_ledger().declare(_run_id, _args.ceiling_tokens,
                               declared_by="scripts/tgbench_ours.py", call_class="extraction")
spend.set_current_run(_run_id)

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
    t0 = time.time()
    try:
        meta = model_stub.invoke(d, text, timeout=1800)
    except spend.SpendRefusalStop as exc:
        print(f"spend guard: {exc} — clean stop", flush=True)
        break
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
_rec = spend.default_ledger().reconcile(_run_id)
print(f"spend reconcile [{_run_id}]: {'OK' if _rec['ok'] else 'MISMATCH'} "
      f"settled {_rec['settled_total']:,} vs model_call {_rec['model_call_total']:,}")
