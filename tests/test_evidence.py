"""Evidence capture: the raw artifact behind every score is written to disk so a
reviewer can confirm the score without re-running the harness."""
from harness.evidence import EvidenceStore


def test_writes_evidence_and_returns_readable_path(tmp_path):
    store = EvidenceStore(root=tmp_path)
    path = store.write(
        agency_id="census",
        probe_id="d1_robots",
        target="https://www.census.gov/robots.txt",
        content="User-agent: *\nAllow: /\n",
    )
    p = tmp_path / path if not str(path).startswith(str(tmp_path)) else __import__("pathlib").Path(path)
    written = __import__("pathlib").Path(path)
    assert written.exists()
    assert written.read_text() == "User-agent: *\nAllow: /\n"
    # Organized by agency so a reviewer can browse one agency's evidence bundle.
    assert "census" in str(written)
    assert "d1_robots" in str(written)


def test_target_url_is_made_filesystem_safe(tmp_path):
    store = EvidenceStore(root=tmp_path)
    path = store.write(
        agency_id="bls",
        probe_id="d2_content_negotiation",
        target="https://api.bls.gov/data?series=CES&format=json",
        content="{}",
    )
    written = __import__("pathlib").Path(path)
    assert written.exists()
    # No raw '/', '?', '&', ':' leaking into the filename.
    name = written.name
    for bad in ("/", "?", "&", ":"):
        assert bad not in name


def test_evidence_is_truncated_with_a_marker(tmp_path):
    store = EvidenceStore(root=tmp_path, max_bytes=50)
    path = store.write("census", "d1_catalog", "https://census.gov/data.json",
                       "X" * 500)
    written = __import__("pathlib").Path(path).read_text()
    assert len(written) < 500
    assert "truncated" in written.lower()


def test_distinct_targets_do_not_collide(tmp_path):
    store = EvidenceStore(root=tmp_path)
    p1 = store.write("census", "d1_stable_urls", "https://census.gov/a", "A")
    p2 = store.write("census", "d1_stable_urls", "https://census.gov/b", "B")
    assert p1 != p2
    assert __import__("pathlib").Path(p1).read_text() == "A"
    assert __import__("pathlib").Path(p2).read_text() == "B"
