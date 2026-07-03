"""Shared fixtures for extraction tests: redirect all on-disk writes into tmp_path so tests
never touch the real events/, corpus/staging/, or kg/schema.yaml.

The extraction parser reads the *real* kg/schema.yaml (the authoritative type catalogue);
only the event log's schema_version read is redirected to a minimal tmp schema.
"""
import pytest

from kg import eventlog
from kg.extraction import metrics as metrics_mod
from kg.extraction import staging


@pytest.fixture
def ext_iso(tmp_path, monkeypatch):
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    monkeypatch.setattr(metrics_mod, "_METRICS_DIR", tmp_path / "metrics")
    monkeypatch.setattr(staging, "_REVIEW_DIR", tmp_path / "proposed")
    return tmp_path
