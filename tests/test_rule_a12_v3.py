"""Generation 10: reason strings that describe the evidence.

`cc_tasks/2026-09-13_rule_a12_v3.md` §3. Two corrections, one property each, and the property
is the same both times — **a Finding's reason describes what was observed** (DD-055):

* `RULE-A12-v2` tests `wrong_content_type` before `robots_status`, so a host whose
  `/robots.txt` 404s with an HTML error page is described as having SERVED a robots.txt with the
  wrong content type. The verdict is right and the sentence is false. `v3` reads the status
  first and says what `RULE-A4-v1` says on the same bytes.
* `_common.unobserved_error` printed the error CLASS's note whichever branch of
  `_common.unobserved` fired, so a probe blinded by a REFUSAL STATUS carried the note of a class
  that had nothing to do with it — and for a probe whose class is `None`, that note reads *"the
  collector observed the surface"* about a probe the same sentence has just called unobserved.

**Both corrections are versioned, and the tests hold both versions.** A reason string is inside
the byte-identical re-derivation comparison, so correcting one in place would make every stored
payload carrying it un-re-derivable. `v2` keeps its module and `reason_text: 1` keeps its text,
and each is asserted here beside its successor — a test that checked only the new string would
pass for a rule that had quietly re-scored the corpus.

Nothing here reaches a network: the evidence is the stored payloads, and the one fixture test
binds a loopback socket and issues a single request without the standing rate limit.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

from scan import errors as scan_errors                                # noqa: E402
from scan import load_params                                          # noqa: E402
from scan.model import Observation                                    # noqa: E402
from scan.rules import CURRENT, REGISTRY, V10, judge as judge_rule    # noqa: E402
from scan.rules import _common                                        # noqa: E402

#: The published Tier A Finding that carries the false sentence, and the cycle whose payload
#: holds the Observations behind it. Named once: three tests read the same evidence.
FEDRES = "host:www.federalreserve.gov"
SOURCE_CYCLE = "scan_2026-09-10"


def _payload(name: str) -> dict:
    p = REPO / "state" / f"{name}.json"
    if not p.is_file():
        pytest.skip(f"{p.relative_to(REPO)} is not on disk")
    return json.loads(p.read_text(encoding="utf-8"))


def _fedres_observations() -> list:
    """The robots/probe pair `RULE-A12-v2` judged `host:www.federalreserve.gov` on.

    Read off the stored cycle rather than built, because decision 5 asks for EVIDENCE and not a
    fixture: the sentence being corrected is on a published Finding, and a hand-built pair
    would test the rule against my reading of the evidence instead of against the evidence.
    """
    src = _payload(SOURCE_CYCLE)
    rows = [o for o in src["observations_detail"]
            if o["target_doc_id"] == FEDRES and o["leg"] == "A12"]
    assert rows, f"{SOURCE_CYCLE} carries no A12 observation for {FEDRES}"
    return [Observation(**r) for r in rows]


# ------------------------------------------------------------------ RULE-A12-v3

def test_the_false_sentence_reproduces_under_v2_and_is_corrected_under_v3():
    """The pair, on the real bytes. Asserting only that v3 is right would leave the fix
    unanchored — a rule that said "no robots.txt served" for everything would pass that."""
    obs = _fedres_observations()
    params = load_params()
    robots = next(o for o in obs if "present" in (o.parsed or {}))
    # The evidence, stated, so this test documents the case it is about.
    assert (robots.response or {}).get("status") == 404
    assert (robots.parsed or {})["wrong_content_type"] is True
    assert (robots.parsed or {})["served_content_type"] == "text/html"

    v2 = judge_rule("RULE-A12-v2", obs, params)
    v3 = judge_rule("RULE-A12-v3", obs, params)
    assert v2.verdict == v3.verdict == "fail", (v2.verdict, v3.verdict)
    assert "is served with a content type that cannot be robots.txt" in v2.reason, (
        "the recorded false sentence no longer reproduces under v2; v2 is immutable and every "
        "Finding recorded under it must keep re-deriving from its own bytes")
    assert _common.NO_ROBOTS_SERVED in v3.reason, v3.reason
    assert "HTTP 404" in v3.reason
    assert "is served with a content type" not in v3.reason


def test_a12_v3_and_a4_v1_say_the_same_sentence_about_an_absent_robots_txt():
    """Decision 1's "read from a shared constant so the two rules cannot drift", enforced
    against A4-v1's SHIPPED BYTES rather than by editing them.

    `RULE-A4-v1` is immutable — every Finding recorded under it re-derives from its own source —
    so it cannot import the constant. What can be checked is that its literal still contains the
    string `RULE-A12-v3` builds its sentence from; the day someone edits A4-v1's wording, this
    fails and names the drift. Same shape as the content-hash pin the generation-4 lint uses for
    `rule_a3_v4`.
    """
    a4_src = (REPO / "assessment" / "harness" / "scan" / "rules" / "rule_a4.py").read_text(
        encoding="utf-8")
    assert _common.NO_ROBOTS_SERVED in a4_src, (
        f"RULE-A4-v1 no longer contains {_common.NO_ROBOTS_SERVED!r}; A12-v3 builds its "
        f"sentence from that constant precisely so the two say one thing about one piece of "
        f"evidence, and they have drifted")
    obs = _fedres_observations()
    params = load_params()
    a12 = judge_rule("RULE-A12-v3", obs, params)
    # And on the SAME evidence A4 judges — its own leg's robots observation — A4 says it too.
    robots = next(o for o in obs if "present" in (o.parsed or {}))
    a4_obs = [Observation(**{**robots.to_dict(), "leg": "A4", "spec_code": "A4"})]
    a4 = judge_rule("RULE-A4-v1", a4_obs, params)
    assert _common.NO_ROBOTS_SERVED in a4.reason and _common.NO_ROBOTS_SERVED in a12.reason


def _a12_pair(params: dict, *, robots_status, wrong_type: bool, ctype: str,
              present: bool, probe_status=200, self_allowed=True):
    """A robots/probe pair for one branch of A12. Built, because these are the branches no
    stored cycle happens to contain; the branch that IS in a cycle is tested on that cycle."""
    def obs(url, parsed, status, leg="A12"):
        return Observation.make(
            "A12", leg, "host:x", url, "robots", "0.1.0", params,
            {"method": "GET", "url": url},
            {"status": status, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 1},
            parsed=parsed,
            error_class=scan_errors.classify_status(status, params))
    return [obs("https://x/robots.txt",
                {"present": present, "wrong_content_type": wrong_type,
                 "served_content_type": ctype, "robots_status": robots_status,
                 "probe_url": "https://x/p", "self_ua": params["manners"]["user_agent"],
                 "self_ua_allowed": self_allowed, "per_ua": {}},
                robots_status),
            obs("https://x/p", {"probe": "a12_target"}, probe_status)]


def test_v3_changes_the_sentence_for_an_unserved_file_and_nothing_else():
    """Every branch both versions can reach, compared. `v3` may differ from `v2` ONLY where the
    file was not served, and never in a verdict."""
    params = load_params()
    # (case, expect the reasons to differ)
    cases = [
        ("404 with an HTML error page — the corrected case",
         dict(robots_status=404, wrong_type=True, ctype="text/html", present=False), True),
        ("404 with a plain-text body",
         dict(robots_status=404, wrong_type=False, ctype="text/plain", present=False), True),
        ("200 with an HTML soft-404 shell — the branch v2 was written for",
         dict(robots_status=200, wrong_type=True, ctype="text/html", present=False), False),
        ("served and coherent",
         dict(robots_status=200, wrong_type=False, ctype="text/plain", present=True), False),
        ("served, and disallows this client",
         dict(robots_status=200, wrong_type=False, ctype="text/plain", present=True,
              self_allowed=False), False),
        ("served and permits, and the edge refuses",
         dict(robots_status=200, wrong_type=False, ctype="text/plain", present=True,
              probe_status=403), False),
    ]
    for label, kw, reason_differs in cases:
        obs = _a12_pair(params, **kw)
        v2 = judge_rule("RULE-A12-v2", obs, params)
        v3 = judge_rule("RULE-A12-v3", obs, params)
        assert v2.verdict == v3.verdict, f"{label}: verdict moved {v2.verdict} -> {v3.verdict}"
        if reason_differs:
            assert v2.reason != v3.reason, f"{label}: v3 did not correct the sentence"
            assert _common.NO_ROBOTS_SERVED in v3.reason, f"{label}: {v3.reason}"
        else:
            assert v2.reason == v3.reason, (
                f"{label}: v3 changed a sentence it was not sent to change\n"
                f"  v2: {v2.reason}\n  v3: {v3.reason}")


def test_v3_is_the_current_rule_for_a12_and_v2_is_still_in_the_registry():
    assert CURRENT["A12"] == "RULE-A12-v3"
    assert "RULE-A12-v2" in REGISTRY and "RULE-A12-v1" in REGISTRY
    assert [m.RULE_ID for m in V10] == ["RULE-A12-v3"]


# ------------------------------------------------------------------ unobserved_error

def _probe(params: dict, *, error_class, status):
    return Observation.make(
        "A10", "A10", "scan-x", "https://x/p", "lighthouse", "0.1.0", params,
        {"method": "GET", "url": "https://x/p"},
        {"status": status, "headers": {}, "body_sha256": None, "body_path": None,
         "bytes": 0, "elapsed_ms": 1},
        parsed={"probe": "invalid_route"}, error_class=error_class)


def test_unobserved_error_names_the_branch_that_fired():
    """Decision 2. `_common.unobserved` returns True for two different reasons and the note has
    to say which one."""
    params = {**load_params(), "reason_text": 2}
    refused = tuple(params["manners"]["unobservable_statuses"])
    assert 403 in refused, "this test is about a status the manners list names; it no longer does"

    # (a) the STATUS fired. The class is `http_4xx`, which is OBSERVED — not blind — so the
    #     only thing making this unobserved is the refusal status, and the note must say so.
    by_status = _probe(params, error_class="http_4xx", status=403)
    assert not scan_errors.is_blind("http_4xx", scan_errors.harness_of(params))
    assert _common.unobserved(by_status, params)
    f = _common.unobserved_error("RULE-A10-v3", "A10", [by_status], by_status, params, "the probe")
    assert "HTTP 403" in f.reason, f.reason
    assert "unobservable_statuses" in f.reason, f.reason
    assert scan_errors.note_for("http_4xx") not in f.reason, (
        "the class's note is printed for a probe the class did not blind")

    # (b) the CLASS fired. No response arrived at all, so the class's note is the evidence.
    by_class = _probe(params, error_class="connection_reset", status=None)
    assert scan_errors.is_blind("connection_reset", scan_errors.harness_of(params))
    g = _common.unobserved_error("RULE-A10-v3", "A10", [by_class], by_class, params, "the probe")
    assert "connection_reset" in g.reason
    assert scan_errors.note_for("connection_reset") in g.reason, g.reason
    assert "unobservable_statuses" not in g.reason


def test_the_contradiction_scheme_1_produces_is_real_and_is_preserved():
    """The defect, reproduced — and kept reproducible, because three stored Findings carry it.

    A probe with NO error class and a refusal status is unobserved (the status fired) and
    scheme 1 prints `note_for(None)`, which is *"the collector observed the surface"*. The same
    sentence calls the probe unobserved and its note says it was observed. Scheme 1 must keep
    saying it or the payloads that recorded it stop re-deriving; scheme 2 must not.
    """
    base = load_params()
    probe = _probe(base, error_class=None, status=403)
    old = _common.unobserved_error("RULE-A10-v3", "A10", [probe], probe,
                                   {**base, "reason_text": 1}, "the probe")
    new = _common.unobserved_error("RULE-A10-v3", "A10", [probe], probe,
                                   {**base, "reason_text": 2}, "the probe")
    assert "the collector observed the surface" in old.reason, (
        "the recorded contradiction no longer reproduces under scheme 1; every payload whose "
        "Findings carry it would stop re-deriving")
    assert "the collector observed the surface" not in new.reason
    assert "HTTP 403" in new.reason and "unobservable_statuses" in new.reason


def test_an_unversioned_params_set_gets_the_scheme_every_stored_finding_was_made_under():
    """The default is 1, and an unknown scheme is a hard error rather than a silent fallback —
    the same contract `rule_version` has, for the same reason."""
    assert _common.reason_text({}) is _common._note_scheme_1
    assert _common.reason_text({"reason_text": 1}) is _common._note_scheme_1
    assert _common.reason_text({"reason_text": 2}) is _common._note_scheme_2
    with pytest.raises(ValueError, match="not a known reason-text scheme"):
        _common.reason_text({"reason_text": 99})


def test_every_rule_that_calls_unobserved_error_still_reaches_the_same_verdicts():
    """The four callers, on a probe each of them scores on. The note changed; no branch did."""
    src_dir = REPO / "assessment" / "harness" / "scan" / "rules"
    callers = sorted(p.stem for p in src_dir.glob("rule_*.py")
                     if "unobserved_error" in p.read_text(encoding="utf-8"))
    assert callers == ["rule_a10_v3", "rule_a5_v2", "rule_a8_v3", "rule_a8_v4"], callers
    base = load_params()
    for scheme in (1, 2):
        params = {**base, "reason_text": scheme}
        obs = [_probe(params, error_class="http_4xx", status=403),
               Observation.make("A10", "A10", "scan-x", "https://x/", "lighthouse", "0.1.0",
                                params, {"method": "GET", "url": "https://x/"},
                                {"status": 200, "headers": {}, "body_sha256": None,
                                 "body_path": None, "bytes": 0, "elapsed_ms": 1},
                                parsed={"probe": "valid", "renderer": "none",
                                        "extent": {"visible_chars": 5000}})]
        f = judge_rule("RULE-A10-v3", obs, params)
        assert f.verdict == "error", (scheme, f.verdict)


# ------------------------------------------------------------------ the ninth fixture

def test_the_ninth_fixture_answers_robots_txt_with_a_404_carrying_html():
    """The control the set did not have. One request, no rate limit, loopback only.

    Every other fixture either serves a robots.txt, resets before any response, or — in
    `fails_all` — answers 200 with the soft-404 shell, which is the case `RULE-A12-v2`'s
    wrong-content-type branch was written for and gets RIGHT. The case it gets wrong had no
    control until now, which is why a live federal host was the first thing to find it.
    """
    from scan.fixtures.server import FixtureServer
    with FixtureServer("robots_404_html") as base:
        try:
            urllib.request.urlopen(f"{base}/robots.txt", timeout=5)
            pytest.fail("/robots.txt returned a success status; the fixture serves the file")
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
            assert exc.headers.get("Content-Type", "").startswith("text/html")
            assert b"<html" in exc.read()
        # …and the rest of the surface is `passes_all`, or the fixture would be testing two
        # things at once.
        with urllib.request.urlopen(f"{base}/index.html", timeout=5) as r:
            assert r.status == 200


def test_the_fixture_is_in_the_pre_registered_control_table():
    """A fixture the control cycle runs and the table does not name would make `RULE-E5-v2`
    report the cycle invalid; one the table names and no fixture provides, the same. The two
    lists are one list."""
    params = load_params()
    from scan.fixtures.server import MODES
    assert sorted(params["e5_control"]["expected_verdicts"]) == sorted(MODES)
    row = params["e5_control"]["expected_verdicts"]["robots_404_html"]
    assert row == {"default": "pass", "A4": "fail", "A11-declared": "fail", "A12": "fail"}


# ------------------------------------------------------------------ the re-judgement

#: The five payloads generation 10 wrote, and the payload each supersedes. A literal, because a
#: gate that reads its expectation out of the artifact under test can only ever pass.
GEN10 = [("scan_2026-09-07_rj2",  "scan_2026-09-07_rj3"),
         ("scan_2026-09-07b_rj3", "scan_2026-09-07b_rj4"),
         ("scan_2026-09-09_rj2",  "scan_2026-09-09_rj3"),
         ("scan_2026-09-10_rj2",  "scan_2026-09-10_rj3"),
         ("self_2026-09-13",      "self_2026-09-13_rj1")]

DIFF = REPO / "state" / "rejudgement_diff_2026-09-13.json"


def _diffs() -> dict:
    if not DIFF.is_file():
        pytest.skip(f"{DIFF.relative_to(REPO)} does not exist; the re-judgement has not run")
    return {d["new"]: d for d in json.loads(DIFF.read_text(encoding="utf-8"))}


def test_generation_ten_moved_no_verdict_anywhere():
    """Decision 3's gate, and it is stricter than every re-judgement before it.

    Generations 5 to 9 each corrected a JUDGEMENT, and their gate was "every move lands on
    `error` and something names it". This one corrects two SENTENCES. A verdict that moved would
    mean the change reached past the reason string into the decision, which is the one thing it
    must not do — so the number is zero and there is no permitted set to be within.
    """
    diffs = _diffs()
    assert sorted(diffs) == sorted(n for _o, n in GEN10), sorted(diffs)
    moved = {n: d["verdict_moves"] for n, d in diffs.items() if d["verdict_moves"]}
    assert not moved, moved
    for old, new in GEN10:
        d = diffs[new]
        assert d["old"] == old, (d["old"], old)
        assert not d["only_in_old"] and not d["only_in_new"], (
            f"{new} does not judge the same set as {old}")


def test_the_reasons_that_changed_are_the_two_this_generation_corrects():
    """What DID move, named. Every changed sentence must be one of the two corrections — the
    A12 branch order or the `unobserved_error` note — and nothing else.

    Read from the reason strings themselves rather than from the leg, because "A12 changed" is
    not evidence that A12 changed FOR THE RIGHT REASON: a rule that had also reworded an
    unrelated branch would show up on the same leg.
    """
    diffs = _diffs()
    total = 0
    for _old, new in GEN10:
        for r in diffs[new]["reason_changes"]:
            total += 1
            a12 = (_common.NO_ROBOTS_SERVED in r["to"]
                   and "content type that cannot be robots.txt" in r["from"]
                   or _common.NO_ROBOTS_SERVED in r["to"]
                   and "no robots.txt is served" in r["from"])
            note = "was not observed" in r["to"] and "was not observed" in r["from"]
            assert a12 or note, (
                f"{new} {r['target']} {r['leg']}: a reason changed that is neither of this "
                f"generation's two corrections\n  from: {r['from']}\n  to:   {r['to']}")
            assert r["verdict"] == r["verdict"]
    assert total > 0, "no reason changed at all; the generation did nothing"


def test_the_published_finding_with_the_false_sentence_is_superseded_by_a_true_one():
    """The one published Tier A Finding this generation exists for, followed through.

    `host:www.federalreserve.gov`'s A12 Finding in `scan_2026-09-10_rj2` says the host served a
    robots.txt with the wrong content type; the host answered 404. Its successor in
    `scan_2026-09-10_rj3` says what the evidence says, at the same verdict.
    """
    diffs = _diffs()
    rows = [r for r in diffs["scan_2026-09-10_rj3"]["reason_changes"]
            if r["target"] == FEDRES and r["leg"] == "A12"]
    assert len(rows) == 1, rows
    r = rows[0]
    assert r["verdict"] == "fail"
    assert r["rule"] == "RULE-A12-v2 -> RULE-A12-v3"
    assert "content type that cannot be robots.txt" in r["from"]
    assert _common.NO_ROBOTS_SERVED in r["to"] and "HTTP 404" in r["to"]


def test_no_re_judged_payload_records_evidence_or_a_request():
    """A re-judgement creates no Observation and contacts no host. Asserted on the payloads,
    because it is the claim that makes re-judging history legitimate at all."""
    for _old, new in GEN10:
        p = REPO / "state" / f"{new}.json"
        if not p.is_file():
            pytest.skip(f"{new} has not been written")
        body = json.loads(p.read_text(encoding="utf-8"))
        assert body["observations_detail"] == []
        assert body["requests_total"] == 0 and body["requests_per_host"] == {}
        assert body["cycle_kind"] == "rejudged"
        assert body["control_verdict"] == "pass"
