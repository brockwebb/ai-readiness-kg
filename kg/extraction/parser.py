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
- **Property enums and required properties (v0.3, DD-010):** a node whose enumerated property
  (schema ``property_values``) holds a value outside the enum is quarantined; a node missing a
  property the schema lists under ``required_properties`` (Claim.evidence_grade) is quarantined
  with a clear reason. Both lists are read from schema.yaml, never duplicated here.

proposed_relationships (model-supplied plus auto-routed unknown edges) are staged for
operator batch review (§6); this parser never writes them to the graph.

The declarative envelope contract lives in output_schema.json; type validity is read from
schema.yaml (the single source of truth), so the two never drift.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

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
    # v0.3 (DD-009): machine-visibility node types.
    "practices": "Practice",
    "tools": "Tool",
    "platforms": "Platform",
}


@dataclass
class ExtractionResult:
    document_id: str
    nodes: list = field(default_factory=list)          # {id, type, item}
    edges: list = field(default_factory=list)          # {type, from_id, to_id, from_type, to_type, item}
    quarantined: list = field(default_factory=list)    # {kind, reason, item}
    proposed_relationships: list = field(default_factory=list)  # staged, never written
    # v0.3.5 precheck (ADDENDUM-01 §2): nodes whose own span lacks their name, counted
    # BEFORE any quarantine decision so a pilot verdict reports it as a number.
    precheck_span_lacks_name: int = 0

    def counts(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "quarantined": len(self.quarantined),
            "proposed_relationships": len(self.proposed_relationships),
        }


#: ADDENDUM-06's closed list, plus the two the harness itself produces (`cross_chunk` from
#: chunk-local extraction, `unstated` for an omitted field).
DIVERSION_REASONS = ("cross_chunk", "structural_inference", "endpoint_not_located",
                     "predicate_not_located", "distance_exceeded", "unstated")

#: Observed model phrasings that mean a listed reason. Data, not code (standard 2).
_DIVERSION_SYNONYMS = {
    "structural_only": "structural_inference",
    "structural_evidence_only": "structural_inference",
    "schema_cannot_express": "other:schema_cannot_express",
    "unsupported_edge_type": "other:schema_cannot_express",
    "auto_routed_unknown_edge": "other:schema_cannot_express",
}


def normalize_diversion_reason(raw) -> str:
    """Map a model-supplied `diversion_reason` onto the closed list.

    The leading token before ':' or an em/en dash is taken, because the observed failure is a
    listed reason followed by prose ("structural_evidence_only — Table 2 groups Lexical
    Diversity under..."), not a wholly invented one. A near-miss synonym maps to its member;
    anything else becomes `other`. Promoted verbatim in behaviour from
    `scripts/chunked_pilot.py`, whose report-side version this replaces."""
    head = re.split(r"[:\u2014\u2013]", str(raw if raw is not None else "unstated"), 1)[0]
    head = head.strip().lower().replace(" ", "_")
    if head in DIVERSION_REASONS:
        return head
    return _DIVERSION_SYNONYMS.get(head, "other")


def _quarantine(result, kind, reason, item):
    result.quarantined.append({"kind": kind, "reason": reason, "item": item})


# --- v0.3.4 (task 2026-08-26_overnight_burn Lane 0; 2026-08-22_probe_decision.md) ---------
# Instrument attributes that require a covering per-attribute span in `grounding_spans`.
# A filled attribute without one is NULLED at parse (never a quarantine of the node) — the
# probe found `method` fabricated from world knowledge (F 0.25/0.17).
INSTRUMENT_SPAN_REQUIRED = ("owner", "year", "method")
# Edge types asserting a semantic relation: their span must contain both endpoint names —
# heading/list-structure inference routes to proposed_relationships (F 0.26 on kernel-v03).
SEMANTIC_EDGE_TYPES = frozenset({"has_component", "subtype_of", "consumes",
                                 "extends", "implements"})
