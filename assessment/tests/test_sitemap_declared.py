"""D0-r2 defect 2: d1_sitemap read the fixed path /sitemap.xml and had no
non-stale condition. On census.gov the declared sitemap (robots.txt) and the
fixed path are different documents; the fixed path's 5,408 entries carry
lastmod values from 2013-2015 and scored PASS. The June task made the ENUMERATOR
follow robots.txt; the probe still read the fixed path. This closes the probe."""
from datetime import date
from pathlib import Path

import pytest

from harness.probes.d1_sitemap import (
    SOURCE_FIXED_PATH, SOURCE_ROBOTS, SitemapProbe, newest_lastmod, parse_lastmod,
)
from harness.records import Score
from harness.evidence import EvidenceStore
from harness.run import run_agency

from tests.helpers import FakeFetcher, fetched
from tests.test_runner import SETTINGS, _responses, BASE

FIXTURES = Path(__file__).parent / "fixtures"
ROBOTS = (FIXTURES / "robots_census_shaped.txt").read_text()
STALE_FIXED = (FIXTURES / "sitemap_fixed_path_stale.xml").read_text()
CURRENT_INDEX = (FIXTURES / "sitemap_index_current.xml").read_text()
DECLARED = "https://x.gov/sitemapindex/sitemap.xml"
FIXED = "https://x.gov/sitemap.xml"
TODAY = date(2026, 9, 2)
STALE_DAYS = SETTINGS.sitemap_stale_after_days


def _probe():
    return SitemapProbe(STALE_DAYS)


# --- which document is read -----------------------------------------------------
def test_resolve_follows_the_robots_declared_sitemap_even_uppercase():
    assert _probe().resolve(BASE, ROBOTS) == (DECLARED, SOURCE_ROBOTS)


def test_resolve_falls_back_to_the_fixed_path_and_says_so():
    assert _probe().resolve(BASE, "User-agent: *\nAllow: /\n") == (FIXED, SOURCE_FIXED_PATH)
    assert _probe().resolve(BASE, "") == (FIXED, SOURCE_FIXED_PATH)


# --- staleness: the QuickFacts-shaped case and the clean case -------------------
def test_fixed_path_with_2013_to_2015_lastmods_is_partial_with_the_newest_as_evidence():
    f = fetched(FIXED, body=STALE_FIXED)
    score, evidence, obs = _probe().evaluate(f, sitemap_source=SOURCE_FIXED_PATH, today=TODAY)
    assert score == Score.PARTIAL
    assert "stale" in evidence and "2015-11-30T14:05:00Z" in evidence
    assert obs["sitemap_source"] == "fixed_path_fallback"
    assert obs["sitemap_lastmod"] == "2015-11-30T14:05:00Z"
    assert obs["sitemap_lastmod_count"] == 3 and obs["sitemap_entries"] == 4
    warn = obs["sitemap_stale_warning"]
    assert warn["fired"] is True and warn["determinable"] is True
    assert warn["rule_id"] == "sitemap_stale" and warn["rule_version"]
    assert warn["stale_after_days"] == STALE_DAYS and warn["evaluated_on"] == "2026-09-02"


def test_declared_index_with_a_recent_lastmod_passes():
    f = fetched(DECLARED, body=CURRENT_INDEX)
    score, evidence, obs = _probe().evaluate(f, sitemap_source=SOURCE_ROBOTS, today=TODAY)
    assert score == Score.PASS
    assert obs["sitemap_lastmod"] == "2026-08-15"
    assert obs["sitemap_stale_warning"]["fired"] is False
    assert obs["sitemap_stale_warning"]["age_days"] == 18


def test_threshold_is_a_strict_boundary():
    body = ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://x.gov/a</loc><lastmod>2025-09-02</lastmod></url></urlset>')
    on_the_day = SitemapProbe(365).evaluate(fetched(FIXED, body=body), today=TODAY)
    assert on_the_day[0] == Score.PASS and on_the_day[2]["sitemap_stale_warning"]["age_days"] == 365
    one_day_over = SitemapProbe(364).evaluate(fetched(FIXED, body=body), today=TODAY)
    assert one_day_over[0] == Score.PARTIAL


def test_no_lastmod_anywhere_is_recorded_null_and_not_scored_stale():
    body = ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://x.gov/a</loc></url></urlset>')
    score, evidence, obs = _probe().evaluate(fetched(FIXED, body=body), today=TODAY)
    assert score == Score.PASS
    assert obs["sitemap_lastmod"] is None
    assert obs["sitemap_stale_warning"]["determinable"] is False
    assert obs["sitemap_stale_warning"]["fired"] is False
    assert "not determinable" in evidence


