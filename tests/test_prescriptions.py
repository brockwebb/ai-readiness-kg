"""The prescription layer: bound to the check, sourced on disk, valued from the cycle of record.

`cc_tasks/2026-09-17_prescription_layer.md` decision 3. The invariant every prior-art shape
this layer borrows from shares — WCAG, CIS Benchmarks, OpenSSF Scorecard, Lighthouse, NIST
SP 800-53 — is that *an action is bound to the check that would detect its absence, and the
same check verifies its completion.* These tests hold that binding closed from both ends:

* no `harness_leg` indicator without an action, and no failing rule outcome without one;
* no action without a technique source that is verbatim in a document this repository holds,
  and without a `verifies_by` that resolves to a rule a new cycle would judge with;
* no band that is not a legal value, no band source that is neither a document locator nor a
  `notional:` marker carrying its class, and no action without the technique class that fixes
  both of its bands — a blank band reads as "no effort" and a per-action guess reads as a
  measurement, so the layer does neither (DN-005 ADDENDUM_03);
* no authored value: `bodies_failing_now` is recomputed here from the published matrices of
  the cycle of record and compared cell for cell against what the record carries.

The Cypher half is skipped, never failed, when Neo4j is unreachable — the same contract as
`tests/test_framework_projection_roundtrip.py`, which is also what makes verifying this layer
by Cypher valid at all (DD-057).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

RECORD = REPO / "framework" / "ai_readiness_framework.json"
PY = "/opt/anaconda3/bin/python3" if Path("/opt/anaconda3/bin/python3").exists() else sys.executable

#: The shape of the layer, as a literal. A test that reads its expectation out of the artifact
#: under test can only ever pass; these numbers move only when a task says they should.
#: 45 / 17 / 90 until `cc_tasks/2026-09-18_dcat_field_rules.md` added generation 11's four legs
#: (B1, B4, D3, G4) and one action for each of their nine failing outcomes.
EXPECTED_ACTIONS = 54
EXPECTED_LEGS = 21
EXPECTED_NOTIONAL_BANDS = 108

#: The class table of `cc_tasks/2026-09-17_notional_bands.md` decision 1, as a literal. The
#: RESULT's §0 tables the same 45 rows with a reason for each row that is not obvious, so a
#: reader who disputes a class disputes a number here rather than a sentence somewhere.
#: Generation 11 added five `edit_existing` (one per field outcome) and four `publish_new_file`
#: (each leg's `no_product_record`, which carries a `technique_class_reason`).
EXPECTED_PER_CLASS = {
    "edit_existing": 22,
    "publish_new_file": 18,
    "change_server_behaviour": 10,
    "expose_api": 1,
    "harness_side": 3,
}
#: Decision 2's band table, restated here rather than imported, so that moving a band in the
#: tagger fails a test instead of silently re-banding 45 actions.
EXPECTED_BANDS = {
    "edit_existing": ("hours", "none"),
    "publish_new_file": ("days", "staff_time"),
    "change_server_behaviour": ("weeks", "staff_time"),
    "expose_api": ("quarter", "procurement"),
    "harness_side": ("hours", "none"),
}


def _module(name: str):
    spec = importlib.util.spec_from_file_location(f"_{name}", REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def tp():
    return _module("tag_prescriptions")


@pytest.fixture(scope="module")
def pres():
    return _module("prescriptions")


@pytest.fixture(scope="module")
def doc():
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def acts(doc):
    return [n for n in doc["nodes"] if "Action" in n["labels"]]


@pytest.fixture(scope="module")
def remediates(doc):
    return [e for e in doc["edges"] if e["type"] == "REMEDIATES"]


# ------------------------------------------------------------------ the binding, both ends
def test_every_harness_leg_indicator_has_at_least_one_action(doc, remediates):
    """Decision 3's first clause. `measurement_basis: harness_leg` is the tiering task's own
    field, so this is the join between the two layers rather than a list kept in step by
    hand."""
    harness = {n["properties"]["code"] for n in doc["nodes"]
               if "AssessmentIndicator" in n["labels"]
               and n["properties"].get("measurement_basis") == "harness_leg"}
    assert len(harness) == EXPECTED_LEGS
    remediated = {e["to"].removeprefix("ind:") for e in remediates}
    assert harness - remediated == set(), f"no action for {sorted(harness - remediated)}"
    assert remediated - harness == set(), f"action on a non-harness leg {sorted(remediated - harness)}"


def test_every_failing_outcome_of_every_current_rule_has_exactly_one_action(tp, acts):
    """Decision 2: *at least one action per failing outcome its rule can return.* One, here —
    which is also what keeps (`from`, `type`, `to`) unique for the write-back's delta."""
    want = {(leg, name) for leg, outs in tp.OUTCOMES.items() for name in outs}
    got = [(a["properties"]["leg"], a["properties"]["outcome"]) for a in acts]
    assert sorted(got) == sorted(want)
    assert len(got) == len(set(got)) == EXPECTED_ACTIONS


