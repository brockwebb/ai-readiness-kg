#!/usr/bin/env python3
"""Per-document build metrics (schema_v0.1.md §5.6, DD-005 QC).

Concept density is the guard against a repeat of the fss-policy-kg ~13% thin concept layer;
quarantine rate and proposed_relationships volume feed the pilot audit (§9) and the
autonomy-ramp control limits. Metrics are written to a file and emitted as an event.
"""
from __future__ import annotations

import json
from pathlib import Path

# Token estimate is a coarse heuristic, not a real tokenizer — named so it's tunable and not
# a magic literal (standard 2). Concept density is reported per 1k of these estimated tokens.
CHARS_PER_TOKEN = 4

_METRICS_DIR = Path(__file__).resolve().parent.parent.parent / "corpus" / "staging" / "metrics"


def estimate_tokens(text: str) -> int:
    """Coarse token estimate (~len/CHARS_PER_TOKEN). At least 1 to avoid divide-by-zero."""
    return max(1, round(len(text) / CHARS_PER_TOKEN))


def compute(doc_id: str, source_text: str, result) -> dict:
    """Compute the §5.6 metrics from an ExtractionResult and the source text."""
    tokens = estimate_tokens(source_text)
    n_concepts = sum(1 for n in result.nodes if n["type"] == "Concept")
    n_definitions = sum(1 for n in result.nodes if n["type"] == "Definition")
    total_items = len(result.nodes) + len(result.edges) + len(result.quarantined)
    return {
        "doc_id": doc_id,
        "estimated_tokens": tokens,
        "concepts": n_concepts,
        "concepts_per_1k_tokens": round(n_concepts / (tokens / 1000), 4),
        "definitions_count": n_definitions,
        "nodes": len(result.nodes),
        "edges": len(result.edges),
        "quarantined": len(result.quarantined),
        "quarantine_rate": round(len(result.quarantined) / total_items, 4) if total_items else 0.0,
        "proposed_relationships_count": len(result.proposed_relationships),
    }


def write_metrics_file(metrics: dict, metrics_dir: Path | None = None) -> Path:
    """Write metrics to ``corpus/staging/metrics/<doc_id>.json`` and return the path."""
    metrics_dir = metrics_dir or _METRICS_DIR
    metrics_dir.mkdir(parents=True, exist_ok=True)
    path = metrics_dir / f"{metrics['doc_id']}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path
