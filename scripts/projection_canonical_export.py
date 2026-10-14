#!/usr/bin/env python3
"""Canonical export and hash of the projected graph (task
`cc_tasks/2026-10-12_projection_replay_measured_then_batched.md` decision 3).

The equivalence gate for any change to the projection: "the graph after the change must be the
graph before it" is checked by hashing a canonical form of the graph, never by comparing counts.

Canonical form. Neo4j element ids are storage addresses, not identity, so a node is identified
by its CONTENT: its sorted labels and its properties (minus `volatile_properties`), serialised as
sorted-key JSON; the node's digest is the sha256 of that line. A relationship is its type, the
digests of its two endpoints and its properties. The export is the sorted multiset of node lines
followed by the sorted multiset of relationship lines; the hash is the sha256 of that text.
Twins (two nodes with identical content) are kept as two lines, so a duplicated node changes the
hash; that is the fusion/duplication class DD-020 and the unlabelled-twin repair were about.

Scope. Every node in the database except those carrying an `exclude_labels` label (Seldon's
artifact graph, which shares the database under disjoint labels and is not a projection of this
log), and every relationship with at least one endpoint in scope. Both lists are read from
controls.yaml `projection.canonical_export`, at call time.

    python scripts/projection_canonical_export.py [--out logs/<name>.jsonl]

prints {"sha256", "nodes", "relationships", "per_label"} as JSON; `--out` also writes the
canonical lines so two exports can be diffed line by line.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

CONTROLS_PATH = REPO / "controls.yaml"


def export_config() -> dict:
    """controls.yaml `projection.canonical_export`. Both keys required: a scope that is not
    declared is not a scope a hash can be compared across."""
    doc = yaml.safe_load(CONTROLS_PATH.read_text(encoding="utf-8")) or {}
    block = ((doc.get("projection") or {}).get("canonical_export"))
    if not isinstance(block, dict):
        raise SystemExit(f"FATAL: no projection.canonical_export block in {CONTROLS_PATH}")
    for key in ("exclude_labels", "volatile_properties"):
        if not isinstance(block.get(key), list):
            raise SystemExit(f"FATAL: projection.canonical_export.{key} must be a list")
    return {"exclude_labels": list(block["exclude_labels"]),
            "volatile_properties": list(block["volatile_properties"])}


def _typed(v):
    """JSON fallback for driver value types (temporal, spatial): the type name is part of the
    value, so a string and a date that print alike do not hash alike."""
    return f"<{type(v).__name__}>{v}"


def _dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      default=_typed)


def canonical(nodes, rels, exclude_labels, volatile) -> tuple[list[str], list[str]]:
    """Pure. `nodes`: iterable of (element_id, labels, props); `rels`: iterable of (start_id,
    end_id, type, props). Returns (sorted node lines, sorted relationship lines)."""
    excluded, vol = set(exclude_labels), set(volatile)
    digest: dict[str, str] = {}
    node_lines = []
    for eid, labels, props in nodes:
        if excluded & set(labels):
            continue
        line = _dumps({"labels": sorted(labels),
                       "props": {k: v for k, v in props.items() if k not in vol}})
        digest[eid] = hashlib.sha256(line.encode("utf-8")).hexdigest()
        node_lines.append(line)
    rel_lines = []
    for start, end, rtype, props in rels:
        if start not in digest and end not in digest:
            continue
        rel_lines.append(_dumps({
            "type": rtype,
            # an out-of-scope endpoint (a Seldon artifact) is named as such, not by content
            "start": digest.get(start, "out_of_scope"),
            "end": digest.get(end, "out_of_scope"),
            "props": {k: v for k, v in props.items() if k not in vol}}))
    return sorted(node_lines), sorted(rel_lines)


def summarise(node_lines: list[str], rel_lines: list[str]) -> dict:
    h = hashlib.sha256()
    for line in node_lines + ["--relationships--"] + rel_lines:
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    per_label: dict[str, int] = {}
    for line in node_lines:
        key = ":".join(json.loads(line)["labels"]) or "<unlabelled>"
        per_label[key] = per_label.get(key, 0) + 1
    return {"sha256": h.hexdigest(), "nodes": len(node_lines),
            "relationships": len(rel_lines), "per_label": dict(sorted(per_label.items()))}


def export_live(session, cfg: dict) -> tuple[list[str], list[str]]:
    """Read the whole database in one read transaction, so nodes and relationships come from
    one snapshot."""
    def _read(tx):
        nodes = [(r["id"], r["labels"], r["props"]) for r in tx.run(
            "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props")]
        rels = [(r["s"], r["e"], r["t"], r["props"]) for r in tx.run(
            "MATCH (a)-[r]->(b) RETURN elementId(a) AS s, elementId(b) AS e, type(r) AS t, "
            "properties(r) AS props")]
        return nodes, rels
    nodes, rels = session.execute_read(_read)
    return canonical(nodes, rels, cfg["exclude_labels"], cfg["volatile_properties"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, help="also write the canonical lines here")
    args = ap.parse_args(argv)
    cfg = export_config()
    import build_projection as bp
    from neo4j import GraphDatabase
    uri, user, pw = bp._neo4j_creds()
    db = bp._database()
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    try:
        with driver.session(database=db) as session:
            node_lines, rel_lines = export_live(session, cfg)
    finally:
        driver.close()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("\n".join(node_lines + ["--relationships--"] + rel_lines) + "\n",
                            encoding="utf-8")
    out = summarise(node_lines, rel_lines)
    out.update({"database": db, "exclude_labels": cfg["exclude_labels"],
                "volatile_properties": cfg["volatile_properties"]})
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
