"""Config loading. Per Engineering Standards §4, a missing config file fails loud
and early with a message naming the file — it never falls through to a silent
default that produces wrong behavior."""
import pytest

from harness.config import load_harness_config, load_agencies, ConfigError

REPO = __import__("pathlib").Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "config"


def test_loads_http_config_from_toml():
    cfg = load_harness_config(CONFIG_DIR / "harness.toml")
    assert cfg.user_agent.startswith("FSS-AI-Readiness-Probe")
    assert cfg.timeout_seconds == 20
    assert cfg.politeness_delay_seconds == 1.0
    assert cfg.evidence_root == "evidence"
    # Body cap must be large enough that real federal DCAT catalogs parse whole.
    assert cfg.max_body_bytes >= 20_000_000
    assert cfg.max_evidence_bytes > 0


def test_track_as_of_dates_come_from_config():
    cfg = load_harness_config(CONFIG_DIR / "harness.toml")
    assert cfg.track_as_of_date("frontier_near") == "2024-09"
    assert cfg.track_as_of_date("frontier_deep") == "2026-01"
    assert cfg.track_as_of_date("core") == ""


def test_loads_agencies_with_required_fields():
    agencies = load_agencies(CONFIG_DIR / "agencies.toml")
    ids = {a["id"] for a in agencies}
    assert {"census", "bls", "bea"} <= ids
    census = next(a for a in agencies if a["id"] == "census")
    assert census["catalog_url"] == "https://www.census.gov/data.json"
    assert census["base_url"] == "https://www.census.gov"


def test_missing_config_file_fails_loud_naming_the_path(tmp_path):
    missing = tmp_path / "does_not_exist.toml"
    with pytest.raises(ConfigError) as exc:
        load_harness_config(missing)
    assert "does_not_exist.toml" in str(exc.value)


def test_web_surface_sampling_tunables_come_from_config():
    """Sampling size, cap and seed are config, never buried in source (§2). The
    seed is config so a reviewer can redraw the same sample."""
    cfg = load_harness_config(CONFIG_DIR / "harness.toml")
    assert cfg.sitemap_sample_per_section >= 1
    assert cfg.sitemap_max_sections >= 0
    assert isinstance(cfg.sitemap_sample_seed, int)


def test_barrier_attempt_count_comes_from_config():
    cfg = load_harness_config(CONFIG_DIR / "harness.toml")
    assert cfg.no_barriers_attempts >= 1


def test_zero_barrier_attempts_fails_loud_rather_than_scoring_nothing(tmp_path):
    """A misconfigured attempt count would silently produce a probe that never
    fetches. Fail at load, naming the key (§4)."""
    bad = tmp_path / "harness.toml"
    good = (CONFIG_DIR / "harness.toml").read_text()
    bad.write_text(good.replace("attempts = 3", "attempts = 0"))
    with pytest.raises(ConfigError) as exc:
        load_harness_config(bad)
    assert "attempts" in str(exc.value)


def test_zero_sitemap_sample_size_fails_loud(tmp_path):
    bad = tmp_path / "harness.toml"
    good = (CONFIG_DIR / "harness.toml").read_text()
    bad.write_text(good.replace("sample_per_section = 3", "sample_per_section = 0"))
    with pytest.raises(ConfigError) as exc:
        load_harness_config(bad)
    assert "sample_per_section" in str(exc.value)


def test_census_records_its_sitemap_expectation():
    agencies = load_agencies(CONFIG_DIR / "agencies.toml")
    census = next(a for a in agencies if a["id"] == "census")
    assert census["sitemap_url"] == "https://www.census.gov/sitemapindex/sitemap.xml"


def test_agency_without_a_recorded_sitemap_is_allowed():
    """robots.txt still supplies one; a missing expectation is not an error."""
    agencies = load_agencies(CONFIG_DIR / "agencies.toml")
    bls = next(a for a in agencies if a["id"] == "bls")
    assert "sitemap_url" not in bls


# --- probe-depth tunables (task 2026-09-02_probe_depth_d0r2) --------------------
def test_probe_depth_tunables_come_from_config():
    cfg = load_harness_config(CONFIG_DIR / "harness.toml")
    assert cfg.sitemap_stale_after_days == 365
    assert "robots" in cfg.robots_directive_meta_names
    assert {"noindex", "nofollow", "none"} <= set(cfg.robots_blocking_directives)
    assert "*" in cfg.crawler_declared_user_agents
    assert cfg.crawler_observe_user_agents == ()
    assert 403 in cfg.crawler_refusal_statuses and 429 in cfg.crawler_refusal_statuses


@pytest.mark.parametrize("old, new, key", [
    ("stale_after_days = 365", "stale_after_days = 0", "stale_after_days"),
    ("stale_after_days = 365", 'stale_after_days = "365"', "stale_after_days"),
    ('discovery_blocking_directives = ["noindex", "nofollow", "none"]',
     "discovery_blocking_directives = []", "discovery_blocking_directives"),
    ('observe_user_agents = []', 'observe_user_agents = "GPTBot"', "observe_user_agents"),
    ("refusal_statuses = [401, 403, 429]", "refusal_statuses = []", "refusal_statuses"),
    ("refusal_statuses = [401, 403, 429]", 'refusal_statuses = ["403"]', "refusal_statuses"),
])
def test_bad_probe_depth_values_fail_loud_naming_the_key(tmp_path, old, new, key):
    good = (CONFIG_DIR / "harness.toml").read_text()
    assert old in good
    bad = tmp_path / "harness.toml"
    bad.write_text(good.replace(old, new))
    with pytest.raises(ConfigError) as exc:
        load_harness_config(bad)
    assert key in str(exc.value)


def test_missing_probe_depth_section_fails_loud(tmp_path):
    good = (CONFIG_DIR / "harness.toml").read_text()
    bad = tmp_path / "harness.toml"
    bad.write_text(good.replace("[probes.crawler_access]", "[probes.crawler_access_renamed]"))
    with pytest.raises(ConfigError) as exc:
        load_harness_config(bad)
    assert "crawler_access" in str(exc.value)


def test_enforced_observations_file_is_resolved_relative_to_the_config_dir(tmp_path):
    (tmp_path / "edge.json").write_text("{}")
    (tmp_path / "agencies.toml").write_text(
        '[[agency]]\nid = "a"\nname = "A"\nbase_url = "https://a.gov"\n'
        'enforced_observations_file = "edge.json"\n')
    agencies = load_agencies(tmp_path / "agencies.toml")
    assert agencies[0]["enforced_observations_file"] == str((tmp_path / "edge.json").resolve())


def test_blank_enforced_observations_file_fails_loud(tmp_path):
    (tmp_path / "agencies.toml").write_text(
        '[[agency]]\nid = "a"\nname = "A"\nbase_url = "https://a.gov"\n'
        'enforced_observations_file = ""\n')
    with pytest.raises(ConfigError) as exc:
        load_agencies(tmp_path / "agencies.toml")
    assert "enforced_observations_file" in str(exc.value)


def test_no_agency_ships_with_an_enforced_file_or_extra_identities():
    """The public tier sends only its own identity and holds no edge logs until
    an operator supplies them; the shipped config must say so."""
    for a in load_agencies(CONFIG_DIR / "agencies.toml"):
        assert "enforced_observations_file" not in a
