"""What the first scan cycle taught, asserted before the second one runs.

`cc_tasks/2026-09-07_scan_harness_v3.md` §2 — the one gate of that task. Six properties, each
of which the 2026-09-07 cycle showed was true by nobody's doing:

1. **A Finding's id scheme is a parameter, and raising it moves no stored id.** History
   re-derives under its own params, which the gate recovers from git.
2. **Every failure has a name.** The closed set had no member for a connection reset, so 92
   observations were filed as `dns`; `unknown` is now the only remainder and it is counted.
3. **One probe per object per cycle.** A1 and A3 HEADed the same 25 links independently — 559
   duplicate requests in one cycle. Asserted here from the fixture server's own request log,
   which is the only evidence of what was actually fetched.
4. **A control that fails is what makes a zero mean something.** Four fixtures, not two: the
   two branches that mattered most in the first cycle (a host that refuses an identified
   client, a host that resets the connection) had no control at all.
5. **A surface admitted to be measured is not gapped for being thin.**
6. **A per-cycle Result name carries its cycle** (DD-056), refused before anything is written.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from support.sourcescan import strip_prose

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from scan import errors, load_params                                # noqa: E402
from scan.clock import VirtualClock                                 # noqa: E402
from scan.fixtures.server import MODES, FixtureServer               # noqa: E402
from scan.model import Finding, params_hash                         # noqa: E402
from scan.rules import (CURRENT, GENERATIONS, REGISTRY, SHARED_LEGS,  # noqa: E402
                        _common, consumes, parse_rule_id)

import cycle_results                                                # noqa: E402

PARAMS_REL = "assessment/harness/scan/params.yaml"

#: The three cycles whose Findings are on the log, with what each recorded. Literals, because a
#: gate that reads its expectation out of the artifact under test can only ever pass.
PRIOR_CYCLES = {
    "scan_smoke_2026-09-06": 286,
    "scan_controls_2026-09-06": 33,
    "scan_2026-09-07": 437,
}


def _rederive_module():
    """`rederive.py` by path — `assessment/harness/` holds a second `run.py`, and only the
    path disambiguates the two."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_rederive_v3", SCAN / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _params_for(payload: dict) -> dict:
    """The parameter set this cycle was MEASURED under, recovered from git by hash.

    Never reconstructed by hand: an approximation of an old parameter set would make the gate
    pass for the wrong reason. This is the same recovery `test_scan_harness.py`'s single-cycle
    history gate performs, lifted here so it covers all three.
    """
    revs = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_REL],
                          capture_output=True, text=True, cwd=str(REPO)).stdout.split()
    for rev in revs:
        txt = subprocess.run(["git", "show", f"{rev}:{PARAMS_REL}"],
                             capture_output=True, text=True, cwd=str(REPO)).stdout
        if txt.strip() and params_hash(yaml.safe_load(txt)) == payload["params_hash"]:
            return yaml.safe_load(txt)
    raise AssertionError(
        f"no commit of {PARAMS_REL} hashes to {payload['params_hash'][:12]}…; the parameters "
        f"this cycle was measured under are not recoverable, so its Findings can never be "
        f"re-derived")


# ------------------------------------------------------ §1.1 the id scheme is a parameter
def test_finding_identity_1_stamps_the_constant_and_2_stamps_the_rule_id():
    assert _common.rule_version("RULE-A3-v4", {"finding_identity": 1}) == "v1"
    assert _common.rule_version("RULE-A3-v4", {"finding_identity": 2}) == "v4"
    assert _common.rule_version("RULE-A1-v3", {"finding_identity": 2}) == "v3"
    # Absent means 1: every stored Finding was made under a params set that predates the key,
    # and it must re-derive byte-identically.
    assert _common.rule_version("RULE-A3-v4", {}) == "v1"
    with pytest.raises(ValueError):
        _common.rule_version("RULE-A3-v4", {"finding_identity": 99})


def test_the_id_scheme_changes_the_id_which_is_why_it_is_a_parameter():
    """Both schemes over the same evidence, so the difference is the scheme and nothing else.

    If these ids were equal the parameter would be decorative; because they differ, raising it
    is a re-identification — which is exactly why it is versioned data that history carries
    with it rather than an edit to `_common.RULE_VERSION`.
    """
    base = {"cycle": {"name": "t"}, "manners": {"unobservable_statuses": []}}
    ids = set()
    for scheme in (1, 2):
        p = dict(base, finding_identity=scheme)
        ids.add(Finding.make(rule_id="RULE-A3-v4", rule_version=_common.rule_version("RULE-A3-v4", p),
                             leg="A3", target_doc_id="d", verdict="pass", evidence=["obs_x"],
                             reason="r", params=p).finding_id)
    assert len(ids) == 2


