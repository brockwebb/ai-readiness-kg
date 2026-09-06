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


def test_schema_version_is_on_the_current_line():
    """v0.4.0 (2026-09-06, DD-051) adds the ASSESSMENT LAYER and `operationalized_by`.

    This tripwire pins the line so a version bump is a deliberate edit here rather than a
    silent drift. It fired on the 0.3 -> 0.4 bump, which is the behaviour it exists for. The
    v0.3 catalogue itself is not re-asserted here — `tests/test_schema_append_only.py` holds
    the append-only invariant, and duplicating it would give two places to update and one
    place to forget.
    """
    major, minor = (int(x) for x in SCHEMA["schema_version"].split(".")[:2])
    assert (major, minor) == (0, 4), SCHEMA["schema_version"]


def test_v02_edges_carry_external_alignment():
    for etype in ("uses_measure", "measures", "has_component", "subtype_of", "precedes"):
        assert SCHEMA["edge_types"][etype].get("external_alignment"), f"{etype} missing alignment"


# --- v0.3 edges (2026-08-21, AUTH-1 / DD-009) -----------------------------------------

def test_v03_recommends():
    assert schema_loader.is_valid_endpoint(SCHEMA, "recommends", "Document", "Practice")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "recommends", "Practice", "Document")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "recommends", "Document", "Claim")


def test_v03_supported_by():
    assert schema_loader.is_valid_endpoint(SCHEMA, "supported_by", "Practice", "Claim")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "supported_by", "Claim", "Practice")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "supported_by", "Document", "Claim")


def test_v03_implemented_by():
    assert schema_loader.is_valid_endpoint(SCHEMA, "implemented_by", "Measure", "Tool")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "implemented_by", "Tool", "Measure")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "implemented_by", "Instrument", "Tool")


def test_v03_consumes():
    assert schema_loader.is_valid_endpoint(SCHEMA, "consumes", "Platform", "Standard")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "consumes", "Standard", "Platform")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "consumes", "Platform", "Framework")


def test_v03_applies_to_index_paired():
    assert schema_loader.is_valid_endpoint(SCHEMA, "applies_to", "Practice", "Concept")
    assert schema_loader.is_valid_endpoint(SCHEMA, "applies_to", "Measure", "Concept")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "applies_to", "Concept", "Practice")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "applies_to", "Practice", "Construct")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "applies_to", "Tool", "Concept")


def test_v03_targets():
    assert schema_loader.is_valid_endpoint(SCHEMA, "targets", "Practice", "Platform")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "targets", "Platform", "Practice")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "targets", "Measure", "Platform")


def test_v03_supersedes():
    assert schema_loader.is_valid_endpoint(SCHEMA, "supersedes", "Document", "Document")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "supersedes", "Document", "Standard")
    assert not schema_loader.is_valid_endpoint(SCHEMA, "supersedes", "Standard", "Standard")


def test_v03_edges_carry_external_alignment_or_explicit_none():
    # Task rule: a URI where reasonable, else literally `external_alignment: none`. Silent
    # omission is not allowed.
    for etype in ("recommends", "supported_by", "implemented_by", "consumes",
                  "applies_to", "targets", "supersedes"):
        assert "external_alignment" in SCHEMA["edge_types"][etype], f"{etype} missing alignment key"


def test_v03_node_types_present():
    assert {"Practice", "Tool", "Platform"} <= schema_loader.node_types(SCHEMA)


def test_v03_enums_read_from_schema():
    assert schema_loader.property_values(SCHEMA, "Claim")["evidence_grade"] == [
        "peer_reviewed_experiment", "platform_official", "measured_practitioner",
        "practitioner_assertion", "inference"]
    assert schema_loader.property_values(SCHEMA, "Measure")["tier"] == [
        "public", "agency_instrumented", "paid"]
    assert schema_loader.property_values(SCHEMA, "Practice")["scope"] == [
        "dataset", "api", "bulk_file", "tool", "content", "advisory", "site", "any"]
    assert "practitioner" in schema_loader.property_values(SCHEMA, "Document")["source_type"]
    assert schema_loader.required_properties(SCHEMA, "Claim") == ["evidence_grade"]
    assert schema_loader.required_properties(SCHEMA, "Measure") == []
