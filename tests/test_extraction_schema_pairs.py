"""schema_loader strict index-pairing: legal pairs enforced, cross pairs rejected."""
from kg.extraction import schema_loader

SCHEMA = schema_loader.load_schema()


def test_single_pair_edges():
    assert schema_loader.is_valid_endpoint(SCHEMA, "defines", "Document", "Definition")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "defines", "Concept", "Definition")


def test_extends_is_index_paired_not_cross():
    assert schema_loader.is_valid_endpoint(SCHEMA, "extends", "Definition", "Definition")
    assert schema_loader.is_valid_endpoint(SCHEMA, "extends", "Framework", "Framework")
    # cross pairs are illegal
    assert not schema_loader.is_valid_endpoint(SCHEMA, "extends", "Definition", "Framework")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "extends", "Framework", "Definition")


def test_builds_on_is_cross_product():
    for a in ("Standard", "Framework"):
        for b in ("Standard", "Framework"):
            assert schema_loader.is_valid_endpoint(SCHEMA, "builds_on", a, b)


def test_conflicts_with_symmetric_same_type_pairs():
    assert schema_loader.is_valid_endpoint(SCHEMA, "conflicts_with", "Definition", "Definition")
    assert schema_loader.is_valid_endpoint(SCHEMA, "conflicts_with", "Claim", "Claim")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "conflicts_with", "Definition", "Claim")


def test_unknown_edge_has_no_valid_endpoint():
    assert not schema_loader.is_valid_endpoint(SCHEMA, "correlates_with", "Concept", "Concept")


def test_every_edge_has_pairs_metadata():
    for etype in schema_loader.edge_types(SCHEMA):
        assert schema_loader.legal_pairs(SCHEMA, etype), f"{etype} missing pairs"


# --- v0.2 edges ----------------------------------------------------------------------

def test_v02_uses_measure():
    assert schema_loader.is_valid_endpoint(SCHEMA, "uses_measure", "Instrument", "Measure")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "uses_measure", "Measure", "Instrument")


def test_v02_measures_extended_endpoints():
    for a, b in [("Measure", "Construct"), ("Measure", "Concept"), ("Instrument", "Concept")]:
        assert schema_loader.is_valid_endpoint(SCHEMA, "measures", a, b)
    assert not schema_loader.is_valid_endpoint(SCHEMA, "measures", "Instrument", "Construct")


def test_v02_has_component_part_whole():
    assert schema_loader.is_valid_endpoint(SCHEMA, "has_component", "Framework", "Concept")
    assert schema_loader.is_valid_endpoint(SCHEMA, "has_component", "Concept", "Concept")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "has_component", "Concept", "Framework")


def test_v02_subtype_and_precedes():
    assert schema_loader.is_valid_endpoint(SCHEMA, "subtype_of", "Concept", "Concept")
    assert schema_loader.is_valid_endpoint(SCHEMA, "precedes", "Concept", "Concept")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "subtype_of", "Framework", "Concept")


def test_schema_version_is_v02():
    assert SCHEMA["schema_version"] == "0.2"


def test_v02_edges_carry_external_alignment():
    for etype in ("uses_measure", "measures", "has_component", "subtype_of", "precedes"):
        assert SCHEMA["edge_types"][etype].get("external_alignment"), f"{etype} missing alignment"
