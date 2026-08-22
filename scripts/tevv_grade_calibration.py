#!/usr/bin/env python3
"""TEVV Phase 4 — evidence_grade calibration against document-level signals
(task 2026-08-22_kernel_tevv). Zero spend.

For every live kernel Claim: compare evidence_grade with the document's
is_platform_operator (document_annotation events, DD-014) and source_type (manifest).
Confusion matrices for the two gated classes; distribution table for the rest.
Writes corpus/staging/metrics/tevv_grade_calibration.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog  # noqa: E402
from run_baseline_gates import live_events  # noqa: E402

# Task text says "source_type in {academic, preprint}"; the schema enum has no `preprint`
# (arXiv papers are manifested as `academic`). Recorded as a discrepancy in the RESULT.
PEER_REVIEWED_SOURCE_TYPES = {"academic"}


def collect() -> dict:
    events = live_events(list(eventlog.replay()))
    src_type, is_po = {}, {}
    for ev in events:
        if ev.get("event_type") == "manifest_add":
            src_type[ev["payload"]["doc_id"]] = ev["payload"]["source_type"]
        elif ev.get("event_type") == "document_annotation" and ev.get("property") == "is_platform_operator":
            is_po[ev["doc_id"]] = ev.get("value")
    claims = []
    for ev in events:
        if ev.get("event_type") == "node_asserted" and ev["payload"].get("type") == "Claim" \
                and (ev.get("provenance") or {}).get("corpus_epoch") == "kernel-v03":
            g = (ev["payload"].get("item") or {}).get("evidence_grade")
            d = ev["doc_id"]
            claims.append({"doc_id": d, "grade": g, "is_platform_operator": is_po.get(d),
                           "source_type": src_type.get(d)})
    return {"claims": claims, "n_docs_annotated": len(is_po)}


def confusion(claims: list[dict], grade: str, truth) -> dict:
    tp = sum(1 for c in claims if c["grade"] == grade and truth(c))
    fp = sum(1 for c in claims if c["grade"] == grade and not truth(c))
    fn = sum(1 for c in claims if c["grade"] != grade and truth(c))
    tn = sum(1 for c in claims if c["grade"] != grade and not truth(c))
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    return {"grade": grade, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec}


def main() -> int:
    data = collect()
    claims = data["claims"]
    po = confusion(claims, "platform_official", lambda c: c["is_platform_operator"] is True)
    pr = confusion(claims, "peer_reviewed_experiment", lambda c: c["source_type"] in PEER_REVIEWED_SOURCE_TYPES)
    # false positives by document, so the finding names where the confusion lives
    po_fp_docs = Counter(c["doc_id"] for c in claims if c["grade"] == "platform_official" and c["is_platform_operator"] is not True)
    pr_fp_docs = Counter(c["doc_id"] for c in claims if c["grade"] == "peer_reviewed_experiment" and c["source_type"] not in PEER_REVIEWED_SOURCE_TYPES)
    dist = defaultdict(Counter)
    for c in claims:
        dist[c["grade"] or "MISSING"][f"{c['source_type']}|po={c['is_platform_operator']}"] += 1
    out = {"n_claims": len(claims), "n_docs_annotated": data["n_docs_annotated"],
           "platform_official": {**po, "fp_by_doc": dict(po_fp_docs.most_common())},
           "peer_reviewed_experiment": {**pr, "fp_by_doc": dict(pr_fp_docs.most_common()),
                                        "truth_source_types": sorted(PEER_REVIEWED_SOURCE_TYPES)},
           "grade_by_source_signal": {g: dict(v) for g, v in dist.items()},
           "grade_totals": dict(Counter(c["grade"] or "MISSING" for c in claims))}
    (REPO / "corpus/staging/metrics/tevv_grade_calibration.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in ("platform_official", "peer_reviewed_experiment"):
        r = out[k]; print(f"{k:26s} tp={r['tp']} fp={r['fp']} fn={r['fn']} tn={r['tn']} precision={r['precision']} recall={r['recall']}")
        print("   fp by doc:", r["fp_by_doc"])
    print("grade totals:", out["grade_totals"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
