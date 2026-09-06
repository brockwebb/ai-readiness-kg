"""The scan harness's design properties, asserted rather than intended.

Task `cc_tasks/2026-09-06_harness_scaffold.md`. Four of these tests exist because the property
they check is one a reader would otherwise have to take on trust: that the AUTO tier spends
nothing on models, that no constant hides in a collector, that stored evidence is the evidence
cited, and that a Finding really can be re-derived without re-measuring.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

from scan import load_params                                        # noqa: E402
from scan.fixtures.server import FixtureServer                      # noqa: E402
from scan.model import Finding, Observation, store_evidence         # noqa: E402
from scan.rules import BY_LEG, REGISTRY                             # noqa: E402


def scan_run():
    """`assessment/harness/scan/run.py` loaded BY PATH. A bare `import run` picks up the G1
    harness's own `assessment/harness/run.py`, which is one directory up and on the same
    sys.path — the two runners share a name and nothing but the path disambiguates them."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_run_mod", SCAN / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ zero model spend
#: Any import that would let a collector or rule call a model.
MODEL_MODULES = {"anthropic", "openai", "google", "google.generativeai", "cohere", "mistralai",
                 "ollama", "litellm", "transformers", "langchain", "llama_cpp",
                 "kg.extraction.model_stub", "harness.consumers"}


