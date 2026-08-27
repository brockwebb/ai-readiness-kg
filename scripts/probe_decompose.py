#!/usr/bin/env python3
"""Probe Phase 2 — atomic decomposition (task 2026-08-22_faithfulness_probe).

Hybrid, recorded as a standing decision: attributes whose value is a short literal (name,
steward, owner, year, version, operator, license, url, response_type, term, aliases) become
one deterministic fact each — "<attr> is <value>" — with no model call; free-text fields
(claim_text, verbatim_text, text, description, method, measurement_notes) are split into
propositions by the pinned model via kg/extraction/decompose_template.md (batched, versioned,
stamped). Edges decompose to exactly one fact "<from> <rel> <to>". Facts are generated only for
span_entailable: true attributes (schema v0.3.2). Output corpus/staging/metrics/probe_facts.jsonl.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg.extraction import model_stub, schema_loader  # noqa: E402

PREFIX = "probe"      # --prefix: reuse the protocol on another sample (e.g. repair success measure)
SAMPLE = REPO / "corpus/staging/metrics/probe_sample.jsonl"
OUT = REPO / "corpus/staging/metrics/probe_facts.jsonl"
RAW_DIR = REPO / "events/raw/probe_decompose"


def set_prefix(prefix: str) -> None:
    global PREFIX, SAMPLE, OUT, RAW_DIR
    PREFIX = prefix
    SAMPLE = REPO / f"corpus/staging/metrics/{prefix}_sample.jsonl"
    OUT = REPO / f"corpus/staging/metrics/{prefix}_facts.jsonl"
    RAW_DIR = REPO / f"events/raw/{prefix}_decompose"
TEMPLATE = REPO / "kg/extraction/decompose_template.md"
FREE_TEXT = {"claim_text", "verbatim_text", "text", "description", "method", "measurement_notes"}
BATCH = 8


def decompose_version() -> str:
    for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*decompose_version:\s*(\S+)", line)
        if m:
            return m.group(1)
    raise model_stub.ModelConfigError("no decompose_version header")


def fact_id(item_id: str, attr: str, text: str) -> str:
    return "f_" + hashlib.sha1(f"{item_id}|{attr}|{text}".encode()).hexdigest()[:12]


def deterministic_facts(item: dict, se: dict) -> tuple[list[dict], list[tuple[str, str]]]:
    """(facts, pending free-text (attr, value) pairs for the model)."""
    facts, pending = [], []
    if item["kind"] == "edge":
        x = item["extra"]
        facts.append({"attribute": None, "fact_text": f"{x['from_id']} {x['edge_type']} {x['to_id']}"})
        return facts, pending
    for attr, val in (item.get("extra") or {}).items():
        if not se.get(attr) or val in (None, "", [], {}):
            continue
        if attr in FREE_TEXT:
            pending.append((attr, str(val)))
        elif isinstance(val, list):
            for v in val:
                facts.append({"attribute": attr, "fact_text": f"{attr}: {v}"})
        else:
            facts.append({"attribute": attr, "fact_text": f"{attr}: {val}"})
    return facts, pending


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prefix", default="probe"); a = ap.parse_args(); set_prefix(a.prefix)
    model_stub.guard_no_api_key()
    schema = schema_loader.load_schema(); dv = decompose_version(); cfg = model_stub.load_model_config()
    items = [json.loads(l) for l in SAMPLE.read_text(encoding="utf-8").splitlines() if l.strip()]
    done = set()
    if OUT.exists():
        # (item_id, event_id) pairs: an item is done only if THIS sample's event_id already
        # has facts. Was a set of item_ids alone, which made the `event_id in done` half of
        # the resume test always false — a relaunch re-decomposed every item and appended a
        # second copy of the fact set (2026-08-27, pilot_instrB).
        done = {(r["item_id"], r["event_id"]) for r in
                (json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip())}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    n_det = n_model = 0
    out = OUT.open("a", encoding="utf-8")
    model_queue: list[tuple[dict, str, str]] = []
    for it in items:
        if (it["item_id"], it["event_id"]) in done:
            continue
        se = schema_loader.span_entailable(schema, it["type"]) if it["kind"] == "node" else {}
        facts, pending = deterministic_facts(it, se)
        for f in facts:
            rec = {"fact_id": fact_id(it["event_id"], f["attribute"] or "", f["fact_text"]),
                   "item_id": it["item_id"], "event_id": it["event_id"], "attribute": f["attribute"],
                   "fact_text": f["fact_text"], "source": "deterministic", "decompose_version": dv}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n"); n_det += 1
        for attr, val in pending:
            model_queue.append((it, attr, val))
    out.flush()
    print(f"deterministic facts: {n_det}; free-text fields for the model: {len(model_queue)}")
    if a.dry_run:
        return 0
    tpl = TEMPLATE.read_text(encoding="utf-8")
    for b in range(0, len(model_queue), BATCH):
        batch = model_queue[b:b + BATCH]
        payload = [{"item_id": f"{it['event_id']}::{attr}", "type": it["type"], "field": attr, "text": val}
                   for it, attr, val in batch]
        prompt = tpl.replace("{{items_json}}", json.dumps(payload, ensure_ascii=False, indent=1))
        meta = model_stub.invoke(f"decompose:{b}", "", prompt=prompt, timeout=300, config=cfg)
        (RAW_DIR / f"batch_{b:04d}.{dv}.{cfg['model_id']}.json").write_text(
            json.dumps({"batch": b, "usage": meta["usage"], "cost_usd": meta["cost_usd"],
                        "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        got = meta["output"].get("facts") or []
        by_key = {f"{it['event_id']}::{attr}": (it, attr, val) for it, attr, val in batch}
        covered = set()
        for f in got:
            key = f.get("item_id"); tup = by_key.get(key)
            if not tup or not f.get("fact_text"):
                continue
            it, attr, _ = tup; covered.add(key)
            rec = {"fact_id": fact_id(it["event_id"], attr, f["fact_text"]), "item_id": it["item_id"],
                   "event_id": it["event_id"], "attribute": attr, "fact_text": f["fact_text"],
                   "source": "model", "decompose_version": dv, "model_id": cfg["model_id"]}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n"); n_model += 1
        for key, (it, attr, val) in by_key.items():
            if key not in covered:   # model dropped it: fall back to the whole field as one fact
                rec = {"fact_id": fact_id(it["event_id"], attr, val), "item_id": it["item_id"],
                       "event_id": it["event_id"], "attribute": attr, "fact_text": val,
                       "source": "fallback_whole_field", "decompose_version": dv}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n"); n_model += 1
        out.flush()
        print(f"  batch {b // BATCH + 1}/{(len(model_queue) + BATCH - 1) // BATCH}: {len(got)} facts", flush=True)
    out.close()
    print(f"facts written: deterministic {n_det}, model {n_model}, total {n_det + n_model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
