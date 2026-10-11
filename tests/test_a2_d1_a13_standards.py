"""The standards behind A2, D1 and A13, and the discoverability claims
(`cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards.md`).

Stdlib + pyyaml. Nothing here needs Neo4j, the network or the gitignored corpus files: the
admission is checked on the committed ledger, event log and manifest; the binding on the
committed framework record; the Results' values on the committed delta table.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import add_candidate_indicator as ACI  # noqa: E402
import admit_a2_d1_a13_standards as ADM  # noqa: E402
import dn001_floor as FLOOR  # noqa: E402
import register_seeded_delta_results as REG  # noqa: E402

RECORD = REPO / "framework" / "ai_readiness_framework.json"
#: indicator -> the documents decision 1 binds to it. `openapi-specification-core` was admitted
#: by kernel-v03 and is bound here, not re-admitted.
BOUND = {"A2": {"openapi-specification-core", "openapi-specification-v2-0"},
         "D1": {"spdx-license-list", "cc-by-4-0-deed", "cc0-1-0-deed"},
         "A13": {"rfc-9727-api-catalog"}}
ADMITTED = {d["doc_id"] for d in ADM.DOCS}


def _entries() -> dict:
    m = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    return m["entries"]


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------ admission

def test_the_five_documents_are_included_verified_standards():
    e = _entries()
    assert ADMITTED == {"openapi-specification-v2-0", "spdx-license-list", "cc-by-4-0-deed",
                        "cc0-1-0-deed", "rfc-9727-api-catalog"}
    for d in ADMITTED:
        assert e[d]["screening"]["decision"] == "included", d
        assert e[d]["integrity"]["status"] == "verified", d
        assert e[d]["identity"]["canonical_path"] == f"corpus/kernel/{d}.md", d


def test_each_manifest_add_carries_its_fetch_its_capture_hash_and_its_licence():
    rows = [json.loads(l) for l in
            (REPO / "events" / "batch-001.jsonl").read_text(encoding="utf-8").split("\n")
            if l.strip() and '"manifest_add"' in l]
    adds = {r["payload"]["doc_id"]: r["payload"] for r in rows
            if r["payload"]["doc_id"] in ADMITTED}
    assert set(adds) == ADMITTED
    for d, p in adds.items():
        acq = p["acquisition"]
        assert p["source_type"] == "standard", d
        assert acq["acquired_by"] == "scripts/fetch_allowlisted.py", d
        assert acq["fetch_log"] == "logs/2026-10-11_standards_fetch.jsonl", d
        assert len(acq["capture_sha256"]) == 64 and acq["capture_sha256"] != p["content_hash"]
        assert acq["verification"]["sha256"] == p["content_hash"], d
        assert acq["licence"].strip(), f"{d}: no licence recorded"
        assert acq["fetched_from"] == p["primary_url"], d


def test_the_epoch_is_declared_with_the_five_members():
    ev = [json.loads(l) for l in
          (REPO / "corpus" / "evidence" / "decisions.jsonl").read_text(encoding="utf-8")
          .split("\n") if ADM.EPOCH in l]
    decl = [e for e in ev if e["event_type"] == "corpus_epoch_declared"]
    assert len(decl) == 1
    assert set(decl[0]["payload"]["member_doc_ids"]) == ADMITTED


def test_openapi_3x_is_the_document_already_held_not_a_second_copy():
    """Corpus before web (DN-001 decision 4): the rule accepts any `3.x`, and the corpus holds
    OAS 3.2.0, so no 3.x document is among this task's admissions."""
    e = _entries()
    assert e["openapi-specification-core"]["screening"]["decision"] == "included"
    assert not any("3.1" in e[d]["identity"].get("title", "") for d in ADMITTED)
    from scan.rules import rule_a2_v5
    assert rule_a2_v5._DESCRIPTION_VERSION.match("3.2.0")
    assert rule_a2_v5._DESCRIPTION_VERSION.match("2.0")


# ------------------------------------------------------------------------ binding

def test_a2_d1_and_a13_are_evidenced_by_their_standards_and_a2_d1_carry_no_gap():
    g = _record()
    included = {k for k, v in _entries().items() if v["screening"]["decision"] == "included"}
    for code, docs in BOUND.items():
        got = {e["to"][len("doc:"):] for e in g["edges"]
               if e["from"] == f"ind:{code}" and e["type"] == "EVIDENCED_BY"}
        assert docs <= got, f"ind:{code} lacks {sorted(docs - got)}"
        assert got <= included, f"ind:{code} cites an unadmitted document"
    nodes = {n["id"]: n["properties"] for n in g["nodes"]}
    for code in ("A2", "D1"):
        assert not nodes[f"ind:{code}"].get("gap"), code
        for d in BOUND[code]:
            assert f"`{d}`" in nodes[f"ind:{code}"]["evidence_raw"], (code, d)
    assert "named, not admitted" not in nodes["ind:A13"]["evidence_raw"]


