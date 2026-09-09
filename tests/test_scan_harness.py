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
from scan.rules import BY_LEG, CURRENT, REGISTRY                   # noqa: E402


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
    for key in ("manners", "crawl", "probes", "a1_formats", "a4_crawlers", "a5_discovery",
                "a6_markup", "a8_freshness", "a9_m2m", "a10_soft404", "d1_licence",
                "d4_catalog", "f4_changelog", "g1d_uncertainty", "e5_control"):
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
    # 16 legs; REGISTRY holds every version ever shipped for them, which is 16 + one v2 per
    # leg the 2026-09-06 conformance review found deviating. It may only grow: a pruned entry
    # is a stored Finding that can no longer be re-derived (DD-053 §6).
    from scan.rules import CANDIDATE_LEGS, FRAMEWORK_LEGS, GENERATIONS
    assert len(FRAMEWORK_LEGS) == 16, "16 framework legs; a candidate is not one of them"
    assert len(BY_LEG) == len(FRAMEWORK_LEGS) + len(CANDIDATE_LEGS)
    # Summed over the GENERATIONS list rather than over four names: a fifth generation used to
    # mean editing this arithmetic, and the version of it that was forgotten would be the one
    # that mattered. V4 (`RULE-A1-v3`, `RULE-A3-v4`) is what found that.
    assert len(REGISTRY) == sum(len(g) for g in GENERATIONS) + len(CANDIDATE_LEGS)
    assert {REGISTRY[r].LEG for r in REGISTRY} == set(BY_LEG)


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


def _fresh_control_cycle(tmp_path):
    """Run the control gate now and return its payload.

    Pointed at a payload ON DISK, this test rots: `params.yaml` changes, every derived id moves
    with it, and the gate correctly reports `params_changed` — which reads as a failure when it
    is the guard working. Running the cycle makes the test self-contained and always current,
    which is affordable precisely because the controls are local and free. That property is
    also what `run.py --merge-controls` exists for.
    """
    run_mod = scan_run()
    params = load_params()
    cf, e5, control_obs, ok = run_mod.run_controls(params)
    assert ok, e5.reason
    return {"params_hash": __import__("importlib").import_module("scan.model").params_hash(params),
            "findings_detail": [],
            "control_findings_detail": [f.to_dict() for f in cf] + [e5.to_dict()],
            "observations_detail": [o.to_dict() for o in control_obs]}, params


def test_findings_re_derive_byte_identically_from_stored_observations(tmp_path):
    """§3's re-derivation gate: delete every Finding, re-judge from Observations alone, demand
    identity. Meaningful only because a Finding's id is derived from (rule, version, sorted obs
    ids, params hash) rather than assigned."""
    from scan.rederive import rederive
    payload, params = _fresh_control_cycle(tmp_path)
    res = rederive(payload, params)
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
    from scan.rules import CURRENT
    assert ok and e5.rule_id == CURRENT["E5"]
    e5_obs = [o for o in control_obs if o.leg == "E5"]
    # One per fixture, counted from the pre-registered table rather than from a literal `2`:
    # `cc_tasks/2026-09-07_scan_harness_v3.md` §1.4 added a third and a fourth fixture, and a
    # hard-coded count is a test that has to be edited every time the control set grows.
    n_fixtures = len(params["e5_control"]["expected_verdicts"])
    assert len(e5_obs) == n_fixtures, "one E5 Observation per fixture"
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
    # One Finding per control leg per fixture, plus E5's own — derived, not a literal, for the
    # reason above. `CONTROL_FIXTURE_LEGS` is the fifteen product legs plus the candidate; E5
    # judges the CYCLE and has no per-fixture Finding.
    n_fixtures = len(params["e5_control"]["expected_verdicts"])
    expected = len(run_mod.CONTROL_FIXTURE_LEGS) * n_fixtures + 1
    assert first["control_findings"] == second["control_findings"] == expected
    assert all(f["rule_id"] in REGISTRY for f in second["control_findings_detail"])
    assert len([o for o in second["observations_detail"]
                if o["collector"] == "control_fixture"]) == n_fixtures


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
    payload, params = _fresh_control_cycle(None)
    assert payload["control_findings_detail"], "the cycle recorded no control findings"
    assert any(o["target_doc_id"].startswith("control:")
               for o in payload["observations_detail"]), "fixture evidence was not retained"
    out = rd.rederive(payload, params)
    assert out["identical"], out
    assert out["recorded"] == len(payload["findings_detail"]) + len(payload["control_findings_detail"])
    assert sum(1 for f in payload["control_findings_detail"]
               if f["rule_id"].startswith("RULE-E5-")) == 1, "E5 judges the cycle, once"


