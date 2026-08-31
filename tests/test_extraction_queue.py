"""Extraction queue (task 2026-08-27_extraction_queue + ADDENDUM-01, binding).

Every test drives a real entry point against a tmp event log. No total is hardcoded:
ADDENDUM-01 §2 requires counts be derived live, because the base file's numbers were stale
within three days of being written — and because this project has six recorded instances of a
test measuring a committed artifact instead of the generator that produced it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg import eventlog, queue  # noqa: E402


@pytest.fixture
def qenv(tmp_path, monkeypatch):
    """A queue over a tmp event log, tmp manifest, tmp profiles and tmp ledger."""
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": {
        "doc-a": {"doc_id": "doc-a", "identity": {"title": "A", "doc_type": "academic"},
                  "screening": {"decision": "included", "rationale": "in"}},
        "doc-b": {"doc_id": "doc-b", "identity": {"title": "B", "doc_type": "federal"},
                  "screening": {"decision": "included", "rationale": "in"}},
        "doc-out": {"doc_id": "doc-out", "identity": {"title": "O"},
                    "screening": {"decision": "excluded", "rationale": "out"}}}}))
    profiles = tmp_path / "run_profiles.yaml"
    profiles.write_text(yaml.safe_dump({
        "default": "prof_new",
        "profiles": {
            "prof_old": {"corpus_epoch": "epoch-old", "template_sha256": "a" * 64},
            "prof_new": {"corpus_epoch": "epoch-new", "template_sha256": "b" * 64},
            "prof_unpinned": {"corpus_epoch": "epoch-u"}}}))
    ledger = tmp_path / "spend_ledger.jsonl"
    ledger.write_text("")
    monkeypatch.setattr(queue, "_MANIFEST_PATH", manifest)
    monkeypatch.setattr(queue, "_PROFILES_PATH", profiles)
    monkeypatch.setattr(queue, "_LEDGER_PATH", ledger)
    monkeypatch.setattr(queue, "_DIXIE_DECISIONS", tmp_path / "decisions.jsonl")
    return {"tmp": tmp_path, "profiles": profiles, "ledger": ledger}


def _extraction(doc, epoch, eid, ts="2026-01-01T00:00:00+00:00"):
    eventlog.append({"event_type": "node_asserted", "doc_id": doc,
                     "provenance": {"corpus_epoch": epoch, "extraction_event_id": eid,
                                    "model_id": "m", "timestamp": ts},
                     "payload": {"id": "n1"}}, batch=queue.QUEUE_BATCH)


# ---------------------------------------------------------------- §7.1 refusal

def test_a_request_for_a_non_included_document_is_refused_not_emitted(qenv):
    """Admission precedes request. An event here would put work on an append-only log that no
    manifest decision backs — so it is a refusal WITH the reason, not a silent no-op."""
    with pytest.raises(queue.QueueRefusal) as exc:
        queue.request("doc-out", 1, "operator", "why")
    assert "not manifest-included" in str(exc.value)
    with pytest.raises(queue.QueueRefusal):
        queue.request("never-heard-of-it", 1, "operator", "why")
    assert queue.live_requests() == {}, "a refusal must leave no event behind"


def test_an_unpinned_profile_is_refused(qenv):
    """§1's other precondition: queueing future work against a prompt that can drift under it
    is how a burn silently changes instrument mid-flight."""
    with pytest.raises(queue.QueueRefusal) as exc:
        queue.request("doc-a", 1, "operator", "why", profile="prof_unpinned")
    assert "not sha-pinned" in str(exc.value)
    with pytest.raises(queue.QueueRefusal):
        queue.request("doc-a", 1, "operator", "why", profile="no_such_profile")


# ---------------------------------------------------------------- §7.2 state machine

def test_state_machine_not_requested_to_queued_to_extracting_to_extracted(qenv):
    assert queue.project()["doc-a"]["extraction_state"] == "not_requested"

    queue.request("doc-a", 1, "operator", "please")
    assert queue.project()["doc-a"]["extraction_state"] == "queued"

    # extracting: an OUTSTANDING reservation carrying this doc_id
    qenv["ledger"].write_text(json.dumps(
        {"record": "reserve", "run_id": "r", "reservation_id": "res1",
         "estimate_tokens": 1, "doc_id": "doc-a"}) + "\n")
    assert queue.project()["doc-a"]["extraction_state"] == "extracting"

    # settled -> no longer in flight; extraction under the pinned profile -> extracted
    with qenv["ledger"].open("a") as fh:
        fh.write(json.dumps({"record": "settle", "run_id": "r", "reservation_id": "res1",
                             "actual_tokens": 1}) + "\n")
    _extraction("doc-a", "epoch-new", "e1")
    assert queue.project()["doc-a"]["extraction_state"] == "extracted"


def test_withdraw_returns_a_document_to_not_requested(qenv):
    queue.request("doc-a", 1, "operator", "please")
    queue.withdraw("doc-a", "changed my mind")
    assert queue.project()["doc-a"]["extraction_state"] == "not_requested"
    # and a later request revives it — ordinary replay, no special case
    queue.request("doc-a", 2, "operator", "again")
    assert queue.project()["doc-a"]["extraction_state"] == "queued"


def test_latest_request_wins(qenv):
    queue.request("doc-a", 9, "operator", "first")
    queue.request("doc-a", 1, "operator", "second", superseding=True)
    row = queue.project()["doc-a"]
    assert row["priority"] == 1 and row["superseding"] is True


# ------------------------------------------- ADDENDUM-01 §4: the pin is read, never held

def test_flipping_the_pinned_profile_flips_extracted_to_stale_with_no_code_change(qenv):
    """The projection must READ the pin at projection time. A captured pin keeps reporting
    documents as extracted after the thing they were extracted under stops being current —
    and the production profile moved twice while this task was open."""
    _extraction("doc-a", "epoch-old", "e-old")
    doc = qenv["profiles"]
    cfg = yaml.safe_load(doc.read_text())

    cfg["default"] = "prof_old"
    doc.write_text(yaml.safe_dump(cfg))
    assert queue.pinned_profile() == "prof_old"
    assert queue.project()["doc-a"]["extraction_state"] == "extracted"

    cfg["default"] = "prof_new"          # the ONLY change
    doc.write_text(yaml.safe_dump(cfg))
    assert queue.project()["doc-a"]["extraction_state"] == "stale"


def test_a_superseding_request_moves_a_stale_document_back_into_the_worklist(qenv):
    _extraction("doc-a", "epoch-old", "e-old")
    assert queue.project()["doc-a"]["extraction_state"] == "stale"
    assert queue.worklist() == []
    queue.request("doc-a", 5, "burn", "re-extract under the new pin", superseding=True)
    assert queue.project()["doc-a"]["extraction_state"] == "queued"
    assert queue.worklist() == ["doc-a"]


def test_an_ambiguous_epoch_never_guesses_a_profile(qenv):
    """Several profiles can share a corpus epoch. Guessing one silently decides extracted vs
    stale, so the profile is reported unknown AND flagged instead."""
    cfg = yaml.safe_load(qenv["profiles"].read_text())
    cfg["profiles"]["prof_twin"] = {"corpus_epoch": "epoch-new", "template_sha256": "c" * 64}
    qenv["profiles"].write_text(yaml.safe_dump(cfg))
    _extraction("doc-a", "epoch-new", "e1")
    entry = queue.project()["doc-a"]["extracted_under"][0]
    assert entry["profile"] is None and entry["profile_ambiguous"] is True
    assert queue.project()["doc-a"]["extraction_state"] == "stale"


# ---------------------------------------------------------------- §7.3 worklist

def test_the_worklist_is_ordered_by_priority_and_ignores_everything_off_the_ledger(qenv):
    queue.request("doc-b", 1, "operator", "urgent")
    queue.request("doc-a", 9, "operator", "later")
    assert queue.worklist() == ["doc-b", "doc-a"]


def test_an_oversize_document_never_enters_the_worklist(qenv):
    queue.request("doc-a", 1, "operator", "please")
    eventlog.append({"event_type": "bulk_doc_skipped_oversize", "doc_id": "doc-a",
                     "chars": 9, "limit": 1}, batch=queue.QUEUE_BATCH)
    assert queue.project()["doc-a"]["extraction_state"] == "skipped_oversize"
    assert queue.worklist() == []
    # ... and clearing it puts the document back
    eventlog.append({"event_type": "bulk_doc_oversize_cleared", "doc_id": "doc-a"},
                    batch=queue.QUEUE_BATCH)
    assert queue.worklist() == ["doc-a"]


# ---------------------------------------------------------------- §7.4 reconciliation

def test_status_totals_reconcile_against_the_manifest_ADD_EVENTS_not_a_constant(qenv):
    """ADDENDUM-01 §2: no hardcoded totals. The base file's "currently 168" was stale within
    three days; this reads both sides live and reports whether they agree."""
    for doc in ("doc-a", "doc-b"):
        eventlog.append({"event_type": "manifest_add", "doc_id": doc,
                         "payload": {"doc_id": doc}}, batch=queue.QUEUE_BATCH)
    tot = queue.status_totals()
    assert tot["included"] == tot["manifest_add_events"] == 2
    assert tot["reconciles"] is True
    assert tot["total"] == 2


def test_a_reconciliation_MISMATCH_is_reported_not_hidden(qenv):
    """CONTROL: the check must be able to fail. A document admitted by event but absent from
    the projection (or the reverse) means one of the two is wrong."""
    eventlog.append({"event_type": "manifest_add", "doc_id": "doc-a",
                     "payload": {"doc_id": "doc-a"}}, batch=queue.QUEUE_BATCH)
    tot = queue.status_totals()
    assert tot["included"] == 2 and tot["manifest_add_events"] == 1
    assert tot["reconciles"] is False


# ---------------------------------------------------------------- backfill

def test_backfill_is_derived_from_epochs_and_is_idempotent(qenv):
    (qenv["tmp"] / "decisions.jsonl").write_text("\n".join(json.dumps(
        {"event_type": "corpus_epoch_declared",
         "payload": {"epoch": e, "member_doc_ids": m}})
        for e, m in (("epoch-old", ["doc-a"]), ("epoch-new", ["doc-b"]))))
    assert queue.corpus_epochs() == {"epoch-old": ["doc-a"], "epoch-new": ["doc-b"]}
    monkey = list(queue.BACKFILL)
    queue.BACKFILL = (("epoch-old", "prof_old", 50, "historical"),)
    try:
        plan = queue.backfill_plan()
        assert [r["document_id"] for r in plan] == ["doc-a"]
        queue.request("doc-a", 50, "backfill", "historical", profile="prof_old")
        assert queue.backfill_plan() == [], "a document already requested is not re-planned"
    finally:
        queue.BACKFILL = tuple(monkey)
