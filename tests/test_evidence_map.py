"""The evidence map (`cc_tasks/2026-10-02_evidence_map_record.md`, DN-009 decision 2).

Three things the task asks for, and the controls that show each check can fail:

* idempotence: `docs/evidence/claims.yaml` is what `scripts/build_evidence_map.py` renders now,
  byte for byte, and a second render is identical;
* every `record` and `needs_measurement` claim's evidence resolves: a Finding on the cycle of
  record (in the projection and at the line its locator names), a Result on the graph, an
  admitted corpus document, a framework record node, or a named query;
* every numeral in a claim's prose is on that claim's `numbers` list, and the list equals the
  script's freshly computed values.

The graph is required for a render; when Neo4j is down the graph tests skip, as the brief
pack's do, and the pure tests (the classifiers and the numeral scan) still run.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import build_evidence_map as E  # noqa: E402

TASK = E.TASK


@pytest.fixture(scope="module")
def graph():
    import build_brief_pack as BP
    g = BP.graph_or_none(required=False)
    if g is None:
        pytest.skip("Neo4j unreachable; the evidence map's record claims are unverified")
    return g


@pytest.fixture(scope="module")
def rendered(graph):
    return E.render(graph)


@pytest.fixture(scope="module")
def on_disk():
    return yaml.safe_load(E.CLAIMS.read_text(encoding="utf-8"))


def ours(doc):
    return [c for c in doc["claims"] if c.get("source_task") == TASK]


# ------------------------------------------------------------------------ idempotence

def test_claims_file_regenerates_byte_for_byte(rendered):
    assert E.CLAIMS.read_text(encoding="utf-8") == rendered, (
        "docs/evidence/claims.yaml has drifted from the record; re-run "
        "scripts/build_evidence_map.py")


def test_a_second_render_is_identical(graph, rendered):
    assert E.render(graph) == rendered


# ------------------------------------------------------------------------ schema

def test_every_claim_has_the_schema(on_disk):
    ids = [c["id"] for c in on_disk["claims"]]
    assert len(ids) == len(set(ids)), "duplicate claim ids"
    for c in on_disk["claims"]:
        assert re.fullmatch(r"CL-\d{3,}", c["id"]), c["id"]
        assert c["status"] in E.STATUSES, c
        assert c["text"].strip() and c["source_task"], c
        for e in c["evidence"]:
            assert e["kind"] in E.EVIDENCE_KINDS, e
            assert e["id"] and e["locator"], e
    # This task writes only record and needs_measurement entries (task decision 1).
    assert {c["status"] for c in ours(on_disk)} <= {"record", "needs_measurement"}
    assert all(c["evidence"] for c in ours(on_disk)), "a record claim with no evidence"


# ------------------------------------------------------------------------ evidence resolves

def test_every_record_claims_evidence_resolves(graph, on_disk):
    import json
    m = E.Map(graph)
    record_ids = {n["id"] for n in m.s.record["nodes"]}
    included = {k for k, v in m.s.manifest.items() if v["screening"]["decision"] == "included"}
    fids, rids = set(), set()
    for c in ours(on_disk):
        for e in c["evidence"]:
            k, i = e["kind"], e["id"]
            if k == "finding":
                fids.add(i)
                path, line = e["locator"].rsplit(":", 1)
                row = (REPO / path).read_text(encoding="utf-8").splitlines()[int(line) - 1]
                assert json.loads(row)["finding_id"] == i, f"{c['id']}: {e['locator']} is not {i}"
            elif k == "indicator":
                assert i in record_ids, f"{c['id']}: {i} is not a record node"
            elif k == "document":
                assert i in included, f"{c['id']}: {i} is not an admitted document"
                path, line = e["locator"].rsplit(":", 1)
                row = (REPO / path).read_text(encoding="utf-8").splitlines()[int(line) - 1]
                ev = json.loads(row)
                assert ev["event_type"] == "manifest_add"
                assert (ev.get("doc_id") or ev["payload"]["doc_id"]) == i
            elif k == "result":
                rids.add(i)
            elif k == "query":
                assert i in E.QUERIES, f"{c['id']}: query {i} is not named in QUERIES"
    rows, _ = graph.read("MATCH (f:Finding {cycle: $c}) WHERE f.finding_id IN $ids "
                         "RETURN f.finding_id AS id", limit=len(fids) + 1, c=m.cycle,
                         ids=sorted(fids))
    assert {r["id"] for r in rows} == fids, "a cited Finding is not on the cycle of record"
    rows, _ = graph.read("MATCH (r:Artifact:Result) WHERE r.artifact_id IN $ids "
                         "RETURN r.artifact_id AS id", limit=len(rids) + 1, ids=sorted(rids))
    assert {r["id"] for r in rows} == rids, "a cited Result is not on the graph"


# ------------------------------------------------------------------------ numbers

def test_every_numeral_in_a_claim_is_on_its_numbers_list(on_disk):
    for c in on_disk["claims"]:
        held = {d["value"] for d in c.get("numbers") or []}
        stray = [x for x in E.numerals(c["text"]) if x not in held]
        assert not stray, f"{c['id']}: numerals {stray} are not on its numbers list"


def test_every_number_equals_the_scripts_computed_value(rendered, on_disk):
    fresh = {c["key"]: c for c in ours(yaml.safe_load(rendered))}
    for c in ours(on_disk):
        assert c["key"] in fresh, f"{c['id']} ({c['key']}) is no longer computed"
        assert c["numbers"] == fresh[c["key"]]["numbers"], c["id"]
        assert c["text"] == fresh[c["key"]]["text"], c["id"]


def test_the_numeral_scan_sees_a_typed_number():
    """Positive control: a typed number in prose is seen; a backticked one is not."""
    assert E.numerals("there are 1,009 findings and 0.2 of it") == ["1,009", "0.2"]
    assert E.numerals("leg `A10` on `scan_2026-09-10_rj4` (`DN-009 decision 6`)") == []


# ------------------------------------------------------------------------ other tasks' claims

def test_other_tasks_claims_are_carried_through_and_ids_are_not_reused(graph, monkeypatch,
                                                                       tmp_path, on_disk):
    foreign = {"id": "CL-900", "key": "prior_art.example", "question": "prior art",
               "text": "A claim the prior-art task owns.", "status": "prior_art",
               "evidence": [{"kind": "document", "id": "x", "locator": "y"}],
               "numbers": [], "source_task": "cc_tasks/2026-10-02_evidence_map_prior_art.md"}
    dropped = dict(ours(on_disk)[0])
    kept = [c for c in on_disk["claims"] if c["key"] != dropped["key"]]
    p = tmp_path / "claims.yaml"
    p.write_text(yaml.safe_dump({"claims": kept + [foreign]}, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(E, "CLAIMS", p)
    out = yaml.safe_load(E.render(graph))
    by_id = {c["id"]: c for c in out["claims"]}
    assert by_id["CL-900"] == foreign, "another task's claim was not carried through"
    regained = next(c for c in out["claims"] if c["key"] == dropped["key"])
    assert int(regained["id"][3:]) > 900, "a new key reused an id below the file's highest"
    for c in kept:
        if c.get("source_task") == TASK:
            assert by_id[c["id"]]["key"] == c["key"], f"{c['id']} was renumbered"


# ------------------------------------------------------------------------ classifiers

@pytest.mark.parametrize("verdict, reason, classes, want", [
    ("error", "the surface could not be observed: refused", ["refused"], "access_denial"),
    ("error", "markup could not be extracted: robots_disallowed", ["robots_disallowed"],
     "access_denial"),
    ("error", "the catalog could not be observed: http_5xx", ["http_5xx"], "error_other"),
    ("fail", "the host answered HTTP 403 to /robots.txt itself for x", ["refused"],
     "access_denial"),
    ("fail", "robots.txt DISALLOWS the product path for 8 of 8 AI-crawler user agents", [],
     "access_denial"),
    ("fail", "no licence in the product page's markup, in an HTTP Link header", [], "absence"),
    ("fail", "a catalog is served at https://www.census.gov/data.json but the product is not "
             "in it: no record names it", [], "absence"),
    ("fail", "only PDF served; first: https://example.gov/a.pdf", [], "nonconformant"),
    ("pass", "anything", [], "pass"),
])
def test_q2_category(verdict, reason, classes, want):
    f = {"finding_id": "fnd_x", "verdict": verdict, "reason": reason}
    assert E.q2_category(f, classes) == want


def test_q2_category_refuses_a_reason_it_cannot_place():
    with pytest.raises(SystemExit):
        E.q2_category({"finding_id": "fnd_x", "verdict": "fail", "reason": "something new"}, [])


def test_q1_requirement_classes():
    assert E.req_class({"kind": "open_source", "who_provides": "this_project"}) == "open_tooling"
    assert E.req_class({"kind": "hosted_paid", "who_provides": "this_project"}) == "funding"
    assert E.req_class({"kind": "benchmark_set", "who_provides": "this_project"}) == "no_standard"
    assert E.req_class({"kind": "open_source", "who_provides": "publisher"}) == \
        "agency_cooperation"
    with pytest.raises(SystemExit):
        E.req_class({"id": "x", "kind": "telepathy", "who_provides": "this_project"})


def test_q1_partition_covers_every_unmeasured_framework_indicator(on_disk):
    rows = on_disk["tables"]["q1_measurement_boundary"]
    import json
    rec = json.loads((REPO / E.RECORD_PATH).read_text(encoding="utf-8"))
    from framework_writeback import _candidate_ids
    cand = _candidate_ids(rec)
    want = sorted(n["properties"]["code"] for n in rec["nodes"]
                  if "AssessmentIndicator" in n["labels"] and n["id"] not in cand
                  and n["properties"]["measurement_status"] != "measured")
    assert sorted(r["indicator"] for r in rows) == want
    assert {r["class"] for r in rows} <= set(E.Q1_ORDER) | {E.Q1_NOT_BLOCKED}