# ------------------------------------------------- two rule versions, one history
def test_history_re_derives_under_the_rule_that_made_it_not_the_current_one():
    """The property the versioning exists for. Twelve legs moved to `v2` on 2026-09-06; the
    286 Findings recorded under `v1` must still come back byte-identical when re-judged, or
    the harness has silently re-scored history under rules that did not exist when the
    surfaces were measured.

    The `v1` cycle was measured under the `v1` params, so the gate is run with them — read
    from git rather than reconstructed, because a hand-written approximation of an old
    parameter set would make this test pass for the wrong reason.
    """
    import importlib.util
    import subprocess
    import yaml
    from scan.model import params_hash
    payload_path = REPO / "state" / "scan_smoke_2026-09-06.json"
    if not payload_path.is_file():
        pytest.skip("no v1 cycle payload on disk")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    # Find the commit whose params.yaml actually HASHES to the one this cycle ran under. The
    # first version of this test read `HEAD:params.yaml` and skipped when it did not match —
    # so the moment params moved on, the test silently stopped testing anything. A gate that
    # skips itself when the thing it guards changes is not a gate.
    revs = subprocess.run(
        ["git", "log", "--format=%H", "--", "assessment/harness/scan/params.yaml"],
        capture_output=True, text=True, cwd=str(REPO)).stdout.split()
    wanted = None
    for rev in revs:
        txt = subprocess.run(["git", "show", f"{rev}:assessment/harness/scan/params.yaml"],
                             capture_output=True, text=True, cwd=str(REPO)).stdout
        if txt.strip() and params_hash(yaml.safe_load(txt)) == payload["params_hash"]:
            wanted = yaml.safe_load(txt)
            break
    assert wanted is not None, (
        f"no commit of params.yaml hashes to {payload['params_hash'][:12]}…; the parameters "
        f"this cycle was measured under are not recoverable, so its Findings can never be "
        f"re-derived")
    spec = importlib.util.spec_from_file_location("scan_rederive_hist", SCAN / "rederive.py")
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    out = rd.rederive(payload, wanted)
    assert out["identical"], out
    recorded_versions = {f["rule_id"] for f in
                         payload["findings_detail"] + payload["control_findings_detail"]}
    assert any(r.endswith("-v1") for r in recorded_versions)


def test_every_shipped_rule_version_stays_in_the_registry():
    """A pruned REGISTRY entry is a stored Finding that can no longer be re-derived. CURRENT
    may move; REGISTRY may only grow."""
    from scan.rules import CURRENT, GENERATIONS, REGISTRY, parse_rule_id
    assert set(CURRENT.values()) <= set(REGISTRY)
    for gen in GENERATIONS:
        assert {m.RULE_ID for m in gen} <= set(REGISTRY)
    # Each generation supersedes the one before for the same leg, never the reverse — checked
    # over the GENERATIONS list rather than over named pairs, so a new one cannot slip past by
    # simply not being mentioned. A generation's rule need not carry that generation's version
    # NUMBER: `RULE-A3-v4` and `RULE-A1-v3` ship together in V4 because A3 had one more
    # ancestor than A1. What must hold is that a later generation's rule for a leg outranks
    # every earlier one, and that the highest-ranked is the one CURRENT points at.
    seen: dict = {}
    for gen in GENERATIONS:
        for m in gen:
            prior = seen.get(m.LEG)
            v = int(parse_rule_id(m.RULE_ID)["version"].lstrip("v"))
            assert prior is None or v > prior, f"{m.LEG}: {m.RULE_ID} does not outrank v{prior}"
            seen[m.LEG] = v
    highest = {}
    for gen in GENERATIONS:
        for m in gen:
            highest[m.LEG] = m.RULE_ID
    for leg, rule_id in highest.items():
        assert CURRENT[leg] == rule_id, f"{leg} is CURRENT on {CURRENT[leg]}, not {rule_id}"


