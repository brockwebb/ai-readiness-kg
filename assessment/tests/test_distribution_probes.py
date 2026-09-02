"""D1-stable + D2 probes that fetch one distribution endpoint and score the live
response (plus the distribution metadata)."""
from harness.records import Score, Track
from harness.probes.d1_stable_urls import StableUrlProbe
from harness.probes.d2_programmatic import ProgrammaticAccessProbe
from harness.probes.d2_content_negotiation import ContentNegotiationProbe
from harness.probes.d2_bulk import BulkAvailabilityProbe
from harness.probes.d2_no_barriers import NoBarriersProbe

from tests.helpers import fetched

CSV_DIST = {"mediaType": "text/csv", "downloadURL": "https://x.gov/a.csv"}
HTML_DIST = {"mediaType": "text/html", "accessURL": "https://x.gov/a.html"}
SERVICE_DIST = {"mediaType": "application/json", "accessURL": "https://api.x.gov/a"}


# --- D1 stable, semantic URLs ----------------------------------------------
def test_stable_url_pass_when_resolves_directly():
    f = fetched("https://x.gov/a.csv", status=200,
                headers={"Content-Type": "text/csv"}, body="a,b\n1,2\n")
    assert StableUrlProbe().evaluate(f, CSV_DIST)[0] == Score.PASS


def test_stable_url_fail_when_not_resolvable():
    f = fetched("https://x.gov/a.csv", status=404, body="")
    assert StableUrlProbe().evaluate(f, CSV_DIST)[0] == Score.FAIL


def test_stable_url_partial_when_redirected_to_session_like_url():
    f = fetched("https://x.gov/a.csv", status=200, body="x")
    f.final_url = "https://x.gov/a.csv;jsessionid=ABC123"
    assert StableUrlProbe().evaluate(f, CSV_DIST)[0] == Score.PARTIAL


def test_stable_url_is_core_d1():
    assert StableUrlProbe().dimension == "D1"
    assert StableUrlProbe().track is Track.CORE


# --- D2 programmatic access -------------------------------------------------
def test_programmatic_pass_when_plain_get_returns_data():
    f = fetched("https://x.gov/a.csv", status=200,
                headers={"Content-Type": "text/csv"}, body="a,b\n1,2\n")
    assert ProgrammaticAccessProbe().evaluate(f, CSV_DIST)[0] == Score.PASS


def test_programmatic_fail_when_login_walled():
    f = fetched("https://x.gov/a", status=200, body="Please sign in to continue")
    f.final_url = "https://x.gov/login"
    assert ProgrammaticAccessProbe().evaluate(f, HTML_DIST)[0] == Score.FAIL


def test_programmatic_fail_when_unreachable():
    f = fetched("https://x.gov/a", status=None, body="", error="timed out")
    assert ProgrammaticAccessProbe().evaluate(f, CSV_DIST)[0] == Score.FAIL


# --- D2 content negotiation -------------------------------------------------
def test_content_negotiation_pass_with_machine_format():
    f = fetched("https://x.gov/a.csv", status=200,
                headers={"Content-Type": "text/csv"}, body="a,b\n")
    assert ContentNegotiationProbe().evaluate(f, CSV_DIST)[0] == Score.PASS


def test_content_negotiation_partial_when_only_html():
    f = fetched("https://x.gov/a.html", status=200,
                headers={"Content-Type": "text/html"}, body="<html></html>")
    assert ContentNegotiationProbe().evaluate(f, HTML_DIST)[0] == Score.PARTIAL


def test_content_negotiation_fail_when_unreachable():
    f = fetched("https://x.gov/a", status=None, body="", error="dns")
    assert ContentNegotiationProbe().evaluate(f, CSV_DIST)[0] == Score.FAIL


# --- D2 bulk availability ---------------------------------------------------
def test_bulk_pass_with_direct_download_url():
    f = fetched("https://x.gov/a.csv", status=200, body="a,b\n")
    assert BulkAvailabilityProbe().evaluate(f, CSV_DIST)[0] == Score.PASS


def test_bulk_partial_with_only_service_access_url():
    f = fetched("https://api.x.gov/a", status=200, body="{}")
    assert BulkAvailabilityProbe().evaluate(f, SERVICE_DIST)[0] == Score.PARTIAL


# --- D2 no anti-machine barriers --------------------------------------------
def test_no_barriers_pass_when_clean():
    f = fetched("https://x.gov/a.csv", status=200,
                headers={"Content-Type": "text/csv"}, body="a,b\n1,2\n")
    assert NoBarriersProbe().evaluate(f, CSV_DIST)[0] == Score.PASS


def test_no_barriers_fail_on_captcha():
    f = fetched("https://x.gov/a", status=200,
                body="<div class='g-recaptcha'></div> please verify you are human")
    assert NoBarriersProbe().evaluate(f, HTML_DIST)[0] == Score.FAIL


def test_no_barriers_fail_on_auth_status():
    f = fetched("https://x.gov/a", status=403, body="Forbidden")
    assert NoBarriersProbe().evaluate(f, HTML_DIST)[0] == Score.FAIL
