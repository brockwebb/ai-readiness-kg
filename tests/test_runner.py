"""End-to-end orchestration of one agency against a fake catalog + endpoints,
exercised without the network via FakeFetcher."""
import json

from harness.records import Track
from harness.evidence import EvidenceStore
from harness.run import run_agency, SITE_PROBES, METADATA_PROBES, DISTRIBUTION_PROBES

from tests.helpers import FakeFetcher, fetched

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

    out = run_agency(agency, fetcher, store, timestamp="2026-06-23T00:00:00Z",
                     max_datasets=10, max_dists_per_dataset=10)

    results = out["results"]
    rollup = out["rollup"]

    # Every probe family ran.
    probe_ids = {r.probe_id for r in results}
    for p in SITE_PROBES:
        assert p.probe_id in probe_ids
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
    out = run_agency(agency, fetcher, store, timestamp="2026-06-23T00:00:00Z")
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
                     timestamp="2026-06-23T00:00:00Z", max_datasets=2)
    # Only 2 of 5 datasets probed -> metadata probe instances run 2x each.
    meta_runs = [r for r in out["results"] if r.probe_id == "d4_license"]
    assert len(meta_runs) == 2
    assert out["enumeration"]["datasets_probed"] == 2
    assert out["enumeration"]["datasets_total"] == 5