def test_a_v2_rule_is_a_new_module_and_v1_is_untouched():
    """`deviates` -> write v2, never edit v1 (task §2). A v1 module whose bytes changed after
    Findings were recorded under it would make the re-derivation gate a tautology."""
    import subprocess
    from scan.rules import V1
    for m in V1:
        rel = Path(m.__file__).resolve().relative_to(REPO)
        r = subprocess.run(["git", "diff", "--stat", "HEAD", "--", str(rel)],
                           capture_output=True, text=True, cwd=str(REPO))
        assert not r.stdout.strip(), f"{rel} was edited: {r.stdout.strip()}"


# ------------------------------------------------------- A12: the candidate host-level rule
def _a12_obs(robots_status, present, self_allowed, probe_status, params):
    """The (robots, probe) pair A12 judges, built directly. The branch that matters most —
    permitted in the file, refused at the edge — is NOT reachable from either control fixture,
    because `fails_all` models a content-poor host and not an access-refusing one. Constructing
    it here is the honest substitute; a fixture that modelled it is named as the residual in
    the RESULT."""
    robots = Observation.make(
        "A12", "A12", "host:x", "https://x/robots.txt", "robots", "1", params,
        {"method": "GET", "url": "https://x/robots.txt"},
        {"status": robots_status, "headers": {}, "body_sha256": None, "body_path": None,
         "bytes": 1, "elapsed_ms": 1},
        parsed={"present": present, "robots_status": robots_status,
                "self_ua": params["manners"]["user_agent"], "self_ua_allowed": self_allowed,
                "probe_url": "https://x/product", "per_ua": {}},
        error_class="http_4xx" if (robots_status or 0) >= 400 else None)
    probe = Observation.make(
        "A12", "A12", "host:x", "https://x/product", "http", "1", params,
        {"method": "GET", "url": "https://x/product"},
        {"status": probe_status, "headers": {}, "body_sha256": None, "body_path": None,
         "bytes": 1, "elapsed_ms": 1},
        parsed={"probe": "a12_target"},
        error_class="http_4xx" if (probe_status or 0) >= 400 else None)
    return [robots, probe]


def test_a12_fails_when_robots_permits_and_the_host_refuses():
    """The incoherence A12 exists to name, and the branch no control fixture reaches."""
    from scan.rules import REGISTRY
    params = load_params()
    for status in params["manners"]["unobservable_statuses"]:
        f = REGISTRY["RULE-A12-v1"].judge(
            _a12_obs(200, True, True, status, params), params)
        assert f.verdict == "fail", (status, f.reason)
        assert "disagree" in f.reason


def test_a12_is_not_applicable_when_robots_disallows_us():
    """A host obeyed is not a host in conflict with itself — that reading is A4's."""
    from scan.rules import REGISTRY
    params = load_params()
    f = REGISTRY["RULE-A12-v1"].judge(_a12_obs(200, True, False, 200, params), params)
    assert f.verdict == "not_applicable", f.reason


def test_a12_passes_on_a_404_because_a_404_is_not_a_refusal():
    """A12 asks whether we were turned away, not whether the path exists. Scoring a 404 as
    incoherence would make A12 a second, worse A9."""
    from scan.rules import REGISTRY
    params = load_params()
    for status in (200, 301, 404):
        f = REGISTRY["RULE-A12-v1"].judge(_a12_obs(200, True, True, status, params), params)
        assert f.verdict == "pass", (status, f.reason)


