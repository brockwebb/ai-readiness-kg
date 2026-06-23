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