def test_every_outcome_names_a_branch_that_is_still_in_its_rule(tp):
    """An outcome is anchored by a VERBATIM fragment of the rule branch's own reason string. A
    rule version that rewords the branch fails here rather than leaving a prescription bound to
    a sentence nothing produces."""
    for leg, outs in tp.OUTCOMES.items():
        rid, src = tp.rule_module_source(leg)
        for name, frag in outs.items():
            assert frag in src, f"{leg}/{name}: not in {rid}"


def test_every_action_verifies_by_a_rule_a_new_cycle_judges_with(acts):
    """Decision 3: *a `verifies_by` that resolves to a rule in `rules.CURRENT`.* Not merely a
    rule that exists — `REGISTRY` holds every version ever shipped, and an action bound to a
    superseded one would be verified by a check no cycle runs."""
    from scan.rules import CURRENT, REGISTRY
    for a in acts:
        p = a["properties"]
        assert p["verifies_by"] in REGISTRY, a["id"]
        assert CURRENT[p["leg"]] == p["verifies_by"], a["id"]


def test_every_remediates_edge_carries_the_outcome_and_the_rule(tp, remediates):
    keys = [(e["from"], e["to"], e["properties"]["outcome"]) for e in remediates]
    assert len(keys) == len(set(keys)), "two edges share (from, to, outcome)"
    triples = [(e["from"], e["type"], e["to"]) for e in remediates]
    assert len(triples) == len(set(triples)), "two REMEDIATES edges share (from, type, to)"
    from scan.rules import CURRENT
    for e in remediates:
        p = e["properties"]
        assert p["rule_id"] == CURRENT[p["leg"]]
        assert p["reason_fragment"] == tp.OUTCOMES[p["leg"]][p["outcome"]]


# ------------------------------------------------------------------ the sources
def test_every_action_has_a_technique_source_quoted_from_a_document_on_disk(tp, acts):
    """Decision 1: *at least one per action, quoted or located per DN-001.* Both, here: the
    locator names the file and the doc_id, and the quote is checked as a substring of it, so a
    source cannot drift from the document it cites."""
    for a in acts:
        srcs = a["properties"]["technique_source"]
        assert srcs, a["id"]
        for s in srcs:
            path, _, rest = s.partition(" (doc_id `")
            doc_id = rest.split("`", 1)[0]
            assert tp.SOURCES[doc_id] == path, s
            quote = s.split(": \"", 1)[1].rstrip("\"")
            assert quote in (REPO / path).read_text(encoding="utf-8"), s[:120]


def test_every_technique_source_document_is_a_file_this_repository_holds(tp):
    for doc_id, rel in tp.SOURCES.items():
        assert (REPO / rel).exists(), f"{doc_id} -> {rel}"


def test_the_corpus_technique_sources_are_admitted_documents(tp):
    """A corpus source is cited by doc_id, so the doc_id has to be one the manifest admits
    (DD-003). The one non-corpus source is the instrument's own parameters and says so in its
    key."""
    manifest = set(json.loads((REPO / "corpus" / "manifest.json")
                              .read_text(encoding="utf-8"))["entries"])
    for doc_id in tp.SOURCES:
        if doc_id.startswith("internal:"):
            continue
        assert doc_id in manifest, doc_id