def test_a12_fails_when_the_host_refuses_robots_txt_itself():
    """`www.bls.gov` does exactly this. A rule that only asked "does robots permit?" would
    have to answer "unknown" and fall through."""
    from scan.rules import REGISTRY
    params = load_params()
    f = REGISTRY["RULE-A12-v1"].judge(_a12_obs(403, False, None, 403, params), params)
    assert f.verdict == "fail" and "/robots.txt itself" in f.reason


def test_a12_findings_are_never_counted_in_a_fraction():
    """DD-054: a candidate is reported, not adopted. The exclusion is mechanical — the
    reporting layer reads `CANDIDATE_LEGS`, never a remembered code."""
    from scan.rules import CANDIDATE_LEGS, CURRENT, FRAMEWORK_LEGS
    assert "A12" in CANDIDATE_LEGS
    assert "A12" not in FRAMEWORK_LEGS
    assert set(FRAMEWORK_LEGS) | CANDIDATE_LEGS == set(CURRENT)


def test_a_host_surface_is_judged_only_by_host_legs():
    """A well-known set is not a document: no product page, no downloads, no methodology.
    Running the fifteen product legs against one would manufacture fifteen `fail` verdicts per
    host about properties a host is not supposed to have."""
    run_mod = scan_run()
    tgts = run_mod.targets(load_params())
    hosts = [t for t in tgts if t["surface_kind"] == "well_known"]
    docs = [t for t in tgts if t["surface_kind"] != "well_known"]
    assert hosts and docs
    assert all(t["legs"] == list(run_mod.HOST_LEGS) for t in hosts)
    assert all("A12" not in t["legs"] for t in docs)


def test_every_target_either_has_a_document_or_an_id_the_projection_knows():
    """`admitted` means "there is a `:Document` to hang `OBSERVED_ON` on", and the checkable
    property is that every target has one OR is synthetic under an id kind the projection
    recognises. Nothing may be neither.

    This clause used to read `all(t["admitted"] for t in docs)` and was true only because the
    synthetic `host:` row was the sole non-document surface and carried `surface_kind ==
    "well_known"`. Targets v2 added `home:` and `machine:` rows
    (`cc_tasks/2026-09-08_scan_run_3b.md` decision 1) — synthetic, documentless by design, and
    not well-known — so the old clause read a correct id scheme as an admission failure.

    Asserted against `publish.SYNTHETIC_PREFIXES` itself, because the id scheme and the
    projection's list of what it recognises going out of step is not hypothetical: they did,
    and 957 observations of ordinary host surfaces were counted as
    `observed_on_missing_document` until the list caught up (that RESULT §1).
    """
    from scan.publish import CONTROL_PREFIX, SYNTHETIC_PREFIXES
    run_mod = scan_run()
    known = tuple(SYNTHETIC_PREFIXES) + (CONTROL_PREFIX,)
    unplaceable = [t["doc_id"] for t in run_mod.targets(load_params())
                   if not t["admitted"] and not str(t["doc_id"]).startswith(known)]
    assert not unplaceable, (
        f"target(s) with neither a :Document nor an id the projection places: {unplaceable}")
    synthetic = [t for t in run_mod.targets(load_params())
                 if str(t["doc_id"]).startswith(tuple(SYNTHETIC_PREFIXES))]
    assert synthetic and not any(t["admitted"] for t in synthetic), (
        "a synthetic id claims to be admitted; `admitted` is what says a :Document exists")


# ------------------------------------------------- the guard that stopped a live cycle
def test_a_present_but_none_status_never_raises():
    """`.get("status", 999)` looks safe and is not: `status` is always PRESENT on an
    Observation and holds `None` whenever nothing was fetched — a robots disallow, a DNS
    failure, a timeout — so the default never fires and the comparison raises. It stopped the
    2026-09-07 cycle 20 minutes in, on a surface whose links include robots-disallowed paths.

    Asserted for EVERY current rule, not just the four that had the bug: the shape of the
    input is what makes it a trap, and any rule may meet it.
    """
    from scan.rules import CURRENT, REGISTRY
    params = load_params()
    for leg, rule_id in sorted(CURRENT.items()):
        blind = Observation.make(
            leg, leg, "d", "https://x/p", "http", "1", params,
            {"method": "GET", "url": "https://x/p"},
            {"status": None, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 0},
            parsed={"probe": "link"}, error_class="robots_disallowed")
        served = Observation.make(
            leg, leg, "d", "https://x/q", "http", "1", params,
            {"method": "GET", "url": "https://x/q"},
            {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 5, "elapsed_ms": 1},
            parsed={"probe": "link", "content_type": "text/html"}, error_class=None)
        f = REGISTRY[rule_id].judge([blind, served], params)   # must not raise
        assert f.verdict in ("pass", "fail", "not_applicable", "error"), (leg, f.verdict)


