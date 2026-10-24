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

SQ-022b (squiddy DN-050 R-219 to R-221). Every property the source projection writes onto an item is a slot now
(squiddy `tools/sq019_transcribe_schema.py` NODE_EXTRA, EDGE_EXTRA), so the loop below fills it; a scalar slot is
written in the type the schema declares (`_coerce`; `year` is an integer); `grounding_thin`, the one derived annotation
this graph builds (DI-003), is set by the source projection's own `is_thin_span`. A Document's properties that neither
catalog measured (`source_type`, `pub_date`, `construct_arm`, `is_platform_operator`, `grounding_surface`) are this
repository's primary acquisition record, folded from its event log exactly as `build_projection.build` folds it
(`acquisition_fold`), with the dixie catalog answering only where that record carries no value; `content_hash` is the
kit's own sha256 of the held bytes (the manifest's `sha256`), never either catalog's.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import typing
from pathlib import Path

#: source property -> slot, where the transcription renamed it (squiddy tools/sq019_transcribe_schema.py); the
#: projection's extra properties renamed on the way in are read from `domain.airkg_schema.renamed_extra`
RENAMED = {"grounding_span": "grounding_text", "method": "instrument_method", "id": "item_id",
           "prov_extraction_event_id": "extraction_event_id"}
#: properties of the projected item that are the kit's own fields on the node, set below and never from the item
OWNED = {"doc_id", "prov_wasDerivedFrom"}
#: the Document properties R-219 takes from the primary acquisition record (manifest_add, document_annotation)
ACQUISITION_PROPERTIES = ("source_type", "pub_date", "construct_arm", "is_platform_operator", "grounding_surface")
#: the fold, by doc_id, read once per process from this repository's event log (`_acquisition`); None until read
_ACQ: dict | None = None
_BP = None


def _projection(graph):
    """ai-readiness-kg's `scripts/build_projection.py`, from the repository the graph names (as squiddy's adopter
    imports it): the acquisition fold and `is_thin_span` are its code, never a copy."""
    global _BP
    if _BP is None:
        repo = Path(graph.domain["airkg"]["repo"])
        for p in (repo / "scripts", repo):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        _BP = importlib.import_module("build_projection")
    return _BP


def acquisition_fold(events, bp, skip_reason) -> dict:
    """{doc_id: {property: value}} as `build_projection.build` leaves a Document, from its event stream in log order:
    a projectable `document_annotation` SETs its property (`annotation_update`'s whitelist); a `manifest_add` SETs
    `source_type`, `pub_date` and `content_hash` (a null removes) and coalesces `construct_arm` and
    `grounding_surface` (scripts/build_projection.py, the `kg_replay` pass)."""
    out: dict[str, dict] = {}
    for ev in events:
        skip = skip_reason(ev)
        if skip == "skipped_non_graph_purpose":
            continue
        ann = bp.annotation_update(ev)
        if ann is not None:
            doc, prop, value = ann
            out.setdefault(doc, {})[prop] = value
            continue
        if skip is not None or ev.get("event_type") != "manifest_add":
            continue
        p = ev["payload"]
        d = out.setdefault(p["doc_id"], {})
        for k in ("source_type", "pub_date", "content_hash"):
            d[k] = p.get(k)
        for k in ("construct_arm", "grounding_surface"):
            if p.get(k) is not None:
                d[k] = p[k]
    return out


def _acquisition(graph) -> dict:
    global _ACQ
    if _ACQ is None:
        bp = _projection(graph)
        sel = bp.ReplaySelection()
        _ACQ = acquisition_fold(bp.kg_events(), bp, sel.skip_reason)
    return _ACQ


def _record(entry: dict) -> dict:
    raw = entry.get("dixie_record")
    return json.loads(raw) if raw else {}


def manifest_projection(entry: dict, graph) -> dict:
    """The Document's properties that come from the manifest verbatim; the manifest-to-ledger gate compares these.
    `content_hash` is the manifest's `sha256`, the kit's measurement of the held bytes (R-219 rule 1); `pub_date` is
    no longer here, because R-219 rule 2 takes it from the acquisition record first (`emit`)."""
    ident = _record(entry).get("identity") or {}
    props = {"id": entry["id"], "doc_id": entry["id"], "title": entry.get("title"),
             "source_url": entry.get("source_url"), "disposition": entry.get("disposition"),
             "local_path": entry.get("local_path"), "sha256": entry.get("sha256"),
             "authors": [str(a) for a in ident.get("authors_or_org") or []] or None,
             "primary_url": ident.get("source_url"), "content_hash": entry.get("sha256"),
             # SQ-021: an inbox entry has no dixie record; its class is the entry's own `doc_type`
             "doc_type": ident.get("doc_type") or entry.get("doc_type"), "dixie_record": entry.get("dixie_record"),
             "dixie_decision": entry.get("dixie_decision"), "dixie_rationale": entry.get("dixie_rationale")}
    return {k: v for k, v in props.items() if v is not None}


