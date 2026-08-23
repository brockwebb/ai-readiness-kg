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


# --- span-coverage invariant (task 2026-08-22_faithfulness_probe, Phase 7) ----------------
from kg.extraction.grounding import covers, partial_span_reason  # noqa: E402


def test_covers_requires_item_text_inside_span():
    assert covers("Data must be published in a machine-readable format.", "published in a machine-readable format")
    assert not covers("published in a machine-", "published in a machine-readable format")   # truncated
    assert not covers("", "x") and not covers("x", "")


def test_partial_span_reason_mutation_positive_control():
    # seeded known-partial span: the Claim's text runs past the span
    bad = {"claim_text": "Is the methodology internally consistent with other CPI methodologies",
           "grounding_span": "Is the methodology internally"}
    assert partial_span_reason(bad) == "span_partial: grounding_span does not cover 'claim_text'"
    good = {"claim_text": "Is the methodology internally consistent",
            "grounding_span": "Q3. Is the methodology internally consistent?"}
    assert partial_span_reason(good) is None
    assert partial_span_reason({"grounding_span": "anything", "description": "not a covered attr"}) is None