def test_served_fires_on_a_missing_key_and_a_none_value_alike():
    from scan.rules import _common
    params = load_params()

    class _O:
        def __init__(self, response):
            self.response = response

    assert _common.served(_O({"status": 200}))
    assert _common.served(_O({"status": 301}))
    assert not _common.served(_O({"status": 404}))
    assert not _common.served(_O({"status": None})), "the bug: a present key holding None"
    assert not _common.served(_O({})), "and a missing key"
    assert not _common.served(_O(None))


def test_a_v3_leaves_its_v2_byte_identical():
    """Same rule as v2-over-v1: a corrected module is a NEW module. A v2 whose bytes changed
    after Findings were recorded under it would make the re-derivation gate a tautology."""
    import subprocess
    from scan.rules import V2
    for m in V2:
        rel = Path(m.__file__).resolve().relative_to(REPO)
        r = subprocess.run(["git", "diff", "--stat", "HEAD", "--", str(rel)],
                           capture_output=True, text=True, cwd=str(REPO))
        assert not r.stdout.strip(), f"{rel} was edited: {r.stdout.strip()}"


def test_parse_rule_id_derives_indicator_and_version_for_every_shipped_rule():
    """`Rule.version` and `Rule -[:MEASURES]-> AssessmentIndicator` are DERIVED from the rule
    id (`cc_tasks/2026-09-07_framework_projection_repair.md` §2). The property that makes a
    derivation safe is that it holds for every id that exists, so assert it over REGISTRY
    rather than over a hand-picked four."""
    import json as _json
    from scan.rules import CURRENT, MODULES, parse_rule_id

    codes = {n["properties"]["code"] for n in
             _json.loads((REPO / "framework" / "ai_readiness_framework.json")
                         .read_text(encoding="utf-8"))["nodes"]
             if n["labels"][0] == "AssessmentIndicator"}
    for m in MODULES:
        p = parse_rule_id(m.RULE_ID)
        assert p["version"] == m.RULE_ID.rsplit("-", 1)[1]
        assert p["indicator_code"] in codes, f"{m.RULE_ID} -> {p['indicator_code']}, not a code"
        # the leg keeps the qualifier the indicator code drops
        assert m.LEG.startswith(p["indicator_code"])
    assert parse_rule_id("RULE-A11-declared-v2")["indicator_code"] == "A11"
    assert parse_rule_id("RULE-A11-declared-v2")["qualifier"] == "declared"
    assert parse_rule_id("RULE-G1-D-v1")["indicator_code"] == "G1-D"
    assert parse_rule_id("RULE-A12-v1") == {"rule_id": "RULE-A12-v1", "indicator_code": "A12",
                                            "qualifier": None, "version": "v1"}
    assert set(CURRENT.values()) <= {m.RULE_ID for m in MODULES}


@pytest.mark.parametrize("bad", ["A1-v1", "RULE-A1", "RULE-a1-v1", "RULE-A1-v", "RULE--v1",
                                 "RULE-H1-v1", "RULE-A1-v1-extra"])
def test_parse_rule_id_refuses_what_it_cannot_derive(bad):
    """Loud, not lenient: a rule id this cannot parse would otherwise become a Rule node with
    no indicator and no version, which is exactly the state this task is repairing."""
    from scan.rules import parse_rule_id
    with pytest.raises(ValueError):
        parse_rule_id(bad)
