"""D0-r2 defect 1: d1_robots read robots.txt only. A page can withdraw itself
from discovery with <meta name="robots"> or an X-Robots-Tag header, and 77 of
98 sampled QuickFacts pages did (nofollow) while census.gov's robots.txt scored
PASS. The page-level leg reads both, per fetched page, from fixtures."""
import json
from pathlib import Path

from harness.probes.d1_robots_directives import (
    RobotsDirectivesProbe, parse_directives, robots_meta, x_robots_tag,
)
from harness.records import SOURCE_CATALOG, SOURCE_SITEMAP, Score
from harness.evidence import EvidenceStore
from harness.run import run_agency

from tests.helpers import FakeFetcher, fetched
from tests.test_runner import SETTINGS, _web_responses, _web_agency, BASE

FIXTURES = Path(__file__).parent / "fixtures"
NOFOLLOW_PAGE = (FIXTURES / "page_quickfacts_nofollow.html").read_text()
CLEAN_PAGE = (FIXTURES / "page_clean_no_directives.html").read_text()
URL = "https://x.gov/quickfacts/fact/table/US/PST045225"

META_NAMES = SETTINGS.robots_directive_meta_names
BLOCKING = SETTINGS.robots_blocking_directives


def _probe():
    return RobotsDirectivesProbe(META_NAMES, BLOCKING)


# --- the QuickFacts-shaped case and the clean case ---------------------------
def test_nofollow_meta_scores_partial_with_the_directive_as_evidence():
    page = fetched(URL, headers={"Content-Type": "text/html"}, body=NOFOLLOW_PAGE)
    score, evidence, obs = _probe().evaluate(page, {})
    assert score == Score.PARTIAL
    assert "meta[robots]=nofollow" in evidence
    # The observation carries every directive, blocking or not, by meta name.
    assert obs["robots_meta"]["robots"] == ["nofollow"]
    assert obs["robots_meta"]["googlebot"] == ["max-snippet:-1", "max-image-preview:large"]
    assert obs["x_robots_tag"] == {}


def test_clean_page_passes_and_records_that_nothing_was_seen():
    page = fetched(URL, headers={"Content-Type": "text/html"}, body=CLEAN_PAGE)
    score, evidence, obs = _probe().evaluate(page, {})
    assert score == Score.PASS
    assert obs == {"robots_meta": {}, "x_robots_tag": {}}
    assert "no robots meta" in evidence and "no X-Robots-Tag" in evidence


def test_description_and_viewport_metas_are_not_read_as_directives():
    assert robots_meta(CLEAN_PAGE, META_NAMES) == {}


# --- X-Robots-Tag ----------------------------------------------------------------
def test_x_robots_tag_noindex_scores_partial_even_on_a_clean_body():
    page = fetched(URL, headers={"Content-Type": "text/html",
                                 "X-Robots-Tag": "noindex, nofollow"}, body=CLEAN_PAGE)
    score, evidence, obs = _probe().evaluate(page, {})
    assert score == Score.PARTIAL
    assert obs["x_robots_tag"] == {"*": ["noindex", "nofollow"]}
    assert "x-robots-tag[*]=noindex" in evidence


def test_x_robots_tag_token_prefix_is_kept_and_valued_directives_are_not_tokens():
    parsed = x_robots_tag({"x-robots-tag": "max-snippet:-1, googlebot: noindex, nofollow"})
    assert parsed == {"*": ["max-snippet:-1"], "googlebot": ["noindex", "nofollow"]}


def test_x_robots_tag_scoped_to_one_bot_still_withdraws_the_page():
    page = fetched(URL, headers={"X-Robots-Tag": "googlebot: noindex"}, body=CLEAN_PAGE)
    score, evidence, _ = _probe().evaluate(page, {})
    assert score == Score.PARTIAL
    assert "x-robots-tag[googlebot]=noindex" in evidence


