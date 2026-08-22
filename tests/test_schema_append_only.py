"""Append-only invariant (schema_v0.1.md §6, task 2026-08-21_v03_visibility_kernel Phase 1):
everything in schema v0.2 — node types, each node's properties, edge types, and each edge's
legal `pairs` — must be a STRICT subset of what the live kg/schema.yaml declares. The v0.2
catalogue is hardcoded here as the frozen reference on purpose: the test must not read its
baseline from the file it is checking."""
from kg.extraction import schema_loader

SCHEMA = schema_loader.load_schema()

V02_NODE_PROPERTIES = {
    "Document": ["doc_id", "title", "authors", "pub_date", "source_type", "primary_url",
                 "content_hash", "manifest_event_id"],
    "Definition": ["term", "verbatim_text", "grounding_span", "normative_status", "as_of_date"],
    "Concept": ["name", "aliases", "description", "grounding_span"],
    "Construct": ["name", "description", "measurement_notes"],
    "Instrument": ["name", "owner", "year", "method"],
    "Measure": ["text", "response_type", "grounding_span"],
    "Claim": ["claim_text", "grounding_span", "claim_type"],
    "Standard": ["name", "version", "steward", "as_of_date"],
    "Framework": ["name", "owner", "year"],
}

V02_PROPERTY_VALUES = {
    ("Document", "source_type"): ["federal", "academic", "industry", "standard", "intergovernmental"],
    ("Definition", "normative_status"): ["statute", "policy", "standard", "academic", "industry"],
    ("Claim", "claim_type"): ["empirical", "normative", "speculative"],
}

V02_EDGE_PAIRS = {
    "defines": [("Document", "Definition")],
    "mentions": [("Document", "Concept")],
    "asserts": [("Document", "Claim")],
    "about": [("Claim", "Concept")],
    "operationalizes": [("Instrument", "Construct")],
    "measures": [("Measure", "Construct"), ("Measure", "Concept"), ("Instrument", "Concept")],
    "grounds": [("Construct", "Definition")],
    "extends": [("Definition", "Definition"), ("Framework", "Framework")],
    "conflicts_with": [("Definition", "Definition"), ("Claim", "Claim")],
    "cites": [("Document", "Document")],
    "builds_on": [("Standard", "Standard"), ("Standard", "Framework"),
                  ("Framework", "Standard"), ("Framework", "Framework")],
    "implements": [("Standard", "Concept")],
    "uses_measure": [("Instrument", "Measure")],
    "has_component": [("Framework", "Concept"), ("Concept", "Concept")],
    "subtype_of": [("Concept", "Concept")],
    "precedes": [("Concept", "Concept")],
}

V02_SYMMETRIC = {"conflicts_with"}

V02_PROVENANCE = ["grounding_span", "location", "extraction_event_id", "model_id",
                  "schema_version", "timestamp"]


def test_version_advanced_past_v02():
    major, minor = (int(x) for x in SCHEMA["schema_version"].split(".")[:2])
    assert (major, minor) >= (0, 3)


def test_v02_node_types_strict_subset():
    live = schema_loader.node_types(SCHEMA)
    assert set(V02_NODE_PROPERTIES) < live, "v0.2 node types must be a STRICT subset"


def test_v02_node_properties_preserved():
    for ntype, props in V02_NODE_PROPERTIES.items():
        live_props = SCHEMA["node_types"][ntype]["properties"]
        assert set(props) <= set(live_props), f"{ntype} lost a v0.2 property"


def test_v02_property_values_preserved():
    for (ntype, prop), values in V02_PROPERTY_VALUES.items():
        live = schema_loader.property_values(SCHEMA, ntype)[prop]
        assert set(values) <= set(live), f"{ntype}.{prop} lost a v0.2 enum value"
        # ordering of the frozen prefix is preserved too (descending-strength enums rely on it)
        assert live[:len(values)] == values, f"{ntype}.{prop} reordered the v0.2 enum"


def test_v02_edge_types_strict_subset():
    live = set(schema_loader.edge_types(SCHEMA))
    assert set(V02_EDGE_PAIRS) < live, "v0.2 edge types must be a STRICT subset"


def test_v02_edge_pairs_preserved():
    for etype, pairs in V02_EDGE_PAIRS.items():
        live = set(schema_loader.legal_pairs(SCHEMA, etype))
        assert set(pairs) <= live, f"{etype} lost a v0.2 legal pair"
        for a, b in pairs:
            assert schema_loader.is_valid_endpoint(SCHEMA, etype, a, b)


def test_v02_symmetry_preserved():
    for etype in V02_SYMMETRIC:
        assert SCHEMA["edge_types"][etype].get("symmetric") is True


def test_v02_provenance_preserved():
    assert set(V02_PROVENANCE) <= set(schema_loader.provenance_required(SCHEMA))


def test_every_live_edge_has_pairs_and_known_endpoints():
    # new edges must obey the same machine-enforced contract as the old ones
    live_nodes = schema_loader.node_types(SCHEMA)
    for etype in schema_loader.edge_types(SCHEMA):
        pairs = schema_loader.legal_pairs(SCHEMA, etype)
        assert pairs, f"{etype} has no pairs"
        for a, b in pairs:
            assert a in live_nodes and b in live_nodes, f"{etype} pair {a}->{b} names unknown type"
