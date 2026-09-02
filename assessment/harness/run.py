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

from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional, Tuple

from .config import HarnessConfig, load_agencies, load_harness_config
from .crawler_access import (
    effective_crawler_access,
    load_enforced_observations,
    mismatch_warning,
)
from .enumerate_sitemap import enumerate_web_surfaces
from .enumerate_targets import parse_catalog
from .evidence import EvidenceStore
from .fetch import HttpFetcher
from .jsonld import dataset_nodes, dcat_record_from_nodes, has_dataset_markup
from .probes.base import unpack_verdict
from .records import (
    SOURCE_CATALOG,
    SOURCE_SITE,
    SOURCE_SITEMAP,
    ProbeResult,
    Score,
)

# --- Probe registry --------------------------------------------------------
from .probes.d1_robots import RobotsProbe
from .probes.d1_robots_directives import RobotsDirectivesProbe
from .probes.d1_sitemap import SOURCE_ROBOTS, SitemapProbe
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


@dataclass(frozen=True)
class ProbeSettings:
    """The probe tunables a run needs, lifted from harness.toml. Required by
    `run_agency` so no probe is ever built on a value that lives in source."""

    sitemap_stale_after_days: int
    robots_directive_meta_names: Tuple[str, ...]
    robots_blocking_directives: Tuple[str, ...]
    crawler_declared_user_agents: Tuple[str, ...]
    crawler_observe_user_agents: Tuple[str, ...]
    crawler_refusal_statuses: Tuple[int, ...]
    # The identity the harness sends; it is the token whose declared-vs-observed
    # comparison needs no extra request.
    harness_user_agent: str

    @classmethod
    def from_config(cls, cfg: HarnessConfig) -> "ProbeSettings":
        return cls(
            sitemap_stale_after_days=cfg.sitemap_stale_after_days,
            robots_directive_meta_names=tuple(cfg.robots_directive_meta_names),
            robots_blocking_directives=tuple(cfg.robots_blocking_directives),
            crawler_declared_user_agents=tuple(cfg.crawler_declared_user_agents),
            crawler_observe_user_agents=tuple(cfg.crawler_observe_user_agents),
            crawler_refusal_statuses=tuple(cfg.crawler_refusal_statuses),
            harness_user_agent=cfg.user_agent,
        )


# Site probes fetch a well-known path off base_url (run once per agency). Built
# per run because d1_sitemap carries a config threshold.
def site_probes(settings: ProbeSettings) -> list:
    return [RobotsProbe(), SitemapProbe(settings.sitemap_stale_after_days),
            CatalogProbe(), LlmsTxtProbe(), McpProbe()]


# Ids of the site probes, for callers that need the set without a settings object.
SITE_PROBE_IDS = ("d1_robots", "d1_sitemap", "d1_catalog", "frontier_llms_txt",
                  "frontier_mcp")


# Page-level probes run per web-surface page in addition to DISTRIBUTION_PROBES.
# Built per run because the directive vocabulary is config.
def page_probes(settings: ProbeSettings) -> list:
    return [RobotsDirectivesProbe(settings.robots_directive_meta_names,
                                  settings.robots_blocking_directives)]

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

# Accept header that favors machine formats (drives content negotiation). Sent to
# web-surface pages as well: asking an HTML product page for a machine format is
# precisely the content-negotiation test.
_MACHINE_ACCEPT = "application/json, text/csv, application/xml;q=0.9, */*;q=0.1"


def _record(probe, target, score, evidence_text, timestamp, evidence_path,
            source=SOURCE_CATALOG, observations=None) -> ProbeResult:
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
        source=source,
        observations=dict(observations or {}),
    )


def _fetch_attempts(fetcher, url: str, accept: str, n: int,
                    user_agent: Optional[str] = None) -> List:
    """Fetch one target n times. The fetcher enforces the politeness delay between
    calls, so repeated attempts are spaced the same as any other request."""
    return [fetcher.get(url, accept=accept, user_agent=user_agent)
            for _ in range(max(1, n))]


