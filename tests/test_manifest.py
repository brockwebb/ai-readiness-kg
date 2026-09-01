"""Tests for the corpus manifest gate (kg/manifest.py, DD-003).

Hermetic: both manifest and eventlog module paths are redirected into tmp_path so the real
corpus/, events/, and kg/schema.yaml are never touched. The event log is the source of
truth here too — assertions read the replayed state, not just the JSON projection.
"""
import json

import pytest

from kg import eventlog, manifest


@pytest.fixture(autouse=True)
def gate_does_not_mint_research_tasks(monkeypatch):
    """These tests admit tiny fixture files, and every one of them trips the DD-030 extent
    gate — correctly: 11 bytes IS thin. They are tests of admission VALIDATION, so they stub
    the gate's auto-task rather than assert on it; `tests/test_ingest_convert.py` owns the
    gate's own behaviour. Without the stub the global guard in conftest fails them loudly,
    which is what it is for."""
    from kg.ingest import gate
    monkeypatch.setattr(gate, "register_gap_task",
                        lambda doc_id, gap_class, detail: "task-stub")



@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway repo tree: corpus/, events/, and a minimal schema, all under tmp_path."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")

    # eventlog paths
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    # manifest paths
    monkeypatch.setattr(manifest, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(manifest, "_CORPUS_DIR", corpus)
    monkeypatch.setattr(manifest, "_MANIFEST_PATH", corpus / "manifest.json")
    return tmp_path


def _write_corpus_file(repo, name, content="hello world"):
    path = repo / "corpus" / name
    path.write_text(content, encoding="utf-8")
    return path


def _good_fields(**overrides):
    base = dict(
        doc_id="fcsm-25-03",
        title="A Framework for Data Quality",
        authors=["FCSM"],
        pub_date="2025",
        source_type="federal",
        primary_url="https://example.gov/fcsm-25-03",
        inclusion_rationale="Primary federal guidance on data quality dimensions.",
        discovered_via="manual",
    )
    base.update(overrides)
    return base


# --- happy path -----------------------------------------------------------------------

def test_acquisition_evidence_rides_in_event_when_supplied(repo):
    f = _write_corpus_file(repo, "doc.txt", "content")
    tevv = {"final_url": "https://x/y.pdf", "http_status": 200, "page_count": 12}
    manifest.add(str(f), **_good_fields(), acquisition=tevv)
    entry = list(eventlog.replay())[0]["payload"]
    assert entry["acquisition"] == tevv


def test_acquisition_absent_when_not_supplied(repo):
    f = _write_corpus_file(repo, "doc.txt", "content")
    manifest.add(str(f), **_good_fields())
    entry = list(eventlog.replay())[0]["payload"]
    assert "acquisition" not in entry


def test_add_writes_event_and_hashes(repo):
    """Stage-0 rewire (2026-07-05): add() writes the admission event but no longer
    auto-rebuilds manifest.json — the file is the Dixie evidence-ledger projection
    and refreshing it here would clobber v2 with unledgered state."""
    f = _write_corpus_file(repo, "fcsm.txt", "the content")
    doc_id = manifest.add(str(f), **_good_fields())
    assert doc_id == "fcsm-25-03"

    # event written to the log. An admission now emits the DD-030 convertibility verdict
    # alongside it, so this asserts the ADMISSION event rather than counting the log — the
    # count was never what the test was about.
    events = list(eventlog.replay())
    adds = [e for e in events if e["event_type"] == "manifest_add"]
    assert len(adds) == 1
    assert [e["event_type"] for e in events if e["event_type"] != "manifest_add"] \
        == ["conversion_gap"], "an 11-byte fixture is thin, and the gate says so"
    ev = adds[0]
    entry = ev["payload"]
    assert entry["doc_id"] == "fcsm-25-03"

    # hash is the real sha256 of the file, local_path is corpus-relative
    import hashlib
    expected_hash = hashlib.sha256(b"the content").hexdigest()
    assert entry["content_hash"] == expected_hash
    assert entry["local_path"] == "corpus/fcsm.txt"
    assert entry["status"] == "active"
    assert entry["discovered_via"] == "manual"

    # and the projection was NOT touched by add()
    assert not (repo / "corpus" / "manifest.json").exists()


def test_admission_state_replayed_not_projected(repo):
    manifest.add(str(_write_corpus_file(repo, "b.txt", "bbb")), **_good_fields(
        doc_id="zeta-01", primary_url="https://example.gov/z"))
    manifest.add(str(_write_corpus_file(repo, "a.txt", "aaa")), **_good_fields(
        doc_id="alpha-01", primary_url="https://example.gov/a"))
    ids = sorted(e["payload"]["doc_id"] for e in eventlog.replay()
                 if e["event_type"] == "manifest_add")
    assert ids == ["alpha-01", "zeta-01"]


# --- the five rejection paths ---------------------------------------------------------

def test_accepts_intergovernmental_source_type(repo):
    f = _write_corpus_file(repo, "oecd.txt", "oecd content")
    doc_id = manifest.add(str(f), **_good_fields(
        doc_id="oecd-ai-index", source_type="intergovernmental",
        primary_url="https://oecd.ai/en/"))
    assert doc_id == "oecd-ai-index"


def test_reject_missing_field(repo):
    f = _write_corpus_file(repo, "x.txt")
    fields = _good_fields()
    del fields["title"]
    with pytest.raises(manifest.ManifestError, match="missing required field"):
        manifest.add(str(f), **fields)
    assert list(eventlog.replay()) == []  # nothing written on rejection


def test_reject_file_not_under_corpus(repo):
    outside = repo / "elsewhere.txt"
    outside.write_text("nope", encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="not under corpus/"):
        manifest.add(str(outside), **_good_fields())
    assert list(eventlog.replay()) == []


def test_reject_duplicate_doc_id(repo):
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        primary_url="https://example.gov/one"))
    with pytest.raises(manifest.ManifestError, match="duplicate doc_id"):
        manifest.add(str(_write_corpus_file(repo, "two.txt", "two")), **_good_fields(
            primary_url="https://example.gov/two"))  # same doc_id, different url + content


