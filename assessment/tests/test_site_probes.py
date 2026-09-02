"""Scoring logic for the site-level probes (run once per agency base_url)."""
from harness.records import Score, Track
from harness.probes.d1_robots import RobotsProbe
from harness.probes.d1_sitemap import SitemapProbe
from harness.probes.d1_catalog import CatalogProbe
from harness.probes.frontier_llms_txt import LlmsTxtProbe
from harness.probes.frontier_mcp import McpProbe

from tests.helpers import fetched

# The staleness threshold is config; tests build the probe the way main() does.
STALE_DAYS = 365


# --- D1 robots.txt ---------------------------------------------------------
def test_robots_pass_when_permits_and_declares_sitemap():
    f = fetched("https://x.gov/robots.txt", body=(
        "User-agent: *\nAllow: /\nSitemap: https://x.gov/sitemap.xml\n"))
    score, ev = RobotsProbe().evaluate(f)
    assert score == Score.PASS
    assert "sitemap" in ev.lower()


def test_robots_partial_when_permits_but_no_sitemap():
    f = fetched("https://x.gov/robots.txt", body="User-agent: *\nAllow: /\n")
    score, _ = RobotsProbe().evaluate(f)
    assert score == Score.PARTIAL


def test_robots_fail_when_blanket_blocks_all_agents():
    f = fetched("https://x.gov/robots.txt", body="User-agent: *\nDisallow: /\n")
    score, ev = RobotsProbe().evaluate(f)
    assert score == Score.FAIL
    assert "block" in ev.lower()


def test_robots_fail_when_absent():
    f = fetched("https://x.gov/robots.txt", status=404, body="Not Found")
    assert RobotsProbe().evaluate(f)[0] == Score.FAIL


def test_robots_is_core_d1():
    assert RobotsProbe().track is Track.CORE
    assert RobotsProbe().dimension == "D1"


# --- D1 sitemap.xml --------------------------------------------------------
def test_sitemap_pass_when_parses_with_urls():
    body = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://x.gov/a</loc></url></urlset>')
    f = fetched("https://x.gov/sitemap.xml", body=body)
    assert SitemapProbe(STALE_DAYS).evaluate(f)[0] == Score.PASS


def test_sitemap_partial_when_present_but_unparseable():
    f = fetched("https://x.gov/sitemap.xml", body="not xml at all")
    assert SitemapProbe(STALE_DAYS).evaluate(f)[0] == Score.PARTIAL


def test_sitemap_fail_when_absent():
    f = fetched("https://x.gov/sitemap.xml", status=404, body="")
    assert SitemapProbe(STALE_DAYS).evaluate(f)[0] == Score.FAIL


# --- D1 structured catalog (data.json) -------------------------------------
def test_catalog_pass_with_dataset_array():
    f = fetched("https://x.gov/data.json", body='{"dataset":[{"title":"A"}]}',
                headers={"Content-Type": "application/json"})
    assert CatalogProbe().evaluate(f)[0] == Score.PASS


def test_catalog_partial_when_json_but_wrong_shape():
    f = fetched("https://x.gov/data.json", body='{"foo":"bar"}')
    assert CatalogProbe().evaluate(f)[0] == Score.PARTIAL


def test_catalog_fail_when_missing_or_not_json():
    f = fetched("https://x.gov/data.json", status=404, body="<html>nope</html>")
    assert CatalogProbe().evaluate(f)[0] == Score.FAIL


# --- frontier_near: llms.txt -----------------------------------------------
def test_llms_txt_pass_when_present_and_structured():
    body = "# Example Agency\n\n> Public data.\n\n## Datasets\n- [Pop](https://x.gov/pop)\n"
    f = fetched("https://x.gov/llms.txt", body=body)
    p = LlmsTxtProbe()
    assert p.evaluate(f)[0] == Score.PASS
    assert p.track is Track.FRONTIER_NEAR
    assert p.track.as_of_date == "2024-09"
    assert p.dimension is None  # frontier probes are off the core dimensions


def test_llms_txt_partial_when_present_but_trivial():
    f = fetched("https://x.gov/llms.txt", body="   \n")
    assert LlmsTxtProbe().evaluate(f)[0] == Score.PARTIAL


def test_llms_txt_fail_when_absent():
    f = fetched("https://x.gov/llms.txt", status=404, body="")
    assert LlmsTxtProbe().evaluate(f)[0] == Score.FAIL


# --- frontier_deep: MCP / WebMCP -------------------------------------------
def test_mcp_pass_with_valid_tool_schema():
    body = '{"tools":[{"name":"query","description":"q"}]}'
    f = fetched("https://x.gov/.well-known/mcp.json", body=body,
                headers={"Content-Type": "application/json"})
    p = McpProbe()
    assert p.evaluate(f)[0] == Score.PASS
    assert p.track is Track.FRONTIER_DEEP
    assert p.track.as_of_date == "2026-01"


def test_mcp_partial_when_json_but_no_tools_or_resources():
    f = fetched("https://x.gov/.well-known/mcp.json", body='{"x":1}')
    assert McpProbe().evaluate(f)[0] == Score.PARTIAL


def test_mcp_fail_when_absent():
    f = fetched("https://x.gov/.well-known/mcp.json", status=404, body="")
    assert McpProbe().evaluate(f)[0] == Score.FAIL