def _attempts_evidence(attempts: List, extra_by_ua: Optional[Dict[str, List]] = None) -> str:
    """Every attempt's raw response, so a refusal fraction is verifiable by eye.
    Attempts sent under other identities follow, labelled by identity."""
    if len(attempts) == 1 and not extra_by_ua:
        return attempts[0].evidence_text()
    parts = []
    for i, a in enumerate(attempts, start=1):
        parts.append(f"===== ATTEMPT {i} of {len(attempts)} =====")
        parts.append(a.evidence_text())
    for ua, ua_attempts in (extra_by_ua or {}).items():
        for i, a in enumerate(ua_attempts, start=1):
            parts.append(f"===== USER-AGENT {ua!r} ATTEMPT {i} of {len(ua_attempts)} =====")
            parts.append(a.evidence_text())
    return "\n".join(parts)


def _score_endpoint(probes, attempts, distribution, agency_id, evidence_store,
                    timestamp, source, results, access_observations=None,
                    extra_attempts_by_ua=None):
    """Run the endpoint-fetching probes that apply to `source` over one target.

    `access_observations` (the crawler-access triad) is attached to the barrier
    probe's record: that probe owns the attempts the observed leg is read from.
    """
    url = attempts[0].requested_url
    for probe in probes:
        if not probe.applies_to(source):
            continue
        if probe.multi_attempt:
            score, ev, obs = unpack_verdict(probe.evaluate_attempts(attempts, distribution))
            evidence_text = _attempts_evidence(attempts, extra_attempts_by_ua)
        else:
            score, ev, obs = unpack_verdict(probe.evaluate(attempts[0], distribution))
            evidence_text = attempts[0].evidence_text()
        if probe.probe_id == NoBarriersProbe.probe_id and access_observations:
            obs = {**obs, **access_observations}
            evidence_text = (
                f"{evidence_text}\n\nCRAWLER ACCESS (declared / enforced / observed):\n"
                f"{json.dumps(access_observations, indent=2, default=str)}"
            )
        path = evidence_store.write(agency_id, probe.probe_id, url, evidence_text)
        results.append(_record(probe, url, score, ev, timestamp, path, source=source,
                               observations=obs))


def _normalize_for_match(url: str) -> str:
    """Compare URLs the way a reviewer would: ignore scheme, case, trailing slash.

    Used only for the evidence-only catalog-completeness and catalog-coverage
    facts, never for a score, so a loose match errs toward saying a page IS in
    the catalog, which makes both facts conservative.
    """
    text = (url or "").strip().lower()
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    text = text.split("#")[0]
    return text.rstrip("/")


def catalog_reference_urls(datasets: List[dict]) -> set:
    """Every URL a data.json catalog points at, normalized: each distribution's
    downloadURL and accessURL, and each dataset's landingPage. The set a machine
    that trusts the catalog can reach."""
    urls = set()
    for ds in datasets or []:
        if not isinstance(ds, dict):
            continue
        landing = ds.get("landingPage")
        if isinstance(landing, str) and landing.strip():
            urls.add(_normalize_for_match(landing))
        for dist in ds.get("distribution", []) or []:
            if not isinstance(dist, dict):
                continue
            for key in ("downloadURL", "accessURL"):
                value = dist.get(key)
                if isinstance(value, str) and value.strip():
                    urls.add(_normalize_for_match(value))
    return urls


