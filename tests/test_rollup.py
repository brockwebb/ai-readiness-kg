"""Per-agency rollup behavior. The load-bearing invariant: frontier-track scores
NEVER enter the core composite (the access-axis firewall)."""
from harness.records import SOURCE_SITEMAP, Score, Track, ProbeResult
from harness.rollup import rollup_agency


def _r(probe_id, dimension, track, score, as_of_date=""):
    return ProbeResult(
        probe_id=probe_id,
        target="https://example.gov/x",
        dimension=dimension,
        track=track,
        score=score,
        as_of_date=as_of_date,
        evidence="",
        timestamp="2026-06-23T00:00:00Z",
        evidence_path="evidence/example/x.txt",
    )


def test_core_composite_sums_only_core_scores_across_dimensions():
    results = [
        _r("d1_robots", "D1", Track.CORE, Score.PASS),     # 2
        _r("d2_api", "D2", Track.CORE, Score.PARTIAL),     # 1
        _r("d3_schema", "D3", Track.CORE, Score.FAIL),     # 0
        _r("d4_license", "D4", Track.CORE, Score.PASS),    # 2
    ]
    roll = rollup_agency("example", results)
    assert roll["core_composite"] == 5
    assert roll["core_composite_max"] == 8  # 4 core probes * 2


def test_frontier_pass_does_not_change_core_composite():
    """The firewall: a perfect frontier score adds nothing to the headline."""
    core_only = [_r("d3_schema", "D3", Track.CORE, Score.PASS)]
    with_frontier = core_only + [
        _r("frontier_llms_txt", None, Track.FRONTIER_NEAR, Score.PASS, "2024-09"),
        _r("frontier_mcp", None, Track.FRONTIER_DEEP, Score.PASS, "2026-01"),
    ]
    base = rollup_agency("example", core_only)
    augmented = rollup_agency("example", with_frontier)
    assert base["core_composite"] == augmented["core_composite"] == 2
    assert base["core_composite_max"] == augmented["core_composite_max"] == 2


def test_frontier_tracks_reported_separately_with_as_of_date():
    results = [
        _r("d3_schema", "D3", Track.CORE, Score.PASS),
        _r("frontier_llms_txt", None, Track.FRONTIER_NEAR, Score.PASS, "2024-09"),
        _r("frontier_mcp", None, Track.FRONTIER_DEEP, Score.FAIL, "2026-01"),
    ]
    roll = rollup_agency("example", results)
    assert roll["frontier_near"]["score"] == 2
    assert roll["frontier_near"]["as_of_date"] == "2024-09"
    assert roll["frontier_deep"]["score"] == 0
    assert roll["frontier_deep"]["as_of_date"] == "2026-01"
    # "has llms.txt but not WebMCP" is a distinct, readable state.
    assert roll["frontier_near"]["score"] > 0
    assert roll["frontier_deep"]["score"] == 0


def test_core_dimension_vector_groups_by_dimension():
    results = [
        _r("d1_robots", "D1", Track.CORE, Score.PASS),    # D1: 2
        _r("d1_sitemap", "D1", Track.CORE, Score.PARTIAL),  # D1: +1 -> 3
        _r("d3_schema", "D3", Track.CORE, Score.FAIL),    # D3: 0
    ]
    roll = rollup_agency("example", results)
    vec = roll["core_dimension_vectors"]
    assert vec["D1"]["score"] == 3
    assert vec["D1"]["max"] == 4
    assert vec["D1"]["n_probes"] == 2
    assert vec["D3"]["score"] == 0
    assert vec["D3"]["max"] == 2
    # Dimensions with no probes are still present as zero — an absent dimension is
    # itself a finding, not a silent omission.
    assert vec["D2"]["n_probes"] == 0
    assert vec["D4"]["n_probes"] == 0


