#!/usr/bin/env python3
"""The ai-readiness-kg graph as a read-only MCP server, on stdio. **Zero spend.**

`cc_tasks/2026-09-17_mcp_over_the_graph.md`, implementing DN-005 §2.4: "the same server shape
over the `ai-readiness-kg` Neo4j database … exposes the research, the documentation, the
framework, the evidence and the prescriptions through one interface."

WHY THIS EXISTS
  Everything this project measures is answerable today only by reading a file, running a
  script or typing Cypher. The framework record, the published matrices, the retained response
  bodies and the prescription layer are four different shapes in three different places, and
  nothing lets a client ask one question across them. This server is that one interface, and
  decision 2's rule is what makes it usable as evidence rather than as a summary: **every fact
  comes back with the address a stranger would open to check it** (DD-001), and
  `resolve_locator` opens it.

ADOPT BEFORE CREATE (Standard 7), and the two servers this was copied from:

  * `/Users/brock/Documents/GitHub/icsp_notebook/kg/mcp_server.py` — the fss-policy-kg server.
    **Copied:** the whole architecture (thin FastMCP shell over a verb layer that tests without
    a transport), the read-only posture with two belts, string-literal stripping in the keyword
    rail, the `MAX_ROWS = 200` flood cap, and the `run_cypher` escape hatch as the one power
    tool beside a set of named verbs. **Differed:** its database rail is a pattern that refuses
    `seldon-*`, and this project's database IS `seldon-ai-readiness-kg` — see
    `airkg_guard.assert_allowed_db`, which is an allow-list of one name read from
    `seldon.yaml`. Its refusals raise; decision 1 says a refusal here is a returned message.
    It has no locator discipline: its verbs return node ids and verbatim text, which is a
    locator for a corpus of documents and not for a graph whose facts come from four sources.
  * `/Users/brock/Documents/GitHub/census-mcp-server/src/census_mcp/server.py` — the Census
    server. **Copied:** the orientation tool a client is told to call first (`get_overview`
    here, `get_methodology_guidance` there), and the shape that matters most — every data
    answer carries the pragmatics needed to read it, so the client cannot get a number without
    the caveat. Here that is `projection_gate` on `get_overview` and on every `run_cypher`
    result, the `(notional)` marker and `band_note` on every prescription answer, and the
    `hash_meaning` sentence on the cycle. **Differed:** it is built on the low-level
    `mcp.server.Server` rather than FastMCP, under its ADR-005 (FastMCP's handshake succeeded
    but its tools did not surface in Claude Desktop on mcp 1.9.4). That was a 2025 defect
    against an old library; fastmcp 3.2.3 is what the fss-policy-kg server runs under today
    and what this one uses. If tools ever fail to surface in Desktop, ADR-005 is the first
    place to look and this paragraph is the pointer.

RUN
    /opt/anaconda3/bin/python3 mcp/airkg_server.py            # stdio, the project database
    /opt/anaconda3/bin/python3 mcp/airkg_server.py --no-graph # record-only, no Neo4j at all
    /opt/anaconda3/bin/python3 mcp/airkg_server.py --no-graph --run out/<frame>   # your site

`mcp/` is deliberately NOT a Python package. A `mcp/__init__.py` at this repository's root
shadows the installed `mcp` distribution that `fastmcp` imports, and `import fastmcp` then
fails with `ImportError: cannot import name 'McpError' from 'mcp'` for the whole test suite.
A directory with no `__init__.py` is not a regular package, so the installed distribution still
wins the import — and loading these modules by path is the idiom `scripts/` already uses here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MCP_DIR))

import airkg_guard as guard      # noqa: E402
import airkg_tools as T          # noqa: E402

try:
    from fastmcp import FastMCP
except ImportError:              # fail loud (Standard 4)
    raise SystemExit("FATAL: fastmcp is required. /opt/anaconda3/bin/python3 has it; "
                     "otherwise `pip install 'fastmcp>=3'`.")

SERVER_NAME = "ai-readiness-kg"

INSTRUCTIONS = """\
Read-only knowledge graph of the AI-readiness framework for federal statistical publishers,
its measurement instrument, and the evidence behind every verdict it has published.

CALL `get_overview` FIRST. It gives the framework's counts by measurement tier and basis, the
cycle of record every verdict comes from, the bodies on that cycle, and — the part that decides
whether anything else here is current — the status of the framework projection gate.

EVERY ANSWER CARRIES LOCATORS. A `locators` list (or a `locator` on a row) names the record
node, the matrix cell, the retained response body and its sha256, the graph node or the corpus
document a fact came from. Cite them. `run_cypher` returns the projection gate's status beside
its rows for the same reason: a stale projection does not look stale, it answers.

