"""Cycle 4's gate: the complete frame, first cycle under the fixed instrument.

`cc_tasks/2026-09-10_scan_run_4.md` §3. Everything here is read from the payload the run wrote,
never recomputed by contacting anything — the cycle is over and this is its record.

The manners clauses are checked TWO ways, because one of them cannot see the whole truth. An
Observation records a request, but the fetcher issues requests an Observation never carries:
`/robots.txt` is read inside `_robots_for`, and a link probe issues one HEAD per link inside a
single Observation's `parsed`. So "was robots read first" is not answerable from the
Observations alone — 11 of the 33 netlocs that carry Observations have no `/robots.txt`
Observation, and every one of them was in fact read. What is answerable, and what this file
asserts, is that the socket count leaves room for it on every netloc, and that the structural
guarantee holds: `raw_get` and `raw_head` both enter through `_gate`, which is DD-062's whole
point and is tested against a live fixture in `test_manners_robots_first.py`.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import errors, load_params                                # noqa: E402
from scan.manners import same_site                                  # noqa: E402

CYCLE = "scan_2026-09-10"
PAYLOAD = REPO / "state" / f"{CYCLE}.json"
TARGETS = REPO / "state" / "scan_targets_fss_2026-09_v5.json"

#: The seven declared in `docs/design/fss_flagship_declarations.md` and admitted at targets v5.
DECLARED = {"DRSMSU", "NAHMSAPHIS", "NCES", "SAMHSACBHS", "BLS", "BTS", "ORES"}
#: The three whose hosts answer 403 to the identified client, across four cycles now.
REFUSING = {"BLS", "BTS", "ORES"}


@pytest.fixture(scope="module")
def payload():
    if not PAYLOAD.is_file():
        pytest.skip(f"{CYCLE} has not been run")
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def targets():
    return json.loads(TARGETS.read_text(encoding="utf-8"))


def issued_requests(payload: dict) -> dict:
    """`{netloc: [url, …]}` for requests that ACTUALLY WENT OUT.

    `errors.NOT_FETCHED` is the filter and it is read from `errors.py` rather than listed here.
    An `off_host` link and a `robots_disallowed` path are recorded WITH their URL precisely so
    the log shows the policy was applied; counting those as contacts turned 161 recorded
    exclusions into 44 imaginary hosts the first time this replay was written.
    """
    out: dict = {}
    for o in payload["observations_detail"]:
        url = (o.get("request") or {}).get("url") or ""
        if not url or url.startswith("fixture://"):
            continue
        if o.get("error_class") in set(errors.NOT_FETCHED):
            continue
        netloc = urllib.parse.urlsplit(url).netloc.lower()
        if netloc.startswith("127.0.0.1"):
            continue                                   # the control fixtures are us
        out.setdefault(netloc, []).append(url)
    return out


# ------------------------------------------------------------------ the site bound

def test_no_request_left_the_site_bound(payload, targets):
    """§3: every request in the log is same-site to a roster site key. **0 off-site.**"""
    keys = {h["site_key"] for h in targets["hosts"]}
    assert len(keys) == 19
    contacted = set(issued_requests(payload)) | set(payload["requests_per_host"])
    off = sorted(n for n in contacted if not any(same_site(n, k) for k in keys))
    assert off == [], f"the cycle contacted a netloc on no roster site: {off}"


def test_the_contact_set_is_wider_than_the_roster_and_that_is_the_bound_working(payload,
                                                                                targets):
    """The task file says "the 22 netlocs of targets v5 and no other". The frame is 22 netlocs;
    the CONTACT SET is not, and never was — cycle 3 reached 24.

    A statistical agency serves its products from siblings of its own host: `apps.bea.gov`,
    `data.census.gov`, `wonder.cdc.gov`. DD-063 binds the scanner to the SITE, by RFC 6265
    §5.1.3 domain matching, exactly so a deep link into a body's own tooling is followable and a
    hop to another body's host is not. A bound of "the roster netlocs and no other" would score
    every agency that uses a subdomain as unreachable, which measures our frame rather than
    their publishing.

    So the number to hold is the SITE count, and it is 19 in both.
    """
    keys = {h["site_key"] for h in targets["hosts"]}
    contacted = set(payload["requests_per_host"])
    assert len(contacted) > len({h["host"] for h in targets["hosts"]})
    assert len({k for k in keys if any(same_site(n, k) for n in contacted)}) <= 19


def test_every_contacted_netloc_had_room_for_its_robots_read(payload):
    """§3: 0 robots-late.

    The socket counter (`manners.Fetcher.requests`) counts every request; the Observations
    carry a subset. If a netloc's socket count were ever EQUAL to the number of requests its
    Observations carry, there would have been no room for the `/robots.txt` read that
    `_gate` performs before the first of them, and robots-first would have been violated.
    """
    per_host = payload["requests_per_host"]
    tight = {n: (per_host.get(n, 0), len(urls))
             for n, urls in issued_requests(payload).items()
             if per_host.get(n, 0) < len(urls) + 1}
    assert tight == {}, f"no room for a robots.txt read on: {tight}"


def test_the_two_netlocs_with_no_observation_at_all_were_read_and_then_refused(payload):
    """A netloc in the socket log with no Observation carrying a request is robots-first doing
    exactly what it is for: read the file, then obey it. Their disallowed paths are recorded as
    `robots_disallowed` Observations, with their URLs, and no request went out."""
    silent = set(payload["requests_per_host"]) - set(issued_requests(payload))
    disallowed = {urllib.parse.urlsplit((o.get("request") or {}).get("url") or "").netloc.lower()
                  for o in payload["observations_detail"]
                  if o.get("error_class") == "robots_disallowed"}
    assert silent <= disallowed, (
        f"a netloc was contacted, produced no observation and refused nothing: "
        f"{sorted(silent - disallowed)}")


def test_the_request_count_is_reported_per_site(payload, targets):
    """§4 asks for the count per SITE, and a per-netloc table does not answer it: a body's
    manners claim is about what we asked of that body, and `apps.bea.gov` is BEA."""
    keys = {h["site_key"] for h in targets["hosts"]}
    per_site: Counter = Counter()
    for netloc, n in payload["requests_per_host"].items():
        hit = [k for k in keys if same_site(netloc, k)]
        assert len(hit) == 1, f"{netloc} matches {hit}; a netloc belongs to exactly one site"
        per_site[hit[0]] += n
    assert sum(per_site.values()) == payload["requests_total"]
    assert set(per_site) <= keys


# ------------------------------------------------------------------ tiers and identities

def test_zero_tier_c_findings_outside_the_tier0_legs(payload, targets):
    """DD-059. Above tier 0 a catalog has no product vintage and no bulk download, so a
    comparison there would stop being like-for-like."""
    tier = {r["doc_id"]: r.get("tier") for r in targets["rows"]}
    allowed = set(load_params()["tier0"]["legs"])
    stray = sorted({(r["doc_id"], leg) for r in payload["matrix"]
                    if tier.get(r["doc_id"]) == "C"
                    for leg in r["verdicts"] if leg not in allowed})
    assert stray == [], f"Tier C was judged outside tier 0: {stray}"


def test_no_two_rows_of_one_host_minted_the_same_finding_identity(payload):
    """A `finding_id` is derived from the rule, its version, its Observations and the params
    hash. Two rows of one host that both judged a leg would collide, and a collision means one
    of the two measurements is invisible."""
    seen = Counter(f["finding_id"] for f in payload["findings_detail"])
    dupes = {k: n for k, n in seen.items() if n > 1}
    assert dupes == {}, f"duplicate finding identities: {dupes}"


def test_an_unnamed_error_class_is_reported_and_never_becomes_a_verdict(payload):
    """`unknown` is the classifier's ONLY remainder, so a cycle that produces any is a cycle
    whose map is missing a rule. It is counted and reported per cycle and never absorbed into a
    neighbouring class — and, whatever it is, it must not have produced a verdict about a
    product. Cycle 4 produced one: `httpx.TooManyRedirects` on Census's invalid-route probe.
    """
    unknown = [o for o in payload["observations_detail"]
               if o.get("error_class") == "unknown"]
    assert len(unknown) == payload["error_class_unknown"]
    for o in unknown:
        assert (o.get("response") or {}).get("error"), (
            "an unnamed class with no transport error recorded is unreadable later")
        for f in payload["findings_detail"]:
            if o["obs_id"] in f.get("evidence", []):
                assert f["verdict"] == "error", (
                    f"{f['rule_id']} reached {f['verdict']} from an observation the collector "
                    f"never made; DD-052 §6")


# ------------------------------------------------------------------ the seven flagships

def test_the_seven_declared_flagships_were_measured(payload, targets):
    rows = {r["agency"] for r in targets["rows"]
            if r["surface_kind"] == "flagship" and str(r["doc_id"]).startswith("flagship:")}
    assert rows == DECLARED
    measured = {r["agency"] for r in payload["matrix"]
                if str(r["doc_id"]).startswith("flagship:")}
    assert measured == DECLARED, f"a declared flagship was not measured: {DECLARED - measured}"


def test_the_refusing_three_are_error_and_never_a_verdict_about_the_product(payload):
    """Decision 4, and DD-052 §6. A 403 says the collector could not observe. It is never a
    statement that the product failed, and never that it passed."""
    for r in payload["matrix"]:
        if not str(r["doc_id"]).startswith("flagship:") or r["agency"] not in REFUSING:
            continue
        verdicts = set(r["verdicts"].values())
        assert verdicts <= {"error"}, (
            f"{r['agency']}'s refused flagship carries {sorted(verdicts)}; a host that refused "
            f"us told us nothing about its product")


def test_the_four_reachable_flagships_produced_real_verdicts(payload):
    live = {r["agency"]: r["verdicts"] for r in payload["matrix"]
            if str(r["doc_id"]).startswith("flagship:") and r["agency"] in DECLARED - REFUSING}
    assert set(live) == DECLARED - REFUSING
    for agency, verdicts in live.items():
        assert set(verdicts.values()) - {"error"}, (
            f"{agency}'s flagship errored on every leg; its declaration may name a page the "
            f"scanner cannot read at all (frame-v5 RESULT §6 item 3)")
