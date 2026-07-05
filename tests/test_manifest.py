"""Tests for the corpus manifest gate (kg/manifest.py, DD-003).

Hermetic: both manifest and eventlog module paths are redirected into tmp_path so the real
corpus/, events/, and kg/schema.yaml are never touched. The event log is the source of
truth here too — assertions read the replayed state, not just the JSON projection.
"""
import json

import pytest

from kg import eventlog, manifest


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

    # event written to the log
    events = list(eventlog.replay())
    assert len(events) == 1
    ev = events[0]
    assert ev["event_type"] == "manifest_add"
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
    ids = sorted(e["payload"]["doc_id"] for e in eventlog.replay())
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
