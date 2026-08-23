#!/usr/bin/env python3
"""Whole-graph repair Phase 4 — attribute nulling (task 2026-08-23_whole_graph_repair).
Zero spend. For every repair_filled_attr.jsonl entry: if the item's CURRENT span (after any
grounding_relocated overlay) still does not carry the attribute value, emit an
`attribute_nulled` overlay (reason unsupported_by_span) to events/batch-011.jsonl. Entries
whose item is still awaiting model relocation (on the Phase 3 worklist with neither a
grounding_relocated nor a span_unrepairable event) are DEFERRED, since the span may still
change. Idempotent: existing (item, attribute) nulls are skipped."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from kg import eventlog                         # noqa: E402
from kg.extraction.grounding import normalize   # noqa: E402

WORK = REPO / "corpus/staging/metrics/repair_filled_attr.jsonl"
P3 = REPO / "corpus/staging/metrics/repair_phase3_worklist.jsonl"
OUT = REPO / "corpus/staging/metrics/repair_null_summary.json"
BATCH = 11
TASK = "cc_tasks/2026-08-23_whole_graph_repair.md"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    relocated, settled, nulled = {}, set(), set()
    for ev in eventlog.replay():
        et = ev.get("event_type"); key = (ev.get("doc_id"), ev.get("item_id"))
        if et == "grounding_relocated": relocated[key] = ev["new_span"]; settled.add(key)
        elif et == "span_unrepairable": settled.add(key)
        elif et == "attribute_nulled": nulled.add((key[0], key[1], ev["attribute"]))
    pending = {(json.loads(l)["doc_id"], json.loads(l)["item_id"]) for l in P3.read_text().splitlines() if l.strip()} - settled
    counts = Counter(); by_attr = Counter()
    for l in WORK.read_text(encoding="utf-8").splitlines():
        if not l.strip(): continue
        w = json.loads(l); key = (w["doc_id"], w["item_id"])
        if (key[0], key[1], w["attribute"]) in nulled: counts["already_nulled"] += 1; continue
        if key in pending: counts["deferred_pending_relocation"] += 1; continue
        span = relocated.get(key)
        if span is not None:
            ns = normalize(span); vals = w["value"] if isinstance(w["value"], list) else [w["value"]]
            if all(normalize(str(v)) in ns for v in vals):
                counts["resolved_by_relocation"] += 1; continue
        counts["nulled"] += 1; by_attr[w["attribute"]] += 1
        if not a.dry_run:
            eventlog.append({"event_type": "attribute_nulled", "doc_id": w["doc_id"], "target_event_id": w["event_id"],
                             "item_id": w["item_id"], "attribute": w["attribute"], "old_value": w["value"],
                             "reason": "unsupported_by_span", "task": TASK}, batch=BATCH)
    out = {**counts, "nulled_by_attribute": dict(by_attr), "dry_run": a.dry_run}
    OUT.write_text(json.dumps(out, indent=1) + "\n"); print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
