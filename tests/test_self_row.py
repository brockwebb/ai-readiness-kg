"""The self row: measured, re-derivable, and honest about which authority answered.

`cc_tasks/2026-09-13_self_row.md` §3. Six properties a reader of the published row would
otherwise have to take on trust:

* the payload **re-derives byte-identically** — and it can only be re-derived if the parameters
  it was measured under are recoverable, which for this cycle means the committed `params.yaml`
  recovered from git by `base_params_hash` plus the recorded `params_overlay`. That
  reconstruction is the point of the first test: an in-memory overlay with no record of itself
  would have made this the one payload nothing can ever re-judge;
* every Finding records **the URL it actually read**;
* the per-leg authority claim agrees with those URLs, so "this publication" is a derived fact and
  not a label;
* the six tier-0 verdicts are registered Results at the values the payload holds;
* both integrity readings are 0;
* the socket counter names **only** the published authority — no federal host, no reference host.

The Neo4j-backed test skips when the database is down, which is this repo's convention. The rest
do not: the payload is on disk either way. Every test skips cleanly before the scan has been run,
because the payload is the run's output and the run is not a test.
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from scan import load_params                                          # noqa: E402
from scan.model import params_hash                                    # noqa: E402

PUB = yaml.safe_load((REPO / "docs" / "reports" / "publication.yaml")
                     .read_text(encoding="utf-8"))
CYCLE = PUB["self_scan_cycle"]
PARAMS_REL = "assessment/harness/scan/params.yaml"


def _payload_or_skip(name: str) -> dict:
    p = REPO / "state" / f"{name}.json"
    if not p.is_file():
        pytest.skip(f"{p.relative_to(REPO)} does not exist; the self-scan has not been run")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture
def payload() -> dict:
    return _payload_or_skip(CYCLE)


@pytest.fixture
def row() -> dict:
    return _payload_or_skip(f"self_l0_{CYCLE}")


@pytest.fixture
def session():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                          # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


def _base_params(payload: dict) -> dict:
    """`params.yaml` as it was when this cycle ran, recovered from git BY HASH.

    The same discipline `tests/test_scan_harness_v4.py::_params_for` applies to every other
    cycle: never reconstructed by hand, because an approximation of an old parameter set makes
    the gate pass for the wrong reason.
    """
    want = payload["base_params_hash"]
    revs = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_REL],
                          capture_output=True, text=True, cwd=str(REPO)).stdout.split()
    for rev in revs:
        txt = subprocess.run(["git", "show", f"{rev}:{PARAMS_REL}"],
                             capture_output=True, text=True, cwd=str(REPO)).stdout
        if txt.strip() and params_hash(yaml.safe_load(txt)) == want:
            return yaml.safe_load(txt)
    if params_hash(load_params()) == want:
        return load_params()
    raise AssertionError(
        f"no commit of {PARAMS_REL} hashes to {want[:12]}…; the base parameters this cycle was "
        f"measured under are not recoverable, so its Findings can never be re-derived")


def test_the_overlaid_parameters_are_reconstructible_from_the_record(payload):
    """The overlay is not a shortcut past re-derivability; it is a recorded construction.

    `scripts/run_self_scan.py` runs `run.py` under the committed parameters with the cycle
    IDENTITY overlaid in memory, because editing `params.cycle` would re-point
    `register_l0_report_results.netlocs_declared` and break the re-derivation of a published
    Result. What makes that legitimate rather than a hole is exactly this: base + overlay
    reproduces the hash every Observation and Finding of the cycle carries.
    """
    base = _base_params(payload)
    overlay = payload["params_overlay"]
    assert set(overlay) == {"cycle"}, (
        f"the overlay changes {sorted(overlay)}; only the cycle identity may differ, or the self "
        f"row was not measured by the same instrument as the report")
    rebuilt = {**base, **overlay}
    assert params_hash(rebuilt) == payload["params_hash"], (
        "base_params_hash + params_overlay does not reproduce the cycle's params_hash; the "
        "parameters this cycle ran under are not recoverable from its own record")
    assert overlay["cycle"]["name"] == payload["cycle"]
    assert overlay["cycle"]["targets"] == payload["targets"]


def test_the_self_payload_re_derives_byte_identically(payload):
    """Every Finding re-judged from the stored Observations alone, under the parameters
    reconstructed above. Nothing is fetched; if this needed the network the split would be a
    fiction."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rederive_self", REPO / "assessment" / "harness" / "scan" / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rebuilt = {**_base_params(payload), **payload["params_overlay"]}
    out = mod.rederive(payload, rebuilt)
    assert out["identical"], json.dumps(out, indent=1)[:2000]


def test_every_finding_records_the_url_it_read(payload, row):
    """Decision 2's first clause. A verdict whose URL is not on the record is a verdict nobody
    can check, and on this host the URL is the whole question."""
    obs = {o["obs_id"]: o for o in payload["observations_detail"]}
    for f in payload["findings_detail"]:
        urls = [(obs[o].get("request") or {}).get("url") or obs[o].get("target_url")
                for o in f.get("evidence") or [] if o in obs]
        assert [u for u in urls if u], f"{f['leg']} cites no Observation carrying a URL"
    for leg, v in row["legs"].items():
        assert v["urls_read"], f"the row prints {leg} with no URL read"
        for r in v["reads"]:
            assert r.get("url"), f"{leg} carries an evidence entry with no URL: {r}"


