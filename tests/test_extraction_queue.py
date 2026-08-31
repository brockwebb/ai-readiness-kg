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


# ------------------------------------------------------- deferral (bulk_v038 Phase 0.3)
def test_a_deferral_is_a_third_thing_not_a_withdrawal_and_not_silence(qenv):
    """`not_requested` means nobody looked; `deferred` means we looked and declined, and the
    reason is on the record. Collapsing the two would make the extract/defer cut invisible the
    moment it was taken — that cut is 159 of 194 documents, i.e. most of the corpus."""
    queue.defer("doc-a", "no consumer")
    rows = queue.project()
    assert rows["doc-a"]["extraction_state"] == "deferred"
    assert rows["doc-a"]["deferred_reason"] == "no consumer"
    assert rows["doc-b"]["extraction_state"] == "not_requested"
    assert rows["doc-b"]["deferred_reason"] is None


def test_a_deferral_is_refused_while_a_live_request_stands(qenv):
    """Two live decisions about one document, disagreeing: the worklist would still run it
    while the status surface reported it declined."""
    queue.request("doc-a", 1, "test", "wanted")
    with pytest.raises(queue.QueueRefusal) as exc:
        queue.defer("doc-a", "no consumer")
    assert "live extraction_request" in str(exc.value)
    assert queue.project()["doc-a"]["extraction_state"] == "queued"


def test_a_later_request_revives_a_deferred_document(qenv):
    """Correct-forward, never a deletion: the deferral stays on the log and the request
    follows it. A cut taken today must not permanently bar a document whose consumer appears
    tomorrow."""
    queue.defer("doc-a", "no consumer")
    assert queue.project()["doc-a"]["extraction_state"] == "deferred"
    queue.request("doc-a", 1, "test", "a crosswalk item needs it now")
    assert queue.project()["doc-a"]["extraction_state"] == "queued"


def test_deferring_an_unadmitted_document_is_refused_not_logged(qenv):
    with pytest.raises(queue.QueueRefusal):
        queue.defer("doc-out", "no consumer")
    with pytest.raises(queue.QueueRefusal):
        queue.defer("ghost", "no consumer")
    assert not queue.deferrals()


def test_a_reasonless_deferral_is_refused(qenv):
    """An unexplained gap in the corpus is exactly what the queue exists to prevent."""
    with pytest.raises(queue.QueueRefusal):
        queue.defer("doc-a", "")


def test_a_deferral_does_not_erase_extraction_history(qenv):
    """Deferral speaks to future work only. A document already extracted under the pin still
    reads `extracted` after it is deferred — otherwise the cut would hide real graph content
    and the projection would under-report what is in the KG."""
    _extraction("doc-a", "epoch-new", "e1")
    queue.defer("doc-a", "no consumer")
    assert queue.project()["doc-a"]["extraction_state"] == "extracted"


def test_deferred_documents_never_reach_the_worklist(qenv):
    """The point of the cut: `next` must not hand the burn a document we declined to spend
    on. This drives the same derivation the driver reads, not a copy of it."""
    queue.request("doc-b", 1, "test", "wanted")
    queue.defer("doc-a", "no consumer")
    assert list(queue.worklist()) == ["doc-b"]


def test_the_suite_cannot_write_to_the_real_event_log(qenv):
    """The autouse guard in conftest, driven rather than assumed. Two tests wrote synthetic
    `ground_truth_floor` events for documents that do not exist into
    events/batch-021_ground_truth.jsonl — three of them committed — because nothing stopped
    them. The no-delete invariant then protects that pollution permanently."""
    from kg import eventlog
    real = Path(__file__).resolve().parent.parent / "events"
    monkey = eventlog._EVENTS_DIR
    eventlog._EVENTS_DIR = real
    try:
        with pytest.raises(AssertionError) as exc:
            eventlog.append({"event_type": "junk"}, batch=999)
        assert "REAL event log" in str(exc.value)
    finally:
        eventlog._EVENTS_DIR = monkey
        # A MUTATED guard lets the write through, and this test would then leave its own junk
        # shard in the real log — which is exactly the failure it exists to prevent. It did,
        # once, during the mutation matrix. Clean up unconditionally, not on the happy path.
        (real / "batch-999.jsonl").unlink(missing_ok=True)


def test_a_deferral_outranks_stale_because_stale_claims_work_is_owed(qenv):
    """`stale` means re-extraction is owed under the current pin. A deferral is the decision
    that it is NOT owed, so it must win — otherwise every previously-extracted document the
    cut declined keeps advertising work nobody intends to do. Live measurement: 104 of the
    159 documents the bulk_v038 cut deferred were reading `stale`."""
    _extraction("doc-a", "epoch-old", "e1")
    assert queue.project()["doc-a"]["extraction_state"] == "stale"
    queue.defer("doc-a", "no consumer")
    row = queue.project()["doc-a"]
    assert row["extraction_state"] == "deferred"
    assert row["latest_extraction"]["corpus_epoch"] == "epoch-old"   # history not erased


