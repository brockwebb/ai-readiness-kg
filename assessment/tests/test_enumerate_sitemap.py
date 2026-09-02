"""Web-surface enumeration from a declared sitemap: parsing, drift, failure
recording, deduplication, and seeded stratified sampling.

Ported behavior from census-web-concept-inventory stage 01; these tests pin the
three disciplines that came with it (follow robots.txt and record drift, a failed
child is recorded not fatal, counts reconcile) plus the sampling contract this
harness adds.
"""
from pathlib import Path

import pytest

from harness.enumerate_sitemap import (
    enumerate_web_surfaces,
    parse_robots_sitemaps,
    parse_sitemap_index,
    parse_urlset,
    resolve_sitemap_url,
    sample_sections,
    section_of,
)
from harness.records import SOURCE_SITEMAP

from tests.helpers import FakeFetcher, fetched

FIXTURES = Path(__file__).parent / "fixtures"

INDEX_URL = "https://x.gov/sitemapindex/sitemap.xml"
TABLES = "https://x.gov/sitemapindex/tables.xml"
PUBS = "https://x.gov/sitemapindex/publications.xml"
QF = "https://x.gov/quickfacts/fact/sitemap/US/PST045217"

ROBOTS = f"User-agent: *\nDisallow: /search-results.html\n\nSITEMAP: {INDEX_URL}\n"


def _sitemap_responses(qf_status=200, qf_body=""):
    return {
        INDEX_URL: fetched(INDEX_URL, body=(FIXTURES / "sitemap_index.xml").read_text()),
        TABLES: fetched(TABLES, body=(FIXTURES / "sitemap_tables.xml").read_text()),
        PUBS: fetched(PUBS, body=(FIXTURES / "sitemap_publications.xml").read_text()),
        QF: fetched(QF, status=qf_status, body=qf_body),
    }


# --- robots.txt parsing -----------------------------------------------------
def test_robots_sitemap_directive_is_case_insensitive():
    """census.gov emits SITEMAP: uppercase, the case a naive reader misses."""
    assert parse_robots_sitemaps(ROBOTS) == [INDEX_URL]
    assert parse_robots_sitemaps("sitemap: https://y.gov/s.xml") == ["https://y.gov/s.xml"]


def test_robots_with_no_sitemap_directive_yields_nothing():
    assert parse_robots_sitemaps("User-agent: *\nDisallow:\n") == []


# --- which sitemap is followed ---------------------------------------------
def test_robots_declaration_is_followed_over_configured_value_and_drift_recorded():
    url, source, drift = resolve_sitemap_url(ROBOTS, "https://x.gov/old-sitemap.xml")
    assert url == INDEX_URL
    assert source == "robots.txt"
    assert "old-sitemap.xml" in drift and INDEX_URL in drift


def test_configured_value_is_the_fallback_when_robots_declares_none():
    url, source, drift = resolve_sitemap_url("User-agent: *\n", INDEX_URL)
    assert (url, source) == (INDEX_URL, "config")
    assert "no Sitemap directive" in drift


def test_no_sitemap_anywhere_is_recorded_not_raised():
    result = enumerate_web_surfaces(FakeFetcher({}), robots_body="User-agent: *\n")
    assert result.has_sitemap is False
    assert result.targets == []
    assert "no sitemap declared" in result.note


# --- sitemap document parsing ----------------------------------------------
def test_parse_sitemap_index_returns_children_in_order():
    children = parse_sitemap_index((FIXTURES / "sitemap_index.xml").read_text())
    assert children == [TABLES, PUBS, QF]


def test_parse_sitemap_index_rejects_a_urlset():
    with pytest.raises(ValueError):
        parse_sitemap_index((FIXTURES / "sitemap_tables.xml").read_text())


def test_parse_urlset_keeps_lastmod_as_written():
    entries = parse_urlset((FIXTURES / "sitemap_tables.xml").read_text())
    assert ("https://x.gov/tables/t01.html", "2026-02-01") in entries
    # A <url> with no <lastmod> yields None rather than a fabricated date.
    pubs = dict(parse_urlset((FIXTURES / "sitemap_publications.xml").read_text()))
    assert pubs["https://x.gov/publications/p01.html"] is None


def test_section_label_is_the_child_sitemap_stem():
    assert section_of(TABLES) == "tables"
    # The QuickFacts child has no extension; the last path segment is the label,
    # matching the section names in the prior-art universe.
    assert section_of(QF) == "PST045217"


# --- sampling ---------------------------------------------------------------
def test_sample_is_stratified_per_section_and_capped():
    entries = {
        "tables": [(f"https://x.gov/tables/t{i}.html", None) for i in range(20)],
        "small": [("https://x.gov/small/only.html", None)],
    }
    sampled = sample_sections(entries, sample_per_section=3, seed=1)
    by_section = {}
    for t in sampled:
        by_section.setdefault(t["section"], []).append(t["url"])
    assert len(by_section["tables"]) == 3
    # A section smaller than the sample size contributes what it has, not an error.
    assert len(by_section["small"]) == 1
    assert all(t["source"] == SOURCE_SITEMAP for t in sampled)


