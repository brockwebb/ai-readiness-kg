#!/usr/bin/env python3
"""The read-only MCP server over this graph: its rails, its locators, and its tools driven by
an in-process MCP client.

`cc_tasks/2026-09-17_mcp_over_the_graph.md` decisions 1 to 5, under DN-005 §2.4.

Three things are tested, in the order the task's decisions put them:

  1. **The rails** (decision 1) — the read-only guard's refusal table, every write verb driven
     through it, and the one-database rail. Pure functions, so they run offline with no driver
     and no graph, exactly as `icsp_notebook/tests/test_mcp_server.py` runs its two rails.
  2. **The locators** (decision 2) — every tool's answer carries a locator for every fact, and
     each locator RESOLVES: the record path exists and holds the node id, the matrix path
     exists and holds the cell, the evidence file exists and hashes to the sha256 beside it,
     the graph node exists. A locator field that is present and wrong is the defect this
     catches; asserting presence alone would not.
  3. **The tools through a client** (decision 5) — the acceptance test is one question per tool
     asked through `fastmcp.Client` in memory, not a chat transcript.

Neo4j: the graph-backed tests skip when the database is unreachable, the same way
`tests/test_framework_projection_roundtrip.py` and `tests/test_prescriptions.py` do — a
developer without the database gets a green suite and an unverified claim rather than a false
red. The record-backed and rail tests need no database at all.
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MCP_DIR = REPO / "mcp"


def _mod(name: str):
    """A module under `mcp/` by path. `mcp/` is deliberately NOT a package: a top-level
    `mcp/__init__.py` in this repository shadows the installed `mcp` distribution that
    `fastmcp` imports, and `import fastmcp` then dies with
    `ImportError: cannot import name 'McpError' from 'mcp'`. Loading by path is the same
    idiom `scripts/` already uses here.

    Registered under its OWN name rather than the `_`-prefixed one the other tests use, and
    `mcp/` goes on `sys.path`: the server module does `import airkg_tools`, so a second module
    object under a second name would put two `Tools` classes in one process and
    `isinstance(server_tools, tools_mod.Tools)` would be False for two identical classes. One
    file, one module.
    """
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
def guard():
    return _mod("airkg_guard")


# ---------------------------------------------------------------- rail 1: read-only (decision 1)

READ_QUERIES = [
    "MATCH (i:AssessmentIndicator) RETURN i.code LIMIT 5",
    "match (n) return count(n)",
    "MATCH (f:Finding {cycle: 'scan_2026-09-10_rj2'}) RETURN f.verdict, count(*)",
    "PROFILE MATCH (n:Rule) RETURN n",
    "MATCH (a:Action)-[:REMEDIATES]->(i) RETURN a.id, i.code ORDER BY a.id",
    "CALL db.labels() YIELD label RETURN label",
]

#: Decision 1's list, one row per verb, plus the two shapes a bare keyword list misses: a write
#: hidden in a subquery and a write hidden behind a comment.
WRITE_QUERIES = [
    ("CREATE (n:Hack) RETURN n", "CREATE"),
    ("MERGE (n:AssessmentIndicator {code: 'A1'})", "MERGE"),
    ("MATCH (i:AssessmentIndicator) SET i.tier = 'public'", "SET"),
    ("MATCH (n) DETACH DELETE n", "DELETE"),
    ("MATCH (i) REMOVE i.tier", "REMOVE"),
    ("DROP CONSTRAINT indicator_id", "DROP"),
    ("MATCH (n) FOREACH (x IN [1] | SET n.k = x)", "FOREACH"),
    ("LOAD CSV FROM 'file:///x.csv' AS row CREATE (:N)", "LOAD CSV"),
    ("MATCH (n) CALL { CREATE (:Y) } RETURN n", "CREATE"),
    ("CALL apoc.create.node(['X'], {}) YIELD node RETURN node", "apoc.create.node"),
    ("MATCH (n) // harmless\nDELETE n", "DELETE"),
]


@pytest.mark.parametrize("q", READ_QUERIES)
def test_a_read_query_is_not_refused(guard, q):
    assert guard.refusal(q) is None, q


@pytest.mark.parametrize("q,verb", WRITE_QUERIES)
def test_every_write_verb_is_refused_and_the_refusal_names_it(guard, q, verb):
    msg = guard.refusal(q)
    assert msg is not None, f"not refused: {q}"
    assert verb.lower() in msg.lower(), f"refusal does not name {verb}: {msg}"
    assert "read-only" in msg.lower()


def test_a_write_word_inside_a_string_literal_is_not_a_write(guard):
    """Searching for the literal text 'create' is a read. Copied from the fss-policy-kg rail,
    which strips string literals before scanning for exactly this reason."""
    assert guard.refusal(
        "MATCH (a:Action) WHERE a.description CONTAINS 'create' RETURN a.id") is None
    assert guard.refusal(
        'MATCH (d:Document) WHERE d.title CONTAINS "DELETE" RETURN d.doc_id') is None


def test_an_empty_query_is_refused(guard):
    assert guard.refusal("") is not None
    assert guard.refusal("   \n  ") is not None


# ---------------------------------------------------------------- rail 2: one database, by name

def test_the_project_database_is_allowed(guard):
    assert guard.assert_allowed_db("seldon-ai-readiness-kg") == "seldon-ai-readiness-kg"


@pytest.mark.parametrize("db", ["wintermute-intake", "seldon-fss-policy-kg", "arnold",
                                "pragmatics", "neo4j", "seldon-blank"])
def test_every_other_database_is_refused(guard, db):
    """The INVERSION of the fss-policy-kg rail, and the copy/differ this server could not take
    over: that server refuses `seldon-*` because its own database is `fss-policy-kg`, and this
    project's database IS `seldon-ai-readiness-kg`. A name-pattern rail would refuse this
    server's only database, so the rail here is an allow-list of exactly one name, read from
    `seldon.yaml` and never from a caller."""
    with pytest.raises(SystemExit) as exc:
        guard.assert_allowed_db(db)
    assert db in str(exc.value)


def test_the_allowed_database_is_read_from_seldon_yaml_not_hardcoded(guard):
    """`seldon.yaml:neo4j.database` is the one declaration; the guard reads it."""
    import yaml
    declared = yaml.safe_load((REPO / "seldon.yaml").read_text(encoding="utf-8"))
    assert guard.project_database() == declared["neo4j"]["database"]


# ---------------------------------------------------------------- decision 2: tools + locators

@pytest.fixture(scope="module")
def tools_mod():
    return _mod("airkg_tools")


@pytest.fixture(scope="module")
def offline(tools_mod):
    """Tools with no graph behind them. Everything the RECORD answers still answers
    (decision 3: the record is the source of truth), and a graph question says so rather than
    guessing."""
    return tools_mod.Tools(graph=None)


@pytest.fixture(scope="module")
def tools(tools_mod):
    g = tools_mod.Graph()
    if not g.available():
        pytest.skip("Neo4j unreachable, the MCP server's graph answers are unverified")
    return tools_mod.Tools(graph=g)


def _all_locators(obj):
    """Every locator anywhere in an answer, at any depth. The point of walking the whole
    structure rather than a named field is that a tool cannot hide an unlocated fact in a
    nested row."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "locators" and isinstance(v, list):
                out.extend(v)
            elif k == "locator" and isinstance(v, dict):
                out.append(v)
            else:
                out.extend(_all_locators(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_all_locators(v))
    return out


# --- get_overview

def test_overview_counts_indicators_by_tier_and_basis_from_the_record(offline):
    o = offline.get_overview()
    fw = o["framework"]
    by_tier = fw["indicators_by_measurement_tier"]
    by_basis = fw["indicators_by_measurement_basis"]
    assert sum(by_tier.values()) == sum(by_basis.values()) == fw["indicators_total"]
    # Settled by `cc_tasks/2026-09-17_unassigned_indicators.md` (34 M, 2 O, 5 D, 8 unassigned)
    # and moved by `cc_tasks/2026-09-18_tool_docs_ingest.md`, which admitted the oasdiff and
    # Wayback CDX documentation and tiered A7, F2 and F3 O: 34 M, 5 O, 5 D, 5 unassigned.
    # Then `cc_tasks/2026-09-18_dcat_field_rules.md` tiered E1 and E3 M (`judged_reading`) and
    # added nine actions for generation 11's four rules: 36 M, 5 O, 5 D, 3 unassigned; 54.
    assert by_tier["M"] == 36 and by_tier["O"] == 5 and by_tier["D"] == 5
    assert by_tier["unassigned"] == 3
    assert fw["counts"]["actions"] + fw["counts"]["actions_on_candidate_indicators"] == 54


def test_overview_names_the_cycle_of_record_its_date_and_its_bodies(offline):
    o = offline.get_overview()
    c = o["cycle_of_record"]
    assert c["cycle"] == "scan_2026-09-10_rj2"
    assert c["measured"] == "2026-09-10"
    assert c["n_bodies"] == len(c["bodies"]) == 16
    assert "BEA" in c["bodies"]


def test_overview_reports_the_projection_gate_status(tools):
    """Decision 3: a client must be able to tell whether a Cypher answer is current. The status
    is COMPUTED against the database, cell for cell, not read off a cached claim — the whole
    reason DD-057 exists is that a stale projection does not look stale, it answers."""
    g = tools.get_overview()["projection_gate"]
    assert g["status"] == "green", g
    assert g["nodes_compared"] > 100
    assert g["mismatches"] == []
    assert "test_framework_projection_roundtrip" in str(g["locators"])


def test_overview_without_a_graph_reports_the_gate_unverified_not_green(offline):
    g = offline.get_overview()["projection_gate"]
    assert g["status"] == "unverified"
    assert "neo4j" in g["reason"].lower()


# --- get_indicator

def test_indicator_carries_its_definition_construct_spec_rule_tier_and_actions(offline):
    i = offline.get_indicator("A1")
    assert i["code"] == "A1"
    assert "structured data" in i["indicator"]
    assert i["construct"] == "Machine-readable formats"
    assert i["criterion"]["code"] == "A"
    assert i["tier"] == "public"
    assert i["measurement_tier"] == "M"
    assert i["measurement_basis"] == "harness_leg"
    assert i["tier_source"].startswith("rules.CURRENT['A1']")
    assert i["spec"]["rule_id"] == "RULE-A1-v4"
    assert i["rule"]["rule_id"] == "RULE-A1-v4" and i["rule"]["version"] == "v4"
    assert {a["id"] for a in i["actions"]} == {
        "act:a1-serve-the-data-files-with-their-own-media-type",
        "act:a1-publish-a-structured-distribution"}


def test_an_unknown_indicator_code_says_so_and_lists_the_codes(offline):
    i = offline.get_indicator("ZZ9")
    assert "not an indicator" in i["error"]
    assert "A1" in i["codes"]


def test_indicator_reports_pass_and_fail_on_the_cycle_of_record(tools):
    i = tools.get_indicator("A1")
    v = i["cycle_of_record"]["verdicts"]
    assert i["cycle_of_record"]["cycle"] == "scan_2026-09-10_rj2"
    assert sum(v.values()) > 0
    assert set(v) <= {"pass", "fail", "error", "not_applicable"}


# --- get_body

def test_body_names_the_finding_and_the_evidence_for_every_judged_cell(tools):
    b = tools.get_body("BEA")
    assert b["body"] == "BEA" and b["cycle"] == "scan_2026-09-10_rj2"
    assert b["n_judged"] == len(b["legs"]) > 0
    assert b["summary"].startswith(f"{b['n_failing']} failing of {b['n_judged']} judged")
    for cell in b["legs"]:
        assert cell["finding_id"].startswith("fnd_"), cell
        assert cell["verdict"] in ("pass", "fail", "error", "not_applicable")
        assert cell["reason"], cell
        assert cell["evidence"], f"{cell['leg']} cites no observation"
        for ev in cell["evidence"]:
            # Either the response body is retained under its sha256, or the observation says
            # in words why there is none — the `links` collector HEAD-probes and keeps no body
            # (`assessment/harness/scan/collectors/links.py`). What is forbidden is a cell
            # that cites evidence and cannot say where it is.
            if ev["retained"]:
                assert ev["sha256"] and ev["path"] and ev["sha256_verified"], ev
            else:
                assert ev["retention"] and ev["locator"]["kind"] == "graph", ev


def test_an_unknown_body_says_so_and_lists_the_bodies(offline):
    b = offline.get_body("NOSUCH")
    assert "not a body" in b["error"] and "BEA" in b["bodies"]


# --- get_prescriptions

def test_prescriptions_with_no_argument_rank_by_bodies_failing_now(offline):
    p = offline.get_prescriptions()
    n = [a["value"]["bodies_failing_now"] for a in p["actions"]]
    assert len(p["actions"]) == 54
    assert n == sorted(n, reverse=True)
    assert p["band_note"].startswith("Notional relative estimate")


def test_prescriptions_for_one_body_cover_exactly_the_legs_it_fails(offline):
    """The matrix says which legs the body fails; the record says which actions close them.
    `scripts/prescriptions.py` is the authority for both and this tool is that script as a
    query, so the two must agree leg for leg."""
    import importlib.util as iu
    spec = iu.spec_from_file_location("_presc", REPO / "scripts" / "prescriptions.py")
    presc = iu.module_from_spec(spec)
    sys.modules[spec.name] = presc
    spec.loader.exec_module(presc)
    cycle = presc.snapshot_cycle()
    expected = set(presc.failing(cycle)["BEA"])

    p = offline.get_prescriptions(body="BEA")
    assert {a["leg"] for a in p["actions"]} == {
        l for l in expected if any(x["leg"] == l for x in presc.actions(presc.load_record()))}
    assert p["failing_legs"] and set(p["failing_legs"]) == expected


def test_prescriptions_filter_by_leg(offline):
    p = offline.get_prescriptions(leg="A5")
    assert p["actions"] and {a["leg"] for a in p["actions"]} == {"A5"}


def test_a_band_with_no_estimate_prints_pending_and_never_a_number(offline):
    """Decision 2. Every band carries a notional value since
    `cc_tasks/2026-09-17_notional_bands.md`, so this drives the rule with an action whose band
    is empty again — the state the task file still describes — rather than asserting the rule
    is unreachable."""
    import importlib.util as iu
    spec = iu.spec_from_file_location("_presc2", REPO / "scripts" / "prescriptions.py")
    presc = iu.module_from_spec(spec)
    sys.modules[spec.name] = presc
    spec.loader.exec_module(presc)
    a = presc.actions(presc.load_record())[0]

    assert offline.band_word(a, "effort") not in ("", "pending")
    blank = {**a, "effort_band": "", "effort_source": "estimate:pending"}
    assert offline.band_word(blank, "effort") == "pending"
    # And the tool prints the word, not the raw cell.
    row = next(r for r in offline.get_prescriptions()["actions"] if r["id"] == a["id"])
    assert row["effort"] == offline.band_word(a, "effort")


# --- get_evidence

def test_evidence_walks_the_finding_to_the_retained_bytes(tools):
    b = tools.get_body("BEA")
    fid = b["legs"][0]["finding_id"]
    e = tools.get_evidence(fid)
    assert e["finding_id"] == fid
    assert e["rule_id"] and e["rule_version"] and e["reason"]
    assert e["observations"]
    for o in e["observations"]:
        assert o["obs_id"].startswith("obs_")
        assert o["sha256"] and o["captured_at"]
        assert o["exists"] is True, o          # the bytes are on disk, not just named
        assert o["sha256_verified"] is True, o  # and they hash to the name


def test_an_unknown_finding_id_says_so(tools):
    e = tools.get_evidence("fnd_000000000000000000000000")
    assert "no Finding" in e["error"]


# --- get_document and search_text

def test_get_document_returns_the_document_with_its_locator(tools):
    d = tools.get_document("w3c-dwbp-2017")
    assert d["doc_id"] == "w3c-dwbp-2017"
    assert d["primary_url"].startswith("http")
    assert d["content_hash"]
    assert d["counts"]["definitions"] >= 0


def test_an_unknown_doc_id_says_so(tools):
    d = tools.get_document("no-such-document-here")
    assert "no Document" in d["error"]


def test_search_text_carries_a_doc_id_on_every_corpus_hit(tools):
    s = tools.search_text("machine-readable")
    assert s["hits"]
    kinds = {h["kind"] for h in s["hits"]}
    assert kinds & {"definition", "indicator", "action", "technique"}
    for h in s["hits"]:
        assert "doc_id" in h and "section" in h
        if h["kind"] in ("definition", "technique"):
            assert h["doc_id"], h


# --- get_cycle_of_record

def test_cycle_of_record_carries_both_hashes_the_matrices_and_the_supersession(tools):
    c = tools.get_cycle_of_record()
    assert c["cycle"] == "scan_2026-09-10_rj2"
    assert c["kind"] == "rejudged"
    assert c["derived_from"] == "scan_2026-09-10"
    assert len(c["derived_from_params_hash"]) == 64
    assert len(c["judgement_params_hash"]) == 64
    assert c["derived_from_params_hash"] != c["judgement_params_hash"]
    assert {m["kind"] for m in c["matrices"]} == {"tierA", "product"}
    # DN-004: `_rj3` is on the log and moved no verdict this report publishes.
    assert c["supersession"]["successor"] == "scan_2026-09-10_rj3"
    assert c["supersession"]["verdict_moves"] == 0
    assert "superseded" in c["supersession"]["line"]


# --- run_cypher

def test_run_cypher_answers_a_read(tools):
    r = tools.run_cypher("MATCH (i:AssessmentIndicator) RETURN count(i) AS n")
    assert r["rows"] == [{"n": 49}]
    assert r["database"] == "seldon-ai-readiness-kg"


def test_run_cypher_caps_the_rows_it_returns(tools, guard):
    r = tools.run_cypher("MATCH (f:Finding) RETURN f.finding_id AS id")
    assert len(r["rows"]) == guard.MAX_ROWS
    assert r["truncated"] is True


def test_run_cypher_returns_the_refusal_as_a_message_not_an_exception(tools):
    """Decision 1, in the tool rather than in the rail: no raise, a row-shaped answer that
    says why."""
    r = tools.run_cypher("MATCH (i:AssessmentIndicator) SET i.tier = 'paid'")
    assert "rows" not in r
    assert r["refused"].startswith("refused:") and "SET" in r["refused"]


# --- the locators, walked

def test_every_locator_in_every_tool_answer_resolves(tools):
    """Decision 2: "A result without a source locator … is a defect". A locator that is
    present and points at nothing is the same defect wearing a field name, so every locator
    every tool emits is resolved against the thing it names."""
    b = tools.get_body("BEA")
    answers = {
        "get_overview": tools.get_overview(),
        "get_indicator": tools.get_indicator("A1"),
        "get_body": b,
        "get_prescriptions": tools.get_prescriptions(body="BEA"),
        "get_prescriptions_all": tools.get_prescriptions(),
        "get_evidence": tools.get_evidence(b["legs"][0]["finding_id"]),
        "get_document": tools.get_document("w3c-dwbp-2017"),
        "search_text": tools.search_text("machine-readable"),
        "get_cycle_of_record": tools.get_cycle_of_record(),
        "run_cypher": tools.run_cypher("MATCH (r:Rule {current: true}) RETURN r.rule_id AS id"),
    }
    bad = []
    for name, ans in answers.items():
        locs = _all_locators(ans)
        if not locs:
            bad.append(f"{name}: carries NO locator")
            continue
        for loc in locs:
            got = tools.resolve_locator(loc)
            if not got["resolved"]:
                bad.append(f"{name}: {loc} -> {got['detail']}")
    assert not bad, "\n".join(bad[:20])


def test_the_resolver_refuses_a_locator_that_points_at_nothing(tools):
    """The negative control for the test above: a resolver that returned True for everything
    would make that test vacuous."""
    assert not tools.resolve_locator(
        {"kind": "record", "path": "framework/ai_readiness_framework.json",
         "node_id": "ind:NOPE"})["resolved"]
    assert not tools.resolve_locator(
        {"kind": "evidence", "path": "corpus/evidence/scan/ff/deadbeef", "sha256": "d" * 64}
    )["resolved"]
    assert not tools.resolve_locator(
        {"kind": "graph", "label": "Finding", "id_property": "finding_id",
         "id": "fnd_000000000000000000000000"})["resolved"]
    assert not tools.resolve_locator({"kind": "nonesuch"})["resolved"]


def test_every_technique_quote_parses_to_a_doc_id(tools_mod, offline):
    """`search_text` and the prescription locators get their `doc_id` by parsing the technique
    quote. A parser that matched a few and returned `None` for the rest would leave most hits
    unlocated while every test above still passed, so the parse rate is asserted outright."""
    quotes = [q for n in offline._nodes("Action")
              for q in (n["properties"].get("technique_source") or [])]
    unparsed = [q for q in quotes if tools_mod._technique_address(q)[0] is None]
    assert quotes, "the record holds no technique sources; this proves nothing"
    assert unparsed == [], unparsed[:3]


# ------------------------------------------------- decision 5: the tools through an MCP client

@pytest.fixture(scope="module")
def server_mod():
    return _mod("airkg_server")


@pytest.fixture(scope="module")
def client_call(server_mod, tools_mod):
    """An in-process MCP client over the real server object. No stdio, no subprocess: FastMCP's
    in-memory transport IS the client, which is what makes "ask each tool one question" an
    acceptance test rather than a transcript (decision 5)."""
    g = tools_mod.Graph()
    if not g.available():
        pytest.skip("Neo4j unreachable, the MCP server's graph answers are unverified")
    from fastmcp import Client
    mcp, _tools = server_mod.create_server(graph=g)

    def call(name, args=None):
        async def go():
            async with Client(mcp) as c:
                return await c.call_tool(name, args or {})
        return asyncio.run(go()).data

    call.mcp = mcp
    return call


def test_the_client_lists_the_nine_tools_in_order(client_call, tools_mod):
    from fastmcp import Client

    async def go():
        async with Client(client_call.mcp) as c:
            return await c.list_tools()
    listed = asyncio.run(go())
    assert [t.name for t in listed] == list(tools_mod.TOOL_ORDER)
    assert len(listed) == 9


def test_every_tool_carries_a_description_and_is_marked_read_only(client_call):
    from fastmcp import Client

    async def go():
        async with Client(client_call.mcp) as c:
            return await c.list_tools()
    for t in asyncio.run(go()):
        assert t.description and len(t.description) > 40, t.name
        assert t.annotations.readOnlyHint is True, t.name


ONE_QUESTION_EACH = [
    ("get_overview", {}, lambda a: a["cycle_of_record"]["cycle"] == "scan_2026-09-10_rj2"),
    ("get_indicator", {"code": "A5"}, lambda a: a["code"] == "A5" and a["actions"]),
    ("get_body", {"name": "NCHS"}, lambda a: a["body"] == "NCHS" and a["legs"]),
    ("get_prescriptions", {"body": "NCHS"}, lambda a: a["body"] == "NCHS" and a["actions"]),
    ("get_document", {"doc_id": "rfc-9309-robots-exclusion-protocol"},
     lambda a: a["doc_id"] == "rfc-9309-robots-exclusion-protocol"),
    ("search_text", {"q": "sitemap"}, lambda a: a["hits"]),
    ("get_cycle_of_record", {}, lambda a: len(a["judgement_params_hash"]) == 64),
    ("run_cypher", {"query": "MATCH (a:Action) RETURN count(a) AS n"},
     lambda a: a["rows"] == [{"n": 54}]),
]


@pytest.mark.parametrize("name,args,ok", ONE_QUESTION_EACH,
                         ids=[r[0] for r in ONE_QUESTION_EACH])
def test_each_tool_answers_one_question_through_the_client(client_call, name, args, ok):
    answer = client_call(name, args)
    assert ok(answer), answer


def test_get_evidence_answers_through_the_client(client_call):
    """Separate from the table above because its argument is an id the previous call yields —
    a two-step traversal is the shape a client actually uses."""
    body = client_call("get_body", {"name": "NCHS"})
    fid = body["legs"][0]["finding_id"]
    e = client_call("get_evidence", {"finding_id": fid})
    assert e["finding_id"] == fid and e["observations"]


def test_a_write_through_the_client_comes_back_as_a_refusal_not_an_error(client_call):
    a = client_call("run_cypher", {"query": "MATCH (n) DETACH DELETE n"})
    assert a["refused"].startswith("refused:") and "DELETE" in a["refused"]


def test_the_server_refuses_to_start_against_another_database(server_mod):
    with pytest.raises(SystemExit) as exc:
        server_mod.create_server(database="wintermute-intake")
    assert "wintermute-intake" in str(exc.value)


def test_the_server_starts_without_a_graph_and_says_so(server_mod, tools_mod):
    """The record-only mode is a real mode: `seldon verify`, a CI box and a laptop without the
    database all get a server whose framework and prescription answers are complete."""
    mcp, tools = server_mod.create_server(graph=None)
    assert isinstance(tools, tools_mod.Tools)
    assert tools.get_overview()["projection_gate"]["status"] == "unverified"


# ------------------------------------------------------------ decision 4: the registration

def test_the_repo_registers_the_server_in_mcp_json():
    """Decision 4. The file Claude Code reads must name the interpreter that can import
    `fastmcp` and the server file that exists."""
    import json
    cfg = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
    entry = cfg["mcpServers"]["ai-readiness-kg"]
    assert Path(entry["command"]).exists(), entry["command"]
    server = entry["args"][-1]
    assert (REPO / server).exists() or Path(server).exists(), server
    assert "mcp/airkg_server.py" in server


def test_the_generated_doc_names_every_tool(tools_mod):
    """Decision 4: one page, with the tool list and a real call and output each."""
    doc = (REPO / "docs" / "design" / "mcp_over_the_graph.md").read_text(encoding="utf-8")
    for name in tools_mod.TOOL_ORDER:
        assert f"### `{name}" in doc, f"the page does not document {name}"
    assert "`mcp/airkg_doc.py`" in doc


def test_the_page_on_disk_is_what_the_tools_answer_now(tools):
    """Decision 4 says the page is "generated by running the tools, not typed", and this is
    what makes that checkable: the generator re-renders into memory and compares. A page whose
    example output no longer matches the tool is the drift a hand-written page has silently."""
    import importlib.util as iu
    spec = iu.spec_from_file_location("airkg_doc", MCP_DIR / "airkg_doc.py")
    doc = iu.module_from_spec(spec)
    sys.modules[spec.name] = doc
    spec.loader.exec_module(doc)
    assert doc.main(["--check"]) == 0


def test_a_locator_label_is_never_interpolated_into_cypher_unchecked(tools):
    """Invariant 4: this repository never interpolates payload text into Cypher. The only two
    places this server builds a query from a name are the projection gate (a literal tuple)
    and the `graph` locator resolver, whose label arrives inside a dict. A label that is not a
    label this graph has is refused before a query is built, not sent."""
    bad = tools.resolve_locator(
        {"kind": "graph", "label": "Finding) DETACH DELETE (n", "id_property": "finding_id",
         "id": "x"})
    assert not bad["resolved"]
    assert "not a label" in bad["detail"]
    assert tools.resolve_locator(
        {"kind": "graph", "label": "Rule", "id_property": "rule_id",
         "id": "RULE-A1-v4"})["resolved"]


# ------------------------------------------- the credentials an MCP client does NOT hand over

def test_the_server_connects_with_no_neo4j_variables_in_the_environment(
        tools, tools_mod, monkeypatch):
    """The defect this replays was found by driving the registered server over stdio, not by
    reading it: an MCP client starts the server process with an environment of its own, and
    `seldon.config.get_neo4j_driver` reads environment variables ONLY — falling back to the
    literal `neo4j`/`password` when they are unset. So the same code that answered `green` in a
    shell answered `AuthError` to every graph question the moment Claude Code launched it, and
    eight of the nine tools would have said "Neo4j unreachable" to a client with no way to tell
    that from a real outage.

    The server resolves credentials the way the rest of this repository does — the ONE resolver
    in `scripts/build_projection.py`: both environment spellings, then `~/.wintermute/.env`,
    which is the fallback `CLAUDE.md` documents. No second parser.
    """
    for var in ("NEO4J_USER", "NEO4J_PASS", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    # The `tools` fixture has already reached the database in this process, so an unreachable
    # graph HERE is the credential defect and not an outage: this fails, it does not skip.
    g = tools_mod.Graph()
    assert g.available(), g.error
    rows, _ = g.read("MATCH (r:Rule) RETURN count(r) AS c", limit=1)
    assert rows[0]["c"] > 0


def test_no_credentials_anywhere_fails_loud_and_never_guesses_a_password(
        tools_mod, monkeypatch, tmp_path):
    """Standard 4: a missing credential fails at startup naming the exact variables, and never
    falls through to a default that produces a wrong answer. `neo4j`/`password` IS such a
    default, and it is what produced the AuthError above."""
    for var in ("NEO4J_USER", "NEO4J_PASS", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))       # no ~/.wintermute/.env under this HOME
    g = tools_mod.Graph()
    with pytest.raises(SystemExit) as exc:
        g.available()
    msg = str(exc.value)
    assert "NEO4J_USER" in msg and "wintermute" in msg