def catalog_sitemap_coverage(datasets: List[dict], has_catalog: bool, web) -> dict:
    """The observed fact behind D0-r2 defect 3: of the URLs the site's own sitemap
    declares, what fraction does the catalog reference as a distribution or
    landing page? Numerator and denominator are explicit; per-section counts are
    kept because the D0-r2 finding was that one whole section (QuickFacts,
    21.8% of census.gov's universe) is referenced zero times.

    The FRACTION is evidence only: a fractional threshold is deferred until the
    January pilot yields an observed distribution (rubric v1.1, open item). The
    categorical fact -- a section with ZERO catalog references -- is scored by
    `apply_catalog_coverage_rule` (rule `catalog_zero_coverage` v1, rubric v1.1
    Decision 1, task 2026-09-02_rubric_amendments_coverage_lastmod). A null
    fraction means the denominator is zero (no sitemap universe was
    enumerated), which must read as not measurable, never as 0.0.
    """
    universe_by_section = getattr(web, "universe_by_section", {}) if web else {}
    catalog_urls = catalog_reference_urls(datasets) if has_catalog else set()
    per_section = {}
    numerator = 0
    denominator = 0
    for section in sorted(universe_by_section):
        urls = universe_by_section[section]
        covered = sum(1 for u in urls if _normalize_for_match(u) in catalog_urls)
        per_section[section] = {
            "sitemap_urls": len(urls),
            "in_catalog": covered,
            "fraction": round(covered / len(urls), 6) if urls else None,
        }
        numerator += covered
        denominator += len(urls)
    applicable = bool(has_catalog and web is not None and getattr(web, "has_sitemap", False)
                      and denominator > 0)
    return {
        "fraction_scored": False,
        "zero_coverage_rule": f"{COVERAGE_RULE_ID}/{COVERAGE_RULE_VERSION}",
        "applicable": applicable,
        "numerator": "sitemap-declared URLs referenced by the catalog as a "
                     "distribution downloadURL/accessURL or a dataset landingPage",
        "numerator_value": numerator,
        "denominator": "unique URLs declared by the site's sitemap (all parsed sections)",
        "denominator_value": denominator,
        "fraction_in_catalog": round(numerator / denominator, 6) if denominator else None,
        "catalog_reference_urls_compared": len(catalog_urls),
        "per_section": per_section,
        "sections_with_zero_coverage": sorted(
            s for s, v in per_section.items() if v["sitemap_urls"] and v["in_catalog"] == 0),
        "note": (
            "Coverage is measured over the whole enumerated sitemap universe, not "
            "the probed sample. A null fraction means no sitemap universe was "
            "enumerated. The fraction is not scored (threshold deferred to the "
            "January pilot, rubric v1.1 open item); a section with zero catalog "
            "references scores d1_catalog PARTIAL (rule catalog_zero_coverage v1)."
        ),
    }


# Rubric v1.1, D1 catalog zero-coverage clause (Decision 1 of task
# 2026-09-02_rubric_amendments_coverage_lastmod). Versioned like `sitemap_stale`
# so a re-score can name the rule that produced it.
COVERAGE_RULE_ID = "catalog_zero_coverage"
COVERAGE_RULE_VERSION = 1


def apply_catalog_coverage_rule(score: Score, evidence: str, coverage: dict):
    """Categorical coverage rule: a section of the enumerated sitemap universe
    that the catalog references ZERO times scores d1_catalog PARTIAL, with the
    section name and its denominator as evidence.

    No threshold is involved -- this is absence, not a fraction -- so the rule
    needs no config value. It only ever lowers PASS to PARTIAL: a probe verdict
    of PARTIAL (wrong-shape JSON) or FAIL (no catalog) is left alone, and the
    rule is not determinable when no sitemap universe was enumerated. Returns
    `(score, evidence, warning)`; the warning is recorded whether or not it
    fired so a re-score can see the rule was evaluated.
    """
    determinable = bool(coverage.get("applicable"))
    zero = coverage.get("sections_with_zero_coverage") or []
    per_section = coverage.get("per_section") or {}
    sections = [{"section": s, "sitemap_urls": per_section[s]["sitemap_urls"]}
                for s in zero] if determinable else []
    fired = determinable and bool(sections)
    warning = {
        "rule_id": COVERAGE_RULE_ID,
        "rule_version": COVERAGE_RULE_VERSION,
        "fired": fired,
        "determinable": determinable,
        "sections_with_zero_coverage": sections,
    }
    if fired and score == Score.PASS:
        detail = "; ".join(f"section {d['section']}: 0 of {d['sitemap_urls']} "
                           f"sitemap URLs referenced" for d in sections)
        evidence = (f"{evidence}; catalog covers none of a sitemap section "
                    f"({detail}; rule {COVERAGE_RULE_ID} v{COVERAGE_RULE_VERSION})")
        score = Score.PARTIAL
    return score, evidence, warning


