#!/usr/bin/env python3
"""TEVV Phase 2 — test-retest re-extraction (task 2026-08-22_kernel_tevv).

Re-extracts the stability sample under the IDENTICAL model, prompt-template version and
schema version that produced each document's original extraction (read from the original
events, never assumed). Pinned copies of the historical template/schema live in
scripts/tevv_pins/ (exported from git at the commits that produced them; sha-verified here
against git). Everything the pipeline writes is routed to the tagged shard
events/batch-008_tevv_retest.jsonl with `purpose: tevv_retest` on every event, raw responses
to events/raw/tevv_retest/, per-doc metrics and proposed_relationships to tevv_retest/
subdirs — the originals are never overwritten and the graph never sees the retest.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog                                     # noqa: E402
from kg.extraction import model_stub, pipeline, state       # noqa: E402
from kg.extraction import metrics as metrics_mod, staging, schema_loader  # noqa: E402
import run_bulk_extraction as rbe                           # noqa: E402

SAMPLE = REPO / "corpus" / "staging" / "metrics" / "tevv_stability_sample.json"
TAG = "tevv_retest"
BATCH = 8
RAW_DIR = REPO / "events" / "raw" / TAG
PINS = REPO / "scripts" / "tevv_pins"
# prompt_version -> (pinned template, pinned schema, git commit the pins were exported from)
PIN_INDEX = {
    "0.2.0": ("prompt_template_0.2.0.md", "schema_0.2.yaml", "69ebfdc"),
    "0.3.0": ("prompt_template_0.3.0.md", "schema_0.3.yaml", "10e3d07"),
}
LOG = REPO / "docs" / "research" / "2026-08-22_tevv_retest_log.md"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def verify_pins() -> None:
    """Each pin must be byte-identical to the git object it claims to come from."""
    for pv, (tpl, sch, commit) in PIN_INDEX.items():
        for rel, name in (("kg/extraction/prompt_template.md", tpl), ("kg/schema.yaml", sch)):
            want = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=REPO,
                                  capture_output=True, text=True, check=True).stdout
            have = (PINS / name).read_text(encoding="utf-8")
            if want != have:
                raise SystemExit(f"FATAL: pin {name} differs from git {commit}:{rel}")


def original_provenance(doc_id: str) -> dict:
    """model_id / prompt_version / schema_version / corpus_epoch / source_sha256 of the LIVE
    original extraction, from its assertion events (fail loud if none)."""
    from run_baseline_gates import live_events
    for ev in live_events(list(eventlog.replay())):
        if ev.get("event_type") == "node_asserted" and ev["doc_id"] == doc_id:
            p = ev["provenance"]
            return {k: p.get(k) for k in ("model_id", "prompt_version", "schema_version",
                                           "corpus_epoch", "source_sha256")}
    raise SystemExit(f"FATAL: no live assertion events for {doc_id} — cannot pin its provenance")


def tagged_append(original_append):
    def _append(event: dict, batch: int, tag: str | None = None) -> str:
        return original_append({**event, "purpose": TAG}, BATCH, tag=TAG)
    return _append


def run(only: str | None, max_docs: int | None) -> int:
    model_stub.guard_no_api_key()
    verify_pins()
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))["stability"]
    if only:
        sample = [s for s in sample if s["doc_id"] == only]
    done = {ev["doc_id"] for ev in eventlog.replay(tag=TAG) if ev.get("event_type") == "build_metrics"}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    metrics_mod._METRICS_DIR = REPO / "corpus" / "staging" / "metrics" / TAG
    staging._REVIEW_DIR = REPO / "corpus" / "staging" / "proposed_relationships" / TAG
    eventlog.append = tagged_append(eventlog.append)      # route + flag every pipeline write
    state.EXTRACTION_BATCH = BATCH
    processed = 0
    for s in sample:
        if max_docs is not None and processed >= max_docs:
            break
        doc_id = s["doc_id"]
        if doc_id in done:
            print(f"  {doc_id}: already retested — skip"); continue
        prov = original_provenance(doc_id)
        pv = prov["prompt_version"]
        if pv not in PIN_INDEX:
            raise SystemExit(f"FATAL: no pinned template for prompt_version {pv!r} ({doc_id})")
        tpl, sch, commit = PIN_INDEX[pv]
        # Pin the template + schema the ORIGINAL run used (module globals, read at call time)
        model_stub._PROMPT_PATH = PINS / tpl
        schema_loader._SCHEMA_PATH = PINS / sch
        eventlog._SCHEMA_PATH = PINS / sch
        assert model_stub.prompt_version() == pv and eventlog.schema_version() == prov["schema_version"]
        cfg = model_stub.load_model_config()
        if cfg["model_id"] != prov["model_id"]:
            cfg = {**cfg, "model_id": prov["model_id"]}   # original model, not the current pin
        rbe.apply_profile({"v1": "v1", "kernel-v03": "kernel_v03"}[prov["corpus_epoch"]])
        path = rbe.corpus_members()[doc_id]
        text = rbe.doc_text(path)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != prov["source_sha256"]:
            raise SystemExit(f"FATAL: {doc_id} source sha changed since original extraction")
        print(f"  retest {doc_id} ({len(text):,} chars) under prompt {pv} / schema "
              f"{prov['schema_version']} / {cfg['model_id']} …", flush=True)
        t0 = time.time()
        meta = model_stub.invoke(doc_id, text, timeout=1800, config=cfg)
        wall = round(time.time() - t0, 1)
        raw = RAW_DIR / f"{doc_id}.{sha[:12]}.{pv}.{meta['model_id']}.retest.json"
        raw.write_text(json.dumps({"doc_id": doc_id, "purpose": TAG, "doc_sha256": sha,
                                   "prompt_version": pv, "schema_version": prov["schema_version"],
                                   "pins_commit": commit, "model_id": meta["model_id"],
                                   "usage": meta["usage"], "cost_usd": meta["cost_usd"],
                                   "duration_ms": meta["duration_ms"], "wall_s": wall,
                                   "ts": _now(), "raw_result": meta["raw_result"]},
                                  ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        summary = pipeline.extract_document(
            doc_id, text, output=meta["output"], model_meta=meta,
            extra_provenance={"corpus_epoch": prov["corpus_epoch"], "source_sha256": sha,
                              "retest_of_prompt_version": pv, "pins_commit": commit})
        m = summary["metrics"]
        tok = rbe.usage_tokens(meta)
        line = (f"| `{doc_id}` | {prov['corpus_epoch']} | {pv} / {prov['schema_version']} | "
                f"{len(text):,} | {wall} s | {tok:,} | {m['nodes']}n/{m['edges']}e/{m['quarantined']}q |")
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        print(f"    ok: {m['nodes']}n/{m['edges']}e/{m['quarantined']}q | {wall}s | {tok:,} tokens")
        processed += 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--max-docs", type=int, default=None)
    a = ap.parse_args()
    if not LOG.exists():
        LOG.write_text("# TEVV retest log\n\n| doc | epoch | prompt / schema | chars | wall | tokens | result |\n|---|---|---|---|---|---|---|\n", encoding="utf-8")
    return run(a.only, a.max_docs)


if __name__ == "__main__":
    raise SystemExit(main())
