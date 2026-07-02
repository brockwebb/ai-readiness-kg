"""Tests for the sharded append-only event log (kg/eventlog.py, DD-008).

Hermetic: the module's shard directory and schema path are redirected into tmp_path so
tests never touch the real events/ or kg/schema.yaml.
"""
import json

import pytest

from kg import eventlog


@pytest.fixture
def isolated_log(tmp_path, monkeypatch):
    """Point eventlog at a throwaway events dir and a minimal schema in tmp_path."""
    events_dir = tmp_path / "events"
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events_dir)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema_path)
    return events_dir


def test_append_returns_event_id_and_injects_fields(isolated_log):
    eid = eventlog.append({"type": "manifest_add", "doc_id": "d1"}, batch=1)
    assert isinstance(eid, str) and len(eid) == 32  # uuid4 hex

    events = list(eventlog.replay())
    assert len(events) == 1
    ev = events[0]
    assert ev["event_id"] == eid
    assert ev["type"] == "manifest_add"
    assert ev["doc_id"] == "d1"
    assert ev["schema_version"] == "0.1"
    # timestamp is a parseable UTC ISO-8601 stamp
    assert ev["timestamp"].endswith("+00:00")


def test_shard_filename_zero_padded(isolated_log):
    eventlog.append({"type": "x"}, batch=7)
    assert (isolated_log / "batch-007.jsonl").is_file()


def test_replay_orders_across_batches_then_lines(isolated_log):
    # Append out of batch order and interleaved to prove ordering is by shard then line.
    eventlog.append({"n": 1}, batch=1)
    eventlog.append({"n": 4}, batch=2)
    eventlog.append({"n": 2}, batch=1)
    eventlog.append({"n": 5}, batch=2)
    eventlog.append({"n": 3}, batch=1)

    ns = [ev["n"] for ev in eventlog.replay()]
    assert ns == [1, 2, 3, 4, 5]


def test_shard_contents_are_valid_jsonl(isolated_log):
    eventlog.append({"type": "a"}, batch=1)
    eventlog.append({"type": "b"}, batch=1)

    shard = isolated_log / "batch-001.jsonl"
    lines = shard.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        rec = json.loads(line)  # raises if not valid JSON
        assert set(("event_id", "timestamp", "schema_version")) <= rec.keys()


def test_current_batch_reports_highest(isolated_log):
    assert eventlog.current_batch() == 0
    eventlog.append({"type": "x"}, batch=1)
    eventlog.append({"type": "x"}, batch=5)
    eventlog.append({"type": "x"}, batch=3)
    assert eventlog.current_batch() == 5


def test_replay_empty_when_no_shards(isolated_log):
    assert list(eventlog.replay()) == []


def test_append_stamps_are_authoritative(isolated_log):
    # Caller-supplied provenance fields must not override the log's own stamps.
    eid = eventlog.append(
        {"event_id": "FAKE", "timestamp": "1999", "schema_version": "9.9"}, batch=1
    )
    ev = list(eventlog.replay())[0]
    assert ev["event_id"] == eid != "FAKE"
    assert ev["timestamp"] != "1999"
    assert ev["schema_version"] == "0.1"


def test_replay_fails_loud_on_corrupt_line(isolated_log):
    eventlog.append({"type": "good"}, batch=1)
    with (isolated_log / "batch-001.jsonl").open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    with pytest.raises(ValueError, match="corrupt event"):
        list(eventlog.replay())