# --- bot-specific meta, the `none` shorthand, repeated tags ----------------------
def test_bot_specific_meta_noindex_scores_partial():
    body = '<html><head><meta name="GPTBot" content="noindex"></head></html>'
    score, evidence, obs = _probe().evaluate(fetched(URL, body=body), {})
    assert score == Score.PARTIAL
    assert obs["robots_meta"] == {"gptbot": ["noindex"]}


def test_configured_meta_name_without_bot_suffix_is_read():
    body = '<html><head><meta name="slurp" content="none"></head></html>'
    score, _, obs = _probe().evaluate(fetched(URL, body=body), {})
    assert score == Score.PARTIAL
    assert obs["robots_meta"] == {"slurp": ["none"]}


def test_unknown_meta_name_is_ignored_even_with_a_blocking_word():
    body = '<html><head><meta name="twitter:card" content="noindex"></head></html>'
    score, _, obs = _probe().evaluate(fetched(URL, body=body), {})
    assert score == Score.PASS and obs["robots_meta"] == {}


def test_repeated_robots_metas_are_concatenated_in_order():
    body = ('<html><head><meta name="robots" content="max-snippet:-1">'
            '<meta name="robots" content="NOINDEX"></head></html>')
    assert robots_meta(body, META_NAMES) == {"robots": ["max-snippet:-1", "noindex"]}


def test_parse_directives_splits_and_lowercases():
    assert parse_directives(" NoIndex ,nofollow, ,max-snippet:-1") == \
        ["noindex", "nofollow", "max-snippet:-1"]


def test_unretrievable_page_fails_with_empty_observations():
    page = fetched(URL, status=403, body="Forbidden")
    score, evidence, obs = _probe().evaluate(page, {})
    assert score == Score.FAIL
    assert "no directive readable" in evidence
    assert obs == {"robots_meta": {}, "x_robots_tag": {}}


# --- declarations ---------------------------------------------------------------
def test_probe_is_core_d1_and_applies_to_pages_only():
    p = _probe()
    assert p.dimension == "D1"
    assert p.applies_to(SOURCE_SITEMAP)
    assert not p.applies_to(SOURCE_CATALOG)


def test_probe_refuses_to_build_without_a_blocking_vocabulary():
    import pytest
    with pytest.raises(ValueError):
        RobotsDirectivesProbe(META_NAMES, [])


def test_blocking_vocabulary_comes_from_config_not_source():
    assert "nofollow" in BLOCKING and "noindex" in BLOCKING
    assert "robots" in META_NAMES


# --- through the runner ---------------------------------------------------------
def test_runner_records_directives_per_web_page_with_observations(tmp_path):
    resp = _web_responses(page_body=NOFOLLOW_PAGE)
    out = run_agency(_web_agency(), FakeFetcher(resp), EvidenceStore(root=tmp_path),
                     settings=SETTINGS, timestamp="2026-09-02T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)
    recs = [r for r in out["results"] if r.probe_id == "d1_robots_directives"]
    assert {r.source for r in recs} == {SOURCE_SITEMAP}
    assert len(recs) == 2 and all(r.score == Score.PARTIAL for r in recs)
    assert all(r.observations["robots_meta"]["robots"] == ["nofollow"] for r in recs)
    # Serialized record carries the observation under the data-dictionary name.
    d = recs[0].to_dict()
    assert "robots_meta" in d["observations"] and "x_robots_tag" in d["observations"]
    assert json.loads(json.dumps(d)) == d
    # Site-level robots.txt still scores on its own terms: the door is open.
    robots = next(r for r in out["results"] if r.probe_id == "d1_robots")
    assert robots.score == Score.PASS


def test_runner_does_not_apply_the_page_probe_to_catalog_distributions(tmp_path):
    out = run_agency(_web_agency(), FakeFetcher(_web_responses()), EvidenceStore(root=tmp_path),
                     settings=SETTINGS, timestamp="2026-09-02T00:00:00Z", sitemap_sample_seed=1)
    assert not any(r.probe_id == "d1_robots_directives" and r.source == SOURCE_CATALOG
                   for r in out["results"])
