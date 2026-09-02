"""d2_no_barriers scored over n fetches instead of one.

The case this exists for: an edge that refuses automated clients some of the time.
A single fetch returns either a refusal or a page and cannot tell "always refuses"
from "refuses four times in five", so its verdict on such a surface is a coin
flip. Measured live on census.gov QuickFacts, 2026-09-02: 4 refusals in 5 probes
of one page, at the harness politeness delay.
"""
from harness.probes.d2_no_barriers import NoBarriersProbe
from harness.probes.d1_stable_urls import StableUrlProbe
from harness.probes.d2_bulk import BulkAvailabilityProbe
from harness.probes.d2_programmatic import ProgrammaticAccessProbe
from harness.probes.d2_content_negotiation import ContentNegotiationProbe
from harness.records import SOURCE_CATALOG, SOURCE_SITEMAP, Score

from tests.helpers import fetched

URL = "https://x.gov/quickfacts/fact/table/US/PST045217"
DIST = {"mediaType": "text/html", "accessURL": URL}

OK = lambda: fetched(URL, status=200, headers={"Content-Type": "text/html"},
                     body="<html><body>QuickFacts table</body></html>")
REFUSED = lambda: fetched(URL, status=403, body="Forbidden")


def test_all_attempts_clean_passes_and_reports_a_zero_refusal_fraction():
    score, evidence, _ = NoBarriersProbe().evaluate_attempts([OK(), OK(), OK()], DIST)
    assert score == Score.PASS
    assert "refusal_fraction=0.00" in evidence
    assert "attempts=3" in evidence


def test_one_refusal_in_three_fails_and_carries_the_fraction():
    """The load-bearing case: two of three attempts succeeded and the verdict is
    still FAIL, because a machine that must retry is being gated."""
    score, evidence, _ = NoBarriersProbe().evaluate_attempts([OK(), REFUSED(), OK()], DIST)
    assert score == Score.FAIL
    assert "refused on 1/3 attempts" in evidence
    assert "refusal_fraction=0.33" in evidence
    assert "HTTP 403" in evidence


def test_every_attempt_refused_is_also_fail_but_distinguishable_in_evidence():
    always = NoBarriersProbe().evaluate_attempts([REFUSED(), REFUSED(), REFUSED()], DIST)[:2]
    sometimes = NoBarriersProbe().evaluate_attempts([OK(), OK(), REFUSED()], DIST)[:2]
    assert always[0] == sometimes[0] == Score.FAIL
    # Same score, different evidence: the reviewer can tell always from sometimes.
    assert "3/3" in always[1] and "refusal_fraction=1.00" in always[1]
    assert "1/3" in sometimes[1] and "refusal_fraction=0.33" in sometimes[1]


def test_per_attempt_statuses_are_recorded_in_order():
    score, evidence, _ = NoBarriersProbe().evaluate_attempts(
        [REFUSED(), OK(), REFUSED(), REFUSED(), REFUSED()], DIST)
    assert score == Score.FAIL
    assert "statuses=[403, 200, 403, 403, 403]" in evidence
    assert "refused on 4/5 attempts" in evidence


def test_captcha_body_counts_as_a_refusal_even_at_status_200():
    captcha = fetched(URL, status=200, body="<div class='g-recaptcha'></div>")
    score, evidence, _ = NoBarriersProbe().evaluate_attempts([OK(), captcha], DIST)
    assert score == Score.FAIL
    assert "barrier markers in body" in evidence


def test_transport_failure_across_attempts_fails_separately_from_refusal():
    down = fetched(URL, status=None, body="", error="TimeoutError: timed out")
    score, evidence, _ = NoBarriersProbe().evaluate_attempts([down, down], DIST)
    assert score == Score.FAIL
    assert "not retrievable on 2/2 attempts" in evidence
    assert "timed out" in evidence


def test_a_single_attempt_scores_the_same_way_as_before():
    """Backward compatibility: one fetch through the old entry point is one
    attempt, and a lone refusal is still a refusal."""
    assert NoBarriersProbe().evaluate(REFUSED(), DIST)[0] == Score.FAIL
    assert NoBarriersProbe().evaluate(OK(), DIST)[0] == Score.PASS


def test_no_attempts_is_reported_not_crashed():
    score, evidence, _ = NoBarriersProbe().evaluate_attempts([], DIST)
    assert score == Score.FAIL
    assert "no fetch attempts" in evidence


# --- which probes may be pointed at which surface ---------------------------
def test_distribution_only_probes_are_not_applied_to_web_pages():
    """Bulk availability and programmatic access are questions about a catalog
    distribution. Asking them of a product page manufactures a score out of a
    category error, so the probe declares it does not apply."""
    for probe in (BulkAvailabilityProbe(), ProgrammaticAccessProbe()):
        assert probe.applies_to(SOURCE_CATALOG)
        assert not probe.applies_to(SOURCE_SITEMAP)


def test_surface_agnostic_probes_declare_both_sources():
    for probe in (NoBarriersProbe(), StableUrlProbe(), ContentNegotiationProbe()):
        assert probe.applies_to(SOURCE_CATALOG)
        assert probe.applies_to(SOURCE_SITEMAP)


def test_only_the_barrier_probe_is_multi_attempt():
    assert NoBarriersProbe().multi_attempt is True
    for probe in (StableUrlProbe(), ContentNegotiationProbe(),
                  BulkAvailabilityProbe(), ProgrammaticAccessProbe()):
        assert probe.multi_attempt is False
