#!/usr/bin/env python3
"""Load kg/schema.yaml — the authoritative node/edge type catalogue.

The parser reads type validity from here rather than from a duplicate static schema, so
there is a single source of truth (schema.yaml, transcribed from docs/schema_v0.1.md).
The edge whitelist is exactly ``edge_types`` keys: schema §3 says an edge type not in that
table cannot be written.
"""
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:  # fail loud (standard 4)
    raise SystemExit("FATAL: 'pyyaml' is required to load kg/schema.yaml (pip install pyyaml)")

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.yaml"


def load_schema(path: Path | None = None) -> dict:
    """Load and lightly validate schema.yaml. Fail loud on missing required sections."""
    path = path or _SCHEMA_PATH
    if not path.is_file():
        raise FileNotFoundError(f"schema not found: {path}")
    with path.open(encoding="utf-8") as fh:
        schema = yaml.safe_load(fh)
    for key in ("schema_version", "node_types", "edge_types", "provenance_required"):
        if key not in schema:
            raise ValueError(f"schema.yaml missing required section '{key}'")
    return schema


def node_types(schema: dict) -> set[str]:
    return set(schema["node_types"].keys())


def edge_types(schema: dict) -> dict:
    return schema["edge_types"]


def provenance_required(schema: dict) -> list[str]:
    return list(schema["provenance_required"])


def is_known_edge(schema: dict, etype: str) -> bool:
    """True iff the edge type is in the whitelist (schema §3). Unknown types are never
    written — they route to proposed_relationships."""
    return etype in schema["edge_types"]


def legal_pairs(schema: dict, etype: str) -> list[tuple[str, str]]:
    """The edge type's authoritative (from_type, to_type) endpoint pairs (schema `pairs`).
    Fail loud if the edge lacks explicit pairs — the parser must not fall back to a looser
    gate silently (standard 4)."""
    spec = schema["edge_types"][etype]
    if "pairs" not in spec:
        raise ValueError(f"edge type '{etype}' has no 'pairs' metadata in schema.yaml")
    return [tuple(p) for p in spec["pairs"]]


def is_valid_endpoint(schema: dict, etype: str, from_type: str, to_type: str) -> bool:
    """Strict index-pairing endpoint check (schema §3). (from_type, to_type) must be one of
    the edge's legal `pairs` — NOT the from x to cross product. A whitelisted edge that fails
    this is a schema-expressiveness signal (routed to proposed_relationships), not graph data.

    Symmetric edges (conflicts_with) also accept the reversed pair, though their pairs are
    same-type so this is a no-op in practice."""
    if etype not in schema["edge_types"]:
        return False
    pairs = legal_pairs(schema, etype)
    if (from_type, to_type) in pairs:
        return True
    if schema["edge_types"][etype].get("symmetric") and (to_type, from_type) in pairs:
        return True
    return False
