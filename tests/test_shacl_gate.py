"""SHACL gate candidate (task 2026-08-23_trustgraph_benchmark Phase 6; DD-018).

Covers the two schema->RDF generators (class/property counts against the real kg/schema.yaml)
and the gate's positive control on a tiny synthetic graph: pure rdflib/pyshacl, no event log,
no Neo4j, no model. Skipped, not failed, when rdflib/pyshacl are absent (they are optional
deps: the anaconda python carries them, the stdlib-only CI profile does not).
"""
import sys
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
pyshacl = pytest.importorskip("pyshacl")

from rdflib import Graph, Literal, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, SH  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "benchmarks" / "trustgraph"))
sys.path.insert(0, str(REPO / "scripts"))

import schema_to_owl  # noqa: E402
import schema_to_shacl  # noqa: E402
import run_shacl_gate  # noqa: E402

NS = schema_to_owl.NS


@pytest.fixture(scope="module")
def schema():
    return schema_to_owl.load_schema()


@pytest.fixture(scope="module")
def shapes_graph(schema):
    return schema_to_shacl.build_shapes(schema)


def test_owl_class_and_property_counts_match_schema(schema, tmp_path):
    out = tmp_path / "airkg_schema.ttl"
    schema_to_owl.build_ontology(schema).serialize(destination=str(out), format="turtle")
    counts = schema_to_owl.fidelity_check(out, schema)
    assert counts["classes"] == len(schema["node_types"])
    assert counts["object_properties"] == len(schema["edge_types"])
    g = Graph().parse(out, format="turtle")
    # every node type is a named owl:Class with the schema's `what` as its comment
    for name, spec in schema["node_types"].items():
        assert (NS[name], RDF.type, OWL.Class) in g
        assert g.value(NS[name], rdflib.RDFS.comment) == Literal(spec["what"])
    # symmetric edges and alignment URIs are carried
    assert (NS.conflicts_with, RDF.type, OWL.SymmetricProperty) in g
    assert g.value(NS.subtype_of, rdflib.RDFS.seeAlso) == URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")


def test_shacl_shape_counts_match_schema(schema, shapes_graph, tmp_path):
    out = tmp_path / "airkg_shapes.ttl"
    shapes_graph.serialize(destination=str(out), format="turtle")
    counts = schema_to_shacl.fidelity_check(out, schema)
    assert counts["node_shapes"] == len(schema["node_types"])
    assert counts["class_constraints"] == sum(len(s["pairs"]) for s in schema["edge_types"].values())
    assert counts["required_constraints"] == 1   # Claim.evidence_grade (DD-010)


def _tiny_graph():
    """Doc -defines-> Definition, Doc -asserts-> Claim(evidence_grade ok): conforms."""
    g = Graph()
    doc, defn, claim, c1, c2 = (URIRef(f"urn:t:{x}") for x in ("doc", "def", "claim", "c1", "c2"))
    g.add((doc, RDF.type, NS.Document))
    g.add((doc, NS.source_type, Literal("federal")))
    g.add((defn, RDF.type, NS.Definition))
    g.add((claim, RDF.type, NS.Claim))
    g.add((claim, NS.evidence_grade, Literal("inference")))
    g.add((claim, NS.prov_schema_version, Literal("0.3")))
    for c in (c1, c2):
        g.add((c, RDF.type, NS.Concept))
    g.add((doc, NS.defines, defn))
    g.add((doc, NS.asserts, claim))
    g.add((claim, NS.about, c1))
    g.add((c1, NS.subtype_of, c2))
    return g


GATE = {"enabled": False, "shapes": "benchmarks/trustgraph/airkg_shapes.ttl",
        "threshold_unknown_violations": 0,
        "known_violation_classes": [
            {"name": "dangling_cites_endpoint_untyped"},
            {"name": "required_property_predates_schema", "schema_versions_exempt": ["0.1", "0.2"]}]}


def test_conforming_synthetic_graph_has_no_violations(shapes_graph):
    ev = run_shacl_gate.evaluate(_tiny_graph(), shapes_graph, run_shacl_gate.build_classifiers(GATE))
    assert ev["conforms"] is True
    assert ev["violations_total"] == 0
    assert ev["unknown_violations"] == 0


def test_mutation_positive_control_fires_gate(shapes_graph):
    """Seed one bad-typed edge (Concept -defines-> Concept); it must be an UNKNOWN-class violation."""
    g = _tiny_graph()
    mutation = run_shacl_gate.seed_mutation(g)
    assert mutation["edge"] == "defines"
    ev = run_shacl_gate.evaluate(g, shapes_graph, run_shacl_gate.build_classifiers(GATE))
    assert ev["conforms"] is False
    assert ev["unknown_violations"] == 1
    assert ev["unknown_violations"] > GATE["threshold_unknown_violations"]
    assert ev["groups"][0]["shape"] == "ConceptShape/defines"
    assert ev["groups"][0]["component"] == "MaxCountConstraintComponent"


def test_wrong_target_class_fires_gate(shapes_graph):
    """Legal source, illegal target: Document -defines-> Concept is a sh:class violation, unknown."""
    g = _tiny_graph()
    g.add((URIRef("urn:t:doc"), NS.defines, URIRef("urn:t:c1")))
    ev = run_shacl_gate.evaluate(g, shapes_graph, run_shacl_gate.build_classifiers(GATE))
    assert ev["unknown_violations"] == 1
    assert ev["groups"][0]["component"] == "ClassConstraintComponent"


def test_known_classes_are_recognised_by_predicate(shapes_graph):
    g = _tiny_graph()
    doc = URIRef("urn:t:doc")
    g.add((doc, NS.cites, URIRef("urn:t:never-manifested")))        # untyped cites endpoint
    old = URIRef("urn:t:oldclaim")
    g.add((old, RDF.type, NS.Claim))
    g.add((old, NS.prov_schema_version, Literal("0.2")))              # pre-0.3 Claim, no grade
    g.add((doc, NS.asserts, old))
    ev = run_shacl_gate.evaluate(g, shapes_graph, run_shacl_gate.build_classifiers(GATE))
    assert ev["violations_total"] == 2
    assert ev["unknown_violations"] == 0
    assert ev["violations_by_class"] == {"dangling_cites_endpoint_untyped": 1,
                                         "required_property_predates_schema": 1}


def test_post_03_claim_without_grade_is_unknown(shapes_graph):
    """The exemption is by schema version, not by shape: a 0.3 Claim lacking the grade is unknown."""
    g = _tiny_graph()
    new = URIRef("urn:t:newclaim")
    g.add((new, RDF.type, NS.Claim))
    g.add((new, NS.prov_schema_version, Literal("0.3")))
    ev = run_shacl_gate.evaluate(g, shapes_graph, run_shacl_gate.build_classifiers(GATE))
    assert ev["unknown_violations"] == 1


def test_enum_violation_is_unknown(shapes_graph):
    g = _tiny_graph()
    g.set((URIRef("urn:t:doc"), NS.source_type, Literal("blog")))
    ev = run_shacl_gate.evaluate(g, shapes_graph, run_shacl_gate.build_classifiers(GATE))
    assert ev["unknown_violations"] == 1
    assert ev["groups"][0]["component"] == "InConstraintComponent"


def test_committed_gate_config_is_off_and_names_implemented_classes():
    gate = run_shacl_gate.load_gate_config()
    assert gate["enabled"] is False
    assert gate["threshold_unknown_violations"] == 0
    assert (REPO / gate["shapes"]).is_file()
    run_shacl_gate.build_classifiers(gate)   # raises if a declared class has no classifier