def test_a_superseding_request_beats_stale_so_re_extraction_shows_as_queued(qenv):
    """A document extracted under an older profile and requested again is work IN THE QUEUE,
    not a passive `stale` row. Without the superseding flag the bulk_v038 worklist reported
    6 queued against 35 emitted requests."""
    _extraction("doc-a", "epoch-old", "e1")
    queue.request("doc-a", 1, "test", "re-extract under the new pin", superseding=True)
    assert queue.project()["doc-a"]["extraction_state"] == "queued"


# ------------------------------------------- chunk-unit completeness (bulk_v038 Phase A)
def _census(doc, profile, n, purpose=None):
    eventlog.append({"event_type": queue.CENSUS, "document_id": doc, "profile": profile,
                     "n_chunks": n, "source_sha256": "s"}, batch=queue.QUEUE_BATCH)


def _chunk(doc, chunk_id, purpose):
    eventlog.append({"event_type": "chunk_metrics", "purpose": purpose, "doc_id": doc,
                     "chunk_id": chunk_id, "counts": {}}, batch=queue.QUEUE_BATCH)


def _make_pin_chunk_unit(qenv):
    """Make the pinned profile chunk-unit, the way `bulk_v038` is."""
    doc = yaml.safe_load(qenv["profiles"].read_text())
    doc["profiles"]["prof_new"]["emission_contract"] = "anchor"
    qenv["profiles"].write_text(yaml.safe_dump(doc))


def test_one_chunk_of_forty_does_not_make_a_document_extracted(qenv):
    """Measured live: Phase A sampled a single chunk from 25 documents, every one of them read
    `extracted` under the pin, and the burn worklist those documents should have led fell from
    33 to 10. A chunk-unit profile's completeness is coverage against the census."""
    _make_pin_chunk_unit(qenv)
    _extraction("doc-a", "epoch-new", "e1")
    queue.request("doc-a", 1, "test", "burn it", superseding=True)
    _census("doc-a", "prof_new", 40)
    _chunk("doc-a", "doc-a#c0001", "prof_new")
    row = queue.project()["doc-a"]
    assert row["extraction_state"] == "queued"
    assert (row["chunks_extracted"], row["chunks_total"]) == (1, 40)
    assert queue.worklist() == ["doc-a"]


def test_full_coverage_does_make_it_extracted(qenv):
    """The other direction, or the test above would pass on a projection that never says
    `extracted` at all. A single-chunk document extracted once IS done — that is the live
    case for anthropic-crawler-support-article."""
    _make_pin_chunk_unit(qenv)
    _extraction("doc-a", "epoch-new", "e1")
    _census("doc-a", "prof_new", 2)
    _chunk("doc-a", "doc-a#c0001", "prof_new")
    _chunk("doc-a", "doc-a#c0002", "prof_new")
    assert queue.project()["doc-a"]["extraction_state"] == "extracted"
    assert queue.worklist() == []


def test_a_whole_document_profile_is_unaffected_by_the_census(qenv):
    """v1 and kernel-v03 are whole-document. Applying chunk completeness to them would mark
    the entire extracted corpus incomplete, because none of it has a census."""
    _extraction("doc-a", "epoch-new", "e1")
    assert not queue.chunk_unit_profile("prof_new")
    assert queue.project()["doc-a"]["extraction_state"] == "extracted"


def test_a_chunk_unit_extraction_with_no_census_is_not_called_incomplete(qenv):
    """Legacy chunked runs predate the census event. Absence of evidence must not become
    evidence of incompleteness — that would re-queue paid-for work."""
    _make_pin_chunk_unit(qenv)
    _extraction("doc-a", "epoch-new", "e1")
    assert queue.project()["doc-a"]["extraction_state"] == "extracted"


def test_coverage_is_scoped_to_the_pinned_profile(qenv):
    """Chunks ingested by another run must not count toward this profile's completeness."""
    _make_pin_chunk_unit(qenv)
    _extraction("doc-a", "epoch-new", "e1")
    queue.request("doc-a", 1, "test", "burn it", superseding=True)
    _census("doc-a", "prof_new", 2)
    _chunk("doc-a", "doc-a#c0001", "prof_new")
    _chunk("doc-a", "doc-a#c0002", "some_other_run")
    assert queue.project()["doc-a"]["extraction_state"] == "queued"
