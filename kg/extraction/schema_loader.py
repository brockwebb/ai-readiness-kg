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


def _as_set(v) -> set[str]:
    """A schema from/to field is a scalar type or a list of types; normalize to a set."""
    return set(v) if isinstance(v, list) else {v}


def is_known_edge(schema: dict, etype: str) -> bool:
    """True iff the edge type is in the whitelist (schema §3). Unknown types are never
    written — they route to proposed_relationships."""
    return etype in schema["edge_types"]


def is_valid_endpoint(schema: dict, etype: str, from_type: str, to_type: str) -> bool:
    """Type-validity check for an edge's endpoints (schema §3 "type-validity only").

    from_type must be in the edge's allowed from-set and to_type in its to-set. For
    multi-pair edges (extends, conflicts_with, builds_on) the from/to are sets, so this is
    set-membership, not index pairing — a deliberately loose type gate. conflicts_with is
    symmetric, which set-membership already covers (its from-set == to-set).
    """
    if etype not in schema["edge_types"]:
        return False
    spec = schema["edge_types"][etype]
    return from_type in _as_set(spec["from"]) and to_type in _as_set(spec["to"])