def test_same_seed_redraws_the_same_pages():
    entries = {"tables": [(f"https://x.gov/t{i}.html", None) for i in range(50)]}
    a = sample_sections(entries, 4, seed=20260901)
    b = sample_sections(entries, 4, seed=20260901)
    c = sample_sections(entries, 4, seed=7)
    assert [t["url"] for t in a] == [t["url"] for t in b]
    assert [t["url"] for t in a] != [t["url"] for t in c]


def test_one_section_disappearing_does_not_shift_another_sections_draw():
    """Each section draws from its own stream, so a section that 403s does not
    silently change which pages every other section contributes."""
    full = {
        "alpha": [(f"https://x.gov/a{i}.html", None) for i in range(30)],
        "beta": [(f"https://x.gov/b{i}.html", None) for i in range(30)],
    }
    reduced = {"beta": full["beta"]}
    drawn_full = [t["url"] for t in sample_sections(full, 3, 5) if t["section"] == "beta"]
    drawn_reduced = [t["url"] for t in sample_sections(reduced, 3, 5)]
    assert drawn_full == drawn_reduced


# --- end-to-end enumeration -------------------------------------------------
def test_enumerates_sections_and_samples_each():
    fetcher = FakeFetcher(_sitemap_responses(
        qf_body='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://x.gov/quickfacts/fact/table/US/PST045217</loc></url>'
                '</urlset>'))
    result = enumerate_web_surfaces(fetcher, ROBOTS, sample_per_section=2, seed=1)
    assert result.has_sitemap is True
    assert result.sitemap_url_source == "robots.txt"
    assert result.sections_total == 3
    assert result.sections_parsed == 3
    assert set(result.per_section_sampled) == {"tables", "publications", "PST045217"}
    # The QuickFacts section has one URL, so it contributes one.
    assert result.per_section_sampled["PST045217"] == 1
    assert len(result.targets) == 5


def test_duplicate_url_across_sections_is_counted_once():
    fetcher = FakeFetcher(_sitemap_responses(qf_status=404))
    result = enumerate_web_surfaces(fetcher, ROBOTS, sample_per_section=50, seed=1)
    # tables lists 9 URLs, publications lists 5, one URL is in both.
    assert result.universe_total == 13
    assert result.duplicate_count == 1
    urls = [t["url"] for t in result.targets]
    assert len(urls) == len(set(urls))


def test_refused_child_sitemap_is_recorded_and_the_walk_continues():
    """A 403 on a child sitemap is a barrier observation, not a crash. This is the
    live census.gov case: the QuickFacts child refused the harness on 2026-09-02."""
    fetcher = FakeFetcher(_sitemap_responses(qf_status=403, qf_body="Forbidden"))
    result = enumerate_web_surfaces(fetcher, ROBOTS, sample_per_section=2, seed=1)
    assert result.has_sitemap is True
    assert result.sections_total == 3
    assert result.sections_parsed == 2
    assert len(result.child_failures) == 1
    failure = result.child_failures[0]
    assert failure["section"] == "PST045217"
    assert failure["status"] == 403
    assert "403" in failure["reason"]
    # The other two sections still produced targets.
    assert len(result.targets) == 4


def test_child_that_is_not_a_urlset_is_recorded_not_raised():
    responses = _sitemap_responses()
    responses[QF] = fetched(QF, status=200, body="<html>not a sitemap</html>")
    result = enumerate_web_surfaces(FakeFetcher(responses), ROBOTS,
                                    sample_per_section=2, seed=1)
    assert result.sections_parsed == 2
    assert result.child_failures[0]["section"] == "PST045217"
    assert result.child_failures[0]["status"] == 200


def test_unreachable_sitemap_index_is_recorded_not_raised():
    responses = _sitemap_responses()
    responses[INDEX_URL] = fetched(INDEX_URL, status=403, body="Forbidden")
    result = enumerate_web_surfaces(FakeFetcher(responses), ROBOTS)
    assert result.has_sitemap is False
    assert result.targets == []
    assert "403" in result.note


def test_flat_urlset_at_the_sitemap_url_is_treated_as_one_section():
    """A site with no sitemap index still has a web surface; do not report zero."""
    url = "https://y.gov/sitemap.xml"
    responses = {url: fetched(url, body=(FIXTURES / "sitemap_tables.xml").read_text())}
    result = enumerate_web_surfaces(FakeFetcher(responses),
                                    robots_body=f"Sitemap: {url}",
                                    sample_per_section=2, seed=1)
    assert result.has_sitemap is True
    assert result.sections_total == 1
    assert len(result.targets) == 2


def test_max_sections_caps_the_walk():
    fetcher = FakeFetcher(_sitemap_responses(qf_status=404))
    result = enumerate_web_surfaces(fetcher, ROBOTS, sample_per_section=1,
                                    max_sections=1, seed=1)
    assert result.sections_total == 3
    assert result.sections_parsed == 1
    assert len(result.targets) == 1