TWO SOURCES AND NO THIRD. The framework record and the published matrices are the source of
truth; Neo4j is a projection of them and of the event log. Framework questions are answered
from the record even when the graph holds the same nodes.

BANDS ARE NOTIONAL. Effort and cost on a prescription are relative estimates assigned by
technique class, not predictions of anyone's calendar or budget; `band_note` says so once per
answer. A band with no estimate behind it reads `pending` and never a number. A tool's cost on
`get_requirements` is notional the same way, by tool kind.

WHAT A TEST NEEDS. `get_requirements` answers what stands between an indicator and a verdict —
a tool, the site owner's account, the agency's records, an evaluation set, a second
measurement, the publisher admitting the identified client — and, for one body, groups what the
harness could not see under the requirement that would unlock it.

READ-ONLY, AND SCOPED TO ONE DATABASE. Any write clause or unlisted procedure in `run_cypher`
comes back as a refusal message. This server touches no other graph.
"""


def create_server(graph: T.Graph | None = ..., database: str | None = None, run=None):
    """Build the tools and register them on a fresh FastMCP instance.

    Returns `(mcp, tools)` so a test, a smoke check or the doc generator can reach the verbs
    without a transport — the reason the bodies live in `airkg_tools` and not here.

    `graph` defaults to a `Graph` over the project database; pass `None` for a record-only
    server. `run` points the verbs at an adopter's frame directory (`Tools`). The database rail fires HERE, at startup, before a driver exists: a mis-scoped
    server must never serve.
    """
    if graph is ...:
        graph = T.Graph(database)
    elif database is not None:
        guard.assert_allowed_db(database)
    mcp = FastMCP(SERVER_NAME, instructions=INSTRUCTIONS)
    tools = T.Tools(graph=graph, run=run)
    _register(mcp, tools)
    registered = [t for t in mcp._tool_manager._tools] if hasattr(mcp, "_tool_manager") else []
    del registered
    return mcp, tools


def _register(mcp: FastMCP, t: T.Tools) -> None:
    """The ten verbs as `@mcp.tool` wrappers, in `TOOL_ORDER`.

    Each wrapper only forwards. The docstrings ARE the LLM's interface — they are what a client
    reads to decide which tool to call — so they say what the tool answers and what its answer
    may not be read as, in the Census server's manner.
    """

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Overview (call this first)"})
    def get_overview() -> dict:
        """CALL THIS FIRST. What is in this graph and whether its Cypher answers are current.

        Returns: the framework's indicator counts by measurement tier (M measurable now, O with
        an open tool, D declaration-only, unassigned) and by measurement basis; the record's own
        `counts` and the sentence that says what each counter counts; the action and edge
        totals; the cycle of record, the date it was measured, and the bodies on it; and
        `projection_gate`, computed live against the database, cell for cell.

        `projection_gate.status` is `green`, `stale` or `unverified`. Cypher over the framework
        labels is valid only while it is `green` (DD-057) — a stale projection does not look
        stale, it answers.
        """
        return t.get_overview()

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get indicator"})
    def get_indicator(code: str) -> dict:
        """One assessment indicator by code (`A1`, `A11`, `G1-D`, …).

        Returns its text, its construct and criterion, its measurement spec and the CURRENT
        rule that implements it, its access tier and its measurement tier WITH `tier_source`
        (the document or rule that put it there — a tier with no source is a defect here), every
        note the record carries on it, the actions that remediate it, and its pass/fail/error
        counts on the cycle of record.

        An unknown code returns the list of codes, never a guess.
        """
        return t.get_indicator(code)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get body"})
    def get_body(name: str) -> dict:
        """One publisher's row on the cycle of record (`BLS`, `NCHS`, `CENSUS`, …).

        Returns every judged leg with its verdict, the Finding id behind that verdict, the
        rule that produced it, the reason sentence, and the evidence for each cell down to the
        retained response body and its sha256. A cell whose collector retains no body (a HEAD
        link probe) says so and locates the Observation instead.

        The verdicts are one instrument's reading of one cycle, not an agency's grade.
        """
        return t.get_body(name)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get prescriptions"})
    def get_prescriptions(body: str | None = None, leg: str | None = None) -> dict:
        """What to DO about a failing check: the action, its effort and cost band, the technique
        sources behind it, and the rule outcome that verifies it is closed.

        With no argument: every action, ranked by how many bodies fail it now. With `body`: only
        the legs that body fails on the cycle of record, and which of its surfaces failed. With
        `leg`: one check's actions.

        EFFORT AND COST ARE NOTIONAL — relative bands assigned by technique class, printed with
        `band_note`, which says what they are not. They order actions against each other; they
        do not predict a calendar or a budget.
        """
        return t.get_prescriptions(body=body, leg=leg)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get requirements"})
    def get_requirements(indicator: str | None = None, body: str | None = None) -> dict:
        """What a test this harness cannot run alone would NEED: the tool, the account, the
        agency's records, the evaluation set, the second measurement, or the publisher's grant.
        With `indicator` (`C4`, `A11`, …): the tests that would measure it, and for each what it
        requires — kind, notional cost for a tool, who provides it, and the document or
        definition sentence that says so. Requirements on one `route` are needed together; two
        routes are alternatives. An indicator with none says why.
        With `body` (`CENSUS`, `NCHS`, …): everything the harness could not observe for that
        body on the cycle of record — its error cells with their error classes, the unmeasured
        halves and the untested indicators no body is measured on — grouped by the requirement
        that would unlock them, one `line` per requirement.
        With neither: every requirement, ranked by how many indicators it would unlock.
        Tool costs are NOTIONAL bands by tool kind; `band_note` says what they are not.
        """
        return t.get_requirements(indicator=indicator, body=body)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get evidence"})
    def get_evidence(finding_id: str) -> dict:
        """The evidence under one Finding: every Observation it cites, the retained response
        body's path and sha256, whether those bytes are on disk and hash to that name, when they
        were captured, the error class (both the recorded one and the corrected one where an
        overlay exists), and the rule version that judged them.

        This is the bottom of the traversal: `get_body` gives a Finding id, this gives the
        bytes.
        """
        return t.get_evidence(finding_id)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get document"})
    def get_document(doc_id: str) -> dict:
        """One corpus document by doc_id: title, publication date, source type, primary URL,
        content hash, what the graph hangs off it, and which indicators it evidences.

        The corpus is third-party work retained as evidence under its own terms. An unknown
        doc_id returns the nearest ids, never a guess.
        """
        return t.get_document(doc_id)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Search text"})
    def search_text(q: str, limit: int = 20) -> dict:
        """Lexical, case-insensitive substring search over the definition layer (graph), the
        indicator text, the action descriptions and the technique quotes (record).

        Every hit carries a locator that resolves. `doc_id` and `section` are the corpus address
        where the text has one — a Definition and a technique quote both do; indicator and
        action text is the record's own prose and its address is the record node on the hit.

        This is lexical and not semantic: absence of a hit is absence of a STRING, never
        evidence that the graph lacks a topic.
        """
        return t.search_text(q, limit=limit)

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Get cycle of record"})
    def get_cycle_of_record() -> dict:
        """Which measurement cycle every published verdict in this graph comes from.

        Returns its name and kind, the collection it was judged from and that collection's
        parameter hash, this judgement's own parameter hash, the rules it ran, the legs it
        judged and the legs it did not with the reason, its matrices, and whether a later
        judgement of the same evidence supersedes it — with the count of verdicts that moved.

        A re-judgement re-reads stored observations and fetches nothing: the evidence is the
        source cycle's, the judgement is this one's.
        """
        return t.get_cycle_of_record()

    @mcp.tool(annotations={"readOnlyHint": True, "title": "Run read-only Cypher"})
    def run_cypher(query: str) -> dict:
        """The escape hatch for questions the nine verbs above do not cover. READ-ONLY.

        Any write clause (CREATE/MERGE/SET/DELETE/REMOVE/DROP/FOREACH/LOAD CSV) or any
        procedure outside the read allow-list comes back as a `refused` message rather than an
        error. Scoped to this project's database and capped at 200 rows.

        The result carries `projection_gate`: when it is not `green`, an answer about the
        framework labels is not the record.
        """
        return t.run_cypher(query)

    # Registration order is the listing order, and `TOOL_ORDER` is what `get_overview`
    # advertises; a tool registered here and missing there would be a tool no overview names.
    assert tuple(f.__name__ for f in (get_overview, get_indicator, get_body,
                                      get_prescriptions, get_requirements, get_evidence,
                                      get_document, search_text, get_cycle_of_record,
                                      run_cypher)) == T.TOOL_ORDER


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Read-only MCP server over the ai-readiness-kg graph (stdio transport).")
    ap.add_argument("--no-graph", action="store_true",
                    help="record-only: answer from the framework record and the published "
                         "matrices, open no database")
    ap.add_argument("--database", default=None,
                    help="refused unless it is seldon.yaml's neo4j.database; present so a "
                         "mis-scoped invocation fails loudly instead of quietly")
    ap.add_argument("--run", metavar="DIR", default=None,
                    help="answer over an adopter's frame directory (out/<frame>/): its cycle of "
                         "record, its matrices and — with --no-graph — the Findings and "
                         "Observations in its payload. cc_tasks/2026-09-19_adopter_path.md")
    args = ap.parse_args(argv)
    mcp, _tools = create_server(graph=None if args.no_graph else ...,
                                database=args.database, run=args.run)
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