# ------------------------------------------------------------------ the bands
def test_every_band_is_a_legal_value_and_every_source_names_where_it_came_from(tp, acts):
    """`cc_tasks/2026-09-17_notional_bands.md` decision 3. A band is one of the legal values —
    never empty, never a free-text guess — and its source is either a document locator or a
    `notional:` marker. A marker without its class would be an estimate with no method."""
    for a in acts:
        p = a["properties"]
        for which, legal in (("effort", tp.EFFORT_BANDS), ("cost", tp.COST_BANDS)):
            value, src = p[f"{which}_band"], p[f"{which}_source"]
            assert value in legal, f"{a['id']}: {which}_band={value!r}"
            assert src and src.strip(), a["id"]
            if src.startswith(tp.NOTIONAL_PREFIX):
                cls = src[len(tp.NOTIONAL_PREFIX):].split(",")[0]
                assert cls in tp.TECHNIQUE_CLASSES, f"{a['id']}: {which}_source class {cls!r}"
                assert cls == p["technique_class"], a["id"]
                assert tp.NOTIONAL_TASK in src, a["id"]
            else:
                assert "/" in src, f"{a['id']}: {which}_source is neither a locator nor notional"


def test_the_notional_bands_are_counted(tp, acts):
    """The count the RESULT reports. A literal here so that sourcing a band from a document is
    a deliberate change to this number rather than a silent one."""
    notional = [(a["id"], b) for a in acts for b in ("effort", "cost")
                if a["properties"][f"{b}_source"].startswith(tp.NOTIONAL_PREFIX)]
    assert len(notional) == EXPECTED_NOTIONAL_BANDS
    assert len(notional) == 2 * EXPECTED_ACTIONS, "a band escaped the marker"


def test_the_pending_literal_is_gone_from_the_record_and_the_code(tp):
    """Decision 3: `estimate:pending` no longer appears anywhere. An empty band that a later
    reader restores by copying the old literal would be a band with no class and no method."""
    for rel in ("framework/ai_readiness_framework.json", "scripts/tag_prescriptions.py",
                "scripts/prescriptions.py", "kg/schema.yaml"):
        assert "estimate:pending" not in (REPO / rel).read_text(encoding="utf-8"), rel


def test_every_action_carries_a_class_and_the_class_fixes_both_bands(tp, acts):
    """Decision 1 and decision 2. The bands are assigned BY CLASS, so two actions of one class
    can never carry different bands — which is what makes the estimate relative rather than
    forty-five separate guesses."""
    assert set(tp.NOTIONAL_BANDS) == set(tp.TECHNIQUE_CLASSES) == set(EXPECTED_BANDS)
    for cls, want in EXPECTED_BANDS.items():
        assert tp.NOTIONAL_BANDS[cls] == want, cls
    seen = {}
    for a in acts:
        p = a["properties"]
        cls = p["technique_class"]
        assert cls in tp.TECHNIQUE_CLASSES, a["id"]
        assert (p["effort_band"], p["cost_band"]) == EXPECTED_BANDS[cls], a["id"]
        seen[cls] = seen.get(cls, 0) + 1
    assert seen == EXPECTED_PER_CLASS


def test_every_class_carries_its_one_line_definition(tp):
    """A class with no definition is a label, and a band assigned from a label is a guess."""
    for cls, what in tp.TECHNIQUE_CLASSES.items():
        assert what and len(what.split()) >= 5, cls


def test_every_action_carries_the_adjustment_instruction_verbatim(tp, acts):
    """Decision 4: once, verbatim, on every action. The instruction is what the band MEANS, so
    a consumer that reads one node off the graph reads it without also reading a document."""
    for a in acts:
        assert a["properties"]["band_note"] == tp.BAND_NOTE, a["id"]
    assert "Adjust" in tp.BAND_NOTE and "does not predict" in tp.BAND_NOTE


