"""The ai-readiness graph's emitter (squiddy SQ-019; DN-049 R-208, R-209). Deterministic, zero model calls.

The kit calls `emit(entry, resolved, graph, classes)` and `manifest_projection(entry, graph)` for a cataloged
document, and `emit_extraction(entry, rows, graph, classes)` for the extraction records `squiddy extract ingest`
admits. Seeded from squiddy/templates/emit.py by `squiddy init` and replaced for this graph, as arnold-evidence's is:
this graph has one manifest kind (`document`) and its items are ai-readiness-kg's, so none of the template's
bibliographic layers apply.

THE DOCUMENT is a dixie catalog entry (`squiddy catalog --from dixie:`). Its id is dixie's `doc_id`, which is also the
key ai-readiness-kg's assessment layer reaches it by (EVIDENCED_BY, EVIDENCED_BY_INTERNAL, OBSERVED_ON; R-209). Its
properties come from the entry and the dixie record it carries whole (`dixie_record`).

AN ITEM is one row of an adopted record (squiddy `tools/l002_adopt.py`, the `airkg` mapping). `claim.claim_kind` is the
source node type or edge type; `claim.props` is the item as ai-readiness-kg's own projection would write it (its
`_scalar_props` of the asserted item, the `prov_*` stamp, the repair overlays); the row's `span` is the kit's located
span, re-derived by ingest. Item ids are kept: a node's id is the projection's key `<doc_id>::<item_id>`, and an edge's
endpoints are the keys the projection resolved. A property the schema transcribes becomes that slot (renamed where
the transcription renamed it); EVERY property rides in `source_item` as JSON, so nothing is dropped to fit.
"""
from __future__ import annotations

import hashlib
import json

#: source property -> slot, where the transcription renamed it (squiddy tools/sq019_transcribe_schema.py)
RENAMED = {"grounding_span": "grounding_text", "method": "instrument_method", "id": "item_id",
           "prov_extraction_event_id": "extraction_event_id"}
#: properties of the projected item that are the kit's own fields on the node, set below and never from the item
OWNED = {"doc_id", "prov_wasDerivedFrom"}


def _record(entry: dict) -> dict:
    raw = entry.get("dixie_record")
    return json.loads(raw) if raw else {}


def manifest_projection(entry: dict, graph) -> dict:
    """The Document's properties that come from the manifest verbatim; the manifest-to-ledger gate compares these."""
    ident = _record(entry).get("identity") or {}
    props = {"id": entry["id"], "doc_id": entry["id"], "title": entry.get("title"),
             "source_url": entry.get("source_url"), "disposition": entry.get("disposition"),
             "local_path": entry.get("local_path"), "sha256": entry.get("sha256"),
             "authors": [str(a) for a in ident.get("authors_or_org") or []] or None,
             "pub_date": None if ident.get("pub_year") is None else str(ident["pub_year"]),
             "primary_url": ident.get("source_url"), "content_hash": ident.get("sha256"),
             "doc_type": ident.get("doc_type"), "dixie_record": entry.get("dixie_record"),
             "dixie_decision": entry.get("dixie_decision"), "dixie_rationale": entry.get("dixie_rationale")}
    return {k: v for k, v in props.items() if v is not None}


def emit(entry: dict, resolved: dict | None, graph, classes: dict) -> list:
    kind = entry.get("kind")
    prim = graph.engine["write"]["primary_class_by_kind"].get(kind)
    if prim != "Document":
        raise SystemExit(f"FATAL: this graph's one manifest kind is `document`; {entry['id']} is {kind!r}")
    return [classes["Document"](**manifest_projection(entry, graph), method="manifest")]


