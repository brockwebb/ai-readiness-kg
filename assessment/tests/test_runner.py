"""End-to-end orchestration of one agency against a fake catalog + endpoints,
exercised without the network via FakeFetcher."""
import json

from harness.config import load_harness_config
from harness.records import SOURCE_CATALOG, SOURCE_SITE, SOURCE_SITEMAP, Track
from harness.evidence import EvidenceStore
from harness.run import (
    run_agency, ProbeSettings, SITE_PROBE_IDS, METADATA_PROBES, DISTRIBUTION_PROBES,
)

from tests.helpers import FakeFetcher, fetched

# Probe tunables come from the real harness.toml, the way main() builds them.
CONFIG_DIR = __import__("pathlib").Path(__file__).resolve().parent.parent / "config"
SETTINGS = ProbeSettings.from_config(load_harness_config(CONFIG_DIR / "harness.toml"))

BASE = "https://x.gov"
CATALOG = {
    "dataset": [
        {
            "title": "Population",
            "description": "estimates",
            "keyword": ["pop"],
            "modified": "2026-01-01",
            "publisher": {"name": "X"},
            "accessLevel": "public",
            "license": "https://x.gov/cc0",
            "accrualPeriodicity": "R/P1Y",
            "distribution": [
                {"mediaType": "text/csv", "downloadURL": f"{BASE}/pop.csv",
                 "describedBy": f"{BASE}/pop-schema.json"},
            ],
        }
    ]
}


def _responses():
    return {
        f"{BASE}/robots.txt": fetched(f"{BASE}/robots.txt",
            body="User-agent: *\nAllow: /\nSitemap: https://x.gov/sitemap.xml\n"),
        f"{BASE}/sitemap.xml": fetched(f"{BASE}/sitemap.xml",
            body='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://x.gov/a</loc></url></urlset>'),
        f"{BASE}/data.json": fetched(f"{BASE}/data.json",
            headers={"Content-Type": "application/json"}, body=json.dumps(CATALOG)),
        f"{BASE}/llms.txt": fetched(f"{BASE}/llms.txt", status=404, body=""),
        f"{BASE}/.well-known/mcp.json": fetched(f"{BASE}/.well-known/mcp.json",
            status=404, body=""),
        f"{BASE}/pop.csv": fetched(f"{BASE}/pop.csv",
            headers={"Content-Type": "text/csv"}, body="a,b\n1,2\n"),
    }


def test_run_agency_produces_results_rollup_and_evidence(tmp_path):
    agency = {"id": "x", "name": "X Agency", "base_url": BASE,
              "catalog_url": f"{BASE}/data.json"}
    store = EvidenceStore(root=tmp_path)
    fetcher = FakeFetcher(_responses())

    out = run_agency(agency, fetcher, store, settings=SETTINGS, timestamp="2026-06-23T00:00:00Z",
                     max_datasets=10, max_dists_per_dataset=10)

    results = out["results"]
    rollup = out["rollup"]

    # Every probe family ran.
    probe_ids = {r.probe_id for r in results}
    for pid in SITE_PROBE_IDS:
        assert pid in probe_ids
    for p in METADATA_PROBES:
        assert p.probe_id in probe_ids
    for p in DISTRIBUTION_PROBES:
        assert p.probe_id in probe_ids

    # Every result carries a timestamp and a written evidence file.
    for r in results:
        assert r.timestamp == "2026-06-23T00:00:00Z"
        assert r.evidence_path
        assert __import__("pathlib").Path(r.evidence_path).exists()

    # Core composite is populated; frontier reported separately (both 404 -> 0).
    assert rollup["core_composite"] > 0
    assert rollup["frontier_near"]["score"] == 0
    assert rollup["frontier_deep"]["score"] == 0
    assert rollup["frontier_near"]["as_of_date"] == "2024-09"

    # A passing core probe never leaked into a frontier track and vice versa.
    frontier_ids = {r.probe_id for r in results if r.track is not Track.CORE}
    assert frontier_ids == {"frontier_llms_txt", "frontier_mcp"}


def test_run_agency_records_missing_catalog_as_d1_finding(tmp_path):
    agency = {"id": "y", "name": "Y", "base_url": BASE, "catalog_url": f"{BASE}/data.json"}
    store = EvidenceStore(root=tmp_path)
    # data.json returns HTML (no machine-readable catalog).
    resp = _responses()
    resp[f"{BASE}/data.json"] = fetched(f"{BASE}/data.json", status=200,
                                        headers={"Content-Type": "text/html"},
                                        body="<html>landing</html>")
    fetcher = FakeFetcher(resp)
    out = run_agency(agency, fetcher, store, settings=SETTINGS, timestamp="2026-06-23T00:00:00Z")
    assert out["enumeration"]["has_machine_readable_catalog"] is False
    # The harness keeps going and still reports site probes — it does not crash.
    assert any(r.probe_id == "d1_catalog" for r in out["results"])


