"""Nothing on the log without its evidence; nothing in the tree the tests left behind.

`cc_tasks/2026-09-07_scan_hygiene.md` §4 — the one gate of that task, and the standing reader
for three properties that were true by nobody's doing until it existed:

1. **A test cannot write into the committed evidence store.** `corpus/evidence/scan/` is the
   one `corpus/` lane that is tracked, and the control fixture server binds an ephemeral port
   which lands in every body carrying `HOSTPORT` — so content addressing did not dedupe the
   litter, it minted a fresh digest per run. 260 blobs were committed this way.
2. **A Finding whose evidence the log does not hold is annotated as such.** Invariant 3 says
   no grounding span, no write; a verdict citing `obs_id`s that no event carries is the same
   claim with the same defect. The 120 orphaned control Findings of 2026-09-06 keep their ids
   and carry a `finding_evidence_unretained` event; `publish.py` refuses to make a new one.
3. **The framework of record agrees with itself.** Every `counts` key is regenerated from
   `nodes`/`edges` by one function with one stated denominator per key, and every
   `EVIDENCED_BY_INTERNAL` edge has one shape.

The Neo4j-backed checks SKIP rather than fail when the database is down, for the reason
`tests/test_framework_projection_roundtrip.py` gives: a developer without the database gets a
green suite and an unverified claim, never a falsely green one.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from scan import load_params                                        # noqa: E402
from scan.fixtures.server import BIND_HOST, FixtureServer           # noqa: E402
from scan.model import EVIDENCE_ROOT                                # noqa: E402

import framework_writeback as fw                                    # noqa: E402
import quarantine_fixture_evidence as qfe                           # noqa: E402

def _evidence_store_status() -> str:
    """`git status --porcelain` for the committed evidence store."""
    out = subprocess.run(["git", "status", "--porcelain", "--",
                          str(EVIDENCE_ROOT.relative_to(REPO))],
                         capture_output=True, text=True, cwd=REPO)
    assert out.returncode == 0, out.stderr
    return out.stdout


#: Snapshotted at IMPORT, which pytest does during collection — before any test in the session
#: runs. §4's clause is "after `pytest tests/ assessment/`, `git status --porcelain corpus/` is
#: empty", and what it means is that the SUITE leaves no litter; comparing the end state
#: against a fixed empty string would instead fail on whatever the operator happens to have
#: uncommitted, which is a different claim and a gate nobody could keep green. Comparing
#: against the baseline says exactly the intended thing and says it whatever order the tests
#: run in.
_EVIDENCE_STATUS_AT_COLLECTION = _evidence_store_status()

#: The count recorded by `cc_tasks/2026-09-07_scan_hygiene.md` §1 and registered as
#: `scan_control_findings_evidence_unretained_2026-09-06`. A literal, because a gate that reads
#: its expectation out of the artifact under test can only ever pass — the same reasoning as
#: `EXPECTED_MEASUREMENT_STATUS` in the framework round-trip gate.
EXPECTED_UNRETAINED = 120


@pytest.fixture(scope="module")
def graph():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                            # noqa: BLE001 - see the docstring
        pytest.skip(f"Neo4j unreachable, scan hygiene unverified in the graph: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


# --------------------------------------------------------------- §2: the tree stays clean
def test_a_fixture_collection_writes_nothing_into_the_committed_evidence_store():
    """The property behind §4's `git status --porcelain corpus/` clause, asserted directly.

    Driving a real control-fixture collection is the only honest test of the guard: a run of
    `tests/test_scan_harness.py` did exactly this and left 24 blobs behind each time. Counting
    the real root before and after is what the operator would have had to do by hand.
    """
    from scan.collectors import http
    from scan.manners import Fetcher
    params = load_params()
    before = sorted(p.name for p in EVIDENCE_ROOT.rglob("*") if p.is_file())
    with FixtureServer("passes_all") as base:
        obs = http.fetch(Fetcher(params), "A1", "control:passes_all", f"{base}/index.html",
                         params, parse_links=True)
    assert obs, "the fixture collection produced no observation, so it proves nothing"
    after = sorted(p.name for p in EVIDENCE_ROOT.rglob("*") if p.is_file())
    assert after == before, (
        f"a fixture collection wrote {len(after) - len(before)} blob(s) into the committed "
        f"evidence store at {EVIDENCE_ROOT}")


def test_the_committed_evidence_store_holds_no_uncited_fixture_output():
    """§4's fixture-host clause, with the discriminator the task file got wrong.

    The task asked for ZERO blobs naming the fixture host. Eight of them are the control
    cycle's OWN evidence — the bytes its Observations cite — and quarantining those would
    strand live Observations, which is the very defect §1 exists to annotate. The check that
    means what the clause meant is: no fixture body that NOTHING on the log points at.
    """
    c = qfe.classify()
    assert c["litter"] == [], (
        f"{len(c['litter'])} fixture-host blob(s) under {EVIDENCE_ROOT} are cited by no "
        f"Observation on the event log; run scripts/quarantine_fixture_evidence.py")
    for p in c["cited_fixture_blobs"]:
        assert qfe.MARKER in p.read_bytes()          # the classifier means what it says
    assert c["cited_fixture_blobs"], (
        "no fixture body is cited by any Observation — the control cycle's evidence has gone "
        "missing, which is a worse finding than the litter this test was written for")


def test_the_suite_leaves_the_evidence_store_exactly_as_it_found_it():
    """§4's `git status --porcelain` clause, as a DELTA against collection time.

    `assessment/` is out of `tests/conftest.py`'s reach and so out of the guard's; it is also
    measured to write nothing here — it imports no part of the scan package. If that ever
    changes, the guard moves to a conftest both trees see, and this docstring is the record of
    why it was not needed on 2026-09-07.
    """
    now = _evidence_store_status()
    assert now == _EVIDENCE_STATUS_AT_COLLECTION, (
        "the test session changed the committed evidence store.\n"
        f"at collection:\n{_EVIDENCE_STATUS_AT_COLLECTION}\nnow:\n{now}")


# ------------------------------------------------- §1: no Finding without its evidence
def test_every_orphan_finding_on_the_log_carries_an_unretained_annotation():
    """The log's own answer, independent of the graph: `finding_derived` events citing an
    `obs_id` no `observation_recorded` event carries, minus the annotated ones, is empty."""
    import annotate_orphan_findings as ann
    orphans = {ev["finding_id"] for ev in ann.orphans()}
    annotated = ann.annotated()
    assert len(orphans) == EXPECTED_UNRETAINED, (
        f"{len(orphans)} Findings on the log cite evidence the log does not hold; "
        f"{EXPECTED_UNRETAINED} were recorded by cc_tasks/2026-09-07_scan_hygiene.md §1. A "
        f"NEW one is a defect in whatever published it, not a number to update here.")
    assert orphans - annotated == set(), (
        f"{len(orphans - annotated)} orphan Finding(s) carry no annotation: "
        f"{sorted(orphans - annotated)[:5]}")


def test_publish_refuses_a_finding_whose_evidence_is_not_on_the_log(tmp_path, monkeypatch):
    """§1's standing rule, on one synthetic orphan. This is what did not exist on 2026-09-06.

    The event log is redirected onto `tmp_path`, so the refusal is exercised against an empty
    log rather than the real one — and the autouse guard in `conftest.py` would refuse the
    write anyway if the refusal failed to fire.
    """
    from kg import eventlog
    from scan import publish
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")

    payload = {
        "cycle": "synthetic", "params_hash": "0" * 64,
        "observations_detail": [],
        "findings_detail": [{"finding_id": "fnd_synthetic_orphan", "rule_id": "RULE-A1-v1",
                             "rule_version": "v1", "spec_code": "A1", "leg": "A1",
                             "target_doc_id": "control:passes_all", "verdict": "pass",
                             "evidence": ["obs_that_was_never_recorded"], "reason": "synthetic",
                             "params_hash": "0" * 64}],
    }
    with pytest.raises(SystemExit) as exc:
        publish.write_events(payload)
    assert "obs_ids that are neither on the log" in str(exc.value)
    assert not (tmp_path / "events").exists() or not any(
        (tmp_path / "events").iterdir()), "a refused payload still wrote to the log"


def test_publish_admits_the_same_finding_once_it_is_annotated(tmp_path, monkeypatch):
    """The other branch: the annotation is what licenses it, so the refusal cannot be a wall
    the 120 recorded Findings could never get back through."""
    from kg import eventlog
    from scan import publish
    events = tmp_path / "events"
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    eventlog.append({"event_type": publish.UNRETAINED_EVENT,
                     "finding_id": "fnd_synthetic_orphan", "reason": "synthetic"},
                    batch=publish.SCAN_BATCH)
    payload = {
        "cycle": "synthetic", "params_hash": "0" * 64,
        "observations_detail": [],
        "findings_detail": [{"finding_id": "fnd_synthetic_orphan", "rule_id": "RULE-A1-v1",
                             "rule_version": "v1", "spec_code": "A1", "leg": "A1",
                             "target_doc_id": "control:passes_all", "verdict": "pass",
                             "evidence": ["obs_that_was_never_recorded"], "reason": "synthetic",
                             "params_hash": "0" * 64}],
    }
    out = publish.write_events(payload)
    assert out["finding_events_written"] == 1
    assert out["findings_evidence_unretained"] == 1


def test_no_finding_in_the_graph_is_both_unsupported_and_unannotated(graph):
    """§4's Cypher clause, verbatim. Labelled, per the lint from `230b282f`."""
    n = graph.run(
        "MATCH (f:Finding) WHERE NOT (:Observation)-[:SUPPORTS]->(f) "
        "AND coalesce(f.evidence_unretained, false) = false RETURN count(f) AS n"
    ).single()["n"]
    assert n == 0, f"{n} Finding(s) have no supporting Observation and no annotation"
    annotated = graph.run(
        "MATCH (f:Finding) WHERE f.evidence_unretained = true RETURN count(f) AS n"
    ).single()["n"]
    assert annotated == EXPECTED_UNRETAINED, (
        f"the graph projects {annotated} annotated Findings, not {EXPECTED_UNRETAINED}; the "
        f"projection is stale or the annotation shard changed")


