"""Per-agency rollup behavior. The load-bearing invariant: frontier-track scores
NEVER enter the core composite (the access-axis firewall)."""
from harness.records import Score, Track, ProbeResult
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