def test_max_datasets_caps_dataset_probing(tmp_path):
    big = {"dataset": [dict(CATALOG["dataset"][0], title=f"d{i}") for i in range(5)]}
    agency = {"id": "z", "name": "Z", "base_url": BASE, "catalog_url": f"{BASE}/data.json"}
    resp = _responses()
    resp[f"{BASE}/data.json"] = fetched(f"{BASE}/data.json",
        headers={"Content-Type": "application/json"}, body=json.dumps(big))
    store = EvidenceStore(root=tmp_path)
    out = run_agency(agency, FakeFetcher(resp), store,
                     settings=SETTINGS, timestamp="2026-06-23T00:00:00Z", max_datasets=2)
    # Only 2 of 5 datasets probed -> metadata probe instances run 2x each on the
    # CATALOG source. d4_license also runs on web-surface pages (a different
    # source, a different denominator), so the count is scoped to the source the
    # cap governs.
    meta_runs = [r for r in out["results"]
                 if r.probe_id == "d4_license" and r.source == SOURCE_CATALOG]
    assert len(meta_runs) == 2
    assert out["enumeration"]["datasets_probed"] == 2
    assert out["enumeration"]["datasets_total"] == 5


# --- Second enumeration source, end to end ----------------------------------
FIXTURES = __import__("pathlib").Path(__file__).parent / "fixtures"

SITEMAP_INDEX = f"{BASE}/sitemapindex/sitemap.xml"
WEB_ROBOTS = (f"User-agent: *\nAllow: /\nSITEMAP: {SITEMAP_INDEX}\n")

DATASET_PAGE = (FIXTURES / "page_with_dataset_jsonld.html").read_text()
FAQ_PAGE = (FIXTURES / "page_with_faq_jsonld.html").read_text()


def _web_responses(page_status=200, page_body=None, extra_pages=None):
    """Catalog fixtures plus a one-section sitemap listing two product pages."""
    body = FAQ_PAGE if page_body is None else page_body
    resp = _responses()
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body=WEB_ROBOTS)
    resp[SITEMAP_INDEX] = fetched(
        SITEMAP_INDEX,
        body='<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
             f'<sitemap><loc>{BASE}/sitemapindex/products.xml</loc></sitemap>'
             '</sitemapindex>')
    resp[f"{BASE}/sitemapindex/products.xml"] = fetched(
        f"{BASE}/sitemapindex/products.xml",
        body='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
             f'<url><loc>{BASE}/quickfacts/US</loc></url>'
             f'<url><loc>{BASE}/tables/t01.html</loc></url>'
             '</urlset>')
    for page in (f"{BASE}/quickfacts/US", f"{BASE}/tables/t01.html"):
        resp[page] = fetched(page, status=page_status,
                             headers={"Content-Type": "text/html"}, body=body)
    resp.update(extra_pages or {})
    return resp


def _web_agency():
    return {"id": "w", "name": "W Agency", "base_url": BASE,
            "catalog_url": f"{BASE}/data.json",
            "sitemap_url": SITEMAP_INDEX}


def test_web_surface_pages_are_probed_and_kept_out_of_the_catalog_composite(tmp_path):
    store = EvidenceStore(root=tmp_path)
    out = run_agency(_web_agency(), FakeFetcher(_web_responses()), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)

    web_results = [r for r in out["results"] if r.source == SOURCE_SITEMAP]
    assert {r.target for r in web_results} == {f"{BASE}/quickfacts/US",
                                              f"{BASE}/tables/t01.html"}
    # Only the probes that declare the sitemap source ran on the pages.
    assert {r.probe_id for r in web_results} == {
        "d1_stable_urls", "d1_robots_directives", "d2_no_barriers",
        "d2_content_negotiation", "d3_metadata_standard", "d4_license"}

    roll = out["rollup"]
    assert roll["web_surface"]["n_targets"] == 2
    assert roll["n_probes_web_surface"] == len(web_results)
    # Catalog composite counts no web-surface result.
    assert roll["n_probes_core"] + roll["n_probes_frontier"] \
        + roll["n_probes_web_surface"] == roll["n_probes_total"]


def test_a_refusing_web_surface_diverges_from_a_clean_catalog(tmp_path):
    """The finding the second source exists to surface: the catalog D2 vector is
    perfect while every sampled page is refused."""
    store = EvidenceStore(root=tmp_path)
    resp = _web_responses(page_status=403, page_body="Forbidden")
    out = run_agency(_web_agency(), FakeFetcher(resp), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)
    roll = out["rollup"]
    catalog_d2 = roll["core_dimension_vectors"]["D2"]
    web_d2 = roll["web_surface"]["core_dimension_vectors"]["D2"]
    assert catalog_d2["score"] == catalog_d2["max"]
    assert web_d2["score"] == 0
    assert web_d2["max"] > 0
    barriers = [r for r in out["results"]
                if r.probe_id == "d2_no_barriers" and r.source == SOURCE_SITEMAP]
    assert all("refusal_fraction=1.00" in r.evidence for r in barriers)


