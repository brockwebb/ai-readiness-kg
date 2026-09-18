"""The requirements layer: what a body or this project would need before a test can run.

`cc_tasks/2026-09-18_requirements_layer.md`, under DN-005 §2.2 and §2.4. An expert system's
rule base pairs a question with what answering it requires; the record already held the
question (the indicator), the test (the rule or the named open tool) and the fix (the action).
This layer adds the requirement — `AssessmentTool` and `Precondition` nodes, and a `REQUIRES`
edge from every indicator the harness cannot measure alone to the thing that would close it.

Five groups, in the order the task's decisions put them:

  1. **Scope** (decision 2) — every indicator the rule reaches has a requirement or a stated
     reason for having none, and the tier rules hold (O rows require their tool, evaluations a
     benchmark set, declarations the agency's records).
  2. **Citations** (decision 3) — every edge's source OPENS: a corpus quote is in the file, a
     record quote is in the field, a tool-map row is in the file at the frozen commit. A
     citation that is present and wrong is the defect a presence check would pass.
  3. **Values** (decision 1) — kinds, costs and who-provides are legal values, every cost is a
     `notional:` marker that names its kind, and nothing reuses the KG's `Tool` label.
  4. **The query** (decision 4) — `get_requirements` answers an indicator, a body and the whole
     map, with a locator on every fact that resolves.
  5. **The views** (decision 5) — the tool map §3 is the record's REQUIRES edges.

Record-backed tests need no database. The body and locator tests that need a Finding's error
class skip when Neo4j is unreachable, as `tests/test_mcp_server.py` does.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MCP_DIR = REPO / "mcp"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

RECORD = REPO / "framework" / "ai_readiness_framework.json"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(f"_req_{name}", REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mcp(name: str):
    """Same idiom as `tests/test_mcp_server.py::_mod`: one module object per file."""
    if str(MCP_DIR) not in sys.path:
        sys.path.insert(0, str(MCP_DIR))
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, MCP_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def tagger():
    return _script("tag_requirements")


@pytest.fixture(scope="module")
def g():
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def inds(g):
    return {n["properties"]["code"]: n for n in g["nodes"] if "AssessmentIndicator" in n["labels"]}


@pytest.fixture(scope="module")
def reqs(g):
    return {n["id"]: n for n in g["nodes"]
            if n["labels"][0] in ("AssessmentTool", "Precondition")}


@pytest.fixture(scope="module")
def edges(g):
    return [e for e in g["edges"] if e["type"] == "REQUIRES"]


def _out(edges, code):
    return [e for e in edges if e["from"] == f"ind:{code}"]


# ------------------------------------------------------------------ 1. scope (decision 2)

def test_the_layer_exists_in_the_record(reqs, edges):
    labels = {n["labels"][0] for n in reqs.values()}
    assert labels == {"AssessmentTool", "Precondition"}
    assert edges, "no REQUIRES edges; everything below would pass vacuously"


def test_every_indicator_in_scope_has_a_requirement_or_says_why_not(inds, edges, tagger):
    """Decision 2's scope: every non-harness_leg indicator, and every harness_leg whose tier
    note records an unmeasured half. Each has at least one REQUIRES edge, or a
    `requirement_none_reason` on the node — or, for an unassigned indicator, its
    `tier_unassigned_reason` UNCHANGED, which is what "nothing with the reason unchanged"
    means."""
    missing = []
    for code, n in inds.items():
        p = n["properties"]
        in_scope = (p.get("measurement_basis") != "harness_leg"
                    or code in tagger.UNMEASURED_HALF)
        if not in_scope:
            continue
        if _out(edges, code):
            assert not p.get("requirement_none_reason"), \
                f"{code} has requirements AND a reason for having none"
            continue
        if p.get("measurement_basis") is None:
            assert p.get("tier_unassigned_reason"), code
            assert not p.get("requirement_none_reason"), \
                f"{code}: an unassigned row keeps its own reason, it gets no second one"
            continue
        if not p.get("requirement_none_reason"):
            missing.append(code)
    assert not missing, f"in scope with neither a requirement nor a reason: {missing}"


def test_no_indicator_outside_scope_carries_a_requirement(inds, edges, tagger):
    """A harness leg with no recorded unmeasured half is measured by its rule and needs
    nothing — except where the tool map §3 named a coverage tool for it, which is the one
    other way in (`closes: coverage`)."""
    for e in edges:
        code = e["from"].removeprefix("ind:")
        p = inds[code]["properties"]
        if p.get("measurement_basis") == "harness_leg" and code not in tagger.UNMEASURED_HALF:
            assert e["properties"]["closes"] == "coverage", (code, e["to"])


def test_every_harness_note_that_records_an_unmeasured_half_is_in_scope(inds, tagger):
    """The scope list is checked against the notes, not typed beside them: a note that says a
    clause is unmeasured and is missing from `UNMEASURED_HALF` is an indicator this layer
    silently skipped. And every entry's quote is verbatim in its note."""
    for code, n in inds.items():
        p = n["properties"]
        if p.get("measurement_basis") != "harness_leg":
            continue
        note = p.get("tier_note") or ""
        if "unmeasured" in note or "not measured" in note:
            assert code in tagger.UNMEASURED_HALF, code
    for code, quote in tagger.UNMEASURED_HALF.items():
        assert quote in (inds[code]["properties"].get("tier_note") or ""), code


