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


# The real events/ directory is the source of truth (invariant 1). A test that appends to it
# writes synthetic facts into the append-only log, where the no-delete rule then protects them
# forever. This happened: tests/test_ground_truth.py drove phase_score without redirecting the
# event log and left `ground_truth_floor` events for documents `d#c1`/`d#c2` — which do not
# exist — in events/batch-021_ground_truth.jsonl, three of them committed.
#
# Autouse, so no future test can opt out by forgetting. Writes are refused unless _EVENTS_DIR
# has been repointed (ext_iso, or a test's own monkeypatch); reads are untouched, because
# tests that assert against the live ledger are legitimate.
_REAL_EVENTS_DIR = eventlog._EVENTS_DIR


@pytest.fixture(autouse=True)
def no_writes_to_the_real_event_log(monkeypatch):
    real_append = eventlog.append

    def guarded(event, batch, tag=None):
        if eventlog._EVENTS_DIR == _REAL_EVENTS_DIR:
            raise AssertionError(
                "test appended to the REAL event log "
                f"(event_type={event.get('event_type')!r}, batch={batch}, tag={tag!r}). "
                "Use the ext_iso fixture, or monkeypatch eventlog._EVENTS_DIR onto tmp_path."
            )
        return real_append(event, batch, tag)

    monkeypatch.setattr(eventlog, "append", guarded)


@pytest.fixture(autouse=True)
def restore_the_pinned_prompt_path(monkeypatch):
    """`apply_arm`/`apply_profile` rebind `model_stub._PROMPT_PATH` as arm-scoped state. A
    test that binds an arm's template and does not put it back leaves every later test reading
    `prompt_version` from the wrong prompt — the same class of defect as the one found in
    production: two reads of what is meant to be one fact, silently disagreeing.

    The restore goes through `monkeypatch`, not a snapshot-and-assign, because ordering bites:
    the guard fixture above already requests `monkeypatch`, so monkeypatch is set up FIRST and
    its undo stack unwinds LAST. A yield-based restore here ran before monkeypatch's undo, and
    monkeypatch then put the polluted value back. Registering the no-op setattr first makes
    this the last undo applied, which is the only ordering that wins."""
    from kg.extraction import model_stub
    monkeypatch.setattr(model_stub, "_PROMPT_PATH", model_stub._PROMPT_PATH)
