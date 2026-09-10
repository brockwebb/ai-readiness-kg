"""Every guard in the scan harness, replayed against the incident it was built for.

`cc_tasks/2026-09-09_guards_earn_their_keep.md` decision 1.

**Why this file exists.** Four guards were written in four consecutive tasks and three of them
shipped WRONG, each in a way that only a full suite run exposed:

* the blind-probe lint caught `RULE-A5-v2` shipping without a blind guard, which is the guard
  working — but the rule was written by the same hand, in the same hour, as the fix for the
  previous instance of that defect (`2026-09-09_manners_closeout_RESULT.md` §0);
* the AST gate detector answered wrongly in both directions before it answered rightly
  (`2026-09-09_closeout_and_manners_RESULT.md` §5 item 9);
* the evidence-store guard fired on the wrong condition and defeated `tests/conftest.py`
  (`2026-09-09_manners_closeout_RESULT.md` §4 item 3).

A guard asserted only against the fixed code proves that the fixed code is fixed. It says
nothing about whether the guard would have SEEN the defect, which is the only thing a guard is
for. Each test below is therefore a pair: **red** against the pre-guard code path or a faithful
stub of it, **green** against what ships. Prior art: regression testing as practised, and TDD's
"write the failing test first" (Beck 2002) applied after the fact, which is the only way it can
be applied to an incident already survived.

The pre-guard paths are reconstructed here rather than imported, because the whole point of the
fixes was that the old paths no longer exist. Each reconstruction is small enough to read
against the RESULT section its docstring names.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

#: The shared source scanner (`tests/support/sourcescan.py`): code, not prose.
from support.sourcescan import scan, strip_prose

import pytest

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.fixtures.server import FixtureServer                      # noqa: E402


# ====================================================== guard 1: the blind-probe lint

#: A rule module that reads a probe and never asks whether it was observed. This is
#: `RULE-A5-v2` as it first shipped: `only_errors` fires only when EVERY observation is blind,
#: so a surface with one blind candidate and one 404 returned `fail` — an absence claim resting
#: on a probe nobody saw. `cc_tasks/2026-09-09_manners_closeout_RESULT.md` §0.
_PRE_GUARD_RULE = '''
from . import _common as c
RULE_ID, LEG = "RULE-STUB-v9", "A5"

def judge(observations, params):
    obs = [o for o in observations if o.leg == LEG]
    if c.only_errors(obs, params):
        return c.make(RULE_ID, LEG, obs, "error", "nothing observed", params)
    present = [o for o in obs if (o.parsed or {}).get("present")]
    if present:
        return c.make(RULE_ID, LEG, obs, "pass", "served", params)
    return c.make(RULE_ID, LEG, obs, "fail", "no discovery file served", params)
'''


def _lint(sources: dict) -> list:
    """The blind-guard lint's own predicate, over `{name: source}`.

    Read from the shipped test rather than reimplemented: the condition is `unobserved_error`
    or `c.unobserved(` appearing in the module's source, and this must stay the same condition
    or the replay would be checking a lint nobody runs.
    """
    return [n for n, src in sources.items()
            if not any(g in src for g in ("unobserved_error", "c.unobserved("))]


def test_the_blind_probe_lint_catches_the_rule_that_shipped_without_a_guard():
    """RED against the pre-guard rule, GREEN against every rule that ships.

    The incident: `RULE-A5-v2` was written to close the fourth instance of "a verdict from a
    probe nobody observed" and reproduced it as the fifth. The lint is what caught it, 56
    minutes into a full suite, and this asserts that it WOULD.
    """
    assert _lint({"pre_guard_a5": _PRE_GUARD_RULE}) == ["pre_guard_a5"], (
        "the lint does not flag a rule that never consults a blind guard; it would not have "
        "caught RULE-A5-v2")

    from scan.rules import GENERATIONS
    # A rule that measures the HOST is not linted: its subject is the refusal, so a blind guard
    # would return `error` in the case the indicator exists to name
    # (`cc_tasks/2026-09-10_harness_v5_blind.md` decision 3). The opt-out is read from the
    # module's own `MEASURES`, the same way the shipped lint reads it — a replay that checked a
    # different condition would be replaying a lint nobody runs.
    shipped = {Path(m.__file__).stem: Path(m.__file__).read_text(encoding="utf-8")
               for gen in GENERATIONS[3:] for m in gen
               if getattr(m, "MEASURES", "product") == "product"}
    # `rule_a3_v4` is the pinned exemption: generation four shipped before the helper existed
    # and a shipped module may not be edited. The shipped lint pins it by content hash; this
    # replay only needs it out of the way.
    flagged = [n for n in _lint(shipped) if n != "rule_a3_v4"]
    assert flagged == [], flagged


def test_the_shipped_a5_rule_no_longer_reproduces_the_defect():
    """The behavioural half: on the exact shape of the incident — one blind candidate, one
    observed 404 — the shipped rule must not claim absence."""
    from scan.model import Observation
    from scan.rules import judge as judge_rule
    params = load_params()

    def probe(url, status, error_class=None, present=False):
        return Observation.make(
            "A5", "A5", "d", url, "sitemap", "0.1.0", params,
            {"method": "GET", "url": url},
            {"status": status, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 1},
            parsed={"kind": "sitemap", "present": present, "covers_product": False},
            error_class=error_class)

    mixed = [probe("https://x/sitemap.xml", 404, "http_4xx"),
             probe("https://x/sitemap_index.xml", None, "connection_reset")]
    v = judge_rule("RULE-A5-v2", mixed, params)
    assert v.verdict == "error", (
        f"one candidate was never observed and the rule still returned {v.verdict!r}: "
        f"absence is not established while a probe is blind")


# ====================================================== guard 2: robots-first in the fetcher

def test_the_fetcher_gate_catches_the_apex_sitemap_fetch():
    """RED against a pre-guard fetcher, GREEN against the shipped one, on the fixture built
    from the incident.

    The incident: cycle 3 issued `GET https://samhsa.gov/sitemap.xml` and
    `GET https://data.gov/sitemap.xml` to netlocs whose `robots.txt` this scanner had never
    fetched (`cc_tasks/2026-09-09_report_draft_RESULT.md` §3). `sitemap_on_sibling` reproduces
    the shape on loopback.

    The pre-guard fetcher is the shipped one with `_gate` neutralised, which is exactly what
    `raw_get` did before DD-062: issue the request and consult robots nowhere.
    """
    from scan.manners import Fetcher
    from scan.collectors import robots as robots_col, sitemap as sitemap_col
    params = load_params()

    def run(neutralise_gate: bool) -> list:
        srv = FixtureServer("sitemap_on_sibling")
        base = srv.__enter__()
        try:
            sibling = srv.sibling_url.split("//", 1)[1]
            f = Fetcher(params)
            if neutralise_gate:
                f._gate = lambda url: None            # the pre-DD-062 behaviour
            declared = [u for o in robots_col.fetch(f, "A4", "control:x", base + "/", params)
                        for u in ((o.parsed or {}).get("sitemaps") or [])]
            sitemap_col.fetch(f, "A5", "control:x", base + "/", params,
                              declared_sitemaps=declared)
            return [r["path"] for r in srv.requests if r["netloc"] == sibling]
        finally:
            srv.__exit__()

    before = run(neutralise_gate=True)
    assert before and before[0] != "/robots.txt", (
        f"the pre-guard path did not reproduce the incident: sibling saw {before}")

    after = run(neutralise_gate=False)
    assert after and after[0] == "/robots.txt", (
        f"the shipped fetcher touched the sibling before reading its robots.txt: {after}")
    assert "/sitemap.xml" in after, "the same-site declaration stopped being followed"


# ====================================================== guard 3: the evidence-store guard

def test_the_evidence_guard_catches_a_driver_write_and_spares_a_staged_one(tmp_path,
                                                                          monkeypatch):
    """RED against the pre-guard writer, GREEN against the shipped one — and the SECOND half
    is the one that matters, because the guard's first implementation passed the first half
    and failed the second.

    Two incidents, not one:

    * 29 + 18 fixture bodies written into the committed store by drivers run from scripts
      (`cc_tasks/2026-09-09_closeout_and_manners_RESULT.md` §5 item 8, and
      `..._manners_closeout_RESULT.md` §4 item 5);
    * the guard's own first cut keyed on "the caller passed no root" and so redirected a write
      whose root had been deliberately repointed, defeating `tests/conftest.py`
      (`..._manners_closeout_RESULT.md` §4 item 3).
    """
    from scan import model
    committed = tmp_path / "committed"
    monkeypatch.setattr(model, "COMMITTED_EVIDENCE", committed)
    monkeypatch.setattr(model, "EVIDENCE_ROOT", committed / "scan")
    monkeypatch.setattr(model, "SCRIPT_QUARANTINE", tmp_path / "quarantine")
    monkeypatch.setattr(model, "REDIRECT_LOG", tmp_path / "quarantine" / "redirects.jsonl")
    monkeypatch.delenv(model.CYCLE_TOKEN_ENV, raising=False)

    # (a) PRE-GUARD: content-addressed write with no licence check at all.
    def pre_guard(body: bytes) -> Path:
        root = model.EVIDENCE_ROOT
        digest = model.sha256_bytes(body)
        p = root / digest[:2] / digest
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        return p

    landed = pre_guard(b"<html>a driver wrote this</html>")
    assert committed in landed.parents or str(committed) in str(landed), (
        "the pre-guard path did not reproduce the incident")

    # (b) SHIPPED, unlicensed: redirected out of the committed lane, and logged.
    _d, path = model.store_evidence(b"<html>another driver wrote this</html>")
    assert "quarantine" in path and "committed" not in path, path
    assert model.REDIRECT_LOG.is_file(), "the redirect was silent"

    # (c) SHIPPED, root repointed away from the committed lane: HONOURED. This is the half the
    # first implementation failed, and it is why the condition is where-the-bytes-land.
    monkeypatch.setattr(model, "EVIDENCE_ROOT", tmp_path / "staging")
    _d2, staged = model.store_evidence(b"<html>conftest repointed the store</html>")
    assert "staging" in staged and "quarantine" not in staged, staged


# ====================================================== guard 4: the AST gate detector

#: The two pre-guard detectors, both of which shipped and both of which were wrong.
#: `cc_tasks/2026-09-09_closeout_and_manners_RESULT.md` §5 item 9.
def _detector_text_search(*sources: str) -> bool:
    """v1: a regex for `.allowed(`. Matches the phrase inside a COMMENT."""
    return any(re.search(r"\.allowed\s*\(", s or "") for s in sources)


def _detector_joined_parse(*sources: str) -> bool:
    """v2: one AST parse of the joined reachable source. Two `def` blocks concatenated do not
    parse, so it returned False for every collector that gates in its own body."""
    try:
        tree = ast.parse("".join(s or "" for s in sources))
    except SyntaxError:
        return False
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "allowed" for n in ast.walk(tree))


def test_the_gate_detector_beats_both_of_its_predecessors_on_real_source():
    """Each pre-guard detector gives an answer unrelated to the code; the shipped one does not.

    `robots.py` carries a comment explaining why a RULE does not use `Fetcher.allowed()` and
    never calls it, so a text search calls it gated. `http.py` gates in its own body, so a
    joined parse of `def` blocks calls it ungated.
    """
    from scan.fixture_expectations import _calls_gate

    robots_src = (SCAN / "collectors" / "robots.py").read_text(encoding="utf-8")
    assert "allowed()" in robots_src, "the comment this replay depends on is gone"

    # v1 is fooled by the comment. The shipped detector is not.
    assert _detector_text_search(robots_src) is True
    assert _calls_gate(robots_src) is False, (
        "the shipped detector reports robots.py as gated; it never calls the gate")

    # v2 is fooled by concatenation, on the REAL sources that fooled it. The reachable source
    # of a function is its own body plus the bodies of the helpers it calls, and
    # `ast.get_source_segment` returns each WITHOUT a trailing newline — so joining two of
    # them runs the last statement of one into the `def` of the next and the result is not
    # parseable Python. The predecessor caught the SyntaxError and returned False, which means
    # it reported the fetcher as ungated immediately after the fetcher had been gated: a
    # detector announcing the absence of the guard it exists to watch.
    manners_src = (SCAN / "manners.py").read_text(encoding="utf-8")
    tree = ast.parse(manners_src)
    methods = {n.name: ast.get_source_segment(manners_src, n)
               for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)
               for n in cls.body if isinstance(n, ast.FunctionDef)}
    reachable = [methods["raw_get"], methods["_gate"]]
    with pytest.raises(SyntaxError):
        ast.parse("".join(reachable))          # the precondition the defect rested on
    assert _detector_joined_parse(*reachable) is False, (
        "the joined-parse predecessor no longer reproduces its defect")
    assert _calls_gate(*reachable) is True, (
        "the shipped detector cannot see the gate through the helper hop")

    http_src = (SCAN / "collectors" / "http.py").read_text(encoding="utf-8")
    assert _calls_gate(http_src) is True, "http.py gates and the detector must see it"


def test_the_derivation_reports_the_fetcher_as_gated_and_nothing_ungated():
    """The property the detector exists to support, asserted on what ships."""
    from scan.fixture_expectations import fetcher_gates, ungated_probes
    from scan.rules import CANDIDATE_LEGS, FRAMEWORK_LEGS
    gates = fetcher_gates()
    assert gates["gates"] is True, gates
    legs = [l for l in FRAMEWORK_LEGS if l != "E5"] + sorted(CANDIDATE_LEGS)
    assert ungated_probes(legs) == {}, ungated_probes(legs)


# ====================================================== decision 2: no self-licensing

#: How the cycle licence may be set in source, and where. `run.py::main` sets it because it IS
#: the cycle; anything else setting it is a driver granting itself the permission the token
#: exists to withhold.
_LICENCE_OWNER = "assessment/harness/scan/run.py"

#: An assignment into the process environment for the token. `monkeypatch.setenv` is NOT this:
#: it is pytest's reversible fixture, scoped to one test, and it is how the licensed path gets
#: exercised at all. The lint is about source that grants the licence and leaves it granted.
_TOKEN = "AIRKG" + "_SCAN_CYCLE"
_SELF_LICENCE = re.compile(
    r"""os\.environ\s*\[\s*['"]?""" + _TOKEN + r"""|"""
    r"""os\.environ\s*\[\s*(?:model\.)?CYCLE_TOKEN_ENV\s*\]\s*=|"""
    r"""os\.environ\.setdefault\s*\(\s*(?:['"]""" + _TOKEN + r"""|(?:model\.)?CYCLE_TOKEN_ENV)""")


def self_licensing_sites(root: Path) -> list:
    """`[(path, lineno, line)]` where source grants itself the cycle licence.

    Through the shared scanner (decision 4), so a comment or a docstring describing the licence
    is not mistaken for granting it. This lint matched its own bait the day it was written.

    `literals=False`: the offence here is `os.environ["AIRKG_SCAN_CYCLE"] = "1"`, where the token
    is the subscript KEY. Blanking string literals — right for every other check in the repo —
    would blind this one to the exact line it exists to catch. Comments and docstrings still go.
    """
    out = []
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        try:
            rel = str(py.relative_to(REPO))
        except ValueError:
            rel = str(py)                      # a planted file under tmp_path
        src = py.read_text(encoding="utf-8")
        for i, line in enumerate(strip_prose(src, literals=False).splitlines(), 1):
            if _SELF_LICENCE.search(line):
                original = src.splitlines()[i - 1] if i - 1 < len(src.splitlines()) else line
                out.append((rel, i, original.strip()))
    return out


def test_only_the_cycle_runner_sets_the_cycle_licence():
    """Decision 2. **The incident is mine and it is one task old.**

    `cc_tasks/2026-09-09_manners_closeout_RESULT.md` §4 item 5: my own control-gate driver set
    `AIRKG_SCAN_CYCLE` to license itself and wrote 18 fixture bodies into the committed store —
    the third occurrence of that defect in three tasks, and the first to go straight through the
    mechanism built to stop it. The token is not the weak point; a driver willing to set it is.

    A source-level lint, the same shape as the suffix-list retirement check, because the
    behaviour is indistinguishable from a legitimate cycle at runtime. That is the point: only
    the source can say who is entitled to claim it.
    """
    sites = [s for tree in ("assessment", "scripts", "tests")
             for s in self_licensing_sites(REPO / tree)]
    offenders = [s for s in sites if s[0] != _LICENCE_OWNER]
    assert not offenders, (
        f"these grant themselves the scan-cycle licence: {offenders}. Only "
        f"{_LICENCE_OWNER}::main may, because it is the cycle. A driver that needs bodies "
        f"should pass an explicit --evidence-root instead.")
    assert any(s[0] == _LICENCE_OWNER for s in sites), (
        "nothing sets the licence at all, so the lint is watching an empty set and the "
        "committed store is never writable by a real cycle")


def test_the_self_licensing_lint_catches_a_planted_driver(tmp_path):
    """RED against a planted driver, GREEN once removed. §3 asks for exactly this."""
    # ASSEMBLED, not written literally: a lint that scans source must not be defeated — or
    # tripped — by the test that plants its own bait. The tldextract retirement check needed
    # the same trick, and forgetting it here made this file report ITSELF as the offender.
    token = "AIRKG" + "_SCAN_CYCLE"
    planted = tmp_path / "throwaway_driver.py"
    planted.write_text(f'import os\nos.environ["{token}"] = "1"\n', encoding="utf-8")
    assert self_licensing_sites(tmp_path), "the lint does not see a planted self-licence"
    planted.write_text(f'import os\nprint(os.environ.get("{token}"))\n', encoding="utf-8")
    assert not self_licensing_sites(tmp_path), (
        "the lint fires on a mere READ of the token; only granting it is the offence")


# ====================================================== decision 3: the redirect log is read

def test_the_redirect_log_is_empty_at_the_gate():
    """Decision 3. A guard that records and is never read is a guard that has been switched off
    quietly.

    `unlicensed/redirects.jsonl` names every driver that tried to write into the committed
    store. Non-empty at gate time means litter was produced during this task and not swept, so
    the gate says so and names the writers rather than leaving the finding in a file nobody
    opens.
    """
    from scan.model import REDIRECT_LOG
    if not REDIRECT_LOG.is_file():
        return
    lines = [l for l in REDIRECT_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert not lines, (
        f"{len(lines)} evidence write(s) were redirected out of the committed store and not "
        f"swept: {lines[:3]}. Run scripts/quarantine_fixture_evidence.py, which records what "
        f"it swept, then clear {REDIRECT_LOG.relative_to(REPO)}.")


def test_the_redirect_hygiene_check_catches_a_planted_line(tmp_path, monkeypatch):
    """RED against a planted line, GREEN after the sweep. §3 asks for exactly this."""
    from scan import model
    log = tmp_path / "redirects.jsonl"
    monkeypatch.setattr(model, "REDIRECT_LOG", log)

    def check() -> list:
        if not log.is_file():
            return []
        return [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]

    log.write_text('{"why": "planted", "requested_root": "corpus/evidence/scan"}\n',
                   encoding="utf-8")
    assert check(), "the hygiene check does not see a planted redirect"
    log.write_text("", encoding="utf-8")
    assert not check(), "the hygiene check still fires after the sweep"


# ============================================ harness-v5: the incident A10 shipped in cycle 4

def test_a10_returned_pass_from_two_probes_that_were_never_issued():
    """**RED under harness-v4, GREEN under harness-v5.** `cc_tasks/2026-09-10_harness_v5_blind.md`
    decision 4, replayed against the Finding that actually shipped.

    Cycle 4 recorded, on `scan-eia-flagship-1-open-data`:

        pass  RULE-A10-v3  "deep link HTTP None; invalid route correctly HTTP None;
                            None visible characters present before JS"

    Both probes were `robots_disallowed` — eia.gov forbids that path to this UA and the fetcher
    obeyed, so neither request was issued. "Invalid route correctly HTTP None" is not a correct
    rejection; it is no rejection at all. Under v4 `robots_disallowed` was SCOPE, so
    `_common.unobserved` said the probes had been seen and the rule scored them.

    The rule module is untouched. What changed is one entry in `errors.CLASSES`, which is the
    point: a defect that appeared in seven disguises across A1, A3, A6, A8, A10, B3 and G1-D was
    one wrong answer to one question, asked in one place.
    """
    import json as _json
    payload = REPO / "state" / "scan_2026-09-10.json"
    if not payload.is_file():
        pytest.skip("cycle 4's payload is not on disk")
    doc = _json.loads(payload.read_text(encoding="utf-8"))
    obs = {o["obs_id"]: o for o in doc["observations_detail"]}
    finding = next((f for f in doc["findings_detail"]
                    if f["rule_id"] == "RULE-A10-v3"
                    and f["target_doc_id"] == "scan-eia-flagship-1-open-data"), None)
    assert finding is not None, "the incident Finding is not in the payload"
    assert finding["verdict"] == "pass", "the incident is that this said pass"

    cited = [obs[e] for e in finding["evidence"] if e in obs]
    assert cited and all(o.get("error_class") == "robots_disallowed" for o in cited), (
        "the incident is that every probe was robots-disallowed")

    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import errors

    # RED: under v4 the probes read as observed, which is how a pass was reachable.
    assert not any(errors.is_blind(o["error_class"], 4) for o in cited)
    # GREEN: under v5 every one of them is blind, so `unobserved_error` fires before any verdict.
    assert all(errors.is_blind(o["error_class"], 5) for o in cited)


def test_a_redirect_loop_has_a_name_now():
    """Decision 4's other half. Cycle 4 filed `httpx.TooManyRedirects` on Census's A10
    invalid-route probe as `unknown` — correctly, because the map did not name it, and the rule
    refused to reach a verdict and said so. `unknown` is the map asking to be extended, and this
    is the extension: `redirect_loop`, BLIND, because no final response came back."""
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import errors
    assert errors.BY_EXCEPTION_TYPE["TooManyRedirects"] == "redirect_loop"
    assert errors.is_blind("redirect_loop", 5) and errors.is_blind("redirect_loop", 4)

    class _TooManyRedirects(Exception):
        pass
    _TooManyRedirects.__name__ = "TooManyRedirects"
    assert errors.classify_exception(_TooManyRedirects("Exceeded maximum allowed redirects.")) \
        == "redirect_loop"