def test_every_binding_is_named_by_the_rule_that_already_cites_it():
    """Decision 1: an admitted source binds only where the rule's text already cites it."""
    rules = REPO / "assessment" / "harness" / "scan" / "rules"
    assert "Swagger 2.0" in (rules / "rule_a2_v6.py").read_text(encoding="utf-8")
    assert "OpenAPI 3.x" in (rules / "rule_a2_v6.py").read_text(encoding="utf-8")
    assert "RFC 9727" in (rules / "rule_a13.py").read_text(encoding="utf-8")
    p = yaml.safe_load((REPO / "assessment" / "harness" / "scan" / "params.yaml")
                       .read_text(encoding="utf-8"))["d1_licence"]
    assert "https://spdx.org/licenses/" in p["recognised_prefixes"]
    assert "https://creativecommons.org/" in p["recognised_prefixes"]
    assert {"CC0", "CC-BY"} <= set(p["recognised_tokens"])


def test_refresh_adds_a_missing_evidence_edge_and_never_removes_one(monkeypatch):
    g = _record()
    rfc = "doc:rfc-9727-api-catalog"
    g["edges"] = [e for e in g["edges"] if not (e["from"] == "ind:A13" and e["to"] == rfc)]
    extra = {"from": "ind:A13", "type": "EVIDENCED_BY", "to": "doc:w3c-dwbp-2017-extra",
             "properties": {"doc_id": "w3c-dwbp-2017-extra"}}
    g["edges"].append(extra)
    out = ACI.refresh(g, "A13")
    assert out["evidenced_by_added"] == [rfc]
    assert extra in g["edges"], "a refresh removed an edge"
    assert ACI.refresh(g, "A13")["evidenced_by_added"] == [], "a second refresh is not a no-op"


def test_refresh_refuses_a_document_the_manifest_does_not_hold(monkeypatch):
    cands = copy.deepcopy(ACI.CANDIDATES)
    cands["A13"]["evidenced_by"] = cands["A13"]["evidenced_by"] + ["not-an-admitted-doc"]
    monkeypatch.setattr(ACI, "CANDIDATES", cands)
    with pytest.raises(SystemExit):
        ACI.refresh(_record(), "A13")


# ------------------------------------------------------------------------ Results

def test_the_registered_values_are_the_delta_tables():
    d = json.loads(REG.DELTA.read_text(encoding="utf-8"))
    vals = {name: v for name, v, _, _ in REG.results(d)}
    h = d["headline"]
    sfx = REG.CYCLE_SUFFIX
    assert vals[f"seeded_delta_pairs_exist_unreachable_{sfx}"] == \
        h["pairs_exist_unreachable_from_every_product_page"]
    assert vals[f"seeded_delta_pairs_exist_{sfx}"] == h["pairs_exist"]
    # The per-object Results partition the headline.
    assert sum(vals[f"seeded_delta_{o}_pairs_exist_{sfx}"] for o in REG.OBJECTS) == \
        h["pairs_exist"]
    assert sum(vals[f"seeded_delta_{o}_pairs_exist_unreachable_{sfx}"] for o in REG.OBJECTS) == \
        h["pairs_exist_unreachable_from_every_product_page"]
    assert len(vals) == len(REG.results(d)), "two Results share a name"


# ------------------------------------------------------------------------ claims and floor

def test_the_claims_file_carries_the_discoverability_claims():
    claims = yaml.safe_load((REPO / "docs" / "evidence" / "claims.yaml")
                            .read_text(encoding="utf-8"))["claims"]
    keys = {c["key"]: c for c in claims}
    for k in ("q7.discoverability.headline", "q7.discoverability.convention",
              "q7.existence.A2", "q7.existence.D1") + tuple(
            f"q7.discoverability.{o}" for o in REG.OBJECTS):
        assert k in keys, k
    assert any(k.startswith("q7.a13.") for k in keys)
    head = keys["q7.discoverability.headline"]
    assert {n["source"].split()[0] for n in head["numbers"]} == {"Result"}
    for leg in ("A2", "D1"):
        docs = {e["id"] for e in keys[f"q7.existence.{leg}"]["evidence"]
                if e["kind"] == "document"}
        assert BOUND[leg] <= docs, leg


def test_quoted_legs_reads_findings_and_result_names():
    claims = {"claims": [
        {"id": "CL-1", "evidence": [{"kind": "finding", "id": "f1"}]},
        {"id": "CL-2", "evidence": [
            {"kind": "result", "id": "uuid-1", "note": "scan_l0_product_d1_fail_x, value 3"},
            {"kind": "result", "id": "uuid-2", "note": "scan_a2_pass_x, value 0, state p"},
            {"kind": "result", "id": "uuid-3", "note": "seeded_delta_api_pairs_exist_x"}]},
    ]}
    payload = {"findings_detail": [{"finding_id": "f1", "leg": "A13"}]}
    assert FLOOR.quoted_legs(claims, payload) == {"A13": ["CL-1"], "A2": ["CL-2"],
                                                   "D1": ["CL-2"]}
