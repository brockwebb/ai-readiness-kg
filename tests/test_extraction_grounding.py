"""Grounding validator: exact, whitespace variance, hyphenation break, OCR ligature, miss."""
from kg.extraction import grounding


SOURCE = (
    "AI readiness is a multidimensional construct describing preparedness.\n"
    "The framework emphasizes data quality and discover-\nability of records.\n"
    "Institutions rely on efﬁcient workﬂows."  # note: ligatures ﬁ (U+FB01), ﬂ (U+FB02)
)


def test_exact_match():
    assert grounding.is_grounded("AI readiness is a multidimensional construct", SOURCE)


def test_whitespace_variance():
    # span uses single spaces where the source has a newline / different spacing
    assert grounding.is_grounded("describing preparedness. The framework emphasizes", SOURCE)


def test_hyphenation_break():
    # "discover-\nability" in the source must match "discoverability" in the span
    assert grounding.is_grounded("discoverability of records", SOURCE)


def test_ocr_ligature():
    # source has ﬁ/ﬂ ligature codepoints; span uses plain ASCII fi/fl
    assert grounding.is_grounded("efficient workflows", SOURCE)


def test_genuine_miss_not_grounded():
    assert not grounding.is_grounded("blockchain enables trustless consensus", SOURCE)


def test_empty_span_not_grounded():
    assert not grounding.is_grounded("", SOURCE)
    assert not grounding.is_grounded("   \n ", SOURCE)


def test_normalize_is_idempotent():
    once = grounding.normalize(SOURCE)
    assert grounding.normalize(once) == once