def test_every_tier_o_row_requires_the_tool_its_tier_source_names(inds, edges, reqs):
    """"Tier O rows require their tool": the tool's `doc_id` is the one the tier source
    cites, so the requirement and the tier cannot name two different instruments."""
    for code, n in inds.items():
        p = n["properties"]
        if p.get("measurement_tier") != "O":
            continue
        tools = [reqs[e["to"]]["properties"] for e in _out(edges, code)
                 if reqs[e["to"]]["labels"][0] == "AssessmentTool"]
        assert tools, f"{code} is tier O and requires no tool"
        assert any(f"`{t['doc_id']}`" in p["tier_source"] for t in tools if t.get("doc_id")), \
            (code, [t.get("doc_id") for t in tools])


def test_every_evaluation_row_requires_a_benchmark_set(inds, edges, reqs):
    for code, n in inds.items():
        if n["properties"].get("measurement_basis") != "evaluation":
            continue
        kinds = {reqs[e["to"]]["properties"]["kind"] for e in _out(edges, code)}
        assert "benchmark_set" in kinds, (code, kinds)


def test_a_definition_that_names_a_generative_engine_requires_one(inds, edges, reqs):
    """Decision 2: "where the definition names a generative engine, a `hosted_paid` or
    `platform_account` tool". C4 is the one definition that does."""
    named = [c for c, n in inds.items()
             if "generative engine" in (n["properties"].get("indicator") or "").lower()
             and n["properties"].get("measurement_basis") == "evaluation"]
    assert named == ["C4"]
    for code in named:
        kinds = {reqs[e["to"]]["properties"]["kind"] for e in _out(edges, code)
                 if reqs[e["to"]]["labels"][0] == "AssessmentTool"}
        assert kinds & {"hosted_paid", "platform_account"}, kinds


def test_every_declaration_requires_the_agencys_records_from_the_publisher(inds, edges, reqs):
    for code, n in inds.items():
        if n["properties"].get("measurement_basis") != "declaration":
            continue
        got = [reqs[e["to"]]["properties"] for e in _out(edges, code)]
        assert any(r["kind"] == "agency_records" and r["who_provides"] == "publisher"
                   for r in got), (code, got)


def test_a_platform_account_tool_never_travels_without_the_account(inds, edges, reqs):
    """A search-console-class tool reads the SITE OWNER's data, so every route that uses one
    also requires the owner's account — otherwise the query would tell a body that a tool
    alone would unlock a test only the body itself can open."""
    for e in edges:
        t = reqs[e["to"]]
        if t["labels"][0] != "AssessmentTool" or t["properties"]["kind"] != "platform_account":
            continue
        route = [reqs[x["to"]]["properties"] for x in edges
                 if x["from"] == e["from"] and x["properties"]["route"] == e["properties"]["route"]]
        assert any(r.get("kind") == "site_owner_account" for r in route), (e["from"], e["to"])


# ------------------------------------------------------------------ 2. citations (decision 3)

def test_every_edge_cites_and_every_citation_opens(edges, tagger, g):
    """Decision 3: "an edge with no citation is a gate failure". Opening it is the stronger
    test and the one run here: the quote is in the file, the field or the frozen tool map."""
    bad = []
    for e in edges:
        p = e["properties"]
        if not p.get("source") or p.get("source_kind") not in tagger.SOURCE_KINDS:
            bad.append(f"{e['from']}->{e['to']}: no citation")
            continue
    assert not bad, bad
    for row in tagger.REQUIRES:
        ok, why = tagger.citation_opens(row["source"], g)
        assert ok, f"{row['code']}->{row['to']}: {why}"


