"""Per-agency rollup: collapse a flat list of ProbeResults (across all of an
agency's targets) into the reportable picture.

Two invariants are enforced here structurally, both by partitioning BEFORE any
summing happens, so no code path can fold the wrong thing into a headline:

1. **The core-vs-frontier firewall.** Frontier-track scores never enter the core
   composite. Partitioned on `track.in_core_composite`.

2. **The surface firewall.** Web-surface results never enter the
   catalog-distribution composite, and are reported as their own vector.
   Partitioned on `result.source`. The two surfaces answer the same rubric
   question about different things: whether a catalog distribution is retrievable
   by a machine, and whether the agency's own web products are. The entire reason
   the second source exists is that those answers can diverge (Census scored D2
   21/24 on catalog distributions while its flagship web product refused
   automated clients at the edge), so a single summed D2 would erase exactly the
   finding the measurement was built to surface. Averaging them would be worse
   than either number alone.

Neither vector is "the real one". They are reported side by side, each with its
own denominator.
"""
from __future__ import annotations

from typing import List

from .records import WEB_SURFACE_SOURCES, ProbeResult, Track

# The four core dimensions, always reported even when a dimension has no probes —
# an absent dimension is a finding, not a silent omission.
CORE_DIMENSIONS = ("D1", "D2", "D3", "D4")

# Max points per probe (Score.PASS).
_MAX_PER_PROBE = 2


def _frontier_summary(results: List[ProbeResult], track: Track) -> dict:
    subset = [r for r in results if r.track is track]
    return {
        "score": sum(int(r.score) for r in subset),
        "max": _MAX_PER_PROBE * len(subset),
        "n_probes": len(subset),
        "as_of_date": track.as_of_date,
        "probe_ids": sorted(r.probe_id for r in subset),
    }


def _dimension_vectors(core_results: List[ProbeResult]) -> dict:
    vectors = {}
    for dim in CORE_DIMENSIONS:
        in_dim = [r for r in core_results if r.dimension == dim]
        vectors[dim] = {
            "score": sum(int(r.score) for r in in_dim),
            "max": _MAX_PER_PROBE * len(in_dim),
            "n_probes": len(in_dim),
        }
    return vectors


def rollup_agency(agency_id: str, results: List[ProbeResult]) -> dict:
    """Aggregate one agency's probe results into the catalog-distribution vector,
    the web-surface vector reported separately, and the two frontier tracks."""
    # Partition by surface FIRST. Everything below sums within one partition.
    web_results = [r for r in results if r.source in WEB_SURFACE_SOURCES]
    catalog_results = [r for r in results if r.source not in WEB_SURFACE_SOURCES]

    core = [r for r in catalog_results if r.track.in_core_composite]
    # Frontier is everything NOT in the core composite — by construction it cannot
    # reach the composite sum below.
    frontier = [r for r in results if not r.track.in_core_composite]

    core_dimension_vectors = _dimension_vectors(core)
    core_composite = sum(v["score"] for v in core_dimension_vectors.values())
    core_composite_max = sum(v["max"] for v in core_dimension_vectors.values())

    web_core = [r for r in web_results if r.track.in_core_composite]
    web_vectors = _dimension_vectors(web_core)
    web_surface = {
        "core_dimension_vectors": web_vectors,
        # Named "vector_total", not "composite": it is the sum of the web-surface
        # dimension vector and is NOT comparable to the catalog composite, which
        # runs a different probe set over a different denominator.
        "vector_total": sum(v["score"] for v in web_vectors.values()),
        "vector_max": sum(v["max"] for v in web_vectors.values()),
        "n_targets": len({r.target for r in web_results}),
        "n_probes": len(web_results),
        "sources": sorted({r.source for r in web_results}),
        "note": (
            "Web-surface results are reported as their own vector and are never "
            "summed into the catalog composite: the two measure different "
            "surfaces, and they are expected to diverge."
        ),
    }

    return {
        "agency_id": agency_id,
        "n_targets": len({r.target for r in catalog_results}),
        "core_dimension_vectors": core_dimension_vectors,
        "core_composite": core_composite,
        "core_composite_max": core_composite_max,
        # Second surface: reported, never summed into the catalog composite.
        "web_surface": web_surface,
        # Frontier tracks: reported, never summed into core.
        "frontier_near": _frontier_summary(results, Track.FRONTIER_NEAR),
        "frontier_deep": _frontier_summary(results, Track.FRONTIER_DEEP),
        # Provenance of both firewalls, carried in the output itself.
        "firewall_note": (
            "Core composite = Part A (icsp_notebook 51fe4574) only, over "
            "catalog-enumerated targets only. Frontier tracks (Part B: llms.txt / "
            "MCP / WebMCP) and web-surface results are each reported separately "
            "and are never folded into the core composite."
        ),
        "n_probes_total": len(results),
        "n_probes_core": len(core),
        "n_probes_frontier": len(frontier),
        "n_probes_web_surface": len(web_results),
    }
