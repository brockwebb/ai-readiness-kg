"""The framework as a graph: parse, round trip, and the loaded counts.

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §2. The round trip is the gate that
lets the JSON become the source of truth (DD-050): a record that cannot reproduce the document
it replaces is not a record. These tests hold that gate closed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import build_framework_graph as bfg  # noqa: E402
import render_framework as rf  # noqa: E402

JSON_PATH = REPO / "framework" / "ai_readiness_framework.json"
SKELETON = REPO / "docs" / "crosswalk" / "usafacts_operationalization_skeleton.md"
SCHEMA = yaml.safe_load((REPO / "kg" / "schema.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def graph():
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ the schema boundary
def test_assessment_labels_are_invisible_to_the_extraction_parser():
    """The assessment layer is AUTHORED. If its labels were in `node_types`, a model reading a
    source document could mint an `AssessmentIndicator` — a document rewriting the framework
    that measures it. Same reasoning that kept `Term` out of the whitelist (DD-044 §4)."""
    from kg.extraction import schema_loader
    live = schema_loader.load_schema()
    assessment = set(SCHEMA["assessment_layer"]["node_types"])
    assert assessment, "assessment_layer is missing from the schema"
    assert not (schema_loader.node_types(live) & assessment)
    assert not (set(schema_loader.edge_types(live)) & set(SCHEMA["assessment_layer"]["edge_types"]))
    assert SCHEMA["assessment_layer"]["parser_visible"] is False


def test_cq_27s_missing_edge_type_now_exists_in_the_parser_whitelist():
    """Issue `2a2b6461`: the graph held 506 Framework and 502 Instrument nodes and ZERO edges
    between them, because no edge type had that domain and range. CQ-27 could not be asked."""
    from kg.extraction import schema_loader
    et = schema_loader.edge_types(schema_loader.load_schema())
    assert "operationalized_by" in et
    assert [list(p) for p in et["operationalized_by"]["pairs"]] == [["Framework", "Instrument"]]


def test_the_schema_epoch_advanced_to_v04():
    assert tuple(int(x) for x in SCHEMA["schema_version"].split(".")[:2]) >= (0, 4)


# ------------------------------------------------------------------ the parse
def test_every_indicator_row_in_the_skeleton_is_parsed(graph):
    """A row the parser cannot represent is a listed diff, never a silent drop."""
    in_doc = len(re.findall(r"^\| [A-G]\d{1,2} \|", SKELETON.read_text(encoding="utf-8"), re.M))
    inds = [n for n in graph["nodes"] if "AssessmentIndicator" in n["labels"]]
    # G1 is two nodes under one row (DD-036), so nodes = rows + 1
    assert len(inds) == in_doc + 1
    assert graph["unparsed_rows"] == []


def test_g1_is_two_indicator_nodes_under_one_construct(graph):
    legs = [n["properties"] for n in graph["nodes"]
            if n["properties"].get("g1_leg_of") == "G1"]
    assert sorted(p["code"] for p in legs) == ["G1-D", "G1-O"]
    assert {p["type"] for p in legs} == {"AUTO", "EVAL"}
    assert len({p["construct"] for p in legs}) == 1


def test_an_evidence_doc_id_becomes_an_edge_only_if_the_manifest_holds_it(graph):
    manifest = set(json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"])
    for e in graph["edges"]:
        if e["type"] == "EVIDENCED_BY":
            assert e["properties"]["doc_id"] in manifest
    # and the ones that are NOT in the manifest are reported, not dropped in silence
    assert isinstance(graph["evidence_doc_ids_not_in_manifest"], list)


def test_a_gap_cell_keeps_its_own_stated_reason(graph):
    gaps = [n["properties"] for n in graph["nodes"]
            if "AssessmentIndicator" in n["labels"] and n["properties"].get("gap")]
    assert gaps, "the skeleton records 20 gaps; none parsed"
    assert all("gap" in g["gap"].lower() for g in gaps)


# ------------------------------------------------------------------ the round-trip gate
def test_the_round_trip_reproduces_every_row_cell_for_cell(graph):
    """DD-050's gate. Zero unexplained diffs or the JSON is not the source of truth."""
    original = rf.skeleton_rows(SKELETON.read_text(encoding="utf-8"))
    rendered = {p["code"]: rf.render_row(p) for p in rf.rows_from_json(graph)}
    assert set(original) == set(rendered)
    bad = []
    for code, o in original.items():
        oc = [rf.norm(c) for c in o.strip().strip("|").split("|")]
        rc = [rf.norm(c) for c in rendered[code].strip().strip("|").split("|")]
        if oc != rc:
            bad.append((code, [(i, x, y) for i, (x, y) in enumerate(zip(oc, rc)) if x != y]))
    assert not bad, bad


def test_the_tier_cell_round_trips_when_it_carries_prose():
    """A11's Tier cell is "`agency_instrumented` (observed leg requires edge logs; declared leg
    stays `public`)". Rendering the ENUM and re-wrapping it in backticks cannot reproduce that,
    and that is exactly how the first round trip failed."""
    g = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    a11 = next(n["properties"] for n in g["nodes"] if n["properties"].get("code") == "A11")
    assert a11["tier"] == "agency_instrumented"
    assert a11["tier_raw"].count("`") == 4
    assert rf.render_row(a11).endswith("| stub |")


# ------------------------------------------------- the write-back and its summary counters
def test_counts_agree_with_the_specs_they_summarise(graph):
    """`counts.collectors_none_known` said 5 after E5 had stopped being `none_known`.

    The write-back in `2026-09-06_harness_scaffold` was done from an ad-hoc command, so the
    derived summary drifted from the nodes it summarises and nothing noticed. A counter that
    can disagree with its own data is a number computed in chat (DD-040): this test is the
    reader that makes it a derivation.
    """
    specs = [n["properties"] for n in graph["nodes"] if "MeasurementSpec" in n["labels"]]
    assert graph["counts"]["measurement_specs"] == len(specs)
    assert graph["counts"]["collectors_none_known"] == sum(
        1 for s in specs if s.get("collector") == "none_known")


def test_the_rule_write_back_is_idempotent():
    """Re-running it on the file it produced must change nothing. If it does, the framework of
    record and the rules package disagree, and only one of them can be right."""
    import framework_writeback_rules as wb  # noqa: E402
    from assessment.harness.scan.rules import BY_LEG

    g = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    before = json.dumps(g, sort_keys=True)
    touched = wb.writeback(g, BY_LEG)
    assert touched == {"specs_rule_id": 0, "indicators_status": 0, "e5_collector": 0}
    assert json.dumps(g, sort_keys=True) == before


def test_every_leg_with_a_rule_carries_its_rule_id(graph):
    """The chain the RESULT quotes is MeasurementSpec -> rule_id -> Finding.evidence -> obs_id
    (F-UJI's metric -> tests -> evidence, DD-052 §2). A spec whose leg has a rule but no
    `rule_id` breaks the first link and the Finding can never be traced back to its spec."""
    from assessment.harness.scan.rules import BY_LEG

    for n in graph["nodes"]:
        if "MeasurementSpec" not in n["labels"]:
            continue
        leg = n["properties"].get("leg")
        if leg in BY_LEG:
            assert n["properties"].get("rule_id") == BY_LEG[leg], leg