# The attribute that names a node, per type, for the semantic-edge endpoint check.
_NAME_ATTR = {"Concept": "name", "Framework": "name", "Standard": "name", "Platform": "name",
              "Tool": "name", "Instrument": "name", "Definition": "term", "Construct": "name"}


def _null_uncovered_instrument_attrs(item: dict, source_text: str) -> dict:
    """Return a copy of the Instrument item with owner/year/method nulled unless
    grounding_spans[attr] exists, is grounded in the document, and covers the value.
    Nulled attribute names are recorded on the item as `nulled_at_parse`."""
    spans = item.get("grounding_spans") or {}
    if not isinstance(spans, dict):
        spans = {}
    out = dict(item)
    nulled = []
    for attr in INSTRUMENT_SPAN_REQUIRED:
        val = out.get(attr)
        if val in (None, "", [], {}):
            continue
        span = spans.get(attr)
        ok = (isinstance(span, str) and span.strip()
              and grounding.is_grounded(span, source_text)
              and grounding.covers(span, str(val)))
        if not ok:
            out[attr] = None
            nulled.append(attr)
    if nulled:
        out["nulled_at_parse"] = nulled
    return out


def _semantic_span_violation(edge: dict, from_item: dict | None, to_item: dict | None,
                             from_type: str, to_type: str) -> str | None:
    """Reason the edge fails the v0.3.4 semantic-span rule, else None. Mechanical check:
    the span must contain both endpoints' NAMES (the prompt additionally allows unambiguous
    referents, which no mechanical check can verify — such edges route to
    proposed_relationships for review rather than being written or lost)."""
    span = edge.get("grounding_span") or ""
    for endpoint, item, ntype in (("from", from_item, from_type), ("to", to_item, to_type)):
        attr = _NAME_ATTR.get(ntype)
        name = (item or {}).get(attr) if attr else None
        if not isinstance(name, str) or not name.strip():
            return f"semantic edge {endpoint}-endpoint ({ntype}) has no name to verify in span"
        if not grounding.covers(span, name):
            return (f"semantic edge span does not contain the {endpoint}-endpoint name "
                    f"{name!r} (v0.3.4: span must state the relation, not page structure)")
    return None


def _property_violation(schema: dict, node_type: str, item: dict) -> str | None:
    """Reason string if ``item`` violates the node type's property contract, else None.
    Required properties (schema ``required_properties``) must be present and non-empty;
    enumerated properties (schema ``property_values``) must hold a listed value when present.
    Checked AFTER the grounding gate so a grounding miss keeps its own, more specific reason."""
    for prop in schema_loader.required_properties(schema, node_type):
        val = item.get(prop)
        if val is None or (isinstance(val, str) and not val.strip()):
            return f"{node_type} missing required property '{prop}' (schema v0.3; absent => quarantine)"
    for prop, allowed in schema_loader.property_values(schema, node_type).items():
        if prop in item and item[prop] is not None and item[prop] not in allowed:
            return (f"{node_type}.{prop} value {item[prop]!r} not in schema enum "
                    f"{list(allowed)}")
    return None


_DIXIE_CFG = Path(__file__).resolve().parent.parent.parent / "dixie_evidence.yaml"


def _span_coverage_default() -> bool:
    """extraction_gates.enforce_span_coverage from dixie_evidence.yaml; absent -> False."""
    if not _DIXIE_CFG.is_file():
        return False
    import yaml
    cfg = yaml.safe_load(_DIXIE_CFG.read_text(encoding="utf-8")) or {}
    return bool((cfg.get("extraction_gates") or {}).get("enforce_span_coverage", False))


