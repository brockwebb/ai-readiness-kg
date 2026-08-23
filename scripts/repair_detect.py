#!/usr/bin/env python3
"""Whole-graph repair Phase 1 — detection sweep (task 2026-08-23_whole_graph_repair, Seldon
803b024f). Zero model spend. Over every live node in both epochs, excluding the probe's
reextract_required strata (Instrument:v1, Instrument:kernel-v03, edge:semantic:kernel-v03 —
edges are not span-repaired here at all):

  span_partial   : grounding_span does not cover the item's text attribute
                   (grounding.COVERAGE_ATTRIBUTES, NFKC-normalized substring) -> repair_span_partial.jsonl
  filled_attr    : a span_entailable:true attribute (schema v0.3.2) whose value is not a
                   normalized substring of the span                           -> repair_filled_attr.jsonl

Items already carrying a grounding_relocated / attribute_nulled overlay (probe Phase 7) are
evaluated on their OVERLAID state so the probe's repairs are not redone.
Writes corpus/staging/metrics/repair_detect_summary.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog                                          # noqa: E402
from kg.extraction import schema_loader                          # noqa: E402
from kg.extraction.grounding import normalize, covers, COVERAGE_ATTRIBUTES  # noqa: E402
from run_baseline_gates import live_events                       # noqa: E402

OUT_DIR = REPO / "corpus/staging/metrics"
REEXTRACT_TYPES = {"Instrument"}          # both epochs flagged by the probe
# attributes that hold free text too long/paraphrased for substring support; they are still
# checked (the rule is mechanical) but reported separately so the finding is legible
TEXT_ATTRS = set(COVERAGE_ATTRIBUTES)


def main() -> int:
    schema = schema_loader.load_schema()
    events = live_events(list(eventlog.replay()))
    relocated, nulled = {}, defaultdict(set)
    for ev in events:
        if ev.get("event_type") == "grounding_relocated":
            relocated[(ev["doc_id"], ev["item_id"])] = ev["new_span"]
        elif ev.get("event_type") == "attribute_nulled":
            nulled[(ev["doc_id"], ev["item_id"])].add(ev["attribute"])
    epoch_of = {}
    for ev in events:
        if ev.get("event_type") == "node_asserted":
            ep = (ev.get("provenance") or {}).get("corpus_epoch")
            if ep: epoch_of[ev["doc_id"]] = ep
    span_partial, filled = [], []
    counts = Counter(); by_doc = Counter(); scanned = Counter()
    for ev in events:
        if ev.get("event_type") != "node_asserted":
            continue
        p = ev["payload"]; typ = p["type"]; it = dict(p.get("item") or {})
        if typ in REEXTRACT_TYPES:
            counts["skipped_reextract_stratum"] += 1; continue
        key = (ev["doc_id"], p["id"])
        span = relocated.get(key, it.get("grounding_span") or "")
        for a in nulled.get(key, ()): it[a] = None
        ep = epoch_of.get(ev["doc_id"], "v1")
        scanned[(typ, ep)] += 1
        # span-partial on the text attribute
        text_attr = next((a for a in COVERAGE_ATTRIBUTES if isinstance(it.get(a), str) and it[a].strip()), None)
        if text_attr and not covers(span, it[text_attr]):
            span_partial.append({"event_id": ev["event_id"], "doc_id": ev["doc_id"], "item_id": p["id"], "type": typ,
                                 "epoch": ep, "attribute": text_attr, "item_text": it[text_attr], "span": span,
                                 "already_relocated": key in relocated})
            counts[("span_partial", ep)] += 1; by_doc[ev["doc_id"]] += 1
        # unsupported span_entailable attributes (excluding the text attribute handled above)
        se = schema_loader.span_entailable(schema, typ)
        ns = normalize(span)
        for attr, val in it.items():
            if not se.get(attr) or attr == text_attr or attr == "grounding_span" or val in (None, "", [], {}):
                continue
            vals = val if isinstance(val, list) else [val]
            unsupported = [v for v in vals if normalize(str(v)) and normalize(str(v)) not in ns]
            if unsupported:
                filled.append({"event_id": ev["event_id"], "doc_id": ev["doc_id"], "item_id": p["id"], "type": typ,
                               "epoch": ep, "attribute": attr, "value": val, "unsupported_values": unsupported,
                               "free_text": attr in TEXT_ATTRS or attr in ("description", "method", "measurement_notes")})
                counts[("filled_attr", ep)] += 1; by_doc[ev["doc_id"]] += 1
    with (OUT_DIR / "repair_span_partial.jsonl").open("w", encoding="utf-8") as f:
        for r in span_partial: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (OUT_DIR / "repair_filled_attr.jsonl").open("w", encoding="utf-8") as f:
        for r in filled: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_nodes = sum(scanned.values())
    summary = {"nodes_scanned": n_nodes, "skipped_reextract_stratum": counts["skipped_reextract_stratum"],
               "span_partial": {"total": len(span_partial), "by_epoch": {e: counts[("span_partial", e)] for e in ("v1", "kernel-v03")},
                                "by_type": dict(Counter(r["type"] for r in span_partial)),
                                "already_relocated_by_probe": sum(r["already_relocated"] for r in span_partial)},
               "filled_attr": {"total": len(filled), "by_epoch": {e: counts[("filled_attr", e)] for e in ("v1", "kernel-v03")},
                               "by_attribute": dict(Counter(r["attribute"] for r in filled)),
                               "free_text_share": (sum(r["free_text"] for r in filled) / len(filled)) if filled else None},
               "scanned_by_type_epoch": {f"{t}:{e}": n for (t, e), n in sorted(scanned.items())},
               "top_docs": by_doc.most_common(15)}
    (OUT_DIR / "repair_detect_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("scanned_by_type_epoch", "top_docs")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
