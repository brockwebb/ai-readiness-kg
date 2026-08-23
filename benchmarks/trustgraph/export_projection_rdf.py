#!/usr/bin/env python3
"""Event log -> RDF projection, no Neo4j (task 2026-08-23_trustgraph_benchmark, Phase 6).

A second disposable projection of the same source of truth (CLAUDE.md invariant 1). It
IMPORTS the overlay logic from scripts/build_projection.py (read_overlays, is_projectable,
annotation_update, NULLABLE_ATTRIBUTES, _scalar_props) rather than re-implementing it, so the
RDF view and the Neo4j view cannot drift on what counts as projectable.

IRI scheme (recorded departure from the Neo4j projection): extracted item ids are
DOC-SCOPED -- 600 of 6,988 ids recur across documents (profiled 2026-08-23) -- so a node IRI
is  <ns>doc/<doc_id>/<item_id>  and a Document is  <ns>doc/<doc_id>.  The Neo4j projection
MERGEs on bare id and therefore fuses same-id items across documents; this export does not.
Edge endpoints are resolved by the event's from_type/to_type: Document -> document IRI,
anything else -> doc-scoped IRI under the asserting document.

Emitted:
  rdf:type airkg:<Type>          per node (Documents from manifest_add)
  airkg:<prop> literal           per scalar item field (lists -> one literal each; nested ->
                                 JSON string, as _scalar_props does)
  prov:wasDerivedFrom <doc>      extracted node -> its document
  airkg:prov_* literals          model_id / schema_version / source_sha256 / extraction_event_id
  airkg:<edge> <to>              per edge (edge grounding_span is NOT carried: a plain triple
                                 has no slot for it; reification was not needed for the
                                 type-conformance question this export serves)
Overlays applied exactly as build_projection.build does: superseded extractions dropped,
endpoint aliases rewritten, document_annotation -> typed literal, grounding_relocated and
attribute_nulled applied LAST.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, XSD

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kg import eventlog  # noqa: E402
import build_projection as bp  # noqa: E402
from schema_to_owl import NS, NS_URI, BOOLEAN_PROPERTIES, load_schema  # noqa: E402

DEFAULT_OUT = REPO / "benchmarks" / "trustgraph" / "projection.ttl"
DOC = Namespace(NS_URI.replace("schema#", "doc/"))


def doc_iri(doc_id: str) -> URIRef:
    return DOC[quote(doc_id, safe="")]


def item_iri(doc_id: str, item_id: str) -> URIRef:
    return DOC[quote(doc_id, safe="") + "/" + quote(str(item_id), safe="")]


def endpoint_iri(end_type: str | None, end_id: str, doc_id: str, aliases: dict) -> URIRef:
    end_id = aliases.get(end_id, end_id)
    if end_type == "Document" or end_type is None and end_id in aliases.values():
        return doc_iri(end_id)
    return item_iri(doc_id, end_id)


def _literal(value):
    if isinstance(value, bool):
        return Literal(value, datatype=XSD.boolean)
    return Literal(value)


def _add_props(g: Graph, node: URIRef, props: dict) -> None:
    for k, v in props.items():
        if v is None:
            continue
        if isinstance(v, list):
            for x in v:
                g.add((node, NS[k], _literal(x)))
        else:
            g.add((node, NS[k], _literal(v)))


def export(events=None, schema: dict | None = None) -> tuple[Graph, dict]:
    """Build the RDF graph. `events` defaults to the live untagged replay (twice: overlays
    are read first by build_projection.read_overlays, then the main pass)."""
    schema = schema or load_schema()
    kg_labels = set(schema["node_types"])
    edge_whitelist = set(schema["edge_types"])
    g = Graph()
    g.bind("airkg", NS)
    g.bind("doc", DOC)
    g.bind("prov", PROV)
    counts = {k: 0 for k in ("documents", "nodes", "edges", "annotations", "overlays_relocated",
                             "overlays_nulled", "skipped_unknown_edge_type",
                             "skipped_superseded_extraction", "skipped_non_graph_purpose",
                             "aliased_endpoints", "skipped_unknown_node_type")}
    superseded, aliases = bp.read_overlays()
    stream = list(eventlog.replay()) if events is None else list(events)

    for ev in stream:
        et = ev.get("event_type")
        if not bp.is_projectable(ev):
            counts["skipped_non_graph_purpose"] += 1
            continue
        ann = bp.annotation_update(ev)
        if ann is not None:
            d, prop, value = ann
            g.add((doc_iri(d), NS[prop], _literal(value)))
            counts["annotations"] += 1
            continue
        if et in ("node_asserted", "edge_asserted"):
            src_sha = (ev.get("provenance") or {}).get("source_sha256")
            if (ev.get("doc_id"), src_sha) in superseded:
                counts["skipped_superseded_extraction"] += 1
                continue
        if et == "manifest_add":
            p = ev["payload"]
            d = doc_iri(p["doc_id"])
            g.add((d, RDF.type, NS.Document))
            _add_props(g, d, {"doc_id": p["doc_id"], "title": p.get("title"),
                              "authors": p.get("authors"), "source_type": p.get("source_type"),
                              "pub_date": p.get("pub_date"), "primary_url": p.get("primary_url"),
                              "content_hash": p.get("content_hash"),
                              "manifest_event_id": ev.get("event_id")})
            counts["documents"] += 1
        elif et == "node_asserted":
            p = ev["payload"]
            label = p.get("type")
            if label not in kg_labels:
                counts["skipped_unknown_node_type"] += 1
                continue
            n = item_iri(ev["doc_id"], p["id"])
            g.add((n, RDF.type, NS[label]))
            props = bp._scalar_props(p.get("item", {}))
            props.pop("id", None)
            props.pop("type", None)
            _add_props(g, n, props)
            prov = ev.get("provenance", {})
            _add_props(g, n, {"prov_model_id": prov.get("model_id"),
                              "prov_schema_version": prov.get("schema_version"),
                              "prov_source_sha256": prov.get("source_sha256"),
                              "prov_extraction_event_id": prov.get("extraction_event_id")})
            g.add((n, PROV.wasDerivedFrom, doc_iri(ev["doc_id"])))
            counts["nodes"] += 1
        elif et in ("edge_asserted", "curated_promotion"):
            p = ev["payload"] if et == "edge_asserted" else ev
            rel = p.get("type") if et == "edge_asserted" else p.get("edge")
            if rel not in edge_whitelist:
                counts["skipped_unknown_edge_type"] += 1
                continue
            for end in (p["from_id"], p["to_id"]):
                if end in aliases:
                    counts["aliased_endpoints"] += 1
            a = endpoint_iri(p.get("from_type"), p["from_id"], ev["doc_id"], aliases)
            b = endpoint_iri(p.get("to_type"), p["to_id"], ev["doc_id"], aliases)
            g.add((a, NS[rel], b))
            counts["edges"] += 1

    # Repair overlays LAST, as build_projection does.
    for ev in stream:
        et = ev.get("event_type")
        if et == "grounding_relocated":
            n = item_iri(ev["doc_id"], ev["item_id"])
            g.remove((n, NS.grounding_span, None))
            g.add((n, NS.grounding_span, Literal(ev["new_span"])))
            g.add((n, NS.grounding_relocated_from, Literal(ev["old_span"])))
            g.add((n, NS.grounding_relocation_method, Literal(ev["method"])))
            counts["overlays_relocated"] += 1
        elif et == "attribute_nulled":
            attr = ev["attribute"]
            if attr not in bp.NULLABLE_ATTRIBUTES:
                continue
            n = item_iri(ev["doc_id"], ev["item_id"])
            g.remove((n, NS[attr], None))
            g.add((n, NS.nulled_attributes, Literal(attr)))
            counts["overlays_nulled"] += 1
    counts["triples"] = len(g)
    return g, counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    g, counts = export()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(args.out), format="turtle")
    print(json.dumps({"out": str(args.out), "counts": counts}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