def test_reject_duplicate_content_hash(repo):
    manifest.add(str(_write_corpus_file(repo, "one.txt", "identical")), **_good_fields(
        doc_id="doc-one", primary_url="https://example.gov/one"))
    with pytest.raises(manifest.ManifestError, match="duplicate content_hash"):
        manifest.add(str(_write_corpus_file(repo, "two.txt", "identical")), **_good_fields(
            doc_id="doc-two", primary_url="https://example.gov/two"))


def test_reject_duplicate_primary_url(repo):
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        doc_id="doc-one", primary_url="https://example.gov/shared"))
    # normalized-equal url (trailing slash + case in host) must still collide
    with pytest.raises(manifest.ManifestError, match="duplicate primary_url"):
        manifest.add(str(_write_corpus_file(repo, "two.txt", "two")), **_good_fields(
            doc_id="doc-two", primary_url="https://EXAMPLE.gov/shared/"))


# --- rebuild + verify -----------------------------------------------------------------
# Stage-0 rewire (2026-07-05): rebuild() projects from the Dixie evidence decisions
# log, not from manifest_add events. Tests seed a real dixie ledger in tmp_path.

def _seed_dixie(repo, monkeypatch):
    import yaml
    from dixie.evidence.eventlog import EventLog as DixieEventLog

    cfg_path = repo / "dixie_evidence.yaml"
    cfg_path.write_text(yaml.safe_dump({
        "project": "test", "corpus_root": "corpus",
        "evidence_dir": "corpus/evidence", "quarantine_dir": "corpus/quarantine",
        "inbox_dir": "corpus/inbox", "document_dirs": ["docs"],
    }))
    monkeypatch.setattr(manifest, "_DIXIE_CONFIG_PATH", cfg_path)
    log = DixieEventLog(repo / "corpus" / "evidence" / "decisions.jsonl")
    log.append("screening_decided", {
        "doc_id": "ledgered-doc", "decision": "included",
        "rationale": "seed", "decided_by": "test"})
    return log


def test_rebuild_projects_dixie_ledger_and_is_byte_stable(repo, monkeypatch):
    _seed_dixie(repo, monkeypatch)
    manifest_path = repo / "corpus" / "manifest.json"

    out = manifest.rebuild()
    assert out == {"manifest_version": 2, "entries": 1}
    first = manifest_path.read_text()
    doc = json.loads(first)
    assert doc["manifest_version"] == 2
    assert "ledgered-doc" in doc["entries"]
    assert doc["note"].startswith("PROJECTION")

    # byte-stable: rebuild twice on unchanged input -> identical bytes
    manifest.rebuild()
    assert manifest_path.read_text() == first


def test_rebuild_fails_loud_without_dixie_config(repo, monkeypatch):
    monkeypatch.setattr(manifest, "_DIXIE_CONFIG_PATH", repo / "nope.yaml")
    with pytest.raises(manifest.ManifestError, match="Dixie evidence ledger|dixie config"):
        manifest.rebuild()