@pytest.mark.parametrize("cycle", sorted(PRIOR_CYCLES))
def test_every_prior_cycle_re_derives_byte_identically(cycle):
    """§2's first clause. Each cycle under ITS OWN rules and ITS OWN params: `finding_identity`
    is now 2 and every stored Finding was made under 1, so a gate that re-judged history under
    today's parameters would fail for the one reason that does not matter."""
    path = REPO / "state" / f"{cycle}.json"
    assert path.is_file(), f"{path} is gone; a cycle's evidence is not replaceable"
    payload = json.loads(path.read_text(encoding="utf-8"))
    recorded = len(payload["findings_detail"]) + len(payload.get("control_findings_detail", []))
    assert recorded == PRIOR_CYCLES[cycle], f"{cycle} recorded {recorded}, not the gate's number"
    out = _rederive_module().rederive(payload, _params_for(payload))
    assert out["identical"], out
    assert out["recorded"] == PRIOR_CYCLES[cycle]


# ------------------------------------------------------------- §1.2 every failure has a name
def test_the_closed_set_grew_and_nothing_left_it():
    """`ERROR_CLASSES` may only grow: it is an input to the derived `obs_id`, so a removed
    member is a stored Observation that can no longer be rehydrated."""
    was = {None, "dns", "timeout", "http_4xx", "http_5xx", "robots_disallowed", "parse_error",
           "collector_unavailable"}
    now = set(errors.ERROR_CLASSES)
    assert was <= now
    # v3 added three; v4 added `off_host`, the mirror of `robots_disallowed` one policy layer
    # up — not fetched because the SCANNER's same-host policy excludes the URL
    # (`cc_tasks/2026-09-08_scan_harness_v4.md` §1.3). The set may only grow, and each entry
    # names the task that added it so a later reader can see the shape of the growth.
    # `sitemap_off_site` joined in `cc_tasks/2026-09-09_closeout_and_manners.md` decision 3:
    # a sitemap declared on another site is recorded with its URL and never requested. It is
    # in the `not_fetched` family beside `robots_disallowed` and `off_host`, and it is growth,
    # which this test permits and pins so that growth is always deliberate.
    # `redirect_loop` joined in `cc_tasks/2026-09-10_harness_v5_blind.md` decision 4. Cycle 4
    # filed `httpx.TooManyRedirects` under `unknown` — correctly, because the map did not name
    # it — and `unknown` is the map asking to be extended. Growth, pinned, deliberate.
    assert now - was == {"connection_reset", "refused", "unknown", "off_host",
                         "sitemap_off_site", "redirect_loop"}


def test_the_blind_set_grew_only_by_the_new_classes():
    """Which classes mean "we did not observe" decides every rule's `error`-vs-`fail`.

    **Harness-versioned since v5** (`cc_tasks/2026-09-10_harness_v5_blind.md`). This test used to
    assert one answer; there are two now, and asserting BOTH is what protects the record. Under
    v4 — the reading every stored payload was judged under — the set is exactly what harness-v3
    left, `robots_disallowed` excluded. Under v5 it gains that one class and nothing else. A
    payload re-derived under its own version therefore cannot move, and the fix cannot leak
    backwards into history.
    """
    from scan import errors as _errors
    was = {"dns", "timeout", "http_5xx", "parse_error", "collector_unavailable"}
    v4 = set(_errors.blind_classes(4))
    assert was <= v4, f"a class stopped being blind under v4: {sorted(was - v4)}"
    assert v4 - was == {"connection_reset", "refused", "unknown", "redirect_loop"}
    assert "robots_disallowed" not in v4, "v4's reading is what nine stored payloads were judged under"
    assert "http_4xx" not in v4

    v5 = set(_errors.blind_classes(5))
    assert v5 - v4 == {"robots_disallowed"}, (
        f"harness-v5 moved more than the one class it declares: {sorted(v5 - v4)}")
    assert "http_4xx" not in v5, "a 404 on a probed path is still the measurement"