def test_every_for_clause_is_verbatim_in_its_indicator(edges, inds):
    for e in edges:
        code = e["from"].removeprefix("ind:")
        clause = e["properties"]["for_clause"]
        assert clause and clause in inds[code]["properties"]["indicator"], (code, clause)


def test_every_tool_doc_source_opens_or_says_why_it_is_not_on_disk(reqs, tagger, g):
    for rid, n in reqs.items():
        if n["labels"][0] != "AssessmentTool":
            continue
        p = n["properties"]
        if p.get("doc_id"):
            spec = next(t for t in tagger.TOOLS if f"tool:{t['slug']}" == rid)
            ok, why = tagger.citation_opens(spec["doc"], g)
            assert ok, f"{rid}: {why}"
            assert p["doc_source"].startswith(tagger.DOCS[p["doc_id"]]), rid
        else:
            assert p["doc_source"] == tagger.NONE_ON_DISK, rid
            assert p.get("doc_source_note"), f"{rid} has no document and no reason"


def test_a_citation_that_does_not_open_is_refused(tagger, g):
    """The negative control: a citation checker that passed everything would make the two
    tests above vacuous."""
    assert not tagger.citation_opens(
        ("corpus", "extruct-readme", "anywhere", "this sentence is not in the README"), g)[0]
    assert not tagger.citation_opens(("record", "ind:C1", "indicator", "not the text"), g)[0]
    assert not tagger.citation_opens(("tool_map", "Sitemap crawl and URL inventory",
                                      "no such cell"), g)[0]
    assert not tagger.citation_opens(("repo_file", "assessment/harness/scan/errors.py",
                                      "no such note"), g)[0]


# ------------------------------------------------------------------ 3. values (decision 1)

def test_node_values_are_legal(reqs, tagger):
    for rid, n in reqs.items():
        p = n["properties"]
        if n["labels"][0] == "AssessmentTool":
            assert rid.startswith("tool:"), rid
            assert p["kind"] in tagger.TOOL_KINDS, rid
            assert p["cost_band"] in tagger.COST_BANDS, rid
            assert p["cost_band"] == tagger.NOTIONAL_TOOL_COST[p["kind"]], rid
            assert p["cost_source"] == tagger.notional_source(p["kind"]), rid
            assert p["band_note"] == tagger.BAND_NOTE, rid
        else:
            assert rid.startswith("pre:"), rid
            assert p["kind"] in tagger.PRECONDITION_KINDS, rid
            assert p["who_provides"] in tagger.WHO_PROVIDES, rid
            assert p.get("description"), rid
        assert p.get("name"), rid


def test_edge_values_are_legal_and_edge_identity_is_unique(edges, tagger):
    keys = [(e["from"], e["to"]) for e in edges]
    assert len(keys) == len(set(keys)), "two REQUIRES edges share (from, to)"
    for e in edges:
        p = e["properties"]
        assert p["closes"] in tagger.CLOSES, e
        assert p.get("route") and p.get("test"), e


def test_every_requirement_is_reached_by_an_edge_or_unlocks_an_error_class(reqs, edges):
    reached = {e["to"] for e in edges}
    for rid, n in reqs.items():
        assert rid in reached or n["properties"].get("unlocks_error_classes"), rid


def test_error_classes_are_mapped_only_when_blind_and_each_at_most_once(reqs, tagger):
    """A requirement may unlock only a class the harness counts as BLIND (it could not see);
    SCOPE is a boundary drawn on purpose and OBSERVED is a measurement. The BLIND classes no
    requirement unlocks are exactly the ones the tagger lists and says why."""
    from scan.errors import CLASSES, BLIND, HARNESS_CURRENT

    def kind(c):
        k = CLASSES[c]["kind"]
        return k.get(HARNESS_CURRENT) if isinstance(k, dict) else k

    seen: dict = {}
    for rid, n in reqs.items():
        for c in n["properties"].get("unlocks_error_classes") or []:
            assert c in CLASSES and kind(c) == BLIND, (rid, c)
            assert c not in seen, f"{c} is unlocked by {seen[c]} and {rid}"
            seen[c] = rid
    blind = {c for c in CLASSES if c is not None and kind(c) == BLIND}
    assert blind - set(seen) == set(tagger.UNMAPPED_ERROR_CLASSES)


