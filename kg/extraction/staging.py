#!/usr/bin/env python3
"""proposed_relationships staging (schema_v0.1.md §5.4, §6).

Relationships the schema cannot express are staged to a review area for operator batch
review, where accepted edge names bump the schema version. This area is never the graph:
nothing here is written to Neo4j or emitted as a graph assertion event.
"""
from __future__ import annotations

import json
from pathlib import Path

_REVIEW_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "corpus" / "staging" / "proposed_relationships"
)


def stage(doc_id: str, proposed_relationships: list, review_dir: Path | None = None) -> Path:
    """Write a document's proposed_relationships to a per-doc JSONL review file (overwriting
    any prior staging for that doc — the extraction run is authoritative). Returns the path."""
    review_dir = review_dir or _REVIEW_DIR
    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / f"{doc_id}.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for pr in proposed_relationships:
            fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
    return path
