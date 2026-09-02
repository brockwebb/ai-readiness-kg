"""D0-r2 defect 3: d1_catalog scored presence and validity, not coverage.
census.gov/data.json scored PASS with 1,798 distributions all on api.census.gov
and zero references to QuickFacts, 21.8% of the site's own sitemap universe. The
coverage of the sitemap universe by the catalog is now an observed fact with a
numerator and a denominator, per section, and it does not change the score."""
import json
from pathlib import Path

from harness.enumerate_sitemap import WebSurfaceResult
from harness.probes.d1_catalog import CatalogProbe
from harness.records import Score
from harness.evidence import EvidenceStore
from harness.run import catalog_reference_urls, catalog_sitemap_coverage, run_agency

from tests.helpers import FakeFetcher, fetched
from tests.test_runner import SETTINGS, _responses, BASE

FIXTURES = Path(__file__).parent / "fixtures"
CATALOG = json.loads((FIXTURES / "data_json_census_shaped.json").read_text())
ROBOTS = (FIXTURES / "robots_census_shaped.txt").read_text()
INDEX = "https://x.gov/sitemapindex/sitemap.xml"
QF_CHILD = "https://x.gov/quickfacts/fact/sitemap/US/PST045217"
TABLES_CHILD = "https://x.gov/sitemapindex/tables.xml"

QF_URLS = [f"{BASE}/quickfacts/fact/table/US/PST045225",
           f"{BASE}/quickfacts/fact/table/CA/PST045225",
           f"{BASE}/quickfacts/fact/table/NY/PST045225"]
TABLE_URLS = [f"{BASE}/tables/t01.html", f"{BASE}/tables/t02.html"]


def _web():
    return WebSurfaceResult(has_sitemap=True, sitemap_url=INDEX,
                            universe_by_section={"PST045217": QF_URLS, "tables": TABLE_URLS},
                            universe_total=5, sections_total=2, sections_parsed=2)


# --- the pure fact ------------------------------------------------------------------
def test_catalog_reference_urls_include_distributions_and_landing_pages():
    urls = catalog_reference_urls(CATALOG["dataset"])
    assert "api.x.gov/data/pep" in urls and "api.x.gov/data/ecn.csv" in urls
    assert "x.gov/tables/t01.html" in urls  # landingPage
    assert len(urls) == 4


def test_census_shaped_catalog_covers_one_of_five_and_a_whole_section_is_at_zero():
    fact = catalog_sitemap_coverage(CATALOG["dataset"], True, _web())
    assert fact["evidence_only"] is True and fact["scored"] is False
    assert fact["applicable"] is True
    assert fact["numerator_value"] == 1 and fact["denominator_value"] == 5
    assert fact["fraction_in_catalog"] == 0.2
    assert fact["per_section"]["PST045217"] == {"sitemap_urls": 3, "in_catalog": 0, "fraction": 0.0}
    assert fact["per_section"]["tables"] == {"sitemap_urls": 2, "in_catalog": 1, "fraction": 0.5}
    assert fact["sections_with_zero_coverage"] == ["PST045217"]


def test_matching_ignores_scheme_case_and_trailing_slash():
    web = WebSurfaceResult(has_sitemap=True, universe_by_section={
        "t": ["HTTP://X.GOV/tables/t01.html/"]})
    fact = catalog_sitemap_coverage(CATALOG["dataset"], True, web)
    assert fact["numerator_value"] == 1


def test_zero_denominator_is_null_not_zero():
    fact = catalog_sitemap_coverage(CATALOG["dataset"], True, None)
    assert fact["denominator_value"] == 0
    assert fact["fraction_in_catalog"] is None
    assert fact["applicable"] is False


def test_no_catalog_means_nothing_is_covered_and_the_fact_says_not_applicable():
    fact = catalog_sitemap_coverage([], False, _web())
    assert fact["applicable"] is False
    assert fact["numerator_value"] == 0 and fact["denominator_value"] == 5
    assert fact["fraction_in_catalog"] == 0.0


def test_the_probe_score_is_unchanged_by_coverage():
    f = fetched(f"{BASE}/data.json", body=json.dumps(CATALOG),
                headers={"Content-Type": "application/json"})
    assert CatalogProbe().evaluate(f)[0] == Score.PASS


# --- through the runner ---------------------------------------------------------------
def _responses_with_universe():
    resp = _responses()
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body=ROBOTS)
    resp[f"{BASE}/data.json"] = fetched(f"{BASE}/data.json", body=json.dumps(CATALOG),
                                        headers={"Content-Type": "application/json"})
    resp[INDEX] = fetched(INDEX, body=(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<sitemap><loc>{QF_CHILD}</loc></sitemap><sitemap><loc>{TABLES_CHILD}</loc></sitemap>'
        '</sitemapindex>'))
    for child, urls in ((QF_CHILD, QF_URLS), (TABLES_CHILD, TABLE_URLS)):
        resp[child] = fetched(child, body=(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"))
    for u in QF_URLS + TABLE_URLS:
        resp[u] = fetched(u, headers={"Content-Type": "text/html"}, body="<html>page</html>")
    for u in ("https://api.x.gov/data/pep", "https://api.x.gov/data/ecn",
              "https://api.x.gov/data/ecn.csv"):
        resp[u] = fetched(u, headers={"Content-Type": "application/json"}, body="{}")
    return resp


def _agency():
    return {"id": "c", "name": "C", "base_url": BASE, "catalog_url": f"{BASE}/data.json",
            "sitemap_url": INDEX}


def test_runner_attaches_coverage_to_the_catalog_record_and_the_rollup(tmp_path):
    out = run_agency(_agency(), FakeFetcher(_responses_with_universe()),
                     EvidenceStore(root=tmp_path), settings=SETTINGS,
                     timestamp="2026-09-02T00:00:00Z",
                     sitemap_sample_per_section=1, sitemap_sample_seed=1)
    rec = next(r for r in out["results"] if r.probe_id == "d1_catalog")
    assert rec.score == Score.PASS  # presence and validity, as before
    fact = rec.observations["catalog_sitemap_coverage"]
    # Coverage is over the whole enumerated universe (5), not the sample (2).
    assert fact["denominator_value"] == 5 and fact["numerator_value"] == 1
    assert fact["sections_with_zero_coverage"] == ["PST045217"]
    assert out["enumeration"]["web_surface"]["catalog_coverage"] == fact
    written = Path(rec.evidence_path).read_text()
    assert "CATALOG COVERAGE OF THE SITEMAP UNIVERSE" in written
    # Still no probe was manufactured from it.
    assert not any("coverage" in r.probe_id for r in out["results"])


def test_runner_reports_coverage_not_measurable_without_a_universe(tmp_path):
    out = run_agency(_agency(), FakeFetcher(_responses_with_universe()),
                     EvidenceStore(root=tmp_path), settings=SETTINGS,
                     timestamp="2026-09-02T00:00:00Z", enumerate_sitemap=False)
    rec = next(r for r in out["results"] if r.probe_id == "d1_catalog")
    assert rec.observations["catalog_sitemap_coverage"]["fraction_in_catalog"] is None
    assert "catalog_coverage" not in out["enumeration"]["web_surface"]