def run_agency(agency: dict, fetcher, evidence_store: EvidenceStore, timestamp: str,
               *, settings: ProbeSettings,
               max_datasets: int = 50, max_dists_per_dataset: int = 3,
               no_barriers_attempts: int = 1,
               sitemap_sample_per_section: int = 3, max_sitemap_sections: int = 0,
               sitemap_sample_seed: int = 0, enumerate_sitemap: bool = True,
               today: Optional[date] = None) -> dict:
    """Probe one agency end-to-end over BOTH enumeration sources.

    Source 1, data.json: catalog datasets and their distributions.
    Source 2, sitemap: a stratified sample of the agency's own web product pages.

    Returns results, rollup, and enumeration metadata for both sources. The two
    surfaces stay separate all the way to the rollup. `today` is injectable so
    the sitemap staleness rule is testable from fixtures."""
    agency_id = agency["id"]
    base_url = agency["base_url"].rstrip("/")
    catalog_url = agency.get("catalog_url") or f"{base_url}/data.json"
    results: List[ProbeResult] = []

    # The enforced leg of the crawler-access triad, when the operator supplied it.
    # A configured file that is missing or malformed fails here, loud, before any
    # request is sent.
    enforced = load_enforced_observations(agency.get("enforced_observations_file"))

    # Fetch the catalog once; reuse it for both the D1 catalog probe and enumeration.
    catalog_fetched = fetcher.get(catalog_url, accept="application/json")

    # robots.txt first: the sitemap probe, the web-surface enumerator and the
    # declared leg of the crawler-access triad all read it, with no second fetch.
    robots_fetched = fetcher.get(f"{base_url}/robots.txt")
    robots_body = robots_fetched.body

    # --- Site probes (once per agency) ---
    held_catalog = None  # d1_catalog is recorded after enumeration, with coverage.
    for probe in site_probes(settings):
        url = probe.url_for(base_url)
        extra_evidence = ""
        if probe.probe_id == "d1_robots":
            f = robots_fetched
            verdict = probe.evaluate(f)
        elif probe.probe_id == "d1_sitemap":
            url, sitemap_source = probe.resolve(base_url, robots_body)
            f = fetcher.get(url)
            fixed = None
            fixed_url = probe.url_for(base_url)
            if (sitemap_source == SOURCE_ROBOTS
                    and _normalize_for_match(url) != _normalize_for_match(fixed_url)):
                # The declared sitemap is not the fixed path: read both so the
                # divergence is evidence rather than an unread assumption.
                fixed = fetcher.get(fixed_url)
                extra_evidence = (f"\n\n===== FIXED PATH {fixed_url} (divergence "
                                  f"comparator, not scored) =====\n{fixed.evidence_text()}")
            verdict = probe.evaluate(f, sitemap_source=sitemap_source,
                                     fixed_path_fetched=fixed, today=today)
        elif probe.probe_id == "d1_catalog" and url == catalog_url:
            f = catalog_fetched
            verdict = probe.evaluate(f)
        else:
            f = fetcher.get(url)
            verdict = probe.evaluate(f)
        score, ev, obs = unpack_verdict(verdict)
        evidence_text = f.evidence_text() + extra_evidence
        if probe.probe_id == "d1_catalog":
            held_catalog = (probe, url, score, ev, obs, evidence_text)
            continue
        path = evidence_store.write(agency_id, probe.probe_id, url, evidence_text)
        results.append(_record(probe, url, score, ev, timestamp, path,
                               source=SOURCE_SITE, observations=obs))

    # --- Enumerate targets from the catalog ---
    enum = parse_catalog(catalog_fetched.body, base_url)
    datasets = []
    if enum.has_machine_readable_catalog:
        try:
            datasets = json.loads(catalog_fetched.body).get("dataset", []) or []
        except (json.JSONDecodeError, ValueError):
            datasets = []

    datasets_probed = datasets[:max_datasets]

    def _probe_target(url: str, distribution: dict, source: str, probes: list):
        """Fetch one target under the harness identity (n attempts), then under
        any extra identities configured for the observed leg, score it, and
        attach the crawler-access triad to the barrier record."""
        attempts = _fetch_attempts(fetcher, url, _MACHINE_ACCEPT, no_barriers_attempts)
        attempts_by_ua = {settings.harness_user_agent: attempts}
        extra_by_ua: Dict[str, List] = {}
        for ua in settings.crawler_observe_user_agents:
            if ua == settings.harness_user_agent or ua in extra_by_ua:
                continue
            extra_by_ua[ua] = _fetch_attempts(fetcher, url, _MACHINE_ACCEPT,
                                              no_barriers_attempts, user_agent=ua)
        attempts_by_ua.update(extra_by_ua)
        access = effective_crawler_access(
            robots_body, url, attempts_by_ua,
            settings.crawler_declared_user_agents,
            settings.crawler_refusal_statuses, enforced)
        access_obs = {
            "effective_crawler_access": access,
            "crawler_policy_mismatch_warning": mismatch_warning(access),
        }
        _score_endpoint(probes, attempts, distribution, agency_id, evidence_store,
                        timestamp, source, results, access_observations=access_obs,
                        extra_attempts_by_ua=extra_by_ua)
        return attempts

    # --- Per-dataset metadata probes + per-distribution endpoint probes ---
    for ds in datasets_probed:
        if not isinstance(ds, dict):
            continue
        ds_id = ds.get("identifier") or ds.get("title") or "dataset"
        for probe in METADATA_PROBES:
            score, ev, obs = unpack_verdict(probe.evaluate(ds))
            evidence_text = (
                f"DATASET: {ds_id}\nPROBE: {probe.probe_id}\nVERDICT: {ev}\n\n"
                f"RECORD:\n{json.dumps(ds, indent=2, default=str)}"
            )
            path = evidence_store.write(agency_id, probe.probe_id, str(ds_id), evidence_text)
            results.append(_record(probe, str(ds_id), score, ev, timestamp, path,
                                   observations=obs))

        for dist in (ds.get("distribution", []) or [])[:max_dists_per_dataset]:
            if not isinstance(dist, dict):
                continue
            url = dist.get("downloadURL") or dist.get("accessURL")
            if not url:
                continue
            _probe_target(url, dist, SOURCE_CATALOG, DISTRIBUTION_PROBES)

    # --- Source 2: web surfaces sampled from the declared sitemap ---
    web = None
    web_enumeration = {"enumerated": False,
                       "note": "sitemap enumeration disabled for this run"}
    if enumerate_sitemap:
        web = enumerate_web_surfaces(
            fetcher,
            robots_body=robots_body,
            configured_sitemap_url=agency.get("sitemap_url", ""),
            sample_per_section=sitemap_sample_per_section,
            max_sections=max_sitemap_sections,
            seed=sitemap_sample_seed,
        )
        pages_with_dataset_markup = []
        web_probes = DISTRIBUTION_PROBES + page_probes(settings)
        for target in web.targets:
            url = target["url"]
            attempts = _probe_target(url, {}, SOURCE_SITEMAP, web_probes)
            page = attempts[0]
            nodes = dataset_nodes(page.body)
            if has_dataset_markup(nodes):
                pages_with_dataset_markup.append(url)

            # Metadata probes read the page's own JSON-LD instead of a DCAT record.
            record = dcat_record_from_nodes(nodes)
            for probe in METADATA_PROBES:
                if not probe.applies_to(SOURCE_SITEMAP):
                    continue
                score, ev, obs = unpack_verdict(probe.evaluate_page(page, nodes=nodes))
                evidence_text = (
                    f"PAGE: {url}\nSECTION: {target.get('section', '')}\n"
                    f"PROBE: {probe.probe_id}\nVERDICT: {ev}\n\n"
                    f"NORMALIZED RECORD FROM IN-PAGE JSON-LD:\n"
                    f"{json.dumps(record, indent=2, default=str)}\n\n"
                    f"RAW JSON-LD NODES:\n"
                    f"{json.dumps(nodes, indent=2, default=str)}"
                )
                path = evidence_store.write(agency_id, probe.probe_id, url,
                                            evidence_text)
                results.append(_record(probe, url, score, ev, timestamp, path,
                                       source=SOURCE_SITEMAP, observations=obs))

        web_enumeration = _web_enumeration_dict(web, enum, pages_with_dataset_markup)

    # --- d1_catalog, recorded now that the sitemap universe is known ---
    coverage = catalog_sitemap_coverage(datasets, enum.has_machine_readable_catalog, web)
    if web_enumeration.get("enumerated"):
        web_enumeration["catalog_coverage"] = coverage
    if held_catalog is not None:
        probe, url, score, ev, obs, evidence_text = held_catalog
        score, ev, warning = apply_catalog_coverage_rule(score, ev, coverage)
        obs = {**obs, "catalog_sitemap_coverage": coverage,
               "catalog_coverage_warning": warning}
        evidence_text = (
            f"{evidence_text}\n\nCATALOG COVERAGE OF THE SITEMAP UNIVERSE "
            f"(fraction observed, not scored; zero-coverage section scored by "
            f"{COVERAGE_RULE_ID} v{COVERAGE_RULE_VERSION}):\n"
            f"{json.dumps(coverage, indent=2, default=str)}\n\n"
            f"ZERO-COVERAGE RULE:\n{json.dumps(warning, indent=2, default=str)}"
        )
        path = evidence_store.write(agency_id, probe.probe_id, url, evidence_text)
        results.append(_record(probe, url, score, ev, timestamp, path,
                               source=SOURCE_SITE, observations=obs))

    rollup = rollup_agency(agency_id, results)
    enumeration = {
        "catalog_url": catalog_url,
        "has_machine_readable_catalog": enum.has_machine_readable_catalog,
        "note": enum.note,
        "datasets_total": len(datasets),
        "datasets_probed": len(datasets_probed),
        "candidate_endpoints": len(enum.targets),
        "no_barriers_attempts": no_barriers_attempts,
        "crawler_access": {
            "declared_user_agents": list(settings.crawler_declared_user_agents),
            "observed_user_agents": [settings.harness_user_agent]
                                    + [ua for ua in settings.crawler_observe_user_agents
                                       if ua != settings.harness_user_agent],
            "enforced_observations_file": agency.get("enforced_observations_file"),
        },
        "web_surface": web_enumeration,
    }
    return {"results": results, "rollup": rollup, "enumeration": enumeration,
            "agency": {"id": agency_id, "name": agency.get("name", "")}}


