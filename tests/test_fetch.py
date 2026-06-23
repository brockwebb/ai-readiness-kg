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
