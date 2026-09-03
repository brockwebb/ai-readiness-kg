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

3. **The eval firewall** (task 2026-09-02_g1_eval_probe_family_v0, step 1). G1
   results — the declared leg (a distribution probe with `dimension = "G1"`) and
   the observed leg (`source = SOURCE_EVAL`, records elicited from a model
   consumer) — are partitioned out FIRST, before either composite is summed, and
   reported as their own block: preservation rate per qualifier class x mode with
   a Wilson 95 % interval and the denominator, the `unparseable` count, and the
   estimate-status distribution. There is no product-level PASS/PARTIAL/FAIL for
   G1 in v0 (design D6; protocol §3: no composite before an intended use).
"""
from __future__ import annotations

import math
from typing import List

from .records import (
    FAMILY_OF,
    EVAL_DIMENSIONS,
    EVAL_SOURCES,
    SOURCE_EVAL,
    UNPARSEABLE,
    WEB_SURFACE_SOURCES,
    Level,
    ProbeResult,
    Track,
)

# The four core dimensions, always reported even when a dimension has no probes —
# an absent dimension is a finding, not a silent omission.
CORE_DIMENSIONS = ("D1", "D2", "D3", "D4")

# Max points per probe (Score.PASS).
_MAX_PER_PROBE = 2

# z for the Wilson 95 % interval — the same constant the burn-close arithmetic
# used (cc_tasks/2026-09-02_post_burn_reconciliation_RESULT.md §2), so G1 rates
# and fabrication rates are interval-comparable.
_WILSON_Z = 1.959964

# Preservation = L3 or better (design D6: "share at L3+").
_PRESERVED_FLOOR = Level.PRESERVED_TRANSFORMED


def wilson_interval(k: int, n: int, z: float = _WILSON_Z):
    """Wilson score interval for k successes in n trials; (None, None) when n = 0
    — an empty denominator is reported as empty, never as 0 %."""
    if n <= 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(centre - half, 6), round(centre + half, 6)


def _is_eval(result) -> bool:
    return (getattr(result, "source", None) in EVAL_SOURCES
            or getattr(result, "dimension", None) in EVAL_DIMENSIONS)


def _observed_cell(records: list) -> dict:
    """One (class, mode) cell of the observed leg."""
    scored = [r for r in records if r.outcome != UNPARSEABLE]
    unparseable = [r for r in records if r.outcome == UNPARSEABLE]
    levels = {lvl.label: 0 for lvl in Level}
    for r in scored:
        levels[Level(r.level).label] += 1
    preserved = sum(1 for r in scored if r.level >= _PRESERVED_FLOOR)
    lo, hi = wilson_interval(preserved, len(scored))
    est = {}
    for r in records:
        est[r.estimate_status] = est.get(r.estimate_status, 0) + 1
    failures = {}
    for r in scored:
        if r.failure_class:
            failures[r.failure_class] = failures.get(r.failure_class, 0) + 1
    return {
        "n": len(records),
        "n_scored": len(scored),
        "n_unparseable": len(unparseable),
        "preserved": preserved,
        "preservation_rate": (round(preserved / len(scored), 6) if scored else None),
        "wilson95": [lo, hi],
        "levels": levels,
        "failure_classes": failures,
        "estimate_status": est,
    }


def g1_block(eval_results: list) -> dict:
    """The G1 block of the rollup: the declared leg (score vector per source, as a
    dimension vector) and the observed leg (per qualifier class x mode cells).
    Reported even when empty — an absent leg is a finding, not a missing key."""
    declared = [r for r in eval_results if r.source not in EVAL_SOURCES]
    observed = [r for r in eval_results if r.source in EVAL_SOURCES]

    declared_by_source = {}
    for r in declared:
        cell = declared_by_source.setdefault(
            r.source, {"score": 0, "max": 0, "n_probes": 0, "probe_ids": set()})
        cell["score"] += int(r.score)
        cell["max"] += _MAX_PER_PROBE
        cell["n_probes"] += 1
        cell["probe_ids"].add(r.probe_id)
    for cell in declared_by_source.values():
        cell["probe_ids"] = sorted(cell["probe_ids"])

    cells = {}
    for r in observed:
        cells.setdefault(r.qualifier_class, {}).setdefault(r.mode, []).append(r)
    observed_block = {
        cls: {mode: _observed_cell(recs) for mode, recs in sorted(modes.items())}
        for cls, modes in sorted(cells.items())
    }
    by_mode = {}
    for r in observed:
        by_mode.setdefault(r.mode, []).append(r)
    # v2 (design D9 / D12, task 2026-09-03_g1_eval_v2): the family is the scored unit, so the
    # family cells are the v2 denominators; class cells above remain for v0/v1 comparability.
    # A record from a v0/v1 file (family "") is grouped by its class's family.
    fam_cells, factor_cells, by_comp = {}, {}, {}
    n_qualifiers = 0
    for r in observed:
        fam = r.family or FAMILY_OF.get(r.qualifier_class, r.qualifier_class)
        fam_cells.setdefault(fam, {}).setdefault(r.mode, []).append(r)
        surface = r.surface_type or "prose_labeled"
        comp = r.compression_level if r.mode == "indirect" else "direct"
        factor_cells.setdefault(surface, {}).setdefault(comp or "none", []).append(r)
        if r.mode == "indirect":
            by_comp.setdefault(comp or "none", []).append(r)
        forms = r.observations.get("forms") if isinstance(r.observations, dict) else None
        n_qualifiers += len(forms) if isinstance(forms, dict) and forms else 1
    return {
        "declared": declared_by_source,
        "observed": {
            "by_class_and_mode": observed_block,
            "by_mode": {m: _observed_cell(recs) for m, recs in sorted(by_mode.items())},
            "by_family_and_mode": {f: {m: _observed_cell(recs) for m, recs in sorted(modes.items())}
                                   for f, modes in sorted(fam_cells.items())},
            "by_surface_and_compression": {sf: {c: _observed_cell(recs) for c, recs in sorted(cells.items())}
                                           for sf, cells in sorted(factor_cells.items())},
            "by_compression_indirect": {c: _observed_cell(recs) for c, recs in sorted(by_comp.items())},
            "all": _observed_cell(observed),
            "n_propositions": len({r.target for r in observed}),
            "n_families": len(observed),
            "n_qualifiers": n_qualifiers,
            "prompt_epochs": sorted({r.prompt_epoch for r in observed}),
            "model_ids": sorted({r.model_id for r in observed}),
            "parser_versions": sorted({r.parser_version for r in observed}),
            "scorer_versions": sorted({getattr(r, "scorer_version", "") for r in observed}),
        },
        "n_records": len(eval_results),
        "note": (
            "G1 is reported as its own block and never enters the core composite, "
            "the web-surface vector or a frontier track. Observed-leg rates are "
            "the share of scored (parseable) records at level L3 or better, with a "
            "Wilson 95 % interval and the denominator; `unparseable` records are "
            "counted separately and never coerced into a score. No product-level "
            "threshold exists in v0 (DD-033)."
        ),
    }


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
    # Eval-family results (G1 declared + observed) leave the pool before anything
    # else is looked at, so no later sum can reach them.
    eval_results = [r for r in results if _is_eval(r)]
    results = [r for r in results if not _is_eval(r)]
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
        # G1 (eval family): its own block, its own denominators.
        "g1": g1_block(eval_results),
        "n_probes_total": len(results) + len(eval_results),
        "n_probes_core": len(core),
        "n_probes_frontier": len(frontier),
        "n_probes_web_surface": len(web_results),
        "n_probes_eval": len(eval_results),
    }