def test_the_authority_claim_on_each_leg_is_derived_from_the_urls(row):
    """Decision 2's second clause, and the reason the row is worth publishing at all: a leg that
    read only paths under the published site measured this publication; a leg that read the
    authority root did not. Re-derived here from `urls_read` rather than trusted."""
    site = row["site_url"]
    for leg, v in row["legs"].items():
        on = [u for u in v["urls_read"] if u.startswith(site)]
        off = [u for u in v["urls_read"] if not u.startswith(site)]
        expect = bool(on) and not off
        assert v["authority_is_this_publication"] is expect, (
            f"{leg} claims authority_is_this_publication={v['authority_is_this_publication']} "
            f"and read on-site {on} / off-site {off}")
    assert set(row["legs_measuring_this_publication"]) | \
           set(row["legs_measuring_the_authority"]) == set(row["legs"]), (
        "a leg is in neither bucket; the row would print a verdict about an unstated object")
    assert not (set(row["legs_measuring_this_publication"])
                & set(row["legs_measuring_the_authority"]))


def test_the_row_carries_every_tier_0_leg_and_no_other(row):
    """The row prints the tier-0 set OF THE CYCLE THAT MEASURED IT, recovered from git by the
    self payload's own `params_hash`.

    Not `load_params()`. The self row is a stored measurement of this publication at one
    moment; the instrument has changed since (DD-066 withdrew G1-D from host-level surfaces)
    and will change again. Asserting a stored row against today's leg list says a measurement
    must obey an instrument that did not exist when it was taken, and the first legitimate
    withdrawal turns the assertion red for the one reason that carries no information.
    """
    import json as _json
    from support.prior_params import tier0_legs_of
    payload = _json.loads((REPO / "state" / f"{row['cycle']}.json").read_text(encoding="utf-8"))
    tier0 = tier0_legs_of(payload)
    assert list(row["legs"]) == tier0, (
        f"the row prints {list(row['legs'])} and the cycle that measured it declared tier-0 "
        f"as {tier0}")
    assert sum(row["verdict_counts"].values()) == len(tier0)


def test_both_integrity_readings_are_zero_on_the_self_payload(row):
    inv = row["invariants"]
    assert inv["observed_on_missing_document"] == 0, inv[
        "observed_on_missing_document_doc_ids"]
    assert inv["findings_evidence_unretained"] == 0, inv[
        "findings_evidence_unretained_ids"]
    assert inv["host_observations"] > 0, (
        "no synthetic host observation; the carve-out these readings depend on is not being "
        "exercised, so their being zero would say nothing")


def test_the_socket_counter_names_only_the_published_authority(payload, row):
    """The network claim, counted at the socket rather than inferred from Observations. No
    federal host and no reference host may appear: a self-scan that touched one would have
    measured something this row does not describe."""
    authority = urllib.parse.urlsplit(PUB["site_url"]).netloc
    contacted = {h for h, n in (payload["requests_per_host"] or {}).items() if n}
    assert contacted == {authority}, (
        f"the self cycle contacted {sorted(contacted)}; the only host it may contact is "
        f"{authority}")
    assert row["requests_per_host"] == payload["requests_per_host"]


def test_the_six_verdicts_are_registered_at_the_values_the_row_holds(session, row):
    """A published row over unregistered verdicts would be a number with no artifact behind it.
    1.0 = pass and 0.0 = fail, which is what `self_row_report` refuses to stretch any further."""
    import self_row_report as srr
    want = {srr.result_name(leg, row["cycle"]): srr.ENCODABLE[v["verdict"]]
            for leg, v in row["legs"].items()}
    live = {r["name"]: r["value"] for r in session.run(
        "MATCH (r:Result) WHERE r.name IN $names AND r.state <> 'superseded' "
        "RETURN r.name AS name, r.value AS value", names=sorted(want))}
    missing = sorted(set(want) - set(live))
    assert not missing, f"the row prints verdicts with no registered Result: {missing}"
    drift = [f"{n}: row {v}, registry {live[n]}" for n, v in want.items() if live[n] != v]
    assert not drift, drift


def test_the_index_prints_the_row_it_measured(row):
    """Decision 5. The page renders the payload — the verdicts, and the authority per leg — and
    the reader is told to read the authority column first, because four of the six legs on a
    project site are not about this publication at all."""
    html = (REPO / "docs" / "index.html").read_text(encoding="utf-8")
    assert row["cycle"] in html
    for leg, v in row["legs"].items():
        assert f"<code>{leg}</code>" in html, f"the index does not print {leg}"
        for u in v["urls_read"]:
            assert u in html, f"the index prints {leg} without the URL it read: {u}"
    assert "RFC 9309" in html and "authority" in html.lower()
    assert "reported and left standing" in html, (
        "the page no longer says a fail stays standing; decision 3 is the reason the row is "
        "publishable at all")
