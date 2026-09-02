"""D0-r2 defect 4: no declared / enforced / observed access triad (skeleton A11).
`declared` is robots.txt eligibility per crawler token; `observed_public` is what
the harness's own requests received per identity, over the multi-attempt fetches
d2_no_barriers already makes; `enforced` is an operator-supplied hook. A
`declared_vs_observed_mismatch` fires when robots.txt allows a client the edge
refused. The QuickFacts-shaped case: `*` allows /quickfacts/, the edge answered
403, 200, 403, 403, 403."""
import json
from pathlib import Path

import pytest

from harness.crawler_access import (
    CHALLENGE_MARKERS, EnforcedObservationsError, MISMATCH_RULE_ID,
    declared_access, effective_crawler_access, enforced_access,
    load_enforced_observations, mismatch_warning, observed_access,
)
from harness.records import SOURCE_CATALOG, SOURCE_SITEMAP, Score
from harness.evidence import EvidenceStore
from harness.run import ProbeSettings, run_agency

from tests.helpers import FakeFetcher, fetched
from tests.test_runner import SETTINGS, _web_responses, _web_agency, BASE

FIXTURES = Path(__file__).parent / "fixtures"
ROBOTS = (FIXTURES / "robots_census_shaped.txt").read_text()
ENFORCED_FILE = FIXTURES / "enforced_observations_sample.json"
URL = f"{BASE}/quickfacts/US"
HARNESS_UA = SETTINGS.harness_user_agent
REFUSALS = SETTINGS.crawler_refusal_statuses
DECLARED = SETTINGS.crawler_declared_user_agents

OK = lambda: fetched(URL, status=200, body="<html>QuickFacts</html>")
REFUSED = lambda: fetched(URL, status=403, body="Forbidden")
RATE_LIMITED = lambda: fetched(URL, status=429, body="slow down")
CHALLENGE = lambda: fetched(URL, status=200, body="<title>Just a moment...</title>")
DOWN = lambda: fetched(URL, status=None, body="", error="TimeoutError")


# --- declared ------------------------------------------------------------------------
def test_declared_access_reads_per_token_groups():
    d = declared_access(ROBOTS, URL, ["*", "usasearch", HARNESS_UA, "Googlebot"])
    assert d["*"] == "allow"
    assert d["usasearch"] == "disallow"
    assert d[HARNESS_UA] == "allow"       # the harness matches the wildcard group
    assert d["Googlebot"] == "allow"


def test_missing_robots_allows_everything():
    assert declared_access("", URL, ["*", "GPTBot"]) == {"*": "allow", "GPTBot": "allow"}


def test_blanket_block_is_disallow_for_everyone_but_a_named_exception():
    robots = "User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nAllow: /\n"
    d = declared_access(robots, URL, ["*", "Googlebot", "GPTBot"])
    assert d == {"*": "disallow", "Googlebot": "allow", "GPTBot": "disallow"}


# --- observed ------------------------------------------------------------------------
def test_observed_outcomes_collapse_only_when_attempts_agree():
    obs = observed_access({
        "served": [OK(), OK()],
        "refused": [REFUSED(), REFUSED()],
        "mixed": [REFUSED(), OK(), REFUSED(), REFUSED(), REFUSED()],
        "challenge": [CHALLENGE()],
        "rate": [RATE_LIMITED()],
        "down": [DOWN()],
        "none": [],
    }, REFUSALS)
    assert obs["served"]["outcome"] == "served" and obs["served"]["refusal_fraction"] == 0.0
    assert obs["refused"]["outcome"] == "refused"
    assert obs["mixed"]["outcome"] == "mixed"
    assert obs["mixed"]["statuses"] == [403, 200, 403, 403, 403]
    assert obs["mixed"]["refusal_fraction"] == 0.8
    assert obs["challenge"]["outcome"] == "challenge"
    assert obs["rate"]["outcome"] == "refused"        # 429 is in the configured refusal list
    assert obs["down"]["outcome"] == "unreachable"
    assert obs["none"]["outcome"] == "unobserved" and obs["none"]["refusal_fraction"] is None


def test_challenge_markers_include_bot_management_interstitials():
    assert "just a moment" in CHALLENGE_MARKERS and "cf-chl" in CHALLENGE_MARKERS


# --- the warning rule ------------------------------------------------------------------
def _access(attempts, robots=ROBOTS, enforced=None):
    return effective_crawler_access(robots, URL, {HARNESS_UA: attempts}, DECLARED,
                                    REFUSALS, enforced)


