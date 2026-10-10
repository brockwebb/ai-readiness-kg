"""The recollection cycle and the composite of record, read from what the run wrote.

`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` (and ADDENDUM_01). Nothing here
contacts anything: the cycle is over and these are its records. The manners clauses follow
`tests/test_scan_run_4.py`, widened by DN-012 d3: a host the roster does not name may be
contacted only because a body DECLARED it, and only on the legs that read that declaration.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import composite, declarations, errors, load_params            # noqa: E402
from scan.manners import same_site                                      # noqa: E402

CYCLE = "scan_2026-10-06_recollect"
COMPOSITE = "scan_2026-10-06_composite_b"
BASE = "scan_2026-09-10_rj5"
TARGETS = REPO / "state" / "scan_targets_fss_2026-09_v5.json"
LEGS = ["A1", "A2", "A3", "A9", "B1", "B3", "B4", "D1", "D3", "D4", "F4", "G4"]
#: The two legs the composite withholds, and why, in one word each: the defect it names.
WITHHELD = {"A2": "api_declarations", "D1": "substrings"}


def _load(name: str) -> dict:
    path = REPO / "state" / f"{name}.json"
    if not path.is_file():
        pytest.skip(f"{name} has not been written")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def payload():
    return _load(CYCLE)


@pytest.fixture(scope="module")
def comp():
    return _load(COMPOSITE)


def issued(payload: dict):
    """`(observation, netloc)` for every request that actually went out to a real host."""
    for o in payload["observations_detail"]:
        url = (o.get("request") or {}).get("url") or ""
        if not url or str(o.get("target_doc_id", "")).startswith("control:"):
            continue
        if o.get("error_class") in set(errors.NOT_REQUESTED):
            continue
        yield o, urllib.parse.urlsplit(url).netloc.lower()


# ------------------------------------------------------------------ the cycle

def test_the_cycle_is_targeted_on_the_twelve_legs_and_judged_nothing_else(payload):
    assert payload["scope"] == "legs" and payload["legs_collected"] == LEGS
    assert payload["control_verdict"] == "pass"
    assert payload["surfaces"] == 46
    assert {f["leg"] for f in payload["findings_detail"]} == set(LEGS)
    assert payload["error_class_counts"].get("unknown", 0) == 0


def test_every_off_roster_request_went_to_a_host_its_body_declared_for_that_leg(payload):
    """DN-012 d3: "those hosts enter the roster for those legs only". A request off every
    roster site is legitimate only if the surface's body declared that host for the leg the
    Observation belongs to (`declarations.admitted_hosts`), read from the `declared` block the
    collector stamped on the Observation itself."""
    keys = {h["site_key"] for h in json.loads(TARGETS.read_text(encoding="utf-8"))["hosts"]}
    agency = {r["doc_id"]: r["agency"] for r in payload["matrix"]}
    decl = declarations.load()
    params = load_params()
    bad = []
    for o, netloc in issued(payload):
        if any(same_site(netloc, k) for k in keys):
            continue
        body = agency.get(o["target_doc_id"])
        admitted = declarations.admitted_hosts(declarations.for_body(decl, body), o["leg"],
                                               params)
        if netloc not in admitted:
            bad.append((netloc, o["leg"], body))
    assert bad == [], f"off-roster requests no declaration admits: {sorted(set(bad))}"


def test_every_contacted_netloc_had_room_for_its_robots_read(payload):
    """`tests/test_scan_run_4.py`'s robots-first replay: the socket count leaves room on every
    netloc for the `/robots.txt` read `manners._gate` makes before the first request."""
    per_host = payload["requests_per_host"]
    urls: dict = {}
    for o, netloc in issued(payload):
        urls.setdefault(netloc, []).append(o["request"]["url"])
    tight = {n: (per_host.get(n, 0), len(u)) for n, u in urls.items()
             if per_host.get(n, 0) < len(u) + 1}
    assert tight == {}, f"no room for a robots.txt read on: {tight}"


# ------------------------------------------------------------------ the composite

def test_the_composite_was_the_cycle_of_record_and_its_successor_overlays_this_cycle(comp):
    """`_composite_b` was the cycle of record from 2026-10-07 until `_composite_c`
    (`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 2), which
    overlays this cycle's re-judgement under generation 15 and withholds nothing."""
    import yaml
    pub = yaml.safe_load((REPO / "docs" / "reports" / "publication.yaml").read_text())
    assert "2026-10-06_composite_b" in pub["released"]
    assert composite.is_composite(comp)
    succ = _load(pub["snapshot_cycle"])
    assert pub["snapshot_cycle"] == "scan_2026-10-06_composite_c"
    over = succ["composed_of"]["overlay"]
    assert _load(over["cycle"])["derived_from"] == CYCLE and over["withheld"] == {}


def test_the_composite_is_its_parts_selected_by_leg_and_nothing_else(comp, payload):
    base = _load(BASE)
    over_legs = comp["composed_of"]["overlay"]["legs"]
    assert comp["composed_of"]["overlay"]["cycle"] == CYCLE
    assert comp["composed_of"]["base"]["cycle"] == BASE
    assert sorted(over_legs) == sorted(set(LEGS) - set(WITHHELD))
    want = ([f for f in base["findings_detail"] if f["leg"] not in over_legs]
            + [f for f in payload["findings_detail"] if f["leg"] in over_legs])
    assert comp["findings_detail"] == want
    assert comp["observations_detail"] == []


def test_the_withheld_legs_name_the_defect_they_are_withheld_for(comp):
    withheld = comp["composed_of"]["overlay"]["withheld"]
    assert set(withheld) == set(WITHHELD)
    for leg, word in WITHHELD.items():
        assert word in withheld[leg], (leg, withheld[leg])
    # ... and the composite shows the base's cells for them.
    assert all(composite.finding_part(comp, f) == BASE
               for f in comp["findings_detail"] if f["leg"] in WITHHELD)


def test_the_first_declaration_is_not_published(comp):
    """The composite that took A2 and D1 was rejected before publication: its matrices are not
    in the published tree, where `prescriptions.published_cycles` would list them."""
    assert not list((REPO / "docs" / "reports").glob("scan_matrix_*_2026-10-06_composite.*"))
    assert (REPO / "state" / "composite_rejected_2026-10-06").is_dir()