def test_rollup_counts_distinct_targets():
    a = _r("d1_robots", "D1", Track.CORE, Score.PASS)
    b = ProbeResult("d1_robots", "https://example.gov/y", "D1", Track.CORE,
                    Score.FAIL, "", "", "2026-06-23T00:00:00Z", "p")
    roll = rollup_agency("example", [a, b])
    assert roll["n_targets"] == 2
    assert roll["agency_id"] == "example"


# --- The surface firewall: web-surface results never enter the catalog composite.
def _w(probe_id, dimension, score, target="https://example.gov/page"):
    """A web-surface result (source = sitemap)."""
    return ProbeResult(
        probe_id=probe_id,
        target=target,
        dimension=dimension,
        track=Track.CORE,
        score=score,
        as_of_date="",
        evidence="",
        timestamp="2026-09-01T00:00:00Z",
        evidence_path="evidence/example/p.txt",
        source=SOURCE_SITEMAP,
    )


def test_web_surface_results_do_not_change_the_catalog_composite():
    """The firewall this task exists for: Census scored D2 21/24 on catalog
    distributions while its flagship web product refused machines. A summed D2
    would erase that, so a page failing every probe must move the catalog
    composite by exactly zero."""
    catalog_only = [_r("d2_no_barriers", "D2", Track.CORE, Score.PASS)]
    with_web = catalog_only + [
        _w("d2_no_barriers", "D2", Score.FAIL),
        _w("d1_stable_urls", "D1", Score.FAIL),
        _w("d3_metadata_standard", "D3", Score.FAIL),
    ]
    base = rollup_agency("example", catalog_only)
    augmented = rollup_agency("example", with_web)
    assert base["core_composite"] == augmented["core_composite"] == 2
    assert base["core_composite_max"] == augmented["core_composite_max"] == 2
    for dim in ("D1", "D2", "D3", "D4"):
        assert (base["core_dimension_vectors"][dim]
                == augmented["core_dimension_vectors"][dim])


def test_the_two_d2_vectors_are_reported_side_by_side_and_can_diverge():
    results = [
        _r("d2_no_barriers", "D2", Track.CORE, Score.PASS),
        _r("d2_content_negotiation", "D2", Track.CORE, Score.PASS),
        _w("d2_no_barriers", "D2", Score.FAIL),
        _w("d2_content_negotiation", "D2", Score.PARTIAL),
    ]
    roll = rollup_agency("example", results)
    assert roll["core_dimension_vectors"]["D2"] == {"score": 4, "max": 4, "n_probes": 2}
    web_d2 = roll["web_surface"]["core_dimension_vectors"]["D2"]
    assert web_d2 == {"score": 1, "max": 4, "n_probes": 2}
    # Neither number is the other's denominator, and nothing sums them.
    assert roll["web_surface"]["vector_total"] == 1
    assert roll["web_surface"]["vector_max"] == 4


def test_web_surface_targets_and_probe_counts_are_reported_separately():
    results = [
        _r("d1_robots", "D1", Track.CORE, Score.PASS),
        _w("d2_no_barriers", "D2", Score.FAIL, target="https://example.gov/a"),
        _w("d2_no_barriers", "D2", Score.FAIL, target="https://example.gov/b"),
    ]
    roll = rollup_agency("example", results)
    assert roll["n_targets"] == 1
    assert roll["web_surface"]["n_targets"] == 2
    assert roll["web_surface"]["n_probes"] == 2
    assert roll["web_surface"]["sources"] == [SOURCE_SITEMAP]
    assert roll["n_probes_web_surface"] == 2


def test_an_agency_with_no_web_surface_reports_an_empty_vector_not_a_missing_key():
    roll = rollup_agency("example", [_r("d1_robots", "D1", Track.CORE, Score.PASS)])
    assert roll["web_surface"]["n_probes"] == 0
    assert roll["web_surface"]["vector_max"] == 0
    for dim in ("D1", "D2", "D3", "D4"):
        assert roll["web_surface"]["core_dimension_vectors"][dim]["n_probes"] == 0