# ------------------------------------------------- §3: the framework agrees with itself
def test_the_framework_counts_are_a_derivation_not_a_memory():
    """`counts` equals a recount of `nodes`/`edges`, key for key.

    The denominators differ between keys ON PURPOSE and `framework_writeback.recount` states
    which is which: the framework's own content excludes candidate indicators (DD-054), the
    instrument's content does not. That is why this compares against the function rather than
    against a literal — a literal here would have to be edited every time a real number moved,
    which is how a gate becomes a rubber stamp.
    """
    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    fresh = fw.recount(g)
    stored = {k: g["counts"].get(k) for k in fresh}
    assert stored == fresh, f"counts drift: {fw.check(g)['counts_drift']}"


def test_rules_built_is_the_number_of_rules_actually_built():
    """The one `counts` key `recount` cannot derive from the JSON, checked against its real
    source. Five spec `rule_id`s name rules that were never built, so the specs cannot supply
    it and the rules package must."""
    from scan.rules import CURRENT
    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    assert g["counts"]["rules_built"] == len(set(CURRENT.values()))


def test_every_internal_evidence_reference_has_the_same_shape():
    """One writer wrote `{to: <ref>, properties: {ref}}` and another
    `{to: "internal:<ref>", properties: {artifact_path}}`; the loader was taught to read both,
    which kept the projection right and left the record ambiguous."""
    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    edges = [e for e in g["edges"] if e["type"] == "EVIDENCED_BY_INTERNAL"]
    assert edges, "no EVIDENCED_BY_INTERNAL edges at all — the fixture for this test is gone"
    assert {tuple(sorted((e.get("properties") or {}).keys())) for e in edges} == {("artifact_path",)}
    assert all(str(e["to"]).startswith("internal:") for e in edges)
    assert all(e["properties"]["artifact_path"] == str(e["to"]).removeprefix("internal:")
               for e in edges)


def test_the_counts_basis_is_recorded_on_the_face_of_the_framework():
    """A number in `counts` is unreadable without its denominator, and a reader of the JSON
    should not have to find a script to learn it."""
    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    assert g.get("counts_basis") == fw.COUNTS_BASIS


def test_the_normalize_write_back_is_idempotent():
    """Re-running it on the file it produced changes nothing — the same reader
    `test_the_rule_write_back_is_idempotent` is for the other write-back."""
    import framework_writeback_normalize as norm
    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    before = json.dumps(g, sort_keys=True)
    assert norm.normalize(g) == {"key_renamed": 0, "prefix_added": 0}
    fw.apply_counts(g)
    assert json.dumps(g, sort_keys=True) == before


def test_the_fixture_host_is_named_once():
    """`BIND_HOST` is the single definition of what the control fixtures look like: the server
    binds it and the quarantine sweep recognises stored bodies by it. Two literals would be two
    definitions, and the one that drifted would be the one that mattered."""
    assert qfe.MARKER == f"{BIND_HOST}:".encode()
    src = (REPO / "assessment" / "harness" / "scan" / "fixtures" / "server.py").read_text(
        encoding="utf-8")
    assert src.count(f'"{BIND_HOST}"') == 1