def test_the_kg_tool_label_is_never_reused(g):
    """`Tool` is a KG node type (`kg/schema.yaml`, 262 extracted nodes on 2026-09-18). The
    framework loader DETACH DELETEs every label it owns before rebuilding, so a framework node
    labelled `Tool` would have deleted the literature's tools on the next projection."""
    import yaml
    kg_types = set(yaml.safe_load((REPO / "kg" / "schema.yaml").read_text(encoding="utf-8"))
                   ["node_types"])
    assert "Tool" in kg_types
    labels = {n["labels"][0] for n in g["nodes"]}
    assert not (labels & kg_types), labels & kg_types
    loader = _script("load_framework_graph")
    assert not (set(loader.ASSESSMENT_LABELS) & kg_types)


def test_the_schema_catalogue_declares_the_new_types(tagger):
    import yaml
    a = yaml.safe_load((REPO / "kg" / "schema.yaml").read_text(encoding="utf-8"))["assessment_layer"]
    t, p = a["node_types"]["AssessmentTool"], a["node_types"]["Precondition"]
    assert t["property_values"]["kind"] == list(tagger.TOOL_KINDS)
    assert t["property_values"]["cost_band"] == list(tagger.COST_BANDS)
    assert p["property_values"]["kind"] == list(tagger.PRECONDITION_KINDS)
    assert p["property_values"]["who_provides"] == list(tagger.WHO_PROVIDES)
    assert a["edge_types"]["REQUIRES"]["pairs"] == [["AssessmentIndicator", "AssessmentTool"],
                                                    ["AssessmentIndicator", "Precondition"]]


def test_the_counts_carry_the_layer(g):
    c = g["counts"]
    assert c["tools"] == sum(1 for n in g["nodes"] if n["labels"][0] == "AssessmentTool")
    assert c["preconditions"] == sum(1 for n in g["nodes"] if n["labels"][0] == "Precondition")
    assert c["requires"] + c["requires_on_candidate_indicators"] == \
        sum(1 for e in g["edges"] if e["type"] == "REQUIRES")
    assert "REQUIRES" in g["counts_basis"]


def test_the_tagger_validates_and_is_idempotent_over_the_record(tagger, g):
    """Re-running the tagger over the record it wrote changes nothing: the layer is a function
    of its tables and the record, never of when it was run."""
    nodes, edges, updates = tagger.build(g)
    merged = tagger.merge(g, nodes, edges, updates)
    assert merged["nodes"] == g["nodes"]
    assert merged["edges"] == g["edges"]


# ------------------------------------------------------------------ 4. the query (decision 4)

@pytest.fixture(scope="module")
def offline():
    return _mcp("airkg_tools").Tools(graph=None)


@pytest.fixture(scope="module")
def tools():
    T = _mcp("airkg_tools")
    gr = T.Graph()
    if not gr.available():
        pytest.skip("Neo4j unreachable, the body view's error classes are unverified")
    return T.Tools(graph=gr)


