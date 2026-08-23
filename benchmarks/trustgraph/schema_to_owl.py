#!/usr/bin/env python3
"""kg/schema.yaml -> OWL/Turtle (task 2026-08-23_trustgraph_benchmark, Phase 2).

Deterministic transcription of the single type catalogue (CLAUDE.md invariant 4) into an
OWL ontology TrustGraph's ontology workbench can load. No invention: every class, property,
comment and alignment URI comes from schema.yaml.

Mapping (why each choice):
  node type       -> owl:Class, rdfs:comment = `what`
  node property   -> owl:DatatypeProperty. One property per distinct NAME (schema.yaml reuses
                     `name`, `grounding_span`, `as_of_date` ... across types), rdfs:domain =
                     the declaring class, or owl:unionOf the declaring classes when >1.
                     rdfs:range xsd:string except the schema-declared boolean
                     (Document.is_platform_operator, v0.3.1). Enum values (property_values)
                     are recorded as rdfs:comment on the property; enforcement lives in SHACL
                     (schema_to_shacl.py), not in the OWL.
  edge type       -> owl:ObjectProperty, rdfs:comment = `meaning`; rdfs:domain/range from the
                     authoritative `pairs` list: union of distinct from-types / to-types.
                     LIMITATION (recorded, not hidden): OWL domain/range cannot express the
                     schema's strict index-pairing (e.g. `extends` is Definition->Definition
                     OR Framework->Framework, never Definition->Framework). The OWL admits
                     the cross product; the SHACL shapes enforce the exact pairs.
                     `symmetric: true` -> also owl:SymmetricProperty.
                     `external_alignment` -> rdfs:seeAlso when it is an http(s) URI.

Usage: python3 benchmarks/trustgraph/schema_to_owl.py [--schema kg/schema.yaml] [--out ...]
Prints the fidelity check (re-parse; class count == node types; object-property count ==
edge types) and exits non-zero if it fails.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

REPO = Path(__file__).resolve().parent.parent.parent
NS_URI = "https://brockwebb.github.io/ai-readiness-kg/schema#"
NS = Namespace(NS_URI)
DEFAULT_SCHEMA = REPO / "kg" / "schema.yaml"
DEFAULT_OUT = REPO / "benchmarks" / "trustgraph" / "airkg_schema.ttl"

# The only non-string property the schema declares (v0.3.1 changelog: "boolean, nullable").
BOOLEAN_PROPERTIES = {"is_platform_operator"}


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict:
    schema = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key in ("schema_version", "node_types", "edge_types"):
        if key not in schema:
            raise SystemExit(f"FATAL: {path} lacks required key {key!r}")
    return schema


def _is_uri(value) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _class_expr(g: Graph, classes: list[str]):
    """A single class IRI, or an anonymous owl:unionOf class when several."""
    if len(classes) == 1:
        return NS[classes[0]]
    node = BNode()
    g.add((node, RDF.type, OWL.Class))
    lst = BNode()
    Collection(g, lst, [NS[c] for c in classes])
    g.add((node, OWL.unionOf, lst))
    return node


def build_ontology(schema: dict) -> Graph:
    g = Graph()
    g.bind("airkg", NS)
    g.bind("owl", OWL)
    onto = URIRef(NS_URI.rstrip("#"))
    g.add((onto, RDF.type, OWL.Ontology))
    g.add((onto, OWL.versionInfo, Literal(str(schema["schema_version"]))))
    g.add((onto, RDFS.comment, Literal(
        "Generated from kg/schema.yaml by benchmarks/trustgraph/schema_to_owl.py. "
        "Domain/range are unions over the schema's `pairs`; exact index-pairing is "
        "enforced by airkg_shapes.ttl (SHACL), not here.")))

    # Classes
    declaring: dict[str, list[str]] = {}
    enum_notes: dict[str, list[str]] = {}
    for cls_name, spec in schema["node_types"].items():
        cls = NS[cls_name]
        g.add((cls, RDF.type, OWL.Class))
        g.add((cls, RDFS.label, Literal(cls_name)))
        if spec.get("what"):
            g.add((cls, RDFS.comment, Literal(spec["what"])))
        for prop in spec.get("properties") or []:
            declaring.setdefault(prop, []).append(cls_name)
        for prop, values in (spec.get("property_values") or {}).items():
            enum_notes.setdefault(prop, []).append(f"{cls_name}: {', '.join(values)}")

    # Datatype properties (one per distinct name; schema order of first appearance)
    for prop, classes in declaring.items():
        p = NS[prop]
        g.add((p, RDF.type, OWL.DatatypeProperty))
        g.add((p, RDFS.label, Literal(prop)))
        g.add((p, RDFS.domain, _class_expr(g, classes)))
        g.add((p, RDFS.range, XSD.boolean if prop in BOOLEAN_PROPERTIES else XSD.string))
        if prop in enum_notes:
            g.add((p, RDFS.comment, Literal("Enumerated values -- " + "; ".join(enum_notes[prop]))))

    # Object properties
    for edge_name, spec in schema["edge_types"].items():
        pairs = spec.get("pairs")
        if not pairs:
            raise SystemExit(f"FATAL: edge type {edge_name!r} has no `pairs` (schema invariant)")
        p = NS[edge_name]
        g.add((p, RDF.type, OWL.ObjectProperty))
        g.add((p, RDFS.label, Literal(edge_name)))
        froms = list(dict.fromkeys(a for a, _ in pairs))
        tos = list(dict.fromkeys(b for _, b in pairs))
        g.add((p, RDFS.domain, _class_expr(g, froms)))
        g.add((p, RDFS.range, _class_expr(g, tos)))
        if spec.get("meaning"):
            g.add((p, RDFS.comment, Literal(spec["meaning"])))
        if spec.get("symmetric"):
            g.add((p, RDF.type, OWL.SymmetricProperty))
        if _is_uri(spec.get("external_alignment")):
            g.add((p, RDFS.seeAlso, URIRef(spec["external_alignment"])))
    return g


def fidelity_check(ttl_path: Path, schema: dict) -> dict:
    """Re-parse the emitted Turtle and compare counts to the schema. Raises on mismatch."""
    g = Graph().parse(ttl_path, format="turtle")
    named_classes = {s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)}
    obj_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    dt_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))
    expected_props = {p for spec in schema["node_types"].values() for p in spec.get("properties") or []}
    counts = {
        "classes": len(named_classes), "node_types": len(schema["node_types"]),
        "object_properties": len(obj_props), "edge_types": len(schema["edge_types"]),
        "datatype_properties": len(dt_props), "distinct_property_names": len(expected_props),
        "triples": len(g),
    }
    if counts["classes"] != counts["node_types"]:
        raise SystemExit(f"FIDELITY FAIL: classes {counts['classes']} != node types {counts['node_types']}")
    if counts["object_properties"] != counts["edge_types"]:
        raise SystemExit(f"FIDELITY FAIL: object properties {counts['object_properties']} != edge types {counts['edge_types']}")
    if counts["datatype_properties"] != counts["distinct_property_names"]:
        raise SystemExit("FIDELITY FAIL: datatype property count != distinct schema property names")
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    schema = load_schema(args.schema)
    g = build_ontology(schema)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(args.out), format="turtle")
    counts = fidelity_check(args.out, schema)
    print(f"wrote {args.out} (schema v{schema['schema_version']})")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
