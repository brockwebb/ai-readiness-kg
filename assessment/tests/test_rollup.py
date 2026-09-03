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


# --- The eval firewall: G1 results never enter the core composite, the web-surface
# vector or a frontier track; they are their own block with their own denominators.
from harness.records import SOURCE_EVAL, UNPARSEABLE, EvalResult, Level, level_to_score
from harness.rollup import g1_block, wilson_interval


def _e(cls, mode, level, outcome=None, target="g1-p", est="exact", failure=None):
    from harness.records import Level, level_to_score
    if outcome == UNPARSEABLE:
        score, lvl = None, None
    else:
        score, lvl = level_to_score(Level(level)), level
    return EvalResult(probe_id="g1_preservation", target=target, qualifier_class=cls, mode=mode, scorer_version="t",
                      outcome=outcome or score.name.lower(), score=score, level=lvl,
                      failure_class=failure, estimate_status=est, model_id="m", prompt_epoch="e", parser_version="t",
                      evidence="", timestamp="2026-09-02T00:00:00Z", evidence_path="p")


def _g1_declared(score, target="https://x.gov/a.csv"):
    return ProbeResult("g1_declared", target, "G1", Track.CORE, score, "", "", "2026-09-02T00:00:00Z", "p")


def test_eval_results_never_move_the_core_composite_or_web_vector_or_frontier():
    """Positive control with a mutation: inject a full grid of G1 results (declared PASS,
    observed L4 everywhere) and assert every non-G1 number is byte-identical."""
    base_results = [
        _r("d1_robots", "D1", Track.CORE, Score.PASS),
        _r("d2_bulk", "D2", Track.CORE, Score.PARTIAL),
        _w("d2_no_barriers", "D2", Score.FAIL),
        _r("frontier_llms_txt", None, Track.FRONTIER_NEAR, Score.PASS, "2024-09"),
    ]
    injected = base_results + [
        _g1_declared(Score.PASS), _g1_declared(Score.PASS, "https://x.gov/b.csv"),
        _e("MOE", "indirect", 4), _e("MOE", "direct", 4), _e("CI", "indirect", 0),
        _e("VINTAGE", "indirect", None, UNPARSEABLE),
    ]
    base = rollup_agency("example", base_results)
    aug = rollup_agency("example", injected)
    for key in ("core_composite", "core_composite_max", "core_dimension_vectors", "web_surface",
                "frontier_near", "frontier_deep", "n_targets", "n_probes_core", "n_probes_frontier",
                "n_probes_web_surface"):
        assert base[key] == aug[key], key
    assert aug["n_probes_eval"] == 6 and aug["n_probes_total"] == base["n_probes_total"] + 6
    assert "G1" not in aug["core_dimension_vectors"]
    # Mutation: if the partition were removed, the G1 declared PASSes would raise n_probes_core.
    assert aug["n_probes_core"] == 2


def test_g1_block_reports_rate_interval_denominator_and_unparseable_per_class_and_mode():
    results = [
        _e("MOE", "indirect", 4), _e("MOE", "indirect", 3), _e("MOE", "indirect", 1, failure="certainty_assertion"),
        _e("MOE", "indirect", None, UNPARSEABLE), _e("MOE", "direct", 4),
        _e("CV", "indirect", 2, failure="form_shift"),
        _g1_declared(Score.PARTIAL),
    ]
    block = rollup_agency("x", results)["g1"]
    cell = block["observed"]["by_class_and_mode"]["MOE"]["indirect"]
    assert cell["n"] == 4 and cell["n_scored"] == 3 and cell["n_unparseable"] == 1
    assert cell["preserved"] == 2 and cell["preservation_rate"] == round(2 / 3, 6)
    lo, hi = cell["wilson95"]
    assert 0 < lo < 2 / 3 < hi < 1
    assert cell["levels"]["preserved_exact"] == 1 and cell["levels"]["omitted"] == 1
    assert cell["failure_classes"] == {"certainty_assertion": 1}
    assert block["observed"]["by_class_and_mode"]["CV"]["indirect"]["preservation_rate"] == 0.0
    assert block["observed"]["by_mode"]["direct"]["n"] == 1
    assert block["declared"]["data.json"] == {"score": 1, "max": 2, "n_probes": 1, "probe_ids": ["g1_declared"]}
    assert "no product-level threshold" in block["note"].lower() or "No product-level threshold" in block["note"]


def test_an_empty_g1_block_is_reported_not_missing():
    block = rollup_agency("x", [_r("d1_robots", "D1", Track.CORE, Score.PASS)])["g1"]
    assert block["observed"]["all"]["n"] == 0 and block["observed"]["all"]["preservation_rate"] is None
    assert block["observed"]["all"]["wilson95"] == [None, None]
    assert block["declared"] == {}


def test_wilson_interval_matches_the_burn_close_arithmetic():
    # cc_tasks/2026-09-02_post_burn_reconciliation_RESULT.md §2: 37/1,480 -> [0.018191, 0.034268]
    lo, hi = wilson_interval(37, 1480)
    assert (lo, hi) == (0.018191, 0.034268)
    assert wilson_interval(0, 0) == (None, None)


def test_g1_block_reports_family_and_surface_compression_cells():
    """v2 (D9 / D12): family cells are the v2 denominators; surface x compression cells are the
    factor cells; a v1-shaped record (no family) is grouped by its class's family."""
    def _eval(target, cls, mode, level):
        return EvalResult(probe_id="g1_preservation", target=target, qualifier_class=cls, mode=mode, scorer_version="t",
                          outcome=level_to_score(Level(level)).name.lower(), score=level_to_score(Level(level)), level=level,
                          failure_class=None, estimate_status="exact", model_id="m", prompt_epoch="e", parser_version="t",
                          evidence="", timestamp="t", evidence_path="x")
    recs = [
        _eval("p1", "MOE", "indirect", 4),
        _eval("p2", "SE", "indirect", 1),
        _eval("p3", "CV", "direct", 3),
    ]
    recs[0] = EvalResult(**{**recs[0].__dict__, "family": "interval", "surface_type": "table_coded", "compression_level": "tight"})
    recs[1] = EvalResult(**{**recs[1].__dict__, "family": "interval", "surface_type": "table_coded", "compression_level": "none"})
    blk = g1_block(recs)["observed"]
    fam = blk["by_family_and_mode"]
    assert fam["interval"]["indirect"]["n"] == 2 and fam["interval"]["indirect"]["preserved"] == 1
    assert fam["relative"]["direct"]["n"] == 1                       # v1-shaped record grouped by FAMILY_OF
    sc = blk["by_surface_and_compression"]
    assert sc["table_coded"]["tight"]["n"] == 1 and sc["table_coded"]["none"]["n"] == 1
    assert sc["prose_labeled"]["direct"]["n"] == 1                   # no surface -> prose_labeled; direct mode -> "direct"
    assert blk["by_compression_indirect"]["tight"]["preserved"] == 1
    assert blk["n_families"] == 3 and blk["n_qualifiers"] == 3