def _locators(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "locators" and isinstance(v, list):
                out.extend(v)
            elif k == "locator" and isinstance(v, dict):
                out.append(v)
            else:
                out.extend(_locators(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_locators(v))
    return out


def test_get_requirements_is_a_registered_tool():
    T = _mcp("airkg_tools")
    assert "get_requirements" in T.TOOL_ORDER


def test_an_indicator_answer_names_its_tests_and_what_each_requires(offline):
    r = offline.get_requirements(indicator="C4")
    assert r["indicator"] == "C4"
    routes = {t["route"] for t in r["tests"]}
    assert len(routes) >= 2, "C4 has a publisher-account route and an engine route"
    for t in r["tests"]:
        assert t["requires"], t
        for q in t["requires"]:
            assert q["kind"] and q["who_provides"] and q["source"], q
            if q["label"] == "AssessmentTool":
                assert q["cost"] in ("none", "tooling", "staff_time", "procurement")


def test_an_indicator_the_harness_measures_says_it_needs_nothing(offline):
    r = offline.get_requirements(indicator="A1")
    assert r["tests"] == []
    assert "RULE-A1" in r["reason"]


def test_an_indicator_with_no_requirement_says_why(offline, g):
    r = offline.get_requirements(indicator="B2")
    assert r["tests"] == [] and "versioned" in r["reason"]
    r = offline.get_requirements(indicator="G5")
    assert r["reason"] == next(n["properties"]["tier_unassigned_reason"] for n in g["nodes"]
                               if n["id"] == "ind:G5")


def test_an_unknown_indicator_says_so(offline):
    r = offline.get_requirements(indicator="ZZ9")
    assert "error" in r and "A1" in r["codes"]


def test_the_whole_map_groups_indicators_under_each_requirement(offline, reqs):
    r = offline.get_requirements()
    got = {x["id"] for x in r["requirements"]}
    assert got == set(reqs)
    two = [x for x in r["requirements"] if len(x["unlocks"]) >= 2]
    assert two, "no requirement unlocks two indicators; grouping would show nothing"
    assert r["band_note"]


def test_a_body_answer_groups_what_it_cannot_see_by_requirement(tools):
    """Decision 4's shape: "a search-console grant would unlock these four" as one line. On the
    cycle of record the refusals are the largest block, and every refused cell must land under
    the one precondition that unlocks `refused`."""
    presc = _script("prescriptions")
    cycle = presc.snapshot_cycle()
    refused_body = None
    for m in presc.matrices(cycle):
        for row in m["rows"]:
            if "error" in row["verdicts"].values() and (m["_kind"] != "product"
                                                        or row.get("declared")):
                refused_body = row["agency"]
                break
        if refused_body:
            break
    assert refused_body, "no body has an error cell on the cycle of record"
    r = tools.get_requirements(body=refused_body)
    assert r["body"] == refused_body and r["cycle"] == cycle
    errs = r["unobserved"]["errors"]
    assert errs and all(c["error_classes"] for c in errs)
    grouped = {x["id"]: x for x in r["by_requirement"]}
    for x in r["by_requirement"]:
        assert x["line"].startswith(x["name"]) and str(len(x["unlocks"])) in x["line"]
    placed = sum(1 for x in r["by_requirement"] for u in x["unlocks"] if u["what"] == "error")
    unplaced = sum(1 for u in r["no_requirement"] if u["what"] == "error")
    assert placed + unplaced >= len(errs)
    if any("refused" in c["error_classes"] for c in errs):
        assert "pre:publisher-admits-the-identified-client" in grouped


def test_an_unknown_body_says_so(offline):
    r = offline.get_requirements(body="NOSUCH")
    assert "error" in r and r["bodies"]


def test_every_locator_in_a_requirements_answer_resolves(tools):
    answers = [tools.get_requirements(), tools.get_requirements(indicator="C4"),
               tools.get_requirements(indicator="A11"), tools.get_requirements(body="CENSUS")]
    bad = []
    for a in answers:
        locs = _locators(a)
        assert locs
        for loc in locs:
            got = tools.resolve_locator(loc)
            if not got["resolved"]:
                bad.append(f"{loc} -> {got['detail']}")
    assert not bad, "\n".join(bad[:20])


# ------------------------------------------------------------------ 5. the views (decision 5)

def test_the_tool_map_section_3_is_the_record(edges):
    text = (REPO / "docs" / "design" / "scan_tool_map.md").read_text(encoding="utf-8")
    section = text.split("\n## 3.")[1].split("\n## ")[0]
    rows = [l for l in section.splitlines() if l.startswith("| ") and not l.startswith("| code")]
    assert len(rows) == len(edges)
    for e in edges:
        code = e["from"].removeprefix("ind:")
        assert any(r.startswith(f"| {code} |") and f"`{e['to']}`" in r for r in rows), \
            (code, e["to"])
    assert "GAPS = [" not in (REPO / "scripts" / "scan_tool_map.py").read_text(encoding="utf-8")


def test_the_tool_map_regenerates_byte_identically():
    r = subprocess.run([sys.executable, "scripts/scan_tool_map.py", "--check"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr


def test_a_tools_who_provides_follows_its_kind(reqs, tagger):
    for rid, n in reqs.items():
        if n["labels"][0] == "AssessmentTool":
            p = n["properties"]
            assert p["who_provides"] == tagger.WHO_RUNS_BY_KIND[p["kind"]], rid


def test_a_cell_is_counted_once_under_a_requirement(tools):
    """A cell refused on one probe and disallowed on another is one cell the publisher's grant
    would unlock. BLS carries both classes on the cycle of record."""
    r = tools.get_requirements(body="BLS")
    for x in r["by_requirement"]:
        cells = [(u["leg"], u["surface"]) for u in x["unlocks"] if u["what"] == "error"]
        assert len(cells) == len(set(cells)), x["id"]
