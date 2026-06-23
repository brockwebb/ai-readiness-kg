"""Target enumeration: parse a machine-readable catalog (Project Open Data
data.json / DCAT-US) into candidate public data-asset endpoints. An agency with
no machine-readable catalog is a D1 finding, recorded — not an error."""
from pathlib import Path

from harness.enumerate_targets import parse_catalog

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_distributions_into_candidate_endpoints():
    content = (FIXTURES / "sample_data.json").read_text()
    result = parse_catalog(content, base_url="https://example.gov")
    assert result.has_machine_readable_catalog is True
    urls = {t["url"] for t in result.targets}
    assert "https://example.gov/files/pop-estimates.csv" in urls
    assert "https://api.example.gov/pop-estimates" in urls
    assert "https://example.gov/econ.html" in urls


def test_each_target_carries_dataset_title_and_media_type():
    content = (FIXTURES / "sample_data.json").read_text()
    result = parse_catalog(content, base_url="https://example.gov")
    csv_target = next(
        t for t in result.targets
        if t["url"] == "https://example.gov/files/pop-estimates.csv"
    )
    assert csv_target["media_type"] == "text/csv"
    assert csv_target["dataset_title"] == "Resident Population Estimates"


def test_dataset_without_distribution_yields_no_target_but_does_not_crash():
    content = (FIXTURES / "sample_data.json").read_text()
    result = parse_catalog(content, base_url="https://example.gov")
    # 3 datasets, one with no distribution -> 3 distributions total.
    assert len(result.targets) == 3


def test_non_json_content_flags_no_machine_readable_catalog():
    html = "<!DOCTYPE html><html><body>Open Data Landing Page</body></html>"
    result = parse_catalog(html, base_url="https://example.gov")
    assert result.has_machine_readable_catalog is False
    assert result.targets == []
    # The finding is recorded with a human-readable reason (a D1 signal).
    assert result.note


def test_valid_json_that_is_not_a_catalog_flags_no_catalog():
    result = parse_catalog('{"hello": "world"}', base_url="https://example.gov")
    assert result.has_machine_readable_catalog is False
    assert result.targets == []