def built(classes: dict) -> dict:
    """Every class this emitter builds, by name, written out so `squiddy init --check` (which reads `classes["X"]`
    in the emitter, K-002 Part B) sees each one, and so a class the schema stopped declaring fails here, loud."""
    return {"Document": classes["Document"], "Definition": classes["Definition"], "Concept": classes["Concept"],
            "Construct": classes["Construct"], "Instrument": classes["Instrument"], "Measure": classes["Measure"],
            "Claim": classes["Claim"], "Standard": classes["Standard"], "Framework": classes["Framework"],
            "Practice": classes["Practice"], "Tool": classes["Tool"], "Platform": classes["Platform"],
            "Defines": classes["Defines"], "Mentions": classes["Mentions"], "Asserts": classes["Asserts"],
            "About": classes["About"], "Operationalizes": classes["Operationalizes"],
            "OperationalizedBy": classes["OperationalizedBy"], "Measures": classes["Measures"],
            "Grounds": classes["Grounds"], "Extends": classes["Extends"], "ConflictsWith": classes["ConflictsWith"],
            "Cites": classes["Cites"], "BuildsOn": classes["BuildsOn"], "Implements": classes["Implements"],
            "UsesMeasure": classes["UsesMeasure"], "HasComponent": classes["HasComponent"],
            "SubtypeOf": classes["SubtypeOf"], "Precedes": classes["Precedes"], "Recommends": classes["Recommends"],
            "SupportedBy": classes["SupportedBy"], "ImplementedBy": classes["ImplementedBy"],
            "Consumes": classes["Consumes"], "AppliesTo": classes["AppliesTo"], "Targets": classes["Targets"],
            "Supersedes": classes["Supersedes"]}


def _class_of(graph, claim_kind: str) -> str:
    m = (graph.domain.get("airkg_schema") or {}).get("class_of") or {}
    if claim_kind not in m:
        raise SystemExit(f"FATAL: no transcribed class for source type {claim_kind!r} (domain.airkg_schema.class_of)")
    return m[claim_kind]


def _coerce(cls, slot: str, value):
    """A source value in the slot's declared shape: a list for a multivalued slot, a boolean for a boolean one, a
    string otherwise (a year the extractor wrote as 2024 is the string "2024"). The value is never changed beyond
    its type; `source_item` holds it as asserted."""
    ann = str(cls.model_fields[slot].annotation)
    if "list" in ann.lower():
        vals = value if isinstance(value, list) else json.loads(value) if isinstance(value, str) and value.startswith("[") else [value]
        return [str(v) for v in vals]
    if "bool" in ann:
        return bool(value)
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)


def _stamp(row: dict) -> dict:
    a = row.get("airkg") or {}
    return {"prov_extractor": f"airkg:{a.get('model_id') or 'unknown'}:{a.get('prompt_version') or 'none'}",
            "prov_extractor_version": a.get("model_id"), "prov_run_id": a.get("extraction_event_id"),
            "method": "extraction", "status": "proposed"}


def emit_extraction(entry: dict, rows: list[dict], graph, classes: dict) -> list:
    """Typed instances for one document's adopted rows. Only `grounded` rows: a row ingest could not ground is never
    a stored item (R-14, R-208)."""
    out, table = [], built(classes)
    for r in rows:
        if r.get("status") != "grounded":
            continue
        c = r["claim"]
        cls = table[_class_of(graph, c["claim_kind"])]
        fields = cls.model_fields
        a = r.get("airkg") or {}
        kw = {"doc_id": entry["id"], "prov_wasDerivedFrom": entry["id"], "grounding_span": dict(r["span"]),
              "source_item": json.dumps(c["props"], ensure_ascii=False, sort_keys=True),
              "batch": a.get("batch"), "chunk_id": a.get("chunk_id"),
              "source_changed": bool(a.get("source_changed")), "span_ambiguous": bool(a.get("span_ambiguous")),
              # squiddy DN-049 ADDENDUM 01 R-217: `false` when the span was located only under the declared
              # normalization; a row without it is verbatim and its item carries no flag (SQ-022)
              "span_raw_equal": a.get("span_raw_equal"),
              "prov_timestamp": a.get("timestamp"), **_stamp(r)}
        if c["kind"] == "node":
            kw["id"] = c["key"]
        else:
            kw["subject"], kw["object"] = c["subject"], c["object"]
        for k, v in c["props"].items():
            slot = RENAMED.get(k, k)
            if v is None or k in OWNED or slot in kw or slot not in fields:
                continue
            kw[slot] = _coerce(cls, slot, v)
        out.append(cls(**{k: v for k, v in kw.items() if v is not None and k in fields}))
    return out


def claim_id(doc_id: str, text: str) -> str:
    """Ingest's claim-mention scan keys a row by this; this graph has no concept vocabulary, so it matches nothing."""
    return f"claim:{doc_id}:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"


def emit_mentions(rows: list[dict], graph, classes: dict) -> list:
    """No mention layer: this graph's Concepts are extracted items, not a vocabulary a scan matches against."""
    if rows:
        raise SystemExit("FATAL: the ai-readiness graph declares no mention layer, and ingest offered mention rows")
    return []