def test_a_class_that_is_not_obvious_says_why_it_was_chosen(tp, acts):
    """Decision 1's last clause. The reason is a property of the node, not only of the RESULT,
    so the row a reader disputes carries its own argument."""
    with_reason = {a["id"] for a in acts
                   if a["properties"].get("technique_class_reason")}
    assert with_reason, "no action records why its class was chosen"
    for a in acts:
        r = a["properties"].get("technique_class_reason")
        if r is not None:
            assert len(r.split()) >= 8, a["id"]


# ------------------------------------------------------------------ the value
def test_bodies_failing_now_is_the_matrix_count_for_that_leg(tp, acts):
    """Decision 3's last clause, recomputed from the published matrices rather than read back
    off the node. E5 and G1-D are on neither matrix of the cycle of record and carry 0 with a
    source that says why, not a blank."""
    cycle = tp.cycle_of_record()
    fails = tp.matrix_fail_bodies(cycle)
    for a in acts:
        v, leg = a["properties"]["value"], a["properties"]["leg"]
        want = fails[leg][0] if leg in fails else 0
        assert v["bodies_failing_now"] == want, f"{a['id']}: {leg}"
        assert v["bodies_failing_now_source"], a["id"]
        assert cycle in v["bodies_failing_now_source"], a["id"]


def test_a_leg_with_more_than_one_failing_outcome_says_the_count_is_an_upper_bound(tp, acts):
    """The matrices carry verdicts, not reasons, so a per-leg count over-states any single
    action on a multi-outcome leg. The node says so rather than letting a reader over-read it."""
    for a in acts:
        leg, v = a["properties"]["leg"], a["properties"]["value"]
        if len(tp.OUTCOMES[leg]) > 1:
            assert "bodies_failing_now_caveat" in v, a["id"]
        else:
            assert "bodies_failing_now_caveat" not in v, a["id"]


def test_value_is_flat_so_the_projection_can_promote_every_sub_key(acts):
    """`load_framework_graph.flatten` promotes every sub-key of `value` to `value_<name>`.
    That is only total while the map stays flat — Neo4j has no map property type."""
    for a in acts:
        for k, val in a["properties"]["value"].items():
            assert not isinstance(val, dict), f"{a['id']}.value.{k}"
            if isinstance(val, list):
                assert all(isinstance(x, str) for x in val), f"{a['id']}.value.{k}"


def test_constructs_served_comes_from_a_decomposes_into_edge(doc, acts):
    by_id = {n["id"]: n for n in doc["nodes"]}
    for a in acts:
        v = a["properties"]["value"]
        ind = f"ind:{a['properties']['indicator_code']}"
        want = sorted({by_id[e["from"]]["properties"].get("name") for e in doc["edges"]
                       if e["type"] == "DECOMPOSES_INTO" and e["to"] == ind
                       and "AssessmentConstruct" in by_id[e["from"]]["labels"]})
        assert v["constructs_served"] == want, a["id"]


def test_downstream_indicators_are_quoted_from_the_record(tp, doc, acts):
    """`where the record says so`. Each entry names the node and field the sentence is in, and
    the sentence is checked against it; a leg with none says the scan found none."""
    by_id = {n["id"]: n for n in doc["nodes"]}
    for up, rows in tp.DOWNSTREAM.items():
        for code, nid, field, quote in rows:
            assert quote in (by_id[nid]["properties"].get(field) or ""), f"{up}->{code}"
    for a in acts:
        v, code = a["properties"]["value"], a["properties"]["indicator_code"]
        want = [c for c, _, _, _ in tp.DOWNSTREAM.get(code, [])]
        assert v["downstream_indicators"] == want, a["id"]
        if not want:
            assert v["downstream_indicators_source"] == tp.NO_DOWNSTREAM, a["id"]


def test_e5_is_the_only_leg_whose_actions_are_not_for_a_publisher(acts):
    """Decision 2: marked false *where that is the case, not omitted.* E5's rule judges this
    instrument's own cycle. A12's subject IS the publisher's host; what is provisional there is
    the indicator (DD-054), and its actions say so in a note instead."""
    not_pub = {a["properties"]["leg"] for a in acts
               if not a["properties"]["applies_to_publisher"]}
    assert not_pub == {"E5"}
    for a in acts:
        if not a["properties"]["applies_to_publisher"]:
            assert a["properties"]["applies_to_note"], a["id"]
        if a["properties"]["leg"] == "A12":
            assert "DD-054" in (a["properties"].get("note") or ""), a["id"]


