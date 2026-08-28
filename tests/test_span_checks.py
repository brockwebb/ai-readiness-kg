"""Mid-noun-phrase truncation check (probe-protocol change v1.0.0, task 2026-08-27_chunked_pilot §5)."""
from kg.extraction import span_checks

DOC = ("The instrument is used to evaluate the completeness, timeliness, accuracy, and "
       "consistency of the state-reported commercial insurance data submitted each year.")


def test_a_span_cut_before_its_head_noun_is_flagged():
    span = ("evaluate the completeness, timeliness, accuracy, and consistency of the "
            "state-reported commercial")
    assert span_checks.is_mid_noun_phrase(span, DOC) is True


def test_a_span_that_ends_on_its_head_noun_is_not_flagged():
    span = ("evaluate the completeness, timeliness, accuracy, and consistency of the "
            "state-reported commercial insurance data")
    assert span_checks.is_mid_noun_phrase(span, DOC) is False


def test_a_span_ending_the_sentence_is_not_flagged():
    assert span_checks.is_mid_noun_phrase(DOC, DOC) is False


def test_a_span_that_does_not_locate_is_not_flagged_here():
    # A grounding miss is a different, louder failure; this check stays silent about it.
    assert span_checks.is_mid_noun_phrase("nowhere in the document at all", DOC) is False


def test_whitespace_and_hyphenation_are_normalized_like_grounding():
    wrapped = DOC.replace("state-reported", "state-repor-\nted")
    span = ("evaluate the completeness, timeliness, accuracy, and consistency of the\n  "
            "state-reported commercial")
    assert span_checks.is_mid_noun_phrase(span, wrapped) is True


def test_empty_inputs_are_not_flagged():
    assert span_checks.is_mid_noun_phrase("", DOC) is False
    assert span_checks.is_mid_noun_phrase("something", "") is False


def test_check_records_the_version():
    out = span_checks.check("evaluate the completeness", DOC)
    assert out["span_check_version"] == span_checks.CHECK_VERSION
    assert set(out) == {"span_mid_phrase", "span_check_version"}
