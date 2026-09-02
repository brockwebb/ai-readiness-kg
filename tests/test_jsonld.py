"""In-page JSON-LD reading and its normalization to DCAT field names, plus the
metadata probes scoring a page through it.

The normalization is a rename, never an upgrade: a field absent from the markup
must stay absent, so a thin page scores as thin.
"""
from pathlib import Path

from harness.jsonld import (
    dataset_nodes,
    dcat_record_from_nodes,
    extract_jsonld_blocks,
    has_dataset_markup,
)
from harness.probes.d3_metadata_standard import MetadataStandardProbe
from harness.probes.d4_license import LicenseProbe
from harness.records import SOURCE_CATALOG, SOURCE_SITEMAP, Score

from tests.helpers import fetched

FIXTURES = Path(__file__).parent / "fixtures"

DATASET_PAGE = (FIXTURES / "page_with_dataset_jsonld.html").read_text()
FAQ_PAGE = (FIXTURES / "page_with_faq_jsonld.html").read_text()
CATALOG_PAGE = (FIXTURES / "page_with_catalog_graph_jsonld.html").read_text()


# --- extraction -------------------------------------------------------------
def test_extracts_a_dataset_node():
    nodes = dataset_nodes(DATASET_PAGE)
    assert len(nodes) == 1
    assert nodes[0]["name"] == "Resident Population Estimates"


def test_page_with_no_jsonld_yields_no_nodes():
    assert dataset_nodes("<html><body>nothing here</body></html>") == []


def test_organization_and_faq_markup_is_not_dataset_markup():
    """The live census.gov QuickFacts shape (2026-09-02): a page can carry JSON-LD
    and still describe none of its data. Markup present is not markup relevant."""
    blocks, failures = extract_jsonld_blocks(FAQ_PAGE)
    assert blocks and failures == 0
    assert dataset_nodes(FAQ_PAGE) == []
    assert has_dataset_markup(dataset_nodes(FAQ_PAGE)) is False


def test_datacatalog_inside_a_graph_is_found_but_is_not_dataset_markup():
    nodes = dataset_nodes(CATALOG_PAGE)
    assert len(nodes) == 1
    assert nodes[0]["name"] == "Example Data Catalog"
    # The completeness signal counts pages describing a dataset, not pages
    # pointing at a catalog.
    assert has_dataset_markup(nodes) is False


def test_malformed_jsonld_block_is_counted_not_raised():
    html = '<script type="application/ld+json">{not json,,}</script>'
    blocks, failures = extract_jsonld_blocks(html)
    assert blocks == []
    assert failures == 1


# --- normalization ----------------------------------------------------------
def test_dataset_node_maps_to_dcat_field_names():
    record = dcat_record_from_nodes(dataset_nodes(DATASET_PAGE))
    assert record["title"] == "Resident Population Estimates"
    assert record["description"].startswith("Annual resident population")
    assert record["keyword"] == ["population", "estimates", "demographics"]
    assert record["publisher"] == {"name": "Example Statistical Agency"}
    assert record["license"] == "https://creativecommons.org/publicdomain/zero/1.0/"
    assert record["modified"] == "2026-08-01"
    assert record["_jsonld_types"] == ["dataset"]


def test_comma_separated_keywords_string_becomes_a_list():
    record = dcat_record_from_nodes(dataset_nodes(CATALOG_PAGE))
    assert record["keyword"] == ["open data", "catalog"]


def test_usage_info_maps_to_rights_not_license():
    """Freeform page prose is rights prose, not a resolvable license."""
    record = dcat_record_from_nodes(dataset_nodes(CATALOG_PAGE))
    assert "license" not in record
    assert record["rights"] == "Public domain, attribution appreciated."


def test_absent_fields_stay_absent():
    nodes = [{"@type": "Dataset", "name": "Bare"}]
    record = dcat_record_from_nodes(nodes)
    assert record["title"] == "Bare"
    for absent in ("description", "keyword", "publisher", "license", "modified"):
        assert absent not in record


def test_no_dataset_level_node_yields_an_empty_record():
    assert dcat_record_from_nodes(dataset_nodes(FAQ_PAGE)) == {}


def test_dataset_is_preferred_over_datacatalog():
    nodes = [{"@type": "DataCatalog", "name": "Catalog"},
             {"@type": "Dataset", "name": "The dataset"}]
    assert dcat_record_from_nodes(nodes)["title"] == "The dataset"


# --- the probes reading a page through it -----------------------------------
def test_metadata_standard_passes_a_page_with_full_dataset_markup():
    score, evidence = MetadataStandardProbe().evaluate_page(
        fetched("https://x.gov/tables/t01.html", body=DATASET_PAGE))
    assert score == Score.PASS
    assert "JSON-LD" in evidence


def test_metadata_standard_fails_a_page_with_no_dataset_markup_and_says_so():
    """FAIL for absent markup must be distinguishable from FAIL for thin markup."""
    score, evidence = MetadataStandardProbe().evaluate_page(
        fetched("https://x.gov/quickfacts/US", body=FAQ_PAGE))
    assert score == Score.FAIL
    assert "no in-page JSON-LD" in evidence


def test_metadata_standard_partial_on_thin_markup_names_what_it_read():
    thin = ('<script type="application/ld+json">'
            '{"@type":"Dataset","name":"T","description":"d"}</script>')
    score, evidence = MetadataStandardProbe().evaluate_page(
        fetched("https://x.gov/t", body=thin))
    assert score == Score.PARTIAL
    assert "scored the node typed dataset" in evidence


def test_license_probe_reads_the_pages_license_field():
    score, _ = LicenseProbe().evaluate_page(
        fetched("https://x.gov/tables/t01.html", body=DATASET_PAGE))
    assert score == Score.PASS


def test_license_probe_partial_on_page_rights_prose():
    score, _ = LicenseProbe().evaluate_page(
        fetched("https://x.gov/catalog", body=CATALOG_PAGE))
    assert score == Score.PARTIAL


# --- applicability declaration ---------------------------------------------
def test_metadata_probes_that_read_pages_declare_the_sitemap_source():
    for probe in (MetadataStandardProbe(), LicenseProbe()):
        assert probe.applies_to(SOURCE_SITEMAP)
        assert probe.applies_to(SOURCE_CATALOG)