def _imported_names(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
            out.add(node.module)
    return out


def test_the_auto_tier_cannot_call_a_model():
    """§Spend: zero model calls on the AUTO tier is a DESIGN PROPERTY of the harness, not a
    habit of its operators. A scanner that could call a model would eventually be asked to."""
    offenders = []
    for py in sorted(SCAN.rglob("*.py")):
        hit = _imported_names(py) & MODEL_MODULES
        if hit:
            offenders.append(f"{py.relative_to(REPO)}: {sorted(hit)}")
    assert not offenders, offenders


# ------------------------------------------------------------------ no hidden constants
#: HTTP status codes and the small arithmetic a collector cannot avoid. Anything else numeric
#: belongs in params.yaml, where it can be swept and where its hash rides on the evidence.
ALLOWED_INTS = {0, 1, 2, 3, 200, 400, 404, 410, 429, 500, 503, 999}


def test_no_collector_hides_a_constant():
    """Prior art (Khan 2026, Wintermute wm-20260906-075432-d860df): one unswept truncation
    constant was worth 14 points. A constant inside a collector cannot be swept, cannot be
    versioned, and cannot be stamped on the evidence it shaped."""
    offenders = []
    for py in sorted((SCAN / "collectors").glob("*.py")):
        for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                    and not isinstance(node.value, bool) and node.value not in ALLOWED_INTS:
                offenders.append(f"{py.name}:{node.lineno} -> {node.value}")
    assert not offenders, offenders


def test_every_parameter_the_collectors_read_exists():
    p = load_params()
    for key in ("manners", "crawl", "a1_formats", "a4_crawlers", "a5_discovery", "a6_markup",
                "a8_freshness", "a9_m2m", "a10_soft404", "d1_licence", "d4_catalog",
                "f4_changelog", "g1d_uncertainty", "e5_control"):
        assert key in p, key
    # §2.3: the byte cap must be null unless someone explicitly sets one.
    assert p["manners"]["max_body_bytes"] is None


# ------------------------------------------------------------------ evidence integrity
def test_stored_evidence_hashes_to_the_hash_a_finding_cites(tmp_path):
    """§2.1: whole body retained, no truncation anywhere. The check is not that a file exists
    but that its BYTES hash to the digest the record carries."""
    body = b"x" * 100_000 + b"\xff\xfe not utf-8 \x00"
    digest, path = store_evidence(body, root=tmp_path)
    import hashlib
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    assert Path(path).stat().st_size == len(body)


def test_an_observation_id_is_derived_from_what_was_observed():
    """Two observations of the same thing under the same params share an id; change any of
    them and the id moves. That is what makes a re-run idempotent."""
    kw = dict(spec_code="A4", leg="A4", target_doc_id="d", target_url="http://x/robots.txt",
              collector="robots", collector_version="1", params={"a": 1},
              request={}, response={"body_sha256": "abc"})
    a = Observation.make(**kw)
    b = Observation.make(**kw)
    assert a.obs_id == b.obs_id
    assert Observation.make(**{**kw, "params": {"a": 2}}).obs_id != a.obs_id
    assert Observation.make(**{**kw, "response": {"body_sha256": "def"}}).obs_id != a.obs_id


def test_error_class_and_verdict_are_closed_sets():
    with pytest.raises(ValueError):
        Observation.make(spec_code="A", leg="A", target_doc_id="d", target_url="u",
                         collector="c", collector_version="1", params={}, request={},
                         response={}, error_class="something_new")
    with pytest.raises(ValueError):
        Finding.make(rule_id="R", rule_version="v1", leg="A", target_doc_id="d",
                     verdict="probably", evidence=[], reason="", params={})


# ------------------------------------------------------------------ rules are pure
def test_no_rule_reaches_the_network_a_clock_or_the_filesystem():
    """§3: a rule takes everything it may read and returns everything it decides. The property
    is only real if the code cannot reach anything else."""
    banned = {"httpx", "requests", "urllib", "socket", "pathlib", "os", "time", "datetime",
              "random", "subprocess"}
    offenders = []
    for py in sorted((SCAN / "rules").glob("*.py")):
        hit = _imported_names(py) & banned
        if hit:
            offenders.append(f"{py.name}: {sorted(hit)}")
    assert not offenders, offenders


def test_every_rule_covers_a_leg_that_has_a_measurement_spec():
    g = json.loads((REPO / "framework" / "ai_readiness_framework.json").read_text(encoding="utf-8"))
    legs = {n["properties"]["leg"] for n in g["nodes"] if "MeasurementSpec" in n["labels"]}
    assert set(BY_LEG) <= legs, sorted(set(BY_LEG) - legs)
    assert len(REGISTRY) == len(BY_LEG) == 16


def test_the_framework_records_the_rule_each_leg_is_judged_by():
    g = json.loads((REPO / "framework" / "ai_readiness_framework.json").read_text(encoding="utf-8"))
    for n in g["nodes"]:
        p = n["properties"]
        if "MeasurementSpec" in n["labels"] and p["leg"] in BY_LEG:
            assert p["rule_id"] == BY_LEG[p["leg"]], p["leg"]


# ------------------------------------------------------------------ the two gates
@pytest.mark.parametrize("fixture,expected", [("passes_all", "pass"), ("fails_all", "fail")])
def test_every_rule_returns_its_expected_verdict_on_the_control_fixture(fixture, expected):
    """§4's positive control, and the reason it is a gate rather than a report: it caught three
    real rule defects on its first run — A8 passing on a bare HTTP Last-Modified header, A9
    accepting a soft-404 HTML shell as an agent surface, and B3 accepting the product page as
    its own methodology document."""
    from scan.manners import Fetcher
    from scan.run import CONTROL_LEGS, run_surface, specs
    params = load_params()
    with FixtureServer(fixture) as base:
        _, findings = run_surface(specs(), {"doc_id": f"control:{fixture}",
                                            "url": f"{base}/index.html"},
                                  params, CONTROL_LEGS, Fetcher(params))
    bad = {f.leg: f.verdict for f in findings if f.verdict != expected}
    assert not bad, bad
    assert len(findings) == len(CONTROL_LEGS)


def test_findings_re_derive_byte_identically_from_stored_observations():
    """§3's re-derivation gate on the smoke-run output: delete every Finding, re-judge from
    Observations alone, demand identity. Meaningful only because a Finding's id is derived
    from (rule, version, sorted obs ids, params hash) rather than assigned."""
    src = REPO / "state" / "scan_smoke_2026-09-06.json"
    if not src.is_file():
        pytest.skip("no smoke-run output on disk")
    from scan.rederive import rederive
    res = rederive(json.loads(src.read_text(encoding="utf-8")), load_params())
    assert res["identical"], res


def test_a_rule_change_moves_the_finding_id_so_history_is_never_silently_rescored():
    """The other half of §6b.5: thresholds may change and history may be re-scored — but the
    re-scored finding must be a DIFFERENT record, not the old one mutated."""
    a = Finding.make(rule_id="RULE-A4", rule_version="v1", leg="A4", target_doc_id="d",
                     verdict="pass", evidence=["obs_1"], reason="r", params={"t": 1})
    b = Finding.make(rule_id="RULE-A4", rule_version="v2", leg="A4", target_doc_id="d",
                     verdict="pass", evidence=["obs_1"], reason="r", params={"t": 1})
    c = Finding.make(rule_id="RULE-A4", rule_version="v1", leg="A4", target_doc_id="d",
                     verdict="pass", evidence=["obs_1"], reason="r", params={"t": 2})
    assert len({a.finding_id, b.finding_id, c.finding_id}) == 3


# ------------------------------------------------------------------ manners
def test_the_scanner_obeys_the_file_it_measures():
    """RFC 9309. The carve-out is explicit and narrow: the paths that ARE the object of
    measurement are always fetched, and everything else honours the disallow."""
    params = load_params()
    from scan.manners import Fetcher
    with FixtureServer("passes_all") as base:
        f = Fetcher(params)
        assert f.allowed(f"{base}/robots.txt")
        assert f.allowed(f"{base}/index.html")
    always = params["manners"]["always_fetch_paths"]
    assert "/robots.txt" in always and "/data.json" in always
    assert params["manners"]["requests_per_second_per_host"] <= 1.0
    assert "ai-readiness-kg-scanner" in params["manners"]["user_agent"]


def test_a_robots_disallow_is_recorded_as_evidence_not_as_an_absence():
    """§2.4: a refusal is a fact about the surface. Dropping it would make a blocked product
    indistinguishable from one that was never probed."""
    from scan.collectors import http as http_collector

    class _Deny:
        def allowed(self, url): return False
    obs = http_collector.fetch(_Deny(), "A1", "d", "http://example.invalid/x", load_params())
    assert len(obs) == 1 and obs[0].error_class == "robots_disallowed"


# --------------------------------------------- a host that refuses us is not a product failure
def _obs(leg: str, status: int, url: str = "https://www.bls.gov/x"):
    return Observation.make(spec_code=leg, leg=leg, target_doc_id="bls-x", target_url=url,
                            collector="http", collector_version="1", params={}, request={},
                            response={"status": status, "bytes": 0, "body_sha256": ""},
                            parsed={}, error_class="http_4xx")


@pytest.mark.parametrize("leg", sorted(BY_LEG))
def test_a_host_that_refuses_every_request_is_an_error_not_a_fail(leg):
    """`www.bls.gov` answered 403 to all 60 requests in the first smoke run and the harness
    scored both BLS surfaces `fail` on all 15 legs — 30 published verdicts asserting that a
    federal statistical agency lacks properties nobody was ever allowed to look for.

    §3 is explicit that `error` means the COLLECTOR could not observe and never that the
    product failed, and `only_errors` was reading `error_class` alone. `http_4xx` covers both
    404 (the path is not served — a real observation of absence) and 403/401/429 (the host
    refused this client — no observation at all), so the class cannot separate them and the
    status has to.
    """
    if leg == "E5":
        pytest.skip("E5 judges the cycle's controls, not a surface")
    params = load_params()
    refused = [_obs(leg, s) for s in params["manners"]["unobservable_statuses"]]
    f = REGISTRY[BY_LEG[leg]].judge(refused, params)
    assert f.verdict == "error", f.reason


@pytest.mark.parametrize("leg", sorted(BY_LEG))
def test_a_404_is_still_a_real_observation_of_absence(leg):
    """The other half of the same rule, and the reason the fix is a status list rather than
    folding `http_4xx` into the blind set. A probed path that is not served IS the
    measurement; turning every 404 into `error` would leave the harness unable to report
    absence at all, which is most of what it is for.

    Asserted on the guard rather than on each rule's verdict: a rule may still answer `error`
    to a single 404 for a reason of its own (A10 needs a valid/invalid route PAIR and one
    observation is not a pair), and that is its contract, not this guard's.
    """
    from scan.rules import _common
    params = load_params()
    assert not _common.only_errors([_obs(leg, 404)], params)
    assert _common.only_errors([_obs(leg, 403)], params)


def test_a_mixed_refusal_is_not_an_error():
    """One 403 among answered probes is not a blind cycle — the surface WAS observed, just not
    at that path. `www.census.gov` returned 26 403s alongside 10 200s and 26 404s, and calling
    that whole surface unobservable would discard real evidence."""
    from scan.rules import _common
    params = load_params()
    assert not _common.only_errors([_obs("A9", 403), _obs("A9", 200)], params)


def test_the_cycles_own_validity_verdict_is_on_the_record():
    """E5's Finding is the cycle's validity verdict and it was not being written.

    `rules_built` said 16 while the projected graph held 15 `:Rule` nodes, because
    `RULE-E5-v1` produced a Finding that lived only in `run.py`'s locals. DD-019 says a cycle
    with zero fired controls is INVALID; the evidence that a given cycle WAS valid has to be
    as durable as the findings it validates, or the claim rests on a log line.
    """
    run_mod = scan_run()
    params = load_params()
    cf, e5, control_obs, ok = run_mod.run_controls(params)
    assert ok and e5.rule_id == "RULE-E5-v1"
    e5_obs = [o for o in control_obs if o.leg == "E5"]
    assert len(e5_obs) == 2, "one E5 Observation per fixture"
    assert set(e5.evidence) == {o.obs_id for o in e5_obs}
    # And the fixture evidence the per-rule control Findings rest on is retained alongside it,
    # or those Findings could never be re-derived.
    assert len(control_obs) > len(e5_obs)


def test_merging_controls_replaces_them_rather_than_accumulating(tmp_path):
    """The fixture server binds an ephemeral port, which leaks into every control
    `target_url` and so into every derived control id: a second control run yields records
    that are NEW, not equal. The first version of `--merge-controls` unioned them and produced
    a payload claiming 61 control findings for a single cycle."""
    run_mod = scan_run()
    params = load_params()
    from scan.model import params_hash as ph
    payload = tmp_path / "cycle.json"
    payload.write_text(json.dumps({
        "params_hash": ph(params), "control_findings": 0,
        "control_findings_detail": [], "observations_detail": []}), encoding="utf-8")
    assert run_mod.merge_controls(payload, params) == 0
    first = json.loads(payload.read_text(encoding="utf-8"))
    assert run_mod.merge_controls(payload, params) == 0
    second = json.loads(payload.read_text(encoding="utf-8"))
    assert first["control_findings"] == second["control_findings"] == len(BY_LEG) * 2 - 1
    assert len([o for o in second["observations_detail"]
                if o["collector"] == "control_fixture"]) == 2


def test_merging_controls_refuses_across_a_params_change(tmp_path):
    """Folding control records derived under one parameter set into a cycle measured under
    another leaves a payload whose parts disagree about the constants that shaped them."""
    run_mod = scan_run()
    payload = tmp_path / "cycle.json"
    payload.write_text(json.dumps({"params_hash": "not-the-current-one"}), encoding="utf-8")
    assert run_mod.merge_controls(payload, load_params()) == 2


def test_the_re_derivation_gate_covers_the_control_findings_too():
    """The gate started out comparing only the 255 surface Findings. The control Findings are
    the ones whose determinism matters most — they are what licenses the cycle — and their
    evidence was being thrown away, so they could not be checked at all. Retaining the fixture
    Observations brought all 31 into the gate, at which point E5 exposed a second bug: it
    judges the CYCLE, so grouping its observations per fixture re-derived two E5 Findings
    where the cycle recorded one.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_rederive_mod", SCAN / "rederive.py")
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    payload = json.loads((REPO / "state" / "scan_smoke_2026-09-06.json").read_text(encoding="utf-8"))
    assert payload["control_findings_detail"], "the cycle recorded no control findings"
    assert any(o["target_doc_id"].startswith("control:")
               for o in payload["observations_detail"]), "fixture evidence was not retained"
    out = rd.rederive(payload, load_params())
    assert out["identical"], out
    assert out["recorded"] == len(payload["findings_detail"]) + len(payload["control_findings_detail"])
    assert sum(1 for f in payload["control_findings_detail"]
               if f["rule_id"] == "RULE-E5-v1") == 1, "E5 judges the cycle, once"
