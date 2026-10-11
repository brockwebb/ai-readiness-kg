"""The two collection changes part 2 admits, each red on the pre-change collector and green after.

`cc_tasks/2026-10-07_seed_known_locations_verify_ADDENDUM_01.md` A:

* **A13 collection.** The discoverability candidate is a leg of every Tier A product surface
  (`run.targets`); a targeted cycle reads each surface's product page from a stored cycle
  instead of fetching it (`run.py --pages-from`, `runner.stored_page`); and A2's collector fetches
  RFC 9727's `/.well-known/api-catalog` on the product host and on a verified API host, and
  `/data.json` at the API host's root (`runner._convention_fetches`).
* **D1 terms read.** The terms page is kept whole up to `d1_sources.terms_text_max_bytes`, and a
  page over it is `error` naming the bytes kept (`runner._terms_text`).

No network: a fetcher that serves a fixed map, records every URL asked, and raises on anything
else.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import declarations, load_params                            # noqa: E402
from scan.rules import CURRENT                                          # noqa: E402
from scan.rules import judge as judge_rule                              # noqa: E402

HOST = "https://stats.example.gov"
PAGE = f"{HOST}/products/estimates.html"
API_HOST = "https://api.stats.example.gov"
API = f"{API_HOST}/v2"
TERMS = f"{HOST}/developers/terms.html"
DOC = "flagship:stats.example.gov/products/estimates.html"
ALL = list(declarations.SEED_SOURCES)


@pytest.fixture
def params():
    return load_params()


@pytest.fixture(autouse=True)
def _staged(tmp_path, monkeypatch):
    """Bodies the collectors store go to a tmp tree, never the committed evidence store."""
    from scan import model
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path)


class _Fetcher:
    """Serves `pages` ({url: (status, content_type, body)}); everything else is a 404. Records
    every URL asked. `forbid` makes any request at all a test failure."""

    def __init__(self, pages: dict, forbid: bool = False):
        self.pages, self.asked, self.forbid, self.requests = pages, [], forbid, {}

    def allowed(self, url):
        return True

    def raw_get(self, url):
        if self.forbid:
            raise AssertionError(f"a request was made: {url}")
        self.asked.append(url)
        st, ct, body = self.pages.get(url, (404, "text/html", b"<html>not found</html>"))
        return {"status": st, "headers": {"content-type": ct}, "body": body, "elapsed_ms": 1,
                "final_url": url}

    raw_head = raw_get


def _decl(**api) -> dict:
    """A body's scheme-2 declaration with every seed source searched for every object."""
    return {"scheme": 2, "searched": {o: list(ALL) for o in declarations.SEARCH_OBJECTS},
            "api_base": dict({"url": API, "seeded_from": ["model_knowledge:test"],
                              "status": "verified", "verified_at": "2026-10-11T00:00:00Z"},
                             **api),
            "inventory_urls": [], "changelog_urls": [], "unresolved": []}


def _target(decl, **kw) -> dict:
    return dict({"doc_id": DOC, "url": PAGE, "agency": "X", "declared": decl}, **kw)


# ============================================================ A13 collection

def test_a13_is_a_leg_of_every_tier_a_product_surface_and_of_no_host_surface(params):
    from scan import run
    tgts = run.targets(params)
    product = [t for t in tgts if t["surface_kind"] != "well_known" and t["tier"] == "A"]
    hosts = [t for t in tgts if t["surface_kind"] == "well_known"]
    assert product and hosts
    assert all("A13" in t["legs"] for t in product)
    assert not any("A13" in t["legs"] for t in hosts)
    assert all(t["legs"] == list(run.HOST_LEGS) for t in hosts)