def acquisition_properties(entry: dict, graph, cls) -> dict:
    """R-219 rule 2: each unmeasured property from the acquisition record where it carries a value, else from the
    dixie catalog where dixie has that property at all (`pub_year` for `pub_date`; `doc_type` for `source_type` when it
    is inside the closed list), else absent."""
    acq = _acquisition(graph).get(entry["id"]) or {}
    ident = _record(entry).get("identity") or {}
    dixie = {"pub_date": None if ident.get("pub_year") is None else str(ident["pub_year"]),
             "source_type": ident.get("doc_type")}
    out = {}
    for k in ACQUISITION_PROPERTIES:
        v = acq.get(k)
        if v is None:
            v = dixie.get(k)
            allowed = _allowed(cls, k)
            if v is not None and allowed is not None and v not in allowed:
                v = None
        if v is not None:
            out[k] = _coerce(cls, k, v)
    return out


def _allowed(cls, slot: str) -> list | None:
    extra = cls.model_fields[slot].json_schema_extra or {}
    meta = (extra.get("linkml_meta") or {}) if isinstance(extra, dict) else {}
    return meta.get("equals_string_in")


def emit(entry: dict, resolved: dict | None, graph, classes: dict) -> list:
    kind = entry.get("kind")
    prim = graph.engine["write"]["primary_class_by_kind"].get(kind)
    if prim != "Document":
        raise SystemExit(f"FATAL: this graph's one manifest kind is `document`; {entry['id']} is {kind!r}")
    cls = classes["Document"]
    return [cls(**manifest_projection(entry, graph), **acquisition_properties(entry, graph, cls), method="manifest")]


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


def _declared(ann):
    """The one Python type a generated field declares: `list`, `bool`, `int`, or `str` (a Literal of strings, a plain
    string, or anything else), read from the annotation's structure with `Optional` removed, never from its text (an
    enum value such as "intergovernmental" contains "int")."""
    args = [a for a in typing.get_args(ann) if a is not type(None)] if typing.get_origin(ann) is typing.Union else [ann]
    if int in args and set(args) <= {int, str}:
        # `year` (SQ-022b): integer first, with a string arm only so the events written before R-221 still validate
        # on replay; every value the emitter writes takes the integer arm or none
        return int
    if len(args) != 1:
        return str
    a = args[0]
    if typing.get_origin(a) in (list, typing.List) or a is list:
        return list
    return a if a in (bool, int) else str


def _coerce(cls, slot: str, value):
    """A source value in the slot's declared type (squiddy DN-050 R-221): a list of strings for a multivalued slot, a
    boolean for a boolean one, an integer for an integer one, a string otherwise (a structure as its JSON). The value
    is never changed beyond its type, and `source_item` holds it as asserted. An integer slot given text with no
    integer form (empty, "n.d.", a range "2011–2014", prose) has no value in that type: None, so the slot stays absent,
    the text stays in `source_item`, and squiddy's docs/evidence/sq022b/year_not_integer.jsonl lists every such item
    (SQ-022b found 8 of 356 asserted years). A boolean, a list or a structure in an integer slot is a type confusion,
    not text, and fails loud. (SQ-022 found `year` written "2024" where the extractor and the old store had 2024.)"""
    kind = _declared(cls.model_fields[slot].annotation)
    if kind is list:
        vals = value if isinstance(value, list) else json.loads(value) if isinstance(value, str) and value.startswith("[") else [value]
        return [str(v) for v in vals]
    if kind is bool:
        return bool(value)
    if kind is int:
        if isinstance(value, bool):
            raise SystemExit(f"FATAL: {cls.__name__}.{slot} is an integer slot and was given the boolean {value!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            s = value.strip()
            return int(s) if s.lstrip("-").isdigit() else None
        raise SystemExit(f"FATAL: {cls.__name__}.{slot} is an integer slot and was given {type(value).__name__} "
                         f"{value!r} (DN-050 R-221)")
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
    renamed = {**RENAMED, **((graph.domain.get("airkg_schema") or {}).get("renamed_extra") or {})}
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
            slot = renamed.get(k, k)
            if v is None or k in OWNED or slot in kw or slot not in fields:
                continue
            kw[slot] = _coerce(cls, slot, v)
        # DI-003, DN-050 R-220: the derived annotation, by the source projection's own rule over the item's final
        # quote (after any relocation overlay, which the adopter has applied) and its name; true or absent. A name
        # is any truthy value, as `_spans` records it (scripts/build_projection.py, the node branch of `kg_replay`)
        name = c["props"].get("name")
        if "grounding_thin" in fields and name and \
                _projection(graph).is_thin_span(c["props"].get("grounding_span"), name):
            kw["grounding_thin"] = True
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
