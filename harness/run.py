"""Harness orchestrator + CLI.

Runs the probe set against an agency's public surface, emits per-target scored
records (with raw evidence on disk) and a per-agency rollup that keeps the core
composite and the two frontier tracks separate.

Reproducible by anyone with a browser + Python: public endpoints only, no auth, no
API keys, zero third-party dependencies. That reproducibility is the design's
source of authority.

Traceability: the core-vs-frontier split each probe declares (via Track) traces to
icsp_notebook task 51fe4574, flagship term "AI-ready data" — Part A = core,
Part B (llms.txt / MCP / WebMCP) = frontier.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .config import load_agencies, load_harness_config
from .enumerate_targets import parse_catalog
from .evidence import EvidenceStore
from .fetch import HttpFetcher
from .records import ProbeResult

# --- Probe registry --------------------------------------------------------
from .probes.d1_robots import RobotsProbe
from .probes.d1_sitemap import SitemapProbe
from .probes.d1_catalog import CatalogProbe
from .probes.frontier_llms_txt import LlmsTxtProbe
from .probes.frontier_mcp import McpProbe
from .probes.d3_metadata_standard import MetadataStandardProbe
from .probes.d3_provenance import ProvenanceProbe
from .probes.d3_schema import SchemaProbe
from .probes.d3_access_tier import AccessTierProbe
from .probes.d4_versioning import VersioningProbe
from .probes.d4_cadence import CadenceProbe
from .probes.d4_license import LicenseProbe
from .probes.d4_integrity import IntegrityProbe
from .probes.d1_stable_urls import StableUrlProbe
from .probes.d2_programmatic import ProgrammaticAccessProbe
from .probes.d2_content_negotiation import ContentNegotiationProbe
from .probes.d2_bulk import BulkAvailabilityProbe
from .probes.d2_no_barriers import NoBarriersProbe
from .rollup import rollup_agency

# Site probes fetch a well-known path off base_url (run once per agency).
SITE_PROBES = [RobotsProbe(), SitemapProbe(), CatalogProbe(), LlmsTxtProbe(), McpProbe()]

# Metadata probes score a DCAT dataset record (pure; run per dataset).
METADATA_PROBES = [
    MetadataStandardProbe(), ProvenanceProbe(), SchemaProbe(), AccessTierProbe(),
    VersioningProbe(), CadenceProbe(), LicenseProbe(), IntegrityProbe(),
]

# Distribution probes fetch one endpoint (run per distribution).
DISTRIBUTION_PROBES = [
    StableUrlProbe(), ProgrammaticAccessProbe(), ContentNegotiationProbe(),
    BulkAvailabilityProbe(), NoBarriersProbe(),
]

# Accept header that favors machine formats (drives content negotiation).
_MACHINE_ACCEPT = "application/json, text/csv, application/xml;q=0.9, */*;q=0.1"


def _record(probe, target, score, evidence_text, timestamp, evidence_path) -> ProbeResult:
    return ProbeResult(
        probe_id=probe.probe_id,
        target=target,
        dimension=probe.dimension,
        track=probe.track,
        score=score,
        as_of_date=probe.track.as_of_date,
        evidence=evidence_text,
        timestamp=timestamp,
        evidence_path=evidence_path,
    )


def run_agency(agency: dict, fetcher, evidence_store: EvidenceStore, timestamp: str,
               max_datasets: int = 50, max_dists_per_dataset: int = 3) -> dict:
    """Probe one agency end-to-end. Returns results, rollup, and enumeration meta."""
    agency_id = agency["id"]
    base_url = agency["base_url"].rstrip("/")
    catalog_url = agency.get("catalog_url") or f"{base_url}/data.json"
    results: List[ProbeResult] = []

    # Fetch the catalog once; reuse it for both the D1 catalog probe and enumeration.
    catalog_fetched = fetcher.get(catalog_url, accept="application/json")

    # --- Site probes (once per agency) ---
    for probe in SITE_PROBES:
        url = probe.url_for(base_url)
        if probe.probe_id == "d1_catalog" and url == catalog_url:
            f = catalog_fetched
        else:
            f = fetcher.get(url)
        score, ev = probe.evaluate(f)
        path = evidence_store.write(agency_id, probe.probe_id, url, f.evidence_text())
        results.append(_record(probe, url, score, ev, timestamp, path))

    # --- Enumerate targets from the catalog ---
    enum = parse_catalog(catalog_fetched.body, base_url)
    datasets = []
    if enum.has_machine_readable_catalog:
        try:
            datasets = json.loads(catalog_fetched.body).get("dataset", []) or []
        except (json.JSONDecodeError, ValueError):
            datasets = []

    datasets_probed = datasets[:max_datasets]

    # --- Per-dataset metadata probes + per-distribution endpoint probes ---
    for ds in datasets_probed:
        if not isinstance(ds, dict):
            continue
        ds_id = ds.get("identifier") or ds.get("title") or "dataset"
        for probe in METADATA_PROBES:
            score, ev = probe.evaluate(ds)
            evidence_text = (
                f"DATASET: {ds_id}\nPROBE: {probe.probe_id}\nVERDICT: {ev}\n\n"
                f"RECORD:\n{json.dumps(ds, indent=2, default=str)}"
            )
            path = evidence_store.write(agency_id, probe.probe_id, str(ds_id), evidence_text)
            results.append(_record(probe, str(ds_id), score, ev, timestamp, path))

        for dist in (ds.get("distribution", []) or [])[:max_dists_per_dataset]:
            if not isinstance(dist, dict):
                continue
            url = dist.get("downloadURL") or dist.get("accessURL")
            if not url:
                continue
            f = fetcher.get(url, accept=_MACHINE_ACCEPT)
            for probe in DISTRIBUTION_PROBES:
                score, ev = probe.evaluate(f, dist)
                path = evidence_store.write(agency_id, probe.probe_id, url, f.evidence_text())
                results.append(_record(probe, url, score, ev, timestamp, path))

    rollup = rollup_agency(agency_id, results)
    enumeration = {
        "catalog_url": catalog_url,
        "has_machine_readable_catalog": enum.has_machine_readable_catalog,
        "note": enum.note,
        "datasets_total": len(datasets),
        "datasets_probed": len(datasets_probed),
        "candidate_endpoints": len(enum.targets),
    }
    return {"results": results, "rollup": rollup, "enumeration": enumeration,
            "agency": {"id": agency_id, "name": agency.get("name", "")}}


def _write_outputs(out_dir: Path, agency_id: str, agency_run: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = [r.to_dict() for r in agency_run["results"]]
    (out_dir / f"{agency_id}_records.json").write_text(
        json.dumps(records, indent=2))
    (out_dir / f"{agency_id}_rollup.json").write_text(
        json.dumps({"agency": agency_run["agency"],
                    "enumeration": agency_run["enumeration"],
                    "rollup": agency_run["rollup"]}, indent=2))


def main(argv=None) -> int:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="FSS AI Data Readiness probe harness")
    parser.add_argument("--config-dir", default=str(repo / "config"))
    parser.add_argument("--output-dir", default=str(repo / "results"))
    parser.add_argument("--agency", action="append", default=None,
                        help="agency id(s) to run (default: all in agencies.toml)")
    parser.add_argument("--max-datasets", type=int, default=25)
    parser.add_argument("--max-dists-per-dataset", type=int, default=2)
    parser.add_argument("--list", action="store_true", help="list configured agencies and exit")
    args = parser.parse_args(argv)

    config_dir = Path(args.config_dir)
    cfg = load_harness_config(config_dir / "harness.toml")
    agencies = load_agencies(config_dir / "agencies.toml")

    if args.list:
        for a in agencies:
            print(f"{a['id']:10s} {a['name']}  -> {a.get('catalog_url', a['base_url'])}")
        return 0

    if args.agency:
        wanted = set(args.agency)
        agencies = [a for a in agencies if a["id"] in wanted]
        if not agencies:
            parser.error(f"no configured agency matched {sorted(wanted)}")

    fetcher = HttpFetcher(
        user_agent=cfg.user_agent,
        timeout_seconds=cfg.timeout_seconds,
        max_retries=cfg.max_retries,
        politeness_delay_seconds=cfg.politeness_delay_seconds,
        max_body_bytes=cfg.max_body_bytes,
    )
    evidence_store = EvidenceStore(root=Path(cfg.evidence_root),
                                   max_bytes=cfg.max_evidence_bytes)
    out_dir = Path(args.output_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for agency in agencies:
        print(f"[{agency['id']}] probing {agency['base_url']} ...")
        run = run_agency(agency, fetcher, evidence_store, timestamp,
                         max_datasets=args.max_datasets,
                         max_dists_per_dataset=args.max_dists_per_dataset)
        _write_outputs(out_dir, agency["id"], run)
        roll = run["rollup"]
        enum = run["enumeration"]
        print(f"  catalog: {'yes' if enum['has_machine_readable_catalog'] else 'NO (D1 finding)'}"
              f"  datasets probed: {enum['datasets_probed']}/{enum['datasets_total']}")
        print(f"  core composite: {roll['core_composite']}/{roll['core_composite_max']}"
              f"  | frontier_near: {roll['frontier_near']['score']}/{roll['frontier_near']['max']}"
              f"  | frontier_deep: {roll['frontier_deep']['score']}/{roll['frontier_deep']['max']}")
        print(f"  wrote {out_dir / (agency['id'] + '_records.json')} and _rollup.json")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
