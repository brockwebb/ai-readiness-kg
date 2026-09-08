"""The standing readers for harness-v4's four properties, and this task's gate.

`cc_tasks/2026-09-08_scan_harness_v4.md`. Every one of these is a property that was true by
nobody's doing until this task, and two of them have already put a wrong number on the log:

1. **A rule never reaches a verdict from a probe it did not observe.** `RULE-A10-v2` returned
   `pass` on `scan-eia-flagship-1-open-data` because the invalid-route probe was killed
   mid-connection and "not HTTP 200" was the only test it ran. DD-052 §6 forbids `error`
   meaning the product FAILED; nothing forbade it meaning the product PASSED.
2. **One same-host policy, in one function.** It was enforced in `collectors/links.probe` and
   nowhere else, so `follow_latest_pointer` dereferenced `public.govdelivery.com`.
3. **A latest-vintage pointer is on the product's host and is not a mailing list.**
4. **A stored cycle can be re-judged under corrected rules without re-measurement** — the
   claim skeleton §6b.5 makes, exercised rather than asserted, and with the legs it CANNOT
   judge named rather than silently zeroed.

The slow tests here run the control fixtures, which are loopback-only and free but rate-limited
at one request per second per host. **No test in this file may touch a non-fixture host**, and
one of them asserts exactly that over the fixture request log.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from scan import errors as scan_errors                               # noqa: E402
from scan import load_params, manners                                # noqa: E402
from scan.collectors import links as links_collector                 # noqa: E402
from scan.collectors import v2clauses                                # noqa: E402
from scan.fixtures.server import MODES, FixtureServer                # noqa: E402
from scan.model import Observation, params_hash                      # noqa: E402
from scan.rules import (CURRENT, GENERATIONS, REGISTRY,              # noqa: E402
                        V5, judge as judge_rule)
from scan.rules import _common                                       # noqa: E402

PARAMS_REL = "assessment/harness/scan/params.yaml"

#: The five payloads this task's gate re-derives. The fifth — cycle 2 itself — joined the set
#: when cycle 2 closed; the two `_rj1` payloads join it for the next task.
PRIOR_CYCLES = {
    "scan_smoke_2026-09-06": 286,
    "scan_controls_2026-09-06": 33,
    "scan_2026-09-07": 437,
    "scan_2026-09-07_controls": 33,
    "scan_2026-09-07b": 469,
}

#: The fixture whose existence IS the fix's proof. Named once, here, because three tests need
#: it and a second literal would be a second definition of which control isolates the defect.
ISOLATING_FIXTURE = "invalid_route_unobserved"


def _mod(path: Path, name: str):
    """A module by PATH — `assessment/harness/` holds a second `run.py`, and only the path
    disambiguates the two."""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _params_for(payload: dict) -> dict:
    """The parameter set a cycle was MEASURED under, recovered from git BY HASH. Never
    reconstructed by hand: an approximation of an old parameter set makes the gate pass for the
    wrong reason."""
    revs = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_REL],
                          capture_output=True, text=True, cwd=str(REPO)).stdout.split()
    for rev in revs:
        txt = subprocess.run(["git", "show", f"{rev}:{PARAMS_REL}"],
                             capture_output=True, text=True, cwd=str(REPO)).stdout
        if txt.strip() and params_hash(yaml.safe_load(txt)) == payload["params_hash"]:
            return yaml.safe_load(txt)
    if params_hash(load_params()) == payload["params_hash"]:
        return load_params()
    raise AssertionError(
        f"no commit of {PARAMS_REL} hashes to {payload['params_hash'][:12]}…; the parameters "
        f"this cycle was measured under are not recoverable, so its Findings can never be "
        f"re-derived")


def _a10_pair(params: dict, *, invalid_error: str | None, invalid_status,
              valid_status: int = 200, visible: int = 5000) -> list:
    """The two observations A10 judges, built directly.

    Built rather than fetched because the case that matters is the one no fixture produced
    until this task: the deep link SERVED and the invalid route unobserved. The fixture now
    exists (`invalid_route_unobserved`) and is exercised by the control gate; this is the unit
    reading of the same branch, and it is the exact shape of the EIA observation pair.
    """
    def obs(url, kind, status, err, parsed_extra):
        return Observation.make(
            "A10", "A10", "scan-x", url, "lighthouse", "0.1.0", params,
            {"method": "GET", "url": url},
            {"status": status, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 1,
             **({"error": "RemoteProtocolError: Server disconnected without sending a "
                          "response."} if err else {})},
            parsed={"probe": kind, "renderer": "none", **parsed_extra}, error_class=err)
    return [obs("https://x/product", "valid", valid_status, None,
                {"extent": {"visible_chars": visible}}),
            obs("https://x/product/__probe__", "invalid_route", invalid_status, invalid_error,
                {})]


# ============================================================ §1.1 an unobserved probe

def test_the_recorded_false_positive_reproduces_under_v2_and_is_error_under_v3():
    """The one substantive measurement defect cycle 2 found, both halves.

    Asserting only that `v3` returns `error` would leave the fix unanchored: a rule that
    returned `error` for everything would pass it. The gate is the PAIR — `v2` still says
    `pass` on this evidence, because `v2` is immutable and history must keep re-deriving under
    it, and `v3` says `error` on the same bytes.
    """
    params = load_params()
    obs = _a10_pair(params, invalid_error="connection_reset", invalid_status=None)
    v2 = judge_rule("RULE-A10-v2", obs, params)
    v3 = judge_rule("RULE-A10-v3", obs, params)
    assert v2.verdict == "pass", "the recorded defect no longer reproduces under v2"
    assert "invalid route correctly HTTP None" in v2.reason
    assert v3.verdict == "error", v3.reason
    assert "connection_reset" in v3.reason
    assert "invalid-route probe" in v3.reason


def test_a_blind_deep_link_is_also_error_not_a_verdict_about_the_product():
    """The mirror probe. The invalid route is the one that produced the false positive, but a
    rule that guarded only the probe that happened to fail last time would be a patch."""
    params = load_params()
    obs = _a10_pair(params, invalid_error=None, invalid_status=404)
    obs[0].error_class = "refused"
    obs[0].response["status"] = None
    assert judge_rule("RULE-A10-v3", obs, params).verdict == "error"


def test_v3_agrees_with_v2_wherever_both_actually_observed():
    """`v3` changes the blind case and nothing else. Every branch reachable from two REAL
    probes must return what `v2` returned, or the guard has quietly re-scored the corpus."""
    params = load_params()
    cases = [dict(invalid_error=None, invalid_status=404),                    # pass
             dict(invalid_error=None, invalid_status=200),                    # soft-404 fail
             dict(invalid_error=None, invalid_status=404, valid_status=404),  # dead deep link
             dict(invalid_error=None, invalid_status=404, visible=10)]        # JS shell
    for kw in cases:
        obs = _a10_pair(params, **kw)
        v2 = judge_rule("RULE-A10-v2", obs, params)
        v3 = judge_rule("RULE-A10-v3", obs, params)
        assert (v2.verdict, v2.reason) == (v3.verdict, v3.reason), kw


def test_unobserved_error_is_none_when_the_probe_is_real():
    """The helper must be a guard and not a filter: it returns a Finding only for a probe that
    was never observed, and `None` — go on judging — for every other."""
    params = load_params()
    real, blind = _a10_pair(params, invalid_error="connection_reset", invalid_status=None)
    assert _common.unobserved_error("RULE-X-v1", "A10", [real], real, params, "x") is None
    assert _common.unobserved_error("RULE-X-v1", "A10", [real], None, params, "x") is None
    assert _common.unobserved_error("RULE-A10-v3", "A10", [real, blind], blind, params,
                                    "the invalid-route probe") is not None


def test_every_rule_from_generation_four_consults_the_blind_guard():
    """The lint §1.1 asks for. A rule that reads an individual probe and never asks whether it
    was observed is the defect this generation exists to close, and it is invisible on review:
    the omission looks exactly like the code that is right.

    **`rule_a3_v4` is the one exemption and it is pinned, not waived.** It shipped in
    generation 4 before the helper existed, and a shipped rule module may not be edited
    (`cc_tasks/2026-09-08_scan_harness_v4.md` "Zero edits") — every Finding recorded under it
    must keep re-deriving from its bytes. The exemption is by CONTENT HASH, so the moment
    anyone touches that file the exemption stops applying and the lint speaks. Its own gap is
    reported in the RESULT as a cycle-5 item, not hidden here.
    """
    import hashlib
    exempt = {"rule_a3_v4": "the fourth generation shipped before the helper existed; "
                            "immutable, and its blind-handling gap is a recorded cycle-5 item"}
    gen4_plus = [m for gen in GENERATIONS[3:] for m in gen]
    assert gen4_plus, "no generation-4-or-later rule to lint"
    missing = []
    for m in gen4_plus:
        src = Path(m.__file__).read_text(encoding="utf-8")
        stem = Path(m.__file__).stem
        if stem in exempt:
            # Pinned: the exemption is for THESE bytes and no others.
            digest = hashlib.sha256(src.encode()).hexdigest()[:16]
            assert digest == "3ff4b228658cfc0f", (
                f"{stem} changed; the lint exemption was pinned to its bytes and no longer "
                f"applies. Add `unobserved_error` to it, or re-pin with the reason.")
            continue
        if "unobserved_error" not in src:
            missing.append(m.RULE_ID)
    assert not missing, (
        f"{missing} are generation-4-or-later rules that never consult "
        f"`_common.unobserved_error`. A verdict from a probe the collector did not observe is "
        f"a measurement of the scanner, not of the product.")


def test_the_new_generation_is_new_modules_and_its_predecessors_are_untouched():
    """v2-over-v1, v3-over-v2, and now v5-over-v2: a corrected rule is a NEW module. A module
    whose bytes changed after Findings were recorded under it would make the re-derivation
    gate a tautology."""
    for m in V5:
        assert Path(m.__file__).is_file()
    for rid in ("RULE-A10-v2", "RULE-A8-v2"):
        rel = Path(REGISTRY[rid].__file__).resolve().relative_to(REPO)
        r = subprocess.run(["git", "diff", "--stat", "HEAD", "--", str(rel)],
                           capture_output=True, text=True, cwd=str(REPO))
        assert not r.stdout.strip(), f"{rel} was edited: {r.stdout.strip()}"
    assert CURRENT["A10"] == "RULE-A10-v3"
    assert CURRENT["A8"] == "RULE-A8-v3"


# ============================================================ §1.2 the isolating fixture

def test_there_are_five_fixtures_and_every_one_has_a_pre_registered_table():
    params = load_params()
    expected = params["e5_control"]["expected_verdicts"]
    assert set(expected) == set(MODES) == {
        "passes_all", "fails_all", "refuses_identified_client", "resets_connection",
        ISOLATING_FIXTURE}
    for fixture, table in expected.items():
        if isinstance(table, dict):
            assert "default" in table, fixture
    assert expected[ISOLATING_FIXTURE] == {"default": "pass", "A10": "error"}


def test_the_isolating_fixture_serves_everything_and_kills_only_the_invalid_route():
    """What separates this control from `resets_connection`: partial blindness.

    `resets_connection` resets EVERY path, so every leg is `error` and the surface is
    uniformly unobservable — it cannot reproduce "the invalid route was never observed and
    everything else was served", which is the state that produced the false positive.
    """
    from scan.manners import Fetcher
    params = load_params()
    suffix = params["a10_soft404"]["invalid_path_suffix"]
    run_mod = _mod(SCAN / "run.py", "scan_run_v4_iso")
    with FixtureServer(ISOLATING_FIXTURE) as base:
        obs, findings = run_mod.run_surface(
            run_mod.specs(), {"doc_id": f"control:{ISOLATING_FIXTURE}",
                              "url": f"{base}/index.html"},
            params, ["A10"], Fetcher(params))
    by_probe = {(o.parsed or {}).get("probe"): o for o in obs}
    assert by_probe["valid"].error_class is None
    assert (by_probe["valid"].response or {})["status"] == 200
    assert by_probe["invalid_route"].error_class == "connection_reset"
    assert by_probe["invalid_route"].target_url.endswith(suffix)
    assert [f.verdict for f in findings] == ["error"], [f.reason for f in findings]
    assert findings[0].rule_id == "RULE-A10-v3"


@pytest.mark.slow
def test_the_control_gate_passes_on_all_five_fixtures():
    """§2's first clause, whole. Every rule its pre-registered verdict on five fixtures,
    `unknown` = 0, and the fixture that isolates the defect actually fires.

    A control that fails is what makes a zero mean something. A rule that returned `error` for
    every input would pass a gate made only of `pass` and `fail` cases — which is what the
    first two fixtures were — and a rule that returned `pass` for an unobserved probe passed
    every gate that existed before this one.
    """
    run_mod = _mod(SCAN / "run.py", "scan_run_v4_gate")
    params = load_params()
    _cf, e5, control_obs, ok = run_mod.run_controls(params)
    assert ok, e5.reason
    assert e5.verdict == "pass", e5.reason

    seen = {}
    for o in control_obs:
        p = o.parsed or {}
        if p.get("fixture"):
            seen[p["fixture"]] = p
    assert set(seen) == set(params["e5_control"]["expected_verdicts"])
    for fixture, p in seen.items():
        assert p["unexpected"] == [], f"{fixture}: {p['unexpected']}"
    assert seen[ISOLATING_FIXTURE]["verdicts"]["A10"] == "error", (
        "the fixture that isolates the defect did not fire; a control that cannot reproduce "
        "the defect cannot certify the fix")

    classes = {c for p in seen.values() for c in p["error_classes"]}
    assert "refused" in classes
    assert "connection_reset" in classes
    assert "off_host" in classes, (
        "no fixture recorded an off-host exclusion, so a cycle reporting zero proves nothing")
    assert "unknown" not in classes, (
        f"a control fixture produced an UNCLASSIFIED failure; the map is missing a rule "
        f"({sorted(classes)})")


# ============================================================ §1.3 one same-host policy

def test_one_same_host_policy_and_two_spellings_that_may_not_disagree():
    params = load_params()
    assert manners.same_host_only(params) is True
    assert params["probes"]["same_host_only"] == params["link_probe"]["same_host_only"], (
        "the superseded spelling is kept readable for the cycles measured under it and may "
        "not diverge from the key that governs")
    with pytest.raises(ValueError, match="declared twice"):
        manners.same_host_only({"probes": {"same_host_only": True},
                                "link_probe": {"same_host_only": False}})
    # A params set that predates the policy defaults to enforcing it, never to probing freely.
    assert manners.same_host_only({}) is True
    assert manners.same_host_only({"probes": {"same_host_only": False}}) is False


def test_on_roster_host_is_the_one_gate_both_collectors_call():
    """Read from the SOURCE, not from behaviour: two collectors that happen to agree today are
    not one policy. `cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.1 is what an inline copy of
    the rule in one of them looks like a cycle later."""
    for mod in (links_collector, v2clauses):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert "on_roster_host" in src, mod.__name__
    assert "same_host_only" not in Path(links_collector.__file__).read_text(encoding="utf-8"), (
        "links.probe still reads the policy key directly instead of going through the gate")


def test_an_off_host_link_is_recorded_and_never_fetched():
    """The exclusion is evidence. It used to be a `continue`, so nothing on the log could show
    whether the policy had been applied or to what — the same reasoning that makes a robots
    disallow an Observation rather than a silence."""
    from scan.manners import Fetcher
    params = load_params()
    with FixtureServer("passes_all") as base:
        f = Fetcher(params)
        found = [{"href": f"{base}/estimates.csv", "text": "estimates"},
                 {"href": "https://creativecommons.org/publicdomain/zero/1.0/",
                  "text": "CC0"}]
        obs = links_collector.probe(f, "link_probe", "control:x", found, params,
                                    page_url=f"{base}/index.html")
        asked = dict(f.requests)
    off = [o for o in obs if (o.parsed or {}).get("off_host")]
    assert len(off) == 1, [o.target_url for o in obs]
    assert off[0].error_class == "off_host"
    assert (off[0].response or {})["status"] is None
    assert off[0].request["fetched"] is False
    assert not any("creativecommons.org" in h for h in asked), asked
    assert scan_errors.CLASSES["off_host"]["blind"] is False, (
        "an off-host exclusion is the measurement's scope boundary, not a failure to see; "
        "marking it blind would turn a page whose links are all off-host into `error`")


def test_a_latest_pointer_off_host_is_recorded_and_never_fetched():
    """The collector that had no host policy at all. Same gate, same record shape."""
    from scan.manners import Fetcher
    params = load_params()
    with FixtureServer("passes_all") as base:
        f = Fetcher(params)
        out = v2clauses.follow_latest_pointer(
            f, [{"how": "anchor text 'subscribe to govdelivery email'",
                 "url": "https://public.govdelivery.com/accounts/USCENSUS/signup/12426"},
                {"how": "href token", "url": f"{base}/estimates-latest.csv"}],
            params, surface_url=f"{base}/index.html")
        asked = dict(f.requests)
    assert out["pointers_tried"][0]["off_host"] is True
    assert out["pointers_tried"][0]["resolved"] is False
    assert not any("govdelivery" in h for h in asked), asked
    assert out["latest_pointer_resolves"] is True, "the same-host pointer still resolves"


@pytest.mark.slow
def test_no_request_in_the_control_cycle_leaves_the_loopback():
    """§2's third clause, asserted at the socket. `manners.Fetcher.requests` is keyed by host
    and counts what was actually ASKED, which is the only number the manners claim is about."""
    from scan.manners import Fetcher
    from scan.fixtures.server import BIND_HOST
    run_mod = _mod(SCAN / "run.py", "scan_run_v4_hosts")
    params = load_params()
    asked = collections.Counter()
    for fixture in sorted(MODES):
        with FixtureServer(fixture) as base:
            f = Fetcher(params)
            run_mod.run_surface(run_mod.specs(), {"doc_id": f"control:{fixture}",
                                                  "url": f"{base}/index.html"},
                                params, run_mod.CONTROL_FIXTURE_LEGS, f)
            asked.update(f.requests)
    off = sorted(h for h in asked if not h.startswith(BIND_HOST))
    assert not off, f"the control cycle reached {off}: {dict(asked)}"


# ============================================================ §1.4 A8's pointer

def _stored_govdelivery_observation():
    """The real record, out of the real cycle payload. A hand-built stand-in would test the
    rule against my idea of the evidence rather than against the evidence."""
    payload = json.loads((REPO / "state" / "scan_2026-09-07b.json").read_text(encoding="utf-8"))
    for row in payload["observations_detail"]:
        tried = ((row.get("parsed") or {}).get("latest") or {}).get("pointers_tried") or []
        if any("govdelivery" in (t.get("url") or "") for t in tried):
            return Observation(**row)
    raise AssertionError("the govdelivery pointer is not in state/scan_2026-09-07b.json")


def test_the_stored_govdelivery_pointer_would_have_been_credited_and_now_is_not():
    """The near miss, made reachable.

    On the real ACS record A8 never got as far as the pointer: the surface declares no
    `dateModified`, so both `v2` and `v3` stop at the first clause — which is exactly why the
    govdelivery pointer manufactured no verdict in cycle 2 (A8 was 23 fail / 3 error, zero
    pass). *That is luck, not design*, and a test that only replayed the record would certify
    the luck. So the STORED pointer entry — verbatim, `resolved: true`, HTTP 200,
    `public.govdelivery.com` — is put on a surface that DOES declare a date, which is the one
    surface property that stands between that record and a `pass`.

    The stored entry carries no `off_host` flag and no `anchor_text`; neither field existed
    when it was written. So this also pins the property that makes re-judging the past possible
    at all: `RULE-A8-v3` recomputes the host comparison from the URL and reads the anchor out
    of `how`. A rule that needed the collector's new fields could only judge the future.
    """
    params = load_params()
    stored = _stored_govdelivery_observation()
    ptr = next(t for t in (stored.parsed or {})["latest"]["pointers_tried"]
               if "govdelivery" in t["url"])
    assert ptr["resolved"] is True and ptr["status"] == 200
    assert "off_host" not in ptr and "anchor_text" not in ptr, (
        "this record predates both fields; that is the point of the test")
    o = Observation.make(
        "A8", "A8", stored.target_doc_id, stored.target_url, "structured_data", "0.1.0",
        params, {"method": "GET", "url": stored.target_url},
        {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
         "bytes": 1, "elapsed_ms": 1},
        parsed={"keys": ["dateModified"],
                "latest": {"pointers_found": 1, "latest_pointer_resolves": True,
                           "pointers_tried": [ptr]}})
    v2 = judge_rule("RULE-A8-v2", [o], params)
    v3 = judge_rule("RULE-A8-v3", [o], params)
    assert v2.verdict == "pass", (
        "the near miss no longer reproduces under v2; the test has stopped testing anything")
    assert "govdelivery" in v2.reason
    assert v3.verdict == "fail", v3.reason
    assert "no latest-vintage pointer on its own host" in v3.reason
    assert "off-host" in v3.reason or "subscription anchor" in v3.reason


def test_the_real_acs_record_still_fails_on_the_clause_it_failed_on():
    """And the record itself, unchanged: A8 stops at the missing declared date under both
    versions. A correction that also moved a surface it was not about would be re-scoring."""
    params = load_params()
    o = _stored_govdelivery_observation()
    v2, v3 = judge_rule("RULE-A8-v2", [o], params), judge_rule("RULE-A8-v3", [o], params)
    assert v2.verdict == v3.verdict == "fail"
    assert v2.reason == v3.reason == "no declared release or modification date on the surface"


def test_a8_v3_still_passes_a_same_host_pointer_that_resolves():
    """The guard must not swallow the branch it guards. A rule that failed everything would
    pass a test that only checks the govdelivery case."""
    params = load_params()
    o = Observation.make(
        "A8", "A8", "scan-x", "https://x/product", "structured_data", "0.1.0", params,
        {"method": "GET", "url": "https://x/product"},
        {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
         "bytes": 1, "elapsed_ms": 1},
        parsed={"keys": ["dateModified"],
                "latest": {"pointers_found": 1, "latest_pointer_resolves": True,
                           "pointers_tried": [{"how": "href token", "anchor_text": "latest",
                                               "url": "https://x/data-latest.csv",
                                               "status": 200, "resolved": True}]}})
    f = judge_rule("RULE-A8-v3", [o], params)
    assert f.verdict == "pass", f.reason


def test_the_subscription_tokens_are_a_parameter_and_the_test_case_is_in_them():
    p = load_params()["a8_latest"]
    assert "govdelivery" in p["excluded_anchor_tokens"]
    assert "subscribe" in p["excluded_anchor_tokens"]
    assert not set(p["excluded_anchor_tokens"]) & set(p["anchor_tokens"]), (
        "a token that both includes and excludes makes the matcher's answer depend on "
        "evaluation order")


# ============================================================ §1.5 re-judgement

@pytest.fixture(scope="module")
def rederive_mod():
    return _mod(SCAN / "rederive.py", "scan_rederive_v4")


def _rejudged(rederive_mod, cycle: str) -> dict:
    payload = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    return rederive_mod.rejudge(payload, load_params())


def test_a_rejudgement_creates_no_observation_and_cites_the_source_cycles(rederive_mod):
    """The property that makes it a re-judgement rather than a measurement, and the one the
    publish path depends on: every `obs_id` a re-judged Finding cites is already on the log,
    so publishing adds judgements and no evidence."""
    src = json.loads((REPO / "state" / "scan_2026-09-07b.json").read_text(encoding="utf-8"))
    out = _rejudged(rederive_mod, "scan_2026-09-07b")
    assert out["observations_detail"] == []
    assert out["cycle"] == "scan_2026-09-07b_rj1"
    assert out["derived_from"] == "scan_2026-09-07b"
    assert out["derived_from_params_hash"] == src["params_hash"]
    assert out["params_hash"] == params_hash(load_params())
    assert out["requests_total"] == 0
    source_ids = {o["obs_id"] for o in src["observations_detail"]}
    cited = {e for f in out["findings_detail"] for e in f["evidence"]}
    assert cited and cited <= source_ids


def test_a_leg_whose_current_rule_consumes_an_absent_leg_is_not_judged(rederive_mod):
    """Cycle 1 has no `link_probe` leg — it was introduced by harness-v3 — and `RULE-A1-v3` /
    `RULE-A3-v4` read it. Judging them from whatever else sits under `A1` would produce a
    number that looks like a re-judgement and is not one. DD-055: not measured is a reason."""
    out = _rejudged(rederive_mod, "scan_2026-09-07")
    assert set(out["legs_not_judged"]) >= {"A1", "A3", "E5"}
    for leg in ("A1", "A3"):
        assert "link_probe" in out["legs_not_judged"][leg]
        assert leg not in out["legs_judged"]
        assert not any(f["leg"] == leg for f in out["findings_detail"])


def test_e5_is_never_rejudged_and_says_why(rederive_mod):
    """The control set itself changed. Re-judging a four-fixture record against a five-fixture
    expectation would report a change in the INSTRUMENT as a failure of the source cycle."""
    out = _rejudged(rederive_mod, "scan_2026-09-07b")
    assert "E5" in out["legs_not_judged"]
    assert "fifth fixture" in out["legs_not_judged"]["E5"]
    assert not any(f["leg"] == "E5" for f in out["findings_detail"])
    assert out["control_findings_detail"] == []


def test_the_rejudgement_names_the_rules_that_differ_from_the_source(rederive_mod):
    out = _rejudged(rederive_mod, "scan_2026-09-07b")
    assert out["rules_changed_since_source"]["A10"] == {"source": "RULE-A10-v2",
                                                        "current": "RULE-A10-v3"}
    assert out["rules_changed_since_source"]["A8"] == {"source": "RULE-A8-v2",
                                                       "current": "RULE-A8-v3"}
    # Every leg whose rule did NOT move must produce the same verdict on the same evidence:
    # a re-judgement that moved an unrelated leg would be re-scoring, not correcting.
    unchanged = [leg for leg in out["legs_judged"]
                 if leg not in out["rules_changed_since_source"]]
    moved = [m for m in out["verdicts_moved"] if m["leg"] in unchanged]
    assert not moved, moved


def test_the_rejudgement_removes_at_least_the_recorded_false_positive(rederive_mod):
    """The number this task exists to correct. `scan_a10_pass_2026-09-07b` = 17 contains at
    least the EIA surface, whose `pass` rests on a connection nobody observed."""
    out = _rejudged(rederive_mod, "scan_2026-09-07b")
    a10 = [m for m in out["verdicts_moved"] if m["leg"] == "A10"]
    assert any(m["doc_id"] == "scan-eia-flagship-1-open-data"
               and m["from"] == "pass" and m["to"] == "error" for m in a10), a10


# ============================================================ §2 the gate

@pytest.mark.parametrize("cycle", sorted(PRIOR_CYCLES))
def test_every_prior_cycle_re_derives_byte_identically(cycle):
    """§2's second clause. Each payload re-derives under ITS OWN rules and ITS OWN params,
    recovered from git by hash — a cycle measured under `finding_identity: 1` is re-judged
    under 1, or the gate would fail for the one reason that does not matter."""
    payload = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    mod = _mod(SCAN / "rederive.py", f"rederive_{cycle}")
    out = mod.rederive(payload, _params_for(payload))
    assert out["identical"], json.dumps(out, indent=1)[:2000]
    assert out["recorded"] == PRIOR_CYCLES[cycle]


# ============================================================ §3 the re-judged figures

@pytest.mark.slow
def test_every_numeral_in_the_re_judged_figures_resolves_to_an_artifact():
    """§3's figures, through the SAME gate the measured cycle's go through.

    `tests/test_scan_figures.py` is written around one cycle — `params.cycle.name` — so the
    re-judged cycle's F1 and F5 would otherwise be the only published figures nothing checks.
    They are the figures a reader is most likely to quote, because they are the corrected ones.
    The gate is imported rather than reimplemented: a second copy of "does this numeral resolve"
    is a second thing to be wrong, and the copy that drifted would be the one guarding the
    numbers that moved.
    """
    figs_mod = _mod(REPO / "tests" / "test_scan_figures.py", "scan_figures_gate_v4")
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from scan.figures import build, config, load_results
        results = load_results()
    except Exception as exc:                                          # noqa: BLE001
        pytest.skip(f"Neo4j unreachable, re-judged figures unverified: {exc}")
    cycle = "scan_2026-09-07b_rj1"
    if not (REPO / "state" / f"scan_matrix_{cycle.removeprefix('scan_')}.json").is_file():
        pytest.skip(f"{cycle} has not been reported yet")
    figs = build(config(cycle), results, only=("per_leg_pass_rate", "cycle_over_cycle"))
    bad = figs_mod.audit(figs, results, cycle=cycle)
    assert not bad, "\n".join(bad)


def test_the_control_gate_captures_nothing_into_the_committed_evidence_store(monkeypatch):
    """The defect this task shipped and its own hygiene gate caught (RESULT §5.5).

    `run.py::main` redirects `model.EVIDENCE_ROOT` to a per-cycle staging root before
    collecting anything; `rederive.control_gate_record` reached `run_controls` DIRECTLY and
    inherited the default — `corpus/evidence/scan/` — putting 54 fixture blobs into the
    committed store across three command-line runs.

    Driven through a stub runner rather than the five real fixtures, because what has to hold
    is a property of the REDIRECT and not of the fixtures: whatever the gate collects lands
    outside the committed store, and the root is restored afterwards. The fixtures themselves
    are exercised by the control gate above, at their own price.
    """
    from scan import model as _model
    rd = _mod(SCAN / "rederive.py", "scan_rederive_evidence_root")
    committed = _model.EVIDENCE_ROOT
    seen = {}

    class _F:
        rule_id, verdict, reason = "RULE-E5-v2", "pass", "stubbed"

    class _Stub:
        @staticmethod
        def run_controls(params):
            # Whatever a collector stores WHILE the gate runs must not land in the store.
            seen["root"] = _model.EVIDENCE_ROOT
            seen["path"] = _model.store_evidence(b"fixture body")[1]
            return [], _F(), [], True

    monkeypatch.setattr(rd, "run_module", lambda: _Stub)
    out = rd.control_gate_record(load_params())

    assert out["ok"] is True
    assert seen["root"] != committed, "the gate collected into the committed evidence store"
    assert str(committed) not in str(seen["path"]), seen["path"]
    assert _model.EVIDENCE_ROOT == committed, "the gate did not restore the evidence root"