def _stored_row(params) -> dict:
    """A link-probe page Observation as a stored cycle recorded it."""
    from scan.model import Observation
    o = Observation.make("link_probe", "link_probe", DOC, PAGE, "http", "0.1.0", params,
                         {"method": "GET", "url": PAGE, "ua": "x"},
                         {"status": 200, "headers": {"content-type": "text/html"},
                          "body_sha256": "a" * 64, "body_path": None, "bytes": 10,
                          "elapsed_ms": 1},
                         parsed={"content_type": "text/html", "final_url": PAGE,
                                 "extension": "html", "links": [{"href": f"{HOST}/x",
                                                                 "text": "x"}],
                                 "link_candidates": {"scheme": 1, "probed": 25},
                                 "declared": {"scheme": 1, "body": "X", "field": "api_base",
                                              "unresolved": [], "api_base": None}},
                         captured_at="2026-10-06T22:42:16+00:00")
    return o.to_dict()


def test_a_stored_page_is_read_never_fetched_and_carries_this_cycles_declaration(params):
    from scan.runner import STORED_PAGE_COLLECTOR, collect_leg
    row = _stored_row(params)
    f = _Fetcher({}, forbid=True)
    obs = collect_leg({"leg": "link_probe"},
                      _target(_decl(), stored_page={"cycle": "scan_old", "row": row}), params, f)
    assert len(obs) == 1, "no link is probed when the page is read from a stored cycle"
    o = obs[0]
    assert o.collector == STORED_PAGE_COLLECTOR and o.obs_id != row["obs_id"]
    assert o.captured_at == row["captured_at"] and o.response == row["response"]
    assert o.parsed["links"] == row["parsed"]["links"]
    assert o.parsed["read_from_cycle"] == {"cycle": "scan_old", "obs_id": row["obs_id"],
                                           "captured_at": row["captured_at"]}
    assert "link_candidates" not in o.parsed, "another cycle's probe counts are not carried"
    assert o.parsed["declared"]["scheme"] == 2, "this cycle's block, not the stored one"


def test_a_stored_page_of_another_surface_is_refused(params):
    from scan.runner import stored_page
    row = dict(_stored_row(params), target_doc_id="home:other.example.gov")
    with pytest.raises(ValueError, match="not the link_probe page"):
        stored_page({"cycle": "scan_old", "row": row}, "link_probe", DOC, PAGE, params)


def test_a2_fetches_the_convention_locations_on_the_product_and_api_hosts(params):
    from scan.runner import collect_leg
    f = _Fetcher({API: (200, "application/json", b'{"openapi": "3.0.3"}')})
    obs = collect_leg({"leg": "A2"}, _target(_decl()), params, f)
    want = [f"{HOST}/.well-known/api-catalog", f"{API_HOST}/.well-known/api-catalog",
            f"{API_HOST}/data.json"]
    for u in want:
        assert u in f.asked, u
    conv = {(o.target_url, o.parsed["probe"], o.parsed["convention_of"]) for o in obs
            if (o.parsed or {}).get("probe") in ("api_catalog", "convention_inventory")}
    assert conv == {(want[0], "api_catalog", "product_host"),
                    (want[1], "api_catalog", "api_host"),
                    (want[2], "convention_inventory", "api_host")}
    assert f"{HOST}/data.json" not in f.asked, "the product host's /data.json is D4's fetch"


def test_an_unverified_api_host_is_not_asked_for_its_convention_locations(params):
    from scan.runner import collect_leg
    f = _Fetcher({})
    collect_leg({"leg": "A2"}, _target(_decl(status="refused_robots")), params, f)
    assert f"{HOST}/.well-known/api-catalog" in f.asked
    assert not any(u.startswith(API_HOST + "/.well-known") or u == f"{API_HOST}/data.json"
                   for u in f.asked)