# ------------------------------------------------------------------ the writer and the query
def test_the_write_back_is_idempotent_over_the_record_it_produced(tp):
    """Re-deriving the layer from the record on disk must produce the record on disk. If it
    does not, the table and the record disagree and only one of them can be right."""
    import framework_writeback as fw
    g = fw.load()
    nodes, edges = tp.build(g)
    merged = tp.merge(g, nodes, edges)
    out = fw.save(merged, script=tp.SCRIPT, task=tp.TASK, changes={}, dry_run=True)
    assert out["delta_summary"]["nodes_added"] == {}
    assert out["delta_summary"]["edges_added"] == {}
    assert out["delta_summary"]["nodes_changed"] == 0
    assert out["delta_summary"]["edges_changed"] == 0
    assert out.get("unchanged") is True


def test_the_counts_block_carries_the_layer(doc, remediates):
    """A layer of 45 nodes that no counter mentions is the drift DD-040 names."""
    cand = {n["id"] for n in doc["nodes"] if n["properties"].get("status") == "candidate"}
    c = doc["counts"]
    assert c["actions"] == sum(1 for e in remediates if e["to"] not in cand)
    assert c["actions_on_candidate_indicators"] == sum(1 for e in remediates if e["to"] in cand)
    assert c["actions"] + c["actions_on_candidate_indicators"] == EXPECTED_ACTIONS
    assert "actions" in doc["counts_basis"]


