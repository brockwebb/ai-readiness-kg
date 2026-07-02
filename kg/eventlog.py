#!/usr/bin/env python3
"""Sharded, append-only event log for the ai-readiness-kg build (DD-008).

The event log is the source of truth. The graph is a disposable projection rebuilt
by replaying these events; the events themselves are never mutated or deleted. Sharding
by ingest batch (``events/batch-NNN.jsonl``) is deliberate from the first event: a single
monolithic log grows past hosting size limits, so batches are bounded and independently
appendable (DD-008).

Every appended event is stamped with an ``event_id`` (uuid4), a UTC ``timestamp``, and the
active ``schema_version`` (read from ``kg/schema.yaml``) so each line is self-describing and
survives being handed to a stranger (DD-001). Stdlib only — no third-party dependencies.
"""
from __future__ import annotations

import datetime
import json
import re
import uuid
from pathlib import Path
from typing import Iterator

# Repo root = parent of the kg/ directory this module lives in.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_EVENTS_DIR = _REPO_ROOT / "events"
_SCHEMA_PATH = _REPO_ROOT / "kg" / "schema.yaml"

# Top-level `schema_version: "0.1"` line in kg/schema.yaml. Stdlib-only parse: we need
# exactly one scalar from a known key, not a YAML engine. Anchored to column 0 so a nested
# key of the same name could never shadow the top-level one.
_SCHEMA_VERSION_RE = re.compile(r'^schema_version:\s*"?([^"\s#]+)"?\s*(?:#.*)?$')


def _events_dir() -> Path:
    """The shard directory, created on first use so append never fails on a fresh clone."""
    _EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    return _EVENTS_DIR


def _shard_path(batch: int) -> Path:
    """events/batch-{NNN}.jsonl, NNN zero-padded to 3 digits."""
    if not isinstance(batch, int) or isinstance(batch, bool) or batch < 0:
        raise ValueError(f"batch must be a non-negative int, got {batch!r}")
    return _events_dir() / f"batch-{batch:03d}.jsonl"


def _now_iso() -> str:
    """Current time as a UTC ISO-8601 string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def schema_version() -> str:
    """Read the active schema version from kg/schema.yaml. Fail loud (standard 4) if the
    file or the top-level ``schema_version`` key is missing — a silent default would stamp
    every event with a wrong, unrecoverable version."""
    if not _SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"schema file not found: {_SCHEMA_PATH}")
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            m = _SCHEMA_VERSION_RE.match(line)
            if m:
                return m.group(1)
    raise ValueError(f"no top-level 'schema_version' key in {_SCHEMA_PATH}")


def append(event: dict, batch: int) -> str:
    """Append one event as a JSON line to ``events/batch-{batch:03d}.jsonl`` and return its
    ``event_id``.

    Injects (and overwrites, so the log's provenance is authoritative, not caller-supplied):
    ``event_id`` (uuid4 hex), ``timestamp`` (UTC ISO-8601), ``schema_version`` (from
    kg/schema.yaml). The line is flushed immediately so a crash mid-run leaves a valid prefix.
    """
    if not isinstance(event, dict):
        raise TypeError(f"event must be a dict, got {type(event).__name__}")
    event_id = uuid.uuid4().hex
    record = {
        **event,
        "event_id": event_id,
        "timestamp": _now_iso(),
        "schema_version": schema_version(),
    }
    line = json.dumps(record, ensure_ascii=False)
    with _shard_path(batch).open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
    return event_id


def current_batch() -> int:
    """Highest existing batch number, or 0 if no shards exist yet."""
    if not _EVENTS_DIR.is_dir():
        return 0
    highest = 0
    for path in _EVENTS_DIR.glob("batch-*.jsonl"):
        m = re.fullmatch(r"batch-(\d+)", path.stem)
        if m:
            highest = max(highest, int(m.group(1)))
    return highest


def replay() -> Iterator[dict]:
    """Yield every event across all shards, in batch order then line order.

    Fail loud on a corrupt line — a silently skipped event is a silently wrong projection
    (standard 4)."""
    if not _EVENTS_DIR.is_dir():
        return
    shards = sorted(
        (p for p in _EVENTS_DIR.glob("batch-*.jsonl") if re.fullmatch(r"batch-(\d+)", p.stem)),
        key=lambda p: int(p.stem.split("-", 1)[1]),
    )
    for shard in shards:
        with shard.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"corrupt event at {shard.name}:{lineno}: {exc}") from exc