def parse_extraction(output: dict, source_text: str, schema: dict | None = None,
                     enforce_span_coverage: bool | None = None) -> ExtractionResult:
    """Validate ``output`` against ``schema`` and ``source_text``. Returns an ExtractionResult
    partitioning every item into valid nodes/edges, quarantine, or proposed_relationships.

    Raises ValueError on a structurally invalid envelope (not a dict, or no document_id) —
    a malformed envelope is an upstream bug, not a per-item quarantine.

    ``enforce_span_coverage`` (task 2026-08-22_faithfulness_probe Phase 7): when True, a node
    whose grounding_span does not COVER its text attribute (grounding.COVERAGE_ATTRIBUTES)
    is quarantined with reason ``span_partial``. None -> read
    dixie_evidence.yaml::extraction_gates.enforce_span_coverage (default False until the
    whole-graph follow-on sized from the probe turns it on)."""
    if enforce_span_coverage is None:
        enforce_span_coverage = _span_coverage_default()
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
    id_items: dict[str, dict] = {}   # v0.3.4: valid nodes' items, for the semantic-span check

    # --- node layers (§5 emission order) --------------------------------------------------
    for layer, node_type in LAYER_TYPES.items():
        for item in output.get(layer, []) or []:
            nid = item.get("id")
            if not nid:
                _quarantine(result, layer, "node missing 'id'", item)
                continue
            span = item.get("grounding_span")
            # v0.3.5 precheck: does the node's own span contain its name-class attribute?
            # Counted for every node regardless of the coverage gate, before any quarantine.
            name_val = item.get("name") or item.get("term") or item.get("text")
            if isinstance(name_val, str) and name_val.strip() and \
                    not grounding.covers(str(span or ""), name_val):
                result.precheck_span_lacks_name += 1
            if not span or not str(span).strip():
                _quarantine(result, layer, "missing grounding_span (§4: no span, no write)", item)
                continue
            if not grounding.is_grounded(span, source_text):
                _quarantine(result, layer, "grounding_span not found in source text", item)
                continue
            violation = _property_violation(schema, node_type, item)
            if violation:
                _quarantine(result, layer, violation, item)
                continue
            if enforce_span_coverage:
                partial = grounding.partial_span_reason(item)
                if partial:
                    _quarantine(result, layer, partial, item)
                    continue
            if node_type == "Instrument":
                # v0.3.4: per-attribute span map — uncovered owner/year/method are nulled
                # here (attribute-level), the node itself stays admitted.
                item = _null_uncovered_instrument_attrs(item, source_text)
            id_types[nid] = node_type
            id_items[nid] = item
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
        if etype in SEMANTIC_EDGE_TYPES:
            # v0.3.4: the span must state the relation — both endpoint names inside it.
            violation = _semantic_span_violation(edge, id_items.get(from_id),
                                                 id_items.get(to_id), from_type, to_type)
            if violation:
                result.proposed_relationships.append({
                    "source": "auto_routed_semantic_span",
                    "suggested_edge": etype,
                    "from_id": from_id, "to_id": to_id,
                    "from_type": from_type, "to_type": to_type,
                    "grounding_span": span, "location": edge.get("location"),
                    "note": violation,
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
        raw_reason = pr.get("diversion_reason")
        result.proposed_relationships.append({
            "source": "model",
            "suggested_edge": pr.get("suggested_edge") or pr.get("type"),
            "from_id": pr.get("from_id"), "to_id": pr.get("to_id"),
            "grounding_span": pr.get("grounding_span"), "location": pr.get("location"),
            "note": pr.get("note"),
            # ADDENDUM-06 closed list, ENFORCED HERE (v0.3.7, ADDENDUM-03 §1.3) rather than
            # left to the report. Measured on the chunked pilot: over the first 10 chunks the
            # model emitted 34 distinct values for this field, most of them whole sentences.
            # A model cannot be bound by an instruction; it can be bound by a parser. The
            # normalization moved out of scripts/chunked_pilot.py so that every consumer of
            # the shard sees one closed vocabulary instead of each re-deriving its own.
            "diversion_reason": normalize_diversion_reason(raw_reason),
            # The raw value is PRESERVED on the shard: normalization is for the vocabulary,
            # not a licence to discard what the model actually said.
            "diversion_reason_raw": raw_reason,
        })

    return result