@pytest.mark.parametrize("args", [["--all"], ["--bands"], ["--pending"], ["--body", "NCHS"]])
def test_the_query_runs_and_prints_every_action_it_should(tp, args):
    """`--pending` is kept as an alias because the predecessor's RESULT cites it as the
    re-derivation command; it prints the same table under its new name."""
    r = subprocess.run([PY, str(REPO / "scripts" / "prescriptions.py"), *args],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr[-2000:]
    assert r.stdout.strip()
    if args in (["--bands"], ["--pending"]):
        assert r.stdout.count("act:") >= EXPECTED_ACTIONS
        for cls in tp.TECHNIQUE_CLASSES:
            assert cls in r.stdout


def test_the_query_prints_the_notional_marker_once_and_the_note_once(tp):
    """Decision 4: the note goes once per body output and once in `--all`, not per action. A
    sentence repeated 45 times is a sentence nobody reads."""
    for args in (["--all"], ["--body", "NCHS"]):
        r = subprocess.run([PY, str(REPO / "scripts" / "prescriptions.py"), *args],
                           capture_output=True, text=True, cwd=REPO)
        assert r.returncode == 0, r.stderr[-2000:]
        # `Notional` capitalised opens the note and appears nowhere else; the marker on the
        # header line is lower-case. Counting a longer fragment would count the wrapping.
        assert r.stdout.count("Notional") == 1, args
        assert r.stdout.count("(notional)") == 1, args
        assert "pending" not in r.stdout, args


def test_the_query_refuses_a_body_that_is_not_on_the_cycle_of_record():
    r = subprocess.run([PY, str(REPO / "scripts" / "prescriptions.py"), "--body", "NOSUCH"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 2
    assert "is not a body on cycle" in r.stdout


def test_the_schema_catalogue_declares_the_two_new_types():
    import yaml
    a = yaml.safe_load((REPO / "kg" / "schema.yaml").read_text(encoding="utf-8"))["assessment_layer"]
    assert "Action" in a["node_types"]
    assert a["node_types"]["Action"]["property_values"]["technique_class"] == \
        ["edit_existing", "publish_new_file", "change_server_behaviour",
         "expose_api", "harness_side"]
    assert a["node_types"]["Action"]["property_values"]["effort_band"] == \
        ["hours", "days", "weeks", "quarter"]
    assert a["node_types"]["Action"]["property_values"]["cost_band"] == \
        ["none", "tooling", "staff_time", "procurement"]
    assert a["edge_types"]["REMEDIATES"]["pairs"] == [["Action", "AssessmentIndicator"]]
    assert a["parser_visible"] is False


def test_the_parser_still_cannot_mint_an_action():
    """The assessment layer is AUTHORED. If `Action` were parser-visible, a model reading a
    source document could mint a prescription — the same reasoning that keeps
    `AssessmentIndicator` out (`tests/test_framework_graph.py`)."""
    import yaml
    from kg.extraction import schema_loader
    live = schema_loader.load_schema()
    assert "Action" not in schema_loader.node_types(live)
    assert "REMEDIATES" not in schema_loader.edge_types(live)


# ------------------------------------------------------------------ the graph (DD-057)
@pytest.fixture(scope="module")
def graph():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                    # noqa: BLE001 - see docstring
        pytest.skip(f"Neo4j unreachable, the prescription projection is unverified: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


def test_cypher_every_harness_leg_indicator_has_an_action(graph):
    orphans = [r["c"] for r in graph.run(
        "MATCH (i:AssessmentIndicator {measurement_basis: 'harness_leg'}) "
        "WHERE NOT (i)<-[:REMEDIATES]-(:Action) RETURN i.code AS c ORDER BY c")]
    assert orphans == [], f"harness legs with no action: {orphans}"
    n = graph.run("MATCH (i:AssessmentIndicator {measurement_basis: 'harness_leg'}) "
                  "RETURN count(i) AS c").single()["c"]
    assert n == EXPECTED_LEGS


def test_cypher_every_action_is_bound_to_a_current_rule(graph):
    from scan.rules import CURRENT
    rows = list(graph.run(
        "MATCH (a:Action)-[r:REMEDIATES]->(i:AssessmentIndicator) "
        "RETURN a.id AS id, a.verifies_by AS rid, a.leg AS leg, r.outcome AS outcome, "
        "size(a.technique_source) AS n ORDER BY a.id"))
    assert len(rows) == EXPECTED_ACTIONS
    for r in rows:
        assert CURRENT[r["leg"]] == r["rid"], r["id"]
        assert r["n"] >= 1, r["id"]
        assert r["outcome"], r["id"]


def test_cypher_the_bands_are_notional_and_the_value_is_promoted(graph):
    rows = list(graph.run(
        "MATCH (a:Action) RETURN a.id AS id, a.technique_class AS k, a.effort_band AS e, "
        "a.effort_source AS es, a.cost_band AS c, a.cost_source AS cs, a.band_note AS bn, "
        "a.value_bodies_failing_now AS v ORDER BY a.id"))
    assert len(rows) == EXPECTED_ACTIONS
    per_class = {}
    for r in rows:
        assert (r["e"], r["c"]) == EXPECTED_BANDS[r["k"]], r["id"]
        for src in (r["es"], r["cs"]):
            assert src == f"notional:technique_class:{r['k']}, task 2026-09-17_notional_bands", \
                r["id"]
        assert r["bn"] and r["bn"].startswith("Notional relative estimate"), r["id"]
        assert isinstance(r["v"], int), r["id"]
        per_class[r["k"]] = per_class.get(r["k"], 0) + 1
    assert per_class == EXPECTED_PER_CLASS


def test_cypher_the_prescription_query_the_layer_exists_to_make(graph):
    """DN-005 §2.3's sentence, as one query: for a failing leg, what to do and how much of the
    system it moves. A read of the graph, not of the record."""
    rows = list(graph.run(
        "MATCH (a:Action)-[r:REMEDIATES]->(i:AssessmentIndicator) "
        "WHERE a.value_bodies_failing_now > 0 "
        "RETURN i.code AS code, r.outcome AS outcome, a.title AS title, "
        "a.value_bodies_failing_now AS bodies, a.effort_band AS effort "
        "ORDER BY bodies DESC, code, outcome"))
    assert rows, "the layer answers nothing"
    assert rows[0]["bodies"] >= 13
    assert all(r["effort"] in ("hours", "days", "weeks", "quarter") for r in rows)
