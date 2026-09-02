"""The pure parts of the fetch layer: header normalization and body decoding that
turn a raw HTTP response into the Fetched artifact probes evaluate."""
from harness.fetch import build_fetched, Fetched


def test_header_keys_are_lowercased_for_stable_lookup():
    f = build_fetched(
        requested_url="https://x.gov/a",
        final_url="https://x.gov/a",
        status=200,
        raw_headers=[("Content-Type", "application/json"), ("X-Foo", "Bar")],
        raw_bytes=b"{}",
    )
    assert f.headers["content-type"] == "application/json"
    assert f.headers["x-foo"] == "Bar"
    assert f.content_type == "application/json"


def test_body_decoded_as_text():
    f = build_fetched(
        requested_url="https://x.gov/a",
        final_url="https://x.gov/a",
        status=200,
        raw_headers=[("Content-Type", "text/plain; charset=utf-8")],
        raw_bytes="café".encode("utf-8"),
    )
    assert f.body == "café"
    assert f.ok is True


def test_redirect_recorded_via_final_url():
    f = build_fetched(
        requested_url="https://x.gov/data",
        final_url="https://x.gov/data/",
        status=200,
        raw_headers=[],
        raw_bytes=b"",
    )
    assert f.requested_url == "https://x.gov/data"
    assert f.final_url == "https://x.gov/data/"
    assert f.was_redirected is True


def test_body_cap_is_configurable_so_large_catalogs_still_parse():
    # Regression: a ~2MB DCAT catalog was truncated mid-JSON by a too-small fixed
    # cap and misread as "no machine-readable catalog". The cap must be tunable and
    # large enough that real federal catalogs are retained whole.
    big = b'{"dataset":[' + b'{"x":1},' * 300_000 + b'{"x":1}]}'
    assert len(big) > 2_000_000
    f = build_fetched(
        requested_url="https://x.gov/data.json",
        final_url="https://x.gov/data.json",
        status=200,
        raw_headers=[("Content-Type", "application/json")],
        raw_bytes=big,
        max_body_bytes=50_000_000,
    )
    import json
    assert len(f.body) == len(big)  # nothing truncated
    assert isinstance(json.loads(f.body), dict)  # parses cleanly


def test_body_cap_truncates_beyond_limit():
    f = build_fetched(
        requested_url="https://x.gov/a",
        final_url="https://x.gov/a",
        status=200,
        raw_headers=[],
        raw_bytes=b"x" * 100,
        max_body_bytes=10,
    )
    assert len(f.body) == 10


def test_error_artifact_is_not_ok():
    f = Fetched(
        requested_url="https://x.gov/a",
        final_url="https://x.gov/a",
        status=None,
        headers={},
        body="",
        error="timed out",
    )
    assert f.ok is False
    assert f.error == "timed out"


def test_gzipped_body_is_decompressed_and_the_transformation_is_visible():
    """Sitemaps are commonly served gzipped. A gzipped body decoded as text is
    unusable to every probe, so it is decompressed, and the evidence file says
    so, because a silent transformation of the artifact behind a score is not
    auditable (§4)."""
    import gzip
    raw = gzip.compress(b'<urlset><url><loc>https://x.gov/a</loc></url></urlset>')
    f = build_fetched("https://x.gov/sitemap.xml.gz", "https://x.gov/sitemap.xml.gz",
                      200, [("Content-Type", "application/xml")], raw)
    assert f.decompressed is True
    assert "<loc>https://x.gov/a</loc>" in f.body
    assert "DECOMPRESSED: True" in f.evidence_text()


def test_plain_body_is_untouched_and_not_marked_decompressed():
    f = build_fetched("https://x.gov/a.csv", "https://x.gov/a.csv", 200,
                      [("Content-Type", "text/csv")], b"a,b\n1,2\n")
    assert f.decompressed is False
    assert f.body == "a,b\n1,2\n"


def test_undecompressible_gzip_body_records_an_error_rather_than_garbage():
    f = build_fetched("https://x.gov/a.gz", "https://x.gov/a.gz", 200,
                      [("Content-Encoding", "gzip")], b"\x1f\x8b\x08not-really-gzip")
    assert f.error and "decompress" in f.error