def test_verify_clean_then_catches_tamper(repo):
    f = _write_corpus_file(repo, "doc.txt", "original")
    manifest.add(str(f), **_good_fields())
    assert manifest.verify() == []  # clean

    f.write_text("tampered", encoding="utf-8")
    problems = manifest.verify()
    assert len(problems) == 1
    assert problems[0]["issue"] == "hash_mismatch"
    assert problems[0]["doc_id"] == "fcsm-25-03"


def test_verify_catches_missing_file(repo):
    f = _write_corpus_file(repo, "doc.txt", "original")
    manifest.add(str(f), **_good_fields())
    f.unlink()
    problems = manifest.verify()
    assert len(problems) == 1
    assert problems[0]["issue"] == "missing"


def test_accepts_practitioner_source_type(repo):
    # schema v0.3 (DD-009): SME / industry-practitioner guidance that is not a product page.
    f = _write_corpus_file(repo, "sme.txt", "visibility diagnostic framework")
    doc_id = manifest.add(str(f), **_good_fields(
        doc_id="sme-visibility-diagnostic", source_type="practitioner",
        primary_url="https://example.org/visibility"))
    assert doc_id == "sme-visibility-diagnostic"


def test_source_types_in_sync_with_schema():
    from kg.extraction import schema_loader
    schema = schema_loader.load_schema()
    assert list(manifest._SOURCE_TYPES) == schema_loader.property_values(schema, "Document")["source_type"]


# --- v0.3.3 optional Document fields (task 2026-08-24_source_triage Phase 0) ----------

def test_construct_arm_and_grounding_surface_ride_in_event_when_supplied(repo):
    f = _write_corpus_file(repo, "doc.txt", "content")
    manifest.add(str(f), **_good_fields(), construct_arm="publication_actionability",
                 grounding_surface="slides")
    entry = list(eventlog.replay())[0]["payload"]
    assert entry["construct_arm"] == "publication_actionability"
    assert entry["grounding_surface"] == "slides"


def test_v033_fields_absent_when_not_supplied(repo):
    f = _write_corpus_file(repo, "doc.txt", "content")
    manifest.add(str(f), **_good_fields())
    entry = list(eventlog.replay())[0]["payload"]
    assert "construct_arm" not in entry
    assert "grounding_surface" not in entry


def test_reject_invalid_construct_arm(repo):
    f = _write_corpus_file(repo, "doc.txt", "content")
    with pytest.raises(manifest.ManifestError, match="construct_arm"):
        manifest.add(str(f), **_good_fields(), construct_arm="marketing")
    assert list(eventlog.replay()) == []


def test_reject_invalid_grounding_surface(repo):
    f = _write_corpus_file(repo, "doc.txt", "content")
    with pytest.raises(manifest.ManifestError, match="grounding_surface"):
        manifest.add(str(f), **_good_fields(), grounding_surface="hologram")
    assert list(eventlog.replay()) == []


def test_construct_arms_in_sync_with_schema():
    import yaml
    from pathlib import Path
    schema = yaml.safe_load(
        (Path(manifest.__file__).parent / "schema.yaml").read_text(encoding="utf-8"))
    vals = schema["node_types"]["Document"]["property_values"]
    assert tuple(vals["construct_arm"]) == manifest._CONSTRUCT_ARMS
    assert tuple(vals["grounding_surface"]) == manifest._GROUNDING_SURFACES


# --- content supersession (task 2026-08-29_corpus_t0_t1_substrate ADDENDUM-01 §-0.5) ----
# A document can be legitimately re-acquired after admission: wrong extent corrected, a
# corrupt PDF replaced. Four such corrections were made in July 2026 and recorded in the
# dixie evidence ledger with `superseded_sha256`, but never mirrored into the KG event log,
# so `verify()` reported four hash_mismatches that were not drift at all. The fix is a
# `content_update` event replayed over the admission entry — never an edit to the original
# `manifest_add`, which stays exactly as written (invariant 1).

def _admit(repo, name="doc.txt", content="original bytes", **over):
    f = _write_corpus_file(repo, name, content)
    manifest.add(str(f), **_good_fields(**over))
    return f


