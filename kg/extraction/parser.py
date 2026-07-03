#!/usr/bin/env python3
"""Parse and validate a whole-document extraction output (schema_v0.1.md §2-5).

Enforced here, in code (not by convention):
- **Grounding gate (§4):** every extracted node and edge must carry a ``grounding_span``
  that string-matches the source (whitespace/OCR-tolerant). Missing span or a genuine miss
  => the item is quarantined with a reason, never ingested.
- **Edge whitelist (§3):** an edge whose ``type`` is not in schema.yaml is rejected at parse
  and routed to proposed_relationships — it never reaches the valid-edge set.
- **Endpoint type-validity (§3):** a known edge whose (from_type -> to_type) is not allowed
  is quarantined.

proposed_relationships (model-supplied plus auto-routed unknown edges) are staged for
operator batch review (§6); this parser never writes them to the graph.

The declarative envelope contract lives in output_schema.json; type validity is read from
schema.yaml (the single source of truth), so the two never drift.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import grounding, schema_loader

# Output layer name -> schema node type. These are the layers §5 emits, in order.
LAYER_TYPES = {
    "concepts": "Concept",
    "definitions": "Definition",
    "claims": "Claim",
    "instruments": "Instrument",
    "measures": "Measure",
    "standards": "Standard",
    "frameworks": "Framework",
    "constructs": "Construct",
}


@dataclass
class ExtractionResult:
    document_id: str
    nodes: list = field(default_factory=list)          # {id, type, item}
    edges: list = field(default_factory=list)          # {type, from_id, to_id, from_type, to_type, item}
    quarantined: list = field(default_factory=list)    # {kind, reason, item}
    proposed_relationships: list = field(default_factory=list)  # staged, never written

    def counts(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "quarantined": len(self.quarantined),
            "proposed_relationships": len(self.proposed_relationships),
        }


def _quarantine(result, kind, reason, item):
    result.quarantined.append({"kind": kind, "reason": reason, "item": item})


def parse_extraction(output: dict, source_text: str, schema: dict | None = None) -> ExtractionResult:
    """Validate ``output`` against ``schema`` and ``source_text``. Returns an ExtractionResult
    partitioning every item into valid nodes/edges, quarantine, or proposed_relationships.

    Raises ValueError on a structurally invalid envelope (not a dict, or no document_id) —
    a malformed envelope is an upstream bug, not a per-item quarantine."""
    if schema is None:
        schema = schema_loader.load_schema()
    if not isinstance(output, dict):
        raise ValueError(f"extraction output must be a dict, got {type(output).__name__}")
    doc_id = output.get("document_id")
    if not doc_id:
        raise ValueError("extraction output missing 'document_id'")

    result = ExtractionResult(document_id=doc_id)
    # id -> node type, built from VALID nodes only (+ the document itself). Edges may only
    # reference nodes that survived the grounding gate.
    id_types: dict[str, str] = {doc_id: "Document"}

    # --- node layers (§5 emission order) --------------------------------------------------
    for layer, node_type in LAYER_TYPES.items():
        for item in output.get(layer, []) or []:
            nid = item.get("id")
            if not nid:
                _quarantine(result, layer, "node missing 'id'", item)
                continue
            span = item.get("grounding_span")
            if not span or not str(span).strip():
                _quarantine(result, layer, "missing grounding_span (§4: no span, no write)", item)
                continue
            if not grounding.is_grounded(span, source_text):
                _quarantine(result, layer, "grounding_span not found in source text", item)
                continue
            id_types[nid] = node_type
            result.nodes.append({"id": nid, "type": node_type, "item": item})

    # --- edges ----------------------------------------------------------------------------
    for edge in output.get("edges", []) or []:
        etype = edge.get("type")
        span = edge.get("grounding_span")
        from_id, to_id = edge.get("from_id"), edge.get("to_id")

        # Edge whitelist (§3): unknown type => route to proposed_relationships, never write.
        if not schema_loader.is_known_edge(schema, etype):
            result.proposed_relationships.append({
                "source": "auto_routed_unknown_edge",
                "suggested_edge": etype,
                "from_id": from_id, "to_id": to_id,
                "grounding_span": span, "location": edge.get("location"),
                "note": edge.get("note"),
            })
            continue
        if not span or not str(span).strip():
            _quarantine(result, "edge", "missing grounding_span (§4: no span, no write)", edge)
            continue
        from_type, to_type = id_types.get(from_id), id_types.get(to_id)
        if from_type is None or to_type is None:
            _quarantine(result, "edge", "unresolved endpoint id (missing or quarantined node)", edge)
            continue
        if not grounding.is_grounded(span, source_text):
            _quarantine(result, "edge", "grounding_span not found in source text", edge)
            continue
        # Grounded + resolvable but not a legal endpoint pair: the relationship is real but
        # the schema can't express it in this form. Route to proposed_relationships (§9
        # expressiveness signal), never quarantine and never write it to the graph.
        if not schema_loader.is_valid_endpoint(schema, etype, from_type, to_type):
            result.proposed_relationships.append({
                "source": "auto_routed_invalid_pair",
                "suggested_edge": etype,
                "from_id": from_id, "to_id": to_id,
                "from_type": from_type, "to_type": to_type,
                "grounding_span": span, "location": edge.get("location"),
                "note": f"whitelisted edge '{etype}' with illegal endpoint pair "
                        f"{from_type}->{to_type} (not in schema pairs)",
            })
            continue
        result.edges.append({"type": etype, "from_id": from_id, "to_id": to_id,
                             "from_type": from_type, "to_type": to_type, "item": edge})

    # --- cites (Document -> Document; to_id may be an out-of-output corpus doc) ------------
    for cite in output.get("cites", []) or []:
        span = cite.get("grounding_span")
        from_id, to_id = cite.get("from_id"), cite.get("to_id")
        if not span or not str(span).strip():
            _quarantine(result, "cites", "missing grounding_span (§4: no span, no write)", cite)
            continue
        if from_id != doc_id:
            _quarantine(result, "cites", "cites from_id is not this document", cite)
            continue
        if not to_id:
            _quarantine(result, "cites", "cites missing to_id (cited document reference)", cite)
            continue
        if not grounding.is_grounded(span, source_text):
            _quarantine(result, "cites", "grounding_span not found in source text", cite)
            continue
        result.edges.append({"type": "cites", "from_id": from_id, "to_id": to_id,
                             "from_type": "Document", "to_type": "Document", "item": cite})

    # --- model-supplied proposed_relationships (staged, never written) --------------------
    for pr in output.get("proposed_relationships", []) or []:
        result.proposed_relationships.append({
            "source": "model",
            "suggested_edge": pr.get("suggested_edge") or pr.get("type"),
            "from_id": pr.get("from_id"), "to_id": pr.get("to_id"),
            "grounding_span": pr.get("grounding_span"), "location": pr.get("location"),
            "note": pr.get("note"),
        })

    return result
