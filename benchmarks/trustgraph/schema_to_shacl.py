#!/usr/bin/env python3
"""kg/schema.yaml -> SHACL shapes (task 2026-08-23_trustgraph_benchmark, Phase 6).

Same script family as schema_to_owl.py; same namespace. Where the OWL can only state union
domain/range, SHACL states the schema's exact, machine-enforced `pairs` (schema.yaml
section 3: strict index-pairing). One sh:NodeShape per node type, sh:targetClass the class:

  for every edge type e and every class C:
     if (C, T1..Tn) are the legal pairs for e  -> sh:property [ sh:path e ; sh:class T1 ]
                                                  (sh:or over sh:class when n > 1)
     else                                       -> sh:property [ sh:path e ; sh:maxCount 0 ]
  The maxCount-0 leg is what makes a bad-SOURCE edge (a `defines` out of a Concept) fire at
  all: without it, an edge type absent from C's shape would pass silently. With it the shape
  set is closed over the edge whitelist, exactly like the parser.
  enum property (property_values)  -> sh:property [ sh:path p ; sh:in (values) ]
  required_properties              -> sh:property [ sh:path p ; sh:minCount 1 ]
  is_platform_operator             -> sh:datatype xsd:boolean (schema v0.3.1)

Usage: python3 benchmarks/trustgraph/schema_to_shacl.py [--schema ...] [--out ...]
Prints a fidelity check (node shapes == node types; sh:class/or legs == sum over pairs).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace
from rdflib.collection import Collection
from rdflib.namespace import RDF, RDFS, SH, XSD

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_to_owl import BOOLEAN_PROPERTIES, DEFAULT_SCHEMA, NS, NS_URI, REPO, load_schema  # noqa: E402

DEFAULT_OUT = REPO / "benchmarks" / "trustgraph" / "airkg_shapes.ttl"
SHAPES = Namespace(NS_URI.replace("schema#", "shapes#"))


def _allowed_targets(schema: dict) -> dict[tuple[str, str], list[str]]:
    """(from_class, edge) -> [to_class...] from the authoritative pairs, schema order."""
    out: dict[tuple[str, str], list[str]] = {}
    for edge, spec in schema["edge_types"].items():
        for a, b in spec["pairs"]:
            out.setdefault((a, edge), []).append(b)
    return out


def build_shapes(schema: dict) -> Graph:
    g = Graph()
    g.bind("airkg", NS)
    g.bind("airkgsh", SHAPES)
    g.bind("sh", SH)
    allowed = _allowed_targets(schema)
    edge_names = list(schema["edge_types"])

    for cls_name, spec in schema["node_types"].items():
        shape = SHAPES[cls_name + "Shape"]
        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.targetClass, NS[cls_name]))
        g.add((shape, RDFS.comment, Literal(f"Shape for airkg:{cls_name} generated from kg/schema.yaml v{schema['schema_version']}")))

        for edge in edge_names:
            ps = BNode()
            g.add((shape, SH.property, ps))
            g.add((ps, SH.path, NS[edge]))
            targets = allowed.get((cls_name, edge))
            if targets is None:
                g.add((ps, SH.maxCount, Literal(0)))
                g.add((ps, SH.message, Literal(f"{edge} is not a legal edge out of {cls_name} (schema.yaml pairs)")))
            elif len(targets) == 1:
                g.add((ps, SH["class"], NS[targets[0]]))
                g.add((ps, SH.message, Literal(f"{cls_name} -{edge}-> must target {targets[0]}")))
            else:
                alts = []
                for t in targets:
                    alt = BNode()
                    g.add((alt, SH["class"], NS[t]))
                    alts.append(alt)
                lst = BNode()
                Collection(g, lst, alts)
                g.add((ps, SH["or"], lst))
                g.add((ps, SH.message, Literal(f"{cls_name} -{edge}-> must target one of {', '.join(targets)}")))

        for prop, values in (spec.get("property_values") or {}).items():
            ps = BNode()
            g.add((shape, SH.property, ps))
            g.add((ps, SH.path, NS[prop]))
            lst = BNode()
            Collection(g, lst, [Literal(v) for v in values])
            g.add((ps, SH["in"], lst))
            g.add((ps, SH.message, Literal(f"{cls_name}.{prop} must be one of the schema enum values")))

        for prop in spec.get("required_properties") or []:
            ps = BNode()
            g.add((shape, SH.property, ps))
            g.add((ps, SH.path, NS[prop]))
            g.add((ps, SH.minCount, Literal(1)))
            g.add((ps, SH.message, Literal(f"{cls_name}.{prop} is required (schema.yaml required_properties)")))

        for prop in spec.get("properties") or []:
            if prop in BOOLEAN_PROPERTIES:
                ps = BNode()
                g.add((shape, SH.property, ps))
                g.add((ps, SH.path, NS[prop]))
                g.add((ps, SH.datatype, XSD.boolean))
    return g


def fidelity_check(ttl_path: Path, schema: dict) -> dict:
    g = Graph().parse(ttl_path, format="turtle")
    shapes = set(g.subjects(RDF.type, SH.NodeShape))
    n_class_legs = len(list(g.subject_objects(SH["class"])))
    expected_legs = sum(len(spec["pairs"]) for spec in schema["edge_types"].values())
    n_maxcount0 = sum(1 for _s, o in g.subject_objects(SH.maxCount) if int(o) == 0)
    expected_maxcount0 = len(schema["node_types"]) * len(schema["edge_types"]) - len(_allowed_targets(schema))
    n_in = len(list(g.subject_objects(SH["in"])))
    expected_in = sum(len(spec.get("property_values") or {}) for spec in schema["node_types"].values())
    n_min = len(list(g.subject_objects(SH.minCount)))
    expected_min = sum(len(spec.get("required_properties") or []) for spec in schema["node_types"].values())
    counts = {"node_shapes": len(shapes), "node_types": len(schema["node_types"]),
              "class_constraints": n_class_legs, "schema_pairs": expected_legs,
              "forbidden_edge_constraints": n_maxcount0, "expected_forbidden": expected_maxcount0,
              "enum_constraints": n_in, "schema_enums": expected_in,
              "required_constraints": n_min, "schema_required": expected_min, "triples": len(g)}
    for a, b in (("node_shapes", "node_types"), ("class_constraints", "schema_pairs"),
                 ("forbidden_edge_constraints", "expected_forbidden"),
                 ("enum_constraints", "schema_enums"), ("required_constraints", "schema_required")):
        if counts[a] != counts[b]:
            raise SystemExit(f"FIDELITY FAIL: {a}={counts[a]} != {b}={counts[b]}")
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    schema = load_schema(args.schema)
    g = build_shapes(schema)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(args.out), format="turtle")
    counts = fidelity_check(args.out, schema)
    print(f"wrote {args.out} (schema v{schema['schema_version']})")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