def test_barrier_probe_fetches_n_times_and_evidence_holds_every_attempt(tmp_path):
    store = EvidenceStore(root=tmp_path)
    fetcher = FakeFetcher(_web_responses())
    out = run_agency(_web_agency(), fetcher, store, settings=SETTINGS, timestamp="2026-09-01T00:00:00Z",
                     no_barriers_attempts=3, sitemap_sample_per_section=1,
                     sitemap_sample_seed=1)
    page = [r for r in out["results"]
            if r.probe_id == "d2_no_barriers" and r.source == SOURCE_SITEMAP][0]
    assert "attempts=3" in page.evidence
    # Each attempt is a real fetch, and every one is written to the evidence file.
    fetches = [u for u, _ in fetcher.calls if u == page.target]
    assert len(fetches) == 3
    written = __import__("pathlib").Path(page.evidence_path).read_text()
    assert written.count("ATTEMPT") == 3


def test_catalog_completeness_signal_is_evidence_only_with_its_denominator(tmp_path):
    """A page carrying Dataset markup that no distribution references is catalog
    fragmentation. It is emitted with a denominator and never scored."""
    store = EvidenceStore(root=tmp_path)
    resp = _web_responses(page_body=DATASET_PAGE)
    out = run_agency(_web_agency(), FakeFetcher(resp), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)
    signal = out["enumeration"]["web_surface"]["catalog_completeness"]
    assert signal["evidence_only"] is True and signal["scored"] is False
    assert signal["applicable"] is True
    assert signal["denominator_value"] == 2
    assert signal["pages_absent_from_catalog"] == 2
    assert signal["fraction_absent_from_catalog"] == 1.0
    # No probe was created from it.
    assert not any(r.probe_id.startswith("catalog_completeness")
                   for r in out["results"])


def test_completeness_fraction_is_null_when_no_page_carries_dataset_markup(tmp_path):
    """A zero denominator must read as not measurable, never as a clean 0.0."""
    store = EvidenceStore(root=tmp_path)
    out = run_agency(_web_agency(), FakeFetcher(_web_responses(page_body=FAQ_PAGE)),
                     store, settings=SETTINGS, timestamp="2026-09-01T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)
    signal = out["enumeration"]["web_surface"]["catalog_completeness"]
    assert signal["denominator_value"] == 0
    assert signal["fraction_absent_from_catalog"] is None


def test_a_page_that_is_in_the_catalog_is_not_counted_as_absent(tmp_path):
    store = EvidenceStore(root=tmp_path)
    catalog = {"dataset": [dict(CATALOG["dataset"][0], distribution=[
        {"mediaType": "text/html", "accessURL": f"{BASE}/tables/t01.html"}])]}
    resp = _web_responses(page_body=DATASET_PAGE)
    resp[f"{BASE}/data.json"] = fetched(f"{BASE}/data.json",
        headers={"Content-Type": "application/json"}, body=json.dumps(catalog))
    out = run_agency(_web_agency(), FakeFetcher(resp), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)
    signal = out["enumeration"]["web_surface"]["catalog_completeness"]
    assert signal["denominator_value"] == 2
    assert signal["pages_absent_from_catalog"] == 1
    assert signal["examples_absent_from_catalog"] == [f"{BASE}/quickfacts/US"]


def test_unreachable_sitemap_section_is_recorded_and_the_run_continues(tmp_path):
    store = EvidenceStore(root=tmp_path)
    resp = _web_responses()
    resp[f"{BASE}/sitemapindex/products.xml"] = fetched(
        f"{BASE}/sitemapindex/products.xml", status=403, body="Forbidden")
    out = run_agency(_web_agency(), FakeFetcher(resp), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z", sitemap_sample_seed=1)
    web = out["enumeration"]["web_surface"]
    assert web["enumerated"] is True
    assert web["sections_parsed"] == 0
    assert web["child_failures"][0]["status"] == 403
    assert web["pages_probed"] == 0
    # The catalog side still produced a full result set.
    assert out["rollup"]["core_composite"] > 0


def test_sitemap_enumeration_can_be_switched_off(tmp_path):
    store = EvidenceStore(root=tmp_path)
    out = run_agency(_web_agency(), FakeFetcher(_web_responses()), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z", enumerate_sitemap=False)
    assert out["enumeration"]["web_surface"]["enumerated"] is False
    assert not any(r.source == SOURCE_SITEMAP for r in out["results"])


def test_site_probe_results_carry_the_site_source(tmp_path):
    store = EvidenceStore(root=tmp_path)
    out = run_agency(_web_agency(), FakeFetcher(_web_responses()), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z", sitemap_sample_seed=1)
    robots = next(r for r in out["results"] if r.probe_id == "d1_robots")
    assert robots.source == SOURCE_SITE


def test_sitemap_url_drift_against_the_recorded_expectation_is_reported(tmp_path):
    store = EvidenceStore(root=tmp_path)
    agency = dict(_web_agency(), sitemap_url=f"{BASE}/old/sitemap.xml")
    out = run_agency(agency, FakeFetcher(_web_responses()), store,
                     settings=SETTINGS, timestamp="2026-09-01T00:00:00Z", sitemap_sample_seed=1)
    web = out["enumeration"]["web_surface"]
    assert web["sitemap_url"] == SITEMAP_INDEX
    assert web["sitemap_url_source"] == "robots.txt"
    assert "old/sitemap.xml" in web["sitemap_url_drift"]
