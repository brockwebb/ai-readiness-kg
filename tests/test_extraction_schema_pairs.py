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
