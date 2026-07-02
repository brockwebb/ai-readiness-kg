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

def test_add_writes_event_updates_manifest_and_hashes(repo):
    f = _write_corpus_file(repo, "fcsm.txt", "the content")
    doc_id = manifest.add(str(f), **_good_fields())
    assert doc_id == "fcsm-25-03"

    # event written to the log
    events = list(eventlog.replay())
    assert len(events) == 1
    ev = events[0]
    assert ev["event_type"] == "manifest_add"
    assert ev["payload"]["doc_id"] == "fcsm-25-03"

    # manifest.json projection updated
    manifest_json = json.loads((repo / "corpus" / "manifest.json").read_text())
    assert manifest_json["schema_version"] == "0.1"
    assert len(manifest_json["documents"]) == 1
    entry = manifest_json["documents"][0]

    # hash is the real sha256 of the file, local_path is corpus-relative
    import hashlib
    expected_hash = hashlib.sha256(b"the content").hexdigest()
    assert entry["content_hash"] == expected_hash
    assert entry["local_path"] == "corpus/fcsm.txt"
    assert entry["status"] == "active"
    assert entry["discovered_via"] == "manual"


def test_manifest_sorted_by_doc_id(repo):
    manifest.add(str(_write_corpus_file(repo, "b.txt", "bbb")), **_good_fields(
        doc_id="zeta-01", primary_url="https://example.gov/z"))
    manifest.add(str(_write_corpus_file(repo, "a.txt", "aaa")), **_good_fields(
        doc_id="alpha-01", primary_url="https://example.gov/a"))
    docs = json.loads((repo / "corpus" / "manifest.json").read_text())["documents"]
    assert [d["doc_id"] for d in docs] == ["alpha-01", "zeta-01"]


# --- the five rejection paths ---------------------------------------------------------

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

def test_rebuild_is_idempotent_and_pure_from_events(repo):
    manifest.add(str(_write_corpus_file(repo, "one.txt", "one")), **_good_fields(
        doc_id="doc-one", primary_url="https://example.gov/one"))
    manifest.add(str(_write_corpus_file(repo, "two.txt", "two")), **_good_fields(
        doc_id="doc-two", primary_url="https://example.gov/two"))

    manifest_path = repo / "corpus" / "manifest.json"
    first = manifest_path.read_text()

    # delete the projection, rebuild purely from the event log -> byte-identical
    manifest_path.unlink()
    manifest.rebuild()
    assert manifest_path.read_text() == first

    # a second rebuild changes nothing
    manifest.rebuild()
    assert manifest_path.read_text() == first


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