def test_content_update_supersedes_the_admission_hash(repo):
    """The re-acquired bytes become the entry's content_hash, so verify() is clean."""
    f = _admit(repo)
    old = list(eventlog.replay())[0]["payload"]["content_hash"]
    f.write_text("corrected bytes", encoding="utf-8")
    assert manifest.verify(), "precondition: the changed file must mismatch before the update"

    new = manifest.content_update(
        "fcsm-25-03", reason="extent_corrected",
        superseded_content_hash=old, evidence={"dixie_record": "note@447"})

    assert manifest.verify() == [], "content_update did not clear the mismatch"
    entry = {e["doc_id"]: e for e in manifest._load_entries()}["fcsm-25-03"]
    assert entry["content_hash"] == new != old
    # the admission event is untouched
    adds = [e for e in eventlog.replay() if e["event_type"] == "manifest_add"]
    assert len(adds) == 1 and adds[0]["payload"]["content_hash"] == old


def test_content_update_records_both_hashes_and_the_reason(repo):
    f = _admit(repo)
    old = list(eventlog.replay())[0]["payload"]["content_hash"]
    f.write_text("corrected bytes", encoding="utf-8")
    new = manifest.content_update("fcsm-25-03", reason="corrupt_source_replaced",
                                  superseded_content_hash=old,
                                  evidence={"dixie_record": "note@443"})
    ev = [e for e in eventlog.replay() if e["event_type"] == "content_update"][-1]
    p = ev["payload"]
    assert p["superseded_content_hash"] == old and p["content_hash"] == new
    assert p["reason"] == "corrupt_source_replaced"
    assert p["evidence"] == {"dixie_record": "note@443"}


def test_content_update_on_unknown_doc_is_loud(repo):
    _admit(repo)
    with pytest.raises(manifest.ManifestError, match="not admitted"):
        manifest.content_update("never-admitted", reason="extent_corrected",
                                superseded_content_hash="0" * 64, evidence={})


def test_content_update_refuses_a_stale_superseded_hash(repo):
    """Blind chaining is how a supersession event silently adopts whatever is on disk. The
    caller must name the hash it believes it is replacing, and be right."""
    f = _admit(repo)
    f.write_text("corrected bytes", encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="superseded_content_hash"):
        manifest.content_update("fcsm-25-03", reason="extent_corrected",
                                superseded_content_hash="f" * 64, evidence={})


def test_content_update_requires_a_known_reason(repo):
    f = _admit(repo)
    old = list(eventlog.replay())[0]["payload"]["content_hash"]
    f.write_text("corrected bytes", encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="reason"):
        manifest.content_update("fcsm-25-03", reason="because_i_said_so",
                                superseded_content_hash=old, evidence={})


def test_superseded_hash_does_not_block_a_later_admission(repo):
    """The dedup gate keys on the CURRENT hash set. A superseded hash is retired: another
    document may legitimately arrive carrying the bytes this one used to have (the
    quarantined original, re-admitted under its own doc_id)."""
    f = _admit(repo)
    old = list(eventlog.replay())[0]["payload"]["content_hash"]
    f.write_text("corrected bytes", encoding="utf-8")
    manifest.content_update("fcsm-25-03", reason="extent_corrected",
                            superseded_content_hash=old, evidence={})
    other = _write_corpus_file(repo, "other.txt", "original bytes")   # the retired hash
    manifest.add(str(other), **_good_fields(doc_id="fcsm-25-03-megastatute",
                                            primary_url="https://example.gov/old"))
    assert {e["doc_id"] for e in manifest._load_entries()} == {"fcsm-25-03",
                                                               "fcsm-25-03-megastatute"}


# --- duplicate manifest_add: the log-level invariant add() cannot express -----------------
# ResearchTask 95f286e4. The report was "195 raw manifest_add events, 194 distinct doc_ids;
# kg.manifest is supposed to reject duplicate adds and one got through." It did not get
# through: `add()` refused duplicate doc_ids then and refuses them now. The 2026-08-14 event
# for `introducing-the-oecd-ai-capability-indicators` was written straight to shard 005,
# bypassing add(), because it was an operator-cleared EXTENT CORRECTION (CLEARANCE 2,
# cc_tasks/2026-08-14_bulk_v1_closeout.md) and `content_update` did not exist until
# 2026-08-29 — fifteen days later. The guard that was missing is at the LOG level, not the
# call level, and that is what these tests pin.