def test_quickfacts_shaped_case_fires_the_mismatch():
    access = _access([REFUSED(), OK(), REFUSED(), REFUSED(), REFUSED()])
    layers = access["layers"][HARNESS_UA]
    assert layers["declared"] == "allow"
    assert layers["observed_public"]["outcome"] == "mixed"
    assert layers["enforced"] is None
    warn = mismatch_warning(access)
    assert warn["fired"] is True
    assert warn["rule_id"] == MISMATCH_RULE_ID and warn["rule_version"]
    hit = warn["declared_vs_observed_mismatch"][0]
    assert hit["user_agent"] == HARNESS_UA
    assert hit["statuses"] == [403, 200, 403, 403, 403]
    assert hit["refusal_fraction"] == 0.8


def test_clean_case_does_not_fire():
    warn = mismatch_warning(_access([OK(), OK(), OK()]))
    assert warn["fired"] is False and warn["declared_vs_observed_mismatch"] == []


def test_disallowed_and_refused_is_consistent_not_a_mismatch():
    robots = "User-agent: *\nDisallow: /quickfacts/\n"
    warn = mismatch_warning(_access([REFUSED(), REFUSED()], robots=robots))
    assert warn["fired"] is False


def test_disallowed_but_served_is_recorded_without_firing():
    robots = "User-agent: *\nDisallow: /quickfacts/\n"
    warn = mismatch_warning(_access([OK(), OK()], robots=robots))
    assert warn["fired"] is False
    assert warn["declared_disallowed_but_served"] == [HARNESS_UA]


def test_a_single_challenge_page_among_served_attempts_fires():
    assert mismatch_warning(_access([OK(), CHALLENGE(), OK()]))["fired"] is True


def test_declared_only_tokens_carry_no_observed_leg():
    access = _access([OK()])
    assert access["layers"]["Googlebot"]["observed_public"] is None
    assert access["layers"]["Googlebot"]["declared"] == "allow"
    assert set(DECLARED) <= set(access["layers"])


# --- the enforced hook -------------------------------------------------------------------
def test_no_path_means_no_enforced_observations():
    assert load_enforced_observations(None) is None
    assert load_enforced_observations("") is None


def test_enforced_file_loads_and_merges_into_the_layers():
    enforced = load_enforced_observations(str(ENFORCED_FILE))
    access = _access([OK()], enforced=enforced)
    assert access["layers"]["*"]["enforced"]["action"] == "challenge"
    assert access["layers"]["Googlebot"]["enforced"]["action"] == "allow"
    assert access["layers"][HARNESS_UA]["enforced"] is None
    assert access["enforced_source"].startswith("sample edge export")
    assert access["enforced_note"] is None


def test_enforced_access_is_null_for_urls_the_file_does_not_cover():
    enforced = load_enforced_observations(str(ENFORCED_FILE))
    assert enforced_access(enforced, "https://x.gov/other", ["*"]) == {"*": None}


def test_missing_enforced_file_fails_loud(tmp_path):
    with pytest.raises(EnforcedObservationsError) as exc:
        load_enforced_observations(str(tmp_path / "nope.json"))
    assert "nope.json" in str(exc.value)


@pytest.mark.parametrize("bad", [
    "not json",
    json.dumps({"schema": "wrong", "observations": {}}),
    json.dumps({"schema": "enforced_observations/1", "observations": []}),
    json.dumps({"schema": "enforced_observations/1",
                "observations": {"https://x.gov/u": {"*": {"action": "smite"}}}}),
])
def test_malformed_enforced_file_fails_loud(tmp_path, bad):
    p = tmp_path / "enforced.json"
    p.write_text(bad)
    with pytest.raises(EnforcedObservationsError):
        load_enforced_observations(str(p))