def test_classification_is_a_map_and_not_a_fallback():
    """The defect was `"timeout" if "timeout" in type(exc).__name__.lower() else "dns"` — a
    guess with a default, which filed 92 connection resets as name-resolution failures."""
    import errno
    import socket
    import httpx

    def wrap(cls, msg, cause=None):
        e = cls(msg)
        e.__cause__ = cause
        return e

    cases = {
        "connection_reset": [wrap(httpx.ConnectError, "[Errno 54] Connection reset by peer"),
                             wrap(httpx.ConnectError, "x",
                                  OSError(errno.ECONNRESET, "Connection reset by peer")),
                             httpx.RemoteProtocolError("Server disconnected")],
        "dns": [wrap(httpx.ConnectError, "x",
                     socket.gaierror(8, "nodename nor servname provided"))],
        "timeout": [httpx.ConnectTimeout("x"), httpx.ReadTimeout("x")],
        # ECONNREFUSED is a TCP-layer refusal (nothing listening) and `refused` is an
        # HTTP-layer one. Folding them together would make "hosts that refuse this scanner"
        # include hosts that are simply down.
        # A redirect loop had no name until harness-v5 and resolved to `unknown`, which is
        # what `unknown` is for. It has one now, and it is BLIND: no final response arrived.
        "redirect_loop": [httpx.TooManyRedirects("x")],
        "unknown": [wrap(httpx.ConnectError, "x", OSError(errno.ECONNREFUSED, "refused")),
                    wrap(httpx.ConnectError, "nothing anyone has seen before")],
    }
    for want, excs in cases.items():
        for e in excs:
            assert errors.classify_exception(e) == want, f"{type(e).__name__}: {e}"

    p = load_params()
    assert errors.classify_status(404, p) == "http_4xx"      # the measurement
    assert errors.classify_status(403, p) == "refused"       # the refusal
    assert errors.classify_status(429, p) == "refused"
    assert errors.classify_status(503, p) == "http_5xx"
    assert errors.classify_status(200, p) is None
    assert errors.classify_status(None, p) is None


def test_no_collector_still_guesses_an_error_class():
    """The fallback is gone from every collector, not just the two the RESULT named."""
    for py in sorted((SCAN / "collectors").glob("*.py")):
        # `literals=False`: two of the three needles ARE literals — the guessed class is the
        # string "dns" itself. Comments and docstrings still go, so a collector may explain
        # what it no longer does without being reported as still doing it.
        src = strip_prose(py.read_text(encoding="utf-8"), literals=False)
        assert 'else "dns"' not in src, py.name
        assert 'error_class="dns"' not in src, py.name
        assert "error_class_for" not in src, py.name


def test_the_misfiled_observations_are_overlaid_and_never_edited():
    """Append-only: the observation lines still say `dns` and an overlay says what they are.

    **Counted per PASS, not over the whole shard.** `rc.overlaid()` is deliberately
    pass-agnostic — it is the idempotence guard that stops a second pass re-correcting a record
    a first pass already corrected — so it grew to 359 when
    `cc_tasks/2026-09-07_scan_run_2.md` §1.2 added the 266 status-derived overlays. THIS test
    is about the harness-v3 `recorded_error` pass and its 93; asserting against the total made
    it a test of how many passes have ever run.
    """
    import reclassify_observation_errors as rc
    from kg import eventlog
    remaining = rc.misfiled()
    overlaid = rc.overlaid()
    assert {ev["obs_id"] for ev, _ in remaining} <= overlaid, (
        f"{len([1 for ev, _ in remaining if ev['obs_id'] not in overlaid])} misfiled "
        f"observation(s) carry no overlay")
    # `classified_from` defaults to `recorded_error`: the 93 predate the field.
    mine = [ev for ev in eventlog.replay()
            if ev.get("event_type") == rc.EVENT
            and ev.get("classified_from", "recorded_error") == "recorded_error"]
    # 93 from the harness-v3 pass, plus the 3 `cc_tasks/2026-09-10_harness_v5_blind.md`
    # decision 4 added when `redirect_loop` got a name: the same three Census A10 probes that
    # cycle 4 filed under `unknown`, corrected the only way this repo corrects anything, by
    # overlay. The number is pinned per pass so growth stays deliberate and visible.
    assert len(mine) == 96, (
        f"{len(mine)} `recorded_error` overlays, not the 93 the harness-v3 task recorded plus "
        f"the 3 harness-v5 added (total across all passes: {len(overlaid)})")


