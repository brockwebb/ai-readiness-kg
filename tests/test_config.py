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