def test_a13_judges_the_api_catalog_it_could_not_see_before(params):
    """End to end over one surface: the product page read from a stored cycle, the API that
    exists and is not linked from it, and an RFC 9727 catalog served on the product host. Before
    the change A13 said the convention location "was not fetched" (`error`)."""
    from scan import run
    row = _stored_row(params)
    pages = {API: (200, "application/json", b'{"openapi": "3.0.3"}'),
             f"{HOST}/.well-known/api-catalog": (200, "application/linkset+json",
                                                 b'{"linkset": []}')}
    decl = _decl()
    t = _target(decl, stored_page={"cycle": "scan_old", "row": row})
    obs, findings = run.run_surface(run.specs(), t, params, ["A2", "D1", "F4", "D4", "A13"],
                                    _Fetcher(pages))
    a13 = next(f for f in findings if f.leg == "A13")
    assert "api pass (the API: an API catalog is served at " \
           f"{HOST}/.well-known/api-catalog" in a13.reason, a13.reason
    assert not any(o.leg == "link_probe" and (o.parsed or {}).get("probe") == "link"
                   for o in obs)


def test_stored_pages_are_found_per_target_and_refused_when_missing(params, tmp_path,
                                                                     monkeypatch):
    from scan import run
    monkeypatch.setattr(run, "STATE_DIR", tmp_path)
    row = _stored_row(params)
    (tmp_path / "scan_old.json").write_text(json.dumps({"observations_detail": [row]}))
    assert run.stored_pages("scan_old", [{"doc_id": DOC}]) == {DOC: row}
    with pytest.raises(SystemExit, match="recorded no product page"):
        run.stored_pages("scan_old", [{"doc_id": DOC}, {"doc_id": "home:else"}])


# ============================================================ D1 terms read

def _d1(params, body: bytes, ceiling: int | None = None):
    from scan.runner import collect_leg
    if ceiling is not None:
        params["d1_sources"]["terms_text_max_bytes"] = ceiling
    decl = _decl(terms_url=TERMS, terms={"status": "verified",
                                         "verified_at": "2026-10-11T00:00:00Z"})
    f = _Fetcher({PAGE: (200, "text/html", b"<html><body>product</body></html>"),
                  TERMS: (200, "text/html", body)})
    obs = collect_leg({"leg": "D1"}, _target(decl), params, f)
    return obs, judge_rule(CURRENT["D1"], obs, params)


def _terms_page(pad: int) -> bytes:
    """A terms page whose licence statement sits after `pad` bytes of other terms."""
    filler = "<p>" + ("These terms govern use of the API. " * (pad // 36 + 1))[:pad] + "</p>"
    return (f"<html><body><h1>Terms of Service</h1>{filler}"
            f"<p>Data are in the PUBLIC DOMAIN.</p></body></html>").encode()


def test_d1_reads_a_terms_page_whole_past_twenty_thousand_characters(params):
    """census.gov's terms page is 302,319 bytes; the collector kept 20,000 characters, so a
    licence stated past them was never read and the leg could only be `error`."""
    body = _terms_page(60_000)
    obs, f = _d1(params, body)
    terms = next(o for o in obs if o.target_url == TERMS)
    assert len(terms.parsed["terms_text"].encode()) == len(body)
    assert terms.parsed["terms_text_truncated"] is False
    assert f.verdict == "pass" and "PUBLIC DOMAIN" in f.reason, f.reason


def test_d1_a_page_over_the_ceiling_is_error_naming_the_bytes_kept(params):
    body = _terms_page(8_000)
    obs, f = _d1(params, body, ceiling=4_000)
    terms = next(o for o in obs if o.target_url == TERMS)
    assert terms.parsed["terms_text_truncated"] is True
    assert terms.parsed["terms_text_ceiling"] == 4_000
    assert f.verdict == "error", f.reason
    assert f"was read to 4000 of its {len(body)} bytes" in f.reason, f.reason


def test_the_ceiling_is_declared_in_params_not_in_the_collector(params):
    src = (REPO / "assessment" / "harness" / "scan" / "runner.py").read_text(encoding="utf-8")
    assert "[:20000]" not in src
    assert int(params["d1_sources"]["terms_text_max_bytes"]) >= 1_376_062