# ----------------------------------------------------- §1.3 one probe per object per cycle
def test_a_surfaces_links_are_headed_once_per_cycle():
    """Asserted from the fixture server's REQUEST LOG — what was actually fetched, not what the
    runner meant to fetch. A1 and A3 read the same shared observations; before this leg existed
    each HEADed all 25 links, which is 559 duplicate requests against public federal hosts in
    the 2026-09-07 cycle and no additional evidence for either rule."""
    from scan.manners import Fetcher
    from scan.runner import collect_leg
    params = load_params()
    server = FixtureServer("passes_all")
    with server as base:
        target = {"doc_id": "control:passes_all", "url": f"{base}/index.html"}
        f = Fetcher(params, clock=VirtualClock())
        obs = []
        for leg in list(SHARED_LEGS) + ["A1", "A3"]:
            obs += collect_leg({"leg": leg}, target, params, f)
    heads = [r["path"] for r in server.requests if r["method"] == "HEAD"]
    assert heads, "no link was HEADed at all, so this proves nothing"
    assert len(heads) == len(set(heads)), (
        f"an object was HEADed more than once in one cycle: "
        f"{sorted({p for p in heads if heads.count(p) > 1})}")
    # And the legs that used to collect their own now collect nothing.
    assert collect_leg({"leg": "A1"}, target, params, None) == []
    assert collect_leg({"leg": "A3"}, target, params, None) == []
    assert obs, "the shared leg observed nothing"


def test_the_current_a1_and_a3_read_the_shared_leg():
    assert SHARED_LEGS == ("link_probe",)
    assert consumes(CURRENT["A1"]) == ("link_probe",)
    assert consumes(CURRENT["A3"]) == ("link_probe",)
    # The superseded modules stay in REGISTRY and are still the rules their Findings re-derive
    # under; they simply are not what a new cycle judges with.
    assert {"RULE-A1-v2", "RULE-A3-v3"} <= set(REGISTRY)
    # NOT pinned to a version. Which rule is CURRENT is a moving fact by design — that is
    # what `GENERATIONS` is for, and `test_every_shipped_rule_version_stays_in_the_registry`
    # already asserts CURRENT is the highest shipped generation for each leg. What this test
    # owns is that whatever is current reads the SHARED leg, which the two lines above check.
    assert CURRENT["A1"] in REGISTRY and CURRENT["A3"] in REGISTRY


def test_a_rule_that_consumes_a_shared_leg_regroups_the_same_way_on_re_derivation():
    """`run.py` and `rederive.py` must group identically or a re-derivation moves the derived
    id from identical evidence. One function, `rules.consumes`, is what makes that true."""
    import inspect
    from scan import rederive as _rd  # noqa: F401  (import guard: the module must load)
    for src in (SCAN / "run.py", SCAN / "rederive.py"):
        assert "consumes(" in src.read_text(encoding="utf-8"), src.name
    assert inspect.isfunction(consumes)


# ------------------------------------------------------------------- §1.4 the controls
def test_every_fixture_has_a_pre_registered_table_and_every_table_a_fixture():
    """The invariant this test owns, stated without a count.

    It used to pin the four fixture NAMES, which made adding the fifth
    (`invalid_route_unobserved`, `cc_tasks/2026-09-08_scan_harness_v4.md` §1.2) look like a
    regression. What must hold is the correspondence: a fixture with no pre-registered
    expectation is a control that cannot fail, and an expectation with no fixture is an
    expectation nothing tests. The current roster is pinned by name in
    `tests/test_scan_harness_v4.py`, where the fixture that added to it lives.
    """
    params = load_params()
    expected = params["e5_control"]["expected_verdicts"]
    assert set(expected) == set(MODES)
    assert {"passes_all", "fails_all", "refuses_identified_client",
            "resets_connection"} <= set(MODES), "a control fixture may not be removed"
    for fixture, table in expected.items():
        if isinstance(table, dict):
            assert "default" in table, fixture


