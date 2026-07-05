#!/usr/bin/env python3
"""Document state machine + extraction event writer (schema_v0.1.md §7).

Lifecycle: discovered -> manifest_added -> extracted -> validated -> ingested.
Nothing skips manifest_added: attempting extraction on a document without a manifest_add
event is a hard error (§3/§7 — harvester finds are inert until the manifest gate opens).

All graph writes go through the existing sharded event log (kg.eventlog); the projected
graph is rebuilt by replaying these events. This module never mutates the log.
"""
from __future__ import annotations

import uuid

from kg import eventlog

# Ordered lifecycle. Index gives a total order for "at least this far" comparisons.
STATES = ["discovered", "manifest_added", "extracted", "validated", "ingested"]
_ORDER = {s: i for i, s in enumerate(STATES)}

# Extraction events land in their own shard, keeping the manifest stream (batch 1) clean.
EXTRACTION_BATCH = 2


class ExtractionError(RuntimeError):
    """Raised when the state machine's preconditions are violated (fail loud, standard 4)."""


def current_state(doc_id: str) -> str:
    """Replay the event log and return the document's furthest-reached state.

    manifest_add events advance a doc to ``manifest_added``; ``doc_state`` transition events
    advance it further. The maximum state reached wins (monotonic lifecycle)."""
    reached = _ORDER["discovered"]
    for ev in eventlog.replay():
        etype = ev.get("event_type")
        if etype == "manifest_add" and ev.get("payload", {}).get("doc_id") == doc_id:
            reached = max(reached, _ORDER["manifest_added"])
        elif etype == "doc_state" and ev.get("doc_id") == doc_id:
            to_state = ev.get("to_state")
            if to_state in _ORDER:
                reached = max(reached, _ORDER[to_state])
    return STATES[reached]


def require_state(doc_id: str, minimum: str) -> str:
    """Assert the document has reached at least ``minimum``; return its current state.
    Raises ExtractionError otherwise."""
    state = current_state(doc_id)
    if _ORDER[state] < _ORDER[minimum]:
        raise ExtractionError(
            f"document '{doc_id}' is in state '{state}'; needs at least '{minimum}' "
            f"(nothing skips manifest_added — §7)"
        )
    return state


def new_extraction_event_id() -> str:
    """One id per extraction run of a document; stamped on every item from that run (§4)."""
    return uuid.uuid4().hex


def transition(doc_id: str, to_state: str, *, batch: int | None = None) -> str:
    """Emit a ``doc_state`` transition event and return its event_id. The from_state is read
    live so the log records the actual prior state.

    ``batch`` resolves EXTRACTION_BATCH at call time (not def time) so a run driver may
    retarget the shard for its run (bulk v1 uses batch 4) by setting the module attribute."""
    if batch is None:
        batch = EXTRACTION_BATCH
    if to_state not in _ORDER:
        raise ValueError(f"unknown state {to_state!r}; must be one of {STATES}")
    from_state = current_state(doc_id)
    return eventlog.append(
        {"event_type": "doc_state", "doc_id": doc_id,
         "from_state": from_state, "to_state": to_state},
        batch=batch,
    )


def assert_item(doc_id: str, kind: str, extraction_event_id: str, provenance: dict,
                item: dict, *, batch: int | None = None) -> str:
    """Emit one node/edge assertion event carrying its provenance stamp (§4). ``kind`` is
    'node_asserted' or 'edge_asserted'."""
    if batch is None:
        batch = EXTRACTION_BATCH
    return eventlog.append(
        {"event_type": kind, "doc_id": doc_id,
         "extraction_event_id": extraction_event_id,
         "provenance": provenance, "payload": item},
        batch=batch,
    )