def test_mutation_the_doc_id_check_is_what_rejects_a_duplicate_doc_id(repo, monkeypatch):
    """Positive control on `test_reject_duplicate_doc_id`.

    That test uses a different file and a different URL, so the content_hash and primary_url
    checks cannot fire — but nothing in it PROVES that. Neuter the doc_id comparison and the
    add must succeed; if it still raises, the test above is measuring a different guard, which
    is this repo's recurring M2 failure mode."""
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        primary_url="https://example.gov/one"))

    real = manifest._load_entries
    monkeypatch.setattr(manifest, "_load_entries",
                        lambda: [{**e, "doc_id": "something-else"} for e in real()])
    manifest.add(str(_write_corpus_file(repo, "two.txt", "two")), **_good_fields(
        primary_url="https://example.gov/two"))
    assert len(manifest.duplicate_adds()) == 1, (
        "with the doc_id check blinded the duplicate must land, proving the check is the "
        "thing that rejects it")


def test_duplicate_adds_finds_a_bypassed_duplicate_and_calls_it_unexplained(repo):
    """An event written around add() — the actual mechanism — with no supersession claim."""
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        primary_url="https://example.gov/one"))
    assert manifest.duplicate_adds() == {}

    eventlog.append({"event_type": "manifest_add", "payload": {
        **_good_fields(primary_url="https://example.gov/two"),
        "local_path": "corpus/two.txt", "content_hash": "b" * 64, "status": "active"}},
        batch=manifest._MANIFEST_BATCH)
    dup = manifest.duplicate_adds()
    assert list(dup) == ["fcsm-25-03"] and dup["fcsm-25-03"]["n_adds"] == 2
    assert dup["fcsm-25-03"]["explained"] is False, (
        "a bypassed add that claims no supersession is a corrupt log, not a correction")


def test_duplicate_adds_recognises_a_declared_supersession(repo):
    """The historical event's shape: the later add names the hash it replaces."""
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        primary_url="https://example.gov/one"))
    first = manifest._load_entries()[0]["content_hash"]
    eventlog.append({"event_type": "manifest_add", "payload": {
        **_good_fields(primary_url="https://example.gov/two"),
        "local_path": "corpus/two.pdf", "content_hash": "c" * 64, "status": "active",
        "inclusion_rationale": "Full report. Supersedes the partial component capture.",
        "acquisition": {"verification": {"sha256": "c" * 64,
                                         "supersedes_sha256": first}}}},
        batch=manifest._MANIFEST_BATCH)
    dup = manifest.duplicate_adds()["fcsm-25-03"]
    assert dup["explained"] is True
    assert dup["supersedes_sha256"] == first
    assert dup["effective_entry"] == "corpus/two.pdf", (
        "shard order decides which entry is effective; the later add must win")


def test_the_later_add_is_the_effective_entry(repo):
    """Why the corpus is not damaged by the historical duplicate: replay takes the later
    event, so the entry in force is the corrected one."""
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        primary_url="https://example.gov/one"))
    eventlog.append({"event_type": "manifest_add", "payload": {
        **_good_fields(primary_url="https://example.gov/two"),
        "local_path": "corpus/two.pdf", "content_hash": "d" * 64, "status": "active"}},
        batch=manifest._MANIFEST_BATCH)
    entries = {e["doc_id"]: e for e in manifest._load_entries()}
    assert entries["fcsm-25-03"]["content_hash"] == "d" * 64


# --- regression monitor against the REAL log ---------------------------------------------
#: The one duplicate the log is allowed to carry, pinned by event id. It is historical and
#: explained; a NEW one is a defect, because `content_update(reason="extent_corrected")` has
#: existed since 2026-08-29 and is how this correction is expressed now.
_KNOWN_DUPLICATE = {
    "introducing-the-oecd-ai-capability-indicators": (
        "712a7c38694848b2a372ea72fd331190", "d2ad0f8ce2d94312a2d95e0ee3b0ae8b"),
}


def test_live_log_carries_only_the_known_explained_duplicate():
    """Runs against the real event log, not a fixture. A second duplicate — or this one
    losing its supersession claim — fails here."""
    import kg.manifest as real_manifest
    dup = real_manifest.duplicate_adds()
    assert set(dup) == set(_KNOWN_DUPLICATE), (
        f"unexpected duplicate manifest_add doc_ids: "
        f"{sorted(set(dup) - set(_KNOWN_DUPLICATE))}; use "
        f"content_update(reason='extent_corrected') for a re-acquisition")
    for doc_id, event_ids in _KNOWN_DUPLICATE.items():
        row = dup[doc_id]
        assert tuple(row["event_ids"]) == event_ids
        assert row["explained"] is True
        assert row["supersedes_sha256"] == row["content_hashes"][0], (
            "the supersession claim must name the hash it actually replaces; if these stop "
            "matching, the two events are not the pair this allowlist vouches for")
