"""Per-agency rollup: collapse a flat list of ProbeResults (across all of an
agency's targets) into the reportable picture.

The load-bearing invariant, enforced here structurally: frontier-track scores
never enter the core composite. Core and frontier are partitioned by
`track.in_core_composite` before any summing happens, so there is no code path
that can accidentally fold a frontier score into the headline.
"""
from __future__ import annotations

from typing import List

from .records import ProbeResult, Track

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


def rollup_agency(agency_id: str, results: List[ProbeResult]) -> dict:
    """Aggregate one agency's probe results into core dimension vectors, a core
    composite, and the two frontier tracks reported separately."""
    core = [r for r in results if r.track.in_core_composite]
    # Frontier is everything NOT in the core composite — by construction it cannot
    # reach the composite sum below.
    frontier = [r for r in results if not r.track.in_core_composite]

    core_dimension_vectors = {}
    for dim in CORE_DIMENSIONS:
        in_dim = [r for r in core if r.dimension == dim]
        core_dimension_vectors[dim] = {
            "score": sum(int(r.score) for r in in_dim),
            "max": _MAX_PER_PROBE * len(in_dim),
            "n_probes": len(in_dim),
        }

    core_composite = sum(v["score"] for v in core_dimension_vectors.values())
    core_composite_max = sum(v["max"] for v in core_dimension_vectors.values())

    targets = {r.target for r in results}

    return {
        "agency_id": agency_id,
        "n_targets": len(targets),
        "core_dimension_vectors": core_dimension_vectors,
        "core_composite": core_composite,
        "core_composite_max": core_composite_max,
        # Frontier tracks: reported, never summed into core.
        "frontier_near": _frontier_summary(results, Track.FRONTIER_NEAR),
        "frontier_deep": _frontier_summary(results, Track.FRONTIER_DEEP),
        # Provenance of the firewall, carried in the output itself.
        "firewall_note": (
            "Core composite = Part A (icsp_notebook 51fe4574) only. Frontier tracks "
            "(Part B: llms.txt / MCP / WebMCP) are reported separately and are never "
            "folded into the core composite."
        ),
        "n_probes_total": len(results),
        "n_probes_core": len(core),
        "n_probes_frontier": len(frontier),
    }