def test_the_control_gate_passes_on_all_four_fixtures():
    """§2's second clause: every rule returns its PRE-REGISTERED verdict, every error class the
    fixtures are built to produce actually appears, and `unknown` is zero.

    A control that fails is the evidence that a zero means something (Cleveland's argument for
    a control mark on a chart; the scan-run RESULT §5 makes the same point about eight legs at
    0/23). A rule that returned `error` for every input would pass a gate made only of `pass`
    and `fail` cases, which is what the first two fixtures were.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_run_v3", SCAN / "run.py")
    run_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_mod)
    params = load_params()
    _cf, e5, control_obs, ok = run_mod.run_controls(params, clock=VirtualClock())
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

    classes = {c for p in seen.values() for c in p["error_classes"]}
    assert "refused" in classes, (
        "no fixture produced `refused`, so a cycle reporting zero refusals proves nothing")
    assert "connection_reset" in classes, (
        "no fixture produced `connection_reset`, the class 92 StatCan observations needed")
    assert "unknown" not in classes, (
        f"a control fixture produced an UNCLASSIFIED failure; the map is missing a rule")


# ------------------------------------------------------------- §1.5 the admission escape
def test_a_scan_surface_is_not_gapped_for_being_thin(tmp_path, monkeypatch):
    """A landing page admitted to be MEASURED emits no `conversion_gap`. Its extent IS the
    measurement (A10, B3), so gapping it registers a ResearchTask asking for the
    re-acquisition of a page that was acquired correctly — 22 of which had to be withdrawn by
    hand after the 2026-09-07 admission."""
    from kg import eventlog, manifest
    from kg.ingest import gate as ingest_gate
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    corpus = REPO / "corpus" / "scan"
    corpus.mkdir(parents=True, exist_ok=True)
    page = corpus / "zz-test-scan-surface.html"
    page.write_text("<!doctype html><html><body><nav><a href='/a'>a</a>"
                    "<a href='/b'>b</a></nav><p>thin</p></body></html>", encoding="utf-8")
    calls = []
    monkeypatch.setattr(ingest_gate, "check", lambda *a, **k: calls.append(a))
    try:
        common = dict(title="t", authors=["a"], pub_date="2026-09-07", source_type="federal",
                      inclusion_rationale="test")
        manifest.add(page, doc_id="zz-test-scan-surface",
                     primary_url="https://example.gov/zz-test-scan-surface",
                     purpose="scan_surface", **common)
    finally:
        page.unlink(missing_ok=True)
    # The gate is reached for a corpus document and short-circuited for a scan surface, so the
    # real check is on `_convertibility_gate` itself rather than on whether `check` was called.
    assert manifest._GATE_EXEMPT_PURPOSES == ("scan_surface",)


def test_the_convertibility_gate_returns_early_for_a_scan_surface(monkeypatch):
    from kg import manifest
    from kg.ingest import gate as ingest_gate
    reached = []
    monkeypatch.setattr(ingest_gate, "check", lambda *a, **k: reached.append(a))
    manifest._convertibility_gate("d", Path("x.html"), {"purpose": "scan_surface"})
    assert reached == [], "the gate ran on a surface admitted to be measured"
    manifest._convertibility_gate("d", Path("x.html"), {"purpose": "corpus_document"})
    assert len(reached) == 1, "the gate did NOT run on an ordinary corpus document"


def test_an_unknown_purpose_is_refused_not_ignored():
    from kg import manifest
    assert set(manifest._PURPOSES) == {"corpus_document", "scan_surface"}
    assert set(manifest._GATE_EXEMPT_PURPOSES) <= set(manifest._PURPOSES)


def test_every_admitted_scan_surface_carries_the_purpose():
    from kg import manifest
    scan = [e for e in manifest._load_entries() if str(e["doc_id"]).startswith("scan-")]
    assert len(scan) == 26, f"{len(scan)} scan surfaces admitted, not the 26 on record"
    missing = [e["doc_id"] for e in scan if e.get("purpose") != "scan_surface"]
    assert not missing, missing


# --------------------------------------------------------- §1.6 a name carries its cycle
def test_a_per_cycle_name_without_its_cycle_is_refused():
    with pytest.raises(cycle_results.ResultNameError):
        cycle_results.check_name("scan_surfaces_next", "scan_2026-09-08")
    # A metric the first cycle never bound bare, so it is not on the exception list and must
    # carry its cycle from the first time it is used.
    with pytest.raises(cycle_results.ResultNameError):
        cycle_results.check_names(["scan_a1_pass_2026-09-08", "scan_link_probes_shared"],
                                  "scan_2026-09-08")


def test_the_first_cycles_exceptions_belong_to_the_first_cycle_and_to_no_other():
    """**Corrected 2026-09-07 by `cc_tasks/2026-09-07_scan_run_2.md`.** This test used to
    assert that `check_name("scan_surfaces", "scan_2026-09-08")` PASSES, and the check was
    written to match. Both were wrong in the same direction.

    DD-056 §"What is not renamed" says the bare names the first cycle bound stand and "are
    **never reused** by a later cycle", and `cycle_results`' own docstring repeats it. The
    check ignored the cycle, so cycle 2 would have passed the pre-flight with a bare
    `scan_surfaces` and then been refused by `seldon result register` (AD-028) mid-run, after
    the measurement — which is the exact incident DD-056 was written about. The allow-list is
    the record of an exception; scoping it to `FIRST_CYCLE` is what keeps it from being a
    loophole.
    """
    cycle_results.check_name("scan_surfaces_2026-09-08", "scan_2026-09-08")
    # The first cycle re-registering its own bound name: allowed, and the only case that is.
    cycle_results.check_name("scan_surfaces", cycle_results.FIRST_CYCLE)
    cycle_results.check_name("scan_a1_pass_rate", cycle_results.FIRST_CYCLE)
    for later in ("scan_2026-09-07b", "scan_2026-09-08"):
        with pytest.raises(cycle_results.ResultNameError, match="first-cycle exception"):
            cycle_results.check_name("scan_surfaces", later)
        assert cycle_results.name_for("scan_surfaces", later).endswith(
            cycle_results.cycle_suffix(later))
    # `scan_control_findings` is deliberately NOT on the list: DD-056's motivating incident is
    # that it was already bound at 31 by the 2026-09-06 control cycle, so the 2026-09-07 cycle
    # was refused and registered `scan_control_findings_2026-09-07` instead. The name the
    # convention was learned from is the one name it does not excuse.
    with pytest.raises(cycle_results.ResultNameError):
        cycle_results.check_name("scan_control_findings", "scan_2026-09-08")
    assert len(cycle_results.FIRST_CYCLE_EXCEPTIONS) == 101


def test_the_exception_list_is_exactly_what_the_registrar_would_emit_bare():
    """Not a hand-kept list: every entry is a name `scan_report.py` actually produces without a
    cycle suffix. A stale entry would be a licence for a name nothing emits."""
    import re
    # Explicitly the FIRST cycle: `scan_report.py` now reads `params.cycle.name`, so with no
    # `--cycle` it reports whatever cycle is current and emits nothing bare at all — which
    # would make this test pass vacuously against an empty set on cycle 2 and fail loudly on
    # cycle 3. The exception list is a fact about the first cycle, so it is checked against
    # the first cycle.
    out = subprocess.run([sys.executable, "scripts/scan_report.py", "--dry-run",
                          "--cycle", cycle_results.FIRST_CYCLE],
                         capture_output=True, text=True, cwd=str(REPO))
    assert out.returncode == 0, out.stderr[-500:]
    emitted = {l.split("\t")[0] for l in out.stdout.splitlines() if "\t" in l}
    bare = {n for n in emitted if not re.search(r"_\d{4}-\d{2}-\d{2}$", n)}
    assert bare == set(cycle_results.FIRST_CYCLE_EXCEPTIONS)


def test_the_registrar_checks_every_name_before_registering_any():
    """AD-028's own discipline, applied one level up: a run that binds half a cycle's Results
    and then refuses is worse than one that refuses first."""
    import inspect
    src = inspect.getsource(cycle_results.register)
    assert src.index("check_names") < src.index("subprocess.run")


# ------------------------------------------------------------------ registry integrity
def test_the_new_generation_is_new_modules_and_its_predecessors_are_untouched():
    """`deviates` -> write a new module, never edit the old one. A module whose bytes changed
    after Findings were recorded under it would make the re-derivation gate a tautology."""
    for m in [x for gen in GENERATIONS[:-1] for x in gen]:
        rel = Path(m.__file__).resolve().relative_to(REPO)
        r = subprocess.run(["git", "diff", "--stat", "HEAD", "--", str(rel)],
                           capture_output=True, text=True, cwd=str(REPO))
        assert not r.stdout.strip(), f"{rel} was edited: {r.stdout.strip()}"
    # The newest generation's rules OUTRANK their predecessors; the specific version numbers
    # are not the property this test owns. The pin ("v3", "v4") reported generation 6 — which
    # ships RULE-A1-v4, RULE-A3-v5 and RULE-A8-v4 — as a regression.
    # `test_every_shipped_rule_version_stays_in_the_registry` checks the ranking properly.
    for m in GENERATIONS[-1]:
        assert parse_rule_id(m.RULE_ID)["version"].startswith("v")