# --- through the runner ---------------------------------------------------------------------
def test_barrier_record_carries_the_triad_and_the_warning_fires_on_a_refusing_page(tmp_path):
    resp = _web_responses(page_status=403, page_body="Forbidden")
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body=ROBOTS)
    resp["https://x.gov/sitemapindex/sitemap.xml"] = resp[
        "https://x.gov/sitemapindex/sitemap.xml"]
    fetcher = FakeFetcher(resp)
    out = run_agency(_web_agency(), fetcher, EvidenceStore(root=tmp_path),
                     settings=SETTINGS, timestamp="2026-09-02T00:00:00Z",
                     no_barriers_attempts=3, sitemap_sample_per_section=1,
                     sitemap_sample_seed=1)
    rec = next(r for r in out["results"]
               if r.probe_id == "d2_no_barriers" and r.source == SOURCE_SITEMAP)
    assert rec.score == Score.FAIL
    access = rec.observations["effective_crawler_access"]
    assert access["layers"][HARNESS_UA]["declared"] == "allow"
    assert access["layers"][HARNESS_UA]["observed_public"]["outcome"] == "refused"
    assert rec.observations["crawler_policy_mismatch_warning"]["fired"] is True
    assert rec.observations["refusal_fraction"] == 1.0
    # The declared-only tokens are listed with no observed leg: never sent.
    assert access["layers"]["Googlebot"]["observed_public"] is None
    # By default no request went out under any identity but the harness's.
    assert all(len(c) == 2 for c in fetcher.calls)
    written = Path(rec.evidence_path).read_text()
    assert "CRAWLER ACCESS (declared / enforced / observed)" in written
    # The catalog distribution got the same triad, on its own record.
    cat = next(r for r in out["results"]
               if r.probe_id == "d2_no_barriers" and r.source == SOURCE_CATALOG)
    assert cat.observations["crawler_policy_mismatch_warning"]["fired"] is False


def test_extra_observe_identities_are_sent_and_reported_per_identity(tmp_path):
    settings = ProbeSettings(**{**SETTINGS.__dict__,
                                "crawler_observe_user_agents": ("GPTBot",)})
    resp = _web_responses()
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body=ROBOTS)
    # The edge serves the harness and refuses the named token.
    for page in (f"{BASE}/quickfacts/US", f"{BASE}/tables/t01.html"):
        resp[(page, "GPTBot")] = fetched(page, status=403, body="Forbidden")
    fetcher = FakeFetcher(resp)
    out = run_agency(_web_agency(), fetcher, EvidenceStore(root=tmp_path),
                     settings=settings, timestamp="2026-09-02T00:00:00Z",
                     no_barriers_attempts=2, sitemap_sample_per_section=1,
                     sitemap_sample_seed=1)
    rec = next(r for r in out["results"]
               if r.probe_id == "d2_no_barriers" and r.source == SOURCE_SITEMAP)
    # The score is the harness identity's: served.
    assert rec.score == Score.PASS
    layers = rec.observations["effective_crawler_access"]["layers"]
    assert layers[HARNESS_UA]["observed_public"]["outcome"] == "served"
    assert layers["GPTBot"]["declared"] == "allow"
    assert layers["GPTBot"]["observed_public"]["outcome"] == "refused"
    warn = rec.observations["crawler_policy_mismatch_warning"]
    assert warn["fired"] is True
    assert [h["user_agent"] for h in warn["declared_vs_observed_mismatch"]] == ["GPTBot"]
    ua_calls = [c for c in fetcher.calls if len(c) == 3 and c[0] == rec.target]
    assert len(ua_calls) == 2 and all(c[2] == "GPTBot" for c in ua_calls)
    assert Path(rec.evidence_path).read_text().count("USER-AGENT 'GPTBot' ATTEMPT") == 2
    assert out["enumeration"]["crawler_access"]["observed_user_agents"] == [HARNESS_UA, "GPTBot"]


def test_configured_enforced_file_reaches_the_record(tmp_path):
    agency = dict(_web_agency(), enforced_observations_file=str(ENFORCED_FILE))
    resp = _web_responses()
    resp[f"{BASE}/robots.txt"] = fetched(f"{BASE}/robots.txt", body=ROBOTS)
    out = run_agency(agency, FakeFetcher(resp), EvidenceStore(root=tmp_path),
                     settings=SETTINGS, timestamp="2026-09-02T00:00:00Z",
                     sitemap_sample_per_section=2, sitemap_sample_seed=1)
    rec = next(r for r in out["results"] if r.probe_id == "d2_no_barriers"
               and r.target == f"{BASE}/quickfacts/US")
    layers = rec.observations["effective_crawler_access"]["layers"]
    assert layers["*"]["enforced"]["action"] == "challenge"


def test_malformed_enforced_file_stops_the_run_before_any_request(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    agency = dict(_web_agency(), enforced_observations_file=str(bad))
    fetcher = FakeFetcher(_web_responses())
    with pytest.raises(EnforcedObservationsError):
        run_agency(agency, fetcher, EvidenceStore(root=tmp_path), settings=SETTINGS,
                   timestamp="2026-09-02T00:00:00Z")
    assert fetcher.calls == []


def test_default_config_sends_no_third_party_identity():
    assert SETTINGS.crawler_observe_user_agents == ()
    assert "*" in DECLARED and 429 in REFUSALS
