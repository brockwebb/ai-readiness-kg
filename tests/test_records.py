"""Behavior of the probe result data model: the score scale, the track firewall,
and JSON serialization that becomes the on-disk audit record."""
import json

from harness.records import Score, Track, ProbeResult


def test_score_scale_is_pass_partial_fail_2_1_0():
    # Pass/partial/fail only (2/1/0). No maturity tiers — Goodhart bait.
    assert int(Score.PASS) == 2
    assert int(Score.PARTIAL) == 1
    assert int(Score.FAIL) == 2 - 2  # 0, written so the intent is explicit


def test_core_track_is_in_core_composite_frontier_tracks_are_not():
    # The firewall: only core counts toward the headline composite.
    assert Track.CORE.in_core_composite is True
    assert Track.FRONTIER_NEAR.in_core_composite is False
    assert Track.FRONTIER_DEEP.in_core_composite is False


def test_probe_result_serializes_every_required_field():
    # The CC task fixes the emitted record shape exactly.
    result = ProbeResult(
        probe_id="d1_robots",
        target="https://example.gov/robots.txt",
        dimension="D1",
        track=Track.CORE,
        score=Score.PASS,
        as_of_date="",
        evidence="User-agent: *\nAllow: /\nSitemap: https://example.gov/sitemap.xml",
        timestamp="2026-06-23T00:00:00Z",
        evidence_path="evidence/example/d1_robots.txt",
    )
    d = result.to_dict()
    assert d["score"] == 2
    assert d["probe_id"] == "d1_robots"
    assert d["target"] == "https://example.gov/robots.txt"
    assert d["track"] == "core"
    assert d["dimension"] == "D1"
    assert d["as_of_date"] == ""
    assert d["timestamp"] == "2026-06-23T00:00:00Z"
    assert d["evidence_path"] == "evidence/example/d1_robots.txt"
    # The raw artifact travels with the record so the score is auditable.
    assert "Sitemap:" in d["evidence"]
    # Round-trips through JSON without loss.
    assert json.loads(json.dumps(d)) == d


def test_frontier_probe_result_carries_its_as_of_date():
    # The dating convention lives in the data, not just the rubric prose.
    result = ProbeResult(
        probe_id="frontier_llms_txt",
        target="https://example.gov/llms.txt",
        dimension=None,
        track=Track.FRONTIER_NEAR,
        score=Score.FAIL,
        as_of_date="2024-09",
        evidence="HTTP 404",
        timestamp="2026-06-23T00:00:00Z",
        evidence_path="evidence/example/frontier_llms_txt.txt",
    )
    d = result.to_dict()
    assert d["track"] == "frontier_near"
    assert d["as_of_date"] == "2024-09"
    assert d["dimension"] is None