def _web_enumeration_dict(web, catalog_enum, pages_with_dataset_markup) -> dict:
    """Web-surface enumeration metadata, including the evidence-only catalog
    completeness signal.

    The signal: of the sampled web pages that carry in-page schema.org Dataset
    markup, what fraction is referenced by no data.json distribution. It is
    EVIDENCE ONLY and deliberately not a probe. The rubric scores presence of a
    machine-readable catalog, not its completeness; turning completeness into a
    score is a rubric decision, not a code change. It is emitted so a reviewer can
    see catalog fragmentation with an explicit denominator rather than inferring
    it, and so the denominator being zero is visible as "not measurable here"
    rather than collapsing to a fraction that reads as good news."""
    catalog_urls = {_normalize_for_match(t["url"]) for t in catalog_enum.targets}
    absent = [u for u in pages_with_dataset_markup
              if _normalize_for_match(u) not in catalog_urls]
    denominator = len(pages_with_dataset_markup)
    both_sources = bool(catalog_enum.has_machine_readable_catalog and web.has_sitemap)
    completeness = {
        "evidence_only": True,
        "scored": False,
        "applicable": both_sources,
        "denominator": "sampled web-surface pages carrying in-page schema.org "
                       "Dataset markup",
        "denominator_value": denominator,
        "pages_absent_from_catalog": len(absent),
        "fraction_absent_from_catalog": (
            round(len(absent) / denominator, 6) if denominator else None
        ),
        "catalog_distribution_urls_compared": len(catalog_urls),
        "examples_absent_from_catalog": sorted(absent)[:10],
        "note": (
            "Evidence only, never a score. A null fraction means the denominator "
            "is zero: no sampled page carried in-page Dataset markup, so catalog "
            "completeness is not measurable from this sample. That is itself a D3 "
            "observation about the web surface, not a passing result."
        ),
    }
    return {
        "enumerated": True,
        "has_sitemap": web.has_sitemap,
        "sitemap_url": web.sitemap_url,
        "sitemap_url_source": web.sitemap_url_source,
        "sitemap_url_drift": web.drift,
        "sections_total": web.sections_total,
        "sections_parsed": web.sections_parsed,
        "per_section_parsed": web.per_section_parsed,
        "per_section_sampled": web.per_section_sampled,
        "child_failures": web.child_failures,
        "universe_total": web.universe_total,
        "duplicate_count": web.duplicate_count,
        "sample_seed": web.sample_seed,
        "sample_per_section": web.sample_per_section,
        "pages_probed": len(web.targets),
        "pages_with_dataset_markup": len(pages_with_dataset_markup),
        "note": web.note,
        "catalog_completeness": completeness,
    }


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
    # Web-surface (second source) caps. Defaults come from harness.toml; these
    # override for one run without editing config, so a small live run stays
    # small without changing the recorded configuration.
    parser.add_argument("--sitemap-sample-size", type=int, default=None,
                        help="pages sampled per sitemap section "
                             "(default: [sitemap] sample_per_section)")
    parser.add_argument("--max-sitemap-sections", type=int, default=None,
                        help="cap on child sitemaps walked, 0 for no cap "
                             "(default: [sitemap] max_sections)")
    parser.add_argument("--sitemap-seed", type=int, default=None,
                        help="sampling seed (default: [sitemap] sample_seed)")
    parser.add_argument("--no-sitemap", action="store_true",
                        help="skip web-surface enumeration; catalog source only")
    parser.add_argument("--no-barriers-attempts", type=int, default=None,
                        help="fetches per target for d2_no_barriers "
                             "(default: [probes.d2_no_barriers] attempts)")
    parser.add_argument("--list", action="store_true", help="list configured agencies and exit")
    args = parser.parse_args(argv)

    if args.no_barriers_attempts is not None and args.no_barriers_attempts < 1:
        parser.error("--no-barriers-attempts must be >= 1")
    if args.sitemap_sample_size is not None and args.sitemap_sample_size < 1:
        parser.error("--sitemap-sample-size must be >= 1")

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

    attempts = (args.no_barriers_attempts if args.no_barriers_attempts is not None
                else cfg.no_barriers_attempts)
    per_section = (args.sitemap_sample_size if args.sitemap_sample_size is not None
                   else cfg.sitemap_sample_per_section)
    max_sections = (args.max_sitemap_sections if args.max_sitemap_sections is not None
                    else cfg.sitemap_max_sections)
    seed = args.sitemap_seed if args.sitemap_seed is not None else cfg.sitemap_sample_seed

    settings = ProbeSettings.from_config(cfg)

    for agency in agencies:
        print(f"[{agency['id']}] probing {agency['base_url']} ...")
        run = run_agency(agency, fetcher, evidence_store, timestamp,
                         settings=settings,
                         max_datasets=args.max_datasets,
                         max_dists_per_dataset=args.max_dists_per_dataset,
                         no_barriers_attempts=attempts,
                         sitemap_sample_per_section=per_section,
                         max_sitemap_sections=max_sections,
                         sitemap_sample_seed=seed,
                         enumerate_sitemap=not args.no_sitemap)
        _write_outputs(out_dir, agency["id"], run)
        roll = run["rollup"]
        enum = run["enumeration"]
        print(f"  catalog: {'yes' if enum['has_machine_readable_catalog'] else 'NO (D1 finding)'}"
              f"  datasets probed: {enum['datasets_probed']}/{enum['datasets_total']}")
        print(f"  core composite: {roll['core_composite']}/{roll['core_composite_max']}"
              f"  | frontier_near: {roll['frontier_near']['score']}/{roll['frontier_near']['max']}"
              f"  | frontier_deep: {roll['frontier_deep']['score']}/{roll['frontier_deep']['max']}")
        web = enum["web_surface"]
        if web.get("enumerated"):
            cat_d2 = roll["core_dimension_vectors"]["D2"]
            web_d2 = roll["web_surface"]["core_dimension_vectors"]["D2"]
            print(f"  web surface: {web['pages_probed']} pages from "
                  f"{web['sections_parsed']}/{web['sections_total']} sections"
                  f"  ({len(web['child_failures'])} section(s) unreachable)")
            print(f"  D2 catalog-distribution: {cat_d2['score']}/{cat_d2['max']}"
                  f"  | D2 web-surface: {web_d2['score']}/{web_d2['max']}"
                  f"   (separate vectors, never summed)")
        print(f"  wrote {out_dir / (agency['id'] + '_records.json')} and _rollup.json")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