def test_unparseable_and_empty_documents_keep_their_partial_verdicts():
    assert _probe().evaluate(fetched(FIXED, body="not xml"), today=TODAY)[0] == Score.PARTIAL
    empty = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    assert _probe().evaluate(fetched(FIXED, body=empty), today=TODAY)[0] == Score.PARTIAL


def test_absent_sitemap_fails():
    score, _, obs = _probe().evaluate(fetched(DECLARED, status=404, body=""),
                                      sitemap_source=SOURCE_ROBOTS, today=TODAY)
    assert score == Score.FAIL and obs["sitemap_source"] == "robots.txt"


# --- lastmod parsing --------------------------------------------------------------
@pytest.mark.parametrize("raw, expected", [
    ("2024-05-01", date(2024, 5, 1)),
    ("2024-05-01T10:00:00Z", date(2024, 5, 1)),
    ("2024-05-01T10:00:00+02:00", date(2024, 5, 1)),
    ("2024-05-01T10:00:00.123-05:00", date(2024, 5, 1)),
    ("yesterday", None), ("", None), (None, None), ("2024-13-01", None),
])
def test_parse_lastmod_handles_w3c_datetime_forms(raw, expected):
    assert parse_lastmod(raw) == expected


def test_newest_lastmod_ignores_unparseable_values_but_counts_them():
    raw, newest, count = newest_lastmod(["2013-04-02", "garbage", None, "2015-11-30"])
    assert raw == "2015-11-30" and newest == date(2015, 11, 30) and count == 3


# --- divergence between declared and fixed path ----------------------------------
def test_divergence_is_reported_as_evidence_and_the_declared_document_is_scored():
    declared = fetched(DECLARED, body=CURRENT_INDEX)
    fixed = fetched(FIXED, body=STALE_FIXED)
    score, evidence, obs = _probe().evaluate(declared, sitemap_source=SOURCE_ROBOTS,
                                             fixed_path_fetched=fixed, today=TODAY)
    assert score == Score.PASS  # the declared document is current
    div = obs["sitemap_divergence"]
    assert div["same_document"] is False
    assert div["fixed_path"]["entries"] == 4
    assert div["fixed_path"]["sitemap_lastmod"] == "2015-11-30T14:05:00Z"
    assert div["fixed_path"]["stale"] is True


def test_threshold_must_be_a_positive_integer():
    for bad in (0, -1, True, "365"):
        with pytest.raises(ValueError):
            SitemapProbe(bad)


def test_threshold_is_config_not_a_constant():
    assert STALE_DAYS == 365


# --- through the runner ------------------------------------------------------------
def _agency():
    return {"id": "s", "name": "S", "base_url": BASE, "catalog_url": f"{BASE}/data.json"}


def test_runner_scores_the_declared_sitemap_and_reads_the_fixed_path_for_divergence(tmp_path):
    resp = _responses()
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body=ROBOTS)
    resp[DECLARED] = fetched(DECLARED, body=CURRENT_INDEX)
    resp[FIXED] = fetched(FIXED, body=STALE_FIXED)
    fetcher = FakeFetcher(resp)
    out = run_agency(_agency(), fetcher, EvidenceStore(root=tmp_path), settings=SETTINGS,
                     timestamp="2026-09-02T00:00:00Z", enumerate_sitemap=False,
                     today=TODAY)
    rec = next(r for r in out["results"] if r.probe_id == "d1_sitemap")
    assert rec.target == DECLARED
    assert rec.score == Score.PASS
    assert rec.observations["sitemap_source"] == "robots.txt"
    assert rec.observations["sitemap_divergence"]["same_document"] is False
    urls = [c[0] for c in fetcher.calls]
    assert DECLARED in urls and FIXED in urls
    # Both documents are in the evidence file, the fixed path labelled as comparator.
    written = Path(rec.evidence_path).read_text()
    assert "FIXED PATH" in written and "divergence comparator" in written


def test_runner_falls_back_to_the_fixed_path_when_robots_declares_none(tmp_path):
    resp = _responses()
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body="User-agent: *\nAllow: /\n")
    resp[FIXED] = fetched(FIXED, body=STALE_FIXED)
    fetcher = FakeFetcher(resp)
    out = run_agency(_agency(), fetcher, EvidenceStore(root=tmp_path), settings=SETTINGS,
                     timestamp="2026-09-02T00:00:00Z", enumerate_sitemap=False,
                     today=TODAY)
    rec = next(r for r in out["results"] if r.probe_id == "d1_sitemap")
    assert rec.target == FIXED
    assert rec.score == Score.PARTIAL  # the stale fixed path is what a guessing client gets
    assert rec.observations["sitemap_source"] == "fixed_path_fallback"
    assert "sitemap_divergence" not in rec.observations
    assert [c[0] for c in fetcher.calls].count(FIXED) == 1
