#!/usr/bin/env python3
"""Probe Phase 7 — repair path on PROBE ITEMS ONLY (task 2026-08-22_faithfulness_probe).

Reads probe_aggregate.json (MAP class per fact) and, per item:
  - class span_truncated / subject_dropped -> deterministic re-location: exact or
    NFKC-normalized substring search of the item's text attribute in the document text.
    Success -> `grounding_relocated` overlay event {doc_id, event_id, item_id, old_span,
    new_span, method}. Failure -> counted, left as is.
  - class filled_attribute -> `attribute_nulled` overlay event {doc_id, event_id, item_id,
    attribute, old_value, reason: unsupported_by_span} for each unsupported attribute.
Overlays are graph events (untagged shard batch-010), applied LAST by build_projection.py;
the original assertion events are never mutated. Strata flagged reextract_required are
skipped. Writes corpus/staging/metrics/probe_repair.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog                                   # noqa: E402
from kg.extraction.grounding import normalize, COVERAGE_ATTRIBUTES, covers  # noqa: E402
import run_bulk_extraction as rbe                         # noqa: E402

AGG = REPO / "corpus/staging/metrics/probe_aggregate.json"
SAMPLE = REPO / "corpus/staging/metrics/probe_sample.jsonl"
FACTS = REPO / "corpus/staging/metrics/probe_facts.jsonl"
OUT = REPO / "corpus/staging/metrics/probe_repair.json"
OVERLAY_BATCH = 10     # events/batch-010.jsonl — probe repair overlays (graph shard)
TASK = "cc_tasks/2026-08-22_faithfulness_probe.md"
RELOCATE_CLASSES = {"span_truncated", "subject_dropped"}


def find_span(item_text: str, doc_text: str) -> tuple[str, str] | None:
    """Exact match first, then NFKC/whitespace-normalized; returns (new_span, method)."""
    if item_text in doc_text:
        return item_text, "exact"
    nt, ni = normalize(doc_text), normalize(item_text)
    k = nt.find(ni)
    if k >= 0:
        return nt[k:k + len(ni)], "nfkc_normalized"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    agg = json.loads(AGG.read_text())
    skip_strata = {s for s, v in agg["verdicts"].items() if v == "reextract_required"}
    items = {it["event_id"]: it for it in (json.loads(l) for l in SAMPLE.read_text().splitlines() if l.strip())}
    facts = {f["fact_id"]: f for f in (json.loads(l) for l in FACTS.read_text().splitlines() if l.strip())}
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    texts: dict[str, str] = {}
    by_item: dict[str, list] = defaultdict(list)
    for fid, v in agg["per_fact"].items():
        by_item[v["event_id"]].append((fid, v))
    counts = Counter(); relocated, nulled, failed = [], [], []
    for eid, fvs in by_item.items():
        it = items[eid]
        if it["stratum"] in skip_strata:
            counts["skipped_reextract_stratum"] += 1; continue
        classes = {v["class"] for _, v in fvs if v["class"]}
        if classes & RELOCATE_CLASSES and it["kind"] == "node":
            text_attr = next((a for a in COVERAGE_ATTRIBUTES if isinstance(it["extra"].get(a), str) and it["extra"][a].strip()), None)
            if text_attr and not covers(it["grounding_span"], it["extra"][text_attr]):
                doc = it["doc_id"]
                if doc not in texts: texts[doc] = rbe.doc_text(members[doc])
                hit = find_span(it["extra"][text_attr], texts[doc])
                if hit:
                    new_span, method = hit
                    relocated.append({"event_id": eid, "item_id": it["item_id"], "doc_id": doc, "attribute": text_attr,
                                      "old_span": it["grounding_span"], "new_span": new_span, "method": method})
                else:
                    failed.append({"event_id": eid, "item_id": it["item_id"], "doc_id": doc, "attribute": text_attr,
                                   "reason": "item text not found in document text"})
            else:
                counts["relocate_not_applicable"] += 1
        if "filled_attribute" in classes and it["kind"] == "node":
            for fid, v in fvs:
                if v["class"] == "filled_attribute" and facts[fid].get("attribute") and facts[fid]["attribute"] not in COVERAGE_ATTRIBUTES:
                    attr = facts[fid]["attribute"]
                    nulled.append({"event_id": eid, "item_id": it["item_id"], "doc_id": it["doc_id"], "attribute": attr,
                                   "old_value": it["extra"].get(attr), "fact_id": fid, "reason": "unsupported_by_span"})
    # dedupe nulls per (item, attribute)
    seen = set(); nulled = [n for n in nulled if not ((n["event_id"], n["attribute"]) in seen or seen.add((n["event_id"], n["attribute"])))]
    if not a.dry_run:
        for r in relocated:
            eventlog.append({"event_type": "grounding_relocated", "doc_id": r["doc_id"], "target_event_id": r["event_id"],
                             "item_id": r["item_id"], "attribute": r["attribute"], "old_span": r["old_span"],
                             "new_span": r["new_span"], "method": r["method"], "task": TASK}, batch=OVERLAY_BATCH)
        for n in nulled:
            eventlog.append({"event_type": "attribute_nulled", "doc_id": n["doc_id"], "target_event_id": n["event_id"],
                             "item_id": n["item_id"], "attribute": n["attribute"], "old_value": n["old_value"],
                             "reason": n["reason"], "probe_fact_id": n["fact_id"], "task": TASK}, batch=OVERLAY_BATCH)
    out = {"relocated": len(relocated), "relocation_failed": len(failed), "attributes_nulled": len(nulled),
           "items_in_reextract_strata_skipped": counts["skipped_reextract_stratum"],
           "relocate_not_applicable": counts["relocate_not_applicable"],
           "relocated_detail": relocated, "failed_detail": failed, "nulled_detail": nulled, "dry_run": a.dry_run}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print({k: v for k, v in out.items() if not k.endswith("_detail")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
